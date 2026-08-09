# ACH Fault-Class Expansion (F-01, F-02, F-05) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the golden-mini fault-mutant fixture from one fault class to four, proving the checker and behavioral suite generalize across classes with zero contract changes.

**Architecture:** Three new hand-authored variant files under `tests/golden-mini/src/mutants/`, three new entries in the existing `mutants` array of `fault-mutants.json`, tightened selftest expectations (`killed=4` plus per-variant single-region diff checks), and one-sentence doc updates. The checker and suite are untouched.

**Tech Stack:** Python 3 stdlib, the existing F-04 infrastructure (`tools/check_fault_mutants.py`, behavioral `test_cell_suite.py`), the existing selftest framework.

## Global Constraints

- Variants are exact copies of `src/mini.py` with exactly one changed region each.
- No checker changes, no suite changes, no `fault-mutants.json` schema changes, no `rules.toml` changes.
- The mutant entries carry `fault`, `id`, `target`, `variant`, and `cell` string fields exactly like the F-04 entry.
- Every variant must be killed by the existing behavioral suite. A survivor means a suite gap: stop and report, do not extend the contract silently.
- No release, tag, or push without explicit user instruction.

---

## File Structure

| Path | Responsibility |
|---|---|
| `tests/golden-mini/src/mutants/mini.F-01-missing-transition.py` | `Open × M2` ignores instead of transitioning to `Closed`. |
| `tests/golden-mini/src/mutants/mini.F-02-transfer-fault.py` | `Open × M2` transitions to `Idle` instead of `Closed`. |
| `tests/golden-mini/src/mutants/mini.F-05-corrupt-state.py` | `UV-M1-dup` increments `dup_count` by 2 instead of 1. |
| `tests/golden-mini/domain-analysis/mini/fault-mutants.json` | Four `mutants` entries, everything else unchanged. |
| `tools/selftest/run_selftest.py` | `killed=4` assertion + per-variant single-region diff checks. |
| `prompts/04-testgen.md` | One sentence adding the F-01/F-02/F-05 operator pattern. |
| `docs/roadmap.md` | Item 8 status: 4 of 22 classes operationalized. |
| `docs/superpowers/plans/2026-08-09-ach-fault-classes-expansion.md` | This execution checklist. |

## Operator Definitions (verbatim from the spec)

| Class | Operator | Fixture cell |
|---|---|---|
| F-01 missing transition | `transition →X` cell does not transition — implementation ignores | `Open × M2` (→Closed) |
| F-02 transfer fault | `transition →X` cell transitions to the wrong target | `Open × M2` (→Closed, goes to `Idle`) |
| F-05 corrupt state | `handle` cell corrupts the counted state by the wrong amount | `Open × UV-M1-dup` (`handle (counted)`) |

---

### Task 1: Three variants, config entries, kill proofs

**Files:**
- Create: `tests/golden-mini/src/mutants/mini.F-01-missing-transition.py`
- Create: `tests/golden-mini/src/mutants/mini.F-02-transfer-fault.py`
- Create: `tests/golden-mini/src/mutants/mini.F-05-corrupt-state.py`
- Modify: `tests/golden-mini/domain-analysis/mini/fault-mutants.json`

**Interfaces:**
- Consumes: `src/mini.py` at HEAD (32 lines, from the F-04 work).
- Produces: four killed mutants; the exact variant contents that Task 2's
  diff checks verify.

- [ ] **Step 1: Create the F-01 variant**

Copy `tests/golden-mini/src/mini.py` to
`tests/golden-mini/src/mutants/mini.F-01-missing-transition.py`. In the
copy, replace the M2 Open branch:

```python
        if event == "M2":
            if self.state == "Open":
                self.state = "Closed"
                return "transition"
            return "ignored"
```

with:

```python
        if event == "M2":
            if self.state == "Open":
                return "ignored"  # F-01 missing transition: Open x M2 never fires
            return "ignored"
```

Nothing else changes.

- [ ] **Step 2: Create the F-02 variant**

