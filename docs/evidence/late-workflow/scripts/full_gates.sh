#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python tools/selftest/test_late_workflow.py
.venv/bin/python tools/gobreaker_late_readiness.py --output-dir "${READINESS_EVIDENCE_DIR:-$(mktemp -d)}"
bash docs/evidence/late-completion/scripts/full_gates.sh "$@"
