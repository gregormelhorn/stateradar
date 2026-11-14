# Open domain questions

## Q-01

**Fault:** F-11

**Trigger:** step-3 lock-discipline annotation

**Question:** May OnStateChange read or operate on the same breaker, and when must notification finish?

**Current behaviour:** Observed-in-code unless qualified. Transition and generation commit before synchronous notification. A same-goroutine State or Counts call waits on the mutex already held. Other lock-taking calls wait too. gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:354 ("cb.state = state") gobreaker.go:356 ("cb.toNewGeneration(now)") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Document restrictions and blocking / allow reentry with a specified ordering.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-02

**Fault:** F-11

**Trigger:** step-3 lock-discipline annotation

**Question:** May ReadyToTrip query or operate on the same breaker?

**Current behaviour:** Observed-in-code unless qualified. Policy runs with the mutex held after failure counts change. Same-goroutine lock-taking reentry blocks. Name alone does not take the lock. gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").

**Options:** Document a non-reentrant policy contract / permit reentry with a defined snapshot.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-03

**Fault:** F-07

**Trigger:** step-5 lint

**Question:** What releases HalfOpen capacity when an admitted request never finishes or an Allow callback is abandoned?

**Current behaviour:** Observed-in-code unless qualified. Admissions consume the generation limit. HalfOpen has no expiry. At capacity, later calls are refused indefinitely until enough successes or one failure is reported. An outstanding closure can still report later. gobreaker.go:271 ("return func(success bool) {") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:315 ("cb.counts.onSuccess()") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {") gobreaker.go:378 ("cb.expiry = zero").

**Options:** Require every caller to report / define timeout or cancellation / define explicit abandonment.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-04

**Fault:** F-14

**Trigger:** step-3 checklist

**Question:** What is the report cardinality and conflicting report policy for each successful Allow?

**Current behaviour:** Observed-in-code unless qualified. Same-generation reports all reach accounting. Duplicate successes can close HalfOpen without that many distinct successful requests. Conflicting reports commit in lock order until a generation change makes the remaining report stale. gobreaker.go:271 ("return func(success bool) {") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:299 ("if generation != before {") gobreaker.go:303 ("if success {") gobreaker.go:315 ("cb.counts.onSuccess()") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {").

**Options:** Require exactly one report / ignore duplicates / reject duplicate or contradictory reports.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-05

**Fault:** F-13

**Trigger:** doctrine mapping

**Question:** When must Open cooldown and Closed interval take effect, including an exact deadline, idle periods and Counts reads?

**Current behaviour:** Observed-in-code unless qualified. State/admission/completion refresh strictly after deadline. Name and Counts do not refresh. Closed resets once and re-anchors to the triggering sample. No scheduled callback fires while idle. gobreaker.go:210 ("now := time.Now()") gobreaker.go:220 ("return cb.counts") gobreaker.go:280 ("now := time.Now()") gobreaker.go:297 ("now := time.Now()") gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") gobreaker.go:341 ("if cb.expiry.Before(now) {") gobreaker.go:373 ("cb.expiry = now.Add(cb.interval)") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").

**Options:** Specify lazy refresh and exact comparison / define autonomous expiry / align Counts with State.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-06

**Fault:** F-15

**Trigger:** adversarial trace

**Question:** Can a stale completion advance expiry, and should a current failure delayed across a reset invoke ReadyToTrip?

**Current behaviour:** Observed-in-code unless qualified. Completion samples and refreshes before generation filtering. A stale completion can open recovery and notify, or clear a Closed interval, while its own outcome is discarded. IsSuccessful runs before filtering. gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:297 ("now := time.Now()") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:341 ("if cb.expiry.Before(now) {").

**Options:** Document refresh and classification effects / isolate stale completion effects.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-07

**Fault:** F-13

**Trigger:** step-5 lint

**Question:** What does instant rejection mean under lock contention and callback delays?

**Current behaviour:** Observed-in-code unless qualified. Refusal bypasses the request function. The admission lock can delay both decision and return. Time is sampled after lock acquisition, so the decision can differ from one made at call entry. gobreaker.go:229 ("generation, err := cb.beforeRequest()") gobreaker.go:231 ("return nil, err") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:280 ("now := time.Now()") gobreaker.go:284 ("return generation, ErrOpenState") gobreaker.go:286 ("return generation, ErrTooManyRequests") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Define rejection after serialized decision / define a latency or fail-fast contract.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-08

**Fault:** F-03

**Trigger:** seam-contract sweep

**Question:** How should a ReadyToTrip panic or goroutine exit affect failure counting, trip decision and caller outcome?

**Current behaviour:** Observed-in-code unless qualified. Failure count commits before policy. Panic during ordinary Execute accounting reaches the recovery defer and can record a second failure if the generation still matches. TwoStep has no recovery wrapper. Goexit runs unlock but skips the ordinary result. gobreaker.go:234 ("defer func() {") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:295 ("defer cb.mutex.Unlock()") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:327 ("cb.setState(StateOpen, now)").

**Options:** Specify callback obligations / contain failure / surface a distinct failure.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-09

**Fault:** F-03

**Trigger:** seam-contract sweep

**Question:** What must survive an OnStateChange panic or goroutine exit?

**Current behaviour:** Observed-in-code unless qualified. State and reset commit before notification. A panic from admission notification occurs before Execute installs its recovery defer and can prevent the triggering request from being admitted. A notification panic during request-panic accounting can replace the original panic. gobreaker.go:229 ("generation, err := cb.beforeRequest()") gobreaker.go:234 ("defer func() {") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:238 ("panic(e)") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:354 ("cb.state = state") gobreaker.go:356 ("cb.toNewGeneration(now)") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Specify propagation and state commitment / isolate notification failure.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-10

**Fault:** F-03

**Trigger:** seam-contract sweep

**Question:** How should classifier panic, blocking, Goexit and reentry affect the original result and accounting?

**Current behaviour:** Observed-in-code unless qualified. Classifier is outside the breaker lock. Panic goes through the Execute defer as failure; blocking or Goexit can prevent completion. It can be invoked concurrently and can reenter; its result can become stale. gobreaker.go:234 ("defer func() {") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:244 ("return result, err") gobreaker.go:294 ("cb.mutex.Lock()").

**Options:** Define classifier obligations and concurrency / define a fallback.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-11

**Fault:** F-09

**Trigger:** step-5 lint

**Question:** What should Execute do when the caller leaves, the request stalls or calls Goexit?

**Current behaviour:** Observed-in-code unless qualified. Execute holds no cancellation handle. Stalled work retains an admission; caller-managed cancellation only counts if it eventually produces a reportable return. Goexit runs the defer with nil recover and no outcome. gobreaker.go:234 ("defer func() {") gobreaker.go:235 ("e := recover()") gobreaker.go:236 ("if e != nil {") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))").

