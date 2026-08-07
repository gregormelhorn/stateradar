#!/usr/bin/env python3
"""Rules-registry generator and checker (single source: formats/rules.toml).

The registry owns rule identity, classification, the closed vocabularies,
and the fault-class catalogue. This tool renders them into marked blocks

    <!-- generated:rules key=<name> -->
    ...rendered content...
    <!-- /generated:rules -->

inside prompts/00-methods-reference.md, prompts/02-pilot.md, AGENTS.md
and README.md, and verifies the registry's own constraints:

  C1  enforcement=checker  => checker_ref AND selftest_ref present;
      selftest_ref "TODO" is a warned-about backlog entry, never a pass
  C2  enforcement=lint     => rendered into the Step-5 block (step5_order)
      or anchored in prose (lint_ref)
  C3  class=fault-model    => at least one `detects` entry
  C4  every fault class without a detecting rule => warning (the ODC gap
      signal: a fault class nobody looks for)
  C5  marker keys in the target files and renderable keys must match 1:1

Usage:
  python3 tools/gen_rules.py --check      verify blocks + constraints (CI)
  python3 tools/gen_rules.py --write      re-render all generated blocks
  python3 tools/gen_rules.py --selftest   red-then-green self-verification

Stdlib only (tomllib, Python >= 3.11). Exit 0 = OK, 1 = violations.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
import textwrap
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = "formats/rules.toml"
TARGETS = [
    "prompts/00-methods-reference.md",
    "prompts/02-pilot.md",
    "AGENTS.md",
    "README.md",
]

MARKER = re.compile(
    r"<!-- generated:rules key=([a-z0-9-]+) -->\n(.*?)\n<!-- /generated:rules -->",
    re.S,
)

CLASSES = {"wellformedness", "completeness", "fault-model", "process",
           "empirical-pattern"}
ENFORCEMENTS = {"checker", "test", "lint", "prompt", "human", "data"}


def load(root: Path) -> dict:
    return tomllib.loads((root / REGISTRY).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- rendering

def _pa_sort_key(rule_id: str) -> tuple[int, str]:
    m = re.fullmatch(r"PA-(\d+)([a-z]?)", rule_id)
    return (int(m.group(1)), m.group(2)) if m else (999, rule_id)


def render_pa_condensed(reg: dict) -> str:
    lines = []
    rules = [r for r in reg["rules"] if r["id"].startswith("PA-")]
    for r in sorted(rules, key=lambda r: _pa_sort_key(r["id"])):
        body = textwrap.wrap(r["statement"], width=71,
                             break_on_hyphens=False, break_long_words=False)
        lines.append(f"{r['id']:<7}{body[0]}")
        lines.extend(f"{'':<7}{cont}" for cont in body[1:])
    return "```text\n" + "\n".join(lines) + "\n```"


def render_disposition_vocab(reg: dict) -> str:
    holes = set(reg["vocab"]["holes"])
    vals = [v + ("*" if v in holes else "") for v in reg["vocab"]["dispositions"]]
    body = textwrap.fill(" | ".join(vals), width=76)
    return "```text\n" + body + "\n```"


def render_partb_vocab(reg: dict) -> str:
    defs = reg["vocab"].get("disposition_defs", {})
    parts = []
    for v in reg["vocab"]["dispositions"]:
        base = f"`{v}`"
        if v in defs:
            base += f" ({defs[v]})"
        parts.append(base)
    return ("> The disposition vocabulary you must use (from the methods "
            "reference): " + " | ".join(parts) + ". "
            + reg["render"]["partb_vocab_tail"])


def render_uv_categories(reg: dict) -> str:
    return "\n".join(
        f"* {c['label']} ({c['fault']}, sidecar key: `{c['key']}`)"
        for c in reg["uv_categories"])


def render_checker_catalogue(reg: dict) -> str:
    rules = [r for r in reg["rules"] if "catches" in r]
    rules.sort(key=lambda r: r["catches_order"])
    return "\n".join(f"* {r['catches']}" for r in rules)


def render_step5_lints(reg: dict) -> str:
    rules = [r for r in reg["rules"] if "step5_order" in r]
    rules.sort(key=lambda r: r["step5_order"])
    # renders join with single newlines; a unit that needs blank-line
    # separation (a paragraph between bullet runs) carries the extra
    # leading/trailing newline in its own render text
    return "\n".join(r["render"] for r in rules)


def render_readme_finds(reg: dict) -> str:
    finds = reg["readme_finds"]
    out = []
    for i, f in enumerate(finds):
        tail = "." if i == len(finds) - 1 else ";"
        out.append(f"* {f['text']}{tail}")
    return "\n".join(out)


def render_all(reg: dict) -> dict[str, str]:
    return {
        "pa-condensed": render_pa_condensed(reg),
        "disposition-vocab": render_disposition_vocab(reg),
        "partb-vocab": render_partb_vocab(reg),
        "uv-categories": render_uv_categories(reg),
        "checker-catalogue": render_checker_catalogue(reg),
        "step5-lints": render_step5_lints(reg),
        "readme-finds": render_readme_finds(reg),
    }


# -------------------------------------------------------------- constraints

def constraints(reg: dict, root: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    fault_ids = [f["id"] for f in reg.get("faults", [])]
    if len(fault_ids) != len(set(fault_ids)):
        errors.append("duplicate fault ids")
    rule_ids = [r["id"] for r in reg["rules"]]
    if len(rule_ids) != len(set(rule_ids)):
        dupes = {i for i in rule_ids if rule_ids.count(i) > 1}
        errors.append(f"duplicate rule ids: {sorted(dupes)}")

    detected: set[str] = set()
    for r in reg["rules"]:
        rid = r["id"]
        if r.get("class") not in CLASSES:
            errors.append(f"{rid}: unknown class {r.get('class')!r}")
        if r.get("enforcement") not in ENFORCEMENTS:
            errors.append(f"{rid}: unknown enforcement {r.get('enforcement')!r}")
        if r.get("enforcement") == "checker":
            if not r.get("checker_ref"):
                errors.append(f"{rid}: enforcement=checker without checker_ref")
            st = r.get("selftest_ref")
            if not st:
                errors.append(f"{rid}: enforcement=checker without selftest_ref "
                              "(write TODO to acknowledge the backlog)")
            elif st == "TODO":
                warnings.append(f"selftest backlog: {rid} "
                                f"({r.get('checker_ref', '?')})")
            else:
                tok = st.split()[0]
                if "/" in tok and not (ROOT / tok).exists():
                    errors.append(f"{rid}: selftest_ref path missing: {tok}")
        if r.get("enforcement") == "lint" and "step5_order" not in r \
                and not r.get("lint_ref"):
            errors.append(f"{rid}: enforcement=lint but neither step5_order "
                          "nor lint_ref")
        if r.get("class") == "fault-model" and not r.get("detects"):
            errors.append(f"{rid}: class=fault-model without detects")
        for f in r.get("detects", []):
            if f not in fault_ids:
                errors.append(f"{rid}: detects unknown fault {f}")
            detected.add(f)
        if r.get("checker_candidate"):
            warnings.append(f"checker candidate (backlog): {rid} — {r['title']}")

    for f in reg.get("faults", []):
        if f["id"] not in detected:
            warnings.append(f"fault class without detector: "
                            f"{f['id']} ({f['name']})")
    for uc in reg.get("uv_categories", []):
        if uc["fault"] not in fault_ids:
            errors.append(f"uv category {uc['label']!r}: unknown fault "
                          f"{uc['fault']}")
    for rf in reg.get("readme_finds", []):
        if rf["fault"] not in fault_ids:
            errors.append(f"readme find {rf['text'][:40]!r}: unknown fault "
                          f"{rf['fault']}")

    # C-n: every checker-shaped tool must be cited by at least one rule
    _checker_tools = [
        "tools/check_matrix.py",
        "tools/check_reachability.py",
        "tools/guard_proofs.py",
        "tools/ensemble_convergence.py",
        "tools/benchmark_evidence.py",
        "tools/dsc_check.py",
    ]
    all_checker_refs = " ".join(
        r.get("checker_ref", "") for r in reg.get("rules", [])
    )
    for tool in _checker_tools:
        if tool not in all_checker_refs:
            warnings.append(f"checker-shaped tool not cited by any rule: {tool}")

    # RR5: rules with no render target (no catches, render, lint_ref, prose_ref)
    # become dark-prose warnings — their normative prose has no anchor.
    for r in reg.get("rules", []):
        has_target = any(
            r.get(k) for k in ["catches", "render", "lint_ref", "prose_ref"]
        )
        if not has_target and r.get("enforcement") != "checker":
            warnings.append(f"dark rule (no prose anchor): {r['id']} — {r['title']}")
        # Verify prose_ref file exists (section existence is best-effort)
        pref = r.get("prose_ref", "")
        if pref and "#" in pref:
            fname = pref.split("#", 1)[0]
            target_path = root / fname
            if not target_path.is_file():
                errors.append(f"{r['id']}: prose_ref file not found: {fname}")

    return errors, warnings


# ------------------------------------------------------------- check/write

def check(root: Path) -> tuple[list[str], list[str]]:
    reg = load(root)
    errors, warnings = constraints(reg, root)
    blocks = render_all(reg)
    used: set[str] = set()
    for rel in TARGETS:
        text = (root / rel).read_text(encoding="utf-8")
        for m in MARKER.finditer(text):
            key, content = m.group(1), m.group(2)
            if key not in blocks:
                errors.append(f"{rel}: unknown generated block key={key}")
                continue
            used.add(key)
            if content != blocks[key]:
                errors.append(
                    f"{rel}: block key={key} drifted from the registry — "
                    "edit formats/rules.toml, then run "
                    "`python3 tools/gen_rules.py --write`")
    for key in sorted(set(blocks) - used):
        errors.append(f"generated block key={key} not used in any target file")
    # every disposition value must still appear in 00 and 02 (the old
    # VOCAB x2 guarantee, now sourced from the registry)
    for rel in ("prompts/00-methods-reference.md", "prompts/02-pilot.md"):
        text = (root / rel).read_text(encoding="utf-8")
        for v in reg["vocab"]["dispositions"]:
            plain = v.replace(" → <target>", "")
            if plain not in text:
                errors.append(f"{rel}: disposition value {plain!r} missing")
    return errors, warnings


def write(root: Path) -> int:
    reg = load(root)
    blocks = render_all(reg)
    changed = 0
    for rel in TARGETS:
        p = root / rel
        text = p.read_text(encoding="utf-8")

        def sub(m: re.Match) -> str:
            key = m.group(1)
            if key not in blocks:
                raise SystemExit(f"{rel}: unknown generated block key={key}")
            return (f"<!-- generated:rules key={key} -->\n"
                    f"{blocks[key]}\n<!-- /generated:rules -->")

        new = MARKER.sub(sub, text)
        if new != text:
            p.write_text(new, encoding="utf-8")
            changed += 1
            print(f"  rewrote {rel}")
    print(f"gen_rules: {changed} file(s) updated")
    return 0


# ---------------------------------------------------------------- selftest

def selftest() -> int:
    failures: list[str] = []

    def expect(name: str, want_fail: bool, errors: list[str], needle: str = ""):
        failed = bool(errors)
        if failed != want_fail:
            failures.append(f"{name}: expected {'FAIL' if want_fail else 'OK'},"
                            f" got {errors[:3]}")
        elif needle and not any(needle in e for e in errors):
            failures.append(f"{name}: expected message containing {needle!r}: "
                            f"{errors[:3]}")
        else:
            print(f"  ok  {name} ({'fails as required' if want_fail else 'passes'})")

    reg = load(ROOT)

    # red 1: checker rule without selftest_ref must fail constraints
    import copy
    broken = copy.deepcopy(reg)
    victim = next(r for r in broken["rules"]
                  if r.get("enforcement") == "checker" and r.get("selftest_ref"))
    del victim["selftest_ref"]
    e, _ = constraints(broken, ROOT)
    expect("checker without selftest_ref", True, e, "selftest_ref")

    # red 2: detects pointing at an unknown fault must fail
    broken = copy.deepcopy(reg)
    broken["rules"][0]["detects"] = ["F-99"]
    e, _ = constraints(broken, ROOT)
    expect("unknown fault id in detects", True, e, "F-99")

    # red 3: fault-model rule without detects must fail
    broken = copy.deepcopy(reg)
    victim = next(r for r in broken["rules"] if r.get("class") == "fault-model")
    victim.pop("detects", None)
    e, _ = constraints(broken, ROOT)
    expect("fault-model without detects", True, e, "without detects")

    # red 4: a drifted generated block must fail --check
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "formats").mkdir()
        (tmp / "prompts").mkdir()
        shutil.copy(ROOT / REGISTRY, tmp / REGISTRY)
        for rel in TARGETS:
            (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, tmp / rel)
        target = tmp / "AGENTS.md"
        text = target.read_text(encoding="utf-8")
        m = MARKER.search(text)
        if m is None:
            failures.append("drift red case: no generated block in AGENTS.md")
        else:
            target.write_text(text.replace(m.group(2), m.group(2) + " DRIFT"),
                              encoding="utf-8")
            e, _ = check(tmp)
            expect("drifted block", True, e, "drifted")

    # green: the real tree passes
    e, _ = check(ROOT)
    expect("working tree", False, e)

    if failures:
        print("GEN_RULES SELFTEST: FAIL")
        for f in failures:
            print(" -", f)
        return 1
    print("GEN_RULES SELFTEST: OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    g.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if args.write:
        return write(ROOT)
    errors, warnings = check(ROOT)
    for w in warnings:
        print(f"  warn  {w}")
    if errors:
        print("RULES REGISTRY: FAIL")
        for e in errors:
            print(" -", e)
        return 1
    reg = load(ROOT)
    print(f"RULES REGISTRY: OK ({len(reg['rules'])} rules, "
          f"{len(reg.get('faults', []))} fault classes, "
          f"{len(warnings)} warnings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
