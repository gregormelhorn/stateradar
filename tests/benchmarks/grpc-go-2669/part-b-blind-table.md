# Part B — blind disposition table (grpc-go v1.18.0 `addrConn`)

Produced by a fresh blind session (zero tool use) from the event
catalogue, the two requirement documents, and nothing else
(`tools/part_b_pack.py` package, 2026-08-07). Diffed against
`disposition-matrix.md` in `part-b-diff.md`.

## Disposition table

States per PA-17, from the requirements' public names: `Idle`, `Connecting` (sub-states by condition: `Connecting_Dialing`, `Connecting_HandshakeWait`, `Connecting_HealthChecking`), `Ready`, `Transient_Failure` (sub-states: `Transient_Failure_Backoff`, `Transient_Failure_ServerUnhealthy`), `Shutdown`. `Connecting_HandshakeWait` is the condition "TCP dial returned, HTTP/2 SETTINGS preface not yet received" — a sub-state of the requirements' CONNECTING ("waiting to make progress on ... handshake"), not an assumed state.

| Event id | Situation (state / condition) | Disposition | What should happen / requirement basis |
|---|---|---|---|
| **E01** `connect` | `Idle` | transition → `Connecting_Dialing` | Requirements: IDLE→CONNECTING on any new RPC activity; start the dial loop. |
| E01 | `Connecting_*` (any sub-state) | ignore (documented) | Attempt already in progress; duplicate connect is a no-op (catalogue gate: non-Idle → no-op). |
| E01 | `Ready` | ignore (documented) | Already connected; nothing to start. |
| E01 | `Transient_Failure_*` | ignore (documented) | Retry is owned by the backoff loop; requirements allow TF→CONNECTING only "wait time ... is over", so connect must not short-circuit backoff. (Contrast E05, which is the sanctioned short-circuit.) |
| E01 | `Shutdown` | reject | Returns `errConnClosing`. Requirements: SHUTDOWN is terminal; new work fails immediately. |
| **E02** `teardown` | Any state except `Shutdown`, payload `err != errConnDrain` | transition → `Shutdown` | Close transport hard, nil `ac.transport`, clear `curAddr`, remember `tearDownErr`, remove channelz. Requirements: SHUTDOWN reachable from every state by application action; never left. |
| E02 | `Ready`, payload `err == errConnDrain` | transition → `Shutdown` | Same, but GracefulClose the current transport (drain). Note the documented unlock window around GracefulClose admits interleavings (P-01 family). |
| E02 | `Shutdown` | ignore (documented) | Idempotent no-op (state==Shutdown guard); double close guarded at cc level too. |
| **E03** `update.addrs.keep` (list contains `curAddr`) | `Ready` | handle | Store the new list, keep the live connection; no state change (READY→READY "incremental successful communication"). |
| E03 | `Idle`, `Connecting_*`, `Transient_Failure_*` | reject | Returns false; the wrapper then tears this ac down and recreates — net effect for this ac: transition → `Shutdown`, replacement ac starts at `Connecting`. Only Ready may keep. |
| E03 | `Shutdown` | handle — **anomalous, should be ignore (documented)** | Catalogue: mutates `addrs` and returns true on a dead object forever (Q-09). Requirements give Shutdown no observable behaviour; a dead-object write is a divergence, not a requirement. |
| **E17** `update.addrs.drop` (list omits `curAddr`) | `Ready` | reject | Returns false → wrapper teardown+recreate: this ac transition → `Shutdown`; new ac dials the new list from `Connecting`. |
| E17 | `Idle`, `Connecting_*`, `Transient_Failure_*` | reject | Same false→recreate path (P-04b: lands mid-reconnect, still teardown+recreate). |
| E17 | `Shutdown` | handle — **anomalous, should be ignore (documented)** | Same Q-09 dead-object mutation as E03/Shutdown. |
| **E04** `get.ready.transport` | `Ready` ∧ transport present | handle | Return the transport. |
| E04 | `Idle` | handle + transition → `Connecting_Dialing` | Kick connect (requirements: any attempt to start an RPC pushes IDLE→CONNECTING); return "not ready" to the caller, who waits. |
| E04 | `Connecting_*`, `Transient_Failure_*` | reject | Declared not-ready signal (nil transport, no side effect). Must not trigger a dial in TF (backoff owns retry timing). |
| E04 | `Shutdown` | reject | nil; new RPCs fail immediately per requirements. |
| **E05** `reset.backoff` | `Transient_Failure_Backoff` (sleep in progress) | handle → transition → `Connecting_Dialing` | Channel close wakes the sleep immediately; `backoffIdx` reset to INITIAL_BACKOFF. Requirements (backoff doc): reset makes reconnect behave like a fresh connection; TF→CONNECTING is the legal exit. |
| E05 | `Idle`, `Connecting_*`, `Ready` | handle | Zeroes `backoffIdx`, swaps a fresh channel; no transition (only a sleeping select observes the close). Repeated calls are each a fresh E05 — idempotent in effect. |
| E05 | `Shutdown` | handle — **anomalous, should be ignore (documented)** | Dead-object mutation (catalogue Q-09 note); no state check exists on this public API. Concurrency hazard: see P-03a. |
| **E06** `dial.ok` (health gate FALSE) | `Connecting_Dialing` (the producing loop phase — only place it can legitimately occur) | handle → transition → `Ready` | Publish transport, set `curAddr`. Requirements: CONNECTING→READY when all connection steps succeed. Backoff reset on SETTINGS receipt applies per backoff doc (see E10/UV03 for Off-mode gap). |
| E06 | All other states | ignore (documented) | Sequential loop structure — cannot occur outside its phase. **Exception:** the post-teardown race is unguarded → see UV08 / P-01a. |
| **E16** `dial.ok.healthmanaged` (health gate TRUE) | `Connecting_Dialing` | handle → transition → `Connecting_HealthChecking` | Transport is up but not yet vouched serving; `curAddr` deliberately not set until first serving report. Requirements: READY demands all handshaking "succeeded" — withholding READY until the health verdict is the conservative reading; CONNECTING→CONNECTING (incremental progress) covers the sub-state move. |
| E16 | All other states | ignore (documented) | Same sequential-phase argument; same UV08 exposure as E06. |
| **E07** `dial.err` | `Connecting_Dialing`, payload `err == errConnClosing` | handle | Goroutine exits; ac is already `Shutdown` (teardown raced the dial); no state write. |
| E07 | `Connecting_Dialing` / `Connecting_HandshakeWait`, other error, more addresses remain | handle | Advance to next address, stay `Connecting_Dialing`. **Divergence flag:** requirements demand CONNECTING→TRANSIENT_FAILURE for "any failure in any of the steps" (and the API doc promises a TF notification per recoverable failure); per-address failures that stay CONNECTING skip that visible TF visit. Open point. |
| E07 | `Connecting_Dialing`, last address | handle | Feeds E15 (`addrs.exhausted`). |
| E07 | All other states | ignore (documented) | Phase-result; cannot occur elsewhere. |
| **E08** `transport.goaway` | `Ready` (current transport), any reason | handle → (via transport death) transition → `Transient_Failure`/`Connecting_Dialing` | Fire `reconnect`; if reason is `GoAwayTooManyPings`, additionally bump keepalive (monotonic max). **Divergence flag:** requirements say GOAWAY with no active/pending RPCs should yield READY→IDLE (server load-shedding); the addrConn only reconnects. Whether the ClientConn layer supplies the IDLE behaviour is outside these inputs — open point. |
| E08 | `Connecting_HandshakeWait` / `Connecting_HealthChecking` (live transport of current attempt) | handle | Same: keepalive adjust if applicable; attempt fails and loop continues. |
| E08 | Any state, stale transport generation | handle (params only), otherwise ignore (documented) | Keepalive adjust still applies (P-05b — a global, monotonic parameter); the stale `reconnect` resolves against the dead generation's own closure, never the current attempt (UV01). |
| E08 | `Shutdown` | ignore (documented) | Late callback on a dead generation; keepalive adjust is the only residue, harmless. |
| E08 | Unknown `GoAwayReason` value | handle (reconnect) + ignore (documented) for params | Unknown reasons fall through the params switch by design; reconnect fires regardless. |
| **E09** `transport.closed` | `Ready` | handle → transition → `Transient_Failure` → `Connecting_Dialing` | Unblocks the loop; success-at-death resets `backoffIdx`, so the TF dwell may be zero-length — but requirements list no READY→CONNECTING transition, so the TF visit is mandatory even with zero wait (the API doc explicitly warns of these "apparently spurious" notifications). Whether the implementation emits the TF visit is not stated in the inputs → open point. |
| E09 | `Connecting_HandshakeWait` | handle | "Closed before preface" — the attempt fails as E07; next address or E15. |
| E09 | `Connecting_HealthChecking` / `Transient_Failure_ServerUnhealthy` | handle → transition → `Transient_Failure_Backoff` or next address | Transport death ends the health-managed episode (P-06a). |
| E09 | Any state, stale generation | ignore (documented) | Per-attempt event objects; old close already consumed (UV01). |
| E09 | `Shutdown` | ignore (documented) | Teardown already closed the transport; onClose takes no ac lock, no-op. |
| **E10** `preface.received` | `Connecting_HandshakeWait`, reqHandshake On | handle → transition → `Ready` (or `Connecting_HealthChecking` if E16 gate) | Completes handshake wait. Per backoff doc, backoff resets to INITIAL_BACKOFF here (SETTINGS = server accepted the connection). |
| E10 | `Ready`, reqHandshake Hybrid (death-check) | handle | Consulted only if the transport dies: died-without-preface counts as a failed attempt (backoff not reset). |
| E10 | Any state, reqHandshake Off | ignore (accidental) | Never read (Q-04) — connection was published unverified; also leaves the backoff-doc "reset on SETTINGS" obligation unwitnessed. Open point. |
| E10 | Any state, stale generation | ignore (documented) | Per-generation closure. |
| **E11** `backoff.timer.fired` | `Transient_Failure_Backoff` | handle → transition → `Connecting_Dialing` | Requirements: TF→CONNECTING exactly when "wait time required to implement exponential backoff is over". |
| E11 | `Shutdown` (teardown during the sleep) | ignore (documented) | Wakes, hits the Shutdown check, goroutine exits without dialing. |
| E11 | All other states | ignore (documented) | Timer exists only inside the sleep; cannot fire elsewhere. |
| **E12** `health.report.serving` | `Connecting_HealthChecking`, transport identity matches | handle → transition → `Ready` | First serving report sets `curAddr` and publishes READY. CONNECTING→READY legal. |
| E12 | `Ready`, same transport (repeat) | ignore (documented) | Equal-state reports are no-ops. |
| E12 | `Transient_Failure_ServerUnhealthy`, same transport | handle → transition → `Ready` — **divergence flag** | Last-write-wins under the lock, so the implementation returns to Ready; but requirements forbid TF→READY (only TF→CONNECTING/SHUTDOWN legal). Either the sub-state should not have been externally reported as TRANSIENT_FAILURE, or a CONNECTING hop is required. Open point. |
| E12 | Any state, stale transport | ignore (documented) | Transport-identity guard (UV07). |
| E12 | `Shutdown` | ignore (documented) | Transport nil'd at teardown → identity guard fails. |
| **E13** `health.report.notserving` | `Ready` (health-managed, same transport) | handle → transition → `Transient_Failure_ServerUnhealthy` | READY→TF legal ("any failure encountered while expecting successful communication"). Connection stays up; RPCs stop being routed here. |
| E13 | `Connecting_HealthChecking`, same transport | handle → transition → `Transient_Failure_ServerUnhealthy` | CONNECTING→TF legal; `curAddr` was never set. |
| E13 | Any state, stale transport | ignore (documented) | Identity guard (UV07, P-06b). |
| E13 | `Shutdown` | ignore (documented) | Identity guard (transport is nil). |
| **E14** `health.stream.ended` | Any health-managed situation (`Connecting_HealthChecking`, `Ready`, `Transient_Failure_ServerUnhealthy`), payload Unimplemented | handle | Log "health disabled"; no state write — the connection keeps its last verdict. If it ends before any verdict, the ac is stranded in `Connecting_HealthChecking` until the transport dies (UV09 adjacency). |
| E14 | Same situations, other error payload | handle | Error log only; no state write; the client-side health machinery has its own stream retry/backoff upstream. |
| E14 | `Shutdown` / stale | handle (log only) | Harmless; no state to touch. |
| **E15** `addrs.exhausted` | `Connecting_Dialing` (loop fell through every address) | handle → transition → `Transient_Failure_Backoff` | Compute backoff per the backoff algorithm (exponential, jitter, MAX_BACKOFF cap; per-attempt timeout floor MIN_CONNECT_TIMEOUT via UV04), sleep, wait for E11/E05. CONNECTING→TF legal. |
| E15 | `Shutdown` (teardown raced the loop) | ignore (documented) | Shutdown check at TF entry → goroutine exits; state stays `Shutdown`. |
| E15 | All other states | ignore (documented) | Internal phase-result; cannot occur elsewhere. |
| **UV01** stale E08/E09 from a previous transport generation | any state after a new attempt started | ignore (documented) | Generation isolation: one event object per attempt; a dead generation's callbacks resolve only against their own closures. Required and satisfied. |
| **UV02** duplicate GoAway frames | `Ready` / `Connecting_*` | handle (first), ignore (documented) (repeats) | `Event.Fire` idempotent; keepalive adjust is a monotonic max, so replays are harmless. |
| **UV03** preface never sent — reqHandshake On | `Connecting_HandshakeWait` | handle | Preface timer closes the transport; attempt fails (E07); next address or E15. Correct per "waiting to make progress" semantics; also protects the backoff-reset-on-SETTINGS rule. |
| UV03 — Hybrid | `Ready` (transport published pre-verdict) | handle → transition → `Transient_Failure`/`Connecting` | Watcher closes an already-READY transport — a READY connection retroactively failed. Legal (READY→TF) but a false READY was exposed. |
| UV03 — Off | `Ready` | ignore (accidental) — **defect flag (Q-04)** | Never checked; unverified connection stays READY, and backoff may be reset without a SETTINGS frame — contradicts the backoff doc's reset condition. Open point. |
| **UV04** dial/handshake exceeds connectDeadline | `Connecting_Dialing` / `Connecting_HandshakeWait` | handle | Deadline fails the attempt → E07 path. Matches backoff doc: `TryConnect(Max(current_deadline, now()+MIN_CONNECT_TIMEOUT))` — every attempt must terminate. |
| **UV05** GoAway and close near-simultaneous | `Ready` (same transport) | handle | Both fire the same idempotent reconnect event; order-independent; keepalive adjust applied whichever arrives second. Required and satisfied. |
| **UV06** health report with no managed stream (commission) | any | ignore (documented) | Not producible: the report closure is reachable only via `healthCheckFunc`; a post-cancel late report is dropped by the transport-identity guard. |
| **UV07** health report bound to a stale transport | any | ignore (documented) | Transport-identity guard; the required disposition, satisfied. |
| **UV08** dial.ok/dial.ok.healthmanaged lands after teardown completed | `Shutdown` | Required: ignore (documented) — close the new transport, stay `Shutdown`. Actual per catalogue: handle → transition → `Ready` — **defect (Q-01)** | Requirements are unambiguous: "Channels that enter this state never leave this state." Re-publishing a transport and setting READY on a Shutdown ac violates the terminal-state guarantee and leaks a live transport nothing will ever close. |
| **UV09** health stream delivers no verdict, ever (loss; delay indistinguishable) | `Connecting_HealthChecking` | UNSPECIFIED — **gap (Q-08)** | No timeout exists; the ac can wait forever in CONNECTING. Requirements set no health deadline (open point), but indefinite CONNECTING with a live transport serves no one. |
| UV09 | `Transient_Failure_ServerUnhealthy` | UNSPECIFIED — **gap (Q-08)**, leaning divergence | Requirements state TF channels "will eventually switch to CONNECTING". A TF sub-state that can persist forever (no verdict, transport healthy at the TCP level) breaches that "eventually" unless the transport happens to die. |
| **P-01a** E02 teardown THEN stale E06 dial.ok | `Shutdown`, in-flight dial result arrives | E02: transition → `Shutdown`; then stale E06 required: ignore (documented); actual: handle → `Ready` — **defect (Q-01)** | The resurrection case of UV08, reachable through the documented unlock window in tearDown's GracefulClose. |
| **P-01b** E06 dial.ok THEN E02 teardown | `Ready` when teardown arrives | E06: transition → `Ready`; E02: transition → `Shutdown` | Normal shutdown: transport nil'd and closed (GracefulClose if drain). No residue. |
| **P-02a** E05 reset THEN E15 TF entry | reset lands before the backoff sleep begins | E05: handle (backoffIdx zeroed, fresh channel); E15: handle → `Transient_Failure_Backoff` — **divergence flag (Q-03)** | The already-computed sleep duration is not shortened; the fresh channel means this reset can never wake that sleep. The backoff doc's intent (reset ⇒ behave like a new connection) is only honoured for the *next* cycle. Open point. |
| **P-02b** E15 TF entry THEN E05 reset | sleep in progress | E15: handle → `Transient_Failure_Backoff`; E05: handle → transition → `Connecting_Dialing` | Channel close wakes the select immediately; the sanctioned TF→CONNECTING early exit. |
| **P-03a** E05 (holding cc.mu) concurrent WITH E09-driven state update (holding ac.mu, needing cc.mu) | any state with both in flight | UNSPECIFIED — **defect (Q-02): deadlock** | Lock-order inversion (cc.mu→ac.mu vs ac.mu→cc.mu). Required disposition is that both serialize as ordinary handle; instead survival depends on interleaving. No requirement permits a public API call to wedge the channel. |
| **P-03b** state update completes, THEN E05 | any | handle / handle | Serializes fine; each event disposed per its base row. Order alone decides P-03a vs P-03b — that asymmetry is the finding. |
| **P-04a** E03/E17 update.addrs THEN E09 transport.closed | update arrives in `Ready` | E03: handle (keep) or E17: reject→recreate; subsequent E09 on a replaced ac: ignore (documented) (stale generation) — the new ac starts from `Connecting` at the top | Requirements: the replacement channel's IDLE/CONNECTING entry is the "new RPC activity" path. |
| **P-04b** E09 transport.closed THEN E03/E17 | update lands in `Connecting_*` mid-reconnect | E09: handle (loop resumes); E03/E17: reject → teardown+recreate — old ac transition → `Shutdown`, new ac `Connecting` | Only Ready may keep; a mid-reconnect update always recreates. |
| **P-05a** E08 goaway THEN E09 close (same transport) | `Ready` | E08: handle (params + reconnect); E09: ignore (documented) (reconnect already fired, idempotent) | Net: one reconnect, params adjusted. |
| **P-05b** E09 close THEN E08 goaway | `Ready`→reconnecting | E09: handle (reconnect fires); late E08: handle for keepalive params only, ignore (documented) for the second Fire | Params adjust is order-independent by monotonic-max design. |
| **P-06a** E13 not-serving THEN E09 transport closed | `Ready`/`Connecting_HealthChecking` | E13: transition → `Transient_Failure_ServerUnhealthy`; E09: handle → transition → `Transient_Failure_Backoff` → eventually `Connecting_Dialing` | Sub-state move within TRANSIENT_FAILURE; externally still TF→CONNECTING, legal. |
| **P-06b** E09 THEN stale E13 | reconnecting, old transport's verdict arrives | E09: handle; E13: ignore (documented) — transport-identity guard | The required stale-report disposition, satisfied. |
| **P-07a** E02 teardown THEN E01 connect | `Shutdown` | E02: transition → `Shutdown`; E01: reject (`errConnClosing`) | "Any new RPCs should fail immediately"; terminal state honoured on this path. |
| **P-07b** E01 connect THEN E02 teardown | `Connecting_Dialing` when teardown arrives | E01: transition → `Connecting_Dialing`; E02: transition → `Shutdown` — in-flight dial aborts via context, loop exits at its Shutdown checks (E07 `errConnClosing` / E15 Shutdown check) | Clean abort — subject to the P-01a window if the dial result was already past the point of no return. |

## Coverage checklist

- [x] E01
- [x] E02
- [x] E03
- [x] E17
- [x] E04
- [x] E05
- [x] E06
- [x] E16
- [x] E07
- [x] E08
- [x] E09
- [x] E10
- [x] E11
- [x] E12
- [x] E13
- [x] E14
- [x] E15
- [x] UV01
- [x] UV02
- [x] UV03
- [x] UV04
- [x] UV05
- [x] UV06
- [x] UV07
- [x] UV08
- [x] UV09
- [x] P-01a
- [x] P-01b
- [x] P-02a
- [x] P-02b
- [x] P-03a
- [x] P-03b
- [x] P-04a
- [x] P-04b
- [x] P-05a
- [x] P-05b
- [x] P-06a
- [x] P-06b
- [x] P-07a
- [x] P-07b

All 26 catalogue events and all 14 pair orderings covered — 40 of 40.
