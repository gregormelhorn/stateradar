# Finding verification

The source and README were read through their final lines. Draft output is retained in `draft-verify.json`. Every draft item below was checked against the source, including the two unclear verdicts. Initial findings were saved before the probe ran.

## Draft claims

- **C1** (supported). observed-in-code gobreaker.go:126 ("mutex      sync.Mutex"). Retained for breaker state and counters. F22 cites operation lock sites. Wrapper assignment and classifier evaluation are outside this protection.
- **C2** (supported). observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"). Retained as admission ordering for F08, F14 and F20.
- **C3** (supported). observed-in-code gobreaker.go:230 ("if err != nil {"). Retained as rejection limit. The private generation value is discarded publicly. The word ‘immediately’ describes rejection without executing the request. Mutex acquisition and expiry notifications can take time.
- **C4** (supported). observed-in-code gobreaker.go:234 ("defer func() {"). Retained with the installation boundary after successful admission and the coverage of later classification and accounting.
- **C5** (supported). observed-in-code gobreaker.go:237 ("cb.afterRequest(generation, false)"). Qualified to a non-nil recovered value and a returning failure report. F16–F19 separate panic origins and the second-panic case.
- **C6** (supported). observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). Retained with the order classifier, lock, generation check. Stale normal results can still run the classifier and return.
- **C7** (supported). observed-in-code gobreaker.go:284 ("return generation, ErrOpenState"). Retained for a state-aware check that still sees Open. Expired Open may already have become HalfOpen.
- **C8** (supported). observed-in-code gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). Retained. Admission uses cumulative Requests for the half-open generation. F11 traces abandoned and late-report schedules.
- **C9** (supported). observed-in-code gobreaker.go:289 ("cb.counts.onRequest()"). Retained. Admission increments Requests once. Outcome reporting can happen zero or multiple times.
- **C10** (supported). observed-in-code gobreaker.go:299 ("if generation != before {"). Retained after state refresh. A skipped outcome can still cause reset or notification before the check.
- **C11** (supported). observed-in-code gobreaker.go:298 ("state, generation := cb.currentState(now)"). Retained. F04, F13 and F21 distinguish effects of refresh from accounting.
- **C12** (supported). observed-in-code gobreaker.go:313 ("cb.counts.onSuccess()"). Retained for a matching closed completion. The effect is confirmed by the underlying Counts method.
- **C13** (supported). observed-in-code gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). Retained with matching generation and with repeated invocation as a separate contract question.
- **C14** (supported). observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). Retained for a matching closed failure. Count increment precedes predicate and panic can prevent opening.
- **C15** (supported). observed-in-code gobreaker.go:330 ("cb.setState(StateOpen, now)"). Retained for a matching half-open failure. The path goes straight to setState and clears counters on transition.
- **C16** (supported). observed-in-code gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). Retained with lazy refresh on the next state-aware operation, strict Before comparison and no state notification.
- **C17** (supported). observed-in-code gobreaker.go:341 ("if cb.expiry.Before(now) {"). Retained with lazy refresh on the next state-aware operation. The failure and success boundaries are recorded separately in F04–F06 and F20–F21.
- **C18** (supported). observed-in-code gobreaker.go:349 ("if cb.state == state {"). Retained as a source-backed limit. No notification or reset occurs on the equal-state early return.
- **C19** (supported). observed-in-code gobreaker.go:356 ("cb.toNewGeneration(now)"). Retained. State assignment, generation increment and count clearing precede notification.
- **C20** (supported). observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Retained. It is a synchronous call and executes while the caller holds the lock.
- **C21** (supported). observed-in-code gobreaker.go:365 ("cb.counts.clear()"). Retained, using separate source lines for increment and clear.
- **C22** (supported). observed-in-code gobreaker.go:371 ("cb.expiry = zero"). Retained. Zero is the literal zero time from a zero-initialized time.Time variable, not a computed expiry.
- **C23** (supported). observed-in-code gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). Retained. Open expiry uses the recorded now plus timeout. This is a timestamp rather than a timer.
- **C24** (supported). observed-in-code gobreaker.go:378 ("cb.expiry = zero"). Retained. Zero half-open expiry accompanies the lack of a half-open check in currentState.
- **C25** (supported). observed-in-code gobreaker.go:267 ("if err != nil {"). Retained. The public rejected result is nil callback plus error.
- **C26** (supported). observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). Expanded. The generation is captured by value and invocation rereads the pointer through the captured wrapper. F01–F07 cover identity.
- **C27** (supported). observed-in-code gobreaker.go:95 ("// ReadyToTrip is called with a copy of Counts whenever a request fails in the closed state."). Retained as the Settings comment and README wording. A stale completion can bypass ReadyToTrip and half-open has a separate transition.
- **C28** (unclear). observed-in-code gobreaker.go:242 ("result, err := req()"). Jev unclear on the compound citation. Split the observed order at 229, 242 and 243. Successful admission, request and classification/report are distinct.
- **C29** (supported). observed-in-code gobreaker.go:238 ("panic(e)"). Qualified. Same non-nil recovered value propagates if the report returns. A second panic is independently observable in F18.
- **C30** (unclear). observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"). Jev unclear on the compound citation. Split acquisition at 294, refresh at 298 and mismatch at 299–300. The guarantee covers accounting and leaves refresh effects visible.
- **C31** (supported). observed-in-code gobreaker.go:281 ("state, generation := cb.currentState(now)"). Retained, using 277–278 for the lock and 281 for the state/generation check.

