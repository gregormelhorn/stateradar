# Timed agent-only run — raw outputs (2026-11-13)

Target: github.com/silenceper/pool @ 6084537e520652192f41aebfd88d822c00b9447a,
component channelPool (channel.go).
Pack: gregormelhorn/stateradar @ a331daece7981b93846aca568a280128b486118a
(sparse checkout without docs/, tests/benchmarks/, README.md, CHANGELOG.md),
prompt 02-pilot.md v1.17.
Routing: off by instruction (no `local_models.py` call, no ledger). Part B ran
in a fresh blind subagent on the `part_b_pack.py --for-dispatch` package.
Steering agent: claude-opus-5-5, the same model as in the second routed pilot.

| Path | Content |
|---|---|
| `comparison.md` | comparison with benchmark silenceper-pool-32 and both routed pilots, including exact cost (added afterwards, outside the run session) |
| `SHAS.txt` | pack and pool SHAs, work directory, routing off |
| `timing.md` | UTC start/end per step and per tool run, blind-subagent usage |
| `analysis/` | the whole analysis directory as written into the pool clone, including the run's own `check_guards.py`, `check_matrix.py` and `merge_sidecar_sections.py` |
| `as-is-tests.md` | executed as-is Go tests, commands, exact outcomes (it names the raw outputs `go-outputs/R*.txt` and earlier test versions `go-outputs/asis_test.go.v1`; in this folder they are in `go-test-outputs/` and `go-tests/`, the raw evidence is left unedited) |
| `go-tests/` | the final as-is test file and its two earlier versions |
| `go-test-outputs/` | raw `go test` outputs R0 to R5 and R0c (R0 and R5 hang on the repository's `TestPool_Get`; `timing.md` and `comparison.md` call the repository-only run `R0-repo-tests-skip-TestPool_Get.txt` "R0b") |
| `checker-outputs/` | outputs of every checker run, including the red ones |
| `part-b/` | the dispatch package as sent, the contracts file, the dispatch start time and the blind subagent's table |
| `authoring-helpers/` | the matrix generator and its header/footer |

## Tool/prompt problems reported by the run session

From `analysis/summary.md` ("Tool and prompt problems met in this run") and
the session's report. The disposition column gives the state on main at the
time this folder was added (main @ 9487c42), updated by the follow-up that
fixed items 1, 2 and 5.

| # | Problem | Disposition |
|---|---|---|
| 1 | `gen_analysis_sidecar.py` parses a prose table whose first header cell is `State` (`\| State \| Condition \|`) as a matrix sub-table and reports a phantom event `Condition` without an error. | Fixed: a header block without `\| **` state rows declares no events (red-first selftest). |
| 2 | `gen_analysis_sidecar.py` reads `\| DOC-` rows of a `###` sub-section into the doctrine map; dsc_check then fails on the schema and on undeclared doc ids. | Fixed: the doctrine table ends at the next heading of any level (red-first selftest). |
| 3 | `gen_analysis_sidecar.py` does not emit `pairs`, guard groups or the ODC fields; the run merged them with its own `merge_sidecar_sections.py`. | Open (roadmap entry 11), as after both routed pilots. |
| 4 | `check_reachability.py` reports a state that only an interleaving reaches (Open_Waiting_IdleStranded, pair P-01b) as unreachable. | Open; by design under single-event semantics. The run left it red and reported it. |
| 5 | `part_b_pack.py` leaves debris where it removes ids ("guard group , branch discard", "itself a .") and repeated file names where it strips citations ("(channel.go, channel.go)"). | Fixed: an id before a comma takes the space before it, an article before a clause-final id goes, and a file name repeated in a comma list is kept once (red-first test). A dangling label such as "guard group" stays. |
| 6 | The disposition vocabulary has no value for a crash or panic; the run used `handle` with the panic stated and a Q. | Open. |
| 7 | The prompt's routing section prescribes `model routing: not configured` when the keys are unset; here routing was off by instruction. | Recorded; both facts are stated in the run's summary. |
| 8 | In the final checker run the `check_guards` exit code printed empty (`PIPESTATUS` unavailable in that shell). | Measurement glitch of the run; run 1 recorded `exit=1` for the same result. |
| 9 | The system `python3` on the run machine lacks `z3` and `jsonschema`; the checkers ran under `uv` with `tools/requirements-dev.txt`. | Environment; no tool change. |
