# Adversarial traces

The single instance is local. A caller may protect a common resource through separate instances, but the library does not model or connect to that resource. No shared failure or external recovery reset reaches independent instances through this API, so shared-fate, backoff dispersion and recovery herd probes are inapplicable. semaphore/semaphore.go:22 ("w := &Weighted{size: n}").

### P-01a — Acquire then holder Release

Size 1 full, queue empty → live A locks, fails fit, appends then unlocks → H releases 1 under the same lock; notifier charges A, unlinks and closes ready → A returns nil.

Observed-in-code evidence: semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:123 ("s.mu.Lock()"); semaphore/semaphore.go:156 ("s.cur += w.n"); semaphore/semaphore.go:157 ("s.waiters.Remove(next)"); semaphore/semaphore.go:158 ("close(w.ready)"); semaphore/semaphore.go:105 ("return nil").

Decision: Q-12.

### P-01b — Holder Release then Acquire

Same start → H frees 1 and sees no head → A locks and evaluates fresh state; immediate charge and nil.

Observed-in-code evidence: semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:136 ("if next == nil {"); semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:57 ("s.cur += n").

Decision: none — control trace (code observation).

### P-02a — TryAcquire observes before Release

Size 2, one held, empty queue → T locks and observes one free for TryAcquire(2) → T returns false; H subsequently releases one.

Observed-in-code evidence: semaphore/semaphore.go:112 ("s.mu.Lock()"); semaphore/semaphore.go:113 ("success := s.size-s.cur >= n && s.waiters.Len() == 0"); semaphore/semaphore.go:118 ("return success"); semaphore/semaphore.go:124 ("s.cur -= n").

Decision: Q-11.

Assertion: Fresh capacity two, one unit held and no queue → a TryAcquire(2) sees insufficient capacity before the holder releases one → that try returns false without changing the semaphore.

cited text contemplates this ordering: no — semaphore/semaphore.go:110 ("// On success, returns true. On failure, returns false and leaves the semaphore unchanged."). jev: unclear, scope 0.03. The public comment omits the specified ordering. Code supplies the observation and the question remains open.

### P-02b — Release commits before TryAcquire

Same start → H releases one then unlocks → T reads two free under lock and returns true; no prior unlocked observation is reused.

Observed-in-code evidence: semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:130 ("s.mu.Unlock()"); semaphore/semaphore.go:112 ("s.mu.Lock()"); semaphore/semaphore.go:113 ("success := s.size-s.cur >= n && s.waiters.Len() == 0"); semaphore/semaphore.go:115 ("s.cur += n").

Decision: none — control trace (code observation).

### P-03a — Acquire then context closes

Size 1, live valid Acquire → if closure after observed-open entry check but before immediate return, grant may succeed; if queued, Done removes the entry; if already returned nil, closure alone does not release.

Observed-in-code evidence: semaphore/semaphore.go:43 ("case <-done:"); semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:75 ("case <-done:"); semaphore/semaphore.go:85 ("s.waiters.Remove(elem)"); semaphore/semaphore.go:105 ("return nil").

Decision: Q-10.

### P-03b — Context closure then Acquire

Before invocation, a standard context's Done already closed and one unit fits → locked admission sees Done → Err and no charge.

Observed-in-code evidence: semaphore/semaphore.go:39 ("done := ctx.Done()"); semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:43 ("case <-done:"); semaphore/semaphore.go:49 ("return ctx.Err()").

Decision: Q-10 Q-11.

Assertion: Fresh capacity one and a standard context whose Done already closed → caller invokes Acquire(1) before any other interaction → call returns ctx.Err without taking capacity despite being able to fit.

cited text contemplates this ordering: no — semaphore/semaphore.go:36 ("// are available or ctx is done. On success, returns nil. On failure, returns"). jev: unclear, scope 0.03. The public comment omits the specified ordering. Code supplies the observation and the question remains open.

### P-04a — Cancel before releasing at handoff

Size 1 full, positive head queued, live context → close its Done → holder releases. If cancellation wins the lock, it unlinks; otherwise holder charges, unlinks, closes ready, and the canceled call rolls back from either select continuation. It returns Err in both.

Observed-in-code evidence: semaphore/semaphore.go:75 ("case <-done:"); semaphore/semaphore.go:76 ("s.mu.Lock()"); semaphore/semaphore.go:81 ("s.cur -= n"); semaphore/semaphore.go:85 ("s.waiters.Remove(elem)"); semaphore/semaphore.go:99 ("select {"); semaphore/semaphore.go:101 ("s.Release(n)"); semaphore/semaphore.go:123 ("s.mu.Lock()"); semaphore/semaphore.go:156 ("s.cur += w.n"); semaphore/semaphore.go:158 ("close(w.ready)").

Decision: Q-10.

### P-04b — Release before cancel at handoff

