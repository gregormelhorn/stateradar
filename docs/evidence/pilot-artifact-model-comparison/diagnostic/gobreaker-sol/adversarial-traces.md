# Adversarial traces

Pair order denotes entry or start order; commits are stated independently. Observer pairs use distinct actors. Name is immutable and lock-free, so overlap with Name cannot change either result. Constructors allocate different objects, and classifier, result and policy on one invocation have causal order. Independent cross-call combinations are represented by admission/observer versus those stages and the free probes.

### P-01a — Admission → StateRead

Open overdue. A admits, refreshing to HalfOpen and incrementing Requests; B reads HalfOpen after unlock.

Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:281 ("state, generation := cb.currentState(now)") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). Decision → Q-05.

### P-01b — StateRead → Admission

Open overdue. B reads and refreshes to HalfOpen with zero admissions; A then admits and increments.

Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:281 ("state, generation := cb.currentState(now)") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). Decision → Q-05.

### P-02a — Admission → CountsRead

Closed. A commits admission, releases lock and waits in its request. B sees Requests=1 and no result.

Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:220 ("return cb.counts") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:289 ("cb.counts.onRequest()"). Decision → Q-18.

### P-02b — CountsRead → Admission

Closed. B snapshots zero before A acquires admission lock. A then commits one.

Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:220 ("return cb.counts") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:289 ("cb.counts.onRequest()"). Decision → Q-18.

### P-03a — Admission → Report

HalfOpen full with one pending probe. A's second Allow is refused; the first caller reports true and closes.

Observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {") gobreaker.go:317 ("cb.setState(StateClosed, now)"). Decision → Q-03.

### P-03b — Report → Admission

HalfOpen full. First caller reports success and closes; A's second Allow now admits in Closed.

Observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {") gobreaker.go:317 ("cb.setState(StateClosed, now)"). Decision → Q-03.

### P-04a — Admission → Result

HalfOpen full. A's Execute is refused while B is outside the lock. B returns success, then classification and completion close.

Observed-in-code gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:317 ("cb.setState(StateClosed, now)"). Decision → Q-18.

### P-04b — Result → Admission

HalfOpen full. B returns and completes successfully before A obtains the lock. A admits in Closed. If only the return happened before A locks, A can still be refused.

Observed-in-code gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:317 ("cb.setState(StateClosed, now)"). Decision → Q-18.

### P-05a — StateRead → Report

Open overdue with old TwoStep callback. State transitions first and notifies; callback then checks generation and skips outcome.

Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Decision → Q-06.

### P-05b — Report → StateRead

Open overdue. Old callback takes completion lock, transitions to HalfOpen and notifies, then discards its outcome; State reads HalfOpen.

Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Decision → Q-06.

- Reachability: Open → HalfOpen — domain-analysis/circuitBreaker/_probe/pilot_test.go:82 ("stale report failed to refresh")

### P-06a — StateRead → Result

Closed interval overdue with old Execute in flight. State clears then request returns and classifies; completion skips old counters.

Observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:338 ("cb.toNewGeneration(now)"). Decision → Q-06.

### P-06b — Result → StateRead

Closed interval overdue. Old request returns, classifies and completion clears, discarding outcome; State sees Closed with new generation.

Observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:338 ("cb.toNewGeneration(now)"). Decision → Q-06.

### P-07a — CountsRead → Report

Closed with one Allow pending. Metrics sees one admission and no outcome. Success report then increments success.

Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:220 ("return cb.counts") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:313 ("cb.counts.onSuccess()"). Decision → Q-18.

### P-07b — Report → CountsRead

Closed. Success report first increments success; metrics sees admission and success.

Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:220 ("return cb.counts") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:313 ("cb.counts.onSuccess()"). Decision → Q-18.

### P-08a — CountsRead → Result

Closed. Metrics sees pending admission before function returns and before classifier submits result.

Observed-in-code gobreaker.go:220 ("return cb.counts") gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:313 ("cb.counts.onSuccess()"). Decision → Q-18.

### P-08b — Result → CountsRead

Closed. Function returns, classifier and completion commit, then metrics sees success. If metrics arrives between return and completion it sees pending instead.

Observed-in-code gobreaker.go:220 ("return cb.counts") gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:313 ("cb.counts.onSuccess()"). Decision → Q-18.

### P-09a — StateRead → CountsRead

Closed interval overdue with nonzero stored counts. State clears before metrics reads zero.

Observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:220 ("return cb.counts") gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") gobreaker.go:338 ("cb.toNewGeneration(now)"). Decision → Q-05.

### P-09b — CountsRead → StateRead

Closed interval overdue. Metrics returns prior counts. State subsequently clears.

Observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:220 ("return cb.counts") gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") gobreaker.go:338 ("cb.toNewGeneration(now)"). Decision → Q-05.

### P-10a — Admission → Classify

HalfOpen with final available slot. A takes it before B classifies an earlier success. B's success below threshold stays HalfOpen.

Observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). Decision → Q-18.

### P-10b — Classify → Admission

HalfOpen full. B starts its classifier and blocks outside lock. A locks and is refused before B can report success. Releasing B can close.

Observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). Decision → Q-18.

