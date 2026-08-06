# Event catalogue — grpc-go v1.18.0 `addrConn`

<!-- event-ids: E01 E02 E03 E17 E04 E05 E06 E16 E07 E08 E09 E10 E11 E12 E13 E14 E15 UV01 UV02 UV03 UV04 UV05 UV06 UV07 UV08 UV09 -->

Abstraction note (PA-10): dial results (E06/E16/E07) and address
exhaustion (E15) are internal phase-results of the sequential
`resetTransport` loop (clientconn.go:966-1145); they can only occur in
the loop phase that produces them. Cells that mark them
`ignore (documented)` in other states cite this sequential structure.

Part-B repairs (part-b-diff, 2026-08-07) — two catalogue gaps produced
blind-pass artefacts; stated here so the class cannot recur:

* **The handshake wait is inside the dial phase.** The HTTP/2 preface
  wait is a `select` inside `createTransport` before it returns
  (clientconn.go:1190-1201, On mode; Hybrid spawns a watcher and
  returns; Off returns immediately). Dial and handshake wait are one
  sequential phase whose only outcomes are the phase-results
  E06/E16/E07 — no event is dispatched against a separate
  "handshake-wait" state, so a blind reader must not derive one from
  E10's wording; it folds into `Connecting_Dialing`.
* **State-name canonicalization (PA-17).** `_` is reserved for the
  sub-state separator, so multi-word API state names collapse to one
  PascalCase word: TRANSIENT_FAILURE → `TransientFailure` (never
  `Transient_Failure`). Canonical leaf states: Idle, Connecting_Dialing,
  Connecting_HealthChecking, Ready, TransientFailure_Backoff,
  TransientFailure_ServerUnhealthy, Shutdown.

## Base events

| id | name | source | ext/int | payload gist | produced at | consumed at | gate type |
|---|---|---|---|---|---|---|---|
| E01 | `connect` | balancer (`acbw.Connect`), RPC path (`getReadyTransport` on Idle) | external | none | balancer_conn_wrappers.go:318-322, clientconn.go:1314-1317 | clientconn.go:670-686 | service-side state: `ac.state` (Shutdown→error, non-Idle→no-op, Idle→dial) |
| E02 | `teardown` | ClientConn (`Close` clientconn.go:879-881, `removeAddrConn` clientconn.go:626-635), balancer (`RemoveSubConn` balancer_conn_wrappers.go:234-246, empty `UpdateAddresses` balancer_conn_wrappers.go:281-283) | external | `err` (errConnDrain vs other) | callers above | clientconn.go:1326-1364 | payload content: `err==errConnDrain` selects GracefulClose (clientconn.go:1340-1348); service-side state: Shutdown→no-op |
| E03 | `update.addrs.keep` | balancer (`acbw.UpdateAddresses`, new list contains `curAddr`) | external | addr list | balancer_conn_wrappers.go:278-314 | clientconn.go:694-722 | payload content (membership of `curAddr`, clientconn.go:709-717) AND service-side state (only Ready keeps; Shutdown mutates+true; else false→wrapper recreates) |
| E17 | `update.addrs.drop` | balancer (same call, list does NOT contain `curAddr`) | external | addr list | same | same | same gate — split per payload so each matrix cell has one disposition |
| E04 | `get.ready.transport` | RPC path / balancer picker | external | none | picker_wrapper.go via `acbw` | clientconn.go:1302-1319 | service-side state: Ready∧transport→return it; Idle→connect; else nil |
| E05 | `reset.backoff` | user API `cc.ResetConnectBackoff` | external | none | clientconn.go:843-849 | clientconn.go:1291-1297 | service-side state: only a sleeping backoff select observes the channel close (clientconn.go:1128,1138) |
| E06 | `dial.ok` | transport seam (createTransport returns nil error; health gate FALSE) | internal (result of external seam) | new transport | clientconn.go:1025 | clientconn.go:1026-1052 | service-side state: health gate clientconn.go:1039 (see E16) |
| E16 | `dial.ok.healthmanaged` | same, health gate TRUE | internal | new transport | clientconn.go:1025 | clientconn.go:1039-1048 | gate = static config: `!disableHealthCheck ∧ healthCheckConfig!=nil ∧ scopts.HealthCheckEnabled ∧ healthCheckFunc!=nil` (clientconn.go:1039-1043) |
| E07 | `dial.err` | transport seam (dial error, preface timeout, closed before preface) | internal | error | clientconn.go:1025, 1192-1200, 1217-1229 | clientconn.go:1054-1063 | payload content: `err==errConnClosing` ⇒ goroutine exit (clientconn.go:1056-1058) |
| E08 | `transport.goaway` | server via transport callback `onGoAway` | external | `GoAwayReason` (internal/transport/transport.go:711-724) | internal/transport/http2_client.go (GoAway frame) | clientconn.go:1163-1168, 954-964 | payload content: only `GoAwayTooManyPings` adjusts keepalive (clientconn.go:956); any reason fires `reconnect` |
| E09 | `transport.closed` | server / network via transport callback `onClose` | external | none | internal/transport/http2_client.go:759-787 | clientconn.go:1170-1174 → unblocks 1070 | none (unconditional) |
| E10 | `preface.received` | server via `onPrefaceReceipt` (HTTP/2 SETTINGS) | external | none | internal/transport/http2_client.go | clientconn.go:1176-1179; read at 1080 (Hybrid), 1196 (On) | service-side state: consumed only during handshake wait / Hybrid death-check |
| E11 | `backoff.timer.fired` | internal timer | internal | none | clientconn.go:1129 | clientconn.go:1134-1137 | none |
| E12 | `health.report.serving` | health service stream via `reportHealth(true)` | external | bool true | health/client.go:96-105 | clientconn.go:1259-1270 | service-side state: `ac.transport==newTr` guard (clientconn.go:1262); first report also sets `curAddr` (1266-1269) |
| E13 | `health.report.notserving` | health service via `reportHealth(false)` | external | bool false | health/client.go:96-100 | clientconn.go:1271-1273 | same transport-identity guard |
| E14 | `health.stream.ended` | health service (healthCheckFunc returns) | external | error (Unimplemented vs other) | health/client.go:54-107 | clientconn.go:1276-1288 | payload content: Unimplemented → health disabled log; else error log. No state write. E14 fires only when healthCheckFunc *returns* — its internal per-stream retry loop (health/client.go:57-100) is already over; no monitoring resumes after E14 (Q-08) |
| E15 | `addrs.exhausted` | internal (address loop fell through) | internal | none | clientconn.go:978-1116 | clientconn.go:1118-1131 | service-side state: Shutdown check clientconn.go:1121 |