## Draft questions

- **Q1**. Resolved for accounting on the same breaker by explicit-requirement README.md:77–79. Retained separate questions for expiry side effects and replacement identity (F01–F06, F13, F21).
- **Q2**. Resolved in ordinary admission by explicit-requirement README.md:41–43 and observed-in-code gobreaker.go:285 (`cb.counts.Requests >= cb.maxRequests`) and :289 (`cb.counts.onRequest()`). The later guard belongs to the completion. Abandonment and replay remain open (F09–F11).
- **Q3**. Resolved for an ordinary request panic by explicit-requirement README.md:90–91, scoped to request-origin panics. Classifier and reporting-hook failures remain open (F16–F21).
- **Q4**. Retained as questions about repeats, abandonment and replacement. Same-object stale accounting is covered by explicit-requirement README.md:77–79. Late diagnostic expectations for replacement remain open (F03).
- **Q5**. Retained as a callback contract question (F22). The lock sites rule out synchronous same-breaker reentry through the listed methods.
- **Q6**. Resolved for results sent before an actual reset by explicit-requirement README.md:77–79. Retained the distinct questions about lazy refresh, first operation after expiry and which observers cause the reset (F13).
- **Q7**. Retained as a half-open abandonment/recovery question (F11). Code shows zero expiry in half-open and no half-open branch in currentState. The default timeout is for Open only.
- **Q8**. Recorded serialization. Observed-in-code gobreaker.go:294 (`cb.mutex.Lock()`), :325 (`cb.counts.onFailure()`), :326 (`if cb.readyToTrip(cb.counts) {`). Arrival order at the mutex determines matching reports. Intent around callback reentry, blocking and errors remains open (F17, F22).
- **Q9**. Removed the proposed public question about rejection generation. Both public callers return only an error and nil result/callback on ordinary rejection, observed-in-code gobreaker.go:231 (`return nil, err`) and :268 (`return nil, err`). Admission can still panic during notification (F20).
- **Q10**. Retained as a question about what fills or releases the per-generation capacity (F10–F12). Explicit-requirement README.md:41–43 states the half-open limit. Observed-in-code gobreaker.go:365 (`cb.counts.clear()`) resets accounting for each transition.

## Final findings and independent checks

Each check below was reviewed at its cited line and against neighboring control flow. Checks with a compound schedule were assessed from all needed sites and the public probe where available. Raw verdicts remain in `final-jev.json`.

### F01

Retained the observed outcome and scoped contract question or control.

