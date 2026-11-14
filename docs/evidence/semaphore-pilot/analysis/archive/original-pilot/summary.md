# Weighted semaphore pilot

model routing: on (unevaluated, cascade plan stage 3)  
routing variant: routed

One `semaphore.Weighted` instance and its Context boundary. No decisions were adopted. The main deliverable is [open-questions.md](open-questions.md). See the [as-is model](as-is.machine.mmd), [matrix](disposition-matrix.md), [traces](adversarial-traces.md) and [blind comparison](part-b-diff.md). The state grid tracks the queue at mutex boundaries. Per-invocation admission and holder progress and the signed-counter domain appear as companion state axes in the chart and extraction. Counts below are for the declared grid.

## Findings

- **Zero-weight progress (Q-01, Q-13).** At full capacity, canceling a positive head can leave the newly exposed zero-weight head asleep. The probe showed that `TryAcquire(0)` still fails with that head queued and `Release(0)` runs notification and completes it. Whether zero weight is supported is open.
- **Post-panic consistency (Q-04).** `Release` subtracts before it checks for over-release, then unlocks and panics. Recovering and then trying to acquire weight two on a size-one instance succeeds in the probe. Whether the recovered instance is supported remains open.
- **Ownership and order (Q-05–Q-08, Q-10–Q-12).** An invocation can complete ahead of an earlier invocation delayed before admission. Two calls from the same logical requester account independently. Pending grant can roll back before return, and cancellation after a successful return leaves charge held. Wrong Release can consume another holding, even without panic. TryAcquire can wait on its internal mutex despite bypassing the request queue.
- **Input and seam contract (Q-02, Q-03, Q-09).** Oversize waits off queue until Done. Signed weights and capacities are unchecked. Injected Context methods can affect progress and failure outside the mutex.

## Coverage

| Case | Catalogue or trace | Cited finding in linked analysis | Decision |
|---|---|---|---|
| Full-capacity cancellation with zero tail | UV-ContextOrder / UV-Weight, P-07a, T-10 | G-07 skips at exactly zero free, while G-05 would grant; tested later Release(0) and no completion prior to it | Q-01, Q-13 |
| Below-capacity cancellation and FIFO | ContextDone / Grant, P-06a, T-10 | Rescan can grant tail; failed fit blocks smaller successors | Q-12 |
| Oversized and deadlines | UV-Weight / UV-Delay, T-01 | Oversized waits outside the queue; callers can still acquire; nil Done never fires | Q-02 |
| Signed inputs and sentinel | UV-Weight, T-05 | Unchecked charge, subtraction and signed wrap; zero is literal | Q-03 |
| Recovery and wrong ownership | UV-RepeatRelease / UV-UnownedRelease, P-08a/b | Panic leaves mutation, and a plausible aggregate debit can spend another holder’s weight | Q-04, Q-07 |
| Omitted or delayed teardown and restart | UV-Abandon / UV-Delay / UV-Recreate, T-02/T-07/T-13 | Queued entry, detached element and held aggregate have separate lifetimes; old instance continues when used | Q-05 |
| Second acquisition while first pending | UV-RepeatAcquire, P-05a, P-06a/b | Two goroutines can queue separately, one Release(1) grants one; later invocation can finish first if it queues or admits first | Q-06, Q-10, Q-12 |
| Second acquisition while first held | UV-RepeatAcquire / UV-RepeatTry, P-05b | New successful acquire consumes another unit; full capacity causes deferral or failed try | Q-06, Q-12 |
| Wrong receiver versus wrong lifetime | UV-WrongReceiver / UV-ForeignContext, T-06 | Wrong receiver changes another aggregate; foreign Context governs the selected acquisition | Q-08 |
| Callback loss, spontaneous input and teardown | UV-ContextFault / UV-RepeatedDone, T-08/T-09 | Done before lock; Err after cleanup; repeat standard cancel is idempotent. Nil or inconsistent custom operations propagate | Q-09 |
| Cancel, grant and return ordering | P-03a/b, P-04a/b, P-07b, T-04/T-12/T-13 | Rollback in both queued cancellation continuations, no auto-release after success, transient grant visible | Q-10 |
| Observation to lock and commit | TryAcquire / Acquire, P-02a/b, T-03 | Capacity/queue are first sampled under mutex, Done rechecked under lock; wait on lock can delay return | Q-11 |
| Queue backlog, lifecycle overlap and grant vs. return | Grant / UV-Abandon, T-11/T-14 | List has no configured bound and FIFO grant does not enforce goroutine return order | Q-05, Q-12 |
| Missing shutdown, implicit destructor, shared reset and retries | Extraction and invariants | No constructor-to-shutdown path, destructor, shared event or retry scheduler in the API. Release/notification is an in-instance queue drain. | Q-05 for caller ownership |

## Executed checks

