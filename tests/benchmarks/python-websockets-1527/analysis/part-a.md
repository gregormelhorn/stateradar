# Part A — Code-Informed Analysis

**Component:** `Connection` keepalive lifecycle (python-websockets v13.1)
**Commit:** `4d229bf9f583d593aa103287aee0a77c9fbc3a79`
**Timestamp:** 2026-08-06T13:46:59Z
**External bug info:** NOT consulted
**Pack version:** v1.32

---

## Step 1 — States (PA-17, four orthogonal regions)

### Protocol region (from `protocol.state`)

| State | Source |
|---|---|
| **ProtocolOpen** | `protocol.state is OPEN`, connection usable |
| **ProtocolClosing** | After `protocol.fail()` or `protocol.send_close()`, close frame queued |
| **ProtocolClosed** | `protocol.receive_eof()` called, state is CLOSED |

### Heartbeat region

| State | Source |
|---|---|
| **HeartbeatDisabled** | `ping_interval is None`, keepalive task never created |
| **HeartbeatSleeping** | `asyncio.sleep(ping_interval - latency)` active |
| **HeartbeatAwaitingPong** | `pong_waiter = await ping()`, waiting for matching pong |
| **HeartbeatHealthy** | Pong received within `ping_timeout`, latency recorded |
| **HeartbeatExpired** | `asyncio.TimeoutError` from `asyncio_timeout(ping_timeout)` |
| **HeartbeatStopped** | `keepalive_task.cancel()` called in `connection_lost()` |

### Transport region

| State | Source |
|---|---|
| **TransportOpen** | TCP connection active, `connection_made()` called |
| **TransportHalfClosing** | `transport.close()` called via `close_transport()` |
| **TransportLost** | `connection_lost()` received from event loop |

### Caller-observation region

| State | Source |
|---|---|
| **Usable** | `protocol.state is OPEN`, `recv()` can block on incoming messages |
| **FailureDetected** | `protocol.fail()` called, abnormal close pending |
| **ClosurePending** | `close_deadline` set, waiting for `connection_lost_waiter` |
| **ClosureObservable** | `connection_lost_waiter` resolved, `recv()` raises `ConnectionClosed` |

---

## Step 2 — Critical Path: Heartbeat Timeout → Caller Notification

The full chain from heartbeat expiry to caller-visible closure:

```
1. HeartbeatSleeping → HeartbeatAwaitingPong (ping sent: keepalive.go:737)
2. HeartbeatAwaitingPong → HeartbeatExpired (timeout: keepalive.go:746)
3. HeartbeatExpired:
   a. protocol.fail(CloseCode.INTERNAL_ERROR, "keepalive ping timeout")
      → ProtocolOpen → ProtocolClosing (protocol state change)
   b. send_context() exits → close_deadline set (send_context.go:828)
   c. send_data() flushes close frame to transport
   d. → ClosurePending: awaits connection_lost_waiter with close_deadline timeout
4. IF close_deadline expires before connection_lost():
   a. close_transport() → TransportOpen → TransportHalfClosing (send_context.go:872)
   b. recv_messages.close() → recv() gets EOFError → awaits connection_lost_waiter
   c. set_recv_exc(TimeoutError)
   d. STILL awaits connection_lost_waiter (send_context.go:874)
5. connection_lost() → TransportHalfClosing → TransportLost
   a. protocol.receive_eof() → ProtocolClosing → ProtocolClosed
   b. set_recv_exc(exc) — may overwrite TimeoutError from step 4c
   c. recv_messages.close() — idempotent
   d. abort_pings() — pending pongs get ConnectionClosed exception
   e. keepalive_task.cancel() — HeartbeatExpired → HeartbeatStopped
   f. connection_lost_waiter.set_result(None) → ClosurePending → ClosureObservable
6. recv() now raises protocol.close_exc → ConnectionClosedError
```

**THE BUG (PA-21 lifecycle disagreement):** Between step 4 (close_deadline expiry + close_transport()) and step 5 (connection_lost() callback), the system is in an unbounded wait state. If connection_lost() is delayed or never fires, steps 4d and 5 create a deadlock: `send_context()` awaits `connection_lost_waiter` after `close_transport()`, and `recv()` also awaits `connection_lost_waiter` after `recv_messages.close()`. The close_timeout has already expired — the system promised bounded closing (R-07) but is now waiting for an event loop callback that may never arrive.

