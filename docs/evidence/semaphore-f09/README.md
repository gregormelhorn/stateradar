# Semaphore F-09 cancellation-leak slice

The generated `omit-cancel-unlink` mutant removes only
`s.waiters.Remove(elem)` from the queued cancellation branch. `Acquire` still
returns `context.Canceled`, but its queue entry remains and prevents access to
otherwise free capacity. This is a separate F-09 binding, not a renamed F-05
counter/rollback mutation. The evaluated implementation remains unchanged.

The oracle is the accepted DR-010 error-return guarantee: no own holding or
queue entry remains after an error. DR-005 supplies the cancellation/abandonment
obligation. No new owner decision or fixed-latency contract is introduced.

## Executed comparison

Command (from repository root):

```sh
.venv/bin/python tools/semaphore_f09.py --output-dir docs/evidence/semaphore-f09/runs
```

| Run | Observed result | Evidence |
|---|---|---|
| Full baseline | PASS, 34 cells and 16 pair orderings complete | `runs/full-baseline.go.jsonl` |
| Weak baseline | PASS, 10 race-detector repetitions | `runs/weak-baseline.txt` |
| Independent capacity canary `zero-charges` | KILLED at `Acquire_NoWaiters x Release` | `runs/capacity-canary.txt` |
| Same canary under weak suite | SURVIVED; rejected by the canary gate | `runs/weak-canary-control.txt`, `comparison.txt` |
| F-09 under weak suite | SURVIVED in all 10 repetitions | `runs/weak-f09.txt` |
| F-09 under full suite | KILLED at `Acquire_WaitersPending x ContextDone`; complete suite | `runs/full-f09.txt`, `runs/full-f09.go.jsonl` |

The result-only weak test queues an Acquire behind a holding, cancels it, and
checks the returned error. A read-only scheduling barrier establishes enqueue;
no private field is mutated. Deliberately, it makes no post-cancel resource
assertion. It is a separate negative control and never replaces a contract test.

The full cancellation cell calls `numericAvailable(s, 2)` after consuming the
error. This public `TryAcquire`/`Release` projection fails on the retained queue
entry. The full run reports 12 failing cells, including the declared target;
other failures reflect the same leak in shared scenarios or cleanup. These are
not twelve independent defects. The cell runner requires all 34 cell scenarios
and 16 pair orderings to finish before emitting mutation-verdict evidence.

The independently generated `zero-charges` canary corrupts capacity at Release,
not at cancellation. Its observed correct-cell kill proves that the public
capacity projection is exercised. The slice runner executes this canary before
F-09. Survival, timeout, incomplete discovery, inconsistent accounting, or a
failure at only an unrelated cell blocks dependent execution. The weak-canary
control passes its actual SURVIVED verdict into the same gate and observes
BLOCKED. The subsequent F-09 weak run is a deliberate negative control under the
already verified full-suite projection, not an assertion that the weak suite
has adequate observability. This preflight is implemented in the semaphore
slice runner; the generic generator's declaration check alone is not claimed
as an executed canary.

## Failure paths observed before the final green run

- `gate-red.txt`: with the canary gate initially a no-op, three assertions fail
  across four selftests. The runner continues past an unobservable canary.
  `gate-green.txt`: the same four tests pass after enforcing the gate.
- `initial-blocked.txt`: the first real F-09 run finds the target-cell failure,
  but a later synchronous Acquire in P-06b hangs behind the leaked entry. The
  incomplete run is BLOCKED, not counted as a kill. P-06b now additionally checks
  the already-contracted spare capacity before its blocking call. All existing
  assertions remain, and the full mutant run now reaches completion.
- `weak-discovery-blocked.txt`: the first weak Go overlay used a noncanonical
  macOS temporary path and discovered zero tests despite exit 0. Exact discovery
  rejected it. Canonicalizing the overlay path produced ten verified executions.

The mutant is generated through `mutant-generation.json` and included in
`fault-mutants.json`. CI runs both the generic mutation suite and this weak/full
comparison plus its four gate selftests. Source mutation now has five named
semaphore mutants; matrix coverage remains 41 mutants across 32 cells. Four
contract limits and two queued cells lacking matrix operators remain excluded.
This is one real-component F-09 slice; a second component and general class-wide
completion are still pending.

## Full acceptance

```sh
bash docs/evidence/semaphore-f09/scripts/full_gates.sh
```

This includes the new executed comparison; all 13 accepted decision contracts,
ordinary/scheduled Go race tests and upstream regressions; full cells/pairs;
generated-mutant drift checks; matrix and source mutation; sidecar, guards and
reachability; mypy; registry, deterministic-layer, tool, local-model, pilot,
finding-preservation and accounting selftests; and `git diff --check`.
No model API calls are needed. These are deterministic test results, not a new
model-quality or cost comparison.

`implementation-gates.txt` records the complete successful pre-commit command
above (exit 0). Expected red probes are checked as such; they are not ignored
failures. Source/test anchoring is refreshed in a subsequent artifact-only
reconciliation commit, with a final full acceptance run retained separately.
