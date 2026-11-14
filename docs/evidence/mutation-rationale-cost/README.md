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
Source/test commit and reconciliation evidence will be recorded after freezing.
The live comparison follows the predeclared [protocol](protocol.md).
