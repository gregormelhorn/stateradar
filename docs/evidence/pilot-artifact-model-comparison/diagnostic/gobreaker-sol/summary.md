# CircuitBreaker domain behaviour pilot

model routing: on (unevaluated, cascade plan stage 3)
routing variant: routed
Jev model: jev-1.14.0

Scope is one initialized breaker, including the TwoStep wrapper as an alternate public topology. The model uses the three public modes and treats expiry, capacity and outstanding work as guard context. The sidecar stores one transition target per cell. Where a matching HalfOpen outcome can close or reopen, the matrix text and statechart retain both branches. HalfOpen→Open is therefore explicit in the model even though the compact outcome cell projects the success target. The pair catalogue concentrates on independently scheduled admission/observation versus completion or callbacks. Causal stages, immutable Name reads, constructor replacement, and other callback schedules are discussed in the traces. The optional independent traditional review was skipped.

## Counts

| Item | Count |
|---|---:|
| States | 3 |
| Events, including 23 undesired variants | 35 |
| Interaction pairs / orderings | 18 / 36 |
| Matrix cells | 105 |
| UNSPECIFIED | 9 |
| Accidental ignores | 0 |
| Crash-labelled cells with linked questions | 15 |
| Proven guard groups | 14 |
| Guard violations | 0 |
| Not formalizable | 1 |
| Consolidated findings / open questions | 23 / 23 |
| Blind situations reviewed | 135 |
| Blind divergences, each linked to a Q | 31 |

## Findings and coverage

