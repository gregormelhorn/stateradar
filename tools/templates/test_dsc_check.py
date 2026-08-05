"""Pack checker gate — dsc_check for every sidecar-carrying component.

Copy this file to tests/domain/test_dsc_check.py in the consuming repo
and adjust PACK_CHECKER to your pack location (submodule, vendored
copy, or sibling checkout). One parametrized test per component keeps
failures attributable. A violation breaks the build: grid totality,
DR links, fragment citations, diagram sync, manifest staleness.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
#: Adjust to your pack checkout (Option A submodule, Option B vendored,
#: sibling-repo development checkout).
PACK_CHECKER = ROOT / "tools" / "prompt-pack" / "tools" / "dsc_check.py"

COMPONENTS = sorted(
    d.name
    for d in (ROOT / "domain-analysis").iterdir()
    if d.is_dir() and (d / "analysis.json").is_file()
)

#: Components whose diagram uses flat leaf names while the matrix rows
#: are compound (lane family + leaf). The mermaid sync check does not
#: apply there; the matrix is the authority.
NO_MODEL_SYNC: set[str] = set()


@pytest.mark.parametrize("component", COMPONENTS)
def test_dsc_check(component: str) -> None:
    """dsc_check exits 0 for the component at HEAD."""
    assert PACK_CHECKER.is_file(), f"pack checker missing: {PACK_CHECKER}"
    args = [
        sys.executable,
        str(PACK_CHECKER),
        str(ROOT / "domain-analysis" / component),
        "--repo",
        str(ROOT),
    ]
    model = ROOT / "domain-analysis" / component / "as-is.machine.mmd"
    if component not in NO_MODEL_SYNC and model.is_file():
        args += ["--model", "as-is.machine.mmd"]
    result = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
    assert result.returncode == 0, (
        f"dsc_check failed for {component}:\n{result.stdout}\n{result.stderr}"
    )
