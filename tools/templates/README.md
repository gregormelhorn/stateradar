# templates — consumer wrappers

Part of [tools](../README.md).

## Overview

This directory holds two files that a consuming repository copies into its
own tree. They connect the consumer's per-component analysis to the shared
checkers in the StateRadar pack. The files only delegate: each one locates
the pack checkout and runs a pack tool as a subprocess. No checking logic
lives here.

## Interface

- `check_matrix.py` — a per-component wrapper script.
  - Copy it to `<repo>/domain-analysis/<component>/check_matrix.py`.
  - Run it as `python3 domain-analysis/<component>/check_matrix.py`.
  - It runs `<pack>/tools/check_matrix.py <component-dir>` and passes the
    exit code through.
  - `ADIR` — the directory that holds the wrapper (the component analysis
    directory).
  - `_REPO` — `ADIR.parents[1]`, the analyzed repository.
  - `_SIBLINGS` — `ADIR.parents[2]`, the parent of the analyzed repository.
    This assumes the wrapper sits at `<repo>/domain-analysis/<component>/`.
  - `_CANDIDATES` — where the wrapper looks for the pack:
    - if `STATERADAR_PACK` is set to a non-empty value, it looks only
      there; a set-but-empty `STATERADAR_PACK` counts as unset;
    - otherwise it looks for the vendored submodule
      `<repo>/tools/prompt-pack` (the layout the root README recommends in
      [What you actually run](../../README.md#what-you-actually-run)), then
      for the sibling checkouts `_SIBLINGS/stateradar` and
      `_SIBLINGS/pack`, in that order.
  - `PACK` — the first candidate's `tools/check_matrix.py` that exists,
    else the first candidate's path, which then fails the existence check.
- `test_dsc_check.py` — a pytest template.
  - Copy it to `<repo>/tests/domain/test_dsc_check.py`.
  - Run it as `pytest tests/domain/test_dsc_check.py`. It requires
    `pytest`, which is not in `tools/requirements-dev.txt`.
  - `ROOT` — three levels above the test file, that is the consuming
    repository root.
  - `PACK_CHECKER` — defaults to `ROOT/tools/prompt-pack/tools/dsc_check.py`
    (the submodule layout). Adjust it for a vendored copy or a sibling
    checkout.
  - `COMPONENTS` — the sorted names of the directories under
    `ROOT/domain-analysis/` that contain an `analysis.json`. Each one
    becomes one parametrized test case. It is computed at import time, so
    a missing `ROOT/domain-analysis/` raises `FileNotFoundError` during
    pytest collection.
  - Each case runs `dsc_check.py` on `<ROOT>/domain-analysis/<component>`
    with `--repo ROOT` and working directory `ROOT`, and asserts exit
    code 0.
  - It adds `--model as-is.machine.mmd` when that file exists in the
    component directory and the component is not listed in
    `NO_MODEL_SYNC`.
  - `NO_MODEL_SYNC` — a set of component names, empty by default, that
    skip the Mermaid↔matrix sync check. Add a component to it when its
    diagram uses flat leaf names while its matrix rows are compound.
    - A compound row label is a lane family plus a leaf: the bold part
      names the family and the plain word after it names the leaf. For
      example, the row `| **Open** Idle |` declares the state `Open Idle`
      (family `Open`, leaf `Idle`).
    - `dsc_check.py` resolves a bare `Idle` drawn inside a
      `state Open { ... }` container to `Open Idle`, so such a diagram
      needs no entry. `NO_MODEL_SYNC` is for diagrams that draw the flat
      leaf `Idle` without the enclosing container.

## Invariants

- `STATERADAR_PACK` is exclusive. When it is set to a non-empty value, the
  sibling directories are never searched (`_CANDIDATES`).
- The wrapper contains no matrix-checking logic. It forwards the exit
  status of the pack's `tools/check_matrix.py` unchanged.
- If the pack checker is missing, the wrapper exits with code 2 and prints
  "pack checker missing; looked in: <locations> (set STATERADAR_PACK)" to
  stderr, listing every location it searched.
- `test_dsc_check.py` fails a component's case if `PACK_CHECKER` does not
  exist ("pack checker missing: <path>") or if `dsc_check.py` exits
  non-zero. The failure message includes the checker's stdout and stderr.

## Side Effects

- `check_matrix.py`:
  - reads the `STATERADAR_PACK` environment variable;
  - starts one subprocess,
    `sys.executable <pack>/tools/check_matrix.py <component-dir>`;
  - writes no files.
- `test_dsc_check.py`:
  - starts one `dsc_check.py` subprocess per component. With `--repo`,
    that checker runs `git diff` for the staleness check; see
    [tools Side Effects](../README.md#side-effects);
  - writes no files.

## Verification

Commands below run from the StateRadar pack root (not the consuming
repository) and assume the dev requirements are installed (see
[System Verification](../../README.md#system-verification)).

The selftest copies `check_matrix.py` into a temporary
`repo/domain-analysis/mini/` built from
[golden-mini](../../README.md#glossary) and checks these wrapper cases:

- "wrapper template, pack sibling stateradar" and
  "wrapper template, pack sibling pack": a sibling checkout is found and the
  check passes;
- "wrapper template, pack sibling absent": no pack is found and the output
  says "set STATERADAR_PACK";
- "wrapper template, wrong STATERADAR_PACK beside a sibling": a wrong
  explicit path fails even though a sibling exists;
- "wrapper template, STATERADAR_PACK": an explicit path is found and the
  check passes.

No pack test exercises `test_dsc_check.py`, and
`python3 tools/run_tool_tests.py` exercises neither template.

- Run: `python3 tools/selftest/run_selftest.py`
