# Part A — Code-Informed Analysis: SearchQueue

**Component:** SearchQueue admission/permit lifecycle
**Repo:** meilisearch/meilisearch
**Commit:** fff2ef5a42658b16a937d922aabc3fb7f89f2018
**Rust toolchain:** not installed (read-only analysis)
**Timestamp:** 2026-08-06T16:43:42Z
**External bug info:** NOT consulted

---

## 1. Structure (search_queue.rs, 206 LOC)

Three actors:
1. **Caller** (`try_get_search_permit`, L177-196): creates a oneshot channel, transfers the sender to the scheduler, blocks on the receiver until a Permit or a dropped channel (rejection), then checks `time_to_abort`.
2. **Scheduler** (`run`, L114-175): owns `queue: Vec<oneshot::Sender<Permit>>` (waiting entries), `searches_running: usize` (local gate), `search_finished: mpsc::Receiver<()>` (release signals). Biased select: releases first, then admissions.
3. **Permit** (L46-67): holds `mpsc::Sender<()>`; explicit `drop(self).await` sends `()`; implicit `Drop::drop` **also** sends `()` via spawned task.

## 2. State model (four lifecycle regions)

### Request lifecycle (caller view)
`Created → AdmissionSubmitting → Waiting → PermitReceived → Executing → Completed | Rejected | Cancelled | Obsolete`

### Admission-claim lifecycle (scheduler view)
`NotRegistered → Transferred → StoredAndEligible → Selected → Granted | Evicted | GrantedDead`

Note: the scheduler's "StoredAndEligible" entries are `oneshot::Sender<Permit>` halves. Nothing in the file ever removes an entry except selection (`swap_remove`) or eviction (`swap_remove`). There is **no cancellation event** that reaches the scheduler's population.

### Permit lifecycle
`CapacityUnit → BeingGranted → Held → ReleaseSignal1 | ReleaseSignal2 → Returned`

### Capacity/metrics
- `searches_running` (local gate + published metric)
- `queue.len()` (published as `searches_waiting`)

## 3. Mechanism trace (with code lines)

**Immediate admission** (R-03): `run` L154-159: `searches_running < parallelism && queue.is_empty()` → increment, `send(Permit)`. OK.

**Waiting admission** (R-04): `run` L168: `queue.push(search_request)`. OK.

**Queue-full eviction** (R-05): `run` L166-168: `queue.len() >= capacity` → random `swap_remove` + `drop(thing)` → the evicted caller's receiver errors → `TooManySearchRequests`. Then push. OK in principle; see Q-06.

**Capacity zero** (R-15): `run` L161-164: drop immediately. OK.

**Release + refill** (R-07): `run` L146-152: `search_finished.recv()` → `saturating_sub(1)` → if queue non-empty, random pick + `channel.send(Permit { sender })`. **No `searches_running += 1` after the grant.** See Q-04.

**Explicit release** (`Permit::drop(self)`, L50-56): `sender.send(()).await` → signal 1. Then the consumed `self` goes out of scope → `Drop for Permit` (L58-67) fires → clones sender, spawns task → signal 2. **Two release signals per explicit drop.** See Q-01.

**Implicit release** (`Drop` only, e.g. panic/cancel while holding): 1 signal. OK in isolation.

**time_to_abort** (R-10): `try_get_search_permit` L186-192: elapsed checked **only after** the permit arrives. Obsolete waiters wait in the queue unbounded, get selected, receive the permit, then drop it explicitly (→ 2 signals). See Q-05.

**Delivery failure** (R-12): `let _ = channel.send(...)` in both grant paths (L150, L157). Failure ignored; dead waiter already `swap_remove`d. Slot unused for that turn. See Q-03.

**Channel closed** (R-13): `receive_new_searches.recv() → None → continue` (L140-144). Loop never exits. OK.

## 4. Findings

### Q-01 — Explicit drop releases the permit TWICE (exactly-once violated)

