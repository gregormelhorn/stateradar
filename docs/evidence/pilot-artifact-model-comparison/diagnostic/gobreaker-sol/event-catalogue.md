# Event catalogue

<!-- event-ids: Admission StateRead CountsRead NameRead Report Result Classify TripDecision Notify Setup Expiry Complete UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 UV-15 UV-16 UV-17 UV-18 UV-19 UV-20 UV-21 UV-22 UV-23 -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| Admission | external | request caller | Execute or Allow asks permission for one operation. observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"). |
| StateRead | external | state observer | State reads the breaker state. observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)"). |
| CountsRead | external | metrics observer | Counts reads the current counters. observed-in-code gobreaker.go:220 ("return cb.counts"). |
| NameRead | external | identity observer | Name reads the configured name. observed-in-code gobreaker.go:202 ("return cb.name"). |
| Report | external | TwoStep completion owner | Invoke the callback returned by Allow with a Boolean outcome. observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). |
| Result | external | Execute request function | The admitted request returns value and error, or unwinds via panic. observed-in-code gobreaker.go:242 ("result, err := req()"). |
| Classify | external | IsSuccessful callback | Classify the request error before submitting the result. observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). |
| TripDecision | external | ReadyToTrip callback | Policy receives a copy of Counts and returns whether to trip. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). |
| Notify | external | OnStateChange callback | Receive breaker name and previous and next states. observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). |
| Setup | external | lifecycle owner | Construct a breaker with Settings, optionally via the TwoStep constructor. observed-in-code gobreaker.go:141 ("func NewCircuitBreaker(st Settings) *CircuitBreaker {"). |
| Expiry | internal | clock observed at boundary | Evaluate elapsed closed interval or open cooldown on eligible calls. observed-in-code gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). |
| Complete | internal | completion dispatch | Apply outcome after sampling time and checking the admission generation. observed-in-code gobreaker.go:298 ("state, generation := cb.currentState(now)"). |
| UV-01 | external | Admission / request caller | Caller never invokes an acquisition. observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"). |
| UV-02 | external | Admission / request caller | Admission is delayed across a boundary or mutex wait. observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"). |
| UV-03 | external | Admission / request caller | Same caller makes a second admission while the first is pending or while its operation or report callback remains held. Includes simultaneous admissions. observed-in-code gobreaker.go:289 ("cb.counts.onRequest()"). |
| UV-04 | external | Admission / request caller | Call uses the wrong initialized breaker, a nil or zero receiver, or passes a nil Execute function. observed-in-code gobreaker.go:242 ("result, err := req()"). |
| UV-05 | external | StateRead / state observer | Observer omits or delays State, Counts or Name. Also covers time passing without an eligible call. observed-in-code gobreaker.go:210 ("now := time.Now()"). |
| UV-06 | external | StateRead / state observer | Observer reads repeatedly, concurrently, or at the wrong time. Includes Counts and Name. observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). |
| UV-07 | external | Report / TwoStep completion owner | Caller abandons the returned callback or omits a report indefinitely. observed-in-code gobreaker.go:271 ("return func(success bool) {"). |
| UV-08 | external | Report / TwoStep completion owner | Delayed Execute or TwoStep outcome before or after generation change. Includes classification that crosses the boundary. observed-in-code gobreaker.go:299 ("if generation != before {"). |
| UV-09 | external | Report / TwoStep completion owner | Repeat a report with the same outcome in its original generation or after clearing. observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). |
| UV-10 | external | Report / TwoStep completion owner | Concurrent contradictory reports on the same callback. observed-in-code gobreaker.go:303 ("if success {"). |
| UV-11 | external | Report / TwoStep completion owner | Attempt to report with no granted callback, including invoking nil returned on refusal. observed-in-code gobreaker.go:268 ("return nil, err"). |
| UV-12 | external | Report / TwoStep completion owner | Supply a plausible wrong Boolean or invoke another live operation's callback. observed-in-code gobreaker.go:271 ("return func(success bool) {"). |
| UV-13 | external | Result / Execute request function | Request hangs, panics, exits its goroutine, or returns after cancellation by its caller. observed-in-code gobreaker.go:234 ("defer func() {"). |
| UV-14 | external | Result / Execute request function | Request returns a plausible wrong result or error, including typed nil error. observed-in-code gobreaker.go:242 ("result, err := req()"). |
| UV-15 | external | Classify / IsSuccessful callback | IsSuccessful blocks, panics or exits its goroutine. observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). |
| UV-16 | external | Classify / IsSuccessful callback | Concurrent invocations use shared caller policy state or classify a plausible error unexpectedly. observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). |
| UV-17 | external | TripDecision / ReadyToTrip callback | ReadyToTrip blocks, panics, exits its goroutine or reenters a lock-taking method. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). |
| UV-18 | external | Notify / OnStateChange callback | OnStateChange blocks, panics, exits its goroutine or reenters a lock-taking method. observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). |
| UV-19 | external | Notify / OnStateChange callback | Policy or notification crosses an expiry while holding the mutex, or callback reenters by scheduling a separate goroutine. observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). |
| UV-20 | external | Notify / OnStateChange callback | User callback refers to the wrong breaker or returns a surprising policy decision. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). |
| UV-21 | external | Setup / lifecycle owner | Owner omits, delays, repeats, replaces, or abandons construction. Includes calls on the old object after replacement. observed-in-code gobreaker.go:142 ("cb := new(CircuitBreaker)"). |
| UV-22 | external | Setup / lifecycle owner | Use zero or negative durations, very large limits, unintended valid policies or a copied breaker. observed-in-code gobreaker.go:153 ("if st.Interval <= 0 {"). |
| UV-23 | internal | Expiry / clock observed at boundary | Sample before, at, or after deadline, after a long delay, or with a clock anomaly. observed-in-code gobreaker.go:341 ("if cb.expiry.Before(now) {"). |

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| Admission: request caller | UV-01 | UV-02 | UV-03 | UV-02 | UV-03 | UV-04 | UV-04 |
| StateRead: state observer | UV-05 | UV-05 | UV-06 | UV-06 | UV-06 | UV-06 | UV-04 |
| CountsRead: metrics observer | UV-05 | UV-05 | UV-06 | UV-06 | UV-06 | UV-06 | UV-04 |
| NameRead: identity observer | UV-05 | UV-05 | UV-06 | UV-06 | UV-06 | UV-06 | UV-04 |
| Report: TwoStep completion owner | UV-07 | UV-08 | UV-09 | UV-08 | UV-10 | UV-11 | UV-12 |
| Result: Execute request function | UV-13 | UV-13 | n/a: one Go invocation has one ordinary return. gobreaker.go:242 ("result, err := req()") | UV-08 | n/a: one invocation has one ordinary return or panic. gobreaker.go:242 ("result, err := req()") | n/a: execution follows successful admission. gobreaker.go:229 ("generation, err := cb.beforeRequest()") | UV-14 |
| Classify: IsSuccessful callback | UV-15 | UV-15 | n/a: one call per normal return. gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") | UV-08 | UV-16 | n/a: invocation follows normal request return. gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") | UV-16 |
| TripDecision: ReadyToTrip callback | UV-17 | UV-17 | n/a: one call per current closed failure. gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") | UV-19 | UV-17 | n/a: invocation follows current closed failure. gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") | UV-20 |
| Notify: OnStateChange callback | UV-18 | UV-18 | n/a: one synchronous call per setState change. gobreaker.go:358 ("if cb.onStateChange != nil {") | UV-19 | UV-18 | n/a: same-state update returns before hook. gobreaker.go:349 ("if cb.state == state {") | UV-20 |
| Setup: lifecycle owner | UV-21 | UV-21 | UV-21 | UV-21 | UV-21 | UV-21 | UV-22 |
| Expiry: clock observed at boundary | UV-05 | UV-23 | n/a: one check per operation; clearing replaces the deadline. gobreaker.go:338 ("cb.toNewGeneration(now)") | UV-23 | n/a: one stored state selects deadline kind. gobreaker.go:335 ("switch cb.state {") | n/a: evaluation is inline on an eligible operation. gobreaker.go:334 ("func (cb *CircuitBreaker) currentState(now time.Time) (State, uint64) {") | UV-23 |
| Complete: completion dispatch | UV-07 | UV-08 | UV-09 | UV-08 | UV-10 | n/a: private method with causal callers. gobreaker.go:293 ("func (cb *CircuitBreaker) afterRequest(before uint64, success bool) {") | UV-12 |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Admission → StateRead | observer samples recovery before or after admission |
| P-01b | StateRead → Admission | observer samples recovery before or after admission |
| P-02a | Admission → CountsRead | snapshot before or after admission commit |
| P-02b | CountsRead → Admission | snapshot before or after admission commit |
| P-03a | Admission → Report | TwoStep contenders, completion versus next admission |
| P-03b | Report → Admission | TwoStep contenders, completion versus next admission |
| P-04a | Admission → Result | Execute contenders, result versus next admission |
| P-04b | Result → Admission | Execute contenders, result versus next admission |
| P-05a | StateRead → Report | TwoStep observer versus report across deadline |
| P-05b | Report → StateRead | TwoStep observer versus report across deadline |
| P-06a | StateRead → Result | Execute observer versus returned result across deadline |
| P-06b | Result → StateRead | Execute observer versus returned result across deadline |
| P-07a | CountsRead → Report | TwoStep metrics versus report or generation reset |
| P-07b | Report → CountsRead | TwoStep metrics versus report or generation reset |
| P-08a | CountsRead → Result | Execute metrics versus completion |
| P-08b | Result → CountsRead | Execute metrics versus completion |
| P-09a | StateRead → CountsRead | state refresh versus raw counter observation |
| P-09b | CountsRead → StateRead | state refresh versus raw counter observation |
| P-10a | Admission → Classify | Execute contender versus classification delay |
| P-10b | Classify → Admission | Execute contender versus classification delay |
| P-11a | StateRead → Classify | state refresh while classifier is running |
| P-11b | Classify → StateRead | state refresh while classifier is running |
| P-12a | CountsRead → Classify | raw count while classifier is running |
| P-12b | Classify → CountsRead | raw count while classifier is running |
| P-13a | Admission → TripDecision | contender versus locked policy |
| P-13b | TripDecision → Admission | contender versus locked policy |
| P-14a | StateRead → TripDecision | state observation versus locked policy |
| P-14b | TripDecision → StateRead | state observation versus locked policy |
| P-15a | CountsRead → TripDecision | raw snapshot versus locked policy |
| P-15b | TripDecision → CountsRead | raw snapshot versus locked policy |
| P-16a | Admission → Notify | contender versus locked notification |
| P-16b | Notify → Admission | contender versus locked notification |
| P-17a | StateRead → Notify | state observer versus locked notification |
| P-17b | Notify → StateRead | state observer versus locked notification |
| P-18a | CountsRead → Notify | raw snapshot versus locked notification |
| P-18b | Notify → CountsRead | raw snapshot versus locked notification |

