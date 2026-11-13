#!/usr/bin/env python3
"""Part-B input assembler — build the blind-pass input package, and
validate the blind output's coverage mechanically.

The blind pass (02-pilot, PART B) needs exactly three inputs: the event
catalogue, the prose requirements, and the normative contract text of
every event type. Assembling them by hand is how placeholder payloads
get dispatched (dobby trigger-service, 2026-08-05: the first blind
dispatch went out with the literal words CATALOGUE / REQUIREMENTS /
CONTRACTS and was correctly refused). This tool assembles the package
with length guards and checks the returned table against the
catalogue's id declaration.

Assemble:
  python3 tools/part_b_pack.py <analysis-dir> \
      --requirements DECISIONS.md \
      --requirements docs/ARCHITECTURE_CONTEXT.md:M8.3 \
      --contracts src/contracts/transport.py:TriggerWindowEnvelope \
      --contracts src/contracts/events.py:TriggerEvent,TriggerAckEvent \
      [--repo .] [--out part_b_input.md]

  --requirements FILE         whole file
  --requirements FILE:PATTERN only lines from the first PATTERN match
                              to the next markdown heading of the same
                              or higher level (or EOF)
  --contracts FILE.py:A,B     class blocks (docstring and fields) only
  --contracts FILE.md         a prepared contract-text file, whole

Validate a blind output:
  python3 tools/part_b_pack.py <analysis-dir> --check blind_output.md

  Every catalogue event id and every interaction-pair ordering must
  appear exactly once in the blind table. Missing or duplicated rows
  are a hard failure — a coverage gap must be impossible to miss.

The instruction block is extracted live from prompts/02-pilot.md so
the assembled prompt never drifts from the canonical text.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

MIN_INPUT_CHARS = 200


def _catalogue_ids(catalogue: str) -> tuple[list[str], list[str]]:
    """Event ids from the declaration comment + pair orderings."""
    m = re.search(r"<!-- event-ids: (.+?) -->", catalogue)
    if not m:
        raise ValueError("catalogue: no event-ids declaration comment")
    events = m.group(1).split()
    pairs = sorted(set(re.findall(r"P-\d+[ab]\b", catalogue)))
    return events, pairs


def _read_requirements(spec: str, repo: Path) -> str:
    """FILE or FILE:PATTERN → requirement text (guarded)."""
    file_part, _, pattern = spec.partition(":")
    path = repo / file_part
    if not path.is_file():
        raise ValueError(f"requirements file missing: {path}")
    text = path.read_text(encoding="utf-8")
    if not pattern:
        return text
    m = re.search(pattern, text)
    if not m:
        raise ValueError(f"requirements pattern {pattern!r} not found in {path}")
    start = m.start()
    level = len(re.match(r"^#*", text[start:]).group(0)) if text[start] == "#" else 0
    rest = text[start:]
    if level:
        nxt = re.search(rf"^#{{1,{level}}} ", rest[1:], re.M)
        return rest[: nxt.start() + 1 if nxt else len(rest)]
    # No heading at the match (e.g. a bullet inside a bigger entry):
    # cut at the next heading of any level.
    nxt = re.search(r"^#{1,6} ", rest[1:], re.M)
    return rest[: nxt.start() + 1 if nxt else len(rest)]


def _read_contracts(spec: str, repo: Path) -> str:
    """FILE:Class1,Class2 → docstring + fields blocks per class.

    A prepared contract-text file (.md, .txt, .rst) may be passed whole. A
    source file always needs class names: the blind pass must never receive
    implementation code.
    """
    file_part, _, classes = spec.partition(":")
    path = repo / file_part
    if not path.is_file():
        raise ValueError(f"contracts file missing: {path}")
    if not classes:
        if path.suffix.lower() in (".md", ".txt", ".rst"):
            return path.read_text(encoding="utf-8")
        raise ValueError(f"contracts spec needs class names for a source file: {spec!r} "
                         "(or extract the contract text into a .md file)")
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    for cls in classes.split(","):
        cls = cls.strip()
        for i, line in enumerate(lines):
            if line.startswith(f"class {cls}"):
                block = [line]
                for follow in lines[i + 1 :]:
                    if follow.startswith(("class ", "def ")) or (
                        follow and not follow.startswith((" ", "\t", "@", ")"))
                        and not follow[0].islower()
                    ):
                        break
                    block.append(follow)
                    if len(block) >= 60:
                        break
                out.append("\n".join(block).rstrip())
                break
        else:
            raise ValueError(f"class {cls!r} not found in {path}")
    return "\n\n".join(out)


# A citation: file:line or file:a-b, further ", :n" or "and :n" line refs,
# and an optional ("fragment"). The fragment may hold unescaped or
# typographic quotes and even "host:5432" tokens. It ends at the first
# quote-paren before a boundary that leaves its quotes balanced; otherwise
# at the last quote-paren before a later citation, a table-cell bar or the
# end of the line, so no code tail survives. It never crosses a cell. A later
# citation names a file the text cites with a fragment elsewhere, or one
# that exists in the repository (cited_names), never a host name.
_FILE = r"[\w./-]+\.[A-Za-z]{1,4}"


_SKIP_DIRS = {".git", "node_modules", "vendor", "third_party", "target", "build", "dist", "__pycache__"}


def _repo_basenames(repo: Path) -> set[str]:
    names: set[str] = set()
    for dirpath, dirnames, files in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS and not d.startswith(".")]
        names.update(files)
    return names


def cited_names(text: str, repo: Path | None = None) -> frozenset:
    """File names that count as later citations: those cited with a
    fragment somewhere in text, plus file:N tokens that name a file under
    repo, by path or by base name (catalogues cite by base name)."""
    names = {Path(m.group(1)).name for m in re.finditer(
        "(" + _FILE + r")`?:\d+(?:-\d+)?`?\s*\(\s*[\"\u201c]", text)}
    if repo is not None:
        tokens = {m.group(1).strip("`") for m in re.finditer("(" + _FILE + r")`?:\d", text)}
        base = _repo_basenames(repo) if tokens else set()
        names.update(Path(tok).name for tok in tokens
                     if Path(tok).name in base or (repo / tok).is_file())
    return frozenset(names)


def cite_pattern(names: frozenset, table: bool = False) -> re.Pattern:
    """The citation pattern. On a table row (table=True) an unescaped "|"
    is a cell bar that the fallback never crosses; elsewhere "|" is code
    (a || b) like any other character."""
    later = ("(?:[\\w./-]*/)?(?:" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True)) + ")"
             if names else r"(?!)")
    q_open, q_close = r"[\"\u201c]", r"[\"\u201d]"
    # Where the next citation starts: a later file:N, or a prose file followed
    # by its own ("quote") (code such as errors.New("x") is not one). Neither
    # a fragment nor a quote pair crosses it.
    nxt = (r"[\s,(](?:" + later + r"`?:\d|[\w./-]+\.(?:md|txt|rst|adoc)`?\s*\(\s*" + q_open + r")")
    plain = r"(?:(?!" + nxt + r")[^\"\u201c\u201d\n])"
    ch = r"(?:(?!" + nxt + r")(?:\\\||[^|\n]))" if table else r"(?:(?!" + nxt + r")[^\n])"
    bar = r"|\|" if table else ""
    # 1. Quotes balanced inside, closed by a quote-paren before a boundary
    #    (this may cross an unescaped "|" of code even on a table row).
    balanced = (r"((?:" + plain + r"|" + q_open + plain + r"*" + q_close + r")*?)"
                + q_close + r"\s*\)(?=\s*(?:[),;|]|\u2014|$))")
    # 2. Otherwise the last quote-paren before the next citation, a cell bar
    #    (table rows) or the end of the line, so no code tail survives.
    last = (r"(" + ch + r"+?)" + q_close + r"\s*\)(?=(?:(?!" + q_close + r"\s*\))" + ch
            + r")*?(?:" + nxt + bar + r"|$))")
    return re.compile(
        r"(" + _FILE + r")`?:\d+(?:-\d+)?(?:(?:,|\s+and)[ \t]*:\d+(?:-\d+)?)*"
        r"(`?\s*\(\s*" + q_open + balanced +
        r"|`?\s*\(\s*" + q_open + last + r")?", re.M)


def sub_citations(text: str, names: frozenset, repl) -> str:
    """Apply repl to every citation, choosing the table-row pattern per line."""
    prose, table = cite_pattern(names), cite_pattern(names, table=True)
    return "\n".join((table if line.lstrip().startswith("|") else prose).sub(repl, line)
                      for line in text.split("\n"))


# After stripping, a file name directly followed by ("..." means a fragment
# the patterns could not end: the command reports it (backstop for R-PART-B).
_LEFT_FRAGMENT = re.compile("(" + _FILE + r")`?\s*\(\s*[\"\u201c]")


def leftover_fragments(text: str, keep_quotes_from: frozenset = frozenset()) -> list[str]:
    return [m.group(0) for m in _LEFT_FRAGMENT.finditer(text) if _norm(m.group(1)) not in keep_quotes_from]


# Prose source documents: a quote cited from one of them is the normative
# text Part B needs (doctrine lines, requirements), not implementation code
# and not an analysis conclusion. Only files named in quote_files qualify:
# the Part B inputs and the prose files the doctrine lines cite, never a file
# of the analysis directory (method review round 4).
_PROSE_EXT = (".md", ".txt", ".rst", ".adoc")


def _norm(path: str) -> str:
    return str(Path(path.strip("`")).as_posix()).removeprefix("./")


def _citation_stripper(quote_files: frozenset):
    def strip(m: re.Match) -> str:
        if m.group(2) and _norm(m.group(1)) in quote_files:
            quote = m.group(3) if m.group(3) is not None else m.group(4)  # balanced, last
            return f'{m.group(1)} ("{quote}")'
        return m.group(1)
    return strip


def quote_files(doctrine: str, inputs: list[str], repo: Path, analysis_dir: Path) -> frozenset:
    """Prose files whose cited quotes may reach Part B, as paths relative to
    --repo: the Part B inputs and the files the doctrine lines cite. A path
    inside the analysis directory never qualifies. Matching is by exact path,
    so vendor/lib/README.md does not ride on README.md."""
    paths = set()
    for spec in inputs:
        path = Path(spec.split(":", 1)[0])
        if path.is_absolute():
            try:
                path = path.resolve().relative_to(repo)
            except ValueError:
                continue
        paths.add(_norm(str(path)))
    paths.update(_norm(m.group(1)) for m in re.finditer("(" + _FILE + r")`?:\d", doctrine))
    adir = analysis_dir.resolve()
    return frozenset(p for p in paths if p.lower().endswith(_PROSE_EXT)
                     and not (repo / p).resolve().is_relative_to(adir))


# Analysis-only id families. Single-letter families (L-, G-, F-, T-) also
# name domain things ("the T-1 threshold"), so an id of those families is
# kept when the Part B sources (requirements, contracts, doctrine lines) use
# it, and removed otherwise (domain_ids).
_ANALYSIS_ID = re.compile(r"(?:\s*→\s*)?\b(?:Q|PA|SYS|NAT|DR)-[A-Z]*\d[\w-]*")
_LOCAL_ID = re.compile(r"\b(?:L|G|F|T)-[A-Z]*\d[\w-]*")
_MARK = "\x00"


def domain_ids(*sources: str, doctrine: str = "") -> set[str]:
    """Single-letter-family ids the Part B sources themselves use. They are
    domain terms Part B sees anyway; every other L-/G-/F-/T- id in the
    catalogue is an analysis reference (lint, guard, fault, trace). From
    doctrine lines only the quoted text counts: their glosses are Part A's."""
    ids: set[str] = set()
    for source in sources:
        ids.update(_LOCAL_ID.findall(source))
    for quote in re.findall(r"[\"\u201c]([^\"\u201c\u201d\n]+)[\"\u201d]", doctrine):
        ids.update(_LOCAL_ID.findall(quote))
    return ids


