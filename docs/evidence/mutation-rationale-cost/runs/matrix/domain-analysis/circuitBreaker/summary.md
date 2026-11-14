# CircuitBreaker domain behaviour pilot

model routing: on (unevaluated, cascade plan stage 3)
routing variant: matrix
Jev: jev-1.14.0. Baseline: 27b8e2cfc65aacd09abb3968455e4b01df4a83fa.

The primary deliverable is [open-questions.md](open-questions.md). The matrix projects a constructed instance and divides HalfOpen by admission budget. In-flight work, callback execution and mutex ownership are separate tracks described in the traces. Compound cells show one target and describe other branches in text. There are no terminal states or behavioural decisions in this run. No library, existing test, or configuration files were changed.

## Verified findings and coverage

| Applicable case | Evidence and consequence | Question |
|---|---|---|
| Expiry with no input, at equality, or overdue | UV-19, T-11 and T-20. State, admission and outcome can observe a strict deadline; Counts alone can expose stale counters. gobreaker.go:220, 337-342. | Q-01, Q-02 |
| Same caller repeats while Execute is pending | UV-03, T-02. Channel probe reproduces the second request finishing first. Same gate applies at the half-open boundary. gobreaker.go:242, 277-289. | Q-04, Q-07 |
| Same caller repeats while returned callback is outstanding | UV-03, T-03, P-06b. Distinct Allow calls consume distinct budget slots; one success does not refund or satisfy the other. gobreaker.go:266-273, 285-289. | Q-04, Q-07 |
| Duplicate and opposite outcomes | UV-11, UV-12, T-01 and T-14. The lock serializes reports; generation equality does not enforce once-only accounting. A repeated success can close with one distinct trial on a two-trial budget. gobreaker.go:271-272, 294-299, 315-318. | Q-03, Q-11 |
| Omitted, cancelled or delayed outcomes | UV-09, UV-10, UV-15, T-04 to T-06, T-10 and T-13. Without a later report, saturated half-open can stay full; a matching report can close or open it. Stale reports may reconcile time and notify before suppressing their accounting. The classifier can run regardless of accounting staleness. gobreaker.go:243, 271-272, 285-289, 298-306, 334-345. | Q-05, Q-06, Q-17, Q-19 |
| Callback completion and failure on both sides of commit | UV-16 to UV-18, T-06 to T-09. Trip policy reentry and notification reentry block on the same mutex. A policy panic can record two failures; a notification panic can replace an original request panic after transition commit. Classifier reentry is outside the lock and may advance generation. gobreaker.go:207, 234-243, 294-295, 325-327, 354-359. | Q-09, Q-10, Q-12, Q-15, Q-16 |
| Wrong receiver versus wrong hint or report | UV-07, UV-13, UV-14, T-12 and T-15. Valid wrong receivers operate independently; transferred reports target the captured wrapper. Nil and zero-value paths have different failure behavior. gobreaker.go:137, 228-243, 266-273. | Q-08, Q-13, Q-17 |
| Shared resource across instances | T-16 to T-18. Fixed local expiry can align half-open bursts. The capacity calculation comes from the modeled schedules. No service load test was performed. gobreaker.go:285, 342, 376. | Q-14 |
| Shutdown, destructor, queue inventory and retry | No public shutdown or implicit resource release path, no library queue or autonomous retry loop. Caller lifetime can end before accounting. The closure can keep the wrapper reachable. gobreaker.go:234-244, 262-274, 334-380. | Q-06, Q-17 |

The README rule for the default trip threshold and its stale-result sentence were both supported in Jev Choice but fell below the provisional scope cutoff. The two routed control verdicts were voided. Q-18 and Q-19 preserve the specific orderings. The pilot also records timing scope for exact expiry and instant rejection.

## Counts

4 states, 30 events including 19 undesired variants, 28 interaction pairs and 56 orderings, 120 cells, 23 UNSPECIFIED cells, 0 accidental ignores. 14 guard groups proven, 0 guard violations, 2 not formalizable. 17 consolidated behavior findings or contract gaps and 2 additional routing-scope questions give 19 open questions. The existing-test race is a separate validation finding. Part B returned 178 situations, with 86 convergent, 32 convergent-hole, 51 divergences folded into open questions, 1 catalogue artefact and 8 Part B blind spots.

## Executed checks and retained failures

