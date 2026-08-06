# Open domain questions — grpc-go v1.18.0 `addrConn`

Every hole, contradiction, invariant violation, and lint finding from
this pilot, consolidated. Nothing resolved here; human decisions
required. ODC fields per 02-pilot v1.14: `fault` from
formats/rules.toml, `trigger` = detector that found it.

---

Q-01
Question: May a dial attempt that completes after `tearDown` re-publish
its transport and move a Shutdown addrConn to Ready?
Current behaviour: it does — no Shutdown re-check between the last
guard in createTransport and publication/Ready
(observed-in-code, clientconn.go:1026-1052; `updateConnectivityState`
has no terminal guard, clientconn.go:936-942; z3 witness G-05).
Consequences: SYS-1/SYS-3 and DOC-5/DOC-6 violated; balancer receives
Ready (or health-path updates, via the re-armed transport identity
clientconn.go:1029→1262) for a removed SubConn; the new transport is
closed only via eventual ctx propagation (NAT-5); channel-level state
can flap on a closed subchannel.
Options: re-check Shutdown under the publication lock and close newTr |
add a Shutdown guard inside updateConnectivityState (mirror
clientconn.go:340-342) | both.
Proposed: both — the guard closes the class, the re-check closes the
leak (proposed).
fault: F-04 (sneak path out of a terminal state)
trigger: step-3 pairs table → adversarial trace P-01a (PA-24 lint
corroborates)
part-B: independently derived blind (part-b-diff) — rows UV08/P-01a
derive the required disposition (close the new transport, stay
Shutdown) from DOC-5's terminal-state text and mark the actual a defect.
Status: OPEN — human decision required

Q-02
Question: Which lock order over {cc.mu, ac.mu} is authoritative?
`cc.ResetConnectBackoff` takes cc.mu→ac.mu (clientconn.go:843-849 →
1292); every ac state update takes ac.mu→cc.mu
(clientconn.go:949 → 578; also 998-1001 RLock while a writer may wait).
Current behaviour: lock-order inversion; concurrent
ResetConnectBackoff + any subchannel state change can deadlock the
whole ClientConn (P-03a).
Options: snapshot cc.conns under cc.mu, release, then call
ac.resetConnectBackoff outside the lock | make handleSubConnStateChange
run outside ac.mu | document ResetConnectBackoff as unsafe (untenable
for a public API).
Proposed: release cc.mu before touching per-ac locks (proposed).
fault: F-11 (lock/callback deadlock)
trigger: step-3 lock-discipline annotation
part-B: independently derived blind (part-b-diff) — row P-03a marks the
ordering UNSPECIFIED-deadlock: no requirement permits a public API call
to wedge the channel.
Status: OPEN — human decision required

Q-03
Question: Should the backoff sleep after a connection ends use a delay
computed from the *current* backoffIdx (and honor resets that arrived
mid-cycle)?
Current behaviour: `backoffFor` is computed once per outer iteration
(observed-in-code, clientconn.go:975) and used at clientconn.go:1129
even though backoffIdx may have been reset to 0 meanwhile (success at
clientconn.go:1112, or E05 at clientconn.go:1294 whose channel-close
signal is lost when it lands before clientconn.go:1128 captures the
channel). Worst case: up to 120s wait before the first reconnect after
a healthy connection dies (T-05); DOC-15's "resets … for subsequent
attempts regardless of the current state" not honored for the pending
sleep (P-02a).
Options: recompute backoffFor at TF entry | re-read backoffIdx after
success | also re-check resetBackoff generation before sleeping.
Proposed: recompute at TF entry (proposed).
fault: F-18 (stale computed value)
trigger: step-1 extraction, confirmed by traces P-02a/T-05
part-B: independently derived blind (part-b-diff) — row P-02a flags the
lost reset (fresh channel never wakes the pending sleep); blind
divergence E09 folded here: its zero-dwell expectation after a
successful connection dies is exactly what the stale backoffFor denies.
Status: OPEN — human decision required

