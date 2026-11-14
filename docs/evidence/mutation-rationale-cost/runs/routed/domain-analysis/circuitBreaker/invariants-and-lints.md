# Invariants and lint findings

## Assumptions

- NAT-01. Constructed, uncopied breaker and valid callable work. Observed-in-code constructor gobreaker.go:142 ("cb := new(CircuitBreaker)") and dispatch gobreaker.go:242 ("result, err := req()"). Go sync/mutex.go:20 documents the no-copy constraint. Violations Q-08.
- NAT-02. Every admitted two-step request reports once and truthfully for its own work, and callbacks return normally and promptly. Proposed operating assumptions from the separate report contract at gobreaker.go:262-264 and callback settings at README.md:53-63. Neither delivery nor exactly-once is guaranteed there. Q-01–Q-04, Q-07, Q-13.
- NAT-03. Typed counter and duration domains in check_guards.py. No full-generation wrap assumed for stale-result isolation. The unsigned counters and epoch are observed-in-code gobreaker.go:48 ("Requests             uint32") and gobreaker.go:128 ("generation uint64"). Limits Q-12.
- NAT-SYS. Independently constructed breakers can share one failing downstream. Example topology example/http_breaker.go:27-31 binds a breaker to HTTP workload. Correlated arrival schedules are assumed in M-01–M-03.

## System predicates

