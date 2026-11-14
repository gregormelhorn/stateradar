# Adversarial traces

Pair headings describe the observed API or callback order. Attempt order and mutex-commit order can differ. State names refer to the as-is diagram; neither callback body nor admission demand has an independent breaker queue.

### P-01a — Execute → Report

Execute and Allow are separate constructed API forms. A Report cannot be obtained from the same constructed Execute receiver. The cross-form itinerary is structurally excluded; shared implementation has no independent report injection seam.

observed-in-code gobreaker.go:184 ("return &TwoStepCircuitBreaker{"). gobreaker.go:229 ("generation, err := cb.beforeRequest()"). gobreaker.go:271 ("return func(success bool) {").

Question: Q-13.

### P-01b — Report → Execute

Execute and Allow are separate constructed API forms. A Report cannot be obtained from the same constructed Execute receiver. The cross-form itinerary is structurally excluded; shared implementation has no independent report injection seam.

observed-in-code gobreaker.go:184 ("return &TwoStepCircuitBreaker{"). gobreaker.go:229 ("generation, err := cb.beforeRequest()"). gobreaker.go:271 ("return func(success bool) {").

Question: Q-13.

### P-02a — Allow → Report

Start HalfOpen with budget two and one outstanding report. In a, Allow reserves the last slot before the report; failure then opens and ends the newly admitted generation. In b, failure opens first and Allow returns ErrOpenState until expiry.

observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:289 ("cb.counts.onRequest()"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:330 ("cb.setState(StateOpen, now)").

Question: Q-04.

### P-02b — Report → Allow

Start HalfOpen with budget two and one outstanding report. In a, Allow reserves the last slot before the report; failure then opens and ends the newly admitted generation. In b, failure opens first and Allow returns ErrOpenState until expiry.

observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:289 ("cb.counts.onRequest()"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:330 ("cb.setState(StateOpen, now)").

Question: Q-04.

### P-03a — StateRead → Report

Start Closed beyond the interval with a report from that generation. In a State clears before the report locks, in b the report itself clears before validating the captured generation. Both discard accounting. Only the operation owning the lock at observation performs the clear.

observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). gobreaker.go:338 ("cb.toNewGeneration(now)").

Question: Q-05.

### P-03b — Report → StateRead

Start Closed beyond the interval with a report from that generation. In a State clears before the report locks, in b the report itself clears before validating the captured generation. Both discard accounting. Only the operation owning the lock at observation performs the clear.

observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). gobreaker.go:338 ("cb.toNewGeneration(now)").

Question: Q-05.

### P-04a — CountsRead → Report

Start Closed with one current report and no imminent expiry. In a the snapshot returns before the report increments success. In b the returned snapshot includes it. The snapshot locks but never samples time.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:313 ("cb.counts.onSuccess()").

Question: Q-02.

### P-04b — Report → CountsRead

Start Closed with one current report and no imminent expiry. In a the snapshot returns before the report increments success. In b the returned snapshot includes it. The snapshot locks but never samples time.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:313 ("cb.counts.onSuccess()").

Question: Q-02.

### P-05a — StateRead → Execute

Start Open beyond expiry. In a State reconciles and its notification returns before Execute can lock and admit a trial. In b Execute does the same reconciliation before admission, releases the lock, then runs work. State may see HalfOpen while work is pending or Closed after successful completion.

observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:281 ("state, generation := cb.currentState(now)"). gobreaker.go:289 ("cb.counts.onRequest()"). gobreaker.go:242 ("result, err := req()"). gobreaker.go:317 ("cb.setState(StateClosed, now)"). gobreaker.go:342 ("cb.setState(StateHalfOpen, now)").

Question: Q-01.

### P-05b — Execute → StateRead

Start Open beyond expiry. In a State reconciles and its notification returns before Execute can lock and admit a trial. In b Execute does the same reconciliation before admission, releases the lock, then runs work. State may see HalfOpen while work is pending or Closed after successful completion.

observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:281 ("state, generation := cb.currentState(now)"). gobreaker.go:289 ("cb.counts.onRequest()"). gobreaker.go:242 ("result, err := req()"). gobreaker.go:317 ("cb.setState(StateClosed, now)"). gobreaker.go:342 ("cb.setState(StateHalfOpen, now)").