Q-04
Question: In RequireHandshakeOff mode, may backoff reset to initial on
a connection death when no SETTINGS frame was ever received?
Current behaviour: yes — the Off arm reaches the success path without
any preface requirement (observed-in-code, clientconn.go:1104-1114;
no Off branch in clientconn.go:1190-1214), so a TCP-accepting but
non-gRPC endpoint produces a ~1s reconnect loop forever (T-04, M-02),
against DOC-12/DOC-13.
Options: reset only when prefaceReceived fired (all modes) | accept as
the documented price of Off mode with a doc note | remove Off mode.
Proposed: gate the reset on prefaceReceived (proposed; matches DOC-13's
rationale "we know for sure this connection was accepted").
fault: F-02 (invalid reconnect path / wrong reset condition)
trigger: step-5 doctrine mapping (PA-22, DOC-13)
part-B: independently derived blind (part-b-diff) — rows E10/UV03 (Off)
mark the never-read preface an accidental ignore and derive the
violated reset-on-SETTINGS obligation from the backoff doc.
Status: OPEN — human decision required

Q-05
Question: Is `GRPC_GO_REQUIRE_HANDSHAKE=on` intended to select Hybrid?
Current behaviour: `case "on":` has an empty body, so an explicit "on"
leaves the zero value RequireHandshakeHybrid, while an unset variable
selects On via `default:` (observed-in-code,
internal/envconfig/envconfig.go:58-68) — contradicting the doc comment
(envconfig.go:41-43, DOC-20). Tests bypass the parser
(clientconn_test.go:388-389), so nothing catches it. Upstream of this
component's `reqHandshake` gate (clientconn.go:1067); flagged as a
neighbouring-scope defect.
Options: fold "on" into the default arm | leave (variable is
deprecated, removed after 1.18 per envconfig.go:55-58).
Proposed: fold into default (proposed).
fault: F-18 (subtle value fault — config)
trigger: seam-contract sweep (step 1)
Status: OPEN — human decision required

Q-06
Question: Where do DOC-4's IDLE semantics live? The addrConn never
re-enters Idle (no transition targets it), there is no IDLE_TIMEOUT,
and a GOAWAY with no active RPCs triggers reconnect
(cells (Ready, E08)), not IDLE.
Current behaviour: unimplemented at this boundary
(observed-in-code: no code path writes Idle after clientconn.go:680).
Options: accept as channel-level responsibility (model link, out of
this matrix) | record as an unimplemented requirement for the ClientConn
model | implement subchannel idleness.
Proposed: record against the (not yet modelled) ClientConn model
(proposed).
fault: F-19 (unimplemented requirement)
trigger: step-5 doctrine mapping (PA-22, DOC-4)
part-B: independently derived blind (part-b-diff) — row E08 flags that
GOAWAY with no active RPCs should yield READY→IDLE per requirements
while the addrConn only reconnects.
Status: OPEN — human decision required

Q-07
Question: Is the direct TRANSIENT_FAILURE → READY transition on a
health recovery (cell (TransientFailure_ServerUnhealthy, E12),
clientconn.go:1265-1270) acceptable against DOC-6, whose TF row allows
only →CONNECTING and →SHUTDOWN?
Current behaviour: direct TF→Ready (observed-in-code; trace T-06).
Requirement-scope: the table predates LB health checking — cited text
contemplates this transition: no.
Options: accept and annotate the doc | interpose a CONNECTING
notification | treat health-TF as a distinct reported state.
Proposed: accept with documentation (proposed).
fault: F-02 (transfer fault vs. documented legal table)
trigger: step-5 doctrine mapping (PA-22, DOC-6)
part-B: independently derived blind (part-b-diff) — row E12
(TF_ServerUnhealthy) flags the TF→READY transition as forbidden by the
legal-transition table and asks for a CONNECTING hop or a distinct
reported state.
Status: OPEN — human decision required

