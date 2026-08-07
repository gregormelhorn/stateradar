#!/usr/bin/env python3
"""Generate analysis.json sidecars from disposition matrices.

Parses each <analysis-root>/<component>/disposition-matrix.md into the
pack sidecar format (formats/analysis.schema.json) so dsc_check.py can
verify grid totality, DR links, citations, diagram sync, and manifest
staleness. The sidecar is mechanical from the matrix — never hand-edit
it; fix the matrix and regenerate.

Matrix shapes handled (dobby session, 2026-08-05):
- single-table and multi-table matrices (wide event sets split across
  sub-tables, each with its own header row)
- compound row labels ('**fam** leaf' → state "fam leaf"; transition
  targets resolve against the full state list, two-pass)
- hole cells carry '→ Q-nn' for BOTH hole classes (UNSPECIFIED and
  ignore (accidental)); the q ref is extracted from either
- question statuses map DECIDED → RESOLVED (checker vocabulary)

Per-project overlay (optional): <analysis-root>/sidecar-overlay.yaml

  skip:
    appliance-client: "matrix is abridged — pilot work, no grid"
  question_aliases:
    Q-C1: {canonical: Q-Q1, status: "RESOLVED via DR-009"}
  extra_citations:
    - {component: stream-tracker, state: none, event: S2,
       file: src/escape_monitor/server/ingest/streams.py, line: 186,
       fragment: StaleEpochError}

Usage: python3 tools/gen_analysis_sidecar.py [--root REPO] [component ...]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


SRC_ROOTS = ["src", "lib", "app", "pkg", "internal"]
SRC_EXTS = [".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt",
            ".rb", ".cs", ".swift", ".c", ".h", ".cc", ".cpp", ".hpp", ".m"]
SKIP_DIRS = {".git", "node_modules", "dist", "build", "target", "vendor",
             "__pycache__", ".venv", "venv"}


def _src_index(root: Path, overlay: dict) -> dict[str, str]:
    """Basename → repo-relative path for every source file (best effort).

    The pack claims any implementation language works, so the index must
    not be Python-and-src/-only: a missed file silently drops the cell's
    citation, and the cell then fails the 'needs a DR or a citation'
    check with a misleading message.  Roots and extensions are
    overridable per project (sidecar-overlay.yaml: src_roots, src_exts).
    """
    index: dict[str, str] = {}
    roots = overlay.get("src_roots") or SRC_ROOTS
    exts = tuple(overlay.get("src_exts") or SRC_EXTS)
    # When no standard source roots exist (repo with files at top level),
    # fall back to the root directory so citations resolve instead of
    # silently dropping (pladaria/reconnecting-websocket, 2026-08-06).
    bases = [root / r for r in roots if (root / r).is_dir()]
    if not bases:
        bases = [root]
    for base in bases:
        for dirpath, dirnames, files in os.walk(base):
            dirnames[:] = [d for d in dirnames
                           if d not in SKIP_DIRS and not d.startswith(".")]
            for f in files:
                if f.endswith(exts):
                    index.setdefault(f, str(Path(dirpath, f).relative_to(root)))
    return index


def _strip_markdown(text: str) -> str:
    """Strip inline markdown formatting from cell text.

    Bold markers (**reject**) broke startswith("reject") checks;
    inline code and links also interfere with disposition parsing.
    """
    # Bold/italic: **text**, *text*, ***text***
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    # Inline code: `text`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Links: [text](url) — keep the text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    return text.strip()


def _parse_event_annotations(cat_path: Path) -> dict[str, dict]:
    """Parse the '## Event annotations' section of event-catalogue.md.

    Per-event block::

        ### <event-id>
        - gate: <free text>
        - upstream_guards: <comma-separated list>
        - coverage:
          - <category>: <value or 'n/a: reason'>

    Returns {event_id: {"gate": str|None, "upstream_guards": [...],
    "coverage": {category: value}}}.  Missing file or section -> {}.
    The catalogue is the authoring surface for these annotations; the
    sidecar is generated from it (v1.48 — replaces the runner-side
    backfill that hollowed the drift check in v1.47)."""
    if not cat_path.is_file():
        return {}
    text = cat_path.read_text(encoding="utf-8")
    m = re.search(r"^## Event annotations\s*$", text, re.M)
    if not m:
        return {}
    body = text[m.end():]
    nxt = re.search(r"^## ", body, re.M)
    if nxt:
        body = body[: nxt.start()]
    out: dict[str, dict] = {}
    cur: dict | None = None
    in_cov = False
    for line in body.splitlines():
        h = re.match(r"^### (\S+)", line)
        if h:
            cur = out.setdefault(
                h.group(1),
                {"gate": None, "upstream_guards": [], "coverage": {}})
            in_cov = False
            continue
        if cur is None:
            continue
        mg = re.match(r"^- gate:\s*(.+)$", line)
        if mg:
            cur["gate"] = mg.group(1).strip()
            in_cov = False
            continue
        mu = re.match(r"^- upstream_guards:\s*(.+)$", line)
        if mu:
            cur["upstream_guards"] = [
                p.strip() for p in mu.group(1).split(",") if p.strip()]
            in_cov = False
            continue
        if re.match(r"^- coverage:\s*$", line):
            in_cov = True
            continue
        mc = re.match(r"^\s+- ([A-Za-z-]+):\s*(.+)$", line)
        if in_cov and mc:
            cur["coverage"][mc.group(1).strip()] = mc.group(2).strip()
            continue
        if line.strip() and not line.startswith((" ", "\t")):
            in_cov = False
    return out


def _parse_events(header: str) -> list[dict]:
    """Header row cells after the first: 'P1 `put`' / 'UV-P1 `duplicate`'."""
    events = []
    for cell in header.strip().strip("|").split("|")[1:]:
        token = cell.strip().split()[0] if cell.strip() else ""
        if not token:
            continue
        events.append({"id": token, "undesired": token.startswith("UV-")})
    return events


def _parse_cell(
    text: str,
    family: str | None,
    states: list[str],
    src_index: dict[str, str],
) -> dict:
    """One matrix cell → sidecar cell."""
    raw = _strip_markdown(text.strip())
    cell: dict = {}
    q = re.search(r"Q-[\w-]+", raw)
    dr = re.search(r"DR-\d+", raw)

    if "UNSPECIFIED" in raw:
        cell["disposition"] = "UNSPECIFIED"
        if q:
            cell["q"] = q.group(0)
    elif raw.startswith("transition"):
        cell["disposition"] = "transition"
        m = re.search(r"→\s*`?([A-Za-z_][\w-]*)", raw)
        if m:
            target = m.group(1)
            if target in states:
                cell["target"] = target
            elif family and f"{family} {target}" in states:
                cell["target"] = f"{family} {target}"
            else:
                cell["target"] = target  # the checker flags invalid targets
    elif raw.startswith("handle"):
        cell["disposition"] = "handle"
    elif raw.startswith("reject") or raw.startswith("`reject"):
        cell["disposition"] = "reject"
    elif raw.startswith("defer"):
        cell["disposition"] = "defer (queued)"
    elif raw.startswith("ignore"):
        cell["disposition"] = (
            "ignore (accidental)" if "accidental" in raw else "ignore (documented)"
        )
        if "accidental" in raw and q:
            cell["q"] = q.group(0)
    else:
        cell["disposition"] = "UNSPECIFIED"
        if q:
            cell["q"] = q.group(0)

    if dr:
        cell["dr"] = dr.group(0)
    cit = re.search(r"([\w./-]+\.[A-Za-z]{1,4}):(\d+)", raw)
    if cit:
        path = src_index.get(Path(cit.group(1)).name)
        if path:
            cell["citation"] = {"file": path, "line": int(cit.group(2))}
    return cell


def _parse_doc_map(path: Path) -> list[dict]:
    """PA-22 doctrine mapping: parse the machine-readable table under
    '## Doctrine mapping' in invariants-and-lints.md into sidecar
    docLines. Row format: | DOC-n | cell/invariant/constraint/rejected
    | target |. Declarations, never prose (02-pilot v1.4 rule)."""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    if "## Doctrine mapping" not in text:
        return []
    block = text.split("## Doctrine mapping")[1].split("\n## ")[0]
    rows = []
    for line in block.split("\n"):
        s = line.strip()
        if not s.startswith("| DOC-"):
            continue
        cells = [c.strip() for c in s.split("|")[1:-1]]
        if len(cells) >= 3:
            rows.append({"id": cells[0], "mapping": cells[1],
                         "target": cells[2]})
    return rows


def _parse_questions(path: Path) -> list[dict]:
    """open-questions.md → [{id, status}] pairs (DECIDED → RESOLVED)."""
    if not path.is_file():
        return []
    questions = []
    current: dict | None = None
    for line in path.read_text().split("\n"):
        m = re.match(r"^(Q-[\w-]+)", line.strip())
        if m:
            current = {"id": m.group(1), "status": "OPEN"}
            questions.append(current)
        s = re.search(r"\*\*Status:\*\*\s*(.+)", line)
        if s and current is not None:
            status = s.group(1).strip()
            if status.startswith("DECIDED"):
                status = "RESOLVED" + status[len("DECIDED"):]
            current["status"] = status
    return questions


def _load_overlay(analysis_root: Path) -> dict:
    """sidecar-overlay.yaml — skip list, question aliases, citations."""
    empty = {"skip": {}, "question_aliases": {}, "extra_citations": [],
             "src_roots": [], "src_exts": []}
    path = analysis_root / "sidecar-overlay.yaml"
    if not path.is_file():
        return empty
    try:
        import yaml

        data = yaml.safe_load(path.read_text()) or {}
    except ImportError:
        print("note: pyyaml missing — overlay ignored", file=sys.stderr)
        return empty
    return {
        "skip": data.get("skip") or {},
        "question_aliases": data.get("question_aliases") or {},
        "extra_citations": data.get("extra_citations") or [],
        "src_roots": data.get("src_roots") or [],
        "src_exts": data.get("src_exts") or [],
    }


def generate(component: str, analysis_root: Path, src_index: dict[str, str], overlay: dict) -> dict | None:
    """Build the sidecar for one component (None when skipped)."""
    adir = analysis_root / component
    matrix_path = adir / "disposition-matrix.md"
    if not matrix_path.is_file():
        return None
    text = matrix_path.read_text()
    if "<!-- states:" not in text:
        raise ValueError(f"{component}: no states declaration comment")

    # Tables: a header line (first cell contains "state", no ** or ---)
    # opens a block; "| **" rows belong to the current block.
    blocks: list[tuple[list[dict], list[str]]] = []
    for ln in text.split("\n"):
        s = ln.strip()
        if (
            s.startswith("|")
            and "**" not in s
            and "---" not in s
            and "state" in s.split("|")[1].lower()
        ):
            blocks.append((_parse_events(s), []))
        elif s.startswith("| **") and blocks:
            blocks[-1][1].append(s)

    events: list[dict] = []
    seen_events: set[str] = set()
    for block_events, _ in blocks:
        for event in block_events:
            if event["id"] not in seen_events:
                events.append(event)
                seen_events.add(event["id"])

    # Two passes: collect every state first (transition targets resolve
    # against the full list), then parse the cells.
    states: list[str] = []
    row_index: list[tuple[list[dict], str, str, str | None]] = []
    for block_events, block_rows in blocks:
        for row in block_rows:
            label = row.strip().strip("|").split("|")[0].strip()
            # Accept any text between ** markers as the state name, then
            # strip the markers to get plain text.  Previous regex
            # (\w[\w-]*) rejected dots, spaces, and compound names.
            m = re.match(r"\*\*(.+?)\*\*\s*(.*)", label)
            if not m:
                raise ValueError(f"{component}: bad row label {label!r}")
            fam, leaf = m.group(1), m.group(2).strip()
            state = f"{fam} {leaf}" if leaf else fam
            if state not in states:
                states.append(state)
            row_index.append((block_events, row, state, fam if leaf else None))

    cells: list[dict] = []
    for block_events, row, state, family in row_index:
        parts = row.strip().strip("|").split("|")[1:]
        for event, cell_text in zip(block_events, parts, strict=True):
            cell = _parse_cell(cell_text, family, states, src_index)
            cell["state"] = state
            cell["event"] = event["id"]
            cells.append(cell)

    # PA-18 terminal states: <!-- terminal: A, B, C --> auto-generates
    # ignore (documented) cells for every event, eliminating repetitive
    # rows (cenkalti/backoff 2026-08-06: 5 states × 14 events = 70 cells).
    tm = re.search(r"<!--\s*terminal:\s*(.+?) -->", text)
    terminal_states: list[str] = []
    if tm:
        terminal_states = [s.strip() for s in tm.group(1).split(",")]
        for ts in terminal_states:
            if ts not in states:
                states.append(ts)
        # Add cells for terminal states that don't already have rows
        existing = {(c["state"], c["event"]) for c in cells}
        default_cit = {"citation": {"file": "disposition-matrix.md",
                        "line": 0, "fragment": "terminal state declaration"}}
        for ts in terminal_states:
            for ev in events:
                if (ts, ev["id"]) not in existing:
                    cells.append({"state": ts, "event": ev["id"],
                                  "disposition": "ignore (documented)",
                                  **default_cit})

    # Overlay citations for cells whose matrix text carries neither.
    for cell in cells:
        if (
            cell["disposition"] in {"ignore (documented)", "reject", "defer (queued)"}
            and not cell.get("dr")
            and not cell.get("citation")
        ):
            for extra in overlay["extra_citations"]:
                if (
                    extra.get("component") == component
                    and extra.get("state") == cell["state"]
                    and extra.get("event") == cell["event"]
                ):
                    cell["citation"] = {
                        k: v for k, v in extra.items() if k in ("file", "line", "fragment")
                    }

    doc_lines = _parse_doc_map(adir / "invariants-and-lints.md")

    questions = _parse_questions(adir / "open-questions.md")
    known = {q["id"] for q in questions}
    for cell in cells:
        qid = cell.get("q")
        if qid and qid not in known:
            alias = overlay["question_aliases"].get(qid) or {}
            entry = {"id": qid, "status": alias.get("status", "OPEN")}
            if alias.get("canonical"):
                entry["note"] = f"consolidated under {alias['canonical']}"
            questions.append(entry)
            known.add(qid)

    manifest_path = adir / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
    watch = manifest.get("watchPaths") or manifest.get("watch_paths") or []
    cited_drs = sorted({c["dr"] for c in cells if c.get("dr")})

    # Catalogue annotations (gate / upstream_guards / UV coverage) carry
    # through from event-catalogue.md — the catalogue is the source, the
    # sidecar stays generated.
    annotations = _parse_event_annotations(adir / "event-catalogue.md")
    for ev in events:
        ann = annotations.get(ev["id"])
        if not ann:
            continue
        if ann.get("gate") is not None:
            ev["gate"] = ann["gate"]
        if ann.get("upstream_guards"):
            ev["upstream_guards"] = ann["upstream_guards"]
    catalogue_coverage = {
        eid: ann["coverage"] for eid, ann in annotations.items()
        if ann.get("coverage")}

    data = {
        "formatVersion": "1.0",
        "component": component,
        "packVersion": str(manifest.get("pack_version", "")),
        "analyzedSha": manifest.get("analyzedSha", "WORKTREE"),
        "watchPaths": watch,
        "states": states,
        "events": events,
        "cells": cells,
        "questions": questions,
        "behaviouralDrs": cited_drs,
    }
    if doc_lines:
        data["docLines"] = doc_lines

    # The matrix does not carry pairs, guard outcomes, or the coverage
    # table — they live in adversarial-traces.md, guard-results.txt, and
    # event-catalogue.md.  Omitting them silently would let a generated
    # sidecar pass those checks by construction, so declare the absence
    # instead: dsc_check demands a stated reason for every empty section.
    absent = ("the sidecar generator derives cells from disposition-matrix.md "
              "only; this section is not in the matrix. Merge it from {src} "
              "before the component claims L4.")
    data["completeness"] = {
        "pairs": {"count": 0, "reason": absent.format(src="adversarial-traces.md")},
        "guardGroups": {"count": 0, "reason": absent.format(src="guard-results.txt")},
        "coverage": {"count": 0, "reason": absent.format(src="event-catalogue.md")},
    }
    if catalogue_coverage:
        data["coverage"] = catalogue_coverage
        data["completeness"].pop("coverage", None)

    # A hand-merged sidecar keeps its real sections: never regress one to
    # an absence assertion just because this run could not derive it.
    out = adir / "analysis.json"
    if out.is_file():
        try:
            prior = json.loads(out.read_text())
        except json.JSONDecodeError:
            prior = {}
        for section in ("pairs", "guardGroups", "coverage"):
            if prior.get(section) and not data.get(section):
                data[section] = prior[section]
                data["completeness"].pop(section, None)
        if not data["completeness"]:
            data.pop("completeness")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("components", nargs="*")
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--analysis-dir",
        default="domain-analysis",
        help="analysis root relative to --root (default: domain-analysis)",
    )
    args = parser.parse_args()

    # Positional path form: accept the analysis directory itself, as dsc_check
    # does. A directory containing disposition-matrix.md overrides name-based
    # discovery. Paths and names cannot safely share one invocation.
    path_args = [
        Path(component) for component in args.components
        if Path(component).is_dir()
        and (Path(component) / "disposition-matrix.md").is_file()
    ]
    if path_args:
        if len(path_args) != len(args.components):
            print("error: mixing analysis-dir paths and component names — "
                  "pass either paths or names, not both")
            return 2
        parents = {path.resolve().parent for path in path_args}
        if len(parents) != 1:
            print("error: analysis-dir paths must share one parent "
                  "(the analysis root)")
            return 2
        analysis_root = parents.pop()
        root = analysis_root.parent
        args.components = [path.resolve().name for path in path_args]
    else:
        root = Path(args.root).resolve()
        analysis_root = root / args.analysis_dir
    overlay = _load_overlay(analysis_root)
    src_index = _src_index(root, overlay)

    wanted = args.components or [
        d
        for d in sorted(os.listdir(analysis_root))
        if (analysis_root / d).is_dir() and d != "decisions"
    ]
    for component in wanted:
        if component in overlay["skip"]:
            print(f"SKIP {component}: {overlay['skip'][component]}")
            continue
        data = generate(component, analysis_root, src_index, overlay)
        if data is None:
            print(f"SKIP {component}: no disposition matrix")
            continue
        out = analysis_root / component / "analysis.json"
        out.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
        print(
            f"OK {component}: {len(data['states'])} states x "
            f"{len(data['events'])} events = {len(data['cells'])} cells, "
            f"{len(data['questions'])} questions, DRs {data['behaviouralDrs']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