- The canonical catalogue rendered successfully (log 115). An early render rejected array-shaped annotation fields (log 035). The annotations were corrected to the renderer’s single-line text contract.
- Initial matrix check reported row-header markup, missing draft Q links, and missing abstraction label (log 055). Corrected stage check passed (log 089). Final checks follow.
- CHECK MATRIX: OK (3 rows x 19 events) (../logs/119.{stdout,stderr}).
- OK weightedSemaphore: 3 states x 19 events = 57 cells, 13 questions, DRs [] (../logs/120.{stdout,stderr}).
- DSC CHECK: OK (3 states x 19 events, 57 cells, 9 guard groups) (../logs/121.{stdout,stderr}).
- REACHABILITY CHECK: OK (3/3 states reachable from 'Acquire_NoWaiters', 0 terminal) (../logs/122.{stdout,stderr}).
- PART-B COVERAGE: OK (19 events, 16 pair orderings) (../logs/123.{stdout,stderr}).
- Guard script passed (log 118). [Full results and boundary probes](guard-results.txt). Eight proven, one dynamic-state select left unproven, zero guard violations. Proofs use NAT-01 and do not establish intent or exclude the reproduced zero-head liveness case.
- Earlier strict sidecar generation warned about a host stdlib path (log 104). The verbatim Go CancelFunc citation remains in extraction; the matrix uses its repository-local use site with the contract cross-reference. Final sidecar generated cleanly.
- Upstream `go test -timeout=30s ./semaphore` (log 012), upstream race run (log 100), full repository `go test -timeout=30s ./...` (log 117), and final race overlay with five focused probes repeated five times (log 111) passed. No test failures occurred. [Test replay and commands](as-is-validation.md).
- Git reported only the untracked analysis directory (log 113), and listed no tracked differences from HEAD (log 124). Both git reads emitted a macOS xcrun cache warning.

## Blind comparison

19 events and 16 pair orderings were covered across 109 rows. Distinct situations share IDs legitimately. Classification: 24 convergent, 50 convergent-hole, 30 divergence, 2 artefact, 3 pass-B-blind-spot. All divergences link to a Q. Some matches rely on as-is catalogue observations. The preserved package is the exact input, before the two catalogue clarifications. No independent traditional reviewer was run.

## Counts

3 states / 19 events including 13 undesired variants / 8 interaction pairs (16 orderings) / 57 cells / 0 UNSPECIFIED / 6 accidental ignores / 8 guard groups proven / 0 guard violations / 1 not formalizable / 13 consolidated findings / 13 open questions. Three conditional crash cells in the Context-fault column carry Q-09; over-release crash alternatives are documented under Q-04. No behavioural decisions.

## Routing ledger

Four draft-verify calls, three callee batches, one ordering batch, two finding-verification batches and one fresh blind dispatch completed with Jev pinned to `jev-1.14.0` on each Jev call. No provider failures or skipped model calls. One README draft claim failed local citation verification and was re-cited by inspection; Jev did not receive the rejected claim. All three ordering checks were unclear with scope below 0.5; they remain questions. No competing or companion claims were sent.

Ledger file: `routing.sqlite`.

```json
{
  "committed_or_reserved_microdollars": 16218,
  "limit_microdollars": 2000000,
  "calls": [
    {
      "id": 1,
      "provider": "deepseek-flash",
      "amount_microdollars": 803,
      "status": "settled"
    },
    {
      "id": 2,
      "provider": "jev",
      "amount_microdollars": 51,
      "status": "settled"
    },
    {
      "id": 3,
      "provider": "deepseek-flash",
      "amount_microdollars": 2185,
      "status": "settled"
    },
    {
      "id": 4,
      "provider": "jev",
      "amount_microdollars": 210,
      "status": "settled"
    },
    {
      "id": 5,
      "provider": "deepseek-flash",
      "amount_microdollars": 2633,
      "status": "settled"
    },
    {
      "id": 6,
      "provider": "jev",
      "amount_microdollars": 216,
      "status": "settled"
    },
    {
      "id": 7,
      "provider": "deepseek-flash",
      "amount_microdollars": 2488,
      "status": "settled"
    },
    {
      "id": 8,
      "provider": "jev",
      "amount_microdollars": 237,
      "status": "settled"
    },
    {
      "id": 9,
      "provider": "deepseek-flash",
      "amount_microdollars": 6503,
      "status": "settled"
    },
    {
      "id": 10,
      "provider": "jev",
      "amount_microdollars": 343,
      "status": "settled"
    },
    {
      "id": 11,
      "provider": "jev",
      "amount_microdollars": 46,
      "status": "settled"
    },
    {
      "id": 12,
      "provider": "jev",
      "amount_microdollars": 111,
      "status": "settled"
    },
    {
      "id": 13,
      "provider": "jev",
      "amount_microdollars": 113,
      "status": "settled"
    },
    {
      "id": 14,
      "provider": "jev",
      "amount_microdollars": 177,
      "status": "settled"
    },
    {
      "id": 15,
      "provider": "jev",
      "amount_microdollars": 102,
      "status": "settled"
    }
  ]
}
```
