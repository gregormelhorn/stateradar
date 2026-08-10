# UV Coverage Binding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Tick a checkbox in the same work session as its completed action; never reconstruct task state from memory.

**Goal:** Reject coverage entries that claim nonexistent `UV-` events, then extend golden-mini with fixture-proven F-12, F-16, and F-17 UV shapes while preserving the existing F-15 proof.

**Architecture:** Task A adds a narrow phantom-reference check to `dsc_check.py`: only `UV-`-prefixed tokens in coverage values are resolved, so asserted absence, prose, and pair references remain legal. Its red probe is constructed in a temporary copy because the repository currently has zero phantom references. Task B adds three UV columns end-to-end, explicitly asserts every required coverage binding because Task A intentionally does not detect unbound UV columns, refreshes generated outputs, and preserves the hand-authored F-04 mutant's single-region difference.

**Tech Stack:** Python 3 stdlib, `uv` with `jsonschema` and development requirements, existing golden-mini fixture, existing selftest framework, existing matrix/fault mutation checkers.

## Spec deviations

1. **The spec header is broader than its corrected Task-A contract.** The header still says “bind every UV column to its base event's coverage entry.” The detailed Task-A section in corrected spec commit `983689e` explicitly ships only the **phantom** direction. This plan follows the detailed corrected contract: it resolves `UV-` tokens that coverage names, does **not** require every UV event to be named, and does **not** add schema category metadata or name-derived category inference.
2. **The corrected spec’s Task-A verification text supersedes the original live-fixture probe.** The plan uses the corrected constructed `UV-does-not-exist` probe. It does not claim that current golden-mini fails the shipped phantom rule; current phantom violations are measured as zero.
3. **Task B must also update `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py`, although the design’s initial file list did not name it.** `tools/selftest/run_selftest.py` compares every fault variant against `src/mini.py` and rejects a diff with more than eight changed lines. Appending six base branches without synchronizing F-04 produces ten changed lines; synchronizing the hand-authored variant preserves its two-line F-04-only diff. This is fixture maintenance, not a new F-04 mutation or a new fault-class claim.

## Global constraints

- Start only from a clean worktree whose `HEAD` contains corrected-spec commit `983689e`.
- Keep Task 0 limited to `tools/selftest/run_selftest.py` and `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py`.
- Keep Task A limited to `tools/dsc_check.py` and `tools/selftest/run_selftest.py`.
- Task 0 runs first. Its defect exists at HEAD and Task B appends three more branches to `src/mini.py`, which would drive F-04 further apart under a guard that cannot see it.
- Do not add a "died from the declared cell" check. `check_fault_mutants.py` reads only exit codes and `testCommand` is free per component, so that needs an output contract for every cell suite. Named follow-up, out of scope.
- Do not modify `formats/rules.toml`, `formats/analysis.schema.json`, `README.md`, `CHANGELOG.md`, the pack version, `matrix-mutation.json`, `fault-mutants.json`, or `mutant-generation.json`.
- Do not add an unbound-direction rule or migrate the measured 41 unbound variants. The corrected counting definition is: 13 files named `analysis.json` carry UV events; 10 have at least one unbound variant; there are 41 unbound variants. A wider 14-file/59-variant JSON scan includes convergence and ensemble files that are not `dsc_check` inputs.
- Do not infer UV category semantics from an event id. The phantom checker only verifies that an explicitly named `UV-` token resolves to an event id.
- In Task B, `killed=25`, `16` `ignore-to-handle` mutants, and `3 × 7 = 21` cells are **DERIVED TARGETS, UNVERIFIED AT PLAN TIME**. They come from the current `killed=16`, 7 reverse-family mutants, and 3 states × 4 events plus 3 new no-action columns. The executor must report measured results. A mismatch is `BLOCKED(task-B): derived count mismatch`; never adjust an assertion, roadmap text, or expected output to force green.
- Generate the sidecar only with `uv run --with jsonschema python3 tools/gen_analysis_sidecar.py --root tests/golden-mini`. Never use `--root .`.
- Run golden-mini `dsc_check` only with `--repo tests/golden-mini`. Never use `--repo .`.
- Refresh `tests/golden-mini/expected/analysis.json` only with `cp` from the regenerated sidecar. Never hand-edit either JSON file.
- `test_cell_suite.py` couples `EVENTS` to matrix column order through `zip(..., strict=True)`; preserve the same order in the matrix and `EVENTS`.
- Every temporary copied analysis directory that invokes `check_matrix_mutation.py` needs its own absolute `workingDirectory`; retain the existing absolute setting in the hole and annotated selftest cases.
- No release, tag, push, scope widening, or real-component changes.

## Ungated surfaces

| Surface | Gate | Review obligation |
|---|---|---|
| `docs/roadmap.md` item 8 | No executable wording gate | Review the exact before/after prose below: it must claim F-12/F-15/F-16/F-17 only with fixture proof and name F-13/F-14/F-18/F-20 as still unclaimed for their stated reasons. |
| `tests/golden-mini/domain-analysis/mini/event-catalogue.md` names/descriptions | `dsc_check`, cell suite, Part-B selftest, and sidecar generation | Review exact rows and coverage bindings below; no checker infers a category from a name. |
| `tools/dsc_check.py` phantom rule | Constructed red probe plus `run_selftest.py` | The red output must appear in the Task-A commit body and report. |

## File structure

| Path | Responsibility |
|---|---|
| `tools/dsc_check.py` | Resolve every `UV-` token present in a coverage value to an event id; permit all non-UV prose and pair references. |
| `tools/selftest/run_selftest.py` | Prove Task-A phantom failure/green forms; pin Task-B counts, bindings, and Part-B red-fixture precision. |
| `tests/golden-mini/src/mini.py` | Implement the three decided UV event branches. |
| `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py` | Keep the hand-authored F-04 variant behaviorally synchronized with base branches while retaining only the F-04 changed line. |
| `tests/golden-mini/domain-analysis/mini/disposition-matrix.md` | Declare seven ordered events and 21 exact cells. |
| `tests/golden-mini/domain-analysis/mini/event-catalogue.md` | Declare the three events and four explicit coverage bindings, including the pre-existing M1 duplication correction. |
| `tests/golden-mini/tests/test_cell_suite.py` | Keep `EVENTS` in exact matrix-column order. |
| `tests/golden-mini/domain-analysis/mini/analysis.json` | Generated sidecar; regenerate only. |
| `tests/golden-mini/expected/analysis.json` | Golden copy of the generated sidecar; refresh only with `cp`. |
| `tests/golden-mini/src/mutants/mini.F-01-missing-transition.py` | Generated F-01 variant; regenerate only. |
| `tests/golden-mini/src/mutants/mini.F-02-transfer-fault.py` | Generated F-02 variant; regenerate only. |
| `tests/golden-mini/src/mutants/mini.F-05-corrupt-state.py` | Generated F-05 variant; regenerate only. |
| `docs/roadmap.md` | Living, review-only F-class accounting. |

## Start gate — clean handoff

Run this before Task A. It deliberately checks ancestry rather than demanding an exact SHA, because this plan itself may be committed after `983689e`.

```bash
if test -n "$(git status --short)"; then
  printf 'BLOCKED(preflight): working tree is not clean\n'
  git status --short
  exit 1
fi
printf 'ASSERT OK: clean worktree\n'

if test -n "$(git diff --cached --name-only)"; then
  printf 'BLOCKED(preflight): staged files exist\n'
  git diff --cached --name-only
  exit 1
fi
printf 'ASSERT OK: no staged files\n'

git merge-base --is-ancestor 983689e HEAD
rc=$?
if test "$rc" -eq 0; then
  printf 'ASSERT OK: HEAD contains 983689e\n'
else
  printf 'BLOCKED(preflight): HEAD does not contain 983689e\n'
  printf 'exit=%s\n' "$rc"
  exit 1
fi
```

Expected:

```text
ASSERT OK: clean worktree
ASSERT OK: no staged files
ASSERT OK: HEAD contains 983689e
```

If this prints any `BLOCKED(preflight)` line, stop. Do not begin either task.

---

### Task 0: Count mutant regions, not lines, and resynchronise F-04

**Files:**
- Modify: `tools/selftest/run_selftest.py:436-450` (the single-region diff loop)
- Modify: `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py`

**Interfaces:**
- Produces a `regions` count per fault variant; all four must end at exactly 1.
- Leaves `FAULT MUTANTS: OK (killed=4 ...)` intact, but now for the right reason.

Why this task exists: F-04's kill proof is currently hollow. A pseudo-mutant
that removes only the `UV-M2-stale` branch, without applying the sneak-path
mutation at all, is scored `KILLED` (exit=1). The existing guard bounds total
changed lines (1..8); F-04 sits at 3, so it stays green while carrying two
separate diff regions.