Same start → holder releases, charges and closes Ready → close Done before the waiter checks it, causing rollback; after its open check, the call may return nil and must release normally.

Observed-in-code evidence: semaphore/semaphore.go:123 ("s.mu.Lock()"); semaphore/semaphore.go:156 ("s.cur += w.n"); semaphore/semaphore.go:158 ("close(w.ready)"); semaphore/semaphore.go:75 ("case <-done:"); semaphore/semaphore.go:81 ("s.cur -= n"); semaphore/semaphore.go:99 ("select {"); semaphore/semaphore.go:101 ("s.Release(n)"); semaphore/semaphore.go:105 ("return nil").

Decision: Q-10.

### P-05a — Second acquisition pending before handoff

Size 2 and fully held → same logical actor starts two goroutines with live context; each locks and gets its own element → one Release(1) grants only the earlier queued request; later Release(1) grants the other. If A entered Done before the mutex and B reaches the lock first, queue order is B then A, and B can complete first.

Observed-in-code evidence: semaphore/semaphore.go:39 ("done := ctx.Done()"); semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:69 ("ready := make(chan struct{})"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {"); semaphore/semaphore.go:156 ("s.cur += w.n"); semaphore/semaphore.go:158 ("close(w.ready)").

Decision: Q-06 Q-12. The later-invocation order is exercised by TestPilotLaterInvocationAdmitsFirst.

### P-05b — Holder releases before second acquisition

Size 2, 2 held, first request queued for 1 → holder releases 1, which reserves it for the first → same owner issues second while the first holds or has not run; no unit left, so second queues. In a size-2 instance with only one held unit, second can instead succeed immediately and consumes the spare unit.

Observed-in-code evidence: semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:156 ("s.cur += w.n").

Decision: Q-06.

### P-06a — Second acquisition then cancel first

Size 2 with 1 held → A requests 2 as head, then same logical actor B requests 1 → cancel only A, A unlinks and rescan below capacity reserves 1 for B. With shared canceled Context both instead return Err when observed.

Observed-in-code evidence: semaphore/semaphore.go:39 ("done := ctx.Done()"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:75 ("case <-done:"); semaphore/semaphore.go:85 ("s.waiters.Remove(elem)"); semaphore/semaphore.go:87 ("if isFront && s.size > s.cur {"); semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {"); semaphore/semaphore.go:156 ("s.cur += w.n"); semaphore/semaphore.go:101 ("s.Release(n)").

Decision: Q-06 Q-10 Q-12.

### P-06b — Cancel first then second acquisition

Same start → A unlinks before B locks, queue empty → B with independent Context charges immediately; same already-canceled context instead returns Err even though B fits.

Observed-in-code evidence: semaphore/semaphore.go:43 ("case <-done:"); semaphore/semaphore.go:49 ("return ctx.Err()"); semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:85 ("s.waiters.Remove(elem)").

Decision: Q-06 Q-10.

### P-07a — Cancellation removes blocking head at full capacity before release

Start Acquire_WaitersPending, size=cur=1 with Acquire(1) ahead of Acquire(0) → close head's Done → completion unlinks it and skips rescan → Acquire_EligibleHeadPending; TryAcquire(0) refuses and zero request has not returned. Later holder input Release(0) grants it; absent input it remains pending unless its own context closes.

Observed-in-code evidence: semaphore/semaphore.go:75 ("case <-done:"); semaphore/semaphore.go:85 ("s.waiters.Remove(elem)"); semaphore/semaphore.go:87 ("if isFront && s.size > s.cur {"); semaphore/semaphore.go:113 ("success := s.size-s.cur >= n && s.waiters.Len() == 0"); semaphore/semaphore.go:129 ("s.notifyWaiters()"); semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {"); semaphore/semaphore.go:158 ("close(w.ready)").

Decision: Q-01 Q-13.

- Reachability: Acquire_WaitersPending → Acquire_EligibleHeadPending — domain-analysis/weightedSemaphore/_probe/weighted_pilot_test.go:60 ("TryAcquire(0) bypassed the queued zero request")

### P-07b — Release before late cancellation at handoff

Full instance with positive head → holder releases and notifier grants and unlinks under lock → cancel before waiter checks Done; ready or Done branch returns weight once. If closure is after ready-side check, acquisition succeeds; independent holder may already have returned. Return from the notifier does not await the receiver.

Observed-in-code evidence: semaphore/semaphore.go:75 ("case <-done:"); semaphore/semaphore.go:76 ("s.mu.Lock()"); semaphore/semaphore.go:81 ("s.cur -= n"); semaphore/semaphore.go:94 ("case <-ready:"); semaphore/semaphore.go:99 ("select {"); semaphore/semaphore.go:101 ("s.Release(n)"); semaphore/semaphore.go:105 ("return nil"); semaphore/semaphore.go:123 ("s.mu.Lock()"); semaphore/semaphore.go:130 ("s.mu.Unlock()"); semaphore/semaphore.go:156 ("s.cur += w.n"); semaphore/semaphore.go:158 ("close(w.ready)").

Decision: Q-10.

### P-08a — Unowned release before acquisition

Size 1 empty → unrelated actor Release(1) decrements, unlocks and panics → caller recovers → Acquire(2) fits against cur=-1 before oversized branch and can succeed.

Observed-in-code evidence: semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:126 ("s.mu.Unlock()"); semaphore/semaphore.go:127 ("panic("semaphore: released more than held")"); semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:62 ("if n > s.size {").

Decision: Q-03 Q-04 Q-07.

### P-08b — Acquire before unowned release

Size 1 empty → one legitimate holder acquires 1 → unrelated Release(1) silently lowers aggregate to zero → another caller can acquire 1 while the first still uses the resource, then the legitimate release may debit the new holding.

Observed-in-code evidence: semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:122 ("func (s *Weighted) Release(n int64) {"); semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:129 ("s.notifyWaiters()").

Decision: Q-07.

### T-01 — Oversized abandoned

Size 2, weight 3 and Background → failed fast gate, unlock, Done nil waits indefinitely → unrelated Acquire(1) still succeeds. A cancellable same call returns Err after Done.

Observed-in-code evidence: semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:62 ("if n > s.size {"); semaphore/semaphore.go:65 ("<-done"); semaphore/semaphore.go:66 ("return ctx.Err()").

Decision: Q-02.

### T-02 — Owner disappears

A queued caller has no result consumer and no Done closure → without later release remains queued; with Release, private ready is closed, call succeeds and charge is retained even if no consumer ever reads success. Completed holder cancellation has no cleanup.

Observed-in-code evidence: semaphore/semaphore.go:69 ("ready := make(chan struct{})"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:75 ("case <-done:"); semaphore/semaphore.go:94 ("case <-ready:"); semaphore/semaphore.go:105 ("return nil"); semaphore/semaphore.go:156 ("s.cur += w.n"); semaphore/semaphore.go:158 ("close(w.ready)").

Decision: Q-05.

### T-03 — Wait for mutex after cancellation

A samples Done while open, stalls before or inside lock; H can release or another caller can consume capacity; Done closes meanwhile. When A acquires mutex its first gate observes closure even if H freed space. Holding lock delays return.

Observed-in-code evidence: semaphore/semaphore.go:39 ("done := ctx.Done()"); semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:43 ("case <-done:"); semaphore/semaphore.go:49 ("return ctx.Err()"); semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {").

Decision: Q-10 Q-11.

### T-04 — Acquire checks open before immediate commit

A holds mutex and sees open; context owner closes before charge; no resample before return. A succeeds and holder must release. Different from queued ready-side check.

Observed-in-code evidence: semaphore/semaphore.go:43 ("case <-done:"); semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:59 ("return nil"); semaphore/semaphore.go:99 ("select {").

Decision: Q-10.

### T-05 — Signed arithmetic

Size 1, Acquire(-1) can drive cur negative; immediate Acquire(2) then fits before oversize check. With extreme inputs subtraction wraps modulo 2^64 before branch evaluation. Release(-1) can increase cur without a cap check.

Observed-in-code evidence: semaphore/semaphore.go:22 ("w := &Weighted{size: n}"); semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:62 ("if n > s.size {"); semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:125 ("if s.cur < 0 {").

Decision: Q-03.

### T-06 — Wrong receiver

A holds 1 on X; release on Y decrements Y if it has weight, else can panic. X stays charged. Context assigned to wrong request instead affects only its supplied Done path.

Observed-in-code evidence: semaphore/semaphore.go:22 ("w := &Weighted{size: n}"); semaphore/semaphore.go:39 ("done := ctx.Done()"); semaphore/semaphore.go:122 ("func (s *Weighted) Release(n int64) {"); semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:127 ("panic("semaphore: released more than held")").

Decision: Q-08.

### T-07 — Restart / omitted teardown

Create Y while X has a live wait and holding. No reset or cancellation reaches X; later matching Release on X still notifies, while Release on Y affects only Y.

Observed-in-code evidence: semaphore/semaphore.go:22 ("w := &Weighted{size: n}"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:129 ("s.notifyWaiters()").

Decision: Q-05 Q-08.

### T-08 — Custom callback before entry

Done calls TryAcquire on its receiver while A is outside lock; nested TryAcquire can succeed and fill the instance, forcing A to queue. If Done blocks or panics, no A queue entry. No user callback runs inside the instance lock.

Observed-in-code evidence: semaphore/semaphore.go:39 ("done := ctx.Done()"); semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:52 ("if s.size-s.cur >= n && s.waiters.Len() == 0 {"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:112 ("s.mu.Lock()").

Decision: Q-09.

### T-09 — Custom Err after teardown

In pre-cancel, oversize, remove-first, grant-first rollback and ready-recheck paths Err executes after unlock or Release. If Err succeeds it decides return value; if it panics, queued cleanup already happened. An Err callback can reenter Release/TryAcquire, possibly changing weight then. A mismatched nil Err presents success after rollback.

Observed-in-code evidence: semaphore/semaphore.go:48 ("s.mu.Unlock()"); semaphore/semaphore.go:49 ("return ctx.Err()"); semaphore/semaphore.go:64 ("s.mu.Unlock()"); semaphore/semaphore.go:66 ("return ctx.Err()"); semaphore/semaphore.go:81 ("s.cur -= n"); semaphore/semaphore.go:85 ("s.waiters.Remove(elem)"); semaphore/semaphore.go:91 ("s.mu.Unlock()"); semaphore/semaphore.go:92 ("return ctx.Err()"); semaphore/semaphore.go:101 ("s.Release(n)"); semaphore/semaphore.go:102 ("return ctx.Err()").

Decision: Q-09.

### T-10 — Queue removal below and at capacity

Size 2 held 1, head 2 then tail 1; cancel head → rescan grants tail below capacity. Size 1 held 1 and zero tail → same removal skips, as in P-07a. Removing non-head only unlinks.

Observed-in-code evidence: semaphore/semaphore.go:76 ("s.mu.Lock()"); semaphore/semaphore.go:84 ("isFront := s.waiters.Front() == elem"); semaphore/semaphore.go:85 ("s.waiters.Remove(elem)"); semaphore/semaphore.go:87 ("if isFront && s.size > s.cur {"); semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {"); semaphore/semaphore.go:156 ("s.cur += w.n").

Decision: Q-01 Q-12.

### T-11 — Grant order versus return order

Two queued weight-1 calls at size 2 full. A single Release(2) closes channels in FIFO under lock; scheduler can run second goroutine first. No ownership/return handshaking follows the close.

Observed-in-code evidence: semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:129 ("s.notifyWaiters()"); semaphore/semaphore.go:140 ("w := next.Value.(waiter)"); semaphore/semaphore.go:156 ("s.cur += w.n"); semaphore/semaphore.go:157 ("s.waiters.Remove(next)"); semaphore/semaphore.go:158 ("close(w.ready)"); semaphore/semaphore.go:94 ("case <-ready:"); semaphore/semaphore.go:105 ("return nil").

Decision: Q-12.

### T-12 — Concurrent callback outcome on apparent unchanged state

At full capacity one release grants head and drops mutex. Before head rolls back, observer TryAcquire can fail on reserved weight. Once rollback completes, observer can succeed if queue empty. Mutex orders counter writes, so this is temporary reservation rather than lost weight.

Observed-in-code evidence: semaphore/semaphore.go:76 ("s.mu.Lock()"); semaphore/semaphore.go:81 ("s.cur -= n"); semaphore/semaphore.go:99 ("select {"); semaphore/semaphore.go:101 ("s.Release(n)"); semaphore/semaphore.go:112 ("s.mu.Lock()"); semaphore/semaphore.go:113 ("success := s.size-s.cur >= n && s.waiters.Len() == 0"); semaphore/semaphore.go:123 ("s.mu.Lock()"); semaphore/semaphore.go:130 ("s.mu.Unlock()"); semaphore/semaphore.go:156 ("s.cur += w.n").

Decision: Q-10.

### T-13 — Completed cancellation

Size 1 successful nil return → context closes → no release event occurs and no other context receiver tracks the completed call; TryAcquire(1) stays false until a Release.

Observed-in-code evidence: semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:59 ("return nil"); semaphore/semaphore.go:105 ("return nil"); semaphore/semaphore.go:113 ("success := s.size-s.cur >= n && s.waiters.Len() == 0"); semaphore/semaphore.go:124 ("s.cur -= n").

Decision: Q-05 Q-10.

Assertion: A request has already returned nil holding a unit → its context closes before any Release → the prior successful acquisition still consumes its unit.

cited text contemplates this ordering: no — semaphore/semaphore.go:37 ("// ctx.Err() and leaves the semaphore unchanged."). jev: unclear, scope 0.02. The public comment omits the specified ordering. Code supplies the observation and the question remains open.

### T-14 — Unbounded positive queue

Hold full weight, launch distinct Acquire(1) calls with live contexts. Every call appends; there is no admission limit besides per-weight feasibility. Cancellation removes entries one at a time, or holder release starts drain.

Observed-in-code evidence: semaphore/semaphore.go:62 ("if n > s.size {"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:85 ("s.waiters.Remove(elem)"); semaphore/semaphore.go:129 ("s.notifyWaiters()"); semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {").

Decision: Q-12.

