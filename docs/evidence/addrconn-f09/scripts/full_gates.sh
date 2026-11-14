#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python tools/selftest/test_addrconn_f09.py
.venv/bin/python tools/addrconn_f09.py "$@"
bash docs/evidence/generic-canary/scripts/full_gates.sh
