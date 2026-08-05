#!/usr/bin/env python3
"""Cross-model composition report (v1 — report, not a gate).

One machine per bounded context means behaviour surfaces in one model
but lives in another (dobby: the mqtt-consumer's replaying state was
untestable because replay belongs to session-recovery). As the model
count grows, the links between models need inspection: which event
names appear in several catalogues, who produces what, who consumes
what, and where a matrix explicitly hands behaviour to a neighbour
(untestable-via-seam with a reason naming the other component).

Checks (report-only; nothing here breaks a build yet):
- event names in 2+ catalogues: producer/consumer wiring across models
- untestable-via-seam reasons that name another modelled component
  (the explicit model links)

Usage: python3 tools/dsc_compose.py [--repo .] [--analysis-dir domain-analysis]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

#: Sources that legitimately produce without a model (actors outside
#: the analysed system).
EXTERNAL_ACTORS = ("appliance", "GM", "operator", "process", "paho", "transport")


def _events_from_catalogue(path: Path) -> list[dict]:
    """Parse the external+internal event tables of a catalogue."""
    events = []
    text = path.read_text(encoding="utf-8")
    in_table = False
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("## "):
            in_table = "events" in s.lower() and "catalogue" not in s.lower()
        if not in_table or not s.startswith("|") or "---" in s:
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) < 7 or cells[0] in ("id",):
            continue
        events.append(
            {
                "id": cells[0],
                "name": cells[1],
                "source": cells[2],
                "produced": cells[5],
                "consumed": cells[6],
            }
        )
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--analysis-dir", default="domain-analysis")
    args = parser.parse_args()

    root = Path(args.repo).resolve()
    analysis = root / args.analysis_dir
    components = sorted(
        d.name for d in analysis.iterdir() if d.is_dir() and (d / "event-catalogue.md").is_file()
    )
    if not components:
        print("COMPOSE: no catalogues found")
        return 0

    # name -> [(component, event)]
    by_name: dict[str, list[tuple[str, dict]]] = {}
    for comp in components:
        for event in _events_from_catalogue(analysis / comp / "event-catalogue.md"):
            by_name.setdefault(event["name"], []).append((comp, event))

    findings = 0
    print(f"COMPOSE: {len(components)} models, {len(by_name)} distinct event names")

    print("\n## Cross-model event wiring")
    for name, refs in sorted(by_name.items()):
        if len(refs) < 2:
            continue
        comps = ", ".join(sorted({c for c, _ in refs}))
        print(f"  {name}: {comps}")
        findings += 1

    print("\n## Model links (untestable-via-seam → neighbour model)")
    # Scan every coverage file, not only catalogue-carrying components:
    # light-loop components hand behaviour to neighbours too.
    all_components = sorted(
        d.name for d in analysis.iterdir() if d.is_dir() and d.name != "decisions"
    )
    for comp in all_components:
        cov_path = analysis / comp / "matrix-coverage.json"
        if not cov_path.is_file():
            continue
        cov = json.loads(cov_path.read_text())
        for cell, reason in (cov.get("untestable_via_seam") or {}).items():
            targets = [
                c
                for c in all_components
                if c != comp and (c in reason or c.replace("-", " ") in reason)
            ]
            if targets:
                print(f"  {comp} :: {cell} → {', '.join(targets)} ({reason[:80]})")
                findings += 1

    print(f"\nCOMPOSE: {findings} findings (report-only, no gate)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
