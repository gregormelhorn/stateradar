# Matrix Mutation Checker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an opt-in checker that mutates temporary disposition-matrix copies and fails when a declared cell suite does not kill every supported mutant.

**Architecture:** `tools/check_matrix_mutation.py` reads `matrix-mutation.json` beside a component matrix. It validates the JSON contract, runs a baseline command against a temporary analysis copy, then runs the same argv command against one mutated copy per deterministic mutant. Golden-mini supplies a small cell-suite command that consumes the supplied analysis directory. The deterministic selftest proves weak suites fail and the fixture suite kills all mutants.

**Tech Stack:** Python 3 standard library (`argparse`, `dataclasses`, `json`, `pathlib`, `shutil`, `subprocess`, `tempfile`, `time`), Markdown tables, JSON configuration, existing StateRadar selftest framework.

## Global Constraints

- Do not mutate component source, generated tests, sidecars, decision records, or question registers.
- Do not invoke a shell. Pass `testCommand` directly to `subprocess.run()` as an argv list.
- `matrix-mutation.json` requires `formatVersion: 1`, a non-empty argv `testCommand`, and exactly one `{analysis_dir}` element.
- `workingDirectory` is optional and resolves relative to the configuration directory. Its default is that directory.
- `timeoutSeconds` is optional, positive, integral, and defaults to 30.
- The baseline command must pass before mutation. A baseline failure or timeout is `BLOCKED`, not a killed mutant.
- Supported mutations are only transition-to-ignore, transition-target swap, and handle-to-ignore.
- The checker exits zero only when the baseline passes and every mutant is killed.
- Do not add a new methodology rule or fault class. Register `matrix-mutation.json` as a Testgen artifact.
- Do not run upstream projects, alter silenceper, create a release, create a tag, or push without a new user instruction.

---

## File Structure

| Path | Responsibility |
|---|---|
| `tools/check_matrix_mutation.py` | New standalone CLI, configuration validation, matrix parsing, mutation generation, isolated command execution, verdict reporting. |
| `tools/selftest/run_selftest.py` | Red and green deterministic tests for the new CLI. |
| `tests/golden-mini/domain-analysis/mini/matrix-mutation.json` | Golden-mini opt-in configuration. |
| `tests/golden-mini/tests/test_cell_suite.py` | Fixture cell suite that accepts an analysis directory and rejects mutated expected cells. |
| `tools/check_pack_consistency.py` | Declares `matrix-mutation.json` as a Testgen-produced artifact. |
| `prompts/04-testgen.md` | Defines the configuration contract for consumer Testgen output. |
| `README.md` | Lists the checker and its local command. |
| `docs/roadmap.md` | Marks roadmap item 7 shipped only after red/green proof exists. |
| `docs/superpowers/plans/2026-08-07-matrix-mutation-checker.md` | This execution checklist. |

## CLI and Configuration Contract

```text
python3 tools/check_matrix_mutation.py <analysis-dir>
```

The analysis directory contains this file:

```json
{
  "formatVersion": 1,
  "testCommand": [
    "python3",
    "tests/test_cell_suite.py",
    "{analysis_dir}"
  ],
  "workingDirectory": "../..",
  "timeoutSeconds": 30
}
```

The CLI writes one line for the baseline. It writes one line for each mutant.
It ends with one count line.

```text
BASELINE: OK
MUT-001 KILLED state=Idle event=M1 kind=transition-to-ignore exit=1
MUTATION CHECK: OK (killed=N survived=0 errors=0 blocked=0)
```

A survivor makes the final line `MUTATION CHECK: FAIL`. Invalid configuration
uses `CONFIG ERROR:`. A failed baseline uses `BLOCKED:`. A timed-out mutation
uses `ERROR:`.

---

### Task 1: Add the golden-mini command contract and capture the red baseline

**Files:**
- Create: `tests/golden-mini/domain-analysis/mini/matrix-mutation.json`
- Create: `tests/golden-mini/tests/test_cell_suite.py`
- Test: manual command against the future checker

