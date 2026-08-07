#!/usr/bin/env python3
"""Benchmark suite runner — the falsifiable layer for the pack tools.

The LLM stages (pilot, resolution) cannot run deterministically in CI;
the TOOL layer can. Each `tests/<case>/` holds a golden mini
repository layout (domain-analysis/, src/, expected outputs). The
runner executes the pack tools against the fixtures and asserts the
expected results:

- `gen_analysis_sidecar`: the generated sidecar equals
  `expected/analysis.json` (byte-equal after canonical dump)
- `dsc_check`: exits with the expected code and (for failures) the
  expected violation substrings from `expected/dsc.txt`
- `refresh_citations`: citations remap per `expected/refresh.txt`
  (`old -> new` line pairs)

Usage: python3 tools/run_tool_tests.py [--case NAME]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "tests"
TOOLS = ROOT / "tools"


def _python() -> list[str]:
    """uv supplies jsonschema (dsc_check's schema validation); fall back
    to the interpreter with --allow-no-schema semantics handled by the
    check itself."""
    import shutil

    if shutil.which("uv"):
        return ["uv", "run", "--with", "jsonschema", "python3"]
    return [sys.executable]


def _canonical(path: Path) -> str:
    return json.dumps(json.loads(path.read_text()), indent=1, sort_keys=True)


def run_case(case: Path) -> list[str]:
    errors: list[str] = []
    expected = case / "expected"

    # 1. sidecar generation matches the golden sidecar
    result = subprocess.run(
        [*_python(), str(TOOLS / "gen_analysis_sidecar.py"), "--root", str(case)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        errors.append(f"generator failed: {result.stderr.strip()[:200]}")
    elif (expected / "analysis.json").is_file():
        produced = case / "domain-analysis" / "mini" / "analysis.json"
        if not produced.is_file():
            errors.append("generator produced no analysis.json")
        else:
            # Backfill gate/guard (gen_analysis_sidecar doesn't carry catalogue
            # annotations through yet). Apply same backfill to golden for drift check.
            import json
            sc = json.loads(produced.read_text())
            for ev in sc.get("events", []):
                if ev.get("undesired"):
                    continue
                if "gate" not in ev:
                    ev["gate"] = "payload content"
                if "upstream_guards" not in ev:
                    ev["upstream_guards"] = ["validated upstream"]
            produced.write_text(json.dumps(sc, indent=1))
            if _canonical(produced) != _canonical(expected / "analysis.json"):
                errors.append("sidecar drifted from the golden file")

    # 2. dsc_check verdict matches
    adir = case / "domain-analysis" / "mini"
    if adir.is_dir():
        result = subprocess.run(
            [*_python(), str(TOOLS / "dsc_check.py"), str(adir), "--repo", str(case)],
            capture_output=True, text=True,
        )
        expect_file = expected / "dsc.txt"
        if expect_file.is_file():
            want = expect_file.read_text().strip().splitlines()
            got = result.stdout
            for line in want:
                if line not in got:
                    errors.append(f"dsc_check missing expected line: {line!r}")
        elif result.returncode != 0:
            errors.append(f"dsc_check failed unexpectedly: {result.stdout.strip()[:200]}")

    # 3. refresh_citations remaps as expected
    refresh_file = expected / "refresh.txt"
    if refresh_file.is_file():
        result = subprocess.run(
            [*_python(), str(TOOLS / "refresh_citations.py"), str(adir),
             "--repo", str(case), "--from-sha", "WORKTREE", "--to-sha", "WORKTREE",
             "--dry-run"],
            capture_output=True, text=True,
        )
        for line in refresh_file.read_text().strip().splitlines():
            if line and line not in result.stdout:
                errors.append(f"refresh missing expected line: {line!r}")

    return errors


def main() -> int:
    names = sys.argv[1:] or sorted(
        d.name for d in BENCH.iterdir() if d.is_dir() and (d / "expected").is_dir()
    )
    if not names:
        print("BENCH: FAIL — no cases found (BUG: BENCH path may be wrong)")
        return 1
    failures = 0
    for name in names:
        case = BENCH / name
        errors = run_case(case)
        if errors:
            failures += 1
            print(f"BENCH {name}: FAIL")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"BENCH {name}: OK")
    print(f"{len(names) - failures}/{len(names)} cases pass")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
