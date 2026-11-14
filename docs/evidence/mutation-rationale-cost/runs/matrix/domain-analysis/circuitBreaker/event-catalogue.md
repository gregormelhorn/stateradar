# Event catalogue

<!-- event-ids: Execute Allow StateRead CountsRead NameRead Report RequestReturn Classify TripPolicy Notify ReconcileTime UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 UV-15 UV-16 UV-17 UV-18 UV-19 -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| Execute | external | request caller | Execute call carrying a request function. observed-in-code gobreaker.go:228 ("func (cb *CircuitBreaker) Execute(req func() (interface{}, error)) (interface{}, error) {"). |
| Allow | external | request caller | Two-step admission request and resulting completion callback seam. observed-in-code gobreaker.go:265 ("func (tscb *TwoStepCircuitBreaker) Allow() (done func(success bool), err error) {"). |
| StateRead | external | observer | Read state through either public API. observed-in-code gobreaker.go:206 ("func (cb *CircuitBreaker) State() State {"). |
| CountsRead | external | observer | Read counters by value through either public API. observed-in-code gobreaker.go:216 ("func (cb *CircuitBreaker) Counts() Counts {"). |
| NameRead | external | observer | Read configured name through either public API. observed-in-code gobreaker.go:201 ("func (cb *CircuitBreaker) Name() string {"). |
| Report | external | completion reporter | Invoke the returned callback with a success boolean. observed-in-code gobreaker.go:271 ("return func(success bool) {"). |
| RequestReturn | external | injected request function | Return a value and error or panic. observed-in-code gobreaker.go:242 ("result, err := req()"). |
| Classify | external | injected classifier | Return success boolean from the request error. observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). |
| TripPolicy | external | injected trip policy | Return trip boolean after a closed-state failure. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). |
| Notify | external | injected state-change callback | Receive name, previous and next state, then return. observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). |
| ReconcileTime | internal | runtime clock observation | Reconcile elapsed time within admission, completion or State. observed-in-code gobreaker.go:334 ("func (cb *CircuitBreaker) currentState(now time.Time) (State, uint64) {"). |
| UV-01 | external | request caller | Omit requested work or cease calling the breaker. observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"). |
| UV-02 | external | request caller | Delay first or subsequent admission across the configured time threshold. observed-in-code gobreaker.go:280 ("now := time.Now()"). |
| UV-03 | external | request caller | Repeat acquisition from the same caller while Execute is pending or while a returned Allow callback remains outstanding. observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). |
| UV-04 | external | request caller | Deliver admission after withdrawal of demand or replacement of the intended breaker. observed-in-code gobreaker.go:276 ("func (cb *CircuitBreaker) beforeRequest() (uint64, error) {"). |
| UV-05 | external | request caller | Concurrent competing acquisitions near the half-open budget boundary. observed-in-code gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). |
| UV-06 | external | request caller | Unsolicited acquisition without matching business demand. observed-in-code gobreaker.go:289 ("cb.counts.onRequest()"). |
| UV-07 | external | request caller or observer | Use a wrong receiver, an invalid zero-value receiver, or unexpected valid constructor settings. Separately, supply a nil Execute function. observed-in-code gobreaker.go:142 ("cb := new(CircuitBreaker)"). |
| UV-08 | external | observer | Omit or delay reads, poll repeatedly, sample near a transition, make concurrent observations, or read without a monitoring trigger. observed-in-code gobreaker.go:210 ("now := time.Now()"). |
| UV-09 | external | completion reporter | Omit a report through abandonment, cancellation, or losing the returned callback. observed-in-code gobreaker.go:262 ("// Allow checks if a new request can proceed. It returns a callback that should be used to"). |
| UV-10 | external | completion reporter or request producer | Deliver late success or failure after interval reset, open expiry, or another generation change. observed-in-code gobreaker.go:299 ("if generation != before {"). |
| UV-11 | external | completion reporter | Repeat the same success or failure on one returned callback. observed-in-code gobreaker.go:271 ("return func(success bool) {"). |
| UV-12 | external | completion reporter | Report success and failure on the same callback concurrently. observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). |
| UV-13 | external | completion or policy callbacks | Invoke a callback manually without its normal trigger or replay a callback-shaped operation. observed-in-code gobreaker.go:271 ("return func(success bool) {"). |
| UV-14 | external | completion or policy callbacks | Supply a plausible wrong classification, a report for another request, or transfer a completion across owners. observed-in-code gobreaker.go:303 ("if success {"). |
| UV-15 | external | injected request function | Block, never return, exit the goroutine, or return only after caller demand ends. observed-in-code gobreaker.go:242 ("result, err := req()"). |
| UV-16 | external | injected request function or classifier | Panic, stall, reenter, or produce no ordinary classifier return. observed-in-code gobreaker.go:234 ("defer func() {"). |
| UV-17 | external | injected trip or notification callback | Panic, stall indefinitely, or call synchronously back into a locking breaker method. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). |
| UV-18 | external | injected notification callback | Perform an unexpected or partially completed downstream side effect during notification. observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). |
| UV-19 | internal | runtime clock observation | Omit observation, sample exactly at expiry or after many intervals, or observe the same expiry from several callers. observed-in-code gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). |

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| Execute: request caller | UV-01 | UV-02 | UV-03 | UV-04 | UV-05 | UV-06 | UV-07 |
| Allow: request caller | UV-01 | UV-02 | UV-03 | UV-04 | UV-05 | UV-06 | UV-07 |
| StateRead: observer | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-07 |
| CountsRead: observer | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-07 |
| NameRead: observer | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-07 |
| Report: completion reporter | UV-09 | UV-10 | UV-11 | UV-10 | UV-12 | UV-13 | UV-14 |
| RequestReturn: injected request function | UV-15 | UV-15 | UV-13 | UV-10 | UV-15 | UV-16 | UV-14 |
| Classify: injected classifier | UV-16 | UV-16 | UV-13 | UV-10 | UV-14 | UV-16 | UV-14 |
| TripPolicy: injected trip policy | UV-17 | UV-17 | UV-13 | UV-13 | UV-14 | UV-17 | UV-14 |
| Notify: injected state-change callback | UV-17 | UV-17 | UV-13 | UV-13 | UV-18 | UV-17 | UV-18 |
| ReconcileTime: runtime clock observation | UV-19 | UV-19 | UV-19 | UV-19 | UV-19 | UV-19 | UV-19 |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Execute → Report | Admission and a previously issued report |
| P-01b | Report → Execute | Admission and a previously issued report |
| P-02a | Allow → Report | New admission and a previously issued report |
| P-02b | Report → Allow | New admission and a previously issued report |
| P-03a | StateRead → Report | Observer and pending report |
| P-03b | Report → StateRead | Observer and pending report |
| P-04a | CountsRead → Report | Snapshot and completion reporter |
| P-04b | Report → CountsRead | Snapshot and completion reporter |
| P-05a | StateRead → Execute | Observer and request caller at expiry |
| P-05b | Execute → StateRead | Observer and request caller at expiry |
| P-06a | StateRead → Allow | Observer and two-step caller at expiry |
| P-06b | Allow → StateRead | Observer and two-step caller at expiry |
| P-07a | Execute → RequestReturn | New caller and running request |
| P-07b | RequestReturn → Execute | New caller and running request |
| P-08a | StateRead → RequestReturn | Observer and running request |
| P-08b | RequestReturn → StateRead | Observer and running request |
| P-09a | CountsRead → RequestReturn | Snapshot and running request |
| P-09b | RequestReturn → CountsRead | Snapshot and running request |
| P-10a | Classify → Notify | Classifier and notification for different admitted calls |
| P-10b | Notify → Classify | Classifier and notification for different admitted calls |
| P-11a | Execute → Classify | New caller and classifier of an admitted request |
| P-11b | Classify → Execute | New caller and classifier of an admitted request |
| P-12a | CountsRead → Classify | Snapshot and classifier of an admitted request |
| P-12b | Classify → CountsRead | Snapshot and classifier of an admitted request |
| P-13a | StateRead → Classify | Observer and classifier across an expiry |
| P-13b | Classify → StateRead | Observer and classifier across an expiry |
| P-14a | StateRead → Notify | Observer and transition notification |
| P-14b | Notify → StateRead | Observer and transition notification |
| P-15a | Execute → TripPolicy | Other caller and in-progress failure policy |
| P-15b | TripPolicy → Execute | Other caller and in-progress failure policy |
| P-16a | Allow → Notify | New caller and transition notification |
| P-16b | Notify → Allow | New caller and transition notification |
| P-17a | NameRead → Notify | Unchanging name and notification |
| P-17b | Notify → NameRead | Unchanging name and notification |
| P-18a | CountsRead → Execute | Snapshot and new request |
| P-18b | Execute → CountsRead | Snapshot and new request |
| P-19a | CountsRead → Allow | Snapshot and two-step admission |
| P-19b | Allow → CountsRead | Snapshot and two-step admission |
| P-20a | CountsRead → Notify | Snapshot and transition notification |
| P-20b | Notify → CountsRead | Snapshot and transition notification |
| P-21a | StateRead → TripPolicy | Observer and failure policy |
| P-21b | TripPolicy → StateRead | Observer and failure policy |
| P-22a | CountsRead → TripPolicy | Snapshot and failure policy |
| P-22b | TripPolicy → CountsRead | Snapshot and failure policy |
| P-23a | Execute → Notify | New caller and transition notification |
| P-23b | Notify → Execute | New caller and transition notification |
| P-24a | Report → Notify | Competing reports and a transition notification |
| P-24b | Notify → Report | Competing reports and a transition notification |
| P-25a | RequestReturn → Notify | An in-flight request returns during notification |
| P-25b | Notify → RequestReturn | An in-flight request returns during notification |
| P-26a | Classify → TripPolicy | Classification and trip policy for different requests |
| P-26b | TripPolicy → Classify | Classification and trip policy for different requests |
| P-27a | RequestReturn → TripPolicy | In-flight work returns during failure policy |
| P-27b | TripPolicy → RequestReturn | In-flight work returns during failure policy |
| P-28a | Report → TripPolicy | Another report competes with a trip policy |
| P-28b | TripPolicy → Report | Another report competes with a trip policy |