Question: Q-04.

### P-06a — StateRead → Allow

Start Open beyond expiry, budget one. In a State enters HalfOpen, then Allow saturates. In b Allow enters HalfOpen and reserves its slot under one lock, then State returns HalfOpen while the callback remains outstanding. No second slot is admitted. The resulting public state remains HalfOpen while the admission projection is StateHalfOpenSaturated.

observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:289 ("cb.counts.onRequest()"). gobreaker.go:342 ("cb.setState(StateHalfOpen, now)").

Question: Q-01.

### P-06b — Allow → StateRead

Start Open beyond expiry, budget one. In a State enters HalfOpen, then Allow saturates. In b Allow enters HalfOpen and reserves its slot under one lock, then State returns HalfOpen while the callback remains outstanding. No second slot is admitted. The resulting public state remains HalfOpen while the admission projection is StateHalfOpenSaturated.

observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:289 ("cb.counts.onRequest()"). gobreaker.go:342 ("cb.setState(StateHalfOpen, now)").

Question: Q-04.

- Reachability: StateOpen → StateHalfOpenSaturated — domain-analysis/circuitBreaker/_probe/pilot_test.go:182 ("second admission after open expiry = %v")

### P-07a — Execute → RequestReturn

Start HalfOpen with one trial running. Below capacity a new Execute can reserve a slot and finish before the first returns. At capacity it rejects unless the running trial accounts a deciding outcome before admission locks. A raw return alone has no committed effect; classification can delay accounting.

