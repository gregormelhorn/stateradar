# Final Fix Report — ACH F-04 Branch Review

**Date:** 2026-08-08
**Branch:** commits dd2da29..52d5115
**Fix Wave:** ONE wave — 4 findings fixed

## Finding I-1: handle-counter assertion missing

**Rule:** spec § "Behavioral cell suite" bullet 3 requires `handle` to assert counter increment with state unchanged.

**Red probe:**
```bash
# Copy golden-mini to temp, introduce bug: UV-M1-dup returns "handled" without incrementing dup_count
cp -r tests/golden-mini /tmp/golden-mini-probe-i1
# Edited src/mini.py: UV-M1-dup branch returns "handled" without self.dup_count += 1
python3 /tmp/golden-mini-probe-i1/tests/test_cell_suite.py /tmp/golden-mini-probe-i1/domain-analysis/mini
# OUTPUT: CELL SUITE: OK
# EXIT=0  ← SURVIVED, the bug
```

**Fix:** Capture `before_count = m.dup_count` before `m.deliver(event)`. In the handle branch, require `m.dup_count == before_count + 1`.

**Green verification:**
```bash
# Same buggy copy, now with fixed test_cell_suite.py
python3 /tmp/golden-mini-probe-i1/tests/test_cell_suite.py /tmp/golden-mini-probe-i1/domain-analysis/mini
# OUTPUT:
# MISMATCH Closed × UV-M1-dup: expected handle (counter 0→0), got handled state=Closed
# MISMATCH Idle × UV-M1-dup: expected handle (counter 0→0), got handled state=Idle
# MISMATCH Open × UV-M1-dup: expected handle (counter 0→0), got handled state=Open
# EXIT=1  ← KILLED
```

**Baseline still green:**
```bash
python3 tests/golden-mini/tests/test_cell_suite.py tests/golden-mini/domain-analysis/mini
# OUTPUT: CELL SUITE: OK
# EXIT=0
```

## Finding I-2: vacuous green on empty matrix

**Red probe:**
```bash
# Create analysis dir with header + separator, no data rows
mkdir -p /tmp/empty-matrix-probe
cat > /tmp/empty-matrix-probe/disposition-matrix.md << 'MDEOF'
| state | M1 | M2 | UV-M1-dup |
|---|---|---|
MDEOF
python3 tests/golden-mini/tests/test_cell_suite.py /tmp/empty-matrix-probe
# OUTPUT: CELL SUITE: OK
# EXIT=0  ← vacuous green
```

**Fix:** After `parse_matrix()`, if the result is empty, print "CELL SUITE: no matrix cells parsed" to stderr and return 2.

**Green verification:**
```bash
python3 tests/golden-mini/tests/test_cell_suite.py /tmp/empty-matrix-probe
# OUTPUT: CELL SUITE: no matrix cells parsed
# EXIT=2  ← correctly rejected
```

## Finding M-4: document relative-script-path coupling

**Fix:** Added one sentence to `prompts/04-testgen.md` in the fault-class hardening subsection:

> The `testCommand` must invoke the suite by relative path so the checker runs the copied script inside the temporary component copy; an absolute path would exercise the pristine implementation and every mutant would survive.

## Finding M-5: encoding

**Fix:** `tools/check_fault_mutants.py` line ~181: `target_path.write_text(…)` → `target_path.write_text(…, encoding="utf-8")`.

**Verification:** `python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini` still passes.

## Gate Results (all green)

```
$ python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
BASELINE: OK
MUT-001 KILLED fault=F-04 cell=Closed x M1 target=src/mini.py exit=1 duration=0.030s
FAULT MUTANTS: OK (killed=1 survived=0 errors=0 blocked=0)

$ python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
...
MUTATION CHECK: OK (killed=9 survived=0 errors=0 blocked=0)

$ uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
SELFTEST: OK

$ python3 tools/check_pack_consistency.py
RULES REGISTRY: OK (72 rules, 22 fault classes, 0 warnings)
ODC table: OK
PACK CONSISTENCY: OK (20 artifacts, registry, version 1.50)

$ python3 tools/run_tool_tests.py
BENCH golden-mini: OK
BENCH red-mini: OK
2/2 cases pass

$ git diff --check
EXIT=0
```

## Summary

- 3 files changed, all fixes narrow and focused
- No scope creep
- Deferred items NOT touched: ~90-line config/run_command duplication, mutant target existence validation
