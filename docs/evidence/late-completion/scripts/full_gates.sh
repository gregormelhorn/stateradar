#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python tools/selftest/test_late_completion.py
.venv/bin/python tools/selftest/test_late_adapter.py
late_evidence_dir="${LATE_EVIDENCE_DIR:-$(mktemp -d)}"
.venv/bin/python tools/addrconn_late.py "$@" --output-dir "$late_evidence_dir"
.venv/bin/python docs/evidence/late-completion/scripts/audit_repeats.py "$late_evidence_dir"
bash docs/evidence/addrconn-f09/scripts/full_gates.sh "$@"
