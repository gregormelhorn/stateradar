#!/usr/bin/env python3
"""Blind pass automation — assemble, dispatch, and diff in one tool.

Usage:
  # Step 1: assemble blind inputs and print dispatch instructions
  python3 tools/dsc_blind.py <analysis-dir> --dispatch [--repo .]

  # Step 2: after the blind pass runs, diff its output against the matrix
  python3 tools/dsc_blind.py <analysis-dir> --diff blind_output.md [--repo .]

The blind pass is the strongest cheap trust signal in the method. Making
it a one-command operation removes the manual assembly/diff friction that
kept it as a "special occasion" step in early pilots (dobby, 2026-08-05;
reconnecting-websocket, 2026-08-06).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional


# ── Dispatch assembly (reuses part_b_pack logic) ──────────────────────

# Minimum input size to catch placeholder-payload dispatches.
MIN_INPUT_CHARS = 200


def _catalogue_ids(catalogue: str) -> list[str]:
    """Event ids from the declaration comment."""
    m = re.search(r"<!-- event-ids: (.+?) -->", catalogue)
    return [e.strip() for e in m.group(1).split(",")] if m else []


def _pair_orderings(catalogue: str) -> list[str]:
    """Pair ordering ids from the catalogue's pairs table."""
    ids: list[str] = []
    for m in re.finditer(r"\|\s*(P-\d+[ab])\b", catalogue):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    return ids


def _blind_instruction() -> str:
    """The canonical blind-pass instruction from 02-pilot.md."""
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "02-pilot.md"
    text = prompt_path.read_text(encoding="utf-8")
    # Extract the Part B dispatch block
    m = re.search(
        r"> Here is the event catalogue.*?(?=\n\nThen diff its table)",
        text, re.DOTALL,
    )
    if m:
        return m.group(0).strip()
    return ""


def assemble(analysis_dir: Path) -> str:
    """Build the blind-pass dispatch prompt from the three canonical inputs.

    Input 1: event-catalogue.md (verbatim).
    Input 2: README.md (prose requirements, from repo root).
    Input 3: event contracts (normative text from the catalogue's event
             descriptions — the gate annotations, remembrance semantics,
             and payload descriptions are the contract text).
    """
    catalogue_path = analysis_dir / "event-catalogue.md"
    if not catalogue_path.is_file():
        sys.exit(f"no event catalogue at {catalogue_path}")

    catalogue = catalogue_path.read_text(encoding="utf-8")
    instruction = _blind_instruction()

    # Requirements: try README.md at repo root, then requirements doc in analysis dir
    repo_root = analysis_dir.parent.parent  # domain-analysis/<component> → repo root
    readme_path = repo_root / "README.md"
    requirements = ""
    if readme_path.is_file():
        requirements = readme_path.read_text(encoding="utf-8")
    else:
        # Try requirements file referenced in extraction
        req_path = analysis_dir / "requirements.md"
        if req_path.is_file():
            requirements = req_path.read_text(encoding="utf-8")

    # Contracts: the gate-type annotations and remembrance semantics sections
    # from the catalogue serve as the normative event contract text.
    contracts = catalogue  # The catalogue IS the contract text for blind pass

    parts = [
        instruction,
        "\n\n---\n\n## INPUT 1: EVENT CATALOGUE\n\n",
        catalogue,
        "\n\n---\n\n## INPUT 2: PROSE REQUIREMENTS\n\n",
        requirements or "(no requirements document found)",
        "\n\n---\n\n## INPUT 3: EVENT CONTRACTS\n\n",
        contracts,
    ]

    prompt = "".join(parts)
    if len(prompt) < MIN_INPUT_CHARS:
        sys.exit(
            f"assembled prompt is only {len(prompt)} chars — "
            "this is the placeholder-payload failure mode. "
            "Check that the catalogue and requirements exist."
        )
    return prompt


# ── Blind output validation ───────────────────────────────────────────

