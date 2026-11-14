# Generic canary execution and strict fault verdicts

The general fault runner now executes the projection canaries declared by
`mutant-generation.json`. A shared canary runs once before its dependents; only
a completed correct-cell kill unlocks them. Other outcomes block dependent
execution. The semaphore-specific comparison now uses the shared classifier.

`expectedCells` is required in `fault-mutants.json` (semaphore 34, golden-mini
24). Baseline and mutant executions must meet that declared nonzero count,
report consistent unique cell failures, and agree with exit status. Wrong-cell
failures no longer increase the killed counter. Each mutant has exactly one
verdict; the `errors` diagnostic counts only execution errors within BLOCKED.
See [the execution contract](../../fault-mutants.md).

## Observed failure paths and results

- `runner-red.txt`: six initial regression tests fail in 21 assertions/subcases
  against the previous runner. Canary failure does not prevent dependent
  execution; malformed/partial results and wrong-cell accounting are exposed.
- `malformed-red.txt`: an additional malformed `CELL FAIL` line initially becomes
  SURVIVED. The shared parser now rejects it; this also protects matrix checking.
- `runner-green.txt`: nine tests pass, including real subprocess executions,
  dependency order/reuse, transitive blocking, invalid metadata, exact counts,
  inconsistent results, wrong cells, timeout and incomplete/empty discovery.
- `semaphore.txt`: the general runner executes `zero-charges` first, then kills
  all five declared source mutants; killed=5, survived=0, errors=0, blocked=0.
- `semaphore-weak.txt`: the real weak Go suite completes ten repetitions for
  baseline and canary. The canary survives; dependent F-09 is not executed.
  Counts: killed=0, survived=1, errors=0, blocked=1. The control requires this
  nonzero inner result and returns success only when the expected block occurs.
- `golden-mini.txt`: six mutants killed, with the shared counter canary executed
  once before the two dependent variants.

The old pack selftest that treated `python -c 'exit(0)'` as a surviving mirroring
suite is corrected to require BLOCKED. A separate actual matrix-visiting,
implementation-blind loop retains the mirroring negative control: four
independent mutants/canaries survive and two projection dependents are blocked.
No component behavior tests were weakened or removed.

CI includes the new regression suite and real semaphore weak-canary control.
Full acceptance, including all previous gates (exit 0 in `implementation-gates.txt`):

```sh
bash docs/evidence/generic-canary/scripts/full_gates.sh
```

## Second-component assessment

[addrConn readiness](addrconn-readiness.md) records the pinned source and callee
contracts, executed upstream baseline/omission probe, and artifact limitations.
The existing BackoffCancel test passes even without local addrConn cancellation;
parent cancellation can mask the omission. A narrow backoff-worker seam with
the parent kept alive is a proposed next scope. There is no second-component
F-09 kill claim, no decision on the 16 historical questions, and no new model
API cost experiment.

The artifact-only reconciliation pins semaphore manifest and sidecar to
`1438728` (the tested implementation commit) and watches the generic runner.
`staleness-red.txt` records the expected stale anchor before refresh;
`reconciled-gates.txt` records the complete final rerun (exit 0). The source
implementation, all semaphore decisions and both historical benchmark archives
remain unchanged. The archived addrConn checker failure is a readiness finding,
not a suppressed active-pack gate.
