# channelPool — summary

model routing: on (unevaluated, cascade plan stage 3)

Component: `channelPool` (channel.go) of github.com/silenceper/pool at 6084537e520652192f41aebfd88d822c00b9447a. Pilot prompt: `prompts/02-pilot.md` v1.17, pack a331daece7981b93846aca568a280128b486118a. Maturity: **L1–L2 analysis** (extraction, model, matrix, questions, sidecar with green `dsc_check`); no decisions, no cell tests — below L3, so "green means conforming" does not apply.

## Summary count (Step 7)

states 7 / events incl. undesired variants 22 (6 base + 16 undesired) / interaction pairs 9 (18 orderings) / matrix cells 154 / UNSPECIFIED 1 / accidental ignores 22 / guard groups proven 8 / guard violations 0 / not-formalizable 1 / findings 25 / open questions 25

Dispositions (from `analysis.json`): handle 75, ignore (documented) 30, ignore (accidental) 22, transition 21, reject 5, UNSPECIFIED 1. Holes: 23 cells, all linked to Q-01, Q-02, Q-06, Q-07, Q-12, Q-13.

Questions by trigger: step-3 checklist 4, doctrine mapping 4, step-1 extraction 3, step-4 matrix walk 2, adversarial trace 2, step-3 lock-discipline annotation 2, seam-contract sweep 2, jev check 2, step-5 lint 1, step-2 test replay 1, multi-instance probes 1, part-B diff 1. Questions added by a model judgment: Q-23 and Q-24 (Jev scope probabilities 0.30 and 0.31 voided my "yes" scope lines). Questions Flash raised independently in Step-1 drafts (also found by my own pass): Q-01, Q-02, Q-06, Q-07, Q-09, Q-22.

Headline findings (details and executed evidence in `open-questions.md` and `as-is-tests.md`):

* Release leaves blocked Gets blocked forever; `ErrMaxActiveConnReached` is unreachable (Q-01).
* The existing test `TestPool_Get` expects `ErrMaxActiveConnReached` at capacity; the code waits, so the suite hangs until the test timeout (Q-03).
* Close at capacity wakes no waiter (lost wake-up; state `Open_Waiting_Stranded`) (Q-04); a Get/Put interleaving reaches the same state (Q-05).
* Put/Close after Release return nil and close nothing; connections checked out at Release leak (Q-06); Get racing Release has timing-dependent outcomes (Q-07); unlocked read of `c.ping` races with Release (Q-08).
* Factory and Close callbacks run under the pool mutex: stalls and re-entry deadlock (Q-09).
* No ownership tracking: duplicate/foreign Close drives the open count negative and allows more than MaxCap live connections (Q-10); duplicate Put hands one connection to two callers (Q-11).

## Steps and artefacts

| Step | Artefact |
|---|---|
| 0, 1 | `extraction.md` (scope, extraction, seam-contract sweep, 20 doctrine lines, draft review, draft-question dispositions) |
| 2 | `as-is.machine.mmd`, `as-is-validation.md` |
| 3 | `event-catalogue.md` |
| 4 | `disposition-matrix.md`, `check_matrix.py`, `check_guards.py`, `guard-results.txt` |
| 5 | `invariants-and-lints.md`, `check_invariants.py`, `invariant-results.txt` |
| 6 | `adversarial-traces.md` (18 pair traces, 15 free probes, 3 multi-instance probes) |
| 7 | `open-questions.md`, this file |
| 8 | updates in place; verification record below |
| Part B | `part-b-contracts.md` (blind input), `part-b-diff.md` |
| sidecar | `analysis.json` (generator + `merge_sidecar.py`), `manifest.json` |

## Checker runs (pasted output, final state)

