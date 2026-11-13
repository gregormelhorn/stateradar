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
  src_roots: [lib, cmd]          # directories searched for cited files
  src_exts: [".go", ".proto"]    # with the leading dot; case-sensitive

Usage: python3 tools/gen_analysis_sidecar.py [--root REPO] [component ...]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, TypedDict, cast

from sidecar_types import (Cell, CellBody, Citation, Completeness, Disposition, DocLine, Event,
                           GuardGroup, GuardOutcome, Pair, Question, Sidecar)


class Overlay(TypedDict):
    """sidecar-overlay.yaml, read as untrusted YAML (values are not validated)."""
    skip: dict[str, str]
    question_aliases: dict[str, dict[str, str]]
    extra_citations: list[dict[str, Any]]
    src_roots: list[str]
    src_exts: list[str]


class EventAnnotation(TypedDict):
    gate: str | None
    upstream_guards: list[str]
    coverage: dict[str, str]


SRC_ROOTS = ["src", "lib", "app", "pkg", "internal"]
SRC_EXTS = [".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt",
            ".rb", ".cs", ".swift", ".c", ".h", ".cc", ".cpp", ".hpp", ".m"]
SKIP_DIRS = {".git", "node_modules", "dist", "build", "target", "vendor",
             "__pycache__", ".venv", "venv"}


def _src_index(root: Path, overlay: Overlay) -> dict[str, str]:
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


def _parse_event_annotations(cat_path: Path) -> dict[str, EventAnnotation]:
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
    out: dict[str, EventAnnotation] = {}
    cur: EventAnnotation | None = None
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


def _parse_events(header: str) -> list[Event]:
    """Header row cells after the first: 'P1 `put`' / 'UV-P1 `duplicate`'."""
    events: list[Event] = []
    for cell in header.strip().strip("|").split("|")[1:]:
        token = cell.strip().split()[0] if cell.strip() else ""
        if not token:
            continue
        events.append({"id": token, "undesired": token.startswith("UV-")})
    return events


PROSE_EXTS = (".md", ".markdown", ".txt", ".rst", ".adoc")
# Config and schema files a cell may cite as observed behaviour. They are not
# indexed unless a project adds them to src_exts, so their citations are
# dropped, and the generator says so (see generate()).
CONFIG_EXTS = (".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".conf", ".xml", ".sql",
               ".sh", ".tf", ".hcl")


_CIT_TOKEN = r"[\w./-]+\.[A-Za-z]{1,4}:\d+"
_FRAG_OPEN = re.compile(r'(?:-\d+)?`?\s*\(\s*["\u201c]')
_FRAG_END_AT_BOUNDARY = re.compile(r'["\u201d]\s*\)(?=\s*(?:[),;|]|\u2014|$))')
_FRAG_END_ANY = re.compile(r'["\u201d]\s*\)')
_NEXT_FRAGMENT_CITATION = re.compile(_CIT_TOKEN + r'`?\s*\(\s*["\u201c]')


def _outside_fragments(raw: str) -> str:
    """The cell text with each citation's quoted fragment blanked out.

    A fragment opens with ("  or (\u201c right after a file:line and may hold
    unescaped quotes, so it ends where the fragment extractor in _parse_cell
    ends it: at the first quote-paren followed by a boundary (")", ",", ";",
    "|", an em dash or the end), searched only up to the next fragment-cited
    file:line; failing that, at the first quote-paren before it.
    """
    spans: list[tuple[int, int]] = []
    pos = 0
    while (tok := re.compile(_CIT_TOKEN).search(raw, pos)) is not None:
        opener = _FRAG_OPEN.match(raw, tok.end())
        if opener is None:
            pos = tok.end()
            continue
        nxt = _NEXT_FRAGMENT_CITATION.search(raw, opener.end())
        limit = nxt.start() if nxt else len(raw)
        end = (_FRAG_END_AT_BOUNDARY.search(raw, opener.end(), limit)
               or _FRAG_END_ANY.search(raw, opener.end(), limit))
        stop = end.end() if end else limit
        spans.append((opener.start(), stop))
        pos = stop
    for start, stop in reversed(spans):
        raw = raw[:start] + " " + raw[stop:]
    return raw


