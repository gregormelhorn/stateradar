# Adversarial traces

Pairs order observable decisions or commits. Result callbacks operate before the completion lock, so callback return order alone need not determine commit order. Exact scheduling is inferred unless a probe is identified. Name is independent of the state mutex. gobreaker.go:202 ("return cb.name") gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:294 ("cb.mutex.Lock()").

### P-01a — Admit then Report

1. Start HalfOpen budget 1 with an outstanding successful probe.
2. Schedule Admit's decision before Report's decision.
3. B tries Allow and gets ErrTooManyRequests, then A reports true and closes.

Disposition: inferred from observed-in-code gobreaker.go:286 ("return generation, ErrTooManyRequests") gobreaker.go:317 ("cb.setState(StateClosed, now)"). Question: Q-15.

### P-01b — Report then Admit

1. Start HalfOpen budget 1 with an outstanding successful probe.
2. Schedule Report's decision before Admit's decision.
3. A reports true and closes, then B obtains a Closed continuation.

Disposition: inferred from observed-in-code gobreaker.go:286 ("return generation, ErrTooManyRequests") gobreaker.go:317 ("cb.setState(StateClosed, now)"). Question: Q-15.

### P-02a — Admit then Return

1. Start HalfOpen budget 1 with executing successful probe.
2. Schedule Admit's decision before Return's decision.
3. B tries Execute before A commits and rejects; A returns normally and closes.

Disposition: inferred from observed-in-code gobreaker.go:286 ("return generation, ErrTooManyRequests") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:317 ("cb.setState(StateClosed, now)"). Question: Q-15.

### P-02b — Return then Admit

1. Start HalfOpen budget 1 with executing successful probe.
2. Schedule Return's decision before Admit's decision.
3. A's classified success closes; B executes against Closed.

Disposition: inferred from observed-in-code gobreaker.go:286 ("return generation, ErrTooManyRequests") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:317 ("cb.setState(StateClosed, now)"). Question: Q-15.

### P-03a — Admit then Panic

1. Start HalfOpen budget 1 with executing probe about to panic.
2. Schedule Admit's decision before Panic's decision.
3. B admission rejects by cap; A panics, reopens and repanics.

Disposition: inferred from observed-in-code gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:238 ("panic(e)") gobreaker.go:284 ("return generation, ErrOpenState") gobreaker.go:286 ("return generation, ErrTooManyRequests") gobreaker.go:330 ("cb.setState(StateOpen, now)"). Question: Q-16.

### P-03b — Panic then Admit

1. Start HalfOpen budget 1 with executing probe about to panic.
2. Schedule Panic's decision before Admit's decision.
3. A panic reopens first; B receives ErrOpenState.

Disposition: inferred from observed-in-code gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:238 ("panic(e)") gobreaker.go:284 ("return generation, ErrOpenState") gobreaker.go:286 ("return generation, ErrTooManyRequests") gobreaker.go:330 ("cb.setState(StateOpen, now)"). Question: Q-16.

### P-04a — State then Report

1. Start Open due with a stale continuation.
2. Schedule State's decision before Report's decision.
3. Observer refreshes to HalfOpen; A reports stale and adds no failure.

Disposition: inferred from observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). Question: Q-04.

### P-04b — Report then State

1. Start Open due with a stale continuation.
2. Schedule Report's decision before State's decision.
3. A reports stale, first refreshes to HalfOpen and emits notification; State sees HalfOpen.

Disposition: inferred from observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). Question: Q-04.

### P-05a — Counts then Report

1. Start Closed with a pending successful report, interval disabled.
2. Schedule Counts's decision before Report's decision.
3. B reads zero success; A reports success.

Disposition: inferred from observed-in-code gobreaker.go:220 ("return cb.counts") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:313 ("cb.counts.onSuccess()"). Question: none — control trace.

### P-05b — Report then Counts

1. Start Closed with a pending successful report, interval disabled.
2. Schedule Report's decision before Counts's decision.
3. A reports success; B reads one success.

Disposition: inferred from observed-in-code gobreaker.go:220 ("return cb.counts") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:313 ("cb.counts.onSuccess()"). Question: none — control trace.

### P-06a — State then Return

1. Start Closed with due interval, stale Execute work.
2. Schedule State's decision before Return's decision.
3. B State clears, then A classifies and its successful outcome is stale.

