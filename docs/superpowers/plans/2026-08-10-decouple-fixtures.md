# Decouple Fixtures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Tick a checkbox in the same work session as its completed action; never reconstruct task state from memory.

**Goal:** Bind the F-04 sneak-path fault variant to the existing deterministic generator and prove that generation reproduces the existing tracked variant byte-for-byte.

**Architecture:** Task A first makes the existing selftest require four bound variants and no `UNBOUND` output, then observes that assertion red while F-04 is still hand-authored. A constructed temporary binding proves the generator detects a one-line byte mismatch; the real binding is then checked against the unchanged tracked variant *before* write mode is allowed. The write-mode check is intentionally directional: the tracked F-04 file is the reference, never material to be edited until a binding passes.

**Tech Stack:** Python 3 stdlib, existing `tools/gen_mutant_variants.py`, existing golden-mini fixture, existing selftest framework, `uv` with development requirements and `jsonschema`.

## Spec deviations

1. **The start gate checks ancestry rather than literal equality of `HEAD`.** At planning time, `HEAD` is exactly `30aa9c4` (`30aa9c442e7769acb0175b701eeae8e122c3310e`) and the worktree is clean. Requiring literal equality at execution would make the plan impossible to run after this plan itself is committed, because the clean-tree rule then necessarily gives `HEAD` a later commit. This plan therefore requires `30aa9c4` to be an ancestor of `HEAD`; it still blocks a tree not based on the measured design commit.
2. **Task A updates `tools/selftest/run_selftest.py` as well as the binding JSON.** The live selftest at `tools/selftest/run_selftest.py:564-569` currently asserts `checked=3`. Without its exact update, a correct F-04 binding makes the pack selftest red. The design spec names the required postcondition (`checked=4`, no `UNBOUND` line), so the selftest change is a required coupled gate, not scope widening.

## Global constraints

- Begin only from a clean worktree whose `HEAD` contains `30aa9c4`.
- Task A source changes are limited to `tests/golden-mini/domain-analysis/mini/mutant-generation.json` and `tools/selftest/run_selftest.py`. The plan file changes only to tick Task-A checkboxes in the Task-A commit.
- Do **not** modify `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py`. It is the byte-identity reference. A `DRIFT` result in check mode is `BLOCKED(task-A)`, not permission to rewrite that file.
- Do **not** modify `tools/gen_mutant_variants.py`, `tools/check_fault_mutants.py`, `tools/check_matrix_mutation.py`, or `tools/part_b_pack.py`.
- Keep the region-counting gate in `tools/selftest/run_selftest.py`; do not remove or weaken it.
- Do not touch `analysis.json`, `expected/analysis.json`, `fault-mutants.json`, `matrix-mutation.json`, the matrix, the catalogue, the cell suite, generated sidecars, versions, `CHANGELOG.md`, `README.md`, or roadmap prose.
- If a later command would need to regenerate a sidecar, the only permitted command is `uv run --with jsonschema python3 tools/gen_analysis_sidecar.py --root tests/golden-mini`; this Task A must not run it. Never use `--root .`.
- Run golden-mini `dsc_check` only with `--repo tests/golden-mini`; never use `--repo .`.
- Do not rely on `cmd; echo "exit=$?"`: it leaves the shell successful. Every planned assertion captures `rc=$?` and explicitly tests it.
- If any temporary copied analysis directory ever invokes `check_matrix_mutation.py`, give that copy an absolute `workingDirectory`; this plan invokes that checker only against the live fixture and must not edit its configuration.
- Preserve these measured outputs: `MUTATION CHECK: OK (killed=25 survived=0 errors=0 blocked=0)`, `FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)`, `DSC CHECK: OK (3 states x 7 events, 21 cells, 0 guard groups)`, and `PACK CONSISTENCY: OK (20 artifacts, registry, version 1.51)`.
- A stale exact-current-text block, any unexpected red probe, `DRIFT` after the real binding, `SURVIVED`, changed F-04 variant, changed count, or red full gate is `BLOCKED(task-A): <measured reason>`. Paste the complete output and stop. Do not alter expected values, tracked variants, or the plan to make a check green.
- No Task-B implementation, release, tag, push, version bump, or scope widening is authorized by this plan.

## Ungated surfaces

| Surface | Executable gate | Review obligation |
|---|---|---|
| `mutant-generation.json` F-04 binding | Constructed wrong-replacement red probe; real `--check` byte identity; write-mode F-04 status check; generator selftest | Verify the exact one-line `match` and one-line `replace` below; no other source line is allowed into either array. |
| `tools/selftest/run_selftest.py` count/no-`UNBOUND` assertion | Observed red before binding and green after binding | Verify that the green assertion rejects `DRIFT`, `BLOCKED`, and `UNBOUND`, rather than merely looking for `checked=4`. |
| Plan checkbox state | No executable pack gate | Review that only Task-A boxes are changed from `[ ]` to `[x]` in the Task-A commit; Task B remains absent except for its one-sentence section. |

## File structure

| Path | Responsibility |
|---|---|
| `tests/golden-mini/domain-analysis/mini/mutant-generation.json:55-73` | Add the F-04 `replace-block` binding whose generated contents must equal the existing tracked variant. |
| `tools/selftest/run_selftest.py:564-569` | Pin the generator’s green golden-mini case to four bound variants and forbid an `UNBOUND` line. |
| `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py` | Read-only byte-identity reference; write mode must leave it unmodified. |

## Start gate — clean handoff

Run this before Task A. The ancestry form is deliberate; see Spec deviation 1.

```bash
required=30aa9c442e7769acb0175b701eeae8e122c3310e
status=$(git status --short)
if test -n "$status"; then
  printf 'BLOCKED(preflight): working tree is not clean\n%s\n' "$status"
  exit 1
fi
printf 'ASSERT OK: clean worktree\n'

staged=$(git diff --cached --name-only)
if test -n "$staged"; then
  printf 'BLOCKED(preflight): staged files exist\n%s\n' "$staged"
  exit 1
fi
printf 'ASSERT OK: no staged files\n'

git merge-base --is-ancestor "$required" HEAD
rc=$?
if test "$rc" -eq 0; then
  printf 'ASSERT OK: HEAD contains 30aa9c4\n'
else
  printf 'BLOCKED(preflight): HEAD does not contain 30aa9c4\nexit=%s\n' "$rc"
  exit 1
fi
```

Expected:

```text
ASSERT OK: clean worktree
ASSERT OK: no staged files
ASSERT OK: HEAD contains 30aa9c4
```

If any `BLOCKED(preflight)` line prints, do not edit a file or start Task A. Paste the complete output into the Task-A report.

---

### Task A: Generate the F-04 sneak-path variant without changing its reference file

**Files:**
- Modify: `tools/selftest/run_selftest.py:564-569`
- Modify: `tests/golden-mini/domain-analysis/mini/mutant-generation.json:55-73`
- Modify only for tracking at commit time: `docs/superpowers/plans/2026-08-10-decouple-fixtures.md`
- Read-only: `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py`

