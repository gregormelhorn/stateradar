# Event catalogue

<!-- event-ids: Configure Execute Allow ReportSuccess ReportFailure ReadState ReadCounts ReadName RequestResult Classify TripDecision Notify ObserveExpiry ApplySuccess ApplyFailure UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 UV-15 UV-16 UV-17 UV-18 UV-20 UV-21 -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| Configure | external | constructor caller | Settings select a new breaker and its policy, observed-in-code gobreaker.go:142 ("cb := new(CircuitBreaker)") and gobreaker.go:177 ("cb.toNewGeneration(time.Now())"). |
| Execute | external | request submitter | Pass a function for admission and execution, observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()") and gobreaker.go:242 ("result, err := req()"). |
| Allow | external | two-step submitter | Ask for admission and an outcome callback, observed-in-code gobreaker.go:265 ("func (tscb *TwoStepCircuitBreaker) Allow() (done func(success bool), err error) {") and gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). |
| ReportSuccess | external | outcome reporter | Report true through the callback returned by Allow, observed-in-code gobreaker.go:271 ("return func(success bool) {") and gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). |
| ReportFailure | external | outcome reporter | Report false through the callback returned by Allow, observed-in-code gobreaker.go:271 ("return func(success bool) {") and gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). |
| ReadState | external | state observer | Request reported state, observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)"). |
| ReadCounts | external | counts observer | Request the counters, observed-in-code gobreaker.go:220 ("return cb.counts"). |
| ReadName | external | name observer | Request the configured name, observed-in-code gobreaker.go:202 ("return cb.name"). |
| RequestResult | external | injected request | Return a value/error, panic, or fail to return after admission, observed-in-code gobreaker.go:242 ("result, err := req()") and gobreaker.go:235 ("e := recover()"). |
| Classify | external | injected classifier | Return an error classification for Execute, observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). |
| TripDecision | external | injected trip policy | Return a decision after a counted closed failure, observed-in-code gobreaker.go:325 ("cb.counts.onFailure()") and gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). |
| Notify | internal | breaker notification to injected observer | Call the registered state-change observer with name and state pair, observed-in-code gobreaker.go:358 ("if cb.onStateChange != nil {") and gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). |
| ObserveExpiry | internal | clock sampled by breaker | Compare expiry with sampled time, observed-in-code gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") and gobreaker.go:341 ("if cb.expiry.Before(now) {"). |
| ApplySuccess | internal | breaker completion accounting | Apply a successful outcome, observed-in-code gobreaker.go:299 ("if generation != before {") and gobreaker.go:315 ("cb.counts.onSuccess()"). |
| ApplyFailure | internal | breaker completion accounting | Apply a failed outcome, observed-in-code gobreaker.go:299 ("if generation != before {") and gobreaker.go:325 ("cb.counts.onFailure()"). |
| UV-01 | external | injected request or submitter | Work never returns, exits its goroutine, or panics, or submitter abandons interest. |
| UV-02 | external | request submitter and injected request | Slow completion or submission, later overlapping request, and elapsed deadline while work remains outstanding. |
| UV-03 | external | request submitter | A second Execute from the same caller while the first is pending, or after it returns and the caller still owns its result. |
| UV-04 | external | public caller | Nil request, a call on the wrong valid breaker, or a nil or unconstructed receiver. Receiver selection differs from erroneous report payload. |
| UV-05 | external | two-step submitter | Attempt arrives late, or caller stops before or during submission, or after receiving the completion callback. |
| UV-06 | external | two-step submitter | Same caller issues a second Allow before the first returns, or after the first returns while it still holds its callback. |
| UV-07 | external | outcome reporter | Report omitted after an accepted trial, including logical teardown by caller. |
| UV-08 | external | outcome reporter or long-running request | Outcome after generation rollover, elapsed expiry, or application cancellation. Success and failure are separate outcomes. |
| UV-09 | external | outcome reporter | Same completion repeated sequentially or concurrently with equal or contradictory Booleans. |
| UV-10 | external | outcome reporter or injected callback | Unsolicited completion without admission, including invoking a nil callback returned with rejection. |
| UV-11 | external | outcome reporter or injected classifier/policy | A valid but wrong Boolean, a callback reused for another request, or trip policy using an unintentionally misleading ratio. |
| UV-12 | external | observer | Missing, late, repeated, or interleaved read of state, counts or name. |
| UV-13 | external | injected classifier | Classifier panics, blocks, or exits the goroutine. |
| UV-14 | external | injected classifier | Classification finishes after generation changed, or re-enters the breaker before committing its result. |
| UV-15 | external | injected trip policy | Trip callback panics, blocks, exits, or re-enters mutex-taking methods. |
| UV-16 | external | injected observer | Observer absent, panics, blocks, exits, or re-enters mutex-taking methods. |
| UV-17 | internal | observer callback consumer | Repeated same-named transitions across cycles or instances, or consumer misattributes the notification. Unsolicited callback invocation is possible outside the breaker by whoever owns the function. |
| UV-18 | internal | clock observation | Deadline elapses without a qualifying call, delayed observation, equality at deadline, or clock time differs from intended schedule. |
| UV-20 | external | constructor caller | Construction omitted, or two calls create independently configured instances when one was intended. |
| UV-21 | external | constructor caller | Negative durations or valid but unintended large request limit, interval or timeout. |

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| Configure: constructor caller | UV-20 | n/a: no independent delivery at this boundary, gobreaker.go:142 ("cb := new(CircuitBreaker)"). | UV-20 | n/a: no independent delivery at this boundary, gobreaker.go:142 ("cb := new(CircuitBreaker)"). | n/a: no independent delivery at this boundary, gobreaker.go:142 ("cb := new(CircuitBreaker)"). | n/a: no independent delivery at this boundary, gobreaker.go:142 ("cb := new(CircuitBreaker)"). | UV-21 |
| Execute: request submitter | UV-01 | UV-02 | UV-03 | UV-02 | UV-03 | UV-04 | UV-04 |
| Allow: two-step submitter | UV-05 | UV-05 | UV-06 | UV-05 | UV-06 | UV-04 | UV-04 |
| ReportSuccess: outcome reporter | UV-07 | UV-08 | UV-09 | UV-08 | UV-09 | UV-10 | UV-11 |
| ReportFailure: outcome reporter | UV-07 | UV-08 | UV-09 | UV-08 | UV-09 | UV-10 | UV-11 |
| ReadState: state observer | UV-12 | UV-12 | UV-12 | UV-12 | n/a: no independent delivery at this boundary, gobreaker.go:211 ("state, _ := cb.currentState(now)"). | n/a: no independent delivery at this boundary, gobreaker.go:211 ("state, _ := cb.currentState(now)"). | UV-04 |
| ReadCounts: counts observer | UV-12 | UV-12 | UV-12 | UV-12 | n/a: no independent delivery at this boundary, gobreaker.go:220 ("return cb.counts"). | n/a: no independent delivery at this boundary, gobreaker.go:220 ("return cb.counts"). | UV-04 |
| ReadName: name observer | UV-12 | UV-12 | UV-12 | UV-12 | n/a: no independent delivery at this boundary, gobreaker.go:202 ("return cb.name"). | n/a: no independent delivery at this boundary, gobreaker.go:202 ("return cb.name"). | UV-04 |
| RequestResult: injected request | UV-01 | UV-02 | n/a: no independent delivery at this boundary, gobreaker.go:242 ("result, err := req()"). | UV-08 | n/a: no independent delivery at this boundary, gobreaker.go:242 ("result, err := req()"). | UV-10 | UV-11 |
| Classify: injected classifier | UV-13 | UV-13 | n/a: no independent delivery at this boundary, gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). | UV-14 | n/a: no independent delivery at this boundary, gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). | UV-10 | UV-11 |
| TripDecision: injected trip policy | UV-15 | UV-15 | n/a: no independent delivery at this boundary, gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). | n/a: no independent delivery at this boundary, gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). | n/a: no independent delivery at this boundary, gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). | UV-10 | UV-11 |
| Notify: breaker notification to injected observer | UV-16 | UV-16 | UV-17 | UV-17 | UV-17 | UV-17 | UV-17 |
| ObserveExpiry: clock sampled by breaker | UV-18 | UV-18 | n/a: no independent delivery at this boundary, gobreaker.go:341 ("if cb.expiry.Before(now) {"). | UV-18 | n/a: no independent delivery at this boundary, gobreaker.go:341 ("if cb.expiry.Before(now) {"). | n/a: no independent delivery at this boundary, gobreaker.go:341 ("if cb.expiry.Before(now) {"). | UV-18 |
| ApplySuccess: breaker completion accounting | n/a: no independent delivery at this boundary, gobreaker.go:304 ("cb.onSuccess(state, now)"). | UV-08 | UV-09 | UV-08 | UV-09 | UV-10 | UV-11 |
| ApplyFailure: breaker completion accounting | n/a: no independent delivery at this boundary, gobreaker.go:306 ("cb.onFailure(state, now)"). | UV-08 | UV-09 | UV-08 | UV-09 | UV-10 | UV-11 |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Execute → ReadState | Execute submitter and observer on one breaker |
| P-01b | ReadState → Execute | Execute submitter and observer on one breaker |
| P-02a | Execute → ReadCounts | Execute submitter and counts observer on one breaker |
| P-02b | ReadCounts → Execute | Execute submitter and counts observer on one breaker |
| P-03a | Allow → ReportSuccess | new admission and outstanding successful trial callback |
| P-03b | ReportSuccess → Allow | new admission and outstanding successful trial callback |
| P-04a | Allow → ReportFailure | new admission and outstanding failed trial callback |
| P-04b | ReportFailure → Allow | new admission and outstanding failed trial callback |
| P-05a | ReportSuccess → ReadState | outcome callback and expiry-observing reader |
| P-05b | ReadState → ReportSuccess | outcome callback and expiry-observing reader |
| P-06a | ReportFailure → ReadState | outcome callback and expiry-observing reader |
| P-06b | ReadState → ReportFailure | outcome callback and expiry-observing reader |
| P-07a | ReportSuccess → ReadCounts | outcome callback and counts observer |
| P-07b | ReadCounts → ReportSuccess | outcome callback and counts observer |
| P-08a | ReportFailure → ReadCounts | outcome callback and counts observer |
| P-08b | ReadCounts → ReportFailure | outcome callback and counts observer |
| P-09a | ReadState → ReadCounts | independent readers near expiry |
| P-09b | ReadCounts → ReadState | independent readers near expiry |
| P-10a | RequestResult → ReadState | injected workload return overlapping observer |
| P-10b | ReadState → RequestResult | injected workload return overlapping observer |
| P-11a | Classify → ReadState | injected classifier return overlapping observer |
| P-11b | ReadState → Classify | injected classifier return overlapping observer |
| P-12a | Allow → ReadState | new trial and observer at expiry |
| P-12b | ReadState → Allow | new trial and observer at expiry |
| P-13a | Allow → ReadCounts | new trial and counts observer |
| P-13b | ReadCounts → Allow | new trial and counts observer |
| P-14a | ReportSuccess → ReportFailure | different actors holding independent trial callbacks |
| P-14b | ReportFailure → ReportSuccess | different actors holding independent trial callbacks |
| P-15a | TripDecision → ReadState | policy inside lock and competing reader |
| P-15b | ReadState → TripDecision | policy inside lock and competing reader |

