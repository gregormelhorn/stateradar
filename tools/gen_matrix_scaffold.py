#!/usr/bin/env python3
"""Generate a disposition-matrix skeleton from states + event catalogue.

The LLM fills cells; it should never have to hold the table structure
(wide-grid totality is the measured failure class — dobby, 2026-08-05:
23 columns forced a sub-table split by hand). This tool emits the
skeleton: header rows per sub-table, one row per state, empty cells,
the machine-readable declarations.

Usage:
  python3 tools/gen_matrix_scaffold.py <analysis-dir> \
      --states "idle active closed" [--columns 8] [--write]

Reads the event ids (incl. undesired variants) from the component's
event-catalogue.md declaration comment. Without --write it prints;
with --write it creates disposition-matrix.md (refuses to overwrite
an existing matrix — the matrix is authority, never clobber it).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_COLUMNS = 8


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis_dir")
    parser.add_argument("--states", required=True,
                        help="space-separated leaf state names")
    parser.add_argument("--columns", type=int, default=DEFAULT_COLUMNS,
                        help="max event columns per sub-table")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()

    adir = Path(args.repo).resolve() / args.analysis_dir
    catalogue_path = adir / "event-catalogue.md"
    if not catalogue_path.is_file():
        print(f"SCAFFOLD: no event-catalogue.md in {adir}", file=sys.stderr)
        return 2
    m = re.search(r"<!-- event-ids: (.+?) -->", catalogue_path.read_text())
    if not m:
        print("SCAFFOLD: catalogue has no event-ids declaration", file=sys.stderr)
        return 2
    events = m.group(1).split()
    states = args.states.split()

    tables: list[str] = []
    for i in range(0, len(events), args.columns):
        chunk = events[i : i + args.columns]
        header = "| state | " + " | ".join(chunk) + " |"
        sep = "|" + "---|" * (len(chunk) + 1)
        rows = ["| **%s** | %s |" % (s, " | ".join([""] * len(chunk))) for s in states]
        tables.append("\n".join([header, sep, *rows]))

    out = (
        "# Disposition matrix — <component>\n\n"
        f"<!-- states: {' '.join(states)} -->\n\n"
        + "\n\n".join(tables)
        + "\n\n## Guard notes\n\n- (one note per guarded (state, event) pair)\n"
    )

    matrix_path = adir / "disposition-matrix.md"
    if args.write:
        if matrix_path.is_file():
            print(f"SCAFFOLD: {matrix_path} exists — refusing to overwrite "
                  "the authority surface", file=sys.stderr)
            return 1
        matrix_path.write_text(out)
        print(f"SCAFFOLD: wrote {matrix_path} "
              f"({len(states)} states x {len(events)} events, "
              f"{len(tables)} sub-tables)")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