### P-11a — StateRead → Classify

Closed interval overdue. State clears before A calls classifier. Classifier still runs and its outcome is stale.

Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). Decision → Q-06.

### P-11b — Classify → StateRead

Closed. Classifier starts and pauses. State clears after deadline. Classifier resumes and returns; accounting discards stale outcome.

Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). Decision → Q-06.

### P-12a — CountsRead → Classify

Closed. Counts snapshots an admission with no completion; classifier runs then submits result.

Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:220 ("return cb.counts") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:313 ("cb.counts.onSuccess()"). Decision → Q-18.

### P-12b — Classify → CountsRead

Closed. Classifier starts and pauses outside lock. Counts can read old outcome totals before the classifier returns or Complete commits.

Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:220 ("return cb.counts") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:313 ("cb.counts.onSuccess()"). Decision → Q-18.

### P-13a — Admission → TripDecision

Closed. A admits before B's failure takes the policy lock; B's copied Counts includes A's admission.

Observed-in-code gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:280 ("now := time.Now()") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:327 ("cb.setState(StateOpen, now)"). Decision → Q-07.

### P-13b — TripDecision → Admission

Closed. B's failure runs a blocking trip policy with mutex held; A waits. Policy returns true and commits Open. A samples after lock and, if still before expiry, is refused.

Observed-in-code gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:280 ("now := time.Now()") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:327 ("cb.setState(StateOpen, now)"). Decision → Q-07.

### P-14a — StateRead → TripDecision

Closed. State locks first, can clear interval; a pre-clear failure then skips trip policy. With current generation it invokes policy.

Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). Decision → Q-06.

### P-14b — TripDecision → StateRead

Closed. Policy holds mutex while State waits. True commits Open; after unlock State sees Open unless timeout already elapsed.

Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). Decision → Q-06.

### P-15a — CountsRead → TripDecision

Closed. Counts locks before failure counts change and returns prior totals. Then policy receives updated copy.

Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:220 ("return cb.counts") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:365 ("cb.counts.clear()"). Decision → Q-02.

### P-15b — TripDecision → CountsRead

Closed. Policy starts while lock held. Counts waits; sees cleared totals if policy trips and notification finishes, or recorded failure if policy returns false.

Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:220 ("return cb.counts") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:365 ("cb.counts.clear()"). Decision → Q-02.

### P-16a — Admission → Notify

Closed. A commits admission first. B subsequently trips and notifies; A's later completion is stale. If A itself refreshes overdue Open, notification happens before A's admission commit.

Observed-in-code gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:280 ("now := time.Now()") gobreaker.go:281 ("state, generation := cb.currentState(now)") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:299 ("if generation != before {") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)") gobreaker.go:354 ("cb.state = state") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Decision → Q-01.

### P-16b — Notify → Admission

Overdue Open. B's transition commits HalfOpen and notifies under lock. A waits, then admits if a slot remains; no stale pre-lock snapshot.

Observed-in-code gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:280 ("now := time.Now()") gobreaker.go:281 ("state, generation := cb.currentState(now)") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:299 ("if generation != before {") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)") gobreaker.go:354 ("cb.state = state") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Decision → Q-01.

### P-17a — StateRead → Notify

Open overdue. State starts and refreshes, commits, then notifies before returning HalfOpen.

Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:212 ("return state") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)") gobreaker.go:354 ("cb.state = state") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Decision → Q-01.

### P-17b — Notify → StateRead

Another eligible call commits HalfOpen and notifies while B's State waits. B returns HalfOpen after unlock. Reentrant State in the callback waits on itself.

Observed-in-code gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:212 ("return state") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)") gobreaker.go:354 ("cb.state = state") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Decision → Q-01.

### P-18a — CountsRead → Notify

Closed. Counts first reads old generation; another call trips, clears and notifies.

Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:220 ("return cb.counts") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:354 ("cb.state = state") gobreaker.go:356 ("cb.toNewGeneration(now)") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") gobreaker.go:365 ("cb.counts.clear()"). Decision → Q-01.

### P-18b — Notify → CountsRead

Notification executes after clear while Counts waits. After unlock Counts returns the new snapshot, possibly including any earlier admission commit.

