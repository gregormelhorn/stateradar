# CircuitBreaker domain behaviour pilot

model routing: on (unevaluated, cascade plan stage 3)  
routing variant: routed

Source HEAD `27b8e2cfc65aacd09abb3968455e4b01df4a83fa`. One constructed breaker, with its TwoStepCircuitBreaker public wrapper represented through the same core lifecycle. The three stored modes are Closed, Open and HalfOpen. The model retains generation, expiry, count and caller lifecycle as guarded context. The generated sidecar records the primary transition in each cell; notes cover alternate and cross-phase effects. No decision records were made. Optional traditional reviewer cross-check was not performed.

## Findings and coverage

Each question has an associated finding or decision gap. The classification below reports the as-is evidence. Proposed decisions remain open.

| Case | Catalogue or trace | Verified finding and decision |
|---|---|---|
| Transition hook reentry | UV-16, T-07, P-12a/b | Blocking reproduced. State/count reset commit before notification and the callback re-enters the held mutex. Callback contract gap Q-01. gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:356 ("cb.toNewGeneration(now)"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). |
| Trip-policy reentry | UV-15, T-08, P-15a/b | Blocking reproduced, with failure already incremented. Callback contract gap Q-02. gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:325 ("cb.counts.onFailure()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). |
| Duplicate or contradictory report | UV-09, T-01 | Premature HalfOpen close with one distinct request reproduced. No data race is needed because both invocations serialize. API accounting issue Q-03. gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:294 ("cb.mutex.Lock()"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"). |
| Omitted, delayed or abandoned trial | UV-01, UV-05, UV-07, T-02/T-12 | No input leaves the HalfOpen budget consumed. Later same-generation success closes at threshold; failure opens. Goexit can leave an admission alone. Progress gap Q-04 and runtime scope Q-20. gobreaker.go:235 ("e := recover()"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:317 ("cb.setState(StateClosed, now)"), gobreaker.go:330 ("cb.setState(StateOpen, now)"), gobreaker.go:378 ("cb.expiry = zero"). |
| Idle, late and equal deadline | UV-12, UV-18, T-10/T-14, P-09a/b | Counts does not refresh expired state or counters. Exact equality stays under strict Before. Timer and read contract Q-05. gobreaker.go:211 ("state, _ := cb.currentState(now)"), gobreaker.go:220 ("return cb.counts"), gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"), gobreaker.go:341 ("if cb.expiry.Before(now) {"). |
| Admission during a slow callback | T-17, P-15a | Refusal can wait for the lock and a fresh time sample. Wording and latency contract Q-06. gobreaker.go:277 ("cb.mutex.Lock()"), gobreaker.go:280 ("now := time.Now()"), gobreaker.go:284 ("return generation, ErrOpenState"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). |
| Abnormal classifier, trip and notification outcomes | UV-13–UV-16, T-09/T-11, P-12a/b | Classifier panic is accounted as failure; trip panic in normal completion can double-count; hook panic leaves state committed; a nested panic can replace the request panic. Callback fault contract Q-07. gobreaker.go:237 ("cb.afterRequest(generation, false)"), gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:325 ("cb.counts.onFailure()"), gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"), gobreaker.go:354 ("cb.state = state"), gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). |
| Nil and wrong receiver or payload | UV-04, UV-10, UV-11, T-13/T-18 | Nil invocation can panic; wrong valid instance uses its own breaker; caller-supplied outcome applies to the bound breaker. Validation and attribution Q-08, Q-13, Q-18. gobreaker.go:242 ("result, err := req()"), gobreaker.go:268 ("return nil, err"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"). |
| Late or canceled completion | UV-08, UV-14, T-10/T-11, P-05a/b and P-06a/b | Result delivery, classifier invocation, expiry and counters are distinct effects. Both stale Boolean outcomes can advance expired Open before accounting is skipped. Same-generation cancellation is invisible. Q-09 and Q-22. gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))"), gobreaker.go:244 ("return result, err"), gobreaker.go:298 ("state, generation := cb.currentState(now)"), gobreaker.go:299 ("if generation != before {"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"). |
| HalfOpen threshold and order | P-03a/b, P-04a/b, P-14a/b | At capacity, concurrent admission can be refused until success changes generation; failure invalidates other reports. Equality wording and recovery policy Q-10. gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {"), gobreaker.go:317 ("cb.setState(StateClosed, now)"), gobreaker.go:330 ("cb.setState(StateOpen, now)"). |
| Shared downstream | M-01–M-03 | Aligned expiry yielded four trials per wave through three failure cycles. Partial recovery and unbounded Closed admissions are inferred aggregate effects. Q-11. gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:317 ("cb.setState(StateClosed, now)"), gobreaker.go:342 ("cb.setState(StateHalfOpen, now)"), gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)"). |
| Counter wrap | T-15 | Runtime concern inferred from unsigned widths and increments. No wrap stress test. Q-12. gobreaker.go:48 ("Requests             uint32"), gobreaker.go:56 ("c.Requests++"), gobreaker.go:128 ("generation uint64"), gobreaker.go:364 ("cb.generation++"). |
| Upstream test assumptions | TestCustomCircuitBreaker | Wrong receiver at gobreaker_test.go:247. Separate full race run flagged direct private-count read at gobreaker_test.go:258. Follow-up Q-14. |
| Same caller issues another Execute or Allow | UV-03, UV-06, T-03–T-06; P-13a/b | Pending Execute and Allow may overlap. Below capacity, each admits; at capacity, the next rejects. After return, retained result or callback supplies no caller identity. A later admitted workload or report can finish first. Q-15. gobreaker.go:242 ("result, err := req()"), gobreaker.go:265 ("func (tscb *TwoStepCircuitBreaker) Allow() (done func(success bool), err error) {"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"), gobreaker.go:289 ("cb.counts.onRequest()"). |
| Replacement, teardown and references | UV-20, T-13 | Replacement is fresh construction. Callback can retain the original object and original generation; there is no internal per-request storage or retirement event. Runtime cost unmeasured. Q-16. gobreaker.go:142 ("cb := new(CircuitBreaker)"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:299 ("if generation != before {"). |
| Value normalization | UV-21, Configure | Nonpositive defaults are broader in Settings comments than README zero examples. Q-17. gobreaker.go:153 ("if st.Interval <= 0 {"), gobreaker.go:159 ("if st.Timeout <= 0 {"). |
| Reader order and snapshot | UV-12, T-16, P-07a/b and P-08a/b | Lock protects per-call consistency. Counts before State can see a preceding generation and can differ from Counts after it. Q-19. gobreaker.go:207 ("cb.mutex.Lock()"), gobreaker.go:217 ("cb.mutex.Lock()"), gobreaker.go:338 ("cb.toNewGeneration(now)"), gobreaker.go:365 ("cb.counts.clear()"). |
| Requirement control status | T-30–T-34 | Jev did not back O01–O03 under both thresholds. Q-21 and Q-22 were retained from routing. O01 also placed acceptance before function supply. The scope review records that wording issue and keeps the answered check. O02 folds into the existing Q-06. O04 and O05 omit material schedule/lock details in the requirements and fold into Q-05 and Q-01. |
| Inapplicable mechanisms | Scope and lint sweep | There is no installed timer, retry loop, work buffer, channel ownership transfer, destructor or resource release method inside this boundary. State and counts are mutex protected. Real cancellation and replacement effects are covered above. gobreaker.go:229 ("generation, err := cb.beforeRequest()"), gobreaker.go:242 ("result, err := req()"), gobreaker.go:244 ("return result, err"), gobreaker.go:265 ("func (tscb *TwoStepCircuitBreaker) Allow() (done func(success bool), err error) {"), gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)"), gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {"). |

Verification used original source and tests. The 47 source claim checks yielded 45 supported and two unclear, V45 and V46. Both were retained after reading the lock, defer and sample together at gobreaker.go:277-281 and gobreaker.go:294-299. A line that samples time alone does not prove the preceding lock. Both test claim checks were supported. Findings use the actual mutex discipline, distinguish the literal zero-time sentinel from computed deadlines, and separate callback deadlock from test-harness data races. Callback panic experiments support specific schedules; they do not establish intent.

## Executed checks

| Check | Result |
|---|---|
| Canonical catalogue renderer and round trip | PILOT CATALOGUE: OK (055, 119) |
| Matrix stage 1 | Initial FAIL (069): plain state labels and bold abstraction were not parsed. Corrected to template format; CHECK MATRIX: OK (074). |
| Guard script | 17 proven, 0 violations, 3 not-formalizable, 20 total. Boundary output and assumptions in guard-results.txt (068/070 command batch). |
| Matrix stage 2 | CHECK MATRIX: OK (3 rows x 35 events), log 121 |
| Strict sidecar | OK circuitBreaker: 3 states x 35 events = 105 cells, 22 questions, DRs [], log 117. Earlier build warned about dropping README prose citation (090); matching matrix cells retain code evidence and the requirement is mapped in doctrine. |
| DSC and Mermaid | DSC CHECK: OK (3 states x 35 events, 105 cells, 20 guard groups), log 120 |
| Reachability | REACHABILITY CHECK: OK (3/3 states reachable from 'Closed', 0 terminal), log 118 |
| Blind pass | PART-B COVERAGE: OK (35 events, 30 pair orderings); 15 as-is rows reported, logs 060 and 122 |
| Go baseline | PASS, log 025 |
| Go overlay | 10 probes passed (086). Final probe-only race run passed (114), including explicit HalfOpen → Closed assertion. |
| Final full non-race overlay suite and probe-only race suite | PASS, logs 133 and 134. |
| Pilot artifact audit | PILOT DELIVERABLES: OK (presence and source anchor), logs 129 and 140. Git emitted xcrun cache-permission warnings while successfully resolving HEAD. |
| Go full overlay race run | FAIL in upstream TestCustomCircuitBreaker at gobreaker_test.go:258, log 091. See as-is-validation.md. |

The pairs table uses representative orderings for shared mutable effects. Immutable Name reads commute; construction has no prior instance to race; calls on alternate front ends cannot share one public receiver. Alternate same-effect callback/admission schedules are covered in UV and free traces. The displayed pairs are not the Cartesian product of public methods and every fault variant.

The model run classified 126 situational rows including 19 divergences. Each divergence folds into an open Q. No new recurring divergence class can be established from this single run. The prompt did not change.

Counts: 3 states / 35 events (20 undesired) / 15 interaction pairs and 30 orderings / 105 matrix cells / 18 UNSPECIFIED / 0 accidental ignores / 17 guard groups proven / 0 guard violations / 3 not-formalizable / 22 findings or decision gaps / 22 open questions.

## Routing ledger

Ledger file: `routing.sqlite`. All provider reservations settled. The one failed routing command was the pre-provider seam-time batch, S05 citation fragment missing near line 49 (079). The corrected batch used the exact line 50 fragment and all five checks returned (093). No provider failure and no prescribed routing call was skipped.

```json
{
  "committed_or_reserved_microdollars": 22620,
  "limit_microdollars": 2000000,
  "calls": [
    {
      "id": 1,
      "provider": "deepseek-flash",
      "amount_microdollars": 2872,
      "status": "settled"
    },
    {
      "id": 2,
      "provider": "jev",
      "amount_microdollars": 263,
      "status": "settled"
    },
    {
      "id": 3,
      "provider": "deepseek-flash",
      "amount_microdollars": 4339,
      "status": "settled"
    },
    {
      "id": 4,
      "provider": "jev",
      "amount_microdollars": 449,
      "status": "settled"
    },
    {
      "id": 5,
      "provider": "deepseek-flash",
      "amount_microdollars": 4062,
      "status": "settled"
    },
    {
      "id": 6,
      "provider": "jev",
      "amount_microdollars": 403,
      "status": "settled"
    },
    {
      "id": 7,
      "provider": "deepseek-flash",
      "amount_microdollars": 7479,
      "status": "settled"
    },
    {
      "id": 8,
      "provider": "jev",
      "amount_microdollars": 176,
      "status": "settled"
    },
    {
      "id": 9,
      "provider": "jev",
      "amount_microdollars": 63,
      "status": "settled"
    },
    {
      "id": 10,
      "provider": "jev",
      "amount_microdollars": 175,
      "status": "settled"
    },
    {
      "id": 11,
      "provider": "jev",
      "amount_microdollars": 703,
      "status": "settled"
    },
    {
      "id": 12,
      "provider": "jev",
      "amount_microdollars": 140,
      "status": "settled"
    },
    {
      "id": 13,
      "provider": "jev",
      "amount_microdollars": 886,
      "status": "settled"
    },
    {
      "id": 14,
      "provider": "jev",
      "amount_microdollars": 418,
      "status": "settled"
    },
    {
      "id": 15,
      "provider": "jev",
      "amount_microdollars": 192,
      "status": "settled"
    }
  ]
}
```