def blind_catalogue(text: str, keep_ids: set[str] | frozenset = frozenset(),
                    keep_quotes_from: frozenset = frozenset(), later_names: frozenset = frozenset()) -> str:
    """The catalogue as Part B may see it.

    02-pilot rule 3 puts a verbatim code fragment into every observed-in-code
    citation, and the catalogue carries the analysis's own ids (questions,
    lints, invariants, guards, decisions, faults, traces). Part B must see
    neither the code nor Part A's conclusions (R-PART-B; routed pilot
    2026-11-13). Citations keep the file name only, without line or code
    fragment (a quote cited from a file in keep_quotes_from stays);
    analysis ids and the labels that introduced them are removed; L-, G-,
    F- and T- ids survive only when listed in keep_ids. Prose
    conclusions cannot be removed mechanically: the agent still reads the
    package (rule 7). Pass later_names=cited_names(text, repo) so that bare
    citations of repository files end a fragment; assemble does.
    """
    names = cited_names(text) | frozenset(later_names)
    text = sub_citations(text, names, _citation_stripper(frozenset(keep_quotes_from)))
    text = _ANALYSIS_ID.sub(_MARK, text)
    text = re.sub(r"(?:\s*→\s*)?" + _LOCAL_ID.pattern,
                  lambda m: m.group(0) if m.group(0).lstrip(" \t→") in keep_ids else _MARK, text)
    # Labels whose only content was a removed id: "lint L-4", "Finding → Q-12",
    # "see DR-002"; "see" in prose stays.
    text = re.sub(r"\b(?=[A-Z])(?i:see|cf\.)[ \t]*(?=\x00)", "\x01", text)  # a sentence start
    text = re.sub(r"\b(?i:see|cf\.)[ \t]*(?=\x00)", "", text)
    text = re.sub(r"(?:\b(?:recorded as\s+)?lints?\s*|\b[Ff]inding\s*(?::\s*)?)(?=\x00)", "", text)
    # Parentheses that held only removed ids, then the ids with their separators.
    text = re.sub(r"(?m)(^[ \t]*)?(?(1)|[ \t]*)\((?:[\s,;\x01]|\x00)*\x00(?:[\s,;]|\x00)*\)(?(1)[ \t]*)",
                  lambda m: m.group(1) or "", text)
    # A removed id between two separators takes one of them with it; at the
    # end of a clause it takes the separator before it; before text it
    # leaves that separator ("cache; lint L-4; G-01 holds" keeps a ";").
    text = re.sub(r"\x00(?:[ \t]*(?:[,;]|\band\b)[ \t]*\x00)+", _MARK, text)  # id lists
    while _MARK in text:
        text = re.sub(r"[ \t]*[,;][ \t]*\x00(?=[ \t]*[,;])", "", text)
        text = re.sub(r"[ \t]*(?:[,;]|\band\b)?[ \t]*\x00(?=[ \t]*(?:[).|\]\n]|\x00|$))", "", text)
        text = re.sub(r"\x00[ \t]*(?![ \t]*(?:[,;).|\]\n]|\x00|$))", "", text)
        text = re.sub(r"(?<![,;])\x00(?=[ \t]*[,;])", "", text)
    # Debris: a reference word left before a separator, doubled separators
    # and doubled spaces ("see DR-002; then" -> "; then").
    text = re.sub(r"[,;][ \t]*([,;])", r"\1", text)
    # A sentence that started with a removed label starts with a capital, and
    # one left as bare punctuation ("Cf. DR-002.") goes.
    text = re.sub(r"\x01[ \t]*\.+[ \t]*", "", text)
    text = re.sub(r"\x01[ \t]*[;,]*[ \t]*([a-z])", lambda m: m.group(1).upper(), text)
    text = re.sub(r"\x01[ \t]*[;,]*", "", text)
    text = re.sub(r"\|[ \t]{2,}\|", "| |", text)
    text = re.sub(r"(?<=\S)[ \t]{2,}(?=\S)", " ", text)
    return re.sub(r"(?<=[^\s|])[ \t]+$", "", text, flags=re.M)