- **F01.01** (supported). Allow obtains the admission generation from the breaker currently in the wrapper. observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). Retained in the stated schedule.
- **F01.02** (supported). Allow's completion reads the breaker pointer from the captured wrapper at invocation. observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). Retained in the stated schedule.
- **F01.03** (supported). Construction starts a new generation on each created breaker. observed-in-code gobreaker.go:177 ("cb.toNewGeneration(time.Now())"). Retained in the stated schedule.
- **F01.04** (supported). NewCircuitBreaker allocates a distinct breaker. observed-in-code gobreaker.go:142 ("cb := new(CircuitBreaker)"). Retained in the stated schedule.
- **F01.05** (supported). The completion guard compares the numeric generations without testing original breaker identity. observed-in-code gobreaker.go:299 ("if generation != before {"). Retained in the stated schedule.
- **F01.06** (supported). Success accounting increments TotalSuccesses. observed-in-code gobreaker.go:60 ("c.TotalSuccesses++"). Retained in the stated schedule.
- **F01.07** (supported). Failure accounting increments TotalFailures. observed-in-code gobreaker.go:66 ("c.TotalFailures++"). Retained in the stated schedule.
- **F01.08** (supported). Admission, rather than deferred completion, increments Requests. observed-in-code gobreaker.go:289 ("cb.counts.onRequest()"). Retained in the stated schedule.
- **F01.09** (supported). Closed failure calls the receiving breaker's ReadyToTrip with its current counts. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). Retained in the stated schedule.

### F02

Retained the observed outcome and scoped contract question or control.

- **F02.01** (supported). A TwoStep wrapper contains a breaker pointer, so shallow copying a wrapper copies that pointer. observed-in-code gobreaker.go:137 ("cb *CircuitBreaker"). Retained in the stated schedule.
- **F02.02** (unclear). The closure references the Allow receiver, so rebinding the caller's pointer variable does not change its captured receiver. observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). Retain code-plus-language inference, verified by the A/A/B counter assertions. Capture is in 265 and 271–273. Invocation of a Go pointer receiver does not bind to the caller's variable.

### F03

Retained the observed outcome and scoped contract question or control.

- **F03.01** (supported). Completion on a replacement with a differing current generation returns before outcome accounting. observed-in-code gobreaker.go:299 ("if generation != before {"). Retained in the stated schedule.
- **F03.02** (supported). A request retry while the target remains open returns ErrOpenState. observed-in-code gobreaker.go:284 ("return generation, ErrOpenState"). Retained in the stated schedule.

### F04

Retained the observed outcome and scoped contract question or control.

- **F04.01** (supported). Completion refreshes state before the mismatch check. observed-in-code gobreaker.go:298 ("state, generation := cb.currentState(now)"). Retained in the stated schedule.
- **F04.02** (supported). The open expiry check can transition to half-open during deferred completion. observed-in-code gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). Retained in the stated schedule.
- **F04.03** (supported). That state transition invokes the replacement's notifier if configured. observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Retained in the stated schedule.
- **F04.04** (supported). A subsequent admitted retry increments the half-open request count. observed-in-code gobreaker.go:289 ("cb.counts.onRequest()"). Retained in the stated schedule.

### F05

Retained the observed outcome and scoped contract question or control.

- **F05.01** (supported). Matching half-open success tests the consecutive success threshold. observed-in-code gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). Retained in the stated schedule.
- **F05.02** (supported). Threshold success in half-open closes the receiving breaker. observed-in-code gobreaker.go:317 ("cb.setState(StateClosed, now)"). Retained in the stated schedule.
- **F05.03** (supported). A generation change clears all counters. observed-in-code gobreaker.go:365 ("cb.counts.clear()"). Retained in the stated schedule.
- **F05.04** (supported). The original half-open breaker rejects further admissions at its charged request limit. observed-in-code gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). Retained in the stated schedule.

### F06

Retained the observed outcome and scoped contract question or control.

- **F06.01** (supported). A matching half-open failure opens the receiving breaker. observed-in-code gobreaker.go:330 ("cb.setState(StateOpen, now)"). Retained in the stated schedule.
- **F06.02** (supported). Reopening installs a new open expiry. observed-in-code gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). Retained in the stated schedule.
- **F06.03** (supported). A retry before the new open expiry returns ErrOpenState. observed-in-code gobreaker.go:284 ("return generation, ErrOpenState"). Retained in the stated schedule.

### F07

Retained the observed outcome and scoped contract question or control.