- [x] **Step 1: Switch the assertion from line count to region count**

In `tools/selftest/run_selftest.py`, replace this exact current text:

```python
            variant = (ROOT / "tests" / "golden-mini" / "src" / "mutants" / variant_name).read_text().splitlines()
            hunks = [l for l in difflib.unified_diff(base, variant, lineterm="")
                     if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
            if len(hunks) == 0 or len(hunks) > 8:
                failures.append(f"{variant_name}: expected a small single-region diff, got {len(hunks)} changed lines")
            else:
                print(f"  ok  {variant_name} single-region diff (passes)")
```

with:

```python
            variant = (ROOT / "tests" / "golden-mini" / "src" / "mutants" / variant_name).read_text().splitlines()
            regions = [op for op in difflib.SequenceMatcher(None, base, variant).get_opcodes()
                       if op[0] != "equal"]
            if len(regions) != 1:
                failures.append(f"{variant_name}: a fault variant must differ from the base in exactly "
                                f"one region, got {len(regions)}. More than one region means the variant "
                                f"has drifted from the base and its kill no longer proves its fault class.")
            else:
                print(f"  ok  {variant_name} single-region diff (passes)")
```

- [x] **Step 2: Observe it red against F-04, and only F-04**

```bash
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py 2>&1 | grep -E 'single-region|exactly one region'
```

Expected: three `ok ... single-region diff (passes)` lines for F-01, F-02 and
F-05, and exactly one failure naming `mini.F-04-sneak-path.py` with
`got 2`. The selftest exits nonzero.

If F-04 is not the only failure, stop and report `BLOCKED(task-0)` with the
full output. **Paste this output** — it is the R-RED-PROBE evidence, and
unlike Task A's it did not need constructing.

- [x] **Step 3: Resynchronise F-04 with the base**

In `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py`, insert the branch
that the previous wave added to the base but never carried across. Insert it
**immediately before** the final `raise ValueError(event)` line, so the file
matches the base everywhere except the sneak-path region:

```python
        if event == "UV-M2-stale":
            return "ignored"
```

Do **not** change the F-04 mutation itself. The only intended difference from
the base stays `return "ignored"  # F-04 sneak path: Closed x M1 accepted`
where the base raises `RejectedError`.

- [x] **Step 4: Confirm exactly one region, and that F-04 still dies from its own mutation**

```bash
python3 - <<'PY'
import difflib, pathlib
base = pathlib.Path('tests/golden-mini/src/mini.py').read_text().splitlines()
for n in ['mini.F-01-missing-transition.py','mini.F-02-transfer-fault.py',
          'mini.F-04-sneak-path.py','mini.F-05-corrupt-state.py']:
    v = (pathlib.Path('tests/golden-mini/src/mutants')/n).read_text().splitlines()
    r = [op for op in difflib.SequenceMatcher(None, base, v).get_opcodes() if op[0] != 'equal']
    print(f'{n:34} regions={len(r)}')
PY
```

Expected: `regions=1` for all four.

Then prove the kill is single-cause again:

```bash
rm -rf /tmp/f04chk && cp -R tests/golden-mini /tmp/f04chk
cp /tmp/f04chk/src/mutants/mini.F-04-sneak-path.py /tmp/f04chk/src/mini.py
( cd /tmp/f04chk && python3 tests/test_cell_suite.py domain-analysis/mini ) 2>&1 | head -5
```

Expected: exactly one line, `MISMATCH Closed × M1: expected reject, got ignored`,
and **no `Traceback` and no `ValueError`**. **Paste this.** A traceback here
means the resynchronisation is incomplete.

- [x] **Step 5: Run the full gate**

```bash
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini | tail -1
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini | tail -1
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini | tail -1
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py 2>&1 | tail -1
python3 tools/check_pack_consistency.py 2>&1 | tail -1
python3 tools/run_tool_tests.py 2>&1 | tail -1
git diff --check
git status --short
```

Expected: `FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)`,
`MUTATION CHECK: OK (killed=16 survived=0 errors=0 blocked=0)`,
`MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)`,
`SELFTEST: OK`, `PACK CONSISTENCY: OK (20 artifacts, registry, version 1.51)`,
`2/2 cases pass`, `git diff --check` silent, and `git status --short` listing
only the two Task-0 files.

- [x] **Step 6: Commit Task 0**

```bash
git add tools/selftest/run_selftest.py tests/golden-mini/src/mutants/mini.F-04-sneak-path.py
git commit -m "Count mutant regions, not lines; resynchronise F-04" \
  -m "F-04's kill proof had gone hollow. The previous wave appended a
UV-M2-stale branch to src/mini.py; F-04 is hand-authored and was not carried
along, leaving it with two separate diff regions - its sneak-path mutation
plus a missing event branch.

Measured before the fix: a pseudo-mutant removing ONLY the UV-M2-stale
branch, with the sneak-path mutation NOT applied, scored exit=1 and would
have been counted KILLED. So F-04's share of killed=4 proved only that the
suite crashes on a missing handler.

The existing guard bounded total changed lines (1..8) and F-04 sat at 3, so
it stayed green - the weakness recorded as 'minor (deferred)' in an earlier
ledger, now having cost a real proof.

Evidence:
- red probe, already present, no construction needed:
    mini.F-04-sneak-path.py: expected exactly one region, got 2
  with F-01, F-02, F-05 passing
- after resynchronisation: regions=1 for all four variants
- F-04 now dies single-cause: 'MISMATCH Closed x M1: expected reject, got
  ignored' with no traceback
- FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)
- MUTATION CHECK: OK (killed=16 survived=0 errors=0 blocked=0)
- SELFTEST: OK  |  PACK CONSISTENCY: OK  |  2/2 tool cases"
```

---

### Task A: Reject phantom UV coverage bindings

**Files:**
- Modify: `tools/dsc_check.py:135-140`
- Modify: `tools/selftest/run_selftest.py:243-248`

**Interfaces:**
- Produces the diagnostic `UV binding: coverage <base>/<cat> names <id>, which is not an event`.
- Accepts coverage values that are strings or JSON lists; only `UV-`-prefixed tokens in string items are reference claims.
- Does not produce an unbound-UV diagnostic.
- Leaves golden-mini at `MUTATION CHECK: OK (killed=16 survived=0 errors=0 blocked=0)`.

- [x] **Step 1: Add the Task-A selftest cases before the checker implementation**

In `tools/selftest/run_selftest.py`, replace this exact current text (lines 243-248):

```python
        # R-UPSTREAM-GUARD: missing upstream_guards on event must fail
        mutated("missing upstream-guard annotation",
                lambda r: r["events"][0].pop("upstream_guards", None),
                "R-UPSTREAM-GUARD")

        # J3: UV coverage must bind at zero UV events
```

with this exact text:

```python
        # R-UPSTREAM-GUARD: missing upstream_guards on event must fail
        mutated("missing upstream-guard annotation",
                lambda r: r["events"][0].pop("upstream_guards", None),
                "R-UPSTREAM-GUARD")

        # PA-13a: coverage values may be asserted absence, prose, or one/more
        # existing UV ids. Only a UV-prefixed reference is a resolvable claim.
        legal_uv_bindings = sidecar(tmp, FLAT)
        raw = json.loads((legal_uv_bindings / "analysis.json").read_text())
        for event in raw["events"]:
            if event["id"] == "UV1":
                event["id"] = "UV-present"
        for cell in raw["cells"]:
            if cell["event"] == "UV1":
                cell["event"] = "UV-present"
        raw["coverage"]["E1"].update({
            "loss": "applicable — transport may drop this call",
            "delay": "UV-present, UV-present",
            "duplication": ["UV-present", "UV-present"],
            "out-of-order": ["P-01a", "P-01b"],
        })
        (legal_uv_bindings / "analysis.json").write_text(json.dumps(raw))
        expect("UV binding permits prose and known variants", False,
               *dsc(legal_uv_bindings))
        mutated("phantom UV coverage binding",
                lambda r: r["coverage"]["E1"].update(loss="UV-does-not-exist"),
                "UV binding: coverage E1/loss names UV-does-not-exist, which is not an event")

        # J3: UV coverage must bind at zero UV events
```

- [x] **Step 2: Observe the selftest assertion red before the checker exists**

```bash
out=$(uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py 2>&1)
rc=$?
printf '%s\n' "$out" | grep -A2 -F 'phantom UV coverage binding: expected FAIL, got rc=0'
printf '%s\n' "$out" | tail -1
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 1 \
  && printf '%s\n' "$out" | grep -Fq 'phantom UV coverage binding: expected FAIL, got rc=0' \
  && printf '%s\n' "$out" | grep -Fq 'DSC CHECK: OK (2 states x 2 events, 4 cells, 1 guard groups)'; then
  printf 'ASSERT RED AS REQUIRED\n'
else
  printf '%s\n' "$out"
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
 - phantom UV coverage binding: expected FAIL, got rc=0
DSC CHECK: OK (2 states x 2 events, 4 cells, 1 guard groups)
SELFTEST: FAIL
exit=1
ASSERT RED AS REQUIRED
```

