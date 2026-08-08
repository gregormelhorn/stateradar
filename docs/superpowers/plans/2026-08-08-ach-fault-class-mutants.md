# ACH Fault-Class Mutant (F-04 Sneak-Path) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove roadmap item 8 end-to-end on one fault class: a behavioral cell suite kills an F-04 sneak-path implementation mutant, and a mirroring string-comparison suite provably survives it.

**Architecture:** `tests/golden-mini` becomes a real fixture: `src/mini.py` is a real 3-state machine, `tests/test_cell_suite.py` drives it through the declared seam against the matrix read from `{analysis_dir}`. A new `tools/check_fault_mutants.py` swaps hand-authored implementation variants inside isolated component copies and reports `KILLED`/`SURVIVED`/`ERROR`/`BLOCKED`. The same behavioral suite keeps killing all nine item-7 spec mutants.

**Tech Stack:** Python 3 stdlib (`argparse`, `dataclasses`, `importlib.util`, `json`, `pathlib`, `shutil`, `subprocess`, `tempfile`, `time`), the existing golden-mini fixture, the existing selftest framework.

## Global Constraints

- No binder-driven mutant generation; variants are explicit files shipped with the component.
- Only F-04 is in scope. No other fault classes.
- No `rules.toml` schema change; the existing `binder = "sneak-path"` field already names the operator.
- No change to `tools/check_matrix_mutation.py`.
- The checker never patches code; it swaps pre-authored variant files.
- `fault-mutants.json` requires `formatVersion: 1`, an argv `testCommand` with exactly one `{analysis_dir}` token, and a non-empty `mutants` list.
- Every mutant entry requires `fault`, `id`, `target`, `variant`, and `cell` string fields; `variant` must exist relative to the resolved component root.
- Verdicts: baseline failure or timeout is `BLOCKED`; nonzero mutant exit is `KILLED`; zero is `SURVIVED`; timeout or launch error is `ERROR`.
- Before committing to `main`, run the full pack gate set and paste actual outputs into the commit body.
- No release, tag, or push without explicit user instruction.

---

## File Structure

| Path | Responsibility |
|---|---|
| `tests/golden-mini/src/mini.py` | Real 3-state machine honoring the 3×3 matrix. Declared seam: `Mini.deliver(event_id)`. |
| `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py` | F-04 variant: `Closed × M1` sneak-accepts instead of rejecting. |
| `tests/golden-mini/domain-analysis/mini/disposition-matrix.md` | Updated citations to the new `mini.py` line numbers. |
| `tests/golden-mini/expected/analysis.json` | Regenerated sidecar carrying the new citations. |
| `tests/golden-mini/domain-analysis/mini/fault-mutants.json` | Item-8 opt-in config: one F-04 mutant. |
| `tests/golden-mini/tests/test_cell_suite.py` | Behavioral suite: parses matrix, navigates via seam, asserts outcomes. |
| `tools/check_fault_mutants.py` | New checker: baseline + variant swap + verdicts. |
| `tools/selftest/run_selftest.py` | New red/green cases for the fault-mutant checker. |
| `tools/check_pack_consistency.py` | Registers `fault-mutants.json` as a Testgen artifact. |
| `prompts/04-testgen.md` | Fault-class hardening subsection defining the contract. |
| `README.md` | Tool list entry for `check_fault_mutants`. |
| `docs/roadmap.md` | Item 8 partial status: F-04 shipped. |
| `docs/superpowers/plans/2026-08-08-ach-fault-class-mutants.md` | This execution checklist. |

## Canonical Contracts

**Behavioral suite outcome mapping.** For each matrix cell, the suite maps
`Mini` outcomes to dispositions:

| Matrix disposition | Required behavior |
|---|---|
| `transition →X` | `deliver` returns `"transition"` and projected `state == X` |
| `handle` | `deliver` returns `"handled"` and state unchanged (counter may increment) |
| `ignore (documented)` | `deliver` returns `"ignored"` and state unchanged |
| `reject` | `deliver` raises `RejectedError` and state unchanged |

**Seam navigation (no state injection):** `Idle` = fresh instance; `Open` =
deliver `M1`; `Closed` = deliver `M1`, then `M2`.

**`fault-mutants.json` golden-mini content:**

```json
{
  "formatVersion": 1,
  "testCommand": ["python3", "tests/test_cell_suite.py", "{analysis_dir}"],
  "workingDirectory": "../..",
  "timeoutSeconds": 5,
  "mutants": [
    {
      "fault": "F-04",
      "id": "F-04-sneak-path-Closed-M1",
      "target": "src/mini.py",
      "variant": "src/mutants/mini.F-04-sneak-path.py",
      "cell": "Closed x M1"
    }
  ]
}
```

