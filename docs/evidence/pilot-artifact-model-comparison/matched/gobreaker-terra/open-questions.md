# Open questions — preliminary, not consolidated

## Q-01
Question: May ReadyToTrip or OnStateChange call State, Counts, Execute or Allow on the same breaker?
Current behaviour: these callbacks run on a path holding the same mutex (observed-in-code, gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)")); State and Counts also acquire it (gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:217 ("cb.mutex.Lock()")). Re-entry into those methods blocks. The cited README callback descriptions do not state a reentrancy restriction.
Options: allow reentrancy | prohibit and document it | change callback execution contract.
Proposed: specify the callback contract and avoid holding the lock across user code.
Status: OPEN — human decision required
Fault: F-13
Trigger: step-3 lock-discipline annotation

## Q-02
Question: Must the TwoStep completion callback be invoked exactly once, and what should repeated or omitted calls do?
Current behaviour: each invocation calls afterRequest (observed-in-code, gobreaker.go:271 ("return func(success bool) {"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)")). A missing completion leaves the admission count in place until a generation reset; a repeated same-generation completion can count again (gobreaker.go:56 ("c.Requests++"), gobreaker.go:60 ("c.TotalSuccesses++"), gobreaker.go:299 ("if generation != before {")). HalfOpen admissions at the limit are rejected (gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {")).
Options: require exactly once | make repeated calls idempotent | add abandonment semantics.
Proposed: document and enforce an explicit completion policy.
Status: OPEN — human decision required
Fault: F-14
Trigger: step-3 checklist

## Q-03
Question: Should elapsed expiry be reflected in Counts and notifications without a later operation that checks currentState?
Current behaviour: State, admission and completion check expiry; Counts returns the stored counters (gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:220 ("return cb.counts")). README.md:49 ("- `Timeout` is the period of the open state,") does not specify an independent timer or a Counts read ordering.
Options: retain lazy evaluation and document it | refresh on reads | schedule expiry.
Proposed: clarify the observable timing contract.
Status: OPEN — human decision required
Fault: F-13
Trigger: adversarial trace

## Q-04
Question: What should happen when a configured callback blocks or panics, including while recording a request panic?
Current behaviour: callbacks are invoked directly (gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)")); request panic recovery first calls afterRequest (gobreaker.go:237 ("cb.afterRequest(generation, false)")). Callback guarantees are not specified in README.
Options: propagate | recover and report | constrain callbacks.
Proposed: document outcomes for each callback and timing.
Status: OPEN — human decision required
Fault: F-12
Trigger: seam-contract sweep

These questions are preliminary. The draft question lists, doctrine mapping, matrix holes, traces and verification have not been fully reconciled; this is not the required final question set.
