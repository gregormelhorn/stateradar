# Invariants and lint findings — grpc-go v1.18.0 `addrConn`

## NAT invariants (environment assumptions; analysis may assume, tests may not)

* **NAT-1** `backoffIdx >= 0`; `Backoff(retries) ∈ [0, MaxDelay·1.2]`
  (jitter ±0.2, internal/backoff/backoff.go:44-77). Observed-in-code.
* **NAT-2** Per transport instance, `onClose` fires at most once
  (`t.state == closing` guard, internal/transport/http2_client.go:761-766)
  and callback closures are bound to their transport generation
  (clientconn.go:1163-1179).
* **NAT-3** `healthCheckFunc` invokes `reportHealth` serially from one
  goroutine and returns after ctx cancellation (health/client.go:59-66);
  at most one trailing `reportHealth(false)` after cancellation
  (health/client.go:96-100).
* **NAT-4** Balancer/wrapper never delivers an empty address list
  (balancer_conn_wrappers.go:214-216, 280-283).
* **NAT-5** Cancelling `ac.ctx` eventually closes an established
  transport and fires `onClose` (controlbuf get returns on ctxDone →
  loopy exits → conn.Close → reader error → t.Close,
  internal/transport/http2_client.go:326-338,
  internal/transport/controlbuf.go:299-321). *Eventual*, not bounded.
* **NAT-SYS-1** N clients (or N subchannels) sharing one backend observe
  its failure and recovery near-simultaneously; per-process
  `grpcrand` jitter (internal/grpcrand/grpcrand.go:30, seeded once) is
  the only decorrelation between their backoff schedules (DOC-12).

## SYS invariants (obligations), checked state by state against the as-is model

| id | predicate | verdict |
|---|---|---|
| SYS-1 | `state==Shutdown` is terminal: no later write to `state` | **VIOLATED** — `updateConnectivityState` has no Shutdown guard (clientconn.go:936-942, contrast csMgr clientconn.go:340-342); reachable via cell (Shutdown, UV08): clientconn.go:1026-1052 publishes and sets Ready after tearDown. z3 witness in G-05. → Q-01 |
| SYS-2 | `state==Ready ⇒ transport != nil` | holds — Ready is set only after `transport=newTr` (clientconn.go:1029→1051; reportHealth path guarded by identity clientconn.go:1262); tearDown clears both under one lock (clientconn.go:1332-1336) |
| SYS-3 | `state==Shutdown ⇒ transport==nil ∧ ctx cancelled` | **VIOLATED** — same race: clientconn.go:1027-1030 re-publishes `transport` on a Shutdown ac. → Q-01 |
| SYS-4 | at most one `resetTransport` goroutine per ac | holds — spawned only on the Idle→Connecting edge (clientconn.go:676-684) and Idle is never re-entered (no transition targets Idle in the matrix) |
| SYS-5 | every `ac.state` change notifies the balancer | holds by construction (clientconn.go:942-949); but per-address failures produce no TF notification in On mode (DOC-7 tension → Q-14) |
| SYS-6 | `backoffIdx==0` only after a server-accepted connection (DOC-13) or an explicit reset | **VIOLATED in Off mode** — clientconn.go:1104-1114 resets on transport death without any preface (Q-04); the reset-at-death timing also leaves `backoffFor` stale (Q-03) |
| SYS-7 | one global lock order over {ac.mu, cc.mu} | **VIOLATED** — cc.mu→ac.mu (clientconn.go:843-849→1292) vs ac.mu→cc.mu (clientconn.go:949→578; 998-1001). → Q-02 |

## Doctrine mapping

<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 DOC-5 DOC-6 DOC-7 DOC-8 DOC-9 DOC-10 DOC-11 DOC-12 DOC-13 DOC-14 DOC-15 DOC-16 DOC-17 DOC-18 DOC-19 DOC-20 -->

Machine-readable closure of the DOC sweep (PA-22, retrofit). Rows
restate the prose table in the next section 1:1 — the notes column
carries the tie-back; no mapping was added or changed. DOC-1/DOC-14
use the `structural` kind (realized by the model's structure, reason
names the enforcing check); DOC-20 uses `guard` (discharged by a
guard-group proof) — the vocabulary was widened for exactly these
three after the retrofit exposed the gap (2026-08-07).

