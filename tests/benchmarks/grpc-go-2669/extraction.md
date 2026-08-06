# Extraction — grpc-go v1.18.0 `addrConn` sub-connection lifecycle

Component: `addrConn` in `clientconn.go` (grpc-go, tag v1.18.0, SHA
a02b0774206b209466313a0b525d2c738fe407eb). All citations are
path-relative to the clone root.

## Step 0 — Scope statement

**Machine boundary.** One `addrConn` instance: the lifecycle of a
sub-connection to one resolved address list, from creation (`newAddrConn`,
clientconn.go:592-622) to teardown (`tearDown`, clientconn.go:1326-1364).
Modelled symbols: the `addrConn` struct (clientconn.go:902-932) and its
methods `connect`, `updateConnectivityState`, `resetTransport`,
`createTransport`, `startHealthCheck`, `resetConnectBackoff`,
`getReadyTransport`, `tearDown`, `adjustParams`, `tryUpdateAddrs`, plus
the fields they touch (`state`, `transport`, `curAddr`, `addrs`,
`backoffIdx`, `resetBackoff`, `tearDownErr`, `healthCheckEnabled`,
`ctx`/`cancel`).

**Actors.**
* the balancer (via `acBalancerWrapper`: `Connect`, `UpdateAddresses`,
  balancer_conn_wrappers.go:278-325) and the ClientConn
  (`removeAddrConn`, `Close`, `ResetConnectBackoff`)
* the transport seam (`transport.NewClientTransport` and its callbacks
  `onPrefaceReceipt`, `onGoAway`, `onClose`, clientconn.go:1163-1187)
* the health-check service (via `internal.HealthCheckFunc` /
  `reportHealth`, clientconn.go:1253-1289)
* timers: the per-attempt connect deadline (clientconn.go:996,1161) and
  the backoff timer (clientconn.go:1129)

**Excluded (callee contracts only, not modelled):** ClientConn channel
state (`connectivityStateManager`), balancer implementations, resolver,
`http2Client` internals, `retryThrottler`, channelz. Calls into them are
treated as contracts and cited (seam sweep below).

**Model links.**
* Channel-level state aggregation (`csMgr`, DOC-8/DOC-9 API surface)
  is owned by a ClientConn model, not this one. Cells about
  channel-level IDLE (DOC-4) that this matrix cannot express cite that
  missing neighbour model (→ Q-06).
* The reconnect behaviour of a *replacement* addrConn created by
  `acBalancerWrapper.UpdateAddresses` (balancer_conn_wrappers.go:285-313)
  belongs to the new instance; this matrix models the old instance's
  teardown only.

## Step 1 — Extraction

### States (explicit enum + implicit flags)

The explicit state variable is `ac.state connectivity.State`
(clientconn.go:922, enum connectivity/connectivity.go:52-63: Idle,
Connecting, Ready, TransientFailure, Shutdown). Implicit sub-state
dimensions that change event dispositions:

| # | State (PA-17 name) | Defining condition | Provenance |
|---|---|---|---|
| S1 | Idle | `state==Idle`, no `resetTransport` goroutine, `transport==nil`. Initial state (zero value of `connectivity.State`, connectivity/connectivity.go:54) | observed-in-code clientconn.go:592-601 ("ac := &addrConn{"), 922 |
| S2 | Connecting_Dialing | `state==Connecting`, `transport==nil`; `resetTransport` inside the address loop (dial and/or preface wait in flight) | observed-in-code clientconn.go:978-1025 ("addrLoop:") |
| S3 | Connecting_HealthChecking | `state==Connecting`, `transport!=nil`; health check managing state, no verdict yet | observed-in-code clientconn.go:1038-1048 ("healthcheckManagingState") |
| S4 | Ready | `state==Ready`, `transport!=nil`; loop parked on `<-reconnect.Done()` | observed-in-code clientconn.go:1051 ("updateConnectivityState(connectivity.Ready)"), 1070 |
| S5 | TransientFailure_Backoff | `state==TransientFailure`, `transport==nil`; sleeping in the backoff select | observed-in-code clientconn.go:1125-1143 ("updateConnectivityState(connectivity.TransientFailure)") |
| S6 | TransientFailure_ServerUnhealthy | `state==TransientFailure`, `transport!=nil`; health check reported not-serving, loop still parked on `<-reconnect.Done()` | observed-in-code clientconn.go:1271-1273 ("updateConnectivityState(connectivity.TransientFailure)") |
| S7 | Shutdown | `state==Shutdown`; ctx cancelled, `transport==nil` (invariant intent; see Q-01) | observed-in-code clientconn.go:1326-1339 |

