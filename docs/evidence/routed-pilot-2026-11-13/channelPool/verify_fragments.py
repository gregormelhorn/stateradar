#!/usr/bin/env python3
"""Verify every `file:line ("fragment")` citation in the analysis markdown
against the repo with the pack's ±3-line window. Exists because the
generated sidecar carries no fragments, so dsc_check cannot verify them."""
import re, sys
from pathlib import Path
here = Path(__file__).resolve().parent
repo = here.parents[1]
pat = re.compile(r"([\w./-]+\.(?:go|md)):(\d+)(?:-\d+)?\s*\(\"((?:[^\"\\]|\\.)+)\"\)")
bad = ok = 0
for md in sorted(here.glob("*.md")):
    for n, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
        for f, ln, frag in pat.findall(line):
            src = repo / f
            if not src.exists():
                continue
            lines = src.read_text(encoding="utf-8").splitlines()
            ln = int(ln)
            window = "\n".join(lines[max(0, ln - 4):ln + 3])
            frag = frag.replace('\\"', '"')
            if frag in window:
                ok += 1
            else:
                bad += 1
                print(f"FAIL {md.name}:{n}: {f}:{ln} ({frag!r})")
print(f"fragments ok={ok} failed={bad}")
sys.exit(1 if bad else 0)