- Severity: **Critical**
- Confidence: High (direct code reading)
- Classification: E (possible implementation defect)
- Requirements: R-07, INV-08, INV-09, INV-01
- Cell: (Held, PermitReleaseRequested)
- Path: `Permit::drop(self)` L50-56 sends `()` → `self` then drops → `impl Drop` L58-67 spawns another `send(())`.
- Effect: every explicit release emits **two** release signals. Scheduler does `saturating_sub` twice and may grant **two** waiters per one logical release.
- Evidence: search_queue.rs L52-55 + L62-65. Route call sites (search.rs:600,666,900,967; multi_search.rs:195,307,379; facet_search.rs:331) all use `permit.drop().await` — the buggy path is the production path everywhere. The module doc even recommends explicit drop.
- Escalation: with parallelism=2, two running searches, 3 queued waiters: P1 explicit drop → signal1 grants W1 (metric 2→1, no re-increment per Q-04), signal2 grants W2 (metric 1→0). Actual running: P2+W1+W2 = **3 > parallelism 2**. Metric says 0. The immediate-admission gate (`searches_running < parallelism`) then admits yet another request → 4 running. **Parallelism safety broken by a cascade starting at exactly-once.**
- `saturating_sub` (Q21) does not fix this; it only clamps the metric at 0, masking the duplicate release while the extra grants proceed.

### Q-02 — Cancelled waiting callers never leave the admission population

- Severity: **Critical**
- Confidence: High
- Classification: E
- Requirements: R-08, R-09, R-16, INV-03, INV-04, INV-05, INV-06, INV-14
- Cell: (Waiting, WaitingCallerCancelled) → **UNSPECIFIED**
- Path: queue entries are `oneshot::Sender<Permit>`. A cancelled caller drops its receiver; the scheduler can only notice on a failed `send` (L150). Nothing else removes the entry.
- Effect: dead entries (a) occupy waiting capacity (R-02/INV-02), (b) count in `searches_waiting()` indefinitely (INV-06), (c) remain eligible for selection and eviction (INV-03/INV-14), (d) can cause a **live** waiter to be randomly evicted instead (R-16/INV-05), (e) when selected, waste the slot for the whole turn (delivery fails silently, Q-03).
- Evidence: no code path in the 206 LOC ever prunes the queue. There is no deadline, no heartbeat, no dead-letter check on the stored senders except the failed `send`.

### Q-03 — Failed permit delivery burns the freed slot; no progress that turn

- Severity: **High**
- Confidence: High
- Classification: E
- Requirements: R-12, INV-07
- Cell: (StoredAndEligible, PermitDeliveryFailed) → silent ignore
- Path: L150 `let _ = channel.send(...)` in the release branch. If the recipient is dead, the send fails and the freed slot is lost until the **next** release signal. There is no retry, no alternate selection in the same turn.
- Effect: under load with many dead waiters, every release can be consumed by a dead entry; live waiters starve. Scheduler continuity (INV-12) holds, but progress (R-12) does not.
- Interacts with Q-01: the duplicate second signal selects again — possibly another dead entry.

### Q-04 — `searches_running` is decremented on refill but never re-incremented

- Severity: **High**
- Confidence: High
- Classification: E
- Requirements: R-01, R-14, INV-13, INV-01
- Cell: (ExecutionCapacityFull, ReleaseSignalProcessed)
- Path: release branch L146-152 decrements on release, grants a waiter, and never adds the running count back. Each release-with-refill nets −1 on the metric. Over N refills the metric drifts toward 0 while N searches still run.
- Effect: (a) `searches_running()` lies (INV-13); (b) the immediate-admission gate `searches_running < parallelism` uses the corrupted value and over-admits (INV-01).
- Evidence: compare L156 (`searches_running += 1` on immediate admission) with L146-152 (no increment on refill grant).

### Q-05 — `time_to_abort` is evaluated only after the permit is granted

- Severity: **Medium**
- Confidence: High
- Classification: E (partial) / D (requirement ambiguity)
- Requirements: R-10, INV-11
- Cell: (PermitReceived, WaitAgeLimitExceeded)
- Path: L186-192: elapsed measured from channel creation to permit receipt; only then is the permit dropped. The obsolete waiter occupied queue capacity the whole time and consumed a grant that a live waiter could have used.
- Effect: INV-11 holds at the letter (no obsolete execution), but the obsolete request still spends queue capacity and triggers the Q-01 double-release when it drops explicitly. The requirement's "Any permit associated with that outcome must be returned" is satisfied, but late and twice.

### Q-06 — Eviction and selection operate on a polluted population

