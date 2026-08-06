# Disposition Matrix — python-websockets Keepalive Lifecycle

<!-- states: ProtocolOpen, ProtocolClosing, ProtocolClosed, HeartbeatSleeping, HeartbeatAwaitingPong, HeartbeatExpired, TransportOpen, TransportHalfClosing, TransportLost, Usable, FailureDetected, ClosurePending, ClosureObservable, HeartbeatStopped -->

## Table A — Heartbeat Events

| state | EV-01 KeepaliveEnabled | EV-03 PingIntervalElapsed | EV-05 MatchingPongReceived | EV-06 PingTimeoutElapsed | EV-18 KeepaliveTaskCancelled | EV-19 PendingPingAborted |
|---|---|---|---|---|---|---|
| **HeartbeatSleeping** | ignore (documented) — already enabled, idempotent | transition → HeartbeatAwaitingPong — ping sent keepalive.go:737 | ignore (accidental) → Q-01 — no ping pending | ignore (accidental) → Q-01 — no ping pending | transition → HeartbeatStopped — keepalive_task.cancel() connection_lost.go:936 | ignore (accidental) → Q-01 |
| **HeartbeatAwaitingPong** | ignore (documented) — already enabled | ignore (accidental) → Q-01 — ping already sent | transition → HeartbeatSleeping — latency recorded keepalive.go:742-747 | transition → HeartbeatExpired — TimeoutError keepalive.go:746-755 | transition → HeartbeatStopped — task cancelled | handle — pong_waiter gets ConnectionClosed abort_pings.go:704-714 |
| **HeartbeatExpired** | ignore (documented) — connection considered unusable | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 — after timeout, pong irrelevant | ignore (documented) — already expired | transition → HeartbeatStopped — cancelled by connection_lost | N/A — no pings pending after expiry |
| **HeartbeatStopped** | ignore (documented) — keepalive terminated, terminal heartbeat state | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal, idempotent | ignore (documented) — terminal |

## Table B — Protocol + Transport Events

| state | EV-07 ProtocolFailureRequested | EV-08 CloseFrameOrEOFQueued | EV-09 OutgoingDataFlushed | EV-12 TransportCloseRequested | EV-13 TransportLost | EV-17 ConnectionClosedObserved |
|---|---|---|---|---|---|---|
| **ProtocolOpen** | transition → ProtocolClosing — protocol.fail() keepalive.go:752-754 | handle — close frame queued, send_context flushes | transition → ClosurePending — close_deadline set send_context.go:819-824 | ignore (accidental) → Q-01 | transition → TransportLost — ResetWithoutClosingHandshake mod.rs:622 | ignore (accidental) → Q-01 |
| **ProtocolClosing** | ignore (documented) — already closing | handle — close frame already queued | handle — flushing close frame | transition → TransportHalfClosing — close_transport() send_context.go:872 | transition → ProtocolClosed — protocol.receive_eof() connection_lost.go:931 | transition → ClosureObservable — connection_lost_waiter resolved |
| **ProtocolClosed** | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal |
| **TransportOpen** | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | transition → TransportHalfClosing | transition → TransportLost — connection_lost() callback | ignore (accidental) → Q-01 |
| **TransportHalfClosing** | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (documented) — already requested | transition → TransportLost — event loop delivers callback | ignore (accidental) → Q-01 |
| **TransportLost** | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal |

## Table C — Caller-Facing Licecycle Events

| state | EV-11 CloseDeadlineExpired | EV-14 PeerCloseReceived | EV-15 ReceiveRequested | EV-16 ReceiveWaiterReleased | EV-20 UserCloseRequested | EV-21 SendOrDrainFailed |
|---|---|---|---|---|---|---|
| **Usable** | ignore (accidental) → Q-01 — close_deadline not set yet | transition → ProtocolClosing — protocol.receive_eof triggered | handle — blocks on recv_messages.get() mod.rs:275 | ignore (accidental) → Q-01 — no pending receive | transition → ProtocolClosing — close() mod.rs:542-570 | transition → ClosurePending — send_context drain fails |
| **FailureDetected** | ignore (accidental) → Q-01 — enters ClosurePending first | transition → ProtocolClosing | handle — recv still possible while can_read | ignore (accidental) → Q-01 | transition → ProtocolClosing | transition → ClosurePending |
| **ClosurePending** | **UNSPECIFIED → Q-C1** — THE BUG. close_transport() is called but then awaits connection_lost_waiter again. Caller remains blocked. send_context.go:863-874 | transition → ProtocolClosing | ignore (accidental) → Q-01 — closing | UNSPECIFIED → Q-C1 — only released when connection_lost_waiter resolves | ignore (documented) — already closing | ignore (accidental) → Q-01 |
| **ClosureObservable** | ignore (documented) — already resolved | ignore (documented) — terminal | transition → HeartbeatStopped — recv raises ConnectionClosed mod.rs:279 | transition → ClosureObservable (idempotent) | ignore (documented) — terminal | ignore (documented) — terminal |

## Guard Groups

All `not-formalizable: dynamic-state`. Protocol state, transport state, heartbeat
state, and caller-visible state are four orthogonal regions with no formalizable
guards.

## Sidecar Completeness

```json
"completeness": {
  "pairs": {"count": 0, "reason": "single-threaded asyncio event loop, no concurrent event sources"},
  "guardGroups": {"count": 0, "reason": "all guards dynamic-state across four orthogonal lifecycle regions"},
  "coverage": {"count": 4, "reason": "four external sources: heartbeat timer, transport callbacks, caller API, peer frames"}
}
```

<!-- terminal: HeartbeatStopped, ProtocolClosed, TransportLost -->
