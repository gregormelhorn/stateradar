# Second routed pilot — raw outputs (2026-11-13)

Target: github.com/silenceper/pool @ 6084537e520652192f41aebfd88d822c00b9447a, component channelPool (channel.go).
Pack: gregormelhorn/stateradar @ a331daece7981b93846aca568a280128b486118a (sparse checkout without docs/, tests/benchmarks/, README.md, CHANGELOG.md), prompt 02-pilot.md v1.17.
Routing: on; `--model jev-1.14.0`; one ledger, limit 1,000,000 µ$.

| Path | Content |
|---|---|
| `summary.md` | copy of `analysis/channelPool/summary.md` |
| `analysis/channelPool/` | the whole analysis directory as written into the pool clone |
| `timing.md` | UTC start/end per pilot step and per local_models call |
| `as-is-tests.md` | executed as-is Go tests, commands, exact outcomes |
| `go-tests/asis_test.go` | the as-is test file (scratch copy of the pool repo) |
| `test-runs/` | raw `go test` outputs (existing suite, as-is runs) |
| `routing/` | task files, every draft-verify / jev-batch / blind output (`*.json`, `*.stdout.json`, `*.stderr.txt`), scope decisions written before Step-6 Jev calls, the inspected Part-B package (`part-b-blind.package.md`) and the blind table (`part-b-blind.md`), ledger `status` JSON (`ledger-status-after-pilot.json`, `ledger-status-final.json`), `review_drafts.py` |
| `checker-runs/` | outputs of every checker run, including the red ones |
| `work/` | matrix generator and its header/footer, post-repair Part-B package (not sent) |
