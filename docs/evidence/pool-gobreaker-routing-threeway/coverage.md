# Finding coverage and evidence depth

Control tests stayed outside the pilots. The Pool probe passed 25 race-detector repetitions. Its negative control rechecked idle readiness and failed at the intended assertion. Four gobreaker controls passed three race-detector repetitions. [Control output](control-results.txt). Pilot test results below are [retained verbatim](behavior-results.txt); [probe sources](probes/) are stored as `.go.txt` so recursive Go test discovery cannot compile them as extra packages. Overlay maps in the raw runs use absolute paths and need regeneration after relocation. Pool hooks pause existing paths without deciding the oracle. Test-only setup manipulates clocks or scheduling; behavioral outcomes are checked separately.

IDs belong to individual runs. In particular, the historical P-04a is matched by its sequence, not by a local P-04a label. The cutoff of Pool routed occurred after its probes but before a sidecar and final report existed. Its entries below establish saved findings, not a complete accepted pilot.

## Pool

| Behavior | Routed, incomplete | Matrix | Hybrid |
| --- | --- | --- | --- |
| Historical P-04a at capacity | Q-04 / P-06a; TestPilotPutInMissWindow, log 069 | Q-12 / P-05a; TestPilotPutAfterEmptyObservation/AtCapacity, logs 046/156 | Q-02 / P-01b; TestPilotObservationGap/AtCapacity, logs 040/148 |
| Below-capacity redundant Factory beside idle | Same probe tests max=2 | BelowCapacity subtest | BelowCapacity subtest |
| Release strands queued or stale-observation Get | Q-02; TestPilotReleaseWindows, at and below capacity | Q-02; TestPilotReleaseAfterEmptyObservation, both capacity branches; repeated-acquisition probe covers queued wait | Q-03; TestPilotReleaseBeforeGetCommit tests at capacity; below-capacity refusal is cited in traces |
| Close frees accounting capacity without waking old waiter | Q-05; TestPilotCloseFreesSlotWithoutWake | Q-06; TestPilotCloseDoesNotWake | Q-04/Q-11; TestPilotCloseFailureAndRelease |
| Same caller's second Get, pending and holding | Q-06 / T-01/T-02; repeated-acquisition probe and cited held case | Q-05; TestPilotRepeatedGetAndLatePut and TestPilotHeldSecondAcquisition | Q-05; TestPilotSameCaller asserts distinct held resources and two pending requests |
| Caller abandonment with and without later input | Q-06 / T-03; TestPilotRepeatedAndAbandonedAcquisition | Q-05; TestPilotAbandonedCaller | Q-05; TestPilotCallerDeparture |
| Queue backing storage after logical removal | Q-13, cited mutation | Q-13 / T-12, cited mutation | Q-07 / T-04, cited mutation |
| Expiry and private handoff health behavior | Q-12 / T-07; source trace, callback probes | Q-04/Q-14/Q-18; TestPilotHandoffSkipsPingAndRetainsSlot plus cited expiry traces | Q-06; TestPilotHandoffSkipsPing plus cited expiry traces |
| Ping/Release callback effects | Q-07/Q-18; check/call gap and entered callback tests; race detector log 068 | Q-04; forced check/call nil panic and entered callback outcomes tested; no race-detector run | Q-09; entered callback success/error tested; race detector logs 109/163 |
| Factory/Close reentry and drain | Locked reentry, failed cleanup and duplicate Release probes | Reentry, both success/error serialization, duplicate Release and drain-panic interruption probes | Reentry, locked Factory success/error and duplicate drain probes; drain panic cited |

Every at-capacity P-04a probe asserts all three material outcomes: idle inventory coexists with a pending first Get, a later Get takes idle inventory, and another Put completes the first. All three also distinguish the below-capacity allocation branch. The Pool hybrid probe's final Put uses another held value; this still establishes wake-up of the older waiter after the bypass.

