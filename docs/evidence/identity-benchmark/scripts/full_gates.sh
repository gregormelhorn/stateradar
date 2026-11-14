#!/usr/bin/env bash
set -euo pipefail
export PATH="$PWD/.venv/bin:$PATH"
python examples/weighted-semaphore/verify_q01.py
python examples/weighted-semaphore/domain-analysis/weightedSemaphore/verify.py
python tools/gen_mutant_variants.py examples/weighted-semaphore/domain-analysis/weightedSemaphore --check
python tools/check_matrix_mutation.py examples/weighted-semaphore/domain-analysis/weightedSemaphore
python tools/check_fault_mutants.py examples/weighted-semaphore/domain-analysis/weightedSemaphore
python tools/selftest/test_mutation_binding.py
python tools/selftest/test_cell_rationale.py
python tools/selftest/test_finding_benchmark.py
mypy
python tools/check_pack_consistency.py
python tools/gen_rules.py --selftest
python tools/selftest/run_selftest.py
for suite in local_budget local_models jev_local jev_eval draft_verify draft_cells pilot_artifacts run_sol_pilot run_flash_pilot hybrid_pilot; do
    printf '%s\n' "Suite: ${suite}"
    python "tools/selftest/test_${suite}.py"
done
python tools/run_tool_tests.py
python tools/gen_analysis_sidecar.py --root tests/golden-mini
python tools/dsc_check.py tests/golden-mini/domain-analysis/mini --repo tests/golden-mini
python tools/check_reachability.py tests/golden-mini/domain-analysis/mini
git diff --check
python tools/selftest/test_pilot_accounting.py
