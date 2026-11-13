# Second routed pilot — raw outputs (2026-11-13)

Target: github.com/silenceper/pool @ 6084537e520652192f41aebfd88d822c00b9447a, component channelPool (channel.go).
Pack: gregormelhorn/stateradar @ a331daece7981b93846aca568a280128b486118a (sparse checkout without docs/, tests/benchmarks/, README.md, CHANGELOG.md), prompt 02-pilot.md v1.17.
Routing: on; `--model jev-1.14.0`; one ledger, limit 1,000,000 µ$.

| Path | Content |
|---|---|
| `comparison.md` | comparison with benchmark silenceper-pool-32 and the first routed pilot (added afterwards, outside the pilot session) |
| `summary.md` | copy of `analysis/channelPool/summary.md` |
| `analysis/channelPool/` | the whole analysis directory as written into the pool clone |
| `timing.md` | UTC start/end per pilot step and per local_models call |
| `as-is-tests.md` | executed as-is Go tests, commands, exact outcomes |
| `go-tests/asis_test.go` | the as-is test file (scratch copy of the pool repo) |
| `test-runs/` | raw `go test` outputs (existing suite, as-is runs) |
| `routing/` | task files, every draft-verify / jev-batch / blind output (`*.json`, `*.stdout.json`, `*.stderr.txt`), scope decisions written before Step-6 Jev calls, the inspected Part-B package (`part-b-blind.package.md`) and the blind table (`part-b-blind.md`), ledger `status` JSON (`ledger-status-after-pilot.json`, `ledger-status-final.json`), `review_drafts.py` |
| `checker-runs/` | outputs of every checker run, including the red ones |
| `work/` | matrix generator and its header/footer, post-repair Part-B package (not sent) |

## Tool/prompt problems reported by the pilot session

Added afterwards from `summary.md` ("Prompt and tool problems hit") and the
session's report; the disposition column says what the follow-up commit
changed.

| # | Problem | Disposition |
|---|---|---|
| 1 | Routing rule 6 names two outcomes for a draft question (a Q or a fold); many were answered by the code, outside scope, or meta-questions about another file. | Rule 6 (v1.18) adds a reasoned disposition: `answered: <file:line>` or `outside scope: <why>`; a model judgment never answers one. |
| 2 | `tools/templates/check_matrix.py` located the pack at `parents[3]/"stateradar"`; a checkout named `pack` needed a hand edit. | The template tries `STATERADAR_PACK`, then siblings `stateradar` and `pack`, and names where it looked (red-first selftest in `run_selftest.py`). |
| 3 | `gen_analysis_sidecar.py` does not carry `pairs`, `guardGroups` or the ODC fields; the pilot merged them with a per-run `merge_sidecar.py`. | Open (roadmap entry 11), as after the first pilot. |
| 4 | `part_b_pack.py` left bare line numbers that followed a citation ("unlock at 136, 151, 156 or 160", ", 194") in the sent package. | Further line numbers of the same file (`file:136, 151 or 160`, `file:175, 194`) are stripped with the citation; a bare number followed by a word stays prose (red-first tests). Rule 7 asks for line numbers written inside citations. |
| 5 | `blind` printed `PART-B COVERAGE: OK …` on stdout after the JSON. | The coverage report goes to stderr; stdout is one JSON document (red-first test). |
| 6 | The Part-B task text kept a stray `>` line from the prompt's blockquote. | Every blockquote marker is removed, empty lines included (red-first test). |
| 7 | `check_reachability.py` is listed in AGENTS.md §5 but not named in 02-pilot Step 4; it found two real modelling defects. | Step 4 (v1.18) runs it and states its conventions (first state initial, `transition` cells only, declared terminals). |
| 8 | `docs/local-model-routing.md` was outside the sparse checkout. | By instruction; no change. |
| 9 | Part B misread the lock table as "mutex released before Factory" after line numbers were stripped; catalogue remembrance and upstream lines were read as documented intent (8 artefact rows). | Item 4 removes the leftover numbers; the remembrance/upstream leak stays open (roadmap entry 11), with the pilot's candidate rule "observed in code" recorded there. |
| 10 | `go vet` flags `example/main.go:18` (unbuffered `os.Signal` channel), outside the component. | Recorded; no tool change. |