**Interfaces:**
- Consumes the existing `fault-mutants.json` entry `F-04-sneak-path-Closed-M1` with variant path `src/mutants/mini.F-04-sneak-path.py` and the existing source line `raise RejectedError("M1 rejected in Closed")`.
- Produces a `replace-block` binding with one exact source match and one exact replacement.
- Produces `MUTANT GENERATION: OK (checked=4 drift=0 blocked=0 errors=0)` with no `UNBOUND` line.
- Preserves `FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)` and leaves the tracked F-04 variant absent from `git status --short` after write mode.

- [x] **Step 1: Make the generator green-case selftest require four bound variants**

In `tools/selftest/run_selftest.py`, replace this exact current text:

```python
        if "checked=3" not in out:
            failures.append("generator green case: expected checked=3\n" + out)
        elif "DRIFT" in out or "BLOCKED" in out:
            failures.append("generator green case: unexpected DRIFT/BLOCKED line\n" + out)
        else:
            print("  ok  generator green case checked=3 without DRIFT/BLOCKED (passes)")
```

with this exact text:

```python
        if "checked=4" not in out:
            failures.append("generator green case: expected checked=4\n" + out)
        elif "DRIFT" in out or "BLOCKED" in out or "UNBOUND" in out:
            failures.append("generator green case: unexpected DRIFT/BLOCKED/UNBOUND line\n" + out)
        else:
            print("  ok  generator green case checked=4 without DRIFT/BLOCKED/UNBOUND (passes)")
```

Do not add a binding yet. This assertion must observe the current three-bound/one-unbound state as red first.

- [x] **Step 2: Observe the selftest red before F-04 is bound**

```bash
out=$(uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py 2>&1)
rc=$?
printf '%s\n' "$out" | grep -A5 -Fx ' - generator green case: expected checked=4'
printf '%s\n' "$out" | grep -Fx 'SELFTEST: FAIL'
printf 'exit=%s\n' "$rc"
heading_count=$(printf '%s\n' "$out" | grep -Fc ' - generator green case: expected checked=4')
if test "$rc" -eq 1 \
  && test "$heading_count" -eq 1 \
  && printf '%s\n' "$out" | grep -Fxq 'UNBOUND F-04-sneak-path-Closed-M1 src/mutants/mini.F-04-sneak-path.py (hand-authored)' \
  && printf '%s\n' "$out" | grep -Fxq 'MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)' \
  && printf '%s\n' "$out" | grep -Fxq 'SELFTEST: FAIL'; then
  printf 'ASSERT RED AS REQUIRED\n'
else
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
 - generator green case: expected checked=4
OK F-01 F-01-missing-transition-Open-M2
OK F-02 F-02-transfer-fault-Open-M2
OK F-05 F-05-corrupt-state-Open-UV-M1-dup
UNBOUND F-04-sneak-path-Closed-M1 src/mutants/mini.F-04-sneak-path.py (hand-authored)
MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)
SELFTEST: FAIL
exit=1
ASSERT RED AS REQUIRED
```

Paste the complete value of `$out` into the Task-A report and commit body. If the failure is absent, duplicated, or accompanied by a different selftest failure, stop with `BLOCKED(task-A): generator-count red probe differs from the measured three-bound state`.

- [x] **Step 3: Construct the wrong-replacement byte-identity red probe**

This temporary copy deliberately generates the unmutated `raise` line for F-04. It must drift from the tracked sneak-path file. It modifies only `mktemp` data, never the repository.

```bash
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cp -R tests/golden-mini "$tmp/golden-mini"
python3 - "$tmp/golden-mini/domain-analysis/mini/mutant-generation.json" <<'PY'
from pathlib import Path
import json
import sys

path = Path(sys.argv[1])
data = json.loads(path.read_text())
data["bindings"].insert(2, {
    "fault": "F-04",
    "binder": "sneak-path",
    "id": "F-04-sneak-path-Closed-M1",
    "cell": "Closed x M1",
    "variant": "src/mutants/mini.F-04-sneak-path.py",
    "mode": "replace-block",
    "match": [
        "            raise RejectedError(\"M1 rejected in Closed\")"
    ],
    "replace": [
        "            raise RejectedError(\"M1 rejected in Closed\")"
    ]
})
path.write_text(json.dumps(data, indent=2) + "\n")
PY
out=$(python3 tools/gen_mutant_variants.py --check "$tmp/golden-mini/domain-analysis/mini" 2>&1)
rc=$?
printf '%s\n' "$out"
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 1 \
  && printf '%s\n' "$out" | grep -Fxq 'DRIFT F-04-sneak-path-Closed-M1 src/mutants/mini.F-04-sneak-path.py' \
  && printf '%s\n' "$out" | grep -Fxq 'MUTANT GENERATION: FAIL (checked=4 drift=1 blocked=0 errors=0)'; then
  printf 'ASSERT RED AS REQUIRED\n'
else
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
OK F-01 F-01-missing-transition-Open-M2
OK F-02 F-02-transfer-fault-Open-M2
DRIFT F-04-sneak-path-Closed-M1 src/mutants/mini.F-04-sneak-path.py
OK F-05 F-05-corrupt-state-Open-UV-M1-dup
MUTANT GENERATION: FAIL (checked=4 drift=1 blocked=0 errors=0)
exit=1
ASSERT RED AS REQUIRED
```

Paste this complete output. It is the R-RED-PROBE proving that a one-line mismatch is detectable before the real binding is introduced.

- [x] **Step 4: Add the exact F-04 `replace-block` binding**

In `tests/golden-mini/domain-analysis/mini/mutant-generation.json`, replace this exact current F-05 object:

```json
    {
      "fault": "F-05",
      "binder": "corrupt-state",
      "id": "F-05-corrupt-state-Open-UV-M1-dup",
      "cell": "Open x UV-M1-dup",
      "variant": "src/mutants/mini.F-05-corrupt-state.py",
      "mode": "replace-block",
      "requiresProjection": "dup_count",
      "match": [
        "        if event == \"UV-M1-dup\":",
        "            self.dup_count += 1",
        "            return \"handled\""
      ],
      "replace": [
        "        if event == \"UV-M1-dup\":",
        "            self.dup_count += 2  # F-05 corrupt state: counter moves by the wrong amount",
        "            return \"handled\""
      ]
    }
```

with this exact text:

```json
    {
      "fault": "F-04",
      "binder": "sneak-path",
      "id": "F-04-sneak-path-Closed-M1",
      "cell": "Closed x M1",
      "variant": "src/mutants/mini.F-04-sneak-path.py",
      "mode": "replace-block",
      "match": [
        "            raise RejectedError(\"M1 rejected in Closed\")"
      ],
      "replace": [
        "            return \"ignored\"  # F-04 sneak path: Closed x M1 accepted"
      ]
    },
    {
      "fault": "F-05",
      "binder": "corrupt-state",
      "id": "F-05-corrupt-state-Open-UV-M1-dup",
      "cell": "Open x UV-M1-dup",
      "variant": "src/mutants/mini.F-05-corrupt-state.py",
      "mode": "replace-block",
      "requiresProjection": "dup_count",
      "match": [
        "        if event == \"UV-M1-dup\":",
        "            self.dup_count += 1",
        "            return \"handled\""
      ],
      "replace": [
        "        if event == \"UV-M1-dup\":",
        "            self.dup_count += 2  # F-05 corrupt state: counter moves by the wrong amount",
        "            return \"handled\""
      ]
    }
```