- Baseline `go test -timeout=15s ./...` passed, log 011.
- Initial overlay passed seven probes, log 057. Expanded bounded overlay passed nine probes, log 108. The final nine probe cases also passed under `-race`, log 117.
- Full `go test -race -timeout=25s -count=1 -overlay domain-analysis/circuitBreaker/overlay.json ./...` failed, log 105. Existing TestCustomCircuitBreaker reads private counts at gobreaker_test.go:258 while another goroutine increments them. The production public Counts path takes the mutex. See as-is-validation.md.
- Catalogue render and matrix render succeeded, logs 118 and 119. The initial matrix wrapper run reported missing Q links before the question file existed, log 064. Re-run passed after the question file was written.
- Guard check completed with zero guard failures, log 129. The same run emitted the distinct-admission accounting counterexample `[limit = 2, successes = 2, requests = 1]`. See guard-results.txt.
- Blind coverage passed, log 125. The final catalogue includes a remembrance clarification from the diff. The dispatch package is preserved as sent.
- Source/test/configuration comparison to HEAD returned clean, log 127. The macOS git launcher emitted an xcrun cache warning in that command. The pilot read-only count command in log 132 initially assumed keyed cells; the corrected count in log 133 iterated the sidecar list. The checker invocation with an unsupported help argument in log 112 failed independently of its successful gate invocation.
- The benchmark inputs provide no neighbouring model. The optional separate reviewer pass was not run. This pilot exercised ordering and callback defects with bounded Go probes; some wall-time and shared-resource schedules remain source-derived.

## Final gate output

- Log 137, exit 0. `OK circuitBreaker: 4 states x 30 events = 120 cells, 19 questions, DRs []`
- Log 138, exit 0. `CHECK MATRIX: OK (4 rows x 30 events)`
- Log 139, exit 0. `DSC CHECK: OK (4 states x 30 events, 120 cells, 16 guard groups)`
- Log 140, exit 0. `REACHABILITY CHECK: OK (4/4 states reachable from 'StateClosed', 0 terminal)`
- Log 141, exit 0. `PILOT CATALOGUE: OK`
- Log 142, exit 0. `MATRIX FIELDS: OK (domain-analysis/circuitBreaker/disposition-matrix.md)`
- Log 143, exit 0. `PILOT DELIVERABLES: OK (presence and source anchor; run semantic gates separately)`

The audit emitted the macOS git launcher cache warning and returned exit 0.

## Routing ledger

Drafts and all seam, scope, verification and blind requests completed. No provider failure or skipped provider call. Two draft citations failed their exact-fragment check and were corrected from the original sources. Jev did not judge those two fragments in draft-verify. Inspection and disposition details are in extraction.md. Part B was dispatched once after its final package inspection.

Ledger `routing.sqlite`. Status output follows.

```json
{
  "committed_or_reserved_microdollars": 27688,
  "limit_microdollars": 2000000,
  "calls": [
    {
      "id": 1,
      "provider": "deepseek-flash",
      "amount_microdollars": 2777,
      "status": "settled"
    },
    {
      "id": 2,
      "provider": "jev",
      "amount_microdollars": 222,
      "status": "settled"
    },
    {
      "id": 3,
      "provider": "deepseek-flash",
      "amount_microdollars": 7103,
      "status": "settled"
    },
    {
      "id": 4,
      "provider": "jev",
      "amount_microdollars": 599,
      "status": "settled"
    },
    {
      "id": 5,
      "provider": "deepseek-flash",
      "amount_microdollars": 4097,
      "status": "settled"
    },
    {
      "id": 6,
      "provider": "jev",
      "amount_microdollars": 400,
      "status": "settled"
    },
    {
      "id": 7,
      "provider": "deepseek-flash",
      "amount_microdollars": 10075,
      "status": "settled"
    },
    {
      "id": 8,
      "provider": "jev",
      "amount_microdollars": 194,
      "status": "settled"
    },
    {
      "id": 9,
      "provider": "jev",
      "amount_microdollars": 879,
      "status": "settled"
    },
    {
      "id": 10,
      "provider": "jev",
      "amount_microdollars": 46,
      "status": "settled"
    },
    {
      "id": 11,
      "provider": "jev",
      "amount_microdollars": 705,
      "status": "settled"
    },
    {
      "id": 12,
      "provider": "jev",
      "amount_microdollars": 123,
      "status": "settled"
    },
    {
      "id": 13,
      "provider": "jev",
      "amount_microdollars": 321,
      "status": "settled"
    },
    {
      "id": 14,
      "provider": "jev",
      "amount_microdollars": 147,
      "status": "settled"
    }
  ]
}
```
