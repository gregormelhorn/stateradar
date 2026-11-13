"""Flash drafts disposition-matrix cells; code checks them; Jev judges each one.

Roadmap entry 11 item 2 ("Flash writes, the steering agent decides"). The
steering agent decides the states (with the condition that defines each) and
the events; this module asks DeepSeek Flash for one cited cell per state and
event, checks every cell mechanically (known state and event, closed
disposition vocabulary, transition target among the states, citation fragment
near its line, one cell per pair), sends every citable cell to one Jev batch
as a claim, and renders a matrix block in the 02-pilot cell form plus a review
list. Nothing is accepted automatically: hole cells carry `→ Q-?` and missing
cells `MISSING`, so dsc_check fails until the agent has decided each, and every
Jev answer only orders the agent's re-reading (routing rule 2).
"""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
import argparse
import sys
from typing import Any, NotRequired, TypedDict

import local_models
from local_budget import Budget

ROOT = Path(__file__).resolve().parent.parent
_VOCAB = tomllib.loads((ROOT / "formats" / "rules.toml").read_text(encoding="utf-8"))["vocab"]
DISPOSITIONS = [d.split(" → ")[0] for d in _VOCAB["dispositions"]]  # "transition → <target>" -> "transition"
HOLES = set(_VOCAB["holes"])
EVENTS_PER_TABLE = 8  # the sub-table width the committed matrices use


class CellsState(TypedDict):
    name: str
    condition: str


class CellsEvent(TypedDict):
    id: str
    gist: str


class CellsTask(TypedDict):
    states: list[CellsState]
    events: list[CellsEvent]
    notes: NotRequired[str]


class DraftCell(TypedDict):
    state: str
    event: str
    disposition: str
    target: NotRequired[str]
    line: object
    fragment: object
    note: str
    problems: list[str]
    jev: NotRequired[dict[str, Any]]


CELLS_INSTRUCTIONS = """You draft the as-is disposition matrix of a component for a StateRadar analysis. You propose; you do not decide.

For EVERY state and EVERY event below, write exactly one cell: what the code does when that event occurs in that state.

States (name: the condition that defines it):
{states}

Events (id: gist):
{events}
{notes}
Disposition vocabulary (use exactly one per cell):
- transition (give "target": one of the state names above)
- handle (stays in the state, does something)
- ignore (documented)
- ignore (accidental) (nothing handles it and nothing says it is intended)
- defer (queued)
- reject (a declared refusal signal: error, diagnostic, nack)
- UNSPECIFIED (the outcome depends on timing or is not determined by the code)

Rules:
- Use only the numbered source below. Describe what the code does, not what it should do.
- Each cell cites ONE source line number and a short fragment copied verbatim from that line, for the code that decides the cell.
- "note" says in one short sentence what happens; leave it empty when the disposition says it all.
- Put every gap, contradiction, ambiguity or unspecified behaviour into questions. Do not resolve it.
- Answer with JSON only, no prose, exactly in this shape:
{{"cells": [{{"state": "...", "event": "...", "disposition": "handle", "target": "", "line": 1, "fragment": "...", "note": "..."}}], "questions": ["..."]}}

Source ({source_ref}), one line per number:
{numbered}
"""


def load_task(text: str) -> CellsTask:
    """The agent's decisions: states with their conditions, events with their gists."""
    task = json.loads(text)
    if not isinstance(task, dict):
        raise ValueError("cells task: a JSON object with states and events is required")
    for key, fields in (("states", ("name", "condition")), ("events", ("id", "gist"))):
        items = task.get(key)
        if not isinstance(items, list) or not items:
            raise ValueError(f"cells task: {key} must be a nonempty list")
        names = [item.get(fields[0]) if isinstance(item, dict) else None for item in items]
        if not all(isinstance(item, dict) and all(isinstance(item.get(f), str) and item[f].strip() for f in fields)
                   for item in items):
            raise ValueError(f"cells task: each of {key} needs a nonempty {' and '.join(fields)}")
        if len(set(names)) != len(names):
            raise ValueError(f"cells task: duplicate {fields[0]} in {key}")
        bad = [n for n in names if not re.fullmatch(r"[A-Za-z][\w.-]*", str(n))]
        if bad:
            # A space or a "|" would change the matrix header or row.
            raise ValueError(f"cells task: {fields[0]} must be one word of letters, digits, _, . or -: {bad}")
    if "notes" in task and not isinstance(task["notes"], str):
        raise ValueError("cells task: notes must be a string")
    return task  # type: ignore[return-value]  # shape checked above


