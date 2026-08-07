#!/usr/bin/env python3
"""Ensemble convergence — multi-run matrix diff and mechanical question generation.

Takes N analysis.json sidecars from independent pilot runs, aligns
states and events, computes cell-level convergence, and mechanically
marks divergent cells as UNSPECIFIED → Q.

Core idea (roadmap §5): intersection = high confidence, symmetric
difference = automatic question candidates. The CONVERGENCE protocol
only *measured* divergence; this tool *uses* it.

Usage:
  # Diff two runs, emit merged analysis + report to stdout
  python3 tools/ensemble_convergence.py run1/analysis.json run2/analysis.json

  # Diff three runs, write merged sidecar to a file
  python3 tools/ensemble_convergence.py r1/a.json r2/a.json r3/a.json -o merged.json

  # Also write the convergence report to a markdown file
  python3 tools/ensemble_convergence.py r1/a.json r2/a.json --report report.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# State-name normalization
# ---------------------------------------------------------------------------

def _normalize_state(name: str) -> str:
    """Normalize a state name for cross-run alignment.

    Rules (per PA-17: PascalCase segments or ALLCAPS API enums):
    - lowercase and strip whitespace
    - strip trailing qualifiers like _AttemptInFlight, _Attempting, _BackingOff, _Backoff
    - map known ALLCAPS → PascalCase pairs
    """
    name = name.strip().lower()
    # Strip common derivation suffixes that encode the same semantic state
    for suffix in (
        "_attemptinflight", "_attempting", "_noattempt",
        "_backingoff", "_backoff",
        "_retriesexhausted", "_exhausted",
        "_idle",
    ):
        if name.endswith(suffix):
            base = name[:-len(suffix)]
            if base:  # don't reduce to empty
                return base
    return name


def _align_states(all_state_lists: list[list[str]]) -> dict[str, list[str]]:
    """Build a mapping from canonical state name to per-run state names.

    Returns {canonical: [run0_name_or_None, run1_name_or_None, ...]}.
    Runs that don't have this state get None.
    """
    n_runs = len(all_state_lists)
    # Collect all normalized forms
    norm_to_originals: dict[str, list[Optional[str]]] = defaultdict(
        lambda: [None] * n_runs
    )
    for run_idx, states in enumerate(all_state_lists):
        for s in states:
            norm = _normalize_state(s)
            norm_to_originals[norm][run_idx] = s

    return dict(norm_to_originals)


# ---------------------------------------------------------------------------
# Event alignment
# ---------------------------------------------------------------------------

def _align_events(all_event_lists: list[list[dict]]) -> tuple[
    list[str],                       # canonical event ids (ordered)
    dict[str, list[Optional[str]]],  # canonical → per-run event id or None
]:
    """Align event IDs across runs.

    Events are matched by ID. Returns the union of all event IDs and
    per-run presence.
    """
    all_ids: set[str] = set()
    for events in all_event_lists:
        for e in events:
            all_ids.add(e["id"])

    canonical_ids = sorted(all_ids)
    presence: dict[str, list[Optional[str]]] = {}
    for cid in canonical_ids:
        row = [None] * len(all_event_lists)
        for run_idx, events in enumerate(all_event_lists):
            for e in events:
                if e["id"] == cid:
                    row[run_idx] = cid
                    break
        presence[cid] = row

    return canonical_ids, presence


# ---------------------------------------------------------------------------
# Cell loading and indexing
# ---------------------------------------------------------------------------

def _load_cells_index(analysis_path: Path) -> dict[tuple[str, str], dict]:
    """Load cells from one analysis.json, indexed by (state_name, event_id)."""
    data = json.loads(analysis_path.read_text(encoding="utf-8"))
    cells = data.get("cells", [])
    index: dict[tuple[str, str], dict] = {}
    for cell in cells:
        key = (cell["state"], cell["event"])
        index[key] = cell
    return index


# ---------------------------------------------------------------------------
# Cell-level diff
# ---------------------------------------------------------------------------

def _cell_fingerprint(cell: dict | None) -> Optional[str]:
    """Return a stable fingerprint for a cell's behavioural content.

    The fingerprint captures disposition + target (if transition).
    Citations, Q-refs, and DR-refs are stripped — they differ between runs
    but don't indicate behavioural divergence.
    """
    if cell is None:
        return None
    disp = cell.get("disposition", "")
    if disp == "transition":
        return f"{disp}→{cell.get('target', '?')}"
    return disp


def _divergence_class(
    fingerprints: list[Optional[str]],
) -> str:
    """Classify the divergence pattern across runs.

    Returns one of:
    - convergent: all runs agree
    - disposition-divergent: same cell, different dispositions
    - target-divergent: all transition, different targets
    - presence-divergent: cell exists in some runs but not others
    - noise: all UNSPECIFIED / ignore(accidental) but different Q-ids (not
      behavioural divergence — the holes are already caught)
    """
    # Filter out None (absent runs)
    present = [fp for fp in fingerprints if fp is not None]
    if not present:
        return "all-absent"  # shouldn't happen for aligned cells

    if len(set(present)) == 1:
        return "convergent"

    # Check if all present are hole-class dispositions
    hole_disps = {"UNSPECIFIED", "ignore (accidental)"}
    if all(fp in hole_disps for fp in present):
        return "hole-noise"

    # Check if all are transitions but with different targets
    if all(fp.startswith("transition→") for fp in present):
        return "target-divergent"

    return "disposition-divergent"


# ---------------------------------------------------------------------------
# Merged output
# ---------------------------------------------------------------------------

def _merge_cells(
    canonical_states: dict[str, list[Optional[str]]],
    canonical_events: list[str],
    event_presence: dict[str, list[Optional[str]]],
    cell_indices: list[dict[tuple[str, str], dict]],
    runs_metadata: list[dict],
) -> tuple[list[dict], list[dict], dict]:
    """Merge cells across runs and classify convergence.

    Returns (merged_cells, new_questions, stats).
    """
    n_runs = len(cell_indices)
    merged: list[dict] = []
    questions: list[dict] = []
    q_counter = 1

    stats = {
        "total_aligned_cells": 0,
        "convergent": 0,
        "disposition_divergent": 0,
        "target_divergent": 0,
        "presence_divergent": 0,
        "hole_noise": 0,
        "new_questions": 0,
        "convergence_rate": 0.0,
    }

    for canonical_state, state_names in canonical_states.items():
        for canonical_event in canonical_events:
            # Collect fingerprints and original cells
            fingerprints: list[Optional[str]] = []
            originals: list[Optional[dict]] = []
            for run_idx in range(n_runs):
                run_state = state_names[run_idx]
                run_event = event_presence[canonical_event][run_idx]
                if run_state is None or run_event is None:
                    fingerprints.append(None)
                    originals.append(None)
                else:
                    cell = cell_indices[run_idx].get((run_state, run_event))
                    fingerprints.append(_cell_fingerprint(cell))
                    originals.append(cell)

            d_class = _divergence_class(fingerprints)
            stats["total_aligned_cells"] += 1

            if d_class == "convergent":
                stats["convergent"] += 1
                # Use the first non-None cell as the representative
                for orig in originals:
                    if orig is not None:
                        merged.append(dict(orig))
                        break

            elif d_class == "hole-noise":
                stats["hole_noise"] += 1
                # Already holes in all runs — keep the first one
                for orig in originals:
                    if orig is not None:
                        merged.append(dict(orig))
                        break

            else:
                # Divergent — mechanically mark UNSPECIFIED → Q
                q_id = f"Q-EC-{q_counter:02d}"
                q_counter += 1
                stats["new_questions"] += 1

                if d_class == "disposition-divergent":
                    stats["disposition_divergent"] += 1
                elif d_class == "target-divergent":
                    stats["target_divergent"] += 1
                else:
                    stats["presence_divergent"] += 1

                # Build a descriptive divergence summary
                run_details = []
                for run_idx in range(n_runs):
                    run_label = runs_metadata[run_idx].get("label", f"run-{run_idx + 1}")
                    fp = fingerprints[run_idx]
                    if fp is None:
                        run_details.append(f"{run_label}: absent")
                    else:
                        run_details.append(f"{run_label}: {fp}")

                divergence_detail = "; ".join(run_details)

                # Derive display names from the first run that has this state/event
                display_state = canonical_state
                for sn in state_names:
                    if sn is not None:
                        display_state = sn
                        break
                display_event = canonical_event
                for ep in event_presence.get(canonical_event, [None]):
                    if ep is not None:
                        display_event = ep
                        break

                merged.append({
                    "state": display_state,
                    "event": display_event,
                    "disposition": "UNSPECIFIED",
                    "q": q_id,
                })

                questions.append({
                    "id": q_id,
                    "status": "OPEN",
                    "text": (
                        f"Ensemble divergence at ({canonical_state}, {canonical_event}): "
                        f"{divergence_detail}. "
                        f"Multiple independent pilot runs disagree on the disposition. "
                        f"Human decision required."
                    ),
                })

    # Compute convergence rate over non-hole cells
    behavioural_cells = stats["total_aligned_cells"] - stats["hole_noise"]
    if behavioural_cells > 0:
        convergent_behavioural = stats["convergent"]
        stats["convergence_rate"] = round(
            convergent_behavioural / behavioural_cells * 100, 1
        )
    else:
        stats["convergence_rate"] = 100.0

    return merged, questions, stats


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _render_report(
    stats: dict,
    canonical_states: dict[str, list[Optional[str]]],
    canonical_events: list[str],
    runs_metadata: list[dict],
    merged_cells: list[dict],
    questions: list[dict],
) -> str:
    """Render a markdown convergence report."""
    lines: list[str] = []
    lines.append("# Ensemble Convergence Report")
    lines.append("")

    lines.append("## Runs")
    lines.append("")
    for i, meta in enumerate(runs_metadata):
        label = meta.get("label", f"run-{i + 1}")
        path = meta.get("path", "?")
        lines.append(f"- **{label}:** `{path}`")
    lines.append("")

    lines.append("## State alignment")
    lines.append("")
    lines.append(f"Canonical states: {len(canonical_states)}")
    lines.append("")
    for canonical, per_run in canonical_states.items():
        run_names = [n or "—" for n in per_run]
        lines.append(f"- `{canonical}` ← {', '.join(run_names)}")
    lines.append("")

    lines.append("## Convergence statistics")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Total aligned cells | {stats['total_aligned_cells']} |")
    lines.append(f"| Convergent | {stats['convergent']} |")
    lines.append(f"| Disposition-divergent | {stats['disposition_divergent']} |")
    lines.append(f"| Target-divergent | {stats['target_divergent']} |")
    lines.append(f"| Presence-divergent | {stats['presence_divergent']} |")
    lines.append(f"| Hole noise (non-behavioural) | {stats['hole_noise']} |")
    lines.append(f"| **Behavioural convergence rate** | **{stats['convergence_rate']}%** |")
    lines.append(f"| New questions raised | {stats['new_questions']} |")
    lines.append("")

    if questions:
        lines.append("## Divergent cells → Questions")
        lines.append("")
        for q in questions:
            lines.append(f"### {q['id']}")
            lines.append(f"**Status:** {q['status']}")
            lines.append(f"")
            lines.append(q["text"])
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ensemble convergence — multi-run matrix diff and Q generation."
    )
    parser.add_argument(
        "sidecars",
        nargs="+",
        type=Path,
        help="Two or more analysis.json files from independent pilot runs.",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Write merged analysis.json to this path (default: stdout).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Write convergence report to this markdown file.",
    )
    parser.add_argument(
        "--labels",
        nargs="*",
        help="Labels for each run (positional, one per sidecar).",
    )
    args = parser.parse_args()

    if len(args.sidecars) < 2:
        sys.exit("ensemble_convergence: need at least 2 analysis.json files")

    # Validate all sidecars exist
    for p in args.sidecars:
        if not p.is_file():
            sys.exit(f"not found: {p}")

    # Load all sidecars
    all_data: list[dict] = []
    for p in args.sidecars:
        try:
            all_data.append(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError as e:
            sys.exit(f"invalid JSON in {p}: {e}")

    # Build run metadata
    labels = args.labels or []
    while len(labels) < len(args.sidecars):
        labels.append(f"run-{len(labels) + 1}")

    runs_metadata = [
        {"label": labels[i], "path": str(args.sidecars[i])}
        for i in range(len(args.sidecars))
    ]

    # Extract states and events per run
    all_state_lists = [d.get("states", []) for d in all_data]
    all_event_lists = [d.get("events", []) for d in all_data]

    # Align
    canonical_states = _align_states(all_state_lists)
    canonical_events, event_presence = _align_events(all_event_lists)

    # Load cell indices
    cell_indices = [_load_cells_index(p) for p in args.sidecars]

    # Merge and classify
    merged_cells, questions, stats = _merge_cells(
        canonical_states, canonical_events, event_presence,
        cell_indices, runs_metadata,
    )

    # Build merged analysis.json (clone structure from first run)
    merged = dict(all_data[0])
    merged["states"] = sorted(canonical_states.keys())
    # Union of all events
    all_event_objs: list[dict] = []
    seen_ids: set[str] = set()
    for events in all_event_lists:
        for e in events:
            if e["id"] not in seen_ids:
                seen_ids.add(e["id"])
                all_event_objs.append(dict(e))
    merged["events"] = sorted(all_event_objs, key=lambda e: e["id"])
    merged["cells"] = merged_cells
    # Append ensemble questions
    existing_questions = merged.get("questions", [])
    merged["questions"] = existing_questions + questions
    # Note ensemble provenance
    merged["ensembleConvergence"] = {
        "runs": len(args.sidecars),
        "convergenceRate": stats["convergence_rate"],
        "divergentCells": stats["disposition_divergent"]
        + stats["target_divergent"]
        + stats["presence_divergent"],
        "newQuestions": stats["new_questions"],
    }

    # Output merged analysis
    merged_json = json.dumps(merged, indent=1, ensure_ascii=False)
    if args.output:
        args.output.write_text(merged_json + "\n", encoding="utf-8")
        print(f"Merged analysis written to {args.output}")
    else:
        print(merged_json)

    # Output report
    report = _render_report(
        stats, canonical_states, canonical_events,
        runs_metadata, merged_cells, questions,
    )
    if args.report:
        args.report.write_text(report, encoding="utf-8")
        print(f"Convergence report written to {args.report}")
    else:
        print("\n" + report, file=sys.stderr)

    # Return non-zero if there are divergent cells (for CI gating)
    divergent = (
        stats["disposition_divergent"]
        + stats["target_divergent"]
        + stats["presence_divergent"]
    )
    if divergent > 0:
        print(
            f"⚠ {divergent} divergent cells found — {stats['new_questions']} "
            f"questions raised. Convergence rate: {stats['convergence_rate']}%",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