Observed-in-code gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:220 ("return cb.counts") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:354 ("cb.state = state") gobreaker.go:356 ("cb.toNewGeneration(now)") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") gobreaker.go:365 ("cb.counts.clear()"). Decision → Q-01.

### T-01 — Duplicate while first pending

A starts Execute on goroutine 1. If A has yet to obtain mutex, goroutine 2 from the same logical caller can win the first commit. Below capacity both increment separately and B can return first. At capacity loser returns ErrTooManyRequests; neither waits for handoff or gets a queue entry.

Observed-in-code inputs and inferred schedule gobreaker.go:242 ("result, err := req()") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:294 ("cb.mutex.Lock()"). Decision → Q-18.

### T-02 — Duplicate while callback held

Same caller obtains A via Allow, then Allow B. Limit 2 admits both; a third call is refused. One report on A changes one outcome and frees no admission. Repeating A closes, and B's later false is stale. The wrapper associates neither call with caller identity. With limit 1, B is immediately refused when decision obtains the lock.

Observed-in-code inputs and inferred schedule gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:299 ("if generation != before {") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). Decision → Q-04.

### T-03 — Abandonment with and without late report

At capacity the caller leaves. No matching later input means indefinite refusal in HalfOpen. A later valid callback on the same generation applies and can close (success threshold) or reopen (failure). If another current report already reopened, late matching old report skips outcomes and may refresh expiry. The closure has no response channel to departed caller.

Observed-in-code inputs and inferred schedule gobreaker.go:271 ("return func(success bool) {") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {") gobreaker.go:330 ("cb.setState(StateOpen, now)") gobreaker.go:378 ("cb.expiry = zero"). Decision → Q-03.

### T-04 — Contradictory reports

At limit 1, true first closes and false becomes stale; false first reopens and true becomes stale, with possible later expiry refresh. In Closed without trip, true and false both count in mutex order.

Observed-in-code inputs and inferred schedule gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:299 ("if generation != before {") gobreaker.go:303 ("if success {") gobreaker.go:317 ("cb.setState(StateClosed, now)") gobreaker.go:330 ("cb.setState(StateOpen, now)"). Decision → Q-04.

### T-05 — Replacement with pending report

Construct B while A's callback is held; A callback updates A or is stale there, B stays Closed and unaffected. Passing wrong valid receiver before admission is a separate caller error.

Observed-in-code inputs and inferred schedule gobreaker.go:142 ("cb := new(CircuitBreaker)") gobreaker.go:184 ("return &TwoStepCircuitBreaker{") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:299 ("if generation != before {"). Decision → Q-16.

### T-06 — Open or Closed callback crosses expiry

ReadyToTrip receives sampled now indirectly via its caller. If policy waits longer than timeout then returns true, Open deadline is based on earlier sampled time. Later admission can immediately refresh. If policy panics or exits, failure count remains unless a subsequent eligible call clears it; Execute can count again on panic.

Observed-in-code inputs and inferred schedule gobreaker.go:234 ("defer func() {") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:297 ("now := time.Now()") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:327 ("cb.setState(StateOpen, now)") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). Decision → Q-08.

### T-07 — Notification success and failure around boundary

If expiry refresh invokes notification before admission, successful hook allows later admission commit; panic or Goexit prevents it despite committed HalfOpen. If completion triggers transition, success returns to Execute; failure leaves commit and can prevent ordinary return or replace an active panic. Another thread cannot commit between assignment and hook while mutex is held.

Observed-in-code inputs and inferred schedule gobreaker.go:229 ("generation, err := cb.beforeRequest()") gobreaker.go:234 ("defer func() {") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:281 ("state, generation := cb.currentState(now)") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:354 ("cb.state = state") gobreaker.go:356 ("cb.toNewGeneration(now)") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Decision → Q-09.

### T-08 — Classifier success and failure across reset

A classifier starts outside lock, B clears via State, A returns true/false and stale result is discarded. A classifier panic after reset enters recovery but its failure also skips counts. Before reset the same panic counts as failure if the generation matches. Goexit submits neither. Reentry can itself advance generation.

Observed-in-code inputs and inferred schedule gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:234 ("defer func() {") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {"). Decision → Q-10.

### T-09 — Reenter under and outside lock

OnStateChange calling State blocks at the mutex. ReadyToTrip calling Counts likewise blocks. Name returns directly. Request and classifier run unlocked and can call State or another Execute, possibly changing the generation before their own completion.

Observed-in-code inputs and inferred schedule gobreaker.go:202 ("return cb.name") gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Decision → Q-01.

### T-10 — Impossible report and nil request

Open refusal returns nil callback and error; calling nil panics at the caller. In Closed nil request is admitted, invokes nil, and the recovery path may record failure before rethrow. Open refuses before invoking nil; HalfOpen at cap likewise.

Observed-in-code inputs and inferred schedule gobreaker.go:229 ("generation, err := cb.beforeRequest()") gobreaker.go:231 ("return nil, err") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:242 ("result, err := req()") gobreaker.go:268 ("return nil, err") gobreaker.go:283 ("if state == StateOpen {") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). Decision → Q-13.

