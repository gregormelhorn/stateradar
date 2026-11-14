# Domain question register after Q-01 through Q-11

Behavior descriptions and citations below refer to the frozen upstream baseline
`04914c200cb38d4ea960ee6a4c314a028c632991`. DR-001 through DR-004 subsequently change the
Q-01 through Q-04 branches in the evaluation copy; see [deviation-report.md](deviation-report.md).

## Q-01 — Should zero weight be supported, and if so must an eligible zero waiter complete after the previous head cancels at full capacity?

**Fault:** F-20
**Trigger:** adversarial trace

Question: Should zero weight be supported, and if so must an eligible zero waiter complete after the previous head cancels at full capacity?

Current behaviour: At capacity, removal skips the rescan; Release(0) later runs it and grants the zero waiter. (observed-in-code, semaphore/semaphore.go:85 ("s.waiters.Remove(elem)"); semaphore/semaphore.go:87 ("if isFront && s.size > s.cur {"); semaphore/semaphore.go:129 ("s.notifyWaiters()"); semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {").)

Options: Permit zero with FIFO progress | define zero as a no-op that bypasses FIFO | disallow zero

Proposed: Permit zero with FIFO progress — a request needing no weight can become eligible after cancellation without bypassing an earlier queued request. This recommendation was accepted below.

Decision: Permit zero weight with FIFO progress.
Rationale: proposal rationale adopted (owner-confirmed).
Owner response: "Der Empfehlung folgen".
Decided-via: chat acceptance, Gregor Melhorn, 2026-11-14.
Status: RESOLVED — DR-001

## Q-02 — Should an oversized Acquire wait only for cancellation, including forever with Background, or refuse invalid weight?

**Fault:** F-13
**Trigger:** step-5 lint

Question: Should an oversized Acquire wait only for cancellation, including forever with Background, or refuse invalid weight?

Current behaviour: After the fast check it unlocks and waits off queue. (observed-in-code, semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:62 ("if n > s.size {"); semaphore/semaphore.go:65 ("<-done").)

Options: wait on context | reject promptly | constrain inputs

Original pilot proposal (superseded by decision below): Wait on context — preserve the existing off-queue behavior and document the caller deadline responsibility for unsatisfiable requests.

Decision: Acquire with weight greater than capacity returns an explanatory error without waiting for context cancellation. Existing pre-canceled-context handling is retained; other cancellation orderings remain Q-10. TryAcquire continues to return false for positive oversized weights.
Rationale: proposal rationale adopted (owner-confirmed).
Owner response: "Q-02: sofort verständlichen fehler zurückgeben".
Decided-via: chat acceptance, Gregor Melhorn, 2026-11-14.
Status: RESOLVED — DR-004

## Q-03 — What weight and size domains are supported, including negative and extreme int64 values?

**Fault:** F-05
**Trigger:** step-1 extraction

Question: What weight and size domains are supported, including negative and extreme int64 values?

Current behaviour: Constructor stores any int64; the arithmetic is unchecked; negative Acquire can credit capacity and negative Release can increase held weight. (observed-in-code, semaphore/semaphore.go:22 ("w := &Weighted{size: n}"); semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:124 ("s.cur -= n").)

Options: document a valid domain | validate and signal invalid values | define signed behavior

Original pilot proposal (superseded by decision below): Document a valid domain — specify nonnegative capacity and weights with representable arithmetic; do not silently declare signed misuse supported. Zero progress remains separately governed by Q-01.

Decision: NewWeighted, Acquire, TryAcquire and Release reject negative int64 arguments with panic before changing state. Zero remains supported under DR-001. All nonnegative int64 values are representable inputs; capacity accounting must stay within [0,size].
Rationale: proposal rationale adopted (owner-confirmed).
Owner response: "Panic bei negativen Werten in allen vier Methoden (empfohlen)".
Decided-via: chat acceptance, Gregor Melhorn, 2026-11-14.
Status: RESOLVED — DR-002

## Q-04 — After a recovered over-release panic, is continued use permitted and what counter should callers observe?

**Fault:** F-05
**Trigger:** step-8 verification

Question: After a recovered over-release panic, is continued use permitted and what counter should callers observe?

Current behaviour: Release subtracts, unlocks, then panics. A recovered size-one instance can admit two units. (observed-in-code, semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:125 ("if s.cur < 0 {"); semaphore/semaphore.go:126 ("s.mu.Unlock()"); semaphore/semaphore.go:127 ("panic("semaphore: released more than held")").)

Options: declare instance unusable | preserve old count | specify continuing with drift

Original pilot proposal (superseded by decision below): Declare the recovered instance unusable — preserve the current panic behavior and explicitly disallow continued use rather than implying rollback.

Decision: Release of more than the aggregate held weight panics before subtracting or notifying. Recovery preserves the component counter and queue; this is not a recovery guarantee for the calling application.
Rationale: proposal rationale adopted (owner-confirmed).
Owner response: "gut, ich folge deiner einschätzung".
Decided-via: chat acceptance, Gregor Melhorn, 2026-11-14.
Status: RESOLVED — DR-003

## Q-05 — What responsibility do callers have for abandoning queued calls, held weight or an old instance?

**Fault:** F-07
**Trigger:** step-5 lint

Question: What responsibility do callers have for abandoning queued calls, held weight or an old instance?

Current behaviour: Pending call stays until grant or Done; successful charge stays until Release. A new constructor does not touch the old instance. (observed-in-code, semaphore/semaphore.go:22 ("w := &Weighted{size: n}"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:75 ("case <-done:"); semaphore/semaphore.go:105 ("return nil"); semaphore/semaphore.go:124 ("s.cur -= n").)

Options: document explicit cancellation and release | define reclamation | define a lifecycle boundary

Proposed: Document explicit cancellation and release — each pending call needs cancellation, each successful charge needs release, and creating a new instance does not clean up an old one.

Decision: Explicit cancellation and release. Cancel abandoned pending calls and
handle their return values. Do not release after failure; successful acquisition
requires matching release after work ends, even after Context cancellation.
New instances do not clean up old instances. No automatic reclamation.
Rationale: proposal rationale adopted (owner-confirmed).
Owner response: "Gut, übernehmen wir Q-05 so."
Decided-via: chat acceptance, Gregor Melhorn, 2026-11-14.
Status: RESOLVED — DR-005
Follow-up: contract documentation and focused conformance acceptance pending;
this interview answer does not claim implementation/test completion.

## Q-06 — Should a second acquisition by the same logical caller be independent while the first is pending and while it is held?

**Fault:** F-14
**Trigger:** step-3 checklist

Question: Should a second acquisition by the same logical caller be independent while the first is pending and while it is held?

Current behaviour: Calls get individual queue entries or charge independently. There is no identity field. One unit of release grants one unit waiter when initially full. (observed-in-code, semaphore/semaphore.go:28 ("type Weighted struct {"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:70 ("w := waiter{n: n, ready: ready}"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:156 ("s.cur += w.n").)

Options: document independence and self-blocking | design caller-level deduplication | constrain repeat calls

Proposed: Document independence and self-blocking — each invocation is a separate request even for the same logical caller.

Decision: Each acquisition invocation is independent, whether earlier calls
from the same logical caller are pending or already hold capacity. No merging,
replacement, deduplication or reentrant success. Each success adds its own
release obligation; repeated acquisitions can self-block. A shared Context can
cancel multiple requests without making them a single acquisition.
Rationale: proposal rationale adopted (owner-confirmed).
Owner response: "Gut, übernehmen wir Q-06 so."
Decided-via: chat acceptance, Gregor Melhorn, 2026-11-14.
Status: RESOLVED — DR-006
Follow-up: contract documentation and focused conformance acceptance pending;
this interview answer does not claim implementation/test completion.

## Q-07 — What constitutes a matching Release across callers, and should duplicate or unowned Release be detected while aggregate weight covers it?

**Fault:** F-08
**Trigger:** step-3 checklist

Question: What constitutes a matching Release across callers, and should duplicate or unowned Release be detected while aggregate weight covers it?

Current behaviour: Release uses only the aggregate; wrong release may grant another waiter. Over-release has a separate panic path. (observed-in-code, semaphore/semaphore.go:122 ("func (s *Weighted) Release(n int64) {"); semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:129 ("s.notifyWaiters()").)

Options: allow transferable anonymous weight by contract | require matching ownership | diagnose only aggregate over-release

Proposed: Allow transferable anonymous weight by contract — callers coordinate matching aggregate release; the component does not promise per-caller ownership checks.

Decision: Release responsibility may transfer between goroutines. The application
ensures each release matches held, not already released capacity. The semaphore
checks numeric bounds and aggregate holdings, not caller ownership or request
identity. Duplicate releases can remain undetected while other holdings cover
them. Aggregate over-release retains the state-preserving panic from DR-003.
Rationale: proposal rationale adopted (owner-confirmed).
Owner response: "Gut, übernehmen wir Q-07 so."
Decided-via: chat acceptance, Gregor Melhorn, 2026-11-14.
Status: RESOLVED — DR-007
Follow-up: contract documentation and focused conformance acceptance pending;
this interview answer does not claim implementation/test completion.

## Q-08 — Should wrong instance or foreign but well-formed Context remain caller errors, and how are these detected?

**Fault:** F-18
**Trigger:** step-3 checklist

Question: Should wrong instance or foreign but well-formed Context remain caller errors, and how are these detected?

Current behaviour: Calls affect only the receiver and use the supplied Done signal. A release on another receiver can debit that instance or panic. (observed-in-code, semaphore/semaphore.go:22 ("w := &Weighted{size: n}"); semaphore/semaphore.go:39 ("done := ctx.Done()"); semaphore/semaphore.go:113 ("success := s.size-s.cur >= n && s.waiters.Len() == 0"); semaphore/semaphore.go:124 ("s.cur -= n").)

Options: document caller responsibility | expose diagnostics or attribution requirements

Proposed: Document caller responsibility — the supplied receiver and Context are authoritative; wrong intent is not detectable at this boundary.

Decision: Instance and Context selection are caller responsibilities. Operations
use the supplied receiver and Context without a guarantee of detecting semantic
misselection. Release responsibility may transfer; capacity does not transfer
between instances. Invalid Context implementations remain separately in Q-09.
Rationale: proposal rationale adopted (owner-confirmed).
Owner response: "Gut, übernehmen wir Q-08 so."
Decided-via: chat acceptance, Gregor Melhorn, 2026-11-14.
Status: RESOLVED — DR-008
Follow-up: contract documentation and focused conformance acceptance pending;
this interview answer does not claim implementation/test completion.

## Q-09 — What does Weighted guarantee for nil, blocking, panicking, reentrant or inconsistent custom Context methods?

**Fault:** F-11
**Trigger:** seam-contract sweep

Question: What does Weighted guarantee for nil, blocking, panicking, reentrant or inconsistent custom Context methods?

Current behaviour: Done runs before the lock; Err runs after unlock or rollback. A custom call may block or panic, and a closed Done with nil Err can report false success. (observed-in-code, semaphore/semaphore.go:39 ("done := ctx.Done()"); semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:49 ("return ctx.Err()"); semaphore/semaphore.go:91 ("s.mu.Unlock()"); semaphore/semaphore.go:92 ("return ctx.Err()"); semaphore/semaphore.go:101 ("s.Release(n)"); semaphore/semaphore.go:102 ("return ctx.Err()").)

Options: document conforming Context precondition | declare propagation semantics | define validation

Proposed: Document a conforming Context precondition — rely on the copied Context contract, with no invented recovery or latency guarantees for violations.

Decision: Require a non-nil, contract-conforming Context, including custom
implementations that meet the Go contract. A nil Done channel remains valid.
No automatic substitution, repair, recovery or additional progress guarantee
is promised for blocking, panicking, inconsistent or reentrant methods.
Rationale: proposal rationale adopted (owner-confirmed).
Owner response: "Gut, übernehmen wir Q-09 so."
Decided-via: chat acceptance, Gregor Melhorn, 2026-11-14.
Status: RESOLVED — DR-009
Follow-up: contract documentation and focused conformance acceptance pending;
this interview answer does not claim implementation/test completion.

## Q-10 — Which cancellation orderings promise failure, rollback or success, and what does unchanged mean with concurrent observers?

**Fault:** F-16
**Trigger:** adversarial trace

Question: Which cancellation orderings promise failure, rollback or success, and what does unchanged mean with concurrent observers?

Current behaviour: Locked entry check precedes immediate charge. Queued grants charge before close; both cancellation paths restore the charge when Done is observed. Intervening independent operations can see temporary reservation. (observed-in-code, semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:43 ("case <-done:"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:76 ("s.mu.Lock()"); semaphore/semaphore.go:81 ("s.cur -= n"); semaphore/semaphore.go:99 ("select {"); semaphore/semaphore.go:101 ("s.Release(n)"); semaphore/semaphore.go:156 ("s.cur += w.n"); semaphore/semaphore.go:158 ("close(w.ready)").)

Options: document exact cancellation boundary and net accounting | define stricter observational guarantee

Proposed: Document the exact cancellation boundary and net accounting — distinguish ready notification, rollback and successful return; do not promise absence of transient reservations.

Decision: Evaluate cancellation at the defined initial and post-queued-grant
checkpoints. Processing cancellation removes the request or rolls back its grant
before returning the Context error. Cancellation after the last applicable
check may coexist with successful return and the DR-005 release obligation.
Error return leaves no own holding or queued entry, but does not promise an
unchanged global state or invisibility of temporary reservations. Existing
negative/oversized input decisions remain unchanged. See DR-010 for boundaries.
Rationale: proposal rationale adopted (owner-confirmed).
Owner response: "Gut, übernehmen wir Q-10 so."
Decided-via: chat acceptance, Gregor Melhorn, 2026-11-14.
Status: RESOLVED — DR-010
Follow-up: contract documentation and focused conformance acceptance pending;
this interview answer does not claim implementation/test completion.

## Q-11 — Does TryAcquire's without-blocking contract exclude ordinary mutex contention, and do canceled callers have a prompt-return guarantee while waiting for the mutex?

**Fault:** F-13
**Trigger:** step-5 lint

Question: Does TryAcquire's without-blocking contract exclude ordinary mutex contention, and do canceled callers have a prompt-return guarantee while waiting for the mutex?

Current behaviour: Both calls unconditionally lock; Acquire checks Done only after locking. (observed-in-code, semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:43 ("case <-done:"); semaphore/semaphore.go:112 ("s.mu.Lock()").)

Options: document no waiter-queue blocking | require immediate acquisition attempt | specify cancellation latency

Proposed: Document no waiter-queue blocking — TryAcquire may wait for its internal mutex; no real-time cancellation bound is promised.

Decision: TryAcquire does not enter the capacity waiter queue or wait for future
releases, but may wait for the internal mutex before its single admission check.
Cancellation does not interrupt mutex acquisition; DR-010 checkpoints apply.
No fixed return or cancellation-latency bound is promised, including at a
Context deadline. Correct cancellation processing and accounting remain required.
Rationale: proposal rationale adopted (owner-confirmed).
Owner response: "Gut, übernehmen wir Q-11 so."
Decided-via: chat acceptance, Gregor Melhorn, 2026-11-14.
Status: RESOLVED — DR-011
Follow-up: contract documentation and focused conformance acceptance pending;
this interview answer does not claim implementation/test completion.

## Q-12 — What FIFO ordering, head-of-line blocking, grant versus return order and backlog limit should be public guarantees?

**Fault:** F-20
**Trigger:** step-5 lint

Question: What FIFO ordering, head-of-line blocking, grant versus return order and backlog limit should be public guarantees?

Current behaviour: Barging is refused; notifier stops at first unfit head; ready closure and goroutine return are distinct; admission queue has no cap. (observed-in-code, semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:113 ("success := s.size-s.cur >= n && s.waiters.Len() == 0"); semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {"); semaphore/semaphore.go:158 ("close(w.ready)").)

Options: publish FIFO grant policy and limits | specify another policy | keep policy implementation-defined

Proposed: Publish FIFO grant policy and limits — prevent barging, distinguish grant order from return order, and make the uncapped backlog and caller responsibility explicit.

Status: OPEN — human decision required

## Q-13 — Should a public API describe that Release(0) can change queue state and wake eligible waiters?

**Fault:** F-15
**Trigger:** part-B diff

Question: Should a public API describe that Release(0) can change queue state and wake eligible waiters?

Current behaviour: A non-panicking Release(0) always invokes notification. (observed-in-code, semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:129 ("s.notifyWaiters()"); semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {").)

Options: document notification effect | constrain zero release | specify no-op

Proposed: Document notification effect — Release(0) can notify eligible waiters; it is not necessarily an observable no-op. Recheck consistency with the owner decision on Q-01.

Status: OPEN — human decision required
