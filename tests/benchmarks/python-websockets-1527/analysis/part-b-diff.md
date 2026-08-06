# Part B Diff — Connection Keepalive Lifecycle

**Commit:** `4d229bf9f583d593aa103287aee0a77c9fbc3a79`
**Timestamp:** 2026-08-06T13:46:59Z
**External bug info:** NOT consulted

---

## Classification Key

| Class | Description |
|---|---|
| A | Requirement semantics missing from implementation model |
| B | Implementation-only accidental state |
| C | Legitimate refinement of requirement-level state |
| D | Missing or ambiguous requirement |
| E | Possible implementation defect |
| F | Test-coverage gap |
| G | Runtime detail outside statechart scope |

---

## Diff Results

### 1. CloseDeadlineExpired disposition — THE CRITICAL FINDING

| | Part A (code) | Part B (requirements) |
|---|---|---|
| State | ClosurePending / Close_DeadlineSet | Close_DeadlineSet |
| Event | EV-11 CloseDeadlineExpired | EV-11 CloseDeadlineExpired |
| Expected | transition → ClosureObservable + force caller notification | UNSPECIFIED (requirement gap) |
| Observed | close_transport() + set_recv_exc() + AWAITS connection_lost_waiter | N/A (blind) |

**Classification: E (Possible implementation defect)**

Part A reveals: after close_timeout expires and close_transport() runs, the code RE-ENTERS the wait for connection_lost(). The caller remains blocked. Part B identified this cell as UNSPECIFIED — neither code nor requirements specify what should happen. The code takes an action (close transport) but doesn't complete the chain (notify callers). The requirements say "bounds the time" but don't define the bounding action.

The boundedness requirement (R-07) is violated in practice: the close_timeout fires, closes the transport, but does not resolve the caller's wait. The timeout bounds one step (transport closure) but not the full chain (caller notification).

**This is the primary finding. It matches success criterion: "a missing transition after close-deadline expiry."**

### 2. connection_lost_waiter as single point of synchronization

| | Part A | Part B |
|---|---|---|
| What resolves caller wait? | `connection_lost_waiter.set_result()` in `connection_lost()` only | Requirements say TransportLost unblocks (R-09) but don't specify if there's an alternative path |
| What happens without TransportLost? | Nothing resolves the waiter | R-07 implies close_timeout should force resolution |

**Classification: E — caller notification incorrectly coupled to transport-loss callback delivery.**

The implementation has a single synchronisation point (`connection_lost_waiter`) that is only resolved by the event loop callback. The close_timeout mechanism closes the transport but does not resolve the waiter. Part B's requirement analysis correctly identifies that R-07 demands an alternative resolution path.

### 3. Four lifecycle regions without explicit synchronisation

| | Part A | Part B |
|---|---|---|
| Heartbeat → Protocol | protocol.fail() changes state | R-04: "initiates abnormal closure" |
| Protocol → Transport | send_context → close_transport() or wait for connection_lost() | R-07: close_timeout bounds closing |
| Transport → Caller | connection_lost_waiter.set_result() only | R-09: "pending receives are unblocked" |

**Classification: A — Requirement semantics missing from implementation model.**

Part B models four regions that must synchronize. Part A shows three of the four synchronizations exist, but the Transport → Caller synchronization has only one path (connection_lost callback). The close_timeout path (Protocol → Transport → Caller) is incomplete — it reaches Transport but never reaches Caller.

### 4. Keepalive task AssertionError

| | Part A | Part B |
|---|---|---|
| What happens after keepalive timeout? | `raise AssertionError("send_context() should wait for connection_lost()")` | Requirements don't specify task lifecycle |

**Classification: B — Implementation-only accidental state.**

The keepalive() method contains a runtime assertion that assumes send_context() always waits for connection_lost(). When close_timeout fires and send_context() returns before connection_lost(), the assertion fails. This is an implementation detail the requirements don't address.

### 5. set_recv_exc race condition

| | Part A | Part B |
|---|---|---|
| Close_timeout sets recv_exc | TimeoutError | — |
| connection_lost sets recv_exc | Actual exception (e.g., ConnectionClosed) | — |
| Which wins? | First-caller-wins (if self.recv_exc is None guard) | R-12: "must preserve abnormal-close classification" |

**Classification: E — Possible implementation defect.**

If close_timeout fires first, it sets `recv_exc = TimeoutError`. When connection_lost() fires later, `set_recv_exc(exc)` returns early because `recv_exc is not None`. The caller sees TimeoutError instead of the keepalive-timeout cause. This violates R-12 (cause preservation) because the keepalive timeout's `CloseCode.INTERNAL_ERROR` is masked by the close_timeout's `TimeoutError`.

---

## Summary

| Class | Count | Key finding |
|---|---|---|
| A | 1 | Transport → Caller synchronization missing close_timeout path |
| B | 1 | Keepalive AssertionError assumption |
| C | 0 | — |
| D | 1 | R-07 doesn't specify CloseDeadlineExpired mechanism |
| E | 3 | Q-C1 (unbounded closure), recv_exc race, connection_lost_waiter coupling |
| F | 1 | No test for stalled transport after close_timeout |
| G | 0 | — |

**Primary finding:** `CloseDeadlineExpired` does not force caller-visible termination. The close_timeout closes the transport but re-enters the wait for `connection_lost_waiter`, which only resolves via event loop callback. This is a lifecycle disagreement (PA-21) between the close-timeout track (Protocol → Transport) and the caller-notification track (Transport → Caller).

**Secondary finding:** The close_timeout's `TimeoutError` can overwrite the keepalive timeout's abnormal close cause, violating R-12.

**No external bug information was consulted. Findings frozen.**