`workingDirectory` (`../..` from `domain-analysis/mini/`) resolves to
`tests/golden-mini` — the component root. The checker copies the whole
component root per run, swaps `target` with `variant`, and substitutes
`{analysis_dir}` with the analysis directory inside that copy.

---

### Task 1: Real golden-mini implementation and citation updates

**Files:**
- Rewrite: `tests/golden-mini/src/mini.py`
- Modify: `tests/golden-mini/domain-analysis/mini/disposition-matrix.md`
- Regenerate: `tests/golden-mini/expected/analysis.json`

**Interfaces:**
- Produces: `Mini` class with `state: str`, `dup_count: int`,
  `deliver(event: str) -> str`, and module-level `RejectedError`. Task 2
  imports exactly these names.
- Produces: matrix citations pointing at the lines listed below.

- [ ] **Step 1: Write the real state machine**

Overwrite `tests/golden-mini/src/mini.py` with exactly this content
(line numbers are load-bearing for Task 1 Step 2 citations):

```python
"""golden-mini fixture component: a 3-state event-driven machine."""


class RejectedError(Exception):
    """The component rejected the event."""


class Mini:
    """Three-state machine used by the StateRadar golden fixture."""

    def __init__(self) -> None:
        self.state = "Idle"
        self.dup_count = 0

    def deliver(self, event: str) -> str:
        """Deliver one event through the declared seam."""
        if event == "M1":
            if self.state == "Idle":
                self.state = "Open"
                return "transition"
            if self.state == "Open":
                return "ignored"
            raise RejectedError("M1 rejected in Closed")
        if event == "M2":
            if self.state == "Open":
                self.state = "Closed"
                return "transition"
            return "ignored"
        if event == "UV-M1-dup":
            self.dup_count += 1
            return "handled"
        raise ValueError(event)
```

Resulting lines: `self.state = "Open"` at 19, `return "ignored"` (Open×M1)
at 22, `raise RejectedError` at 23, `self.state = "Closed"` at 26,
`return "ignored"` (M2 fall-through) at 28, `self.dup_count += 1` at 30.

- [ ] **Step 2: Update the matrix citations**

In `tests/golden-mini/domain-analysis/mini/disposition-matrix.md`, replace
each citation with the new line number:

| Old | New |
|---|---|
| `mini.py:10` | `mini.py:19` |
| `mini.py:20` | `mini.py:28` |
| `mini.py:30` | `mini.py:30` |
| `mini.py:40` | `mini.py:22` |
| `mini.py:50` | `mini.py:26` |
| `mini.py:60` | `mini.py:30` |
| `mini.py:70` | `mini.py:23` |
| `mini.py:80` | `mini.py:28` |
| `mini.py:90` | `mini.py:30` |

Do not change any disposition text, declaration, or row order.

- [ ] **Step 3: Regenerate the expected sidecar**

```bash
python3 tools/gen_analysis_sidecar.py --root tests/golden-mini
cp tests/golden-mini/domain-analysis/mini/analysis.json \
   tests/golden-mini/expected/analysis.json
python3 tools/run_tool_tests.py
```

Expected: `run_tool_tests.py` reports `2/2 cases pass`. The drift check
compares the generated sidecar with the regenerated expected file; both
carry the new citations.

- [ ] **Step 4: Record the old-suite red baseline**

```bash
cd tests/golden-mini && python3 tests/test_cell_suite.py domain-analysis/mini; echo "exit=$?"
```

Expected: exit 1 — the old string-comparison suite compares exact cell
strings and the citations changed. This proves Task 2 must replace the
suite, not just extend it. Save the output for the final commit body.

### Task 2: Behavioral cell suite (replaces string comparison)

**Files:**
- Rewrite: `tests/golden-mini/tests/test_cell_suite.py`

**Interfaces:**
- Consumes: `Mini`, `RejectedError` from Task 1; `disposition-matrix.md`
  via the `{analysis_dir}` argv.
- Produces: exit 0 with `CELL SUITE: OK` on full match; exit 1 with
  `MISMATCH <state> × <event>: expected <disposition>, got <actual>` lines
  otherwise. Used by both `check_matrix_mutation.py` (item 7) and
  `check_fault_mutants.py` (item 8).

- [ ] **Step 1: Write the behavioral suite**

Overwrite `tests/golden-mini/tests/test_cell_suite.py`:

