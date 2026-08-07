#!/usr/bin/env python3
"""Benchmark dating protocol — contamination-honest evidence classification.

Adopts the LiveCodeBench / CWE-Trace pattern: every case carries
dating metadata, and the runner auto-classifies cases into
*primary evidence* (issue published after model release) and
*regression anchor* (rest).

Fields per case (in expected.json -> dating):
  issue_published: ISO date of the upstream issue/PR
  model:           model name used for the pilot run
  model_release:   ISO date the model was released (or the model card date)
  model_cutoff:    ISO date of the model's knowledge cutoff

Classification rule:
  primary_evidence:  issue_published > model_release
  regression_anchor: issue_published <= model_release OR fields missing
  unknown:           dating section absent or incomplete (needs manual fill)

Usage:
  # Classify all benchmarks
  python3 tools/benchmark_evidence.py

  # Classify and write the README evidence table
  python3 tools/benchmark_evidence.py --write-readme

  # Just print classification
  python3 tools/benchmark_evidence.py --format table
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional


BENCHMARKS_DIR = Path(__file__).resolve().parent.parent / "tests" / "benchmarks"
README_PATH = Path(__file__).resolve().parent.parent / "tests" / "benchmarks" / "README.md"


def _parse_date(s: str | None) -> Optional[date]:
    """Parse ISO date string, returning None if missing or malformed."""
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _load_benchmarks() -> list[dict]:
    """Load all benchmark expected.json files with dating metadata."""
    results = []
    for case_dir in sorted(BENCHMARKS_DIR.iterdir()):
        if not case_dir.is_dir():
            continue
        expected_path = case_dir / "expected.json"
        if not expected_path.is_file():
            continue
        try:
            data = json.loads(expected_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"warning: invalid JSON in {expected_path}", file=sys.stderr)
            continue
        data["_case"] = case_dir.name
        results.append(data)
    return results


def classify(dating: dict | None) -> str:
    """Classify a case based on its dating metadata.

    Returns: 'primary', 'regression', or 'unknown'
    """
    if not dating:
        return "unknown"

    issue_published = _parse_date(dating.get("issue_published"))
    model_release = _parse_date(dating.get("model_release"))
    model = dating.get("model")
    model_cutoff = _parse_date(dating.get("model_cutoff"))

    if issue_published is None or model_release is None:
        return "unknown"

    if model is None:
        return "unknown"

    if issue_published > model_release:
        return "primary"
    else:
        return "regression"


def _classification_label(cls: str) -> str:
    if cls == "primary":
        return "✅ Primary evidence"
    elif cls == "regression":
        return "📎 Regression anchor"
    else:
        return "❓ Unknown (dating metadata incomplete)"


def _generate_readme_section(benchmarks: list[dict]) -> str:
    """Generate the Oracle-confirmed benchmarks table section."""
    lines: list[str] = []
    lines.append("## Oracle-confirmed benchmarks")
    lines.append("")

    # Classification summary
    primary = sum(1 for b in benchmarks if classify(b.get("dating")) == "primary")
    regression = sum(1 for b in benchmarks if classify(b.get("dating")) == "regression")
    unknown = sum(1 for b in benchmarks if classify(b.get("dating")) == "unknown")

    lines.append(f"Primary evidence: {primary}, Regression anchors: {regression}, Unknown: {unknown}")
    lines.append("")
    lines.append("Caveat: public issues may predate model training cutoffs. ")
    lines.append("Cases where the issue was published **after** the model's release date ")
    lines.append("are marked as *primary evidence*; the rest serve as *regression anchors* ")
    lines.append("(the pack still correctly reads the pre-generated matrices).")
    lines.append("")

    lines.append("| # | Project | Issue | Defect class | Evidence |")
    lines.append("|---|---|---|---|---|")

    for i, case in enumerate(benchmarks, 1):
        name = case.get("_case", "?")
        project = name.replace("-", "/", 1) if "-" in name else name
        # Try to get issue from the case data
        issue_ref = "?"
        repo = case.get("repo", "")
        commit = case.get("commit", "")
        if repo and commit:
            issue_ref = f"[{commit}]({repo}/tree/{commit})"

        defect_class = "?"
        dating = case.get("dating", {})
        cls = classify(dating)
        label = _classification_label(cls)
        lines.append(f"| {i} | {project} | {issue_ref} | {defect_class} | {label} |")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark dating protocol — contamination-honest evidence classification."
    )
    parser.add_argument(
        "--write-readme",
        action="store_true",
        help="Rewrite the Oracle-confirmed benchmarks section in tests/benchmarks/README.md.",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format for classification (default: table).",
    )
    args = parser.parse_args()

    benchmarks = _load_benchmarks()
    if not benchmarks:
        print("No benchmarks found.")
        return 0

    if args.format == "json":
        result = []
        for case in benchmarks:
            dating = case.get("dating", {})
            cls = classify(dating)
            result.append({
                "case": case["_case"],
                "classification": cls,
                "issue_published": dating.get("issue_published"),
                "model": dating.get("model"),
                "model_release": dating.get("model_release"),
                "model_cutoff": dating.get("model_cutoff"),
            })
        json.dump(result, sys.stdout, indent=1, default=str)
        print()
        return 0

    # Table format
    print(f"{'Case':<30} {'Published':<12} {'Model':<20} {'Released':<12} {'Class':<12}")
    print("-" * 90)
    for case in benchmarks:
        dating = case.get("dating", {})
        cls = classify(dating)
        published = dating.get("issue_published", "?")
        model = dating.get("model", "?")
        released = dating.get("model_release", "?")
        print(f"{case['_case']:<30} {published:<12} {model:<20} {released:<12} {cls:<12}")

    print()
    primary = sum(1 for b in benchmarks if classify(b.get("dating")) == "primary")
    regression = sum(1 for b in benchmarks if classify(b.get("dating")) == "regression")
    unknown = sum(1 for b in benchmarks if classify(b.get("dating")) == "unknown")
    print(f"Primary evidence: {primary}, Regression anchors: {regression}, Unknown: {unknown}")

    if args.write_readme:
        # Read existing README, find and replace the Oracle-confirmed section
        readme = README_PATH.read_text(encoding="utf-8")
        section_start = readme.find("## Oracle-confirmed benchmarks")
        if section_start == -1:
            print("error: ## Oracle-confirmed benchmarks section not found in README.md",
                  file=sys.stderr)
            return 1
        # Find next ## heading after section_start
        next_section = readme.find("\n## ", section_start + 10)
        if next_section == -1:
            next_section = len(readme)

        new_section = _generate_readme_section(benchmarks)
        updated = readme[:section_start] + new_section + readme[next_section:]
        README_PATH.write_text(updated, encoding="utf-8")
        print(f"\nUpdated {README_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
