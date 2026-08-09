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
        # Backfill gate/guard + UV coverage on generated compound sidecar
        sc = json.loads((gate / "analysis.json").read_text())
        for ev in sc.get("events", []):
            if ev.get("undesired"):
                continue
            if "gate" not in ev:
                ev["gate"] = "payload content"
            if "upstream_guards" not in ev:
                ev["upstream_guards"] = ["validated upstream"]
        if "coverage" not in sc:
            sc["coverage"] = {}
        for ev in sc.get("events", []):
            if not ev.get("undesired"):
                if ev["id"] not in sc["coverage"]:
                    sc["coverage"][ev["id"]] = {"loss": "n/a: local", "delay": "n/a: sync", "duplication": "n/a: sync", "out-of-order": "n/a: sync", "contradiction": "n/a: sync", "commission": "n/a: sync", "value": "n/a: payload validated"}
        (gate / "analysis.json").write_text(json.dumps(sc, indent=1))
        expect("compound fixture", False, *dsc(gate, "--repo", str(COMPOUND), "--model", "as-is.machine.mmd"))

        data = json.loads((gate / "analysis.json").read_text())
        states = set(data["states"])
        if states != {"Open Idle", "Open Busy", "Closed"}:
            failures.append(f"compound row labels not parsed: {sorted(states)}")
        cited = [c for c in data["cells"] if c.get("citation")]
        if not any(c["citation"]["file"].endswith(".ts") for c in cited):
            failures.append("non-Python citations were dropped by the generator")
        else:
            print("  ok  TypeScript citations survive the generator")

        print("silent omission (v1.20: absence must be asserted)")
        d = sidecar(tmp, FLAT)
        raw = json.loads((d / "analysis.json").read_text())
        for key in ("pairs", "guardGroups"):
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
            "stateDiagram-v2\n    [*] --> Open\n    state Open {\n        Idle --> Busy : E1\n    }\n")
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
        mutated("missing UV coverage entry",
                lambda r: r["coverage"]["E1"].pop("commission"),
                "UV coverage")
        # PA-22 — a declared doctrine line without a mapping must fail
        mutated("unmapped doctrine line",
                lambda r: r["docLines"].pop(0),
                "DOC-1 declared but not mapped")
        # PA-22 — a doctrine line mapped to a nonexistent cell must fail
        mutated("doctrine mapped to missing cell",
                lambda r: r["docLines"][0].update(target="Nowhere x E9"),
                "not in the grid")
        # PA-22 — a rejection without a reviewable reason must fail
        mutated("doctrine rejected without reason",
                lambda r: r["docLines"][2].update(target="no"),
                "without a reviewable reason")
        # ODC fault validation: unknown F-99 must fail
        mutated("unknown ODC fault class",
                lambda r: r["questions"][0].update(fault=["F-99"]),
                "F-99")
        # R-GATE-TYPE: missing gate on event must fail
        mutated("missing gate-type annotation",
                lambda r: r["events"][0].pop("gate", None),
                "R-GATE-TYPE")
        # R-UPSTREAM-GUARD: missing upstream_guards on event must fail
        mutated("missing upstream-guard annotation",
                lambda r: r["events"][0].pop("upstream_guards", None),
                "R-UPSTREAM-GUARD")

        # J3: UV coverage must bind at zero UV events
        d = sidecar(tmp, FLAT)
        raw = json.loads((d / "analysis.json").read_text())
        raw["events"] = [{"id": "E1", "gate": "payload", "upstream_guards": ["caller"]}, {"id": "UV1", "undesired": True}]
        raw["cells"] = [{"state": "S0", "event": "E1", "disposition": "handle"}, {"state": "S0", "event": "UV1", "disposition": "handle"}, {"state": "S1", "event": "E1", "disposition": "handle"}, {"state": "S1", "event": "UV1", "disposition": "handle"}]
        raw["questions"] = []
        raw["behaviouralDrs"] = []
        raw["docLines"] = []
        raw["pairs"] = []
        raw["guardGroups"] = []
        raw["completeness"] = {"pairs": {"count": 0, "reason": "no interaction pairs in this test fixture"}, "guardGroups": {"count": 0, "reason": "no guard groups in this test fixture"}}
        # Remove doctrine declaration from invariants-and-lints.md since we dropped docLines
        inv_path = d / "invariants-and-lints.md"
        if inv_path.is_file():
            inv_path.write_text(inv_path.read_text().replace("DOC-1 DOC-2 DOC-3", ""))
        raw.pop("coverage", None)
        (d / "analysis.json").write_text(json.dumps(raw))
        expect("UV coverage without assertions", True, *dsc(d), needle="UV coverage")
        raw["coverage"] = {"E1": {"loss": "n/a: local", "delay": "n/a: sync", "duplication": "n/a: sync", "out-of-order": "n/a: sync", "contradiction": "n/a: sync", "commission": "n/a: sync", "value": "n/a: payload validated upstream"}}
        (d / "analysis.json").write_text(json.dumps(raw))
        expect("UV coverage with assertions", False, *dsc(d))

        print("matrix checker (markdown side)")

        def cmx(adir: Path) -> tuple[int, str]:
            r = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "check_matrix.py"), str(adir)],
                capture_output=True, text=True)
            return r.returncode, (r.stdout + r.stderr).strip()

        def mutation(adir: Path) -> tuple[int, str]:
            r = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "check_matrix_mutation.py"), str(adir)],
                capture_output=True, text=True)
            return r.returncode, (r.stdout + r.stderr).strip()

        gm = ROOT / "tests" / "golden-mini" / "domain-analysis" / "mini"
        d5 = tmp / "cm-green"
        shutil.copytree(gm, d5)
        expect("check_matrix green on golden-mini", False, *cmx(d5))
        no_config = sidecar(tmp, gm)
        (no_config / "matrix-mutation.json").unlink()
        expect("mutation checker rejects missing configuration", True,
               *mutation(no_config), needle="CONFIG ERROR: missing matrix-mutation.json")

        weak = sidecar(tmp, gm)
        (weak / "matrix-mutation.json").write_text(json.dumps({
            "formatVersion": 1,
            "testCommand": ["python3", "-c", "import sys; raise SystemExit(0)", "{analysis_dir}"],
            "workingDirectory": ".",
            "timeoutSeconds": 5,
        }))
        expect("mutation checker reports weak suite survivors", True,
               *mutation(weak), needle="SURVIVED")

        expect("mutation checker golden-mini kills supported mutants", False,
               *mutation(gm), needle="MUTATION CHECK: OK")

        no_placeholder = sidecar(tmp, gm)
        (no_placeholder / "matrix-mutation.json").write_text(json.dumps({
            "formatVersion": 1,
            "testCommand": ["python3", "-c", "pass"],
        }))
        expect("mutation checker rejects missing placeholder", True,
               *mutation(no_placeholder), needle="CONFIG ERROR: testCommand must contain exactly one {analysis_dir}")

        repeated_placeholder = sidecar(tmp, gm)
        (repeated_placeholder / "matrix-mutation.json").write_text(json.dumps({
            "formatVersion": 1,
            "testCommand": ["python3", "{analysis_dir}", "{analysis_dir}"],
        }))
        expect("mutation checker rejects repeated placeholder", True,
               *mutation(repeated_placeholder), needle="CONFIG ERROR: testCommand must contain exactly one {analysis_dir}")

        non_array_command = sidecar(tmp, gm)
        (non_array_command / "matrix-mutation.json").write_text(json.dumps({
            "formatVersion": 1,
            "testCommand": "python3 tests/test_cell_suite.py {analysis_dir}",
        }))
        expect("mutation checker rejects non-array command", True,
               *mutation(non_array_command), needle="CONFIG ERROR: testCommand must be a non-empty array of strings")

        baseline_failure = sidecar(tmp, gm)
        (baseline_failure / "matrix-mutation.json").write_text(json.dumps({
            "formatVersion": 1,
            "testCommand": ["python3", "-c", "raise SystemExit(3)", "{analysis_dir}"],
            "workingDirectory": ".",
        }))
        expect("mutation checker blocks failed baseline", True,
               *mutation(baseline_failure), needle="BLOCKED: baseline exit=3")

        baseline_timeout = sidecar(tmp, gm)
        (baseline_timeout / "matrix-mutation.json").write_text(json.dumps({
            "formatVersion": 1,
            "testCommand": ["python3", "-c", "import time; time.sleep(2)", "{analysis_dir}"],
            "workingDirectory": ".",
            "timeoutSeconds": 1,
        }))
        expect("mutation checker blocks timed-out baseline", True,
               *mutation(baseline_timeout), needle="BLOCKED: baseline timeout=1s")

        print("fault mutant checker")

        def fault_check(adir: Path) -> tuple[int, str]:
            r = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "check_fault_mutants.py"), str(adir)],
                capture_output=True, text=True)
            return r.returncode, (r.stdout + r.stderr).strip()

        def component(tmp: Path, name: str) -> Path:
            dst = tmp / name
            shutil.copytree(ROOT / "tests" / "golden-mini", dst)
            return dst

        fdir = ROOT / "tests" / "golden-mini" / "domain-analysis" / "mini"
        rc, out = fault_check(fdir)
        expect("fault mutant baseline kills all four fixture mutants", False,
               rc, out, needle="FAULT MUTANTS: OK")
        if "killed=4" not in out:
            failures.append("fault mutant count: expected killed=4\n" + out)
        else:
            print("  ok  fault mutant count killed=4 (passes)")
        if "KILLED" not in out:
            failures.append("fault mutant kill proof: no KILLED line\n" + out)
        else:
            print("  ok  fault mutant kill proof (passes)")

        import difflib
        base = (ROOT / "tests" / "golden-mini" / "src" / "mini.py").read_text().splitlines()
        for variant_name in [
            "mini.F-01-missing-transition.py",
            "mini.F-02-transfer-fault.py",
            "mini.F-04-sneak-path.py",
            "mini.F-05-corrupt-state.py",
        ]:
            variant = (ROOT / "tests" / "golden-mini" / "src" / "mutants" / variant_name).read_text().splitlines()
            hunks = [l for l in difflib.unified_diff(base, variant, lineterm="")
                     if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
            if len(hunks) == 0 or len(hunks) > 8:
                failures.append(f"{variant_name}: expected a small single-region diff, got {len(hunks)} changed lines")
            else:
                print(f"  ok  {variant_name} single-region diff (passes)")

        mirror = component(tmp, "mirror-suite")
        cfg = json.loads((mirror / "domain-analysis" / "mini" / "fault-mutants.json").read_text())
        cfg["testCommand"] = ["python3", "-c", "import sys; sys.exit(0)", "{analysis_dir}"]
        (mirror / "domain-analysis" / "mini" / "fault-mutants.json").write_text(json.dumps(cfg))
        expect("mirroring suite survives F-04 mutant (F-21 blind spot)", True,
               *fault_check(mirror / "domain-analysis" / "mini"), needle="SURVIVED")

        no_fm = component(tmp, "fault-no-config")
        (no_fm / "domain-analysis" / "mini" / "fault-mutants.json").unlink()
        expect("fault mutant rejects missing config", True,
               *fault_check(no_fm / "domain-analysis" / "mini"),
               needle="CONFIG ERROR: missing fault-mutants.json")

        bad_ver = component(tmp, "fault-bad-version")
        cfg = json.loads((bad_ver / "domain-analysis" / "mini" / "fault-mutants.json").read_text())
        cfg["formatVersion"] = 2
        (bad_ver / "domain-analysis" / "mini" / "fault-mutants.json").write_text(json.dumps(cfg))
        expect("fault mutant rejects formatVersion 2", True,
               *fault_check(bad_ver / "domain-analysis" / "mini"),
               needle="CONFIG ERROR: formatVersion must be integer 1")

        no_variant = component(tmp, "fault-no-variant")
        (no_variant / "src" / "mutants" / "mini.F-04-sneak-path.py").unlink()
        expect("fault mutant rejects missing variant file", True,
               *fault_check(no_variant / "domain-analysis" / "mini"),
               needle="missing variant file")

        no_ph = component(tmp, "fault-no-placeholder")
        cfg = json.loads((no_ph / "domain-analysis" / "mini" / "fault-mutants.json").read_text())
        cfg["testCommand"] = ["python3", "tests/test_cell_suite.py"]
        (no_ph / "domain-analysis" / "mini" / "fault-mutants.json").write_text(json.dumps(cfg))
        expect("fault mutant rejects missing placeholder", True,
               *fault_check(no_ph / "domain-analysis" / "mini"),
               needle="exactly one {analysis_dir}")

        blocked = component(tmp, "fault-blocked")
        cfg = json.loads((blocked / "domain-analysis" / "mini" / "fault-mutants.json").read_text())
        cfg["testCommand"] = ["python3", "-c", "raise SystemExit(3)", "{analysis_dir}"]
        (blocked / "domain-analysis" / "mini" / "fault-mutants.json").write_text(json.dumps(cfg))
        expect("fault mutant blocks failed baseline", True,
               *fault_check(blocked / "domain-analysis" / "mini"),
               needle="BLOCKED: baseline exit=3")

        # PA-13a (markdown table side): an empty coverage cell must fail
        d6 = tmp / "cm-red"
        shutil.copytree(gm, d6)
        with (d6 / "event-catalogue.md").open("a", encoding="utf-8") as f:
            f.write("\n## Undesired-coverage\n\n"
                    "| source | loss | delay |\n|---|---|---|\n"
                    "| operator | UV-M1-dup |  |\n")
        expect("empty coverage cell", True, *cmx(d6), needle="empty cell")
        # PA-17: a lowercase / flag-like state name must fail
        d7 = tmp / "cm-pa17"
        shutil.copytree(gm, d7)
        mx = d7 / "disposition-matrix.md"
        mx.write_text(mx.read_text().replace(
            "<!-- states: Idle Open Closed -->",
            "<!-- states: Idle open_pending Closed -->"))
        expect("PA-17 naming violation", True, *cmx(d7), needle="PA-17")
        # PA-10: a matrix without an abstraction statement must fail
        d8 = tmp / "cm-pa10"
        shutil.copytree(gm, d8)
        mx = d8 / "disposition-matrix.md"
        mx.write_text("\n".join(ln for ln in mx.read_text().splitlines()
                                if not ln.startswith("Abstraction")) + "\n")
        expect("missing abstraction statement (PA-10)", True, *cmx(d8),
               needle="PA-10")
        # PA-4: an event with neither classification nor classified base
        d9 = tmp / "cm-pa4"
        shutil.copytree(gm, d9)
        ec = d9 / "event-catalogue.md"
        ec.write_text(ec.read_text().replace(
            "| UV-M1-dup | duplicate open | operator | external | id | op | svc |",
            "| UV-M1-dup | duplicate open | operator |  | id | op | svc |"))
        expect("unclassified event (PA-4)", True, *cmx(d9), needle="PA-4")
        # requirement-scope rule: a control trace citing a requirement
        # without the scope line must fail
        d10 = tmp / "cm-scope"
        shutil.copytree(gm, d10)
        (d10 / "adversarial-traces.md").write_text(
            "# Traces\n\n**T-01** duplicate open in Open.\n"
            "(a) M1; UV-M1-dup.\n(b) counted, no transition.\n"
            "(c) none — control trace. Cites DOC-1.\n")
        expect("citing control trace without scope line", True, *cmx(d10),
               needle="scope line")
        # and WITH the scope line it passes
        d11 = tmp / "cm-scope-ok"
        shutil.copytree(gm, d11)
        (d11 / "adversarial-traces.md").write_text(
            "# Traces\n\n**T-01** duplicate open in Open.\n"
            "(a) M1; UV-M1-dup.\n(b) counted, no transition.\n"
            "(c) none — control trace. Cites DOC-1. Cited text contemplates\n"
            "this ordering: yes.\n")
        expect("scope line satisfied (wrapped across lines)", False, *cmx(d11))

        print("part-B row coverage")

        def pbp(blind: Path) -> tuple[int, str]:
            r = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "part_b_pack.py"),
                 "domain-analysis/mini",
                 "--repo", str(ROOT / "tests" / "golden-mini"),
                 "--check", str(blind)],
                capture_output=True, text=True)
            return r.returncode, (r.stdout + r.stderr).strip()

        checklist = "\n- [x] M1\n- [x] M2\n- [x] UV-M1-dup\n"
        full = tmp / "blind-full.md"
        full.write_text("| id | disposition |\n|---|---|\n"
                        "| M1 | handle |\n| M2 | reject |\n"
                        "| UV-M1-dup | ignore (documented) |\n" + checklist)
        expect("blind table complete", False, *pbp(full))
        # a finer-grained table (several situation rows per event id,
        # cross-references in prose cells) is MORE information — must pass
        fine = tmp / "blind-fine.md"
        fine.write_text("| id | situation | disposition |\n|---|---|---|\n"
                        "| **M1** | Idle | handle |\n"
                        "| M1 | Open (after M2, see UV-M1-dup) | reject |\n"
                        "| M2 | any | reject |\n"
                        "| UV-M1-dup | any | ignore (documented) |\n" + checklist)
        expect("blind table finer than one row per id", False, *pbp(fine))
        # R-BLIND-ROW-COVERAGE: a missing catalogue row must fail
        partial = tmp / "blind-partial.md"
        partial.write_text("| id | disposition |\n|---|---|\n"
                           "| M1 | handle |\n| M2 | reject |\n"
                           "\n- [x] M1\n- [x] M2\n")
        expect("blind table missing row", True, *pbp(partial),
               needle="missing row: UV-M1-dup")
        # a duplicated checklist tick must fail — coverage must be countable
        dup = tmp / "blind-dup.md"
        dup.write_text("| id | disposition |\n|---|---|\n"
                       "| M1 | handle |\n| M2 | reject |\n"
                       "| UV-M1-dup | ignore (documented) |\n"
                       + checklist + "- [x] M2\n")
        expect("duplicated checklist tick", True, *pbp(dup),
               needle="duplicated checklist entry: M2")

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
        "<!-- states: Idle, Open, Closed, Dead -->\n"
        "<!-- terminal: Closed -->\n"
        "| state | connect | close | tick |\n"
        "| **Idle** | transition → Open | ignore (documented) | ignore (documented) |\n"
        "| **Open** | ignore (documented) | transition → Closed | handle |\n"
        "| **Closed** | ignore (documented) | ignore (documented) | handle |\n"
        "| **Dead** | ignore (documented) | ignore (documented) | ignore (documented) |\n"
    )
    gen_sidecar(adir)
    expect("unreachable state must fail", True,
           *chk(adir),
           needle="unreachable")

    print("ensemble convergence")

    def ens(*args: Path | str) -> tuple[int, str]:
        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "ensemble_convergence.py"),
             *(str(a) for a in args)],
            capture_output=True, text=True)
        return r.returncode, (r.stdout + r.stderr).strip()

    ENS = ROOT / "tools" / "selftest" / "ensemble"
    # Green: identical sidecars must converge 100%
    expect("ensemble convergent (identical)", False,
           *ens(ENS / "run1.json", ENS / "run1.json"),
           needle="100.0%")
    # Red: divergent sidecars must fail and report divergence
    expect("ensemble divergent (2 runs)", True,
           *ens(ENS / "run1.json", ENS / "run2.json"),
           needle="divergent")
    # Red: three-way divergence must also fail
    expect("ensemble divergent (3 runs)", True,
           *ens(ENS / "run1.json", ENS / "run2.json", ENS / "run3.json"),
           needle="divergent")
    # Baseline acceptance: actual device-connection CONVERGENCE sidecars
    DC = ROOT / "tests" / "device-connection"
    rc, out = ens(DC / "run1" / "analysis.json", DC / "run2" / "analysis.json")
    expect("ensemble baseline: exit 1 + needle", True, rc, out, needle="93.8%")
    if "Total aligned cells | 32" not in out:
        failures.append(
            f"ensemble baseline: expected 32 aligned cells, got:\n{out[:2000]}")
    if "Structural findings" not in out:
        failures.append("ensemble baseline: no structural findings count")
    else:
        print("  ok  ensemble baseline: aligned grid 4×8 @ 93.8%")
    # T3a: deterministic reports — run twice with identical inputs, byte-identical output
    import hashlib
    r1_out = ens(ENS / "run1.json", ENS / "run2.json")[1]
    r2_out = ens(ENS / "run1.json", ENS / "run2.json")[1]
    if r1_out != r2_out:
        failures.append("ensemble: deterministic output failed — two runs differ")
    else:
        print("  ok  ensemble deterministic output (byte-identical on repeat)")
    # R1: input-order invariance — shuffle one input, reports must be identical
    import random
    d = json.loads((ENS / "run1.json").read_text())
    rng = random.Random(42)
    rng.shuffle(d["states"])
    rng.shuffle(d["events"])
    rng.shuffle(d["cells"])
    shuffled_path = tmp / "ensemble-shuffled.json"
    shuffled_path.write_text(json.dumps(d))
    # Both invocations with --labels to normalize run path labels
    r1_shuf = ens(ENS / "run1.json", ENS / "run2.json",
                  "--labels", "run-a", "run-b")[1]
    r2_shuf = ens(shuffled_path, ENS / "run2.json",
                  "--labels", "run-a", "run-b")[1]
    if r1_shuf != r2_shuf:
        failures.append("ensemble: input-order invariance failed — shuffled differs")
    else:
        print("  ok  ensemble input-order invariance (shuffled states/events/cells)")
    # T3b: zero-denominator — no aligned states
    rc_z, out_z = ens(ENS / "zero1.json", ENS / "zero2.json")
    expect("ensemble zero-alignment", True, rc_z, out_z, needle="n/a (no aligned cells)")
    if "100.0%" in out_z:
        failures.append("ensemble zero-alignment: must not report 100.0% with no cells")
    # T3c: intra-run collision — two states normalize identically in same run
    rc_c, out_c = ens(ENS / "collision.json", ENS / "collision.json")
    if rc_c != 2:
        failures.append(f"ensemble collision guard: expected exit 2, got {rc_c}\n{out_c[:500]}")
    elif "Disconnected" not in out_c or "DISCONNECTED" not in out_c:
        failures.append("ensemble collision guard: must name both originals")
    expect("ensemble collision guard", True, rc_c, out_c, needle="intra-run collision")

    # Baseline acceptance: device-connection CONVERGENCE sidecars
    DEV = ROOT / "tests" / "device-connection"
    rc, out = ens(DEV / "run1" / "analysis.json", DEV / "run2" / "analysis.json")
    # Must exit 1 (has divergence)
    if rc != 1:
        failures.append(f"baseline acceptance: expected exit 1, got {rc}")
    # Must report structural findings >= 3
    if "Structural findings" not in out or "3" not in out:
        failures.append("baseline acceptance: structural findings missing or < 3")
    else:
        print("  ok  ensemble baseline: exit 1 + structural >= 3")
    # Aligned cell count must be 32 (4 states x 8 events)
    if "Total aligned cells | 32" not in out:
        failures.append(f"baseline acceptance: expected 32 aligned cells")
    else:
        print("  ok  ensemble baseline: aligned cells = 32")

    print("benchmark dating protocol")
    import benchmark_evidence

    # Primary: issue after model release
    assert benchmark_evidence.classify({
        "issue_published": "2026-07-13",
        "model": "claude-sonnet-4-20250514",
        "model_release": "2025-05-14",
        "model_cutoff": "2025-01-01",
    }) == "primary", "post-release issue must be primary"
    # Regression: issue before model release
    assert benchmark_evidence.classify({
        "issue_published": "2024-10-22",
        "model": "claude-sonnet-4-20250514",
        "model_release": "2025-05-14",
        "model_cutoff": "2025-01-01",
    }) == "regression", "pre-release issue must be regression"
    # Red: issue published before model release must NOT be primary
    assert benchmark_evidence.classify({
        "issue_published": "2024-10-22",
        "model": "claude-sonnet-4-20250514",
        "model_release": "2025-05-22",
        "model_cutoff": "2025-03-01",
    }) == "regression", "pre-release issue must be regression, not primary"
    # Unknown: missing fields
    assert benchmark_evidence.classify(None) == "unknown", "missing dating is unknown"
    assert benchmark_evidence.classify({}) == "unknown", "empty dating is unknown"
    # Red: issue published but no model release → unknown (not primary)
    assert benchmark_evidence.classify({
        "issue_published": "2026-07-13",
        "model": "claude-sonnet-4-20250514",
    }) == "unknown", "missing model_release is unknown"
    print("  ok  benchmark dating classification correct")

    if failures:
        print("\nSELFTEST: FAIL")
        for f in failures:
            print(" -", f)
        return 1
    print("\nSELFTEST: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
