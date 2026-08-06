"""Per-component wrapper for the pack's generic matrix checker.

The logic lives in the StateRadar pack (`tools/check_matrix.py`); this
wrapper keeps the per-component artifact contract (02-pilot step 4)
stable. PACK points at the pack root (this benchmark lives inside the
pack repo: tests/benchmarks/grpc-go-2669).

Run: python3 tests/benchmarks/grpc-go-2669/check_matrix.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parents[3] / "tools" / "check_matrix.py"
ADIR = Path(__file__).resolve().parent

if __name__ == "__main__":
    if not PACK.is_file():
        print(f"pack checker missing: {PACK}", file=sys.stderr)
        sys.exit(2)
    sys.exit(subprocess.run([sys.executable, str(PACK), str(ADIR)]).returncode)