## Remembrance semantics

Observed-in-code. Generation and counters are stored per instance gobreaker.go:128 ("generation uint64"). Reset increments generation and clears all counters gobreaker.go:364 ("cb.generation++") gobreaker.go:365 ("cb.counts.clear()"). Admission counts once gobreaker.go:289 ("cb.counts.onRequest()") and reports do not release that admission count gobreaker.go:315 ("cb.counts.onSuccess()"). Old reports compare only generation gobreaker.go:299 ("if generation != before {"). Execute stack and retained Allow callback keep their captured values gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). No per-request history, queue, retention limit for caller-held closures, cancellation or shutdown entry point appears in the public surface gobreaker.go:262 ("// Allow checks if a new request can proceed. It returns a callback that should be used to").

## Lock-discipline annotation

Observed-in-code. State, Counts, admission and completion acquire the same mutex gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:294 ("cb.mutex.Lock()"). ReadyToTrip and OnStateChange are invoked from lock-held paths gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). The Settings docs describe invocation gobreaker.go:95 ("// ReadyToTrip is called with a copy of Counts whenever a request fails in the closed state.") gobreaker.go:100 ("// OnStateChange is called whenever the state of the CircuitBreaker changes.") and give no reentry contract. Execute request and IsSuccessful run between the admission unlock and completion lock gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). Name reads the immutable configured name gobreaker.go:202 ("return cb.name").