def _normalize_id(eid: str) -> str:
    """Normalize event ids so blind passes using dashes (ws-open) match
    catalogue declarations using dots (ws.open) and vice versa."""
    return eid.strip().replace("-", ".").lower()


def _check_coverage(catalogue_ids: list[str], pair_ids: list[str],
                    blind_text: str) -> list[str]:
    """Verify catalogue event ids appear in blind table HEADERS.

    Only scans column headers, not cell body text (where words like
    'close' appear in transition descriptions). UV and pair ids are
    reported as warnings since blind passes without code access may
    not model them."""
    errors: list[str] = []
    # Extract header rows only (rows where first column is "state" or "State")
    headers: list[str] = []
    in_table = False
    for line in blind_text.split("\n"):
        s = line.strip()
        if s.startswith("|") and "---" not in s:
            first_cell = s.strip("|").split("|")[0].strip().lower()
            if "state" in first_cell:
                headers.append(s)
    header_text = _normalize_id("\n".join(headers))

    # Check main event ids (not UVs, not pairs — those are optional for blind pass)
    main_ids = [e for e in catalogue_ids
                if not e.startswith(("uv-", "UV-"))]
    for eid in main_ids:
        if _normalize_id(eid) not in header_text:
            errors.append(f"missing event column: {eid}")

    # Warn (don't fail) for missing UVs and pairs
    for eid in catalogue_ids:
        if eid.startswith(("uv-", "UV-")) and _normalize_id(eid) not in header_text:
            errors.append(f"warning: UV column not in blind table: {eid}")
    for pid in pair_ids:
        if _normalize_id(pid) not in header_text:
            errors.append(f"warning: pair column not in blind table: {pid}")

    return errors


def _extract_table_rows(text: str) -> str:
    """Extract table body rows (skip headers and separators)."""
    lines = []
    in_table = False
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("|") and "---" not in s:
            if not in_table:
                in_table = True
                continue  # skip header
            lines.append(s)
        elif in_table and not s.startswith("|"):
            in_table = False
    return "\n".join(lines)


# ── Diff against matrix ───────────────────────────────────────────────

def _parse_blind_disposition(cell_text: str) -> str:
    """Extract disposition from a blind-pass cell.

    Blind pass uses the same vocabulary: transition → T, handle, ignore
    (documented), ignore (accidental), defer (queued), reject, UNSPECIFIED.
    """
    t = cell_text.strip().lower()
    if t.startswith("transition"):
        return "transition"
    if "unspecified" in t:
        return "UNSPECIFIED"
    if "ignore (accidental)" in t:
        return "ignore (accidental)"
    if "ignore (documented)" in t or t.startswith("ignore"):
        return "ignore (documented)"
    if "defer" in t:
        return "defer (queued)"
    if "reject" in t:
        return "reject"
    if "handle" in t:
        return "handle"
    return "UNSPECIFIED"


def diff_blind(analysis_dir: Path, blind_path: Path) -> dict:
    """Diff blind output against the matrix sidecar.

    Returns counts: convergent, convergent_hole, divergence, artefact,
    blind_spot, total.
    """
    sidecar_path = analysis_dir / "analysis.json"
    if not sidecar_path.is_file():
        sys.exit(f"no analysis.json at {sidecar_path} — run gen_analysis_sidecar first")

    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    blind_text = blind_path.read_text(encoding="utf-8")

    cells = sidecar.get("cells", [])
    counts = {
        "convergent": 0, "convergent_hole": 0, "divergence": 0,
        "artefact": 0, "blind_spot": 0, "total": len(cells),
    }

    # Build a lookup from the blind table: (state, event) → disposition
    blind_lookup: dict[tuple[str, str], str] = {}
    blind_rows = _extract_table_rows(blind_text).split("\n")
    for row in blind_rows:
        parts = [p.strip() for p in row.strip("|").split("|")]
        if len(parts) < 2:
            continue
        blind_state = _strip_markdown(parts[0])
        # Header detection: first column has "state" → skip
        if "state" in blind_state.lower():
            continue
        for i, cell in enumerate(parts[1:], 1):
            if i <= len(sidecar.get("events", [])):
                event_id = sidecar["events"][i - 1]["id"]
                blind_lookup[(blind_state, _normalize_id(event_id))] = _parse_blind_disposition(cell)

    for cell in cells:
        key = (cell["state"], _normalize_id(cell["event"]))
        blind_disp = blind_lookup.get(key)
        matrix_disp = cell["disposition"]

        if blind_disp is None:
            counts["blind_spot"] += 1
        elif blind_disp == matrix_disp:
            counts["convergent"] += 1
        elif blind_disp == "UNSPECIFIED" and matrix_disp == "UNSPECIFIED":
            counts["convergent_hole"] += 1
        elif blind_disp == "ignore (accidental)" and matrix_disp == "ignore (accidental)":
            counts["convergent_hole"] += 1
        else:
            counts["divergence"] += 1

    return counts