```python
#!/usr/bin/env python3
"""Golden-mini behavioral cell suite: drives Mini through the declared seam."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

NAVIGATE = {"Idle": [], "Open": ["M1"], "Closed": ["M1", "M2"]}
EVENTS = ["M1", "M2", "UV-M1-dup"]


def load_mini(component_root: Path):
    spec = importlib.util.spec_from_file_location(
        "mini_impl", component_root / "src" / "mini.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_matrix(path: Path) -> dict[tuple[str, str], str]:
    rows: dict[tuple[str, str], str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("| state"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or set(cells[0]) <= {"-", ":"}:
            continue
        state = cells[0].strip("*")
        for event, raw in zip(EVENTS, cells[1:], strict=True):
            token = raw.split("`")[0].strip()
            rows[(state, event)] = token
    return rows


def check(module, state: str, event: str, expected: str) -> str | None:
    kind = expected.split()[0]  # transition | handle | ignore | reject
    m = module.Mini()
    for nav in NAVIGATE[state]:
        m.deliver(nav)
    before = m.state
    try:
        outcome = m.deliver(event)
    except module.RejectedError:
        return None if kind == "reject" and m.state == before else (
            f"expected {expected}, got reject"
        )
    if kind == "transition":
        target = expected.split("→", 1)[1].strip()
        if outcome == "transition" and m.state == target:
            return None
        return f"expected {expected}, got {outcome} state={m.state}"
    if kind == "handle":
        if outcome == "handled" and m.state == before:
            return None
        return f"expected handle, got {outcome} state={m.state}"
    if kind == "ignore":
        if outcome == "ignored" and m.state == before:
            return None
        return f"expected ignore, got {outcome} state={m.state}"
    if kind == "reject":
        return f"expected reject, got {outcome}"
    return f"unknown disposition {expected}"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("CELL SUITE: expected one analysis directory", file=sys.stderr)
        return 2
    analysis_dir = Path(argv[1]).resolve()
    component_root = analysis_dir.parent.parent
    module = load_mini(component_root)
    matrix = parse_matrix(analysis_dir / "disposition-matrix.md")
    failures = 0
    for (state, event), expected in sorted(matrix.items()):
        problem = check(module, state, event, expected)
        if problem:
            print(f"MISMATCH {state} × {event}: {problem}")
            failures += 1
    if failures:
        return 1
    print("CELL SUITE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

Note: `parse_matrix` extracts the disposition token before the citation
backtick, matching the matrix cell format.

- [ ] **Step 2: Prove the baseline green**

```bash
cd tests/golden-mini && python3 tests/test_cell_suite.py domain-analysis/mini
```

Expected: `CELL SUITE: OK`, exit 0.

- [ ] **Step 3: Prove the item-7 regression**

```bash
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
```

Expected: `MUTATION CHECK: OK (killed=9 survived=0 errors=0 blocked=0)`.
Every spec mutant is still killed behaviorally: `transition→ignore` on
`Idle × M1` expects ignored but Mini still transitions; `handle→ignore` on
`UV-M1-dup` expects ignored but Mini still increments `dup_count`; target
swaps expect the wrong projected state.

- [ ] **Step 4: Run the selftest to confirm existing cases stay green**

```bash
uv run --with-requirements tools/requirements-dev.txt \
  python3 tools/selftest/run_selftest.py
```

Expected: `SELFTEST: OK` — the existing
`mutation checker golden-mini kills supported mutants` case passes with
the behavioral suite.

### Task 3: Fault-mutant config, variant, and checker (TDD)

**Files:**
- Create: `tests/golden-mini/domain-analysis/mini/fault-mutants.json`
- Create: `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py`
- Create: `tools/check_fault_mutants.py`
- Test: `tools/selftest/run_selftest.py`

**Interfaces:**
- Consumes: the behavioral suite from Task 2.
- Produces: `main(argv: Sequence[str] | None = None) -> int` in
  `check_fault_mutants.py`, accepting exactly one analysis-directory path.

- [ ] **Step 1: Create the opt-in config and the sneak-path variant**

Create `tests/golden-mini/domain-analysis/mini/fault-mutants.json` with the
exact golden-mini contract from the Canonical Contracts section.

Create `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py` as an exact
copy of the Task 1 `mini.py` with one change — the `RejectedError` raise
line becomes:

```python
            return "ignored"  # F-04 sneak path: Closed x M1 accepted
```

- [ ] **Step 2: Record the missing-checker red baseline**

```bash
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
```

Expected: exit 2, `can't open file ... check_fault_mutants.py`. Save output.

- [ ] **Step 3: Add the failing selftest cases first**

In `tools/selftest/run_selftest.py`, after the existing
`mutation checker blocks timed-out baseline` case, add:

```python
        def fault_check(adir: Path) -> tuple[int, str]:
            r = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "check_fault_mutants.py"), str(adir)],
                capture_output=True, text=True)
            return r.returncode, (r.stdout + r.stderr).strip()

        def component(tmp: Path, name: str) -> Path:
            dst = tmp / name
            shutil.copytree(ROOT / "tests" / "golden-mini", dst)
            return dst

        fdir = ROOT / "tests" / "golden-mini" / "domain-analysis" / "mini"
        expect("fault mutant baseline kills F-04 sneak path", False,
               *fault_check(fdir), needle="FAULT MUTANTS: OK")
        rc, out = fault_check(fdir)
        if "KILLED" not in out:
            failures.append("fault mutant kill proof: no KILLED line\n" + out)
        else:
            print("  ok  fault mutant kill proof (passes)")

        mirror = component(tmp, "mirror-suite")
        cfg = json.loads((mirror / "domain-analysis" / "mini" / "fault-mutants.json").read_text())
        cfg["testCommand"] = ["python3", "-c", "import sys; sys.exit(0)", "{analysis_dir}"]
        (mirror / "domain-analysis" / "mini" / "fault-mutants.json").write_text(json.dumps(cfg))
        expect("mirroring suite survives F-04 mutant (F-21 blind spot)", True,
               *fault_check(mirror / "domain-analysis" / "mini"), needle="SURVIVED")
```

Expected before Task 3 Step 4: the new cases fail because the checker does
not exist.

- [ ] **Step 4: Implement `tools/check_fault_mutants.py`**

Model it on `tools/check_matrix_mutation.py` with these differences:

```python
@dataclass(frozen=True)
class Mutant:
    fault: str
    identifier: str
    target: str
    variant: str
    cell: str
```

`load_config(adir)` additionally requires a non-empty `mutants` list where
every entry has non-empty `fault`, `id`, `target`, `variant`, and `cell`
strings, and the `variant` file exists under the resolved component root.
Missing or malformed entries raise `ConfigError` with a specific message
(e.g. `mutant 0: missing variant file src/mutants/mini.F-04-sneak-path.py`).

Run flow:

```python
component_root = (config_path.parent / working).resolve()
rel_analysis = config_path.parent.relative_to(component_root)
# per run:
root_copy = tmp / name; shutil.copytree(component_root, root_copy)
# baseline: run command with {analysis_dir} = root_copy / rel_analysis
# per mutant: fresh copy; replace root_copy/target with root_copy/variant content
```

Verdicts and output lines match item 7 conventions:

```text
BASELINE: OK
MUT-001 KILLED fault=F-04 cell=Closed x M1 target=src/mini.py exit=1 duration=0.030s
FAULT MUTANTS: OK (killed=1 survived=0 errors=0 blocked=0)
```

Any `SURVIVED` or `ERROR` exits 1 with `FAULT MUTANTS: FAIL (...)`.

- [ ] **Step 5: Run the red/green proofs**

```bash
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
uv run --with-requirements tools/requirements-dev.txt \
  python3 tools/selftest/run_selftest.py
```

Expected: `FAULT MUTANTS: OK (killed=1 survived=0 errors=0 blocked=0)`,
and the selftest shows the mirroring-survives case as `fails as required`.

### Task 4: Config-error and blocked-baseline selftests

**Files:**
- Modify: `tools/selftest/run_selftest.py`

**Interfaces:**
- Consumes: `fault_check` and `component` helpers from Task 3.

- [ ] **Step 1: Add missing-config case**

```python
        no_fm = component(tmp, "fault-no-config")
        (no_fm / "domain-analysis" / "mini" / "fault-mutants.json").unlink()
        expect("fault mutant rejects missing config", True,
               *fault_check(no_fm / "domain-analysis" / "mini"),
               needle="CONFIG ERROR: missing fault-mutants.json")
```

- [ ] **Step 2: Add bad-formatVersion and missing-variant cases**

```python
        bad_ver = component(tmp, "fault-bad-version")
        cfg = json.loads((bad_ver / "domain-analysis" / "mini" / "fault-mutants.json").read_text())
        cfg["formatVersion"] = 2
        (bad_ver / "domain-analysis" / "mini" / "fault-mutants.json").write_text(json.dumps(cfg))
        expect("fault mutant rejects formatVersion 2", True,
               *fault_check(bad_ver / "domain-analysis" / "mini"),
               needle="CONFIG ERROR: formatVersion must be integer 1")

        no_variant = component(tmp, "fault-no-variant")
        (no_variant / "src" / "mutants" / "mini.F-04-sneak-path.py").unlink()
        expect("fault mutant rejects missing variant file", True,
               *fault_check(no_variant / "domain-analysis" / "mini"),
               needle="missing variant file")
```

- [ ] **Step 3: Add placeholder and blocked-baseline cases**

```python
        no_ph = component(tmp, "fault-no-placeholder")
        cfg = json.loads((no_ph / "domain-analysis" / "mini" / "fault-mutants.json").read_text())
        cfg["testCommand"] = ["python3", "tests/test_cell_suite.py"]
        (no_ph / "domain-analysis" / "mini" / "fault-mutants.json").write_text(json.dumps(cfg))
        expect("fault mutant rejects missing placeholder", True,
               *fault_check(no_ph / "domain-analysis" / "mini"),
               needle="exactly one {analysis_dir}")

        blocked = component(tmp, "fault-blocked")
        cfg = json.loads((blocked / "domain-analysis" / "mini" / "fault-mutants.json").read_text())
        cfg["testCommand"] = ["python3", "-c", "raise SystemExit(3)", "{analysis_dir}"]
        (blocked / "domain-analysis" / "mini" / "fault-mutants.json").write_text(json.dumps(cfg))
        expect("fault mutant blocks failed baseline", True,
               *fault_check(blocked / "domain-analysis" / "mini"),
               needle="BLOCKED: baseline exit=3")
```

- [ ] **Step 4: Run the full selftest**

```bash
uv run --with-requirements tools/requirements-dev.txt \
  python3 tools/selftest/run_selftest.py
```

Expected: `SELFTEST: OK` with all new cases passing.

### Task 5: Registration, prompt, docs, full gates, commit

**Files:**
- Modify: `tools/check_pack_consistency.py`, `prompts/04-testgen.md`,
  `README.md`, `docs/roadmap.md`

**Interfaces:**
- Consumes: stable `fault-mutants.json` contract from Tasks 3–4.

- [ ] **Step 1: Register the artifact and run the red probe**

Add `"fault-mutants.json": ["04-testgen.md"],` to `ARTIFACTS` in
`tools/check_pack_consistency.py`, adjacent to `matrix-mutation.json`.

```bash
python3 tools/check_pack_consistency.py
```

Expected: FAIL — `artifact 'fault-mutants.json' not defined in
['04-testgen.md']`. Save the output as the registration red probe.

- [ ] **Step 2: Define the contract in the Testgen prompt**

After the `matrix-mutation.json` subsection in `prompts/04-testgen.md`, add
a fault-class hardening subsection containing: the F-04 sneak-path operator
definition (an `ignore (documented)` or `reject` cell accepts the event),
the `fault-mutants.json` schema exactly as in the Canonical Contracts
section, the command `python3 tools/check_fault_mutants.py
domain-analysis/<component>`, and the rule that a surviving mutant is a
suite finding, never a reason to weaken or skip a cell test.

- [ ] **Step 3: Run the registration green check**

```bash
python3 tools/check_pack_consistency.py
```

Expected: `PACK CONSISTENCY: OK (20 artifacts, registry, version 1.50)`.

- [ ] **Step 4: README and roadmap**

Add `check_fault_mutants (runs declared cell suites against hand-authored
implementation mutants per fault class)` to the `tools/` list in
`README.md`. In `docs/roadmap.md`, change item 8's status to:

```text
**Status:** 🔶 Partially shipped — F-04 sneak-path end-to-end. The
`fault-mutants.json` contract and `tools/check_fault_mutants.py` prove a
behavioral cell suite kills a sneak-path implementation mutant while a
mirroring suite survives. Remaining fault classes pending.
```

- [ ] **Step 5: Full gate set**

```bash
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
python3 tools/benchmark_evidence.py
git diff --check
git status --short
```

Expected: all green; 20 artifacts; 2/2 tool cases; 6/6 benchmarks.

- [ ] **Step 6: Commit**

```bash
git add tests/golden-mini/ tools/check_fault_mutants.py \
  tools/selftest/run_selftest.py tools/check_pack_consistency.py \
  prompts/04-testgen.md README.md docs/roadmap.md \
  docs/superpowers/plans/2026-08-08-ach-fault-class-mutants.md
git commit -m "Add ACH fault-class mutant checker: F-04 sneak-path" \
  -m "Paste the four red baselines (old suite, missing checker, registration)
and the green outputs (baseline, KILLED line, mirroring SURVIVED, full gates)."
```

- [ ] **Step 7: Stop**

No release, tag, push, or binder-generation work. Report the commit, the
red/green evidence, and the remaining roadmap state.

## Execution Handoff

Execute only Tasks 1–5. The next roadmap work is expanding fault classes
beyond F-04, which needs a new user instruction.