- SYS-01. Admitted Execute invokes work, refused Execute does not. Closed admits; Open refuses before expiry; HalfOpen guards admission. Observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"), gobreaker.go:231 ("return nil, err"), gobreaker.go:242 ("result, err := req()"), gobreaker.go:284 ("return generation, ErrOpenState"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {").
- SYS-02. HalfOpen admitted request count is bounded by MaxRequests. Closed unrestricted; Open rejects; HalfOpen forbids increment at equality, including concurrent callers. Observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:286 ("return generation, ErrTooManyRequests"), gobreaker.go:289 ("cb.counts.onRequest()").
- SYS-03. State changes and Closed intervals reset counts. All state entries reset; Closed intervals are lazy and Counts may still show expired values. A periodic/observational reading needs Q-05. Observed-in-code gobreaker.go:220 ("return cb.counts"), gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"), gobreaker.go:338 ("cb.toNewGeneration(now)"), gobreaker.go:356 ("cb.toNewGeneration(now)"), gobreaker.go:365 ("cb.counts.clear()").
- SYS-04. Open progresses after its timeout. Only Open with a qualifying observation strictly beyond expiry enters HalfOpen. Idle transition and equality are unspecified by the README, Q-05. Observed-in-code gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"), gobreaker.go:341 ("if cb.expiry.Before(now) {"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").
- SYS-05. ReadyToTrip sees a copy of the counted Closed failure. Closed generation match increments and calls policy. Open never calls it; HalfOpen failure directly opens. Observed-in-code gobreaker.go:299 ("if generation != before {"), gobreaker.go:325 ("cb.counts.onFailure()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:330 ("cb.setState(StateOpen, now)").
- SYS-06. Configured hook runs on every transition. All three modes use setState for outgoing transitions; same state and interval rollover do not emit. Fault/reentry Q-01 and Q-07. Observed-in-code gobreaker.go:349 ("if cb.state == state {"), gobreaker.go:356 ("cb.toNewGeneration(now)"), gobreaker.go:358 ("if cb.onStateChange != nil {"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").
- SYS-07. Outcome count never exceeds admitted work absent caller spoofing or wrap. Holds under exactly-once and no-wrap assumptions. In Closed a duplicate report can violate; in HalfOpen it can also close early; Open stale outcomes cannot count. Q-03 and Q-12. Observed-in-code gobreaker.go:56 ("c.Requests++"), gobreaker.go:60 ("c.TotalSuccesses++"), gobreaker.go:67 ("c.ConsecutiveFailures++"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {").
- SYS-08. Cleared counts receive no old outcome. Matching generation guard protects all modes after refresh, modulo wrap. Old work may still cause expiry or classify. Q-09, Q-12 and Q-22. Observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:298 ("state, generation := cb.currentState(now)"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:364 ("cb.generation++"), gobreaker.go:365 ("cb.counts.clear()").
- SYS-09. Refusal timing meets the README's instantly language. Open and saturated HalfOpen refusal paths run after lock and any applicable hook, so an unconditional externally observed latency guarantee fails. Closed can contend before admission. Q-06. Observed-in-code gobreaker.go:224 ("// Execute returns an error instantly if the CircuitBreaker rejects the request."), gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:284 ("return generation, ErrOpenState"), gobreaker.go:286 ("return generation, ErrTooManyRequests"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").
- SYS-10. Normal accepted completion returns the original result and error. All modes deliver original payload after counting unless workload or callback interrupts execution. Old work still returns if callbacks finish. Q-07 and Q-09. Observed-in-code gobreaker.go:242 ("result, err := req()"), gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:244 ("return result, err"), gobreaker.go:299 ("if generation != before {").
- SYS-11. An admitted request panic is treated as failure and the same panic escapes. Applies to accepted Closed and HalfOpen and stale work in Open subject to the generation guard. Hook or policy panic can replace it; Goexit and legacy nil case bypass it. Q-07 and Q-20. Observed-in-code gobreaker.go:235 ("e := recover()"), gobreaker.go:237 ("cb.afterRequest(generation, false)"), gobreaker.go:238 ("panic(e)"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

## Lints

- L-01, fault F-20, trigger step-5 lint. HalfOpen has no timeout around admitted work or completion; overload refusal at equality can last indefinitely. Q-04. gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:378 ("cb.expiry = zero").
- L-02, fault F-09, trigger step-5 lint. Neither front end exposes cancellation; caller departure does not free half-open admission. Q-04, Q-09. gobreaker.go:229 ("generation, err := cb.beforeRequest()"), gobreaker.go:265 ("func (tscb *TwoStepCircuitBreaker) Allow() (done func(success bool), err error) {"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)").
- L-03, fault F-03, trigger seam-contract sweep. Injected operation failure and callback panic/reentrancy contracts are incomplete. Q-01, Q-02, Q-07, Q-13. gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").
- L-04, fault F-07, trigger step-5 lint. Caller and breaker lifecycle can disagree after the caller stops, or an old callback outlives application replacement. Q-04, Q-16. gobreaker.go:142 ("cb := new(CircuitBreaker)"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:299 ("if generation != before {").
- L-05, fault F-10, trigger multi-instance probes. Open expiry relaxes refusal across instances and HalfOpen success lifts the remaining cap; no jitter or aggregate budget. Q-11. gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:317 ("cb.setState(StateClosed, now)"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").
- L-06, fault F-22, trigger step-5 lint. Concurrently visible cap refusal can happen while only a subset of admitted trials have completed. Q-10 and Q-15. gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:289 ("cb.counts.onRequest()"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {").
- L-07, fault F-05, trigger step-5 lint. Admission and outcome totals can wrap. Q-12. gobreaker.go:48 ("Requests             uint32"), gobreaker.go:56 ("c.Requests++"), gobreaker.go:60 ("c.TotalSuccesses++").
- Open has refusal diagnostic and a lazy expiry. No terminal lifecycle state, retry loop, internal work queue, destructor, or channel-based task transfer exists in the modeled component. Construction initializes state and counters, and there is no shutdown operation. Observed-in-code gobreaker.go:142 ("cb := new(CircuitBreaker)"), gobreaker.go:177 ("cb.toNewGeneration(time.Now())"), gobreaker.go:244 ("return result, err"), gobreaker.go:265 ("func (tscb *TwoStepCircuitBreaker) Allow() (done func(success bool), err error) {"), gobreaker.go:284 ("return generation, ErrOpenState"), gobreaker.go:365 ("cb.counts.clear()"). Cancellation and caller-owned capability retention remain Q-04, Q-09 and Q-16.

<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 DOC-5 DOC-6 DOC-7 DOC-8 DOC-9 DOC-10 DOC-11 DOC-12 DOC-13 DOC-14 DOC-15 DOC-16 DOC-17 DOC-18 DOC-19 DOC-20 DOC-21 DOC-22 DOC-23 DOC-24 DOC-25 DOC-26 DOC-27 DOC-28 -->

## Doctrine mapping

| Doctrine | Kind | Target |
|---|---|---|
| DOC-1 | structural | Pattern description, represented by the diagram and matrix reachability checker |
| DOC-2 | invariant | SYS-01 |
| DOC-3 | cell | Closed x Configure |
| DOC-4 | cell | Closed x Configure |
| DOC-5 | cell | Closed x ReadName |
| DOC-6 | invariant | SYS-02 |
| DOC-7 | guard | G-01 |
| DOC-8 | invariant | SYS-03 |
| DOC-9 | guard | G-10 |
| DOC-10 | invariant | SYS-04 |
| DOC-11 | guard | G-03 |
| DOC-12 | invariant | SYS-05 |
| DOC-13 | cell | Closed x TripDecision |
| DOC-14 | guard | G-04 |
| DOC-15 | guard | G-08 |
| DOC-16 | invariant | SYS-06 |
| DOC-17 | cell | Closed x Classify |
| DOC-18 | cell | Closed x ApplySuccess |
| DOC-19 | cell | Closed x ApplyFailure |
| DOC-20 | guard | G-05 |
| DOC-21 | invariant | SYS-07 |
| DOC-22 | invariant | SYS-03 |
| DOC-23 | invariant | SYS-08 |
| DOC-24 | structural | Execute function seam represented by the required event column checked by the grid gate |
| DOC-25 | invariant | SYS-01 |
| DOC-26 | invariant | SYS-09 |
| DOC-27 | invariant | SYS-10 |
| DOC-28 | invariant | SYS-11 |