## Remembrance semantics

Observed-in-code: admissions consume a counter until a generation reset gobreaker.go:289 ("cb.counts.onRequest()") and gobreaker.go:365 ("cb.counts.clear()"). Generation is a uint64 gobreaker.go:128 ("generation uint64"). Request result and returned callback are caller-owned. A retained closure keeps its receiver and generation available gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). Breaker stores no per-request history; equality check at gobreaker.go:299 ("if generation != before {"). Lifetime and memory use depend on external references.

## Lock-discipline annotation

Observed-in-code: State gobreaker.go:207 ("cb.mutex.Lock()"), Counts gobreaker.go:217 ("cb.mutex.Lock()"), admission gobreaker.go:277 ("cb.mutex.Lock()"), and completion gobreaker.go:294 ("cb.mutex.Lock()") take the same mutex. Trip policy gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") and transition observer gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") execute in these paths. Request and classifier execute outside the mutex gobreaker.go:242 ("result, err := req()") and gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). Settings contracts README.md:53-63 specify neither reentrancy nor panic policy.

## Catalogue notes

Execute and Allow are alternate public front ends on their respective constructed instances. The internal outcome events describe bookkeeping phases, and do not denote independently callable operations.

## Event annotations

### Configure
- gate: payload settings
- upstream_guards: Direct Go calls, typed assignments only. No upstream value normalization.
- coverage:
  - loss: UV-20
  - delay: n/a: no independent delivery at this boundary, gobreaker.go:142 ("cb := new(CircuitBreaker)").
  - duplication: UV-20
  - out-of-order: n/a: no independent delivery at this boundary, gobreaker.go:142 ("cb := new(CircuitBreaker)").
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go:142 ("cb := new(CircuitBreaker)").
  - commission: n/a: no independent delivery at this boundary, gobreaker.go:142 ("cb := new(CircuitBreaker)").
  - value: UV-21

