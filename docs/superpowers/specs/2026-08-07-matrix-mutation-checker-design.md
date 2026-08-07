# Matrix Mutation Checker Design

**Date:** 2026-08-07  
**Scope:** Add a pack tool that checks whether a declared cell suite detects controlled mutations of a disposition matrix.

## Goal

Add `tools/check_matrix_mutation.py`. The tool mutates a temporary matrix copy.
It runs the component cell suite against that copy. The tool reports whether
the suite kills or misses each mutation.

A surviving mutant shows that the declared suite does not detect one changed
matrix contract. The tool does not mutate source code.

## Scope

The first version supports these matrix mutations only:

1. Change `transition → Target` to `ignore (documented)`.
2. Replace a transition target with another declared state.
3. Change `handle` to `ignore (documented)`.

The tool works only for a component that has a disposition matrix and a valid
`matrix-mutation.json` file. It runs the suite command from that file.

## Non-goals

- Do not mutate implementation source, generated tests, sidecars, DRs, or
  question registers.
- Do not add guard syntax or guard-negation mutations.
- Do not add all disposition substitutions.
- Do not run a shell command string.
- Do not change silenceper or any upstream project.
- Do not claim that a killed mutant proves the implementation is correct. It
  proves only that the declared suite detects the changed matrix contract.

## Component Contract

A component opts in with `matrix-mutation.json` beside its
`disposition-matrix.md` file.

```json
{
  "formatVersion": 1,
  "testCommand": [
    "python3",
    "tests/test_cell_suite.py",
    "{analysis_dir}"
  ],
  "workingDirectory": "../..",
  "timeoutSeconds": 30
}
```

`testCommand` is a JSON array of non-empty strings. It contains exactly one
`{analysis_dir}` token. The checker replaces that token with the temporary
mutated analysis directory.

`workingDirectory` is optional. When present, it is a relative path from the
configuration file directory. When absent, the checker uses that directory.

`timeoutSeconds` is optional. It must be a positive integer. The default is
30 seconds.

The command must read the supplied analysis directory. A suite that ignores the
directory can run but its mutants will survive.

## Execution Model

1. Read the matrix and the component configuration.
2. Validate the configuration before it starts a child process.
3. Copy the complete analysis directory into a temporary directory.
4. Run the declared command once against the unmodified temporary copy.
5. Stop with `BLOCKED` if that baseline command fails or times out.
6. Create one temporary copy for each deterministic mutant.
7. Replace only the selected cell in that copy.
8. Run the declared command with the mutated copy substituted for
   `{analysis_dir}`.
9. Remove every temporary copy after the result is recorded.

The checker sorts states, events, targets, and mutation kinds. It gives every
mutant a stable ID from its state, event, and mutation kind.

## Verdicts and Exit Status

| Verdict | Command result | Checker result |
|---|---|---|
| `KILLED` | nonzero exit before the timeout | continue |
| `SURVIVED` | zero exit | record a failure |
| `ERROR` | command launch error or timeout | record an error |
| `BLOCKED` | baseline nonzero exit or timeout | stop before mutation |

The checker exits zero only if the baseline passes and every mutant is killed.
It exits nonzero if any mutant survives, any mutation run errors, or the
configuration is invalid.

The report lists the mutant ID, state, event, mutation kind, old cell, new
cell, command exit status, duration, and verdict. It prints a final count for
killed, survived, errors, and blocked results.

## Fixture and Selftest

Extend `tests/golden-mini` with:

- `domain-analysis/mini/matrix-mutation.json`;
- a small cell-suite command that accepts the supplied analysis directory;
- expected matrix contracts for the nine fixture cells.

The cell suite reads the provided `disposition-matrix.md`. It fails when a
supported fixture mutation changes an expected cell contract.

Add deterministic selftest cases to `tools/selftest/run_selftest.py`:

1. A weak command that exits zero causes at least one `SURVIVED` result and a
   nonzero checker exit.
2. The golden-mini command kills every supported mutant and returns zero.
3. Missing configuration fails.
4. A missing or repeated `{analysis_dir}` token fails.
5. A non-array command fails.
6. A baseline failure reports `BLOCKED` and creates no mutation verdicts.
7. A timeout reports `ERROR` or `BLOCKED`, as applicable.

The selftest must observe the red failure before it observes the green result.

## Integration

Add the tool to the pack consistency source-to-prompt map under
`04-testgen.md`. Add it to the README tool list and the local checker command
section. Update roadmap item 7 from planned to shipped only after the red and
green selftests pass.

Do not add a new methodology rule or fault class in this version. The checker
is a Testgen assurance tool, not a new analysis rule.

## Verification

Before the implementation commit, run the focused mutation selftest, then run:

```bash
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
python3 tools/benchmark_evidence.py
git diff --check
```

The complete gate set must be green. The commit body must contain the observed
red and green mutation-checker output.

## Completion Boundary

A local pack commit completes this work. Do not add an upstream mutation run,
change silenceper behavior, create a release, create a tag, or push without a
new user instruction.
