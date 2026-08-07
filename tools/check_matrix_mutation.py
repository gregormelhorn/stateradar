#!/usr/bin/env python3
"""Run declared cell suites against temporary disposition-matrix mutants.

Usage: python3 tools/check_matrix_mutation.py <analysis-dir>
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

PLACEHOLDER = "{analysis_dir}"
DEFAULT_TIMEOUT_SECONDS = 30


class ConfigError(Exception):
    """The component mutation configuration or matrix is invalid."""


@dataclass(frozen=True)
class Config:
    command: tuple[str, ...]
    working_directory: Path
    timeout_seconds: int


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
    return Config(tuple(command), working_directory, timeout)


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
        if row and row[0] == "state":
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
        output = (exc.stdout or "") + (exc.stderr or "")
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
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


def run(adir: Path) -> int:
    config = load_config(adir)
    states, cells = parse_cells(adir / "disposition-matrix.md")
    mutations = build_mutations(states, cells)
    killed = survived = errors = 0
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
        print("BASELINE: OK")
        for mutation in mutations:
            mutant_dir = copy_analysis(adir, tmp, mutation.identifier)
            apply_mutation(mutant_dir / "disposition-matrix.md", mutation)
            result = run_command(config, mutant_dir)
            if result.timed_out or result.launch_error:
                errors += 1
                _print_mutation(mutation, "ERROR", result)
            elif result.returncode == 0:
                survived += 1
                _print_mutation(mutation, "SURVIVED", result)
            else:
                killed += 1
                _print_mutation(mutation, "KILLED", result)
    if survived or errors:
        print(f"MUTATION CHECK: FAIL (killed={killed} survived={survived} errors={errors} blocked=0)")
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
