#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python tools/selftest/test_fault_runner.py
.venv/bin/python docs/evidence/generic-canary/scripts/semaphore_weak_control.py
bash docs/evidence/semaphore-f09/scripts/full_gates.sh