### Execute
- gate: service state for admission
- upstream_guards: Direct API has no nil or instance-purpose validation. Example binds its own receiver in example/http_breaker.go:27.
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-02
  - contradiction: UV-03
  - commission: UV-04
  - value: UV-04

### Allow
- gate: service state for admission
- upstream_guards: Direct API supplies no caller identity or request lifecycle validation.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05
  - contradiction: UV-06
  - commission: UV-04
  - value: UV-04

### ReportSuccess
- gate: payload Boolean and service generation and threshold
- upstream_guards: Closure binds receiver and generation. No upstream single-shot or result truth guarantee.
- coverage:
  - loss: UV-07
  - delay: UV-08
  - duplication: UV-09
  - out-of-order: UV-08
  - contradiction: UV-09
  - commission: UV-10
  - value: UV-11

### ReportFailure
- gate: payload Boolean and service generation and trip policy
- upstream_guards: Same caller-side ownership as the success report.
- coverage:
  - loss: UV-07
  - delay: UV-08
  - duplication: UV-09
  - out-of-order: UV-08
  - contradiction: UV-09
  - commission: UV-10
  - value: UV-11

### ReadState
- gate: service expiry
- upstream_guards: No upstream scheduling or receiver-purpose validation.
- coverage:
  - loss: UV-12
  - delay: UV-12
  - duplication: UV-12
  - out-of-order: UV-12
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go:211 ("state, _ := cb.currentState(now)").
  - commission: n/a: no independent delivery at this boundary, gobreaker.go:211 ("state, _ := cb.currentState(now)").
  - value: UV-04