**Options:** Specify caller ownership and release obligation / add a defined cancellation policy.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-12

**Fault:** F-18

**Trigger:** step-3 checklist

**Question:** What validates a wrong breaker, wrong closure, or plausible wrong result?

**Current behaviour:** Observed-in-code unless qualified. A valid receiver uses its own state and a report closure uses its captured wrapper/generation. Boolean outcomes are trusted and returned Execute values pass through. Wrong receiver and wrong payload have distinct effects. gobreaker.go:202 ("return cb.name") gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:271 ("return func(success bool) {") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:299 ("if generation != before {").

**Options:** Document caller identity responsibility / validate operation identity where available.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-13

**Fault:** F-17

**Trigger:** step-3 checklist

**Question:** What should happen on nil or zero receiver, nil request or calling a nil report after refusal?

**Current behaviour:** Observed-in-code unless qualified. No validation guards these calls. A rejected Execute never invokes its nil request; an admitted nil request panics after admission. A zero breaker may admit then panic on nil policy/classifier. Rejected Allow returns nil, whose direct invocation panics in the caller. gobreaker.go:171 ("if st.IsSuccessful == nil {") gobreaker.go:202 ("return cb.name") gobreaker.go:231 ("return nil, err") gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:268 ("return nil, err").

**Options:** Require initialized receiver and nonnil callable / define defensive outcomes.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-14