## Remembrance semantics

An outcome carries the generation captured at admission. observed-in-code gobreaker.go:271 ("return func(success bool) {"). A generation advance clears the five counters. observed-in-code gobreaker.go:364 ("cb.generation++"). observed-in-code gobreaker.go:365 ("cb.counts.clear()"). No per-request registry or queue is present. observed-in-code gobreaker.go:128 ("generation uint64"). A retained completion references its wrapper and generation, and the generation comparison happens after checking time. observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). observed-in-code gobreaker.go:298 ("state, generation := cb.currentState(now)"). observed-in-code gobreaker.go:299 ("if generation != before {"). Requests measures admitted requests in the current generation, with no per-report decrement. observed-in-code gobreaker.go:56 ("c.Requests++"). Counter wrap and captured-reference lifetime require separate decisions. Every enum state change advances the generation. observed-in-code gobreaker.go:356 ("cb.toNewGeneration(now)").

## Lock-discipline annotation

State, Counts, admission and accounting each acquire the same mutex. observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"). observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"). ReadyToTrip and OnStateChange are synchronous calls on locked paths. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Execute calls the request and IsSuccessful between the admission and accounting lock sections. observed-in-code gobreaker.go:242 ("result, err := req()"). observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). Name reads the immutable configured name without acquiring the mutex. observed-in-code gobreaker.go:202 ("return cb.name"). Callback-specific reentrancy and failure guarantees are absent from the contract.

