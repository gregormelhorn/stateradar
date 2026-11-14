# Open questions

Each question remains open for the described ordering. README.md:77–79 (explicit-requirement) addresses discarded counts after a reset. It does not specify notification delivery, hook eligibility, retries, or result delivery in those orderings.

- **F01** Is each completion conventionally single-use, or is repeated reporting supposed to count? (observed-in-code anchor: gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)")).
- **F02** Must closing represent distinct trials, and what is a duplicate report expected to do? (observed-in-code anchor: gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {")).
- **F03** Should an abandoned operation have an expiration or a way to report abandonment? (observed-in-code anchor: gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {")).
- **F04** Should a matching result still decide recovery after its original caller has stopped waiting? (observed-in-code anchor: gobreaker.go:317 ("cb.setState(StateClosed, now)")).
- **F05** Should a late failure reopen the breaker after the caller's departure? (observed-in-code anchor: gobreaker.go:330 ("cb.setState(StateOpen, now)")).
- **F06** Explicit requirement README.md:41–43 gives an admission cap. Should successful completion ever return capacity within that half-open generation? (observed-in-code anchor: gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {")).
- **F07** Explicit requirement README.md:77–79 specifies ignoring pre-clear outcomes in Counts. Is lack of acknowledgement intended, and does ReadyToTrip's failure rule include a stale failure? (observed-in-code anchor: gobreaker.go:299 ("if generation != before {")).
- **F08** Which calls should advance an elapsed open timeout and can stale completion be the trigger? (observed-in-code anchor: gobreaker.go:342 ("cb.setState(StateHalfOpen, now)")).
- **F09** README.md:77–79 covers the count reset and ignored results. Should Counts reflect a rollover before a resolving call, and should an old failure reach ReadyToTrip? (observed-in-code anchor: gobreaker.go:338 ("cb.toNewGeneration(now)")).
- **F10** Should classification run for a stale result, and may the classifier overlap other requests and transitions? (observed-in-code anchor: gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))")).
- **F11** README.md:90–91 covers request panic and rethrow. How does that contract interact with stale failure observers? (observed-in-code anchor: gobreaker.go:237 ("cb.afterRequest(generation, false)")).
- **F12** Should a classifier panic report request failure and replace the normal return pair? (observed-in-code anchor: gobreaker.go:237 ("cb.afterRequest(generation, false)")).
- **F13** Is a failure charge and callback retry intended when ReadyToTrip panics? (observed-in-code anchor: gobreaker.go:325 ("cb.counts.onFailure()")).
- **F14** Which panic should reach the caller, and is prior accounting supposed to remain visible? (observed-in-code anchor: gobreaker.go:238 ("panic(e)")).
- **F15** Should a caller retrying a panicked done invocation repeat accounting, and how should it learn whether the first report committed? (observed-in-code anchor: gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)")).
- **F16** Should callback failure propagate after state is committed, and should any reporting retry be attempted? (observed-in-code anchor: gobreaker.go:356 ("cb.toNewGeneration(now)")).
- **F17** Should fallback after a notification panic advance expiry, and which notification panic should reach the caller? (observed-in-code anchor: gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)")).
- **F18** Should a transition notification panic abort admission after committing the transition? (observed-in-code anchor: gobreaker.go:229 ("generation, err := cb.beforeRequest()")).
- **F19** Should an otherwise stale callback propagate a notification panic, and what should retries mean? (observed-in-code anchor: gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)")).
- **F20** Which methods may callbacks call synchronously on the same breaker? Is lock-held callback execution part of the API contract? (observed-in-code anchor: gobreaker.go:294 ("cb.mutex.Lock()")).
- **F21** What contract, if any, covers termination without returning or panicking after admission? (observed-in-code anchor: gobreaker.go:235 ("e := recover()")).
- **F22** Are reassignment and retained callbacks supported, and should callback lifetime follow the admission or receiver value? (observed-in-code anchor: gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)")).
- **F23** Should a callback verdict after expiry apply to the earlier generation, and what time is the new timeout measured from? (observed-in-code anchor: gobreaker.go:325 ("cb.counts.onFailure()")).
- **F24** Should elapsed interval limit panic fallback, and should the first failure remain visible anywhere? (observed-in-code anchor: gobreaker.go:237 ("cb.afterRequest(generation, false)")).
- **F25** Should a failed notification change what the caller sees when a half-open trial closes or reopens the breaker? (observed-in-code anchor: gobreaker.go:356 ("cb.toNewGeneration(now)")).
- **F26** What, if any, cancellation protocol is expected when the application stops waiting for an admitted request? (observed-in-code anchor: gobreaker.go:242 ("result, err := req()")).
- **F27** Should client abandonment affect reporting or response delivery, or are those decisions entirely the application's responsibility? (observed-in-code anchor: gobreaker.go:244 ("return result, err")).
- **F28** Is the retry expected to be atomic with the original report, and what visibility should the partial count have between them? (observed-in-code anchor: gobreaker.go:295 ("defer cb.mutex.Unlock()")).
- **F29** Is generation wraparound within the supported lifetime bound? (observed-in-code anchor: gobreaker.go:364 ("cb.generation++")).

- **Exact expiry.** Should an operation observing a timestamp exactly equal to the current expiry advance the lifecycle? The code uses strict comparison for each stored state (observed-in-code: gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"), gobreaker.go:341 ("if cb.expiry.Before(now) {")). No exact-equality probe.

- **Counter capacity.** What is the supported operation and reporting volume per closed generation, given the fixed-width admission and accounting counters? (observed-in-code: gobreaker.go:48 ("Requests             uint32"), gobreaker.go:49 ("TotalSuccesses       uint32"), gobreaker.go:50 ("TotalFailures        uint32")).
- **Observation callback failure.** Should a call to State propagate a notification's panic after committing the observed transition? Is retry without notification replay the intended recovery contract? (observed-in-code: gobreaker.go:208 ("defer cb.mutex.Unlock()"), gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:354 ("cb.state = state"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)")).