```text
$ python3 domain-analysis/channelPool/check_matrix.py
CHECK MATRIX: OK (7 rows x 22 events)
$ python3 ../pack/tools/dsc_check.py domain-analysis/channelPool --repo . --model as-is.machine.mmd
DSC CHECK: OK (7 states x 22 events, 154 cells, 9 guard groups)
$ python3 ../pack/tools/check_reachability.py domain-analysis/channelPool
REACHABILITY CHECK: OK (7/7 states reachable from 'Open_IdleAvailable', 1 terminal)
$ python3 domain-analysis/channelPool/check_guards.py   (first 12 lines; full output in guard-results.txt)
group G-01 construction validation: proven
group G-02 idle-expiry decision: proven
group G-04 Get slow path: proven
group G-05 waiter wake-up: proven
group G-06 Put routing: proven
group G-07 Close routing: proven
group G-08 Release routing: proven
group G-09 Get entry: proven
group G-03 ping validity: not-formalizable: external-call: the branch depends on the user Ping callback result (channel.go:123-124)
G-01 implication valid => MaxIdle>=0 and MaxCap>=InitialCap>=0: proven
G-01 witness: MaxCap == 0 accepted by validation: yes [InitialCap = 0, MaxIdle = 0, MaxCap = 0]
G-04 ordering: released (factoryNil) and at capacity selects 'wait', not 'ErrClosed': witness [maxActive = 0, openingConns = 0, factoryNil = True]
$ python3 domain-analysis/channelPool/check_invariants.py
SYS-1 under E-CLOSE without NAT-4 (foreign or duplicate Close): violation, witness [waiters = 0, MaxCap = 0, checkedOut' = 0, MaxIdle = 0, openingConns' = -1, idle = 0, openingConns = 0, checkedOut = 0]
SYS-1 and SYS-2 under E-CLOSE with NAT-4: preserved (unsat)
SYS-2 under UV-PUT-FOREIGN (enqueue): violation, witness [MaxCap = 1, checkedOut' = 0, MaxIdle = 1, openingConns' = 0, idle' = 1, idle = 0, openingConns = 0, checkedOut = 0, waiters = 0]
SYS-1 and SYS-2 under E-GET create: preserved (unsat)
live connections <= MaxCap after foreign Close then Get create: violation, witness [waiters = 0, MaxIdle = 0, liveConns' = 2, o_after_get = 1, idle = 0, liveConns = 1, o_after_close = 0, openingConns = 1, checkedOut = 1, MaxCap = 1]
SYS-3 under E-CLOSE with waiters (NAT-4 holds): violation, witness [MaxCap = 1, waiters = 1, checkedOut' = 0, MaxIdle = 0, openingConns' = 0, idle = 0, waiters' = 1, openingConns = 1, checkedOut = 1]
SYS-3 under E-PUT handoff (one waiter leaves): preserved (unsat)
```

Red runs during the pilot, and what changed (all outputs in the evidence bundle `checker-runs/`):

1. `check_matrix.py` before `open-questions.md` existed: 23 "hole cell: Q-nn not in open-questions.md" errors (expected Stage-1/Stage-2 split; Stage-1 checks were already clean).
2. `dsc_check.py` red probe: one citation fragment deliberately corrupted in a throw-away copy → `DSC CHECK: FAIL - citation: fragment 'c.openingConns -= 2' not near channel.go:211`. Shows the fragment check is live.
3. `check_reachability.py` first run: FAIL — five states unreachable from `Open_IdleAvailable`, and `Released` "has no outgoing transitions and is not marked terminal". Both were modelling defects of the artefact, fixed in the artefact, not in the checker: (a) `Released` is terminal under PA-18, so it is now declared (`<!-- terminal: Released -->`) with its explicit row kept; (b) five guarded cells said `handle` although one branch changes state; they now name the state-changing branch as `transition → …` and keep the staying branch in the cell text (abstraction statement updated). Behaviour of every cell unchanged. Rerun: OK.
4. A citation sweep over all artefacts (`checker-runs/06-all-artifact-citations.txt`) first reported 3 misses — formatting of my English glosses inside the quote, not wrong citations; fixed: 255/255 fragments found.

## Step 8 — finding verification

1. **Concurrency claims, with the synchronisation primitive.**
   * Q-01: the only `close(` in channel.go is on `conns` (channel.go:238); request channels are only received (channel.go:137) and sent once (channel.go:183). No primitive wakes a waiter on Release. Confirmed bug (liveness). Executed T1.
   * Q-04: Close holds `mu` (channel.go:206-207) and touches only `openingConns` and the callback; the waiter's only wake-up is a send on its request channel, done only by Put (channel.go:183). Confirmed. Executed T3.
   * Q-05: the receive at channel.go:110 and the `default` at channel.go:130 run without `mu`; `mu` is taken at channel.go:131. The window between them admits a complete Put (channel.go:172-192). Ordering is not prevented by any primitive. Confirmed as a reachable interleaving (inferred; T4 is statistical).
   * Q-07: the channel snapshot is read under `mu` (channel.go:96-98) and then used without it; Release's clearing (channel.go:225-232) and `close(conns)` (channel.go:238) are separate steps. Confirmed.
   * Q-08: read of `c.ping` at channel.go:123 holds no lock; the write at channel.go:229 holds `mu`. No happens-before edge → data race under the Go memory model. Confirmed; race detector output in `as-is-tests.md` T5.
   * Q-09: `sync.RWMutex.Lock` is not re-entrant (Go documentation; NAT-8 class language contract); Factory at channel.go:154 and the Close callback at channel.go:212 run with `mu` held. Confirmed; T8 executes the deadlock.
   * Q-10/Q-11: no atomic or ownership structure guards the count; every path is under `mu` (no lost update), so the defect is semantic (missing ownership), not a race. Severity kept as API-contract issue.
