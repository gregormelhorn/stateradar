# Q-02/Q-03/Q-04: accepted numeric contracts and observed deviations

The owner accepted the revised numeric-contract recommendations, explicitly
selected panic for negative inputs in all four methods, and then selected an
immediate explanatory error for oversized Acquire. These decisions apply only
to the evaluation copy. They do not authorize an upstream release.

| Question | Record | Implemented behavior |
| --- | --- | --- |
| Q-03 | DR-002 | Negative NewWeighted, Acquire, TryAcquire and Release arguments panic before mutation, including when the Context is already canceled. Zero remains valid. |
| Q-04 | DR-003 | An over-release panics before subtraction or notification. Recovery retains the previous counter and queue. |
| Q-02 | DR-004 | A live oversized Acquire returns an error containing requested weight and capacity without waiting for cancellation. Existing pre-canceled Context priority remains unchanged; other races are still Q-10. |

Model and DRs were recorded before tests and implementation. The focused model
refines numeric branches of 13 historical cells; 44 are outside this slice.
No original cell is claimed fully resolved. Previous DR-001 coverage remains
separate. Nine questions (Q-05 through Q-13) remain OPEN.

## Red before implementation

The completed behavior run in [red.txt](red.txt) reports eight failing test
groups and two passing control groups. Failures cover absent negative-input
rejection, corrupted post-panic capacity, and oversized requests waiting for
cancellation. Zero/MaxInt64 boundaries and pre-canceled oversized handling pass.

An earlier run aborted on the *second*, otherwise valid Release after a
recovered over-release. [red-initial-aborted.txt](red-initial-aborted.txt) retains
that evidence. Before changing runtime code, the test was amended to report
this unexpected panic as a failing test, allowing the remaining groups to run.
It was not changed to permit that behavior. Both decision test files stayed
byte-identical from the completed red run through green; see before-hashes.json.

The source guard audit also failed before the fix ([guard-red.txt](guard-red.txt)).
Its initial setup mistakenly imported unavailable PyYAML; the dependency-free
check reads the exact DR header fields instead. That setup error is retained
separately and is not counted as a behavioral red.

## Fix and green

[implementation.patch](implementation.patch) is the exact change from the Q-01
baseline. Validation precedes mutation; valid additions and subtractions stay
within [0,size] for every representable nonnegative int64 capacity. Oversized
Acquire returns a size error rather than waiting on Done. Original upstream
sources other than semaphore.go, upstream tests and DR-001 tests are unchanged.

- Ten new test groups x 50 repetitions: **500/500 passed with race detector**
  ([green.txt](green.txt)).
- Combined acceptance checks all **15 groups x 50 = 750 group passes**, including
  Q-01, and all **49 actual test/subtest names**, then runs upstream and decision
  tests with the race detector ([acceptance.txt](acceptance.txt)).
- Three guard partitions and four bounded-arithmetic obligations pass under
  the stated assumptions ([guard-green.txt](guard-green.txt)). These are not
  proofs of every scheduler interleaving; behavior tests exercise the code.
- Empty discovery and missing test mapping are rejected
  ([discovery-red.txt](discovery-red.txt), [coverage-red.txt](coverage-red.txt)).
- Full pack gates and accounting selftests pass
  ([pack-gates.txt](pack-gates.txt), [accounting-tests.txt](accounting-tests.txt)).

The first combined acceptance rejected a mistaken expectation of 55 names:
Go emits 49 test/subtest results here, because slash-separated names do not
create six extra intermediate tests. The observed output is retained in
[acceptance-discovery-mismatch.txt](acceptance-discovery-mismatch.txt). The
checker expectation was corrected to the 49 actually declared test/subtest
names; no behavior test or result was changed. Exact discovery and repetition
counts remain required.

No remaining deviation from these targeted decisions was observed. The original
as-is analysis remains immutable and source-pinned to upstream; it is not a
reconciled model of this evaluation copy. Full Step-04/06 completion, generic
mutation coverage and resolution of Q-05..Q-13 are not claimed.
