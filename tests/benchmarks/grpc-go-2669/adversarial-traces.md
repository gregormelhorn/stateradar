# Adversarial traces — grpc-go v1.18.0 `addrConn`

Format per trace: (a) sequence, (b) what the code does (provenance),
(c) question raised, or `none — control trace` (with the
requirement-scope line where a verdict cites text).

## Systematic — interaction-pair orderings

**P-01a** teardown, then stale dial success.
(a) E01 connect → dial in flight; createTransport passes its last
Shutdown check (clientconn.go:1243-1248) and returns newTr; E02 tearDown
runs to completion (state=Shutdown, transport=nil, ctx cancelled,
clientconn.go:1326-1364); the resetTransport goroutine resumes at
clientconn.go:1026.
(b) curAddr/transport re-published (1027-1030); health gate false ⇒
`updateConnectivityState(connectivity.Ready)` (1051) — no Shutdown
guard (936-942). Balancer receives Ready for a removed SubConn. The
zombie loop survives until the next Shutdown check or `acctx.Done`
(1140-1142); the resurrected transport is closed only via NAT-5.
(c) **Q-01** (SYS-1/SYS-3, DOC-5 violated).

**P-01b** dial success published, then teardown.
(a) E06 → Ready; E02 tearDown.
(b) transport nil'd, Shutdown set, GracefulClose iff errConnDrain
(clientconn.go:1332-1348); loop wakes via reconnect (NAT-5) and exits at
clientconn.go:1121-1123.
(c) none — control trace. Cites DOC-5 ("Channels may enter this state
… application explicitly requested a shutdown"). Cited text contemplates
this ordering: yes.

**P-02a** reset.backoff, then TF entry.
(a) During Connecting_Dialing (or just before the TF lock at
clientconn.go:1120), E05 fires: closes the current `resetBackoff`
channel and replaces it (1293-1295), backoffIdx=0.
(b) The loop then enters TF and reads `b := ac.resetBackoff` (1128) —
the NEW channel, never closed; it sleeps the full `backoffFor` computed
at 975 from the PRE-reset backoffIdx.
(c) **Q-03** — DOC-15 says backoff "resets … for subsequent attempts
regardless of the current state"; the very next attempt still waits the
stale duration. Cited text contemplates this ordering: no.

**P-02b** TF entry, then reset.backoff.
(a) Loop sleeping in the select (1133-1143); E05 closes the captured
channel.
(b) `case <-b` (1138): timer stopped, immediate next iteration with
backoffIdx=0.
(c) none — control trace. Cites DOC-15 ("wakes up all subchannels in
transient failure … attempt another connection immediately"). Cited
text contemplates this ordering: yes.

**P-03a** ResetConnectBackoff holds cc.mu while a state update holds ac.mu.
(a) T1: `cc.ResetConnectBackoff` acquires cc.mu (843) and blocks on
ac.mu (1292). T2: resetTransport/tearDown/reportHealth holds ac.mu and
calls `updateConnectivityState` → `handleSubConnStateChange` which
blocks on cc.mu (949, 578) — or blocks on `cc.mu.RLock` at 999 while
the writer waits.
(b) Cycle cc.mu→ac.mu vs ac.mu→cc.mu: **deadlock**; both goroutines and
every later cc.mu user (including `cc.Close`) hang.
(c) **Q-02**.

**P-03b** state update completes, then ResetConnectBackoff.
(a) Same events, serialized.
(b) No cycle; reset applies.
(c) none — control trace (order decides survival — that is PA-1's
"order must never decide" applied to locks; the hazard itself is Q-02).

**P-04a** update.addrs (Ready, curAddr kept), then transport closes.
(a) E03 keeps the connection (709-721); E09 later.
(b) Reconnect walks the NEW `ac.addrs` from the top (974-979).
(c) none — control trace. Cites DOC-18 / tryUpdateAddrs comment
("The ac will keep using the existing connection"). Cited text
contemplates this ordering: yes.

**P-04b** transport closes, then update.addrs while reconnecting.
(a) E09 → Connecting; E03/E17 arrives.
(b) tryUpdateAddrs returns false (not Ready, 705-707); wrapper tears
this ac down and builds a replacement which dials addrs[0]
(balancer_conn_wrappers.go:285-313) — observed-in-tests
clientconn_test.go:977-1131 (V-11).
(c) none — control trace. Cites the test's contract comment
(clientconn_test.go:975-976 "UpdateAddresses should cause the next
reconnect to begin from the top of the list"). Cited text contemplates
this ordering: yes. Note: achieved by instance replacement, not by the
dead in-place mechanism (Q-10).

**P-05a** goaway, then close.
(a) E08: adjustParams under ac.mu→cc.mu (1163-1168, 954-964),
reconnect.Fire; E09: onClose fires the same event (1170-1174).
(b) Fire is idempotent; loop resumes once.
(c) none — control trace.

**P-05b** close, then late goaway.
(a) E09 first; E08 after.
(b) reconnect already fired (no-op); adjustParams still bumps cc.mkp
monotonically (959-961) — a dead transport can still raise the
keepalive floor.
(c) none — control trace (monotonic max makes the late write safe;
observed-in-code clientconn.go:959).

**P-06a** health not-serving, then transport closes.
(a) E13 → TransientFailure_ServerUnhealthy (1271-1273); E09.
(b) Loop resumes (1070), hcancel, TF_Backoff, backoff sleep, redial.
(c) none — control trace.

**P-06b** transport closes, then stale not-serving report.
(a) E09; the health goroutine's last `reportHealth(false)` arrives
after the next attempt began (NAT-3 tail report).
(b) Guard `ac.transport != newTr` (1262) no-ops it — the new attempt's
transport differs (or is nil).
(c) none — control trace (guard cited; the guard's dependence on
transport identity is exactly what UV08 resurrection would break —
noted under Q-01).

**P-07a** teardown, then connect.
(a) E02 → Shutdown; balancer retries E01.
(b) `errConnClosing` returned (672-674).
(c) none — control trace.

**P-07b** connect, then teardown before dial resolves.
(a) E01 spawns the loop; E02 during dial.
(b) connectCtx (child of ac.ctx) cancelled → dial error → error path
sees Shutdown → errConnClosing → goroutine exits (1181, 1221-1226,
1056-1058). The narrow success-window variant is P-01a.
(c) none — control trace.

## Free probes

**T-01** Duplicate teardown (cc.Close after RemoveSubConn).
(b) Second call no-ops on the Shutdown guard (1328-1331). Idempotent.
(c) none — control trace.

**T-02** connect() called concurrently twice from Idle.
(b) Both take ac.mu; first flips Idle→Connecting and spawns; second
sees non-Idle, returns nil (676-678). SYS-4 holds.
(c) none — control trace.

**T-03** Server accepts TCP, never speaks HTTP/2 (UV03), default On mode.
(b) prefaceTimer fires at connectDeadline → newTr.Close, "timed out
waiting for server handshake" (1192-1195) → next addr/TF/backoff;
backoffIdx grows (no reset without preface, 1084 unreached). Conforms
to DOC-13.
(c) none — control trace. Cites DOC-13 ("reset … when the SETTINGS
frame is received"). Cited text contemplates this ordering: yes.

**T-04** Same server, RequireHandshakeOff.
(b) createTransport returns immediately (no preface branch,
1190-1214 has no Off arm); Ready (1051); connection dies; backoffIdx=0
at 1112 **without any SETTINGS ever received**; cycle repeats every
Backoff(0)≈1s forever — no exponential growth.
(c) **Q-04** — violates DOC-12/DOC-13. Cited text contemplates this
ordering: no (the doc assumes reset only on server acceptance).

**T-05** Failures raise backoffIdx to 4; then a connection succeeds and
lives for hours; then dies.
(b) backoffFor was computed at 975 with backoffIdx=4 (~6.5s); success
resets backoffIdx=0 at 1112; the post-death TF sleep at 1129 still uses
the STALE ~6.5s (worst case 120s) before the first re-dial.
(c) **Q-03** (second face of P-02a).

**T-06** Health-checked server flaps SERVING → NOT_SERVING → SERVING
with the transport alive.
(b) Ready → TF_ServerUnhealthy (1271-1273) → Ready (1265-1270):
TRANSIENT_FAILURE → READY directly.
(c) **Q-07** — DOC-6's TF row allows only →CONNECTING/→SHUTDOWN. Cited
text contemplates this ordering: no (the table predates LB health
checking).

**T-07** Health stream established, server never sends any response
(UV09) while state is Connecting_HealthChecking.
(b) No timeout exists; RecvMsg blocks (health/client.go:88); ac remains
Connecting until the transport itself dies. RPCs see a permanently
connecting subchannel.
(c) **Q-08**.

**T-08** healthCheckFunc exits with a non-Unimplemented error (e.g.
stream type assertion, health/client.go:73-77) while Ready.
(b) Error logged (1286-1287); health monitoring silently over; ac stays
Ready unmonitored forever.
(c) **Q-08** (monitoring loss is silent — "failures must be loud" has
no doctrine line here, but DOC-3's recovery promise now depends solely
on transport death).

**T-09** GOAWAY(too_many_pings) storm: three GoAways from consecutive
transports.
(b) Each doubles the keepalive floor via monotonic max (957-961):
2·Time each cycle, ratcheting cc.mkp upward permanently; never decays.
(c) **Q-16** — is a permanently ratcheting, never-decaying keepalive
floor intended? The mutated field (cc.mkp) belongs to the ClientConn
model (model link); the ac-side dispatch (G-07) is proven and
documented, so the question is raised for the owning model.

**T-10** NAT violation: empty `ac.addrs` forced (violates NAT-4).
(b) addrLoop body never runs; TF (1125); sleep; iterate — a silent
1s-cadence spin (with resolveNow each iteration, 971-973) that never
dials and never surfaces an error.
(c) raised: robustness disposition for NAT-4 violation — folded into
Q-09 (dead/degenerate-input handling) as the "no defensive check"
variant; upstream guards make it unreachable today
(balancer_conn_wrappers.go:214-216, 280-283).

## Multi-instance probes (NAT-SYS-1)

**M-01** Shared-fate reset via ResetConnectBackoff. N subchannels (or N
processes behind an operator runbook) in TF_Backoff after a backend
outage; the operator's network-restored hook calls
`cc.ResetConnectBackoff` everywhere.
(b) Every subchannel's sleep is interrupted simultaneously
(846-848 → 1138); all dial at once; jitter is bypassed for this first
synchronized attempt. If the backend is still cold, all N fail
together, all sleep Backoff(0)+jitter — partially re-dispersed by
jitter only after the reset.
(c) **Q-13** — DOC-12 requires dispersal; the API creates a
synchronized start. Cited text contemplates this ordering: no (DOC-12
addresses backoffs "started at the same time", and this API
deliberately starts them at the same time).

**M-02** Backoff dispersion over 3 failure cycles. N subchannels in one
process share the seeded-once `grpcrand` source; across processes seeds
differ by start time.
(b) Jitter ±20% per cycle (backoff.go:70-73) disperses schedules
geometrically; no shared-seed lockstep observed in-tree. Dispersion
holds — but the Off-mode fast loop (T-04) has jitter only around 1s, so
N clients converge on ~1s cadence against a TCP-accepting-but-dead LB.
(c) folded into Q-04 (aggregate face of the Off-mode reset).

**M-03** Degraded-recovery herd. Backend recovers, accepts SETTINGS,
dies after 2s, repeatedly (crash loop).
(b) Every accepted connection resets backoffIdx=0 at death (1112); all
N subchannels re-dial ~Backoff(0)≈1s±20% after each crash — the
exponential ladder never climbs because every cycle "succeeded"
(DOC-13-conformant: SETTINGS was received). Aggregate: N dials/s
indefinitely against a crash-looping server.
(c) raised: is 1s-cadence-forever the intended aggregate behaviour for
a crash-looping backend? DOC-13's reset rule makes it so; DOC-12's
"must not attempt substantially more often" is arguably preserved
per-connection. Recorded as the proposal inside Q-13 (documented herd
characteristics), not a separate defect.
