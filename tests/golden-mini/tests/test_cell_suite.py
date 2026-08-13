#!/usr/bin/env python3
"""Golden-mini behavioral cell suite: drives Mini through the declared seam."""

from __future__ import annotations

import importlib.util
import json
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


def duplication_variants(analysis_dir: Path) -> set[str]:
    """Event ids the sidecar binds to the 'duplication' UV category.

    Read from coverage bindings, never inferred from the event name: a name is
    a label, a binding is a declaration. `prompts/04-testgen.md` requires
    'duplication = deliver twice', and idempotence is unobservable on a single
    delivery - a fault that only escalates on the repeat passes every cell.
    """
    sidecar = analysis_dir / "analysis.json"
    if not sidecar.is_file():
        return set()
    coverage = json.loads(sidecar.read_text(encoding="utf-8")).get("coverage", {})
    variants: set[str] = set()
    for categories in coverage.values():
        if not isinstance(categories, dict):
            continue
        value = categories.get("duplication")
        if not isinstance(value, str) or value.startswith("n/a"):
            continue
        variants.update(token for token in value.split() if token.startswith("UV-"))
    return variants


def check(module, state: str, event: str, expected: str,
          duplicates: set[str] = frozenset()) -> str | None:
    kind = expected.split()[0]  # transition | handle | ignore | reject
    # A duplication variant is delivered twice; every other event once.
    deliveries = 2 if event in duplicates else 1
    m = module.Mini()
    for nav in NAVIGATE[state]:
        m.deliver(nav)
    before = m.state
    before_count = m.dup_count
    try:
        for _ in range(deliveries):
            outcome = m.deliver(event)
            if m.state != before and kind in ("handle", "ignore"):
                # Catch an escalation on any delivery, not only the last one.
                return (f"expected {expected} to leave the state unchanged across "
                        f"{deliveries} deliveries, state moved {before}->{m.state}")
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
        if (outcome == "handled" and m.state == before
                and m.dup_count == before_count + deliveries):
            return None
        return (f"expected handle (counter {before_count}→{before_count + deliveries} "
                f"over {deliveries} deliveries), got {outcome} "
                f"counter={m.dup_count} state={m.state}")
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
    duplicates = duplication_variants(analysis_dir)
    failures = 0
    checked = 0
    for (state, event), expected in sorted(matrix.items()):
        checked += 1
        problem = check(module, state, event, expected, duplicates)
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