Paste the complete `out` value into the task report and eventual Task-A commit body. If another new failure appears, stop with `BLOCKED(task-A): phantom selftest red probe has an unexpected failure`.

- [x] **Step 3: Implement the phantom-only checker**

In `tools/dsc_check.py`, replace this exact current text (lines 135-140):

```python
    for src, cats in data.get("coverage", {}).items():
        for cat in CATEGORIES:
            v = cats.get(cat)
            if v is None or v == [] or v == "":
                E(f"coverage: {src}/{cat} is empty (variant ids or 'n/a: reason')")
    for q in data.get("questions", []):
```

with this exact text:

```python
    for src, cats in data.get("coverage", {}).items():
        for cat in CATEGORIES:
            v = cats.get(cat)
            if v is None or v == [] or v == "":
                E(f"coverage: {src}/{cat} is empty (variant ids or 'n/a: reason')")

    # A coverage value may be an asserted absence, prose, one variant id, or
    # several ids. Only UV-prefixed tokens are variant-reference claims: they
    # must resolve to an event in this sidecar. Prose and pair references stay
    # legal because they do not make such a claim.
    event_ids = {event["id"] for event in data.get("events", [])}
    for base, categories in data.get("coverage", {}).items():
        for category, value in categories.items():
            values = value if isinstance(value, list) else [value]
            for item in values:
                if not isinstance(item, str):
                    continue
                for variant_id in re.findall(r"\bUV-[\w-]+\b", item):
                    if variant_id not in event_ids:
                        E(f"UV binding: coverage {base}/{category} names {variant_id}, "
                          "which is not an event")
    for q in data.get("questions", []):
```

Do not change the existing `CATEGORIES`, `uv_categories`, `base_events`, or J3 loop. The new rule validates only explicit `UV-` reference claims, so it must not inspect every non-`n/a:` coverage value.

- [x] **Step 4: Run the constructed checker red probe and observe the exact diagnostic**

```bash
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cp -R tests/golden-mini/domain-analysis/mini "$tmp/mini"
python3 - "$tmp/mini/analysis.json" <<'PY'
from pathlib import Path
import json
import sys

path = Path(sys.argv[1])
data = json.loads(path.read_text())
data["coverage"]["M1"]["loss"] = "UV-does-not-exist"
path.write_text(json.dumps(data))
PY
uv run --with jsonschema python3 tools/dsc_check.py "$tmp/mini" --repo tests/golden-mini
rc=$?
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 1; then
  printf 'ASSERT RED AS REQUIRED\n'
else
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
DSC CHECK: FAIL
 - UV binding: coverage M1/loss names UV-does-not-exist, which is not an event
exit=1
ASSERT RED AS REQUIRED
```

Paste this complete output into the task report and Task-A commit body. This is the R-RED-PROBE evidence for the shipped checker.

- [x] **Step 5: Run the selftest after the checker exists**

```bash
out=$(uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py 2>&1)
rc=$?
printf '%s\n' "$out" | grep -Fx '  ok  UV binding permits prose and known variants (passes)'
printf '%s\n' "$out" | grep -Fx '  ok  phantom UV coverage binding (fails as required)'
printf '%s\n' "$out" | tail -1
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 0 \
  && printf '%s\n' "$out" | grep -Fxq '  ok  UV binding permits prose and known variants (passes)' \
  && printf '%s\n' "$out" | grep -Fxq '  ok  phantom UV coverage binding (fails as required)' \
  && printf '%s\n' "$out" | grep -Fxq 'SELFTEST: OK'; then
  printf 'ASSERT OK\n'
else
  printf '%s\n' "$out"
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
  ok  UV binding permits prose and known variants (passes)
  ok  phantom UV coverage binding (fails as required)
SELFTEST: OK
exit=0
ASSERT OK
```

- [x] **Step 6: Confirm the real golden-mini sidecar stays green**

```bash
out=$(uv run --with jsonschema python3 tools/dsc_check.py tests/golden-mini/domain-analysis/mini --repo tests/golden-mini 2>&1)
rc=$?
printf '%s\n' "$out"
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 0 \
  && test "$out" = 'DSC CHECK: OK (3 states x 4 events, 12 cells, 0 guard groups)'; then
  printf 'ASSERT OK\n'
else
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
DSC CHECK: OK (3 states x 4 events, 12 cells, 0 guard groups)
exit=0
ASSERT OK
```

- [x] **Step 7: Run the Task-A independent full gate**

```bash
expect_line() {
  expected=$1
  shift
  out=$("$@" 2>&1)
  rc=$?
  if test "$rc" -eq 0 && printf '%s\n' "$out" | grep -Fx -- "$expected" >/dev/null; then
    printf '%s\nexit=0\nASSERT OK\n' "$expected"
  else
    printf '%s\nexit=%s\nASSERT FAILED\n' "$out" "$rc"
    return 1
  fi
}

expect_line 'DSC CHECK: OK (3 states x 4 events, 12 cells, 0 guard groups)' \
  uv run --with jsonschema python3 tools/dsc_check.py tests/golden-mini/domain-analysis/mini --repo tests/golden-mini || exit 1
expect_line 'MUTATION CHECK: OK (killed=16 survived=0 errors=0 blocked=0)' \
  python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini || exit 1
expect_line 'FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)' \
  python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini || exit 1
expect_line 'MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)' \
  python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini || exit 1
expect_line 'SELFTEST: OK' \
  uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py || exit 1
expect_line 'PACK CONSISTENCY: OK (20 artifacts, registry, version 1.51)' \
  python3 tools/check_pack_consistency.py || exit 1
expect_line '2/2 cases pass' python3 tools/run_tool_tests.py || exit 1
expect_line 'Results: 6 passed, 0 failed, 6 total' python3 tools/run_benchmark.py || exit 1
expect_line 'Primary evidence: 3, Regression anchors: 3, Unknown: 0' \
  python3 tools/benchmark_evidence.py || exit 1
expect_line "REACHABILITY CHECK: OK (3/3 states reachable from 'Idle', 1 terminal)" \
  uv run --with jsonschema python3 tools/check_reachability.py tests/golden-mini/domain-analysis/mini || exit 1

diff_out=$(git diff --check 2>&1)
diff_rc=$?
if test "$diff_rc" -eq 0 && test -z "$diff_out"; then
  printf 'diff-check: clean\nexit=0\nASSERT OK\n'
else
  printf '%s\nexit=%s\nASSERT FAILED\n' "$diff_out" "$diff_rc"
  exit 1
fi
```

Expected stable output lines:

```text
DSC CHECK: OK (3 states x 4 events, 12 cells, 0 guard groups)
MUTATION CHECK: OK (killed=16 survived=0 errors=0 blocked=0)
FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)
MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)
SELFTEST: OK
PACK CONSISTENCY: OK (20 artifacts, registry, version 1.51)
2/2 cases pass
Results: 6 passed, 0 failed, 6 total
Primary evidence: 3, Regression anchors: 3, Unknown: 0
REACHABILITY CHECK: OK (3/3 states reachable from 'Idle', 1 terminal)
diff-check: clean
```

Every successful command also prints `exit=0` and `ASSERT OK`. Paste all output into the Task-A report.

- [x] **Step 8: Verify Task-A file scope before committing**

```bash
expected='tools/dsc_check.py
tools/selftest/run_selftest.py'
actual=$(git diff --name-only | LC_ALL=C sort)
if test "$actual" = "$expected"; then
  printf '%s\n' "$actual"
  printf 'ASSERT OK: Task-A file scope\n'
else
  printf 'EXPECTED:\n%s\nACTUAL:\n%s\nASSERT FAILED\n' "$expected" "$actual"
  exit 1
fi
```

Expected:

```text
tools/dsc_check.py
tools/selftest/run_selftest.py
ASSERT OK: Task-A file scope
```

- [x] **Step 9: Commit Task A**