def _parse_cell(
    text: str,
    family: str | None,
    states: list[str],
    src_index: dict[str, str],
    unresolved: set[str] | None = None,
) -> CellBody:
    """One matrix cell → sidecar cell, without its state and event.

    A cited file name that does not resolve through src_index is added to
    `unresolved` (the caller reports it): the citation is dropped.
    """
    raw = _strip_markdown(text.strip())
    q = re.search(r"Q-[\w-]+", raw)
    dr = re.search(r"DR-\d+", raw)
    disposition: Disposition
    target: str | None = None
    hole_q = q.group(0) if q else None  # kept only on hole cells

    if "UNSPECIFIED" in raw:
        disposition = "UNSPECIFIED"
    elif raw.startswith("transition"):
        disposition = "transition"
        hole_q = None
        m = re.search(r"→\s*`?([A-Za-z_][\w-]*)", raw)
        if m:
            target = m.group(1)
            if target not in states and family and f"{family} {target}" in states:
                target = f"{family} {target}"
            # an unknown target is kept: the checker flags it
    elif raw.startswith("handle"):
        disposition, hole_q = "handle", None
    elif raw.startswith("reject") or raw.startswith("`reject"):
        disposition, hole_q = "reject", None
    elif raw.startswith("defer"):
        disposition, hole_q = "defer (queued)", None
    elif raw.startswith("ignore"):
        if "accidental" in raw:
            disposition = "ignore (accidental)"
        else:
            disposition, hole_q = "ignore (documented)", None
    else:
        disposition = "UNSPECIFIED"

    # A crash (panic, escaping exception, process exit) is `handle crash:
    # ... -> Q-nn` (02-pilot v1.19): the code does something, but nobody
    # decided it. The question stays on the cell so dsc_check verifies it.
    # Only a `crash:` label right after the disposition word (and a
    # transition's target) counts: "does not crash: returns nil" is prose.
    if re.match(r"(?:handle|reject|defer[ \t]*\(queued\)|ignore[ \t]*\([^)]*\)|UNSPECIFIED"
                r"|transition[ \t]*→[ \t]*`?[\w-]+`?)[^\w]*crash:", raw, re.I):
        crash_q = re.search(r"\bQ-\d[\w-]*", raw)
        if disposition != "handle":
            raise ValueError(f"a crash cell is written `handle crash: ...`, not {disposition} "
                             f"(02-pilot step 4): {raw[:80]!r}")
        if not crash_q:
            raise ValueError(f"crash cell without a question (02-pilot step 4): {raw[:80]!r}")
        hole_q = crash_q.group(0)

    # Key order (disposition, target or q, dr, citation) is part of the
    # golden sidecars, which are compared byte for byte.
    cell: CellBody = {"disposition": disposition}
    if target is not None:
        cell["target"] = target
    if hole_q is not None:
        cell["q"] = hole_q
    if dr:
        cell["dr"] = dr.group(0)
    # file:line, optionally followed by ("fragment") (02-pilot rule 3). Keep
    # the fragment: dsc_check verifies it near the cited line. Read it from
    # the unstripped text, because inline-code stripping can alter it.
    # The first token that resolves is the citation, so a host:port or a
    # version string earlier in the cell does not hide it. Every candidate
    # that does not resolve goes to `unresolved`, also next to a resolved
    # one (a cell records one citation, so a second one is dropped); the
    # caller drops the candidates that are not file names.
    # Candidates come from the cell without its quoted fragments: a fragment
    # may quote "mini.py:19" or "app.json:12" (a log line, a stack trace),
    # which is neither the citation nor a dropped one.
    outside = _outside_fragments(raw)
    found = list(re.finditer(r"([\w./-]+\.[A-Za-z]{1,4}):(\d+)", outside))
    if unresolved is not None:
        unresolved.update(m.group(1) for m in found if not src_index.get(Path(m.group(1)).name))
    cit = next((m for m in found if src_index.get(Path(m.group(1)).name)), None)
    if cit:
        path = src_index.get(Path(cit.group(1)).name)
        if path:
            citation: Citation = {"file": path, "line": int(cit.group(2))}
            cell["citation"] = citation
            # The fragment may hold unescaped or typographic quotes and
            # "host:5432" tokens: it ends at a quote-paren followed by a
            # boundary, or at the last one before a later citation on the line.
            head = re.escape(cit.group(1)) + r"`?:" + cit.group(2) + r'(?:-\d+)?`?\s*\(\s*["\u201c]'
            # A later citation names a source file or a file cited with a
            # fragment in the same text (mirrors part_b_pack.cited_names),
            # never a host name.
            names = set(src_index) | {Path(m.group(1)).name for m in re.finditer(
                r'([\w./-]+\.[A-Za-z]{1,4})`?:\d+(?:-\d+)?`?\s*\(\s*["\u201c]', text)}
            later = "(?:[\\w./-]*/)?(?:" + "|".join(
                re.escape(n) for n in sorted(names, key=len, reverse=True)) + ")"
            end = (r'["\u201d]\s*\)(?=\s*(?:[),;|]|\u2014|$)'
                   r'|(?:(?!["\u201d]\s*\)).)*?[\s,(]' + later + r'`?:\d)')
            frag = (re.search(head + r"(.+?)" + end, text, re.M)
                    or re.search(head + r'(.+?)["\u201d]\s*\)', text))
            if frag:
                citation["fragment"] = frag.group(1).replace('\\"', '"')
    return cell


