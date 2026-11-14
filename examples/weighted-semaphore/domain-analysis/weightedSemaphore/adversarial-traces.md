# Reconciled adversarial traces

All historical P/T identities are retained. These are evaluation-copy verdicts under accepted DRs. Focused tests below exercise the stated mechanism; cell tests and the complete decision suite are also required. Historical Part B is not relabeled current.

### P-01a — Acquire then Release

A feasible request queues behind held capacity; the later release reserves, unlinks and wakes it.

Authority: DR-012 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-012.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:97 ("elem := s.waiters.PushBack(w)").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:82 ("func TestDR006RepeatedPending(").

### P-01b — Release then Acquire

Release frees capacity before admission. A live fitting request succeeds through the empty-queue fast path.

Authority: DR-012 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-012.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:79 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:63 ("func TestDR006RepeatedHeld(").

### P-02a — TryAcquire before Release

An insufficient-capacity try returns false without queueing. A later release permits a subsequent independent try.

Authority: DR-011 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-011.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:145 ("success := s.size-s.cur >= n && s.waiters.Len() == 0").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:245 ("func TestDR011TryDoesNotQueue(").

### P-02b — Release before TryAcquire

The try samples the newly available capacity under the mutex and succeeds if no queue remains.

Authority: DR-011 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-011.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:145 ("success := s.size-s.cur >= n && s.waiters.Len() == 0").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:245 ("func TestDR011TryDoesNotQueue(").

### P-03a — Acquire then cancellation

After the final fast-path check success may occur; completed success is not reclaimed. Queued cancellation instead removes or rolls back.

Authority: DR-010 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-010.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:84 ("s.cur += n").

Focused observed-in-tests evidence: examples/weighted-semaphore/schedule/checkpoints_test.go.txt:46 ("func TestScheduleDR010FastLateCancel(").

### P-03b — Cancellation then Acquire

A preclosed conforming Context rejects before capacity admission even if weight fits.

Authority: DR-010 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-010.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:76 ("return ctx.Err()").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:201 ("func TestDR010PreCanceled(").

### P-04a — Cancel before Release at handoff

Cancellation selected before holder release either removes the entry or rolls back the grant made before cleanup obtains the lock. The result is a Context error.

Authority: DR-010 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-010.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:107 ("s.cur -= n").

Focused observed-in-tests evidence: examples/weighted-semaphore/schedule/checkpoints_test.go.txt:82 ("func TestScheduleDR010CancelSelectedRollback(").

### P-04b — Release before cancellation

If cancellation precedes the post-grant check, rollback occurs. After that check success may occur and retains the release obligation.

Authority: DR-010 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-010.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:127 ("s.Release(n)").

Focused observed-in-tests evidence: examples/weighted-semaphore/schedule/checkpoints_test.go.txt:65 ("func TestScheduleDR010GrantedRollback(").

### P-05a — Second acquisition before handoff

Distinct calls enqueue separately, even from one logical caller. The notifier grants by enqueue order; execution and return order may differ.

Authority: DR-006 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-006.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:97 ("elem := s.waiters.PushBack(w)").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:82 ("func TestDR006RepeatedPending(").

### P-05b — Handoff before second acquisition

Once an earlier call holds capacity, the second call is independent: it can charge spare capacity or self-block when none remains.

Authority: DR-006 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-006.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:79 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:63 ("func TestDR006RepeatedHeld(").

### P-06a — Second acquisition before cancellation of first

Removing the blocked head grants an eligible successor, including zero at full capacity. Shared Context cancellation may cause both calls to fail independently.

Authority: DR-001 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-001.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:113 ("if isFront {").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_q01_test.go:106 ("func TestDR001SpareCapacity(").

### P-06b — Cancel first before second acquisition

After removal, a live fitting second call can admit. Reusing the already-canceled Context causes initial rejection.

Authority: DR-010 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-010.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:76 ("return ctx.Err()").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:201 ("func TestDR010PreCanceled(").

### P-07a — Cancel head at full capacity before release

The eligible zero-weight prefix now progresses without a later Release(0). A remaining positive head still blocks its successors. Historical eligible-retained state is eliminated.

Authority: DR-001 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-001.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:113 ("if isFront {").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_q01_test.go:76 ("func TestDR001FullZeroPrefix(").

### P-07b — Release then late cancellation

Grant precedes cancellation. Before the final check the recipient rolls back; after it, success retains capacity until Release.

Authority: DR-010 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-010.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:127 ("s.Release(n)").

Focused observed-in-tests evidence: examples/weighted-semaphore/schedule/checkpoints_test.go.txt:99 ("func TestScheduleDR010QueuedLateCancel(").

### P-08a — Unowned excess release then acquisition

Over-release panics before mutation. Recovery cannot expose negative capacity accounting; a subsequent oversized Acquire returns a size error.

Authority: DR-003 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-003.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:166 ("if n > s.cur {").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_numeric_test.go:146 ("func TestDR003OverReleaseEmptyPartialFull(").

### P-08b — Acquire then another actor releases

A valid responsibility transfer works. A mistaken release within aggregate holdings cannot be distinguished by this API; caller matching remains required.

Authority: DR-007 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-007.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:107 ("s.cur -= n").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:131 ("func TestDR007DuplicateWithinAggregate(").

### T-01 — Oversized abandoned request

A live oversized request returns a size error immediately, without queueing or waiting for cancellation. A preclosed Context retains priority.

Authority: DR-004 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-004.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:92 ("return fmt.Errorf(").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_numeric_test.go:201 ("func TestDR004OversizedImmediateError(").

### T-02 — Owner disappears

