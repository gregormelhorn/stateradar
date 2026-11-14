# Open domain questions


## Q-01 — Should expiry be autonomous, inclusive, and anchored to the original schedule?

**Fault:** F-13

**Trigger:** step-1 extraction

**Question:** Should expiry be autonomous, inclusive, and anchored to the original schedule?

**Current behaviour:** observed-in-code. Open or closed interval changes only at State, admission or accounting. A strictly later sample reconciles once and starts the next window from its sample. gobreaker.go:280 ("now := time.Now()"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). gobreaker.go:341 ("if cb.expiry.Before(now) {"). gobreaker.go:373 ("cb.expiry = now.Add(cb.interval)").

**Options:** Specify lazy strict observation / specify inclusive observation / provide scheduled expiry

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-02 — Should Counts refresh an elapsed closed interval, and should State be allowed to mutate or notify?

**Fault:** F-05

**Trigger:** step-5 lint

**Question:** Should Counts refresh an elapsed closed interval, and should State be allowed to mutate or notify?

**Current behaviour:** observed-in-code. Counts reads stored values. State can clear a closed generation or cause a half-open notification. Adjacent snapshots can therefore disagree about freshness. gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:338 ("cb.toNewGeneration(now)"). gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Document each read / reconcile both / expose separate snapshot and refresh

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-03 — Should every Allow callback accept at most one report?

**Fault:** F-14

**Trigger:** adversarial trace

**Question:** Should every Allow callback accept at most one report?

**Current behaviour:** observed-in-code. While generation matches, repeat success can close half-open with fewer distinct completed requests; repeat failure can inflate counts or trip; opposite results serialize, and a generation change masks whichever report arrives later. gobreaker.go:271 ("return func(success bool) {"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:315 ("cb.counts.onSuccess()"). gobreaker.go:325 ("cb.counts.onFailure()").

**Options:** Trust caller / make callback idempotent / expose refusal

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-04 — What exactly should half-open count, and what outcomes should reopen or close it?

**Fault:** F-02

**Trigger:** step-4 matrix walk

**Question:** What exactly should half-open count, and what outcomes should reopen or close it?

**Current behaviour:** observed-in-code. Admission charges a generation budget, capped at equality. Failure opens at once; consecutive reported successes reaching the budget close. Rejected requests leave counters alone. gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:289 ("cb.counts.onRequest()"). gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). gobreaker.go:330 ("cb.setState(StateOpen, now)").

**Options:** Document generation budget / specify distinct trial completions / define another policy

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-05 — Which effects of stale work should still run?

**Fault:** F-15

**Trigger:** adversarial trace

**Question:** Which effects of stale work should still run?

**Current behaviour:** observed-in-code. Normal Execute calls its classifier and returns the original outcome even when accounting is stale. A stale report still checks time, can refresh a generation or notify during open expiry, and skips closed trip policy or outcome writes. gobreaker.go:242 ("result, err := req()"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:342 ("cb.setState(StateHalfOpen, now)").

**Options:** Keep current effects / disable stale classification / make stale reports observationally inert

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-06 — How should missing, cancelled, stalled or Goexit work and caller teardown affect the breaker?

**Fault:** F-07

**Trigger:** step-5 lint

**Question:** How should missing, cancelled, stalled or Goexit work and caller teardown affect the breaker?

**Current behaviour:** observed-in-code. No cancellation or teardown registration is exposed. Missing reports retain admission counts; saturated HalfOpen cannot recover without a current outcome. A later success or failure may still affect the retained breaker or be stale. No per-request buffer was found. gobreaker.go:234 ("defer func() {"). gobreaker.go:235 ("e := recover()"). gobreaker.go:242 ("result, err := req()"). gobreaker.go:271 ("return func(success bool) {"). gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:334 ("func (cb *CircuitBreaker) currentState(now time.Time) (State, uint64) {").

**Options:** Require explicit reporting / document indefinite hold / define cancellation or expiry

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-07 — Should a second acquisition by the same caller be independent?

**Fault:** F-16

**Trigger:** adversarial trace

**Question:** Should a second acquisition by the same caller be independent?

**Current behaviour:** observed-in-code. Both APIs count each successful admission. A second Execute can finish before the first. Two Allow calls below the cap return independent callbacks; at capacity the second is refused. Reporting one neither completes the other nor refunds a slot. gobreaker.go:242 ("result, err := req()"). gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). gobreaker.go:271 ("return func(success bool) {"). gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:289 ("cb.counts.onRequest()").

