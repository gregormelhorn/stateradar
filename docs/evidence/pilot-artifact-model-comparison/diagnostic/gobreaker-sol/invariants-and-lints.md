# Invariants and lints

- SYS-1 (proposed predicate from README.md:18,87). Execute only starts caller work after admission. Closed admits, Open before expiry refuses, HalfOpen refuses at the cap. Expiry may change the state before deciding. Observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()") gobreaker.go:231 ("return nil, err") gobreaker.go:242 ("result, err := req()") gobreaker.go:284 ("return generation, ErrOpenState") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). Q-07 covers timing.
- SYS-2 (proposed from README.md:58,77-78). Every state change resets counts then invokes the optional hook. Closed→Open, Open→HalfOpen and both HalfOpen exits all go through setState. Closed interval refresh clears without notification. Observed-in-code gobreaker.go:327 ("cb.setState(StateOpen, now)") gobreaker.go:330 ("cb.setState(StateOpen, now)") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)") gobreaker.go:354 ("cb.state = state") gobreaker.go:356 ("cb.toNewGeneration(now)") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Autonomous time interpretation remains open (Q-05); hook delivery and failure Q-01/Q-09.
- SYS-3 (proposed from README.md:60-63). A current normal Execute outcome follows the classifier. Closed updates both kinds; Open has no current public admissions; HalfOpen success increments and failure reopens before counters are retained. An old outcome is filtered, even if classifier ran. Observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:299 ("if generation != before {") gobreaker.go:303 ("if success {") gobreaker.go:313 ("cb.counts.onSuccess()") gobreaker.go:315 ("cb.counts.onSuccess()") gobreaker.go:330 ("cb.setState(StateOpen, now)"). Q-06/Q-10/Q-17.
- SYS-4 (proposed from README.md:65-74). Outcomes correspond to admitted requests and a request contributes at most one outcome in its generation. Closed and HalfOpen can violate this under repeat Allow reports; Open starts with zero counters. Requests measures admissions, not active work. Observed-in-code gobreaker.go:271 ("return func(success bool) {") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:315 ("cb.counts.onSuccess()") gobreaker.go:365 ("cb.counts.clear()"). Q-03/Q-04/Q-08/Q-15/Q-17.
- SYS-5 (proposed from README.md:79). No older admission mutates outcome counters in the new generation, under non-wrap NAT-4 plus the range assumption. Closed and Open may still refresh before discard; HalfOpen discards mismatches without refresh. Observed-in-code gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") gobreaker.go:341 ("if cb.expiry.Before(now) {"). Q-06/Q-15.
- SYS-6 (proposed from README.md:89-91). An admitted Execute returns its supplied result/error or accounts and propagates its request panic, if user seams return. Same in Closed and HalfOpen; Open before expiry has no admitted work. Earlier admitted work can finish while Open. Callback failure violates unconditional panic/return wording. Observed-in-code gobreaker.go:235 ("e := recover()") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:238 ("panic(e)") gobreaker.go:244 ("return result, err") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Q-08/Q-09/Q-10/Q-19.
- NAT-1–NAT-6 are recorded in extraction. The projections use constructed objects, known enum values, no Mutex copying after use and bounded integer representations. Non-wrap is a separate assumption where used.

## Lint sweep

| Lint | Reviewed result |
|---|---|
| Waiting/connecting/stopping without timeout | HalfOpen has no deadline and caller work has no built-in maximum wait. Q-03/Q-07/Q-11. gobreaker.go:378 ("cb.expiry = zero") gobreaker.go:242 ("result, err := req()") |
| Retry maximum | No retry loop or automatic resubmission in Execute/Allow. A later call is a new admission. gobreaker.go:229 ("generation, err := cb.beforeRequest()") gobreaker.go:242 ("result, err := req()") gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()") |
| External failure outcome | Request panic is normally accounted and propagated; failure paths of the three configured callbacks remain open. Q-08/Q-09/Q-10/Q-19. gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") |
| External cancellation | No breaker cancellation seam; callers can return context errors or abandon reports. Q-03/Q-11/Q-16. gobreaker.go:242 ("result, err := req()") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") |
| Terminal or error diagnostics | Active states are recurrent. Rejections use exported errors; a stale completion has no diagnostic for its skipped accounting. Q-06/Q-21. gobreaker.go:284 ("return generation, ErrOpenState") gobreaker.go:286 ("return generation, ErrTooManyRequests") gobreaker.go:300 ("return") |
| Startup/shutdown | Constructor starts a generation in Closed; no shutdown path or retirement mechanism. Q-13/Q-16/Q-17. gobreaker.go:142 ("cb := new(CircuitBreaker)") gobreaker.go:177 ("cb.toNewGeneration(time.Now())") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") |
| Unbounded queue or overload | No breaker queue, Closed has no cap, and a mutex can block callers. Q-07/Q-15/Q-18. gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:289 ("cb.counts.onRequest()") |
| Synchronized resets | Fixed Open cooldown and transition-relative Closed reset can synchronize under correlated demand. M-01–M-03, Q-14. gobreaker.go:373 ("cb.expiry = now.Add(cb.interval)") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)") |
| Lifecycle disagreement | Caller can leave without ending breaker accounting. At HalfOpen cap this prevents recovery if no outcome ever arrives. Q-03/Q-11. gobreaker.go:271 ("return func(success bool) {") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:378 ("cb.expiry = zero") |
| Dual cleanup | No breaker-owned resource destructor or explicit release. Execute defer only submits an outcome for recoverable panic; normal and deferred reporting can interact if accounting panics. Q-08. gobreaker.go:234 ("defer func() {") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") |
| Async cancellation isolation | Breaker creates no task or channel. User tasks may outlive caller and can still report by holding a closure. Q-11/Q-16. gobreaker.go:242 ("result, err := req()") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") |
| User model | Concurrent admission can reject a seemingly available HalfOpen probe; lock waits and raw Counts can obscure the commit boundary. Q-05/Q-07/Q-18. gobreaker.go:220 ("return cb.counts") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") |

