#!/usr/bin/env python3
"""Coverage and schema check for the STE sense report.

Usage: check_sense_report.py report.json lint_output.txt dictionary.json
Verifies: every lint-flagged word has a verdict; verdicts come from the
enum; grounded verdicts cite an entry key that exists in the dictionary;
snippets stay short. Exit 0 = OK, 1 = violations.
"""
import json, re, sys
from pathlib import Path

ENUM = {"ok", "wrong-sense", "wrong-pos", "unapproved",
        "technical-name-candidate", "covered-by-project-dictionary", "needs-human"}
UNGROUNDED = {"needs-human"}

def main() -> int:
    report = json.loads(Path(sys.argv[1]).read_text())
    lint = Path(sys.argv[2]).read_text() if sys.argv[2] != "none" else ""
    dic = json.loads(Path(sys.argv[3]).read_text())
    errors = []
    findings = report.get("findings", [])
    covered = {f["word"].lower() for f in findings}
    for w in set(re.findall(r"'([^']+)' is not in the STE dictionary", lint)):
        if w.lower() not in covered:
            errors.append(f"flagged word without verdict: {w!r}")
    for f in findings:
        if f.get("verdict") not in ENUM:
            errors.append(f"{f.get('word')}: verdict {f.get('verdict')!r} not in enum")
        if f.get("verdict") not in UNGROUNDED and f.get("entryKey") not in dic:
            errors.append(f"{f.get('word')}: entryKey {f.get('entryKey')!r} not in dictionary")
        if len(f.get("entrySnippet", "").split()) > 8:
            errors.append(f"{f.get('word')}: entrySnippet longer than 8 words")
    if errors:
        print("SENSE REPORT: FAIL")
        for e in errors: print(" -", e)
        return 1
    print(f"SENSE REPORT: OK ({len(findings)} findings, "
          f"{len(covered)} words covered)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