**Interfaces:**
- Consumes: the existing golden-mini `disposition-matrix.md`.
- Produces: a portable command that receives a temporary analysis directory as `sys.argv[1]`.

- [x] **Step 1: Add the fixture configuration**

Create `tests/golden-mini/domain-analysis/mini/matrix-mutation.json`:

```json
{
  "formatVersion": 1,
  "testCommand": [
    "python3",
    "tests/test_cell_suite.py",
    "{analysis_dir}"
  ],
  "workingDirectory": "../..",
  "timeoutSeconds": 5
}
```

The configuration directory is `tests/golden-mini/domain-analysis/mini`.
`../..` therefore resolves to `tests/golden-mini`, where the fixture script
will live.

- [x] **Step 2: Add the fixture cell-suite command**

Create `tests/golden-mini/tests/test_cell_suite.py`. It must require exactly
one analysis-directory argument. It must read
`<analysis-dir>/disposition-matrix.md`. It must parse the one fixture table,
then compare these complete cell strings after `strip()`:

```python
EXPECTED = {
    "Idle": {
        "M1": "transition →Open `mini.py:10`",
        "M2": "ignore (documented) `mini.py:20`",
        "UV-M1-dup": "handle (counted) `mini.py:30`",
    },
    "Open": {
        "M1": "ignore (documented) `mini.py:40`",
        "M2": "transition →Closed `mini.py:50`",
        "UV-M1-dup": "handle (counted) `mini.py:60`",
    },
    "Closed": {
        "M1": "reject `mini.py:70`",
        "M2": "ignore (documented) `mini.py:80`",
        "UV-M1-dup": "handle (counted) `mini.py:90`",
    },
}
```

Use `sys.exit(2)` for wrong arguments or parse errors. Use `sys.exit(1)` for
an expected-cell mismatch. Print `CELL SUITE: OK` only after all nine cells
match.

Use this parser shape:

```python
def parse_matrix(path: Path) -> dict[str, dict[str, str]]:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines()
             if line.startswith("|")]
    header = [part.strip() for part in lines[0].strip("|").split("|")]
    events = header[1:]
    result: dict[str, dict[str, str]] = {}
    for line in lines[2:]:
        cells = [part.strip() for part in line.strip("|").split("|")]
        state = cells[0].strip("*")
        result[state] = dict(zip(events, cells[1:], strict=True))
    return result
```

- [x] **Step 3: Run the fixture command against the unmodified analysis**

Run:

```bash
cd tests/golden-mini
python3 tests/test_cell_suite.py domain-analysis/mini
```

Expected: `CELL SUITE: OK` and exit zero.

- [x] **Step 4: Record the missing-tool red baseline**

Run:

```bash
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
```

Expected before Task 2: nonzero exit because the checker file does not exist.
Save the command output for the final commit Evidence block.

### Task 2: Implement configuration validation, matrix parsing, and mutation generation

**Files:**
- Create: `tools/check_matrix_mutation.py`
- Test: `tools/selftest/run_selftest.py` (new focused cases added in Task 3)

**Interfaces:**
- Consumes: `<analysis-dir>/disposition-matrix.md` and `<analysis-dir>/matrix-mutation.json`.
- Produces: immutable `Cell`, `Mutation`, and `Config` records; a sorted list of supported mutations.

- [x] **Step 1: Define the data records and CLI parser**

Create `tools/check_matrix_mutation.py` with:

```python
@dataclass(frozen=True)
class Config:
    command: tuple[str, ...]
    working_directory: Path
    timeout_seconds: int

@dataclass(frozen=True)
class Cell:
    state: str
    event: str
    raw: str
    line_index: int
    column_index: int

@dataclass(frozen=True)
class Mutation:
    identifier: str
    state: str
    event: str
    kind: str
    old: str
    new: str
    line_index: int
    column_index: int
```