def _parse_doc_map(path: Path) -> list[DocLine]:
    """PA-22 doctrine mapping: parse the machine-readable table under
    '## Doctrine mapping' in invariants-and-lints.md into sidecar
    docLines. Row format: | DOC-n | cell/invariant/constraint/rejected
    | target |. Declarations, never prose (02-pilot v1.4 rule)."""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    if "## Doctrine mapping" not in text:
        return []
    # The table ends at the next heading of any level: a '###' sub-section
    # may hold other '| DOC-' rows (agent-only run 2026-11-13).
    block = re.split(r"\n#{1,6}[ \t]", text.split("## Doctrine mapping")[1], maxsplit=1)[0]
    rows: list[DocLine] = []
    for line in block.split("\n"):
        s = line.strip()
        if not s.startswith("| DOC-"):
            continue
        cells = [c.strip() for c in s.split("|")[1:-1]]
        if len(cells) >= 3:
            rows.append({"id": cells[0], "mapping": cells[1],
                         "target": cells[2]})
    return rows


def _parse_questions(path: Path) -> list[Question]:
    """open-questions.md → [{id, status}] pairs (DECIDED → RESOLVED)."""
    if not path.is_file():
        return []
    questions: list[Question] = []
    current: Question | None = None
    for line in path.read_text().split("\n"):
        # 'Q-01', '## Q-01: title' and '**Q-01**' all open a question.
        m = re.match(r"^(?:#{1,6}\s+|\*\*)?(Q-(?:[A-Z]+-)*\d[\w-]*?)(?=[\s:*.,)\u2014]|$)", line.strip())
        if m:
            current = {"id": m.group(1), "status": "OPEN"}
            questions.append(current)
        # ODC fields (02-pilot R-ODC-FIELDS): '**Fault:** F-13, F-09' and
        # '**Trigger:** step-4 matrix walk', or as a list item ('- fault:
        # F-13'). A plain 'Fault: ...' line is prose, and the first field of
        # each kind in a question wins.
        odc = re.match(r"^(?:\*\*(fault|trigger):\*\*|\*\*(fault|trigger)\*\*:|[-*][ \t]+(fault|trigger):)"
                       r"[ \t]*(.*)$", line.strip(), re.I)
        if odc and current is not None:
            label = (odc.group(1) or odc.group(2) or odc.group(3)).lower()
            value = odc.group(4)
            if label == "fault" and "fault" not in current:
                current["fault"] = re.findall(r"F-\d{2}\b", value)
            elif label == "trigger" and "trigger" not in current:
                current["trigger"] = value.strip().strip("`").strip()
        s = re.search(r"\*\*Status:\*\*\s*(.+)", line)
        if s and current is not None:
            status = s.group(1).strip()
            if status.startswith("DECIDED"):
                status = "RESOLVED" + status[len("DECIDED"):]
            current["status"] = status
    return questions


def _parse_pairs(catalogue: Path, traces: Path) -> list[Pair]:
    """Step-3 pair ids (P-01a, P-01b, ...) declared in event-catalogue.md,
    each with the adversarial-traces.md heading that carries its id. A pair
    without such a heading gets an empty trace, which dsc_check reports
    ("no trace"): an untraced pair is a gap, not something to drop."""
    if not catalogue.is_file():
        return []
    ids = sorted(set(re.findall(r"\bP-\d+[a-z]\b", catalogue.read_text(encoding="utf-8"))),
                 key=lambda pid: (int(re.findall(r"\d+", pid)[0]), pid))
    text = traces.read_text(encoding="utf-8") if traces.is_file() else ""
    pairs: list[Pair] = []
    for pid in ids:
        m = re.search(r"^#{1,6}[ \t]+" + re.escape(pid) + r"\b[ \t]*(?:[\u2014:.-]+[ \t]*)?(.*)$",
                      text, re.M)
        trace = f"{traces.name}#{pid}: {m.group(1).strip()}".rstrip(": ") if m else ""
        pairs.append({"id": pid, "trace": trace})
    return pairs


