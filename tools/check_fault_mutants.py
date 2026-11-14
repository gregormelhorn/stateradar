#!/usr/bin/env python3
"""Run complete cell suites against fault mutants, gated by executed projection canaries.

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

from subprocess_text import as_text
from mutation_verdict import cell_verdict

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
    expected_cells: int | None = None
    dependencies: tuple[tuple[str, str], ...] = ()


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

    expected = raw.get("expectedCells")
    if not isinstance(expected, int) or isinstance(expected, bool) or expected <= 0:
        raise ConfigError("expectedCells must be a positive integer")

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

    ids = [m.identifier for m in mutants]
    if len(ids) != len(set(ids)):
        raise ConfigError("duplicate mutant id")
    if any(i in ("baseline", ".", "..") or "/" in i or "\\" in i for i in ids):
        raise ConfigError("mutant id must be a unique directory name other than baseline")
    dependencies = projection_dependencies(adir, set(ids))
    return Config(tuple(command), component_root, rel_analysis, timeout, expected, dependencies), mutants


def projection_dependencies(adir: Path, ids: set[str]) -> tuple[tuple[str, str], ...]:
    """Read the existing generator's projection contract, without duplicating it.

    A canary may require the very projection it proves: that self edge is the
    bootstrap execution, never a cached assertion. All other cycles are invalid.
    """
    path = adir / "mutant-generation.json"
    if not path.exists():
        return ()
    try:
        raw = json.loads(path.read_text())
    except (ValueError, OSError) as exc:
        raise ConfigError(f"invalid mutant-generation.json: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError("mutant-generation.json must be an object")
    projections, bindings = raw.get("projections", {}), raw.get("bindings", [])
    if not isinstance(projections, dict) or not isinstance(bindings, list):
        raise ConfigError("projections must be an object and bindings an array")
    for name, projection in projections.items():
        if (not isinstance(projection, dict) or
                not isinstance(projection.get("provenBy"), str) or
                projection["provenBy"] not in ids):
            raise ConfigError(f"projection {name}: provenBy must name a declared mutant")
    dependencies = {}
    seen = set()
    for binding in bindings:
        if not isinstance(binding, dict) or not isinstance(binding.get("id"), str):
            raise ConfigError("binding must have a string id")
        identifier = binding["id"]
        if identifier not in ids or identifier in seen:
            raise ConfigError(f"unknown or duplicate binding id: {identifier}")
        seen.add(identifier)
        if "requiresProjection" not in binding:
            continue
        projection = binding["requiresProjection"]
        if not isinstance(projection, str) or projection not in projections:
            raise ConfigError(f"binding {identifier}: required projection undeclared")
        canary = projections[projection]["provenBy"]
        if canary != identifier:
            dependencies[identifier] = canary
    for identifier in dependencies:
        chain = set()
        current = identifier
        while current in dependencies:
            if current in chain:
                raise ConfigError(f"cyclic canary dependencies at {current}")
            chain.add(current)
            current = dependencies[current]
    return tuple(dependencies.items())


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
        # The partial output arrives as bytes even with text=True, and either
        # stream may be None: decode each one before joining them.
        output = as_text(exc.stdout) + as_text(exc.stderr)
        return CommandResult(None, output, time.monotonic() - started, timed_out=True)
    except OSError as exc:
        return CommandResult(None, str(exc), time.monotonic() - started, launch_error=str(exc))
    return CommandResult(completed.returncode, completed.stdout + completed.stderr, time.monotonic() - started)


def _print_verdict(
    number: int, mutant: Mutant, verdict: str, result: CommandResult
) -> None:
    exit_status = "timeout" if result.timed_out else str(result.returncode)
    print(
        f"MUT-{number:03d} {verdict} fault={mutant.fault} cell={mutant.cell} id={mutant.identifier} "
        f"target={mutant.target} exit={exit_status} duration={result.duration_seconds:.3f}s"
    )


def classify_result(result: CommandResult, cell: str, expected: int) -> tuple[str, str]:
    """One mutually exclusive verdict; nonzero exits alone never prove a kill."""
    if result.timed_out or result.launch_error:
        return "BLOCKED", "execution timeout or launch error"
    try:
        verdict = cell_verdict(result.output, expected)
    except ValueError as exc:
        return "BLOCKED", str(exc)
    if result.returncode == 0 and not verdict.failed:
        return "SURVIVED", "completed suite passed"
    if result.returncode != 1:
        return "BLOCKED", "exit code inconsistent with completed behavior verdict"
    if not verdict.failed:
        return "BLOCKED", "nonzero exit without failing cells"
    if cell not in verdict.failed:
        return "BLOCKED", f"WRONG CELL: declared {cell!r}, suite reported {sorted(verdict.failed)}"
    return "KILLED", "declared cell failed in completed suite"


def run(adir: Path) -> int:
    config, mutants = load_config(adir)
    assert config.expected_cells is not None  # validated by load_config
    expected = config.expected_cells
    dependencies = dict(config.dependencies)
    by_id = {m.identifier: m for m in mutants}
    numbers = {m.identifier: n for n, m in enumerate(mutants, 1)}
    outcomes: dict[str, str] = {}
    errors = 0  # diagnostic subset of BLOCKED, never an additional mutant verdict

    with tempfile.TemporaryDirectory(prefix="fault-mutants-") as raw_tmp:
        tmp = Path(raw_tmp)
        baseline_copy = copy_component(config.component_root, tmp, "baseline")
        baseline = run_command(config, baseline_copy)
        if baseline.timed_out or baseline.launch_error or baseline.returncode != 0:
            print(f"BLOCKED: baseline exit={baseline.returncode} timeout={baseline.timed_out} "
                  f"launch_error={baseline.launch_error}")
            return 1
        try:
            baseline_verdict = cell_verdict(baseline.output, expected)
            if baseline_verdict.failed:
                raise ValueError("exit 0 with failing cells")
        except ValueError as exc:
            print(f"BLOCKED: baseline {exc}")
            return 1
        print(f"BASELINE: OK (cells={expected})")

        def evaluate(identifier: str) -> str:
            nonlocal errors
            if identifier in outcomes:
                return outcomes[identifier]
            mutant = by_id[identifier]
            canary = dependencies.get(identifier)
            if canary is not None and evaluate(canary) != "KILLED":
                outcomes[identifier] = "BLOCKED"
                print(f"MUT-{numbers[identifier]:03d} BLOCKED id={identifier} fault={mutant.fault} "
                      f"cell={mutant.cell} canary={canary} verdict={outcomes[canary]}; not executed")
                return "BLOCKED"
            mutant_copy = copy_component(config.component_root, tmp, identifier)
            target_path = mutant_copy / mutant.target
            variant_path = mutant_copy / mutant.variant
            target_path.write_text(variant_path.read_text(encoding="utf-8"), encoding="utf-8")
            result = run_command(config, mutant_copy)
            verdict, reason = classify_result(result, mutant.cell, expected)
            outcomes[identifier] = verdict
            errors += int(result.timed_out or result.launch_error is not None)
            _print_verdict(numbers[identifier], mutant, verdict, result)
            if verdict == "BLOCKED":
                print("  BLOCKED: " + reason)
            if identifier in dependencies.values():
                print(f"CANARY id={identifier}: {verdict}")
            return verdict

        for mutant in mutants:
            evaluate(mutant.identifier)

    killed = sum(v == "KILLED" for v in outcomes.values())
    survived = sum(v == "SURVIVED" for v in outcomes.values())
    blocked = sum(v == "BLOCKED" for v in outcomes.values())
    ok = killed == len(mutants)
    print(f"FAULT MUTANTS: {'OK' if ok else 'FAIL'} (killed={killed} survived={survived} "
          f"errors={errors} blocked={blocked})")
    return 0 if ok else 1


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
