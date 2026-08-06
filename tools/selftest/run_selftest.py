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


def chk(adir: Path) -> tuple[int, str]:
    """Run check_reachability.py and return (rc, output)."""
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "check_reachability.py"), str(adir)],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def gen_sidecar(adir: Path) -> None:
    """Generate analysis.json by running gen_analysis_sidecar in the parent."""
    # adir is domain-analysis/component; --root is the parent of domain-analysis
    root = adir.parent.parent
    comp = adir.name
    subprocess.run([sys.executable, str(ROOT / "tools" / "gen_analysis_sidecar.py"),
                    "--root", str(root), "--analysis-dir", "domain-analysis", comp],
                   capture_output=True, text=True)


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
        import z3  # noqa: F401
    except ImportError as exc:
        print(f"selftest needs the dev dependencies ({exc.name}): "
              "uv run --with-requirements tools/requirements-dev.txt "
              "python3 tools/selftest/run_selftest.py", file=sys.stderr)
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

        # Red cases for the registry's selftest backlog (formats/rules.toml:
        # every rule with enforcement=checker cites its red proof here).
        print("registry-backed dsc red cases")

        def mutated(name: str, fn, needle: str) -> None:
            """Copy the flat fixture, apply fn to the sidecar dict, expect FAIL."""
            d = sidecar(tmp, FLAT)
            raw = json.loads((d / "analysis.json").read_text())
            fn(raw)
            (d / "analysis.json").write_text(json.dumps(raw))
            expect(name, True, *dsc(d), needle=needle)

        # R-DISPOSITION-VOCAB
        mutated("unknown disposition",
                lambda r: r["cells"][0].update(disposition="maybe"), "maybe")
        # R-GRID-TOTALITY
        mutated("missing grid cell",
                lambda r: r["cells"].pop(0), "expected exactly 1")
        # R-HOLE-Q
        mutated("hole without Q",
                lambda r: (r["cells"][0].update(disposition="UNSPECIFIED"),
                           r["cells"][0].pop("q", None)),
                "hole without a valid Q")
        # PA-3a
        mutated("guard outcome invalid",
                lambda r: r["guardGroups"][0].update(outcome="skipped"), "skipped")
        # PA-3b
        mutated("not-formalizable without category",
                lambda r: r["guardGroups"][0].update(
                    outcome="not-formalizable", reason="too hard"),
                "not-formalizable")
        # R-INTERACTION-PAIRS (sidecar side)
        mutated("pair without trace",
                lambda r: r["pairs"][0].pop("trace"), "trace")
        # R-DR-REVERSE
        mutated("uncited behavioural DR",
                lambda r: r["behaviouralDrs"].append("DR-777"),
                "cited by no matrix cell")
        # R-DR-FILE-EXISTS
        def _rewire_dr(r):
            for c in r["cells"]:
                if c.get("dr"):
                    c["dr"] = "DR-002"
        mutated("cited DR file missing", _rewire_dr, "does not exist")
        # R-SIDECAR-SCHEMA
        mutated("schema violation", lambda r: r.update(states="notalist"),
                "schema:")
        # PA-13a — a checklist category (here: a SHARD-added one) that
        # silently produces no entry must fail, per source
        mutated("missing checklist category",
                lambda r: r["coverage"]["src"].pop("commission"),
                "src/commission")

        print("matrix checker (markdown side)")

        def cmx(adir: Path) -> tuple[int, str]:
            r = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "check_matrix.py"), str(adir)],
                capture_output=True, text=True)
            return r.returncode, (r.stdout + r.stderr).strip()

        gm = ROOT / "tests" / "golden-mini" / "domain-analysis" / "mini"
        d5 = tmp / "cm-green"
        shutil.copytree(gm, d5)
        expect("check_matrix green on golden-mini", False, *cmx(d5))
        # PA-13a (markdown table side): an empty coverage cell must fail
        d6 = tmp / "cm-red"
        shutil.copytree(gm, d6)
        with (d6 / "event-catalogue.md").open("a", encoding="utf-8") as f:
            f.write("\n## Undesired-coverage\n\n"
                    "| source | loss | delay |\n|---|---|---|\n"
                    "| operator | UV-M1-dup |  |\n")
        expect("empty coverage cell", True, *cmx(d6), needle="empty cell")

        print("part-B row coverage")

        def pbp(blind: Path) -> tuple[int, str]:
            r = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "part_b_pack.py"),
                 "domain-analysis/mini",
                 "--repo", str(ROOT / "tests" / "golden-mini"),
                 "--check", str(blind)],
                capture_output=True, text=True)
            return r.returncode, (r.stdout + r.stderr).strip()

        full = tmp / "blind-full.md"
        full.write_text("| id | disposition |\n|---|---|\n"
                        "| M1 | handle |\n| M2 | reject |\n"
                        "| UV-M1-dup | ignore (documented) |\n")
        expect("blind table complete", False, *pbp(full))
        # R-BLIND-ROW-COVERAGE: a missing catalogue row must fail
        partial = tmp / "blind-partial.md"
        partial.write_text("| id | disposition |\n|---|---|\n"
                           "| M1 | handle |\n| M2 | reject |\n")
        expect("blind table missing row", True, *pbp(partial),
               needle="missing row: UV-M1-dup")

    print("guard proofs (z3, PA-1/PA-2)")
    sys.path.insert(0, str(ROOT / "tools"))
    import guard_proofs
    import z3

    x = z3.Int("x")
    nat = [x >= 0, x <= 10]
    ok = guard_proofs.check_group(
        "clean", [("low", x < 5), ("high", x >= 5)], assumptions=nat)
    expect("disjoint covering group", ok.outcome != "proven",
           0, "\n".join(ok.findings))
    # PA-1 red: overlapping guards must come back as a violation
    ov = guard_proofs.check_group(
        "overlap", [("a", x < 5), ("b", x < 10)], assumptions=nat)
    expect("overlapping guards (PA-1)", True,
           1 if ov.outcome == "violation" else 0,
           "\n".join(ov.findings), needle="PA-1 overlap")
    # PA-2 red: a domain gap without an else must come back as a violation
    gap = guard_proofs.check_group(
        "gap", [("a", x < 5), ("b", x > 7)], assumptions=nat)
    expect("coverage gap (PA-2)", True,
           1 if gap.outcome == "violation" else 0,
           "\n".join(gap.findings), needle="PA-2 gap")
    # has_else discharges coverage but never disjointness
    still = guard_proofs.check_group(
        "else-overlap", [("a", x < 5), ("b", x < 10)],
        assumptions=nat, has_else=True)
    expect("has_else keeps disjointness red", True,
           1 if still.outcome == "violation" else 0,
           "\n".join(still.findings), needle="PA-1 overlap")
    probes = guard_proofs.boundary_probe(
        [("low", x < 5), ("high", x >= 5)], [{x: 4}, {x: 5}, {x: 6}])
    if [labels for _, labels in probes] != [["low"], ["high"], ["high"]]:
        failures.append(f"boundary probe misassigned branches: {probes}")
    else:
        print("  ok  boundary probes assign below/at/above correctly")

    print("reachability")
    # Red: an unreachable state in the matrix must FAIL.
    # Build a minimal fixture with an unreachable 'dead' state.
    unr = tmp / "reach-red"
    adir = unr / "domain-analysis" / "gate"
    adir.mkdir(parents=True)
    (adir / "disposition-matrix.md").write_text(
        "<!-- states: idle, open, closed, dead -->\n"
        "<!-- terminal: closed -->\n"
        "| state | connect | close | tick |\n"
        "| **idle** | transition → open | ignore (documented) | ignore (documented) |\n"
        "| **open** | ignore (documented) | transition → closed | handle |\n"
        "| **closed** | ignore (documented) | ignore (documented) | handle |\n"
        "| **dead** | ignore (documented) | ignore (documented) | ignore (documented) |\n"
    )
    gen_sidecar(adir)
    expect("unreachable state must fail", True,
           *chk(adir),
           needle="unreachable")

    if failures:
        print("\nSELFTEST: FAIL")
        for f in failures:
            print(" -", f)
        return 1
    print("\nSELFTEST: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
