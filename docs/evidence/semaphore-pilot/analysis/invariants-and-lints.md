# Invariants and lint findings

<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 DOC-5 DOC-6 DOC-7 DOC-8 DOC-9 DOC-10 DOC-11 -->

## Doctrine mapping

| Doctrine | Kind | Target |
|---|---|---|
| DOC-1 | rejected | Repository issue triage instruction. It applies to reporters using the tracker. |
| DOC-2 | invariant | SYS-01 |
| DOC-3 | invariant | SYS-01 |
| DOC-4 | structural | The checked Acquire and TryAcquire columns each model a signed weight argument. |
| DOC-5 | invariant | SYS-02 |
| DOC-6 | invariant | SYS-03 |
| DOC-7 | invariant | SYS-04 |
| DOC-8 | invariant | SYS-05 |
| DOC-9 | invariant | SYS-05 |
| DOC-10 | cell | Acquire_WaitersPending x TryAcquire |
| DOC-11 | invariant | SYS-06 |

## Predicates and state-by-state check

NAT-01 (proposed assumption): size ≥ 0, operation weights ≥ 0, cur within [0,size] before a supported operation, head ≤ size, and all arithmetic representable. Matching release implies its weight ≤ cur. The public contract leaves this domain open, Q-03/Q-07. NAT-02: Context obeys Done/Err contract. NAT-03: follow pointer/no-copy discipline and release after success. NAT-SYS: if callers create several independent instances, there is no shared external event at this boundary.

| Predicate | No waiters | Waiters pending | Eligible head pending |
|---|---|---|---|
| SYS-01 Charge stays within capacity under NAT-01 and matching releases | Fast charge bounded by fit; invalid arithmetic or recovered panic breaks bound (Q-03/Q-04) | Grant bounded by fit; unowned release can violate real holder bound (Q-07) | Zero grant consumes no capacity; same invalid-input gaps |
| SYS-02 Live feasible Acquire eventually proceeds if no earlier blocker remains and it fits | Immediate after entry mutex | FIFO refusal can block small tail; cancellation can expose it (Q-12) | Zero head with no later input stays pending (Q-01) |
| SYS-03 Successful Acquire returns nil and has accounted weight | Immediate charge then nil | Notifier charge before ready; nil if Done recheck open | Same after later notification |
| SYS-04 Failed Acquire returns ctx.Err and leaves no residual charge/queue entry | Preclosed or oversized return Err without charge | Unlink or roll back; notification can progress others and transient charge is observable (Q-10) | Unlink or rollback; rescan gap can leave other entries queued (Q-01) |
| SYS-05 TryAcquire promptly returns true/false with only successful charge | Fit controls bool; waits for mutex (Q-11) | False even with spare capacity; waits for mutex (Q-11/Q-12) | False even for weight zero; same mutex contention |
| SYS-06 Valid Release subtracts n and allows notification | Decrements then scans empty list | Decrements then may grant several heads | Release(0) can notify without decreasing charge (Q-13) |

