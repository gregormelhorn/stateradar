# Disposition Matrix — valkey-glide Inflight Permit

<!-- states: CapacityAvailable, NoCapacity, RequestPending, CallerTimedOut, RequestCompleted, RequestAbandoned, PermitReleased -->

## Events

| state | reserve_request | command_completes | timeout_fires | release_permit | internal_cleanup | reserve_fails |
|---|---|---|---|---|---|---|
| **CapacityAvailable** | transition → RequestPending — counter decremented mod.rs:908-925 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 — nothing to release | ignore (accidental) → Q-01 | handle — returns Err, counter unchanged mod.rs:914 |
| **NoCapacity** | handle — reserve fails, returns false mod.rs:914 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 — nothing to release | ignore (accidental) → Q-01 | handle — returns false |
| **RequestPending** | ignore (accidental) → Q-01 — already reserved | transition → RequestCompleted — send_command returned | transition → CallerTimedOut — run_with_timeout expired mod.rs:565 | ignore (accidental) → Q-02 — permit not released until command completes | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 |
| **CallerTimedOut** | ignore (accidental) → Q-01 — already reserved | ignore (accidental) → Q-03 — internal request still running, completion happens in background | ignore (accidental) → Q-01 — already timed out | **UNSPECIFIED → Q-04** — THE BUG. Requirement 3 says "release immediately." Code does NOT release here; it waits for send_command to return (line 637). | transition → RequestAbandoned — internal request eventually completes | ignore (accidental) → Q-01 |
| **RequestCompleted** | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | transition → PermitReleased mod.rs:920-922 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 |
| **RequestAbandoned** | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-02 — permit was or will be released via internal cleanup | transition → PermitReleased — eventual release | ignore (accidental) → Q-01 |
| **PermitReleased** | transition → RequestPending — new permit cycle | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | handle — idempotent, counter += 1 (Req 6) mod.rs:921 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 |

## Critical Finding

**Q-04: CallerTimedOut → PermitReleased transition missing.**

The column `release_permit` in state `CallerTimedOut` is `UNSPECIFIED`.
Requirement 3 states: "A request that times out from the caller's perspective
releases its caller-facing capacity immediately." The code does NOT implement
this — `release_inflight_request()` at `socket_listener.rs:637` runs only after
`send_command` returns, which may be long after the timeout.

Additionally, the `send_command` function at `mod.rs:565` wraps the command in
`run_with_timeout`, which uses `tokio::time::timeout`. When the timeout fires,
the inner future (the Redis command) continues executing. The `ClientWrapper`
owned by the inner future may retain a clone of the `Arc<AtomicIsize>` inflight
counter, keeping it alive beyond the caller's timeout.

This creates two coupled defects:
1. The permit is not released when the timeout fires (missing transition).
2. The permit may be held by the abandoned internal request until it completes.

Impact per Requirement 5: "A stalled request to one cluster node must not
exhaust capacity for unrelated healthy nodes." When a node becomes unresponsive,
every request to that node acquires a permit via `reserve_inflight_request`,
times out, but never releases the permit. Healthy nodes are blocked because
`inflight_requests_allowed` stays at or below zero.

ODC: fault F-07 (lifecycle coupling; secondary F-01 missing transition), trigger: step-4 matrix walk

---

## Sidecar Completeness

```json
"completeness": {
  "pairs": {"count": 0, "reason": "single permit lifecycle, no concurrent event sources at permit level"},
  "guardGroups": {"count": 0, "reason": "all guards dynamic-state (AtomicIsize load/fetch_add)"},
  "coverage": {"count": 1, "reason": "one external source: caller submitting requests"}
}
```