## Doctrine mapping

<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 DOC-5 DOC-6 DOC-7 DOC-8 DOC-9 DOC-10 DOC-11 DOC-12 DOC-13 DOC-14 DOC-15 DOC-16 DOC-17 DOC-18 DOC-19 DOC-20 DOC-21 DOC-22 DOC-23 DOC-24 DOC-25 DOC-26 DOC-27 -->

| Doctrine | Mapping | Target |
|---|---|---|
| DOC-1 | invariant | SYS-1 |
| DOC-2 | structural | Initial Closed edge and Setup cells record allocation |
| DOC-3 | structural | Setup cells and G-01 to G-03 capture configuration |
| DOC-4 | cell | Closed x NameRead |
| DOC-5 | guard | G-04 |
| DOC-6 | guard | G-01 |
| DOC-7 | cell | Closed x Expiry |
| DOC-8 | guard | G-15 |
| DOC-9 | cell | Open x Expiry |
| DOC-10 | guard | G-03 |
| DOC-11 | cell | Closed x TripDecision |
| DOC-12 | cell | Closed x TripDecision |
| DOC-13 | guard | G-11 |
| DOC-14 | guard | G-08 |
| DOC-15 | invariant | SYS-2 |
| DOC-16 | cell | Closed x Classify |
| DOC-17 | invariant | SYS-3 |
| DOC-18 | invariant | SYS-3 |
| DOC-19 | guard | G-09 |
| DOC-20 | invariant | SYS-4 |
| DOC-21 | invariant | SYS-2 |
| DOC-22 | invariant | SYS-5 |
| DOC-23 | constraint | NAT-3 |
| DOC-24 | invariant | SYS-1 |
| DOC-25 | cell | Open x Admission |
| DOC-26 | invariant | SYS-6 |
| DOC-27 | invariant | SYS-6 |

DOC-7/9/21 map to lazy refresh and retain Q-05 for the unresolved deadline scope. DOC-25's instantaneous reading has a reproducible lock path that can wait (Q-07). DOC-27's same-panic guarantee fails if notification raises during deferred accounting (Q-19). DOC-17/18 count matching outcomes subject to DOC-22. DOC-23 relies on the caller seam contract NAT-3 and retains Q-13/Q-11 for invalid functions and termination.
