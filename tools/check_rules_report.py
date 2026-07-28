#!/usr/bin/env python3
"""Coverage and schema check for the STE rules report.

Usage: check_rules_report.py report.json rules.json [map.json]
Verifies: scope discipline (full = every rule id exactly once; sample =
declared subset covered exactly), verdict enum, rule grounding, quote
length, machine-checked entries name a Vale rule. Exit 0 = OK.
"""
import json, sys
from pathlib import Path

ENUM = {"compliant", "violation", "not-applicable", "machine-checked", "needs-human"}

def main() -> int:
    report = json.loads(Path(sys.argv[1]).read_text())
    rules = json.loads(Path(sys.argv[2]).read_text())
    map_rules = {}
    if len(sys.argv) > 3:
        map_rules = json.loads(Path(sys.argv[3]).read_text()).get("rules", {})
    errors = []
    rows = report.get("rules", [])
    seen = [r.get("ruleId") for r in rows]
    scope = report.get("scope", "full")
    expected = set(rules) if scope == "full" else set(report.get("sampleIds", []))
    if scope != "full" and not expected:
        errors.append("sample scope without sampleIds declaration")
    if sorted(seen) != sorted(expected):
        missing = expected - set(seen); extra = set(seen) - expected
        if missing: errors.append(f"rules without verdict: {sorted(missing)}")
        if extra: errors.append(f"verdicts outside scope: {sorted(extra)}")
    if len(seen) != len(set(seen)):
        errors.append("duplicate rule verdicts")
    for r in rows:
        if r.get("ruleId") not in rules:
            errors.append(f"{r.get('ruleId')}: not a known rule id")
        if r.get("verdict") not in ENUM:
            errors.append(f"{r.get('ruleId')}: verdict {r.get('verdict')!r} not in enum")
        if r.get("verdict") == "machine-checked" and not r.get("valeRule"):
            errors.append(f"{r.get('ruleId')}: machine-checked without a Vale rule name")
        mr = map_rules.get(r.get("ruleId"))
        if mr and mr["verdict"] != "judge":
            if r.get("verdict") != mr["verdict"]:
                errors.append(f"{r.get('ruleId')}: map says {mr['verdict']!r}, report says {r.get('verdict')!r}")
            if mr["verdict"] == "machine-checked" and r.get("valeRule") != mr.get("valeRule"):
                errors.append(f"{r.get('ruleId')}: map vale rule {mr.get('valeRule')!r} not inherited")
        for f in r.get("findings", []) or []:
            if len(f.get("quote", "").split()) > 8:
                errors.append(f"{r.get('ruleId')}: quote longer than 8 words")
    if errors:
        print("RULES REPORT: FAIL")
        for e in errors: print(" -", e)
        return 1
    print(f"RULES REPORT: OK (scope {scope}, {len(rows)} rules)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
