# channelPool — Pilot summary (agent-only run)

* Component: `channelPool` (channel.go, pool.go) of github.com/silenceper/pool @ `6084537e520652192f41aebfd88d822c00b9447a`
* Pack: stateradar @ `a331daece7981b93846aca568a280128b486118a`, prompt 02-pilot v1.17
* **model routing: not configured** (agent-only baseline: routing OFF by instruction, `tools/local_models.py` was never called, no DeepSeek or Jev call). Steps 1, 6 and 8 were done by the pilot agent. Part B went to a fresh blind subagent, as the Part-B dispatch notes describe.
* Maturity: L1/L2 analysis with an L4-style sidecar (dsc_check green). Below L3 (no cell tests yet), so "green means conforming" does **not** apply.

## Counts (Step 7 format)

| states | events incl. undesired variants | interaction pairs | matrix cells | UNSPECIFIED | accidental ignores | guard groups proven | guard violations | not-formalizable | findings | open questions |
|---|---|---|---|---|---|---|---|---|---|---|
| 9 | 27 (9 base + 18 UV) | 9 (18 orderings) | 243 | 0 | 36 | 8 | 1 (G-09) | 0 | 19 Part A + 1 Part B (one per question); 8 SYS invariants violated, 11 lint items with findings, 6 code/test/doc contradictions | 20 |

Cell dispositions (from analysis.json): handle 80, ignore (documented) 55, transition 37, ignore (accidental) 36, defer (queued) 25, reject 10. Holes = 36 (all `ignore (accidental)`, each with a Q link).

Part B: 62 blind rows → convergent 22, convergent-hole 33, divergence 5, pass-B-blind-spot 1, artefact 0, reference-only 1. Every divergence is closed (Q-03, Q-12 folded; Q-20 new).

As-is tests: 18 written (`as-is-tests.md` in the evidence folder). 17 confirm their claim with PASS; T11 confirms by the expected race-detector FAIL. The repository's TestPool_Get hangs (timeout 60 s).

## Checker outputs (final run, `checker-outputs/all-checkers-run4-final.txt`)

```text
CHECK MATRIX: OK (9 rows x 27 events)
check_guards: G-01..G-08 proven, G-09 violation (PA-2 gap: no guard fires, witness connIsNil=False, pingConfigured=False) — a finding (Q-11); script exits 1 on a violation
OK channelPool: 9 states x 27 events = 243 cells, 20 questions, DRs []
merged: 18 pairs, 9 guard groups, ODC fields on 20 questions
DSC CHECK: OK (9 states x 27 events, 243 cells, 9 guard groups)
REACHABILITY CHECK: FAIL — state 'Open_Waiting_IdleStranded' is unreachable from initial state 'Open_Idle'   (optional checker, see below)
PART-B COVERAGE: OK (27 events, 18 pair orderings)
```

dsc_check was run as `uv run --with-requirements stateradar/tools/requirements-dev.txt python3 stateradar/tools/dsc_check.py pool/domain-analysis/channelPool --repo pool --model as-is.machine.mmd`. The system python3 has neither z3 nor jsonschema (`ModuleNotFoundError: No module named 'z3'`).

## Step-8 verification: corrections and reclassifications

