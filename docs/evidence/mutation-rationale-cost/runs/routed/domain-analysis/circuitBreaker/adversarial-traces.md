# Adversarial traces

Pair ordering refers to the first relevant lock acquisition or callback observation named in the sequence. Invocation alone does not establish commit order. Cited source defines these observed paths. Test-backed schedules are indexed separately in as-is-validation.md.

### P-01a — Execute first

1. Expired Open. Execute acquires the mutex and changes state, unlocks after admission, then pauses in work. The independent reader sees HalfOpen before work commits.
2. Observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:281 ("state, generation := cb.currentState(now)"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:242 ("result, err := req()"), gobreaker.go:211 ("state, _ := cb.currentState(now)").
3. Question Q-05.

### P-01b — ReadState first

1. Expired Open. Reader takes the mutex first and advances to HalfOpen. Execute subsequently takes its own sample and admits the trial; threshold success can close later.
2. Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:317 ("cb.setState(StateClosed, now)").
3. Question Q-05.

### P-02a — Execute first

1. Closed. A enters Execute, increments Requests, unlocks and pauses in work. A concurrent Counts sees one admission and zero outcomes. Work can finish later.
2. Observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:242 ("result, err := req()"), gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:220 ("return cb.counts").
3. Question Q-19.

### P-02b — ReadCounts first

1. Closed. Counts reader takes its snapshot before A acquires admission lock. A then increments Requests. Snapshot is zero.
2. Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:220 ("return cb.counts"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:289 ("cb.counts.onRequest()").
3. Question Q-19.

### P-03a — Allow first

1. HalfOpen at capacity one. B takes admission lock before A reports true and gets ErrTooManyRequests. A then commits success and closes.
2. Observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:286 ("return generation, ErrTooManyRequests"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"), gobreaker.go:317 ("cb.setState(StateClosed, now)").
3. Question Q-10.
- Reachability: HalfOpen → Closed — domain-analysis/circuitBreaker/_probe/as_is_test.go:104 ("ordered success left state %v")

### P-03b — ReportSuccess first

1. HalfOpen at capacity one. A reports true and closes under lock. B then admits in the new Closed generation.
2. Observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:317 ("cb.setState(StateClosed, now)"), gobreaker.go:365 ("cb.counts.clear()"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:289 ("cb.counts.onRequest()").
3. Question Q-10.

### P-04a — Allow first

1. HalfOpen with A pending. At capacity, B is refused before A fails; below capacity B admits and its later success or failure is stale after A reopens.
2. Observed-in-code gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:286 ("return generation, ErrTooManyRequests"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:330 ("cb.setState(StateOpen, now)").
3. Question Q-10.

### P-04b — ReportFailure first

1. HalfOpen with A pending. A reports failure and reopens before B's admission sample. Before expiry B receives ErrOpenState; after expiry B may take the new trial.
2. Observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:330 ("cb.setState(StateOpen, now)"), gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"), gobreaker.go:281 ("state, generation := cb.currentState(now)"), gobreaker.go:284 ("return generation, ErrOpenState"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)").
3. Question Q-10.

### P-05a — ReportSuccess first

1. Closed after a pending report's interval expired. Success callback samples first, clears and drops report; State sees Closed with new expiry.
2. Observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:298 ("state, generation := cb.currentState(now)"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"), gobreaker.go:338 ("cb.toNewGeneration(now)"), gobreaker.go:211 ("state, _ := cb.currentState(now)").
3. Question Q-09.

### P-05b — ReadState first

1. Closed after interval expiry. State clears the generation first. Success callback samples again and drops its old generation.
2. Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:338 ("cb.toNewGeneration(now)"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:299 ("if generation != before {").
3. Question Q-09.

### P-06a — ReportFailure first

1. Expired Open with a callback from prior Closed. Failure callback samples first, advances Open to HalfOpen, drops old accounting; observer returns HalfOpen.
2. Observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:298 ("state, generation := cb.currentState(now)"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:211 ("state, _ := cb.currentState(now)").
3. Question Q-09.

### P-06b — ReadState first

1. Expired Open. Reader first advances to HalfOpen. Stale failure later skips accounting and HalfOpen remains.
2. Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:299 ("if generation != before {").
3. Question Q-09.

### P-07a — ReportSuccess first

1. Closed with one pending admission. Matching success commits under lock; Counts then returns one success.
2. Observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:304 ("cb.onSuccess(state, now)"), gobreaker.go:313 ("cb.counts.onSuccess()"), gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:220 ("return cb.counts").
3. none — control trace.

### P-07b — ReadCounts first

1. Closed with one pending admission. Counts first returns one admission and zero successes; success later commits.
2. Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:220 ("return cb.counts"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:313 ("cb.counts.onSuccess()").
3. Question Q-19.

### P-08a — ReportFailure first

1. Closed with trip policy true. Report failure commits and clears before a Counts read. Counts returns zero even though a failure was counted in the previous generation.
2. Observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:325 ("cb.counts.onFailure()"), gobreaker.go:327 ("cb.setState(StateOpen, now)"), gobreaker.go:365 ("cb.counts.clear()"), gobreaker.go:220 ("return cb.counts").
3. Question Q-19.

### P-08b — ReadCounts first

1. Closed. Counts snapshots before the failure increments and trips. After the trip, fresh Counts is cleared.
2. Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:220 ("return cb.counts"), gobreaker.go:325 ("cb.counts.onFailure()"), gobreaker.go:327 ("cb.setState(StateOpen, now)"), gobreaker.go:365 ("cb.counts.clear()").
3. Question Q-19.

### P-09a — ReadState first

1. Closed with expired interval and nonzero counts. State samples and clears, then Counts returns zero.
2. Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"), gobreaker.go:338 ("cb.toNewGeneration(now)"), gobreaker.go:365 ("cb.counts.clear()"), gobreaker.go:220 ("return cb.counts").
3. Question Q-05.

### P-09b — ReadCounts first

1. Closed with expired interval. Counts returns old snapshot; State then clears under its lock.
2. Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:220 ("return cb.counts"), gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"), gobreaker.go:338 ("cb.toNewGeneration(now)").
3. Question Q-05.

### P-10a — RequestResult first

1. Closed with one admission. The workload can return an error, pause in classification, and a reader can still see Closed before the failure commits and trips.
2. Observed-in-code gobreaker.go:242 ("result, err := req()"), gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:327 ("cb.setState(StateOpen, now)").
3. Question Q-13.

### P-10b — ReadState first

1. Closed with work pending. Reader sees Closed, then workload returns a failing result and accounting can open the breaker.
2. Observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:242 ("result, err := req()"), gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:327 ("cb.setState(StateOpen, now)").
3. Question Q-13.

### P-11a — Classify first

1. Closed with interval crossing. Classifier returns but completion has not acquired the lock. Reader may clear; completion resamples and drops its now-stale result.
2. Observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:338 ("cb.toNewGeneration(now)"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:299 ("if generation != before {").
3. Question Q-09.

### P-11b — ReadState first

1. Closed with interval elapsed. Reader clears while A is blocked in classification. A eventually returns and afterRequest finds a stale generation.
2. Observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:338 ("cb.toNewGeneration(now)"), gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:299 ("if generation != before {").
3. Question Q-09.

### P-12a — Allow first

1. Expired Open. Allow samples first, promotes and admits in one locked visit, then returns a callback. Reader sees HalfOpen. A failing notification can abort before admission.
2. Observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:281 ("state, generation := cb.currentState(now)"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:211 ("state, _ := cb.currentState(now)").
3. Question Q-07.

### P-12b — ReadState first

1. Expired Open. Reader promotes before Allow, which then sees HalfOpen, acquires capacity, and returns a callback. A notification panic in State escapes there; a later Allow may still admit.
2. Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)").
3. Question Q-07.

### P-13a — Allow first

1. HalfOpen below limit. Allow increments Requests before returning the closure. Counts can see the new Requests even before the caller receives the closure.
2. Observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:278 ("defer cb.mutex.Unlock()"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:290 ("return generation, nil"), gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:220 ("return cb.counts").
3. Question Q-19.

### P-13b — ReadCounts first

1. HalfOpen below limit. Counts takes its snapshot before Allow increments Requests. Later read can observe the admission.
2. Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:220 ("return cb.counts"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:289 ("cb.counts.onRequest()").
3. Question Q-19.

### P-14a — ReportSuccess first

1. HalfOpen with two admissions and MaxRequests 2. A's success counts one; B's failure then opens and clears.
2. Observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:315 ("cb.counts.onSuccess()"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"), gobreaker.go:330 ("cb.setState(StateOpen, now)"), gobreaker.go:365 ("cb.counts.clear()").
3. Question Q-10.

### P-14b — ReportFailure first

1. Same start. B's failure opens, then A's success becomes stale and cannot close the breaker.
2. Observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:330 ("cb.setState(StateOpen, now)"), gobreaker.go:365 ("cb.counts.clear()"), gobreaker.go:299 ("if generation != before {").
3. Question Q-10.

### P-15a — TripDecision first

1. Closed with pending failure. ReadyToTrip runs under completion lock. Separate State waits while policy runs, then sees Open after commit, or Closed if policy returns false. Reentrant State cannot get the lock.
2. Observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:325 ("cb.counts.onFailure()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:327 ("cb.setState(StateOpen, now)"), gobreaker.go:207 ("cb.mutex.Lock()").
3. Question Q-02.

### P-15b — ReadState first

1. Closed with outstanding work. State first observes Closed; completion then locks, updates failure count, and invokes policy. State has already returned.
2. Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:325 ("cb.counts.onFailure()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").
3. none — control trace.

### T-01 — Duplicate completion

1. HalfOpen with MaxRequests 2 → Allow once → invoke the same true result twice → second invocation closes with only one admitted request. Concurrent true reports serialize and can do the same. A false report can instead reopen and invalidate a following true.
2. Observed-in-code gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:315 ("cb.counts.onSuccess()"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"), gobreaker.go:330 ("cb.setState(StateOpen, now)").
3. Question Q-03.

### T-02 — Abandoned half-open trial

1. HalfOpen at limit one → retain callback without calling it → further Allow returns ErrTooManyRequests each time. No input leaves the budget consumed. A later true closes, while a later false reopens. Application teardown does not invalidate the callback.
2. Observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:286 ("return generation, ErrTooManyRequests"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:317 ("cb.setState(StateClosed, now)"), gobreaker.go:330 ("cb.setState(StateOpen, now)"), gobreaker.go:378 ("cb.expiry = zero").
3. Question Q-04.

### T-03 — Execute twice while pending

1. Closed. The same application launches Execute A in a goroutine, which admits and waits in work. It starts B on the same breaker below capacity. B admits and returns before A. Both calls own their own results, Requests increments twice, and neither waits for handoff. In HalfOpen at capacity B is refused; below capacity B may enter and finish before A.
2. Observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"), gobreaker.go:242 ("result, err := req()"), gobreaker.go:244 ("return result, err"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:286 ("return generation, ErrTooManyRequests"), gobreaker.go:289 ("cb.counts.onRequest()").
3. Question Q-15.

### T-04 — Execute again while retaining result

1. A returns a value, then the caller retains it and calls Execute B. The breaker does not track payload ownership or a release. B goes through current state admission independently.
2. Observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"), gobreaker.go:244 ("return result, err"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:289 ("cb.counts.onRequest()").
3. Question Q-15.

### T-05 — Allow twice while first pending

1. A and B are issued in separate goroutines by one caller. A can hold admission mutex before return; B waits and checks after A increments. With limit one B rejects, with limit two both admit. B may receive its closure or report ahead of A after A unlocks. A report completes only its own capability by convention; implementation stores no per-attempt identity.
2. Observed-in-code gobreaker.go:265 ("func (tscb *TwoStepCircuitBreaker) Allow() (done func(success bool), err error) {"), gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"), gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:278 ("defer cb.mutex.Unlock()"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:289 ("cb.counts.onRequest()").
3. Question Q-15.

### T-06 — Allow again while holding first result

1. With max two, A receives and holds callback, then B requests independently and can report first. A single B report consumes one outcome only, and Requests remains two. With max one, second admission rejects at equality. Later A report true can close or false can reopen.
2. Observed-in-code gobreaker.go:265 ("func (tscb *TwoStepCircuitBreaker) Allow() (done func(success bool), err error) {"), gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:315 ("cb.counts.onSuccess()"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"), gobreaker.go:330 ("cb.setState(StateOpen, now)").
3. Question Q-15.

### T-07 — State notification reentry

1. A result trips the breaker, state is set and counts are reset under completion lock. Hook calls Counts and blocks at the same mutex. Original call waits inside hook. A separate API caller that needs the mutex also waits.
2. Observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:295 ("defer cb.mutex.Unlock()"), gobreaker.go:354 ("cb.state = state"), gobreaker.go:356 ("cb.toNewGeneration(now)"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"), gobreaker.go:217 ("cb.mutex.Lock()").
3. Question Q-01.

### T-08 — Trip policy reentry

1. Failure increments first. Policy calls Counts with the completion lock held and blocks; policy cannot commit its decision and neither caller nor other admissions progress. Name is lock-free.
2. Observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:295 ("defer cb.mutex.Unlock()"), gobreaker.go:325 ("cb.counts.onFailure()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:202 ("return cb.name").
3. Question Q-02.

### T-09 — Callback failures around commit

1. Classifier panic before accounting is counted as failure by Execute recovery; a policy panic after failure increment can cause another same-generation increment. A notification panic after state commit preserves the new state and cleared counts. On request panic, a later policy or hook panic during recovery wins.
2. Observed-in-code gobreaker.go:234 ("defer func() {"), gobreaker.go:235 ("e := recover()"), gobreaker.go:237 ("cb.afterRequest(generation, false)"), gobreaker.go:238 ("panic(e)"), gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:295 ("defer cb.mutex.Unlock()"), gobreaker.go:325 ("cb.counts.onFailure()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:354 ("cb.state = state"), gobreaker.go:356 ("cb.toNewGeneration(now)"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").
3. Question Q-07.

### T-10 — Idle expiry and stale observing callback

1. Closed admits two callbacks. One trips Open; wait beyond deadline, then Counts leaves it untouched. Stale success or failure can be the first caller to advance to HalfOpen before returning without counting.
2. Observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:220 ("return cb.counts"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:298 ("state, generation := cb.currentState(now)"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)").
3. Question Q-09.

### T-11 — Classifier crossing a reset

1. Old Execute returns its raw error and blocks in IsSuccessful. New Execute trips and clears. Resume classifier success or failure. Execute still returns its raw result and generation check drops either accounting outcome.
2. Observed-in-code gobreaker.go:242 ("result, err := req()"), gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:244 ("return result, err"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:327 ("cb.setState(StateOpen, now)"), gobreaker.go:365 ("cb.counts.clear()").
3. Question Q-09.

### T-12 — Runtime exit and no retry

1. Work calls Goexit. Execute's deferred recover returns nil, so no outcome is entered; no retry or completion is scheduled. Closed count shows an admission only. A HalfOpen trial would continue to occupy a slot.
2. Observed-in-code gobreaker.go:234 ("defer func() {"), gobreaker.go:235 ("e := recover()"), gobreaker.go:236 ("if e != nil {"), gobreaker.go:237 ("cb.afterRequest(generation, false)"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:378 ("cb.expiry = zero").
3. Question Q-20.

### T-13 — Replacement and wrong instance

1. A worker holds A's closure. Caller constructs B and accidentally invokes A's closure when B's work ends. A alone can update or discard according to its generation; B's occupancy remains.
2. Observed-in-code gobreaker.go:142 ("cb := new(CircuitBreaker)"), gobreaker.go:265 ("func (tscb *TwoStepCircuitBreaker) Allow() (done func(success bool), err error) {"), gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:299 ("if generation != before {").
3. Question Q-16.

### T-14 — Deadline equality

1. At exact sampled equality Open stays Open; with nonzero Closed expiry, equality preserves counts. One representable tick later a qualifying call can advance/reset. State, admission and completion take the sample only under the lock.
2. Observed-in-code gobreaker.go:210 ("now := time.Now()"), gobreaker.go:280 ("now := time.Now()"), gobreaker.go:297 ("now := time.Now()"), gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"), gobreaker.go:341 ("if cb.expiry.Before(now) {").
3. Question Q-05.

### T-15 — Oversized counters

1. Closed with interval disabled accumulates more than the uint32 range under successful load. Wrap of successful admissions and successes is given by field type and increments. No large runtime loop was used.
2. Observed-in-code gobreaker.go:48 ("Requests             uint32"), gobreaker.go:56 ("c.Requests++"), gobreaker.go:60 ("c.TotalSuccesses++"), gobreaker.go:370 ("if cb.interval == 0 {").
3. Question Q-12.

### T-16 — Cross-method snapshot

1. Expired Closed with old counts: Counts can return old snapshot, State resets, then Counts sees empty. Each call is safe under lock; caller should decide if that observation is sufficient.
2. Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:220 ("return cb.counts"), gobreaker.go:338 ("cb.toNewGeneration(now)"), gobreaker.go:365 ("cb.counts.clear()").
3. Question Q-19.

### T-17 — New call waits before refusal

1. One result trips Open and blocks in OnStateChange. A competing Execute tries the mutex and cannot even sample state. Once hook returns, new sample can reject with ErrOpenState or admit after timeout. Request body never runs on rejection.
2. Observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"), gobreaker.go:231 ("return nil, err"), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:280 ("now := time.Now()"), gobreaker.go:284 ("return generation, ErrOpenState"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").
3. Question Q-06.

### T-18 — Bad request versus missing capability

1. A nil Execute function in Closed is admitted and panics at invocation; Open refusal skips the invocation. Invoking nil done after Allow refusal panics at the caller; fabricated Boolean on a valid closure is accepted for its bound generation.
2. Observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"), gobreaker.go:231 ("return nil, err"), gobreaker.go:237 ("cb.afterRequest(generation, false)"), gobreaker.go:242 ("result, err := req()"), gobreaker.go:268 ("return nil, err"), gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)").
3. Question Q-08.

## Shared downstream

### M-01 — Aligned retry waves

1. Four breakers trip together after the same downstream failure. Wait past their equal Open durations, then release four concurrent call attempts. Each admits its first HalfOpen trial. All fail and reopen. Repeat through three cycles; aggregate admitted work is four per cycle in the executable probe.
2. Observed-in-code gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:330 ("cb.setState(StateOpen, now)"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). Probe TestPilotSharedRecoveryWaves.
3. Q-11.

### M-02 — Same bounds and repeated recovery

1. N breakers have the same Timeout and observe failure together. At a shared traffic tick after timeout all enter HalfOpen and spend individual budgets. Repeat after each common failure for three cycles. Up to N × MaxRequests can enter each wave if sufficient callers arrive before outcomes close or reopen the breakers. Random seed does not enter the expiry calculation.
2. Inferred aggregate from each instance's observed-in-code branches gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:330 ("cb.setState(StateOpen, now)"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").
3. Q-11.

### M-03 — Partial recovery and successive resets

1. Shared downstream recovers partially. A has a successful trial and closes, removing its local HalfOpen admission bound. It contributes unrestricted Closed admissions despite B still limiting or refusing. B subsequently closes after successful trials and adds Closed load. Within three repeated recovery and failure cycles synchronized traffic can amplify load; effect size depends on arrivals and trip policies.
2. Inferred aggregate from observed-in-code admission and recovery gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"), gobreaker.go:317 ("cb.setState(StateClosed, now)"), gobreaker.go:327 ("cb.setState(StateOpen, now)").
3. Q-11.

## Requirement checks

### T-30 — Requirement scope check O01

A constructed Closed breaker accepts an Execute request → caller supplies a request → Execute runs the given request.

Explicit-requirement README.md:87 ("The method `Execute` runs the given request if `CircuitBreaker` accepts it.").

- cited text contemplates this ordering: no
- jev: unclear, scope 0.02
- Verdict: Q-21. The submitted assertion places acceptance before supplying the function, while Execute receives the function first. The source describes what Execute does with an accepted call. The original answered check is retained and was not repeated.

### T-31 — Requirement scope check O02

A constructed breaker rejects the request → caller invokes Execute → Execute returns an error instantly.

Explicit-requirement README.md:88 ("`Execute` returns an error instantly if `CircuitBreaker` rejects the request.").

- cited text contemplates this ordering: yes
- jev: supported, scope 0.33
- Verdict: Control verdict void under routing rule 5. Q-06.

### T-32 — Requirement scope check O03

A request was sent before a count clear → it completes after the clear → its result does not affect the cleared Counts.

Explicit-requirement README.md:79 ("Counts` ignores the results of the requests sent before clearing.").

- cited text contemplates this ordering: yes
- jev: unclear, scope 0.18
- Verdict: Control verdict void under routing rule 5. Q-22.

### T-33 — Requirement scope check O04

An idle Open breaker has no State, admission or completion calls → time is exactly at the timeout deadline → state changes autonomously and immediately to HalfOpen.

Explicit-requirement README.md:50 ("after which the state of `CircuitBreaker` becomes half-open.").

- cited text contemplates this ordering: no
- jev: unclear, scope 0.01
- Verdict: Citation omits material timing or lock order. Q-05.

### T-34 — Requirement scope check O05

A breaker changes state with nonnil OnStateChange → state and counts are committed while the breaker holds its mutex → callback runs inside the same lock and returns before public calls can proceed.

Explicit-requirement README.md:58 ("`OnStateChange` is called whenever the state of `CircuitBreaker` changes.").

- cited text contemplates this ordering: no
- jev: unclear, scope 0.01
- Verdict: Citation omits material timing or lock order. Q-01.

