# Timing — second routed pilot (silenceper/pool, channelPool)

All times UTC.

| Step | Start | End | Notes |
|---|---|---|---|
| Setup (clones, key check, venv) | 2026-11-13T00:41:01Z | 2026-11-13T00:41:50Z | pack a331daece7981b93846aca568a280128b486118a, pool 6084537e520652192f41aebfd88d822c00b9447a |
| Read prompt + pack tools | 2026-11-13T00:41:50Z | 2026-11-13T00:43:06Z | |
| Step 0 scope + Step 1 extraction (incl. draft-verify) | 2026-11-13T00:43:06Z | | |
| local_models: draft-verify README.md | 2026-11-13T00:43:13Z | 2026-11-13T00:43:19Z | exit 0; dv-README |
| local_models: draft-verify README_ZH_CN.md | 2026-11-13T00:43:19Z | 2026-11-13T00:43:26Z | exit 0; dv-README_ZH_CN |
| local_models: draft-verify channel.go | 2026-11-13T00:43:26Z | 2026-11-13T00:43:41Z | exit 0; dv-channel |
| local_models: draft-verify pool.go | 2026-11-13T00:43:41Z | 2026-11-13T00:43:45Z | exit 0; dv-pool |
| local_models: draft-verify channel_rpc_test.go | 2026-11-13T00:43:45Z | 2026-11-13T00:43:53Z | exit 0; dv-channel_rpc_test |
| local_models: draft-verify example/main.go | 2026-11-13T00:43:53Z | 2026-11-13T00:43:58Z | exit 0; dv-example_main |
| Step 2 prep: existing test suite replay (go test -race -timeout 60s) | 2026-11-13T00:46:30Z | 2026-11-13T00:47:43Z | TestPool_Get timed out at channel.go:137 |
| Step 2 prep: existing suite without TestPool_Get (-skip) | 2026-11-13T00:55:31Z | 2026-11-13T00:55:35Z | see existing-tests-skip-get.txt |
| Steps 2-4 written (as-is model, validation, catalogue, matrix); stage-1 check run | | 2026-11-13T00:58:39Z | Step 1 closed at extraction write |
| Step 5 invariants and lints (check_guards, check_invariants run) | | 2026-11-13T01:00:27Z | |
| Step 6 adversarial traces (incl. jev-batch ordering) | 2026-11-13T01:00:27Z | | |
| local_models: jev-batch ordering README.md | 2026-11-13T01:00:27Z | 2026-11-13T01:00:28Z | exit 0; jev-order-README |
| local_models: jev-batch ordering channel.go | 2026-11-13T01:00:28Z | 2026-11-13T01:00:28Z | exit 0; jev-order-channel |
| local_models: jev-batch ordering pool.go | 2026-11-13T01:00:28Z | 2026-11-13T01:00:29Z | exit 0; jev-order-pool |
| Step 6 traces + Step 7 questions written; sidecar + dsc_check | | 2026-11-13T01:05:24Z | |
| Step 8 finding verification (incl. jev-batch claims) | 2026-11-13T01:05:24Z | | |
| local_models: jev-batch claims channel.go | 2026-11-13T01:05:24Z | 2026-11-13T01:05:24Z | exit 0; jev-claims-channel |
| local_models: jev-batch claims channel_rpc_test.go | 2026-11-13T01:05:24Z | 2026-11-13T01:05:24Z | exit 0; jev-claims-test |
| local_models: jev-batch claims README.md | 2026-11-13T01:05:24Z | 2026-11-13T01:05:25Z | exit 0; jev-claims-README |
| local_models: jev-batch claims pool.go | 2026-11-13T01:05:25Z | 2026-11-13T01:05:25Z | exit 0; jev-claims-pool |
| Step 8 verification (Jev claims + own re-read + citation sweep) | | 2026-11-13T01:06:15Z | |
| Part B (package, inspect, blind, diff) | 2026-11-13T01:06:15Z | | |
| local_models: blind --package-only | 2026-11-13T01:06:21Z | 2026-11-13T01:06:21Z | exit 0; part-b-package-only |
| local_models: blind (Flash, real run) | 2026-11-13T01:06:47Z | 2026-11-13T01:07:07Z | exit 0; part-b-blind-run |
| Part B done (diff, catalogue repair, Q-25, reachability fix, checker reruns) | | 2026-11-13T01:10:47Z | |
| Summary + ledger status | 2026-11-13T01:10:47Z | | |
| Summary + ledger status (pilot complete) | | 2026-11-13T01:12:11Z | |
| As-is Go tests (write + run) | 2026-11-13T01:12:11Z | | |
| as-is: go test -race -count=1 -timeout 60s ./... (required command) | 2026-11-13T01:13:59Z | 2026-11-13T01:15:01Z | see asis-run-required.txt |
| as-is: same command with -v | 2026-11-13T01:15:14Z | 2026-11-13T01:16:16Z | asis-run-required-v.txt |
| as-is: -v -skip '^TestPool_Get$' | 2026-11-13T01:16:16Z | 2026-11-13T01:16:22Z | asis-run-skip-get-v.txt |
| As-is Go tests written and recorded (as-is-tests.md) | | 2026-11-13T01:17:13Z | |
| Packaging evidence (clone, copy, commit) | 2026-11-13T01:17:28Z | | end time reported in the coordinator report (this file is committed during the step) |
