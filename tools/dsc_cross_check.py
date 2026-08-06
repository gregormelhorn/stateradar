#!/usr/bin/env python3
"""Cross-check traditional review findings against the disposition matrix.

After a traditional code review (separate session, no statechart
methodology), map every finding to a matrix cell. A finding that maps
to an existing cell confirms the matrix covers it. A finding that does
not map exposes a gap.

Usage:
  python3 tools/dsc_cross_check.py <analysis-dir> <review-notes.md> [--repo .]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _extract_findings(review_path: Path) -> list[dict]:
    """Extract findings with file:line citations from review notes.

    Returns list of {file, line, text, severity} dicts.
    """
    findings: list[dict] = []
    text = review_path.read_text(encoding="utf-8")
    # Find numbered findings with file:line references
    pattern = re.compile(
        r"(?:^|\n)(?:\*{1,2}\s*|#+\s*|(?:CRITICAL|HIGH|MEDIUM|LOW)[\s:]*)?"
        r"(?:R\d+\s*[:.]\s*)?"
        r"(?:.*?)([\w./-]+\.[A-Za-z]{1,6}):(\d+)",
        re.MULTILINE,
    )
    for m in pattern.finditer(text):
        findings.append({
            "file": m.group(1),
            "line": int(m.group(2)),
            "text": text[max(0, m.start() - 100):m.end() + 100].strip(),
        })
    return findings


def _load_matrix_cells(analysis_dir: Path) -> list[dict]:
    """Load cells from analysis.json (generate if needed)."""
    sidecar_path = analysis_dir / "analysis.json"
    if not sidecar_path.is_file():
        sys.exit(f"no analysis.json at {sidecar_path} — run gen_analysis_sidecar first")
    return json.loads(sidecar_path.read_text(encoding="utf-8")).get("cells", [])


def cross_check(analysis_dir: Path, review_path: Path,
                src_index: dict[str, str]) -> dict:
    """Match review findings to matrix cells.

    Returns:
        matched: [(finding, cell), ...]
        unmatched: [finding, ...]
        matrix_uncovered: [cell, ...] — cells with UNSPECIFIED/ignore(accidental)
                          that have no matching review finding
    """
    findings = _extract_findings(review_path)
    cells = _load_matrix_cells(analysis_dir)

    matched: list[tuple[dict, dict]] = []
    unmatched: list[dict] = []

    for f in findings:
        # Resolve file basename through source index
        resolved = src_index.get(Path(f["file"]).name, f["file"])
        # Find cells citing this file:line
        candidates = [
            c for c in cells
            if c.get("citation", {}).get("file") == resolved
            and c.get("citation", {}).get("line") == f["line"]
        ]
        if candidates:
            for c in candidates:
                matched.append((f, c))
        else:
            # Also try partial match: same file, line within ±5
            candidates_near = [
                c for c in cells
                if c.get("citation", {}).get("file") == resolved
                and abs(c.get("citation", {}).get("line", 0) - f["line"]) <= 5
            ]
            if candidates_near:
                for c in candidates_near:
                    matched.append((f, c))
            else:
                unmatched.append(f)

    # Matrix cells that are holes but have no reviewer coverage
    matrix_uncovered = [
        c for c in cells
        if c["disposition"] in ("UNSPECIFIED", "ignore (accidental)")
        and not any(
            m_cell.get("state") == c["state"]
            and m_cell.get("event") == c["event"]
            for _, m_cell in matched
        )
    ]

    return {
        "matched": matched,
        "unmatched": unmatched,
        "matrix_uncovered": matrix_uncovered,
    }


def main() -> int:
    p = argparse.ArgumentParser(
        description="Cross-check traditional review against matrix"
    )
    p.add_argument("analysis_dir", help="path to domain-analysis/<component>/")
    p.add_argument("review_notes", help="path to review notes markdown")
    p.add_argument("--repo", default=".", help="repository root")
    args = p.parse_args()

    adir = Path(args.analysis_dir).resolve()
    review_path = Path(args.review_notes)
    if not review_path.is_file():
        sys.exit(f"review notes not found: {review_path}")

    # Build minimal source index from repo root
    root = Path(args.repo).resolve()
    src_index: dict[str, str] = {}
    repo_src = root / "src"
    if repo_src.is_dir():
        for f in repo_src.rglob("*"):
            if f.is_file() and f.suffix in (
                ".py", ".ts", ".tsx", ".go", ".rs", ".js",
            ):
                src_index.setdefault(f.name, str(f.relative_to(root)))

    result = cross_check(adir, review_path, src_index)

    n_matched = len(result["matched"])
    n_unmatched = len(result["unmatched"])
    n_holes = len(result["matrix_uncovered"])

    print(f"CROSS-CHECK: {n_matched} findings mapped to matrix cells")
    print(f"  {n_unmatched} findings without matrix cell → review gap or method-only finding")
    print(f"  {n_holes} matrix holes without reviewer coverage → inspection gap")

    if n_unmatched > 0:
        print("\nUnmatched review findings:")
        for f in result["unmatched"]:
            print(f"  - {Path(f['file']).name}:{f['line']}")

    if n_holes > 0:
        print(f"\nMatrix holes without reviewer coverage:")
        for c in result["matrix_uncovered"][:15]:
            print(f"  - ({c['state']}, {c['event']}): {c['disposition']}")
        if n_holes > 15:
            print(f"  ... and {n_holes - 15} more")

    return 0 if n_unmatched == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
