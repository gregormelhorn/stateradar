# selftest — red/green checker tests

Part of [tools](../README.md).

## Overview

This directory holds the tests of the pack's deterministic layer. A checker
that has only ever passed proves nothing, so the tests run each checker red
as well as green: every case states what must fail and what must pass.

There are two kinds of test:

- `run_selftest.py`, one script that drives the core checkers and
  generators as subprocesses against the fixtures in this directory and
  against [golden-mini](../../README.md#glossary);
- the `test_*.py` files, each a `unittest` module. Most are named after
  the tool they test; the others cover a feature, a workflow or an
  evidence archive.

Prerequisites are listed under [Verification: Prerequisites](#prerequisites).

## Interface

- `run_selftest.py` — the red/green selftest of the deterministic layer.
  - Usage: `python3 tools/selftest/run_selftest.py`.
  - It prints one `ok` line per passing case and ends with
    "SELFTEST: OK" or "SELFTEST: FAIL" plus the failed expectations.
  - Exit codes: 0 means every case met its expectation, 1 means at least
    one did not, and 2 means `jsonschema` or `z3` is not installed.
  - Sections, in the order the script prints them:
    - baseline: `dsc_check.py` passes on the flat and the compound fixture,
      and `gen_analysis_sidecar.py` parses the compound matrix;
    - the sidecar schema on generator output, and `sidecar_types.py`
      against `formats/analysis.schema.json` (type drift);
    - [disposition matrix](../../README.md#glossary) red cases: silent
      omission, Mermaid model sync, citation drift, manifest discipline
      (for example a snake_case `watch_paths` key) and the registry-backed
      `dsc_check.py` rules;
    - `check_matrix.py` and the consumer wrapper in
      [templates](../templates/README.md), including a pack vendored at
      `tools/prompt-pack`;
    - `check_matrix_mutation.py`, `check_fault_mutants.py` and
      `gen_mutant_variants.py`;
    - `part_b_pack.py --check` row coverage of a blind table;
    - `guard_proofs.py` (z3 disjointness, coverage and boundary probes;
      a z3 `unknown` result must not come back `proven`);
    - `check_reachability.py`;
    - `ensemble_convergence.py`;
    - `benchmark_evidence.classify` (the benchmark dating protocol);
    - `check_matrix_mutation.trailing_citation`: the ignore-to-handle
      mutation keeps a cell's citation in every form the sidecar generator
      reads (backticked file names, escaped and typographic quotes, a
      provenance parenthesis);
    - the timeout path of the two mutation runners;
    - `dsc_stamp.py` re-pins a stale manifest at HEAD while `dsc_check.py
      --repo` still reports it stale, and `check_pack_consistency.py`
      fails on ODC-table drift.
- `test_*.py` — the `unittest` files.
  - Most are named after the tool they test, for example
    `test_local_budget.py` for `local_budget.py`.
  - The others cover a feature, a workflow or an archive, for example:
    - `test_late_adapter.py` runs the late-completion adapter
      `examples/grpc-addrconn/late-completion/run.py` on a copy;
    - `test_draft_verify.py` tests the `draft-verify` subcommand of
      `local_models.py`;
    - `test_fault_runner.py` tests `check_fault_mutants.py`, and
      `test_mutation_binding.py` tests `check_matrix_mutation.py`;
    - `test_gepa_heldout_archive.py` replays the archived held-out evidence
      through `verify_gepa_heldout.py`.
  - Every file has a `__main__` entry, so it runs as
    `python3 tools/selftest/<file>.py`.
  - The five `test_fresh_pair_*.py` files also run in module form,
    `python3 -m unittest tools.selftest.<name>`, which is how CI runs them.

Subdirectories (fixtures, no contracts):

- analysis: (no contract) - the flat fixture: an `analysis.json` with its
  `as-is.machine.mmd`, `decisions/DR-001.yaml` and
  `invariants-and-lints.md`. Its citations point at
  `tools/selftest/src/mini.py`.
- src: (no contract) - `mini.py`, the source file that the flat fixture
  cites.
- compound: (no contract) - a miniature repository:
  `domain-analysis/gate/` (a multi-table matrix with compound rows, a
  Mermaid container and non-Python citations) and `src/gate.ts`.
- ensemble: (no contract) - sidecars for `ensemble_convergence.py`:
  `run1.json`, `run2.json`, `run3.json`, the zero-cell pair `zero1.json`
  and `zero2.json`, and `collision.json` (two states that normalize to
  the same name).

Many cases also use `tests/golden-mini`, which lives outside this
directory: they copy it into a temporary directory and mutate the copy.

## Invariants

- Most checker rules in `formats/rules.toml` name `run_selftest.py` or a
  `test_*.py` file here as their `selftest_ref`, the red case that proves
  the rule can fail. The rest point at `tests/red-mini` or
  `gen_rules.py --selftest`. `gen_rules.py --check` requires every checker
  rule to have such a reference (see
  [tools Invariants](../README.md#invariants)).
- Cases mutate copies, never the tracked fixtures, with one exception
  described under [Side Effects](#side-effects).
- `run_selftest.py` refuses to run without `jsonschema` and `z3`, so a
  missing dependency cannot turn red cases into silent passes.
- Fixture shadowing hazard: `src/mini.py` here has the same basename as
  `tests/golden-mini/src/mini.py`.
  - `gen_analysis_sidecar.py` resolves a bare citation filename by walking
    the source roots under its `--root` (the root itself when none exists),
    and the first hit wins in an unsorted walk.
  - With `--root .` it walks the whole repository, so golden-mini
    citations can be emitted against `tools/selftest/src/mini.py`.
  - Scope `--root` to the component's repository, as the CI step
    "reachability check (golden-mini)" does with
    `--root tests/golden-mini`.

## Side Effects

- Temporary files: `run_selftest.py` works in temporary directories that
  are removed before it returns, so a run leaves nothing under `$TMPDIR`.
  The stamp section creates a throwaway git repository there, and the pack
  consistency section copies the repository (without `.git`, `.venv` and
  `docs/evidence/`) there. For the wrapper
  template cases it creates symlinks there that point at the repository
  root. Many `test_*.py` files also use temporary directories.
- Tracked file rewrite: on every run, `run_selftest.py` runs
  `gen_analysis_sidecar.py --root tools/selftest/compound` and then
  rewrites the tracked `compound/domain-analysis/gate/analysis.json` in
  place with backfilled annotations.
  - The committed file equals that output, so on a green run the rewrite
    is byte-identical and a clean tree stays clean.
  - A generator change shows up as a modified file.
- Subprocesses:
  - `run_selftest.py` starts the pack tools listed under Interface with
    the current interpreter, plus one sleeping process to exercise the
    mutation runners' timeout path.
  - `test_pilot_artifacts.py` runs `git init`, `git add`, `git commit`
    and `git rev-parse` in a temporary repository.
- Network: `run_selftest.py` makes no network calls. The provider-facing
  selftests (`test_jev_local.py`, `test_local_models.py`) patch the HTTP
  call, and the `test_*.py` files pass with `DEEPSEEK_API_KEY` and
  `TYPESAFE_API_KEY` unset.
- No selftest starts a real Codex CLI session: the runner tests patch the
  process launch or use a fake `codex` script.

## Verification

Commands run from the repository root and assume the dev requirements are
installed (see [System Verification](../../README.md#system-verification)).

### Prerequisites

- `run_selftest.py` needs `jsonschema` and `z3-solver` from
  `tools/requirements-dev.txt`.
- Seven selftests also need the `gepa` package from
  `docs/evidence/gepa-bounded/requirements.txt`; without it they fail with
  "No module named 'gepa'":
  - `test_gepa_search.py` and `test_gepa_selection_upstream.py` import
    `gepa` themselves;
  - `test_gepa_heldout_diagnostic.py`, `test_gepa_heldout_archive.py`,
    `test_gepa_training_archive.py`, `test_gepa_prospective_archive.py` and
    `test_gepa_prospective_budget.py` import a tool that needs it (see
    [tools Overview](../README.md#overview)).
- No selftest needs API keys or a Codex account; see
  [Side Effects](#side-effects).

### Commands

CI runs `run_selftest.py` and all 54 `test_*.py` files in
`.github/workflows/pack-ci.yml`: 27 files in job `consistency` and 27 in
job `gepa-evaluation`.

| CI step | Job | `test_*.py` files |
| --- | --- | --- |
| reusable late-completion oracle and addrConn reference | `consistency` | 3 |
| pinned addrConn backoff slice and decisions | `consistency` | 1 |
| semaphore F-09 observability and weak/full comparison | `consistency` | 1 |
| mutation verdict and cell rationale selftests | `consistency` | 6 |
| local model routing selftests | `consistency` | 11 |
| isolated routing pair and restart accounting | `consistency` | 5 |
| GEPA evaluator, search adapter and accounting red probes | `gepa-evaluation` | 18 |
| routing label evaluation and red probes | `gepa-evaluation` | 9 |

Every `test_*.py` file has a `__main__` entry and runs standalone. The
first command runs one file; the second runs all of them in turn, stops
at the first failing file and names it; it includes the seven
`gepa`-dependent files, so install both requirements files first. The CI
steps that follow use `run_selftest.py` and the module form.

- Run: `python3 tools/selftest/test_local_budget.py`
- Run: `( for f in tools/selftest/test_*.py; do python3 "$f" || { echo "FAIL: $f"; exit 1; }; done )`
- CI step "deterministic-layer selftest" (job `consistency`):
  - Run: `python3 tools/selftest/run_selftest.py`
- CI step "isolated routing pair and restart accounting" (job
  `consistency`):
  - Run: `python3 -m unittest tools.selftest.test_fresh_pair_gates tools.selftest.test_fresh_pair_server tools.selftest.test_fresh_pair_smoke_check tools.selftest.test_fresh_pair_recovery tools.selftest.test_fresh_pair_restart`
