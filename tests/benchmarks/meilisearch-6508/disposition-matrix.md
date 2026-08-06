# Disposition Matrix — Meilisearch SearchQueue Admission

<!-- states: CallerCreated, AdmissionSubmitting, Waiting, PermitReceived, Executing, Completed, Rejected, Cancelled, StoredAndEligible, Selected, Granted, Evicted, CapacityUnit, Held, ReleasePending, Returned, Running -->

## Table A — Caller Lifecycle Events

| state | EV-02 PermitRequested | EV-13 PermitReceivedByCaller | EV-20 WaitingCallerCancelled | EV-21 WaitAgeLimitExceeded | EV-17 ExecutingCallerCancelled | EV-16 SearchExecutionFinished |
|---|---|---|---|---|---|---|
| **CallerCreated** | transition → AdmissionSubmitting try_get_search_permit:177-183 | ignore (accidental) → Q-D2 | ignore (accidental) → Q-D2 | ignore (accidental) → Q-D2 | ignore (accidental) → Q-D2 | ignore (accidental) → Q-D2 |
| **Waiting** | ignore (documented) — already waiting | transition → PermitReceived | **UNSPECIFIED → Q-D2** — sender remains in queue search_queue.rs:168 | ignore (accidental) → Q-D2 — only checked after permit L186 | ignore (accidental) → Q-D2 | ignore (accidental) → Q-D2 |
| **PermitReceived** | ignore (documented) — already have permit | ignore (documented) — already received | ignore (accidental) → Q-D2 | transition → Rejected — permit dropped, error returned L186-192 | transition → Returned — implicit Drop fires L58-67 | transition → Completed |
| **Rejected** | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal |
| **Cancelled** | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal |

## Table B — Scheduler Admission Events

| state | EV-04 SchedulerReceivesAdmissionRequest | EV-09 RequestAddedToWaitingPopulation | EV-10 WaitingRequestSelected | EV-11 WaitingRequestRejected | EV-14 PermitDeliveryFailed | EV-26 QueueEntryCeasesToBeEligible |
|---|---|---|---|---|---|---|
| **StoredAndEligible** | ignore (documented) — already stored | ignore (documented) — already in queue | transition → Granted — swap_remove + send L131-138 | transition → Evicted — swap_remove + drop L166-168 | transition → GrantedDead — send fails silently L150 | **UNSPECIFIED → Q-D2** — no pruning path exists |
| **Granted** | ignore (documented) — already granted | ignore (documented) — left queue | ignore (documented) — already selected | ignore (documented) — already granted | ignore (accidental) → Q-D3 — slot lost for turn | ignore (documented) — already removed |
| **Evicted** | ignore (documented) — terminal | ignore (documented) — removed from queue | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal |
| **GrantedDead** | ignore (documented) — recipient gone | ignore (documented) — removed from queue | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal | ignore (documented) — terminal |

## Table C — Permit + Capacity Events

| state | EV-05 ExecutionSlotAvailable | EV-18 PermitReleaseRequested | EV-19 ReleaseSignalProcessed | EV-22 ObsoletePermitReturned |
|---|---|---|---|---|
| **CapacityUnit** | transition → Held — immediate grant L154-159 or refill L148-152 | ignore (accidental) → Q-D1 | ignore (accidental) → Q-D1 | ignore (accidental) → Q-D1 |
| **Held** | ignore (documented) — already held | transition → ReleasePending — explicit drop L52-55 AND implicit Drop L62-67 (D1) | ignore (accidental) → Q-D1 | ignore (accidental) → Q-D1 |
| **ReleasePending** | ignore (accidental) → Q-D1 | ignore (documented) — already releasing | transition → CapacityUnit — one signal per decrement. D1: two signals per explicit drop | ignore (accidental) → Q-D1 |
| **Returned** | ignore (documented) — terminal | ignore (documented) — terminal, idempotent per D1 claim | ignore (documented) — terminal | ignore (documented) — terminal |

## Guard Groups

All `not-formalizable: dynamic-state`. Scheduler loop, admission counter, random selection index.

## Sidecar Completeness

```json
"completeness": {
  "pairs": {"count": 0, "reason": "single-threaded scheduler loop, serialized admission events"},
  "guardGroups": {"count": 0, "reason": "all guards dynamic-state"},
  "coverage": {"count": 2, "reason": "two external sources: caller requests and permit releases"}
}
```
