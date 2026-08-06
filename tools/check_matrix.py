#!/usr/bin/env python3
"""Generic per-component matrix checker (the 02-pilot stage-1/stage-2 check).

Every pilot I ran duplicated this logic per component (dobby session,
2026-08-05: four near-identical scripts). This is the shared version:
it parses the machine-readable declarations (never prose) and checks
grid coverage, citation presence, hole→Q links, and pair→trace links.

Checks:
- Stage 1: every row covers every catalogue event exactly once (rows
  accumulate across sub-tables); every reject / ignore (documented) /
  defer cell carries a citation (`file.py:NNN`, a DR id, or an explicit
  `inferred` marker); no empty cells.
- Stage 2: every hole cell (UNSPECIFIED / ignore (accidental)) carries
  a `→ Q-nn` reference that exists in open-questions.md; every
  interaction pair id in the catalogue appears in adversarial-traces.md.

Usage: python3 tools/check_matrix.py <analysis-dir>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# A citation is `file.<ext>:NNN` in any implementation language (the
# pack claims language neutrality; ".py:" alone silently failed every
# Go/TS/Rust matrix — grpc-go addrconn pilot, 2026-08-07), a DR id, or
# an explicit `inferred` marker.
CITATION_OK = ("DR-", "inferred")
CITATION_RE = re.compile(r"[\w./-]+\.[A-Za-z]{1,4}:\d+")


def _events(catalogue: str) -> list[str]:
    m = re.search(r"<!-- event-ids: (.+?) -->", catalogue)
    if not m:
        raise ValueError("catalogue: no event-ids declaration comment")
    return m.group(1).split()


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    adir = Path(sys.argv[1])
    errors: list[str] = []

    cat_path = adir / "event-catalogue.md"
    if not cat_path.is_file():
        print(f"CHECK MATRIX: no event-catalogue.md in {adir}")
        return 2
    cat = cat_path.read_text(encoding="utf-8")
    events = _events(cat)

    matrix = (adir / "disposition-matrix.md").read_text(encoding="utf-8")
    if "<!-- states:" not in matrix:
        errors.append("matrix: no states declaration comment")

    # PA-17 state naming: PascalCase segments joined by "_"
    # (Open_AwaitingStability), ALL-CAPS API enums (CONNECTING,
    # TRANSIENT_FAILURE), compound row labels word by word ("Open Idle").
    # A name a blind reader cannot derive — implementation flags,
    # comparisons, lowercase — is a modelling error.
    word_ok = re.compile(r"^[A-Z][A-Za-z0-9]*(?:_[A-Z][A-Za-z0-9]*)*$")
    decl = re.search(r"<!-- states: (.+?) -->", matrix)
    if decl:
        raw = decl.group(1)
        names = ([s.strip() for s in raw.split(",")] if "," in raw
                 else raw.split())
        for name in names:
            for word in name.split(" "):
                if word and not word_ok.match(word):
                    errors.append(
                        f"state {name!r} violates PA-17 naming "
                        f"(offending word {word!r}: use PascalCase segments "
                        f"with '_' separators or the ALL-CAPS API enum name)")

    rows: dict[str, int] = {}
    for line in matrix.split("\n"):
        s = line.strip()
        if not s.startswith("| **"):
            continue
        label = s.split("|")[1].strip().replace("**", "").strip()
        cells = s.split("|")[2:-1]
        rows[label] = rows.get(label, 0) + len(cells)
        for cell in cells:
            c = cell.strip()
            if not c:
                errors.append(f"empty cell in row {label}")
                continue
            if (
                c.startswith(("reject", "ignore (documented", "defer"))
                and not CITATION_RE.search(c)
                and not any(tok in c for tok in CITATION_OK)
                and "Q-" not in c
            ):
                errors.append(f"uncited {c[:50]!r} in row {label}")

    total = sum(rows.values())
    if total != len(events) * len(rows):
        errors.append(
            f"grid: {total} cells across {len(rows)} rows, "
            f"expected {len(events)} per row"
        )

    # Stage 1: undesired-coverage totality, when the catalogue carries
    # the table (an empty cell is an error — a checklist category must
    # never silently produce no variant).
    if "## Undesired-coverage" in cat:
        cov = cat.split("## Undesired-coverage")[1].split("##")[0]
        for line in cov.split("\n"):
            if (
                line.strip().startswith("|")
                and "**" not in line
                and "---" not in line
                and "source" not in line.lower()
            ):
                cells = [c.strip() for c in line.split("|")[1:-1]]
                for c in cells[1:]:
                    if not c:
                        errors.append(f"coverage: empty cell in {cells[0]}")

    # Stage 2: hole cells carry Q refs present in open-questions.md
    oq_path = adir / "open-questions.md"
    oq = oq_path.read_text(encoding="utf-8") if oq_path.is_file() else ""
    qids = set(re.findall(r"\b(Q-[\w-]+)\b", oq))
    for m in re.finditer(r"(UNSPECIFIED|ignore \(accidental\))[^\n|]*", matrix):
        q = re.search(r"Q-[\w-]+", m.group(0))
        if not q:
            errors.append(f"hole cell without Q ref: {m.group(0)[:60]!r}")
        elif q.group(0) not in qids:
            errors.append(f"hole cell: {q.group(0)} not in open-questions.md")

    # Stage 2: every pair id appears in the traces
    traces_path = adir / "adversarial-traces.md"
    if traces_path.is_file():
        traces = traces_path.read_text(encoding="utf-8")
        for pair in sorted(set(re.findall(r"P-\d+[ab]", cat))):
            if pair not in traces:
                errors.append(f"pair {pair} missing from adversarial-traces.md")

    if errors:
        print("CHECK MATRIX: FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print(f"CHECK MATRIX: OK ({len(rows)} rows x {len(events)} events)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
