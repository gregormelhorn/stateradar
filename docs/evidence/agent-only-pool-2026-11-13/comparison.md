# Agent-only run vs. benchmark silenceper-pool-32 — comparison

Agent-only run: pack a331dae, prompt v1.17, pool @ 6084537, model routing
OFF, run on 2026-11-13 02:24:30-02:59:04 UTC (`SHAS.txt`, `timing.md`).
Oracle: `tests/benchmarks/silenceper-pool-32/`, the first routed pilot
(`docs/evidence/routed-pilot-2026-11-13/comparison.md`) and the second routed
pilot (`docs/evidence/routed-pilot-2-2026-11-13/comparison.md`), whose
structure and counting rules this file follows. The comparison was written
after the run, outside the run session, by a reviewer who had read the oracle;
the run session had not.

## Blinding

This run was blind to the oracle, like the second pilot.

* The sparse checkout of the pack excluded `docs/`, `tests/benchmarks/`,
  `README.md` and `CHANGELOG.md` (`SHAS.txt`), so neither the benchmark, the
  evidence of either routed pilot nor the roadmap entry was readable. The
  operator brief is not part of the evidence folder, so its wording could not
  be checked here.
* The v1.17 prompt (`prompts/02-pilot.md` @ a331dae) names the first routed
  pilot of silenceper/pool in its changelog (line 6), so the session knew the
  component had been piloted before, and its rule 10 (line 133) says that in
  the first pilot "the task's example race was the benchmark finding". It does
  not describe that race, and the session did not see either pilot's finding.