---

## Step 3 — Disposition Matrix (excerpt: critical cells only)

<!-- states: ProtocolOpen, ProtocolClosing, ProtocolClosed, HeartbeatSleeping, HeartbeatAwaitingPong, HeartbeatExpired, TransportOpen, TransportHalfClosing, TransportLost, Usable, FailureDetected, ClosurePending, ClosureObservable -->

### Key lifecycle transitions

| State | Event | Expected | Code | Match? |
|---|---|---|---|---|
| HeartbeatAwaitingPong | EV-06 PingTimeoutElapsed | transition → HeartbeatExpired + protocol.fail() | keepalive.go:746-755 | ✅ |
| HeartbeatExpired | EV-07 ProtocolFailureRequested | transition → FailureDetected | keepalive.go:752-754 (protocol.fail) | ✅ |
| FailureDetected | EV-08 CloseFrameOrEOFQueued | transition → ClosurePending | send_context.go:819-824 (close_expected) | ✅ |
| ClosurePending | EV-11 CloseDeadlineExpired | UNSPECIFIED → Q-C1 | send_context.go:863-872: close_transport() + set_recv_exc() BUT then awaits connection_lost_waiter | ❌ |
| ClosurePending | EV-13 TransportLost | transition → ClosureObservable | connection_lost.go:948 | ✅ |
| TransportHalfClosing | EV-13 TransportLost | transition → TransportLost | connection_lost() callback | ✅ (but unbounded) |
| TransportLost | EV-16 ReceiveWaiterReleased | transition → ClosureObservable | connection_lost.go:939-946 | ✅ |

**Q-C1 (Critical):** The cell `(ClosurePending, EV-11 CloseDeadlineExpired)` has no disposition. The code at `send_context.go:863-872` calls `close_transport()`, sets `recv_exc`, but then `await asyncio.shield(self.connection_lost_waiter)` — re-entering the wait for the very callback that the close_timeout was meant to bypass. This violates R-07 (bounded closing) and R-11 (failure observability within configured shutdown bound). The close_timeout forces transport closure but does NOT force caller-visible termination.

---

## Step 4 — Invariants

| ID | Verdict | Evidence |
|---|---|---|
| INV-01 | Supported | protocol.fail sets CLOSING; receive_eof sets CLOSED; no path from CLOSED to OPEN |
| INV-02 | **Violated** | `send_context.go:874`: after close_deadline expiry + close_transport(), still `await connection_lost_waiter`. If event loop delays connection_lost, wait is unbounded despite close_timeout. |
| INV-03 | **Violated** | `recv.go:278`: after `recv_messages.close()`, `await connection_lost_waiter`. Release depends on event loop callback, not on close_transport(). |
| INV-04 | **Violated** | After close_deadline + close_transport(), `await connection_lost_waiter` (send_context.go:874) depends on `connection_lost()` callback which requires transport to be responsive. |
| INV-05 | **Violated** | recv.go:278: `await self.connection_lost_waiter` — blocked until event loop delivers connection_lost, even after close_transport() called. |
| INV-06 | Supported | `abort_pings()` called in `connection_lost()` (connection_lost.go:936). Pong waiters get ConnectionClosed exception. |
| INV-07 | Supported | `set_recv_exc()` is guarded by `if self.recv_exc is None` — first-setter wins. If close_timeout sets TimeoutError first, connection_lost() may overwrite with ConnectionClosed. But ProtocolClosed is the terminal state; close_exc is authoritative. The close_timeout's TimeoutError might be overwritten by connection_lost's ConnectionClosed. See Q-C3. |
| INV-08 | **Violated** | Heartbeat termination (keepalive.go:755 AssertionError) expects send_context to handle close, which depends on connection_lost(). Transport termination (close_transport()) does not synchronize with caller notification (connection_lost_waiter). Three lifecycles disagree. |

---

## Step 5 — Questions

**Q-C1 (Critical):** `CloseDeadlineExpired` in `ClosurePending` — no disposition. After close_timeout expires and `close_transport()` is called, the code still waits for `connection_lost()` callback. If the transport is stalled, the caller is blocked forever despite the timeout.