_DOC_ROW = re.compile(r"^(?:[-*]|\d+\.|\|)\s*\**DOC-\d+")


def _extract_doctrine(extraction: str) -> str:
    """The doctrine lines of an extraction: DOC-n bullets, numbered items or
    table rows under a heading (any level) that names doctrine. Rows outside
    such a section (status or mapping tables) are never taken."""
    lines: list[str] = []
    section_level = 0
    for line in extraction.split("\n"):
        s = line.strip()
        heading = re.match(r"^(#{1,6})\s", s)
        if heading and "doctrine" in s.lower():
            section_level = len(heading.group(1))
            continue
        if heading and section_level and len(heading.group(1)) <= section_level:
            section_level = 0
        if section_level and _DOC_ROW.match(s):
            lines.append(s)
    return "\n".join(lines)


def _part_b_instruction(pack_root: Path) -> str:
    """The canonical blind-pass instruction from prompts/02-pilot.md."""
    pilot = (pack_root / "prompts" / "02-pilot.md").read_text(encoding="utf-8")
    m = re.search(r"(> Here is the event catalogue.*?)(?=\n\n(?=> |\w)|\Z)", pilot, re.S)
    if not m:
        raise ValueError("02-pilot.md: PART B instruction block not found")
    return m.group(1)


def assemble(args: argparse.Namespace, pack_root: Path) -> int:
    repo = Path(args.repo).resolve()
    adir = repo / args.analysis_dir
    catalogue_path = adir / "event-catalogue.md"
    if not catalogue_path.is_file():
        print(f"PART-B PACK: no event catalogue at {catalogue_path}", file=sys.stderr)
        return 2
    catalogue = catalogue_path.read_text(encoding="utf-8")
    events, pairs = _catalogue_ids(catalogue)

    # Doctrine lines travel with the requirements: every artefact in the
    # dobby Part-B runs (G2 storm guard, trigger-lane policy) traced to a
    # doctrine line missing from the blind input.
    doctrine = ""
    extraction_path = adir / "extraction.md"
    if extraction_path.is_file():
        ext = extraction_path.read_text(encoding="utf-8")
        doctrine = _extract_doctrine(ext)
        if not doctrine and re.search(r"\bDOC-\d+", ext):
            # A silent skip sent Part B no doctrine lines (routed pilot 2026-11-13).
            raise ValueError(f"{extraction_path} names DOC-n lines but none is a bullet, numbered "
                             "item or table row under a heading that names doctrine")
    sources = [(f"INPUT 2: REQUIREMENTS ({spec})", _read_requirements(spec, repo))
               for spec in args.requirements]
    sources += [(f"INPUT 3: EVENT CONTRACT TEXTS ({spec})", _read_contracts(spec, repo))
                for spec in args.contracts]
    keep_ids = domain_ids(*(text for _, text in sources), doctrine=doctrine)
    keep_quotes = quote_files(doctrine, list(args.requirements) + list(args.contracts), repo, adir)

    later = cited_names(catalogue + "\n" + doctrine, repo)
    blind_copy = blind_catalogue(catalogue, keep_ids, keep_quotes, later)
    try:
        same_ids = _catalogue_ids(blind_copy) == (events, pairs)
    except ValueError:
        same_ids = False
    if not same_ids:
        raise ValueError("stripping analysis ids changed the catalogue's event ids; rename event or "
                         "pair ids that look like analysis ids (Q-, PA-, SYS-, NAT-, DR-, or L-/G-/F-/T- "
                         "ids the requirements do not use)")
    blocks: list[tuple[str, str]] = [
        ("INPUT 1: EVENT CATALOGUE (code fragments and analysis references removed)", blind_copy)]
    blind_doctrine = blind_catalogue(doctrine, keep_ids, keep_quotes, later) if doctrine else ""
    if blind_doctrine:
        blocks.append(("INPUT 2b: DOCTRINE LINES (from the extraction)", blind_doctrine))
    blocks += sources
    left = leftover_fragments(blind_copy + "\n" + blind_doctrine, keep_quotes)
    if left:
        print("PART-B PACK: possible code fragments left after a citation (check the package, rule 7): "
              + "; ".join(left[:10]), file=sys.stderr)
    kept = sorted(set(_LOCAL_ID.findall(blind_copy + "\n" + blind_doctrine)))
    both = catalogue + "\n" + doctrine
    removed = sorted(set(_LOCAL_ID.findall(sub_citations(both, later, r"\1"))) - set(kept))
    if removed:
        # A domain term the sources never use goes too: the agent sees which.
        print("PART-B PACK: removed as analysis references (a domain term among them is a "
              "known loss: record it in part-b-diff.md, never edit the inputs to restore it): "
              + ", ".join(removed), file=sys.stderr)
    if kept:
        # Rule 7: the agent judges these while reading the package.
        print("PART-B PACK: kept in the catalogue or doctrine lines because the requirements, "
              "contracts or quoted doctrine text use them: " + ", ".join(kept), file=sys.stderr)

    # Length guard: the dropped-payload failure mode (dobby 2026-08-05).
    short = [name for name, text in blocks if len(text) < MIN_INPUT_CHARS]
    if short:
        print("PART-B PACK: input blocks suspiciously short — payload dropped?")
        for name in short:
            print(f" - {name}")
        return 1

    instruction = _part_b_instruction(pack_root)
    ids_line = " ".join(events) + " — plus the pair orderings " + " ".join(pairs)
    parts = [
        "You are the BLIND adversarial pass (Part B) of a domain-behaviour "
        "analysis. You have NO access to the implementation. Do NOT read any "
        "files, do NOT use any tools, do NOT search any repository — the "
        "inputs below are complete and are your ONLY sources. If you catch "
        "yourself wanting to look something up, label it an open point instead.",
        "",
        "TASK: " + instruction.lstrip("> ").replace("\n> ", "\n"),
        "",
        "The catalogue's event ids are: " + ids_line + ".",
        "",
    ]
    for name, text in blocks:
        parts.append(f"=== {name} ===\n\n{text}\n")
    parts.append(
        "Respond with ONLY the table and the coverage checklist: every "
        "catalogue event id, listed once, ticked. A missing row must be "
        "impossible to miss."
    )
    package = "\n".join(parts)

    if args.for_dispatch:
        header = (
            "DISPATCH THIS PACKAGE VERBATIM, IN FULL, AS THE TASK TEXT.\n"
            "A Part-B dispatch with placeholder inputs is the known failure "
            "mode (twice in dobby, 2026-08-05): the blind agent MUST refuse "
            "it — that refusal is the control working.\n"
            "Package: %d chars, %d events, %d pair orderings.\n\n"
        ) % (len(package), len(events), len(pairs))
        package = header + package

    out = Path(args.out) if args.out else None
    if out:
        out.write_text(package, encoding="utf-8")
        print(f"PART-B PACK: {out} ({len(package)} chars, "
              f"{len(events)} events, {len(pairs)} pair orderings)")
    else:
        print(package)
    return 0