A transient TransientFailure blip exists inside the address loop in
Hybrid handshake mode (clientconn.go:1097): TF is set and the loop
immediately continues to the next address (auto-transition back to
Connecting). Modelled as a self-loop annotation of S2, recorded as a
contradiction with the On-mode behaviour (Q-14).

Reachable combinations: the two implicit dimensions (`transport` nil-ness,
loop phase) are functions of the enum + health gate as listed; other
combinations (`Ready ∧ transport==nil`) are unreachable in the
single-goroutine loop (proven reasoning in invariants SYS-2), *except*
via the teardown race (Q-01) which produces `Shutdown ∧ transport!=nil`
and then `Ready` on a dead instance.

### External events

Catalogued fully in event-catalogue.md (E01…E17, UV01…UV09). Producers
and consumers cited there.

### Internal events

* `addrs.exhausted` (E15) — the address loop falls through
  (clientconn.go:1118-1125).
* `backoff.timer.fired` (E11) — clientconn.go:1129-1137.
* dial results (E06/E16/E07) — return values of `createTransport`
  consumed synchronously at clientconn.go:1025-1064.

### Transitions, guards, actions

| From | Event | Guard | To | Actions | Provenance |
|---|---|---|---|---|---|
| Idle | connect | `state==Idle` (clientconn.go:676) | Connecting_Dialing | spawn `resetTransport` goroutine | clientconn.go:670-686 |
| Idle | getReadyTransport | `state==Idle` (clientconn.go:1310) | Connecting_Dialing | calls `connect()` | clientconn.go:1302-1319 |
| Connecting_Dialing | dial ok, health gate false | 4-way gate clientconn.go:1039 | Ready | set `curAddr`,`transport`; notify balancer | clientconn.go:1026-1052 |
| Connecting_Dialing | dial ok, health gate true | clientconn.go:1039-1047 | Connecting_HealthChecking | spawn `startHealthCheck` | clientconn.go:1045 |
| Connecting_Dialing | dial err | more addrs left | (stay) | next address; `transport=nil`, re-set Connecting per address | clientconn.go:1054-1063, 986-987 |
| Connecting_Dialing | addrs exhausted | not Shutdown (clientconn.go:1121) | TransientFailure_Backoff | start backoff timer `backoffFor` | clientconn.go:1118-1131 |
| Connecting_HealthChecking | health serving | `transport==newTr` (clientconn.go:1262) | Ready | first report sets `curAddr` | clientconn.go:1259-1270 |
| Connecting_HealthChecking | health not-serving | `transport==newTr` | TransientFailure_ServerUnhealthy | — | clientconn.go:1271-1273 |
| Ready / Connecting_HealthChecking / TransientFailure_ServerUnhealthy | transport closed / goaway | via `reconnect.Fire()` | TransientFailure_Backoff | `backoffIdx=0` (On/Off; Hybrid only if preface received), `hcancel`, sleep stale `backoffFor` | clientconn.go:1066-1131 |
| TransientFailure_Backoff | backoff timer fired | — | Connecting_Dialing | `backoffIdx++`, `resolveNow` on next iteration | clientconn.go:1134-1137, 971-973 |
| TransientFailure_Backoff | resetConnectBackoff | channel identity (clientconn.go:1128,1138) | Connecting_Dialing | `backoffIdx=0`, immediate retry | clientconn.go:1291-1297, 1138-1139 |
| any except Shutdown | tearDown | `state!=Shutdown` (clientconn.go:1328) | Shutdown | `transport=nil`, cancel ctx, `tearDownErr`, `curAddr={}`; GracefulClose iff `err==errConnDrain` | clientconn.go:1326-1364 |
| Shutdown | stale dial success | **no guard** | Ready (!) | re-publishes `curAddr`/`transport`, sets Ready | observed-in-code clientconn.go:1026-1052 — see Q-01 |

### Timeouts and timers

* Per-address connect deadline: `max(getMinConnectTimeout()=20s,
  backoffFor)` (clientconn.go:991-996, 52-54, 74-76; DOC-10/DOC-11).
  Enforced by `connectCtx` deadline (clientconn.go:1181) and
  `prefaceTimer` (clientconn.go:1161, 1192-1195, 1202-1213).
* Backoff timer: `time.NewTimer(backoffFor)` (clientconn.go:1129),
  `backoffFor = ac.dopts.bs.Backoff(ac.backoffIdx)` computed once per
  outer iteration (clientconn.go:975) — **before** the address loop;
  the post-loop sleep can therefore use a value computed from a
  `backoffIdx` that has since been reset (Q-03).
* No timer exists for the health verdict (Connecting_HealthChecking) or
  for TransientFailure_ServerUnhealthy (Q-08).