Copy `src/mini.py` to `tests/golden-mini/src/mutants/mini.F-02-transfer-fault.py`.
In the copy, the M2 Open branch becomes:

```python
        if event == "M2":
            if self.state == "Open":
                self.state = "Idle"  # F-02 transfer fault: Open x M2 lands in Idle
                return "transition"
            return "ignored"
```

Nothing else changes.

- [ ] **Step 3: Create the F-05 variant**

Copy `src/mini.py` to `tests/golden-mini/src/mutants/mini.F-05-corrupt-state.py`.
In the copy, the UV-M1-dup branch becomes:

```python
        if event == "UV-M1-dup":
            self.dup_count += 2  # F-05 corrupt state: counter moves by the wrong amount
            return "handled"
```

Nothing else changes.

- [ ] **Step 4: Verify each variant differs in exactly one region**

```bash
for v in F-01-missing-transition F-02-transfer-fault F-05-corrupt-state; do
  echo "=== $v ==="
  diff tests/golden-mini/src/mini.py "tests/golden-mini/src/mutants/mini.$v.py"
done
```

Expected: each diff shows exactly one changed region (one hunk, a handful of
changed lines). If a variant differs more, fix the variant.

- [ ] **Step 5: Append the three mutant entries**

In `tests/golden-mini/domain-analysis/mini/fault-mutants.json`, extend the
`mutants` array (keep the existing F-04 entry first):

```json
    ,
    {
      "fault": "F-01",
      "id": "F-01-missing-transition-Open-M2",
      "target": "src/mini.py",
      "variant": "src/mutants/mini.F-01-missing-transition.py",
      "cell": "Open x M2"
    },
    {
      "fault": "F-02",
      "id": "F-02-transfer-fault-Open-M2",
      "target": "src/mini.py",
      "variant": "src/mutants/mini.F-02-transfer-fault.py",
      "cell": "Open x M2"
    },
    {
      "fault": "F-05",
      "id": "F-05-corrupt-state-Open-UV-M1-dup",
      "target": "src/mini.py",
      "variant": "src/mutants/mini.F-05-corrupt-state.py",
      "cell": "Open x UV-M1-dup"
    }
```

Validate: `python3 -c "import json; json.load(open('tests/golden-mini/domain-analysis/mini/fault-mutants.json'))"`.

- [ ] **Step 6: Run the kill proof**

```bash
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
```

Expected: `BASELINE: OK`, four `KILLED` lines (MUT-001 through MUT-004
numbered in config order: F-04, F-01, F-02, F-05), and
`FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)`.

If any mutant SURVIVES: stop. The suite has a gap for that branch. Report
the surviving mutant and the expected vs actual behavior; do not extend the
contract to accommodate it.

- [ ] **Step 7: Run the item-7 regression**

```bash
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
```

Expected: `MUTATION CHECK: OK (killed=9 survived=0 errors=0 blocked=0)`.

- [ ] **Step 8: Commit Task 1**

```bash
git add tests/golden-mini/src/mutants/mini.F-01-missing-transition.py \
  tests/golden-mini/src/mutants/mini.F-02-transfer-fault.py \
  tests/golden-mini/src/mutants/mini.F-05-corrupt-state.py \
  tests/golden-mini/domain-analysis/mini/fault-mutants.json
git commit -m "Add F-01, F-02, F-05 fault-class mutants to golden-mini" \
  -m "Evidence:
- Per-variant single-region diffs (paste all three)
- FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0) with four KILLED lines
- MUTATION CHECK: OK (killed=9 survived=0 errors=0 blocked=0)"
```

### Task 2: Selftest tightening and doc updates

**Files:**
- Modify: `tools/selftest/run_selftest.py`
- Modify: `prompts/04-testgen.md`
- Modify: `docs/roadmap.md`

**Interfaces:**
- Consumes: the four killed mutants from Task 1.

- [ ] **Step 1: Tighten the baseline selftest case**

