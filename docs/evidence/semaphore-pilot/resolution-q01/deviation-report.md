# DR-001 deviation and implementation evidence

The owner accepted Q-01 on 2026-11-14. This implements only that decision in
`examples/weighted-semaphore`, not in upstream golang.org/x/sync.

## Observed deviation before the fix

The five new decision scenarios ran against pinned upstream source. Four
full-capacity scenarios failed with `eligible zero waiter did not complete
without another input`; the spare-capacity control passed. See [red.txt](red.txt).
The guard proof also failed with a concrete counterexample: size=1, cur=1,
head=0, front=true. See [guard-red.txt](guard-red.txt).

The first setup attempt lacked the upstream test-only errgroup dependency and
did not compile. [setup-failure.txt](setup-failure.txt) preserves it; it is not
counted as a behavior red. Copying that unchanged dependency enabled the real
red run. No original upstream tests were modified.

## Applied change and acceptance

[implementation.patch](implementation.patch) changes only the head-cancellation
condition and its comment. Removing the `size > cur` restriction allows the
existing notifier to grant eligible zero requests. It still stops at a blocked
positive head. [before-hashes.json](before-hashes.json) records the exact
pre-fix tests and evaluation source files; every file except `semaphore.go`
remained byte-identical through the green run.

- Five scenarios, 50 repetitions each: **250/250 passed with the race detector**
  ([green.txt](green.txt)).
- Upstream and decision regression suite passed with the race detector
  ([upstream-and-decision-tests.txt](upstream-and-decision-tests.txt)).
- Source-bound guard partition, boundary probes and progress condition passed
  under the stated NAT assumptions ([guard-green.txt](guard-green.txt)).
- Empty test discovery fails, rather than producing vacuous green
  ([discovery-red.txt](discovery-red.txt)). The combined CI command passed
  ([acceptance.txt](acceptance.txt)).

No remaining deviation from the five DR-001 expectations was observed. This is
not proof of every possible scheduling interleaving. Twelve questions remain
OPEN; other branches of the partially decided cancellation cell remain open.
The original 57-cell as-is analysis is unchanged. No full Step-04 cell suite,
whole-component reconciliation or broader F-20 mutation-registry support is
claimed. `matrix-coverage.json` enumerates all 57 original cells, with one
partially decided cell and 56 outside this resolution, plus the limited zero
TryAcquire FIFO control. Non-target cells are not labelled untestable.
