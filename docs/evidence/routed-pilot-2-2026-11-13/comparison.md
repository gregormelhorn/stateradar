# Second routed pilot vs. benchmark silenceper-pool-32 — comparison

Routed run: pack a331dae, prompt v1.17, pool @ 6084537, routing on (Flash +
`jev-1.14.0`), run on 2026-11-13 00:41-01:18 UTC. Oracle:
`tests/benchmarks/silenceper-pool-32/` and the first routed pilot
(`docs/evidence/routed-pilot-2026-11-13/comparison.md`). The comparison was
written after the run, outside the pilot session, by the reviewer who had read
the oracle; the pilot session had not.

## Blinding

This run was blind to the oracle, unlike the first pilot.

* The operator brief named no finding. The pilot's sparse checkout excluded
  `docs/`, `tests/benchmarks/`, `README.md` and `CHANGELOG.md`, so neither the
  benchmark, the first pilot's evidence nor the roadmap entry describing it was
  readable.
* The `draft-verify` task (`routing/task-code.txt`) is finding-neutral (rule
  10): it asks for states, events, guards, locks, waiting and cancellation
  paths, and names no behaviour.
* Flash's own `channel.go` draft raised the primary finding as its first
  question: "What happens to blocked Get waiters when Release is called?
  connReqs are not closed in Release, so it is unclear whether waiters ever
  unblock." (`routing/dv-channel.json`, question 1; question 2 notes that no
  code closes a request channel).

## Primary finding