**Fault:** F-10

**Trigger:** multi-instance probes

**Question:** Should similarly configured breakers disperse recovery and closed-window reset load on a shared backend?

**Current behaviour:** Observed-in-code unless qualified. Deadline is local transition sample plus fixed settings. Independent actors may align, under correlated demand and failures. Aggregate effect is deployment-dependent. gobreaker.go:190 ("const defaultTimeout = time.Duration(60) * time.Second") gobreaker.go:341 ("if cb.expiry.Before(now) {") gobreaker.go:373 ("cb.expiry = now.Add(cb.interval)") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").

**Options:** Keep recovery local / specify jitter or shared recovery limits.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-15

**Fault:** F-05

**Trigger:** step-5 lint

**Question:** What supported bounds apply to counters, generation age and extreme configuration?

**Current behaviour:** Observed-in-code unless qualified. Counters are uint32, generation uint64 and settings include arbitrary positive representable durations. No saturation or rollover guard is present. Runtime relevance depends on traffic and retention. gobreaker.go:48 ("Requests             uint32") gobreaker.go:56 ("c.Requests++") gobreaker.go:61 ("c.ConsecutiveSuccesses++") gobreaker.go:67 ("c.ConsecutiveFailures++") gobreaker.go:128 ("generation uint64") gobreaker.go:150 ("cb.maxRequests = st.MaxRequests") gobreaker.go:156 ("cb.interval = st.Interval") gobreaker.go:162 ("cb.timeout = st.Timeout") gobreaker.go:364 ("cb.generation++").

**Options:** Document supported limits / define rollover and saturation semantics.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-16

**Fault:** F-07

**Trigger:** step-3 checklist

**Question:** Does replacing or abandoning an instance invalidate outstanding work and callbacks?

**Current behaviour:** Observed-in-code unless qualified. Construction returns a distinct object. Existing work and closure reports keep the original instance; no teardown or cancellation entry point is exposed. gobreaker.go:142 ("cb := new(CircuitBreaker)") gobreaker.go:184 ("return &TwoStepCircuitBreaker{") gobreaker.go:242 ("result, err := req()") gobreaker.go:271 ("return func(success bool) {") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)").

**Options:** Document independent lifetimes / define retirement and late report policy.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-17

**Fault:** F-01

**Trigger:** step-1 extraction

**Question:** What are the public startup and HalfOpen exit guarantees, and what population should policy counts describe?

**Current behaviour:** Observed-in-code unless qualified. Construction starts Closed. HalfOpen uses admission count and success streak, reopens on first current failure without ReadyToTrip. Closed policy sees the current failure plus admissions that may still be pending. gobreaker.go:142 ("cb := new(CircuitBreaker)") gobreaker.go:177 ("cb.toNewGeneration(time.Now())") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:315 ("cb.counts.onSuccess()") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:330 ("cb.setState(StateOpen, now)").

**Options:** Document current policy and counter population / define distinct completion requirements.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-18

**Fault:** F-15

**Trigger:** adversarial trace

**Question:** What ordering or fairness can concurrent callers and observers rely on?

**Current behaviour:** Observed-in-code unless qualified. Admission and completion are separate mutex acquisitions. A later admission may finish first; Counts can show admitted work before outcome or show a prior generation until State refreshes. No caller identity or breaker-owned wait queue. gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:278 ("defer cb.mutex.Unlock()") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:298 ("state, generation := cb.currentState(now)").