observed-in-code gobreaker.go:242 ("result, err := req()"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:289 ("cb.counts.onRequest()"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:317 ("cb.setState(StateClosed, now)"). gobreaker.go:330 ("cb.setState(StateOpen, now)").

Question: Q-07.

### P-07b — RequestReturn → Execute

Start HalfOpen with one trial running. Below capacity a new Execute can reserve a slot and finish before the first returns. At capacity it rejects unless the running trial accounts a deciding outcome before admission locks. A raw return alone has no committed effect; classification can delay accounting.

observed-in-code gobreaker.go:242 ("result, err := req()"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:289 ("cb.counts.onRequest()"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:317 ("cb.setState(StateClosed, now)"). gobreaker.go:330 ("cb.setState(StateOpen, now)").

Question: Q-07.

### P-08a — StateRead → RequestReturn

Start Closed around the interval boundary. State can clear either before request return or between return and accounting. If accounting locks first beyond expiry it advances generation itself. Original result still comes back.

observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:242 ("result, err := req()"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:244 ("return result, err"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {").

Question: Q-05.

### P-08b — RequestReturn → StateRead

Start Closed around the interval boundary. State can clear either before request return or between return and accounting. If accounting locks first beyond expiry it advances generation itself. Original result still comes back.

observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:242 ("result, err := req()"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:244 ("return result, err"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {").

Question: Q-05.

### P-09a — CountsRead → RequestReturn

With a pending Closed request, snapshot before raw return sees admission only. Snapshot after raw return can still see admission only if classifier pauses before accounting. Snapshot after accounting sees the outcome.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:242 ("result, err := req()"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:313 ("cb.counts.onSuccess()").

Question: Q-02.

### P-09b — RequestReturn → CountsRead

With a pending Closed request, snapshot before raw return sees admission only. Snapshot after raw return can still see admission only if classifier pauses before accounting. Snapshot after accounting sees the outcome.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:242 ("result, err := req()"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:313 ("cb.counts.onSuccess()").

Question: Q-02.

### P-10a — Classify → Notify

Two Execute requests allowed in Closed. One trips while the other classifies. In a classifier can finish before the notification starts but loses accounting if the trip acquired the mutex first. In b it can finish while Notify holds the mutex and then wait; after unlock it is stale.

observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:327 ("cb.setState(StateOpen, now)"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-05.

### P-10b — Notify → Classify

Two Execute requests allowed in Closed. One trips while the other classifies. In a classifier can finish before the notification starts but loses accounting if the trip acquired the mutex first. In b it can finish while Notify holds the mutex and then wait; after unlock it is stale.

observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:327 ("cb.setState(StateOpen, now)"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-05.

### P-11a — Execute → Classify

The prior classifier and new admission run on different goroutines. New admission locks separately. If classifying first, a later admission may still occur before accounting commits; once a failure commits Open the same gate refuses.

observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:284 ("return generation, ErrOpenState"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:327 ("cb.setState(StateOpen, now)").

Question: Q-07.

### P-11b — Classify → Execute

The prior classifier and new admission run on different goroutines. New admission locks separately. If classifying first, a later admission may still occur before accounting commits; once a failure commits Open the same gate refuses.

observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:284 ("return generation, ErrOpenState"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:327 ("cb.setState(StateOpen, now)").

Question: Q-05.

### P-12a — CountsRead → Classify

In a Counts snapshots while the earlier classifier waits. In b suspend after classifier result and before accounting takes the lock: Counts can still return the pre-accounting snapshot.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()").

Question: Q-02.

### P-12b — Classify → CountsRead

In a Counts snapshots while the earlier classifier waits. In b suspend after classifier result and before accounting takes the lock: Counts can still return the pre-accounting snapshot.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()").

Question: Q-02.

### P-13a — StateRead → Classify

A classifier can finish before or after State rolls Closed generation. If State runs between classifier and accounting, outcome is dropped. If accounting commits before expiry, later State clears it.

observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {").

Question: Q-05.

### P-13b — Classify → StateRead

A classifier can finish before or after State rolls Closed generation. If State runs between classifier and accounting, outcome is dropped. If accounting commits before expiry, later State clears it.

observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {").

Question: Q-05.

### P-14a — StateRead → Notify

State can itself observe Open expiry and call Notify before returning. A competing State entered while Notify holds mutex waits. If it is synchronous notification reentry, the same goroutine cannot release the mutex.

observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:208 ("defer cb.mutex.Unlock()"). gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-09.

### P-14b — Notify → StateRead

State can itself observe Open expiry and call Notify before returning. A competing State entered while Notify holds mutex waits. If it is synchronous notification reentry, the same goroutine cannot release the mutex.

observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:208 ("defer cb.mutex.Unlock()"). gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-09.

### P-15a — Execute → TripPolicy

Earlier failure trip policy holds the accounting lock. Execute can admit before that accounting starts, or enqueue for the mutex while policy runs and then see Open if trip is true. A reentrant Execute cannot obtain the lock.

observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:283 ("if state == StateOpen {"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:327 ("cb.setState(StateOpen, now)").

Question: Q-15.

### P-15b — TripPolicy → Execute

Earlier failure trip policy holds the accounting lock. Execute can admit before that accounting starts, or enqueue for the mutex while policy runs and then see Open if trip is true. A reentrant Execute cannot obtain the lock.

observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:283 ("if state == StateOpen {"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:327 ("cb.setState(StateOpen, now)").

Question: Q-15.

### P-16a — Allow → Notify

Before failure notification, Allow may admit in Closed. During notification it waits for mutex; afterward it sees Open and rejects if the deadline is live. If notification lasted beyond expiry, Allow may reconcile to HalfOpen and admit.

observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:281 ("state, generation := cb.currentState(now)"). gobreaker.go:284 ("return generation, ErrOpenState"). gobreaker.go:341 ("if cb.expiry.Before(now) {"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-04.

### P-16b — Notify → Allow

Before failure notification, Allow may admit in Closed. During notification it waits for mutex; afterward it sees Open and rejects if the deadline is live. If notification lasted beyond expiry, Allow may reconcile to HalfOpen and admit.

observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:281 ("state, generation := cb.currentState(now)"). gobreaker.go:284 ("return generation, ErrOpenState"). gobreaker.go:341 ("if cb.expiry.Before(now) {"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-09.

### P-17a — NameRead → Notify

Read Name before notification or from inside it. The configured name is assigned at construction and read without taking the mutex, including through the wrapper.

observed-in-code gobreaker.go:144 ("cb.name = st.Name"). gobreaker.go:202 ("return cb.name"). gobreaker.go:249 ("return tscb.cb.Name()"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Disposition: handle both reads and callback. Question: none — control trace.

### P-17b — Notify → NameRead

Read Name before notification or from inside it. The configured name is assigned at construction and read without taking the mutex, including through the wrapper.

observed-in-code gobreaker.go:144 ("cb.name = st.Name"). gobreaker.go:202 ("return cb.name"). gobreaker.go:249 ("return tscb.cb.Name()"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Disposition: handle both reads and callback. Question: none — control trace.

### P-18a — CountsRead → Execute

Before Execute admission, snapshot excludes it. After the lock releases and while request is blocked, snapshot includes admission without its result. Both commits independently acquire the mutex.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:242 ("result, err := req()"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:289 ("cb.counts.onRequest()").

Question: Q-02.

### P-18b — Execute → CountsRead

Before Execute admission, snapshot excludes it. After the lock releases and while request is blocked, snapshot includes admission without its result. Both commits independently acquire the mutex.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:242 ("result, err := req()"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:289 ("cb.counts.onRequest()").

Question: Q-02.

### P-19a — CountsRead → Allow

Before Allow, snapshot excludes the new admission. After the callback is returned and before it is called, snapshot shows Requests already incremented and outcome unchanged.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). gobreaker.go:271 ("return func(success bool) {"). gobreaker.go:289 ("cb.counts.onRequest()").

Question: Q-02.

### P-19b — Allow → CountsRead

Before Allow, snapshot excludes the new admission. After the callback is returned and before it is called, snapshot shows Requests already incremented and outcome unchanged.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). gobreaker.go:271 ("return func(success bool) {"). gobreaker.go:289 ("cb.counts.onRequest()").

Question: Q-02.

### P-20a — CountsRead → Notify

Counts may snapshot before state change. During Notify it waits, then snapshots committed reset. Synchronous reentry stalls on the same lock.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:354 ("cb.state = state"). gobreaker.go:356 ("cb.toNewGeneration(now)"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-02.

### P-20b — Notify → CountsRead

Counts may snapshot before state change. During Notify it waits, then snapshots committed reset. Synchronous reentry stalls on the same lock.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:354 ("cb.state = state"). gobreaker.go:356 ("cb.toNewGeneration(now)"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-09.

### P-21a — StateRead → TripPolicy

State can return Closed before failed accounting gets the mutex. State during a true trip policy waits, then samples Open or reconciles elapsed Open. Synchronous reentry stalls.

observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:327 ("cb.setState(StateOpen, now)").

Question: Q-09.

### P-21b — TripPolicy → StateRead

State can return Closed before failed accounting gets the mutex. State during a true trip policy waits, then samples Open or reconciles elapsed Open. Synchronous reentry stalls.

observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:211 ("state, _ := cb.currentState(now)"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:327 ("cb.setState(StateOpen, now)").

Question: Q-09.

### P-22a — CountsRead → TripPolicy

Independent Counts before failed accounting sees the pre-failure snapshot. During the trip policy it waits and afterwards sees either incremented failure or cleared counters. The trip policy itself gets the full copy immediately after increment.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:325 ("cb.counts.onFailure()"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:327 ("cb.setState(StateOpen, now)").

Question: Q-09.

### P-22b — TripPolicy → CountsRead

Independent Counts before failed accounting sees the pre-failure snapshot. During the trip policy it waits and afterwards sees either incremented failure or cleared counters. The trip policy itself gets the full copy immediately after increment.

observed-in-code gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:220 ("return cb.counts"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:325 ("cb.counts.onFailure()"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:327 ("cb.setState(StateOpen, now)").

Question: Q-09.

### P-23a — Execute → Notify

Execute may admit before a competing notification starts. Execute started during Notify waits until callback return and then gates on current state with a fresh clock sample. User work of an already admitted request can run during Notify.

observed-in-code gobreaker.go:242 ("result, err := req()"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:280 ("now := time.Now()"). gobreaker.go:281 ("state, generation := cb.currentState(now)"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-15.

### P-23b — Notify → Execute

Execute may admit before a competing notification starts. Execute started during Notify waits until callback return and then gates on current state with a fresh clock sample. User work of an already admitted request can run during Notify.

observed-in-code gobreaker.go:242 ("result, err := req()"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:280 ("now := time.Now()"). gobreaker.go:281 ("state, generation := cb.currentState(now)"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-15.

### P-24a — Report → Notify

One report may commit before a different report triggers notification. A report initiated during the notification waits. If its captured generation is older after unlock, the result is discarded after time reconciliation.

observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:354 ("cb.state = state"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-05.

### P-24b — Notify → Report

One report may commit before a different report triggers notification. A report initiated during the notification waits. If its captured generation is older after unlock, the result is discarded after time reconciliation.

observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:354 ("cb.state = state"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-05.

### P-25a — RequestReturn → Notify

Raw return can precede notification or happen during it because request runs outside lock. Classify can also run during notification; accounting waits and rejects old generation writes after notification.

observed-in-code gobreaker.go:242 ("result, err := req()"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-05.

### P-25b — Notify → RequestReturn

Raw return can precede notification or happen during it because request runs outside lock. Classify can also run during notification; accounting waits and rejects old generation writes after notification.

observed-in-code gobreaker.go:242 ("result, err := req()"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-05.

### P-26a — Classify → TripPolicy

Classification can run before or during another request's locked trip policy. When true policy commits first, accounting of the classified result is stale. False policy preserves generation and the classified result can apply after unlock.

observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:327 ("cb.setState(StateOpen, now)").

Question: Q-05.

### P-26b — TripPolicy → Classify

Classification can run before or during another request's locked trip policy. When true policy commits first, accounting of the classified result is stale. False policy preserves generation and the classified result can apply after unlock.

observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:327 ("cb.setState(StateOpen, now)").

Question: Q-05.

### P-27a — RequestReturn → TripPolicy

Raw request return can occur on either side of another trip-policy call, or during it. Generation is examined after classification and mutex acquisition. Therefore raw return order alone does not settle applied versus ignored.

observed-in-code gobreaker.go:242 ("result, err := req()"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").

Question: Q-05.

### P-27b — TripPolicy → RequestReturn

Raw request return can occur on either side of another trip-policy call, or during it. Generation is examined after classification and mutex acquisition. Therefore raw return order alone does not settle applied versus ignored.

observed-in-code gobreaker.go:242 ("result, err := req()"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").

Question: Q-05.

### P-28a — Report → TripPolicy

An earlier two-step report may apply before a different failure invokes the trip policy. During that policy the report waits. On true, drop a stale report. On false, apply under matching generation. A reentrant report stalls.

observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:327 ("cb.setState(StateOpen, now)").

Question: Q-05.

### P-28b — TripPolicy → Report

An earlier two-step report may apply before a different failure invokes the trip policy. During that policy the report waits. On true, drop a stale report. On false, apply under matching generation. A reentrant report stalls.

observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:327 ("cb.setState(StateOpen, now)").

Question: Q-05.

### T-01 — duplicate success below capacity

HalfOpen budget two → Allow once → report true twice → Closed; no second distinct trial was admitted.

observed-in-code gobreaker.go:271 ("return func(success bool) {"). gobreaker.go:315 ("cb.counts.onSuccess()"). gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). gobreaker.go:317 ("cb.setState(StateClosed, now)").

Question: Q-03.

### T-02 — same caller while Execute still pending

Caller spawns its first Execute and blocks it inside request, then issues another. Closed: the second finishes before the first and increments its own request and outcome. In half-open admission is independent below capacity and refused at capacity. No pending admission queue.

observed-in-code gobreaker.go:242 ("result, err := req()"). gobreaker.go:277 ("cb.mutex.Lock()"). gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:289 ("cb.counts.onRequest()").

Question: Q-07.

### T-03 — same caller holding an unreported Allow callback

HalfOpen budget two → Allow A → Allow B → third rejects. Report A reaches one success, B still has to report and Requests remains two. At budget one B rejects even after A has been handed to the caller.

observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). gobreaker.go:271 ("return func(success bool) {"). gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:289 ("cb.counts.onRequest()"). gobreaker.go:315 ("cb.counts.onSuccess()").

Question: Q-07.

### T-04 — missing report versus later report

HalfOpen budget one → Allow → caller withdraws. With no later report, successive admissions reject indefinitely. Later success closes or failure opens if generation matches. The callback still addresses its wrapper.

observed-in-code gobreaker.go:271 ("return func(success bool) {"). gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:317 ("cb.setState(StateClosed, now)"). gobreaker.go:330 ("cb.setState(StateOpen, now)"). gobreaker.go:334 ("func (cb *CircuitBreaker) currentState(now time.Time) (State, uint64) {").

Question: Q-06.

### T-05 — stale report is first post-expiry observer

Closed → two callbacks issued → one false trips → after expiry other false reaches afterRequest, observes HalfOpen and discards accounting → next Allow gets first half-open slot.

observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:327 ("cb.setState(StateOpen, now)"). gobreaker.go:342 ("cb.setState(StateHalfOpen, now)").

Question: Q-05.

### T-06 — classifier blocks across closed interval

Execute request returns error → classifier blocks outside lock → State clears generation → classifier returns false → stale result ignored, original error goes back. If classifier panics, deferred accounting still rejects stale and propagates the panic if afterRequest returns.

observed-in-code gobreaker.go:234 ("defer func() {"). gobreaker.go:237 ("cb.afterRequest(generation, false)"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"). gobreaker.go:244 ("return result, err"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:338 ("cb.toNewGeneration(now)").

Question: Q-05.

### T-07 — trip policy panic before and after generation rollover

Current failure increments and ReadyToTrip panics. Execute's defer repeats accounting after accounting unlock, so it can increment again in same generation. If released mutex lets another operation reset first, that retry is stale. Stale failures never enter the trip callback at all.

observed-in-code gobreaker.go:234 ("defer func() {"). gobreaker.go:237 ("cb.afterRequest(generation, false)"). gobreaker.go:295 ("defer cb.mutex.Unlock()"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:325 ("cb.counts.onFailure()"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {").

Question: Q-10.

### T-08 — notification success and failure around transition

Notify for transition runs only after generation reset; synchronous return allows caller through. Panic propagates after commit, can replace an original request panic during deferred reporting, and on admission prevents work from starting. No notification for closed periodic reset.

observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"). gobreaker.go:234 ("defer func() {"). gobreaker.go:237 ("cb.afterRequest(generation, false)"). gobreaker.go:338 ("cb.toNewGeneration(now)"). gobreaker.go:354 ("cb.state = state"). gobreaker.go:356 ("cb.toNewGeneration(now)"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-10.

### T-09 — synchronous callback reentry

Trip policy or notification calls State in same goroutine. Lock is held at callback and deferred unlock is later; State waits. Name remains available. Other goroutines calling locking methods wait too.

observed-in-code gobreaker.go:202 ("return cb.name"). gobreaker.go:207 ("cb.mutex.Lock()"). gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:295 ("defer cb.mutex.Unlock()"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)").

Question: Q-09.

### T-10 — Goexit vs ordinary cancellation demand

Execute request Goexits: deferred recover is nil and records no outcome. Ordinary request may return after caller demand ends, then classifier and generation-gated accounting still run. The caller owns any underlying operation cancellation.

observed-in-code gobreaker.go:234 ("defer func() {"). gobreaker.go:235 ("e := recover()"). gobreaker.go:237 ("cb.afterRequest(generation, false)"). gobreaker.go:242 ("result, err := req()"). gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))").

Question: Q-06.

### T-11 — exact deadline vs before and after

Open with sampled time before or equal to expiry remains open. Strictly later first observing call transitions and notifies. With no call stored Open persists beyond deadline. Multiple closed intervals yield one new generation on next sample.

observed-in-code gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). gobreaker.go:338 ("cb.toNewGeneration(now)"). gobreaker.go:341 ("if cb.expiry.Before(now) {"). gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").

Question: Q-01.

### T-12 — wrong receiver vs plausible wrong completion

Invoke Allow on a different valid wrapper and its own breaker is charged. Invoke the old callback with a plausible Boolean from unrelated work and that update goes to the captured original wrapper, subject to generation.

observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()"). gobreaker.go:271 ("return func(success bool) {"). gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). gobreaker.go:299 ("if generation != before {").

Question: Q-08.

### T-13 — caller teardown retained callback and runtime retention

Replace application reference with a new wrapper while old callback is retained. Old callback can still affect old breaker. Dropping every reference leaves only runtime reachability; memory cost was not measured.

observed-in-code gobreaker.go:184 ("return &TwoStepCircuitBreaker{"). gobreaker.go:185 ("cb: NewCircuitBreaker(st),"). gobreaker.go:271 ("return func(success bool) {"). gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)").

Question: Q-17.

### T-14 — concurrent opposite reports

One HalfOpen callback receives true and false. With budget one, whichever locks first closes or opens and the later one becomes stale. With budget two and first success below threshold, subsequent failure can still open. In Closed both outcomes can count if no reset occurs.

observed-in-code gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:299 ("if generation != before {"). gobreaker.go:303 ("if success {"). gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). gobreaker.go:325 ("cb.counts.onFailure()"). gobreaker.go:330 ("cb.setState(StateOpen, now)").

Question: Q-03.

### T-15 — nil request and invalid zero-value wrappers

Closed admitted nil Execute invokes nil and accounts failure on constructed instance before repanic. Open or saturated gate returns a refusal before invoking nil. Zero wrapper dereferences a nil inner pointer before admission recovery.

observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()"). gobreaker.go:231 ("return nil, err"). gobreaker.go:234 ("defer func() {"). gobreaker.go:237 ("cb.afterRequest(generation, false)"). gobreaker.go:242 ("result, err := req()"). gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()").

Question: Q-08.

## Multi-instance probes

### T-16 — Shared-fate reset

Inferred under NAT shared service. For N identical breakers with maxRequests M and synchronized failures, callers cause up to N*M half-open admissions following each fixed timeout. Across three cycles with failing first trials: up to N*M attempts per cycle if arrivals reserve before any failure commits, and as few as N when one failure per breaker commits first. observed-in-code gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:330 ("cb.setState(StateOpen, now)"). gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). Question: Q-14.

### T-17 — Fixed-window dispersion

Inferred under NAT shared service. In cycles one, two and three, equal timeout settings and aligned clocks/calls retain aligned eligibility. Different incoming request or recovery times shift the window. No random seed is consulted by the breaker. observed-in-code gobreaker.go:159 ("if st.Timeout <= 0 {"). gobreaker.go:280 ("now := time.Now()"). gobreaker.go:341 ("if cb.expiry.Before(now) {"). gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). Question: Q-14.

### T-18 — Partial recovery

Inferred under NAT shared service. A reaches half-open and succeeds while B remains Open on cycle one. A closes and exposed load becomes caller-limited; B later probes. If the service degrades in cycles two and three, both may reopen, align future windows and repeat the burst. observed-in-code gobreaker.go:283 ("if state == StateOpen {"). gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). gobreaker.go:327 ("cb.setState(StateOpen, now)"). gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). Question: Q-14.

## Requirement-scope checks

### T-19 — Default threshold ordering

Closed breaker uses the default ReadyToTrip → policy is presented counts whose consecutive failures are six → default policy returns true.

README.md:56 ("Default `ReadyToTrip` returns true when the number of consecutive failures is more than 5.").
cited text contemplates this ordering: yes
jev: supported, scope 0.06

The routed control verdict is void. Executable code directly compares the count with five. Question: Q-18.

### T-20 — Autonomous inclusive timeout ordering

Open breaker reaches exactly Timeout with no API activity → clock reaches equality → the stored state autonomously becomes half-open and synchronously calls any installed handler.

README.md:50 ("after which the state of `CircuitBreaker` becomes half-open.").
cited text contemplates this ordering: no
jev: unclear, scope 0.01

The scope omits equality and API inactivity. observed-in-code gobreaker.go:341 ("if cb.expiry.Before(now) {"). Question: Q-01.

### T-21 — Stale outcome after an independently committed clear

A request was sent before Counts cleared → its result arrives after clearing → Counts ignores that result.

README.md:79 ("`Counts` ignores the results of the requests sent before clearing.").
cited text contemplates this ordering: yes
jev: supported, scope 0.19

The routed control verdict is void. TestGeneration exercises one independent clear schedule. Question: Q-19.

### T-22 — Instant refusal during active notification

Open breaker has an unrelated callback holding its mutex → another actor calls Execute before expiry → caller receives a rejection immediately despite contention.

README.md:88 ("`Execute` returns an error instantly if `CircuitBreaker` rejects the request.").
cited text contemplates this ordering: no
jev: unclear, scope 0.01

The assertion adds contention and binds the outcome to time before mutex acquisition. observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"). Question: Q-15.
