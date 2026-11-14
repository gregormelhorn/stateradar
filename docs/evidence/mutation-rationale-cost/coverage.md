# Finding-by-finding review

This review compares final artifacts without changing them or answering their
open domain questions. Q identifiers below are local to each run. A finding
can be retained while its experimental validation differs.

| Behavior | Routed evidence | Matrix evidence | Assessment |
|---|---|---|---|
| Stale completion accounting and expiry effects | Q-09/Q-22; ExpiryAndStaleReport, StaleClassifierAndReturn | Q-05/Q-19; StaleReportReconcilesOpen | Both cover the primary control. Both final tests kill a disabled generation guard in 5/5 repetitions. |
| Duplicate completion | Q-03; DuplicateDone | Q-03; DuplicateAndAbandoned | Both reproduce premature HalfOpen closure. |
| Missing HalfOpen completion | Q-04; AbandonAndLateReport | Q-06; DuplicateAndAbandoned | Both preserve the indefinite-slot question; routed additionally executes separate late true/false branches. |
| Notification and policy reentry | Separate Q-01/Q-02; CallbackReentry | Grouped Q-09; ReentryBounded | Same two callback findings, grouped differently. Bounded nonreturn alone is not a general latency proof; the mutex contract supplies the mechanism. |
| Policy panic, repeated accounting and panic replacement | Q-07; CallbackPanics | Q-10; TripPanicDoubleAccounting, NotificationPanicReplacesRequestPanic | Both execute the critical effects. |
| Classifier panic | Q-07; CallbackPanics | Q-10 and source citations | Present in both; only routed executes this specific branch. |
| Stale classification and original error return | Q-09; StaleClassifierAndReturn | Q-05, source/trace analysis | Present in both; routed has the explicit staged behavior test. |
| Second Execute while first is pending | Q-15; ExecuteOvertakes | Q-07; SameCallerWhilePending | Both demonstrate that the second can finish first. |
| Two outstanding Allow callbacks below the limit, no refund after first report | Q-15 and traces | Q-07; SameOwnerOutstandingBelowBudget | Both describe independence; matrix adds a direct final probe of both callbacks and refusal of a third. |
| First post-expiry Allow reaches saturation | Guarded notes, AdmissionOrdering covers related before/after completion | Explicit StateHalfOpenSaturated; AllowThenStateAtOpenExpiry and pair reachability | Matrix supplies an additional scheduled-expiry/public-observation probe. The private expiry write schedules time only; assertions use the public seam. |
| Lazy deadlines, count snapshots, equality and rejection latency | Q-05/Q-06/Q-19 | Q-01/Q-02/Q-15 | Primarily regrouping, not lost findings. |
| Same downstream across multiple instances | Q-11; SharedRecoveryWaves, 3 cycles x 4 instances | Q-14 and multi-instance traces | Both identify aggregate risk; routed executes a synthetic wave probe, matrix stays source-derived. Neither measures production load. |
| Numeric wrap and capability misuse | Q-12/Q-18 | Q-11/Q-13 | Both retain the questions; no production wrap proof. |
| Nil/zero/wrong receivers and nonpositive settings | Q-08/Q-17 | Q-08 | Regrouped. These are separate from wrapper reassignment. |
| Classifier policy authority and concurrency | Q-13 explicitly asks both | Q-16 asks classification authority; catalogue records calls between locked sections | Authority is preserved. Matrix does not state the classifier concurrency contract question as explicitly. |
| Goexit | Q-04/Q-20; Goexit | Q-06; GoexitAbandonsAdmission | Both reproduce admission without an outcome. |
| Compatibility-mode panic(nil) | Explicit runtime-scope Q-20, untested | Not explicitly developed | Additional routed question, not an executed control or established defect. |
| Test quality | Q-14 plus validation notes | Validation notes | Both retain the wrong expiry assertion target and observed upstream race; matrix does not create a separate owner Q for the test note. |
| Retention and replacement | Q-16 | Q-17/Q-06 | General lifecycle issue present in both; see concrete missing case below. |

## Concrete gap shared by both

The independently retained `wrapper-control.go.txt` reproduces serialized
reassignment through exported Go values: obtain `done` from `a`, assign `*a = *b`,
then invoke `done(true)`. The new breaker has zero requests and one success.
Five race-detector repetitions pass. This is the same additional case found in
the older reference, not a novel held-out discovery or a decision that copying
must be supported.

Routed Q-08's unconditional statement that the callback remains bound to the
original breaker needs a scope restriction or a reassignment trace and question.
Matrix Q-17 identifies the wrapper capture and ordinary copying but omits the
reassignment sequence and resulting accounting. Mentioning replacement or
copying broadly does not cover this concrete outcome. Neither raw analysis was
silently repaired after its metered session ended.

## Question count and routing noise

The 22 routed questions and 19 matrix questions are not counts of distinct bugs.
Most differences come from grouping: two reentry questions become one, settings
join receiver validation, and snapshots join expiry. Each run adds two Jev-scope
questions. The stale-result scope question is shared (routed Q-22, matrix Q-19).
The other differs: routed Q-21 preserves an incorrectly ordered acceptance
assertion; matrix Q-18 asks about the default six-failure predicate despite a
supported Choice and low scope probability. These retained questions show
review work created by formulation/scope disagreement. They do not establish
additional runtime bugs, and do not justify changing the provisional threshold
or automatically resolving any question.

The supplemental generation-guard experiment was triggered by an intermediate
matrix probe that checked effects only after a later Allow. Final log 113 shows
the controller adding notification assertions before that Allow. The final
matrix suite then detects the mutant. The earlier concern is resolved for the
final output; it is not reported as a surviving final defect.
