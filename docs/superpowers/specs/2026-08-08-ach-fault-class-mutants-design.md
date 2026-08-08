# ACH Fault-Class Mutant Design — F-04 Sneak-Path v1

**Date:** 2026-08-08
**Scope:** Prove roadmap item 8 on one fault class with one implementation
mutant, one behavioral cell suite, and red/green evidence.

## Goal

Show that a **behavioral** cell suite kills an implementation mutant that
violates the matrix via F-04 (sneak path), and that a mirroring
string-comparison suite does not. This separates item 8 from item 7: item 7
mutates the spec, item 8 mutates the implementation.

## The F-04 binder, operationalized

`formats/rules.toml` already declares `F-04 sneak path` with binder
`sneak-path` and the line "events accepted where the specification says
ignore or reject". v1 gives the binder one concrete mutation operator:

> **sneak-path operator:** a cell whose disposition is `ignore (documented)`
> or `reject` accepts the event — the implementation ignores instead of
> rejecting, or transitions instead of ignoring.

## Architecture

### Real golden-mini implementation

`tests/golden-mini/src/mini.py` becomes a real state machine honoring the
existing 3-state × 3-event matrix. The declared seam is a `Mini` class with
`deliver(event_id)` returning an outcome (`transition`, `ignored`,
`handled`, or raising `RejectedError`) plus the projected `state` and the
duplicate counter. Matrix citations in `disposition-matrix.md` update to the
new line numbers. `tests/golden-mini/expected/analysis.json` is regenerated
and committed because the sidecar carries those citations.

### Behavioral cell suite

`tests/golden-mini/tests/test_cell_suite.py` is rewritten. It:

1. Reads `disposition-matrix.md` from the analysis directory passed as
   `{analysis_dir}`.
2. Navigates to each state through the seam only (`M1` from `Idle` reaches
   `Open`; `M1`,`M2` reaches `Closed`). No state injection.
3. Delivers every event per state and maps outcomes to the disposition
   vocabulary: `transition →X` requires the projected target state,
   `handle` requires the counter increment with state unchanged,
   `ignore (documented)` requires no state change, `reject` requires
   `RejectedError` with state unchanged.
4. Exits 0 only when every cell matches; prints one line per mismatch and
   exits 1.

The same suite serves both checkers:

- **Item 7:** the matrix mutation checker passes a mutated matrix copy as
  `{analysis_dir}`. The implementation does not change, so the suite
  detects the spec change and exits nonzero — the mutant is killed.
- **Item 8:** the fault-mutant checker swaps the implementation file. The
  matrix is unchanged, so the suite detects the sneak path and exits
  nonzero — the mutant is killed.

### Fault-mutant checker

New tool `tools/check_fault_mutants.py <analysis-dir>`. The component opts
in with `fault-mutants.json` beside `disposition-matrix.md`:

```json
{
  "formatVersion": 1,
  "testCommand": ["python3", "tests/test_cell_suite.py", "{analysis_dir}"],
  "workingDirectory": "../..",
  "timeoutSeconds": 5,
  "mutants": [
    {
      "fault": "F-04",
      "id": "F-04-sneak-path-Closed-M1",
      "target": "src/mini.py",
      "variant": "src/mutants/mini.F-04-sneak-path.py",
      "cell": "Closed x M1"
    }
  ]
}
```

Execution:

1. Resolve the component root from `workingDirectory` (relative to the
   config file's parent). Compute the analysis directory's relative path
   inside it.
2. Copy the component root to a temporary directory. Run the baseline
   command there. A failing or timed-out baseline is `BLOCKED`.
3. For each mutant, make a fresh temporary copy, replace `target` with
   `variant`, run the command with `{analysis_dir}` pointing inside the
   copy.
4. Verdicts: nonzero exit is `KILLED`, zero is `SURVIVED`, timeout or
   launch error is `ERROR`. Any survivor or error exits nonzero.

The checker never edits or patches code itself. Mutants are explicit
variant files shipped with the component. This keeps v1 honest: one
hand-authored mutant per fault class until binder-driven generation exists.

### Sneak-path mutant

`tests/golden-mini/src/mutants/mini.F-04-sneak-path.py` is `mini.py` with
exactly one change: `Closed × M1` returns `ignored` instead of raising
`RejectedError`. The matrix says `reject` for that cell. The behavioral
suite kills it. A mirroring suite that only compares matrix text does not.

## Selftest additions

In `tools/selftest/run_selftest.py`:

1. **Green baseline:** `check_fault_mutants.py` on golden-mini exits 0 with
   `FAULT MUTANTS: OK (killed=1 ...)`.
2. **Kill proof:** the F-04 mutant is reported `KILLED`.
3. **Mirroring blind spot:** a string-comparison suite that parses the
   matrix and always exits 0 reports the mutant `SURVIVED`, and the checker
   exits nonzero. This is the F-21 evidence that justifies item 8.
4. **Item 7 regression:** `check_matrix_mutation.py` on golden-mini still
   kills all 9 spec mutants with the behavioral suite.
5. **Config errors:** missing `fault-mutants.json`, bad `formatVersion`,
   missing variant file, and missing or repeated `{analysis_dir}` each
   produce `CONFIG ERROR`.
6. **Blocked baseline:** a failing baseline reports `BLOCKED` and no mutant
   lines.

## Integration

- `fault-mutants.json` registered as a Testgen artifact in
  `tools/check_pack_consistency.py` (with the required red probe first:
  registration fails until `04-testgen.md` defines it).
- `prompts/04-testgen.md` gains the fault-class hardening subsection: the
  F-04 operator definition, the `fault-mutants.json` contract, and the rule
  that a surviving mutant is a suite finding, never a reason to weaken a
  test.
- `README.md` tool list gains `check_fault_mutants`.
- `docs/roadmap.md` item 8 moves to a partial status: F-04 shipped with
  end-to-end proof; remaining classes pending.

## Non-goals

- No binder-driven mutant generation. Variants are hand-authored in v1.
- No other fault classes (F-05, F-06, F-07+).
- No `rules.toml` schema change. The existing `binder = "sneak-path"`
  field already names the operator; v1 defines it in the prompt and spec.
- No change to `tools/check_matrix_mutation.py`.
- No release, tag, or push without explicit instruction.

## Verification

Focused proofs first (baseline green, mutant killed, mirroring survives),
then the full gate set:

```bash
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
python3 tools/benchmark_evidence.py
git diff --check
```

All must be green. The commit body records the red and green outputs.

## Completion boundary

A local commit completes v1. Roadmap item 8 becomes partially shipped
(F-04 only). No upstream runs, no silenceper changes, no release or push.