- Severity: **Medium**
- Confidence: High
- Classification: E
- Requirements: R-05, R-09, R-16, INV-05, INV-14
- Path: `rng.gen_range(0..queue.len())` over a queue containing dead entries (Q-02). Uniformly random eviction can pick live waiters while dead ones survive; uniform selection can pick dead entries (wasting turns, Q-03).
- Effect: one cancelled request can indirectly cause an unrelated live request to be rejected (INV-05).

## 5. Invariants

| ID | Verdict | Evidence |
|---|---|---|
| INV-01 parallelism safety | **Violated** | Q-01 cascade: duplicate release → 2 grants → metric drift → gate over-admits |
| INV-02 live waiting capacity | **Violated** | dead entries occupy queue capacity (Q-02) |
| INV-03 no terminal waiter eligible | **Violated** | no pruning path exists (Q-02) |
| INV-04 no permit after cancellation | Supported (de facto) | dead recipient's send fails (L150) — caller never executes, but only discovered lazily |
| INV-05 cancellation isolation | **Violated** | polluted eviction/selection population (Q-06) |
| INV-06 live waiting metric | **Violated** | `searches_waiting = queue.len()` includes dead entries indefinitely (Q-02) |
| INV-07 failed-delivery progress | **Violated** | `let _ = channel.send(...)`, no same-turn retry (Q-03) |
| INV-08 exactly-one release | **Violated** | explicit drop = 2 signals (Q-01) |
| INV-09 no phantom release | **Violated** | duplicate signals admit extra waiters (Q-01) |
| INV-10 rejection finality | Supported | dropped oneshot receiver errors permanently |
| INV-11 obsolete cleanup | Partial | permit returned but late, and twice (Q-05) |
| INV-12 scheduler continuity | Supported | `continue` on None; `let _ =` everywhere; loop never exits |
| INV-13 running metric integrity | **Violated** | refill grants not re-incremented (Q-04) |
| INV-14 admission population integrity | **Violated** | dead entries remain (Q-02) |
| INV-15 terminal outcome exclusivity | Supported | obsolete caller sees only the error; permit never escapes |

## 6. Test review (221 LOC, tests/search/search_queue.rs)

Existing coverage: immediate grant (2 tests incl. explicit drop), time_to_abort, full-queue timeout, eviction headers, crash-while-holding (implicit release), capacity=0.

**Missing:**
- waiting-caller cancellation (Test A)
- cancelled waiter under full queue (Test B)
- failed permit delivery (Test C)
- exactly-once release / duplicate-signal admission count (Test D)
- `searches_running` correctness across refill grants
- metric divergence after cancellations
- parallelism bound under explicit-drop load

Note: the existing explicit-drop test (`search_queue_register_with_explicit_drop`) passes precisely because it never checks metrics or the parallelism bound under queued load — the duplicate release is invisible to it.

## 7. Answers to required questions (selection)

1. Caller joins the waiting population when the scheduler executes `queue.push` (L168).
2. Yes — caller (receiver) can cease while the scheduler's sender entry remains (Q-02).
3. Only selection or eviction (`swap_remove`) removes an entry; there is no cancellation event.
4-5. The scheduler learns of cancellation **only lazily, on attempted delivery** (failed oneshot send).
6-9. Capacity, eviction, selection, and waiting metrics all use the same `queue` — none are filtered for liveness.
11. Dead recipient: send fails silently; slot lost for the turn (Q-03).
12. No — no retry within the same turn.
13. Running capacity is consumed at grant time in the immediate path (increment), but never restored in the refill path (Q-04).
14. Yes — failed refill leaves metric and capacity inconsistent (Q-03, Q-04).
15. Yes — via polluted eviction population (Q-06).
16. Yes — indefinitely (Q-02).
17. Yes — explicit drop emits two signals (Q-01).
18. Yes — `Permit::drop(self)` is followed by `Drop::drop` (Q-01).
19. The second release is merely masked by `saturating_sub`, not harmless (Q-01).
20. Yes — two waiters can be granted per one logical release (Q-01).
21. It conceals the violation (Q-01).
22. `time_to_abort` only inspects elapsed time **after** admission (Q-05).
23. Yes — obsolete requests occupy waiting capacity until granted (Q-05).
24-27. None of the existing tests prove these.