Do not run write mode in this step. The next step is the mandatory check-mode proof against the unchanged tracked F-04 reference file.

- [x] **Step 5: Prove byte identity in generator check mode before any write**

```bash
out=$(python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini 2>&1)
rc=$?
printf '%s\n' "$out"
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 0 \
  && printf '%s\n' "$out" | grep -Fxq 'OK F-01 F-01-missing-transition-Open-M2' \
  && printf '%s\n' "$out" | grep -Fxq 'OK F-02 F-02-transfer-fault-Open-M2' \
  && printf '%s\n' "$out" | grep -Fxq 'OK F-04 F-04-sneak-path-Closed-M1' \
  && printf '%s\n' "$out" | grep -Fxq 'OK F-05 F-05-corrupt-state-Open-UV-M1-dup' \
  && printf '%s\n' "$out" | grep -Fxq 'MUTANT GENERATION: OK (checked=4 drift=0 blocked=0 errors=0)' \
  && ! printf '%s\n' "$out" | grep -Fq 'UNBOUND'; then
  printf 'ASSERT OK: check-mode byte identity\n'
else
  printf 'BLOCKED(task-A): F-04 binding does not reproduce the tracked reference\n'
  exit 1
fi
```

Expected:

```text
OK F-01 F-01-missing-transition-Open-M2
OK F-02 F-02-transfer-fault-Open-M2
OK F-04 F-04-sneak-path-Closed-M1
OK F-05 F-05-corrupt-state-Open-UV-M1-dup
MUTANT GENERATION: OK (checked=4 drift=0 blocked=0 errors=0)
exit=0
ASSERT OK: check-mode byte identity
```

Paste this complete output. If it prints `DRIFT`, stop exactly here with the printed `BLOCKED(task-A)` line. **Never run write mode and never change `mini.F-04-sneak-path.py` to make this check pass.**

- [x] **Step 6: Run write mode and prove it leaves F-04 unmodified**

```bash
out=$(python3 tools/gen_mutant_variants.py tests/golden-mini/domain-analysis/mini 2>&1)
rc=$?
status=$(git status --short)
f04_status=$(git status --short -- tests/golden-mini/src/mutants/mini.F-04-sneak-path.py)
git diff --quiet -- tests/golden-mini/src/mutants/mini.F-04-sneak-path.py
diff_rc=$?
expected_status=' M tests/golden-mini/domain-analysis/mini/mutant-generation.json
 M tools/selftest/run_selftest.py'
printf '%s\n' "$out"
printf 'exit=%s\n' "$rc"
printf 'git status --short:\n%s\n' "$status"
if test "$rc" -eq 0 \
  && printf '%s\n' "$out" | grep -Fxq 'MUTANT GENERATION: OK (generated=4 drift=0 blocked=0 errors=0)' \
  && test -z "$f04_status" \
  && test "$diff_rc" -eq 0 \
  && test "$status" = "$expected_status"; then
  printf 'F04 STATUS: clean\nASSERT OK: write mode preserved the tracked F-04 file\n'
else
  printf 'BLOCKED(task-A): write mode changed F-04 or changed an out-of-scope file\n'
  exit 1
fi
```

Expected:

```text
GENERATED F-01 F-01-missing-transition-Open-M2 -> src/mutants/mini.F-01-missing-transition.py
GENERATED F-02 F-02-transfer-fault-Open-M2 -> src/mutants/mini.F-02-transfer-fault.py
GENERATED F-04 F-04-sneak-path-Closed-M1 -> src/mutants/mini.F-04-sneak-path.py
GENERATED F-05 F-05-corrupt-state-Open-UV-M1-dup -> src/mutants/mini.F-05-corrupt-state.py
MUTANT GENERATION: OK (generated=4 drift=0 blocked=0 errors=0)
exit=0
git status --short:
 M tests/golden-mini/domain-analysis/mini/mutant-generation.json
 M tools/selftest/run_selftest.py
F04 STATUS: clean
ASSERT OK: write mode preserved the tracked F-04 file
```

Paste this complete output. The `GENERATED F-04` line names an attempted write; the empty F-04 status and zero F-04 diff prove its bytes were already identical.

- [x] **Step 7: Observe the Task-A selftest green**

```bash
out=$(uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py 2>&1)
rc=$?
printf '%s\n' "$out" | grep -Fx '  ok  generator check mode green on golden-mini (passes)'
printf '%s\n' "$out" | grep -Fx '  ok  generator green case checked=4 without DRIFT/BLOCKED/UNBOUND (passes)'
printf '%s\n' "$out" | grep -Fx 'SELFTEST: OK'
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 0 \
  && printf '%s\n' "$out" | grep -Fxq '  ok  generator check mode green on golden-mini (passes)' \
  && printf '%s\n' "$out" | grep -Fxq '  ok  generator green case checked=4 without DRIFT/BLOCKED/UNBOUND (passes)' \
  && printf '%s\n' "$out" | grep -Fxq 'SELFTEST: OK'; then
  printf 'ASSERT OK\n'
else
  printf '%s\nASSERT FAILED\n' "$out"
  exit 1
fi
```

Expected:

```text
  ok  generator check mode green on golden-mini (passes)
  ok  generator green case checked=4 without DRIFT/BLOCKED/UNBOUND (passes)
SELFTEST: OK
exit=0
ASSERT OK
```

- [x] **Step 8: Run Task A’s independent full gate**

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
expect_line 'MUTANT GENERATION: OK (checked=4 drift=0 blocked=0 errors=0)' \
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
MUTANT GENERATION: OK (checked=4 drift=0 blocked=0 errors=0)
SELFTEST: OK
PACK CONSISTENCY: OK (20 artifacts, registry, version 1.51)
2/2 cases pass
Results: 6 passed, 0 failed, 6 total
Primary evidence: 3, Regression anchors: 3, Unknown: 0
REACHABILITY CHECK: OK (3/3 states reachable from 'Idle', 1 terminal)
diff-check: clean
```

Every line above is followed by `exit=0` and `ASSERT OK`. Paste the complete gate output into the Task-A report and commit body.

- [x] **Step 9: Verify Task-A source-file scope before tracking checkboxes**

```bash
expected='tests/golden-mini/domain-analysis/mini/mutant-generation.json
tools/selftest/run_selftest.py'
actual=$(git diff --name-only | LC_ALL=C sort)
if test "$actual" = "$expected"; then
  printf '%s\n' "$actual"
  printf 'ASSERT OK: Task-A source-file scope\n'
else
  printf 'EXPECTED:\n%s\nACTUAL:\n%s\nASSERT FAILED\n' "$expected" "$actual"
  exit 1