def check(args: argparse.Namespace) -> int:
    adir = Path(args.repo).resolve() / args.analysis_dir
    catalogue = (adir / "event-catalogue.md").read_text(encoding="utf-8")
    events, pairs = _catalogue_ids(catalogue)
    blind = Path(args.check).read_text(encoding="utf-8")
    # A blind table is keyed by its FIRST cell. Counting id mentions
    # across whole rows flagged every cross-reference ("via E07 path")
    # as a duplicate, and a per-(state,event) table — finer than one
    # row per event, which is more information, not less — as invalid
    # (grpc-go addrconn pilot, 2026-08-07). Coverage now means: every
    # id keys >= 1 table row, and the final checklist ticks it exactly
    # once. A missing row must be impossible to miss; granularity is
    # the blind pass's choice.
    key_cells = []
    for ln in blind.split("\n"):
        s = ln.strip()
        if s.startswith("|"):
            key_cells.append(s.split("|")[1].strip().lstrip("*").strip())
    checklist = re.findall(r"^\s*- \[x\] ([\w-]+)\s*$", blind, re.M)
    errors: list[str] = []
    for ident in events + pairs:
        keyed = sum(1 for c in key_cells
                    if re.match(rf"{re.escape(ident)}(?![\w-])", c))
        if keyed == 0:
            errors.append(f"missing row: {ident} (no table row keyed by it)")
        ticks = checklist.count(ident)
        if ticks == 0:
            errors.append(f"missing checklist tick: {ident}")
        elif ticks > 1:
            errors.append(f"duplicated checklist entry: {ident} ({ticks}x)")
    if errors:
        print("PART-B COVERAGE: FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print(f"PART-B COVERAGE: OK ({len(events)} events, {len(pairs)} pair orderings)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis_dir", help="e.g. domain-analysis/trigger-service")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--requirements", action="append", default=[],
                        help="FILE or FILE:PATTERN (repeatable)")
    parser.add_argument("--contracts", action="append", default=[],
                        help="FILE:Class1,Class2 (repeatable)")
    parser.add_argument("--out", help="write the package here (default: stdout)")
    parser.add_argument("--check", metavar="BLIND_OUTPUT.md",
                        help="validate a blind table's coverage instead of assembling")
    parser.add_argument("--for-dispatch", action="store_true",
                        help="print the package with a dispatch header that warns "
                             "against placeholder dispatches")
    args = parser.parse_args()
    pack_root = Path(__file__).resolve().parent.parent
    if args.check:
        return check(args)
    if not args.requirements and not args.contracts:
        print("PART-B PACK: assemble mode needs --requirements and/or --contracts",
              file=sys.stderr)
        return 2
    try:
        return assemble(args, pack_root)
    except ValueError as error:  # missing inputs, undeliverable doctrine, stripped ids
        print(f"PART-B PACK: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