```bash
git add tools/dsc_check.py tools/selftest/run_selftest.py
git commit -m "Reject phantom UV coverage bindings" \
  -m "Adds the phantom half of UV coverage integrity only: every UV-prefixed
coverage token must resolve to an event id. It deliberately permits asserted
absence, prose, and pair references, and deliberately does not require every
UV event to be named.

Evidence:
- red selftest before mechanism: phantom UV coverage binding expected FAIL, got rc=0
- constructed red probe:
  DSC CHECK: FAIL
   - UV binding: coverage M1/loss names UV-does-not-exist, which is not an event
  exit=1
- selftest green: prose/known-variants and phantom cases both exercised
- DSC CHECK: OK (3 states x 4 events, 12 cells, 0 guard groups)
- MUTATION CHECK: OK (killed=16 survived=0 errors=0 blocked=0)
- FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)
- MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)
- SELFTEST: OK
- PACK CONSISTENCY: OK (20 artifacts, registry, version 1.51)
- run_tool_tests: 2/2 cases pass
- run_benchmark: Results: 6 passed, 0 failed, 6 total
- git diff --check: clean"

subject=$(git log -1 --oneline | sed 's/^[0-9a-f][0-9a-f]* //')
if test "$subject" = 'Reject phantom UV coverage bindings' \
  && test -z "$(git diff --cached --name-only)" \
  && test -z "$(git status --short)"; then
  printf 'ASSERT OK: Task-A commit exists and tree is clean\n'
else
  printf 'ASSERT FAILED: Task-A commit or clean-tree check\n'
  git log -1 --oneline
  git status --short
  exit 1
fi
```

Expected:

```text
[main <Task-A-SHA>] Reject phantom UV coverage bindings
ASSERT OK: Task-A commit exists and tree is clean
```

`<Task-A-SHA>` is Git-generated and is not an expected literal. Paste `git log -1 --oneline` and the entire commit message from `git show --format=full HEAD` into the task report.

**Task-A deliverable:** `dsc_check.py` rejects a phantom `UV-` reference with the exact diagnostic; both its red path and legal prose/list forms are selftested; all existing golden-mini gates remain green.

**Do not:** fix `M1.duplication` yet, migrate the unbound artifacts, add schema fields, edit a generated JSON file, release, tag, or push.

---

### Task B: Add F-12, F-16, and F-17 golden-mini UV columns

**Files:**
- Modify: `tools/selftest/run_selftest.py:327-343` and `:622-655`
- Modify: `tests/golden-mini/src/mini.py:32-34`
- Modify: `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py:29-32`
- Modify: `tests/golden-mini/domain-analysis/mini/disposition-matrix.md:5-13`
- Modify: `tests/golden-mini/domain-analysis/mini/event-catalogue.md:3-36`
- Modify: `tests/golden-mini/tests/test_cell_suite.py:11`
- Regenerate: `tests/golden-mini/domain-analysis/mini/analysis.json`
- Refresh by `cp`: `tests/golden-mini/expected/analysis.json`
- Regenerate: `tests/golden-mini/src/mutants/mini.F-01-missing-transition.py`, `mini.F-02-transfer-fault.py`, `mini.F-05-corrupt-state.py`
- Modify: `docs/roadmap.md:94-99`

**Interfaces:**
- Consumes Task A’s phantom checker; it catches typoed coverage IDs but intentionally does not detect omitted coverage IDs.
- Produces ordered `EVENTS = ["M1", "M2", "UV-M1-dup", "UV-M2-stale", "UV-M1-lost", "UV-M2-conflict", "UV-M1-spurious"]`.
- Produces explicit sidecar coverage bindings `M1/duplication=UV-M1-dup`, `M1/loss=UV-M1-lost`, `M2/contradiction=UV-M2-conflict`, and `M1/commission=UV-M1-spurious`.
- Produces the **derived, unverified-at-plan-time target** `MUTATION CHECK: OK (killed=25 survived=0 errors=0 blocked=0)` and 16 `ignore-to-handle` mutations.

- [x] **Step 1: Add count, UV-shape, and binding assertions before fixture changes**

In `tools/selftest/run_selftest.py`, replace this exact current hole-count block (lines 327-330):

```python
        if "killed=15" not in out_hole:
            failures.append("hole cell: expected killed=15 (one fewer than 16)\n" + out_hole)
        else:
            print("  ok  hole cell produces no ignore-to-handle mutant (passes)")
```

with this exact text:

```python
        if "killed=24" not in out_hole:
            failures.append("hole cell: expected killed=24 (one fewer than 25)\n" + out_hole)
        else:
            print("  ok  hole cell produces no ignore-to-handle mutant (passes)")
```

Then replace this exact current golden-mini count block (lines 335-339):

```python
        if "killed=16" not in out_gm:
            failures.append("matrix mutation count: expected killed=16\n" + out_gm)
        else:
            print("  ok  matrix mutation count killed=16 (passes)")
        if "new='handle `mini.py:28`'" not in out_gm:
```

with this exact text:

```python
        if "killed=25" not in out_gm:
            failures.append("matrix mutation count: expected killed=25\n" + out_gm)
        else:
            print("  ok  matrix mutation count killed=25 (passes)")
        ignore_to_handle = [line for line in out_gm.splitlines()
                            if "kind=ignore-to-handle" in line]
        if len(ignore_to_handle) != 16:
            failures.append("matrix mutation family: expected 16 ignore-to-handle mutants, "
                            f"got {len(ignore_to_handle)}\n" + out_gm)
        else:
            print("  ok  matrix mutation family has 16 ignore-to-handle mutants (passes)")
        for event in ("UV-M1-lost", "UV-M2-conflict", "UV-M1-spurious"):
            actual = sum("KILLED" in line and "kind=ignore-to-handle" in line
                         and f"event={event}" in line
                         for line in out_gm.splitlines())
            if actual != 3:
                failures.append("UV matrix mutation: expected three KILLED ignore-to-handle "
                                f"mutants for {event}, got {actual}\n" + out_gm)
            else:
                print(f"  ok  UV matrix mutation has three KILLED {event} mutants (passes)")
        coverage = json.loads((gm / "analysis.json").read_text())["coverage"]
        expected_bindings = {
            ("M1", "duplication"): "UV-M1-dup",
            ("M1", "loss"): "UV-M1-lost",
            ("M2", "contradiction"): "UV-M2-conflict",
            ("M1", "commission"): "UV-M1-spurious",
        }
        for (base, category), event in expected_bindings.items():
            actual = coverage.get(base, {}).get(category)
            if actual != event:
                failures.append("UV coverage binding: expected "
                                f"{base}/{category}={event!r}, got {actual!r}")
            else:
                print(f"  ok  UV coverage binding {base}/{category}={event} (passes)")
        if "new='handle `mini.py:28`'" not in out_gm:
```

- [x] **Step 2: Make the two deliberate Part-B red cases assert exactly one stated reason**

In `tools/selftest/run_selftest.py`, replace this exact current text (lines 645-655):

```python
        expect("blind table missing row", True, *pbp(partial),
               needle="missing row: UV-M1-dup")
        # a duplicated checklist tick must fail — coverage must be countable
        dup = tmp / "blind-dup.md"
        dup.write_text("| id | disposition |\n|---|---|\n"
                       "| M1 | handle |\n| M2 | reject |\n"
                       "| UV-M1-dup | ignore (documented) |\n"
                       "| UV-M2-stale | ignore (documented) |\n"
                       + checklist + "- [x] M2\n")
        expect("duplicated checklist tick", True, *pbp(dup),
               needle="duplicated checklist entry: M2")
```

with this exact text:

```python
        rc_partial, out_partial = pbp(partial)
        expect("blind table missing row", True, rc_partial, out_partial,
               needle="missing row: UV-M1-dup")
        partial_errors = [line for line in out_partial.splitlines()
                          if line.startswith(" - ")]
        expected_partial_errors = [
            " - missing row: UV-M1-dup (no table row keyed by it)",
        ]
        if partial_errors != expected_partial_errors:
            failures.append("blind partial: expected only missing row: UV-M1-dup\n" + out_partial)
        else:
            print("  ok  blind partial fails only for missing row UV-M1-dup (passes)")
        # a duplicated checklist tick must fail — coverage must be countable
        dup = tmp / "blind-dup.md"
        dup.write_text("| id | disposition |\n|---|---|\n"
                       "| M1 | handle |\n| M2 | reject |\n"
                       "| UV-M1-dup | ignore (documented) |\n"
                       "| UV-M2-stale | ignore (documented) |\n"
                       + checklist + "- [x] M2\n")
        rc_dup, out_dup = pbp(dup)
        expect("duplicated checklist tick", True, rc_dup, out_dup,
               needle="duplicated checklist entry: M2")
        dup_errors = [line for line in out_dup.splitlines() if line.startswith(" - ")]
        expected_dup_errors = [" - duplicated checklist entry: M2 (2x)"]
        if dup_errors != expected_dup_errors:
            failures.append("blind dup: expected only duplicated checklist entry: M2\n" + out_dup)
        else:
            print("  ok  blind dup fails only for duplicated checklist M2 (passes)")
```

- [x] **Step 3: Observe all Task-B assertions red before changing the fixture**