Found: **yes**, independently. Q-01 ("What must Release do with Gets that are
blocked waiting for a connection?"), with SYS-4, L-6, L-9, L-11 and trace
P-01a, and **executed**: `as-is-tests.md` T1 logs `AS-IS: waiter still blocked
300ms after Release; connReqs=1`. Expected phrases `connReqs` (1 occurrence in
`open-questions.md`) and `waiter` (17) are present.

`expected.json` unspecified cells:

| expected | routed | match |
|---|---|---|
| Released × Put | Released × E-PUT = `ignore (accidental) → Q-06` | hole: yes; literal UNSPECIFIED: no |
| Active_IdleExhausted_AtCapacity × Release | Open_AtCapacity × E-RELEASE = transition → Released (no waiter yet); Open_AtCapacity_Waiting and Open_Waiting_Stranded × E-RELEASE = transition → Released, waiters stay blocked → Q-01 | finding: yes; hole label: no |

As in the first pilot, the routed matrix records the observed behaviour with a
question instead of the label `UNSPECIFIED`; a scorer that requires the literal
label on those two cells counts them as missed.

## Cell-level agreement (aligned base grid, 4 states × 7 events = 28 cells)

The baseline cell values are the agent-only run's as-is matrix as quoted in the
first pilot's comparison. State alignment (the routed model has 7 states):
Active_HasIdle ↔ Open_IdleAvailable ∪ Open_IdleFull;
Active_IdleExhausted_UnderCap ↔ Open_Empty; Active_IdleExhausted_AtCapacity ↔
Open_AtCapacity ∪ Open_AtCapacity_Waiting ∪ Open_Waiting_Stranded; Released ↔
Released. Events: Get, Put, Close, Release, FactoryFail, IdleTimeout ↔ E-GET,
E-PUT, E-CLOSE, E-RELEASE, UV-FACTORY-ERR, I-IDLE-EXPIRE. The routed run has no
separate PingFail event: a failed Ping is a guarded branch of E-GET (G-03,
not-formalizable), so the PingFail column is compared against E-GET's Ping
branch. A cell counts as agreeing when every aligned routed sub-state agrees.

| baseline state | Get | Put | Close | Release | FactoryFail | IdleTimeout | PingFail |
|---|---|---|---|---|---|---|---|
| Active_HasIdle | = (handle; routed: guarded transition, else stays) | = (handle; routed: transition → Open_IdleFull at MaxIdle, else stays) | = | = | **≠** handle vs reject | **≠** handle vs ignore (accidental) → Q-13 | = (discard via Close, retry) |
| Active_IdleExhausted_UnderCap | = (guarded transition, else stays) | = (transition → idle) | **≠** UNSPECIFIED Q-06 vs handle | = | **≠** UNSPECIFIED Q-05 vs reject → Q-17 | = ignore (documented) | = ignore (documented: no idle connection) |
| Active_IdleExhausted_AtCapacity | = (defer; routed: transition → Open_AtCapacity_Waiting / handle) | = (handle; routed: transition / handoff) | **≠** UNSPECIFIED Q-06 vs transition (→ Open_Waiting_Stranded, Q-04 lost wake-up) | **≠ label** UNSPECIFIED Q-01 vs transition → Q-01 | **≠** UNSPECIFIED Q-05 vs ignore (documented) | **≠** ignore (documented) vs mixed (documented; accidental → Q-13 in Open_Waiting_Stranded) | = (handoff path skips Ping → Q-14, as in the first pilot) |
| Released | = reject | = hole (UNSPECIFIED vs ignore (accidental) → Q-06) | **≠** ignore (documented) vs ignore (accidental) → Q-06 | = | = ignore (documented) | = ignore (documented) | = ignore (documented) |

Convergent 19 / 28 (68 %); divergent 9, of which 1 is label-only (the same
finding). First routed pilot: 21 / 28. The baseline's own `CONVERGENCE.md`
reports 28 / 28 between its two agent-only runs.

Divergences, assessed against channel.go @ 6084537:

* **FactoryFail (3 cells).** The first pilot had the same three. The baseline
  holes rest on counter drift after a factory failure; the code increments only
  after success (channel.go:155-159) and does not call the factory at the cap
  (channel.go:133). This run labels the failure `reject` (the error is returned
  to the caller, channel.go:157) where the first pilot said `handle`; both match
  the code, and the label choice is a vocabulary question.
* **Close below and at capacity (2 cells).** Same as the first pilot: the
  routed run models misuse as variants (UV-CLOSE-DUP, UV-CLOSE-FOREIGN → Q-10)
  and finds that Close at capacity wakes no waiter (Q-04, executed T3).
* **Released × Close (1 cell).** Same as the first pilot: `ignore (accidental)`
  because Close after Release returns nil and closes nothing (T2, T12).
* **IdleTimeout where an idle connection exists (2 cells, new).** The
  baseline treats lazy expiry as `handle` (Active_HasIdle) or `ignore
  (documented)` (at capacity); this run marks an idle connection that ages past
  IdleTimeout with no Get as `ignore (accidental) → Q-13` in Open_IdleAvailable,
  Open_IdleFull and Open_Waiting_Stranded (no timer; the connection stays open
  until a Get receives it). Part B read the same
  behaviour as documented (`part-b-diff.md`, divergence folded into Q-13). The
  code has no timer (expiry is checked at channel.go:115-116 and 141-142 only),
  so both readings describe the same behaviour and differ on whether it is
  intended.

## Finding / question level

| baseline question | routed | match |
|---|---|---|
| Q-01 Release/connReqs leak | Q-01 (executed T1) | matched |
| Q-02 Put integrity (loss, duplicate, foreign) | Q-12 (loss), Q-11 (duplicate, executed T7), Q-10 (foreign, ownership) | matched |
| Q-03 Put after Release | Q-06 (executed T2, T12) | matched |
| Q-04 waiter-path Ping skipped | Q-14 (executed T10) | matched |
| Q-05 FactoryFail handling | Q-17 (fail-fast), Q-19 (nil connection without error, executed T16) | partial; the counter-drift claim is contradicted by the code, as in the first pilot |
| Q-06 Close / openingConns underflow | Q-10 (executed T6: count -1, 2 live connections with MaxCap 1) | matched for duplicate and foreign Close |
| Q-UV-01 Get commission / value | not raised as a question | missed, as in the first pilot |
| Q-07 (to-be) undesired Release variants | Q-06, Q-07; pairs P-01..P-09 | partial |

All six `expected_questions` (Q-01..Q-06) have a routed counterpart; Q-05 only
partly, because its premise is refuted.

New against the baseline: Q-02 waits without bound or cancellation; Q-03
`TestPool_Get` expects `ErrMaxActiveConnReached` and hangs (executed R0); Q-04
lost wake-up on Close (T3); Q-05 a Get/Put interleaving strands a waiter next to
an idle connection (T4, 25 of 3000 iterations); Q-07 Get racing Release; Q-08
unlocked read of the ping function (T5, race detector); Q-09 callbacks under the
mutex (T8 deadlock, T9 450 ms stall); Q-13 lazy expiry; Q-15 InitialCap; Q-16
Len; Q-18 Close-callback errors; Q-20 configuration edge values (MaxCap 0
accepted, T11); Q-21 synchronised reconnects; Q-22 exported Ping panics without
a Ping function (T17); Q-25 age equal to IdleTimeout. Voided control verdicts:
Q-23, Q-24 (Jev scope 0.30 and 0.31 below the provisional 0.5).

Against the first routed pilot: the same primary finding and the same five
substantive divergences from the baseline; the race on `c.ping`, the
re-entrant-callback deadlock and the duplicate-Put handout were already raised
there and are now executed, and the first pilot's Q-03 (enqueue race) is now
Q-05 with an observed interleaving (T4). New in this run: Q-25 (age equal to
IdleTimeout) and the IdleTimeout divergence above. The first pilot's Q-18 (multi-instance) is covered here
by three multi-instance probes in `adversarial-traces.md` without its own
question.

## Executed as-is tests

New in this run (the first pilot's machine did not permit `go test`).
`go test -race -count=1 -timeout 60s ./...` fails: T5 reports the as-is race
(write channel.go:229 in Release, read channel.go:123 in Get), and the
repository's own `TestPool_Get` hangs until the timeout (blocked at
channel.go:137) — before any added test. With `-skip '^TestPool_Get$'`, 22 of
23 as-is tests pass (each PASS observes the claimed as-is behaviour) and all
seven other existing tests pass. Not executed: Q-25's equality case, trace
T-11's race window, and aggregate multi-instance behaviour.

## Cost and time

| | first routed pilot | second routed pilot |
|---|---|---|
| blind to the oracle | no | yes |
| model calls | 15 (6 Flash, 9 Jev) | 20 (7 Flash, 13 Jev) |
| cost | 25,038 µ$ | 22,826 µ$ (Flash 20,751; Jev 2,075) |
| drafted claims, citation failures | 133, 0 | 133, 0 |
| Step-6 orderings backed by Jev | 0 of 6 | 1 of 6 (CT-A, scope 0.58) |
| wall clock | not recorded | about 37 minutes, of which model calls about 70 s |
| model | 7 states (incl. Released_WaitersStranded) | 7 states, 22 events, 154 cells, 1 UNSPECIFIED, 25 questions |
| as-is tests | none (not permitted) | 23 written, 22 observe the claim, 1 race report |

The timed agent-only run of the same component, which the cost comparison
needs, is still open (roadmap entry 11).
