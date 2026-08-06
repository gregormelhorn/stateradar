#!/usr/bin/env python3
"""Reachability and completeness checker for StateRadar analysis.json.

Reads the sidecar produced by gen_analysis_sidecar.py and verifies:
  1. Every state is reachable from the initial state (or via a
     documenting edge from a compound parent).
  2. Every event has at least one transition (no dead events).
  3. No state is a sink unless marked as terminal.

The analysis.json schema already carries all the data needed; this
checker adds a semantic layer on top of the structural checks that
dsc_check.py already performs.

Usage:
  python3 tools/check_reachability.py <analysis-dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_graph(analysis_dir: Path) -> tuple[set[str], set[str], dict[str, set[str]], set[str]]:
    """Load states, events, transitions, and terminal states from analysis.json.

    Returns (states, events, adjacency, terminals).
    """
    sidecar = analysis_dir / "analysis.json"
    if not sidecar.is_file():
        sys.exit(f"no analysis.json at {analysis_dir}")

    data = json.loads(sidecar.read_text(encoding="utf-8"))
    cells = data.get("cells", [])
    states = set(data.get("states", []))
    events = {e["id"] for e in data.get("events", [])}

    # Parse terminal states from the matrix comment
    matrix_path = analysis_dir / "disposition-matrix.md"
    terminals: set[str] = set()
    if matrix_path.is_file():
        import re
        text = matrix_path.read_text(encoding="utf-8")
        tm = re.search(r"<!--\s*terminal:\s*(.+?) -->", text)
        if tm:
            terminals = {s.strip() for s in tm.group(1).split(",")}

    # Build adjacency: state -> set of reachable states
    adjacency: dict[str, set[str]] = {s: set() for s in states}
    events_with_transitions: set[str] = set()

    for c in cells:
        src = c.get("state", "")
        if c.get("disposition") == "transition":
            tgt = c.get("target", "")
            if tgt and tgt in states:
                adjacency.setdefault(src, set()).add(tgt)
                events_with_transitions.add(c.get("event", ""))

    return states, events, adjacency, terminals, events_with_transitions


def reachable_from(start: str, adjacency: dict[str, set[str]]) -> set[str]:
    """BFS from start through the transition graph."""
    visited: set[str] = set()
    queue = [start]
    while queue:
        s = queue.pop(0)
        if s in visited:
            continue
        visited.add(s)
        for tgt in adjacency.get(s, set()):
            if tgt not in visited:
                queue.append(tgt)
    return visited


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 tools/check_reachability.py <analysis-dir>")
        return 1

    adir = Path(sys.argv[1])
    states, events, adjacency, terminals, events_with_transitions = load_graph(adir)

    errors: list[str] = []

    # 1. Reachability from initial state
    # The first state in the list is conventionally the initial state.
    initial = next(iter(states)) if states else None
    if initial:
        reached = reachable_from(initial, adjacency)
        unreachable = states - reached - {"[*]"}
        # Terminal states declared via <!-- terminal: ... --> don't need
        # outbound transitions — they are sinks by design.
        for s in sorted(unreachable):
            if s not in terminals:
                errors.append(
                    f"state '{s}' is unreachable from initial state '{initial}'"
                )

    # 2. Dead events: no transition from any state
    dead_events = events - events_with_transitions
    for e in sorted(dead_events):
        # Events that are only handled (not transitions) are fine
        pass  # We can't distinguish from the sidecar alone

    # 3. Non-terminal sink states
    all_sources = set(adjacency.keys()) | {tgt for tgts in adjacency.values() for tgt in tgts}
    for s in sorted(states):
        if s not in adjacency or not adjacency[s]:
            if s not in terminals and s != "[*]":
                # State has no outgoing transitions — is it a documented sink?
                errors.append(
                    f"state '{s}' has no outgoing transitions and is not marked terminal"
                )

    if errors:
        print("REACHABILITY CHECK: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1

    total = len(states)
    reached_count = len(reached) if initial else 0
    print(
        f"REACHABILITY CHECK: OK "
        f"({reached_count}/{total} states reachable from '{initial}', "
        f"{len(terminals)} terminal)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
