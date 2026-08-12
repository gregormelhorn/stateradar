#!/usr/bin/env python3
"""Golden-mini behavioral cell suite: drives Mini through the declared seam."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

NAVIGATE = {"Idle": [], "Open": ["M1"], "Closed": ["M1", "M2"]}
EVENTS = ["M1", "M2", "UV-M1-dup", "UV-M2-stale", "UV-M1-lost", "UV-M2-conflict", "UV-M1-spurious"]


def load_mini(component_root: Path):
    spec = importlib.util.spec_from_file_location(
        "mini_impl", component_root / "src" / "mini.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_matrix(path: Path) -> dict[tuple[str, str], str]:
    rows: dict[tuple[str, str], str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("| state"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2 or set(cells[0]) <= {"-", ":"}:
            continue
        state = cells[0].strip("*")
        for event, raw in zip(EVENTS, cells[1:], strict=True):
            token = raw.split("`")[0].strip()
            rows[(state, event)] = token
    return rows


def check(module, state: str, event: str, expected: str) -> str | None:
    kind = expected.split()[0]  # transition | handle | ignore | reject
    m = module.Mini()
    for nav in NAVIGATE[state]:
        m.deliver(nav)
    before = m.state
    before_count = m.dup_count
    try:
        outcome = m.deliver(event)
    except module.RejectedError:
        return None if kind == "reject" and m.state == before else (
            f"expected {expected}, got reject"
        )
    if kind == "transition":
        target = expected.split("→", 1)[1].strip()
        if outcome == "transition" and m.state == target:
            return None
        return f"expected {expected}, got {outcome} state={m.state}"
    if kind == "handle":
        if outcome == "handled" and m.state == before and m.dup_count == before_count + 1:
            return None
        return f"expected handle (counter {before_count}→{m.dup_count}), got {outcome} state={m.state}"
    if kind == "ignore":
        if outcome == "ignored" and m.state == before:
            return None
        return f"expected ignore, got {outcome} state={m.state}"
    if kind == "reject":
        return f"expected reject, got {outcome}"
    return f"unknown disposition {expected}"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("CELL SUITE: expected one analysis directory", file=sys.stderr)
        return 2
    analysis_dir = Path(argv[1]).resolve()
    component_root = Path(__file__).resolve().parent.parent
    module = load_mini(component_root)
    matrix = parse_matrix(analysis_dir / "disposition-matrix.md")
    if not matrix:
        print("CELL SUITE: no matrix cells parsed", file=sys.stderr)
        return 2
    failures = 0
    checked = 0
    for (state, event), expected in sorted(matrix.items()):
        checked += 1
        problem = check(module, state, event, expected)
        if problem:
            # Human-readable diagnosis, plus the machine-readable cell-failure
            # contract line. The contract line uses ASCII 'x', matching how
            # fault-mutants.json declares a cell.
            print(f"MISMATCH {state} × {event}: {problem}")
            print(f"CELL FAIL {state} x {event}")
            failures += 1
    # Completion marker, printed on every path that reaches the end of the loop.
    # A per-cell failure line alone is NOT enough for a checker to trust a
    # verdict: a suite can report one failing cell and then crash on a later
    # one, which is exactly how a hollow kill proof arose in this fixture. Only
    # a line that requires the loop to finish separates a clean failure from a
    # crash, because the exit code cannot.
    print(f"CELL SUITE: {checked} cells checked, {failures} failed")
    if failures:
        return 1
    print("CELL SUITE: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
