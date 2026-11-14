# Mutation binding, structured rationale and bounded cost comparison

This increment follows the reconciled weighted-semaphore evaluation. It changes
no runtime behavior or accepted domain decision. All thirteen DRs remain the
authority. Historical pilot artifacts and their 52 retained hashes are intact.

## Executed mutation work

- `mutation-red.txt` / `mutation-green.txt`: four regression cases demonstrate
  that crashes, zero discovery and unrelated cell failures previously counted
  incorrectly, and that a JSON oracle must actually reach the cell suite.
- `semaphore-fault-initial.txt`: two kills, one survivor (`Release(0)`) and one
  blocked result (selected-waiter rollback failed only a pair scenario).
- The cell representatives now also execute the already-decided DR-013 zero
  release and DR-010 selected-waiter rollback scenarios. No existing test or
  runtime implementation was weakened, removed or modified.
- `semaphore-matrix-final.txt`: all 41 supported oracle mutations killed through
  the completed behavioral suite. These cover 32 of 38 cells: four explicit
  contract limits and two `defer (queued)` cells without supported operators
  are not counted as kills. The earlier `semaphore-matrix.txt` is exploratory;
  the template changed during that run. The final run uses one fixed template.
- `semaphore-fault-final.txt`: four generated source mutants killed by their
  named cells. Runtime compilation or incomplete execution never counts.

## Executed rationale work

`rationale-red.txt` records the six original missing-evidence failures.
`rationale-decision-binding-red.txt` demonstrates a separate accepted DR plus
an unrelated valid fragment slipping through. Its green counterpart checks
that the citation now references the named decision. `rationale-green-final.txt`
also checks regeneration, outcome drift and refusal to discard adopted reasons.
All 38 current cells have structured rationale, with explicit scenario scope.
See [format](../../cell-rationale.md). Structural checks do not prove entailment.

## Acceptance

Commands run from the repository root with `.venv/bin` on PATH:

```sh
bash /tmp/stateradar-main-full-gates.sh
python tools/selftest/test_pilot_accounting.py
python tools/selftest/test_mutation_binding.py
python tools/selftest/test_cell_rationale.py
python examples/weighted-semaphore/verify_q01.py --output-dir /tmp/semaphore-mutation-decisions-final
python examples/weighted-semaphore/domain-analysis/weightedSemaphore/verify.py
python tools/gen_mutant_variants.py examples/weighted-semaphore/domain-analysis/weightedSemaphore --check
python tools/check_matrix_mutation.py examples/weighted-semaphore/domain-analysis/weightedSemaphore
python tools/check_fault_mutants.py examples/weighted-semaphore/domain-analysis/weightedSemaphore
```

The shell commands are retained in `pack-gates-command.txt`. Outputs are in
`pack-gates.txt`, `accounting-tests.txt`, `decision-gates.txt`, `model-gates.txt`
and the named mutation/rationale logs. CI runs the same suites directly.
Source/test commit: `9b3723e`. Its staleness signal is retained in
`source-commit-stale.txt`. The artifact-only refresh pins that commit and reruns
full model, decision and pack acceptance in `reconciled-*.txt`, all exit 0.
The current model checker verifies 232 structured citation occurrences.
The live comparison follows the predeclared [protocol](protocol.md).


## Completed matched comparison

Both live gobreaker arms used pack `89a4798`, signed-in Sol/medium and the same
source/settings. Routed: seven gates, $1.1220648 combined conservative equivalent,
11 rereads. Matrix: nine gates, $1.1681280, 14 rereads. Complete controller usage
and settled provider accounting exist for both. Both cover all four primary
controls and kill the supplemental stale-generation mutant in five repetitions.
Both miss the concrete wrapper-reassignment outcome. Keep routed as the default.
See [comparison](comparison.md), [coverage review](coverage.md) and
[machine-readable measurements](measurements.json) for cost assumptions,
unmetered review boundaries, grouping differences, test depth and raw evidence.
The old Pool cost gap remains unknown.

`generator-parent-red.txt` is an additional post-implementation regression
check against isolated parent `0e7ff1c`: its generator drops adopted rationale.
It is not presented as a pre-implementation run. The final generator preservation
and refusal tests pass. `final-pack.txt`, `final-rationale.txt` and
`final-mutation-binding.txt` record the closing repository checks.
