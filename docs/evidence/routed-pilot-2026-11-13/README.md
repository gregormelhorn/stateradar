# Raw evidence: first routed pilot (silenceper/pool, channelPool)

Raw outputs only. Nothing here was edited after the run.

## Versions

| item | version |
|---|---|
| pack (stateradar) | da655aa |
| target repo (silenceper/pool) | 6084537 |
| pilot prompt | v1.16 |
| Jev model | jev-1.14.0 |
| Flash model | deepseek-flash (as recorded in `partb/blind.stdout`) |

## Layout

* `channelPool/` — pilot artefacts (catalogue, matrix, guards, invariants, traces,
  questions, sidecar, manifest, summary) plus the per-run helper scripts
  `check_matrix.py`, `check_guards.py`, `verify_fragments.py`, `merge_sidecar.py`.
* `routing/` — task files, raw stdout/stderr and JSON for every `draft-verify` (`dv-*`)
  and `jev-batch` (`step6-*`, `step8-*`) call, `ledger-status.json`, and `lm.sh`.
* `partb/` — blind-session inputs (requirements, contracts, pre-strip catalogue) and
  raw outputs (`blind-output*.md`, `blind.stdout`, `blind.stderr`).
* `comparison.md` — comparison write-up.

## Commands

All model calls went through the wrapper `routing/lm.sh`:

```bash
python3 <pack>/tools/local_models.py --ledger <tmp>/ledger.db "$@"
```

The `draft-verify` calls were run in parallel, one per source file, in this form
(from the step-1 script; `<file>` ∈ README.md, channel.go, pool.go, channel_rpc_test.go,
`<name>` ∈ readme, channel, pool, tests):

```bash
lm.sh draft-verify pool/<file> routing/task-<name>.md --output routing/dv-<name>.json \
  --model jev-1.14.0 > routing/dv-<name>.stdout 2> routing/dv-<name>.stderr
```

The channel.go re-run added `--max-tokens 12000` (`dv-channel-r2.*`).

The exact argument lists of the `jev-batch` (steps 6 and 8) and `blind` calls were not
recoverable when this folder was assembled; their inputs and outputs are the
`routing/step6-*.json`/`step8-*.json` (input → `*.out.json`) and `partb/` files, and
`channelPool/summary.md` ("Model routing record") lists every call with its result.
Part B was `blind --package-only` twice, then `blind` once.

## Tool/prompt problems reported by the pilot session

The verbatim list of 12 problems was not available when this folder was assembled
(it lives in the pilot session's report, not in the output files). The failed and
rejected model calls are recorded in `channelPool/summary.md` under
"Every failed or not-run model call", and the raw failures are in
`routing/dv-.stderr` and `routing/step8-.stdout` (a mis-quoted wrapper invocation and
a mis-split path argument).

## Excluded

* `ledger.db` — cost ledger (excluded by instruction).
* `routing/step1.sh` — the step-1 driver script; it matched the secret grep
  (`sk-|API_KEY=`), so it was withheld rather than copied. The match appears to be the
  substring `task-` in a file name, but it was not copied without review.
* No file exceeded 2 MB.
