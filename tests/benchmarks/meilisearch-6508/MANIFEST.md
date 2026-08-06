# meilisearch — SearchQueue Admission Lifecycle

**Issue:** [#6508](https://github.com/meilisearch/meilisearch/issues/6508)
**Commit:** `fff2ef5a42658b16a937d922aabc3fb7f89f2018`
**Date:** 2026-08-06
**Oracle:** Confirmed — primary finding matched exactly. Two additional findings
confirmed as novel (D1 #6578, D4 #6577).
**Defect class:** Caller terminal, scheduler admission claim remains eligible (PA-21) — F-09 cancellation leak

## Primary finding

**Missing transition:** `WaitingCallerCancelled → QueueEntryCeasesToBeEligible`

The scheduler's queue stored `oneshot::Sender<Permit>` entries. Cancelled
callers dropped their receivers, but the senders persisted in the queue.
Dead entries polluted capacity enforcement, random eviction, permit selection,
and the `searches_waiting` metric. A live request could be evicted while a
cancelled waiter remained admitted.

**Oracle match:** The issue describes "Cancelled search requests remain in
SearchQueue and can cause spurious TooManySearchRequests." StateRadar
independently derived the identical invariant: "queue capacity, eviction,
metrics, and permit selection operate only on live waiters."

## Additional findings (confirmed by separate issues)

- **D1 (#6578):** `Permit::drop(self)` + `Drop for Permit` sends two release
  signals, causing double capacity return and parallelism violation. (PA-23)
- **D4 (#6577):** `searches_running` not re-incremented on refill grants,
  causing metric undercount and gate over-admission.

## Requirements (Part B input)

R-01 through R-17, including:
- R-08: Cancelled caller must reach terminal state and not later begin execution.
- R-09: Admission decisions must operate on requests that remain eligible.
- R-14: Metrics must not indefinitely count terminal requests as live work.

## StateRadar output

- **Matrix cell:** `(Waiting, WaitingCallerCancelled) = UNSPECIFIED`
- **Oracle mechanisms identified:** 4/4 (capacity, eviction, selection, metrics)
- **Blind diff:** Part B derived the same live-waiter invariant as the issue author.
- **Proposed test:** Independently converged on the oracle's deterministic reproduction
  (metric-based sync, task.abort(), yield_now loop).
- **Blind run confirmed:** The missing transition was required by Part B's
  requirements analysis before any code or issue was seen.
