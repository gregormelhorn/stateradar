# channelPool domain-behaviour pilot

model routing: on (unevaluated, cascade plan stage 3)
routing variant: routed
Jev model: jev-1.14.0

The analysis covers one channelPool, its public Pool interface, optional concrete Ping, injected callbacks, and shutdown. It uses README.md as requirements and channel_rpc_test.go as the existing test suite. The matrix tracks publication, detachment, waiter presence and the reachable state with both queued and idle work. Guard context represents instantaneous accounting, callbacks and per-call phases. Released_Waiting is a pool-lifecycle sink and retains complete API rows. Domain decisions remain open.

## Findings and coverage

The 22 numbered findings and open decisions are in [open-questions.md](open-questions.md). Some are documented behavior gaps or contract choices. The shutdown and readiness schedules were observed with bounded probes. The race is detector-confirmed. Memory-cost and aggregate traffic effects are inferred.

| Case | Evidence and outcome | Open decision |
|---|---|---|
| Pending Get at Release | P-03a, TestPilotPendingRelease. Existing waiter remains blocked. Late Put does not close its value or wake it. channel.go:137, 176, 208–209, 227 and 238 | Q-01, Q-05 |
| Stale admission across Release | P-03a, TestPilotReleaseAdmissionWindow. At capacity queues after detach. Below capacity returns ErrClosed. channel.go:131–150 | Q-01 |
| Readiness changes between select and lock | P-01a, TestPilotAdmissionWindow. At capacity idle and waiter coexist and a later Get overtakes. Below capacity opens another resource despite idle availability. channel.go:110, 131, 133, 135, 154 and 190 | Q-02 |
| Close frees accounting before callback outcome | P-02a, TestPilotCloseAdmission. Pending waiter survives even when new Factory succeeds. Cleanup error returned to close caller. channel.go:211–212 | Q-03, Q-10 |
| Second acquisition while first pending | UV-GetAgain, T-01, TestPilotSameCallerAndAbandonment. Two independent channels and a single Put wakes one. channel.go:134–137 and 179–185 | Q-16 |
| Second acquisition while first held | UV-GetAgain, T-02, same probe. Distinct checkout below cap; saturated caller is enqueued if idle unavailable. No caller identity. pool.go:12 and channel.go:110–135 | Q-16 |
| External departure, no return | UV-AbandonGet, T-03, same probe. Private wait does not end. channel.go:137 | Q-04 |
| External departure, later matching Put | UV-AbandonGet, T-03. Handoff can go to abandoned worker; forwarding strategy controls caller-side retention or block. channel.go:148 and 183 | Q-04 |
| Overflow, expiry and late cleanup | P-04a/b, P-05b, T-10, T-15. Cleanup can be skipped after detach; earlier errors propagate only on selected paths. channel.go:118, 144, 194–196 and 208–212 | Q-05, Q-10, Q-17 |
| Teardown and buffered checkout / health result | P-08a/b, P-13a/b, T-16. Started Ping success can return a value. Failure can re-enter loop after skipped cleanup. A committed private handoff can still complete. channel.go:110–129, 137–148 and 220–229 | Q-06, Q-07, Q-13 |
| Ping access racing Release | TestPilotPingRace, detector log 101. Unsynchronized channel.go:220 read vs channel.go:229 write. Mutex protecting Release does not order that read. channel.go:123 is a second unsynchronized read site under code inspection | Q-06 |
| Callback success / failure across teardown | P-08a/b, P-09a/b, P-10a/b. Dynamic Factory and direct Close serialize with detachment. Entered Ping and captured drain Close can finish after detachment. Their returned-error dispositions differ. channel.go:124, 131–161, 206–212 and 225–241 | Q-06, Q-08, Q-09, Q-10 |
| Reentrant or stalled callback | UV-CallbackDelay, T-07. Factory and ordinary Close block Len reentry as confirmed by TestPilotLockedReentry. Constructor and drain run outside pool lock. channel.go:83, 96, 154, 206–212 and 232–241 | Q-08, Q-21 |
| Factory faults and config | UV-FactoryFault, UV-BadConfig, T-06, T-07. Nil Config crashes; zero caps accepted; negative timeout disables age check. Factory startup error rolls back previous successes; published Factory panic leaves mutex held. channel.go:59, 83–88 and 154–160 | Q-09, Q-12 |
| Duplicate, foreign, nil or contradictory ownership | UV-BadOwnership, UV-WrongPoolPut, P-07a/b, T-05, T-14. Non-nil duplicate returns can be delivered twice; a wrong receiver is separate from a wrong payload. channel.go:168, 183, 190 and 211 | Q-11, Q-22 |
| Read count | P-06, P-11, P-12 and P-14. Len samples idle occupancy, and a captured channel can outlive detachment. channel.go:96–98 and 247 | Q-14 |
| Queue tail and accounting retention | T-04, UV-LatePut. Dequeue reslices without clearing old backing slot; detach leaves slice and accounting. Real cost depends on workload and reachability. channel.go:181–182 and 225–241 | Q-18 |
| Missing work, restart, duplicate release | UV-NewOmitted, UV-GetOmitted, UV-ReleaseOmitted, UV-ReleaseAgain, T-08. New pool is independent, repeat Release can return while drain active, and omitted teardown has no automatic replacement. channel.go:69, 224–241 | Q-15, Q-19 |
| Shared-resource waves | M-01–M-03. Three inferred schedules over a shared backend. Demand can align, while no backoff or recovery reset exists in the component. channel.go:133–159 | Q-20 |
| Autonomous callback duplication and stale delivery | Inapplicable for synchronous injected returns. No callback delivery channel exists. Already-invoked callbacks can finish across detach where lock ordering permits it. channel.go:154, 212, 220 and 241 | Q-06, Q-08, Q-21 |

