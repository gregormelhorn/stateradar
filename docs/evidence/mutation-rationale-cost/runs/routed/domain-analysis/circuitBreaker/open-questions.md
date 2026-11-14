# Open domain questions

## Q-01

**Question:** May OnStateChange call State, Counts, Execute or Allow on the same breaker, and how should competing callers behave during notification?

**Current behaviour:** The state and generation are committed before the hook. The hook runs under the mutex. A reentrant locking call cannot acquire it and the outer call cannot release it until notification returns. Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:354 ("cb.state = state"), gobreaker.go:356 ("cb.toNewGeneration(now)"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Document a non-reentrant synchronous hook / allow reentrancy with an explicit delivery and ordering contract

**Proposed:** Document a non-reentrant synchronous hook.

**Status:** OPEN — human decision required

**Fault:** F-11

**Trigger:** step-3 lock-discipline annotation

## Q-02

**Question:** What may ReadyToTrip call, and is a blocking policy allowed to stall unrelated admissions and reads?

**Current behaviour:** The failure is counted before the policy runs under the mutex. Re-entering a locking API on the same breaker blocks. Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:325 ("cb.counts.onFailure()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").

**Options:** Constrain and document the callback / define a policy isolation contract

**Proposed:** Constrain and document the callback.

**Status:** OPEN — human decision required

**Fault:** F-11

**Trigger:** step-3 lock-discipline annotation

## Q-03

**Question:** Must a completion callback be single-use, including simultaneous duplicate and conflicting calls?

**Current behaviour:** Every matching-generation invocation can count. With MaxRequests 2 one successful trial callback called twice closes HalfOpen without a second admission. In Closed opposite reports can both count and change the failure streak. Observed-in-code gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:315 ("cb.counts.onSuccess()"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {").

**Options:** Require and document exactly one call / define deduplication and which conflicting outcome wins

**Proposed:** Require and document exactly one call.

**Status:** OPEN — human decision required

**Fault:** F-14

**Trigger:** step-3 checklist

## Q-04

**Question:** What recovers a saturated HalfOpen breaker if work or the Allow completion is abandoned, never returns, exits its goroutine, or is delayed indefinitely?

**Current behaviour:** Admissions fill the generation budget. HalfOpen has no expiry. Missing outcomes do not release or replace a slot. A later same-generation report can still close or reopen it. Observed-in-code gobreaker.go:234 ("defer func() {"), gobreaker.go:235 ("e := recover()"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"), gobreaker.go:330 ("cb.setState(StateOpen, now)"), gobreaker.go:378 ("cb.expiry = zero").

**Options:** Make eventual completion a caller obligation / define expiry or explicit cancellation and slot recovery

**Proposed:** Make eventual completion a caller obligation.

**Status:** OPEN — human decision required

**Fault:** F-20

**Trigger:** step-5 lint

## Q-05

**Question:** When must an idle expiry take effect, and should Counts observe it?

**Current behaviour:** Counts serves the stored snapshot. State, admission and completion sample expiry; strictly past expiry resets or transitions. The next qualifying call anchors the next deadline. No autonomous timer is scheduled. Observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:220 ("return cb.counts"), gobreaker.go:280 ("now := time.Now()"), gobreaker.go:297 ("now := time.Now()"), gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"), gobreaker.go:338 ("cb.toNewGeneration(now)"), gobreaker.go:341 ("if cb.expiry.Before(now) {"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)").

**Options:** Specify lazy checks and snapshot semantics / require expiry and notification without traffic

**Proposed:** Specify lazy checks and snapshot semantics.

**Status:** OPEN — human decision required

**Fault:** F-19

**Trigger:** doctrine mapping

## Q-06

**Question:** Is bounded rejection latency promised when a transition hook or policy is slow?

**Current behaviour:** Refusal is decided only after lock acquisition and expiry processing. Competing rejections can wait behind a callback despite README.md:88 saying instantly. Jev supported O02 with scope 0.33, so the cited control is void. Independent analysis also found the mutex delay. Observed-in-code gobreaker.go:224 ("// Execute returns an error instantly if the CircuitBreaker rejects the request."), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Define instantly as no execution after refusal / require a latency bound or a callback constraint

**Proposed:** Define instantly as no execution after refusal.

**Status:** OPEN — human decision required

**Fault:** F-03

**Trigger:** adversarial trace

## Q-07

**Question:** What happens when IsSuccessful, ReadyToTrip or OnStateChange panics or exits, and which panic identity and accounting effects must survive?

**Current behaviour:** Classifier panic reaches Execute recovery and reports failure. A post-request ReadyToTrip panic can trigger a second same-generation failure from recovery. A notification panic after state commit can escape with the commit retained. A policy or hook panic during request-panic accounting can replace the original panic. After a failed Open-to-HalfOpen notification at admission, no trial was counted and a later call can still admit. Observed-in-code gobreaker.go:234 ("defer func() {"), gobreaker.go:235 ("e := recover()"), gobreaker.go:237 ("cb.afterRequest(generation, false)"), gobreaker.go:238 ("panic(e)"), gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:295 ("defer cb.mutex.Unlock()"), gobreaker.go:325 ("cb.counts.onFailure()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:354 ("cb.state = state"), gobreaker.go:356 ("cb.toNewGeneration(now)"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Specify callback preconditions and effects before failure / define callback fault handling and panic precedence

**Proposed:** Specify callback preconditions and effects before failure.

**Status:** OPEN — human decision required

**Fault:** F-03

**Trigger:** step-8 verification

## Q-08

**Question:** What validation is expected for nil work, nil or zero receivers, wrong valid receivers, and a completion capability used for the wrong request?

**Current behaviour:** Nil work panics after admission. A valid wrong breaker applies its own state and policy. A zero breaker has nil classifier and trip policy, and zero two-step wrapper has a nil underlying pointer. The callback stays bound to the original breaker and accepts any Boolean. Observed-in-code gobreaker.go:142 ("cb := new(CircuitBreaker)"), gobreaker.go:171 ("if st.IsSuccessful == nil {"), gobreaker.go:202 ("return cb.name"), gobreaker.go:242 ("result, err := req()"), gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:268 ("return nil, err"), gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)").

**Options:** Require constructed receiver and attributable callback / define boundary validation and safe errors

**Proposed:** Require constructed receiver and attributable callback.

**Status:** OPEN — human decision required

**Fault:** F-18

**Trigger:** step-3 checklist

## Q-09

**Question:** Can late work still classify, return its payload, change state by observing expiry, or report after application cancellation?

**Current behaviour:** Execute still classifies and returns ordinary results after rollover. Stale reports are dropped from accounting after expiry processing, and a stale report can promote Open to HalfOpen. Application cancellation alone has no breaker signal. Same-generation success and failure still apply. Observed-in-code gobreaker.go:242 ("result, err := req()"), gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:244 ("return result, err"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:297 ("now := time.Now()"), gobreaker.go:298 ("state, generation := cb.currentState(now)"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:300 ("return"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)").

**Options:** Document outcome accounting and result delivery separately / define caller cancellation and side-effect limits

**Proposed:** Document outcome accounting and result delivery separately.

**Status:** OPEN — human decision required

**Fault:** F-15

**Trigger:** adversarial trace

## Q-10

**Question:** Which HalfOpen success and failure rules are intended, including boundary equality and reports racing with a new admission?

**Current behaviour:** Admission rejects at Requests equal to the limit. Failure immediately opens. Matching successes close on the threshold. The error docstring says over and README specifies a maximum without describing recovery criteria. Observed-in-code gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:286 ("return generation, ErrTooManyRequests"), gobreaker.go:315 ("cb.counts.onSuccess()"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"), gobreaker.go:317 ("cb.setState(StateClosed, now)"), gobreaker.go:330 ("cb.setState(StateOpen, now)").

**Options:** Document the current guarded behavior / define another trial and recovery policy

**Proposed:** Document the current guarded behavior.

**Status:** OPEN — human decision required

**Fault:** F-22

**Trigger:** step-4 matrix walk

## Q-11

**Question:** Is a synchronized wave of HalfOpen trials across instances acceptable for a shared downstream?

**Current behaviour:** Each instance derives expiry from its local call time and fixed timeout. There is no jitter or shared budget. Concurrent traffic can align trials and subsequent restart cycles. Observed-in-code gobreaker.go:280 ("now := time.Now()"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").

**Options:** Keep per-instance control with documented aggregation / specify coordinated or dispersed probes

**Proposed:** Keep per-instance control with documented aggregation.

**Status:** OPEN — human decision required

**Fault:** F-10

**Trigger:** multi-instance probes

## Q-12

**Question:** What ranges and overflow guarantees apply to long-lived counters and generation identifiers?

**Current behaviour:** Counts use uint32 increments and generation uses uint64 equality. Wrap is possible at their respective bounds. A callback retained across a full generation wrap can theoretically alias the current epoch. Observed-in-code gobreaker.go:48 ("Requests             uint32"), gobreaker.go:56 ("c.Requests++"), gobreaker.go:60 ("c.TotalSuccesses++"), gobreaker.go:67 ("c.ConsecutiveFailures++"), gobreaker.go:128 ("generation uint64"), gobreaker.go:364 ("cb.generation++").

**Options:** Document operational bounds / specify saturation and stale-identity guarantees

**Proposed:** Document operational bounds.

**Status:** OPEN — human decision required

**Fault:** F-05

**Trigger:** step-5 lint

## Q-13

**Question:** Are classifier and trip-policy functions allowed to be stateful, concurrent, misleading, or to classify the same raw error differently?

**Current behaviour:** IsSuccessful can overlap across requests, changes accounting, and leaves the returned error intact. ReadyToTrip is serialized per breaker and receives counts by value, including other admitted work. Observed-in-code gobreaker.go:197 ("return err == nil"), gobreaker.go:242 ("result, err := req()"), gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:244 ("return result, err"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:325 ("cb.counts.onFailure()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").

**Options:** Document concurrency and semantic preconditions / require consistent classification and policy inputs

**Proposed:** Document concurrency and semantic preconditions.

**Status:** OPEN — human decision required

**Fault:** F-18

**Trigger:** seam-contract sweep

## Q-14

**Question:** Should the HalfOpen expiry assertion test the custom breaker, and which public observation should establish the deadline behavior?

**Current behaviour:** The custom test checks defaultCB.expiry at gobreaker_test.go:247. Its state and notification assertions concern customCB. Source clears expiry in HalfOpen. Observed-in-code gobreaker.go:341 ("if cb.expiry.Before(now) {"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:378 ("cb.expiry = zero"). Observed-in-tests gobreaker_test.go:247 ("assert.True(t, defaultCB.expiry.IsZero())"). The full race run separately reports gobreaker_test.go:258 ("assert.Equal(t, Counts{3, 2, 0, 2, 0}, customCB.counts)") overlapping gobreaker.go:56. The model validation records that harness race.

**Options:** Replace the assertion target in a later test change / document the intended test boundary

**Proposed:** Replace the assertion target in a later test change.

**Status:** OPEN — human decision required

**Fault:** F-21

**Trigger:** step-2 test replay

## Q-15

**Question:** May one caller hold overlapping admissions, and is accounting in completion order intended?

**Current behaviour:** Caller identity is absent. Each accepted invocation increments Requests and reserves its own generation sample. A later workload or callback can finish first. There is no queue or handoff and no reservation represented by a returned Execute payload. Observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"), gobreaker.go:242 ("result, err := req()"), gobreaker.go:265 ("func (tscb *TwoStepCircuitBreaker) Allow() (done func(success bool), err error) {"), gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:303 ("if success {"), gobreaker.go:306 ("cb.onFailure(state, now)").

**Options:** Document independent admissions and completion-order accounting / define an ownership or ordering limit

**Proposed:** Document independent admissions and completion-order accounting.

**Status:** OPEN — human decision required

**Fault:** F-16

**Trigger:** adversarial trace

## Q-16

**Question:** What lifetime and retention contract applies when callers hold old callbacks or create a replacement breaker?

**Current behaviour:** A new breaker does not invalidate the old instance. A retained callback can keep the old wrapper and breaker reachable. No per-request map or queue is stored. Retention cost depends on caller references and GC. Observed-in-code gobreaker.go:142 ("cb := new(CircuitBreaker)"), gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:364 ("cb.generation++"), gobreaker.go:365 ("cb.counts.clear()").

**Options:** Document callback ownership and disposal / define explicit retirement and stale capability invalidation

**Proposed:** Document callback ownership and disposal.

**Status:** OPEN — human decision required

**Fault:** F-07

**Trigger:** step-5 lint

## Q-17

**Question:** Should negative durations and unusually large valid settings be accepted as documented defaults or rejected?

**Current behaviour:** Settings comments specify nonpositive defaults while the README names zero. Large typed values are accepted and used directly. Observed-in-code gobreaker.go:147 ("if st.MaxRequests == 0 {"), gobreaker.go:148 ("cb.maxRequests = 1"), gobreaker.go:153 ("if st.Interval <= 0 {"), gobreaker.go:159 ("if st.Timeout <= 0 {"), gobreaker.go:189 ("const defaultInterval = time.Duration(0) * time.Second"), gobreaker.go:190 ("const defaultTimeout = time.Duration(60) * time.Second"), gobreaker.go:373 ("cb.expiry = now.Add(cb.interval)"), gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").

**Options:** Align the README with the Settings contract / define validation ranges

**Proposed:** Align the README with the Settings contract.

**Status:** OPEN — human decision required

**Fault:** F-18

**Trigger:** step-1 extraction

## Q-18

**Question:** What is the supported protection for fabricated completion and reused names or notification payloads?

**Current behaviour:** A rejected Allow returns a nil callback. Calling nil panics in the caller. A valid closure can be invoked without running work. Notifications carry a name and state pair with no distinct identity. Observed-in-code gobreaker.go:145 ("cb.onStateChange = st.OnStateChange"), gobreaker.go:202 ("return cb.name"), gobreaker.go:268 ("return nil, err"), gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Document capability and observer identity requirements / add explicit signals in a later design

**Proposed:** Document capability and observer identity requirements.

**Status:** OPEN — human decision required

**Fault:** F-17

**Trigger:** step-3 checklist

## Q-19

**Question:** Should callers get a coherent state and counts snapshot across separate calls?

**Current behaviour:** Each call is serialized on its own. State can reset counters in between reads. Name is a separate immutable value. Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:220 ("return cb.counts"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:365 ("cb.counts.clear()").

**Options:** Document per-call snapshots / specify an atomic combined observation

**Proposed:** Document per-call snapshots.

**Status:** OPEN — human decision required

**Fault:** F-03

**Trigger:** adversarial trace

## Q-20

**Question:** Which Go runtime edge cases are included in the request panic promise?

**Current behaviour:** Accounting and rethrow require recover to return a non-nil value. Goexit and legacy panic(nil) can yield nil. Modern and compatibility-mode nil panic behavior differ. Observed-in-code gobreaker.go:234 ("defer func() {"), gobreaker.go:235 ("e := recover()"), gobreaker.go:237 ("cb.afterRequest(generation, false)"), gobreaker.go:238 ("panic(e)").

**Options:** Document the supported panic/runtime semantics / define explicit behavior for unusual termination

**Proposed:** Document the supported panic/runtime semantics.

**Status:** OPEN — human decision required

**Fault:** F-03

**Trigger:** step-8 verification

## Q-21

**Question:** Does the acceptance guarantee cover every constructed Closed breaker and every admitted Execute ordering?

**Current behaviour:** Source invokes the accepted request after admission. The submitted O01 phrased acceptance before the caller supplied the function. README line 87 describes the accepted-call outcome, without that ordering. Jev returned unclear with scope 0.02. The original result is retained and the asserted ordering is not a control. Observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"), gobreaker.go:231 ("return nil, err"), gobreaker.go:242 ("result, err := req()").

**Options:** Confirm the documented contract / specify exclusions

**Proposed:** Confirm the documented contract.

**Status:** OPEN — human decision required

**Fault:** F-19

**Trigger:** jev check

## Q-22

**Question:** Does the count-clear promise cover the stated delayed-completion sequence regardless of what caused the clear?

**Current behaviour:** Generation-mismatched outcomes are skipped. README line 79 appears to cover the stated sequence, but Jev returned unclear with scope 0.18, so its control verdict is void under routing rule 5. Observed-in-code gobreaker.go:297 ("now := time.Now()"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:300 ("return"), gobreaker.go:365 ("cb.counts.clear()").

**Options:** Confirm count isolation scope / specify exceptions

**Proposed:** Confirm count isolation scope.

**Status:** OPEN — human decision required

**Fault:** F-15

**Trigger:** jev check