```bash
out=$(uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py 2>&1)
rc=$?
printf '%s\n' "$out" | grep -E '^ - (hole cell: expected killed=24|matrix mutation count: expected killed=25|matrix mutation family: expected 16|UV matrix mutation: expected three|UV coverage binding: expected|blind partial:)'
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 1 \
  && test "$(printf '%s\n' "$out" | grep -c '^ - UV matrix mutation: expected three')" -eq 3 \
  && test "$(printf '%s\n' "$out" | grep -c '^ - UV coverage binding: expected')" -eq 4 \
  && printf '%s\n' "$out" | grep -Fq 'blind partial: expected only missing row: UV-M1-dup'; then
  printf 'ASSERT RED AS REQUIRED\n'
else
  printf '%s\n' "$out"
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected 11 failure headings, exactly these:

```text
 - hole cell: expected killed=24 (one fewer than 25)
 - matrix mutation count: expected killed=25
 - matrix mutation family: expected 16 ignore-to-handle mutants, got 7
 - UV matrix mutation: expected three KILLED ignore-to-handle mutants for UV-M1-lost, got 0
 - UV matrix mutation: expected three KILLED ignore-to-handle mutants for UV-M2-conflict, got 0
 - UV matrix mutation: expected three KILLED ignore-to-handle mutants for UV-M1-spurious, got 0
 - UV coverage binding: expected M1/duplication='UV-M1-dup', got 'n/a: sync'
 - UV coverage binding: expected M1/loss='UV-M1-lost', got 'n/a: local'
 - UV coverage binding: expected M2/contradiction='UV-M2-conflict', got 'n/a: sync'
 - UV coverage binding: expected M1/commission='UV-M1-spurious', got 'n/a: sync'
 - blind partial: expected only missing row: UV-M1-dup
exit=1
ASSERT RED AS REQUIRED
```

Paste the complete `out` value into the task report and Task-B commit body. If the number, event name, binding, or failure reason differs, stop with `BLOCKED(task-B): red assertion output differs from the declared target`.

- [x] **Step 4: Add the three event branches to the base implementation**

In `tests/golden-mini/src/mini.py`, replace this exact current text (lines 32-34):

```python
        if event == "UV-M2-stale":
            return "ignored"
        raise ValueError(event)
```

with this exact text:

```python
        if event == "UV-M2-stale":
            return "ignored"
        if event == "UV-M1-lost":
            return "ignored"
        if event == "UV-M2-conflict":
            return "ignored"
        if event == "UV-M1-spurious":
            raise RejectedError("UV-M1-spurious rejected")
        raise ValueError(event)
```

This append-only placement preserves all existing citations through `mini.py:33`; the three new citations will be `mini.py:35`, `mini.py:37`, and `mini.py:39`.

- [x] **Step 5: Synchronize the hand-authored F-04 variant with the new base branches**

In `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py`, replace this exact current text (lines 29-32):

```python
        if event == "UV-M1-dup":
            self.dup_count += 1
            return "handled"
        raise ValueError(event)
```

with this exact text:

```python
        if event == "UV-M1-dup":
            self.dup_count += 1
            return "handled"
        if event == "UV-M2-stale":
            return "ignored"
        if event == "UV-M1-lost":
            return "ignored"
        if event == "UV-M2-conflict":
            return "ignored"
        if event == "UV-M1-spurious":
            raise RejectedError("UV-M1-spurious rejected")
        raise ValueError(event)
```

Do not run `gen_mutant_variants.py` for this file: F-04 is deliberately `UNBOUND` and hand-authored.

- [x] **Step 6: Expand the disposition matrix in exact column order**

In `tests/golden-mini/domain-analysis/mini/disposition-matrix.md`, replace this exact current text (lines 5-13):

```markdown
Abstraction: flat leaf states, no hierarchy; completeness is relative
to the four-event catalogue.
<!-- terminal: Closed -->

| state | M1 | M2 | UV-M1-dup | UV-M2-stale |
|---|---|---|---|---|
| **Idle** | transition →Open `mini.py:19` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` |
| **Open** | ignore (documented) `mini.py:22` | transition →Closed `mini.py:26` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` |
| **Closed** | reject `mini.py:23` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` |
```

with this exact text:

```markdown
Abstraction: flat leaf states, no hierarchy; completeness is relative
to the seven-event catalogue.
<!-- terminal: Closed -->

| state | M1 | M2 | UV-M1-dup | UV-M2-stale | UV-M1-lost | UV-M2-conflict | UV-M1-spurious |
|---|---|---|---|---|---|---|---|
| **Idle** | transition →Open `mini.py:19` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` | ignore (documented) `mini.py:35` | ignore (documented) `mini.py:37` | reject `mini.py:39` |
| **Open** | ignore (documented) `mini.py:22` | transition →Closed `mini.py:26` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` | ignore (documented) `mini.py:35` | ignore (documented) `mini.py:37` | reject `mini.py:39` |
| **Closed** | reject `mini.py:23` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` | ignore (documented) `mini.py:35` | ignore (documented) `mini.py:37` | reject `mini.py:39` |
```

- [x] **Step 7: Declare and explicitly bind every Task-B catalogue event**

In `tests/golden-mini/domain-analysis/mini/event-catalogue.md`, replace this exact current declaration and table (lines 3-10):

```markdown
<!-- event-ids: M1 M2 UV-M1-dup UV-M2-stale -->

| id | name | source | ext/int | payload | produced | consumed |
|---|---|---|---|---|---|---|
| M1 | open | operator | external | id | op | svc |
| M2 | close | operator | external | id | op | svc |
| UV-M1-dup | duplicate open | operator | external | id | op | svc |
| UV-M2-stale | stale close after shutdown | operator | external | id | op | svc |
```

with this exact text:

```markdown
<!-- event-ids: M1 M2 UV-M1-dup UV-M2-stale UV-M1-lost UV-M2-conflict UV-M1-spurious -->

| id | name | source | ext/int | payload | produced | consumed |
|---|---|---|---|---|---|---|
| M1 | open | operator | external | id | op | svc |
| M2 | close | operator | external | id | op | svc |
| UV-M1-dup | duplicate open | operator | external | id | op | svc |
| UV-M2-stale | stale close after shutdown | operator | external | id | op | svc |
| UV-M1-lost | lost open | operator | external | id | op | svc |
| UV-M2-conflict | contradictory close | operator | external | id | op | svc |
| UV-M1-spurious | spurious open | operator | external | id | op | svc |
```

Then replace this exact current M1 coverage block (lines 18-24):

```markdown
  - loss: n/a: local
  - delay: n/a: sync
  - duplication: n/a: sync
  - out-of-order: n/a: sync
  - contradiction: n/a: sync
  - commission: n/a: sync
  - value: n/a: payload validated
```

with this exact text:

```markdown
  - loss: UV-M1-lost
  - delay: n/a: sync
  - duplication: UV-M1-dup
  - out-of-order: n/a: sync
  - contradiction: n/a: sync
  - commission: UV-M1-spurious
  - value: n/a: payload validated
```

Finally replace this exact current M2 coverage pair (lines 33-34):

```markdown
  - out-of-order: UV-M2-stale
  - contradiction: n/a: sync
```

with this exact text:

```markdown
  - out-of-order: UV-M2-stale
  - contradiction: UV-M2-conflict
