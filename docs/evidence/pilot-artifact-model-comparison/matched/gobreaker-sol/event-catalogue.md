# Event catalogue

<!-- event-ids: Create Admit State Counts Name Report Return Panic Classify TripPolicy Notify Expiry UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| Create | external | Lifecycle owner | Construct an instance and configure its policies. observed-in-code gobreaker.go:142 ("cb := new(CircuitBreaker)") |
| Admit | external | Request initiator | Execute or Allow attempts one new admission. observed-in-code gobreaker.go:281 ("state, generation := cb.currentState(now)") |
| State | external | Observer | Read the state of an instance. observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") |
| Counts | external | Observer | Read a snapshot of five counters. observed-in-code gobreaker.go:220 ("return cb.counts") |
| Name | external | Observer | Read the configured name through either wrapper. observed-in-code gobreaker.go:202 ("return cb.name") |
| Report | external | Continuation holder | Invoke Allow's returned completion callback with a success boolean. observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") |
| Return | external | Execute request callback | Return a result and an error from admitted request work. observed-in-code gobreaker.go:242 ("result, err := req()") |
| Panic | external | Execute request callback | Panic from admitted work. observed-in-code gobreaker.go:237 ("cb.afterRequest(generation, false)") |
| Classify | internal | IsSuccessful policy | Classify the error from Execute request work. observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") |
| TripPolicy | internal | ReadyToTrip policy | Evaluate a copied counter snapshot after a closed failure. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") |
| Notify | internal | State change observer | Invoke configured notification with name and old and new modes. observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") |
| Expiry | internal | Clock sampled during State, admission or completion | Evaluate deadline on an eligible operation. observed-in-code gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") |
| UV-01 | external | Continuation holder | Omit a report, including after the caller abandons admitted work. A later report may or may not arrive. observed-in-code gobreaker.go:271 ("return func(success bool) {") |
| UV-02 | external | Execute request owner | Slow, blocked, abandoned or Goexit request work; unissued admission or caller-side cancellation. observed-in-code gobreaker.go:242 ("result, err := req()") |
| UV-03 | external | Request initiator | Same caller executes again while original work is pending, or calls Allow again while first continuation is outstanding. Concurrent Allow can also overlap before the first return. observed-in-code gobreaker.go:277 ("cb.mutex.Lock()") |
| UV-04 | external | Continuation holder | Repeat the same callback with identical or contradictory payloads, including overlapping calls. observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") |
| UV-05 | external | Request or continuation holder | Old admitted work returns, panics, or reports after a clear, possibly after the next open interval. observed-in-code gobreaker.go:299 ("if generation != before {") |
| UV-06 | external | Continuation holder | Wrong boolean or continuation, pooled/reassigned wrapper, or fabricated current report; nil callback after rejected admission. observed-in-code gobreaker.go:271 ("return func(success bool) {") |
| UV-07 | external | Execute request owner | Pass nil request or panic with nil payload. observed-in-code gobreaker.go:235 ("e := recover()") |
| UV-08 | external | Observer / clock context | Omit or delay a refreshing call, read Counts first, or sample exactly at the deadline; also repeated/out-of-order reads. observed-in-code gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") |
| UV-09 | external | Injected IsSuccessful | Block, panic, Goexit, re-enter, or return valid but wrong classification, including work already stale. observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") |
| UV-10 | external | Injected ReadyToTrip | Block, panic, Goexit, re-enter, or return a valid but unintended decision. observed-in-code gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") |
| UV-11 | external | Injected OnStateChange | Block, panic, Goexit, re-enter, or misdeliver an observation after a state commit. observed-in-code gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") |
| UV-12 | external | Lifecycle and API owner | Use zero-value or nil receiver, copy a live breaker, replace wrapper or try teardown without an API. observed-in-code gobreaker.go:136 ("type TwoStepCircuitBreaker struct {") |
| UV-13 | external | API and request owner | Call wrong valid instance or provide a valid callback/payload for the wrong request. observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()") |
| UV-14 | external | Lifecycle owner | Missing, delayed, duplicate or replacement construction, or valid but unintended Settings. observed-in-code gobreaker.go:153 ("if st.Interval <= 0 {") |

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| Create: Lifecycle owner | UV-14 | UV-14 | UV-14 | UV-14 | UV-14 | UV-14 | UV-14 |
| Admit: Request initiator | UV-02 | UV-02 | UV-03 | UV-03 | UV-03 | UV-03 | UV-07, UV-12, UV-13, UV-14 |
| State: Observer | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-13 |
| Counts: Observer | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-13 |
| Name: Observer | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-13 |
| Report: Continuation holder | UV-01 | UV-05 | UV-04 | UV-05 | UV-04 | UV-06 | UV-06 |
| Return: Execute request callback | UV-02 | UV-05 | UV-03 | UV-05 | UV-05 | UV-03 | UV-07, UV-13 |
| Panic: Execute request callback | UV-02 | UV-05 | UV-03 | UV-05 | UV-05 | UV-03 | UV-07, UV-13 |
| Classify: IsSuccessful policy | UV-09 | UV-09 | UV-09 | UV-05 | UV-09 | UV-09 | UV-09 |
| TripPolicy: ReadyToTrip policy | UV-10 | UV-10 | UV-10 | UV-10 | UV-10 | UV-10 | UV-10 |
| Notify: State change observer | UV-11 | UV-11 | UV-11 | UV-11 | UV-11 | UV-11 | UV-11 |
| Expiry: Clock sampled during State, admission or completion | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Admit → Report | New admission and existing report on same breaker; half-open at budget |
| P-01b | Report → Admit | New admission and existing report on same breaker; half-open at budget |
| P-02a | Admit → Return | New admission and previous Execute return on same breaker |
| P-02b | Return → Admit | New admission and previous Execute return on same breaker |
| P-03a | Admit → Panic | New admission and previous Execute panic on same breaker |
| P-03b | Panic → Admit | New admission and previous Execute panic on same breaker |
| P-04a | State → Report | Observer and delayed report on same breaker |
| P-04b | Report → State | Observer and delayed report on same breaker |
| P-05a | Counts → Report | Snapshot and report on same breaker |
| P-05b | Report → Counts | Snapshot and report on same breaker |
| P-06a | State → Return | Observer and returning Execute on same breaker |
| P-06b | Return → State | Observer and returning Execute on same breaker |
| P-07a | Counts → Return | Snapshot and returning Execute on same breaker |
| P-07b | Return → Counts | Snapshot and returning Execute on same breaker |
| P-08a | State → Panic | Observer and panicking Execute on same breaker |
| P-08b | Panic → State | Observer and panicking Execute on same breaker |
| P-09a | Counts → Panic | Snapshot and panic on same breaker |
| P-09b | Panic → Counts | Snapshot and panic on same breaker |
| P-10a | State → Admit | Independent observer and initiator at an Open expiry |
| P-10b | Admit → State | Independent observer and initiator at an Open expiry |
| P-11a | Counts → Admit | Snapshot and initiator in Closed or HalfOpen |
| P-11b | Admit → Counts | Snapshot and initiator in Closed or HalfOpen |
| P-12a | State → Counts | Independent observers on a breaker with due expiry |
| P-12b | Counts → State | Independent observers on a breaker with due expiry |
| P-13a | Name → Admit | Name observer and initiator sharing one breaker |
| P-13b | Admit → Name | Name observer and initiator sharing one breaker |
| P-14a | Name → Report | Name observer and continuation holder sharing one breaker |
| P-14b | Report → Name | Name observer and continuation holder sharing one breaker |
| P-15a | Name → Return | Name observer and Execute callback sharing one breaker |
| P-15b | Return → Name | Name observer and Execute callback sharing one breaker |
| P-16a | Name → Panic | Name observer and panicking Execute callback sharing one breaker |
| P-16b | Panic → Name | Name observer and panicking Execute callback sharing one breaker |