## Undesired variants

| id | base/source | category (fault) | description | disposition summary |
|---|---|---|---|---|
| UV01 | E08/E09 | out-of-order / stale (F-15) | callback from a previous transport generation after a new attempt started | generation isolation: fresh `reconnect` event per attempt (clientconn.go:1023); old events already consumed |
| UV02 | E08 | duplication (F-14) | duplicate GoAway frames | `Event.Fire` idempotent (contract; consumed clientconn.go:1023,1070); `adjustParams` monotonic max (clientconn.go:959) |
| UV03 | E10 | loss (F-12) | server never sends preface | On: preface timer closes transport, dial fails (clientconn.go:1192-1195); Hybrid: watcher closes an already-READY transport (clientconn.go:1202-1213); Off: never checked → Q-04 |
| UV04 | E06/E07 | delay (F-13) | dial/handshake exceeds connectDeadline | `connectCtx` deadline (clientconn.go:1181, 991-996) fails the attempt |
| UV05 | E08+E09 | contradiction (F-16) | GoAway and close near-simultaneously | both fire the same idempotent event; order-independent (clientconn.go:1163-1174) |
| UV06 | E12/E13 | commission (F-17) | health report with no legitimate trigger (no managed stream) | `reportHealth` closure is invocable only by `healthCheckFunc` (clientconn.go:1275); post-cancel late report guarded by transport identity (1262) |
| UV07 | E12/E13 | value (F-18) | health report bound to a stale transport | transport-identity guard clientconn.go:1262 |
| UV08 | E06/E16 | out-of-order after shutdown (F-15) | dial succeeded; teardown completed before the result is published | **unguarded** — re-publishes transport and sets Ready on a Shutdown ac (clientconn.go:1026-1052) → Q-01 |
| UV09 | E12/E13/E14 | loss (F-12) | health stream never delivers a verdict | no timeout exists → stuck Connecting_HealthChecking / TransientFailure_ServerUnhealthy → Q-08 |