Add `main(argv: Sequence[str] | None = None) -> int`. It accepts exactly one
analysis-directory path. It prints `Usage: ...` and returns 2 for invalid CLI
arguments.

- [x] **Step 2: Add a failing selftest for absent configuration**

In `tools/selftest/run_selftest.py`, add a helper:

```python
def mutation(adir: Path) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_matrix_mutation.py"), str(adir)],
        capture_output=True,
        text=True,
    )
    return result.returncode, (result.stdout + result.stderr).strip()
```

Copy the golden analysis directory with `sidecar(tmp, gm)`. Remove its
`matrix-mutation.json` file. Add this expectation:

```python
expect("mutation checker rejects missing configuration", True,
       *mutation(no_config), needle="CONFIG ERROR: missing matrix-mutation.json")
```

Run the selftest. Expected before the implementation: the new expectation
fails because the checker is missing or does not yet print the required error.

- [x] **Step 3: Implement `load_config(adir: Path) -> Config`**

Read `matrix-mutation.json` with `json.loads`. Reject and report through a
`ConfigError` exception when any condition fails:

- the file is missing or invalid JSON;
- `formatVersion` is not integer `1`;
- `testCommand` is not a non-empty list of non-empty strings;
- the command has zero or more than one `{analysis_dir}` element;
- `workingDirectory` is present but not a string or does not resolve to a directory;
- `timeoutSeconds` is present but is not a positive integer.

Resolve `workingDirectory` against `config_path.parent`. Use
`config_path.parent` when it is absent. Use 30 when `timeoutSeconds` is absent.

At top level, catch `ConfigError`, print `CONFIG ERROR: <reason>`, and return 2.

- [x] **Step 4: Implement matrix cell parsing and mutation construction**

Parse `<!-- states: ... -->` from the matrix. Parse every Markdown table with a
`state` first header. Track the source `line_index` and `column_index` of each
cell. Reject duplicate `(state, event)` cells and empty cells with `CONFIG ERROR`.

Create these mutations in sorted state/event order:

```python
def transition_to_ignore(cell: Cell) -> str | None: ...
def transition_target_swaps(cell: Cell, states: tuple[str, ...]) -> list[str]: ...
def handle_to_ignore(cell: Cell) -> str | None: ...
```

For a transition, preserve the suffix after the target citation. Replace only
`transition →<target>` with `ignore (documented)`. For a handle, replace the
leading `handle` with `ignore (documented)` and preserve the remaining suffix.
For target swaps, preserve the transition marker and suffix. Exclude the
current target. Use IDs in this exact form:

```text
MUT-001 state=<state> event=<event> kind=<kind>
```

Number IDs after sorting by state, event, mutation kind, and replacement text.

- [x] **Step 5: Run the new focused selftest**

Run:

```bash
uv run --with-requirements tools/requirements-dev.txt \
  python3 tools/selftest/run_selftest.py
```

Expected after Step 4: the missing-configuration case passes. Existing
selftests remain green. The future weak-suite and green-suite cases are added
in Task 3.

### Task 3: Execute isolated mutants and prove red/green behavior

**Files:**
- Modify: `tools/check_matrix_mutation.py`
- Modify: `tools/selftest/run_selftest.py`

**Interfaces:**
- Consumes: `Config`, `Mutation`, and the golden-mini fixture command.
- Produces: baseline, `KILLED`, `SURVIVED`, `ERROR`, and `BLOCKED` report lines.

- [x] **Step 1: Add the weak-suite red selftest**

Copy the golden analysis directory. Replace its configuration with:

```json
{
  "formatVersion": 1,
  "testCommand": [
    "python3",
    "-c",
    "import sys; raise SystemExit(0)",
    "{analysis_dir}"
  ],
  "timeoutSeconds": 5
}
```

Add this expectation:

```python
expect("mutation checker reports weak suite survivors", True,
       *mutation(weak), needle="SURVIVED")
```

Run the selftest. Expected before execution support: this expectation fails.

- [x] **Step 2: Implement temporary-copy command execution**

