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

## Task B — planned separately

Task B will be added in a follow-up planning run; no Task-B implementation is authorized by this plan.
