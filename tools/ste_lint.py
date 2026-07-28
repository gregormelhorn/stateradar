#!/usr/bin/env python3
"""Deterministic lint for the machine-checkable STE subset (approximation).

Counts, per prose line (skips code fences, tables, headings, HTML comments):
em dashes, long sentences (> 24 words), passive markers, banned words,
semicolons. Score = violations per 100 words. The delta between two texts
is the signal. This is not a certified STE checker.

Usage: python3 tools/ste_lint.py FILE [FILE ...]
"""
from __future__ import annotations
import re, sys
from pathlib import Path

BANNED = ["utilize", "leverage", "facilitate", "ensure", "prior to",
          "subsequent to", "in order to", "commence", "initiate",
          "furthermore", "moreover", "additionally", "comprehensive",
          "robust", "seamless", "crucial", "delve"]
PASSIVE = re.compile(r"\b(is|are|was|were|be|been|being)\s+\w+ed\b")

def prose_lines(text: str):
    fence = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence or not s or s.startswith(("|", "#", "<!--", ">", "*.")):
            continue
        yield line

def lint(path: Path) -> dict:
    body = "\n".join(prose_lines(path.read_text(encoding="utf-8")))
    words = len(body.split())
    sentences = re.split(r"(?<=[.!?])\s+", body)
    long_s = sum(1 for s in sentences if len(s.split()) > 24)
    em = body.count("\u2014")
    passive = len(PASSIVE.findall(body.lower()))
    banned = sum(len(re.findall(r"\b" + re.escape(b) + r"\b", body.lower())) for b in BANNED)
    semi = body.count(";")
    total = long_s + em + passive + banned + semi
    return {"words": words, "em": em, "long": long_s, "passive": passive,
            "banned": banned, "semi": semi, "total": total,
            "per100w": round(100 * total / max(words, 1), 2)}

if __name__ == "__main__":
    for f in sys.argv[1:]:
        r = lint(Path(f))
        print(f"{Path(f).name:28} words={r['words']:5} em={r['em']:3} long={r['long']:3} "
              f"passive={r['passive']:3} banned={r['banned']:2} semi={r['semi']:3} "
              f"total={r['total']:4} per100w={r['per100w']:6.2f}")
