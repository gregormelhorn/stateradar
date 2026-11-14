# Open domain questions

## Q-01 — Should zero weight be supported, and if so must an eligible zero waiter complete after the previous head cancels at full capacity?

**Fault:** F-20
**Trigger:** adversarial trace

Question: Should zero weight be supported, and if so must an eligible zero waiter complete after the previous head cancels at full capacity?

Current behaviour: At capacity, removal skips the rescan; Release(0) later runs it and grants the zero waiter. (observed-in-code, semaphore/semaphore.go:85 ("s.waiters.Remove(elem)"); semaphore/semaphore.go:87 ("if isFront && s.size > s.cur {"); semaphore/semaphore.go:129 ("s.notifyWaiters()"); semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {").)

Options: Permit zero with FIFO progress | define zero as a no-op that bypasses FIFO | disallow zero

Status: OPEN — human decision required

## Q-02 — Should an oversized Acquire wait only for cancellation, including forever with Background, or refuse invalid weight?

**Fault:** F-13
**Trigger:** step-5 lint

Question: Should an oversized Acquire wait only for cancellation, including forever with Background, or refuse invalid weight?

Current behaviour: After the fast check it unlocks and waits off queue. (observed-in-code, semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:62 ("if n > s.size {"); semaphore/semaphore.go:65 ("<-done").)

Options: wait on context | reject promptly | constrain inputs

Status: OPEN — human decision required

## Q-03 — What weight and size domains are supported, including negative and extreme int64 values?

**Fault:** F-05
**Trigger:** step-1 extraction

Question: What weight and size domains are supported, including negative and extreme int64 values?

Current behaviour: Constructor stores any int64; the arithmetic is unchecked; negative Acquire can credit capacity and negative Release can increase held weight. (observed-in-code, semaphore/semaphore.go:22 ("w := &Weighted{size: n}"); semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:124 ("s.cur -= n").)

Options: document a valid domain | validate and signal invalid values | define signed behavior

Status: OPEN — human decision required

## Q-04 — After a recovered over-release panic, is continued use permitted and what counter should callers observe?

**Fault:** F-05
**Trigger:** step-8 verification

Question: After a recovered over-release panic, is continued use permitted and what counter should callers observe?

Current behaviour: Release subtracts, unlocks, then panics. A recovered size-one instance can admit two units. (observed-in-code, semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:125 ("if s.cur < 0 {"); semaphore/semaphore.go:126 ("s.mu.Unlock()"); semaphore/semaphore.go:127 ("panic("semaphore: released more than held")").)

Options: declare instance unusable | preserve old count | specify continuing with drift

Status: OPEN — human decision required

## Q-05 — What responsibility do callers have for abandoning queued calls, held weight or an old instance?

**Fault:** F-07
**Trigger:** step-5 lint

Question: What responsibility do callers have for abandoning queued calls, held weight or an old instance?

Current behaviour: Pending call stays until grant or Done; successful charge stays until Release. A new constructor does not touch the old instance. (observed-in-code, semaphore/semaphore.go:22 ("w := &Weighted{size: n}"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:75 ("case <-done:"); semaphore/semaphore.go:105 ("return nil"); semaphore/semaphore.go:124 ("s.cur -= n").)

Options: document explicit cancellation and release | define reclamation | define a lifecycle boundary

Status: OPEN — human decision required

## Q-06 — Should a second acquisition by the same logical caller be independent while the first is pending and while it is held?

**Fault:** F-14
**Trigger:** step-3 checklist

Question: Should a second acquisition by the same logical caller be independent while the first is pending and while it is held?

Current behaviour: Calls get individual queue entries or charge independently. There is no identity field. One unit of release grants one unit waiter when initially full. (observed-in-code, semaphore/semaphore.go:28 ("type Weighted struct {"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:70 ("w := waiter{n: n, ready: ready}"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:156 ("s.cur += w.n").)

Options: document independence and self-blocking | design caller-level deduplication | constrain repeat calls

Status: OPEN — human decision required

## Q-07 — What constitutes a matching Release across callers, and should duplicate or unowned Release be detected while aggregate weight covers it?

**Fault:** F-08
**Trigger:** step-3 checklist

Question: What constitutes a matching Release across callers, and should duplicate or unowned Release be detected while aggregate weight covers it?

Current behaviour: Release uses only the aggregate; wrong release may grant another waiter. Over-release has a separate panic path. (observed-in-code, semaphore/semaphore.go:122 ("func (s *Weighted) Release(n int64) {"); semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:129 ("s.notifyWaiters()").)

Options: allow transferable anonymous weight by contract | require matching ownership | diagnose only aggregate over-release

Status: OPEN — human decision required

## Q-08 — Should wrong instance or foreign but well-formed Context remain caller errors, and how are these detected?

**Fault:** F-18
**Trigger:** step-3 checklist

Question: Should wrong instance or foreign but well-formed Context remain caller errors, and how are these detected?

Current behaviour: Calls affect only the receiver and use the supplied Done signal. A release on another receiver can debit that instance or panic. (observed-in-code, semaphore/semaphore.go:22 ("w := &Weighted{size: n}"); semaphore/semaphore.go:39 ("done := ctx.Done()"); semaphore/semaphore.go:113 ("success := s.size-s.cur >= n && s.waiters.Len() == 0"); semaphore/semaphore.go:124 ("s.cur -= n").)

Options: document caller responsibility | expose diagnostics or attribution requirements

Status: OPEN — human decision required

## Q-09 — What does Weighted guarantee for nil, blocking, panicking, reentrant or inconsistent custom Context methods?

**Fault:** F-11
**Trigger:** seam-contract sweep

Question: What does Weighted guarantee for nil, blocking, panicking, reentrant or inconsistent custom Context methods?

Current behaviour: Done runs before the lock; Err runs after unlock or rollback. A custom call may block or panic, and a closed Done with nil Err can report false success. (observed-in-code, semaphore/semaphore.go:39 ("done := ctx.Done()"); semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:49 ("return ctx.Err()"); semaphore/semaphore.go:91 ("s.mu.Unlock()"); semaphore/semaphore.go:92 ("return ctx.Err()"); semaphore/semaphore.go:101 ("s.Release(n)"); semaphore/semaphore.go:102 ("return ctx.Err()").)

Options: document conforming Context precondition | declare propagation semantics | define validation

Status: OPEN — human decision required

## Q-10 — Which cancellation orderings promise failure, rollback or success, and what does unchanged mean with concurrent observers?

**Fault:** F-16
**Trigger:** adversarial trace

Question: Which cancellation orderings promise failure, rollback or success, and what does unchanged mean with concurrent observers?

Current behaviour: Locked entry check precedes immediate charge. Queued grants charge before close; both cancellation paths restore the charge when Done is observed. Intervening independent operations can see temporary reservation. (observed-in-code, semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:43 ("case <-done:"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:76 ("s.mu.Lock()"); semaphore/semaphore.go:81 ("s.cur -= n"); semaphore/semaphore.go:99 ("select {"); semaphore/semaphore.go:101 ("s.Release(n)"); semaphore/semaphore.go:156 ("s.cur += w.n"); semaphore/semaphore.go:158 ("close(w.ready)").)

Options: document exact cancellation boundary and net accounting | define stricter observational guarantee

Status: OPEN — human decision required

## Q-11 — Does TryAcquire's without-blocking contract exclude ordinary mutex contention, and do canceled callers have a prompt-return guarantee while waiting for the mutex?

**Fault:** F-13
**Trigger:** step-5 lint

Question: Does TryAcquire's without-blocking contract exclude ordinary mutex contention, and do canceled callers have a prompt-return guarantee while waiting for the mutex?

Current behaviour: Both calls unconditionally lock; Acquire checks Done only after locking. (observed-in-code, semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:43 ("case <-done:"); semaphore/semaphore.go:112 ("s.mu.Lock()").)

Options: document no waiter-queue blocking | require immediate acquisition attempt | specify cancellation latency

Status: OPEN — human decision required

## Q-12 — What FIFO ordering, head-of-line blocking, grant versus return order and backlog limit should be public guarantees?

**Fault:** F-20
**Trigger:** step-5 lint

Question: What FIFO ordering, head-of-line blocking, grant versus return order and backlog limit should be public guarantees?

Current behaviour: Barging is refused; notifier stops at first unfit head; ready closure and goroutine return are distinct; admission queue has no cap. (observed-in-code, semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:113 ("success := s.size-s.cur >= n && s.waiters.Len() == 0"); semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {"); semaphore/semaphore.go:158 ("close(w.ready)").)

Options: publish FIFO grant policy and limits | specify another policy | keep policy implementation-defined

Status: OPEN — human decision required

## Q-13 — Should a public API describe that Release(0) can change queue state and wake eligible waiters?

**Fault:** F-15
**Trigger:** part-B diff

Question: Should a public API describe that Release(0) can change queue state and wake eligible waiters?

Current behaviour: A non-panicking Release(0) always invokes notification. (observed-in-code, semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:129 ("s.notifyWaiters()"); semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {").)

Options: document notification effect | constrain zero release | specify no-op

Status: OPEN — human decision required