### Retry behaviour and limits

Unbounded retry: the outer `for i := 0; ; i++` loop
(clientconn.go:967) never gives up; exit only on Shutdown
(clientconn.go:982, 1003, 1092, 1121) or ctx done (clientconn.go:1140).
Backoff strategy `backoff.Exponential` (internal/backoff/backoff.go:59-77):
base 1s, factor 1.6, jitter ±20%, capped at MaxDelay (default 120s,
DialContext clientconn.go:229-233). `backoffIdx` reset to 0 on
connection success at *death* time (clientconn.go:1084, 1112) — not at
SETTINGS receipt (DOC-13 tension, Q-03/Q-04). `resetConnectBackoff`
(clientconn.go:1291-1297) zeroes it and wakes the backoff sleep.

### Cancellation paths

* `ac.ctx` child of `cc.ctx` (clientconn.go:601); `tearDown` cancels it
  (clientconn.go:1337). Cancellation aborts an in-flight dial
  (`connectCtx` child, clientconn.go:1181), unblocks the backoff select
  (clientconn.go:1140-1142), and — indirectly — closes an established
  transport (seam sweep NAT-5 below).
* `hctx`/`hcancel` per attempt for the health goroutine
  (clientconn.go:1012-1013, 1055, 1071).

### Failure modes

Dial error, preface timeout (clientconn.go:1192-1195), connection closed
before preface (clientconn.go:1198-1200), transport error/close after
establishment (onClose), server GOAWAY (onGoAway; keepalive param
adjustment clientconn.go:954-964), health not-serving verdict, health
stream failure.

### Apparent invariants

See invariants-and-lints.md (SYS-1…SYS-7, NAT-1…NAT-5, NAT-SYS-1).

### Contradictions and undetermined behaviour

1. `updateConnectivityState` has **no Shutdown guard**
   (clientconn.go:935-950) — unlike the channel-level
   `connectivityStateManager.updateState` which refuses updates after
   Shutdown (clientconn.go:340-342). Combined with the unguarded
   publication window clientconn.go:1026-1052 this contradicts DOC-5
   ("Channels that enter this state never leave this state") → Q-01.
2. Lock order: `ResetConnectBackoff` holds `cc.mu` and takes `ac.mu`
   (clientconn.go:843-849 → 1292); every state update holds `ac.mu` and
   takes `cc.mu` (clientconn.go:949 → 578; also 998-1001) → inversion,
   Q-02.
3. `tryNextAddrFromStart` (clientconn.go:968, 1060, 1100) is created and
   polled but **never fired** anywhere in the tree — dead mechanism →
   Q-10.
4. `tryUpdateAddrs` on Shutdown mutates `ac.addrs` and returns `true`
   (clientconn.go:698-701), which the wrapper treats as success
   (balancer_conn_wrappers.go:285) → Q-09.
5. On-mode intermediate address failures emit no TF notification;
   Hybrid mode emits one per failed address (clientconn.go:1097) —
   inconsistent with each other and with DOC-7 → Q-14.
6. envconfig parse: `GRPC_GO_REQUIRE_HANDSHAKE=on` leaves
   `RequireHandshake` at its zero value `RequireHandshakeHybrid`
   (internal/envconfig/envconfig.go:58-68: `case "on":` has an empty
   body; the doc comment says On is the default after 1.17,
   envconfig.go:41-43) → Q-05 (upstream of this component's
   `reqHandshake` gate, clientconn.go:1067).

### Doctrine-line sweep (DOC-1..DOC-20)

From `grpc-requirements/connectivity-semantics-and-api.md` (CSA),
`grpc-requirements/connection-backoff.md` (CB), and in-tree doc
comments. Classification (adopted / rejected) closes in
invariants-and-lints.md.

