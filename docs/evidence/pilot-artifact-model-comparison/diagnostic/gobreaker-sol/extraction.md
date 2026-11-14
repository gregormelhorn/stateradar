# Scope and extraction

One initialized CircuitBreaker per run, either used directly or through a separately constructed TwoStep wrapper. Actors are admission callers, observers, Execute work and classifier, TwoStep report owners, and the trip and notification callbacks. Clock readings affect the same instance. The breaker owns admission and accounting. The caller owns work, reporting and cancellation. No neighbouring model was supplied. The HTTP example is a client seam; its transport and cancellation policies are outside this boundary. Startup and invalid receivers are boundary variants. State.String formats a value independently of the breaker.

## As-is extraction

- Observed-in-code. Construction starts Closed via the zero enum and starts a generation gobreaker.go:17 ("StateClosed State = iota") gobreaker.go:142 ("cb := new(CircuitBreaker)") gobreaker.go:177 ("cb.toNewGeneration(time.Now())"). Settings are stored per instance. MaxRequests defaults to one, Interval to zero, Timeout to 60 seconds, and nil trip and classification hooks become defaults gobreaker.go:147 ("if st.MaxRequests == 0 {") gobreaker.go:153 ("if st.Interval <= 0 {") gobreaker.go:159 ("if st.Timeout <= 0 {") gobreaker.go:165 ("if st.ReadyToTrip == nil {") gobreaker.go:171 ("if st.IsSuccessful == nil {") gobreaker.go:190 ("const defaultTimeout = time.Duration(60) * time.Second"). OnStateChange remains optional gobreaker.go:145 ("cb.onStateChange = st.OnStateChange").
- Observed-in-code. Closed has zero expiry if interval is disabled and a sampled expiry otherwise. It can have zero or many admissions and outstanding calls. Open has a deadline and zero counters at entry. HalfOpen has zero expiry, with available or exhausted admissions and a success count below the threshold while it remains HalfOpen gobreaker.go:365 ("cb.counts.clear()") gobreaker.go:370 ("if cb.interval == 0 {") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)") gobreaker.go:378 ("cb.expiry = zero") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). Outstanding work from earlier generations can coexist with any state. No request record is kept; the caller or Execute stack holds the generation gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)").
- Observed-in-code. Admission samples clock and refreshes state while holding the mutex, rejects Open or HalfOpen at capacity, otherwise increments Requests and returns the generation gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:280 ("now := time.Now()") gobreaker.go:281 ("state, generation := cb.currentState(now)") gobreaker.go:284 ("return generation, ErrOpenState") gobreaker.go:286 ("return generation, ErrTooManyRequests") gobreaker.go:289 ("cb.counts.onRequest()"). Requests counts admissions, including work that never reports. Completion never decrements it gobreaker.go:303 ("if success {") gobreaker.go:315 ("cb.counts.onSuccess()").
- Observed-in-code. State refreshes expiry, Counts reads the stored counters, Name reads only the name gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:220 ("return cb.counts") gobreaker.go:202 ("return cb.name"). No independent timer invocation appears in the implementation. Strictly after expiry, Closed clears once and re-anchors to sampled time; Open enters HalfOpen. Equal instants stay in the prior generation gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") gobreaker.go:341 ("if cb.expiry.Before(now) {") gobreaker.go:373 ("cb.expiry = now.Add(cb.interval)").
- Observed-in-code. Completion refreshes time before testing equality; stale outcomes skip counters even if their arrival caused a refresh gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:300 ("return"). Current successes and failures update totals and reset the opposite streak gobreaker.go:60 ("c.TotalSuccesses++") gobreaker.go:62 ("c.ConsecutiveFailures = 0") gobreaker.go:66 ("c.TotalFailures++") gobreaker.go:68 ("c.ConsecutiveSuccesses = 0"). Closed failure feeds updated copied Counts to ReadyToTrip gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). Default trips above five gobreaker.go:193 ("return counts.ConsecutiveFailures > 5"). HalfOpen closes on sufficient consecutive successes and reopens on first current failure gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {") gobreaker.go:330 ("cb.setState(StateOpen, now)"). State assignment and clearing precede notification gobreaker.go:354 ("cb.state = state") gobreaker.go:356 ("cb.toNewGeneration(now)") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").
- Observed-in-code. Execute invokes request and classifies the error outside the mutex, returns result and error as supplied after accounting, and reports a recovered non-nil panic as false before re-panicking gobreaker.go:235 ("e := recover()") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:238 ("panic(e)") gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:244 ("return result, err"). A classifier panic can enter the same defer; a callback failure during the deferred accounting can supersede the original panic. Allow reports a Boolean directly, including repeats, with no one-use latch gobreaker.go:271 ("return func(success bool) {") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)").
- Observed-in-code. Request execution, classification and reporting have no cancellation handle or retry loop at this seam gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). No shutdown operation is exposed. Replacing an instance leaves old callbacks bound to their original wrapper gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). Retention cost is unmeasured.
- Inferred. uint32 counter wrap can invalidate ratios or diagnostics in long Closed generations, and uint64 generation wrap can theoretically make an ancient capture compare equal. These are range questions, not observed runtime incidents. See gobreaker.go:48 ("Requests             uint32") gobreaker.go:56 ("c.Requests++") gobreaker.go:128 ("generation uint64") gobreaker.go:364 ("cb.generation++").
- Observed-in-code and explicit-requirement tension. Time-driven prose leaves lazy sampling, exact equality and raw Counts unclear (README.md:45-51,77-79; gobreaker.go:220 ("return cb.counts") gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") gobreaker.go:341 ("if cb.expiry.Before(now) {")). Rejection requires a lock and can wait despite README.md:88. Callback failure can prevent or replace the documented return/panic, README.md:87-91. Negative duration behavior is documented by Settings gobreaker.go:89 ("// If Interval is less than or equal to 0, the CircuitBreaker doesn't clear internal Counts during the closed state.") gobreaker.go:93 ("// If Timeout is less than or equal to 0, the timeout value of the CircuitBreaker is set to 60 seconds.") and implemented in constructor. ErrTooManyRequests comment says “over”; equality rejects gobreaker.go:23 ("// ErrTooManyRequests is returned when the CB state is half open and the requests count is over the cb maxRequests") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {").
- Observed-in-tests. Custom expiry assertion at gobreaker_test.go:247 ("assert.True(t, defaultCB.expiry.IsZero())") reads the default instance while testing custom. TestGeneration exercises explicit State refresh before late success, not a late result that triggers the refresh itself.

## Seam contracts

- NAT-1 Mutex.Lock blocks until the lock becomes available and Unlock synchronizes before a subsequent Lock (installed Go src/sync/mutex.go:23-24,42-44). Lock has no deadline here. Go's Mutex must not be copied after first use (src/sync/mutex.go:20). The injected callback contracts do not give a maximum return time or reentry restriction. Caller-owned request and IsSuccessful can call back into the breaker while unlocked; that does not guarantee that a nested call will succeed.
- NAT-2 Go time.Now returns current local time, Before is strict, Add gives t+d, IsZero tests the zero instant (installed Go src/time/time.go:260-261,280,1169,1346). Time samples usually include a monotonic reading; extreme duration overflow and stripped readings are separate runtime conditions. No callee timeout/error return is specified.
- NAT-3 Execute accepts a caller function and documents its ordinary return and panic (README.md:87-91, gobreaker.go:223 ("// Execute runs the given request if the CircuitBreaker accepts it.")). No cancellation guarantee and no guarantee of a return. ReadyToTrip receives copied counters and supplies a Boolean (gobreaker.go:95 ("// ReadyToTrip is called with a copy of Counts whenever a request fails in the closed state.") gobreaker.go:96 ("// If ReadyToTrip returns true, the CircuitBreaker will be placed into the open state.")). OnStateChange is notified for a transition (gobreaker.go:100 ("// OnStateChange is called whenever the state of the CircuitBreaker changes.")). IsSuccessful classifies an error (gobreaker.go:102 ("// IsSuccessful is called with the error returned from a request.") gobreaker.go:103 ("// If IsSuccessful returns true, the error is counted as a success.")). User callback exceptions, waiting, serialization, and the behavior of a callback which depends on the same breaker are unspecified in these contracts.
- NAT-4 Allow returns an outcome callback only on admission (gobreaker.go:262 ("// Allow checks if a new request can proceed. It returns a callback that should be used to") gobreaker.go:263 ("// register the success or failure in a separate step. If the circuit breaker doesn't allow") gobreaker.go:264 ("// requests, it returns an error.")). The contract does not specify report cardinality, abandonment, or misattribution detection.
- NAT-5 errors.New creates an error with the supplied text (installed Go src/errors/errors.go:62). fmt.Sprintf formats into a returned string (installed Go src/fmt/print.go, String fallback only). Go panic and recover govern stack unwinding and runtime.Goexit runs defers without a recoverable panic (installed Go src/builtin/builtin.go:274-300, src/runtime/panic.go:672-675). Nil-panic behavior depends on Go version and GODEBUG.
- NAT-6 Independent instances can share a failing backend through caller functions. Instance settings have no jitter field gobreaker.go:106 ("type Settings struct {") and open deadlines are based on sampled transition time gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). Correlated load is inferred, with deployment conditions in the traces.

## Doctrine lines

- DOC-1 explicit-requirement README.md:18 ("The struct `CircuitBreaker` is a state machine to prevent sending requests that are likely to fail.")
- DOC-2 explicit-requirement README.md:19 ("The function `NewCircuitBreaker` creates a new `CircuitBreaker`.")
- DOC-3 explicit-requirement README.md:25 ("You can configure `CircuitBreaker` by the struct `Settings`:")
- DOC-4 explicit-requirement README.md:39 ("`Name` is the name of the `CircuitBreaker`.")
- DOC-5 explicit-requirement README.md:41-42 ("`MaxRequests` is the maximum number of requests allowed to pass through when the `CircuitBreaker` is half-open.")
- DOC-6 explicit-requirement README.md:43 ("If `MaxRequests` is 0, `CircuitBreaker` allows only 1 request.")
- DOC-7 explicit-requirement README.md:45-46 ("`Interval` is the cyclic period of the closed state for `CircuitBreaker` to clear the internal `Counts`, described later in this section.")
- DOC-8 explicit-requirement README.md:47 ("If `Interval` is 0, `CircuitBreaker` doesn't clear the internal `Counts` during the closed state.")
- DOC-9 explicit-requirement README.md:49-50 ("`Timeout` is the period of the open state, after which the state of `CircuitBreaker` becomes half-open.")
- DOC-10 explicit-requirement README.md:51 ("If `Timeout` is 0, the timeout value of `CircuitBreaker` is set to 60 seconds.")
- DOC-11 explicit-requirement README.md:53 ("`ReadyToTrip` is called with a copy of `Counts` whenever a request fails in the closed state.")
- DOC-12 explicit-requirement README.md:54 ("If `ReadyToTrip` returns true, `CircuitBreaker` will be placed into the open state.")
- DOC-13 explicit-requirement README.md:55 ("If `ReadyToTrip` is `nil`, default `ReadyToTrip` is used.")
- DOC-14 explicit-requirement README.md:56 ("Default `ReadyToTrip` returns true when the number of consecutive failures is more than 5.")
- DOC-15 explicit-requirement README.md:58 ("`OnStateChange` is called whenever the state of `CircuitBreaker` changes.")
- DOC-16 explicit-requirement README.md:60 ("`IsSuccessful` is called with the error returned from a request.")
- DOC-17 explicit-requirement README.md:61 ("If `IsSuccessful` returns true, the error is counted as a success.")
- DOC-18 explicit-requirement README.md:62 ("Otherwise the error is counted as a failure.")
- DOC-19 explicit-requirement README.md:63 ("If `IsSuccessful` is nil, default `IsSuccessful` is used, which returns false for all non-nil errors.")
- DOC-20 explicit-requirement README.md:65 ("The struct `Counts` holds the numbers of requests and their successes/failures:")
- DOC-21 explicit-requirement README.md:77-78 ("`CircuitBreaker` clears the internal `Counts` either on the change of the state or at the closed-state intervals.")
- DOC-22 explicit-requirement README.md:79 ("`Counts` ignores the results of the requests sent before clearing.")
- DOC-23 explicit-requirement README.md:81 ("`CircuitBreaker` can wrap any function to send a request:")
- DOC-24 explicit-requirement README.md:87 ("The method `Execute` runs the given request if `CircuitBreaker` accepts it.")
- DOC-25 explicit-requirement README.md:88 ("`Execute` returns an error instantly if `CircuitBreaker` rejects the request.")
- DOC-26 explicit-requirement README.md:89 ("Otherwise, `Execute` returns the result of the request.")
- DOC-27 explicit-requirement README.md:90-91 ("If a panic occurs in the request, `CircuitBreaker` handles it as an error and causes the same panic again.")

## Routed extraction review

Each file was independently re-read. README 24/24 claims supported, implementation 43 supported and two unclear, and test source 53 supported and 13 unclear. The citation checker reported zero failures. Draft claims serve as an index; exact source fragments and distinct clauses are checked in the extraction, state and test replay sections.

Implementation C5/C6: keep counter updates, with the separate writes at gobreaker.go:60 ("c.TotalSuccesses++") gobreaker.go:61 ("c.ConsecutiveSuccesses++") gobreaker.go:62 ("c.ConsecutiveFailures = 0") gobreaker.go:66 ("c.TotalFailures++") gobreaker.go:67 ("c.ConsecutiveFailures++") gobreaker.go:68 ("c.ConsecutiveSuccesses = 0"). Test C15/C17/C24/C27/C31/C34/C35/C42/C47/C53/C56/C57/C59: keep test observations after reviewing adjacent setup, preceding request/transition and adjacent assertions in the replay. An isolated assertion is not the full causal ordering. Implementation C2's threshold wording is comment evidence only; the equality branch at gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") controls current behavior. Test C43 does not prove custom expiry is zero; the adjacent assertion uses defaultCB. The independent sweep added lock acquisition timing, callback unwind and Goexit effects, reentrant blocking, duplicate/abandoned reports, exact equality, raw Counts, stale completion refresh, range wrap, and cross-instance assumptions.

### Draft question dispositions

Numbers are one-based indexes in the retained JSON question arrays.

| Source | Draft question | Disposition or fold |
|---|---|---|
| README.md | 1 | fold into Q-21 for the contract and as-is mechanism cited there |
| README.md | 2 | fold into Q-17 for the contract and as-is mechanism cited there |
| README.md | 3 | fold into Q-17 for the contract and as-is mechanism cited there |
| README.md | 4 | fold into Q-17 for the contract and as-is mechanism cited there |
| README.md | 5 | fold into Q-21 for the contract and as-is mechanism cited there |
| README.md | 6 | answered: gobreaker.go:356 and gobreaker.go:365 (all state changes clear; hook ordering separately Q-01) |
| README.md | 7 | fold into Q-01 for the contract and as-is mechanism cited there |
| README.md | 8 | fold into Q-17 for the contract and as-is mechanism cited there |
| README.md | 9 | answered: gobreaker.go:244 (passes nil,nil through; ordinary contract README.md:89) |
| README.md | 10 | fold into Q-19 for the contract and as-is mechanism cited there |
| README.md | 11 | fold into Q-19 for the contract and as-is mechanism cited there |
| README.md | 12 | fold into Q-21 for the contract and as-is mechanism cited there |
| README.md | 13 | fold into Q-01 for the contract and as-is mechanism cited there |
| README.md | 14 | Q-08/Q-09/Q-10 |
| README.md | 15 | Q-05 |
| README.md | 16 | fold into Q-18 for the contract and as-is mechanism cited there |
| README.md | 17 | fold into Q-17 for the contract and as-is mechanism cited there |
| README.md | 18 | fold into Q-17 for the contract and as-is mechanism cited there |
| README.md | 19 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker.go | 1 | answered: gobreaker.go:189 (zero; negative normalization Settings at gobreaker.go:89) |
| gobreaker.go | 2 | fold into Q-18 for the contract and as-is mechanism cited there |
| gobreaker.go | 3 | fold into Q-19 for the contract and as-is mechanism cited there |
| gobreaker.go | 4 | answered: gobreaker.go:243-244 (classify error, pass both through; ordinary contract README.md:60-63,89) |
| gobreaker.go | 5 | fold into Q-04 for the contract and as-is mechanism cited there |
| gobreaker.go | 6 | fold into Q-01 for the contract and as-is mechanism cited there |
| gobreaker.go | 7 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker.go | 8 | fold into Q-05 for the contract and as-is mechanism cited there |
| gobreaker.go | 9 | fold into Q-01 for the contract and as-is mechanism cited there |
| gobreaker.go | 10 | answered: gobreaker.go:189-190,370-378 (disabled closed interval; default open timeout) |
| gobreaker.go | 11 | fold into Q-11 for the contract and as-is mechanism cited there |
| gobreaker.go | 12 | fold into Q-17 for the contract and as-is mechanism cited there |
| gobreaker.go | 13 | fold into Q-17 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 1 | answered: gobreaker.go:193 (default rule explicitly documented README.md:56) |
| gobreaker_test.go | 2 | answered: gobreaker.go:197 (interface nil; README.md:63); typed nil Q-12 |
| gobreaker_test.go | 3 | answered: gobreaker.go:193 (sixth consecutive failure per README.md:56) |
| gobreaker_test.go | 4 | fold into Q-05 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 5 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 6 | answered: gobreaker.go:370-373 (custom interval configured; lazy timing Q-05) |
| gobreaker_test.go | 7 | fold into Q-21 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 8 | Q-03/Q-04 |
| gobreaker_test.go | 9 | answered: gobreaker.go:147-148 (README.md:43) |
| gobreaker_test.go | 10 | answered: gobreaker.go:159-160,190 (Settings covers negative too) |
| gobreaker_test.go | 11 | answered: gobreaker.go:153-154,189 (Settings covers negative too) |
| gobreaker_test.go | 12 | fold into Q-09 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 13 | fold into Q-17 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 14 | fold into Q-17 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 15 | fold into Q-18 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 16 | fold into Q-11 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 17 | answered: gobreaker.go:229-244 (single invocation; any retry policy is caller-owned; Q-11 for termination) |
| gobreaker_test.go | 18 | answered: gobreaker.go:193 and gobreaker_test.go:92 (default and custom separate; Q-17 policy population) |
| gobreaker_test.go | 19 | answered: gobreaker.go:95 and gobreaker_test.go:90 (copy; Q-17 for snapshot population) |
| gobreaker_test.go | 20 | answered: gobreaker.go:243-244 (custom Boolean controls count; return value unchanged; Q-10 for callback failures) |
| gobreaker_test.go | 21 | fold into Q-05 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 22 | outside scope: pseudoSleep is a test helper; public exact-time behavior remains Q-05 |
| gobreaker_test.go | 23 | fold into Q-05 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 24 | fold into Q-02 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 25 | fold into Q-01 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 26 | answered: gobreaker.go:108 (negative MaxRequests unrepresentable) |
| gobreaker_test.go | 27 | Q-15/Q-20 |
| gobreaker_test.go | 28 | answered: gobreaker.go:159-160 (negative duration covered by Settings contract) |
| gobreaker_test.go | 29 | answered: gobreaker.go:153-154 (negative duration covered by Settings contract) |
| gobreaker_test.go | 30 | answered: gobreaker.go:165-166 (default per README.md:55) |
| gobreaker_test.go | 31 | answered: gobreaker.go:171-172 (default per README.md:63) |
| gobreaker_test.go | 32 | answered: gobreaker.go:358 (nil optional; no hook invoked) |
| gobreaker_test.go | 33 | fold into Q-21 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 34 | fold into Q-21 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 35 | answered: gobreaker.go:243-244 (ordinary result and error pass through per README.md:89) |
| gobreaker_test.go | 36 | answered: gobreaker.go:244 (ordinary return per README.md:89) |
| gobreaker_test.go | 37 | fold into Q-19 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 38 | fold into Q-11 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 39 | fold into Q-11 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 40 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 41 | fold into Q-18 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 42 | fold into Q-18 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 43 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 44 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 45 | fold into Q-01 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 46 | fold into Q-02 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 47 | fold into Q-10 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 48 | fold into Q-18 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 49 | outside scope: changing process scheduler settings is a Go runtime action; callback nontermination remains Q-11 |
| gobreaker_test.go | 50 | fold into Q-11 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 51 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 52 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 53 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 54 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 55 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 56 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 57 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 58 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 59 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 60 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 61 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 62 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 63 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 64 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 65 | fold into Q-06 for the contract and as-is mechanism cited there |
| gobreaker_test.go | 66 | fold into Q-06: prior-generation outcome after HalfOpen reopens |

### Jev seam checks

The following claims describe documented guarantees. Reviews retain their conditional scope. Callback termination, panic and reentry gaps remain Q-01/Q-02/Q-03/Q-08/Q-09/Q-10/Q-11/Q-19.

- S1 supported. Execute calls the request when admitted. gobreaker.go:223 ("// Execute runs the given request if the CircuitBreaker accepts it."). Review: contract text supports the stated rule; exceptional callback behavior stays open.
- S2 supported. When it returns normally, Execute returns the request result. gobreaker.go:225 ("// Otherwise, Execute returns the result of the request."). Review: contract text supports the stated rule; exceptional callback behavior stays open.
- S3 supported. Execute documents treating request panic as an error. gobreaker.go:226 ("// If a panic occurs in the request, the CircuitBreaker handles it as an error"). Review: contract text supports the stated rule; exceptional callback behavior stays open.
- S4 supported. Execute documents propagating the same request panic. gobreaker.go:227 ("// and causes the same panic again."). Review: contract text supports the stated rule; exceptional callback behavior stays open.
- S5 supported. ReadyToTrip receives a copy of Counts for a closed-state failure. gobreaker.go:95 ("// ReadyToTrip is called with a copy of Counts whenever a request fails in the closed state."). Review: contract text supports the stated rule; exceptional callback behavior stays open.
- S6 supported. ReadyToTrip true directs the breaker to Open. gobreaker.go:96 ("// If ReadyToTrip returns true, the CircuitBreaker will be placed into the open state."). Review: contract text supports the stated rule; exceptional callback behavior stays open.
- S7 supported. A configured OnStateChange callback receives a notification whenever the breaker changes state. gobreaker.go:100 ("// OnStateChange is called whenever the state of the CircuitBreaker changes."). Review: contract text supports the stated rule; exceptional callback behavior stays open.
- S8 supported. IsSuccessful receives the returned request error. gobreaker.go:102 ("// IsSuccessful is called with the error returned from a request."). Review: contract text supports the stated rule; exceptional callback behavior stays open.
- S9 supported. A true classification counts as success. gobreaker.go:103 ("// If IsSuccessful returns true, the error is counted as a success."). Review: contract text supports the stated rule; exceptional callback behavior stays open.
- S10 supported. A successful Allow gives the caller a callback to report success or failure separately. gobreaker.go:263 ("// register the success or failure in a separate step. If the circuit breaker doesn't allow"). Review: contract text supports the stated rule; exceptional callback behavior stays open.
- S11 supported. Refused Allow returns an error. gobreaker.go:264 ("// requests, it returns an error."). Review: contract text supports the stated rule; exceptional callback behavior stays open.

- stdlib-sync S1 supported. A Mutex must not be copied after first use. Go src/sync/mutex.go:20 ("A Mutex must not be copied after first use."). Review: contract describes the operation; caller timing and callback behavior stay outside the guarantee.
- stdlib-sync S2 supported. A call to Mutex.Lock blocks while the mutex is in use. Go src/sync/mutex.go:43 ("If the lock is already in use"). Review: contract describes the operation; caller timing and callback behavior stay outside the guarantee.
- stdlib-sync S3 supported. Unlock synchronizes before a subsequent Lock. Go src/sync/mutex.go:23 ("synchronizes before"). Review: contract describes the operation; caller timing and callback behavior stay outside the guarantee.
- stdlib-time S1 supported. Time.IsZero tests the zero time instant. Go src/time/time.go:260 ("IsZero reports whether t represents the zero time instant"). Review: contract describes the operation; caller timing and callback behavior stay outside the guarantee.
- stdlib-time S2 supported. Time.Before implements a strict time order. Go src/time/time.go:280 ("Before reports whether the time instant t is before u."). Review: contract describes the operation; caller timing and callback behavior stay outside the guarantee.
- stdlib-time S3 supported. Time.Add returns t+d. Go src/time/time.go:1169 ("Add returns the time t+d."). Review: contract describes the operation; caller timing and callback behavior stay outside the guarantee.
- stdlib-time S4 supported. Time.Now returns the current local time. Go src/time/time.go:1346 ("Now returns the current local time."). Review: contract describes the operation; caller timing and callback behavior stay outside the guarantee.
- stdlib-runtime S1 supported. Goexit terminates the calling goroutine. Go src/runtime/panic.go:672 ("Goexit terminates the goroutine that calls it."). Review: contract describes the operation; caller timing and callback behavior stay outside the guarantee.
- stdlib-runtime S2 supported. Goexit runs deferred calls before termination. Go src/runtime/panic.go:673 ("Goexit runs all deferred calls before terminating the goroutine."). Review: contract describes the operation; caller timing and callback behavior stay outside the guarantee.
- stdlib-errors S1 supported. errors.New returns an error formatting as the supplied text. Go src/errors/errors.go:62 ("New returns an error that formats as the given text."). Review: contract describes the operation; caller timing and callback behavior stay outside the guarantee.

- stdlib-fmt S1 supported. Go src/fmt/print.go:228 ("Sprintf formats according to a format specifier and returns the resulting string."). Review: fallback string formatting only.
- stdlib-builtin S1 supported. Go src/builtin/builtin.go:274 ("The panic built-in function stops normal execution of the current"). Review: standard defer and recover rules apply. Lines 285–300 describe nil-panic runtime compatibility and recover behavior. No runtime version-independent nil payload guarantee is asserted.