- **F07.01** (unclear). The zero-value TwoStep wrapper has a nil breaker pointer. observed-in-code gobreaker.go:137 ("cb *CircuitBreaker"). Retain as a Go zero-value inference from the pointer field and the explicit zero literal in the probe.
- **F07.02** (unclear). Completion attempts to access the nil underlying receiver's mutex after a wrapper is replaced with the zero value. observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"). Retain the panic as observed in tests. The nil dereference location is inferred from the path through 272, 293 and 294. The probe checks panic and A's retained count, without inspecting a stack.

### F08

Reclassified the whole-value overwrite as an observed API edge case with unknown contract. The public probe copies a fresh source value before any mutex-using operation on it. The Go sync.Mutex copy restriction is recorded separately.

- **F08.01** (unclear). Execute has a pointer receiver, so rebinding a caller variable does not retarget the active Execute. observed-in-code gobreaker.go:228 ("func (cb *CircuitBreaker) Execute(req func() (interface{}, error)) (interface{}, error) {"). Retain as pointer-receiver inference corroborated by the public rebinding control. This pointer receiver stays fixed even though its storage can be overwritten by a sequential caller.
- **F08.02** (unclear). Execute reads the classifier field from its receiver after the request returns. observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). Retain from the contiguous order at 242–243 and the test's classifier counters. The field is read from A's receiver address.
- **F08.03** (unclear). Closed failure invokes the ReadyToTrip field on the active receiver, including after receiver storage is overwritten. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). Retain from 325–326 and the failure subcase. A's overwritten storage receives accounting. B's own value stays unchanged.
- **F08.04** (supported). Counts returns the counters stored in the receiver as a value. observed-in-code gobreaker.go:220 ("return cb.counts"). Retained in the stated schedule.
- **F08.05** (supported). A normal Execute returns the request's result and error unchanged. observed-in-code gobreaker.go:244 ("return result, err"). Retained in the stated schedule.

### F09

Retained the observed outcome and scoped contract question or control.

- **F09.01** (unclear). The returned completion closure has no per-call consumed flag. observed-in-code gobreaker.go:271 ("return func(success bool) {"). Retain from the full callback body at 271–273 and three public invocations. The cited declaration alone cannot establish absence of a guard.
- **F09.02** (supported). Requests increments at admission. observed-in-code gobreaker.go:289 ("cb.counts.onRequest()"). Retained in the stated schedule.
- **F09.03** (supported). Failure accounting resets consecutive successes. observed-in-code gobreaker.go:68 ("c.ConsecutiveSuccesses = 0"). Retained in the stated schedule.

### F10

Retained the observed outcome and scoped contract question or control.

- **F10.01** (supported). Each matching half-open success increments the success counters. observed-in-code gobreaker.go:315 ("cb.counts.onSuccess()"). Retained in the stated schedule.
- **F10.02** (supported). The half-open threshold uses consecutive successes with no distinct-admission check. observed-in-code gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). Retained in the stated schedule.
- **F10.03** (supported). A state change enters a new generation. observed-in-code gobreaker.go:356 ("cb.toNewGeneration(now)"). Retained in the stated schedule.
- **F10.04** (supported). Following closure of the breaker, another invocation using the earlier generation is stale. observed-in-code gobreaker.go:299 ("if generation != before {"). Retained in the stated schedule.

### F11

Retained the observed outcome and scoped contract question or control.

- **F11.01** (supported). Half-open admission rejects when the request count reaches its limit. observed-in-code gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). Retained in the stated schedule.
- **F11.02** (supported). Half-open generation installs a zero expiry. observed-in-code gobreaker.go:378 ("cb.expiry = zero"). Retained in the stated schedule.
- **F11.03** (supported). A matching success closes a default one-slot half-open breaker. observed-in-code gobreaker.go:317 ("cb.setState(StateClosed, now)"). Retained in the stated schedule.
- **F11.04** (supported). A matching half-open failure reopens the breaker. observed-in-code gobreaker.go:330 ("cb.setState(StateOpen, now)"). Retained in the stated schedule.

### F12

Retained as a documented control for stale same-breaker accounting. It is not a failure finding.