The extra matrix cases are deeper behavioral checks in some branches, not a new defect family. Matrix directly tests a drain stopped by panic and the check-to-call nil-Ping panic. Hybrid adds race-detector observation, while describing the panic path in source traces. No variant measures actual retained heap size, production load or distributed recovery. All three retain those evidence limits. Pool matrix models construction explicitly, while hybrid begins at successful construction; this explains part of the 182-versus-72 cell difference and prevents treating raw hole/cell totals as quality scores.

## Gobreaker

| Independent control | Routed | Matrix | Hybrid |
| --- | --- | --- | --- |
| Old generation completion does not alter current accounting | Q-02; TestPilotStaleReportRefreshesOpen; final tests log 111 | Q-08; TestPilotCountsAndCompletionClock and TestPilotLateClassificationAfterTrip; log 131 | Q-05; TestPilotLateCompletionRefresh; log 118 |
| Repeated current-generation completion counts again | Q-03; TestPilotDuplicateHalfOpen | Q-01; TestPilotRepeatedDone | Q-02; TestPilotHalfOpenAdmissionAndReports and TestPilotMissingReportAndRepeatedFailure |
| Abandoned HalfOpen admission keeps capacity occupied | Q-04; TestPilotAbandonedTrialAndCap | Q-02; TestPilotAbandonedAndDuplicateAdmission | Q-03; TestPilotMissingReportAndRepeatedFailure |
| Same-instance callback reentry blocks on held mutex | Q-05/Q-06; TestPilotSameMutexReentry checks notification and trip hooks | Q-03; TestPilotStateCallbackReentry | Q-01; TestPilotReentrantStateChangeWaits |

All three also cover lazy expiry before stale accounting, exact expiry equality, later requests completing first, Goexit retaining admission, policy panic causing repeated accounting and state commit before notification panic. Their final focused suites passed with race instrumentation. Routed has 13 top-level probes, matrix 11, hybrid 9 plus nested cases; grouped tests assert several outcomes, so these counts are not interchangeable finding counts.

Routed and hybrid both reproduce the existing upstream TestCustomCircuitBreaker race. Matrix's full upstream suite was run without the race detector; its focused suite used the detector. The fixture race is therefore an additional measured finding in routed/hybrid, not a new component-state race. All three identify the separate wrong-receiver expiry assertion. Unsigned counter/epoch wrap and callback retention are cited in all three, with runtime costs unmeasured. Hybrid executes a small synthetic synchronized-recovery probe; the other reports keep aggregate recovery effects analytical. None measures a real shared backend.

## Quality limits and corrections

No core external control is uniquely found by hybrid. Its Flash schedule review keeps 2/15 proposals unchanged, corrects 12/15 and rejects 1/15. Shared mutexes invalidate several proposed interleavings. The reviewed final traces explicitly respect those locks. The additional sweep therefore creates real source-review work but does not establish a unique core finding in this sample.

Blind row-presence checks passed for outputs with duplicate or multiple situation rows. Pool matrix and hybrid commissioned replacements; gobreaker hybrid retained and classified multiple situation rows per ID. Both preserve the original answers, but they incur different review workloads. Inline as-is qualifiers and code-derived remembrance/lock descriptions also limit independence even when the mechanical as-is marker count is zero. The pilots document those limits rather than claiming every convergent row is an independent confirmation.

A stage checker in gobreaker routed briefly printed a zero-row matrix success when state rows lacked the expected bold syntax (log 039). The pilot noticed it and corrected the syntax before the final nonempty sidecar gates. This is an intermediate-check weakness, not a valid zero-work completion. Matrix workflows avoid that particular Markdown-authoring problem, but still required catalogue annotation and citation repairs. No conclusion here relies on an intermediate green check alone.

One report calls the Part-A scope judgment a human judgment. It was generated by the pilot agent; no human domain decision was supplied or adopted in this comparison. Findings and proposals remain open questions. More repetitions and unseen components are needed to estimate reliability; the one service cutoff cannot be attributed causally to routing technique.