fi
```

Expected:

```text
tests/golden-mini/domain-analysis/mini/mutant-generation.json
tools/selftest/run_selftest.py
ASSERT OK: Task-A source-file scope
```

- [x] **Step 10: Tick Task-A checkboxes in this same work session and commit Task A**

First replace these exact current checkbox lines in this plan with the exact checked lines. Do not change any Task-B text.

```python
from pathlib import Path

# Tick only real checkbox lines: those that START a line. The step titles also
# appear indented inside this very code block, so a plain substring replace
# double-matches and aborts. Line-anchored matching is what makes a
# checkbox-ticking script safe to embed in the file it edits.
path = Path("docs/superpowers/plans/2026-08-10-decouple-fixtures.md")
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
start = next(i for i, l in enumerate(lines) if l.startswith("### Task A"))
end = next(i for i, l in enumerate(lines) if l.startswith("## Task B"))
ticked = 0
for i in range(start, end):
    if lines[i].startswith("- [ ] **Step"):
        lines[i] = lines[i].replace("- [ ] **Step", "- [x] **Step", 1)
        ticked += 1
if ticked != 10:
    raise SystemExit(f"expected to tick 10 Task-A checkboxes, ticked {ticked}")
path.write_text("".join(lines), encoding="utf-8")
print(f"TASK A CHECKBOXES: OK ({ticked}/10 ticked before commit)")
```

Run that exact script with `python3 - <<'PY'` / `PY`, then commit exactly these files:

```bash
git add tests/golden-mini/domain-analysis/mini/mutant-generation.json \
  tools/selftest/run_selftest.py \
  docs/superpowers/plans/2026-08-10-decouple-fixtures.md
git commit -m "Generate F-04 sneak-path mutant" \
  -m "Binds the last hand-authored golden-mini fault variant through the
existing exact-single-match replace-block generator. The tracked F-04 file is
the reference: check mode passed before write mode, and write mode left it
unmodified, proving byte identity rather than merely producing a plausible
variant.

Evidence:
- red selftest before the binding: expected checked=4, observed checked=3
  plus the F-04 UNBOUND line
- constructed wrong-replacement red probe: DRIFT F-04-sneak-path-Closed-M1,
  checked=4 drift=1
- real binding before write: MUTANT GENERATION: OK (checked=4 drift=0 blocked=0 errors=0)
  with no UNBOUND line
- write mode: MUTANT GENERATION: OK (generated=4 drift=0 blocked=0 errors=0)
  and F04 STATUS: clean
- FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)
- MUTATION CHECK: OK (killed=25 survived=0 errors=0 blocked=0)
- DSC CHECK: OK (3 states x 7 events, 21 cells, 0 guard groups)
- SELFTEST: OK
- PACK CONSISTENCY: OK (20 artifacts, registry, version 1.51)
- run_tool_tests: 2/2 cases pass
- run_benchmark: Results: 6 passed, 0 failed, 6 total
- git diff --check: clean"

subject=$(git log -1 --format=%s)
status=$(git status --short)
staged=$(git diff --cached --name-only)
if test "$subject" = 'Generate F-04 sneak-path mutant' \
  && test -z "$status" \
  && test -z "$staged"; then
  printf 'ASSERT OK: Task-A commit exists and tree is clean\n'
else
  printf 'ASSERT FAILED: Task-A commit or clean-tree check\n'
  git log -1 --oneline
  git status --short
  exit 1
fi
```

Expected fixed output after Git’s dynamic commit line:

```text
TASK A CHECKBOXES: OK (10/10 ticked before commit)
ASSERT OK: Task-A commit exists and tree is clean
```

Paste the complete Task-A commit output, `git log -1 --oneline`, `git show --format=full --no-patch HEAD`, and final empty `git status --short` into the Task-A report. This task’s deliverable is complete only after that commit exists.

**Task-A deliverable:** F-04 is generator-bound by an exact one-line replacement, check mode proves byte identity against the unchanged tracked file before write mode, write mode leaves the tracked file clean, the selftest pins four bound/no-unbound behavior, and all measured gates remain green.

**Do not:** change the tracked F-04 variant to fit the binding; alter generator/checker code; remove the region gate; start Task B; regenerate JSON; release, tag, or push.

## Task B — derive the Part-B blind fixtures from the live catalogue declaration

**Task-B authority:** The completed Task-A instructions and their ten checked
boxes above are historical evidence and must remain unchanged. This section
replaces the former one-sentence Task-B placeholder and explicitly authorizes
only the Task-B work below. It supersedes the prior Task-A-only sentence that
said no Task-B implementation was authorized; it does not reopen Task A.

**Task-B spec deviations:** None. The design spec explicitly says to verify the
candidate helper against the real fixture text and adapt it when that text
differs. The implementation therefore preserves the current special
`handle`/`reject` dispositions and the two-row `M1` fine-table example instead
of normalizing all current rows to `ignore (documented)`.

### Task-B-specific constraints

- Modify only `tools/selftest/run_selftest.py` and this plan’s Task-B checkbox
  state. Do not modify `tools/part_b_pack.py`, the event catalogue, generated
  sidecars, the region-counting gate, the Task-A `checked=4` assertion, any
  mutation/fault configuration, versions, `CHANGELOG.md`, `README.md`, or
  roadmap prose.
- `tools/part_b_pack.py` is read-only. Its three existing error forms are the
  oracle: `missing row`, `missing checklist tick`, and `duplicated checklist
  entry`.
- Read the identifiers from the exact `<!-- event-ids: ... -->` declaration in
  `tests/golden-mini/domain-analysis/mini/event-catalogue.md`. The measured
  declaration currently contains `M1 M2 UV-M1-dup UV-M2-stale UV-M1-lost
  UV-M2-conflict UV-M1-spurious`; do not hard-code that complete list in a
  fixture or checklist.
- The current checker output has `7 events, 0 pair orderings`. This task is
  deliberately limited to declaration event IDs required by the committed
  specification. It does not add generation for a future `P-nna/b` pair
  ordering; if one is added later, record a separate follow-up rather than
  widening this task.
- Preserve the current fixture meanings that the Part-B checker does **not**
  validate: `M1` is `handle`, `M2` and `UV-M1-spurious` are `reject`, all other
  current ordinary rows are `ignore (documented)`, and fine `M1` has exactly
  its current two situation rows. The helper’s default for a newly declared ID
  is `ignore (documented)`.
- `partial` must retain the `UV-M1-dup` checklist tick and fail for exactly
  `missing row: UV-M1-dup (no table row keyed by it)`. `dup` must fail for
  exactly `duplicated checklist entry: M2 (2x)`.
- Use `rc=$?` plus an explicit numeric test for every command whose exit status
  is asserted. Do not use `cmd; echo "exit=$?"` as an assertion.
- Preserve these measured outputs: `MUTATION CHECK: OK (killed=25 survived=0
  errors=0 blocked=0)`, `FAULT MUTANTS: OK (killed=4 survived=0 errors=0
  blocked=0)`, `MUTANT GENERATION: OK (checked=4 drift=0 blocked=0 errors=0)`,
  `DSC CHECK: OK (3 states x 7 events, 21 cells, 0 guard groups)`, and `PACK
  CONSISTENCY: OK (20 artifacts, registry, version 1.51)`.
- A stale exact-text edit anchor, unexpected red-probe result, altered Task-A
  assertion or region gate, changed count, red full gate, or a red case with
  any additional Part-B error is `BLOCKED(task-B): <measured reason>`. Paste
  the complete displayed output and stop; do not edit an expected value,
  catalogue, checker, or source fixture to force green.
- No release, tag, push, version change, CHANGELOG entry, or scope widening.

### Task-B ungated surfaces

| Surface | Executable gate | Exact review obligation |
|---|---|---|
| Current blind-table dispositions and fine `M1` prose | `part_b_pack.py` checks only first-column row keys and final checklist ticks; it does not check disposition prose. | In Steps 5–6, compare the literal current rows and the exact `dispositions` mapping / two `M1` replacement rows verbatim. The replacement must retain `handle`, `reject`, `ignore (documented)`, `Idle`, and `Open (after M2, see UV-M1-dup)` exactly as shown. |
| Source of generated IDs | The temporary `M3-growth` catalogue probe uses the same declaration consumed by `part_b_pack.py`; four generated tables are checked against that temporary catalogue. | Verify the parser pattern is exactly `r"<!-- event-ids: (.+?) -->"` and the input path is exactly `tests/golden-mini/domain-analysis/mini/event-catalogue.md`; do not substitute an inline seven-ID list. |
| Deliberate red fixtures | Existing exact-error-list assertions and the temporary-growth equivalents execute. | Compare the two expected lists verbatim: one `missing row: UV-M1-dup` line and one `duplicated checklist entry: M2 (2x)` line, with no extra line. |

### Task B start gate — clean post-Task-A handoff

Run this before any Task-B edit. The ancestry check permits the plan itself to
be committed after the measured Task-A commit while still blocking an unrelated
history.

```bash
required=08c211cfeb14d5656b3dc2f22faffd6fcc81851a
status=$(git status --short)
if test -n "$status"; then
  printf 'BLOCKED(preflight): working tree is not clean\n%s\n' "$status"
  exit 1
