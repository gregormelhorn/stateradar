# Invariants and lints

NAT-01: Constructed, uncopied breaker and legitimate continuation, Go mutex semantics, and effective MaxRequests in [1, 2³²−1]. Go sync/mutex.go:20 ("// A Mutex must not be copied after first use."), gobreaker.go:147 ("if st.MaxRequests == 0 {") gobreaker.go:271 ("return func(success bool) {"). NAT-02: Generation and counter domains are uint64 and uint32 respectively, and callback return is a conditional assumption only. gobreaker.go:48 ("Requests             uint32") gobreaker.go:128 ("generation uint64"). NAT-SYS: In shared dependency deployments, simultaneous upstream failure and similarly timed client attempts may synchronize instances. This is a deployment assumption, with independent instance timers gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").

| ID | Predicate and provenance | Closed | Open | HalfOpen |
| --- | --- | --- | --- | --- |
| SYS-01 | Refusal skips request work; strict instantaneous refusal under contention is open. README.md:88 ("`Execute` returns an error instantly if `CircuitBreaker` rejects the request.") gobreaker.go:231 ("return nil, err") gobreaker.go:277 ("cb.mutex.Lock()") | Ordinary admissions accepted | Before expiry refuses, Q-10 | At budget refuses, Q-10 |
| SYS-02 | Constructor applies settings/defaults on new identity. README.md:19 ("The function `NewCircuitBreaker` creates a new `CircuitBreaker`.") gobreaker.go:142 ("cb := new(CircuitBreaker)") gobreaker.go:177 ("cb.toNewGeneration(time.Now())") | Established | Inherited | Inherited |
| SYS-03 | No more than effective MaxRequests admitted in one half-open generation. README.md:41 ("- `MaxRequests` is the maximum number of requests allowed to pass through") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") | Outside guard | No admissions while stored Open | Proven G-01; reports can duplicate, Q-03 |
| SYS-04 | State changes and due observed Closed intervals clear counts; counters describe admissions and reported outcomes. README.md:77 ("`CircuitBreaker` clears the internal `Counts` either") README.md:78 ("on the change of the state or at the closed-state intervals.") gobreaker.go:365 ("cb.counts.clear()") | Observed lazily, Q-01; exact bounded accounting Q-09 | Zero before expiry; reset on exit | Reset on exit; repeated reporting can make outcomes exceed admissions, Q-03 |
| SYS-05 | Open leaves after timeout, timing wording lacks refresh actor and exact boundary. README.md:50 ("after which the state of `CircuitBreaker` becomes half-open.") gobreaker.go:341 ("if cb.expiry.Before(now) {") | Outside interval | Lazy, Q-01 | No expiry; missing progression Q-02 |
| SYS-06 | Apply copied Closed failure counts with trip predicate. README.md:53 ("- `ReadyToTrip` is called with a copy of `Counts` whenever a request fails in the closed state.") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") | Matching failure increments then calls; panic Q-06 | No invocation | Current failure opens directly, Q-12 |
| SYS-07 | Notify configured observer once per distinct transition. README.md:58 ("- `OnStateChange` is called whenever the state of `CircuitBreaker` changes.") gobreaker.go:349 ("if cb.state == state {") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") | Exit to Open only, not interval clear | Exit to HalfOpen | Either exit. Under lock, Q-05/Q-06 in every transition |
| SYS-08 | Normal Execute return uses classifier; only current result contributes. README.md:60 ("- `IsSuccessful` is called with the error returned from a request.") README.md:79 ("`Counts` ignores the results of the requests sent before clearing.") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:299 ("if generation != before {") | Classifies then counts when current; policy failure Q-06 | Classifier can run for old work, Q-04 | Success counts; failure opens and resets, Q-12 |
| SYS-09 | Stale result contributes no current count. README.md:79 ("`Counts` ignores the results of the requests sent before clearing.") gobreaker.go:299 ("if generation != before {") | Checked after refresh | Checked after possible transition, Q-04 | Checked; generation wrap Q-09 |
| SYS-10 | Execute calls work only after admission and returns unchanged pair after ordinary accounting. README.md:87 ("The method `Execute` runs the given request if `CircuitBreaker` accepts it.") README.md:89 ("Otherwise, `Execute` returns the result of the request.") gobreaker.go:242 ("result, err := req()") gobreaker.go:244 ("return result, err") | Yes under normal return | Eligibility only after transition | Yes below budget; abandoned work Q-02 |
| SYS-11 | Current ordinary request panic feeds failure and escapes with same payload under normal bookkeeping. README.md:90 ("If a panic occurs in the request, `CircuitBreaker` handles it as an error") README.md:91 ("and causes the same panic again.") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:238 ("panic(e)") | Possible callback replacement Q-16 | Stale outcome excluded; expiry notification may fail Q-06 | Failure reopens; possibly panic replacement Q-16 |

