# CircuitBreaker domain-behaviour pilot

model routing: on (unevaluated, cascade plan stage 3)
routing variant: routed
Jev pin: jev-1.14.0

Scope: one constructed breaker and its TwoStep public wrapper, including synchronous callback behavior and caller-held admission continuations. The Execute and TwoStep topologies use independently constructed breaker identities. The model projects Closed, Open and HalfOpen. Due deadlines, HalfOpen budget and generation matches are guards. A caller's active, abandoned or reported work is a separate lifecycle recorded in the traces. Request execution, external transport and cancellation policy belong to the caller. No neighbouring statechart was present in this checkout. observed-in-code gobreaker.go:183 ("func NewTwoStepCircuitBreaker(st Settings) *TwoStepCircuitBreaker {") gobreaker.go:242 ("result, err := req()") gobreaker.go:271 ("return func(success bool) {") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:299 ("if generation != before {") gobreaker.go:334 ("func (cb *CircuitBreaker) currentState(now time.Time) (State, uint64) {").

[Open domain questions](open-questions.md) · [As-is model](as-is.machine.mmd) · [Disposition matrix](disposition-matrix.md) · [Part B comparison](part-b-diff.md)

## Findings and coverage

Seventeen grouped findings or contract gaps correspond to 17 open domain questions. No question records a decision.