## Remembrance semantics

* **Ended transport (closed/GoAway/replaced):** the addrConn remembers
  nothing of it — `ac.transport` is nil'd at teardown
  (clientconn.go:1333) and at the start of every new attempt
  (clientconn.go:987). Late references: callbacks of a dead transport
  hold their own closures (`reconnect`, `prefaceReceived`,
  `onCloseCalled` — one set per attempt, clientconn.go:1023-1024,1153)
  and resolve against those, never against the current attempt. The
  health `reportHealth` closure resolves late calls via the
  `ac.transport != newTr` comparison (clientconn.go:1262) → no-op.
  Bound: one generation; no queue.
* **Ended addrConn (Shutdown):** remembers `tearDownErr`
  (clientconn.go:1338) and — anomalously — accepts `addrs` mutations
  forever (clientconn.go:698-701, Q-09). `curAddr` is cleared
  (clientconn.go:1339). channelz entry removed (clientconn.go:1350-1362).
  A late `connect` resolves to `errConnClosing` (clientconn.go:672-674).
* **Backoff history:** `backoffIdx` survives connection lifetimes
  (field comment clientconn.go:926) and is the only cross-connection
  memory; reset points: success-at-death (clientconn.go:1084,1112) and
  `resetConnectBackoff` (clientconn.go:1294).

## Upstream-guard annotation

| event | guarded upstream | absent here |
|---|---|---|
| E03/E17 | empty list rejected: balancer_conn_wrappers.go:214-216 (`NewSubConn`), 280-283 (`UpdateAddresses` → tearDown instead) | addrConn itself never checks `len(addrs)>0`; `resetTransport` with empty `addrs` would spin TF/backoff cycles without dialing (NAT-4 assumed) |
| E02 | cc-level: `cc.conns==nil` guards double close (clientconn.go:856-858) | ac-level idempotence via `state==Shutdown` (clientconn.go:1328-1331) |
| E12/E13 | health/client.go validates stream type, retries stream with its own backoff (health/client.go:57-79) — that retry loop runs *inside* healthCheckFunc, i.e. before E14; once E14 fires, monitoring is permanently over | no service-name validation at this boundary; no verdict timeout (UV09) |
| E06 | preface requirement per `reqHandshake` mode (clientconn.go:1190-1214); mode set from env at process start (internal/envconfig/envconfig.go:58-68 — parse defect Q-05) | Off mode publishes an unverified connection (Q-04) |
| E05 | none — public experimental API, callable anytime (clientconn.go:843-849) | no state check; lock-order hazard Q-02 |

## Lock-discipline annotation