## Lint results

- F-07/F-13, step-5 lint. Awaiting work or report in HalfOpen has no timeout, cancel or slot reclamation, Q-02. No retry loop exists within the breaker. gobreaker.go:242 ("result, err := req()") gobreaker.go:271 ("return func(success bool) {") gobreaker.go:377 ("default: // StateHalfOpen").
- F-03, seam-contract sweep. Request and all policy failure paths are distinct; no explicit failure contract for injected policies, Q-05/Q-06/Q-16. gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").
- F-02/F-06, step-5 lint. Refusal can follow lock delay and a callback. There is no terminal state, only refusal errors that describe mode or budget. Startup through constructor is defined; invalid receiver use and abandonment have no lifecycle contract, Q-08/Q-10/Q-12/Q-13. gobreaker.go:142 ("cb := new(CircuitBreaker)") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:284 ("return generation, ErrOpenState") gobreaker.go:286 ("return generation, ErrTooManyRequests").
- F-05, step-5 lint. No queue exists; overt overload is immediately decided after lock acquisition, per-generation counters wrap, and Closed admits without a budget, Q-09/Q-10. gobreaker.go:56 ("c.Requests++") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:289 ("cb.counts.onRequest()").
- F-10, multi-instance probes. Open to HalfOpen restores per-instance probe admission after a fixed timeout. Successful HalfOpen to Closed releases that cap, Q-11. gobreaker.go:317 ("cb.setState(StateClosed, now)") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").
- F-07/F-09, step-5 lint. Caller work can terminate while its admission still counts. No channel transfer, destructor, or release API exists at this seam, so explicit/destructor dual release and internal channel ownership are inapplicable. Repeated completion is independently possible, Q-02/Q-03/Q-13. gobreaker.go:271 ("return func(success bool) {") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:289 ("cb.counts.onRequest()").
- F-02/F-13, adversarial trace. A second call during outstanding work can hit HalfOpen capacity even though the caller has yet to see the first result. Overlapping calls may return in reverse order, Q-15. gobreaker.go:242 ("result, err := req()") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {").
- F-21, step-2 test replay. Custom expiry test asserts the other instance, Q-14. gobreaker_test.go:247 ("assert.True(t, defaultCB.expiry.IsZero())").

<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 DOC-5 DOC-6 DOC-7 DOC-8 DOC-9 DOC-10 DOC-11 DOC-12 DOC-13 DOC-14 DOC-15 DOC-16 DOC-17 DOC-18 DOC-19 DOC-20 DOC-21 DOC-22 DOC-23 DOC-24 DOC-25 DOC-26 DOC-27 -->

## Doctrine mapping

| Doctrine | Kind | Target |
| --- | --- | --- |
| DOC-1 | constraint | SYS-01 |
| DOC-2 | constraint | SYS-02 |
| DOC-3 | constraint | SYS-02 |
| DOC-4 | invariant | SYS-02 |
| DOC-5 | invariant | SYS-03 |
| DOC-6 | invariant | SYS-02 |
| DOC-7 | invariant | SYS-04 |
| DOC-8 | invariant | SYS-04 |
| DOC-9 | invariant | SYS-05 |
| DOC-10 | invariant | SYS-02 |
| DOC-11 | invariant | SYS-06 |
| DOC-12 | cell | Closed x Report |
| DOC-13 | invariant | SYS-02 |
| DOC-14 | guard | G-04 |
| DOC-15 | invariant | SYS-07 |
| DOC-16 | invariant | SYS-08 |
| DOC-17 | invariant | SYS-08 |
| DOC-18 | invariant | SYS-08 |
| DOC-19 | invariant | SYS-02 |
| DOC-20 | invariant | SYS-04 |
| DOC-21 | invariant | SYS-04 |
| DOC-22 | invariant | SYS-09 |
| DOC-23 | constraint | SYS-10 |
| DOC-24 | invariant | SYS-10 |
| DOC-25 | invariant | SYS-01 |
| DOC-26 | invariant | SYS-10 |
| DOC-27 | invariant | SYS-11 |

## Step 8 finding verification

The implementation and probe support fault mechanisms under the stated schedules. Duplicate reporting and redirection across an overwritten wrapper are API/accounting issues. Missing progress is a lifecycle issue. Same-lock reentry is a liveness defect under reentry, with documented intent still open. Timing wording, negative-duration defaults and half-open threshold publication are contract gaps. Counter wrap and cross-instance load are contextual risks. No general data race is asserted from separated admission and completion. The zero expiry sentinel is a literal zero value; nil panic depends on runtime mode. The misplaced test assertion is test evidence quality, not a runtime defect.

| Check | Source evidence | Jev | Independent disposition |
| --- | --- | --- | --- |
| finding_docs-01 | README.md:88 ("`Execute` returns an error instantly if `CircuitBreaker` rejects the request.") | supported | README describes Execute rejection as instant. |
| finding_docs-02 | README.md:47 ("If `Interval` is 0, `CircuitBreaker` doesn't clear the internal `Counts` during the closed state.") | unclear | README explicitly names zero for disabled Interval. Source review retains the specific observation using adjacent lines or the probe. See below. |
| finding_docs-03 | README.md:51 ("If `Timeout` is 0, the timeout value of `CircuitBreaker` is set to 60 seconds.") | contradicted | README explicitly names zero for default Timeout. Source review retains the specific observation using adjacent lines or the probe. See below. |
| finding_docs-04 | README.md:58 ("- `OnStateChange` is called whenever the state of `CircuitBreaker` changes.") | supported | README specifies callback on state change without a reentrancy restriction in the cited sentence. |
| new-1 | gobreaker.go:271 ("return func(success bool) {") | unclear | The returned closure is a function capturing the wrapper through a reference. Source review retains the specific observation using adjacent lines or the probe. See below. |
| new-2 | gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") | supported | The closure reads the backing breaker field at invocation and passes the earlier captured generation. |
| new-3 | gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()") | supported | Allow obtains the captured generation from the backing breaker at admission. |
| new-4 | gobreaker.go:325 ("cb.counts.onFailure()") | supported | A Closed failure increments failure counters before the trip predicate is invoked. |
| new-5 | gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") | supported | ReadyToTrip is invoked after the Closed failure counter update. |
| new-6 | gobreaker.go:294 ("cb.mutex.Lock()") | supported | Completion acquires the breaker mutex before touching the state. |
| new-7 | gobreaker.go:295 ("defer cb.mutex.Unlock()") | supported | The completion path defers unlocking the mutex. |
| new-8 | gobreaker.go:237 ("cb.afterRequest(generation, false)") | supported | Execute attempts failure accounting after recovering a non-nil panic. |
| finding_go-01 | gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") | supported | Closed interval has a strict-before guard and a nonzero expiry requirement. |
| finding_go-02 | gobreaker.go:341 ("if cb.expiry.Before(now) {") | supported | Open expiry uses strict Before. |
| finding_go-03 | gobreaker.go:220 ("return cb.counts") | supported | Counts returns stored counters. |
| finding_go-04 | gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") | supported | Half-open rejects at the budget. |
| finding_go-05 | gobreaker.go:378 ("cb.expiry = zero") | supported | Half-open expiry is unset. |
| finding_go-06 | gobreaker.go:271 ("return func(success bool) {") | unclear | Allow makes a closure with no once-only latch. Source review retains the specific observation using adjacent lines or the probe. See below. |
| finding_go-07 | gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") | unclear | Every invocation of that closure passes its admission generation and payload. Source review retains the specific observation using adjacent lines or the probe. See below. |
| finding_go-08 | gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {") | supported | HalfOpen checks its current success streak against admission budget. |
| finding_go-09 | gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") | supported | Classification is evaluated before afterRequest is invoked. |
| finding_go-10 | gobreaker.go:298 ("state, generation := cb.currentState(now)") | supported | Completion refreshes state before checking generation. |
| finding_go-11 | gobreaker.go:299 ("if generation != before {") | supported | Mismatch causes early return before outcome accounting. |
| finding_go-12 | gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") | supported | Notification runs synchronously inside setState if present. |
| finding_go-13 | gobreaker.go:294 ("cb.mutex.Lock()") | supported | Completion takes the mutex. |
| finding_go-14 | gobreaker.go:217 ("cb.mutex.Lock()") | supported | Counts takes the mutex. |
| finding_go-15 | gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") | supported | ReadyToTrip runs after the counter update. |
| finding_go-16 | gobreaker.go:237 ("cb.afterRequest(generation, false)") | supported | Execute recovery attempts failure accounting. |
| finding_go-17 | gobreaker.go:238 ("panic(e)") | supported | Rep​anic is after accounting. |
| finding_go-18 | gobreaker.go:354 ("cb.state = state") | supported | State writes precede notification. |
| finding_go-19 | gobreaker.go:356 ("cb.toNewGeneration(now)") | supported | Generation reset precedes notification. |
| finding_go-20 | gobreaker.go:242 ("result, err := req()") | supported | Execute calls the supplied function directly after admission. |
| finding_go-21 | gobreaker.go:56 ("c.Requests++") | supported | Request count increments on every admitted request. |
| finding_go-22 | gobreaker.go:48 ("Requests             uint32") | supported | Requests is uint32. |
| finding_go-23 | gobreaker.go:128 ("generation uint64") | supported | Generation is uint64. |
| finding_go-24 | gobreaker.go:277 ("cb.mutex.Lock()") | supported | Admission locks even for a rejected call. |
| finding_go-25 | gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)") | supported | Open uses its configured timeout with no jitter in this expression. |
| finding_go-26 | gobreaker.go:330 ("cb.setState(StateOpen, now)") | supported | A current HalfOpen failure opens the breaker. |
| finding_go-27 | gobreaker.go:183 ("func NewTwoStepCircuitBreaker(st Settings) *TwoStepCircuitBreaker {") | unclear | NewTwoStepCircuitBreaker constructs a distinct wrapper backed by a new core. Source review retains the specific observation using adjacent lines or the probe. See below. |
| finding_go-28 | gobreaker.go:159 ("if st.Timeout <= 0 {") | supported | Nonpositive Timeout selects a default. |
| finding_tests-01 | gobreaker_test.go:247 ("assert.True(t, defaultCB.expiry.IsZero())") | supported | The custom breaker scenario asserts the default breaker's expiry at this line. |

- finding_go-06/07: the complete closure spans gobreaker.go:271-273 and the guarded accounting spans gobreaker.go:294-306. Executed DuplicateCompletion establishes absence of a one-shot guard at the public seam.
- finding_go-27: gobreaker.go:183-186 returns the wrapper and calls the new core constructor. The probe constructs two wrappers and observes isolated counts until assignment redirects the old callback.
- finding_docs-02/03: README.md:47 and README.md:51 explicitly cover zero. The wording is inclusive of zero and silent on negatives. Settings comments and checks at gobreaker.go:89, 93, 153 and 159 cover nonpositive values. The model choices remain as returned.
- Follow-up unclear choice: inspect both the closure introduction and body, and compare the independent overlay assertions. It does not overturn the executed outcome.