**Options:** Document commit order only / specify fairness or coordinated snapshots.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-19

**Fault:** F-03

**Trigger:** step-8 verification

**Question:** What counts as the same request panic and its accounting when nil panic or user callbacks intervene?

**Current behaviour:** Observed-in-code unless qualified. Recovered nonnil payload is rethrown only if deferred accounting completes. Go version and runtime setting affect nil panic. Original panic can be replaced by policy or notification panic. gobreaker.go:235 ("e := recover()") gobreaker.go:236 ("if e != nil {") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:238 ("panic(e)") gobreaker.go:242 ("result, err := req()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Define panic precedence and supported runtime semantics.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-20

**Fault:** F-18

**Trigger:** step-3 checklist

**Question:** What guarantees are required of valid but unintended settings and copied breakers?

**Current behaviour:** Observed-in-code unless qualified. Constructor applies supplied settings with documented normalization. A value copy after use violates sync.Mutex contract; two copies or two separately built instances have different ownership. gobreaker.go:145 ("cb.onStateChange = st.OnStateChange") gobreaker.go:150 ("cb.maxRequests = st.MaxRequests") gobreaker.go:153 ("if st.Interval <= 0 {") gobreaker.go:159 ("if st.Timeout <= 0 {") gobreaker.go:168 ("cb.readyToTrip = st.ReadyToTrip") gobreaker.go:174 ("cb.isSuccessful = st.IsSuccessful").

**Options:** Document validation and noncopying contract / reject unsupported settings where detectable.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-21

**Fault:** F-03

**Trigger:** step-4 matrix walk

**Question:** Which refusal sentinel and threshold wording are part of the public contract?

**Current behaviour:** Observed-in-code unless qualified. Open returns ErrOpenState, HalfOpen rejects at equality with ErrTooManyRequests. The error comment says over; errors are exported package variables initialized by errors.New. gobreaker.go:23 ("// ErrTooManyRequests is returned when the CB state is half open and the requests count is over the cb maxRequests") gobreaker.go:24 ("ErrTooManyRequests = errors.New("too many requests")") gobreaker.go:26 ("ErrOpenState = errors.New("circuit breaker is open")") gobreaker.go:283 ("if state == StateOpen {") gobreaker.go:284 ("return generation, ErrOpenState") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:286 ("return generation, ErrTooManyRequests") gobreaker.go:268 ("return nil, err").

**Options:** Document at-or-over and error identity / specify a different diagnostic contract.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-22

**Fault:** F-01

**Trigger:** part-B diff

**Question:** Should State, Counts and expiry share a single observable snapshot, including when State is described as a read?

**Current behaviour:** Observed-in-code unless qualified. State can clear or transition and notify. Counts only snapshots stored fields. The blind table expects fresh Counts in one situation and pure State reads in another. gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:220 ("return cb.counts") gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") gobreaker.go:341 ("if cb.expiry.Before(now) {").

**Options:** Specify read and refresh behavior per API / define coordinated snapshots.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Q-23

**Fault:** F-13

**Trigger:** part-B diff

**Question:** When does one call's result or classification order constrain another caller's observation?

**Current behaviour:** Observed-in-code unless qualified. Returning from user work or entering classification is earlier than committing accounting under mutex. A different observer or admission can execute between those points. gobreaker.go:220 ("return cb.counts") gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:298 ("state, generation := cb.currentState(now)").

**Options:** Document separate commit points / specify ordering across callbacks and observers.

**Proposed:** Record the contract after owner review.

**Status:** OPEN — human decision required

## Step 8 verification

The breaker state and counts paths share the mutex at gobreaker.go:207,217,277,294. Lock and unlock synchronization support the observed serialization. Callback overlap is a scheduling property; no data race in the breaker counters is asserted. The zero time sentinel is a literal zero-value declaration (gobreaker.go:367 ("var zero time.Time")), whereas configured deadlines are computed with Add (gobreaker.go:373 ("cb.expiry = now.Add(cb.interval)") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)")). Equality stays by strict Before; runtime clock anomalies and representation bounds remain conditional. Error sentinels are package variables constructed at init, Q-21. The state/counts projection keeps three public lifecycle states and represents capacity and expiry with predicates.

- Q-01 concurrency contract and bounded reproduction. Reviewed cited lines above.
- Q-02 concurrency contract; same lock proof. Reviewed cited lines above.
- Q-03 lifecycle defect under omission; policy open. Reviewed cited lines above.
- Q-04 API accounting defect under one-outcome predicate. Reviewed cited lines above.
- Q-05 documentation/clock scope. Reviewed cited lines above.
- Q-06 surprising refresh order. Reviewed cited lines above.
- Q-07 API latency gap. Reviewed cited lines above.
- Q-08 panic accounting defect reproduced. Reviewed cited lines above.
- Q-09 API panic propagation and committed state. Reviewed cited lines above.
- Q-10 seam contract gap. Reviewed cited lines above.
- Q-11 lifecycle contract and runtime termination. Reviewed cited lines above.
- Q-12 caller attribution gap. Reviewed cited lines above.
- Q-13 API invalid input contract. Reviewed cited lines above.
- Q-14 deployment concern; inferred. Reviewed cited lines above.
- Q-15 unverifiable-runtime range concern. Reviewed cited lines above.
- Q-16 lifecycle policy gap. Reviewed cited lines above.
- Q-17 documentation gap. Reviewed cited lines above.
- Q-18 concurrent user-model gap. Reviewed cited lines above.
- Q-19 panic contract defect when hook fails; runtime variation for nil. Reviewed cited lines above.
- Q-20 valid configuration contract gap. Reviewed cited lines above.
- Q-21 API boundary wording. Reviewed cited lines above.
- Q-22 Part B read consistency gap. Reviewed cited lines above.
- Q-23 Part B callback ordering gap. Reviewed cited lines above.

### Jev finding claim review

- F1 supported. State acquires the breaker mutex before evaluating time. gobreaker.go:207 ("cb.mutex.Lock()"). Re-read the full branch and retained the claim with its stated conditions.
- F2 supported. Counts acquires the same mutex before reading counters. gobreaker.go:217 ("cb.mutex.Lock()"). Re-read the full branch and retained the claim with its stated conditions.
- F3 supported. Admission locks before taking a time sample. gobreaker.go:277 ("cb.mutex.Lock()"). Re-read the full branch and retained the claim with its stated conditions.
- F4 supported. Completion acquires the mutex before evaluating expiry or generation. gobreaker.go:294 ("cb.mutex.Lock()"). Re-read the full branch and retained the claim with its stated conditions.
- F5 supported. ReadyToTrip runs synchronously after incrementing failure counts under the completion mutex. gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). Re-read the full branch and retained the claim with its stated conditions.
- F6 supported. OnStateChange is invoked synchronously after state and generation commit. gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Re-read the full branch and retained the claim with its stated conditions.
- F7 supported. HalfOpen refuses admission at equality with maxRequests. gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). Re-read the full branch and retained the claim with its stated conditions.
- F8 supported. HalfOpen uses a zero expiry so elapsed time does not release capacity there. gobreaker.go:378 ("cb.expiry = zero"). Re-read the full branch and retained the claim with its stated conditions.
- F9 supported. The Allow closure dispatches each invocation with its captured generation and supplied Boolean without a once latch. gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). Re-read the full branch and retained the claim with its stated conditions.
- F10 supported. HalfOpen closes on post-increment consecutive success count reaching maxRequests. gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). Re-read the full branch and retained the claim with its stated conditions.
- F11 supported. Closed resets only on an eligible call when nonzero expiry is strictly before its sample. gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). Re-read the full branch and retained the claim with its stated conditions.
- F12 supported. Open changes only when expiry is strictly before the sampled time. gobreaker.go:341 ("if cb.expiry.Before(now) {"). Re-read the full branch and retained the claim with its stated conditions.
- F13 supported. Counts returns raw stored counters without evaluating expiry. gobreaker.go:220 ("return cb.counts"). Re-read the full branch and retained the claim with its stated conditions.
- F14 supported. Completion samples currentState before discarding a stale captured generation. gobreaker.go:299 ("if generation != before {"). Re-read the full branch and retained the claim with its stated conditions.
- F15 supported. Execute invokes its classifier before afterRequest takes the mutex or tests generation. gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). Re-read the full branch and retained the claim with its stated conditions.
- F16 supported. Execute's defer reports false on recoverable panic, before rethrowing. gobreaker.go:237 ("cb.afterRequest(generation, false)"). Re-read the full branch and retained the claim with its stated conditions.
- F17 supported. Execute installs the recovery defer after successful admission. gobreaker.go:234 ("defer func() {"). Re-read the full branch and retained the claim with its stated conditions.
- F18 supported. Closed failure increments counters before invoking custom policy. gobreaker.go:325 ("cb.counts.onFailure()"). Re-read the full branch and retained the claim with its stated conditions.
- F19 supported. State assignment and generation clearing happen before notifying the hook. gobreaker.go:356 ("cb.toNewGeneration(now)"). Re-read the full branch and retained the claim with its stated conditions.
- F20 supported. After successful accounting Execute returns the original result and error. gobreaker.go:244 ("return result, err"). Re-read the full branch and retained the claim with its stated conditions.
- F21 supported. Refused Allow returns nil callback and error. gobreaker.go:268 ("return nil, err"). Re-read the full branch and retained the claim with its stated conditions.
- F22 supported. Execute invokes the caller's request after admission has returned. gobreaker.go:242 ("result, err := req()"). Re-read the full branch and retained the claim with its stated conditions.
- F23 supported. Generation advances with a uint64 increment. gobreaker.go:364 ("cb.generation++"). Re-read the full branch and retained the claim with its stated conditions.
- F24 supported. Requests increments on each accepted admission using a uint32 field. gobreaker.go:56 ("c.Requests++"). Re-read the full branch and retained the claim with its stated conditions.
- F25 unclear. Each constructor call allocates a distinct breaker object. gobreaker.go:142 ("cb := new(CircuitBreaker)"). Keep as observed construction: new at 142 and returned at 179; separate initialized instances are distinct.
- F26 supported. Name directly returns the stored name without locking. gobreaker.go:202 ("return cb.name"). Re-read the full branch and retained the claim with its stated conditions.
- F27 unclear. A policy panic can cause a second failure accounting attempt by Execute's defer if the generation still matches. gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). Keep: onFailure increments before policy at 325–326, first afterRequest defers unlock at 295, then Execute defer calls again at 237; the overlay measures two failures.
- F28 unclear. A notification panic can replace a request panic when the deferred accounting calls the hook. gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Keep: rethrow at 238 follows accounting, and setState calls the notification at 359. The overlay observes the replacement payload and committed Open.
- F29 unclear. A nil recover value skips failure accounting. gobreaker.go:235 ("e := recover()"). Keep: the explicit condition at 236 skips the block for nil recover; runtime.Goexit and nil panic are distinct.
- F30 unclear. A report callback carries no request identity beyond its captured breaker and generation. gobreaker.go:271 ("return func(success bool) {"). Keep: the closure body calls afterRequest with captured generation and bool at 272, and only equality is checked at 299.

T1 and T2 were supported. Re-read gobreaker_test.go:247 and 337–342; the first is a test-observation limitation and the second confirms only the order in which State refreshes before the old outcome. Added Part B timing questions Q-22 and Q-23 are independently supported by the same reviewed F2, F3, F11–F15 and F20 claims; no new provider verdict was inferred.

All listed decisions remain OPEN.
