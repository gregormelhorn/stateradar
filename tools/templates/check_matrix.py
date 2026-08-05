"""Per-component wrapper for the pack's generic matrix checker.

The logic lives in the domain-statechart pack
(`tools/check_matrix.py` in the pack checkout); this wrapper keeps the
per-component artifact contract (02-pilot step 4) stable. Adjust PACK
to your pack location (submodule, vendored copy, or sibling checkout).

Run: python3 domain-analysis/<component>/check_matrix.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parents[3] / "domain-statechart" / "tools" / "check_matrix.py"
ADIR = Path(__file__).resolve().parent

if __name__ == "__main__":
    if not PACK.is_file():
        print(f"pack checker missing: {PACK}", file=sys.stderr)
        sys.exit(2)
    sys.exit(subprocess.run([sys.executable, str(PACK), str(ADIR)]).returncode)
