# tools — deterministic layer

Part of [StateRadar](../README.md).

## Overview

`tools/` is the deterministic layer of the StateRadar pack. The analyzing
agent writes data (`disposition-matrix.md`, `analysis.json`,
`manifest.json`), and these scripts verify it. They also generate sidecars
and scaffolds and assemble the blind [Part B](../README.md#glossary) input.

A second group routes bounded drafting and judgment tasks to hosted APIs:
[DeepSeek Flash](../README.md#glossary) drafts, and
[Jev](../README.md#glossary), Typesafe's hosted judgment API, answers narrow
source-grounded checks. "Local" in names such as `local_models.py` and
`local_budget.py` refers to the pack-local CLI, not to on-device models; see
[docs/local-model-routing.md](../docs/local-model-routing.md). The remaining
scripts run and replay [pilot](../README.md#glossary), routing and
[GEPA](../README.md#glossary) experiments from archived evidence.

Most files are standalone CLI scripts that you run as
`python3 tools/<name>.py`. The rest are library modules imported by the
others, for example `sidecar_types`, `local_budget`, `guard_proofs`,
`cell_rationale`, `subprocess_text`, `mutation_verdict`, `pilot_accounting`,
`pilot_output`, `fresh_pair_gates`, `routing_evaluation`, `gepa_eval` and
`gepa_search`.

Dependencies are listed in `tools/requirements-dev.txt`: `jsonschema>=4.21`
and `z3-solver>=4.12` are lower bounds, while `mypy` and its type stubs
(`types-jsonschema`, `types-PyYAML`) are pinned to exact versions. The
optional `gepa` package is pinned separately in
`docs/evidence/gepa-bounded/requirements.txt`. Without it, these tools fail:

- at import, because they import `gepa` at module top:
  `run_gepa_discovery.py` and `run_gepa_heldout.py`;
- at import, because they import one of those two:
  `run_gepa_heldout_exploratory.py`, `run_gepa_prospective.py`,
  `run_gepa_training_baseline.py` and `verify_gepa_prospective.py`;
- when the importing function runs: `gepa_search.optimize_review`,
  `run_gepa_comparison.py` (its `evaluate`), and `verify_gepa_heldout.py`
  and `verify_gepa_training.py` (they import `run_gepa_discovery` inside a
  function).

The selftests that need `gepa` are named in
[selftest Prerequisites](./selftest/README.md#prerequisites).

## Interface

For one component analysis in `<repo>/domain-analysis/<component>/`, run
the core sequence in this order:

1. Check the matrix and the event catalogue
   ([check_matrix.py](#check_matrixpy)):

   ```text
   python3 tools/check_matrix.py <repo>/domain-analysis/<component>
   ```

2. Generate the sidecar from the matrix
   ([gen_analysis_sidecar.py](#generators-and-maintenance)):

   ```text
   python3 tools/gen_analysis_sidecar.py --root <repo> <component>
   ```

3. Check the sidecar, its citations and its manifest
   ([dsc_check.py](#dsc_checkpy)):

   ```text
   python3 tools/dsc_check.py <repo>/domain-analysis/<component> --repo <repo> --model as-is.machine.mmd
   ```

The pack's own gate commands are listed under [Verification](#verification)
and in the root [System Verification](../README.md#system-verification).

The tools are grouped into the sections below. The table doubles as the
section index and shows which sections cost money or account quota:

| Section | Needs API keys ($) | Needs Codex quota | Offline replay available |
| --- | --- | --- | --- |
| [Core checkers](#core-checkers) | No | No | Not needed (runs offline) |
| [Generators and maintenance](#generators-and-maintenance) | No | No | Not needed (runs offline) |
| [Blind pass (Part B), ensembles and cross-checks](#blind-pass-part-b-ensembles-and-cross-checks) | No | No | Not needed (runs offline) |
| [Mutation and fault testing](#mutation-and-fault-testing) | No | No | Not needed (runs offline; needs Go) |
| [Late-completion oracle and pinned references](#late-completion-oracle-and-pinned-references) | No | No | Not needed (needs Go; network unless `--checkout`) |
| [Local model routing (Flash / Jev)](#local-model-routing-flash--jev) | Yes | No | No; the selftests patch the HTTP call |
| [Pilot runners and accounting](#pilot-runners-and-accounting) | Yes: [routed arms](#pilot-runners-and-accounting), `run_flash_pilot.py`, `run_fresh_routing_pair.py` | Yes | Partly: `fresh_pair_smoke_check.py` |
| [Benchmarks and regression runners](#benchmarks-and-regression-runners) | No | No | Not needed (`run_benchmark.py` clones repositories) |
| [Routing evaluation (source-fragment labels)](#routing-evaluation-source-fragment-labels) | Yes, runners | Yes, runners | Yes: `verify_routing_*.py` |
| [GEPA evaluation](#gepa-evaluation) | Yes, runners | Yes, runners | Yes: `verify_gepa_*.py` |

API calls go to DeepSeek and Typesafe with `DEEPSEEK_API_KEY` and
`TYPESAFE_API_KEY`, metered in a ledger whose default cap is stated under
[Invariants](#invariants). Codex sessions use the signed-in Codex/ChatGPT
account. Details are under [Side Effects](#side-effects).

Subdirectories:

- templates: [`./templates/README.md`](./templates/README.md) - wrappers
  that a consuming repository copies into its tree (`check_matrix.py` and
  the `test_dsc_check.py` pytest template).
- selftest: [`./selftest/README.md`](./selftest/README.md) - the red/green
  selftest harness, the `unittest` selftests and their fixtures.

### Core checkers

These run on a component's `domain-analysis/<component>/` directory. The two
largest checkers get their own sub-headings; the rest share
[Other core checkers](#other-core-checkers).

#### dsc_check.py

`dsc_check.py` — the pack checker for one component's
[sidecar](../README.md#glossary) (`analysis.json`).

- Usage:

  ```text
  python3 tools/dsc_check.py <analysis-dir> [--repo ROOT] [--model FILE.mmd] [--allow-no-schema] [--no-staleness]
  ```

  - `--model` is resolved relative to `<analysis-dir>`; the Mermaid sync
    runs only when that file exists.
  - `--repo` turns on the fragment-citation and staleness checks.
  - `--no-staleness` skips only the staleness diff; `dsc_stamp.py` uses it
    to validate an analysis at HEAD before re-pinning.
- Symbols: `main`, `VOCAB` (disposition vocabulary), `HOLES`,
  `GUARD_OUTCOMES`, `NF_REASONS`, `CATEGORIES` (undesired-variant
  categories, read from `formats/rules.toml`), `Q_STATUS`.
- Exit codes: 0 means OK ("DSC CHECK: OK"); 1 means violations
  ("DSC CHECK: FAIL" plus one line per error) or a missing `jsonschema`
  (see [Invariants](#invariants)); 2 means no arguments or a missing
  `analysis.json`.
- Crash paths, which end with an uncaught exception and exit 1:
  - a sidecar without a `states`, `events` or `cells` key raises
    `KeyError`;
  - `--repo` or `--model` given as the last argument, without a value,
    raises `IndexError`.

The complete rule list is `main()` in `tools/dsc_check.py`; the module
docstring summarizes it. The registry rules in `formats/rules.toml` whose
`checker_ref` names `tools/dsc_check.py` cover most, but not all, of these
checks. The failure categories (ids such as PA-22 and R-GATE-TYPE, here and
under [check_matrix.py](#check_matrixpy), are rule ids from
`formats/rules.toml`):

- Schema: the sidecar is validated against `formats/analysis.schema.json`,
  and `cell_rationale.rationale_errors` validates rationale bindings.
- Grid and vocabulary:
  - every (state, event) pair has exactly one cell;
  - every disposition is in `VOCAB`, and a `transition` target is a
    declared state.
- Questions:
  - every hole cell (`UNSPECIFIED` or `ignore (accidental)`), and every
    other cell that names a [Q-nn](../README.md#glossary), must name a
    question in the sidecar `questions` register. For a non-hole cell the
    error text says "open-questions.md does not declare", but the lookup is
    the sidecar register, not that file;
  - each question status starts with a `Q_STATUS` value (`OPEN`,
    `ANSWERED`, `RESOLVED`, `CONFLICT`);
  - a `RESOLVED` question needs at least one cell that names it and links a
    [DR](../README.md#glossary);
  - [ODC](../README.md#glossary) fields: each `fault` id must be a fault
    class in `formats/rules.toml`, and `trigger` must be in its
    `odc_triggers` vocabulary.
- Decisions:
  - every `ignore (documented)`, `reject` and `defer (queued)` cell carries
    a DR or a citation;
  - behavioural-DR reverse coverage: every DR in `behaviouralDrs` is cited
    by at least one cell;
  - DR files: when a `decisions/` directory exists, every cited DR has a
    `decisions/DR-nnn.yaml` file. Without that directory this check is
    skipped.
- Asserted absence: an empty or missing `pairs`, `guardGroups` or
  `coverage` section fails unless `completeness.<section>` is set (for
  example `count: 0` with a `reason`).
- Pairs and guards:
  - every interaction pair has a `trace`;
  - every guard group's outcome is in `GUARD_OUTCOMES`, and a
    `not-formalizable` reason starts with one of `NF_REASONS`
    (`external-call`, `dynamic-state`, `clock`, `unstructured-payload`).
- Undesired-variant coverage:
  - every coverage source has a non-empty entry for every category in
    `CATEGORIES`;
  - every base event has a coverage entry for each of the seven categories
    (a list hard-coded in this check);
  - every `UV-…` id named in a coverage entry is a known event.
- Event annotations: every base event carries a `gate` (R-GATE-TYPE) and
  `upstream_guards` (R-UPSTREAM-GUARD); undesired variants inherit both.
- Doctrine lines (`DOC-n`, the normative sentences extracted from the
  requirements; see [AGENTS.md §2](../AGENTS.md#2-the-objects)), rule PA-22:
  when `invariants-and-lints.md` has a
  `<!-- doc-ids: ... -->` comment, each declared `DOC-n` maps in the
  sidecar `docLines` to a grid cell, a `SYS`/`NAT` id, a `G-nn` guard
  group, or a rejected/structural reason; mapped ids must be declared.
- Mermaid↔matrix sync, only with an existing `--model` file: every state
  appears in the diagram and every transition cell has an edge.
- Fragment citations, only with `--repo`: each cell citation's file exists
  and its fragment appears within ±3 lines of its line.
- Manifest, only when `manifest.json` exists in `<analysis-dir>`:
  - the keys `component`, `watchPaths` and `analyzedSha` are present;
  - a snake_case `watch_paths` key fails, and so does an empty
    `watchPaths`, because the staleness diff would run unfiltered;
  - staleness, only with `--repo` and without `--no-staleness`: a git diff
    of `watchPaths` since
    `analyzedSha` must be empty. The diff is skipped while `analyzedSha` is
    [`WORKTREE`](../README.md#glossary), the placeholder for a manifest
    that is not yet pinned.

#### check_matrix.py

`check_matrix.py` — the generic checker for the
[disposition matrix](../README.md#glossary) (`disposition-matrix.md`) and
the event catalogue (`event-catalogue.md`).

- Usage: `python3 tools/check_matrix.py <analysis-dir>`.
- Rows are the table lines that start with `| **`; a state's cell counts
  accumulate across sub-tables.
- Stage 1 checks:
  - grid size: each row has as many cells as the catalogue's
    `<!-- event-ids: ... -->` comment declares events. Column headers are
    not matched to event ids, so only the count is checked;
  - no [cell](../README.md#glossary) is empty;
  - every `reject`, `ignore (documented)` and `defer` cell carries a
    citation (`file.<ext>:NNN`, a DR id, `inferred` or a `Q-` reference);
  - the matrix declares its states in a `<!-- states: ... -->` comment;
  - PA-17 state naming: each declared state is PascalCase segments joined
    by `_`, or an ALL-CAPS API enum; compound labels are checked word by
    word;
  - every declared state has a row, except states listed in a
    `<!-- terminal: ... -->` comment, which need none; undeclared rows
    fail;
  - when the catalogue has a `## Undesired-coverage` table, no cell in it
    is empty;
  - PA-10: the matrix has a line starting with `Abstraction`;
  - PA-4: every catalogue event is classified `external` or `internal` in
    its table row, or references a classified base event.
- Stage 2 checks:
  - every hole cell carries a `Q-nn` that `open-questions.md` declares.
    The scan is a regular expression over the whole matrix text, not only
    table cells: any `UNSPECIFIED` or `ignore (accidental)` up to the next
    `|` or line end, prose included, must carry a declared `Q-` id;
  - only when `adversarial-traces.md` exists, two further checks run (both
    are skipped without the file):
    - every interaction-pair id (`P-nna/b`) in the catalogue appears in
      it;
    - every control trace that cites a `DOC-n` or `DR-n` carries the line
      "cited text contemplates this ordering: yes/no".
- Exit codes: 0 means OK, 1 means violations ("CHECK MATRIX: FAIL"), and 2
  means a wrong argument count or a missing `event-catalogue.md`. A missing
  `disposition-matrix.md`, or a catalogue without an
  `<!-- event-ids: ... -->` comment, ends with an uncaught exception.

#### Other core checkers

- `guard_proofs.py` — the shared z3 proof procedure for guard groups:
  pairwise disjointness, coverage or an explicit else, and boundary probes.
  - Symbols: `check_group`, `boundary_probe`, `render`, `GroupResult`.
  - Each group's outcome is `"proven"` or `"violation"`.
  - A per-component script supplies only the z3 variables, the guards and
    the [NAT](../README.md#glossary) assumptions. NAT invariants state what
    the component assumes about its environment (for example value
    ranges); SYS invariants state what the component itself must
    guarantee. The proof may rely only on the NAT assumptions.
- `check_reachability.py` — checks that every non-terminal state is
  reachable from the initial state, through matrix transitions or cited
  interaction-pair edges.
  - Usage: `python3 tools/check_reachability.py <analysis-dir> [--repo ROOT]`.
  - The initial state is the first entry of the sidecar `states` list.
  - `--repo` is the root for pair evidence paths; it defaults to
    `<analysis-dir>/../..`.
  - It also checks that no state is a sink (a state with no outgoing
    transition) unless the matrix lists it in its `<!-- terminal: ... -->`
    comment. This tool splits that comment on commas only, while
    `check_matrix.py` also splits on whitespace.
  - Symbols: `main`, `load_graph`, `reachable_from`, `pair_reachability`,
    `pair_edges`.
  - Exit codes: 0 means OK, 1 means violations ("REACHABILITY CHECK: FAIL").
- `cell_rationale.py` — validates explicit rationale bindings against their
  sources.
  - Symbols: `rationale_errors`, `read_bindings`, `KINDS`.
- `sidecar_types.py` — the static types of `analysis.json`.
  - Symbols: `Sidecar` and its TypedDicts (`Cell`, `Event`, `Pair`,
    `GuardGroup`, `Question`, `DocLine`, `Citation`, `Completeness` and
    others).
- `check_pack_consistency.py` — the pack self-check. It runs its checks
  at module level (see the import-time list under
  [Side Effects](#side-effects)).
  - Gating (exit 1, "PACK CONSISTENCY: FAIL", if any fails):
    - `gen_rules.py --check`;
    - the artifact filenames the prompts mention are defined by the
      producing prompt;
    - the README version equals the highest `## vX.Y` heading in
      `CHANGELOG.md` ("Unreleased" entries are ignored);
    - path existence in `README.md`, `AGENTS.md`, `skills/**/*.md` and
      `docs/**/*.md` (files under `docs/superpowers/` are skipped):
      - a backtick path with a file extension must exist when it starts
        with one of the pack roots `prompts/`, `tools/`, `skills/`,
        `commands/`, `examples/`, `formats/`, `tests/` or `.github/`;
        paths under `docs/` and other prefixes are not verified, and
        paths containing `/prompt-pack/` are skipped;
      - a layout line (a line that starts with a path ending in `/`,
        followed by whitespace) under the same roots must name an
        existing directory;
    - the [ODC](../README.md#glossary) trigger list in
      `prompts/02-pilot.md` equals `odc_triggers` in `formats/rules.toml`.
    - `gen_odc_table.py --check`: the ODC table in
      `tests/benchmarks/README.md` matches the benchmark sidecars.
  - Not gating: `git describe --tags --abbrev=0` is compared with the README
    version, and a mismatch prints only a warning.

### Generators and maintenance

- `gen_analysis_sidecar.py` — turns `disposition-matrix.md` into
  `analysis.json`.
  - Usage:

    ```text
    python3 tools/gen_analysis_sidecar.py [--root REPO] [--analysis-dir DIR] [--strict] [component-or-dir ...]
    ```

  - `--strict` exits 1 when notes are emitted.
  - An optional `sidecar-overlay.yaml` adjusts the output.
  - Symbols: `generate`, `main`, `Overlay`, `EventAnnotation`, `SRC_ROOTS`,
    `SRC_EXTS`.
- `gen_matrix_scaffold.py` — builds a matrix skeleton from the states and the
  event catalogue (`main`, `DEFAULT_COLUMNS`); `--write` writes it.
- `gen_rules.py` — renders the generated blocks of `formats/rules.toml` into
  the prompts, `AGENTS.md` and `README.md` (`--check`, `--write`,
  `--selftest`).
  - Symbols: `check`, `constraints`, `write`, `selftest`, `render_all`.
  - `--check` fails ("RULES REGISTRY: FAIL") when a generated block drifts
    from the registry, a block key is unknown or unused, or a disposition
    value is missing from `prompts/00-methods-reference.md` or
    `prompts/02-pilot.md`.
  - It also enforces the registry constraints C1..C5 named in the module
    docstring:
    - C1: a checker rule has a `checker_ref` and a `selftest_ref`, and a
      `selftest_ref` path exists;
    - C2: a lint rule is rendered into the Step-5 block or anchored by
      `lint_ref`;
    - C3: a fault-model rule has at least one `detects` entry;
    - C4: a fault class that no rule detects produces a warning;
    - C5: the marker keys in the target files match the renderable keys.
  - Beyond C1..C5 it rejects duplicate rule or fault ids, unknown `class`
    and `enforcement` values, unknown fault ids in `detects`, inconsistent
    fault `level`/`observability` fields, and `prose_ref` files or
    `<!-- rule:ID -->` anchors that do not exist. The complete list is
    `constraints()` and `check()` in `tools/gen_rules.py`.
  - `"TODO"` handling for `selftest_ref` is stated under
    [Invariants](#invariants).
- `gen_odc_table.py` — generates the ODC coverage table from the benchmark
  sidecars into `tests/benchmarks/README.md` (`build_odc`, `render_table`;
  `--write`, `--check`).
- `gen_mutant_variants.py` — generates implementation variant files for a
  component from its `<analysis-dir>/mutant-generation.json`, validated
  against `fault-mutants.json`.
  - Usage: `python3 tools/gen_mutant_variants.py <analysis-dir> [--check]`.
  - Without `--check` it writes the tracked variant files; with `--check`
    it compares and reports `OK` or `DRIFT`.
  - Users: [golden-mini](../README.md#glossary), the weighted semaphore,
    the addrConn backoff slice and the addrConn late-completion reference.
  - CI runs it with `--check` on `weightedSemaphore`; `addrconn_f09.py` and
    `addrconn_late.py` call it in both modes.
- `refresh_citations.py` — remaps Python `file.py:line` citations between
  two SHAs (`refresh_file`, `main`).
  - Usage:

    ```text
    python3 tools/refresh_citations.py <analysis_dir> [--repo ROOT] [--from-sha SHA] [--to-sha SHA] [--dry-run]
    ```

  - `<analysis_dir>` is relative to `--repo` (default `.`).
  - `--from-sha` has no default value: when it is omitted, the tool reads
    `analyzedSha` from `<analysis_dir>/manifest.json`, and exits 2 with
    "REFRESH: no manifest.json and no --from-sha" when that file is
    missing.
  - `--to-sha` defaults to `HEAD`; `WORKTREE` reads the working tree.
  - `--dry-run` prints the counts without rewriting files.
  - Exit codes: 0 when every citation resolved, 1 when any is unresolved
    ("REFRESH: <n> UNRESOLVED — human review needed:"), 2 for the missing
    manifest above.
  - `CITE_RE` matches only `*.py`; Go and other citations are not remapped.
  - It tries a content anchor first and then a Python `def` offset. It lists
    unresolved citations and never drops them.
- `dsc_stamp.py` — runs `dsc_check.py --repo --no-staleness` and, only if
  the check passes, pins `analyzedSha` to HEAD and writes `date`.
  - The staleness diff is skipped because re-pinning after a
    [reconcile](../README.md#glossary) is exactly the case where watched
    paths changed since the old `analyzedSha`; every other check, including
    the fragment citations at HEAD, must pass.
  - Usage:

    ```text
    python3 tools/dsc_stamp.py <analysis-dir> [--repo .] [--date YYYY-MM-DD] [--model as-is.machine.mmd]
    ```

  - `<analysis-dir>` is relative to `--repo`.
  - It passes `--model` to the checker only if that file exists in
    `<analysis-dir>`; the default is `as-is.machine.mmd`.
  - Exit codes: 0 means checked and stamped, 1 means the check failed and
    nothing was written ("DSC STAMP: check failed — manifest NOT stamped").
  - A missing `manifest.json` after a passing check ends with an uncaught
    `FileNotFoundError`.

### Blind pass (Part B), ensembles and cross-checks

- `part_b_pack.py` — builds the blind input package: catalogue,
  requirements and contracts, with length guards (`MIN_INPUT_CHARS`).
  - Symbols: `assemble`, `check`, `blind_catalogue`.
  - `--check` validates that a returned blind table covers every event id
    and pair ordering.
- `dsc_blind.py` — runs the blind pass as one command: `--dispatch`, then
  `--diff blind_output.md` (`assemble`, `diff_blind`). `--dispatch` prints
  dispatch instructions; it calls no model.
- `ensemble_convergence.py` — diffs matrices across several runs and
  generates questions mechanically (`main`, `ConvergenceStats`).
- `dsc_cross_check.py` — checks traditional review findings against the
  matrix (`cross_check`).
- `dsc_compose.py` — prints a cross-model composition report to stdout. It
  is a report, not a gate.

### Mutation and fault testing

- `check_matrix_mutation.py` — runs the declared cell suites against
  temporary spec [mutants](../README.md#glossary) of the disposition matrix.
  - Symbols: `build_mutations`, `Config`, `load_config`,
    `trailing_citation`.
  - Mutation kinds: `transition_to_ignore`, `transition_target_swaps`,
    `handle_to_ignore`, `ignore_or_reject_to_handle`.
- `check_fault_mutants.py` — runs complete cell suites against fault
  mutants, gated by executed projection [canaries](../README.md#glossary)
  (`run`, `Config`, `classify_result`); see
  [docs/fault-mutants.md](../docs/fault-mutants.md).
- `mutation_verdict.py` — parses cell-loop evidence (`cell_verdict`,
  `CellVerdict`). A process failure alone never counts as a kill.
- `subprocess_text.py` — `as_text` converts captured subprocess output to
  text for the mutation runners.
- `semaphore_f09.py` — runs the executed slice for fault class
  [F-09](../README.md#glossary) (cancellation leak) on the weighted
  semaphore: an independent capacity canary, a weak survivor and a full
  cell kill.

### Late-completion oracle and pinned references

- `late_completion.py` — the language-neutral, cause-specific oracle for
  recorded [late-completion](../README.md#glossary) traces.
  - Symbols: `evaluate`, `validate_profile`, `report`, `EvidenceError`.
- `check_late_workflow.py` — validates reviewed applicability and replay
  execution evidence (`check_plan`, `check_execution`, `write_receipt`).
- `addrconn_late.py` — binds the oracle to the pinned grpc-go reference
  (`main`, `verify_anchor`, `apply_evaluation_patch`).
- `addrconn_f09.py` — checks the pinned addrConn backoff slice (`main`,
  `verify_records`, `verify_harness`).
- `gobreaker_late_readiness.py` — a bounded
  [readiness probe](../README.md#glossary) against gobreaker's public API.

### Local model routing (Flash / Jev)

- `local_models.py` — the CLI entry point.
  - `--ledger PATH` is required; `--limit-microdollars N` sets the limit of
    a new ledger.
  - Subcommands: `status`, `set-limit`, `settle`, `flash`, `jev`,
    `jev-batch`, `draft-verify`, `draft-cells`, `flash-windows`, `blind`.
  - Symbols: `FLASH_URL`, `JEV_URL`, `FlashResult`, `JevResult`,
    `JevBatchResult`, `DraftVerifyResult`, `VerificationFailed`,
    `VerificationUnrecorded`, `ProviderError`, `LedgerError`.
- `local_budget.py` — a persistent SQLite reservation ledger in
  microdollars.
  - Symbols: `Budget` (`reserve`, `settle`, `total`, `calls`, `set_limit`,
    `limit`), `BudgetExceeded`, `LedgerCall`.
- `jev_local.py` — asks Jev one bounded, metered yes/no question about a
  source passage (`main`, `post_json`).
  - Usage:

    ```text
    python3 tools/jev_local.py --ledger PATH [--limit-microdollars N] <source> <question>
    ```

  - It reads only `TYPESAFE_API_KEY` and posts only to `JEV_URL`.
  - `post_json` retries HTTP statuses 429, 503 and 529 (`RETRY_STATUSES`)
    up to 3 times (`MAX_RETRIES`), with 120 s per request
    (`TIMEOUT_SECONDS`).
  - The retry delay is `Retry-After` capped at 60 s, or exponential backoff
    (1, 2, 4 s, capped at 30 s) when the header is absent or not a number.
    Other errors fail at once.
- `jev_eval.py` — `evaluate` compares a Jev batch with independently
  reviewed labels.
- `draft_cells.py` — Flash drafts matrix cells, code checks them, and Jev
  judges each cell (`draft_cells`, `check_cells`, `load_task`, `compare`,
  `DISPOSITIONS`, `HOLES`).
- `hybrid_pilot.py` — renders reviewed matrix fields and checks the
  citations in proposed schedules (`render_matrix`, `render_cell`,
  `review_windows`).
- `pilot_artifacts.py` — renders reviewed catalogue fields and copies exact
  source lines for citations (`render_catalogue`, `citations`,
  `audit_pilot`).

### Pilot runners and accounting

These runners drive full pilots through the signed-in Codex CLI. Each finds
the CLI through `CODEX_APP_RUNTIME_CLI_PATH` when it is set, otherwise
`codex` on `PATH`. They are
[Codex runners](../README.md#glossary); [Sol](../README.md#glossary) is the
Codex model they pin (`run_sol_pilot.py:MODEL`). The "Pool pilot" is the
pilot on `github.com/silenceper/pool` (`channelPool`) at `POOL_SHA`. In a
matched pair, the direct arm runs without provider keys, and the routed arm
gets `DEEPSEEK_API_KEY` and `TYPESAFE_API_KEY` and routes through Flash and
Jev.

- `run_sol_pilot.py` — runs a pilot, or compares tool output modes
  (`run_arm`, `run_checked_arm`, `POOL_SHA`, `GOBREAKER_SHA`,
  `COMPONENTS`).
  - Its `prepare` builds the isolated checkout that the other pilot runners
    reuse.
  - Prerequisites, checked by `main` before any model call:
    - macOS with `/usr/bin/sandbox-exec`;
    - `--output` naming a new directory under `/private/tmp`;
    - `--component-repo` (or its Pool alias `--pool-repo`) naming a local
      clone that contains the pinned component SHA;
    - both `DEEPSEEK_API_KEY` and `TYPESAFE_API_KEY`, unless
      `--prepare-only` is given;
    - the Codex CLI on `PATH` (or `--codex-bin`) and signed in with
      ChatGPT ("Logged in using ChatGPT"), unless `--prepare-only` is
      given;
    - `jsonschema` and `z3` importable by the current interpreter.
  - `--model` defaults to `gpt-6.1-sol` (`MODEL`) and also accepts
    `gpt-6.1-terra`.
- `run_flash_pilot.py` — runs the pinned Pool pilot with Flash steering and
  a Codex blind pass (`run`, `blind_dispatch`).
  - It refuses to start without both provider keys and the Codex CLI, and
    it requires macOS and a new output directory under `/private/tmp`.
- `run_fresh_routing_pair.py` — runs two isolated full pilots, the direct
  and the routed arm, on a pinned `golang-lru` source and measures provider
  and controller costs (`run_arm`, `main`, `SOURCE_SHA`, `PACK_SHA`,
  `CAP`).
  - Usage: `python3 tools/run_fresh_routing_pair.py <out> [--prepare-only]`.
  - Prerequisites (`main` checks the first three, in this order, before it
    creates `<out>`):
    - `<out>` is a new directory under `/private/tmp`, and the host is
      macOS;
    - the Codex CLI is on `PATH`, and both `DEEPSEEK_API_KEY` and
      `TYPESAFE_API_KEY` are set. `--prepare-only` does not lift either
      requirement, and the keys are required even though the direct arm
      makes no provider calls;
    - the committed evidence matches: the cost in
      `docs/evidence/routing-fresh-pair/preflight-model-smoke.json` equals
      the cost recomputed from `model-preflight/usage-checkpoint.json`, its
      recorded server hash equals `fresh_pair_server.py`, and every file
      hash in `reference/freeze.json` matches;
    - a local `golang-lru` clone exists at the hard-coded path
      `/tmp/stateradar-lru-benchmark`; `prepare` fetches `SOURCE_SHA` from
      it for each arm.
  - `CAP` is a soft cap of 5.0 USD-equivalent for the whole run: earlier
    restart-smoke costs plus both arms. The run stops as `BLOCKED` when the
    known total reaches it. Each arm also gets its own ledger at the
    default limit (see [Invariants](#invariants)).
- `fresh_pair_gates.py` — the budget and blind-dispatch guards for the
  matched pilot (`allow_blind`, `route_policy`, `enforce_cap`,
  `live_budget`, `tally`).
- `fresh_pair_server.py` — `run` is the MCP command server for the direct
  arm and the routed arm.
- `fresh_pair_smoke.py` — meters a direct-arm MCP smoke run. It has no
  `__main__` guard (see [Side Effects](#side-effects)).
  - Usage: `python3 tools/fresh_pair_smoke.py [--audit]`.
  - It works in the fixed directory `/tmp/stateradar-lru-pair-preflight`.
  - Without `--audit` it starts a Codex session for the direct arm;
    `--audit` skips that session and re-verifies the existing output, but
    still exits with "BLOCKED(smoke): Codex CLI missing" when no Codex CLI
    is found.
  - In both modes it overwrites the tracked
    `docs/evidence/routing-fresh-pair/preflight-model-smoke.json`, the file
    that `run_fresh_routing_pair.py` checks.
- `fresh_pair_smoke_check.py` — `verify` validates the smoke run's events,
  including the direct-provider refusal.
- `pilot_accounting.py` — writes incremental usage checkpoints for one
  Codex CLI session (`UsageCheckpoint`, `JsonlTail`, `cost_report`,
  `atomic_json`).
- `pilot_output.py` — formats pilot command results from their full logs
  (`compact_output`, `selective_output`, `failure_excerpt`,
  `select_lines`).

### Benchmarks and regression runners

- `run_tool_tests.py` — the tool regression runner over the golden cases in
  `tests/<case>/` (`run_case`, `main`).
  - Usage: `python3 tools/run_tool_tests.py [NAME ...]`; `main()` takes bare
    case names as positional arguments.
  - Discovery that finds no cases is a hard failure.
  - Exit codes: 0 when every case passes, otherwise 1.
  - Each case runs `gen_analysis_sidecar.py --root tests/<case>`, which
    regenerates the tracked `tests/<case>/domain-analysis/mini/analysis.json`
    on every run.
- `run_benchmark.py` — the StateRadar benchmark regression runner
  (`run_benchmark`, `clone_at_commit`, `run_part_a`, `assert_expected`).
- `benchmark_evidence.py` — `classify` dates benchmark evidence to keep
  contamination visible.
- `finding_benchmark.py` — `audit` and `anchor` audit explicit reviewed
  findings.
- `finding_preservation.py` — `audit` checks that a post-review keeps its
  baseline findings unchanged.

### Routing evaluation (source-fragment labels)

- `routing_evaluation.py` — the gates and the label reconciliation
  (`check_splits`, `allow`, `reconcile`).
- `prepare_routing_labels.py` — `main` freezes the reference labels.
- `routing_label_integrity.py` — `verify_source` validates the pinned
  source and the check citations.
- `routing_label_review.py` — `Review` runs an isolated AI review of the
  labels.
- `run_routing_label_eval.py` — `Run` runs the development checks first and
  then the held-out checks: checks on components excluded from development,
  comparing Jev with direct Codex.
- `verify_routing_label_eval.py` — `verify` replays that evidence offline.
- `run_routing_flash_diagnostic.py` — `run` runs the Flash→Jev diagnostic.
- `verify_routing_flash_diagnostic.py` — `verify` replays the diagnostic.
- `routing_flash_eval.py` — `score` audits Flash proposals.
- `routing_compare_prompt.py` — `build` prepares source-only comparator
  inputs.
- `routing_ledger_check.py` — `verify` compares saved ledger summaries with
  the persistent ledger.

### GEPA evaluation

These tools evaluate the `gepa` prompt optimizer. Each evidence archive
below names the runner that produced it and the offline replay that checks
it.

- [docs/evidence/gepa-bounded](../docs/evidence/gepa-bounded/README.md) —
  the bounded three-arm comparison.
  - Runners: `run_gepa_comparison.py` (`Experiment`) and
    `run_gepa_quality_extension.py` (`main`).
  - Replays: `verify_gepa_reference.py`, `verify_gepa_quality.py`.
- [docs/evidence/gepa-discovery](../docs/evidence/gepa-discovery/README.md)
  — the discovery study.
  - Runner: `run_gepa_discovery.py` (`Study`).
  - Replay: `verify_gepa_discovery.py`.
- [docs/evidence/gepa-training-catalog](../docs/evidence/gepa-training-catalog/README.md)
  — the training catalogue baseline.
  - Runner: `run_gepa_training_baseline.py` (`Baseline`).
  - Replay: `verify_gepa_training.py` (`verify_archive` and related
    functions).
- [docs/evidence/gepa-heldout](../docs/evidence/gepa-heldout/README.md) —
  the held-out evaluation.
  - Runners: `run_gepa_heldout.py` (`Heldout`) and
    `run_gepa_heldout_exploratory.py` (`Diagnostic`).
  - Replay: `verify_gepa_heldout.py`.
- [docs/evidence/gepa-prospective](../docs/evidence/gepa-prospective/README.md)
  — the prospective evaluation.
  - Runners: `run_gepa_prospective.py` (`Prospective`) and
    `gepa_prospective_reference.py` (`Review`).
  - Replay: `verify_gepa_prospective.py`.
- Evaluators and audits shared by these runners:
  - `gepa_eval.py` — `validate`, `score`, `validate_splits`,
    `check_access`.
  - `gepa_discovery_eval.py` — `audit`, `check_phase`.
  - `gepa_heldout_eval.py` — `check_splits`, `permit`, `train_feedback`.
  - `gepa_provenance.py` — `validate`.
  - `gepa_training_catalog.py` — `validate_catalog`,
    `validate_independent_review`.
  - `gepa_report.py` — `summarize`, `audit`, `audit_quality`.
  - `gepa_cost_sensitivity.py` — `analyze`.
  - `gepa_selection.py` — `classify`; `report_gepa_selection.py` —
    `report`.
- `gepa_search.py` — the optional adapter (`optimize_review`), which
  imports the `gepa` package when called and requires `gepa==0.1.4`.

## Invariants

- Sidecar direction: the sidecar is derived from the matrix, so fix
  `disposition-matrix.md` and rerun `gen_analysis_sidecar.py` instead of
  editing `analysis.json`. The one inverted component and its reasons are in
  [weightedSemaphore](../examples/weighted-semaphore/domain-analysis/weightedSemaphore/README.md#sidecar-is-the-source).
- `dsc_check.py` needs `jsonschema` to validate the sidecar; without it, it
  exits 1 with "jsonschema is not installed, so the sidecar contract cannot
  be validated" unless `--allow-no-schema` is passed, which accepts
  structural checks only.
- `dsc_stamp.py` stamps `analyzedSha` only after the checker passes. When
  the check fails, it exits 1 and writes nothing.
- `refresh_citations.py` reports unresolved citations and never guesses or
  drops them.
- Every guard group outcome from `guard_proofs.check_group` is `proven` or
  `violation`. Guards that cannot be formalized never reach the module;
  they are marked `not-formalizable: <category>` instead. A z3 `unknown`
  result is a `violation` with a "PA-1 unknown" or "PA-2 unknown" finding,
  never `proven`.
- `local_budget.Budget` rejects any reservation that would push the ledger
  total over its limit (`BudgetExceeded`).
  - A new ledger takes the requested limit, or 2,000,000 microdollars ($2)
    by default.
  - Opening an existing ledger with a different explicit limit raises
    `ValueError("budget limit differs from existing ledger")` and changes
    nothing.
  - Only `set_limit` (`local_models.py --ledger PATH set-limit N`) changes
    the stored limit. It accepts any positive integer, including one below
    the current total; every later reservation then fails.
- Jev results are advisory (`jev_local.py` docstring): the caller keeps
  the source and decides what to do with the returned probability.
- In `mutation_verdict.py`, a process failure alone never proves a mutant
  kill.
- `gen_rules.py --check` requires every checker rule in
  `formats/rules.toml` to have a `checker_ref` and a `selftest_ref`, and
  requires the generated blocks to match the registry.
  - A `selftest_ref` of `"TODO"` passes `--check` (exit 0) with a
    "selftest backlog" warning, although the module docstring calls it
    "never a pass".
  - Where the `selftest_ref` entries point is listed in
    [selftest Invariants](./selftest/README.md#invariants).

### Tool files watched by manifests

Three [manifests](../README.md#glossary) list tool files in their
`watchPaths`. A committed change to one of these files makes that manifest
stale, and the CI step named below fails until the owning analysis is
reconciled and `analyzedSha` is re-pinned. File names below are relative
to `tools/`.

- `examples/weighted-semaphore/domain-analysis/weightedSemaphore/manifest.json`
  watches `check_matrix_mutation.py`, `mutation_verdict.py`,
  `cell_rationale.py`, `semaphore_f09.py` and `check_fault_mutants.py`.
  - Checked by CI step "weighted semaphore current model and cells", which
    runs `dsc_check.py --repo`.
  - Owner:
    [weightedSemaphore](../examples/weighted-semaphore/domain-analysis/weightedSemaphore/README.md).
- `examples/grpc-addrconn/late-completion-manifest.json` watches
  `late_completion.py`, `addrconn_late.py`, `check_late_workflow.py`,
  `selftest/test_late_completion.py`, `selftest/test_late_adapter.py` and
  `selftest/test_late_workflow.py`.
  - Checked by `addrconn_late.py` (`verify_anchor`) in CI step "reusable
    late-completion oracle and addrConn reference".
  - Owner, listing every watched path:
    [late-completion Invariants](../examples/grpc-addrconn/README.md#late-completion-invariants).
- `examples/grpc-addrconn/harness-manifest.json` watches `addrconn_f09.py`.
  - Checked by `addrconn_f09.py` (`verify_harness`) in CI step "pinned
    addrConn backoff slice and decisions".
  - Owner: [grpc-addrconn](../examples/grpc-addrconn/README.md#analysis-and-harness-manifests).

## Side Effects

- Network:
  - `local_models.py` and `jev_local.py` POST to `FLASH_URL`
    (`https://api.deepseek.com/chat/completions`) and `JEV_URL`
    (`https://api.typesafe.ai/v1/systemone`).
    - `local_models.py` reads `DEEPSEEK_API_KEY` and `TYPESAFE_API_KEY`.
    - `jev_local.py` reads only `TYPESAFE_API_KEY` and posts only to
      `JEV_URL`.
  - `addrconn_late.py` and `addrconn_f09.py` clone grpc-go unless
    `--checkout` is given; see the addrConn runner entries below.
  - `run_benchmark.py` clones the benchmark repositories.
  - `run_sol_pilot.py:prepare` runs `go mod download`.
  - When `uv` is on `PATH`, `run_tool_tests.py` runs each tool through
    `uv run --with jsonschema python3`. That can download `jsonschema` and
    bypasses the active virtualenv. Without `uv`, it uses the current
    interpreter (`sys.executable`).
- Cost:
  - DeepSeek and Typesafe calls are charged to the caller's API accounts,
    under the ledger cap (default under [Invariants](#invariants)).
  - Codex CLI sessions run on the signed-in Codex/ChatGPT account and use
    its quota.
- Import-time execution: these four are the only `tools/*.py` files that
  have no `__main__` guard and do work at module level, so importing one
  runs it (the other guardless files are libraries that only define
  functions, classes and constants):
  - `check_pack_consistency.py` runs `gen_rules.py --check`,
    `gen_odc_table.py --check` and `git describe`, and may call
    `sys.exit(1)`;
  - `fresh_pair_smoke.py` starts a Codex session (unless `--audit` is in
    `sys.argv`) and overwrites
    `docs/evidence/routing-fresh-pair/preflight-model-smoke.json`;
  - `routing_label_review.py` and `gepa_prospective_reference.py` create
    their review directory under `docs/evidence/`, fail if it already
    exists, and start Codex sessions.
- SQLite: `local_budget.Budget` creates and updates the `config` and
  `calls` tables in the `--ledger` file, using `BEGIN IMMEDIATE`
  transactions.
- Git:
  - `dsc_check.py` runs `git diff --name-only <sha>..HEAD -- <watchPaths>`,
    only with `--repo` and a non-`WORKTREE` `analyzedSha`.
  - `dsc_stamp.py` and `pilot_artifacts.py` run `git rev-parse HEAD`.
  - `refresh_citations.py` runs `git show <sha>:<path>`.
  - `addrconn_f09.py` and `addrconn_late.py` run read-only git commands;
    see the addrConn runner entries below.
  - `check_pack_consistency.py` runs `git describe --tags --abbrev=0`.
  - `run_sol_pilot.py`:
    - `prepare` runs `git init`, `git fetch`, `git checkout` in a new
      checkout and `git archive` of the pack at the pinned SHA;
    - `main` runs `git rev-parse --verify` on the pack SHA, then
      `git rev-parse HEAD` in each arm's sandboxed checkout to confirm the
      source SHA.
  - `run_flash_pilot.py` runs `git rev-parse --verify` on the pack SHA and
    reuses `prepare`.
  - `run_fresh_routing_pair.py` reuses `prepare` and runs
    `git status --porcelain --untracked-files=all` in each arm's checkout.
- File writes:
  - `gen_analysis_sidecar.py` writes `analysis.json`.
  - `dsc_stamp.py` rewrites `manifest.json` with the new `analyzedSha` and
    `date`.
  - `refresh_citations.py` rewrites analysis artifacts unless `--dry-run`
    is given.
  - `gen_rules.py --write` rewrites the generated blocks in the prompts,
    `AGENTS.md` and `README.md`.
  - `gen_odc_table.py --write` and `benchmark_evidence.py --write-readme`
    rewrite `tests/benchmarks/README.md`.
  - `gen_matrix_scaffold.py --write` writes a matrix scaffold.
  - `gen_mutant_variants.py` writes tracked variant files unless `--check`
    is given.
  - `check_late_workflow.py` writes `workflow-receipt.json`.
  - These write the file named by an `--out` option: `part_b_pack.py` and
    `dsc_blind.py`.
  - These write the file named by an `--output` option:
    - `local_models.py`; its `blind` subcommand also writes
      `<output stem>.package.md`, and `<output stem>.partial.md` when a
      response is truncated;
    - `draft_cells.py`;
    - `ensemble_convergence.py`, which also writes the `--report` file.
  - `hybrid_pilot.py` and `pilot_artifacts.py` write the file named by
    their positional `output` argument.
  - The pilot, routing, GEPA and pinned-reference runners write evidence
    files.
  - `selftest/run_selftest.py` regenerates a tracked fixture in place; see
    [selftest Side Effects](./selftest/README.md#side-effects).
- Subprocesses:
  - `check_matrix_mutation.py` and `check_fault_mutants.py` copy the
    component into temporary directories and run the cell suites.
  - These start Codex CLI sessions:
    - `run_sol_pilot.py`;
    - `run_flash_pilot.py`;
    - `run_fresh_routing_pair.py`;
    - `fresh_pair_smoke.py`, unless `--audit` is given;
    - `fresh_pair_server.py`;
    - `run_gepa_comparison.py` and the runners built on its `Experiment`
      class: `run_gepa_*`, `run_routing_label_eval.py`,
      `routing_label_review.py` and `gepa_prospective_reference.py`.
  - `semaphore_f09.py` and `gobreaker_late_readiness.py` run
    `go test -race` against pinned sources.
  - `dsc_stamp.py` runs `dsc_check.py`.
  - `check_pack_consistency.py` runs `gen_rules.py --check` and
    `gen_odc_table.py --check`.
- addrConn runners (clone, git calls, Go runs and the pack tools they
  start are documented in
  [grpc-addrconn Side Effects](../examples/grpc-addrconn/README.md#side-effects)):
  - `addrconn_f09.py` — clones grpc-go unless `--checkout` is given, runs
    git, Go and pack-checker subprocesses, and writes evidence files;
  - `addrconn_late.py` — clones grpc-go unless `--checkout` is given,
    runs git, Go and pack-checker subprocesses, and writes evidence files.

## Verification

Commands run from the repository root and assume the dev requirements are
installed (see [System Verification](../README.md#system-verification)).

These gates need no Go toolchain and no API keys, and each exits 0 when
green. CI runs each of them in job `consistency`.

- Run: `python3 tools/selftest/run_selftest.py`
- Run: `python3 tools/run_tool_tests.py`
- Run: `python3 tools/gen_rules.py --selftest`
- Run: `python3 tools/check_pack_consistency.py`
- Run: `python3 -m mypy`
  - CI installs `tools/requirements-dev.txt` and
    `docs/evidence/gepa-bounded/requirements.txt` before this step. Install
    both to match CI's type resolution; `mypy.ini` only tells mypy to
    ignore missing `gepa.*` imports.

The per-tool selftests, their CI steps and the per-job counts are in
[selftest Verification](./selftest/README.md#verification). Two CI steps
that cover the tools in this directory start like this:

- CI step "local model routing selftests" (job `consistency`), first
  commands in order:
  - Run: `python3 tools/selftest/test_local_budget.py`
  - Run: `python3 tools/selftest/test_local_models.py`
- CI step "GEPA evaluator, search adapter and accounting red probes" (job
  `gepa-evaluation`), first command (needs the `gepa` requirements file):
  - Run: `python3 tools/selftest/test_gepa_eval.py`
