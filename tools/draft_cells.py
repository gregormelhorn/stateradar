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
        cell: DraftCell = {"state": state, "event": event, "disposition": disposition,
                           "line": item.get("line"), "fragment": item.get("fragment"),
                           "note": note.strip() if isinstance(note, str) else "", "problems": []}
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
    if cell["disposition"] in HOLES:
        head += " → Q-?"
    citation = f' {source_ref}:{cell["line"]} ("{cell["fragment"]}")' if not cell["problems"] else ""
    note = f" — {cell['note']}" if cell["note"] else ""
    return (head + citation + note).replace("|", "\\|")


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