* **Corrected (modelling error).** Every Get takes the mutex first in `getConns` (channel.go:96, channel.go:104) before it looks at the idle store. The first matrix draft said that during Open_Creating "an idle conn, if any, is taken without the mutex" and that a re-entrant Factory Get "finds an idle conn". Both are wrong. Fixed in Open_Creating x GET, Open_Creating x UV-17, UV-12/UV-16 cells, the catalogue lock-discipline annotation, L-12, Q-08 and Q-19. Found because as-is test T10 v1 queued its Get in getConns.
* **Corrected (reachability checker).** Cells whose target depends on a count (last idle conn, last free idle slot, last waiter, o+1 vs X) were written as `handle`, which hid the boundary transitions. They are now guarded transitions (Open_Idle x GET/PUT, Open_Waiting*/x PUT, Open_Creating x FACTORY_OK), and Released is declared terminal with its explicit hole row kept.
* **Verified by execution.** Lost wake-up on Close (T2), stranded waiter with an idle conn (T10, real concurrent calls, 3 strands in 1040 and in 558 runs), waiters blocked after Release (T1), the data race on `c.ping` (race detector: R0b, T11), Put/Close after Release closing nothing (T3, T4), count drift past MaxCap (T5, T6), duplicate hand-out (T7), the Factory result shapes (T8, T9), the nil-function panic in `Ping` (T12), lazy expiry (T13), callback deadlocks (T14), Put blocked by a slow Factory (T15), no replenishment (T16), MaxCap = 0 (T17), hand-off without Ping (T18).
* **Concurrency claims: synchronization cited.** Q-03, Q-04, Q-05 rest on the mutex lock sites (channel.go:131, 172, 206, 225) and on the absence of any waiter wake-up other than Put's send (channel.go:183) and of any `close(req)`. Q-10: the read at channel.go:123/220 has no lock and the write at channel.go:229 is under the lock. That is a data race in the Go memory model, confirmed by the race detector. The nil-function panic it can cause is scheduling-dependent and was not forced: **unverifiable-runtime** (PA-19).
* **Sentinels.** The closed-channel nil (channel.go:111) is a literal sentinel, so it is safe. `openingConns` is a computed counter, so it is fragile: that is the basis of Q-09.
* **Severity recalibration.** Bug (behaviour contradicts docs or tests, or loses progress): Q-01, Q-03, Q-04, Q-05, Q-06, Q-10, Q-13. API-contract issue (PA-20): Q-07, Q-09, Q-11, Q-15. Design observation: Q-02, Q-12, Q-16, Q-17, Q-18, Q-19. Documentation gap: Q-08, Q-14, Q-20. No finding was dropped as wrong.

## Reviewer findings outside scope (Step 7a not run)

Not run (optional; no separate traditional review in this run). Out-of-statechart observations: `go vet` reports `example/main.go:18:2: misuse of unbuffered os.Signal channel as argument to signal.Notify` (example program, excluded from scope). In the tests, TestNew calls `defer p.Release()` before checking `err`, and TestPoolConcurrent has no assertion.

## Tool and prompt problems met in this run

1. **gen_analysis_sidecar.py — phantom event from a prose table.** A prose table in the matrix whose first header cell is "State" (`| State | Condition |`) is parsed as a matrix sub-table header. Exact output: `OK channelPool: 9 states x 28 events = 243 cells, 19 questions, DRs []`, with phantom event id `Condition`. No error is reported. Worked around by renaming the header to "Leaf".
2. **gen_analysis_sidecar.py — doctrine table bleed.** `_parse_doc_map` reads every `| DOC-` row up to the next `\n## `, including a `###` sub-section's table. dsc_check then failed with e.g. `schema: docLines/20/mapping: 'Open_Empty_AtCap x GET' is not one of ['cell', 'invariant', 'constraint', 'rejected', 'structural', 'guard']` and `doctrine: DOC-15, DOC-16 mapped but not declared in doc-ids`. Worked around by making the PA-22 table its own `##` section.
3. **gen_analysis_sidecar.py does not emit pairs, guard groups or the questions' ODC fields.** It writes completeness absences instead ("Merge it from … before the component claims L4"). dsc_check validates `fault`/`trigger` only when they are present, so on a generated sidecar the ODC-vocabulary check never runs. I wrote `merge_sidecar_sections.py`, which lifts them mechanically from their source files.
4. **check_reachability.py** (not required by 02-pilot, run optionally) takes the first declared state as the only initial state and only transition cells as edges. A state that only an interleaving reaches (Open_Waiting_IdleStranded, pair P-01b) cannot be expressed under PA-8 single-event semantics, so it stays red: `state 'Open_Waiting_IdleStranded' is unreachable from initial state 'Open_Idle'`. Left red and reported. It was not silenced.
5. **part_b_pack.py — stripping debris.** Removing ids leaves fragments in the package: "guard group , branch discard", "itself a finding .", "Its validation is guard group and …". Cosmetic.
6. **Disposition vocabulary has no value for a crash/panic.** PING cells use `handle` with the panic stated and a Q (declared in the abstraction statement).
7. **The prompt's routing section** prescribes `model routing: not configured` when the keys are unset. This run had routing switched off by instruction instead. Both facts are stated above.
8. **Measurement script glitch.** In the final checker run, the `check_guards` exit code printed empty because `PIPESTATUS` is unavailable in that shell. Run 1 recorded `exit=1` for the same result.

## Ledger / model calls

No ledger: model routing off, no `local_models.py` call, so there are no failed or skipped model calls.