## Remembrance semantics

observed-in-code gobreaker.go:271 ("return func(success bool) {"). A caller-held continuation records a generation and retains its wrapper. No individual completion or queue is stored by the breaker. Lifecycle replacement creates an independent instance. A late callback refreshes then compares generation. gobreaker.go:298 ("state, generation := cb.currentState(now)"). gobreaker.go:299 ("if generation != before {"). observed-in-code gobreaker.go:56 ("c.Requests++"). Requests counts admissions per generation, independent of caller departure. Successful reports update outcome counters until a state change or interval refresh clears all five. A half-open failure goes straight to a state change. Rejection and stale contribution do not increment outcomes. gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {"). gobreaker.go:330 ("cb.setState(StateOpen, now)"). gobreaker.go:365 ("cb.counts.clear()"). No queue backing store. Retained closure footprint or collection timing is a runtime question. observed-in-code gobreaker.go:128 ("generation uint64"). Only the current generation is retained, bounded by uint64. Counts use uint32 fields. HalfOpen has no expiry. gobreaker.go:48 ("Requests             uint32"). gobreaker.go:378 ("cb.expiry = zero").

## Lock-discipline annotation

observed-in-code gobreaker.go:207 ("cb.mutex.Lock()"). State holds the mutex across refresh and synchronous notification. Counts takes it only for the snapshot. Name reads the configured name without locking. gobreaker.go:217 ("cb.mutex.Lock()"). gobreaker.go:202 ("return cb.name"). observed-in-code gobreaker.go:277 ("cb.mutex.Lock()"). Admission holds the mutex across refresh, possible OnStateChange and its count decision. Completion holds it across refresh, ReadyToTrip and OnStateChange. gobreaker.go:294 ("cb.mutex.Lock()"). gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {"). gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)"). observed-in-code gobreaker.go:242 ("result, err := req()"). Execute invokes request work and classifier after admission unlock and before completion lock. The contracts do not specify same-instance reentry or callback failure and blocking behavior. gobreaker.go:95 ("// ReadyToTrip is called with a copy of Counts whenever a request fails in the closed state."). gobreaker.go:100 ("// OnStateChange is called whenever the state of the CircuitBreaker changes."). gobreaker.go:102 ("// IsSuccessful is called with the error returned from a request.").

## Catalogue notes

The public topologies wrap Execute work directly or issue a continuation through Allow. Read methods exist in both. Reports and Execute results do not share one publicly constructed backing breaker across topologies. A construction targets a new breaker identity. Clock evaluation is internal.

## Event annotations

### Create
- gate: Settings values and optional callbacks
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")
- coverage:
  - loss: UV-14
  - delay: UV-14
  - duplication: UV-14
  - out-of-order: UV-14
  - contradiction: UV-14
  - commission: UV-14
  - value: UV-14

### Admit
- gate: Service state, sampled deadline and admission count
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")
- coverage:
  - loss: UV-02
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-03
  - contradiction: UV-03
  - commission: UV-03
  - value: UV-07, UV-12, UV-13, UV-14

### State
- gate: Service state and sampled deadline
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")
- coverage:
  - loss: UV-08
  - delay: UV-08
  - duplication: UV-08
  - out-of-order: UV-08
  - contradiction: UV-08
  - commission: UV-08
  - value: UV-13

### Counts
- gate: No payload
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")
- coverage:
  - loss: UV-08
  - delay: UV-08
  - duplication: UV-08
  - out-of-order: UV-08
  - contradiction: UV-08
  - commission: UV-08
  - value: UV-13

### Name
- gate: No payload
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")
- coverage:
  - loss: UV-08
  - delay: UV-08
  - duplication: UV-08
  - out-of-order: UV-08
  - contradiction: UV-08
  - commission: UV-08
  - value: UV-13

### Report
- gate: Payload boolean plus service generation and state
- upstream_guards: Only a successful Allow returns a callable completion; caller report cardinality, truth and ownership are undocumented. gobreaker.go:268 ("return nil, err")
- coverage:
  - loss: UV-01
  - delay: UV-05
  - duplication: UV-04
  - out-of-order: UV-05
  - contradiction: UV-04
  - commission: UV-06
  - value: UV-06

### Return
- gate: Payload error plus service generation and state
- upstream_guards: Execute invokes request work only following successful admission. The example uses the initialized breaker and propagates HTTP/read errors. The public topology permits arbitrary request functions. gobreaker.go:231 ("return nil, err"). example/http_breaker.go:26 ("func Get(url string) ([]byte, error) {")
- coverage:
  - loss: UV-02
  - delay: UV-05
  - duplication: UV-03
  - out-of-order: UV-05
  - contradiction: UV-05
  - commission: UV-03
  - value: UV-07, UV-13

### Panic
- gate: Payload recover value plus service generation and state
- upstream_guards: Execute invokes request work only following successful admission. The example uses the initialized breaker and propagates HTTP/read errors. The public topology permits arbitrary request functions. gobreaker.go:231 ("return nil, err"). example/http_breaker.go:26 ("func Get(url string) ([]byte, error) {")
- coverage:
  - loss: UV-02
  - delay: UV-05
  - duplication: UV-03
  - out-of-order: UV-05
  - contradiction: UV-05
  - commission: UV-03
  - value: UV-07, UV-13

### Classify
- gate: Payload error, configured classifier and result
- upstream_guards: Dispatch is private; no independent public event injection. gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))")
- coverage:
  - loss: UV-09
  - delay: UV-09
  - duplication: UV-09
  - out-of-order: UV-05
  - contradiction: UV-09
  - commission: UV-09
  - value: UV-09

