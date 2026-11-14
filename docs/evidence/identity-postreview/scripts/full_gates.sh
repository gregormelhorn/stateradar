#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python tools/selftest/test_finding_preservation.py
.venv/bin/python tools/selftest/test_postreview_evidence.py
bash docs/evidence/identity-benchmark/scripts/full_gates.sh