## Catalogue notes

Request work, cancellation and downstream cleanup are owned by callers. There is no library shutdown API. Execute and Allow share an admission routine but are exposed through different constructed API forms.

## Event annotations

### Execute
- gate: admission state and count; function supplied by caller
- upstream_guards: General library has no caller validation. HTTP example constructs one breaker and checks Execute error at example/http_breaker.go:41 ("if err != nil {").
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-04
  - contradiction: UV-05
  - commission: UV-06
  - value: UV-07

### Allow
- gate: admission state and count
- upstream_guards: The HTTP example uses Execute only. Wrapper callers must check Allow error before invoking the returned function, per the Allow contract.
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-04
  - contradiction: UV-05
  - commission: UV-06
  - value: UV-07

### StateRead
- gate: state and expiry
- upstream_guards: Wrapper forwards the selected receiver. No validation of intended identity. observed-in-code gobreaker.go:254 ("return tscb.cb.State()").
- coverage:
  - loss: UV-08
  - delay: UV-08
  - duplication: UV-08
  - out-of-order: UV-08
  - contradiction: UV-08
  - commission: UV-08
  - value: UV-07

### CountsRead
- gate: mutex acquisition and stored counts
- upstream_guards: Wrapper forwards the selected receiver. No validation of intended identity. observed-in-code gobreaker.go:254 ("return tscb.cb.State()").
- coverage:
  - loss: UV-08
  - delay: UV-08
  - duplication: UV-08
  - out-of-order: UV-08
  - contradiction: UV-08
  - commission: UV-08
  - value: UV-07

### NameRead
- gate: immutable setting
- upstream_guards: Wrapper forwards the selected receiver. No validation of intended identity. observed-in-code gobreaker.go:254 ("return tscb.cb.State()").
- coverage:
  - loss: UV-08
  - delay: UV-08
  - duplication: UV-08
  - out-of-order: UV-08
  - contradiction: UV-08
  - commission: UV-08
  - value: UV-07

### Report
- gate: captured generation and receiver, current state, outcome payload
- upstream_guards: Successful Allow is needed to obtain the function. No once-only or caller-identity guarantee. observed-in-code gobreaker.go:267 ("if err != nil {").
- coverage:
  - loss: UV-09
  - delay: UV-10
  - duplication: UV-11
  - out-of-order: UV-10
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### RequestReturn
- gate: generation at accounting and classifier result for normal return
- upstream_guards: Custom implementation governs failure and liveness. No callback contract guarantees prompt return. observed-in-code gobreaker.go:242 ("result, err := req()").
- coverage:
  - loss: UV-15
  - delay: UV-15
  - duplication: UV-13
  - out-of-order: UV-10
  - contradiction: UV-15
  - commission: UV-16
  - value: UV-14