fi
printf 'ASSERT OK: clean worktree\n'

staged=$(git diff --cached --name-only)
if test -n "$staged"; then
  printf 'BLOCKED(preflight): staged files exist\n%s\n' "$staged"
  exit 1
fi
printf 'ASSERT OK: no staged files\n'

git merge-base --is-ancestor "$required" HEAD
rc=$?
if test "$rc" -eq 0; then
  printf 'ASSERT OK: HEAD contains 08c211c\n'
else
  printf 'BLOCKED(preflight): HEAD does not contain 08c211c\nexit=%s\n' "$rc"
  exit 1
fi
```

Expected:

```text
ASSERT OK: clean worktree
ASSERT OK: no staged files
ASSERT OK: HEAD contains 08c211c
```

Paste the complete start-gate output. If it prints `BLOCKED(preflight)`, do not
edit a file or begin Task B.

---

### Task B: Derive every golden-mini Part-B fixture from catalogue event IDs

**Files:**
- Modify: `tools/selftest/run_selftest.py:668-744` (current Part-B fixture
  block; the line range is measured at `08c211c`)
- Modify only for tracking at commit time:
  `docs/superpowers/plans/2026-08-10-decouple-fixtures.md`
- Read-only: `tests/golden-mini/domain-analysis/mini/event-catalogue.md:3`
- Read-only: `tools/part_b_pack.py:48-55,215-250`

**Interfaces:**
- Consumes the exact event declaration comment in the live golden-mini
  catalogue and the current `pbp` subprocess wrapper.
- Produces `catalogue_event_ids(catalogue: Path) -> list[str]`,
  `blind_table(ids: list[str], *, fine: bool = False, omit_row=(),
  omit_tick=(), duplicate_tick=()) -> str`, and
  `pbp(blind: Path, repo: Path = ROOT / "tests" / "golden-mini") -> tuple[int,
  str]` inside `main()`.
- Produces `full`, `fine`, `partial`, and `dup` fixtures from one ID list and
  explicit named violations, plus a temporary `M3-growth` proof that all four
  generated shapes grow from that declaration.
- Preserves exact current normal-case Part-B output and the two one-reason-only
  red outputs; preserves all measured pack gates listed above.

- [x] **Step 1: Make the Part-B wrapper accept the temporary probe repository**

The following edit script contains the exact current text and exact replacement
text. It must print its one success line or stop.

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("tools/selftest/run_selftest.py")
source = path.read_text(encoding="utf-8")
# Exact current text:
old = '''        def pbp(blind: Path) -> tuple[int, str]:
            r = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "part_b_pack.py"),
                 "domain-analysis/mini",
                 "--repo", str(ROOT / "tests" / "golden-mini"),
                 "--check", str(blind)],
                capture_output=True, text=True)
            return r.returncode, (r.stdout + r.stderr).strip()
'''
# Exact replacement text:
new = '''        def pbp(blind: Path, repo: Path = ROOT / "tests" / "golden-mini") -> tuple[int, str]:
            r = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "part_b_pack.py"),
                 "domain-analysis/mini",
                 "--repo", str(repo),
                 "--check", str(blind)],
                capture_output=True, text=True)
            return r.returncode, (r.stdout + r.stderr).strip()
'''
if source.count(old) != 1:
    raise SystemExit(f"BLOCKED(task-B): pbp current-text count is {source.count(old)}, expected 1")
path.write_text(source.replace(old, new), encoding="utf-8")
print("PBP REPOSITORY PARAMETER: INSTALLED")
PY
```

Expected:

```text
PBP REPOSITORY PARAMETER: INSTALLED
```

This is test scaffolding only. Do not add the catalogue parser or table helper
until the next step’s literal fixture has been observed red.

- [x] **Step 2: Add the literal-fixture growth assertion before adding the helper**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("tools/selftest/run_selftest.py")
source = path.read_text(encoding="utf-8")
# Exact current text:
old = '''        else:
            print("  ok  blind dup fails only for duplicated checklist M2 (passes)")
'''
# Exact replacement text:
new = '''        else:
            print("  ok  blind dup fails only for duplicated checklist M2 (passes)")

        # R-FIXTURE-GROWTH: the present full fixture is a seven-ID literal.
        # Against a temporary catalogue with a new declaration ID it must be red.
        growth_repo = tmp / "blind-growth-repo"
        shutil.copytree(ROOT / "tests" / "golden-mini", growth_repo)
        growth_catalogue = growth_repo / "domain-analysis" / "mini" / "event-catalogue.md"
        growth_catalogue.write_text(growth_catalogue.read_text().replace(
            "<!-- event-ids: M1 M2 UV-M1-dup UV-M2-stale UV-M1-lost UV-M2-conflict UV-M1-spurious -->",
            "<!-- event-ids: M1 M2 UV-M1-dup UV-M2-stale UV-M1-lost UV-M2-conflict UV-M1-spurious M3-growth -->",
            1))
        expect("literal blind table grows with catalogue", False,
               *pbp(full, growth_repo))
'''
if source.count(old) != 1:
    raise SystemExit(f"BLOCKED(task-B): blind-dup anchor count is {source.count(old)}, expected 1")