## Finding verification

The Step-8 batch records 51 separate source checks for code and 3 for tests. Of the code checks 46 were supported and 5 unclear. Kept the five on re-read as follows.

- Q-02-C9: the scheduling overlay establishes the whole sequence. channel.go:110 and channel.go:131–154 together preserve the selected default without a receive recheck.
- Q-09-C30: channel.go:83–88 checks the error, then wraps the returned value without testing it.
- Q-09-C31: channel.go:131 and channel.go:154–160 establish lock, callback, then manual unlock on the normal returns. Escaping panic bypasses it. Ordinary Close differs by using defer at channel.go:207.
- Q-11-C38 and Q-22-C51: channel.go:167–196 has only nil, lifecycle, queue and readiness guards. The duplicate-ownership probe confirms the non-nil duplicate effect. The explicit close-then-return schedule additionally follows channel.go:202–212.
- ErrClosed and ErrMaxActiveConnReached are literal error values, not computed sentinel comparisons. The capacity mismatch is a reachability issue for the latter's return branch. The race detector confirms the direct Ping read/write concurrency defect. The lock-window behaviors are ordering defects or open contract choices and need no data race on protected fields.
- The separate traditional reviewer was optional and was skipped. Retention cost, arbitrary callback effects and multi-instance load were not measured. Overlay noncompletion observations are bounded; the source inventory establishes the absence of a future internal wake for the stranded states.

## Counts and executed checks

| Measure | Count |
|---|---:|
| States | 6 |
| Events including variants | 35 |
| Undesired variants | 22 |
| Pairs / orderings | 16 / 32 |
| Matrix cells | 210 |
| UNSPECIFIED | 0 |
| Accidental ignores | 44 |
| Crash-linked handles | 21 |
| Guard groups proven / violations / not formalizable | 20 / 0 / 3 |
| Consolidated findings / open questions | 22 / 22 |
| Blind situation rows / divergences | 95 / 49 |

