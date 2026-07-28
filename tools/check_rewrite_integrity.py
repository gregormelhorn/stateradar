#!/usr/bin/env python3
"""Meaning-protection check for STE rewrites.

Usage: check_rewrite_integrity.py original.md rewritten.md [protect.txt]
Verifies that protected content survived the rewrite verbatim: fenced
code blocks, inline code spans, identifiers (DR/Q/GG/UV/P/SYS/NAT),
file paths, numbers, URLs, and extra protected tokens. Exit 0 = OK.
"""
import re, sys
from pathlib import Path

ID_RE = re.compile(r"\b(?:DR|Q|GG|UV|P|SYS|NAT)-\d+[ab]?\b")
PATH_RE = re.compile(r"\b[\w./-]+\.(?:py|md|json|yml|yaml|mmd|txt|ini)\b")
NUM_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
URL_RE = re.compile(r"https?://\S+")

def fenced(text: str) -> list[str]:
    return re.findall(r"```.*?```", text, re.S)

def spans(text: str) -> set[str]:
    return set(re.findall(r"`[^`\n]+`", text))

def main() -> int:
    orig = Path(sys.argv[1]).read_text(encoding="utf-8")
    new = Path(sys.argv[2]).read_text(encoding="utf-8")
    protect = []
    if len(sys.argv) > 3 and sys.argv[3] != "none":
        protect = [l.strip() for l in Path(sys.argv[3]).read_text().splitlines()
                   if l.strip() and not l.startswith("#")]
    errors = []
    for block in fenced(orig):
        if block not in new:
            errors.append(f"code block lost/changed: {block.splitlines()[0][:50]}...")
    for token_set, label in (
        (spans(orig), "code span"),
        (set(ID_RE.findall(orig)), "identifier"),
        (set(PATH_RE.findall(orig)), "path"),
        (set(NUM_RE.findall(orig)), "number"),
        (set(URL_RE.findall(orig)), "url"),
        (set(protect), "protected token"),
    ):
        for t in sorted(token_set):
            if t not in new:
                errors.append(f"{label} lost: {t!r}")
    if errors:
        print("REWRITE INTEGRITY: FAIL")
        for e in errors: print(" -", e)
        return 1
    print(f"REWRITE INTEGRITY: OK ({len(fenced(orig))} blocks, "
          f"{len(spans(orig))} spans, ids/paths/numbers/urls verified)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