Q-08
Question: What must happen when the health-check stream never delivers
a verdict, or health monitoring ends with an error?
Current behaviour: no timeout on the first verdict — silent stream
strands the ac in Connecting_HealthChecking (cell hole → this Q,
T-07); a silent stream after a not-serving report strands
TransientFailure_ServerUnhealthy with a live transport, leaving DOC-3's
"eventually CONNECTING" without any path (cell hole → this Q); a
non-Unimplemented healthCheckFunc error only logs and silently disables
monitoring while Ready (observed-in-code, clientconn.go:1276-1288,
T-08).
Options: verdict timeout → TransientFailure | treat health-stream death
as transport-suspect and recycle | accept with documentation.
Proposed: verdict timeout, and recycle on stream error (proposed).
fault: F-13 (delay/loss without guaranteed progress)
trigger: step-3 checklist (loss/delay → UV09) + step-5 lint (waiting
state without timeout)
part-B: independently derived blind (part-b-diff) — rows UV09/E14 mark
the verdictless stream UNSPECIFIED and derive the DOC-3 "eventually
CONNECTING" breach for the stranded TF sub-state.
Status: OPEN — human decision required

Q-09
Question: What is the contract of mutating APIs on a Shutdown addrConn?
`tryUpdateAddrs` mutates `ac.addrs` and returns true
(observed-in-code, clientconn.go:698-701) so the wrapper treats the
update as applied to a dead subconn (balancer_conn_wrappers.go:285);
`resetConnectBackoff` swaps channels on a dead ac
(clientconn.go:1291-1297); no defensive check exists for a degenerate
empty `addrs` (T-10, unreachable today per NAT-4).
Current behaviour: silent acceptance on a dead object.
Options: return false / no-op after Shutdown and let the wrapper
recreate | document the true-on-Shutdown special case | leave.
Proposed: no-op-and-document (proposed).
fault: F-15 (stale/after-shutdown arrival accepted)
trigger: step-4 matrix walk
Status: OPEN — human decision required

Q-10
Question: What was `tryNextAddrFromStart` supposed to do? It is created
and polled every iteration (clientconn.go:968, 1060, 1100) but no code
ever fires it — both `break addrLoop` arms are dead.
Current behaviour: dead mechanism; restart-from-top after address
updates happens only via instance replacement
(balancer_conn_wrappers.go:285-313, V-11).
Options: delete | wire tryUpdateAddrs to fire it (in-place restart).
Proposed: delete (proposed — replacement path is tested).
fault: F-06 (trap door / undocumented dead path)
trigger: step-1 extraction
Status: OPEN — human decision required

Q-11
Question: Is it acceptable that a non-drain `tearDown` never closes the
transport directly, relying on ctx-cancellation propagation through
transport internals (NAT-5), and that this abrupt path kills pending
RPCs while DOC-5 says pending RPCs may continue until the application
cancels them?
Current behaviour: `curTr.Close()` is never called for
`err != errConnDrain` (observed-in-code, clientconn.go:1332-1349);
closure is eventual via internal/transport/http2_client.go:326-338.
Options: close explicitly on teardown | document the indirection and
its latency | align drain/non-drain semantics with DOC-5.
Proposed: close explicitly (proposed).
fault: F-07 (lifecycle coupling across tracks — cleanup owned by a
different lifecycle)
trigger: seam-contract sweep (step 1)
part-B: blind divergence E02 folded here (part-b-diff) — the blind
expects a hard transport close on non-drain teardown, which is exactly
this question's "close explicitly" option; the actual ctx-only path is
the current behaviour recorded above.
Status: OPEN — human decision required

Q-12
Question: Is the unbounded accumulation of `defer hcancel()` closures
acceptable? The defer sits inside the per-address loop body
(observed-in-code, clientconn.go:1012-1013) of a function that returns
only at Shutdown (clientconn.go:967), so every attempt of an ac that
retries for days leaves a queued deferred call (explicit hcancel at
clientconn.go:1055/1071 releases the context, the deferred duplicate
remains queued).
Options: drop the defer (explicit calls cover all paths) | restructure
the loop body into a function.
Proposed: drop the defer after verifying path coverage (proposed).
fault: F-07 (residue of ended attempts held by the long-lived loop)
trigger: step-5 lint (unbounded buffers/queues)
Status: OPEN — human decision required