```

The `M1/duplication` line is the pre-existing data correction moved from Task A. The four explicit bindings are an executable Task-B obligation because Task A deliberately cannot detect a missing binding.

- [x] **Step 8: Make `EVENTS` match the matrix column order**

In `tests/golden-mini/tests/test_cell_suite.py`, replace this exact current line (line 11):

```python
EVENTS = ["M1", "M2", "UV-M1-dup", "UV-M2-stale"]
```

with this exact line:

```python
EVENTS = ["M1", "M2", "UV-M1-dup", "UV-M2-stale", "UV-M1-lost", "UV-M2-conflict", "UV-M1-spurious"]
```

Do not change `NAVIGATE`. Each new event is delivered only after navigation to the state under test.

- [x] **Step 9: Update all four inline Part-B fixtures and make their declared red reasons exact**

After Step 2, replace this exact current block in `tools/selftest/run_selftest.py` (from the current `checklist` assignment through the duplicate-case assertion):

```python
        checklist = "\n- [x] M1\n- [x] M2\n- [x] UV-M1-dup\n- [x] UV-M2-stale\n"
        full = tmp / "blind-full.md"
        full.write_text("| id | disposition |\n|---|---|\n"
                        "| M1 | handle |\n| M2 | reject |\n"
                        "| UV-M1-dup | ignore (documented) |\n"
                        "| UV-M2-stale | ignore (documented) |\n" + checklist)
        expect("blind table complete", False, *pbp(full))
        # a finer-grained table (several situation rows per event id,
        # cross-references in prose cells) is MORE information — must pass
        fine = tmp / "blind-fine.md"
        fine.write_text("| id | situation | disposition |\n|---|---|---|\n"
                        "| **M1** | Idle | handle |\n"
                        "| M1 | Open (after M2, see UV-M1-dup) | reject |\n"
                        "| M2 | any | reject |\n"
                        "| UV-M1-dup | any | ignore (documented) |\n"
                        "| UV-M2-stale | any | ignore (documented) |\n" + checklist)
        expect("blind table finer than one row per id", False, *pbp(fine))
        # R-BLIND-ROW-COVERAGE: a missing catalogue row must fail
        partial = tmp / "blind-partial.md"
        partial.write_text("| id | disposition |\n|---|---|\n"
                           "| M1 | handle |\n| M2 | reject |\n"
                           "| UV-M2-stale | ignore (documented) |\n"
                           "\n- [x] M1\n- [x] M2\n- [x] UV-M2-stale\n")
        rc_partial, out_partial = pbp(partial)
        expect("blind table missing row", True, rc_partial, out_partial,
               needle="missing row: UV-M1-dup")
        partial_errors = [line for line in out_partial.splitlines()
                          if line.startswith(" - ")]
        expected_partial_errors = [
            " - missing row: UV-M1-dup (no table row keyed by it)",
        ]
        if partial_errors != expected_partial_errors:
            failures.append("blind partial: expected only missing row: UV-M1-dup\n" + out_partial)
        else:
            print("  ok  blind partial fails only for missing row UV-M1-dup (passes)")
        # a duplicated checklist tick must fail — coverage must be countable
        dup = tmp / "blind-dup.md"
        dup.write_text("| id | disposition |\n|---|---|\n"
                       "| M1 | handle |\n| M2 | reject |\n"
                       "| UV-M1-dup | ignore (documented) |\n"
                       "| UV-M2-stale | ignore (documented) |\n"
                       + checklist + "- [x] M2\n")
        rc_dup, out_dup = pbp(dup)
        expect("duplicated checklist tick", True, rc_dup, out_dup,
               needle="duplicated checklist entry: M2")
        dup_errors = [line for line in out_dup.splitlines() if line.startswith(" - ")]
        expected_dup_errors = [" - duplicated checklist entry: M2 (2x)"]
        if dup_errors != expected_dup_errors:
            failures.append("blind dup: expected only duplicated checklist entry: M2\n" + out_dup)
        else:
            print("  ok  blind dup fails only for duplicated checklist M2 (passes)")
```

with this exact text:

```python
        checklist = ("\n- [x] M1\n- [x] M2\n- [x] UV-M1-dup\n"
                     "- [x] UV-M2-stale\n- [x] UV-M1-lost\n"
                     "- [x] UV-M2-conflict\n- [x] UV-M1-spurious\n")
        full = tmp / "blind-full.md"
        full.write_text("| id | disposition |\n|---|---|\n"
                        "| M1 | handle |\n| M2 | reject |\n"
                        "| UV-M1-dup | ignore (documented) |\n"
                        "| UV-M2-stale | ignore (documented) |\n"
                        "| UV-M1-lost | ignore (documented) |\n"
                        "| UV-M2-conflict | ignore (documented) |\n"
                        "| UV-M1-spurious | reject |\n" + checklist)
        expect("blind table complete", False, *pbp(full))
        # a finer-grained table (several situation rows per event id,
        # cross-references in prose cells) is MORE information — must pass
        fine = tmp / "blind-fine.md"
        fine.write_text("| id | situation | disposition |\n|---|---|---|\n"
                        "| **M1** | Idle | handle |\n"
                        "| M1 | Open (after M2, see UV-M1-dup) | reject |\n"
                        "| M2 | any | reject |\n"
                        "| UV-M1-dup | any | ignore (documented) |\n"
                        "| UV-M2-stale | any | ignore (documented) |\n"
                        "| UV-M1-lost | any | ignore (documented) |\n"
                        "| UV-M2-conflict | any | ignore (documented) |\n"
                        "| UV-M1-spurious | any | reject |\n" + checklist)
        expect("blind table finer than one row per id", False, *pbp(fine))
        # R-BLIND-ROW-COVERAGE: only the UV-M1-dup row is absent; its
        # checklist tick stays present so this case fails for one reason.
        partial = tmp / "blind-partial.md"
        partial.write_text("| id | disposition |\n|---|---|\n"
                           "| M1 | handle |\n| M2 | reject |\n"
                           "| UV-M2-stale | ignore (documented) |\n"
                           "| UV-M1-lost | ignore (documented) |\n"
                           "| UV-M2-conflict | ignore (documented) |\n"
                           "| UV-M1-spurious | reject |\n"
                           "\n- [x] M1\n- [x] M2\n- [x] UV-M1-dup\n"
                           "- [x] UV-M2-stale\n- [x] UV-M1-lost\n"
                           "- [x] UV-M2-conflict\n- [x] UV-M1-spurious\n")
        rc_partial, out_partial = pbp(partial)
        expect("blind table missing row", True, rc_partial, out_partial,
               needle="missing row: UV-M1-dup")
        partial_errors = [line for line in out_partial.splitlines()
                          if line.startswith(" - ")]
        expected_partial_errors = [
            " - missing row: UV-M1-dup (no table row keyed by it)",
        ]
        if partial_errors != expected_partial_errors:
            failures.append("blind partial: expected only missing row: UV-M1-dup\n" + out_partial)
        else:
            print("  ok  blind partial fails only for missing row UV-M1-dup (passes)")
        # a duplicated checklist tick must fail — coverage must be countable
        dup = tmp / "blind-dup.md"
        dup.write_text("| id | disposition |\n|---|---|\n"
                       "| M1 | handle |\n| M2 | reject |\n"
                       "| UV-M1-dup | ignore (documented) |\n"
                       "| UV-M2-stale | ignore (documented) |\n"
                       "| UV-M1-lost | ignore (documented) |\n"
                       "| UV-M2-conflict | ignore (documented) |\n"
                       "| UV-M1-spurious | reject |\n"
                       + checklist + "- [x] M2\n")
        rc_dup, out_dup = pbp(dup)
        expect("duplicated checklist tick", True, rc_dup, out_dup,
               needle="duplicated checklist entry: M2")
        dup_errors = [line for line in out_dup.splitlines() if line.startswith(" - ")]
        expected_dup_errors = [" - duplicated checklist entry: M2 (2x)"]
        if dup_errors != expected_dup_errors:
            failures.append("blind dup: expected only duplicated checklist entry: M2\n" + out_dup)
        else:
            print("  ok  blind dup fails only for duplicated checklist M2 (passes)")
```

- [x] **Step 10: Run the expanded cell suite directly**

```bash
out=$(cd tests/golden-mini && python3 tests/test_cell_suite.py domain-analysis/mini 2>&1)
rc=$?
printf '%s\n' "$out"
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 0 && test "$out" = 'CELL SUITE: OK'; then
  printf 'ASSERT OK\n'
else
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
CELL SUITE: OK
exit=0
ASSERT OK
```

- [x] **Step 11: Regenerate the sidecar in the correct fixture scope**

```bash
out=$(uv run --with jsonschema python3 tools/gen_analysis_sidecar.py --root tests/golden-mini 2>&1)
rc=$?
printf '%s\n' "$out"
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 0 && test "$out" = 'OK mini: 3 states x 7 events = 21 cells, 0 questions, DRs []'; then
  printf 'ASSERT OK\n'
else
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
OK mini: 3 states x 7 events = 21 cells, 0 questions, DRs []
exit=0
ASSERT OK
```

- [x] **Step 12: Refresh the golden sidecar copy without hand-editing JSON**

```bash
cp tests/golden-mini/domain-analysis/mini/analysis.json tests/golden-mini/expected/analysis.json
cmp -s tests/golden-mini/domain-analysis/mini/analysis.json tests/golden-mini/expected/analysis.json
rc=$?
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 0; then
  printf 'SIDECAR COPY: OK\nASSERT OK\n'
else
  printf 'SIDECAR COPY: FAILED\nASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
exit=0
SIDECAR COPY: OK
ASSERT OK
```

- [x] **Step 13: Check the regenerated sidecar with the correct repository root**

```bash
out=$(uv run --with jsonschema python3 tools/dsc_check.py tests/golden-mini/domain-analysis/mini --repo tests/golden-mini 2>&1)
rc=$?
printf '%s\n' "$out"
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 0 && test "$out" = 'DSC CHECK: OK (3 states x 7 events, 21 cells, 0 guard groups)'; then
  printf 'ASSERT OK\n'
else
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
DSC CHECK: OK (3 states x 7 events, 21 cells, 0 guard groups)
exit=0
ASSERT OK
```

- [x] **Step 14: Verify all four explicit coverage bindings independently**

```bash
python3 - <<'PY'
from pathlib import Path
import json

