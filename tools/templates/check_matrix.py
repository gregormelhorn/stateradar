"""Per-component wrapper for the pack's generic matrix checker.

The logic lives in the StateRadar pack
(`tools/check_matrix.py` in the pack checkout); this wrapper keeps the
per-component artifact contract (02-pilot step 4) stable. The pack is
found through the STATERADAR_PACK environment variable, else as a sibling
checkout named `stateradar` or `pack` of the analysed repository; adjust
_CANDIDATES for a submodule or vendored copy.

Run: python3 domain-analysis/<component>/check_matrix.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ADIR = Path(__file__).resolve().parent
_SIBLINGS = ADIR.parents[2]  # <repo>/domain-analysis/<component> -> parent of <repo>
_CANDIDATES = ([Path(os.environ["STATERADAR_PACK"])] if os.environ.get("STATERADAR_PACK") else []) + [
    _SIBLINGS / "stateradar", _SIBLINGS / "pack"]
PACK = next((c / "tools" / "check_matrix.py" for c in _CANDIDATES if (c / "tools" / "check_matrix.py").is_file()),
            _CANDIDATES[0] / "tools" / "check_matrix.py")

if __name__ == "__main__":
    if not PACK.is_file():
        print("pack checker missing; looked in: " + ", ".join(str(c) for c in _CANDIDATES)
              + " (set STATERADAR_PACK)", file=sys.stderr)
        sys.exit(2)
    sys.exit(subprocess.run([sys.executable, str(PACK), str(ADIR)]).returncode)