Q-13
Question: Should ResetConnectBackoff (and the reset-on-accept rule)
decorrelate the resulting reconnect wave? `cc.ResetConnectBackoff`
wakes every subchannel simultaneously (clientconn.go:846-848 → 1138)
with an immediate, un-jittered dial; a crash-looping backend gets N
dials at ~1s cadence forever because every accepted connection resets
the ladder (clientconn.go:1112; M-01, M-03; DOC-12).
Current behaviour: synchronized reset points, jitter only on subsequent
backoffs.
Options: jitter the post-reset dial | rate-limit fleet resets | accept
and document the herd characteristics.
Proposed: accept and document; the API doc already discourages use
(clientconn.go:836-840) (proposed).
fault: F-10 (synchronized reset herd)
trigger: step-5 lint (synchronized reset points) + multi-instance
probes M-01/M-03
Status: OPEN — human decision required

Q-14
Question: Must a per-address connection failure emit the
CONNECTING→TRANSIENT_FAILURE→CONNECTING notification pair required by
DOC-7? On mode stays silently CONNECTING across the address list
(observed-in-tests, clientconn_state_transition_test.go:267-273, V-05);
Hybrid emits a TF blip per failed address (observed-in-code,
clientconn.go:1097).
Current behaviour: mode-dependent, mutually inconsistent.
Options: per-address TF blip everywhere (DOC-7 literal) | per-list-pass
TF only (current On behaviour) with a doc deviation note.
Proposed: per-list-pass, documented (proposed — matches the tested
contract).
fault: F-03 (missing/inconsistent output notification)
trigger: step-2 test replay (as-is validation V-05)
part-B: independently derived blind (part-b-diff) — row E07 flags that
per-address failures staying CONNECTING skip the DOC-7 TF notification.
Status: OPEN — human decision required

Q-15
Question: What should ResetConnectBackoff do for a subchannel in
TransientFailure_ServerUnhealthy? DOC-15 promises "wakes up all
subchannels in transient failure … attempt another connection
immediately", but this TF variant is parked on `<-reconnect.Done()`
(clientconn.go:1070), not on the backoff select, so the call only
zeroes backoffIdx (cell (TransientFailure_ServerUnhealthy, E05)).
Current behaviour: no reconnect attempt.
Options: also fire reconnect for health-TF | scope DOC-15 to
backoff-TF and document.
Proposed: scope and document (proposed — recycling a live transport on
a backoff API seems unintended).
fault: F-01 (missing transition for a documented event)
trigger: step-4 matrix walk (PA-22 against DOC-15)
Status: OPEN — human decision required

Q-16
Question: Is the permanently ratcheting keepalive floor intended?
GOAWAY(too_many_pings) doubles cc.mkp.Time monotonically with no decay
(observed-in-code, clientconn.go:954-964; T-09). The field belongs to
the ClientConn scope — raised for the owning model (model link).
Options: cap | decay on stable connections | accept (server-directed).
Proposed: accept — server-directed flow control (proposed).
fault: F-05 (accumulating context state never restored)
trigger: adversarial trace T-09
Status: OPEN — human decision required

---

## Summary count

| metric | count |
|---|---|
| states (leaf) | 7 |
| events incl. undesired variants | 26 (17 base + 9 UV) |
| interaction pairs | 7 (14 orderings) |
| matrix cells | 182 |
| UNSPECIFIED | 0 |
| ignore (accidental) | 2 (both → Q-08) |
| guard groups proven | 9 (G-01..G-04, G-06..G-10) |
| guard violations | 1 (G-05 → Q-01) |
| not-formalizable | 2 (G-11 unstructured-payload, G-12 dynamic-state) |
| findings (bug/contradiction/lint, all carried as questions) | 16 |
| open questions | 16 (Q-01..Q-16, all OPEN) |