Pending requests need explicit cancellation and result consumption. A successful holding requires release; disappearance does not reclaim it.

Authority: DR-005 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-005.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:66 ("done := ctx.Done()").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:15 ("func TestDR005CancelPending(").

### T-03 — Cancellation while waiting for mutex

Cancellation does not interrupt lock acquisition. The first under-lock check observes it when execution reaches that point; there is no fixed return deadline.

Authority: DR-011 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-011.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:68 ("s.mu.Lock()").

Focused observed-in-tests evidence: examples/weighted-semaphore/schedule/checkpoints_test.go.txt:117 ("func TestScheduleDR011CancelBeforeMutex(").

### T-04 — Cancel after initial open check

A fast-path call may succeed after its final check. Success requires release even if Done is now closed.

Authority: DR-010 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-010.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:84 ("s.cur += n").

Focused observed-in-tests evidence: examples/weighted-semaphore/schedule/checkpoints_test.go.txt:46 ("func TestScheduleDR010FastLateCancel(").

### T-05 — Signed inputs

Negative constructor and method weights panic before mutation. Zero and MaxInt64 boundaries preserve bounded arithmetic.

Authority: DR-002 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-002.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:26 ("if n < 0 {").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_numeric_test.go:102 ("func TestDR002ZeroAndMaxBoundaries(").

### T-06 — Wrong receiver or Context

Only the actual receiver and supplied Context participate. The intended other instance remains unaffected.

Authority: DR-008 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-008.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:161 ("func (s *Weighted) Release(n int64) {").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:143 ("func TestDR008WrongReceiver(").

### T-07 — Recreation without cleanup

A new instance neither releases old holdings nor cancels old waiters.

Authority: DR-005 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-005.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:29 ("w := &Weighted{size: n}").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:45 ("func TestDR005NewInstanceIndependent(").

### T-08 — Faulty Done callback

Blocking, panicking or reentrant faulty Context methods have no recovery or progress guarantee. This historical probe is outside the supported outcome domain; conforming custom Contexts and nil Done remain supported.

Authority: DR-009 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-009.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:66 ("done := ctx.Done()").

untestable-via-seam: DR-009 excludes faulty Context outcomes. No behavioral pass is claimed. Supported boundary: TestDR009ConformingContexts.

### T-09 — Faulty Err callback

No promised replacement or recovery for a faulty Err implementation. Historical custom-callback observations are not an accepted outcome contract.

Authority: DR-009 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-009.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:76 ("return ctx.Err()").

untestable-via-seam: DR-009 excludes faulty Context outcomes. No behavioral pass is claimed. Supported boundary: TestDR009ConformingContexts.

### T-10 — Head removal with spare or zero capacity

Removal rescans at both boundaries. Eligible positive successors and the zero prefix can progress; non-head removal cannot bypass a still-blocked head.

Authority: DR-001 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-001.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:113 ("if isFront {").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_q01_test.go:126 ("func TestDR001RetainedHeadPreservesFIFO(").

### T-11 — Grant order versus return order

FIFO grants can yield reversed API-return order when the scheduler delays the first recipient.

Authority: DR-012 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-012.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:200 ("close(w.ready)").

Focused observed-in-tests evidence: examples/weighted-semaphore/schedule/checkpoints_test.go.txt:134 ("func TestScheduleDR012ReturnOrder(").

### T-12 — Transient reservation

A granted request can temporarily prevent another try before cancellation rollback; error return has no remaining own reservation.

Authority: DR-010 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-010.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:127 ("s.Release(n)").

Focused observed-in-tests evidence: examples/weighted-semaphore/schedule/checkpoints_test.go.txt:65 ("func TestScheduleDR010GrantedRollback(").

### T-13 — Cancellation after success

Completed success stays charged until matching Release. No post-return Context watcher exists.

Authority: DR-005 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-005.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:84 ("s.cur += n").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:29 ("func TestDR005CancelHeld(").

### T-14 — Uncapped queue

The queue has no waiter-count admission cap. Callers must bound incoming work and cancel obsolete requests. Finite tests exercise backlog, not an infinite-size theorem.

Authority: DR-012 (explicit-requirement). cited text contemplates this ordering: yes — the accepted scope in decisions/DR-012.yaml.

Observed-in-code: examples/weighted-semaphore/semaphore/semaphore.go:97 ("elem := s.waiters.PushBack(w)").

Focused observed-in-tests evidence: examples/weighted-semaphore/semaphore/decision_contract_test.go:317 ("func TestDR012Backlog(").


## Executed pair entry points

Every P-01a through P-08b ordering is also executed directly by TestStatePairs. These named entry points include sequential post-cancellation admission and oversized admission after recovered over-release, in addition to the focused mechanisms cited above.

- P-01a: `TestStatePairs/P-01a` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-01b: `TestStatePairs/P-01b` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-02a: `TestStatePairs/P-02a` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-02b: `TestStatePairs/P-02b` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-03a: `TestStatePairs/P-03a` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-03b: `TestStatePairs/P-03b` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-04a: `TestStatePairs/P-04a` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-04b: `TestStatePairs/P-04b` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-05a: `TestStatePairs/P-05a` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-05b: `TestStatePairs/P-05b` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-06a: `TestStatePairs/P-06a` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-06b: `TestStatePairs/P-06b` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-07a: `TestStatePairs/P-07a` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-07b: `TestStatePairs/P-07b` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-08a: `TestStatePairs/P-08a` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
- P-08b: `TestStatePairs/P-08b` — examples/weighted-semaphore/cells/state_cells_test.go.txt:337 ("func TestStatePairs(").