### TripPolicy
- gate: Service state and callback result
- upstream_guards: Dispatch is private; no independent public event injection. gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {")
- coverage:
  - loss: UV-10
  - delay: UV-10
  - duplication: UV-10
  - out-of-order: UV-10
  - contradiction: UV-10
  - commission: UV-10
  - value: UV-10

### Notify
- gate: Distinct state change and configured callback
- upstream_guards: Dispatch is private; no independent public event injection. gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)")
- coverage:
  - loss: UV-11
  - delay: UV-11
  - duplication: UV-11
  - out-of-order: UV-11
  - contradiction: UV-11
  - commission: UV-11
  - value: UV-11

### Expiry
- gate: Service state and strict expiry-before-now comparison
- upstream_guards: Dispatch is private; no independent public event injection. gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {")
- coverage:
  - loss: UV-08
  - delay: UV-08
  - duplication: UV-08
  - out-of-order: UV-08
  - contradiction: UV-08
  - commission: UV-08
  - value: UV-08

### UV-01
- gate: Service state and admission budget
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")

### UV-02
- gate: Service state, actual callback outcome and generation
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")

### UV-03
- gate: Service state and admission budget
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")

### UV-04
- gate: Service generation, state, payload and lock order
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")

### UV-05
- gate: Service generation after refresh
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")

### UV-06
- gate: Payload and continuation identity
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")

### UV-07
- gate: Payload and runtime recover behavior
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")

### UV-08
- gate: Operation type and strict deadline
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")

### UV-09
- gate: Callback control flow, result and generation
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")

### UV-10
- gate: Callback control flow and result
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")

### UV-11
- gate: Callback control flow
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")

### UV-12
- gate: Receiver validity and per-object lifetime
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")

### UV-13
- gate: Receiver identity or payload supplied by caller
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")

### UV-14
- gate: Settings values, callback availability and object identity
- upstream_guards: No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go:21 ("")