def _strip_markdown(text: str) -> str:
    """Strip inline markdown, same as gen_analysis_sidecar."""
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return text.strip()


# ── CLI ───────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description="Part-B blind pass automation")
    p.add_argument("analysis_dir", help="path to domain-analysis/<component>/")
    p.add_argument("--dispatch", action="store_true",
                   help="assemble and print dispatch prompt for the blind pass")
    p.add_argument("--diff", metavar="BLIND_OUTPUT",
                   help="diff a blind output file against the matrix sidecar")
    p.add_argument("--repo", default=".",
                   help="repository root (for README resolution)")
    p.add_argument("--out", default=None,
                   help="write dispatch prompt to file instead of stdout")
    args = p.parse_args()

    adir = Path(args.analysis_dir).resolve()

    if args.dispatch:
        prompt = assemble(adir)
        if args.out:
            Path(args.out).write_text(prompt, encoding="utf-8")
            print(f"dispatch prompt written to {args.out}")
            print(f"({len(prompt)} chars)")
        else:
            print(prompt)
        return 0

    if args.diff:
        blind_path = Path(args.diff)
        if not blind_path.is_file():
            sys.exit(f"blind output file not found: {blind_path}")

        # Validate coverage
        catalogue_path = adir / "event-catalogue.md"
        if catalogue_path.is_file():
            catalogue = catalogue_path.read_text(encoding="utf-8")
            cat_ids = _catalogue_ids(catalogue)
            pair_ids = _pair_orderings(catalogue)
            errors = _check_coverage(cat_ids, pair_ids,
                                     blind_path.read_text(encoding="utf-8"))
            if errors:
                fatals = [e for e in errors if not e.startswith("warning:")]
                if fatals:
                    print("BLIND COVERAGE: FAIL")
                    for e in fatals:
                        print(f"  - {e}")
                    return 1
                print("BLIND COVERAGE: OK (with warnings)")
                for e in errors:
                    if e.startswith("warning:"):
                        print(f"  - {e}")
            else:
                print(f"BLIND COVERAGE: OK ({len(cat_ids)} events, {len(pair_ids)} pairs)")

        # Diff
        counts = diff_blind(adir, blind_path)
        total = counts["total"]
        print(
            f"\nBLIND DIFF: {total} cells — "
            f"{counts['convergent']} convergent ({_pct(counts['convergent'], total)}), "
            f"{counts['convergent_hole']} convergent-hole ({_pct(counts['convergent_hole'], total)}), "
            f"{counts['divergence']} divergence ({_pct(counts['divergence'], total)}), "
            f"{counts['blind_spot']} blind-spot ({_pct(counts['blind_spot'], total)})"
        )
        if counts["divergence"] > total * 0.3:
            print("\n⚠  high divergence rate — catalogue or requirements may be underspecified")
        if counts["convergent"] > total * 0.4:
            print("✓  strong convergence — behaviour independently derivable from requirements")
        return 0

    p.print_help()
    return 1


def _pct(n: int, total: int) -> str:
    return f"{n / total * 100:.0f}%" if total else "0%"


if __name__ == "__main__":
    sys.exit(main())