coverage = json.loads(Path("tests/golden-mini/domain-analysis/mini/analysis.json").read_text())["coverage"]
expected = {
    ("M1", "duplication"): "UV-M1-dup",
    ("M1", "loss"): "UV-M1-lost",
    ("M2", "contradiction"): "UV-M2-conflict",
    ("M1", "commission"): "UV-M1-spurious",
}
errors = []
for (base, category), event in expected.items():
    actual = coverage.get(base, {}).get(category)
    if actual != event:
        errors.append(f"{base}/{category}: expected {event!r}, got {actual!r}")
if errors:
    print("UV COVERAGE BINDINGS: FAIL")
    for error in errors:
        print(" -", error)
    raise SystemExit(1)
print("UV COVERAGE BINDINGS: OK (4 bindings)")
PY
rc=$?
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 0; then
  printf 'ASSERT OK\n'
else
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
UV COVERAGE BINDINGS: OK (4 bindings)
exit=0
ASSERT OK
```

- [x] **Step 15: Prove generated F-01/F-02/F-05 variants are stale before regeneration**

```bash
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
rc=$?
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 1; then
  printf 'ASSERT RED AS REQUIRED\n'
else
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
DRIFT F-01-missing-transition-Open-M2 src/mutants/mini.F-01-missing-transition.py
DRIFT F-02-transfer-fault-Open-M2 src/mutants/mini.F-02-transfer-fault.py
DRIFT F-05-corrupt-state-Open-UV-M1-dup src/mutants/mini.F-05-corrupt-state.py
UNBOUND F-04-sneak-path-Closed-M1 src/mutants/mini.F-04-sneak-path.py (hand-authored)
MUTANT GENERATION: FAIL (checked=3 drift=3 blocked=0 errors=0)
exit=1
ASSERT RED AS REQUIRED
```

Paste this complete output into the task report and Task-B commit body.

- [x] **Step 16: Regenerate and check the three bound variants**

```bash
out=$(python3 tools/gen_mutant_variants.py tests/golden-mini/domain-analysis/mini 2>&1)
rc=$?
printf '%s\n' "$out" | tail -1
printf 'exit=%s\n' "$rc"
if test "$rc" -ne 0 || ! printf '%s\n' "$out" | grep -Fxq 'MUTANT GENERATION: OK (generated=3 drift=0 blocked=0 errors=0)'; then
  printf '%s\nASSERT FAILED\n' "$out"
  exit 1
fi
printf 'MUTANT GENERATION: OK (generated=3 drift=0 blocked=0 errors=0)\nASSERT OK\n'

out=$(python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini 2>&1)
rc=$?
printf '%s\n' "$out" | tail -1
printf 'exit=%s\n' "$rc"
if test "$rc" -ne 0 || ! printf '%s\n' "$out" | grep -Fxq 'MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)'; then
  printf '%s\nASSERT FAILED\n' "$out"
  exit 1
fi
printf 'MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)\nASSERT OK\n'
```

Expected:

```text
MUTANT GENERATION: OK (generated=3 drift=0 blocked=0 errors=0)
exit=0
MUTANT GENERATION: OK (generated=3 drift=0 blocked=0 errors=0)
ASSERT OK
MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)
exit=0
MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)
ASSERT OK
```

- [x] **Step 17: Confirm the four fault-mutant contracts and the F-04 synchronization**

```bash
out=$(python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini 2>&1)
rc=$?
printf '%s\n' "$out" | tail -1
printf 'exit=%s\n' "$rc"
if test "$rc" -ne 0 || ! printf '%s\n' "$out" | grep -Fxq 'FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)'; then
  printf '%s\nASSERT FAILED\n' "$out"
  exit 1
fi
printf 'FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)\nASSERT OK\n'

python3 - <<'PY'
from pathlib import Path
import difflib

base = Path("tests/golden-mini/src/mini.py").read_text().splitlines()
variant = Path("tests/golden-mini/src/mutants/mini.F-04-sneak-path.py").read_text().splitlines()
changed = [line for line in difflib.unified_diff(base, variant, lineterm="")
           if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]
if len(changed) != 2:
    print(f"F04 SYNC: FAIL (changed-lines={len(changed)})")
    raise SystemExit(1)
print("F04 SYNC: OK (changed-lines=2)")
PY
rc=$?
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 0; then
  printf 'ASSERT OK\n'
else
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)
exit=0
FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)
ASSERT OK
F04 SYNC: OK (changed-lines=2)
exit=0
ASSERT OK
```

- [x] **Step 18: Measure the derived matrix-mutation target and require all nine new UV kills**

```bash
python3 - <<'PY'
from pathlib import Path
import subprocess
import sys

command = [sys.executable, "tools/check_matrix_mutation.py",
           "tests/golden-mini/domain-analysis/mini"]
result = subprocess.run(command, capture_output=True, text=True)
lines = result.stdout.splitlines()
summary = next((line for line in lines if line.startswith("MUTATION CHECK:")), "")
print(summary)
expected_summary = "MUTATION CHECK: OK (killed=25 survived=0 errors=0 blocked=0)"
events = ("UV-M1-lost", "UV-M2-conflict", "UV-M1-spurious")
counts = {
    event: sum("KILLED" in line and "kind=ignore-to-handle" in line
               and f"event={event}" in line for line in lines)
    for event in events
}
if result.returncode != 0 or summary != expected_summary or any(count != 3 for count in counts.values()):
    print("UV MUTATION PIN: FAIL")
    for event, count in counts.items():
        print(f" - {event}: expected 3, got {count}")
    print(result.stdout, end="")
    print(result.stderr, end="")
    raise SystemExit(1)
print("UV MUTATION PIN: OK (3 events x 3 KILLED ignore-to-handle)")
PY
rc=$?
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 0; then
  printf 'ASSERT OK\n'
else
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected **derived target, to be remeasured by the executor**:

```text
MUTATION CHECK: OK (killed=25 survived=0 errors=0 blocked=0)
UV MUTATION PIN: OK (3 events x 3 KILLED ignore-to-handle)
exit=0
ASSERT OK
```

If the summary or any per-event count differs, stop with `BLOCKED(task-B): derived count mismatch` and paste the full checker output. Do not change counts, the roadmap, or assertions.

- [x] **Step 19: Run the full selftest after all fixture changes**

```bash
out=$(uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py 2>&1)
rc=$?
printf '%s\n' "$out" | grep -Fx '  ok  matrix mutation count killed=25 (passes)'
printf '%s\n' "$out" | grep -Fx '  ok  matrix mutation family has 16 ignore-to-handle mutants (passes)'
printf '%s\n' "$out" | grep -Fx '  ok  blind partial fails only for missing row UV-M1-dup (passes)'
printf '%s\n' "$out" | grep -Fx '  ok  blind dup fails only for duplicated checklist M2 (passes)'
printf '%s\n' "$out" | tail -1
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 0 \
  && printf '%s\n' "$out" | grep -Fxq 'SELFTEST: OK'; then
  printf 'ASSERT OK\n'
else
  printf '%s\n' "$out"
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
  ok  matrix mutation count killed=25 (passes)
  ok  matrix mutation family has 16 ignore-to-handle mutants (passes)
  ok  blind partial fails only for missing row UV-M1-dup (passes)
  ok  blind dup fails only for duplicated checklist M2 (passes)
SELFTEST: OK
exit=0
ASSERT OK
```

- [x] **Step 20: Update roadmap item 8 with exact, non-overclaiming accounting**

In `docs/roadmap.md`, replace this exact current paragraph (lines 94-99):

```markdown
The reverse matrix family (ignore/reject → handle) now ships, and golden-mini
carries a `UV-M2-stale` column so the family runs on an undesired-variant
cell. That claims **F-15** (out-of-order/stale) with fixture proof. It does
**not** claim F-12, F-16, or F-17: the registry binds one UV category to one
class, so each needs its own column. F-20 needs a terminal-progress shape,
which is not a UV column at all. Those four remain unclaimed.
```

with this exact text:

```markdown
The reverse matrix family (ignore/reject → handle) now runs on all four
matrix-level undesired-variant shapes in golden-mini: `UV-M1-lost` (F-12
loss), `UV-M2-stale` (F-15 out-of-order/stale), `UV-M2-conflict` (F-16
contradiction), and `UV-M1-spurious` (F-17 spontaneous commission). Each
column has three KILLED reverse-family mutants. This claims **F-12**,
**F-15**, **F-16**, and **F-17** with fixture proof.

It does **not** claim F-13, F-14, or F-18: delay, duplication, and value are
implementation-level in the registry. `UV-M1-dup` is a matrix shape, not an
F-14 implementation mutant. F-20 needs a terminal-progress shape, which is
not a UV column at all.
```

This prose is review-only; the executable evidence is Steps 14 and 18. Do not alter `CHANGELOG.md` or the version.

- [x] **Step 21: Run the Task-B independent full gate**