### ReadCounts
- gate: none beyond receiver and synchronization
- upstream_guards: No upstream freshness or receiver-purpose validation.
- coverage:
  - loss: UV-12
  - delay: UV-12
  - duplication: UV-12
  - out-of-order: UV-12
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go:220 ("return cb.counts").
  - commission: n/a: no independent delivery at this boundary, gobreaker.go:220 ("return cb.counts").
  - value: UV-04

### ReadName
- gate: none
- upstream_guards: Name has no uniqueness guarantee. Wrapper delegates at gobreaker.go:249.
- coverage:
  - loss: UV-12
  - delay: UV-12
  - duplication: UV-12
  - out-of-order: UV-12
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go:202 ("return cb.name").
  - commission: n/a: no independent delivery at this boundary, gobreaker.go:202 ("return cb.name").
  - value: UV-04

### RequestResult
- gate: payload error and request execution path
- upstream_guards: A synchronous call returns at most once normally. User function behavior is otherwise unconstrained.
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: n/a: no independent delivery at this boundary, gobreaker.go:242 ("result, err := req()").
  - out-of-order: UV-08
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go:242 ("result, err := req()").
  - commission: UV-10
  - value: UV-11

### Classify
- gate: payload error
- upstream_guards: Configured classifier defaults if nil. No caller-side result or runtime validation.
- coverage:
  - loss: UV-13
  - delay: UV-13
  - duplication: n/a: no independent delivery at this boundary, gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))").
  - out-of-order: UV-14
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))").
  - commission: UV-10
  - value: UV-11