**Options:** Document independence / introduce caller-level limits or identity

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-08 — What should happen for wrong receivers, zero values, nil requests, and unintended settings?

**Fault:** F-18

**Trigger:** step-3 checklist

**Question:** What should happen for wrong receivers, zero values, nil requests, and unintended settings?

**Current behaviour:** observed-in-code. Wrong valid receivers operate normally. Zero CircuitBreaker lacks default policies; zero wrapper has a nil inner pointer. An admitted nil request panics through Execute recovery. Nonpositive durations normalize and MaxRequests is unsigned. gobreaker.go:142 ("cb := new(CircuitBreaker)"). gobreaker.go:147 ("if st.MaxRequests == 0 {"). gobreaker.go:153 ("if st.Interval <= 0 {"). gobreaker.go:159 ("if st.Timeout <= 0 {"). gobreaker.go:242 ("result, err := req()"). gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()").

**Options:** Document valid receiver preconditions / validate exposed inputs / define zero-value support

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-09 — May ReadyToTrip and OnStateChange reenter breaker methods or block other callers?

**Fault:** F-11

**Trigger:** step-3 lock-discipline annotation

**Question:** May ReadyToTrip and OnStateChange reenter breaker methods or block other callers?

**Current behaviour:** observed-in-code. Both run synchronously under the same mutex used by State, Counts and admission. Same-goroutine reentry into those methods blocks; Name reads without the lock. Other callers wait until the callback returns. gobreaker.go:202 ("return cb.name"). gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Document callback restrictions / define bounded or reentrant callback delivery

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-10 — What should panic and no-return behavior be for each callback?

**Fault:** F-03

**Trigger:** step-8 verification

**Question:** What should panic and no-return behavior be for each callback?