## Catalogue notes

Setup belongs to the lifecycle before the active grid. Execute and Allow are alternate entry points on separately constructed public types. Source labels distinguish actors whose work can overlap on one instance. Omission rows describe consequences of absent stimuli.

## Event annotations

### Admission
- gate: service-side state, current time and admitted request count
- upstream_guards: No production caller validation supplied. Allow delegates to the same admission path gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()")
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-02
  - contradiction: UV-03
  - commission: UV-04
  - value: UV-04

### StateRead
- gate: service-side state and time
- upstream_guards: No caller validation supplied gobreaker.go:206 ("func (cb *CircuitBreaker) State() State {")
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-06
  - contradiction: UV-06
  - commission: UV-06
  - value: UV-04

### CountsRead
- gate: service-side snapshot
- upstream_guards: No caller validation supplied gobreaker.go:216 ("func (cb *CircuitBreaker) Counts() Counts {")
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-06
  - contradiction: UV-06
  - commission: UV-06
  - value: UV-04

### NameRead
- gate: service-side immutable setting
- upstream_guards: No caller validation supplied gobreaker.go:201 ("func (cb *CircuitBreaker) Name() string {")
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-06
  - contradiction: UV-06
  - commission: UV-06
  - value: UV-04

### Report
- gate: payload Boolean and service-side generation, state and recovery counts
- upstream_guards: Only successful Allow returns a callback. No once or truth guarantee gobreaker.go:273 ("}, nil")
- coverage:
  - loss: UV-07
  - delay: UV-08
  - duplication: UV-09
  - out-of-order: UV-08
  - contradiction: UV-10
  - commission: UV-11
  - value: UV-12