Evidence: semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:49 ("return ctx.Err()"); semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:62 ("if n > s.size {"); semaphore/semaphore.go:65 ("<-done"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:81 ("s.cur -= n"); semaphore/semaphore.go:85 ("s.waiters.Remove(elem)"); semaphore/semaphore.go:87 ("if isFront && s.size > s.cur {"); semaphore/semaphore.go:92 ("return ctx.Err()"); semaphore/semaphore.go:101 ("s.Release(n)"); semaphore/semaphore.go:105 ("return nil"); semaphore/semaphore.go:112 ("s.mu.Lock()"); semaphore/semaphore.go:113 ("success := s.size-s.cur >= n && s.waiters.Len() == 0"); semaphore/semaphore.go:115 ("s.cur += n"); semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:129 ("s.notifyWaiters()"); semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {"); semaphore/semaphore.go:156 ("s.cur += w.n"); semaphore/semaphore.go:158 ("close(w.ready)"). SYS-02 includes a proposed liveness interpretation, so the zero-boundary finding remains a decision about support and progress.

## Lint disposition

- Waiting/timeout: caller Context owns deadlines; oversized may never complete with nil Done, Q-02. Mutex waiting can delay both cancellation and tries, Q-11.
- Retries: no retry loop. Notifier repeats on a strictly shortened list until empty or blocked, semaphore/semaphore.go:157 ("s.waiters.Remove(next)").
- External failure and reentrancy: custom Context methods can stall/panic outside lock, Q-09. The seam contract sweep gives the supported Context outcomes.
- Cancellation: queued and granted-but-unreturned have explicit paths. A completed acquisition lacks a cancellation cleanup transition and held weight can be abandoned, Q-05/Q-10. Oversized may await caller cancel forever, Q-02.
- Startup/shutdown: initial capacity stored, no reset or shutdown protocol (Q-05). Negative counter survives recovered panic, Q-04. The panic has a diagnostic; its recovery semantics are open.
- Overload: queue has no entry limit. FIFO head-of-line blocking and concurrent-only refusal on a fitting try are user-model gaps, Q-12. The eligible zero head is another concurrency-only condition, Q-01.
- Synchronized reset: no reset callback, backoff or shared external resource seam. Ordinary Release may grant a burst inside one instance, semaphore/semaphore.go:129 ("s.notifyWaiters()").
- Lifecycle coupling and cancellation isolation: request, grant and holder tracks differ. Ready transfers an accounted grant, explicit rollback at semaphore/semaphore.go:81 ("s.cur -= n") and semaphore/semaphore.go:101 ("s.Release(n)"). After success no cancellation receiver remains, Q-05/Q-10. Dropped caller result does not reclaim weight.
- Dual ownership cleanup: no destructor path. Internal rollback and ordinary caller Release are distinct. Under normal contract the caller releases only on successful return. Unowned and duplicate release remain Q-07; the underlying panic condition remains Q-04.
- Retention: detached element may survive in a call frame until return; this is a runtime concern if observed lifetime matters, Q-05. No retained ownership/tombstone state.

## Step 8 verification

Finding ODC metadata is on each corresponding Q. Q-01 is a reproduced liveness issue conditional on zero being supported. Q-04 is a reproduced API/state consistency issue after panic recovery. Q-03 and Q-07 are contract risks tied to the signed and anonymous aggregate. Q-02, Q-05/Q-06, Q-08–Q-13 represent documentation, progress or boundary decisions. The mutex serializes grant and rollback; no lost update or under-lock user callback is asserted. Guard zero is literal; cur and free are computed quantities, and wraparound matters outside NAT-01.

- F01: Removing a canceled head triggers a rescan only when size exceeds cur, so at full weight there is no rescan. semaphore/semaphore.go:87 ("if isFront && s.size > s.cur {"). Jev supported. Confirmed in the surrounding branch.
- F02: A zero head fits when free weight equals zero. semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {"). Jev unclear. At equality the strict less-than test is false; therefore zero fits. Probe confirms later notification.
- F03: For a live Acquire whose fast path failed and weight exceeds size, the call waits only on context cancellation outside the queue. semaphore/semaphore.go:65 ("<-done"). Jev supported. Confirmed in the surrounding branch.
- F04: A negative weight admitted through the fast path decreases the aggregate charged weight. semaphore/semaphore.go:57 ("s.cur += n"). Jev supported. Confirmed in the surrounding branch.
- F05: Release writes the subtracted value before testing for negative charged weight. semaphore/semaphore.go:124 ("s.cur -= n"). Jev supported. Confirmed in the surrounding branch.
- F06: Release unlocks before panicking on negative charged weight, with no restoration. semaphore/semaphore.go:126 ("s.mu.Unlock()"). Jev supported. Confirmed in the surrounding branch.
- F07: Feasible overlapping Acquire calls allocate separate queue entries without a caller identifier. semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"). Jev unclear. Read private channel creation, payload fields and PushBack together; no owner key is in the payload.
- F08: The context callback Done runs before the semaphore mutex is acquired. semaphore/semaphore.go:39 ("done := ctx.Done()"). Jev unclear. Adjacent mutex acquisition is on source line 41.
- F09: Queued cancellation calls Context.Err after releasing the mutex. semaphore/semaphore.go:92 ("return ctx.Err()"). Jev unclear. Unlock is on source line 91 immediately before Err.
- F10: When cancellation wins the queued select after a ready grant, the weight is subtracted again from the held total and notification runs. semaphore/semaphore.go:81 ("s.cur -= n"). Jev supported. Subtracts exactly once to reverse the earlier notifier increment; wording does not imply two rollbacks.
- F11: After receiving ready, Acquire checks Done and calls Release if it is closed before returning Err. semaphore/semaphore.go:101 ("s.Release(n)"). Jev supported. Confirmed in the surrounding branch.
- F12: TryAcquire checks capacity and queue length under a potentially blocking mutex. semaphore/semaphore.go:112 ("s.mu.Lock()"). Jev supported. Confirmed in the surrounding branch.
- F13: The notifier leaves remaining waiters blocked when the first queued request cannot fit. semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {"). Jev supported. Confirmed in the surrounding branch.
- F14: A successful fast-path acquisition need not recheck Done after charging weight. semaphore/semaphore.go:57 ("s.cur += n"). Jev supported. Confirmed in the surrounding branch.
- F15: A Release of zero can invoke notification while leaving the aggregate charge unchanged. semaphore/semaphore.go:129 ("s.notifyWaiters()"). Jev supported. Confirmed in the surrounding branch.
- F16: Release has no caller identity argument and subtracts from the aggregate charge regardless of holder identity. semaphore/semaphore.go:122 ("func (s *Weighted) Release(n int64) {"). Jev supported. Confirmed in the surrounding branch.
- F17: A notified waiter is removed from the queue before its Ready channel is closed. semaphore/semaphore.go:157 ("s.waiters.Remove(next)"). Jev supported. Confirmed in the surrounding branch.
- F18: Acquire samples the supplied Context's Done channel and has no request-identity check. semaphore/semaphore.go:39 ("done := ctx.Done()"). Jev unclear. Done is the supplied interface method; read receipt and the signature together.

- TF01 and TF02 supported. The cancellation test checks post-release full capacity at semaphore/semaphore_test.go:228 ("if !sem.TryAcquire(2) {"). The panic test exercises the initial panic at semaphore/semaphore_test.go:52 ("release of an unacquired weighted semaphore did not panic"). Neither observes post-recovery behavior; the overlay supplies that check.