Disposition: inferred from observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {"). Question: Q-04.

### P-06b — Return then State

1. Start Closed with due interval, stale Execute work.
2. Schedule Return's decision before State's decision.
3. A classifies and refreshes itself, skips old result; B reads Closed.

Disposition: inferred from observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {"). Question: Q-04.

### P-07a — Counts then Return

1. Start Closed without expiry with pending successful Execute.
2. Schedule Counts's decision before Return's decision.
3. B Counts sees admitted request without success, then A completes.

Disposition: inferred from observed-in-code gobreaker.go:220 ("return cb.counts") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:313 ("cb.counts.onSuccess()"). Question: none — control trace.

### P-07b — Return then Counts

1. Start Closed without expiry with pending successful Execute.
2. Schedule Return's decision before Counts's decision.
3. A completes and B reads one success.

Disposition: inferred from observed-in-code gobreaker.go:220 ("return cb.counts") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:313 ("cb.counts.onSuccess()"). Question: none — control trace.

### P-08a — State then Panic

1. Start Closed at five current consecutive failures with another admitted request.
2. Schedule State's decision before Panic's decision.
3. B reads Closed; A panics and trips under default policy.

Disposition: inferred from observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:193 ("return counts.ConsecutiveFailures > 5") gobreaker.go:327 ("cb.setState(StateOpen, now)"). Question: Q-16.

### P-08b — Panic then State

1. Start Closed at five current consecutive failures with another admitted request.
2. Schedule Panic's decision before State's decision.
3. A panics and trips first; B reads Open.

Disposition: inferred from observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:193 ("return counts.ConsecutiveFailures > 5") gobreaker.go:327 ("cb.setState(StateOpen, now)"). Question: Q-16.

### P-09a — Counts then Panic

1. Start Closed with one admitted request and zero failures.
2. Schedule Counts's decision before Panic's decision.
3. B reads zero failures, then A panics and accounts one failure.

Disposition: inferred from observed-in-code gobreaker.go:220 ("return cb.counts") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:325 ("cb.counts.onFailure()"). Question: Q-16.

### P-09b — Panic then Counts

1. Start Closed with one admitted request and zero failures.
2. Schedule Panic's decision before Counts's decision.
3. A panics and accounts one; B reads it.

Disposition: inferred from observed-in-code gobreaker.go:220 ("return cb.counts") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:325 ("cb.counts.onFailure()"). Question: Q-16.

### P-10a — State then Admit

1. Start Open due, admission budget 2.
2. Schedule State's decision before Admit's decision.
3. B State refreshes to HalfOpen, then A admits first probe.

Disposition: inferred from observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:281 ("state, generation := cb.currentState(now)") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). Question: Q-01.

### P-10b — Admit then State

1. Start Open due, admission budget 2.
2. Schedule Admit's decision before State's decision.
3. A refreshes and admits first probe, then B sees HalfOpen.

Disposition: inferred from observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:281 ("state, generation := cb.currentState(now)") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). Question: Q-01.

### P-11a — Counts then Admit

1. Start Closed without expiry.
2. Schedule Counts's decision before Admit's decision.
3. B snapshot sees zero admissions before A's accepted call.

Disposition: inferred from observed-in-code gobreaker.go:220 ("return cb.counts") gobreaker.go:289 ("cb.counts.onRequest()"). Question: none — control trace.

### P-11b — Admit then Counts

1. Start Closed without expiry.
2. Schedule Admit's decision before Counts's decision.
3. A is admitted and B sees one admission.

Disposition: inferred from observed-in-code gobreaker.go:220 ("return cb.counts") gobreaker.go:289 ("cb.counts.onRequest()"). Question: none — control trace.

### P-12a — State then Counts

1. Start Closed due with a nonzero prior count.
2. Schedule State's decision before Counts's decision.
3. B State clears first and A's Counts sees zero.

Disposition: inferred from observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:220 ("return cb.counts") gobreaker.go:338 ("cb.toNewGeneration(now)"). Question: Q-01.

### P-12b — Counts then State

1. Start Closed due with a nonzero prior count.
2. Schedule Counts's decision before State's decision.
3. A's Counts sees prior count; B State clears.

Disposition: inferred from observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:220 ("return cb.counts") gobreaker.go:338 ("cb.toNewGeneration(now)"). Question: Q-01.

### P-13a — Name then Admit

1. Start Closed without expiry.
2. Schedule Name's decision before Admit's decision.
3. B Name returns configured name, then A admits.

