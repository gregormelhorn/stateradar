# Behavior coverage review

Control programs stayed outside the pilot inputs. The original Pool P-04a
probe passed 25 race-detector repetitions; rechecking readiness in its
negative-control overlay made the expected assertion fail. Four gobreaker
controls passed three race-detector repetitions. See [control results](control-results.txt).

IDs are local to each analysis. The historical P-04a is matched by its
ordering and observable outcomes, not by a local pair label. Ordinary
component failures are retained separately from failed artifact gates.

## Gobreaker, matched pack 394ff35

| Control | Sol final evidence | Terra preliminary evidence |
| --- | --- | --- |
| Stale completion skips current accounting after lazy refresh | Q-04; TestPilotStaleCompletionAdvancesOpen checks notification and cleared Counts; TestPilotIsSuccessfulAfterExpiry covers classification | Extraction notes generation behavior; no corresponding executed behavior probe or verified final trace |
| Duplicate done can count again and close HalfOpen | Q-03; TestPilotDuplicateCompletion | Q-02 cites repeated same-generation completion; no behavior probe |
| Abandoned HalfOpen admission retains allowance | Q-02; TestPilotOmittedCompletionAndSecondAllow checks repeated refusal and later matching success | Q-02 describes the retained admission; no behavior probe |
| Same-instance callback reentry blocks on held mutex | Q-05; TestPilotNotificationReentry, bounded wait plus mutex evidence | Q-01 describes lock-held reentry; no behavior probe |

Sol's ten focused probes passed, also under the race detector. Its upstream
suite passed without race instrumentation. That does not claim the known
upstream fixture race disappeared: the earlier diagnostic Sol run reproduced
it under `-race`. Runtime/heap and aggregate-backend effects remain analytical.

An additional Sol probe, TestPilotWrapperReassignmentRedirectsReport,
performs serialized `*a = *b` through the exported wrapper type and then
calls a previously acquired completion. Public Counts on b reports one
success without an admission. Q-13 distinguishes this from rebinding a
variable to a new pointer. It is an open contract question, not a decided
implementation change or a demonstrated gain caused by the new prompt.

Sol's final blind answer contains 115 situations; the independent row audit
matches every one to exactly one classification. A dropped classification
fails the audit. Several rows depend on code-derived catalogue annotations;
Part B is not independent evidence for those claims. The report explicitly
records this limitation. Fresh strict sidecar generation is byte-identical,
and the six postflight gates still pass.

Terra's entire run is explicitly preliminary: no final catalogue/matrix,
guard proofs, sidecar, blind pass or complete question inventory. Identifying
some of the same problems does not establish equivalent finding coverage.
Its early stop occurred before the time or provider-budget limits and without
a provider authentication/HTTP failure.

## Pool, matched pack 394ff35

| Control or distinct consequence | Sol retained final evidence | Terra preliminary coverage |
| --- | --- | --- |
| Historical P-04a at capacity | Q-04 / P-01a; TestProbeMissThenPut checks idle stock beside the pending first Get, later Get overtaking, then later Put completing the first | No concrete miss-to-lock ordering, overtaking trace or probe |
| Below-capacity redundant Factory beside idle stock | Same probe, capacity 2 subtest | No corresponding ordering or probe |
| Release strands existing and late-enqueued waiters | Q-02; TestProbeWaitersAfterCloseAndRelease and TestProbeMissThenRelease, both capacity branches | Q-01 mentions unnotified waiters; late-enqueue ordering not developed |
| Close frees accounting without waking old waiter | Q-03/Q-10; later fresh Get creates first, failed Close separately observed | Q-01/Q-02 discuss waiter lifecycle and counter decrement; distinct bypass sequence untested |
| Same caller second Get, pending and holding | Q-06; TestProbeAcquisitionOrders checks independent pending waits and two held resources | No explicit two-call treatment for both cases |
| Abandonment with and without later Put | Q-05; T-03 source-backed trace, plus separately tested acquisition/handoff behavior | General cancellation question in Q-01; no complete late-handoff trace |
| Queue backing storage | Q-16 / T-12, cited reslice/copy behavior; heap cost unmeasured | Mentioned in extraction, not consolidated as its own reviewed question |
| Handoff health check | Q-09; direct-delivery probe and source citation | Q-04 identifies the bypass, without a probe |
| Ping/Release boundaries | Q-08/Q-22; success/error and dispatch-gap probes; original-source race detector evidence | Q-07 identifies unsynchronized reference access; outcomes not traced or tested |

Sol's first eight scheduling probes passed also with race instrumentation;
the expanded twelve-probe suite passed without race instrumentation. Its
original-source Ping/Release race probe remained red, and the upstream full
suite retained the TestPool_Get timeout. Those are component findings, not
failed artifact acceptance. Other eight upstream tests passed separately.

The service ended the Sol session with a cybersecurity-risk flag after the
summary was written. This is a failed controller run, despite the retained
artifact completeness. No retry was made. The independent local audit then
found all six gates green, a byte-identical strict sidecar regeneration,
and exactly 101 classifications for 101 blind situations. Preserve both
facts: usable checked artifacts, unsuccessful service completion. No final
Codex usage event exists, so full Pool/Sol cost is unknown.

Terra wrote seven preliminary questions and basic extraction, but no
statechart, catalogue, matrix, guard proof, probes, final verification or
blind pass. Its selected upstream tests do not substitute for these
behavior controls. It stopped after 161.758 seconds, without exhausting the
2700-second limit or $2 provider budget. The partial findings are useful
seeds but do not meet the same completion/coverage bar.
