#!/usr/bin/env python3
"""Run declared cell suites against temporary disposition-matrix mutants.

Usage: python3 tools/check_matrix_mutation.py <analysis-dir>
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from subprocess_text import as_text
from mutation_verdict import cell_verdict

PLACEHOLDER = "{analysis_dir}"
DEFAULT_TIMEOUT_SECONDS = 30


class ConfigError(Exception):
    """The component mutation configuration or matrix is invalid."""


@dataclass(frozen=True)
class Config:
    command: tuple[str, ...]
    working_directory: Path
    timeout_seconds: int
    oracle: str = "markdown"
    coverage_file: str | None = None


@dataclass(frozen=True)
class Cell:
    state: str
    event: str
    raw: str
    line_index: int
    column_index: int


@dataclass(frozen=True)
class Mutation:
    identifier: str
    state: str
    event: str
    kind: str
    old: str
    new: str
    line_index: int
    column_index: int


@dataclass(frozen=True)
class CommandResult:
    returncode: int | None
    output: str
    duration_seconds: float
    timed_out: bool = False
    launch_error: str | None = None


def load_config(adir: Path) -> Config:
    config_path = adir / "matrix-mutation.json"
    if not config_path.is_file():
        raise ConfigError("missing matrix-mutation.json")
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON: {exc.msg}") from exc
    if not isinstance(raw, dict):
        raise ConfigError("configuration must be a JSON object")
    version = raw.get("formatVersion")
    if not isinstance(version, int) or isinstance(version, bool) or version != 1:
        raise ConfigError("formatVersion must be integer 1")

    command = raw.get("testCommand")
    if not isinstance(command, list) or not command or any(
        not isinstance(part, str) or not part for part in command
    ):
        raise ConfigError("testCommand must be a non-empty array of strings")
    if command.count(PLACEHOLDER) != 1:
        raise ConfigError("testCommand must contain exactly one {analysis_dir}")

    working = raw.get("workingDirectory", ".")
    if not isinstance(working, str):
        raise ConfigError("workingDirectory must be a string")
    working_directory = (config_path.parent / working).resolve()
    if not working_directory.is_dir():
        raise ConfigError("workingDirectory must resolve to a directory")

    timeout = raw.get("timeoutSeconds", DEFAULT_TIMEOUT_SECONDS)
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        raise ConfigError("timeoutSeconds must be a positive integer")
    oracle = raw.get("oracle", "markdown")
    if oracle not in ("markdown", "sidecar"):
        raise ConfigError("oracle must be markdown or sidecar")
    coverage = raw.get("coverageFile")
    if coverage is not None and (not isinstance(coverage,str) or Path(coverage).is_absolute() or ".." in Path(coverage).parts):
        raise ConfigError("coverageFile must be a relative analysis file")
    return Config(tuple(command), working_directory, timeout, oracle, coverage)


def _states(lines: list[str]) -> tuple[str, ...]:
    for line in lines:
        if line.startswith("<!-- states: ") and line.endswith(" -->"):
            states = tuple(line[len("<!-- states: ") : -len(" -->")].split())
            if states:
                return states
    raise ConfigError("matrix has no states declaration")


def _split_row(line: str) -> list[str]:
    if not line.startswith("|") or not line.endswith("|"):
        raise ConfigError("matrix row is not a complete Markdown table row")
    return [part.strip() for part in line.strip("|").split("|")]


def _separator(row: list[str]) -> bool:
    return bool(row) and all(set(cell) <= {"-", ":"} for cell in row)


def parse_cells(matrix_path: Path) -> tuple[tuple[str, ...], list[Cell]]:
    lines = matrix_path.read_text(encoding="utf-8").splitlines()
    states = _states(lines)
    cells: list[Cell] = []
    seen: set[tuple[str, str]] = set()
    events: list[str] | None = None

    for line_index, line in enumerate(lines):
        if not line.startswith("|"):
            events = None
            continue
        row = _split_row(line)
        if row and row[0].lower() == "state":
            events = row[1:]
            if not events or len(events) != len(set(events)):
                raise ConfigError("matrix table has invalid event headers")
            continue
        if events is None or _separator(row):
            continue
        if len(row) != len(events) + 1:
            raise ConfigError("matrix row has wrong cell count")
        state = row[0].strip("*")
        if state not in states:
            raise ConfigError(f"matrix row has undeclared state {state!r}")
        for column_index, (event, raw) in enumerate(zip(events, row[1:], strict=True)):
            key = (state, event)
            if key in seen:
                raise ConfigError(f"matrix has duplicate cell {state} × {event}")
            if not raw:
                raise ConfigError(f"matrix has empty cell {state} × {event}")
            seen.add(key)
            cells.append(Cell(state, event, raw, line_index, column_index))
    if not cells:
        raise ConfigError("matrix has no cells")
    return states, cells


def _transition_parts(raw: str, states: tuple[str, ...]) -> tuple[str, str] | None:
    marker = "transition →"
    if not raw.startswith(marker):
        return None
    remainder = raw[len(marker) :]
    for target in sorted(states, key=lambda value: (-len(value), value)):
        if remainder == target:
            return target, ""
        if remainder.startswith(target) and len(remainder) > len(target) and remainder[len(target)].isspace():
            return target, remainder[len(target) :]
    return None


def transition_to_ignore(cell: Cell, states: tuple[str, ...]) -> str | None:
    parts = _transition_parts(cell.raw, states)
    if parts is None:
        return None
    return f"ignore (documented){parts[1]}"


def transition_target_swaps(cell: Cell, states: tuple[str, ...]) -> list[str]:
    parts = _transition_parts(cell.raw, states)
    if parts is None:
        return []
    current, suffix = parts
    return [f"transition →{target}{suffix}" for target in states if target != current]


def handle_to_ignore(cell: Cell) -> str | None:
    if cell.raw == "handle":
        return "ignore (documented)"
    if cell.raw.startswith("handle "):
        return f"ignore (documented){cell.raw[len('handle') :]}"
    return None


# A citation as gen_analysis_sidecar reads it: `file:line` (backticks around
# the whole token or the file name only, an optional line range), optionally
# followed by its ("fragment"), whose quotes may be typographic and whose
# text may itself hold quotes or file:line tokens (02-pilot rule 3).
_CITATION_START = re.compile(r"`?[\w./-]+\.[A-Za-z]{1,4}`?:\d+")
_CITATION = re.compile(r'`?[\w./-]+\.[A-Za-z]{1,4}`?:\d+(?:-\d+)?`?'
                       r'(?:\s*\(\s*["\u201c].*["\u201d]\s*\))?')


def trailing_citation(raw: str) -> str | None:
    """The last citation in a cell when nothing follows it but, at most, the
    parenthesis that closes a provenance note: 'reject (observed-in-code,
    a.go:3 ("x"))' keeps 'a.go:3 ("x")'.

    The last, not the first: a mutant keeps the citation that ends the cell,
    as before the fragment rule. The sidecar generator records the first
    citation that resolves to a source file instead; the two differ only in
    a cell that cites twice.
    """
    text = raw.rstrip()
    for end in (len(text), len(text) - 1 if text.endswith(")") else -1):
        if end < 0:
            continue
        body = text[:end].rstrip()
        for start in reversed([m.start() for m in _CITATION_START.finditer(body)]):
            if _CITATION.fullmatch(body, start):
                return body[start:]
    return None


def ignore_or_reject_to_handle(cell: Cell) -> str | None:
    """Reverse family: a decided no-action cell claims it acts.

    Eligible: 'ignore (documented)' and 'reject'. Holes ('ignore (accidental)',
    'UNSPECIFIED') and 'defer (queued)' are never mutated - see the wave spec.

    Only the trailing citation survives. Everything else the source cell carried
    is dropped, because an annotation that documented the old disposition is a
    lie under the new one: 'ignore (documented) DR-005; reason `f:1` ("x")' must
    become 'handle `f:1` ("x")', never 'handle DR-005; reason `f:1`', which would read as if
    DR-005 authorised handling. This is the wart handle_to_ignore still has.
    """
    for token in ("ignore (documented)", "reject"):
        if cell.raw == token:
            return "handle"
        if cell.raw.startswith(token + " "):
            citation = trailing_citation(cell.raw)
            return f"handle {citation}" if citation else "handle"
    return None


def build_mutations(states: tuple[str, ...], cells: list[Cell]) -> list[Mutation]:
    pending: list[tuple[str, str, str, str, Cell]] = []
    for cell in cells:
        replacement = transition_to_ignore(cell, states)
        if replacement is not None:
            pending.append((cell.state, cell.event, "transition-to-ignore", replacement, cell))
        for replacement in transition_target_swaps(cell, states):
            pending.append((cell.state, cell.event, "transition-target-swap", replacement, cell))
        replacement = handle_to_ignore(cell)
        if replacement is not None:
            pending.append((cell.state, cell.event, "handle-to-ignore", replacement, cell))
        replacement = ignore_or_reject_to_handle(cell)
        if replacement is not None:
            pending.append((cell.state, cell.event, "ignore-to-handle", replacement, cell))

    mutations: list[Mutation] = []
    for number, (state, event, kind, replacement, cell) in enumerate(sorted(pending), start=1):
        mutations.append(Mutation(
            f"MUT-{number:03d}", state, event, kind, cell.raw, replacement,
            cell.line_index, cell.column_index,
        ))
    return mutations


def copy_analysis(adir: Path, tmp: Path, name: str) -> Path:
    destination = tmp / name
    shutil.copytree(adir, destination)
    return destination


def apply_mutation(matrix_path: Path, mutation: Mutation) -> None:
    lines = matrix_path.read_text(encoding="utf-8").splitlines(keepends=True)
    line = lines[mutation.line_index]
    newline = "\n" if line.endswith("\n") else ""
    parts = line.rstrip("\n").split("|")
    part_index = mutation.column_index + 2
    original = parts[part_index]
    if original.strip() != mutation.old:
        raise RuntimeError(f"mutation source drifted for {mutation.identifier}")
    leading = original[: len(original) - len(original.lstrip())]
    trailing = original[len(original.rstrip()) :]
    parts[part_index] = f"{leading}{mutation.new}{trailing}"
    lines[mutation.line_index] = "|".join(parts) + newline
    matrix_path.write_text("".join(lines), encoding="utf-8")


def command_for(config: Config, analysis_dir: Path) -> list[str]:
    return [str(analysis_dir) if part == PLACEHOLDER else part for part in config.command]


def run_command(config: Config, analysis_dir: Path) -> CommandResult:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command_for(config, analysis_dir),
            cwd=config.working_directory,
            capture_output=True,
            text=True,
            timeout=config.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        # The partial output arrives as bytes even with text=True, and either
        # stream may be None: decode each one before joining them.
        output = as_text(exc.stdout) + as_text(exc.stderr)
        return CommandResult(None, output, time.monotonic() - started, timed_out=True)
    except OSError as exc:
        return CommandResult(None, str(exc), time.monotonic() - started, launch_error=str(exc))
    return CommandResult(completed.returncode, completed.stdout + completed.stderr, time.monotonic() - started)


def _print_mutation(mutation: Mutation, verdict: str, result: CommandResult) -> None:
    exit_status = "timeout" if result.timed_out else str(result.returncode)
    print(
        f"{mutation.identifier} {verdict} state={mutation.state} event={mutation.event} "
        f"kind={mutation.kind} old={mutation.old!r} new={mutation.new!r} "
        f"exit={exit_status} duration={result.duration_seconds:.3f}s"
    )


def sidecar_cells(adir: Path) -> tuple[tuple[str,...],list[Cell]]:
    data=json.loads((adir/"analysis.json").read_text())
    states=tuple(data["states"])
    events={e["id"] for e in data["events"]}
    cells=[]
    for c in data["cells"]:
        raw=c["disposition"]
        if raw=="transition":raw+=" →"+c["target"]
        cells.append(Cell(c["state"],c["event"],raw,-1,-1))
    keys={(c.state,c.event) for c in cells}
    if not states or not events or len(keys)!=len(cells) or keys!={(s,e) for s in states for e in events}:
        raise ConfigError("sidecar grid must be nonempty and total")
    return states,cells


def apply_sidecar(adir: Path, mutation: Mutation, states: tuple[str,...]) -> None:
    path=adir/"analysis.json"
    data=json.loads(path.read_text())
    matches=[c for c in data["cells"] if (c["state"],c["event"])==(mutation.state,mutation.event)]
    if len(matches)!=1:raise ConfigError("mutated cell absent or ambiguous")
    cell=matches[0]
    old=cell["disposition"]+(" →"+cell["target"] if cell["disposition"]=="transition" else "")
    if old!=mutation.old:raise ConfigError("sidecar mutation source drifted")
    parts=_transition_parts(mutation.new,states)
    cell["disposition"]="transition" if parts else mutation.new
    cell.pop("target",None)
    if parts:cell["target"]=parts[0]
    # A counterfactual oracle must not retain authority for the old judgment.
    for key in ("dr","q","rationale"):cell.pop(key,None)
    data["mutation"]={"id":mutation.identifier,"state":mutation.state,"event":mutation.event,"kind":mutation.kind}
    path.write_text(json.dumps(data,indent=2)+"\n")


def exclusions(adir: Path, config: Config, cells: list[Cell]) -> dict[tuple[str,str],str]:
    if config.coverage_file is None:return {}
    rows=json.loads((adir/config.coverage_file).read_text())["cells"]
    keys={(c.state,c.event) for c in cells}
    if len(rows)!=len(keys) or {(c["state"],c["event"]) for c in rows}!=keys:
        raise ConfigError("coverage file must cover each cell exactly once")
    excluded={}
    for c in rows:
        reason=c.get("untestable-via-seam")
        if reason is not None:
            if not isinstance(reason,str) or len(reason)<12 or c.get("test"):
                raise ConfigError("invalid untestable-via-seam declaration")
            excluded[c["state"],c["event"]]=reason
        elif not c.get("test"):
            raise ConfigError("coverage cell has neither a test nor a reason")
    return excluded


def run(adir: Path) -> int:
    config = load_config(adir)
    states, cells = sidecar_cells(adir) if config.oracle=="sidecar" else parse_cells(adir / "disposition-matrix.md")
    excluded=exclusions(adir,config,cells)
    eligible=[c for c in cells if (c.state,c.event) not in excluded]
    mutations = build_mutations(states, eligible)
    for (state,event),reason in sorted(excluded.items()):print(f"NOT APPLICABLE: {state} x {event}: {reason}")
    represented={(m.state,m.event) for m in mutations}
    for c in eligible:
        if (c.state,c.event) not in represented:
            print(f"NOT APPLICABLE: {c.state} x {c.event}: no supported operator for {c.raw}")
    if not mutations:raise ConfigError("no applicable mutations")
    killed = survived = errors = blocked = 0
    with tempfile.TemporaryDirectory(prefix="matrix-mutation-") as raw_tmp:
        tmp = Path(raw_tmp)
        baseline = run_command(config, copy_analysis(adir, tmp, "baseline"))
        if baseline.timed_out:
            print(f"BLOCKED: baseline timeout={config.timeout_seconds}s")
            return 1
        if baseline.launch_error:
            print(f"BLOCKED: baseline launch error={baseline.launch_error}")
            return 1
        if baseline.returncode != 0:
            print(f"BLOCKED: baseline exit={baseline.returncode}")
            return 1
        try:
            verdict=cell_verdict(baseline.output,len(eligible))
            if verdict.failed:raise ValueError("baseline claims failures with exit zero")
        except ValueError as exc:
            print(f"BLOCKED: baseline {exc}")
            return 1
        print("BASELINE: OK")
        for mutation in mutations:
            mutant_dir = copy_analysis(adir, tmp, mutation.identifier)
            if config.oracle=="sidecar":apply_sidecar(mutant_dir,mutation,states)
            else:apply_mutation(mutant_dir / "disposition-matrix.md", mutation)
            result = run_command(config, mutant_dir)
            if result.timed_out or result.launch_error:
                errors += 1
                _print_mutation(mutation, "ERROR", result)
            else:
                try:
                    verdict=cell_verdict(result.output,len(eligible))
                    if result.returncode==0 and verdict.failed:
                        raise ValueError("failure markers with exit zero")
                    if result.returncode!=0 and not verdict.failed:
                        raise ValueError("suite reported no cell failure")
                except ValueError as exc:
                    blocked+=1
                    _print_mutation(mutation,"BLOCKED",result)
                    print(f"  BLOCKED: {exc}")
                    continue
                if result.returncode==0:
                    survived+=1
                    _print_mutation(mutation,"SURVIVED",result)
                elif f"{mutation.state} x {mutation.event}" not in verdict.failed:
                    blocked+=1
                    _print_mutation(mutation,"BLOCKED (wrong cell)",result)
                else:
                    killed+=1
                    _print_mutation(mutation,"KILLED",result)

    if survived or errors or blocked:
        print(f"MUTATION CHECK: FAIL (killed={killed} survived={survived} errors={errors} blocked={blocked})")
        return 1
    print(f"MUTATION CHECK: OK (killed={killed} survived=0 errors=0 blocked=0)")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("Usage: python3 tools/check_matrix_mutation.py <analysis-dir>", file=sys.stderr)
        return 2
    try:
        return run(Path(args[0]).resolve())
    except ConfigError as exc:
        print(f"CONFIG ERROR: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"CONFIG ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