- **F12.01** (supported). A first matching half-open failure opens the breaker. observed-in-code gobreaker.go:330 ("cb.setState(StateOpen, now)"). Retained in the stated schedule.
- **F12.02** (supported). The transition clears the counts. observed-in-code gobreaker.go:365 ("cb.counts.clear()"). Retained in the stated schedule.
- **F12.03** (supported). Either old result from the earlier generation exits before accounting. observed-in-code gobreaker.go:299 ("if generation != before {"). Retained in the stated schedule.

### F13

Retained the observed outcome and scoped contract question or control.

- **F13.01** (supported). Closed expiry is recognized when the saved expiry precedes a state-aware operation's time. observed-in-code gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). Retained in the stated schedule.
- **F13.02** (supported). Closed interval refresh starts a new generation without setState. observed-in-code gobreaker.go:338 ("cb.toNewGeneration(now)"). Retained in the stated schedule.
- **F13.03** (supported). Counts reads stored counts without refreshing expiry. observed-in-code gobreaker.go:220 ("return cb.counts"). Retained in the stated schedule.
- **F13.04** (supported). An afterRequest call can itself perform the refresh before attempting to report its outcome. observed-in-code gobreaker.go:298 ("state, generation := cb.currentState(now)"). Retained in the stated schedule.
- **F13.05** (supported). An accepted closed failure calls the trip predicate after recording the failure. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). Retained in the stated schedule.

### F14

Retained the observed outcome and scoped contract question or control.

- **F14.01** (supported). Execute waits synchronously for the request function to return. observed-in-code gobreaker.go:242 ("result, err := req()"). Retained in the stated schedule.
- **F14.02** (supported). The admitted request was incremented before the request ran. observed-in-code gobreaker.go:289 ("cb.counts.onRequest()"). Retained in the stated schedule.
- **F14.03** (supported). When the generation changed, either later outcome is skipped. observed-in-code gobreaker.go:299 ("if generation != before {"). Retained in the stated schedule.
- **F14.04** (unclear). Execute still returns the original request result and error after a skipped report. observed-in-code gobreaker.go:244 ("return result, err"). Retain from 298–300 and 242–244 together, corroborated by aged worker results. Caller channel behavior is observed only in the harness.

### F15

Removed the overbroad acquisition claim from the final report. The ordering concerns only the completion’s own acquisition.

- **F15.01** (supported). Execute evaluates IsSuccessful before entering afterRequest and its mutex. observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). Retained in the stated schedule.
- **F15.02** (contradicted). The accounting lock is acquired only inside afterRequest. observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"). Narrowed. In the normal completion call expression the classifier is evaluated before the afterRequest acquisition at 294. Other methods can take the same mutex, and the classifier can itself call those methods. The original ‘only’ phrasing was removed.
- **F15.03** (supported). An intervening generation change prevents either classification from being counted. observed-in-code gobreaker.go:299 ("if generation != before {"). Retained in the stated schedule.
- **F15.04** (supported). Normal Execute still returns the request's value and error. observed-in-code gobreaker.go:244 ("return result, err"). Retained in the stated schedule.

### F16

Retained the observed outcome and scoped contract question or control.

- **F16.01** (supported). Execute's defer is installed before invoking req and remains active during classification. observed-in-code gobreaker.go:234 ("defer func() {"). Retained in the stated schedule.
- **F16.02** (supported). The deferred handler uses recover. observed-in-code gobreaker.go:235 ("e := recover()"). Retained in the stated schedule.
- **F16.03** (supported). The handler submits a failure for a recovered non-nil panic. observed-in-code gobreaker.go:237 ("cb.afterRequest(generation, false)"). Retained in the stated schedule.
- **F16.04** (supported). When failure reporting returns, Execute re-panics the recovered value. observed-in-code gobreaker.go:238 ("panic(e)"). Retained in the stated schedule.
- **F16.05** (supported). After a generation change failure recording is skipped. observed-in-code gobreaker.go:299 ("if generation != before {"). Retained in the stated schedule.

### F17

Retained as an accounting and panic contract question. The locked mutations are correctly serialized, and the second accounting follows a new lock acquisition.