| critical section | lock | calls out under lock | reentrancy contract |
|---|---|---|---|
| `updateConnectivityState` callers (connect:680, resetTransport:986/1051/1097/1125, reportHealth:1270-1272, tearDown:1336) | `ac.mu` | `cc.handleSubConnStateChange` → **acquires `cc.mu`** (clientconn.go:949, 577-586) and calls the balancer's `HandleSubConnStateChange` under `cc.mu` | balancer callback runs under `cc.mu`; a balancer that calls back into `cc.ResetConnectBackoff`-like APIs deadlocks. No doc warning found in balancer.go for v1.18 → recorded under Q-02 |
| `resetTransport` keepalive read (clientconn.go:998-1001) | `ac.mu` then `cc.mu.RLock` | — | establishes order ac.mu → cc.mu |
| `cc.ResetConnectBackoff` (clientconn.go:843-849) | `cc.mu` then per-ac `ac.mu` (clientconn.go:1292) | — | establishes order **cc.mu → ac.mu — inversion against the row above ⇒ deadlock candidate Q-02** |
| `onGoAway` (clientconn.go:1163-1168) | `ac.mu` then `cc.mu` inside `adjustParams` (clientconn.go:958-962) | fired from the transport reader goroutine | consistent with ac.mu → cc.mu |
| `tearDown` GracefulClose window (clientconn.go:1340-1348) | releases `ac.mu` around `curTr.GracefulClose()` because GracefulClose → Close → onClose | onClose (clientconn.go:1170-1174) takes no ac.mu — safe; the unlock window admits interleavings (P-01 family) |

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| balancer/ClientConn API (E01,E02,E03,E17,E04) | n/a: in-process method calls; absence of a call leaves the current state, every row disposes that | n/a: a delayed call is an ordinary call in a later state; every state row disposes E01-E04 | covered by base grid: (Connecting_Dialing,E01)=no-op clientconn.go:676; (Shutdown,E02)=no-op clientconn.go:1328 | covered by base grid rows (Shutdown,E01/E03/E17) + trace P-07a | P-04a/P-04b, P-07a/P-07b | n/a: every Connect/UpdateAddresses call is legitimate under the balancer contract; no request-response pairing exists to violate | n/a: empty-list payload rejected upstream (balancer_conn_wrappers.go:280-283); membership payload split into E03/E17 |
| user API (E05 reset.backoff) | n/a: optional API; no obligation depends on it arriving | P-02a/P-02b (reset lands before vs during the backoff sleep; stale `backoffFor`) | covered by base grid: each call swaps a fresh channel (clientconn.go:1293-1295), second call is another E05 | covered by base grid (Shutdown,E05) — dead-object mutation, Q-09 | P-03a/P-03b (concurrent with ac.mu→cc.mu holders — deadlock Q-02) | covered by base grid: reset without an outage only zeroes backoffIdx (clientconn.go:1294) | n/a: no payload |
| transport seam (E06,E07,E08,E09,E10) | UV03 | UV04 | UV02 | UV01, UV08 | UV05 | n/a: callbacks are closures created with the transport (clientconn.go:1163-1179); no unsolicited registration path | n/a: unknown GoAwayReason values fall through the switch unhandled by design (clientconn.go:955-963) — documented no-op |
| health service (E12,E13,E14) | UV09 | UV09 (no timeout exists, so any delay is indistinguishable from loss) | covered by base grid: repeated equal reports are no-ops (clientconn.go:936-938) | UV07 | covered by base grid: alternating reports serialize under ac.mu, last write wins (clientconn.go:1259-1274) | UV06 | UV07 |

## Cross-source interaction pairs

Both orderings traced in adversarial-traces.md.

| id | events (sources) | shared entity | question |
|---|---|---|---|
| P-01a | E02 teardown (balancer/user) THEN stale E06 dial.ok (transport seam) | the ac and its being-born transport | resurrection: Shutdown → Ready (Q-01) |
| P-01b | E06 dial.ok THEN E02 teardown | same | normal: teardown clears transport; NAT-5 closes it |
| P-02a | E05 reset.backoff (user) THEN E15 TF entry (transport failure) | `resetBackoff` channel + `backoffFor` | reset does not shorten the already-computed sleep (Q-03) |
| P-02b | E15 TF entry THEN E05 reset.backoff | same | wakes the sleep immediately (clientconn.go:1138) |
| P-03a | E05 via cc.ResetConnectBackoff (holds cc.mu) WHILE E09-driven state update (holds ac.mu) | the two mutexes | lock-order inversion deadlock (Q-02) |
| P-03b | state update first, reset after | same | serializes fine — order decides survival |
| P-04a | E03/E17 update.addrs (balancer) THEN E09 transport.closed (server) | address list + connection | recreate path; new ac starts from top (V-11) |
| P-04b | E09 THEN E03/E17 | same | update lands in Connecting → teardown+recreate mid-reconnect |
| P-05a | E08 goaway THEN E09 close (same transport) | `reconnect` event | adjustParams then reconnect — handled |
| P-05b | E09 close THEN E08 goaway | same | late goaway still adjusts keepalive params (clientconn.go:954-964); Fire idempotent |
| P-06a | E13 health not-serving THEN E09 transport closed | transport + state | TF_ServerUnhealthy → TF_Backoff |
| P-06b | E09 THEN stale E13 | same | guarded by transport identity (clientconn.go:1262) |
| P-07a | E02 teardown (user) THEN E01 connect (balancer) | ac | connect rejected errConnClosing (clientconn.go:672-674) |
| P-07b | E01 connect THEN E02 teardown | ac | dial aborts via ctx; loop exits at Shutdown checks |