2. **Sentinel values.** `nil` is the released sentinel for `conns`, `factory`, `ping`, `close` — literal assignments (channel.go:227-231), safe as sentinels; but `close == nil` doubles as "released" inside Close and turns late Close/Put into silent no-ops (Q-06). `openingConns` is computed (fragile; Q-10). `ErrMaxActiveConnReached` is a literal sentinel returned on a branch no code reaches (Q-01, Q-03).
3. **Line-number accuracy.** Every cited `file:line` was re-read; the sweep found 255/255 fragments within ±3 lines. Jev ordered the re-reading: `jev-batch` claim checks for channel.go (37 claims), channel_rpc_test.go (6), README.md (6), pool.go (2): 44 supported, 5 unclear, 2 contradicted. Re-read of each non-supported claim (routing rule 2), all kept:
   * V-02 (contradicted 0.48): the fragment `case wrapConn := <-conns:` alone does not show the `default` at channel.go:130 that makes the receive non-blocking; re-read channel.go:109-130 — the claim holds.
   * V-08 (contradicted 0.65): the fragment at channel.go:133 cannot show the released test, which is at channel.go:150, outside the ±3 window; re-read both lines — the order holds; z3 G-04 ordering witness.
   * V-15 (unclear): no nil check of the factory result between channel.go:154 and channel.go:161 — holds; executed T16.
   * V-24 (unclear): channel.go:206-212 touch no waiter structure — holds; executed T3, T6.
   * V-34 (unclear): channel.go:59 accepts MaxCap 0 with InitialCap = MaxIdle = 0 — holds; z3 G-01 witness; executed T11.
   * V-41 (unclear): channel_rpc_test.go:191-204 contain no Put, Close or Release — holds.
   * V-43 (unclear): channel_rpc_test.go:257-258 set no Ping field and IdleTimeout 20 s — holds.
   No claim was dropped on Jev's answer. Jev added no question in Step 8.
4. **Severity recalibration.**

| Q | Class |
|---|---|
| Q-01, Q-04, Q-05, Q-07, Q-08 | bug (liveness or race) |
| Q-14 | bug against a doctrine line (DOC-3) |
| Q-03 | test/code contradiction (one of them is wrong) |
| Q-06, Q-10, Q-11, Q-19, Q-22 | API-contract issue (PA-20; Q-22 outside the matrix) |
| Q-09, Q-02, Q-21 | design observation with a documentation gap |
| Q-12, Q-13, Q-15, Q-16, Q-17, Q-18, Q-20, Q-23, Q-24, Q-25 | documentation gap |

No finding was removed. One drafted claim (example/main.go C13, duplicate of C12) was dropped in Step 1.

## Reviewer findings outside scope

No separate Step-7a review was run. Test-quality observations (outside the statechart): TestPool_Put prints "Expecting 1" while asserting MaxIdleCap (channel_rpc_test.go:121-123); TestPool_Close asserts internal fields (F-21, channel_rpc_test.go:148); TestPoolConcurrent and TestPoolConcurrent2 assert nothing; TestNew defers Release before checking the constructor error (channel_rpc_test.go:38-39); the example continues with a nil pool after a constructor error (example/main.go:47-52).

## Model routing record

* Step 1: six `draft-verify` calls (README.md, README_ZH_CN.md, channel.go, pool.go, channel_rpc_test.go, example/main.go), task files finding-neutral. 6 drafts, 0 rejected, 0 truncated, 133 drafted claims, 0 citation failures, Jev on all 133 claims (124 supported, 9 unclear, 0 contradicted), 84 draft questions — every one carried forward to a Q or a reasoned disposition (`extraction.md`).
* Step 6: three `jev-batch` ordering batches (README.md: CT-A, CT-E, CT-F; channel.go: CT-B, CT-C; pool.go: CT-D), scope decisions written before the calls. CT-A backs my "yes" (supported, scope 0.58). CT-B and CT-C: supported but scope 0.30 / 0.31 < 0.5 → my "yes" voided, Q-23 and Q-24 raised. CT-D, CT-E, CT-F: my "no" (Jev unclear, scope 0.02–0.05) → verdicts void, folded into Q-06, Q-06, Q-13. No check re-run.
* Step 8: four `jev-batch` claim batches, 51 checks (above).
* Part B: `blind --package-only`, package read, then `blind` (Flash): finished, coverage OK. Classified in `part-b-diff.md`.
* Failed or skipped model calls: **none**. Every call exited 0; no provider error, no ledger error, no `not run`.

