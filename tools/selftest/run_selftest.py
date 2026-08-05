#!/usr/bin/env python3
"""Selftest for the pack's deterministic layer (dogfooding: red then green).

A checker that has only ever been run against passing input is a checker
nobody has tested.  Each case below states what must fail and what must
pass, so a regression in dsc_check.py or gen_analysis_sidecar.py shows up
as a failed expectation instead of a quietly green build.

Usage: python3 tools/selftest/run_selftest.py     (needs jsonschema)
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLAT = ROOT / "tools" / "selftest" / "analysis"
COMPOUND = ROOT / "tools" / "selftest" / "compound"
failures: list[str] = []


def dsc(adir: Path, *extra: str) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "dsc_check.py"), str(adir), *extra],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def expect(name: str, want_fail: bool, rc: int, out: str, needle: str = "") -> None:
    failed = rc != 0
    if failed != want_fail:
        failures.append(f"{name}: expected {'FAIL' if want_fail else 'OK'}, got rc={rc}\n{out}")
    elif needle and needle not in out:
        failures.append(f"{name}: expected message containing {needle!r}\n{out}")
    else:
        print(f"  ok  {name} ({'fails as required' if want_fail else 'passes'})")


_copies = 0


def sidecar(tmp: Path, src: Path) -> Path:
    """Copy an analysis tree into a fresh directory under tmp."""
    global _copies
    _copies += 1
    dst = tmp / f"{src.name}-{_copies}"
    shutil.copytree(src, dst)
    return dst


def main() -> int:
    try:
        import jsonschema  # noqa: F401
    except ImportError:
        print("selftest needs jsonschema: uv run --with jsonschema python3 "
              "tools/selftest/run_selftest.py", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        print("baseline")
        expect("flat fixture", False, *dsc(FLAT, "--repo", str(ROOT), "--model", "as-is.machine.mmd"))

        # The compound fixture exercises the paths CI never reached:
        # multi-table matrix, compound rows, a Mermaid container, and
        # non-Python citations.
        gen = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "gen_analysis_sidecar.py"), "--root", str(COMPOUND)],
            capture_output=True, text=True)
        if gen.returncode != 0 or "OK gate" not in gen.stdout:
            failures.append(f"generator on compound fixture:\n{gen.stdout}{gen.stderr}")
        else:
            print("  ok  generator parses multi-table matrix with compound rows")
        gate = COMPOUND / "domain-analysis" / "gate"
        expect("compound fixture", False, *dsc(gate, "--repo", str(COMPOUND), "--model", "as-is.machine.mmd"))

        data = json.loads((gate / "analysis.json").read_text())
        states = set(data["states"])
        if states != {"open idle", "open busy", "closed"}:
            failures.append(f"compound row labels not parsed: {sorted(states)}")
        cited = [c for c in data["cells"] if c.get("citation")]
        if not any(c["citation"]["file"].endswith(".ts") for c in cited):
            failures.append("non-Python citations were dropped by the generator")
        else:
            print("  ok  TypeScript citations survive the generator")

        print("silent omission (v1.20: absence must be asserted)")
        d = sidecar(tmp, FLAT)
        raw = json.loads((d / "analysis.json").read_text())
        for key in ("pairs", "guardGroups", "coverage"):
            raw.pop(key, None)
        (d / "analysis.json").write_text(json.dumps(raw))
        expect("omitted sections", True, *dsc(d), needle="does not say why")

        raw["completeness"] = {k: {"count": 0, "reason": "no guarded transitions exist here"}
                               for k in ("pairs", "guardGroups", "coverage")}
        (d / "analysis.json").write_text(json.dumps(raw))
        expect("asserted absence", False, *dsc(d))

        raw["completeness"]["pairs"] = {"count": 0, "reason": "none"}
        (d / "analysis.json").write_text(json.dumps(raw))
        expect("unreasoned absence", True, *dsc(d), needle="too short")

        print("model sync (compound states used to disable this check)")
        d2 = tmp / "sync"
        shutil.copytree(COMPOUND, d2)
        (d2 / "domain-analysis" / "gate" / "as-is.machine.mmd").write_text(
            "stateDiagram-v2\n    [*] --> open\n    state open {\n        idle --> busy : E1\n    }\n")
        expect("state missing from diagram", True,
               *dsc(d2 / "domain-analysis" / "gate", "--repo", str(d2), "--model", "as-is.machine.mmd"),
               needle="missing from diagram")

        print("citation drift")
        d3 = tmp / "drift"
        shutil.copytree(COMPOUND, d3)
        sc = d3 / "domain-analysis" / "gate" / "analysis.json"
        j = json.loads(sc.read_text())
        for cell in j["cells"]:
            if cell.get("citation"):
                cell["citation"]["fragment"] = "no such fragment in the source"
                break
        sc.write_text(json.dumps(j))
        expect("drifted fragment", True, *dsc(d3 / "domain-analysis" / "gate", "--repo", str(d3)),
               needle="not near")

        print("manifest discipline")
        d4 = sidecar(tmp, FLAT)
        (d4 / "manifest.json").write_text(json.dumps(
            {"component": "mini", "watch_paths": ["tools/selftest/src/"], "analyzedSha": "WORKTREE"}))
        expect("snake_case watchPaths", True, *dsc(d4, "--repo", str(ROOT)), needle="camelCase")

    if failures:
        print("\nSELFTEST: FAIL")
        for f in failures:
            print(" -", f)
        return 1
    print("\nSELFTEST: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