| id | mapping | target | notes (prose-table tie-back) |
|---|---|---|---|
| DOC-1 | structural | states declaration = the five connectivity API states plus condition sub-states; enforced by matrix↔mermaid sync and reachability | prose: adopted (state space) |
| DOC-14 | structural | state names carry the API enum spellings; enforced by the PA-17 naming check | prose: adopted (naming) |
| DOC-20 | guard | G-11 | prose: adopted then found contradicted — env parse "on" yields Hybrid (Q-05) |
| DOC-2 | cell | Connecting_Dialing x E06 | On mode waits for preface clientconn.go:1190-1201 — conforms in On; Off reaches Ready without handshake → part of Q-04 |
| DOC-2 | cell | Connecting_Dialing x E16 | same constraint, health-managed dial result (prose: E06/E16) |
| DOC-3 | cell | TransientFailure_Backoff x E11 | invariant "TF eventually → Connecting" — conforms for TF_Backoff |
| DOC-3 | cell | TransientFailure_ServerUnhealthy x UV09 | hole from the same prose row: no path out on a silent health stream → Q-08 |
| DOC-4 | cell | Ready x E08 | requirement (GOAWAY → Idle) unimplemented at this boundary: GOAWAY → TF/reconnect, not Idle; ac never re-enters Idle → Q-06 (F-19) |
| DOC-5 | invariant | SYS-1 | Shutdown terminal — **violated** → Q-01 |
| DOC-5 | cell | Shutdown x UV08 | the violating cell (z3 witness in G-05) |
| DOC-6 | cell | Shutdown x UV08 | legal-transition table constrains every transition cell; this row is violation 1: Shutdown→Ready → Q-01 |
| DOC-6 | cell | TransientFailure_ServerUnhealthy x E12 | violation 2: TransientFailure→Ready — cited text contemplates health checking: no → Q-07 |
| DOC-7 | cell | Connecting_Dialing x E07 | On skips the CONNECTING→TF→CONNECTING blip per failed address (V-05); Hybrid emits it (clientconn.go:1097) → Q-14 |
| DOC-8 | rejected | non-binding here: channel-level API (model link: ClientConn model) | out of scope, noted |
| DOC-9 | rejected | non-binding here: channel-level API (model link: ClientConn model) | out of scope, noted |
| DOC-10 | cell | Connecting_Dialing x UV04 | guard G-04 — conforms (proven) |
| DOC-11 | constraint | NAT-1 | backoff constants backoff.go:41-48, clientconn.go:52-54 — conforms |
| DOC-12 | constraint | NAT-SYS-1 | dispersal obligation; multi-instance traces M-01..M-03; ResetConnectBackoff is a synchronized reset point → Q-13 |
| DOC-13 | invariant | SYS-6 | reset sites clientconn.go:1084/1112 — **violated in Off mode** (Q-04); reset-at-death timing → stale backoffFor (Q-03) |
| DOC-15 | cell | TransientFailure_Backoff x E05 | conforms |
| DOC-15 | cell | TransientFailure_ServerUnhealthy x E05 | does NOT reconnect — partial violation → Q-15 |
| DOC-15 | cell | Connecting_Dialing x E05 | keeps stale sleep → Q-03 |
| DOC-16 | invariant | SYS-2 | transport field writes — holds |
| DOC-16 | invariant | SYS-3 | **violated** (Q-01) |
| DOC-17 | cell | Connecting_Dialing x E01 | connect() no-op on non-Idle (prose: cited on all (non-Idle, E01) cells) — conforms |
| DOC-17 | cell | Connecting_HealthChecking x E01 | conforms |
| DOC-17 | cell | Ready x E01 | conforms |
| DOC-17 | cell | TransientFailure_Backoff x E01 | conforms |
| DOC-17 | cell | TransientFailure_ServerUnhealthy x E01 | conforms |
| DOC-17 | cell | Shutdown x E01 | conforms (Shutdown → error) |
| DOC-18 | cell | Ready x E03 | conforms; Shutdown branch undocumented → Q-09 |
| DOC-19 | constraint | NAT-1 | Backoff(retries) semantics — conforms |

## Doctrine sweep prose detail (Step-5 closure of the DOC sweep; PA-22 cell check)

| DOC | classification | mapping / cell | verdict |
|---|---|---|---|
| DOC-1 | adopted: state space | matrix states (5 API states + condition sub-states) | conforms (Idle is initial, not Connecting — CSA allows either) |
| DOC-2 | adopted: disposition constraint | (Connecting_Dialing, E06/E16); On mode waits for preface clientconn.go:1190-1201 | conforms in On; Off mode reaches Ready without handshake completion → part of Q-04 |
| DOC-3 | adopted: invariant "TF eventually → Connecting" | (TransientFailure_Backoff, E11) | conforms for TF_Backoff; **no path** from TF_ServerUnhealthy on a silent stream — cell (TransientFailure_ServerUnhealthy, UV09) is a hole → Q-08 |
| DOC-4 | adopted then found **unimplemented** | no cell: ac never re-enters Idle; GOAWAY → TF/reconnect, not Idle (cells (Ready, E08)) | unimplemented at this boundary (channel-level model link) → Q-06 (F-19) |
| DOC-5 | adopted: SYS-1 | cell (Shutdown, UV08) | **violated** → Q-01 |
| DOC-6 | adopted: disposition constraint (legal-transition table) | all transition cells | violated twice: Shutdown→Ready (Q-01) and TransientFailure→Ready via (TransientFailure_ServerUnhealthy, E12) — cited text contemplates health checking: no → Q-07 |
| DOC-7 | adopted: disposition constraint | (Connecting_Dialing, E07) | On mode skips the CONNECTING→TF→CONNECTING blip per failed address (V-05); Hybrid emits it (clientconn.go:1097) → Q-14 |
| DOC-8 | rejected as non-binding here: channel-level API (model link: ClientConn model) | — | out of scope, noted |
| DOC-9 | rejected as non-binding here: channel-level API | — | out of scope, noted |
| DOC-10 | adopted: guard G-04 | (Connecting_Dialing, UV04) | conforms (proven) |
| DOC-11 | adopted: NAT-1 constants | backoff.go:41-48, clientconn.go:52-54 | conforms |
| DOC-12 | adopted: NAT-SYS-1 | multi-instance traces M-01..M-03 | jitter present; ResetConnectBackoff is a synchronized reset point → Q-13 |
| DOC-13 | adopted: SYS-6 | reset sites clientconn.go:1084/1112 | **violated in Off mode** (Q-04); reset-at-death timing → stale backoffFor (Q-03) |
| DOC-14 | adopted: naming | state names | conforms |
| DOC-15 | adopted: disposition constraint | (TransientFailure_Backoff, E05) conforms; (TransientFailure_ServerUnhealthy, E05) does NOT reconnect; (Connecting_Dialing, E05) keeps stale sleep | partial violation → Q-15, Q-03 |
| DOC-16 | adopted: SYS-2/SYS-3 | transport field writes | SYS-3 violated (Q-01) |
| DOC-17 | adopted: cited on (non-Idle, E01) cells | — | conforms |
| DOC-18 | adopted: cited on (Ready, E03) | — | conforms; Shutdown branch undocumented → Q-09 |
| DOC-19 | adopted: NAT-1 | — | conforms |
| DOC-20 | adopted then found **contradicted** | env parse G-11 | "on" yields Hybrid → Q-05 |