### T-11 — Caller termination

An Execute request calls runtime.Goexit. Its defers run, recover returns nil and no outcome is submitted. In HalfOpen this keeps one slot; late work in a separate task cannot use the original Execute return channel because Execute exposes no report callback.

Observed-in-code inputs and inferred schedule gobreaker.go:234 ("defer func() {") gobreaker.go:235 ("e := recover()") gobreaker.go:236 ("if e != nil {") gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:378 ("cb.expiry = zero"). Decision → Q-11.

### T-12 — Counter and epoch limits

A long-lived Closed generation with interval disabled admits enough requests to wrap uint32 Requests; a sufficiently ancient retained callback can compare equal after uint64 wrap. Both are theoretical range paths, no runtime occurrence asserted.

Observed-in-code inputs and inferred schedule gobreaker.go:48 ("Requests             uint32") gobreaker.go:56 ("c.Requests++") gobreaker.go:128 ("generation uint64") gobreaker.go:299 ("if generation != before {") gobreaker.go:364 ("cb.generation++") gobreaker.go:370 ("if cb.interval == 0 {"). Decision → Q-15.

### T-13 — Requirement scope O1

Closed with enabled interval → A is admitted → B invokes State after expiry, clearing Counts → A returns success → Counts excludes A's success.

DOC-22 README.md:79 ("`Counts` ignores the results of the requests sent before clearing."). cited text contemplates this ordering: no. jev: unclear, scope 0.02. This order is exercised by TestGeneration (gobreaker_test.go:341-342), but the prose only covers ignoring pre-clear accounting. Decision → Q-06.

### T-14 — Requirement scope O2

Open with no traffic → wall time passes beyond Timeout with no State, admission or completion call → breaker autonomously enters HalfOpen and invokes OnStateChange.

DOC-9 README.md:49 ("- `Timeout` is the period of the open state,"). cited text contemplates this ordering: no. jev: unclear, scope 0.01. No autonomous timer in the observed paths; the next eligible call samples expiry. Decision → Q-05.

### T-15 — Requirement scope O3

Open before deadline with a notification holding the mutex → B calls Execute → B immediately returns ErrOpenState without waiting for notification.

DOC-25 README.md:88 ("`Execute` returns an error instantly if `CircuitBreaker` rejects the request."). cited text contemplates this ordering: no. jev: unclear, scope 0.01. The caller waits to acquire the mutex before a rejection decision. Decision → Q-07.

### T-16 — Requirement scope O4

Closed with policy able to trip → request panics with non-nil payload → failure is recorded and policy trips → notification panics → Execute still propagates the original request panic.

DOC-27 README.md:90 ("If a panic occurs in the request, `CircuitBreaker` handles it as an error"). cited text contemplates this ordering: no. jev: unclear, scope 0.01. The notification panic can replace the original after the transition commits. Decision → Q-19.

### M-01 — Shared-fate reset

Inferred under NAT-6. N breakers open near the same time, use the same timeout and receive demand immediately after it. With MaxRequests M and enough demand, up to N×M initial recovery admissions arrive in each of three cycles. Each first failure reopens its breaker, so observed admissions may be fewer if failures return before all M admissions. Identical demand and failure timing repeat the burst in cycles 2 and 3. gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:330 ("cb.setState(StateOpen, now)") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). Q-14.

### M-02 — Backoff dispersion

Inferred under NAT-6. There is a fixed configured timeout and no random seed or backoff multiplier. Equal opening samples, settings and post-deadline demand produce equal due times in three successive failure cycles; staggered demand or different durations can spread probes. gobreaker.go:162 ("cb.timeout = st.Timeout") gobreaker.go:280 ("now := time.Now()") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). Q-14.

### M-03 — Degraded recovery herd

Inferred under NAT-6. A gets enough successes to close during partial recovery, so its next burst has no HalfOpen cap. B enters HalfOpen later and can add up to its local cap before it fails. On another degradation A may stay Closed until its policy trips, while B immediately reopens on a current HalfOpen failure. Shared impact depends on arrival rates. gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:317 ("cb.setState(StateClosed, now)") gobreaker.go:327 ("cb.setState(StateOpen, now)") gobreaker.go:330 ("cb.setState(StateOpen, now)"). Q-14.