- **F17.01** (supported). Closed failure increments the counts before ReadyToTrip runs. observed-in-code gobreaker.go:325 ("cb.counts.onFailure()"). Retained in the stated schedule.
- **F17.02** (unclear). Panic unwinding from the trip predicate releases the reporting mutex via defer. observed-in-code gobreaker.go:295 ("defer cb.mutex.Unlock()"). Retain from the Go defer at 295 and predicate call at 326. Subsequent Counts calls and the Execute retry complete in the probes.
- **F17.03** (supported). A panic in ordinary Execute accounting causes its recovery handler to make a further failure-report attempt. observed-in-code gobreaker.go:237 ("cb.afterRequest(generation, false)"). Retained in the stated schedule.
- **F17.04** (unclear). TwoStep forwards the result directly with no recovery retry. observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). Retain from the entire closure at 271–273 plus the direct-panic and single-count test. No recover is installed by Allow for its callback.
- **F17.05** (supported). A matching recovery report while still closed increments the failure counters again. observed-in-code gobreaker.go:325 ("cb.counts.onFailure()"). Retained in the stated schedule.

### F18

Retained the observed outcome and scoped contract question or control.

- **F18.01** (unclear). If the recovery report itself panics, it does not return to the explicit re-panic statement. observed-in-code gobreaker.go:237 ("cb.afterRequest(generation, false)"). Retain under the explicitly probed second panic. The reporting call at 237 must return before 238 can run.
- **F18.02** (unclear). Both matching closed failure attempts increment failure counts before the predicate panics. observed-in-code gobreaker.go:325 ("cb.counts.onFailure()"). Retain from 325–326 and the two-count, two-callback observation under an unchanged closed generation. An external boundary during unlock would change this result.

### F19

Separated transition commitment, count clearing, unlock, retry and notification. The tested attempt skips duplicate accounting. Additional refresh remains possible before the retry guard.

- **F19.01** (supported). The new state is assigned before notification. observed-in-code gobreaker.go:354 ("cb.state = state"). Retained in the stated schedule.
- **F19.02** (supported). The state transition updates generation before notification. observed-in-code gobreaker.go:356 ("cb.toNewGeneration(now)"). Retained in the stated schedule.
- **F19.03** (supported). Generation update clears the counts. observed-in-code gobreaker.go:365 ("cb.counts.clear()"). Retained in the stated schedule.
- **F19.04** (supported). The reporting lock is released on notification panic unwind. observed-in-code gobreaker.go:295 ("defer cb.mutex.Unlock()"). Retained in the stated schedule.
- **F19.05** (supported). Execute tries a failure report after a completion notification panic. observed-in-code gobreaker.go:237 ("cb.afterRequest(generation, false)"). Retained in the stated schedule.
- **F19.06** (supported). The retry skips the original outcome when the original generation has been replaced. observed-in-code gobreaker.go:299 ("if generation != before {"). Retained in the stated schedule.
- **F19.07** (unclear). TwoStep does not wrap completion with a recover handler. observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). Retain from 271–273 and the TwoStep subcases recovering the observed panic.

### F20

Retained the observed outcome and scoped contract question or control.

- **F20.01** (supported). Open timeout handling selects a half-open transition. observed-in-code gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). Retained in the stated schedule.
- **F20.02** (unclear). A panic from expiry notification prevents admission from reaching the request increment. observed-in-code gobreaker.go:289 ("cb.counts.onRequest()"). Retain from 281, 289, 342 and 359. The tested panic unwinds before reaching admission and the counters remain empty.
- **F20.03** (supported). Execute performs admission before installing its recover defer. observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"). Retained in the stated schedule.
- **F20.04** (supported). Allow performs admission before creating the returned closure. observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). Retained in the stated schedule.
- **F20.05** (supported). Notification runs synchronously inside the transition. observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Retained in the stated schedule.
- **F20.06** (unclear). A later half-open call does not repeat the open-expiry transition. observed-in-code gobreaker.go:335 ("switch cb.state {"). Retain from 335–345 with 354. The probe checks notification count remains one after retry.

### F21

Separated the hook panic from the skipped accounting. In the panic schedule, unwind occurs before the stale guard is even reached.

