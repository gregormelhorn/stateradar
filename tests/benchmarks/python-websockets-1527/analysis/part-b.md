# Part B — Blind Requirements-Only Analysis

**Component:** Connection keepalive lifecycle (python-websockets v13.1)
**Inputs:** Sections 3 (Requirements R-01–R-12), 4 (Event catalogue EV-01–EV-21), 5 (State dimensions)
**No code, no tests, no implementation details consulted**
**Timestamp:** 2026-08-06T13:46:59Z

---

## Part B — State Model (from requirements only)

### States derived from requirements

From R-01/R-02/R-03/R-04 (heartbeat requirements):
- **Heartbeat_Disabled** — `ping_interval is None`, no keepalive
- **Heartbeat_Idle** — Between pings, sleeping for `ping_interval`
- **Heartbeat_WaitingForPong** — Ping sent, awaiting matching pong within `ping_timeout`
- **Heartbeat_Expired** — `ping_timeout` elapsed without matching pong (R-04: "connection considered unusable")
- **Heartbeat_Stopped** — Keepalive mechanism terminated

From R-05/R-06 (receive-side closure):
- **Connection_Usable** — `recv()` can receive messages
- **Connection_Closing** — Close initiated, messages may still be in transit
- **Connection_Closed** — `recv()` raises `ConnectionClosed`, async iteration exits

Terminal sub-states per R-05:
- **Closed_Normally** — Normal closure
- **Closed_Abnormally** — Protocol error or network failure

From R-07/R-08 (bounded closing):
- **Close_Initiated** — Close handshake started
- **Close_WaitingForPeer** — Waiting for peer's close frame or transport termination
- **Close_DeadlineSet** — `close_timeout` timer started
- **Close_Completed** — `wait_closed()` completes

From R-09 (transport loss):
- **Transport_Active** — TCP connection operational
- **Transport_Lost** — Event loop reports connection lost

### Orthogonal regions

| Region | States |
|---|---|
| Heartbeat | Disabled, Idle, WaitingForPong, Expired, Stopped |
| Connection | Usable, Closing, Closed |
| Close | Initiated, WaitingForPeer, DeadlineSet, Completed |
| Transport | Active, Lost |

---

## Part B — Critical Transition Analysis (from requirements only)

### The heartbeat-timeout-to-closure chain per requirements

R-04 says: "When no Pong arrives before `ping_timeout`, connection is considered unusable and initiates abnormal closure."

This implies a direct chain:
1. `Heartbeat_Expired` → connection becomes unusable
2. Abnormal close initiated (close code 1011, reason "keepalive ping timeout")
3. R-11 says: "caller-facing operations must eventually observe the abnormal closure within the configured shutdown bound"

This means: Heartbeat_Expired → some set of transitions → `recv()` raises ConnectionClosed within `close_timeout`.

R-12 says: "caller-visible closure must preserve the abnormal-close classification and causal information."

R-07 says: "`close_timeout` bounds the time spent completing the closing handshake and terminating the underlying transport. The absence or non-cooperation of the peer must not make a close operation wait without a bound."

**Key implication:** If `Heartbeat_Expired` sets the connection to "unusable" and initiates abnormal close, then the close_timeout must bound the time from Expired to caller-visible closure — REGARDLESS of whether the peer responds or the transport reports loss.

---

## Part B — Disposition Matrix (critical cells)

| State | Event | Expected (from requirements) | Classification |
|---|---|---|---|
| Heartbeat_WaitingForPong | EV-06 PingTimeoutElapsed | transition → Heartbeat_Expired (R-04) | Explicit |
| Heartbeat_Expired | EV-07 ProtocolFailureRequested | transition → Connection_Closing with abnormal cause (R-04, R-12) | Explicit |
| Connection_Closing | EV-16 ReceiveWaiterReleased | transition → Connection_Closed (R-05) | Explicit — but WHEN? |
| Close_WaitingForPeer | EV-11 CloseDeadlineExpired | UNSPECIFIED — R-07 says "must not wait without bound" but doesn't specify what happens when deadline expires | **Hole** |
| Close_DeadlineSet | EV-13 TransportLost | transition → Close_Completed (R-09) | Explicit |
| Close_DeadlineSet | EV-11 CloseDeadlineExpired | UNSPECIFIED — NO requirement says what happens. R-07 says "bounds the time" but doesn't define the bounding action | **Hole** |
| Transport_Lost | EV-16 ReceiveWaiterReleased | transition → Connection_Closed (R-09: "pending receives are unblocked") | Explicit |

