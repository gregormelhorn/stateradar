#!/usr/bin/env python3
"""Generate the ODC (Orthogonal Defect Classification) coverage table
from benchmark sidecar analysis.json files.

Reads fault/trigger fields from questions in each benchmark's analysis.json,
aggregates by fault class, and renders the table into
tests/benchmarks/README.md between generated markers.

Usage: python3 tools/gen_odc_table.py [--write] [--check]
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS_DIR = ROOT / "tests" / "benchmarks"
README_PATH = BENCHMARKS_DIR / "README.md"

MARKER_START = "<!-- generated:odc start -->"
MARKER_END = "<!-- generated:odc end -->"


def load_sidecars() -> dict[str, dict]:
    """Load all benchmark sidecars. Returns {case_name: data}."""
    sidecars: dict[str, dict] = {}
    for case_dir in sorted(BENCHMARKS_DIR.iterdir()):
        if not case_dir.is_dir():
            continue
        path = case_dir / "analysis.json"
        if not path.is_file():
            continue
        try:
            sidecars[case_dir.name] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"warning: invalid JSON in {path}", file=sys.stderr)
    return sidecars


def build_odc(sidecars: dict[str, dict]) -> dict[str, dict[str, list[str]]]:
    """Build ODC table: {fault_id: {trigger: [case_label, ...]}}.

    Excludes test-suite artifacts (F-21).
    """
    odc: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    for case_name, data in sidecars.items():
        for q in data.get("questions", []):
            faults = q.get("fault", [])
            trigger = q.get("trigger", "")
            qid = q["id"]
            label = f"{case_name} ({qid})"
            for f_id in faults:
                # Skip test-suite faults
                if f_id == "F-21":
                    continue
                odc[f_id][trigger].append(label)

    return dict(odc)


def render_table(odc: dict[str, dict[str, list[str]]]) -> str:
    """Render the ODC coverage table as markdown."""
    lines: list[str] = []
    lines.append(MARKER_START)
    lines.append("")
    lines.append("## Fault-class × detector coverage (ODC)")
    lines.append("")
    lines.append("Dominant fault class per finding, from `formats/rules.toml`. "
                 "Generated from benchmark sidecar `fault`/`trigger` fields.")
    lines.append("")
    lines.append("| Fault class | Trigger | Benchmark case(s) |")
    lines.append("|---|---|---|")

    for f_id in sorted(odc):
        by_trigger = odc[f_id]
        for trigger in sorted(by_trigger):
            cases = ", ".join(sorted(set(by_trigger[trigger])))
            lines.append(f"| {f_id} | {trigger} | {cases} |")

    lines.append("")
    lines.append(MARKER_END)
    return "\n".join(lines)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Generate ODC coverage table from sidecars")
    parser.add_argument("--write", action="store_true", help="Write to README.md")
    parser.add_argument("--check", action="store_true", help="Check generated vs committed (exit 1 on drift)")
    args = parser.parse_args()

    sidecars = load_sidecars()
    if not sidecars:
        print("No sidecars found.")
        return 0 if not args.check else 1

    odc = build_odc(sidecars)
    rendered = render_table(odc)

    if args.write:
        readme = README_PATH.read_text(encoding="utf-8")
        if MARKER_START in readme:
            # Replace existing generated block
            start = readme.find(MARKER_START)
            end = readme.find(MARKER_END, start)
            if end == -1:
                print("error: MARKER_END not found", file=sys.stderr)
                return 1
            updated = readme[:start] + rendered + readme[end + len(MARKER_END):]
        else:
            # Add after the existing table section header
            header = "## Fault-class × detector coverage (ODC)"
            pos = readme.find(header)
            if pos == -1:
                print("error: cannot find ODC section header", file=sys.stderr)
                return 1
            # Find end of hand-maintained section (next ## heading)
            next_section = readme.find("\n## ", pos + len(header))
            if next_section == -1:
                next_section = len(readme)
            # Remove hand-maintained table body
            updated = readme[:pos] + rendered + "\n" + readme[next_section:]

        README_PATH.write_text(updated, encoding="utf-8")
        print(f"ODC table written to {README_PATH}")

    if args.check:
        committed = README_PATH.read_text(encoding="utf-8")
        if MARKER_START in committed:
            start = committed.find(MARKER_START)
            end = committed.find(MARKER_END, start)
            committed_block = committed[start:end + len(MARKER_END)]
            if committed_block != rendered:
                print("ODC table drift — run tools/gen_odc_table.py --write")
                return 1
            print("ODC table: OK")
        else:
            print("ODC table: no generated block (run --write first)")
            return 1

    if not args.write and not args.check:
        print(rendered)

    return 0


if __name__ == "__main__":
    sys.exit(main())
