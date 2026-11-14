#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python tools/selftest/test_semaphore_f09.py
.venv/bin/python tools/semaphore_f09.py
bash docs/evidence/identity-postreview/scripts/full_gates.sh