path.write_text(source.replace(old, new), encoding="utf-8")
print("LITERAL GROWTH RED PROBE: INSTALLED")
PY
```

Expected:

```text
LITERAL GROWTH RED PROBE: INSTALLED
```

The only new ID is `M3-growth`, placed only in the temporary copy’s declaration
comment. Do not edit the live catalogue or add a real event.

- [x] **Step 3: Observe the literal fixture fail the growth probe**

```bash
out=$(uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py 2>&1)
rc=$?
red=$(printf '%s\n' "$out" | sed -n '/^SELFTEST: FAIL$/,$p')
expected='SELFTEST: FAIL
 - literal blind table grows with catalogue: expected OK, got rc=1
PART-B COVERAGE: FAIL
 - missing row: M3-growth (no table row keyed by it)
 - missing checklist tick: M3-growth'
printf '%s\n' "$red"
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 1 && test "$red" = "$expected"; then
  printf 'ASSERT RED AS REQUIRED\n'
else
  printf 'ASSERT FAILED\n'
  exit 1
fi
```

Expected:

```text
SELFTEST: FAIL
 - literal blind table grows with catalogue: expected OK, got rc=1
PART-B COVERAGE: FAIL
 - missing row: M3-growth (no table row keyed by it)
 - missing checklist tick: M3-growth
exit=1
ASSERT RED AS REQUIRED
```

Paste this complete displayed red-tail output into the Task-B report. This is
the required observed failure: today’s literal has neither a table row nor a
checklist tick for the declaration-only new ID. If the output differs at all,
stop with `BLOCKED(task-B)`; do not add the helper.

- [x] **Step 4: Add the declaration parser and one table builder**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("tools/selftest/run_selftest.py")
source = path.read_text(encoding="utf-8")
# Exact current text (the pbp form installed in Step 1):
old = r'''        def pbp(blind: Path, repo: Path = ROOT / "tests" / "golden-mini") -> tuple[int, str]:
            r = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "part_b_pack.py"),
                 "domain-analysis/mini",
                 "--repo", str(repo),
                 "--check", str(blind)],
                capture_output=True, text=True)
            return r.returncode, (r.stdout + r.stderr).strip()

        checklist = ("\n- [x] M1\n- [x] M2\n- [x] UV-M1-dup\n"
                     "- [x] UV-M2-stale\n- [x] UV-M1-lost\n"
                     "- [x] UV-M2-conflict\n- [x] UV-M1-spurious\n")
'''
# Exact replacement text:
new = r'''        def pbp(blind: Path, repo: Path = ROOT / "tests" / "golden-mini") -> tuple[int, str]:
            r = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "part_b_pack.py"),
                 "domain-analysis/mini",
                 "--repo", str(repo),
                 "--check", str(blind)],
                capture_output=True, text=True)
            return r.returncode, (r.stdout + r.stderr).strip()

        def catalogue_event_ids(catalogue: Path) -> list[str]:
            import re

            match = re.search(r"<!-- event-ids: (.+?) -->",
                              catalogue.read_text(encoding="utf-8"))
            if not match:
                raise ValueError("catalogue: no event-ids declaration comment")
            return match.group(1).split()

        def blind_table(ids: list[str], *, fine: bool = False,
                        omit_row=(), omit_tick=(), duplicate_tick=()) -> str:
            dispositions = {
                "M1": "handle",
                "M2": "reject",
                "UV-M1-spurious": "reject",
            }
            if fine:
                header = "| id | situation | disposition |\n|---|---|---|\n"
                rows: list[str] = []
                for ident in ids:
                    if ident in omit_row:
                        continue
                    if ident == "M1":
                        rows.extend((
                            "| **M1** | Idle | handle |",
                            "| M1 | Open (after M2, see UV-M1-dup) | reject |",
                        ))
                    else:
                        rows.append(
                            f"| {ident} | any | {dispositions.get(ident, 'ignore (documented)')} |")
            else:
                header = "| id | disposition |\n|---|---|\n"
                rows = [
                    f"| {ident} | {dispositions.get(ident, 'ignore (documented)')} |"
                    for ident in ids
                    if ident not in omit_row
                ]
            ticks = "\n".join(f"- [x] {ident}" for ident in ids
                              if ident not in omit_tick)
            extra = "".join(f"\n- [x] {ident}" for ident in duplicate_tick)
            return header + "\n".join(rows) + "\n\n" + ticks + extra + "\n"

        checklist = ("\n- [x] M1\n- [x] M2\n- [x] UV-M1-dup\n"
                     "- [x] UV-M2-stale\n- [x] UV-M1-lost\n"
                     "- [x] UV-M2-conflict\n- [x] UV-M1-spurious\n")
'''
if source.count(old) != 1:
    raise SystemExit(f"BLOCKED(task-B): helper anchor count is {source.count(old)}, expected 1")
path.write_text(source.replace(old, new), encoding="utf-8")
print("BLIND TABLE HELPERS: INSTALLED")
PY
```

Expected:

```text
BLIND TABLE HELPERS: INSTALLED
```

The parser pattern and missing-declaration message intentionally match
`part_b_pack._catalogue_ids`. The three-item mapping is not a seven-ID fixture
list: it preserves only measured exceptional dispositions while a future
identifier receives `ignore (documented)`.

- [x] **Step 5: Replace the full and fine literals with calls to the builder**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("tools/selftest/run_selftest.py")
source = path.read_text(encoding="utf-8")
# Exact current text:
old = r'''        checklist = ("\n- [x] M1\n- [x] M2\n- [x] UV-M1-dup\n"
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
'''
# Exact replacement text:
new = r'''        ids = catalogue_event_ids(
            ROOT / "tests" / "golden-mini" / "domain-analysis" / "mini"
            / "event-catalogue.md")
        full = tmp / "blind-full.md"
        full.write_text(blind_table(ids))
        expect("blind table complete", False, *pbp(full))
        # a finer-grained table (several situation rows per event id,
        # cross-references in prose cells) is MORE information — must pass
        fine = tmp / "blind-fine.md"
        fine.write_text(blind_table(ids, fine=True))
        expect("blind table finer than one row per id", False, *pbp(fine))
'''
if source.count(old) != 1:
    raise SystemExit(f"BLOCKED(task-B): full/fine literal anchor count is {source.count(old)}, expected 1")