### Result
- gate: payload outcome and service-side admission generation
- upstream_guards: Execute invokes request only after admission. No guarantee on user code returning gobreaker.go:231 ("return nil, err")
- coverage:
  - loss: UV-13
  - delay: UV-13
  - duplication: n/a: one Go invocation has one ordinary return. gobreaker.go:242 ("result, err := req()")
  - out-of-order: UV-08
  - contradiction: n/a: one invocation has one ordinary return or panic. gobreaker.go:242 ("result, err := req()")
  - commission: n/a: execution follows successful admission. gobreaker.go:229 ("generation, err := cb.beforeRequest()")
  - value: UV-14

### Classify
- gate: payload error and callback outcome
- upstream_guards: Constructor supplies default when nil. User termination and serialization guarantees absent gobreaker.go:171 ("if st.IsSuccessful == nil {")
- coverage:
  - loss: UV-15
  - delay: UV-15
  - duplication: n/a: one call per normal return. gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))")
  - out-of-order: UV-08
  - contradiction: UV-16
  - commission: n/a: invocation follows normal request return. gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))")
  - value: UV-16

### TripDecision
- gate: payload Counts and policy Boolean
- upstream_guards: Constructor supplies default when nil. User termination guarantee absent gobreaker.go:165 ("if st.ReadyToTrip == nil {")
- coverage:
  - loss: UV-17
  - delay: UV-17
  - duplication: n/a: one call per current closed failure. gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {")
  - out-of-order: UV-19
  - contradiction: UV-17
  - commission: n/a: invocation follows current closed failure. gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {")
  - value: UV-20

### Notify
- gate: service-side state change and callback presence
- upstream_guards: Constructor copies hook. User termination and reentry guarantees absent gobreaker.go:145 ("cb.onStateChange = st.OnStateChange")
- coverage:
  - loss: UV-18
  - delay: UV-18
  - duplication: n/a: one synchronous call per setState change. gobreaker.go:358 ("if cb.onStateChange != nil {")
  - out-of-order: UV-19
  - contradiction: UV-18
  - commission: n/a: same-state update returns before hook. gobreaker.go:349 ("if cb.state == state {")
  - value: UV-20

### Setup
- gate: payload configuration
- upstream_guards: Zero and negative duration handling in constructor. No caller validation supplied gobreaker.go:153 ("if st.Interval <= 0 {")
- coverage:
  - loss: UV-21
  - delay: UV-21
  - duplication: UV-21
  - out-of-order: UV-21
  - contradiction: UV-21
  - commission: UV-21
  - value: UV-22

### Expiry
- gate: service-side deadline and sampled time
- upstream_guards: Clock sampled from time.Now under mutex for State, admission, and completion gobreaker.go:297 ("now := time.Now()")
- coverage:
  - loss: UV-05
  - delay: UV-23
  - duplication: n/a: one check per operation; clearing replaces the deadline. gobreaker.go:338 ("cb.toNewGeneration(now)")
  - out-of-order: UV-23
  - contradiction: n/a: one stored state selects deadline kind. gobreaker.go:335 ("switch cb.state {")
  - commission: n/a: evaluation is inline on an eligible operation. gobreaker.go:334 ("func (cb *CircuitBreaker) currentState(now time.Time) (State, uint64) {")
  - value: UV-23

### Complete
- gate: payload success and service-side generation and state
- upstream_guards: Private dispatch from Execute or Allow only gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))")
- coverage:
  - loss: UV-07
  - delay: UV-08
  - duplication: UV-09
  - out-of-order: UV-08
  - contradiction: UV-10
  - commission: n/a: private method with causal callers. gobreaker.go:293 ("func (cb *CircuitBreaker) afterRequest(before uint64, success bool) {")
  - value: UV-12