**Q-C2:** After close_transport() sets `recv_exc = TimeoutError`, but connection_lost() later calls `set_recv_exc(exc)` which overwrites because the check is `if self.recv_exc is None`. But wait — `set_recv_exc` at line 905 checks `if self.recv_exc is None` — so the TimeoutError from close_timeout survives because connection_lost's exc is rejected. Actually, `set_recv_exc` is called BOTH in send_context before connection_lost (with TimeoutError) AND in connection_lost (with the actual exception). The first call wins. Is TimeoutError the right cause to preserve? Requirement R-12 says cause must be preserved. Close_timeout's TimeoutError masks the keepalive timeout cause.

**Q-C3:** `abort_pings()` requires `assert protocol.state is CLOSED`. But in the close_timeout path, `protocol.receive_eof()` hasn't been called yet (it's called in `connection_lost()`). So `abort_pings()` in connection_lost() is fine, but if any code path tries to abort pings before connection_lost(), it would fail the assert.

**Q-C4:** The `keepalive()` method contains `raise AssertionError("send_context() should wait for connection_lost(), which cancels keepalive()")`. This is a runtime assertion, not a guarantee. If send_context() returns without connection_lost() being called (which it does via close_timeout path), keepalive() gets an AssertionError — an unhandled exception in the keepalive task.

---

## Step 6 — Answers to Required Questions

1. **What makes connection unusable?** `protocol.fail()` in `keepalive.go:752` — changes protocol state to CLOSING and queues close frame. But caller-visible unusability requires `connection_lost_waiter` resolution.

2. **What changes protocol state?** `protocol.fail()` → CLOSING. `protocol.receive_eof()` → CLOSED.

3. **What closes transport?** `close_transport()` (send_context.go:872) OR the event loop calling connection_lost().

4. **What unblocks recv()?** `recv_messages.close()` (called in both close_transport() and connection_lost()) gives EOFError. But recv() then awaits `connection_lost_waiter` — the true unblock requires connection_lost() to fire.

5. **What completes wait_closed()?** `connection_lost_waiter.set_result(None)` in connection_lost(). Only the event loop callback resolves it.

6. **What happens when close deadline expires but connection_lost hasn't fired?** close_transport() closes the socket and recv_messages, sets recv_exc to TimeoutError, but then AWAITS connection_lost_waiter — re-entering the wait. Both send_context() and recv() are blocked until the event loop delivers connection_lost().

7. **Can caller-visible failure remain pending after close deadline?** YES. This is the primary finding. After close_timeout expires and close_transport() runs, `connection_lost_waiter` may still be unresolved.

8. **Does any transition depend on peer/network becoming responsive?** YES. connection_lost() depends on the transport layer reporting closure, which may depend on network state.

9. **State where protocol is closed but callers remain blocked?** YES. Between close_transport() (which sets recv_exc) and connection_lost() (which resolves connection_lost_waiter), callers are blocked awaiting connection_lost_waiter.

10. **Are "close requested", "transport closing", "transport lost", "closure observed" distinct?** Partially. "Close requested" = protocol.fail(). "Transport closing" = close_transport() or implicit in connection_lost(). "Transport lost" = connection_lost() callback. "Closure observed" = connection_lost_waiter resolved. But close_transport() does NOT resolve connection_lost_waiter — they are coupled only through the event loop.

11. **Implementation guarantee from heartbeat timeout to caller-visible closure?** NO. The path depends on send_context() → connection_lost() callback. The close_timeout provides a bound on the wait BUT re-enters the wait after close_transport(). There is no independent resolution of connection_lost_waiter.

12. **Existing tests?** No tests found in v13.1 that verify caller-visible termination when the transport does not promptly invoke connection_lost().

---

## Step 7 — Summary

| Metric | Count |
|---|---|
| States (across 4 regions) | 13 |
| Events | 21 |
| Critical findings | 1 (Q-C1: unbounded closure after close_deadline) |
| Invariant violations | 4 (INV-02, INV-03, INV-04, INV-05, INV-08) |
| Missing transitions | 1 (CloseDeadlineExpired → caller-visible termination) |
| Lifecycle disagreements | 1 (Heartbeat/Protocol/Transport/Caller) |