```bash
expect_line() {
  expected=$1
  shift
  out=$("$@" 2>&1)
  rc=$?
  if test "$rc" -eq 0 && printf '%s\n' "$out" | grep -Fx -- "$expected" >/dev/null; then
    printf '%s\nexit=0\nASSERT OK\n' "$expected"
  else
    printf '%s\nexit=%s\nASSERT FAILED\n' "$out" "$rc"
    return 1
  fi
}

expect_line 'DSC CHECK: OK (3 states x 7 events, 21 cells, 0 guard groups)' \
  uv run --with jsonschema python3 tools/dsc_check.py tests/golden-mini/domain-analysis/mini --repo tests/golden-mini || exit 1
expect_line 'MUTATION CHECK: OK (killed=25 survived=0 errors=0 blocked=0)' \
  python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini || exit 1
expect_line 'FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)' \
  python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini || exit 1
expect_line 'MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)' \
  python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini || exit 1
expect_line 'SELFTEST: OK' \
  uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py || exit 1
expect_line 'PACK CONSISTENCY: OK (20 artifacts, registry, version 1.51)' \
  python3 tools/check_pack_consistency.py || exit 1
expect_line '2/2 cases pass' python3 tools/run_tool_tests.py || exit 1
expect_line 'Results: 6 passed, 0 failed, 6 total' python3 tools/run_benchmark.py || exit 1
expect_line 'Primary evidence: 3, Regression anchors: 3, Unknown: 0' \
  python3 tools/benchmark_evidence.py || exit 1
expect_line "REACHABILITY CHECK: OK (3/3 states reachable from 'Idle', 1 terminal)" \
  uv run --with jsonschema python3 tools/check_reachability.py tests/golden-mini/domain-analysis/mini || exit 1

diff_out=$(git diff --check 2>&1)
diff_rc=$?
if test "$diff_rc" -eq 0 && test -z "$diff_out"; then
  printf 'diff-check: clean\nexit=0\nASSERT OK\n'
else
  printf '%s\nexit=%s\nASSERT FAILED\n' "$diff_out" "$diff_rc"
  exit 1
fi
```

Expected stable output lines:

```text
DSC CHECK: OK (3 states x 7 events, 21 cells, 0 guard groups)
MUTATION CHECK: OK (killed=25 survived=0 errors=0 blocked=0)
FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)
MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)
SELFTEST: OK
PACK CONSISTENCY: OK (20 artifacts, registry, version 1.51)
2/2 cases pass
Results: 6 passed, 0 failed, 6 total
Primary evidence: 3, Regression anchors: 3, Unknown: 0
REACHABILITY CHECK: OK (3/3 states reachable from 'Idle', 1 terminal)
diff-check: clean
```

Every successful command also prints `exit=0` and `ASSERT OK`. Paste all output into the Task-B report.

- [x] **Step 22: Verify Task-B file scope before committing**

```bash
expected='docs/roadmap.md
tests/golden-mini/domain-analysis/mini/analysis.json
tests/golden-mini/domain-analysis/mini/disposition-matrix.md
tests/golden-mini/domain-analysis/mini/event-catalogue.md
tests/golden-mini/expected/analysis.json
tests/golden-mini/src/mini.py
tests/golden-mini/src/mutants/mini.F-01-missing-transition.py
tests/golden-mini/src/mutants/mini.F-02-transfer-fault.py
tests/golden-mini/src/mutants/mini.F-04-sneak-path.py
tests/golden-mini/src/mutants/mini.F-05-corrupt-state.py
tests/golden-mini/tests/test_cell_suite.py
tools/selftest/run_selftest.py'
actual=$(git diff --name-only | LC_ALL=C sort)
if test "$actual" = "$expected"; then
  printf '%s\n' "$actual"
  printf 'ASSERT OK: Task-B file scope\n'
else
  printf 'EXPECTED:\n%s\nACTUAL:\n%s\nASSERT FAILED\n' "$expected" "$actual"
  exit 1
fi
```

Expected:

```text
docs/roadmap.md
tests/golden-mini/domain-analysis/mini/analysis.json
tests/golden-mini/domain-analysis/mini/disposition-matrix.md
tests/golden-mini/domain-analysis/mini/event-catalogue.md
tests/golden-mini/expected/analysis.json
tests/golden-mini/src/mini.py
tests/golden-mini/src/mutants/mini.F-01-missing-transition.py
tests/golden-mini/src/mutants/mini.F-02-transfer-fault.py
tests/golden-mini/src/mutants/mini.F-04-sneak-path.py
tests/golden-mini/src/mutants/mini.F-05-corrupt-state.py
tests/golden-mini/tests/test_cell_suite.py
tools/selftest/run_selftest.py
ASSERT OK: Task-B file scope
```

- [x] **Step 23: Commit Task B**

```bash
git add docs/roadmap.md \
  tests/golden-mini/domain-analysis/mini/analysis.json \
  tests/golden-mini/domain-analysis/mini/disposition-matrix.md \
  tests/golden-mini/domain-analysis/mini/event-catalogue.md \
  tests/golden-mini/expected/analysis.json \
  tests/golden-mini/src/mini.py \
  tests/golden-mini/src/mutants/mini.F-01-missing-transition.py \
  tests/golden-mini/src/mutants/mini.F-02-transfer-fault.py \
  tests/golden-mini/src/mutants/mini.F-04-sneak-path.py \
  tests/golden-mini/src/mutants/mini.F-05-corrupt-state.py \
  tests/golden-mini/tests/test_cell_suite.py \
  tools/selftest/run_selftest.py
git commit -m "Add remaining matrix-level UV fixture proof" \
  -m "Golden-mini now carries UV-M1-lost (F-12), UV-M2-conflict (F-16),
and UV-M1-spurious (F-17), plus the corrected M1/duplication binding for
UV-M1-dup. The reverse family is therefore exercised on ignore and reject UV
cells. F-13/F-14/F-18 remain implementation-level; F-20 still needs a
terminal-progress shape.

Evidence:
- Task-B red selftest observed the 25/16/three-UV/binding assertions fail
  before fixture changes
- generator red probe: drift=3, exit=1 before regeneration
- MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)
- DSC CHECK: OK (3 states x 7 events, 21 cells, 0 guard groups)
- explicit coverage bindings: 4/4 OK
- MUTATION CHECK: OK (killed=25 survived=0 errors=0 blocked=0)
- UV mutation pin: 3 events x 3 KILLED ignore-to-handle
- FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)
- F04 hand-authored variant synchronized: changed-lines=2
- SELFTEST: OK, including exact one-reason partial/dup Part-B fixtures
- PACK CONSISTENCY: OK (20 artifacts, registry, version 1.51)
- run_tool_tests: 2/2 cases pass
- run_benchmark: Results: 6 passed, 0 failed, 6 total
- git diff --check: clean"

subject=$(git log -1 --oneline | sed 's/^[0-9a-f][0-9a-f]* //')
if test "$subject" = 'Add remaining matrix-level UV fixture proof' \
  && test -z "$(git diff --cached --name-only)" \
  && test -z "$(git status --short)"; then
  printf 'ASSERT OK: Task-B commit exists and tree is clean\n'
else
  printf 'ASSERT FAILED: Task-B commit or clean-tree check\n'
  git log -1 --oneline
  git status --short
  exit 1
fi
```

Expected:

```text
[main <Task-B-SHA>] Add remaining matrix-level UV fixture proof
ASSERT OK: Task-B commit exists and tree is clean
```

`<Task-B-SHA>` is Git-generated and is not an expected literal. Paste `git log -1 --oneline` and the entire commit message from `git show --format=full HEAD` into the task report.

**Task-B deliverable:** golden-mini has seven ordered events, 21 cells, four exact coverage bindings, regenerated sidecar/variants, a manually synchronized F-04 variant, Part-B fixtures with one precise failure each, and honest roadmap accounting.

**Do not:** claim F-13/F-14/F-18/F-20, implement an unbound-direction checker, migrate historical sidecars, change registry/schema/version/changelog, release, tag, or push.

## Completion report requirements

The executor’s final report must paste:

1. The Start-gate output.
2. Task A’s pre-mechanism selftest red output, constructed `UV-does-not-exist` checker red output, Task-A full-gate output, exact two-file scope output, and Task-A commit SHA/message.
3. Task B’s eleven-heading selftest red output, generator drift red output, sidecar generation output, four-binding output, UV mutation-pin output, full-gate output, exact twelve-file scope output, and Task-B commit SHA/message.
4. `git status --short` after each commit, showing no staged or unstaged files.
5. Any `BLOCKED(...)` result verbatim. A block is a result; a survivor, count mismatch, unexpected Part-B error, generator drift after regeneration, or any red gate is not a reason to edit expected values or continue.

No release, tag, or push is part of this plan.
