# Scoped backoff cleanup matrix

<!-- terminal: ShutdownStopped -->

Abstraction: the controlled scheduler exposes three worker/resource projections.
TearDown captures the immediate pending state, then its mandatory follow-up
trace checks worker and timer release before any parent cancellation. ObserveWorker
is a test-seam observation/resume action, not a new upstream API. See scope.md.

| State | TearDown | ObserveWorker |
|---|---|---|
| BackoffWaiting | transition → ShutdownPending (DR-011) | handle |
| ShutdownPending | handle (idempotent local teardown) | transition → ShutdownStopped (DR-011) |
| ShutdownStopped | handle | handle |

All six cells have named executions in `TestRadarCells/<state>/<event>`.
Full-slice resource invariants accompany the cell disposition assertions.
The weak control tests only `BackoffWaiting x TearDown` and its Shutdown state.
It deliberately omits resource release and never substitutes for the full suite.

The broad Q-01..Q-16 decisions are ANSWERED, not RESOLVED implementations.
The 182-cell historical matrix is preserved separately and is not declared
covered by this six-cell regression projection.