### TripDecision
- gate: payload count snapshot and policy result
- upstream_guards: Default is supplied if nil. Call and commit occur under the same breaker lock.
- coverage:
  - loss: UV-15
  - delay: UV-15
  - duplication: n/a: no independent delivery at this boundary, gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").
  - out-of-order: n/a: no independent delivery at this boundary, gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").
  - commission: UV-10
  - value: UV-11

### Notify
- gate: service callback presence and state change
- upstream_guards: No upstream reentrancy or runtime guarantee. Missing hook is supported.
- coverage:
  - loss: UV-16
  - delay: UV-16
  - duplication: UV-17
  - out-of-order: UV-17
  - contradiction: UV-17
  - commission: UV-17
  - value: UV-17

### ObserveExpiry
- gate: service state and time
- upstream_guards: Clock provides time when invoked. The API exposes no standalone clock-event injection.
- coverage:
  - loss: UV-18
  - delay: UV-18
  - duplication: n/a: no independent delivery at this boundary, gobreaker.go:341 ("if cb.expiry.Before(now) {").
  - out-of-order: UV-18
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go:341 ("if cb.expiry.Before(now) {").
  - commission: n/a: no independent delivery at this boundary, gobreaker.go:341 ("if cb.expiry.Before(now) {").
  - value: UV-18

### ApplySuccess
- gate: service generation, state and threshold
- upstream_guards: Completion source and generation are captured at admission.
- coverage:
  - loss: n/a: no independent delivery at this boundary, gobreaker.go:304 ("cb.onSuccess(state, now)").
  - delay: UV-08
  - duplication: UV-09
  - out-of-order: UV-08
  - contradiction: UV-09
  - commission: UV-10
  - value: UV-11

### ApplyFailure
- gate: service generation and trip policy
- upstream_guards: Completion source and generation are captured at admission.
- coverage:
  - loss: n/a: no independent delivery at this boundary, gobreaker.go:306 ("cb.onFailure(state, now)").
  - delay: UV-08
  - duplication: UV-09
  - out-of-order: UV-08
  - contradiction: UV-09
  - commission: UV-10
  - value: UV-11

### UV-01
- gate: payload execution
- upstream_guards: Request runs in caller goroutine. No context in Execute.

### UV-02
- gate: service generation and admission
- upstream_guards: Direct API supplies no deadline for the workload.

### UV-03
- gate: service admission
- upstream_guards: No caller identity. A completed Execute returns the payload, with no release API.

### UV-04
- gate: receiver and function validity
- upstream_guards: Go types do not enforce instance ownership or construction.

### UV-05
- gate: service admission
- upstream_guards: No context and no teardown operation are supplied.

### UV-06
- gate: service admission
- upstream_guards: No caller identity or lock fairness guarantee.

### UV-07
- gate: service occupancy
- upstream_guards: Public contract expects a report and supplies no cancellation API.

### UV-08
- gate: service generation
- upstream_guards: No public API invalidates a report on application cancellation alone.

### UV-09
- gate: payload Boolean and service generation
- upstream_guards: No public contract specifies an exactly-once guarantee.

### UV-10
- gate: capability presence
- upstream_guards: A non-nil callback must come from successful Allow. A caller can invoke nil in Go.

### UV-11
- gate: payload Boolean or counts
- upstream_guards: Outcome truth is not independently verified.

### UV-12
- gate: service snapshot and expiry
- upstream_guards: Public calls have no snapshot protocol spanning methods.

### UV-13
- gate: payload error and callback runtime
- upstream_guards: No failure or latency guarantee in Settings.

### UV-14
- gate: service generation at completion
- upstream_guards: No reentrancy restriction in Settings.

### UV-15
- gate: service lock and callback execution
- upstream_guards: No failure, latency or reentrancy guarantee in Settings.

### UV-16
- gate: service lock and hook presence
- upstream_guards: Optional hook. No failure, latency or reentrancy guarantee in Settings.

### UV-17
- gate: payload name and state pair
- upstream_guards: No unique identifier or event sequence number.

### UV-18
- gate: service state and clock
- upstream_guards: No caller can deliver clock payload directly.

### UV-20
- gate: receiver identity
- upstream_guards: Creation allocates a fresh instance.

### UV-21
- gate: payload settings
- upstream_guards: Constructor receives values after Go type checking.

