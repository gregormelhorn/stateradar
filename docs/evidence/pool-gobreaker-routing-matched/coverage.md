# Behavior comparison

The controls passed on the same source commits. The P-04a negative control failed at the intended assertion when the test-only overlay rechecked idle readiness. The four gobreaker controls passed three repetitions with the race detector. [Control output](control-results.txt).

## Pool

| Behavior | Routed | Hybrid |
| --- | --- | --- |
| Historical P-04a at capacity | `P-01a`, `T-02`, `Q-04`; `TestProbeMissPutAtCapacity` passed (062) | `P-01a`, `Q-01`; `TestPilotIdleMiss/at-capacity` passed (059) |
| Idle miss below capacity opens a new connection | `T-01`, `Q-04`; `TestProbeMissPutBelowCapacity` passed (062) | `T-04`, `Q-01`; `TestPilotIdleMiss/below-capacity` passed (059) |
| Release strands queued or about-to-queue Get calls and late Put bypasses them | `P-02a/b`, `T-03`, `T-04`, `Q-02`; two focused probes passed (062) | `P-03a/b`, `Q-03`; `TestPilotDetachAfterMiss` passed in both branches (059) |
| Close frees capacity without waking the older waiter | `P-03a`, `T-05`, `Q-03`; probe passed (062) | `T-05`, `Q-02`; `TestPilotCloseFreesSlot` passed (059) |
| Callback lifecycle and Ping/Release | `T-10`–`T-12`, `Q-09`; focused callback-outcome probe passed (062) and the detector reported the read in direct `Ping` racing with the write in `Release` (074) | `T-07`, `Q-10`; instrumented callback outcomes and skipped validation tested (059). The detector reported the read in `Get` racing with the same write in `Release` (134) |
| Second Get from the same caller | `T-13`, `Q-15`; two queued acquisitions tested (062), held-lease case traced | `T-01`, `T-02`, `Q-16`; two queued acquisitions tested (059), held-lease case traced |
| Caller abandonment | `T-15`, `Q-14`; cited trace | `T-03`, `Q-05`; `TestPilotAbandonedWait` passed (059) |
| Backing storage retains a removed queue entry | `T-19`, `Q-16`; cited trace | `T-13`, `Q-17`; cited trace |
| Lazy expiry and delayed handoff | `T-16`, `Q-13`; cited trace | `T-06`, `Q-14`; cited trace |

All three steps of the at-capacity result are asserted in both tests. The first acquisition stays pending while an idle connection is present, the later acquisition takes that connection, and a subsequent Put completes the first. Flash W-02 supplied the buffered/queued intermediate state. Its source review and the executed test establish the missed observation, bypass and subsequent wake-up.

Hybrid added focused passing checks (133) for a factory error returned despite a newly idle connection, skipped overflow cleanup when Release detaches before the callback, and return of Release while its already detached counterpart drains. Routed traced the callback overlap and reported the same open questions. Neither pilot estimated retained memory or multi-pool traffic. The Pool upstream `TestPool_Get` timed out separately from both pilots' focused assertions.

## Gobreaker

| Independent control | Routed | Hybrid |
| --- | --- | --- |
| Old generation completion leaves current accounting unchanged | `Q-05`; `TestProbeStaleReturnClassifiesAfterStateChange` passed (061) | `Q-03`, `Q-16`, `P-05/P-06/P-17`; stale report can also advance lazy expiry, tested (145) |
| Repeated current-generation completion counts again | `Q-04`; `TestProbeDuplicateReportClosesWithOneAdmission` passed (061) | `Q-01`, `Q-16`, `T-03`; repeated success closes and makes a distinct pending report stale, tested (145) |
| Abandoned HalfOpen permit keeps capacity occupied | `Q-03`; `TestProbeOmittedReportRetainsHalfOpenQuota` passed (061) | `Q-02`, `T-04`; tested with shared cap and abnormal work exit (145) |
| Same-instance callback reentry waits on the held mutex | `Q-08`, `Q-09`; `TestProbeTransitionCallbackReentryBlocks` passed (061) | `Q-08`, `T-08`, `T-14`; `TestPilotReentrantCallbackWaits` passed (145) |

Both cited lazy expiry before stale-report accounting, panic and callback effects, second admission, and Goexit retaining an admission charge. Hybrid directly tested stale-report notification before an explicit observer and a listener panic preventing admission after the state commit. Routed separately documented the existing assertion using the wrong breaker instance. Both regular upstream suites passed and both full upstream race runs reported the fixture race in `TestCustomCircuitBreaker`. The focused pilot suites passed under the race detector.
