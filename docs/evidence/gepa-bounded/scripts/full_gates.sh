#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python tools/selftest/test_gepa_eval.py
.venv/bin/python tools/selftest/test_gepa_budget.py
.venv/bin/python tools/selftest/test_gepa_search.py
.venv/bin/python tools/selftest/test_gepa_report.py
.venv/bin/python tools/selftest/test_gepa_rates.py
.venv/bin/python tools/verify_gepa_reference.py
.venv/bin/python tools/verify_gepa_quality.py
.venv/bin/python tools/gepa_report.py docs/evidence/gepa-bounded/runs
.venv/bin/python tools/gepa_cost_sensitivity.py docs/evidence/gepa-bounded/runs
bash docs/evidence/late-workflow/scripts/full_gates.sh "$@"