### Classify
- gate: payload and policy function
- upstream_guards: Custom implementation governs failure and liveness. No callback contract guarantees prompt return. observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))").
- coverage:
  - loss: UV-16
  - delay: UV-16
  - duplication: UV-13
  - out-of-order: UV-10
  - contradiction: UV-14
  - commission: UV-16
  - value: UV-14

### TripPolicy
- gate: current generation and Counts snapshot
- upstream_guards: Custom implementation governs failure and liveness. No callback contract guarantees prompt return. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").
- coverage:
  - loss: UV-17
  - delay: UV-17
  - duplication: UV-13
  - out-of-order: UV-13
  - contradiction: UV-14
  - commission: UV-17
  - value: UV-14

### Notify
- gate: state change and callback presence
- upstream_guards: Custom implementation governs failure and liveness. No callback contract guarantees prompt return. observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").
- coverage:
  - loss: UV-17
  - delay: UV-17
  - duplication: UV-13
  - out-of-order: UV-13
  - contradiction: UV-18
  - commission: UV-17
  - value: UV-18

### ReconcileTime
- gate: service-side stored state, expiry and sampled time
- upstream_guards: Synchronous time sample during a locked operation. observed-in-code gobreaker.go:280 ("now := time.Now()").
- coverage:
  - loss: UV-19
  - delay: UV-19
  - duplication: UV-19
  - out-of-order: UV-19
  - contradiction: UV-19
  - commission: UV-19
  - value: UV-19

### UV-01
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: General library has no caller validation. HTTP example constructs one breaker and checks Execute error at example/http_breaker.go:41 ("if err != nil {").

### UV-02
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: General library has no caller validation. HTTP example constructs one breaker and checks Execute error at example/http_breaker.go:41 ("if err != nil {").

### UV-03
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: General library has no caller validation. HTTP example constructs one breaker and checks Execute error at example/http_breaker.go:41 ("if err != nil {").

### UV-04
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: General library has no caller validation. HTTP example constructs one breaker and checks Execute error at example/http_breaker.go:41 ("if err != nil {").

### UV-05
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: General library has no caller validation. HTTP example constructs one breaker and checks Execute error at example/http_breaker.go:41 ("if err != nil {").

### UV-06
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: General library has no caller validation. HTTP example constructs one breaker and checks Execute error at example/http_breaker.go:41 ("if err != nil {").

### UV-07
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: Custom implementation governs failure and liveness. No callback contract guarantees prompt return. observed-in-code gobreaker.go:142 ("cb := new(CircuitBreaker)").

### UV-08
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: Wrapper forwards the selected receiver. No validation of intended identity. observed-in-code gobreaker.go:254 ("return tscb.cb.State()").

### UV-09
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: Successful Allow is needed to obtain the function. No once-only or caller-identity guarantee. observed-in-code gobreaker.go:267 ("if err != nil {").

### UV-10
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: Custom implementation governs failure and liveness. No callback contract guarantees prompt return. observed-in-code gobreaker.go:299 ("if generation != before {").

### UV-11
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: Successful Allow is needed to obtain the function. No once-only or caller-identity guarantee. observed-in-code gobreaker.go:267 ("if err != nil {").

### UV-12
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: Successful Allow is needed to obtain the function. No once-only or caller-identity guarantee. observed-in-code gobreaker.go:267 ("if err != nil {").

### UV-13
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: Custom implementation governs failure and liveness. No callback contract guarantees prompt return. observed-in-code gobreaker.go:271 ("return func(success bool) {").

### UV-14
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: Custom implementation governs failure and liveness. No callback contract guarantees prompt return. observed-in-code gobreaker.go:303 ("if success {").

### UV-15
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: Custom implementation governs failure and liveness. No callback contract guarantees prompt return. observed-in-code gobreaker.go:242 ("result, err := req()").

### UV-16
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: Custom implementation governs failure and liveness. No callback contract guarantees prompt return. observed-in-code gobreaker.go:234 ("defer func() {").

### UV-17
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: Custom implementation governs failure and liveness. No callback contract guarantees prompt return. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").

### UV-18
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: Custom implementation governs failure and liveness. No callback contract guarantees prompt return. observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

### UV-19
- gate: Original operation gate; variant carries the timing, receiver or outcome described
- upstream_guards: Synchronous time sample during a locked operation. observed-in-code gobreaker.go:280 ("now := time.Now()").