| Case | Catalogue or trace | Observed result and question |
|---|---|---|
| Same-caller acquisition while first is pending | UV-03, T-01, P-03a, P-04a, TestPilotSecondExecuteCompletesFirst | Separate admissions. A later admitted call can finish first. At HalfOpen capacity the contender is refused and receives no handoff. gobreaker.go:277 ("cb.mutex.Lock()") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:289 ("cb.counts.onRequest()") Q-18/Q-23 |
| Same-caller acquisition while report is held | UV-03, T-02, P-03b, TestPilotDuplicateAndMissing | Below cap the second Allow gets its own callback; at cap it is refused. A single report never frees an admission in the same generation. gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:285 ("} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {") gobreaker.go:315 ("cb.counts.onSuccess()") Q-03/Q-04 |
| Missing report, late matching success/failure, stale completion | UV-07/08, T-03, P-05b, TestPilotStaleCompletionRefresh | At-capacity HalfOpen can stay stuck. A current report still affects state; an old report can refresh expiry before discarding its outcome. gobreaker.go:298 ("state, generation := cb.currentState(now)") gobreaker.go:299 ("if generation != before {") gobreaker.go:330 ("cb.setState(StateOpen, now)") gobreaker.go:378 ("cb.expiry = zero") Q-03/Q-06 |
| Duplicate, contradictory and foreign reports | UV-09/10/12, T-04 | Repeated successes can close HalfOpen without distinct successes; contradictory reports serialize, and an old generation is checked only after refresh. Wrong closure and wrong Boolean are caller-attribution faults. gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") gobreaker.go:294 ("cb.mutex.Lock()") gobreaker.go:299 ("if generation != before {") gobreaker.go:316 ("if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {") Q-04/Q-12 |
| Lock-held callback and reentry | UV-17/18/19, P-13b, P-17b, T-09, TestPilotNotifyReentry | ReadyToTrip and OnStateChange run under the mutex. Same-goroutine lock-taking reentry blocks; Name is lock-free. gobreaker.go:202 ("return cb.name") gobreaker.go:207 ("cb.mutex.Lock()") gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") Q-01/Q-02/Q-07 |
| Policy panic, delay and goroutine exit | UV-17/19, T-06, TestPilotPolicyPanicAccounting | Count commits before policy; panic in normal Execute accounting can lead to two failure increments. Slow policy can make a later deadline appear due before the next admission. gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:297 ("now := time.Now()") gobreaker.go:325 ("cb.counts.onFailure()") gobreaker.go:326 ("if cb.readyToTrip(cb.counts) {") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)") Q-08 |
| Notification success or failure before/after commit | UV-18/19, T-07, TestPilotNotifyPanicPrecedence, TestPilotRecoveryNotificationPanicBeforeAdmission | State and reset precede notification. Notification panic can prevent admission after refresh or replace an original request panic during accounting. gobreaker.go:229 ("generation, err := cb.beforeRequest()") gobreaker.go:234 ("defer func() {") gobreaker.go:354 ("cb.state = state") gobreaker.go:356 ("cb.toNewGeneration(now)") gobreaker.go:359 ("cb.onStateChange(cb.name, prev, state)") Q-09/Q-19 |
| Classifier success/failure across refresh | UV-08/15/16, P-10b, P-11b, T-08, TestPilotClassifierWindow | Classification runs outside lock, and stale filtering follows it. Panic can enter the failure defer; exit or block can leave no counted outcome. gobreaker.go:237 ("cb.afterRequest(generation, false)") gobreaker.go:243 ("cb.afterRequest(generation, cb.isSuccessful(err))") gobreaker.go:299 ("if generation != before {") Q-06/Q-10/Q-23 |
| Invalid input and wrong instance | UV-04/11/12/21/22, T-05/T-10 | Nil callback panics at caller. An admitted nil request panics after count increment; a valid wrong receiver uses that object's state. Replacement leaves old callbacks attached to the old instance. gobreaker.go:242 ("result, err := req()") gobreaker.go:268 ("return nil, err") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") Q-12/Q-13/Q-16/Q-20/Q-21 |
| Caller departure or Goexit | UV-07/13, T-11, TestPilotGoexit | Breaker has no cancellation seam; caller exit without a report can leave an admission in the generation. No breaker-owned queue, asynchronous delivery, destructor or shutdown entry point was found in this component. gobreaker.go:235 ("e := recover()") gobreaker.go:236 ("if e != nil {") gobreaker.go:242 ("result, err := req()") gobreaker.go:272 ("tscb.cb.afterRequest(generation, success)") Q-03/Q-11/Q-16 |
| Clock and observation | UV-02/05/06/23, P-09, T-13–T-16 | Eligible callers refresh after strict deadline; Counts reads stored totals. Lock wait and callback timing affect the sample. gobreaker.go:220 ("return cb.counts") gobreaker.go:280 ("now := time.Now()") gobreaker.go:337 ("if !cb.expiry.IsZero() && cb.expiry.Before(now) {") gobreaker.go:341 ("if cb.expiry.Before(now) {") Q-05/Q-07/Q-22 |
| Configured and aggregate bounds | UV-22, T-12, M-01–M-03 | Overflow and aggregate backend effects remain inferred; independent fixed cooldowns can align when callers and failures align. gobreaker.go:56 ("c.Requests++") gobreaker.go:128 ("generation uint64") gobreaker.go:364 ("cb.generation++") gobreaker.go:376 ("cb.expiry = now.Add(cb.timeout)") Q-14/Q-15/Q-17/Q-20 |

## Executed checks

| Command or gate | Result |
|---|---|
| `go test -timeout 20s ./...` | PASS, breaker package; example has no tests (010) |
| `go test -timeout 10s -overlay domain-analysis/circuitBreaker/_probe/overlay.json -run '^TestPilot' -v .` | PASS, nine overlay probes (104); initial seven-probe run also passed (077) |
| `go test -race -timeout 20s -overlay domain-analysis/circuitBreaker/_probe/overlay.json -run '^TestPilot' .` | PASS (115) |
| `go test -race -timeout 30s ./...` | FAIL, upstream TestCustomCircuitBreaker accesses counts without the breaker mutex (gobreaker_test.go:258 vs gobreaker.go:56,289; log 116). Full evidence in as-is-validation.md and retained log. |
| `pilot_artifacts.py catalogue … --check` | PILOT CATALOGUE: OK (125) |
| `check_matrix.py` | CHECK MATRIX: OK (3 rows x 35 events), Stage 1 (068) and Stage 2 (123) |
| `check_guards.py` | Exit 0, 14 proven, 1 not-formalizable, 0 violations. Complete results in guard-results.txt (079–080). |
| `gen_analysis_sidecar.py circuitBreaker --strict` | OK circuitBreaker: 3 states x 35 events = 105 cells, 23 questions, DRs [] (114) |
| `dsc_check.py … --repo . --model as-is.machine.mmd` | DSC CHECK: OK (3 states x 35 events, 105 cells, 15 guard groups) (122) |
| `check_reachability.py … --repo .` | REACHABILITY CHECK: OK (3/3 states reachable from 'Closed', 0 terminal) (121) |
| `part_b_pack.py … --check …/part-b-blind.md` | PART-B COVERAGE: OK (35 events, 36 pair orderings); one self-marked as-is ID, Result (099). |
| `git diff --exit-code -- gobreaker.go gobreaker_test.go README.md` | Exit 0, no diff output (124). macOS xcrun cache warnings on stderr. |

| Cross-artifact counts and link check | Cross-artifact check: 98 draft questions, 105 grid cells, 36 pair traces, 23 open questions, all 31 divergences linked (136). |

## Routing results

All three Flash extraction drafts and their Jev verification completed. All 98 draft questions were disposed or folded; the analysis retained its own citations and added questions from the manual sweep. All Jev batches answered. All four proposed requirement orderings were unclear with scope 0.01–0.02; the cited text did not establish the full asserted sequences. Each has a Q in the traces. No provider API errors or skipped model calls. The initial blind answer stopped normally but failed the coverage check by omitting Result (063). Its output is preserved; a fresh response from the same inspected package passed (066). The diff records shared evidence and catalogue cues that limit blind independence.

Ledger file `routing.sqlite`. Executed status (120):

```json
{
  "committed_or_reserved_microdollars": 36709,
  "limit_microdollars": 2000000,
  "calls": [
    {
      "id": 1,
      "provider": "deepseek-flash",
      "amount_microdollars": 2879,
      "status": "settled"
    },
    {
      "id": 2,
      "provider": "jev",
      "amount_microdollars": 225,
      "status": "settled"
    },
    {
      "id": 3,
      "provider": "deepseek-flash",
      "amount_microdollars": 4813,
      "status": "settled"
    },
    {
      "id": 4,
      "provider": "jev",
      "amount_microdollars": 431,
      "status": "settled"
    },
    {
      "id": 5,
      "provider": "deepseek-flash",
      "amount_microdollars": 9906,
      "status": "settled"
    },
    {
      "id": 6,
      "provider": "jev",
      "amount_microdollars": 787,
      "status": "settled"
    },
    {
      "id": 7,
      "provider": "deepseek-flash",
      "amount_microdollars": 6194,
      "status": "settled"
    },
    {
      "id": 8,
      "provider": "deepseek-flash",
      "amount_microdollars": 8329,
      "status": "settled"
    },
    {
      "id": 9,
      "provider": "jev",
      "amount_microdollars": 125,
      "status": "settled"
    },
    {
      "id": 10,
      "provider": "jev",
      "amount_microdollars": 317,
      "status": "settled"
    },
    {
      "id": 11,
      "provider": "jev",
      "amount_microdollars": 201,
      "status": "settled"
    },
    {
      "id": 12,
      "provider": "jev",
      "amount_microdollars": 192,
      "status": "settled"
    },
    {
      "id": 13,
      "provider": "jev",
      "amount_microdollars": 51,
      "status": "settled"
    },
    {
      "id": 14,
      "provider": "jev",
      "amount_microdollars": 879,
      "status": "settled"
    },
    {
      "id": 15,
      "provider": "jev",
      "amount_microdollars": 697,
      "status": "settled"
    },
    {
      "id": 16,
      "provider": "jev",
      "amount_microdollars": 51,
      "status": "settled"
    },
    {
      "id": 17,
      "provider": "jev",
      "amount_microdollars": 469,
      "status": "settled"
    },
    {
      "id": 18,
      "provider": "jev",
      "amount_microdollars": 163,
      "status": "settled"
    }
  ]
}
```
