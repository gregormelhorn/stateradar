# Observation and scheduling seam

The evaluation uses upstream NewWeighted, Acquire, TryAcquire, Release and
standard contexts. Assertions concern error/nil results, pending completions
and positive capacity available through TryAcquire. No assertions compare
implementation fields to the expected model result.

A test-only scheduler waits for each requested queue admission under the
instance mutex, using the existing private queue as a readiness barrier.
It never changes that queue, counter, branch or notification. This establishes
the exact enqueue order; results and accounting are then checked at the public
API. Failure to reach a setup barrier fails the test rather than becoming a
false liveness success. Timed result waits bound failed test execution, not
production scheduling latency. Contexts are canceled during cleanup.

Known positive weight is acquired first; no state is fabricated by writing
fields. Tests keep a live zero request and deliberately issue no Release until
its required completion has been observed. Separate controls preserve FIFO
behind a still-blocking head and positive accounting after zero completion.