def _parse_cells(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    body = text.strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", body, re.S)
    try:
        draft = json.loads(fence.group(1) if fence else body)
    except json.JSONDecodeError as error:
        raise local_models.InvalidDraft(f"not JSON ({error.msg})", text) from error
    if not isinstance(draft, dict) or not isinstance(draft.get("cells"), list):
        raise local_models.InvalidDraft("a cells list is required", text)
    questions = draft.get("questions", [])
    if not isinstance(questions, list) or not all(isinstance(q, str) and q.strip() for q in questions):
        raise local_models.InvalidDraft("a questions list of nonempty strings is required", text)
    if not all(isinstance(cell, dict) for cell in draft["cells"]):
        raise local_models.InvalidDraft("each cell must be an object", text)
    return draft["cells"], questions


def check_cells(task: CellsTask, raw: list[dict[str, Any]], source_lines: list[str]) -> tuple[list[DraftCell], list[str]]:
    """Mechanical checks of each drafted cell; returns the cells and the missing pairs."""
    states = {s["name"] for s in task["states"]}
    events = {e["id"] for e in task["events"]}
    cells: list[DraftCell] = []
    seen: dict[tuple[str, str], int] = {}
    for item in raw:
        state, event = str(item.get("state", "")).strip(), str(item.get("event", "")).strip()
        disposition = str(item.get("disposition", "")).strip()
        target = str(item.get("target") or "").strip()
        note = item.get("note")
        # A note is prose in one table cell: no line break, no cell bar.
        note_text = " ".join(note.split()).replace("|", "/") if isinstance(note, str) else ""
        fragment = item.get("fragment")
        if isinstance(fragment, str) and "|" in fragment:
            # The matrix tools split rows on every "|", escaped or not, so a
            # fragment keeps its longest verbatim piece without one.
            piece = max((part.strip() for part in fragment.split("|")), key=len)
            fragment = piece if len("".join(piece.split())) >= local_models.MIN_FRAGMENT else fragment
        cell: DraftCell = {"state": state, "event": event, "disposition": disposition,
                           "line": item.get("line"), "fragment": fragment, "note": note_text, "problems": []}
        if target:
            cell["target"] = target
        problems = cell["problems"]
        if state not in states:
            problems.append(f"unknown state {state!r}")
        if event not in events:
            problems.append(f"unknown event {event!r}")
        if disposition not in DISPOSITIONS:
            problems.append(f"disposition {disposition!r} is outside the vocabulary")
        elif disposition == "transition" and target not in states:
            problems.append(f"transition target {target!r} is not a state")
        elif disposition != "transition" and target:
            problems.append("only a transition has a target")
        error = local_models._citation_error(source_lines, cell["line"], cell["fragment"])
        if error:
            problems.append(error)
        elif isinstance(cell["fragment"], str) and "|" in cell["fragment"]:
            problems.append('fragment has no verbatim piece without "|" long enough to cite')
        key = (state, event)
        if key in seen:
            problems.append("second cell for this state and event")
            cells[seen[key]]["problems"].append("second cell for this state and event")
        else:
            seen[key] = len(cells)
        cells.append(cell)
    missing = [f"{s['name']} x {e['id']}" for s in task["states"] for e in task["events"]
               if (s["name"], e["id"]) not in seen]
    return cells, missing


def _statement(task: CellsTask, cell: DraftCell) -> str:
    condition = next(s["condition"] for s in task["states"] if s["name"] == cell["state"])
    gist = next(e["gist"] for e in task["events"] if e["id"] == cell["event"])
    outcome = cell["disposition"] + (f" to {cell['target']}" if "target" in cell else "")
    return (f"In state {cell['state']} ({condition}), when {cell['event']} ({gist}) occurs, the code's "
            f"disposition is {outcome}" + (f": {cell['note']}" if cell["note"] else "."))


def _cell_text(cell: DraftCell | None, source_ref: str) -> str:
    if cell is None:
        return "MISSING"
    head = cell["disposition"] + (f" → {cell['target']}" if "target" in cell else "")
    if cell["disposition"] in HOLES or cell["problems"]:
        # A cell with a problem loses its citation; the placeholder keeps the
        # checker red until the agent decides it (a handle or transition
        # without a citation would otherwise pass dsc_check).
        head += " → Q-?"
    citation = f' {source_ref}:{cell["line"]} ("{cell["fragment"]}")' if not cell["problems"] else ""
    note = f" — {cell['note']}" if cell["note"] else ""
    return head + citation + note


def render(task: CellsTask, cells: list[DraftCell], missing: list[str], questions: list[str],
           source_ref: str) -> str:
    """A matrix block in the 02-pilot cell form, then the review list."""
    by_pair = {(c["state"], c["event"]): c for c in cells if not any("second cell" in p for p in c["problems"])}
    name = Path(source_ref).name
    events = [e["id"] for e in task["events"]]
    out = [f"<!-- states: {', '.join(s['name'] for s in task['states'])} -->", "",
           "Drafted by DeepSeek Flash (`draft-cells`); every cell is a proposal until the steering agent "
           "has read its cited line. `→ Q-?` and `MISSING` stay until decided.", ""]
    for start in range(0, len(events), EVENTS_PER_TABLE):
        chunk = events[start:start + EVENTS_PER_TABLE]
        out += [f"### Sub-table {start // EVENTS_PER_TABLE + 1}", "",
                "| State | " + " | ".join(chunk) + " |", "|---|" + "---|" * len(chunk)]
        for state in task["states"]:
            row = [_cell_text(by_pair.get((state["name"], e)), name) for e in chunk]
            out.append(f"| **{state['name']}** | " + " | ".join(row) + " |")
        out.append("")
    review = []
    for c in cells:
        judged = c.get("jev")
        if c["problems"]:
            review.append(f"- {c['state']} x {c['event']}: " + "; ".join(c["problems"]))
        elif judged and judged.get("choice") != "supported":
            review.append(f"- {c['state']} x {c['event']}: jev {judged.get('choice')} "
                          f"(confidence {judged.get('confidence')})")
    review += [f"- {pair}: no cell drafted" for pair in missing]
    out += ["## Review list", "", *(review or ["- none"]), "", "## Draft questions", "",
            *([f"- {q}" for q in questions] or ["- none"]), ""]
    return "\n".join(out)


def draft_cells(budget: Budget, source: str, source_ref: str, task_text: str, flash_key: str, jev_key: str,
                model: str = "jev-latest", max_tokens: int = 16384) -> dict[str, Any]:
    """Draft, check and judge the cells; returns the JSON result (nothing accepted)."""
    task = load_task(task_text)
    source_lines = source.splitlines()
    prompt = CELLS_INSTRUCTIONS.format(
        states="\n".join(f"- {s['name']}: {s['condition']}" for s in task["states"]),
        events="\n".join(f"- {e['id']}: {e['gist']}" for e in task["events"]),
        notes=f"\nNotes from the analysis:\n{task['notes']}\n" if task.get("notes") else "",
        source_ref=source_ref,
        numbered="\n".join(f"{n}: {t}" for n, t in enumerate(source_lines, 1)))
    drafted = local_models.flash(budget, prompt, flash_key, max_tokens)
    raw, questions = _parse_cells(drafted["text"])
    cells, missing = check_cells(task, raw, source_lines)
    citable = [(i, c) for i, c in enumerate(cells) if not c["problems"]]
    verification: dict[str, Any] | None = None
    if citable:
        checks = [{"id": f"cell-{i}", "kind": "claim", "statement": _statement(task, c),
                   "line": c["line"], "fragment": c["fragment"]} for i, c in citable]
        try:
            batch = local_models.jev_batch(budget, source, source_ref, checks, jev_key, model)
        except Exception as error:  # the Flash draft is paid for: keep it (routing rule 8)
            verification = {"error": str(error)}
        else:
            for i, c in citable:
                judged = batch["checks"][f"cell-{i}"]
                c["jev"] = {"choice": judged["choice"], "probabilities": judged["probabilities"],
                            "confidence": judged["confidence"]}
            verification = {"model": batch["model"], "input_tokens": batch["input_tokens"],
                            "cost_microdollars": batch["cost_microdollars"], "error": None}
    return {"source": source_ref, "task": task, "cells": cells, "missing": missing, "questions": questions,
            "draft": {k: v for k, v in drafted.items() if k != "text"}, "verification": verification,
            "matrix": render(task, cells, missing, questions, source_ref), "review_required": True}


def compare(draft: dict[str, Any], sidecar: dict[str, Any]) -> dict[str, Any]:
    """How the agent's final matrix differs from the Flash draft, cell by cell.

    The final cells come from the run's generated analysis.json, so the count
    does not rest on the agent's own report. Each drafted cell is `unchanged`,
    `changed` (with the fields: disposition, target, citation) or `dropped`
    (no final cell for its state and event); counts are split by Jev's choice
    (`not judged` for a cell with a problem or a failed batch). The cell text
    after the citation is not in the sidecar, so a note-only edit is not seen.
    """
    final = {(c["state"], c["event"]): c for c in sidecar["cells"]}
    drafted_pairs = set()
    rows = []
    for cell in draft["cells"]:
        if any("second cell" in p for p in cell["problems"]):
            continue
        key = (cell["state"], cell["event"])
        drafted_pairs.add(key)
        choice = cell.get("jev", {}).get("choice", "not judged")
        end = final.get(key)
        if end is None:
            rows.append({"state": key[0], "event": key[1], "jev": choice, "outcome": "dropped", "fields": []})
            continue
        fields = []
        if end.get("disposition") != cell["disposition"]:
            fields.append("disposition")
        if (end.get("target") or "") != (cell.get("target") or ""):
            fields.append("target")
        cited = end.get("citation") or {}
        if cell["problems"] or cited.get("line") != cell["line"] or cited.get("fragment") != cell["fragment"]:
            fields.append("citation")
        rows.append({"state": key[0], "event": key[1], "jev": choice,
                     "outcome": "changed" if fields else "unchanged", "fields": fields})
    table: dict[str, dict[str, int]] = {}
    for row in rows:
        counts = table.setdefault(row["jev"], {"unchanged": 0, "changed": 0, "dropped": 0})
        counts[row["outcome"]] += 1
    fields_count: dict[str, int] = {}
    for row in rows:
        for field in row["fields"]:
            fields_count[field] = fields_count.get(field, 0) + 1
    return {"by_jev_choice": table, "changed_fields": fields_count,
            "drafted": len(rows), "missing_in_draft": len(draft["missing"]),
            "second_cells_in_draft": sum(any("second cell" in p for p in c["problems"]) for c in draft["cells"]),
            "final_cells_not_drafted": sorted(f"{s} x {e}" for s, e in final if (s, e) not in drafted_pairs),
            "cells": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare a draft-cells result with the run's final sidecar.")
    sub = parser.add_subparsers(dest="command", required=True)
    cmp_parser = sub.add_parser("compare", help="count the agent's changes to the drafted cells")
    cmp_parser.add_argument("draft", type=Path, nargs="+", help="draft-cells JSON result(s)")
    cmp_parser.add_argument("--sidecar", type=Path, required=True, help="the run's analysis.json")
    cmp_parser.add_argument("--output", type=Path,
                            help="save full JSON to this file and print aggregate counts")
    args = parser.parse_args()
    drafts = [json.loads(path.read_text(encoding="utf-8")) for path in args.draft]
    merged = {"cells": [c for d in drafts for c in d["cells"]], "missing": [m for d in drafts for m in d["missing"]]}
    seen: set[tuple[str, str]] = set()
    for cell in merged["cells"]:
        # A pair drafted in two files counts once, like a second cell in one file.
        key = (cell["state"], cell["event"])
        if key in seen and not any("second cell" in p for p in cell["problems"]):
            cell["problems"] = [*cell["problems"], "second cell for this state and event (another draft file)"]
        seen.add(key)
    result = compare(merged, json.loads(args.sidecar.read_text(encoding="utf-8")))
    if args.output:
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result = {key: result[key] for key in (
            "by_jev_choice", "changed_fields", "drafted", "missing_in_draft", "second_cells_in_draft"
        )}
        result["output"] = str(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