def _parse_guard_results(path: Path) -> list[GuardGroup]:
    """guard-results.txt as tools/guard_proofs.render writes it ('group G-01
    name: proven', findings indented), plus the run's own
    'not-formalizable: <category>: <reason>' lines."""
    if not path.is_file():
        return []
    groups: list[GuardGroup] = []
    for line in path.read_text(encoding="utf-8").split("\n"):
        if not line.startswith("group"):
            continue
        # The outcome is the first outcome word after a colon; the group
        # name before it may itself contain colons ("Get: dispose").
        m = re.match(r"^group[ \t]+(G-[\w.-]+)\b.*?:[ \t]*(proven|violation|not-formalizable)\b"
                     r"(?:[ \t]*:[ \t]*(.*?))?[ \t]*$", line)
        if not m:
            _note(f"{path.name}: group line without an outcome (proven, violation, "
                  f"not-formalizable): {line.strip()[:80]!r}")
            continue
        group: GuardGroup = {"id": m.group(1), "outcome": cast(GuardOutcome, m.group(2))}
        if m.group(3) and m.group(3).strip():
            group["reason"] = m.group(3).strip()
        groups.append(group)
    return groups


def _load_overlay(analysis_root: Path) -> Overlay:
    """sidecar-overlay.yaml — skip list, question aliases, citations."""
    empty: Overlay = {"skip": {}, "question_aliases": {}, "extra_citations": [],
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


NOTES: list[str] = []


def _note(message: str) -> None:
    """A finding that does not stop generation; --strict turns it into a
    failure of the run."""
    NOTES.append(message)
    print(f"note {message}", file=sys.stderr)


def generate(component: str, analysis_root: Path, src_index: dict[str, str], overlay: Overlay) -> Sidecar | None:
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
    blocks: list[tuple[list[Event], list[str]]] = []
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

    for block_events, block_rows in blocks:
        if not block_rows:
            _note(f"{component}: table headed "
                  f"{', '.join(e['id'] for e in block_events) or '(no events)'} has no "
                  "'| **' state rows; it declares no events")
    # A header without '| **' state rows is a prose table whose first
    # column happens to be headed "State"; it declares no events
    # (agent-only run 2026-11-13: phantom event "Condition").
    blocks = [b for b in blocks if b[1]]

    events: list[Event] = []
    seen_events: set[str] = set()
    for block_events, _ in blocks:
        for event in block_events:
            if event["id"] not in seen_events:
                events.append(event)
                seen_events.add(event["id"])

    # Two passes: collect every state first (transition targets resolve
    # against the full list), then parse the cells.
    states: list[str] = []
    row_index: list[tuple[list[Event], str, str, str | None]] = []
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

    # A declared state without a '| **' row is named on stderr: rows that
    # lost their bold markers would otherwise drop their table silently
    # (review of the prose-table fix, which no longer counts row-less
    # headers). Terminal states (PA-18) may have no row, and committed
    # matrices list transient states without rows, so this is a note, not
    # an error. Declarations separate names with commas or spaces.
    decl = re.search(r"<!--\s*states:(.*?)-->", text, re.S)
    if decl:
        rest = decl.group(1)
        names = set(states)
        term = re.search(r"<!--\s*terminal:(.*?)-->", text, re.S)
        if term:
            names.update(n for n in re.split(r"[\s,;]+", term.group(1)) if n)
        for _, _, state, family in row_index:
            if family:
                names.update((family, state[len(family):].strip()))
        for name in sorted(names, key=len, reverse=True):
            rest = re.sub(r"(?<![\w.-])" + re.escape(name) + r"(?![\w.-])", " ", rest)
        missing = [w for w in re.split(r"[\s,;]+", rest) if w]
        if missing:
            _note(f"{component}: declared states without a '| **' row: "
                  f"{', '.join(missing)}")

    cells: list[Cell] = []
    unresolved: set[str] = set()
    for block_events, row, state, family in row_index:
        parts = row.strip().strip("|").split("|")[1:]
        for event, cell_text in zip(block_events, parts, strict=True):
            try:
                body = _parse_cell(cell_text, family, states, src_index, unresolved)
            except ValueError as exc:
                raise ValueError(f"{component}: {state} x {event['id']}: {exc}") from exc
            # Key order as before (parsed keys, then state and event): the
            # golden sidecars are compared byte for byte.
            cells.append({**body, "state": state, "event": event["id"]})

    # Loud, not silent: a dropped citation drops its fragment check too (a test
    # file outside the source roots, say). One line per component and file.
    # Only tokens with a known file extension count; anything else in a cell
    # that looks like name.ext:N (host:port, versions) is not a citation and
    # stays quiet. Source extensions are matched as _src_index matches them,
    # case-sensitively, so the reason names the real cause.
    src_exts = tuple(overlay["src_exts"] or SRC_EXTS)
    src_exts_lower = {ext.lower() for ext in src_exts}
    for name in sorted(unresolved):
        ext = Path(name).suffix.lower()
        if name.endswith(src_exts):
            reason = "the file is not under the source roots (sidecar-overlay.yaml: src_roots)"
        elif ext in PROSE_EXTS:
            reason = ("matrix citations resolve to source files only; cite a prose document "
                      "through sidecar-overlay.yaml extra_citations")
        elif ext in CONFIG_EXTS or ext in src_exts_lower:
            reason = ("its extension is not a source extension (sidecar-overlay.yaml: src_exts, "
                      "matched case-sensitively)")
        else:
            continue
        print(f"warning: {component}: citations of {name} dropped: {reason}", file=sys.stderr)

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
        for ts in terminal_states:
            for ev in events:
                if (ts, ev["id"]) not in existing:
                    cells.append({"state": ts, "event": ev["id"],
                                  "disposition": "ignore (documented)",
                                  "citation": {"file": "disposition-matrix.md", "line": 0,
                                               "fragment": "terminal state declaration"}})

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
                    # Overlay YAML is not validated here: a citation missing
                    # its file or line is caught by the schema in dsc_check.
                    cell["citation"] = cast(Citation, {
                        k: v for k, v in extra.items() if k in ("file", "line", "fragment")
                    })

    doc_lines = _parse_doc_map(adir / "invariants-and-lints.md")

    questions = _parse_questions(adir / "open-questions.md")
    known = {q["id"] for q in questions}
    for cell in cells:
        qid = cell.get("q")
        if qid and qid not in known:
            alias = overlay["question_aliases"].get(qid) or {}
            entry: Question = {"id": qid, "status": alias.get("status", "OPEN")}
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
        gate = ann["gate"]
        if gate is not None:
            ev["gate"] = gate
        if ann.get("upstream_guards"):
            ev["upstream_guards"] = ann["upstream_guards"]
    catalogue_coverage = {
        eid: ann["coverage"] for eid, ann in annotations.items()
        if ann.get("coverage")}

    data: Sidecar = {
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

    # Pairs, guard outcomes and the coverage table live outside the matrix
    # (event-catalogue.md + adversarial-traces.md, guard-results.txt,
    # event-catalogue.md) and are derived from there below. A section the
    # sources do not declare is asserted absent with a reason instead of
    # omitted: dsc_check demands a stated reason for every empty section.
    absent = ("the sidecar generator found no {what} in {src}; declare it "
              "there (02-pilot) before the component claims L4.")
    completeness: Completeness = {
        "pairs": {"count": 0, "reason": absent.format(
            what="pair ids (P-01a, ...)", src="event-catalogue.md")},
        "guardGroups": {"count": 0, "reason": absent.format(
            what="guard outcome lines", src="guard-results.txt")},
        "coverage": {"count": 0, "reason": absent.format(
            what="undesired-coverage table", src="event-catalogue.md")},
    }
    data["completeness"] = completeness
    pairs = _parse_pairs(adir / "event-catalogue.md", adir / "adversarial-traces.md")
    if pairs:
        data["pairs"] = pairs
        completeness.pop("pairs", None)
    guard_groups = _parse_guard_results(adir / "guard-results.txt")
    if guard_groups:
        data["guardGroups"] = guard_groups
        completeness.pop("guardGroups", None)
    if catalogue_coverage:
        data["coverage"] = catalogue_coverage
        completeness.pop("coverage", None)

    # A hand-merged sidecar keeps its real sections: never regress one to
    # an absence assertion just because this run could not derive it.
    out = adir / "analysis.json"
    if out.is_file():
        try:
            prior = json.loads(out.read_text())
        except json.JSONDecodeError:
            prior = {}
        # Spelled out per section: TypedDict keys must be literals.
        if prior.get("pairs") and not data.get("pairs"):
            data["pairs"] = prior["pairs"]
            completeness.pop("pairs", None)
        if prior.get("guardGroups") and not data.get("guardGroups"):
            data["guardGroups"] = prior["guardGroups"]
            completeness.pop("guardGroups", None)
        if prior.get("coverage") and not data.get("coverage"):
            data["coverage"] = prior["coverage"]
            completeness.pop("coverage", None)
    if not completeness:
        data.pop("completeness", None)
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
    parser.add_argument(
        "--strict", action="store_true",
        help="exit 1 when the run printed a note (a dropped table, a declared "
             "state without a row)",
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
    if args.strict and NOTES:
        print(f"error: --strict and {len(NOTES)} note(s) above")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
