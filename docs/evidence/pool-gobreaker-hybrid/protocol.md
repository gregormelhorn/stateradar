# Hybrid pilot protocol

Run pinned silenceper/pool 6084537 followed by sony/gobreaker 27b8e2c.
Use the same pack SHA, selective tool output, GPT-6.1 Sol medium through
ChatGPT login, Jev 1.14.0 and fresh Flash Part B. The pilot receives source
and normal docs, not reference artifacts. Flash drafts schedules and Codex
reviews them, sweeps for missed schedules, writes matrix fields and tests.
The renderer validates source fragments and round trips each cell.
Postflight requires matrix render identity, strict sidecar regeneration,
matrix/guards/sidecar/reachability/blind coverage.

Pool acceptance separately checks the whole historical P-04a schedule
(Get misses at capacity, Put buffers before the lock, first Get waits
while a newer Get takes the idle value, another Put wakes the waiter).
Also compare the Release/waiter defect, both repeat Gets, caller
abandonment, queue backing retention, idle expiry, the Ping/Release
race, and callback effects with the existing Codex reference. Distinguish
a proposal from a final cited analysis and from an executed test.

Gobreaker is held out from the hybrid prompt tuning. Check stale completion,
duplicate current completion, abandoned HalfOpen completion and callback
reentry against four independently executed controls. The old compact
and standard runs used a different prompt/routing and serve as context.

Record Codex token usage, inclusive of cache, wall time, retained-log
reads, Flash and Jev ledger totals and reservations. No invoice is
assumed for ChatGPT-plan usage. Keep upstream suite failures separate.
