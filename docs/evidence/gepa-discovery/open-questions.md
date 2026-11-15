# Open question from supervised discovery evaluation

## Q-GEPA-D01 — OPEN: WaitGroup use after synctest bubble completion

**Observed in tests:** `reference/reference_test.go:65` ("func TestWaitGroupSynctestOutsideWait") creates a `sync.WaitGroup`,
calls Add(1) and Done inside `testing/synctest.Test` with no waiter, then invokes
`wg.Wait()` outside the completed bubble. Go 1.27.3 produces a recoverable
nil-pointer runtime panic in 3/3 race-detector runs; see
`synctest-acceptance.jsonl`. This test was created after the final model
output as a counterexample, not used as search or selection feedback.

**Observed in code:** `upstream/waitgroup.go:124` ("return") returns with the bubble flag
set when no waiter exists. `upstream/waitgroup.go:174` ("synctest.IsAssociated(wg)") may call
`IsAssociated` from a zero-counter Wait. The callee
`runtime-reference/synctest-runtime.go:451` ("getg().bubble.id") reads the current goroutine's
bubble id. `runtime-reference/testing-synctest.go:103` ("calling Add or Go from outside that bubble is a fatal error") describes restrictions
on outside Add or Go; it does not explicitly settle this outside Wait ordering.
The general guidance in that source asks for self-contained tests.

**Question:** Is outside Wait after a completed bubble in this exact state
supported, or is the observed panic within an intended isolation restriction?
Only the Go contract owner can decide normative behavior or wording. A possible
interpretation is to document the boundary or make the callee tolerate a
missing bubble; these are **proposals**, not decisions. No upstream issue or
message was sent.
