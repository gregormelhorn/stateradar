# Open domain questions

## Q-01 — When must expiry become observable, and should Counts refresh first?

**Fault:** F-13

**Trigger:** step-1 extraction

**Current behaviour:** A strict comparison runs only from State, admission and completion. Counts and Name never refresh; silence leaves the stored mode unchanged. observed-in-code gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"), gobreaker.go:341 ("if cb.expiry.Before(now) {"), gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:220 ("return cb.counts"), gobreaker.go:373 ("cb.expiry = now.Add(cb.interval)").

**Options:** Lazy refresh with explicit boundary and snapshot semantics / refresh Counts as well / actively schedule expiry.

**Status:** OPEN — human decision required

## Q-02 — What should happen when an admitted probe never completes or its owner abandons it?

**Fault:** F-07

**Trigger:** step-5 lint

**Current behaviour:** Half-open has no expiry. Its budget remains spent whether the caller abandons an Allow continuation or Execute work remains blocked; a later matching report can still change state. observed-in-code gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:377 ("default: // StateHalfOpen").

**Options:** Require and document completion / provide bounded recovery or cancellation.

**Status:** OPEN — human decision required

## Q-03 — Should a completion callback count at most once, including concurrent and contradictory reports?

**Fault:** F-14

**Trigger:** step-3 checklist

**Current behaviour:** The callback has no per-admission latch. Same-generation repeats count; one probe can supply enough successful reports to close. Opposite booleans are processed in lock order until a transition makes the remaining report stale. observed-in-code gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {").

**Options:** Once-only report / explicitly allow multiple reports / diagnose duplicates.

**Status:** OPEN — human decision required

## Q-04 — May stale work classify or advance an expired breaker before its count is ignored?

**Fault:** F-15

**Trigger:** adversarial trace

**Current behaviour:** Execute still classifies; both result paths refresh first. A stale report can publish Open to HalfOpen, reset counters and return without counting. A stale failure or success otherwise leaves the current counters unchanged. observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:298 ("state, generation := cb.currentState(now)"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)").

**Options:** Keep refresh and label its effects / check freshness before any side effect.

**Status:** OPEN — human decision required

## Q-05 — Which callbacks may call back into the breaker or wait on callers that do?

**Fault:** F-11

**Trigger:** step-3 lock-discipline annotation

**Current behaviour:** ReadyToTrip and OnStateChange run under the mutex. Reentry through Counts, State, admission or a report can block permanently. Name does not take that mutex. observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Document callback restrictions / permit reentry with defined ordering.

**Status:** OPEN — human decision required

## Q-06 — What are the failure, blocking, and concurrency contracts of injected policies?

**Fault:** F-03

**Trigger:** seam-contract sweep

**Current behaviour:** Classifier panic enters Execute recovery. A trip predicate panic follows the failure increment and can lead to a second account attempt in Execute. State notification panic follows commit. In State or admission it escapes directly; when invoked in normal Execute accounting it reaches the recovery path. Goexit runs defers without a recoverable value. observed-in-code gobreaker.go:235 ("e := recover()"), gobreaker.go:237 ("cb.afterRequest(generation, false)"), gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:354 ("cb.state = state"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Additional evidence:** observed-in-tests domain-analysis/circuitBreaker/_probe/behavior_test.go:201 ("if c := b.Counts(); c.Requests != 1 || c.TotalFailures != 2 || calls != 2 {"). Scope is a first-call ReadyToTrip panic during normal Execute accounting, followed by normal return from the second invocation.

**Options:** Define panic and Goexit outcomes per policy / isolate policy failures / require return and concurrency safety.

**Status:** OPEN — human decision required

## Q-07 — Who owns receiver, report, outcome and policy identity validation?

**Fault:** F-18

**Trigger:** step-3 checklist

**Current behaviour:** The receiver chooses the breaker. A genuine continuation reports to its captured wrapper and generation; a wrong valid callback or boolean can be applied without detection. The boundary has no request or caller identifier. observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"), gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"), gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:303 ("if success {").

**Options:** Define caller ownership / validate identity or report malformed work.

**Status:** OPEN — human decision required

## Q-08 — What should nil callbacks, uninitialized receivers and nil panic values do?

**Fault:** F-03

**Trigger:** step-4 matrix walk

**Current behaviour:** Constructed Allow returns nil callback on refusal; invoking it panics in the caller. A nil Execute request panics after acceptance. Zero core lacks policy initialization; zero wrapper has nil backing core. Nil panic recovery depends on the Go runtime setting. observed-in-code gobreaker.go:136 ("type TwoStepCircuitBreaker struct {"), gobreaker.go:236 ("if e != nil {"), gobreaker.go:242 ("result, err := req()"), gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").

**Options:** Document constructor and nil preconditions / explicitly reject invalid uses.

**Status:** OPEN — human decision required

## Q-09 — What counter bounds and exact accounting guarantees should Counts expose?

**Fault:** F-05

**Trigger:** step-5 lint

**Current behaviour:** Fields are uint32 and wrap; request and outcome counts can diverge with accepted work, stale work, or duplicate reports. Generation comparison uses uint64 and can alias only after wrap. observed-in-code gobreaker.go:48 ("Requests             uint32"), gobreaker.go:56 ("c.Requests++"), gobreaker.go:60 ("c.TotalSuccesses++"), gobreaker.go:66 ("c.TotalFailures++"), gobreaker.go:365 ("cb.counts.clear()").

**Options:** Specify modulo counters and caveats / enforce a bound and exact accounting.

**Status:** OPEN — human decision required

## Q-10 — What does immediate rejection promise when another operation owns the lock?

**Fault:** F-03

**Trigger:** step-5 lint

**Current behaviour:** Once the admission lock is acquired, refusal skips request work. A callback holding the lock can delay the caller before any refusal is sent. observed-in-code gobreaker.go:224 ("// Execute returns an error instantly if the CircuitBreaker rejects the request."), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:284 ("return generation, ErrOpenState"), gobreaker.go:286 ("return generation, ErrTooManyRequests"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Define immediate as no work after decision / require bounded response.

**Status:** OPEN — human decision required

## Q-11 — Should shared-dependency deployments decorrelate recovery probes?

**Fault:** F-10

**Trigger:** multi-instance probes

**Current behaviour:** Each breaker uses its own fixed expiry and budget. Simultaneous opening and caller traffic can align recovery and subsequent reopening across instances. observed-in-code gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:317 ("cb.setState(StateClosed, now)"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").

**Options:** External staggering / provide an explicit dispersion policy / retain per-instance limits.

**Status:** OPEN — human decision required

## Q-12 — Which half-open closing/reopening semantics and return errors are public guarantees?

**Fault:** F-06

**Trigger:** step-1 extraction

**Current behaviour:** At budget admission returns ErrTooManyRequests; the public comment uses over, which can be read numerically. Matching success threshold closes, failure opens, and Open rejects with ErrOpenState. observed-in-code gobreaker.go:23 ("// ErrTooManyRequests is returned when the CB state is half open and the requests count is over the cb maxRequests"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:286 ("return generation, ErrTooManyRequests"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"), gobreaker.go:330 ("cb.setState(StateOpen, now)").

**Options:** Document exact boundaries, outcomes, and notification order / revise public promise.

**Status:** OPEN — human decision required

## Q-13 — What is the lifetime of old continuations and how should replacement work?

**Fault:** F-07

**Trigger:** step-5 lint

**Current behaviour:** A retained closure holds the wrapper and generation. Dropping or replacing the caller's breaker reference sends no teardown event. Keeping an old wrapper while rebinding a caller variable preserves the old target. Overwriting the wrapper value itself can redirect an old report to the replacement core when generations match. The overlay confirms this with serialized assignment. Copying a live core has further mutex restrictions. observed-in-code gobreaker.go:183 ("func NewTwoStepCircuitBreaker(st Settings) *TwoStepCircuitBreaker {"), gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:299 ("if generation != before {").

**Additional evidence:** observed-in-tests domain-analysis/circuitBreaker/_probe/behavior_test.go:177 ("if got := b.Counts(); got.Requests != 0 || got.TotalSuccesses != 1 {"). The callback captures the wrapper pointer and re-reads its backing field at invocation, observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)").

**Options:** State ownership and copying rules / provide explicit invalidation.

**Status:** OPEN — human decision required

## Q-14 — Which expiry should the custom transition test verify?

**Fault:** F-21

**Trigger:** step-2 test replay

**Current behaviour:** The custom-breaker test checks the default breaker's expiry after custom Open to HalfOpen. That assertion cannot establish custom expiry. observed-in-code gobreaker.go:378 ("cb.expiry = zero"). observed-in-tests gobreaker_test.go:247 ("assert.True(t, defaultCB.expiry.IsZero())").

**Options:** Check custom breaker via a projected behavior / name the intended cross-instance assertion.

**Status:** OPEN — human decision required

## Q-15 — What ordering and capacity promises should repeated admission from the same caller expose?

**Fault:** F-02

**Trigger:** adversarial trace

**Current behaviour:** Admission serializes under the mutex. Closed calls can both enter; completion order can differ. Half-open slots are spent by each accepted admission and never queued. At budget a second call rejects; there is no caller identity. observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:242 ("result, err := req()"), gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:294 ("cb.mutex.Lock()").

**Options:** Document independent admissions and lifetime budget / define per-caller coordination.

**Status:** OPEN — human decision required

## Q-16 — Which request outcomes are guaranteed across panic and generation changes?

**Fault:** F-03

**Trigger:** seam-contract sweep

**Current behaviour:** An ordinary request panic supplies a failed completion before repanic; if stale its contribution is ignored. A panic from failure processing can replace the request panic and a blocking hook can prevent repanic altogether. observed-in-code gobreaker.go:235 ("e := recover()"), gobreaker.go:237 ("cb.afterRequest(generation, false)"), gobreaker.go:238 ("panic(e)"), gobreaker.go:299 ("if generation != before {").

**Options:** Specify exception precedence / preserve original panic irrespective of reporting.

**Status:** OPEN — human decision required

## Q-17 — How should accepted but unintended settings be surfaced?

**Fault:** F-18

**Trigger:** step-1 extraction

**Current behaviour:** Zero max becomes one, nonpositive durations default, valid policies replace defaults. README covers zero durations while Settings comments explicitly cover negative durations. observed-in-code gobreaker.go:147 ("if st.MaxRequests == 0 {"), gobreaker.go:153 ("if st.Interval <= 0 {"), gobreaker.go:159 ("if st.Timeout <= 0 {"), gobreaker.go:165 ("if st.ReadyToTrip == nil {"), gobreaker.go:171 ("if st.IsSuccessful == nil {").

**Options:** Document defaults consistently / validate unintended values.

**Status:** OPEN — human decision required