Add these functions:

```python
def copy_analysis(adir: Path, tmp: Path, name: str) -> Path: ...
def apply_mutation(matrix_path: Path, mutation: Mutation) -> None: ...
def command_for(config: Config, analysis_dir: Path) -> list[str]: ...
def run_command(config: Config, analysis_dir: Path) -> tuple[int, str, float]: ...
```

`copy_analysis` uses `shutil.copytree`. `apply_mutation` changes only the one
recorded table cell in the copied `disposition-matrix.md`. `command_for`
replaces the unique `{analysis_dir}` command element with `str(analysis_dir)`.
`run_command` uses:

```python
subprocess.run(
    command_for(config, analysis_dir),
    cwd=config.working_directory,
    capture_output=True,
    text=True,
    timeout=config.timeout_seconds,
    check=False,
)
```

Measure duration with `time.monotonic()`. Do not use `shell=True`.

Run the baseline first against an unmodified copy. If it exits nonzero, print
`BLOCKED: baseline exit=<code>` and return 1. If it times out, print
`BLOCKED: baseline timeout=<seconds>s` and return 1.

For each mutant, run a fresh copied analysis tree. Classify a nonzero exit as
`KILLED`, zero as `SURVIVED`, and `subprocess.TimeoutExpired` as `ERROR`.
Print the mutant details and final counts. Return 1 if a survivor or error
exists. Return 0 only if every mutant is killed.

- [x] **Step 3: Add the green golden-mini selftest**

Add this expectation:

```python
expect("mutation checker golden-mini kills supported mutants", False,
       *mutation(golden_copy), needle="MUTATION CHECK: OK")
```

Also require `KILLED` in the output and reject `SURVIVED` in the selftest
logic. This proves the fixture command receives and checks the mutated copy.

- [x] **Step 4: Add invalid-contract and execution-error selftests**

Add separate copied configurations and expectations for:

```python
# no placeholder
{"formatVersion": 1, "testCommand": ["python3", "-c", "pass"]}

# repeated placeholder
{"formatVersion": 1, "testCommand": ["python3", "{analysis_dir}", "{analysis_dir}"]}

# non-array command
{"formatVersion": 1, "testCommand": "python3 tests/test_cell_suite.py {analysis_dir}"}

# baseline failure
{"formatVersion": 1, "testCommand": ["python3", "-c", "raise SystemExit(3)", "{analysis_dir}"]}

# timeout
{"formatVersion": 1, "testCommand": ["python3", "-c", "import time; time.sleep(2)", "{analysis_dir}"], "timeoutSeconds": 1}
```

Expect `CONFIG ERROR` for the first three. Expect `BLOCKED` for baseline
failure and baseline timeout. In the two blocked cases, also assert that the
output contains no `MUT-` line.

- [x] **Step 5: Run the focused red and green proofs**

Run:

```bash
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
uv run --with-requirements tools/requirements-dev.txt \
  python3 tools/selftest/run_selftest.py
```

Expected: the direct golden-mini command ends with `MUTATION CHECK: OK`. The
selftest reports the weak-suite case as `fails as required` and the
Golden-mini case as `passes`.

### Task 4: Register the artifact and document the shipped checker

**Files:**
- Modify: `tools/check_pack_consistency.py`
- Modify: `prompts/04-testgen.md`
- Modify: `README.md`
- Modify: `docs/roadmap.md`

**Interfaces:**
- Consumes: the stable CLI and configuration contract from Tasks 1–3.
- Produces: pack consistency coverage and user-facing documentation.

- [x] **Step 1: Add the produced artifact to the pack map**

In `tools/check_pack_consistency.py`, add:

```python
"matrix-mutation.json": ["04-testgen.md"],
```

to `ARTIFACTS`, adjacent to `matrix-coverage.json`.

- [x] **Step 2: Run the registration red probe**

Run:

```bash
python3 tools/check_pack_consistency.py
```

