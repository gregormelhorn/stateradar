#!/usr/bin/env python3
"""Extract the Part-1 writing rules from a text dump of ASD-STE100.

Layout-specific to Issue 7 (pdftotext -layout). Output stays PRIVATE:
the rule texts are ASD copyright. Usage:
  pdftotext -layout ASD-STE100-ISSUE-7.pdf spec.txt
  python3 tools/extract_ste_rules.py spec.txt ~/ste-private/ste-rules-issue7.json
"""
import json, re, sys
from pathlib import Path

def main() -> int:
    lines = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
    rules, cur = {}, None
    rule_re = re.compile(r"^\s*Rule (\d+\.\d+)\s+(.*)$")
    def flush():
        nonlocal cur
        if cur:
            rid, stmt, expl = cur
            rules[rid] = {"id": rid,
                          "statement": " ".join(s.strip() for s in stmt).strip(),
                          "explanation": "\n".join(expl[:12]).strip()}
        cur = None
    for ln in lines:
        if re.match(r"^(Issue 7|Page \d|\s*Simplified Technical English)|^\f", ln):
            continue
        m = rule_re.match(ln)
        if m:
            flush()
            cur = (m.group(1), [m.group(2)], [])
            continue
        if cur:
            rid, stmt, expl = cur
            if not expl and ln.startswith(" ") and ln.strip():
                stmt.append(ln)            # indented statement continuation
            elif ln.strip() or expl:
                expl.append(ln)
    flush()
    Path(sys.argv[2]).write_text(json.dumps(rules, indent=1))
    print(f"extracted {len(rules)} rules -> {sys.argv[2]}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