| id | Source | Normative line (condensed) |
|---|---|---|
| DOC-1 | CSA l.19-24 | Five-state machine; CONNECTING may be the initial state |
| DOC-2 | CSA l.26-29 | READY = connection established through TLS/protocol handshake |
| DOC-3 | CSA l.31-39 | TRANSIENT_FAILURE will eventually switch to CONNECTING; exponential backoff governs the wait |
| DOC-4 | CSA l.41-49 | IDLE on no RPC activity for IDLE_TIMEOUT (300s); RPC pushes out of IDLE; GOAWAY with no active RPCs → IDLE |
| DOC-5 | CSA l.51-57 | SHUTDOWN: new RPCs fail immediately; pending RPCs may continue until the application cancels them; the state is never left |
| DOC-6 | CSA l.59-112 | Legal-transition table; empty cells are disallowed transitions (notably no TF→READY, no READY→CONNECTING direct) |
| DOC-7 | CSA l.145-154 | Notification on every transition; CONNECTING→TF→CONNECTING required per recoverable failure even with zero backoff |
| DOC-8 | CSA l.115-126 | GetState(try_to_connect) semantics (channel-level) |
| DOC-9 | CSA l.134-143 | WaitForStateChange semantics (channel-level) |
| DOC-10 | CB l.16-32 | Backoff algorithm: TryConnect deadline = Max(current_deadline, now+MIN_CONNECT_TIMEOUT); multiply up to MAX_BACKOFF; jitter |
| DOC-11 | CB l.34-39 | Parameters: MIN_CONNECT_TIMEOUT 20s, INITIAL 1s, MULTIPLIER 1.6, MAX 120s, JITTER 0.2 |
| DOC-12 | CB l.45-47 | Backoffs started at the same time must disperse; must not attempt substantially more often than the algorithm |
| DOC-13 | CB l.49-56 | Backoff resets to INITIAL when the SETTINGS frame is received (proof the server accepted the connection) |
| DOC-14 | connectivity/connectivity.go:52-63 | State meanings (TransientFailure "expects to recover"; Shutdown "has started shutting down") |
| DOC-15 | clientconn.go:833-841 | ResetConnectBackoff wakes subchannels in TF for an immediate reconnect and resets backoff for subsequent attempts regardless of current state |
| DOC-16 | clientconn.go:911-914 | `transport` is set when viable; reset to nil when it must no longer be used (GoAway received, closed, torn down) |
| DOC-17 | clientconn.go:667-669 | `connect()` does nothing if the ac is not IDLE |
| DOC-18 | clientconn.go:688-693 | `tryUpdateAddrs` keeps the connection iff the current address is in the new list (Ready case) |
| DOC-19 | internal/backoff/backoff.go:31-37,56-58 | `Backoff(retries)` = wait before the next retry given consecutive-failure count |
| DOC-20 | internal/envconfig/envconfig.go:37-46 | RequireHandshake modes; On is the default after the 1.17 release |

### Seam-contract sweep (NAT candidates)

| Seam | Contract read | Failure semantics | Citation |
|---|---|---|---|
| `transport.NewClientTransport` | returns (transport, error); registers `onPrefaceReceipt`, `onGoAway`, `onClose` closures | dial/preface errors returned; `FailOnNonTempDialError` distinguishes temp errors | internal/transport/transport.go:534-538, internal/transport/http2_client.go:148-161 |
| `ClientTransport.Close` | "should be called only once"; invokes `onClose` exactly once (guarded by `t.state == closing`) | never raises; idempotent via state guard | internal/transport/transport.go:577-580, internal/transport/http2_client.go:759-787 |
| `ClientTransport.GracefulClose` | drains; closes immediately when no active streams; no-op when already draining/closing | never raises | internal/transport/transport.go:582-584, internal/transport/http2_client.go:790-810 |
| ctx-cancellation → transport close | cancelling the transport's lifetime ctx makes `controlBuf.get` return, loopy exits, `t.conn.Close()` runs, reader errors, `t.Close()` fires `onClose` | eventual, not immediate — NAT-5 | internal/transport/http2_client.go:326-338, internal/transport/controlbuf.go:299-321 |
| `grpcsync.Event` | `Fire` idempotent and thread-safe; `HasFired`/`Done` | never raises | internal/grpcsync/event.go:34-60 |
| `internal.HealthCheckFunc` (health/client.go) | calls `reportHealth` from its own goroutine; internal retry with backoff on stream failure; returns on ctx done, on Unimplemented (after reporting healthy), or on type-assertion failure (after reporting healthy) | reports false once after ctx cancellation is possible (RecvMsg error path) | internal/internal.go:38-39, health/client.go:54-107 |
| `backoff.Strategy.Backoff(retries)` | pure function, jittered, capped; never raises | — | internal/backoff/backoff.go:31-37, 59-77 |
| balancer wrapper upstream guards | `NewSubConn`/`UpdateAddresses` reject empty address lists before reaching addrConn | — | balancer_conn_wrappers.go:213-216, 280-283 |
| `cc.handleSubConnStateChange` | acquires `cc.mu`; forwards to balancer wrapper | no-op after cc close (`cc.conns==nil`) | clientconn.go:577-587 |

Call-site note (per method rule): `tearDown` with `err != errConnDrain`
never calls `curTr.Close()` (clientconn.go:1332-1349). That the
transport still closes is **not** visible at the call site; it follows
from the ctx-cancellation contract (NAT-5). The inference is recorded,
with its fragility, as Q-11.