### UV-01
- gate: service-side state, current time and admitted request count
- upstream_guards: No production caller validation supplied. Allow delegates to the same admission path gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()")

### UV-02
- gate: service-side state, current time and admitted request count
- upstream_guards: No production caller validation supplied. Allow delegates to the same admission path gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()")

### UV-03
- gate: service-side state, current time and admitted request count
- upstream_guards: No production caller validation supplied. Allow delegates to the same admission path gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()")

### UV-04
- gate: service-side state, current time and admitted request count
- upstream_guards: No production caller validation supplied. Allow delegates to the same admission path gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()")

### UV-05
- gate: service-side state and time
- upstream_guards: No caller validation supplied gobreaker.go:206 ("func (cb *CircuitBreaker) State() State {")

### UV-06
- gate: service-side state and time
- upstream_guards: No caller validation supplied gobreaker.go:206 ("func (cb *CircuitBreaker) State() State {")

### UV-07
- gate: payload Boolean and service-side generation, state and recovery counts
- upstream_guards: Only successful Allow returns a callback. No once or truth guarantee gobreaker.go:273 ("}, nil")

### UV-08
- gate: payload Boolean and service-side generation, state and recovery counts
- upstream_guards: Only successful Allow returns a callback. No once or truth guarantee gobreaker.go:273 ("}, nil")

### UV-09
- gate: payload Boolean and service-side generation, state and recovery counts
- upstream_guards: Only successful Allow returns a callback. No once or truth guarantee gobreaker.go:273 ("}, nil")

### UV-10
- gate: payload Boolean and service-side generation, state and recovery counts
- upstream_guards: Only successful Allow returns a callback. No once or truth guarantee gobreaker.go:273 ("}, nil")

### UV-11
- gate: payload Boolean and service-side generation, state and recovery counts
- upstream_guards: Only successful Allow returns a callback. No once or truth guarantee gobreaker.go:273 ("}, nil")

### UV-12
- gate: payload Boolean and service-side generation, state and recovery counts
- upstream_guards: Only successful Allow returns a callback. No once or truth guarantee gobreaker.go:273 ("}, nil")

### UV-13
- gate: payload outcome and service-side admission generation
- upstream_guards: Execute invokes request only after admission. No guarantee on user code returning gobreaker.go:231 ("return nil, err")

### UV-14
- gate: payload outcome and service-side admission generation
- upstream_guards: Execute invokes request only after admission. No guarantee on user code returning gobreaker.go:231 ("return nil, err")

### UV-15
- gate: payload error and callback outcome
- upstream_guards: Constructor supplies default when nil. User termination and serialization guarantees absent gobreaker.go:171 ("if st.IsSuccessful == nil {")

### UV-16
- gate: payload error and callback outcome
- upstream_guards: Constructor supplies default when nil. User termination and serialization guarantees absent gobreaker.go:171 ("if st.IsSuccessful == nil {")

### UV-17
- gate: payload Counts and policy Boolean
- upstream_guards: Constructor supplies default when nil. User termination guarantee absent gobreaker.go:165 ("if st.ReadyToTrip == nil {")

### UV-18
- gate: service-side state change and callback presence
- upstream_guards: Constructor copies hook. User termination and reentry guarantees absent gobreaker.go:145 ("cb.onStateChange = st.OnStateChange")

### UV-19
- gate: service-side state change and callback presence
- upstream_guards: Constructor copies hook. User termination and reentry guarantees absent gobreaker.go:145 ("cb.onStateChange = st.OnStateChange")

### UV-20
- gate: service-side state change and callback presence
- upstream_guards: Constructor copies hook. User termination and reentry guarantees absent gobreaker.go:145 ("cb.onStateChange = st.OnStateChange")

### UV-21
- gate: payload configuration
- upstream_guards: Zero and negative duration handling in constructor. No caller validation supplied gobreaker.go:153 ("if st.Interval <= 0 {")

### UV-22
- gate: payload configuration
- upstream_guards: Zero and negative duration handling in constructor. No caller validation supplied gobreaker.go:153 ("if st.Interval <= 0 {")

### UV-23
- gate: service-side deadline and sampled time
- upstream_guards: Clock sampled from time.Now under mutex for State, admission, and completion gobreaker.go:297 ("now := time.Now()")