path.write_text(source.replace(old, new), encoding="utf-8")
print("FULL AND FINE FIXTURES: DERIVED")
PY
```

Expected:

```text
FULL AND FINE FIXTURES: DERIVED
```

This preserves every current full/fine row shown in the exact old/new text;
only the seven-ID enumeration and shared checklist disappear.

- [x] **Step 6: Replace partial and duplicated-tick literals with named helper violations**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("tools/selftest/run_selftest.py")
source = path.read_text(encoding="utf-8")
# Exact current text:
old = r'''        # R-BLIND-ROW-COVERAGE: only the UV-M1-dup row is absent; its
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
'''
# Exact replacement text:
new = r'''        # R-BLIND-ROW-COVERAGE: only the UV-M1-dup row is absent; its
        # checklist tick stays present so this case fails for one reason.
        partial = tmp / "blind-partial.md"
        partial.write_text(blind_table(ids, omit_row={"UV-M1-dup"}))
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
        dup.write_text(blind_table(ids, duplicate_tick={"M2"}))
        rc_dup, out_dup = pbp(dup)
        expect("duplicated checklist tick", True, rc_dup, out_dup,
               needle="duplicated checklist entry: M2")
        dup_errors = [line for line in out_dup.splitlines() if line.startswith(" - ")]
        expected_dup_errors = [" - duplicated checklist entry: M2 (2x)"]
        if dup_errors != expected_dup_errors:
            failures.append("blind dup: expected only duplicated checklist entry: M2\n" + out_dup)
        else:
            print("  ok  blind dup fails only for duplicated checklist M2 (passes)")
'''
if source.count(old) != 1:
    raise SystemExit(f"BLOCKED(task-B): partial/dup literal anchor count is {source.count(old)}, expected 1")
path.write_text(source.replace(old, new), encoding="utf-8")
print("PARTIAL AND DUP FIXTURES: DERIVED")
PY
```

Expected:

```text
PARTIAL AND DUP FIXTURES: DERIVED
```

`omit_row` removes only the table row. Because `omit_tick` is not passed, the
`UV-M1-dup` tick is generated from the complete `ids` input and the partial
case keeps its single intended error structurally.

- [x] **Step 7: Replace the literal red probe with all four generated growth checks**

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("tools/selftest/run_selftest.py")
source = path.read_text(encoding="utf-8")
# Exact current text (installed in Step 2):
old = r'''        # R-FIXTURE-GROWTH: the present full fixture is a seven-ID literal.
        # Against a temporary catalogue with a new declaration ID it must be red.
        growth_repo = tmp / "blind-growth-repo"
        shutil.copytree(ROOT / "tests" / "golden-mini", growth_repo)
        growth_catalogue = growth_repo / "domain-analysis" / "mini" / "event-catalogue.md"
        growth_catalogue.write_text(growth_catalogue.read_text().replace(
            "<!-- event-ids: M1 M2 UV-M1-dup UV-M2-stale UV-M1-lost UV-M2-conflict UV-M1-spurious -->",
            "<!-- event-ids: M1 M2 UV-M1-dup UV-M2-stale UV-M1-lost UV-M2-conflict UV-M1-spurious M3-growth -->",
            1))
        expect("literal blind table grows with catalogue", False,
               *pbp(full, growth_repo))
'''
# Exact replacement text:
new = r'''        growth_repo = tmp / "blind-growth-repo"
        shutil.copytree(ROOT / "tests" / "golden-mini", growth_repo)
        growth_catalogue = growth_repo / "domain-analysis" / "mini" / "event-catalogue.md"
        growth_catalogue.write_text(growth_catalogue.read_text().replace(
            "<!-- event-ids: M1 M2 UV-M1-dup UV-M2-stale UV-M1-lost UV-M2-conflict UV-M1-spurious -->",
            "<!-- event-ids: M1 M2 UV-M1-dup UV-M2-stale UV-M1-lost UV-M2-conflict UV-M1-spurious M3-growth -->",
            1))
        growth_ids = catalogue_event_ids(growth_catalogue)
        growth_full = tmp / "blind-growth-full.md"
        growth_full.write_text(blind_table(growth_ids))
        expect("blind table grows with catalogue", False, *pbp(growth_full, growth_repo))
        growth_fine = tmp / "blind-growth-fine.md"
        growth_fine.write_text(blind_table(growth_ids, fine=True))
        expect("blind fine table grows with catalogue", False, *pbp(growth_fine, growth_repo))
        growth_partial = tmp / "blind-growth-partial.md"
        growth_partial.write_text(blind_table(growth_ids, omit_row={"UV-M1-dup"}))
        rc_growth_partial, out_growth_partial = pbp(growth_partial, growth_repo)
        expect("blind partial grows with catalogue", True,
               rc_growth_partial, out_growth_partial, needle="missing row: UV-M1-dup")
        growth_partial_errors = [line for line in out_growth_partial.splitlines()
                                 if line.startswith(" - ")]
        if growth_partial_errors != expected_partial_errors:
            failures.append("blind growth partial: expected only missing row: UV-M1-dup\n"
                            + out_growth_partial)
        else:
            print("  ok  blind partial grows and still fails only for UV-M1-dup (passes)")
        growth_dup = tmp / "blind-growth-dup.md"
        growth_dup.write_text(blind_table(growth_ids, duplicate_tick={"M2"}))
        rc_growth_dup, out_growth_dup = pbp(growth_dup, growth_repo)
        expect("blind dup grows with catalogue", True,
               rc_growth_dup, out_growth_dup, needle="duplicated checklist entry: M2")
        growth_dup_errors = [line for line in out_growth_dup.splitlines()
                             if line.startswith(" - ")]
        if growth_dup_errors != expected_dup_errors:
            failures.append("blind growth dup: expected only duplicated checklist entry: M2\n"
                            + out_growth_dup)
        else:
            print("  ok  blind dup grows and still fails only for M2 (passes)")
'''
if source.count(old) != 1:
    raise SystemExit(f"BLOCKED(task-B): literal-growth anchor count is {source.count(old)}, expected 1")
path.write_text(source.replace(old, new), encoding="utf-8")
print("GROWTH PROBE: DERIVED FIXTURES INSTALLED")
PY
```

Expected:

```text
GROWTH PROBE: DERIVED FIXTURES INSTALLED
```

This is the green counterpart to the observed red probe, not a new real
catalogue event. `growth_full` and `growth_fine` must pass; `growth_partial`
and `growth_dup` must include `M3-growth` while retaining exactly their one
intentional failure each.

- [x] **Step 8: Observe the complete Part-B fixture suite green**

```bash
out=$(uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py 2>&1)
rc=$?
ok=1
while IFS= read -r expected_line; do
  if ! printf '%s\n' "$out" | grep -Fx "$expected_line"; then
    ok=0
  fi
done <<'LINES'
  ok  blind table complete (passes)
  ok  blind table finer than one row per id (passes)
  ok  blind partial fails only for missing row UV-M1-dup (passes)
  ok  blind dup fails only for duplicated checklist M2 (passes)
  ok  blind table grows with catalogue (passes)
  ok  blind fine table grows with catalogue (passes)
  ok  blind partial grows with catalogue (fails as required)
  ok  blind partial grows and still fails only for UV-M1-dup (passes)
  ok  blind dup grows with catalogue (fails as required)
  ok  blind dup grows and still fails only for M2 (passes)
SELFTEST: OK
LINES
printf 'exit=%s\n' "$rc"
if test "$rc" -eq 0 && test "$ok" -eq 1; then
  printf 'ASSERT OK\n'
else
  printf '%s\nASSERT FAILED\n' "$out"
  exit 1
