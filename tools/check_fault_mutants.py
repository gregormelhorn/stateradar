#!/usr/bin/env python3
"""Run declared cell suites against hand-authored fault-class implementation mutants.

Usage: python3 tools/check_fault_mutants.py <analysis-dir>
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
    """The fault-mutant configuration is invalid."""


@dataclass(frozen=True)
class Config:
    command: tuple[str, ...]
    component_root: Path
    rel_analysis: Path
    timeout_seconds: int


@dataclass(frozen=True)
class Mutant:
    fault: str
    identifier: str
    target: str
    variant: str
    cell: str


@dataclass(frozen=True)
class CommandResult:
    returncode: int | None
    output: str
    duration_seconds: float
    timed_out: bool = False
    launch_error: str | None = None


def load_config(adir: Path) -> tuple[Config, list[Mutant]]:
    config_path = adir / "fault-mutants.json"
    if not config_path.is_file():
        raise ConfigError("missing fault-mutants.json")
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
    component_root = (config_path.parent / working).resolve()
    if not component_root.is_dir():
        raise ConfigError("workingDirectory must resolve to a directory")

    timeout = raw.get("timeoutSeconds", DEFAULT_TIMEOUT_SECONDS)
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        raise ConfigError("timeoutSeconds must be a positive integer")

    rel_analysis = config_path.parent.relative_to(component_root)

    mutants_raw = raw.get("mutants")
    if not isinstance(mutants_raw, list) or not mutants_raw:
        raise ConfigError("mutants must be a non-empty array")

    mutants: list[Mutant] = []
    for index, entry in enumerate(mutants_raw):
        if not isinstance(entry, dict):
            raise ConfigError(f"mutant {index}: must be an object")
        for field in ("fault", "id", "target", "variant", "cell"):
            value = entry.get(field)
            if not isinstance(value, str) or not value:
                raise ConfigError(f"mutant {index}: missing {field}")
        variant_path = component_root / entry["variant"]
        if not variant_path.is_file():
            raise ConfigError(
                f"mutant {index}: missing variant file {entry['variant']}"
            )
        mutants.append(Mutant(
            fault=entry["fault"],
            identifier=entry["id"],
            target=entry["target"],
            variant=entry["variant"],
            cell=entry["cell"],
        ))

    return Config(tuple(command), component_root, rel_analysis, timeout), mutants


def copy_component(component_root: Path, tmp: Path, name: str) -> Path:
    destination = tmp / name
    shutil.copytree(component_root, destination)
    return destination


def command_for(command: tuple[str, ...], analysis_dir: Path) -> list[str]:
    return [str(analysis_dir) if part == PLACEHOLDER else part for part in command]


def run_command(config: Config, root_copy: Path) -> CommandResult:
    analysis_dir = root_copy / config.rel_analysis
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command_for(config.command, analysis_dir),
            cwd=root_copy,
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


def _print_verdict(
    number: int, mutant: Mutant, verdict: str, result: CommandResult
) -> None:
    exit_status = "timeout" if result.timed_out else str(result.returncode)
    print(
        f"MUT-{number:03d} {verdict} fault={mutant.fault} cell={mutant.cell} "
        f"target={mutant.target} exit={exit_status} duration={result.duration_seconds:.3f}s"
    )


COMPLETION_MARKER = " cells checked, "


def reported_cells(output: str) -> list[str]:
    """Cells the suite reported as failing, per the cell-failure contract."""
    cells = []
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("CELL FAIL "):
            cells.append(stripped[len("CELL FAIL "):].strip())
    return cells


def suite_completed(output: str) -> bool:
    """Whether the suite ran to the end of its cell loop.

    Per-cell 'CELL FAIL' lines are not sufficient evidence on their own. A suite
    can report one failing cell and then crash on a later one - that is exactly
    how a hollow kill proof arose in this fixture, and the declared cell was
    present in the output, so checking the cells alone would not have caught it.
    The completion line 'CELL SUITE: <n> cells checked, <m> failed' is only
    reached if the loop finished, which is what separates a clean failure from a
    crash. The exit code cannot: Python returns 1 for an unhandled exception,
    and pytest returns non-zero for internal errors too.
    """
    return any(
        line.strip().startswith("CELL SUITE: ") and COMPLETION_MARKER in line
        for line in output.splitlines()
    )


def run(adir: Path) -> int:
    config, mutants = load_config(adir)
    killed = survived = errors = blocked = 0

    with tempfile.TemporaryDirectory(prefix="fault-mutants-") as raw_tmp:
        tmp = Path(raw_tmp)
        baseline_copy = copy_component(config.component_root, tmp, "baseline")
        baseline = run_command(config, baseline_copy)
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

        for number, mutant in enumerate(mutants, start=1):
            mutant_copy = copy_component(config.component_root, tmp, mutant.identifier)
            target_path = mutant_copy / mutant.target
            variant_path = mutant_copy / mutant.variant
            target_path.write_text(variant_path.read_text(encoding="utf-8"), encoding="utf-8")
            result = run_command(config, mutant_copy)
            if result.timed_out or result.launch_error:
                errors += 1
                _print_verdict(number, mutant, "ERROR", result)
            elif result.returncode == 0:
                survived += 1
                _print_verdict(number, mutant, "SURVIVED", result)
            else:
                cells = reported_cells(result.output)
                if not suite_completed(result.output):
                    # The suite did not reach the end of its cell loop, so it
                    # crashed or does not implement the contract. Either way the
                    # non-zero exit is not evidence that the suite catches the
                    # fault, and must not count as a kill.
                    blocked += 1
                    _print_verdict(number, mutant, "BLOCKED", result)
                    print("  BLOCKED: suite did not run to completion "
                          "(no 'CELL SUITE: <n> cells checked, <m> failed' line)")
                elif not cells:
                    # Ran to completion but named no failing cell, while exiting
                    # non-zero. The verdict cannot be attributed to any cell.
                    blocked += 1
                    _print_verdict(number, mutant, "BLOCKED", result)
                    print(f"  BLOCKED: suite reported no cell failure "
                          f"(expected a 'CELL FAIL {mutant.cell}' line)")
                elif mutant.cell not in cells:
                    # The declared cell must be AMONG the reported cells, not
                    # the only one: a fault in one branch legitimately breaks
                    # several cells. But it must be there.
                    killed += 1
                    blocked += 1
                    _print_verdict(number, mutant, "KILLED (wrong cell)", result)
                    print(f"  WRONG CELL: declared {mutant.cell!r}, "
                          f"suite reported {cells}")
                else:
                    killed += 1
                    _print_verdict(number, mutant, "KILLED", result)

    if survived or errors or blocked:
        print(
            f"FAULT MUTANTS: FAIL (killed={killed} survived={survived} "
            f"errors={errors} blocked={blocked})"
        )
        return 1
    print(
        f"FAULT MUTANTS: OK (killed={killed} survived=0 errors=0 blocked=0)"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print(
            "Usage: python3 tools/check_fault_mutants.py <analysis-dir>",
            file=sys.stderr,
        )
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
