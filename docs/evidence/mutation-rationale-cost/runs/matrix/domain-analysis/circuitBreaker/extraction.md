# Extraction

Scope is in [scope.md](scope.md). One constructed instance starts Closed (the zero enum), then explicitly initializes a generation. No internal goroutine, timer channel or lifecycle stop handle exists in the breaker. observed-in-code gobreaker.go:17 ("StateClosed State = iota"). gobreaker.go:177 ("cb.toNewGeneration(time.Now())"). gobreaker.go:334 ("func (cb *CircuitBreaker) currentState(now time.Time) (State, uint64) {").

## Reachable combinations and effects

- Closed has interval disabled with zero expiry or positive interval with a stored deadline. Each can have no work, outstanding work, or completed work. With an interval, the stored generation can be due but unreconciled. Open has a deadline, can have old outstanding work, and has no current admissions. HalfOpen has no expiry and can have spare admission budget or full budget. Full budget can coexist with pending or abandoned work. Because reports can repeat, reported outcomes need not correspond one-to-one with admissions. Public State reports the same enum for both half-open conditions. observed-in-code gobreaker.go:285 ("cb.counts.Requests >= cb.maxRequests"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:315 ("cb.counts.onSuccess()"). gobreaker.go:370 ("if cb.interval == 0 {"). gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). gobreaker.go:378 ("cb.expiry = zero").
- Constructor normalizes zero max to one, nonpositive interval to zero, nonpositive timeout to sixty seconds, and nil policies to defaults. Name and callbacks are fixed after publication for supported calls. Settings is passed by value and function values may capture mutable state. observed-in-code gobreaker.go:144 ("cb.name = st.Name"). gobreaker.go:148 ("cb.maxRequests = 1"). gobreaker.go:154 ("cb.interval = defaultInterval"). gobreaker.go:160 ("cb.timeout = defaultTimeout"). gobreaker.go:166 ("cb.readyToTrip = defaultReadyToTrip"). gobreaker.go:172 ("cb.isSuccessful = defaultIsSuccessful"). gobreaker.go:190 ("const defaultTimeout = time.Duration(60) * time.Second").
- Execute and Allow call admission. It locks, samples time, reconciles current state, produces ErrOpenState or ErrTooManyRequests if gated, otherwise increments Requests and returns a generation. The comparison is at-or-over; the ErrTooManyRequests comment says over. Execute calls the request and classifier outside the mutex then accounts, returning original result and error. Allow returns a generation-bound callback that may run later or multiple times and bypasses the error classifier. observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"). gobreaker.go:242 ("result, err := req()"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:285 ("cb.counts.Requests >= cb.maxRequests"). gobreaker.go:289 ("cb.counts.onRequest()").
- Outcome locks, refreshes time, checks generation and applies the success bit. Success increments both success counts and resets consecutive failures. Closed failure increments both failure counts and resets consecutive successes before evaluating ReadyToTrip on a value copy. Default threshold is greater than five. A HalfOpen failure reopens and clears rather than recording a lasting failure; reaching the success threshold closes and clears. A live Open outcome cannot originate through normal admission in its own generation. observed-in-code gobreaker.go:60 ("c.TotalSuccesses++"). gobreaker.go:62 ("c.ConsecutiveFailures = 0"). gobreaker.go:66 ("c.TotalFailures++"). gobreaker.go:68 ("c.ConsecutiveSuccesses = 0"). gobreaker.go:193 ("return counts.ConsecutiveFailures > 5"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:330 ("cb.setState(StateOpen, now)").
- State can reconcile time; Counts snapshots stored counters and Name reads immutable setting. Event-triggered refresh starts a new window at the sampled instant, skips catch-up periods, and excludes equality. Reset increments generation and clears all counts; state notification follows commit under the caller's mutex. No per-request identity, queue, once wrapper, cancellation or resource release call exists. observed-in-code gobreaker.go:202 ("return cb.name"). gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). gobreaker.go:341 ("if cb.expiry.Before(now) {"). gobreaker.go:354 ("cb.state = state"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). gobreaker.go:364 ("cb.generation++"). gobreaker.go:365 ("cb.counts.clear()"). gobreaker.go:373 ("cb.expiry = now.Add(cb.interval)").
- Normal return, input panic, policy panic, same-thread callback reentry, blocked request and Goexit have distinct failure outcomes. Execute only registers recovery after successful admission; the recovery scope includes classifier and accounting. Failure accounting can itself panic before the original panic is rethrown. No system retry of request work. observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"). gobreaker.go:234 ("defer func() {"). gobreaker.go:235 ("e := recover()"). gobreaker.go:237 ("cb.afterRequest(generation, false)"). gobreaker.go:238 ("panic(e)"). gobreaker.go:295 ("defer cb.mutex.Unlock()"). Questions Q-06, Q-09, Q-10 and Q-15.
- Test replay appears in as-is-validation.md. The core docs omit half-open exits, observer-triggered time reconciliation, one-report semantics and callback contract details. README.md:47 and README.md:51 specify zero; the Settings comment and constructor extend both defaults to negative values. The instant-refusal wording leaves the mutex timing undefined. The same-panic wording can fail when notification panics during panic accounting. Questions Q-01 through Q-17 index the gaps and observations.

## Callee contracts and environment assumptions

- Request function signature admits normal value/error; Execute docstring explicitly covers request panic. It provides no contract for timeout, cancellation, blocking, side effects or Goexit. NAT-2 and Q-06/Q-10. observed-in-code gobreaker.go:223-227 ("If a panic occurs in the request, the CircuitBreaker handles it as an error").
- ReadyToTrip receives a value copy on closed failure and true opens. Its contract is silent on panic, reentry, concurrency and completion deadlines. NAT-2 and Q-09/Q-10. observed-in-code gobreaker.go:95 ("// ReadyToTrip is called with a copy of Counts whenever a request fails in the closed state.").
- IsSuccessful receives ordinary returned error and returns a Boolean. User implementation gives no panic or deadline guarantee. No concurrency safety requirement is documented. NAT-2 and Q-10/Q-16. observed-in-code gobreaker.go:102 ("// IsSuccessful is called with the error returned from a request.").
- OnStateChange promises delivery on state change; there is no error or acknowledgment return and no reentrancy or deadline guarantee. NAT-2 and Q-09/Q-12. observed-in-code gobreaker.go:100 ("// OnStateChange is called whenever the state of CircuitBreaker changes.").
- Allow's reporting contract and lack of idempotency, ownership or cancellation semantics are NAT-2 gaps, Q-03/Q-06/Q-13. observed-in-code gobreaker.go:262 ("// Allow checks if a new request can proceed. It returns a callback that should be used to").
- Go sync.Mutex blocks an already locked caller and documents unlock-to-lock synchronization and no copying after first use. Go SDK src/sync/mutex.go:20 ("// A Mutex must not be copied after first use."). src/sync/mutex.go:43 ("// If the lock is already in use, the calling goroutine"). Go SDK src/time/time.go:260 ("// IsZero reports whether t represents the zero time instant,"). src/time/time.go:280 ("// Before reports whether the time instant t is before u."). src/time/time.go:1169 ("// Add returns the time t+d."). src/time/time.go:1346 ("// Now returns the current local time."). Equality is excluded by the comparator's definition and by its implementation. Go SDK src/runtime/panic.go:672 ("// Goexit terminates the goroutine that calls it. No other goroutine is affected."). Deferred calls run with a nil recover value on Goexit. Q-01/Q-06/Q-09/Q-17.
- errors.New creates an error with the supplied text, with identity per call; package initializes two sentinels. Go SDK src/errors/errors.go:62 ("// New returns an error that formats as the given text."). observed-in-code gobreaker.go:24 ("ErrTooManyRequests = errors.New"). The example HTTP call forwards request errors at example/http_breaker.go:30 ("return nil, err"). HTTP and response cleanup remain outside the boundary.
- Draft misses added by the agent include same-caller overlap, past-caller-lifetime outcomes, recovery re-accounting, panic replacement, closed stale snapshot, duplicate accounting, hold exhaustion, exact entry-time notification timing, aggregate load, zero-value distinction and generation wrap. Raw model entries are retained alongside this review.

## README doctrine lines

- DOC-1 — explicit-requirement README.md:18. prevents sending requests likely to fail.
- DOC-2 — explicit-requirement README.md:19. constructor creates a new breaker.
- DOC-3 — explicit-requirement README.md:25. Settings configures breaker.
- DOC-4 — explicit-requirement README.md:39. Name identifies breaker.
- DOC-5 — explicit-requirement README.md:41. MaxRequests caps half-open admission.
- DOC-6 — explicit-requirement README.md:43. Zero MaxRequests allows one.
- DOC-7 — explicit-requirement README.md:45. Closed Interval clears Counts cyclically.
- DOC-8 — explicit-requirement README.md:47. Zero interval disables closed-period clearing.
- DOC-9 — explicit-requirement README.md:49. Open Timeout leads to HalfOpen.
- DOC-10 — explicit-requirement README.md:51. Zero Timeout defaults to sixty seconds.
- DOC-11 — explicit-requirement README.md:53. Closed failure calls ReadyToTrip with copy.
- DOC-12 — explicit-requirement README.md:54. True ReadyToTrip opens.
- DOC-13 — explicit-requirement README.md:55. Nil ReadyToTrip uses default.
- DOC-14 — explicit-requirement README.md:56. Default trips above five consecutive failures.
- DOC-15 — explicit-requirement README.md:58. State change calls OnStateChange.
- DOC-16 — explicit-requirement README.md:60. IsSuccessful receives returned error.
- DOC-17 — explicit-requirement README.md:61. True outcome counts as success.
- DOC-18 — explicit-requirement README.md:62. False outcome counts as failure.
- DOC-19 — explicit-requirement README.md:63. Nil classifier defaults to non-nil-error failure.
- DOC-20 — explicit-requirement README.md:65. Counts holds request and outcome numbers.
- DOC-21 — explicit-requirement README.md:77. State changes and closed intervals clear Counts.
- DOC-22 — explicit-requirement README.md:79. Counts ignores results sent before clearing.
- DOC-23 — explicit-requirement README.md:81. Can wrap any request function.
- DOC-24 — explicit-requirement README.md:87. Execute runs accepted request.
- DOC-25 — explicit-requirement README.md:88. Execute instantly rejects with error.
- DOC-26 — explicit-requirement README.md:89. Otherwise returns original request result.
- DOC-27 — explicit-requirement README.md:90. Handles request panic as error and repanics same value.

## Draft question dispositions

- requirements question 1 — What happens in the half-open state when a request succeeds or fails — what are the transitions and guards? → Q-04.

- requirements question 2 — How are requests counted toward MaxRequests in the half-open state, and is a request that is still in flight counted? → Q-04.

- requirements question 3 — If Interval is non-zero, what exactly is the 'cyclic period' start point (from creation, from entering closed state, or from last clear)? → Q-01.

- requirements question 4 — What happens if ReadyToTrip is non-nil but returns false — is it called on every closed-state failure with no other effect? → answered: gobreaker.go:326; false stays.

- requirements question 5 — Does the default ReadyToTrip count consecutive failures including the current failing request? → answered: gobreaker.go:325; current failure counted before policy.

- requirements question 6 — What error does Execute return when it rejects a request — is it specified? → Q-04/Q-15.

- requirements question 7 — Are the Counts incremented before or after IsSuccessful is consulted, and does a panic count as a failure in Counts? → Q-10/Q-16.

- requirements question 8 — Does Execute count requests whose panics were re-raised toward TotalFailures/ConsecutiveFailures? → Q-10.

- requirements question 9 — When state changes, is OnStateChange called before or after Counts is cleared? → Q-12.

- requirements question 10 — What states exist exactly (closed, open, half-open) and what are the allowed transitions? Source implies but does not enumerate them. → Q-04.

- requirements question 11 — In half-open state, after MaxRequests successes, does the state become closed? Source does not specify. → Q-04.

- requirements question 12 — In half-open state, does a single failure cause transition to open? Source does not specify. → Q-04.

- requirements question 13 — What happens if Interval is set and the state is not closed — are Counts cleared periodically then too? → answered: gobreaker.go:335-344; only Closed has periodic clear.

- requirements question 14 — Is the default ReadyToTrip threshold 'more than 5' meaning 6 or more consecutive failures? → answered: gobreaker.go:193; threshold is strictly more than five.

- requirements question 15 — If IsSuccessful is non-nil, does it also apply to panics that are re-raised? → Q-10/Q-16.

- requirements question 16 — If ReadyToTrip is nil and IsSuccessful is nil, does default ReadyToTrip operate on default success classification? → answered: gobreaker.go:165-172 and 243; both defaults compose.

- requirements question 17 — Does Execute return the nil error and result from a request that panic'd, or re-raise the panic and lose the result? → Q-10.

- requirements question 18 — Are requests executed concurrently and does Counts update atomically? → Q-07/Q-09.

- requirements question 19 — What is the behavior of NewCircuitBreaker when given a Settings with ReadyToTrip referencing Counts — specifically does it copy Settings or store the reference? → Q-16/Q-17.

- source question 1 — Line 89 says if Interval <= 0 the breaker doesn't clear Counts during closed state, but line 154 sets interval to defaultInterval (0) when Interval <= 0; combined with line 370, interval==0 yields a zero expiry. Is the documentation consistent with the behavior, and what happens with a positive Interval exactly at expiry boundary? → Q-01.

- source question 2 — Line 337 checks expiry.Before(now) while line 341 also checks expiry.Before(now); the behavior at expiry == now is unspecified (expiry is considered not expired). Is that intended? → Q-01.

- source question 3 — Line 316 transitions half-open to closed when ConsecutiveSuccesses >= maxRequests. What if maxRequests is larger than the number of requests that will ever be attempted in half-open? It is unspecified whether TotalSuccesses vs ConsecutiveSuccesses is intended, and whether requests exactly at maxRequests in half-open are counted properly. → Q-04/Q-06.

- source question 4 — Line 285 rejects requests in half-open when Requests >= maxRequests; however, Requests includes requests counted since the transition to half-open via toNewGeneration. What if some in-flight requests started in the prior generation and complete in the half-open generation? The generation check at line 299 discards their outcome, so it is ambiguous whether their success/failure affects the half-open counters. → Q-05.

- source question 5 — Line 226 says Execute handles a panic as an error and causes the same panic again; line 237 passes false to afterRequest, which counts it as a failure. What if a panic occurs before req is called or during deferred recover? Also, is a panic in a half-open request always resulting in transition to open? → Q-10.

- source question 6 — Line 262 says Allow returns a callback that should be used to register success or failure; the behavior is unspecified if the callback is never called or called multiple times, or called after the generation changed. → Q-03/Q-05/Q-06.

- source question 7 — Line 358 invokes onStateChange while holding cb.mutex. Is it specified that the callback must not call back into the breaker (which would deadlock)? This is unspecified in the source. → Q-09.

- source question 8 — Line 100 says OnStateChange is called whenever the state changes; is it unspecified whether the callback is invoked for transitions triggered by currentState during a read-only State() call (which can trigger toNewGeneration or setState)? → Q-02/Q-12.

- source question 9 — Line 44 says counts are cleared on state change or at closed-state intervals; is it specified whether clearing at the interval boundary also invokes OnStateChange (no, since toNewGeneration does not call it)? It is ambiguous whether interval-based clearing is considered a state change. → answered: gobreaker.go:338 and 356-359; interval is not enum change.

- source question 10 — defaultReadyToTrip at line 193 uses ConsecutiveFailures > 5, but documented as 'more than 5'; line 98 says the same. Is it intended to trip on the 6th consecutive failure, not the 5th? That is documented but the boundary is worth confirming. → answered: gobreaker.go:193; threshold is strict.

- source question 11 — Line 95 says ReadyToTrip is called whenever a request fails in closed state; but afterRequest at line 299 returns early if generations differ, so ReadyToTrip is not called for stale outcomes. Is it specified whether stale failures should still be considered? → Q-05.

- source question 12 — Line 59 onSuccess and line 65 onFailure update consecutive counters; but the source does not specify what happens when a request is over the half-open maxRequests and gets rejected by beforeRequest (line 285) — rejected requests are not counted as requests or failures. Is that intended? → Q-04.

- source question 13 — Line 43-46 mentions Counts ignores results before clearing; combined with generation checks at line 299, the mechanism is generation-based. The source does not specify whether the generation is comparable across state changes (e.g., closed -> open -> closed increments generation each time). Behavior of stale results across multiple state changes is unspecified. → Q-05/Q-11.

- source question 14 — Line 190 defines defaultTimeout as 60s, and line 93 says Timeout <= 0 uses 60s; but line 159 sets cb.timeout = defaultTimeout. Is there any case where timeout is 0 and expiry is computed as now+0, making the open state immediately half-open? (Only if set directly, which is not exposed.) → answered: gobreaker.go:159-162; initialized timeout positive.

- source question 15 — Line 130 field expiry is time.Time; line 371 sets zero for interval==0 closed. In State() at line 211, calling currentState can mutate via toNewGeneration for closed interval expiry or setState for open. Is it specified whether State() is read-only or can transition? The source shows state transitions in currentState, but this side effect during a getter is unspecified in contract terms. → Q-02.

- source question 16 — Line 228 Execute returns nil, err when beforeRequest rejects (line 231); but the request function is not invoked. Is it specified what the return value is for the result in that case? It returns nil, err. → answered: gobreaker.go:229-232; nil result when refused; timing Q-15.

- source question 17 — Line 143-145 only assign name and onStateChange; maxRequests, interval, timeout, readyToTrip, isSuccessful are assigned conditionally. Is it guaranteed that all fields are initialized before toNewGeneration at line 177? Yes per lines 147-175, but not explicitly stated as an ordering requirement. → answered: gobreaker.go:147-177; initialization before generation.

- source question 18 — Line 26 ErrOpenState is returned when open; line 24 ErrTooManyRequests when half-open over maxRequests. The source does not specify which error takes priority if both conditions could occur (they cannot simultaneously, but state evaluation order in beforeRequest is unspecified beyond line 283 then line 285). → answered: gobreaker.go:283-286; stored modes mutually exclusive.

- source question 19 — Line 348 setState returns early when cb.state == state; but toNewGeneration is not called, so consecutive successes in closed state with a changed generation from interval clearing are not affected. Is the early return's interaction with generation increments specified? → answered: gobreaker.go:349-350; same enum does not reset; interval calls reset directly at 338.

- source question 20 — Line 46 says Counts ignores results before clearing; the mechanism is generation. But if a stale result arrives after a new generation has started and the state is half-open, onSuccess may increment ConsecutiveSuccesses incorrectly? Line 299 prevents it via generation mismatch. However, generation is only incremented on toNewGeneration (line 364); if counts are cleared without incrementing generation somewhere, stale results could be counted. Is the only clearing path always incrementing generation? (clear at line 71 is called from toNewGeneration line 365, which increments first.) Yes, but this invariant is implicit and not stated. → Q-05/Q-11.

- tests question 1 — What are the exact field semantics of Counts (order and meaning of the five fields) — the tests assert tuples but the source does not define them. → answered: gobreaker.go:47-52; field definitions and order.

- tests question 2 — What ReadyToTrip default criterion causes tripping after 6 consecutive failures — the source only asserts the outcome, not the rule. → answered: gobreaker.go:193; default predicate.

- tests question 3 — What is the behavior of Allow/done when called in each state, beyond the succeed2Step/fail2Step helpers? → Q-03/Q-04/Q-06.

- tests question 4 — How are counts handled for the request that trips the breaker (reset timing) versus the tripping request itself? → Q-04/Q-12.

- tests question 5 — Is Execute's panic-recovery behavior specified — does it re-panic after counting the failure, and is there any recovery if done is not called? → Q-06/Q-10.

- tests question 6 — What is the interaction between Interval-based count clearing and a request that began before the interval boundary (generation semantics) in general, not just the tested case? → Q-01/Q-05.

- tests question 7 — What happens for a TwoStepCircuitBreaker when Allow is called in StateOpen/StateHalfOpen at/over MaxRequests — is it the same error as single-step Execute? → Q-04/Q-15.

- tests question 8 — Is OnStateChange invoked synchronously and exactly once per transition; is it invoked before or after counts are reset? → Q-09/Q-12.

- tests question 9 — What is the behavior when IsSuccessful is nil or when it panics? → Q-10/Q-16.

- tests question 10 — Are negative MaxRequests values normalized, and how does MaxRequests apply in StateClosed versus StateHalfOpen? → answered: gobreaker.go:108,147,285; unsigned and only used as admission cap in HalfOpen.

- tests question 11 — Is expiry set/reset at transition into StateClosed and StateHalfOpen precisely (tests assert IsZero in some places and non-zero in others), and what does expiry represent in StateClosed? → Q-01/Q-02.

- tests question 12 — What is the expected behavior when State() is called concurrently or when two goroutines observe a timeout boundary simultaneously? → Q-01/Q-02/Q-09.

## Draft claim review

Corrected source C2 to gobreaker.go:285 ("cb.counts.Requests >= cb.maxRequests"); the comment has different wording and cannot establish the equality case.

Corrected tests C10 with the Closed to Open assertions near gobreaker_test.go:181. The later default transitions and fresh-count assertions are covered by TestDefaultCircuitBreaker replay.

Retained unclear requirements C2 using README.md:19 for construction and gobreaker.go:140 for Settings. Retained source C4/C8/C9/C10/C62 using field/range inspection at gobreaker.go:47-53,59-77,229-244. The claims are compound and individual effects were read separately.

Retained tests C4-C7, C13-C15, C20 and C22 at assertion ranges gobreaker_test.go:126-158,198-213,216-242,267-321,329-342. C15 is conditional on the supplied policy; alternating outcomes alone are insufficient. Tests C25 was contradicted by Jev on the single tuple line. The goroutine count, loop bounds, assertion per returned result and aggregate observation at gobreaker_test.go:374-391 support the stated test result. All other supported drafts were treated as pointers to original text, with provenance from the originals.

## Routed callee checks and second verification pass

- seams-01 — ReadyToTrip receives a copy when a request fails in closed state. gobreaker.go:95 ("// ReadyToTrip is called with a copy of Counts whenever a request fails in the closed state."). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-02 — A true return from ReadyToTrip leads to Open. gobreaker.go:96 ("// If ReadyToTrip returns true, the CircuitBreaker will be placed into the open state."). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-03 — OnStateChange is called when the breaker state changes. gobreaker.go:100 ("// OnStateChange is called whenever the state of the CircuitBreaker changes."). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-04 — IsSuccessful receives the error from an ordinary request return. gobreaker.go:102 ("// IsSuccessful is called with the error returned from a request."). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-05 — A true IsSuccessful result is counted as success. gobreaker.go:103 ("// If IsSuccessful returns true, the error is counted as a success."). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-06 — A false IsSuccessful result is counted as failure. gobreaker.go:104 ("// Otherwise the error is counted as a failure."). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-07 — Allow exposes a callback for the caller to register success or failure separately. gobreaker.go:262 ("// Allow checks if a new request can proceed. It returns a callback that should be used to"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-08 — Disallowed Allow returns an error. gobreaker.go:264 ("// requests, it returns an error."). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-09 — The default classifier returns true exactly when the error is nil. gobreaker.go:197 ("return err == nil"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-10 — The default trip policy returns true above five consecutive failures. gobreaker.go:193 ("return counts.ConsecutiveFailures > 5"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-time-01 — When two time instants are equal, Before returns false. /opt/homebrew/Cellar/go/1.27.3/libexec/src/time/time.go:280 ("// Before reports whether the time instant t is before u."). Jev unclear. Retained using strict time comparison semantics and comparison implementation at time.go:280-286.

- seams-time-02 — IsZero identifies the zero time instant. /opt/homebrew/Cellar/go/1.27.3/libexec/src/time/time.go:260 ("// IsZero reports whether t represents the zero time instant,"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-time-03 — Add returns the time plus the duration. /opt/homebrew/Cellar/go/1.27.3/libexec/src/time/time.go:1169 ("// Add returns the time t+d."). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-time-04 — Now returns the current local time. /opt/homebrew/Cellar/go/1.27.3/libexec/src/time/time.go:1346 ("// Now returns the current local time."). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-sync-01 — A goroutine invoking Lock on an already held Mutex blocks until the mutex is available. /opt/homebrew/Cellar/go/1.27.3/libexec/src/sync/mutex.go:43 ("// If the lock is already in use, the calling goroutine"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-sync-02 — A Mutex must not be copied after first use. /opt/homebrew/Cellar/go/1.27.3/libexec/src/sync/mutex.go:20 ("// A Mutex must not be copied after first use."). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-runtime-01 — Goexit terminates the calling goroutine. /opt/homebrew/Cellar/go/1.27.3/libexec/src/runtime/panic.go:672 ("// Goexit terminates the goroutine that calls it. No other goroutine is affected."). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-runtime-02 — Goexit runs deferred calls before terminating the goroutine. /opt/homebrew/Cellar/go/1.27.3/libexec/src/runtime/panic.go:673 ("// Goexit runs all deferred calls before terminating the goroutine. Because Goexit"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- seams-runtime-03 — Recover from a defer during Goexit returns nil because Goexit is not a panic. /opt/homebrew/Cellar/go/1.27.3/libexec/src/runtime/panic.go:674 ("// is not a panic, any recover calls in those deferred functions will return nil."). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-01 — Admission acquires the mutex before it samples time or evaluates the rejection gate. gobreaker.go:277 ("cb.mutex.Lock()"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-02 — Outcome accounting acquires the mutex before reconciling time. gobreaker.go:294 ("cb.mutex.Lock()"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-03 — State invokes reconciliation and can mutate breaker state or generation. gobreaker.go:211 ("state, _ := cb.currentState(now)"). Jev unclear. Split observe call (211), closed generation mutation (338) and open state mutation (342); all under State lock.

- verify-04 — Counts returns stored counts without checking expiry. gobreaker.go:220 ("return cb.counts"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-05 — Half-open admission rejects at equality with its configured maximum. gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-06 — Admission increments Requests before delivering a completion callback. gobreaker.go:289 ("cb.counts.onRequest()"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-07 — Every invocation of the returned callback attempts accounting with the same captured generation. gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-08 — Outcome handling reconciles time before checking generation mismatch. gobreaker.go:298 ("state, generation := cb.currentState(now)"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-09 — A stale generation causes the outcome write to be skipped. gobreaker.go:299 ("if generation != before {"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-10 — The classifier runs before the generation check applied by afterRequest. gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). Jev unclear. Retained. Go evaluates cb.isSuccessful(err) as a call argument before the body at 293-299 runs.

- verify-11 — Current half-open success increments success counters. gobreaker.go:315 ("cb.counts.onSuccess()"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-12 — Current half-open success at threshold enters Closed. gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-13 — Current half-open failure enters Open. gobreaker.go:330 ("cb.setState(StateOpen, now)"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-14 — A current closed-state failure increments failure counters before trip policy runs. gobreaker.go:325 ("cb.counts.onFailure()"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-15 — Trip policy runs in the same locked call as failure accounting. gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-16 — Notification executes synchronously while the transition caller holds the lock. gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-17 — State is assigned before notification runs. gobreaker.go:354 ("cb.state = state"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-18 — Generation and counters are reset before notification. gobreaker.go:356 ("cb.toNewGeneration(now)"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-19 — The Execute recover path invokes failure accounting again when outcome handling panics. gobreaker.go:237 ("cb.afterRequest(generation, false)"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-20 — Execute reraises its recovered panic value only if failure accounting returns. gobreaker.go:238 ("panic(e)"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-21 — Admission occurs before Execute installs its recovery defer. gobreaker.go:229 ("generation, err := cb.beforeRequest()"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-22 — A nil request will be invoked if admission succeeded. gobreaker.go:242 ("result, err := req()"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-23 — Execute returns the original result and error regardless of successful classification. gobreaker.go:244 ("return result, err"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-24 — Generation increments on reset as a uint64 field. gobreaker.go:364 ("cb.generation++"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-25 — Requests increments on admission, with no decrement in this method. gobreaker.go:56 ("c.Requests++"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-26 — The returned callback closes over its wrapper and captured generation. gobreaker.go:271 ("return func(success bool) {"). Jev unclear. Retained via the closure body at gobreaker.go:272, naming tscb.cb and generation.

- verify-27 — Each instance sets fixed expiry from a sampled instant plus timeout. gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-28 — Name reads the configured name without acquiring a mutex. gobreaker.go:202 ("return cb.name"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-29 — Open reconciliation waits for a strict Before comparison. gobreaker.go:341 ("if cb.expiry.Before(now) {"). Jev unclear. Retained after re-reading time.go:280-286 and state update at gobreaker.go:342.

- verify-30 — Periodic closed expiry is reanchored to the time of reconciliation. gobreaker.go:373 ("cb.expiry = now.Add(cb.interval)"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

- verify-31 — The TwoStep constructor allocates its own inner breaker. gobreaker.go:185 ("cb: NewCircuitBreaker(st),"). Jev supported. Reviewed with the original call or contract and its local context; scope follows the artifact analysis.

## Executed probe checks

- probe-01 — Two true calls on a single half-open completion can leave the breaker Closed. domain-analysis/circuitBreaker/_probe/pilot_test.go:35 ("t.Fatalf("duplicate success state = %v", got)"). Jev supported. The assertion and its scheduling setup were reviewed against the executed result.

- probe-02 — An omitted completion can leave a half-open breaker rejecting a later call with ErrTooManyRequests. domain-analysis/circuitBreaker/_probe/pilot_test.go:43 ("t.Fatalf("after abandonment: %v", err)"). Jev supported. The assertion and its scheduling setup were reviewed against the executed result.

- probe-03 — Calling a stale report can trigger a HalfOpen notification before another admission. domain-analysis/circuitBreaker/_probe/pilot_test.go:57 ("t.Fatalf("state notifications before any new call: %v", changes)"). Jev supported. The assertion and its scheduling setup were reviewed against the executed result.

- probe-04 — The second Execute can complete and count its result while the first remains pending. domain-analysis/circuitBreaker/_probe/pilot_test.go:82 ("t.Fatalf("counts before first returns: %+v", got)"). Jev contradicted. Retained. The channel closes on first entry, the second Execute returns synchronously, Counts is read while release remains blocked, and a nonblocking receive checks that the first has not returned. The race-enabled overlay passed.

- probe-05 — The probe expects the callback State reentry not to return in its observation window. domain-analysis/circuitBreaker/_probe/pilot_test.go:116 ("t.Fatal("same-goroutine State reentry returned")"). Jev supported. The assertion and its scheduling setup were reviewed against the executed result.

- probe-06 — A policy panic can lead to two closed failure-accounting attempts for one admission. domain-analysis/circuitBreaker/_probe/pilot_test.go:135 ("t.Fatalf("counts=%+v calls=%d", got, calls)"). Jev unclear. Retained. The callback increments calls before throwing and the assertion separately tests Requests, TotalFailures and calls. The race-enabled overlay passed.

- probe-07 — The notification panic replaces the original request panic in this schedule. domain-analysis/circuitBreaker/_probe/pilot_test.go:146 ("if got := recover(); got != "notification" {"). Jev supported. The assertion and its scheduling setup were reviewed against the executed result.

- probe-08 — State Open and zeroed counts remain committed when notification panics. domain-analysis/circuitBreaker/_probe/pilot_test.go:153 ("t.Fatal("transition did not commit")"). Jev unclear. Retained. The checked predicate is the branch immediately above the failure message. It reads public State and Counts after the panic is recovered. The race-enabled overlay passed.

- probe-09 — The first post-expiry Allow can consume the sole half-open slot. domain-analysis/circuitBreaker/_probe/pilot_test.go:182 ("t.Fatalf("second admission after open expiry = %v", err)"). Jev supported. The assertion and its scheduling setup were reviewed against the executed result.