fi
```

Expected:

```text
  ok  blind table complete (passes)
  ok  blind table finer than one row per id (passes)
  ok  blind partial fails only for missing row UV-M1-dup (passes)
  ok  blind dup fails only for duplicated checklist M2 (passes)
  ok  blind table grows with catalogue (passes)
  ok  blind fine table grows with catalogue (passes)
  ok  blind partial grows with catalogue (fails as required)
  ok  blind partial grows and still fails only for UV-M1-dup (passes)
  ok  blind dup grows with catalogue (fails as required)
  ok  blind dup grows and still fails only for M2 (passes)
SELFTEST: OK
exit=0
ASSERT OK
```

Paste this complete displayed output. The two lines ending in `fails as
required` are expected: their following lines prove each failure contains no
second error and still grows with `M3-growth`.

- [x] **Step 9: Verify Task-B source-file scope before changing tracking boxes**

```bash
expected='tools/selftest/run_selftest.py'
actual=$(git diff --name-only | LC_ALL=C sort)
if test "$actual" = "$expected"; then
  printf '%s\n' "$actual"
  printf 'ASSERT OK: Task-B source-file scope\n'
else
  printf 'EXPECTED:\n%s\nACTUAL:\n%s\nASSERT FAILED\n' "$expected" "$actual"
  exit 1
fi
```

Expected:

```text
tools/selftest/run_selftest.py
ASSERT OK: Task-B source-file scope
```

Paste this complete output. In particular, `tools/part_b_pack.py`, the live
catalogue, and every Task-A file must be absent.

- [x] **Step 10: Run Task B’s independent full gate**

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
expect_line 'MUTANT GENERATION: OK (checked=4 drift=0 blocked=0 errors=0)' \
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
MUTANT GENERATION: OK (checked=4 drift=0 blocked=0 errors=0)
SELFTEST: OK
PACK CONSISTENCY: OK (20 artifacts, registry, version 1.51)
2/2 cases pass
Results: 6 passed, 0 failed, 6 total
Primary evidence: 3, Regression anchors: 3, Unknown: 0
REACHABILITY CHECK: OK (3/3 states reachable from 'Idle', 1 terminal)
diff-check: clean
```

Every line above is followed by `exit=0` and `ASSERT OK`. Paste the complete
gate output into the Task-B report and the commit body. A changed count or any
red gate is `BLOCKED(task-B)`.

- [x] **Step 11: Tick Task-B checkboxes in this work session and commit Task B**

Run this exact line-anchored checkbox script. It intentionally searches only
real lines that start with `- [ ] **Step`; the same text appears indented inside
this script, so a substring replacement would self-match and is forbidden.

```bash
python3 - <<'PY'
from pathlib import Path

path = Path("docs/superpowers/plans/2026-08-10-decouple-fixtures.md")
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
start = next(i for i, line in enumerate(lines) if line.startswith("### Task B"))
ticked = 0
for i in range(start, len(lines)):
    if lines[i].startswith("- [ ] **Step"):
        lines[i] = lines[i].replace("- [ ] **Step", "- [x] **Step", 1)
        ticked += 1
if ticked != 11:
    raise SystemExit(f"expected to tick 11 Task-B checkboxes, ticked {ticked}")
path.write_text("".join(lines), encoding="utf-8")
print(f"TASK B CHECKBOXES: OK ({ticked}/11 ticked before commit)")
PY

diff_out=$(git diff --check 2>&1)
diff_rc=$?
if test "$diff_rc" -eq 0 && test -z "$diff_out"; then
  printf 'ASSERT OK: final diff-check\n'
else
  printf '%s\nexit=%s\nASSERT FAILED\n' "$diff_out" "$diff_rc"
  exit 1
fi

git add tools/selftest/run_selftest.py \
  docs/superpowers/plans/2026-08-10-decouple-fixtures.md
expected_staged='docs/superpowers/plans/2026-08-10-decouple-fixtures.md
tools/selftest/run_selftest.py'
staged=$(git diff --cached --name-only | LC_ALL=C sort)
if test "$staged" = "$expected_staged"; then
  printf 'ASSERT OK: exact Task-B staged files\n'
else
  printf 'EXPECTED STAGED:\n%s\nACTUAL STAGED:\n%s\nASSERT FAILED\n' \
    "$expected_staged" "$staged"
  exit 1
fi

git commit -q -m "Derive Part-B blind fixtures from catalogue IDs" \
  -m "Replaces the four golden-mini Part-B fixture literals and their repeated
checklists with one declaration-driven table builder. The current exceptional
dispositions and M1 fine-table example are preserved; a newly declared ID gets
a normal ignore (documented) row and one checklist tick.

Evidence:
- observed red probe: temporary M3-growth declaration made the literal fixture
  fail with exactly missing row and missing checklist tick
- generated full, fine, partial, and dup fixtures all grow with M3-growth
- partial still has exactly missing row: UV-M1-dup
- dup still has exactly duplicated checklist entry: M2 (2x)
- SELFTEST: OK
- MUTANT GENERATION: OK (checked=4 drift=0 blocked=0 errors=0)
- FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)
- MUTATION CHECK: OK (killed=25 survived=0 errors=0 blocked=0)
- DSC CHECK: OK (3 states x 7 events, 21 cells, 0 guard groups)
- PACK CONSISTENCY: OK (20 artifacts, registry, version 1.51)
- run_tool_tests: 2/2 cases pass
- run_benchmark: Results: 6 passed, 0 failed, 6 total
- git diff --check: clean"

subject=$(git log -1 --format=%s)
status=$(git status --short)
staged=$(git diff --cached --name-only)
if test "$subject" = 'Derive Part-B blind fixtures from catalogue IDs' \
  && test -z "$status" \
  && test -z "$staged"; then
  printf 'ASSERT OK: Task-B commit exists and tree is clean\n'
else
  printf 'ASSERT FAILED: Task-B commit or clean-tree check\n'
  git log -1 --oneline
  git status --short
  git diff --cached --name-only
  exit 1
fi
```

Expected fixed output after Git’s suppressed commit output:

```text
TASK B CHECKBOXES: OK (11/11 ticked before commit)
ASSERT OK: final diff-check
ASSERT OK: exact Task-B staged files
ASSERT OK: Task-B commit exists and tree is clean
```

Paste the complete command output, `git log -1 --oneline`,
`git show --format=full --no-patch HEAD`, and final empty `git status --short`
into the Task-B report. This task’s deliverable is complete only after that
local commit exists.

**Task-B deliverable:** `full`, `fine`, `partial`, and `dup` are generated from
the live catalogue declaration through one helper; the `M3-growth` red probe
was observed before the helper existed and all four generated fixtures now grow
with it; the two deliberate red cases retain their exact sole errors; all
measured gates remain green.

**Do not:** change `tools/part_b_pack.py`; add a real `M3-growth` event; edit
the live event catalogue; remove/soften the two red cases, the region gate, or
the Task-A `checked=4` assertion; derive interaction pairs in this task; touch
Task-A checkboxes; regenerate JSON; release, tag, or push.