Disposition: inferred from observed-in-code gobreaker.go:202 ("return cb.name") gobreaker.go:289 ("cb.counts.onRequest()"). Question: none — control trace.

### P-13b — Admit then Name

1. Start Closed without expiry.
2. Schedule Admit's decision before Name's decision.
3. A admits, then B Name returns same name.

Disposition: inferred from observed-in-code gobreaker.go:202 ("return cb.name") gobreaker.go:289 ("cb.counts.onRequest()"). Question: none — control trace.

### P-14a — Name then Report

1. Start Closed with a pending success report.
2. Schedule Name's decision before Report's decision.
3. B Name reads configured name; A reports success.

Disposition: inferred from observed-in-code gobreaker.go:202 ("return cb.name") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:313 ("cb.counts.onSuccess()"). Question: none — control trace.

### P-14b — Report then Name

1. Start Closed with a pending success report.
2. Schedule Report's decision before Name's decision.
3. A reports success; B Name reads same name.

Disposition: inferred from observed-in-code gobreaker.go:202 ("return cb.name") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:313 ("cb.counts.onSuccess()"). Question: none — control trace.

### P-15a — Name then Return

1. Start Closed with a pending Execute return.
2. Schedule Name's decision before Return's decision.
3. B Name returns configured name; then A finishes normally.

Disposition: inferred from observed-in-code gobreaker.go:202 ("return cb.name") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:244 ("return result, err"). Question: none — control trace.

### P-15b — Return then Name

1. Start Closed with a pending Execute return.
2. Schedule Return's decision before Name's decision.
3. A finishes normally; then B Name returns same name.

Disposition: inferred from observed-in-code gobreaker.go:202 ("return cb.name") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:244 ("return result, err"). Question: none — control trace.

### P-16a — Name then Panic

1. Start Closed with admitted work about to panic.
2. Schedule Name's decision before Panic's decision.
3. B Name reads configured name, then A panics and accounts.

Disposition: inferred from observed-in-code gobreaker.go:202 ("return cb.name") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:238 ("panic(e)"). Question: Q-16.

### P-16b — Panic then Name

1. Start Closed with admitted work about to panic.
2. Schedule Panic's decision before Name's decision.
3. A panics and accounts, then B Name reads same name.

Disposition: inferred from observed-in-code gobreaker.go:202 ("return cb.name") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:238 ("panic(e)"). Question: Q-16.

## Free probes

### T-01 — One continuation twice

