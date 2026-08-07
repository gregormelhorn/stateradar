#!/usr/bin/env python3
"""Golden-mini cell contract suite for matrix mutation checks."""

from __future__ import annotations

import sys
from pathlib import Path

EXPECTED = {
    "Idle": {
        "M1": "transition →Open `mini.py:10`",
        "M2": "ignore (documented) `mini.py:20`",
        "UV-M1-dup": "handle (counted) `mini.py:30`",
    },
    "Open": {
        "M1": "ignore (documented) `mini.py:40`",
        "M2": "transition →Closed `mini.py:50`",
        "UV-M1-dup": "handle (counted) `mini.py:60`",
    },
    "Closed": {
        "M1": "reject `mini.py:70`",
        "M2": "ignore (documented) `mini.py:80`",
        "UV-M1-dup": "handle (counted) `mini.py:90`",
    },
}


def parse_matrix(path: Path) -> dict[str, dict[str, str]]:
    lines = [
        line for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("|")
    ]
    if len(lines) < 3:
        raise ValueError("matrix has no complete table")
    header = [part.strip() for part in lines[0].strip("|").split("|")]
    if header[0] != "state":
        raise ValueError("matrix table has no state header")
    events = header[1:]
    result: dict[str, dict[str, str]] = {}
    for line in lines[2:]:
        cells = [part.strip() for part in line.strip("|").split("|")]
        if len(cells) != len(header):
            raise ValueError("matrix row has wrong cell count")
        state = cells[0].strip("*")
        result[state] = dict(zip(events, cells[1:], strict=True))
    return result


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("CELL SUITE: expected one analysis directory", file=sys.stderr)
        return 2
    try:
        actual = parse_matrix(Path(argv[1]) / "disposition-matrix.md")
    except (OSError, ValueError) as exc:
        print(f"CELL SUITE: {exc}", file=sys.stderr)
        return 2
    for state, events in EXPECTED.items():
        for event, expected in events.items():
            got = actual.get(state, {}).get(event)
            if got != expected:
                print(
                    f"CELL SUITE: {state} × {event}: expected {expected!r}, got {got!r}",
                    file=sys.stderr,
                )
                return 1
    print("CELL SUITE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