Expected: it fails because `matrix-mutation.json` is referenced but not
defined by `04-testgen.md`. Record the output as the registration red probe.

- [x] **Step 3: Define the Testgen output contract**

In `prompts/04-testgen.md`, add a short subsection after the
`matrix-coverage.json` instruction. It must require an optional
`matrix-mutation.json` when a component has an executable cell suite. Include
the exact JSON configuration from this plan and the command:

```bash
python3 tools/check_matrix_mutation.py domain-analysis/<component>
```

State that the command must read `{analysis_dir}`. State that survivors are
coverage findings, not a reason to weaken or skip a cell test.

- [x] **Step 4: Run the registration green check**

Run:

```bash
python3 tools/check_pack_consistency.py
```

Expected: `PACK CONSISTENCY: OK`.

- [x] **Step 5: Add README tool documentation**

Add `check_matrix_mutation` to the `tools/` list in the repository-layout
section. Add this local command after the existing `dsc_check.py` example:

```bash
python3 tools/check_matrix_mutation.py domain-analysis/<component>
```

Explain in one sentence that it creates temporary matrix mutants and fails if
the declared cell suite lets one survive.

- [x] **Step 6: Mark roadmap item 7 shipped**

Replace the planned status for item 7 with a shipped status. Name
`tools/check_matrix_mutation.py`, `matrix-mutation.json`, the three supported
mutation families, and the red/green selftest. Do not modify roadmap items 8
or 9.

### Task 5: Verify the complete pack and commit

**Files:**
- Verify: all Task 1–4 files.
- Commit: checker, fixture, selftests, contract prompt, README, roadmap, pack map, and this plan.

**Interfaces:**
- Consumes: the fully documented checker and red/green evidence.
- Produces: one local pack commit with all gates green.

- [x] **Step 1: Run focused assertions**

Run:

```bash
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
python3 - <<'PY'
from pathlib import Path
text = Path('tests/golden-mini/domain-analysis/mini/matrix-mutation.json').read_text()
assert text.count('{analysis_dir}') == 1
assert '"testCommand"' in text
print('CONFIG CONTRACT: OK')
PY
```

Expected: `MUTATION CHECK: OK` and `CONFIG CONTRACT: OK`.

- [x] **Step 2: Run the complete gate set**

Run:

```bash
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
python3 tools/benchmark_evidence.py
git diff --check
git status --short
```

Expected: selftests prove the weak-suite red case and golden-mini green case.
The pack checker reports `PACK CONSISTENCY: OK`. Tool tests report `2/2 cases
pass`. The benchmark runner reports `5 passed, 0 failed, 5 total`. Evidence
reports `2 primary`, `3 regression`, and `0 unknown`.

- [x] **Step 3: Commit the mutation checker**

```bash
git add \
  tools/check_matrix_mutation.py \
  tools/selftest/run_selftest.py \
  tools/check_pack_consistency.py \
  tests/golden-mini/domain-analysis/mini/matrix-mutation.json \
  tests/golden-mini/tests/test_cell_suite.py \
  prompts/04-testgen.md README.md docs/roadmap.md \
  docs/superpowers/plans/2026-08-07-matrix-mutation-checker.md
git commit -m "Add matrix mutation checker" \
  -m "Runs declared cell suites against isolated matrix mutants. Fails for survivor, error, or blocked results. The golden-mini fixture proves weak-suite red behavior and full-kill green behavior.\n\nEvidence:\n- Paste the missing-tool red baseline.\n- Paste the weak-suite red proof.\n- Paste the pack-registration red proof.\n- Paste the golden-mini green proof and complete gate output."
```

- [x] **Step 4: Stop**

Do not run the checker against an upstream component, alter silenceper,
implement roadmap item 8, create a release, create a tag, or push. Report the
commit, the red/green evidence, and any residual risk.

## Execution Handoff

Execute only Tasks 1 through 5. The follow-on roadmap item is the separate
ACH-style fault-class mutant design. It is not part of this implementation.