In `tools/selftest/run_selftest.py`, find the case
`fault mutant baseline kills F-04 sneak path`. Rename it to
`fault mutant baseline kills all four fixture mutants` and add a killed
count assertion immediately after the existing `expect` call:

```python
        rc, out = fault_check(fdir)
        expect("fault mutant baseline kills all four fixture mutants", False,
               rc, out, needle="FAULT MUTANTS: OK")
        if "killed=4" not in out:
            failures.append("fault mutant count: expected killed=4\n" + out)
        else:
            print("  ok  fault mutant count killed=4 (passes)")
        if "KILLED" not in out:
            failures.append("fault mutant kill proof: no KILLED line\n" + out)
        else:
            print("  ok  fault mutant kill proof (passes)")
```

(Keep the existing KILLED-line check; drop the older duplicate
`fault mutant kill proof` expect if present, folding it here.)

- [ ] **Step 2: Add per-variant single-region diff checks**

Immediately after, add:

```python
        import difflib
        base = (ROOT / "tests" / "golden-mini" / "src" / "mini.py").read_text().splitlines()
        for variant_name in [
            "mini.F-01-missing-transition.py",
            "mini.F-02-transfer-fault.py",
            "mini.F-04-sneak-path.py",
            "mini.F-05-corrupt-state.py",
        ]:
            variant = (ROOT / "tests" / "golden-mini" / "src" / "mutants" / variant_name).read_text().splitlines()
            hunks = [l for l in difflib.unified_diff(base, variant, lineterm="")
                     if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
            if len(hunks) == 0 or len(hunks) > 8:
                failures.append(f"{variant_name}: expected a small single-region diff, got {len(hunks)} changed lines")
            else:
                print(f"  ok  {variant_name} single-region diff (passes)")
```

Expected: all four pass.

- [ ] **Step 3: Run the full selftest**

```bash
uv run --with-requirements tools/requirements-dev.txt \
  python3 tools/selftest/run_selftest.py
```

Expected: `SELFTEST: OK` including the tightened case and the four diff
checks. The mirroring-survives case still reports SURVIVED (its config
carries the same four mutants, all surviving under the no-op suite).

- [ ] **Step 4: Prompt and roadmap sentences**

In `prompts/04-testgen.md`, in the fault-mutant subsection after the F-04
operator definition, add one sentence:

> The same pattern defines F-01 (a `transition →X` cell does not
> transition), F-02 (a `transition →X` cell lands in the wrong target), and
> F-05 (a `handle` cell corrupts the counted state). Golden-mini ships one
> killed mutant per class as the fixture proof.

In `docs/roadmap.md`, update item 8's status line to:

```text
**Status:** 🔶 Partially shipped — 4 of 22 fault classes operationalized
(F-01, F-02, F-04, F-05). The `fault-mutants.json` contract and
`tools/check_fault_mutants.py` prove a behavioral cell suite kills one
hand-authored implementation mutant per class while a mirroring suite
survives. Remaining classes pending; binder-driven generation deferred.
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

Expected: all green; `killed=4`; 20 artifacts; 2/2 tool cases; 6/6
benchmarks; 3 primary/3 regression.

- [ ] **Step 6: Commit Task 2**

```bash
git add tools/selftest/run_selftest.py prompts/04-testgen.md docs/roadmap.md \
  docs/superpowers/plans/2026-08-09-ach-fault-classes-expansion.md
git commit -m "Prove fault-mutant contract generalizes to four classes" \
  -m "Evidence:
- SELFTEST: OK with killed=4 assertion and four single-region diff checks
- FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)
- PACK CONSISTENCY: OK (20 artifacts)
- run_tool_tests: 2/2 cases pass
- run_benchmark: 6 passed, 0 failed, 6 total
- benchmark_evidence: 3 primary, 3 regression, 0 unknown
- git diff --check: OK"
```

- [ ] **Step 7: Stop**

No release, tag, push, or generation work. Report the commits, the killed
lines per fault class, and the roadmap state (4 of 22).

## Execution Handoff

Execute only Tasks 1 and 2. Binder-driven generation needs a new user
instruction and its own spec.
