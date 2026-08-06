# Part B — Blind Requirements-Only Analysis: SearchQueue

**Inputs:** Sections 4 (R-01..R-17), 5 (EV-01..EV-26), 6 (candidate states), 7 (extended state)
**No code, no tests, no implementation details, no issue information**
**Timestamp:** 2026-08-06T16:43:42Z

---

## 1. Required state model (derived from requirements)

### Request lifecycle (R-06, R-17)
`Created → Waiting → PermitReceived → Executing → Completed | Rejected | Cancelled | LimiterUnavailable | Obsolete`

Terminal exclusivity (R-17): exactly one of Rejected / Cancelled / LimiterUnavailable / ObsoleteAfterExcessiveWait / PermitReceived-completed.

### Admission-claim lifecycle (R-04, R-08, R-09)
`NotRegistered → StoredAndEligible → Selected → Granted | Rejected | NoLongerEligible`

R-08/R-09 require a transition `WaitingCallerCancelled → NoLongerEligible`, i.e. a caller reaching a terminal state MUST invalidate the scheduler-side claim before that claim can affect capacity, selection, eviction, or metrics.

### Permit lifecycle (R-06, R-07, INV-08, INV-09)
`Available → Held → Returned`

Exactly-one: one held permit produces exactly one logical return (R-07, INV-08). Duplicate cleanup must not admit an additional search (INV-09). This implies release must be **idempotent**: any second release signal for the same permit must be a no-op.

### Scheduler (R-13, INV-12)
`Running` — must survive caller cancellation, delivery failure, dropped channels, rejections.

### Capacity (R-01, R-02, R-15)
- Execution slots: bounded by parallelism; a grant consumes one; a release returns exactly one.
- Waiting slots: bounded by capacity; only **eligible** requests occupy them (R-09, INV-02, INV-14).

### Metrics (R-14, INV-06, INV-13)
- searches_running = live permits held.
- searches_waiting = live eligible waiters.
Both with at most bounded scheduler-turn staleness; never indefinitely counting terminal requests.

## 2. Required transitions (disposition matrix, critical cells)

| State | Event | Required disposition | Requirement |
|---|---|---|---|
| Waiting | WaitingCallerCancelled | transition → NoLongerEligible; claim must not affect capacity/selection/metrics afterward | R-08, R-09, INV-03, INV-04, INV-05 |
| Waiting | WaitingCapacityFull | transition → Rejected (per policy), caller unblocked with terminal error | R-05, R-11, INV-10 |
| Waiting | WaitingRequestSelected | transition → PermitOffered | R-04 |
| Waiting | WaitAgeLimitExceeded | transition → NoLongerEligible (must not begin obsolete search) | R-10, INV-11 |
| StoredAndEligible | WaitingCallerCancelled | transition → NoLongerEligible | R-08, R-09 |
| StoredAndEligible | PermitGrantAttempted | transition → PermitOffered; on delivery failure → return capacity + continue selection this turn | R-12, INV-07 |
| StoredAndEligible | QueueEntryCeasesToBeEligible | transition → Removed; capacity + metrics reflect removal | R-09, INV-06, INV-14 |
| PermitOffered | PermitDeliveryFailed | transition → Returned + select next eligible waiter immediately | R-12, INV-07 |
| PermitOffered | PermitReceivedByCaller | transition → Held | R-06 |
| Held | PermitReleaseRequested | transition → Returned; exactly one capacity unit restored; further releases are no-ops | R-07, INV-08, INV-09 |
| Held | ExecutingCallerCancelled | transition → Returned (implicit release), exactly one unit | R-07 |
| Returned | PermitReleaseRequested | IGNORE (idempotent) | INV-08, INV-09 |
| PermitReceived | WaitAgeLimitExceeded | transition → Obsolete; permit returned exactly once; caller unblocked with terminal error | R-10, R-11, INV-11 |

**Required cells that the requirements imply but an implementation might miss:**
1. (Waiting/StoredAndEligible, WaitingCallerCancelled) → NoLongerEligible — R-08/R-09 make this mandatory.
2. (PermitOffered, PermitDeliveryFailed) → Returned + immediate progress — R-12/INV-07.
3. (Returned, PermitReleaseRequested) → IGNORE — INV-08/INV-09 demand idempotence.
4. (Waiting, WaitAgeLimitExceeded) → ineligibility **before or at** selection, not only after receipt — R-10's spirit: don't spend grants on obsolete demand.

## 3. Required invariants (from requirements alone)

All 15 invariants from section 12 are derivable:
- INV-01: parallelism is a hard bound; nothing downstream of a release may create extra grants beyond genuinely freed slots.
- INV-02/06/13/14: populations and metrics contain only live eligible work.
- INV-03/04/05: terminal callers cannot be selected, cannot execute, cannot distort others.
- INV-07/12: delivery failure costs nothing but one selection step; the turn continues.
- INV-08/09: release is idempotent.
- INV-10/11: rejection and obsolescence are final; associated permits return.
- INV-15: one caller-visible terminal outcome per attempt.

## 4. Open questions (requirements-level)

Q-B1: What mechanism makes a stored admission claim ineligible when its caller terminates? (R-08/R-09 require it; the requirements do not prescribe the mechanism — could be lazy detection at delivery, periodic pruning, or an explicit cancellation channel.)

Q-B2: How is exactly-once release proven when both explicit and implicit cleanup paths exist for one permit? (INV-08/09 require idempotence — e.g., a once-flag.)

Q-B3: Does wait-age enforcement act on the claim while waiting (proactive expiry) or only on receipt (reactive drop)? R-10 permits reactive, but reactive expiry wastes queue capacity and a grant; proactive ineligibility is the cleaner reading of R-09.

Q-B4: Which population do eviction and selection use? R-05 + R-09 imply only eligible members.

---

## 5. Part B summary

| Metric | Count |
|---|---|
| States (5 regions) | 14 |
| Required mandatory transitions | 12 |
| Invariants derivable from requirements | 15 |
| Requirement-level open questions | 4 |
| Key requirement implications | cancellation⇒ineligibility; delivery-failure⇒immediate progress; release⇒idempotent; metrics⇒live-only; eviction⇒eligible-only |