## Prompt and tool problems hit (also in the evidence report)

1. Routing rule 6 names two outcomes for a draft question (a Q or a fold into an existing Q). Many draft questions were answered by the code itself, were outside scope (test text, example quality), or (pool.go draft, 11 questions) were meta-questions answered by another file. I recorded them as reasoned dispositions ("answered: …", "outside scope: …"); the rule has no word for them.
2. `tools/templates/check_matrix.py` locates the pack at `parents[3]/"stateradar"`; this checkout is named `pack`, so the copied wrapper needed its PACK path edited (the template says to adjust it).
3. `gen_analysis_sidecar.py` does not carry `pairs`, `guardGroups`, or the ODC fields (`fault`, `trigger`) of questions; a per-run `merge_sidecar.py` lifts them from `adversarial-traces.md`, `guard-results.txt`, `open-questions.md`.
4. `part_b_pack.py`'s citation stripper leaves bare line numbers that follow a citation ("unlock at 136, 151, 156 or 160", ", 194"); the sent package carried them. The catalogue now writes full citations there.
5. `blind` writes the coverage-check line (`PART-B COVERAGE: OK …`) to stdout after the JSON, so its stdout is not one JSON document.
6. The assembled Part-B task text keeps a stray `>` line from the prompt's blockquote (package line 4).
7. `check_reachability.py` (in the pack, listed in AGENTS.md §5) is not named in 02-pilot Step 4; I ran it and it found two real modelling defects (above). It derives reachability from `transition` cells only and assumes the first state is the single initial state — the matrix's abstraction statement now follows that.
8. `docs/local-model-routing.md`, referenced by the routing section, is outside this run's sparse checkout by instruction; not read.

## Ledger

Ledger file: `ledger.db` (one pilot ledger, limit 1,000,000 µ$). `local_models.py --ledger ledger.db status` after the last model call:

```json
{
  "committed_or_reserved_microdollars": 22826,
  "limit_microdollars": 1000000,
  "calls": [
    {
      "id": 1,
      "provider": "deepseek-flash",
      "amount_microdollars": 2095,
      "status": "settled"
    },
    {
      "id": 2,
      "provider": "jev",
      "amount_microdollars": 172,
      "status": "settled"
    },
    {
      "id": 3,
      "provider": "deepseek-flash",
      "amount_microdollars": 2016,
      "status": "settled"
    },
    {
      "id": 4,
      "provider": "jev",
      "amount_microdollars": 182,
      "status": "settled"
    },
    {
      "id": 5,
      "provider": "deepseek-flash",
      "amount_microdollars": 4980,
      "status": "settled"
    },
    {
      "id": 6,
      "provider": "jev",
      "amount_microdollars": 433,
      "status": "settled"
    },
    {
      "id": 7,
      "provider": "deepseek-flash",
      "amount_microdollars": 850,
      "status": "settled"
    },
    {
      "id": 8,
      "provider": "jev",
      "amount_microdollars": 57,
      "status": "settled"
    },
    {
      "id": 9,
      "provider": "deepseek-flash",
      "amount_microdollars": 3022,
      "status": "settled"
    },
    {
      "id": 10,
      "provider": "jev",
      "amount_microdollars": 319,
      "status": "settled"
    },
    {
      "id": 11,
      "provider": "deepseek-flash",
      "amount_microdollars": 1500,
      "status": "settled"
    },
    {
      "id": 12,
      "provider": "jev",
      "amount_microdollars": 134,
      "status": "settled"
    },
    {
      "id": 13,
      "provider": "jev",
      "amount_microdollars": 79,
      "status": "settled"
    },
    {
      "id": 14,
      "provider": "jev",
      "amount_microdollars": 116,
      "status": "settled"
    },
    {
      "id": 15,
      "provider": "jev",
      "amount_microdollars": 28,
      "status": "settled"
    },
    {
      "id": 16,
      "provider": "jev",
      "amount_microdollars": 325,
      "status": "settled"
    },
    {
      "id": 17,
      "provider": "jev",
      "amount_microdollars": 127,
      "status": "settled"
    },
    {
      "id": 18,
      "provider": "jev",
      "amount_microdollars": 76,
      "status": "settled"
    },
    {
      "id": 19,
      "provider": "jev",
      "amount_microdollars": 27,
      "status": "settled"
    },
    {
      "id": 20,
      "provider": "deepseek-flash",
      "amount_microdollars": 6288,
      "status": "settled"
    }
  ]
}
```

Failed or skipped model calls: none.