- **F21.01** (supported). The stale callback invokes currentState before the generation check. observed-in-code gobreaker.go:298 ("state, generation := cb.currentState(now)"). Retained in the stated schedule.
- **F21.02** (unclear). The expiry path can enter half-open even when triggered by this stale callback. observed-in-code gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). Retain from 298–299 and 340–342 in that order. The probe records committed HalfOpen following the panic.
- **F21.03** (unclear). A notification panic can escape before the generation guard. observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Retain from 298–299 and 354–359 plus the probe's exact recovered notification panic.
- **F21.04** (supported). On that transition counters clear prior to the notification. observed-in-code gobreaker.go:365 ("cb.counts.clear()"). Retained in the stated schedule.
- **F21.05** (unclear). A following successful admission charges the previously unused slot. observed-in-code gobreaker.go:289 ("cb.counts.onRequest()"). Retain from the later public Allow succeeding after zero Counts in the probe and from the increment at 289.

### F22

Retained as a documentation and callback contract question based on locks. No deadlock test was intentionally run.

- **F22.01** (supported). The trip predicate is called from closed failure accounting under the afterRequest lock. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). Retained in the stated schedule.
- **F22.02** (supported). The notification is synchronous under the state-aware caller's lock. observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Retained in the stated schedule.
- **F22.03** (unclear). Same-breaker State acquires the mutex. observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). Retain direct source observation at 206–208. The deadlock consequence is a source and Go mutex inference. No intentionally blocked test was run.
- **F22.04** (supported). Same-breaker Counts acquires the mutex. observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). Retained in the stated schedule.
- **F22.05** (supported). Same-breaker admission acquires the mutex. observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"). Retained in the stated schedule.
- **F22.06** (supported). Name returns the name without taking the mutex. observed-in-code gobreaker.go:202 ("return cb.name"). Retained in the stated schedule.

### F23

Retained the observed outcome and scoped contract question or control.

- **F23.01** (supported). The constructor takes Settings by value. observed-in-code gobreaker.go:141 ("func NewCircuitBreaker(st Settings) *CircuitBreaker {"). Retained in the stated schedule.
- **F23.02** (supported). The constructor stores the OnStateChange function value. observed-in-code gobreaker.go:145 ("cb.onStateChange = st.OnStateChange"). Retained in the stated schedule.
- **F23.03** (supported). The constructor stores the supplied trip predicate function value. observed-in-code gobreaker.go:168 ("cb.readyToTrip = st.ReadyToTrip"). Retained in the stated schedule.
- **F23.04** (supported). The constructor stores the supplied classification function value. observed-in-code gobreaker.go:174 ("cb.isSuccessful = st.IsSuccessful"). Retained in the stated schedule.

### F24

Retained the observed outcome and scoped contract question or control.

- **F24.01** (supported). The TwoStep callback passes its caller-supplied boolean directly into accounting. observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). Retained in the stated schedule.
- **F24.02** (supported). Execute calls IsSuccessful to obtain the boolean passed into accounting. observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). Retained in the stated schedule.

## Lock and ordering checks

- observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:295 ("defer cb.mutex.Unlock()"), gobreaker.go:298 ("state, generation := cb.currentState(now)") and gobreaker.go:299 ("if generation != before {"). Refresh, generation comparison and accounting on a single breaker are serialized under its mutex. A second operation cannot cross the state boundary between that comparison and the count mutation. Callback bodies at gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") and gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") are synchronous under that lock. If they run long, elapsed wall-clock time can pass a deadline before they return. Another state-aware operation cannot refresh until the lock is released. The timeout installed by setState uses the already sampled now at gobreaker.go:297 ("now := time.Now()") and gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").
- observed-in-code gobreaker.go:237 ("cb.afterRequest(generation, false)"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:295 ("defer cb.mutex.Unlock()"), gobreaker.go:325 ("cb.counts.onFailure()") and gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). If a normal Execute closed failure reaches a panicking predicate, the first increment is committed. Unlock on unwind permits two retry orders. If the same generation is still current, recovery increments failure again. If the retry or an intervening operation refreshes expiry or changes generation first, it skips the outcome at gobreaker.go:299 ("if generation != before {"). The matching order was probed. The intervening order is inferred and remains open under F17.
- observed-in-code gobreaker.go:298 ("state, generation := cb.currentState(now)"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:354 ("cb.state = state"), gobreaker.go:356 ("cb.toNewGeneration(now)") and gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). OnStateChange following an expiry can run before admission or a stale check. On completion-driven transitions the notification follows transition and count clearing, including the HalfOpen success and failure paths. A notification failure can prevent the following work without rolling back the transition. The public probes assert the resulting retry and notification counts. If a long-running notification leaves an Open deadline already passed before Execute retries, a new expiry notification may run then. Its success, panic or whether another operation observes it first is untested.
- observed-in-code gobreaker.go:367 ("var zero time.Time"), gobreaker.go:371 ("cb.expiry = zero") and gobreaker.go:378 ("cb.expiry = zero"). The zero time is Go zero initialization. Configured deadlines use gobreaker.go:373 ("cb.expiry = now.Add(cb.interval)") and gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). No fragile computed sentinel or CAS path was identified.
- observed-in-code gobreaker.go:265 ("func (tscb *TwoStepCircuitBreaker) Allow() (done func(success bool), err error) {"), gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()") and gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). Mutation of the wrapper itself is outside the inner breaker lock. The overwrite probes order assignment before invocation, so the observed redirection is a sequential identity effect. Concurrent replacement and arbitrary copied mutex behavior are outside the probes.

## Additional ordered consequences

- **Classifier or request returns before a trip.** observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:304 ("cb.onSuccess(state, now)") and gobreaker.go:306 ("cb.onFailure(state, now)"). If accounting acquires the lock before the other operation changes the generation, it applies the classification. If the other operation wins the lock and changes the generation first, it discards either classification. A classifier already running remains the function value selected for that call. Its external effects can occur before the stale check. Normal return still reaches the worker. The same-generation and stale controls are F14–F16.
- **ReadyToTrip across a deadline.** observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:295 ("defer cb.mutex.Unlock()"), gobreaker.go:297 ("now := time.Now()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:327 ("cb.setState(StateOpen, now)") and gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). Inferred: if an already admitted closed failure reaches the predicate before expiry, the failure increments before its callback. While the predicate blocks, another call cannot refresh under the mutex. Returning false leaves the count available until lazy expiry is refreshed. Returning true starts a new Open generation and uses the timestamp sampled before the predicate. If the boundary was already refreshed before afterRequest, a stale failure never calls the predicate. If the predicate panics, the unwind releases the lock. A retry on the prior generation may count again or may refresh the expired interval and discard the outcome. On a plain TwoStep report the caller instead receives the panic directly. The deadline-crossing predicate schedules were traced by source, with only stable-window panic and expiry controls probed.
- **Slow or panicking OnStateChange after entering Open.** observed-in-code gobreaker.go:354 ("cb.state = state"), gobreaker.go:356 ("cb.toNewGeneration(now)"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)") and gobreaker.go:237 ("cb.afterRequest(generation, false)"). Inferred: a successful notification leaves the Open state committed. Any later observer may advance it if its deadline passed during notification. If a completion hook panics, Execute recovery can be the next observer after unlock. If the deadline is still in the future, the old report skips on generation mismatch. If due, recovery itself enters HalfOpen. A returning HalfOpen notification lets its retry reach the stale check, followed by re-panic of the first failure. A panicking HalfOpen notification exits the retry before that check and the second panic reaches the outer caller. If a separate observer enters HalfOpen first, recovery sees that committed generation instead. Another operation cannot observe the partially executed notification through the mutex-taking APIs until that notification returns or unwinds. The long or intervening schedules were traced by source and left untested.
- **No callback or result on public rejection.** explicit-requirement README.md:87–89 covers Execute rejecting before running the request. observed-in-code gobreaker.go:231 ("return nil, err"), gobreaker.go:268 ("return nil, err"), gobreaker.go:284 ("return generation, ErrOpenState") and gobreaker.go:286 ("return generation, ErrTooManyRequests"). These are ordinary rejection outcomes. A panic in the pre-admission expiry hook has the distinct F20 result.
