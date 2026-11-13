"""Static types for the analysis sidecar (analysis.json).

These TypedDicts mirror formats/analysis.schema.json, which stays the
contract: the schema is what dsc_check validates at run time, the types are
what mypy checks in the tools that build or read a sidecar. The selftest
(run_selftest.py, "sidecar types match the schema") fails when the two
drift: a property, a required key, or an enum value present in one and not
in the other.

No "from __future__ import annotations" here: with string annotations,
TypedDict cannot see NotRequired and reports every key as required, which
would blind the drift check.
"""
from typing import Literal, NotRequired, TypedDict

Disposition = Literal[
    "transition",
    "handle",
    "ignore (documented)",
    "ignore (accidental)",
    "defer (queued)",
    "reject",
    "UNSPECIFIED",
]

GuardOutcome = Literal["proven", "violation", "not-formalizable"]


class Citation(TypedDict):
    file: str
    line: int
    # Required by the schema unless the file is a prose document (.md, .txt,
    # ...); the type cannot express that condition, so it stays optional here.
    fragment: NotRequired[str]


class Event(TypedDict):
    id: str
    undesired: NotRequired[bool]
    gate: NotRequired[str]
    upstream_guards: NotRequired[list[str]]


class CellBody(TypedDict):
    """A cell as parsed from its matrix text, before state and event are known."""
    disposition: Disposition
    target: NotRequired[str]
    dr: NotRequired[str]
    q: NotRequired[str]
    citation: NotRequired[Citation]


class Cell(TypedDict):
    state: str
    event: str
    disposition: Disposition
    target: NotRequired[str]
    dr: NotRequired[str]
    q: NotRequired[str]
    citation: NotRequired[Citation]


class Pair(TypedDict):
    id: str
    trace: str


class GuardGroup(TypedDict):
    id: str
    outcome: GuardOutcome
    reason: NotRequired[str]


class Question(TypedDict):
    id: str
    status: str
    fault: NotRequired[list[str]]
    trigger: NotRequired[str]
    note: NotRequired[str]


class DocLine(TypedDict):
    id: str
    # Author text from the doctrine table, carried unchecked: the schema's
    # enum (cell, invariant, ...) is enforced by dsc_check, not by the type.
    mapping: str
    target: str


class Absence(TypedDict):
    count: int
    reason: str


class Completeness(TypedDict, total=False):
    pairs: Absence
    guardGroups: Absence
    coverage: Absence


class Sidecar(TypedDict):
    formatVersion: Literal["1.0"]
    component: str
    states: list[str]
    events: list[Event]
    cells: list[Cell]
    packVersion: NotRequired[str]
    analyzedSha: NotRequired[str]
    watchPaths: NotRequired[list[str]]
    pairs: NotRequired[list[Pair]]
    guardGroups: NotRequired[list[GuardGroup]]
    # event id -> UV category key -> event id or "n/a: <reason>"
    coverage: NotRequired[dict[str, dict[str, str]]]
    questions: NotRequired[list[Question]]
    behaviouralDrs: NotRequired[list[str]]
    completeness: NotRequired[Completeness]
    docLines: NotRequired[list[DocLine]]