HalfOpen with budget two → accept A → A reports true twice → first call gives one success on one admission, second closes and clears. Lock serializes but does not consume the closure. Contradictory false first opens immediately and makes later true stale; true first with budget two can leave false current and also reopen. A closing true at budget one instead makes later false stale. Q-03. observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:299 ("if generation != before {") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {") gobreaker.go:330 ("cb.setState(StateOpen, now)"). Executed overlay DuplicateCompletion.

### T-02 — Abandoned continuation with and without later report

HalfOpen budget one → A receives done and leaves without reporting → same caller or another caller's next admission rejects, and further traffic has the same outcome indefinitely under this schedule. If a retained done later reports true, it closes and subsequent admission succeeds. A later false instead opens and restarts the timeout. Q-02/Q-15. observed-in-code gobreaker.go:271 ("return func(success bool) {") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:317 ("cb.setState(StateClosed, now)") gobreaker.go:330 ("cb.setState(StateOpen, now)") gobreaker.go:378 ("cb.expiry = zero"). Executed overlay OmittedCompletionAndSecondAllow.

### T-03 — Same caller, two overlapping Execute calls

Closed → A locks and increments before work, unlocks and blocks in its request → B (second goroutine of same caller) locks, admits, executes and returns failure → A resumes and successfully accounts. No pending wait entry; each accepted request adds one count. Pairs in HalfOpen apply at budget. Below budget both enter unless an intervening completion changes state; if B opens before A commits, A refreshes and sees stale generation, but can still return its request result. Q-15/Q-04. observed-in-code gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:281 ("state, generation := cb.currentState(now)") gobreaker.go:289 ("cb.counts.onRequest()") gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:299 ("if generation != before {"). Executed overlay ExecuteOverlap for the Closed case.

### T-04 — Two Allow calls before first is returned

A and B are goroutines for the same caller. A first obtains the lock, observes state and commits one admission before unlocking. B cannot alter that observation before commit. Once A unlocks, B can return even before A resumes to receive its own callback. Below budget both receive distinct closures, one report only completes its own logical work and increments the shared aggregate. At budget B rejects and receives nil. Q-15. observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()") gobreaker.go:271 ("return func(success bool) {") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:278 ("defer cb.mutex.Unlock()") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:289 ("cb.counts.onRequest()").

### T-05 — Stale report crosses Open expiry

Old A admitted Closed → other failures open → age expiry → old A reports false before any State call → completion first advances to HalfOpen and publishes a second notification, then drops the old outcome. Before expiry the old result only drops. Q-04. observed-in-code gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Executed overlay StaleCompletionAdvancesOpen.

### T-06 — When a reset beats a completion

Assertion: a request admitted in a closed generation → another caller observes expiry and clears counts → the old successful result later arrives → the old result does not contribute to Counts.
DOC-22 README.md:79 ("`Counts` ignores the results of the requests sent before clearing."). cited text contemplates this ordering: no. jev: supported, scope 0.03.
The text covers stale outcome contribution but does not give the actor or the refresh-on-observation ordering. observed-in-tests gobreaker_test.go:337 ("assert.Equal(t, StateClosed, customCB.State())") gobreaker_test.go:342 ("assert.Equal(t, Counts{0, 0, 0, 0, 0}, customCB.counts)"), observed-in-code gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {"). If classifier blocks while the refresh occurs, the old result still calls it and the original result pair can be returned. Executed overlay IsSuccessfulAfterExpiry covers classification before a completion-triggered clear. Q-04.

### T-07 — Reentrant hooks and refusal under contention

Assertion: Open before expiry while a notification holds the mutex → another caller calls Execute before unlock → Execute returns an error immediately instead of waiting for that mutex.
DOC-25 README.md:88 ("`Execute` returns an error instantly if `CircuitBreaker` rejects the request."). cited text contemplates this ordering: no. jev: unclear, scope 0.01.
OnStateChange can read Name but State, Counts, Admit or Report requires the same lock. ReadyToTrip has the identical exclusion while its callback runs. A separate prospective refusal also waits for unlock. Request work and IsSuccessful run outside the lock and can re-enter, modifying the generation before the original result commits. Q-05/Q-10. observed-in-code gobreaker.go:202 ("return cb.name") gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:242 ("result, err := req()") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Executed overlay NotificationReentry.

### T-08 — Deadline with silence and snapshot

Assertion: Open with no further State, Execute, Allow, or completion calls → Timeout is reached → the breaker becomes HalfOpen and emits OnStateChange without another call.
DOC-9 README.md:50 ("after which the state of `CircuitBreaker` becomes half-open."). cited text contemplates this ordering: no. jev: unclear, scope 0.01.
No actor refreshes during silence. Equality is also unexpired. A Counts snapshot does not refresh a due Closed interval and can disagree with a subsequent State-triggered clear. Q-01. observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:220 ("return cb.counts") gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") gobreaker.go:341 ("if cb.expiry.Before(now) {"). Executed overlay CountsDoesNotRefresh.

### T-09 — Policy success, failure and goroutine exit on lifecycle boundaries

Request/classification can return before or after another call changes state. Normal outcome after change skips contribution, classifier panic after change attempts stale failure and re-panics, and Goexit submits no failure. ReadyToTrip is under lock: no external transition can interpose between committed failure count and predicate result. False stays, true opens, panic leaves increment committed and unwinds; in Execute's normal-return path recovery may count again if still current. OnStateChange only begins after state and reset are committed and under lock; return allows triggering path to continue. Panic escapes State/admission/done, or reaches Execute recovery during normal accounting. During existing request panic reporting, a hook panic can replace the recovered value. Goexit executes unlock defer, but skips remaining effects; a blocked hook can stop all locked API progress. Q-05/Q-06/Q-16. observed-in-code gobreaker.go:235 ("e := recover()") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:278 ("defer cb.mutex.Unlock()") gobreaker.go:295 ("defer cb.mutex.Unlock()") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:354 ("cb.state = state") gobreaker.go:356 ("cb.toNewGeneration(now)") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). Executed overlay StateChangePanicKeepsTransition verifies notification panic after commit.

### T-10 — Callback or receiver substitution

A and B are standalone instances → A reserves → caller invokes B's unrelated continuation with A's result → B processes according to B's generation and A remains spent. A replacement constructor leaves the old instance callable via retained done. Rejected Allow returns nil and an error; invoking nil panics in caller. An invalid receiver has call-specific faults, and zero core can admit via Allow only through internal topology, whereas a zero wrapper has no backing breaker. Q-07/Q-08/Q-13. observed-in-code gobreaker.go:137 ("cb *CircuitBreaker") gobreaker.go:183 ("func NewTwoStepCircuitBreaker(st Settings) *TwoStepCircuitBreaker {") gobreaker.go:268 ("return nil, err") gobreaker.go:271 ("return func(success bool) {") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:303 ("if success {").

### T-11 — Counter limits

Under a deliberately long zero-interval Closed lifetime, admission count is modular uint32. Neither closure presence nor generation equality guarantees total outcomes equal distinct requests. Generation wrap, which needs a retained old callback and 2^64 generation increments, is a theoretical alias. Q-09. observed-in-code gobreaker.go:48 ("Requests             uint32") gobreaker.go:56 ("c.Requests++") gobreaker.go:128 ("generation uint64") gobreaker.go:299 ("if generation != before {") gobreaker.go:364 ("cb.generation++").

### T-12 — Settings and panic edge cases

Construct with zero max and negative durations → substitutes one admission, no Closed interval and a 60s timeout. Admitted nil Execute function panics and recovery may account failure before re-panic; rejected Execute never invokes it. Runtime-dependent nil panic must be separated from nil function invocation. Q-08/Q-17. observed-in-code gobreaker.go:147 ("if st.MaxRequests == 0 {") gobreaker.go:153 ("if st.Interval <= 0 {") gobreaker.go:159 ("if st.Timeout <= 0 {") gobreaker.go:231 ("return nil, err") gobreaker.go:235 ("e := recover()") gobreaker.go:242 ("result, err := req()").

## Multi-instance probes (analytic)

### M-01 — Three shared failure/recovery cycles

For N independently constructed breakers, configure identical timeout and one probe each. Common upstream failure trips near simultaneously. On each of three cycles, a synchronized wave of new calls after timeout permits up to N trial calls, common failure reopens each, and requests during the following Open interval refuse. Under those arrivals cycles produce N, N, N trial attempts, plus initial Closed load. Q-11. Inferred from gobreaker.go:284 ("return generation, ErrOpenState") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:330 ("cb.setState(StateOpen, now)") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").

### M-02 — Dispersion

A and B start same expiry and receive trial calls at matching offsets. Breaker uses neither retry nor random seed; with fixed timeout and aligned opens, repeated cycles preserve this alignment. Unequal observed failure or subsequent traffic offsets can separate it. Q-11. Inferred from gobreaker.go:297 ("now := time.Now()") gobreaker.go:341 ("if cb.expiry.Before(now) {") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)").

### M-03 — Partial recovery

Shared service allows A's probe success, then fails before B completes. A closes and can send unrestricted Closed requests until its policy trips. B's current failure opens directly. A's reopened timer begins at its own new trip, and B's at its failed probe. Load amplification depends on client arrivals and upstream recovery capacity. Q-11. Inferred from gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:317 ("cb.setState(StateClosed, now)") gobreaker.go:327 ("cb.setState(StateOpen, now)") gobreaker.go:330 ("cb.setState(StateOpen, now)").

### T-13 — Wrapper value overwritten while a continuation is outstanding

A.Allow returns done → independent B is constructed at the same initial generation → caller assigns \`*a = *b\` before invoking done(true) → old done re-reads the core on A's wrapper and increments B's success count with zero B admissions. This is serialized and does not require a data race. A simple variable rebind leaves the captured wrapper intact. observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:299 ("if generation != before {"). observed-in-tests domain-analysis/circuitBreaker/_probe/behavior_test.go:177 ("if got := b.Counts(); got.Requests != 0 || got.TotalSuccesses != 1 {"). Q-07/Q-13.

### T-14 — Panic in normal failure accounting

Closed Execute work returns an error → failure counter increments → first ReadyToTrip panics → deferred unlock → Execute recovers and asks for failure accounting again → same generation permits second increment and ReadyToTrip returns false → Execute re-panics with original policy value. A competing clear after unlock can instead make the second accounting stale. observed-in-code gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:295 ("defer cb.mutex.Unlock()") gobreaker.go:299 ("if generation != before {") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). observed-in-tests domain-analysis/circuitBreaker/_probe/behavior_test.go:201 ("if c := b.Counts(); c.Requests != 1 || c.TotalFailures != 2 || calls != 2 {"). Q-06/Q-16.