* No model was routed, so there was no draft task to keep finding-neutral.
  Part B went to a fresh blind subagent that received only the package from
  `part_b_pack.py --for-dispatch` (`analysis/part-b-diff.md`,
  `part-b/part-b-dispatch-package.md`). The diff lists the as-is conclusions
  that leaked into the catalogue prose; agreement on those rows is not
  independent. The RELEASE-with-waiters row is among them ("not cleared, not
  signalled"), so Part B's agreement on the primary finding is not
  independent evidence; Part A found it from the code (`extraction.md`,
  Cancellation paths: "Release does not wake waiters").

## Primary finding

Found: **yes**, independently. Q-05 ("What happens to waiting Gets at
Release?", `analysis/open-questions.md`), with invariant SYS-4, lints L-06,
L-09, L-11, L-12 and traces T-02, P-02b, and **executed**: `as-is-tests.md` T1
logs `observed: waiting Get still blocked 600ms after Release and after a Put`
(PASS in R4, `go-test-outputs/R4-final-skip-TestPool_Get.txt`). Q-05 also
records the Get that races Release at MaxCap and queues itself after Release
(the at-cap test, channel.go:133, precedes the released test, channel.go:150).

Expected phrases in `analysis/open-questions.md`: `waiter` on 14 lines;
`connReqs` on **0 lines**. The questions say "waiter list" and "waiter
channel" throughout; the field name `connReqs` appears only in
`extraction.md` (4 lines), `disposition-matrix.md` (2), `analysis.json` (2)
and `adversarial-traces.md` (1). A scorer that looks for the literal phrase
in the question register counts `connReqs` as missing, although the finding
is the same.

`expected.json` unspecified cells:

| expected | agent-only | match |
|---|---|---|
| Released × Put | Released × PUT = `ignore (accidental) → Q-06` | hole: yes; literal UNSPECIFIED: no |
| Active_IdleExhausted_AtCapacity × Release | Open_Empty_AtCap × RELEASE = transition → Released (no waiter yet; → Q-06 for checked-out conns); Open_Waiting, Open_Waiting_BelowCap and Open_Waiting_IdleStranded × RELEASE = transition → Released, waiters block forever → Q-05 | finding: yes; hole label: no |

As in both routed pilots, the matrix records the observed behaviour with a
question instead of the label `UNSPECIFIED` (this run has no `UNSPECIFIED`
cell at all: 36 holes, all `ignore (accidental)` with a Q link,
`analysis/summary.md`, `analysis.json`). A scorer that requires the literal
label on those two cells counts them as missed. The table lists every
sub-state that shows the finding, including the two that the cell grid below
leaves out.

## Cell-level agreement (aligned base grid, 4 states × 7 events = 28 cells)

The baseline cell values are the agent-only baseline's as-is matrix
(`tests/benchmarks/silenceper-pool-32/analysis.json`, 28 base cells), as
quoted in the first pilot's comparison.

State alignment (this run has 9 states, `analysis/extraction.md`,
`analysis/disposition-matrix.md`): Active_HasIdle ↔ Open_Idle ∪
Open_IdleFull; Active_IdleExhausted_UnderCap ↔ Open_Empty_BelowCap;
Active_IdleExhausted_AtCapacity ↔ Open_Empty_AtCap ∪ Open_Waiting; Released ↔
Released. Left out of the grid and named:

* **Open_Waiting_BelowCap** (waiters while o < MaxCap, reached when Close
  frees capacity without waking anyone) and **Open_Waiting_IdleStranded**
  (waiters while an idle conn exists, reached only through the P-01b
  interleaving). The baseline has no waiter below capacity and no waiter
  next to an idle conn. Their holes are covered by Q-03, Q-04 and Q-05.
* **Open_Creating** (a Get holds `mu` while Factory runs, channel.go:131 …
  154 … 160). Left out as a row. It is not a peer of the baseline states but
  the inside of one baseline cell: it is entered only by a Get below
  capacity (Open_Empty_BelowCap or Open_Waiting_BelowCap × GET), it lasts
  only while that Get holds the mutex, and it is left by the Factory result.
  The baseline reads Get × UnderCap as one event run to completion (`handle`,
  citing the factory call), which includes this step. Every caller event in
  Open_Creating is `defer (queued)` on the mutex (Get, Put, Close, Release,
  Len), which records lock contention, a granularity the baseline does not
  model; folding the row into UnderCap would turn at least four agreeing
  cells (Get, Put, Release, IdleTimeout) into divergences that say nothing
  about behaviour (at most 15 / 28). The row does carry the only Factory
  error that can occur, so the UnderCap × FactoryFail cell uses Open_Creating
  × UV-11 (see below), in the same way as the PingFail column uses Get's
  Ping branch. Its own findings are Q-08 and Q-19 (executed T14, T15).

Events: Get, Put, Close, Release, FactoryFail, IdleTimeout ↔ GET, PUT, CLOSE,
RELEASE, UV-11 FACTORY_ERR, IDLE_TIMEOUT. This run has no separate PingFail
event: a failed Ping is branch "discard" of GET's guard group G-03
(`event-catalogue.md`, Undesired-coverage: "a Ping error is a GET guard
input … not a pool-level event"). The PING column of the matrix is the
exported `Ping` method, not a ping failure. So the PingFail column is compared
against GET's Ping branch. The Factory error is an undesired seam variant
(UV-11); in every state except Open_Creating its cell is `ignore (documented)`
("no Factory result exists in this state"), and in Open_Creating it is
`transition → Open_Empty_BelowCap`, the error returned, o unchanged
(channel.go:155-157).

A cell counts as agreeing when every aligned sub-state agrees. A baseline hole
(`UNSPECIFIED`) against an observed behaviour whose question is `matched` in
the question table below counts as a label-only divergence (`≠ label`); a
`partial` match (FactoryFail, baseline Q-05 vs Q-07) does not.

| baseline state | Get | Put | Close | Release | FactoryFail | IdleTimeout | PingFail |
|---|---|---|---|---|---|---|---|
| Active_HasIdle | = (handle; run: transition → Open_Empty_* / Open_Idle by idle count, guard G-03) | = (handle; run: transition → Open_IdleFull at MaxIdle, else stays; Open_IdleFull: handle, closes) | = handle | = transition → Released (→ Q-06 checked-out conns) | **≠** handle vs ignore (documented) | **≠** handle vs ignore (accidental) → Q-12 | = (discard via Close, retry; G-03) |
| Active_IdleExhausted_UnderCap | = (handle; run: transition → Open_Creating, Factory call) | = transition → idle (Open_Idle) | **≠** UNSPECIFIED Q-06 vs handle | = transition → Released | **≠** UNSPECIFIED Q-05 vs transition → Open_Empty_BelowCap, error returned (Open_Creating × UV-11) | = ignore (documented) | = ignore (documented: no idle conn, no Ping on the create path) |
| Active_IdleExhausted_AtCapacity | = (defer; run: transition → Open_Waiting / handle, appended) | = (handle; run: transition → Open_Idle / hand-off to the oldest waiter) | **≠** UNSPECIFIED Q-06 vs transition (Open_Empty_AtCap → Open_Empty_BelowCap; Open_Waiting → Open_Waiting_BelowCap, no wake-up → Q-03) | **≠ label** UNSPECIFIED Q-01 vs transition → Q-05 | **≠** UNSPECIFIED Q-05 vs ignore (documented) | = ignore (documented: no idle conn) | = (hand-off path skips Ping → Q-13, as in both pilots) |
| Released | = reject | **≠ label** UNSPECIFIED Q-03 vs ignore (accidental) → Q-06 | **≠** ignore (documented) vs ignore (accidental) → Q-06 | = ignore (documented) (run adds Q-20: no requirement states it) | = ignore (documented) | = ignore (documented) | = ignore (documented) (Get rejects before any Ping) |

Convergent **19 / 28** (68 %); divergent **9**, of which **2 are
label-only** (the same hole, recorded as observed behaviour with a question).
The nine divergent cells are the same nine as in the second routed pilot
(19 / 28). First routed pilot: 21 / 28 as published, 20 / 28 under the rule
above (it counted Released × Put as agreeing). The baseline's own
`CONVERGENCE.md` reports 28 / 28 between its two agent-only runs.

Divergences, assessed against channel.go @ 6084537 (cloned for this
comparison, not part of the repository):

* **FactoryFail (3 cells).** Both pilots had the same three. The baseline
  rests on counter drift after a factory failure (its Q-05); the code
  increments only after success (channel.go:155-159) and does not call the
  factory at the cap (channel.go:133). This run: with idle conns and at the
  cap, `ignore (documented)`; below the cap, the error is returned and the
  pool goes back to Open_Empty_BelowCap. All three match the code. One
  nuance: a Get that starts with idle conns can still reach the factory if it
  discards every idle conn (expired or Ping-failed, channel.go:115-126) and
  then falls into the create branch; this run models that as passing through
  Open_Empty_BelowCap and Open_Creating, the baseline as `handle` in
  Active_HasIdle. Same behaviour, different state attribution.
* **Close below and at capacity (2 cells).** Same as both pilots. The base
  Close decrements and calls the callback (channel.go:211-212); misuse is
  modelled as variants (UV-04 CLOSE_DUP, UV-08 CLOSE_FOREIGN → Q-09, executed
  T5: `MaxCap=2, live conns=3`; T6), and Close at capacity wakes no waiter
  (channel.go:202-213 has no wake-up; Q-03, executed T2).
* **Label-only (2 cells).** Released × Put and Active_IdleExhausted_AtCapacity
  × Release: the baseline hole is recorded as the observed behaviour with its
  question (Q-06, Q-05), as described under the primary finding.
* **Released × Close (1 cell).** Same as both pilots: `ignore (accidental) →
  Q-06`, because Close after Release returns nil and closes nothing
  (channel.go:208-209; executed T4), against the doc comment "Close
  关闭单条连接" (close a single connection, channel.go:201; contradiction C-4).
* **IdleTimeout with idle conns (1 cell).** Same as the second pilot: an idle
  conn that ages past IdleTimeout with no Get stays open and counted
  (`ignore (accidental) → Q-12` in Open_Idle and Open_IdleFull; executed T13:
  `100ms past expiry closes=0, Len=2`). The code has no timer (expiry is
  checked at channel.go:115-116 and 141-142 only). The baseline's `handle`
  describes the same lazy check; the readings differ on whether it is
  intended.

## Finding / question level

| baseline question | agent-only | match |
|---|---|---|
| Q-01 Release/connReqs leak | Q-05 (executed T1) | matched |
| Q-02 Put integrity (loss, duplicate, foreign) | Q-16 (loss), Q-09 (duplicate Put, executed T7; foreign Put and Close, executed T6) | matched |
| Q-03 Put after Release | Q-06 (executed T3, T4) | matched |
| Q-04 waiter-path Ping skipped | Q-13 (executed T18: `waiter received the dead conn; Ping calls=0`) | matched |
| Q-05 FactoryFail handling | Q-07 (Factory result shapes: (conn, err) leaks the conn, executed T8; (nil, nil) loses a slot, executed T9), Q-18 (no backoff) | partial; the counter-drift claim is contradicted by the code, as in both pilots |
| Q-06 Close / openingConns underflow | Q-09 (executed T5, T6) | matched for duplicate and foreign Close; the "close after Release drives the counter negative" part is contradicted (channel.go:208-209 returns before the decrement) |
| Q-UV-01 Get commission / value | not raised; the undesired-coverage table assigns caller commission to UV-07, UV-08 (Put and Close) and value to UV-09, UV-10 | missed, as in both pilots |
| Q-07 (to-be) undesired Release variants | Q-20 (second Release, from Part B), Q-05, Q-06; pairs P-02, P-03, P-06, P-09 | partial |

All six `expected_questions` (Q-01..Q-06) have a counterpart; Q-05 only
partly, because its premise is refuted.

New against the baseline: Q-01 Get at MaxCap waits although the error
`ErrMaxActiveConnReached` exists, the repository's `TestPool_Get` expects it
and hangs (R0, R5), and MaxCap = 0 is accepted (executed T17); Q-02 waits
without bound or cancellation, `waitTimeOut` unused; Q-03 lost wake-up on
Close and barging by new Gets (T2); Q-04 a Get/Put interleaving strands a
waiter next to an idle conn (T10: 3 in 558 runs, R3: 3 in 1040); Q-08
callbacks under the mutex, re-entry deadlocks (T14); Q-10 unlocked read of
`c.ping` (T11 and the repository's TestPoolConcurrent under `-race`, R0b);
Q-11 exported `Ping` panics without a Ping function and after Release (T12);
Q-12 lazy expiry, age equal to IdleTimeout, meaning of IdleTimeout ≤ 0 (T13);
Q-14 InitialCap called a minimum but never replenished (T16); Q-15 Len
counts idle conns only; Q-17 Close-callback errors discarded; Q-19 Factory
runs under the mutex and blocks Put (T15: `Put blocked 352ms`); Q-20 is a
second Release a documented no-op (Part B divergence).

Against the second routed pilot: the same primary finding, the same nine
divergent cells and largely the same new questions under other numbers
(pilot 2 → this run: Q-03 → Q-01, Q-04 → Q-03, Q-05 → Q-04, Q-08 → Q-10,
Q-09 → Q-08/Q-19, Q-13 and Q-25 → Q-12, Q-20 → Q-01, Q-21 → Q-18, Q-22 →
Q-11). Not raised here: pilot 2's Q-07 as a separate question (Get racing
Release; here inside Q-05, Q-06 and Q-10) and its voided control verdicts
Q-23, Q-24 (a routing artefact). New here: Q-07's (conn, err) case, which
leaks the conn (T8), and Q-20.

## Executed as-is tests

18 as-is tests written (`as-is-tests.md`, `go-tests/asis_test.go`); in the
final run R4 (`go test -race -count=1 -timeout 60s -v -skip
'^TestPool_Get$' ./...`) 17 PASS (each PASS observes the claimed as-is
behaviour) and T11 FAILs as expected with the race report (`WARNING: DATA
RACE`, write channel.go:229 in Release, read channel.go:123 in Get). All 8
other repository tests PASS in R4 (25 PASS lines in
`go-test-outputs/R4-final-skip-TestPool_Get.txt` = 17 as-is + 8 repository),
including TestPoolConcurrent, which in R0b (repository tests only, same
flags) FAILs under `-race` with the same racing pair (7 PASS, 1 FAIL,
`R0-repo-tests-skip-TestPool_Get.txt`) and PASSes without `-race` (R0c).
`as-is-tests.md` infers that the detector reports a pair once per process and
T11 ran first in R4; not verified. The full command, R0 before any added test
and R5 with the final file, hangs on the repository's `TestPool_Get` until
the 60 s timeout (`panic: test timed out after 1m0s`, `TestPool_Get` running,
blocked at channel.go:137; `R0-repo-tests-full.txt`, `R5-final-full.txt`).
T10 failed in R1 and R2 (test-design errors, documented) before the v3 stress
loop observed the state. Not executed: Q-02 (only indirectly, by T1, T2,
T17 blocking), Q-15, Q-16, Q-17, Q-18.

## Cost and time

| | first routed pilot | second routed pilot | agent-only run |
|---|---|---|---|
| blind to the oracle | no | yes | yes |
| model calls | 15 (6 Flash, 9 Jev) | 20 (7 Flash, 13 Jev) | none |
| routed cost (model calls) | 25,038 µ$ | 22,826 µ$ (Flash 20,751; Jev 2,075) | 0 µ$ |
| steering-agent usage | not measured | 84 messages; input 168, cache write (1 h) 425,616, cache read 26,100,528, output 210,476 | main: 77 messages; input 160, cache write (1 h) 400,769, cache read 23,584,230, output 205,780. Blind subagent: 1 message; input 2, cache write (5 min) 55,079, cache read 35,416, output 10,730 (101,227 tokens, as `timing.md` records) |
| steering-agent cost | not measured | $12.84 | $12.54 (main $12.04, subagent $0.50) |
| total cost | not measured | $12.86 | $12.54 |
| wall clock | not recorded | about 37 minutes (00:41:01 to about 01:18) | 34:34 (02:24:30 → 02:59:04) |
| of which model calls | not recorded | about 70 s (68 s summed from the `local_models` rows, incl. the 20 s Flash blind run) | none |
| of which go test | not permitted | about 3.5 minutes (207 s: three full runs of 73, 62, 62 s that each hang on `TestPool_Get`, plus 4 and 6 s) | 2:25 (145 s: R0 62, R0b 2, R0c 2, R1 5, R2 4, R3 3, R4 6, R5 61; R0 and R5 are the `TestPool_Get` hangs) |
| of which checkers | not recorded | not recorded separately (inside agent work) | about 3 s (12 checker and `part_b_pack.py` rows at 1 s resolution; nine read 0 s) |
| of which blind subagent | n/a (Flash blind run) | n/a (counted under model calls) | 1:36 (96 s; the subagent reports 96,231 ms) |
| of which agent work (remainder) | not recorded | about 32 minutes | 30:30 (1,830 s) |
| model | 7 states, 22 events, 154 cells, 2 UNSPECIFIED, 24 ignore (accidental), 23 questions (`routed-pilot-2026-11-13/channelPool/analysis.json`) | 7 states, 22 events, 154 cells, 1 UNSPECIFIED, 22 ignore (accidental), 25 questions | 9 states, 27 events (9 base + 18 UV), 243 cells, 0 UNSPECIFIED, 36 ignore (accidental), 20 questions |
| as-is tests | none (not permitted) | 23 written, 22 observe the claim, 1 race report | 18 written, 17 observe the claim, 1 race report (T11) |

Prices (claude-opus-5-5, per MTok): input $4, output $20, cache read $0.20,
cache write $8 (1-hour TTL) or $5 (5-minute TTL). Steering-agent usage is
summed `message.usage` per distinct `message.id` from the session transcripts
under `~/.claude/projects` on the run machine (measured by the coordinator;
the per-row arithmetic was re-checked here). The first pilot's transcript was
not checked. Wall-clock splits for this run are computed from the tool-time
rows of `timing.md`, which do not overlap; the second pilot's from its
`timing.md`, whose end time (about 01:18) is taken from its comparison,
because the packaging row has no end time.

## What this says

One run each, so differences of a few minutes or a few cells are not a
measured effect. On this pair, routing did not save wall clock: the routed run
took about 37 minutes, the agent-only run 34:34. The routed run spent only
about 70 s in model calls; the gap of about 2.5 minutes comes from go test
(three 60 s hangs against two) and agent work (about 32 minutes against 30:30
plus the 1:36 blind subagent), and is within what one run each can show.
Routing as configured did not lower total cost either. The steering agent is
about 99.8 % of the routed run's cost ($12.84 of $12.86), its usage was about
the same as the agent-only run's (84 against 77 + 1 messages; 26.1 M against
23.6 M cache-read tokens), and the routed run cost $12.86 against $12.54. The
results agree where they can be compared: the primary finding was found and
executed in both, the grid agrees on 19 / 28 cells with the same nine
divergences, and the question sets overlap almost entirely. The agent-only
run's model is larger (9 states, 243 cells), and its question register never
uses the expected phrase `connReqs`.
