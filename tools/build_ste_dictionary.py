#!/usr/bin/env python3
"""Build the Vale dictionary for the full-STE word check.

The pack ships the MECHANISM, not the data: the ASD-STE100 core
dictionary is copyrighted by ASD (the specification is issued free of
charge on request at asd-ste100.org) and is not redistributable here.
Obtain the word list yourself, one word per line, then run:

  python3 tools/build_ste_dictionary.py --wordlist ste-core-words.txt

The script merges: your core list + the STYLE.md project dictionary +
styles/config/vocabularies/Pack/accept.txt, and writes hunspell files
to styles/config/dictionaries/. Enable the check by adding STEDict to
BasedOnStyles in .vale.ini for the paths you want gated.
"""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def style_terms() -> set[str]:
    text = (ROOT / "STYLE.md").read_text(encoding="utf-8")
    m = re.search(r"## Project dictionary.*?\n\n(.*?)\n\n", text, re.S)
    words: set[str] = set()
    if m:
        for token in re.split(r"[·\n]", m.group(1)):
            for w in re.findall(r"[A-Za-z][A-Za-z-]+", token):
                words.add(w)
    return words

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wordlist", action="append", default=[],
                    help="user-supplied word list file(s), one word per line")
    args = ap.parse_args()
    words: set[str] = set()
    for wl in args.wordlist:
        for line in Path(wl).read_text(encoding="utf-8").splitlines():
            w = line.strip()
            if w and not w.startswith("#"):
                words.add(w)
    if not words:
        print("warning: no --wordlist given; dictionary will hold only "
              "project terms — the check is then a technical-name check, "
              "not an STE check", file=sys.stderr)
    words |= style_terms()
    vocab = ROOT / "styles/config/vocabularies/Pack/accept.txt"
    if vocab.exists():
        words |= {w.strip() for w in vocab.read_text().splitlines() if w.strip()}
    # both cases, so sentence-initial capitals do not flag
    words |= {w.lower() for w in set(words)} | {w.capitalize() for w in set(words)}
    out = ROOT / "styles/config/dictionaries"
    out.mkdir(parents=True, exist_ok=True)
    ordered = sorted(words)
    (out / "ste.dic").write_text(f"{len(ordered)}\n" + "\n".join(ordered) + "\n")
    (out / "ste.aff").write_text("SET UTF-8\n")
    print(f"wrote {len(ordered)} entries to {out/'ste.dic'}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
