# Cell-Failure Contract: Make "KILLED" Mean Something

**Date:** 2026-08-10
**Scope:** Declare a machine-readable cell-failure line for cell suites, and
use it so `KILLED` distinguishes "the suite caught the mutant" from "the suite
crashed".
**Status:** measured; ready to plan.

## Measured state, at commit `5d037e7`

### What decides a verdict today

`tools/check_fault_mutants.py:186` — the verdict rests on the exit code alone:

```python
elif result.returncode == 0:
    ... SURVIVED
else:
    ... KILLED
```

`CommandResult.output` captures `stdout + stderr` (line 145) and nothing ever
reads it. `check_matrix_mutation.py` works the same way.

### What the suite already prints

`tests/golden-mini/tests/test_cell_suite.py:84`:

```python
print(f"MISMATCH {state} × {event}: {problem}")
```

Machine-readable by accident, never agreed as a contract, and it uses `×`
(U+00D7) while `fault-mutants.json` declares cells as `"Closed x M1"` in ASCII.

### How many suites exist

```text
cell suites in the repo:  exactly one (tests/golden-mini/tests/test_cell_suite.py)
testCommand entries:      2, both pointing at that one suite
documented output format: none
```

`prompts/04-testgen.md:45` states what to assert per disposition. It says
nothing about how a failure must be reported.

So the migration cost is one suite. The lasting cost is doctrine: every future
component must satisfy the contract, which is the point.

### Why a strict "declared cell" rule is wrong

Measured in the previous wave and carried forward, because it killed the
obvious design:

```text
Matrix mutants: 25/25 die at exactly the mutated cell, 0 crashes.

Fault mutants, declared cell -> cells actually reported:
  Closed x M1      -> [Closed×M1]                          single
  Open x M2 (F-01) -> [Closed×M1, Open×M2]                  more
  Open x M2 (F-02) -> [Closed×M1, Open×M2]                  more
  Open x UV-M1-dup -> [Closed×…, Idle×…, Open×UV-M1-dup]     more
```

F-01 breaks the transition that `NAVIGATE["Closed"]` depends on, so cells in
`Closed` fall with it. F-05 corrupts a state-independent handler, so all three
`UV-M1-dup` cells fail. The implementation has about eight branches for 21
cells; a fault is not confined to one cell. **"Dies from exactly the declared
cell" would fail 3 of 4 legitimate mutants.**

### The case that motivates the wave

The historical hollow F-04, before its resynchronisation:

```text
exit=1   MISMATCH=[Closed×M1]   crash=True
```

`exit != 0`, so it counted as `KILLED`. But the suite had crashed with a
`ValueError` on a missing event branch. A pseudo-mutant containing no F-04
mutation at all also scored `KILLED`. The declared cell *was* among those
reported — so the declared-cell criterion would not have caught it either.
**Only the crash distinguishes it,** and a crash is indistinguishable from a
failure by exit code: Python returns 1 for an unhandled exception, and pytest
returns non-zero for internal errors too.

## The contract

A cell suite must print one line per failing cell, on stdout:

```text
CELL FAIL <state> x <event>
```

ASCII `x` as the separator, matching how `fault-mutants.json` already declares
`cell`. The existing human-readable `MISMATCH … × …` line stays; the new line is
additional, so nothing that reads the old output breaks.

The line is a claim with two consequences:

- **its presence** means the suite reached its assertions and reported a
  verdict, rather than dying on the way
- **its content** names which cells the suite judged wrong

## The rule

In `check_fault_mutants.py`, for each mutant:

| observation | verdict |
|---|---|
| exit 0 | `SURVIVED` (unchanged) |
| exit ≠ 0, ≥1 `CELL FAIL` line, declared cell among them | `KILLED` |
| exit ≠ 0, ≥1 `CELL FAIL` line, declared cell **not** among them | `KILLED (wrong cell)` — a finding, exit non-zero |
| exit ≠ 0, **no** `CELL FAIL` line | `BLOCKED: suite did not report a cell failure` |

The last row is the one that matters. A mutant that makes the suite crash is
not evidence that the suite catches the fault, so it must not be counted as a
kill. `BLOCKED` rather than `ERROR` because the pack's doctrine is that an
ambiguous outcome is stated, never guessed.

Note the rule deliberately requires the declared cell to be **among** the
reported cells, not the only one. That is the corrected criterion; the strict
version is refuted above.

### Suites that do not implement the contract

`BLOCKED: suite printed no CELL FAIL line` fires for them too. That is
intentional: without the line the checker cannot tell a catch from a crash, and
silently falling back to exit-code-only semantics would reinstate exactly the
ambiguity this wave removes. Only one suite exists today, so the migration is
one file.

## Red probes, both constructible

1. **Crash instead of failure.** Build a variant in a temp copy that omits an
   event branch, as the historical F-04 did. Expect
   `BLOCKED: suite did not report a cell failure` and a non-zero checker exit.
   Before the rule, that same variant reports `KILLED`.
2. **Wrong cell.** Declare a mutant's `cell` as a cell it does not affect.
   Expect `KILLED (wrong cell)`. Before the rule it reports plain `KILLED`.

Both must be observed red-before and correct-after. Neither requires changing
a tracked fixture.

## Surfaces that move

- `tests/golden-mini/tests/test_cell_suite.py` — emit `CELL FAIL <state> x <event>`
- `tools/check_fault_mutants.py` — the rule and the two new outcome strings
- `tools/selftest/run_selftest.py` — the two red probes plus a green case
- `prompts/04-testgen.md` — declare the contract for every future cell suite
- `docs/roadmap.md` item 8 — record that kill proofs are now cause-checked

Not moved: `check_matrix_mutation.py`. Its 25 mutants were measured to die at
exactly the mutated cell with zero crashes, so there is no defect to fix there
and widening the change would double the blast radius for no measured gain. It
becomes a named follow-up once the contract has proven itself on the fault
checker.

## Non-goals

- no change to `check_matrix_mutation.py` in this wave
- no change to `part_b_pack.py`, `gen_mutant_variants.py`, or the region gate
- no new fault classes, no fixture events, no real-component work
- no `defer` family
- no CHANGELOG entry, no version bump, no release, tag, or push

## Verification

```bash
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
uv run --with jsonschema python3 tools/dsc_check.py tests/golden-mini/domain-analysis/mini --repo tests/golden-mini
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
git diff --check
```

Expected: `FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)` — the
same four kills as before, but now each one proven to have been caused by its
declared cell rather than merely correlated with a non-zero exit.
`MUTATION CHECK: OK (killed=25 ...)` unchanged.

## Completion boundary

Local commits complete the wave. No release. No tag. No push.