**Two holes identified from requirements alone:**
1. `(Close_WaitingForPeer, EV-11 CloseDeadlineExpired)` — no disposition
2. `(Close_DeadlineSet, EV-11 CloseDeadlineExpired)` — no disposition

The requirements say the close_timeout "bounds" the closing time, but don't specify the mechanism. The bounding action could be: force transport close, unblock callers, set an error cause, or some combination. Without specifying this, the requirement is underspecified — but the HOLE itself is a finding: the requirements don't close the loop.

---

## Part B — Invariants

| ID | Verdict | Reasoning from requirements |
|---|---|---|
| INV-01 | Supported | R-04: "connection is considered unusable" — no return path defined |
| INV-02 | **Unproven** | R-07 says close_timeout bounds closing but doesn't specify bounding mechanism. Cannot prove without implementation. |
| INV-03 | **Required by R-09** | R-09: "pending receives are unblocked" — but only when TransportLost. CloseDeadlineExpired path not covered. |
| INV-04 | **Required by R-07/R-11** | "must not wait without a bound" — but what ensures progress after deadline? Requirements don't say. |
| INV-05 | **Required by R-05/R-11** | "must eventually observe abnormal closure within configured shutdown bound" — must be guaranteed. |
| INV-06 | Supported | R-09: "pending Ping waiters are terminated" when TransportLost. |
| INV-07 | Required by R-12 | "must preserve abnormal-close classification" |
| INV-08 | **Required** | Four lifecycles (heartbeat, protocol, transport, caller) — requirements don't specify synchronization points |

---

## Part B — Required Questions

1. **What makes connection unusable?** `PingTimeoutElapsed` per R-04.
2. **What changes protocol state?** ProtocolFailureRequested after heartbeat expiry.
3. **What closes transport?** Either TransportLost (R-09) or some CloseDeadlineExpired mechanism (R-07 — underspecified).
4. **What unblocks recv()?** Either TransportLost (R-09) or CloseDeadlineExpired (R-07 implies this).
5. **What completes wait_closed()?** TransportLost (R-08, R-09) or CloseDeadlineExpired mechanism.
6. **What happens when close deadline expires?** **UNSPECIFIED.** R-07 says it "bounds" but doesn't say how. This is the primary requirement gap.
7. **Can caller-visible failure remain pending after close deadline?** Requirements say no (R-07, R-11) but don't specify the mechanism that prevents it.
8. **Does any transition depend on peer/network?** TransportLost depends on event loop (R-09). The CloseDeadlineExpired mechanism should NOT depend on peer/network (R-07).
9. **State where protocol closing while callers blocked?** Should not exist per R-05/R-11. If it does, it's a defect.
10. **Are lifecycle points distinct?** Requirements distinguish "close initiated", "transport lost" (R-09), "closure observed" (R-05). "Transport closing" is not a requirement-level concept.
11. **Guarantee from heartbeat timeout to closure?** Required by R-11 ("eventually observe within configured shutdown bound") but mechanism unspecified.
12. **Tests?** N/A — blind analysis can't inspect tests.

---

## Part B — Summary

| Metric | Count |
|---|---|
| States | 12 (across 4 regions) |
| Requirement holes | 2 (CloseDeadlineExpired disposition) |
| Underspecified requirements | R-07 (bounding mechanism), R-11 ("eventually") |
| Required transitions not specified | CloseDeadlineExpired → force close + caller notification |