| Executed command | Result |
|---|---|
| pilot_artifacts.py catalogue --check | PASS, log 144 |
| per-component check_matrix.py | PASS 6 × 35, logs 083 and 160 |
| per-component check_guards.py | PASS 20 proof groups and 3 inspection-only groups, log 090. Formatting corrected after log 087 joined two group lines |
| gen_analysis_sidecar.py --strict | PASS 210 cells and 22 questions, log 161 |
| dsc_check.py --repo . --model as-is.machine.mmd | PASS, log 162. Initial run log 092 flagged missing diagram edges, corrected after reviewing Put vs receipt |
| check_reachability.py --repo . | PASS 6/6, log 163 |
| part_b_pack.py --check part-b-blind.md | PASS 35 events, 32 orderings, log 158 |
| go test -timeout=20s ./... | FAIL, TestPool_Get times out blocked at channel.go:137. log 009 |
| Remaining upstream tests, bounded subset | PASS, log 029 |
| Go probe overlay, finite timeout | PASS 11, log 100. Separate first runs logs 063 and 072 |
| Original-source overlay with -race | FAIL, TestPilotPingRace detects expected data race, log 101 |

The blind package retained the Feature and usage prose from README with verbatim event contract comments. The inspected package and returned table are retained separately from the final, clarified catalogue. The blind output covered every declared ID. The Part B diff records the 95 reviewed situations and closes all divergences to existing open decisions. Observed-in-code material in the catalogue limits independence on some rows.

## Routing status and call exceptions

All paid DeepSeek Flash and Jev calls returned. No provider failure was observed. The first two package-only attempts were rejected before dispatch (log 052 no regex match, log 053 requirements section below size floor). Prepared complete README behavior prose solved this. README draft C3 failed its citation check and was re-cited manually. An RPC Jev batch was rejected for a missing literal citation fragment before response, log 128. All three originally requested checks then ran with the corrected fragment, log 137. No answered check was retried. None of the three requirement-scope attempts passed the paired Choice/scope criterion. All are questions with judgments in the traces.

Ledger file: routing.sqlite

```json
{
  "committed_or_reserved_microdollars": 19217,
  "limit_microdollars": 2000000,
  "calls": [
    {
      "id": 1,
      "provider": "deepseek-flash",
      "amount_microdollars": 1971,
      "status": "settled"
    },
    {
      "id": 2,
      "provider": "jev",
      "amount_microdollars": 164,
      "status": "settled"
    },
    {
      "id": 3,
      "provider": "deepseek-flash",
      "amount_microdollars": 859,
      "status": "settled"
    },
    {
      "id": 4,
      "provider": "jev",
      "amount_microdollars": 52,
      "status": "settled"
    },
    {
      "id": 5,
      "provider": "deepseek-flash",
      "amount_microdollars": 3259,
      "status": "settled"
    },
    {
      "id": 6,
      "provider": "jev",
      "amount_microdollars": 317,
      "status": "settled"
    },
    {
      "id": 7,
      "provider": "deepseek-flash",
      "amount_microdollars": 3099,
      "status": "settled"
    },
    {
      "id": 8,
      "provider": "jev",
      "amount_microdollars": 297,
      "status": "settled"
    },
    {
      "id": 9,
      "provider": "deepseek-flash",
      "amount_microdollars": 6623,
      "status": "settled"
    },
    {
      "id": 10,
      "provider": "jev",
      "amount_microdollars": 106,
      "status": "settled"
    },
    {
      "id": 11,
      "provider": "jev",
      "amount_microdollars": 89,
      "status": "settled"
    },
    {
      "id": 12,
      "provider": "jev",
      "amount_microdollars": 404,
      "status": "settled"
    },
    {
      "id": 13,
      "provider": "jev",
      "amount_microdollars": 107,
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
      "amount_microdollars": 359,
      "status": "settled"
    },
    {
      "id": 16,
      "provider": "jev",
      "amount_microdollars": 861,
      "status": "settled"
    },
    {
      "id": 17,
      "provider": "jev",
      "amount_microdollars": 96,
      "status": "settled"
    },
    {
      "id": 18,
      "provider": "jev",
      "amount_microdollars": 136,
      "status": "settled"
    }
  ]
}
```
