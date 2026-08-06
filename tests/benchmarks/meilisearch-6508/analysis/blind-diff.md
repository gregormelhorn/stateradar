# Blind Diff — SearchQueue

**Commit:** fff2ef5a42658b16a937d922aabc3fb7f89f2018
**Timestamp:** 2026-08-06T16:43:42Z
**External bug info:** NOT consulted

## Classification

A: requirement semantics missing from implementation model
B: implementation-only accidental state
C: legitimate refinement
D: missing/ambiguous requirement
E: possible implementation defect
F: test-coverage gap
G: runtime detail outside scope

---

## D1 — Exactly-once release (Part A Q-01 vs Part B INV-08/INV-09)

- **Part B requirement:** `Held → Returned` exactly once; `Returned → IGNORE` on repeat; idempotence mandatory.
- **Part A observed:** explicit `Permit::drop(self)` emits signal 1; implicit `Drop::drop` then emits signal 2. Every explicit release = two signals. `saturating_sub` clamps the metric; the second signal can grant a second waiter.
- **Classification: E (possible implementation defect).** Critical: cascades to INV-01 (parallelism) via duplicate grants and metric drift.
- Part B required this transition unconditionally; Part A shows it violated on the production path (all routes use explicit drop).

## D2 — Cancelled waiters never become ineligible (Part A Q-02 vs Part B R-08/R-09)

- **Part B requirement:** `(Waiting, WaitingCallerCancelled) → NoLongerEligible` is a MANDATORY transition. Claims of terminal callers must not affect capacity, eviction, selection, or metrics.
- **Part A observed:** cell is UNSPECIFIED. The scheduler's population (`Vec<oneshot::Sender>`) has no pruning path. Dead entries persist until randomly selected or evicted; `searches_waiting()` counts them indefinitely; eviction can hit live waiters.
- **Classification: E.** Critical. This is the "caller-terminal transition that does not synchronize with scheduler-owned state" from the success criteria, found exactly as the benchmark predicts.

## D3 — Failed delivery without immediate progress (Part A Q-03 vs Part B R-12/INV-07)

- **Part B requirement:** `PermitOffered × PermitDeliveryFailed → Returned + select next eligible waiter immediately`.
- **Part A observed:** `let _ = channel.send(...)`; failure ignored; slot idle until next release signal.
- **Classification: E.** High.

## D4 — Running metric drifts on refill grants (Part A Q-04 vs Part B INV-13/R-14)

- **Part B requirement:** searches_running = live held permits, bounded staleness only.
- **Part A observed:** refill grants decrement without re-incrementing; metric drifts to 0 while searches run; immediate-admission gate reads corrupted value and over-admits.
- **Classification: E.** High. Amplifies D1's parallelism cascade.

## D5 — Obsolete-wait cleanup only post-grant (Part A Q-05 vs Part B R-10/R-09)

- **Part B requirement:** wait-age limit should render the claim ineligible, ideally before a grant is spent (Q-B3: reactive permitted, proactive cleaner).
- **Part A observed:** elapsed checked only after permit receipt; obsolete request occupied queue capacity, consumed a grant, then released it — twice (D1).
- **Classification: E (partial) / D.** The letter of R-10 (no obsolete execution) is met; the spirit (don't waste eligibility/capacity on obsolete demand) is not.

## D6 — Eviction/selection over polluted population (Part A Q-06 vs Part B R-05+R-09)

- **Part B requirement:** eviction and selection act only on eligible members (Q-B4).
- **Part A observed:** uniform random over queue containing dead entries (D2).
- **Classification: E.** Medium. One cancelled request can cause an unrelated live rejection (INV-05).

## D7 — Test coverage

- Existing tests: happy paths only. None prove cancellation-before-permit, exactly-once release, failed-delivery progress, or live-only metrics.
- **Classification: F.** The explicit-drop test passes precisely because it never checks the parallelism bound or metrics under queued load.

## Proposed deterministic tests (from Part A §6)

- **Test A** (cancel before permit): parallelism=1, capacity≥1. Hold the only slot; queue one waiter; cancel it; verify it becomes ineligible (per requirements) or stays (defect confirmation); release; verify only live requests progress.
- **Test B** (cancelled waiter under full queue): small capacity; saturate; fill queue; cancel one waiter; submit a live one; verify the live request is admitted or evicted against a live-only population.
- **Test C** (failed delivery): make a waiter disappear before dispatch; verify delivery failure, capacity correctness, same-turn progress for the next live waiter, metric convergence.
- **Test D** (exactly-once): one permit; exercise explicit release; count scheduler release signals and subsequent grants; expect exactly one of each. Also exercise implicit Drop alone and cancelled-holding.

## Diff summary

| ID | Topic | Class | Severity |
|---|---|---|---|
| D1 | Duplicate release signals per explicit drop | E | Critical |
| D2 | Dead waiters never pruned; affect capacity/eviction/selection/metrics | E | Critical |
| D3 | Failed delivery burns slot, no same-turn progress | E | High |
| D4 | searches_running not re-incremented on refill grants | E | High |
| D5 | time_to_abort evaluated only post-grant | E/D | Medium |
| D6 | Random eviction/selection over polluted population | E | Medium |
| D7 | Missing deterministic tests for all of the above | F | — |

**Success criteria met:** caller-terminal transition without scheduler synchronization (D2); waiting entry outliving eligibility (D2); non-live demand driving admission decisions (D2/D6); metrics indefinitely representing terminal requests (D2); failed delivery without guaranteed progress (D3); capacity leak before acquisition — none found; duplicate capacity return after acquisition (D1); running/ownership mismatch (D4); missing deterministic tests (D7).

Findings frozen. External bug information was not consulted before freezing.