## Lint checklist (rules.toml step-5 list)

| lint | finding |
|---|---|
| waiting/connecting/stopping states without timeout | **Connecting_HealthChecking and TransientFailure_ServerUnhealthy have no timeout** — a silent health stream strands them (cells (…, UV09)) → Q-08 (F-13). Per-address dial IS bounded (G-04). Backoff sleep IS bounded (NAT-1) |
| retries without a maximum | retry is unbounded by design (clientconn.go:967); documented reconnection strategy (DOC-3) — accepted, no finding; noted for consumers |
| invoked external operations without explicit failure outcome | `curTr.GracefulClose()` return value discarded (clientconn.go:1347) — contract says no meaningful error (http2_client.go:795-810), accepted with citation. `ac.cc.dopts.healthCheckFunc` error only logged (clientconn.go:1276-1288) → folded into Q-08 |
| externally initiated operations without cancellation handling | in-flight dial IS cancellable (ctx, clientconn.go:1181); health goroutine IS cancellable (hcancel); no finding |
| terminal/error states without documented meaning | Shutdown carries `tearDownErr` (clientconn.go:1338) — conforms; TransientFailure exposes no error to the ac API surface (connection error goes to the picker, clientconn.go:1219) — model link (ClientConn), no local finding |
| undefined startup/shutdown behaviour | startup defined (newAddrConn → Idle); shutdown defined (tearDown); **but** transport closure on non-drain teardown is indirect via NAT-5 → Q-11 (F-07) |
| unbounded queues/buffers, unhandled overload | **`defer hcancel()` inside the retry loop body (clientconn.go:1013) accumulates one deferred call per address attempt for the life of the goroutine** — unbounded growth over an unbounded retry lifetime → Q-12 (F-07 residue of ended attempts) |
| synchronized reset points | `cc.ResetConnectBackoff` resets ALL subchannels at once (clientconn.go:846-848) and DOC-15 promises immediate reconnect — a fleet-wide operator action stampedes the backend (NAT-SYS-1); also `backoffIdx=0` on every accepted connection (clientconn.go:1112) synchronizes across subchannels of one backend after it flaps → Q-13 (F-10), traces M-01..M-03 |
| lifecycle disagreement (PA-21) | ac lifecycle vs `resetTransport` goroutine: teardown (terminal in the API track) does synchronize the loop via state+ctx **except** in the UV08 window → Q-01. ac lifecycle vs health goroutine: synchronized via hctx + transport identity — holds |
| dual ownership cleanup (PA-23) | transport release: explicit (`GracefulClose` on drain teardown, clientconn.go:1347; `newTr.Close` on handshake failure, clientconn.go:1194/1206/1236/1245) vs implicit (ctx cancellation, NAT-5). Exactly-one-close holds inside transport (`t.state==closing` guard, http2_client.go:761-766) — proven at callee, no local finding; the *no-close-at-all* path in the UV08 window relies solely on NAT-5 → noted under Q-01/Q-11 |
| async cancellation isolation (PA-24) | the in-flight dial result is a resource transferred back to a possibly-dead owner: teardown (receiver-side terminal) has no synchronization into the publication path (clientconn.go:1026-1052) → this is exactly Q-01 |
| user-model gap | (Shutdown, UV08) transition→Ready and (TransientFailure_ServerUnhealthy, E12) transition→Ready are reachable only under concurrency/health-checking — invisible in a single-threaded mental model; adversarial traces P-01a and T-06 are their user-facing documentation. Also (TransientFailure_Backoff, E05)'s channel-identity race (P-02a) |