| Case | Variant or trace | Verified observation or unresolved limit | Question |
| --- | --- | --- | --- |
| Lazy expiry and snapshot timing | UV-08, P-12a/b, T-06, T-08 | Counts reads the stored snapshot. State, admission or completion can renew a due generation. Equality alone does not trigger expiry. observed-in-code gobreaker.go:211 ("state, _ := cb.currentState(now)") gobreaker.go:220 ("return cb.counts") gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") gobreaker.go:341 ("if cb.expiry.Before(now) {") | Q-01 |
| Omitted completion, abandonment, slow work | UV-01/02, T-02 | HalfOpen at budget can remain blocked indefinitely; later matching success closes, whereas failure reopens. observed-in-code gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:317 ("cb.setState(StateClosed, now)") gobreaker.go:330 ("cb.setState(StateOpen, now)") gobreaker.go:378 ("cb.expiry = zero") | Q-02 |
| Duplicate and contradictory reports | UV-04, T-01 | One continuation can close HalfOpen by reporting success twice. Opposite payloads apply while current in lock order. observed-in-code gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:299 ("if generation != before {") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {") | Q-03 |
| Stale accounting and refresh | UV-05, P-04a/b, T-05/T-06 | Stale effects include classifier invocation and Open to HalfOpen notification after expiry; contribution is skipped. observed-in-code gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)") | Q-04 |
| Same-lock callback reentry | UV-10/11, T-07 | OnStateChange and ReadyToTrip run under lock; callback entry into Counts or State can block permanently. observed-in-code gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") | Q-05 |
| Callback panic, block and Goexit | UV-09/10/11, T-09/T-14 | Commit timing differs per hook. A ReadyToTrip panic during normal Execute accounting can cause two failure increments, and notification panic can leave state already committed. Goexit runs defers but reports no recoverable panic. observed-in-code gobreaker.go:235 ("e := recover()") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:295 ("defer cb.mutex.Unlock()") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:354 ("cb.state = state") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") | Q-06 |
| Wrong receiver and wrong payload | UV-06/13, T-10/T-13 | Valid incorrect receiver and valid incorrect report act on supplied targets; no identity validation matches the payload to work. observed-in-code gobreaker.go:229 ("generation, err := cb.beforeRequest()") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:303 ("if success {") | Q-07 |
| Invalid invocation and nil panic | UV-07/12, T-10/T-12 | Nil request can panic after admission. Nil/zero receiver responses vary. Nil panic recovery is runtime dependent. observed-in-code gobreaker.go:136 ("type TwoStepCircuitBreaker struct {") gobreaker.go:235 ("e := recover()") gobreaker.go:242 ("result, err := req()") gobreaker.go:268 ("return nil, err") | Q-08 |
| Counter and generation bounds | UV-04/05, T-11 | uint32 counters can wrap, and retained uint64 generation tags can theoretically alias after wrap. Exact-once accounting is separately disproven. observed-in-code gobreaker.go:48 ("Requests             uint32") gobreaker.go:128 ("generation uint64") gobreaker.go:364 ("cb.generation++") | Q-09 |
| Refusal timing and diagnostics | UV-03/11, T-07 | Refusal skips work after decision but still acquires the mutex. observed-in-code gobreaker.go:231 ("return nil, err") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:284 ("return generation, ErrOpenState") gobreaker.go:286 ("return generation, ErrTooManyRequests") | Q-10 |
| Shared-dependency recovery | M-01 to M-03 | Failure/recovery schedules can align independently configured breaker instances. Analytic probes only; arrival and load assumptions are explicit. Inferred from gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:317 ("cb.setState(StateClosed, now)") gobreaker.go:330 ("cb.setState(StateOpen, now)") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)") | Q-11 |
| Half-open boundary and close/reopen policy | Admit, Report, P-01a/b and P-10a/b | Error at budget, success at threshold and failure reopening are distinct. Refresh alone leaves zero admissions. observed-in-code gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {") gobreaker.go:330 ("cb.setState(StateOpen, now)") gobreaker.go:342 ("cb.setState(StateHalfOpen, now)") gobreaker.go:365 ("cb.counts.clear()") | Q-12 |
| Outstanding closure and wrapper replacement | UV-06/12/14, T-10/T-13 | An old continuation holds a wrapper reference. Serialized wrapper overwrite can redirect it to a different breaker at matching generation. Plain variable rebind keeps original ownership. observed-in-code gobreaker.go:266 ("generation, err := tscb.cb.beforeRequest()") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:299 ("if generation != before {") | Q-13 |
| Test replay | Custom transition test | The expiry assertion for the custom transition reads the default breaker's expiry. observed-in-tests gobreaker_test.go:247 ("assert.True(t, defaultCB.expiry.IsZero())") | Q-14 |
| Second acquisition | UV-03, P-01a/b, P-02a/b, T-02/T-03/T-04 | Same caller can overlap Execute or Allow. Below budget admissions remain independent; at budget a second call rejects while first is pending or outstanding. There is no queue. Second admitted work may return first. observed-in-code gobreaker.go:242 ("result, err := req()") gobreaker.go:271 ("return func(success bool) {") gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:289 ("cb.counts.onRequest()") | Q-15 |
| Request panic and reporting precedence | Panic, UV-09/10/11, T-09/T-14 | Ordinary request panic attempts failure accounting before repanic; accounting hook failure can prevent the advertised original outcome. observed-in-code gobreaker.go:235 ("e := recover()") gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:238 ("panic(e)") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") | Q-16 |
| Plausible settings faults | UV-14, T-12 | Negative durations select defaults. README mentions zero and Settings contract addresses nonpositive values. observed-in-code gobreaker.go:89 ("// If Interval is less than or equal to 0, the CircuitBreaker doesn't clear internal Counts during the closed state.") gobreaker.go:93 ("// If Timeout is less than or equal to 0, the timeout value of the CircuitBreaker is set to 60 seconds.") gobreaker.go:153 ("if st.Interval <= 0 {") gobreaker.go:159 ("if st.Timeout <= 0 {") | Q-17 |

Explicit teardown and destructor-driven dual release are inapplicable to this boundary. The admission and reporting paths are a synchronous function call or a caller-owned continuation. Neither transfers ownership through a breaker-managed channel, and there is no release method in the public wrapper seam. Copying, abandonment and stale callbacks were still probed. observed-in-code gobreaker.go:228 ("func (cb *CircuitBreaker) Execute(req func() (interface{}, error)) (interface{}, error) {") gobreaker.go:265 ("func (tscb *TwoStepCircuitBreaker) Allow() (done func(success bool), err error) {") gobreaker.go:271 ("return func(success bool) {"). Scheduler retries and persisted queues are absent from that seam, so their limits are inapplicable. All matrix states have single-event reachability; no additional pair-derived edge was required.

## Counts

3 states / 26 events including 14 undesired variants / 16 interaction pairs (32 orderings) / 78 cells / 6 UNSPECIFIED / 4 accidental ignores / 9 guard groups proven / 0 guard violations / 2 not formalizable / 17 grouped findings / 17 open questions. The 115 blind situations include 60 convergent, 11 convergent-hole, 41 divergences folded into open questions, and 3 Part-B blind spots. Five event IDs had self-reported as-is dependence. The diff records additional dependence on catalogue observations and the compound disposition vocabulary drift.

## Executed checks

| Check | Output |
| --- | --- |
| Catalogue render and byte identity | PILOT CATALOGUE: OK (052, 116) |
| Stage 1 and Stage 2, per-run matrix | CHECK MATRIX: OK (3 rows x 26 events) (069, 118) |
| Guard proof program | 9 proven, 0 violations, 2 inspected but unproven. Full output in guard-results.txt (071). |
| Strict sidecar | OK circuitBreaker: 3 states x 26 events = 78 cells, 17 questions, DRs [] (121) |
| DSC model/schema/citations | DSC CHECK: OK (3 states x 26 events, 78 cells, 11 guard groups) (122) |
| Reachability | REACHABILITY CHECK: OK (3/3 states reachable from 'Closed', 0 terminal) (123) |
| Blind diff closure | 115 situations classified; all 41 divergences link to existing open questions (127). |
| Blind table coverage | PART-B COVERAGE: OK (26 events, 32 pair orderings). 5 as-is event IDs (061, 124). |
| Upstream Go tests | go test -timeout=10s ./... passed (009, 119) |
| Overlay probe tests | 8 initial passes (035); 10 final passes (102), 10 passes under race detector (103). All used finite timeouts. Zero compilation or test failures. |
| Tracked files | git diff --exit-code on source, README, existing test and module files: exit 0, empty diff (120). |

Preserved issues: the first catalogue render rejected list-valued prose fields (048), corrected to the renderer's single-line text. The first matrix gate found unmarked state rows and unresolved links while the questions file was being authored (057), then passed. A diagnostic reader attempted to access a null Jev value (083), corrected and rerun (099). Git emitted xcrun sandbox cache warnings (097, 120) with exit 0. The overlay uses `-vet=off` for injected test discovery; the separate upstream Go run used default vet settings. Reentry observation was bounded, with permanent wait inferred from lock semantics. Shared upstream load probes were analytic. The optional traditional reviewer session was omitted.

## Routing exceptions and ledger

The first implementation draft returned `finish_reason=length` at 12,000 output tokens (023). The prescribed rerun at 16,384 completed (032); the truncated text is retained. Eight draft citations failed and were re-cited from original source, with dispositions in extraction.md. No provider HTTP or authentication failures. All seam, ordering and finding batches answered. None of the three proposed requirement-backed orderings passed scope review, including the supported choice with scope 0.03. All answers were retained. No model call was skipped due to budget. Companion claims were disabled per the run brief.

Ledger file: routing.sqlite

```json
{
  "committed_or_reserved_microdollars": 39909,
  "limit_microdollars": 2000000,
  "calls": [
    {
      "id": 1,
      "provider": "deepseek-flash",
      "amount_microdollars": 2423,
      "status": "settled"
    },
    {
      "id": 2,
      "provider": "jev",
      "amount_microdollars": 177,
      "status": "settled"
    },
    {
      "id": 3,
      "provider": "deepseek-flash",
      "amount_microdollars": 15539,
      "status": "settled"
    },
    {
      "id": 4,
      "provider": "deepseek-flash",
      "amount_microdollars": 3443,
      "status": "settled"
    },
    {
      "id": 5,
      "provider": "jev",
      "amount_microdollars": 347,
      "status": "settled"
    },
    {
      "id": 6,
      "provider": "deepseek-flash",
      "amount_microdollars": 7005,
      "status": "settled"
    },
    {
      "id": 7,
      "provider": "jev",
      "amount_microdollars": 510,
      "status": "settled"
    },
    {
      "id": 8,
      "provider": "deepseek-flash",
      "amount_microdollars": 7086,
      "status": "settled"
    },
    {
      "id": 9,
      "provider": "jev",
      "amount_microdollars": 207,
      "status": "settled"
    },
    {
      "id": 10,
      "provider": "jev",
      "amount_microdollars": 51,
      "status": "settled"
    },
    {
      "id": 11,
      "provider": "jev",
      "amount_microdollars": 873,
      "status": "settled"
    },
    {
      "id": 12,
      "provider": "jev",
      "amount_microdollars": 704,
      "status": "settled"
    },
    {
      "id": 13,
      "provider": "jev",
      "amount_microdollars": 164,
      "status": "settled"
    },
    {
      "id": 14,
      "provider": "jev",
      "amount_microdollars": 51,
      "status": "settled"
    },
    {
      "id": 15,
      "provider": "jev",
      "amount_microdollars": 470,
      "status": "settled"
    },
    {
      "id": 16,
      "provider": "jev",
      "amount_microdollars": 108,
      "status": "settled"
    },
    {
      "id": 17,
      "provider": "jev",
      "amount_microdollars": 300,
      "status": "settled"
    },
    {
      "id": 18,
      "provider": "jev",
      "amount_microdollars": 185,
      "status": "settled"
    },
    {
      "id": 19,
      "provider": "jev",
      "amount_microdollars": 86,
      "status": "settled"
    },
    {
      "id": 20,
      "provider": "jev",
      "amount_microdollars": 180,
      "status": "settled"
    }
  ]
}
```
