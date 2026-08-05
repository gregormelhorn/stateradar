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
    """FILE:Class1,Class2 → docstring + fields blocks per class."""
    file_part, _, classes = spec.partition(":")
    path = repo / file_part
    if not path.is_file():
        raise ValueError(f"contracts file missing: {path}")
    if not classes:
        raise ValueError(f"contracts spec needs class names: {spec!r}")
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

    blocks: list[tuple[str, str]] = [("INPUT 1: EVENT CATALOGUE (verbatim)", catalogue)]
    for spec in args.requirements:
        blocks.append((f"INPUT 2: REQUIREMENTS ({spec})", _read_requirements(spec, repo)))
    for spec in args.contracts:
        blocks.append((f"INPUT 3: EVENT CONTRACT TEXTS ({spec})", _read_contracts(spec, repo)))

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
    table_rows = "\n".join(
        ln for ln in blind.split("\n") if ln.strip().startswith("|")
    )
    errors: list[str] = []
    for ident in events + pairs:
        n = len(re.findall(rf"(?<![\w-]){re.escape(ident)}(?![\w-])", table_rows))
        if n == 0:
            errors.append(f"missing row: {ident}")
        elif n > 1:
            errors.append(f"duplicated row: {ident} ({n} table rows)")
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
    args = parser.parse_args()
    pack_root = Path(__file__).resolve().parent.parent
    if args.check:
        return check(args)
    if not args.requirements and not args.contracts:
        print("PART-B PACK: assemble mode needs --requirements and/or --contracts",
              file=sys.stderr)
        return 2
    return assemble(args, pack_root)


if __name__ == "__main__":
    sys.exit(main())
