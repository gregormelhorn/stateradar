# EGM Drift Report — 2026-11-24 (updated 2026-11-27)

Scope: the EGM contract READMEs created or changed by `egm-bootstrap`. None
of these changes is committed.

- Changed: `README.md` (EGM block appended after License, plus corrected
  facts in the method sections), `examples/README.md`,
  `examples/grpc-addrconn/README.md` and
  `examples/weighted-semaphore/README.md`.
- New: `tools/README.md`, `tools/selftest/README.md`,
  `tools/templates/README.md`, and under `examples/weighted-semaphore/`:
  `errgroup/README.md`, `domain-analysis/README.md` and
  `domain-analysis/weightedSemaphore/README.md`.
- Unchanged on purpose: `examples/device-connection/README.md`. It is the
  requirements input for a blind Part B session, and two run manifests watch
  it.

## Process

1. A bootstrap wrote the first contracts.
2. A drift check compared them with the source.
3. Five rounds of revision followed. Each round was scored by three
   independent reviewers: technical accuracy, newcomer comprehension and
   document structure. Each reviewer scored five aspects: accuracy,
   completeness, clarity, structure and consistency.

The target was 9/10 overall with no aspect below 8. The owner stopped after
round 5.

| Round | Accuracy reviewer | Comprehension reviewer | Structure reviewer | Lowest aspect |
|---|---|---|---|---|
| 1 | 7.3 | 6.5 | 6.5 | 5 |
| 2 | 8.5 | 7.0 | 7.5 | 6 |
| 3 | 7.5 | 7.5 | 8.0 | 6 |
| 4 | 8.0 | 7.8 | 8.0 | 7 |
| 5 | 8.0 | 8.0 | 8.3 | 7 (clarity, comprehension reviewer) |

The definite errors found in round 5 were fixed afterwards. No review round
scored those fixes.

## Resolved drift

### Watched folders

The first pass put READMEs inside folders that manifests watch. Committing
them would have made the weightedSemaphore and addrConn late-completion
manifests stale and turned CI red.

- Those contracts now live under "Child contracts" in the parent READMEs.
- The device-connection code contract lives in `examples/README.md`, so no
  code knowledge reaches the blind-pass input.
- Check: no changed file lies inside a `watchPaths` entry of any manifest in
  this repository. Archived manifests under `docs/evidence/` watch upstream
  checkouts.

### Factual errors corrected in older prose

- device-connection is 147 lines, not 130. Its FAILED-row citations are now
  re-anchored to `device_connection.py:81-82` and `:88-97`.
- The install snippet pinned `v1.50`; it now pins `v1.53`, which is the
  current version and exists on the remote.
- weighted-semaphore has five source faults, not four, and the
  `decision_*_test.go` files are evaluation additions.
- The grpc-addrconn SHA-check order is corrected, and its mutant and canary
  counts now match `fault-mutants.json`.

### Errors corrected in generated text

These were found during review:

- the errgroup importers;
- the `run_tool_tests.py` CLI;
- the `gen_odc_table --write` target;
- the `check_matrix` row check;
- the gepa import set;
- the selftest naming;
- the "run all selftests" loop, which exited 0 on failure;
- the grpc-addrconn commands, which wrote to the same output directory and
  overwrote each other's evidence;
- the `Release(0)` semantics;
- the `SetLimit` panic condition;
- the reuse count of addrConn invariant rows;
- the `tests/run.py` exit codes.

## Code defects (fixed in a follow-up commit)

The six defects that round 5 listed as known gaps are fixed. Each has a red
probe in `tools/selftest/run_selftest.py` that failed for the intended reason
before its fix and passes after it:

- `tools/check_pack_consistency.py` now gates on ODC table drift.
- `tools/dsc_stamp.py` re-pins a stale manifest. It validates with the new
  `dsc_check.py --no-staleness`; `dsc_check.py --repo` still reports
  staleness.
- `tools/guard_proofs.py` reports a z3 `unknown` result as a violation,
  never as `proven`.
- `tools/templates/check_matrix.py` finds a pack vendored at
  `tools/prompt-pack`.
- `tools/selftest/run_selftest.py` leaves nothing under `$TMPDIR`.
- The `tools/run_tool_tests.py` docstring shows the real CLI.

The READMEs no longer have "Known gaps" sections. Still documented as side
effects:

- Four tool modules execute work at import time.
- Two first-run gates rewrite tracked files; the files are byte-identical
  when the run is green.

## Open review findings (round 5, not addressed)

These remain at Nit or Major-clarity level. None of them is a factual error.

- Glossary gaps: guard group (G-nn), hole cell, DOC-n, T-nn trace, red-mini
  and MCP. "Discovery" is also used for both test discovery and bug
  discovery.
- Dense passages: the grpc-addrconn Interface and Side Effects sections, and
  the weighted-semaphore cells overview.
- One-owner duplication:
  - the manifest list in grpc-addrconn;
  - the watched-folder list, stated in two places in the root;
  - the `STATERADAR_PACK` workaround, stated in four places.
- Format nits:
  - subdirectory items in a few files;
  - a stale `two-manifests` anchor;
  - `catalog` used in root prose;
  - CLI-option styling that differs between files.
- Missing details:
  - a run command for the gobreaker readiness fixture;
  - a cgo or C-toolchain note for `-race`;
  - where the `/tmp/stateradar-lru-benchmark` clone comes from.

## Verification run

- Every relative link and `#anchor` in the changed READMEs resolves. The
  check used GitHub slug rules and explicit `<a id>` anchors.
- Every code fence is closed.
- `python3 tools/check_pack_consistency.py` printed
  `PACK CONSISTENCY: OK (24 artifacts, registry, version 1.53)`.
- `python3 tools/gen_rules.py --check` printed
  `RULES REGISTRY: OK (73 rules, 22 fault classes, 0 warnings)`.
- Not run here: the Go, z3 and network commands that the READMEs cite.

## Incident

During round 4, a writer agent imported every `tools/*.py` module.
`tools/fresh_pair_smoke.py` runs on import. It started a Codex smoke run,
which exited at once without a model call, and it overwrote scratch files in
`/private/tmp/stateradar-lru-pair-preflight/`. The repository was not
changed. Later agents read source only.