**Current behaviour:** observed-in-code. A classifier panic can be treated as a request failure. A trip-policy panic during regular accounting may count the failure twice because Execute recovers and attempts accounting again after unlock. A notification panic during panic accounting can replace the request panic after state has committed. Panics during admission bypass Execute recovery. gobreaker.go:229 ("generation, err := cb.beforeRequest()"). gobreaker.go:234 ("defer func() {"). gobreaker.go:237 ("cb.afterRequest(generation, false)"). gobreaker.go:238 ("panic(e)"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:295 ("defer cb.mutex.Unlock()"). gobreaker.go:325 ("cb.counts.onFailure()"). gobreaker.go:354 ("cb.state = state"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Define callback failure boundaries / preserve current panic behavior with a documented contract

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-11 — Should counts and generation tolerate wrap or retain more history?

**Fault:** F-05

**Trigger:** z3 invariant check

**Question:** Should counts and generation tolerate wrap or retain more history?

**Current behaviour:** observed-in-code. Counts are uint32; duplicate reports break a distinct-request accounting bound even without wrap. Generation is uint64 and updates on each reset; equality alone cannot disambiguate a reference retained across a full wrap. Counter wrap and retention cost are unmeasured in production. gobreaker.go:48 ("Requests             uint32"). gobreaker.go:56 ("c.Requests++"). gobreaker.go:60 ("c.TotalSuccesses++"). gobreaker.go:128 ("generation uint64"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:364 ("cb.generation++").

**Options:** Define accounting bounds and loss tolerance / retain identity / document wrap assumptions

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-12 — What guarantee applies to notification side effects and blocked observers?

**Fault:** F-03

**Trigger:** seam-contract sweep

**Question:** What guarantee applies to notification side effects and blocked observers?

**Current behaviour:** observed-in-code. State and counts are committed before a synchronous notification. Callback errors have no return channel and partial downstream effects have no compensation. Notification can consume part of the open timeout and delay refusals. gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:354 ("cb.state = state"). gobreaker.go:356 ("cb.toNewGeneration(now)"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").

**Options:** Document synchronous best effort / specify acknowledgment, isolation or timing

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-13 — Which forged or transferred callback operations need defensive handling?

**Fault:** F-17

**Trigger:** step-3 checklist

**Question:** Which forged or transferred callback operations need defensive handling?

**Current behaviour:** observed-in-code. There is no public independent policy delivery path. A nil returned callback invoked by the caller panics outside the library. Possession of a live callback permits reporting another request's typed value to the captured breaker. gobreaker.go:248 ("func (tscb *TwoStepCircuitBreaker) Name() string {"). gobreaker.go:267 ("if err != nil {"). gobreaker.go:268 ("return nil, err"). gobreaker.go:271 ("return func(success bool) {"). gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). gobreaker.go:303 ("if success {").

**Options:** Require caller ownership / define misuse diagnostics or authentication

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-14 — Who owns aggregate half-open probe load across breakers sharing a service?

**Fault:** F-10

**Trigger:** multi-instance probes

**Question:** Who owns aggregate half-open probe load across breakers sharing a service?

**Current behaviour:** observed-in-code. Each instance sets its own fixed expiry and releases up to its local budget on demand. No coordination, backoff or jitter exists at this seam. gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").

**Options:** Document caller-side responsibility / define shared or dispersed probe policy

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-15 — What does an instant rejection promise under lock contention?

**Fault:** F-03

**Trigger:** doctrine mapping

**Question:** What does an instant rejection promise under lock contention?

**Current behaviour:** observed-in-code. Admission locks before checking state and can wait behind policy or notification. Once the rejection branch is reached, the request is skipped and the error is returned. gobreaker.go:229 ("generation, err := cb.beforeRequest()"). gobreaker.go:231 ("return nil, err"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:283 ("if state == StateOpen {"). gobreaker.go:286 ("return generation, ErrTooManyRequests"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

**Options:** Define instantly as no work executed / specify wall-clock bound or nonblocking admission

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-16 — How should custom policy disagreement and unchanged Execute result be explained?

**Fault:** F-18

**Trigger:** step-1 extraction

**Question:** How should custom policy disagreement and unchanged Execute result be explained?

**Current behaviour:** observed-in-code. A classifier can mark a non-nil error successful or nil error unsuccessful. Execute returns the original value and error. ReadyToTrip consumes a copy of counters including the current failure when applicable. gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:244 ("return result, err"). gobreaker.go:325 ("cb.counts.onFailure()"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").

**Options:** Document unchanged caller result and classification authority / define diagnostic policy

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.


## Q-17 — What reference lifetime and copying guarantees apply?

**Fault:** F-07

**Trigger:** step-3 checklist

**Question:** What reference lifetime and copying guarantees apply?

**Current behaviour:** observed-in-code. The returned closure captures the wrapper and generation; the breaker stores no per-callback registry. A copied wrapper shares its breaker pointer. Copying a mutex-bearing breaker after use conflicts with the Go mutex contract. gobreaker.go:126 ("mutex      sync.Mutex"). gobreaker.go:137 ("cb *CircuitBreaker"). gobreaker.go:271 ("return func(success bool) {"). gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)").

**Options:** Document ownership and retention / define release or explicit misuse constraints

**Proposed:** defer selection to the owner.

**Status:** OPEN — human decision required.

## Q-18 — Does the default predicate require a separately scoped ordering?

**Fault:** F-02

**Trigger:** jev check

**Current behaviour:** observed-in-code gobreaker.go:193 ("return counts.ConsecutiveFailures > 5"). The numeric rule is explicit in README.md:56. The agent reads the threshold example as contemplated. Jev supported the assertion but returned scope 0.06, voiding the routed control verdict.

**Options:** Keep the numeric predicate as the contract / give the six-failure sequence an explicit example.

**Status:** OPEN — human decision required.

## Q-19 — Does the stale-result sentence cover a result arriving after an independently committed clear?

**Fault:** F-15

**Trigger:** jev check

**Current behaviour:** observed-in-code gobreaker.go:299 ("if generation != before {"). The agent reads README.md:79 as covering the ordering for Counts alone. Jev supported the assertion but returned scope 0.19, voiding the routed control verdict. Related Q-05 covers classifier and expiry effects.

**Options:** Document the separate-clear schedule / retain the general stale-accounting sentence.

**Status:** OPEN — human decision required.
