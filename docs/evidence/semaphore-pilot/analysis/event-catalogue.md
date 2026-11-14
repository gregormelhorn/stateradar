# Event catalogue

<!-- event-ids: NewWeighted Acquire TryAcquire Release ContextDone Grant UV-Abandon UV-Delay UV-Recreate UV-RepeatAcquire UV-RepeatTry UV-RepeatRelease UV-WrongReceiver UV-Weight UV-ForeignContext UV-UnownedRelease UV-ContextFault UV-RepeatedDone UV-ContextOrder -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| NewWeighted | external | Constructor caller | Capacity and a new instance. semaphore/semaphore.go:22 ("w := &Weighted{size: n}"). |
| Acquire | external | Request caller | Weighted blocking acquisition request with Context. semaphore/semaphore.go:39 ("done := ctx.Done()"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"). |
| TryAcquire | external | Request caller | Weighted synchronous try request. semaphore/semaphore.go:111 ("func (s *Weighted) TryAcquire(n int64) bool {"); semaphore/semaphore.go:118 ("return success"). |
| Release | external | Holder | Release by weight. semaphore/semaphore.go:122 ("func (s *Weighted) Release(n int64) {"); semaphore/semaphore.go:124 ("s.cur -= n"). |
| ContextDone | external | Context owner | Cancellation or deadline via Done closure. semaphore/semaphore.go:39 ("done := ctx.Done()"); semaphore/semaphore.go:75 ("case <-done:"); semaphore/semaphore.go:100 ("case <-done:"). |
| Grant | internal | Semaphore | Private waiter notification via channel close. semaphore/semaphore.go:69 ("ready := make(chan struct{})"); semaphore/semaphore.go:158 ("close(w.ready)"). |
| UV-Abandon | external | Caller or holder | Omission is a scenario marker, never a semaphore invocation. For an existing request, track caller departure while queued or omitted release after success. semaphore/semaphore.go:38 ("func (s *Weighted) Acquire(ctx context.Context, n int64) error {"); semaphore/semaphore.go:75 ("case <-done:"); semaphore/semaphore.go:122 ("func (s *Weighted) Release(n int64) {"). |
| UV-Delay | external | Caller, holder or context owner | Delayed request, release or cancellation past a caller deadline. semaphore/semaphore.go:65 ("<-done"). |
| UV-Recreate | external | Constructor caller | Concurrent constructors or restart mid-operation using a fresh instance. semaphore/semaphore.go:22 ("w := &Weighted{size: n}"). |
| UV-RepeatAcquire | external | Request caller | Second Acquire by the same logical caller while the first is pending or while its successful weight is still held. semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"). |
| UV-RepeatTry | external | Request caller | Second TryAcquire or a competing try by the same logical caller. semaphore/semaphore.go:113 ("success := s.size-s.cur >= n && s.waiters.Len() == 0"). |
| UV-RepeatRelease | external | Holder | Duplicate, stale, simultaneous or early Release. semaphore/semaphore.go:124 ("s.cur -= n"). |
| UV-WrongReceiver | external | Caller or holder | Well-typed receiver for another Weighted instance, separate from wrong weight. semaphore/semaphore.go:122 ("func (s *Weighted) Release(n int64) {"). |
| UV-Weight | external | Caller or holder | Zero, negative, oversized or extreme signed weight/capacity; valid but unintended weight. semaphore/semaphore.go:28 ("type Weighted struct {"). |
| UV-ForeignContext | external | Request caller | Well-formed Context intended for a different request or lifetime. semaphore/semaphore.go:39 ("done := ctx.Done()"). |
| UV-UnownedRelease | external | Holder | Release of aggregate weight with no matching ownership. semaphore/semaphore.go:124 ("s.cur -= n"). |
| UV-ContextFault | external | Context implementation | Nil interface, custom method blocks/panics/reenters, inconsistent Done/Err or premature signal. semaphore/semaphore.go:39 ("done := ctx.Done()"). |
| UV-RepeatedDone | external | Context owner | Repeated cancellation of a standard context. semaphore/semaphore.go:75 ("case <-done:"). |
| UV-ContextOrder | external | Context owner | Done while mutex acquisition, enqueue, grant or return overlaps. semaphore/semaphore.go:41 ("s.mu.Lock()"). |

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| NewWeighted: Constructor caller | UV-Abandon | UV-Abandon | UV-Recreate | UV-Recreate | UV-Recreate | UV-Recreate | UV-Weight |
| Acquire: Request caller | UV-Abandon | UV-Delay | UV-RepeatAcquire | UV-RepeatAcquire | UV-RepeatAcquire | UV-WrongReceiver | UV-Weight, UV-ForeignContext |
| TryAcquire: Request caller | UV-Abandon | UV-Delay | UV-RepeatTry | UV-RepeatTry | UV-RepeatTry | UV-WrongReceiver | UV-Weight |
| Release: Holder | UV-Abandon | UV-Delay | UV-RepeatRelease | UV-RepeatRelease | UV-RepeatRelease | UV-UnownedRelease | UV-WrongReceiver, UV-Weight |
| ContextDone: Context owner | UV-ContextFault | UV-Delay | UV-RepeatedDone | UV-ContextOrder | UV-ContextOrder | UV-ContextFault | UV-ForeignContext, UV-ContextFault |
| Grant: Semaphore | n/a: grant is an inline close; semaphore/semaphore.go:158 ("close(w.ready)"). | n/a: close is inline; receiver scheduling is separate; semaphore/semaphore.go:158 ("close(w.ready)"). | n/a: head is first unlinked under the lock; semaphore/semaphore.go:157 ("s.waiters.Remove(next)"). | n/a: the notifier reads the current head; semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {"). | n/a: notification is called with the mutex held; semaphore/semaphore.go:129 ("s.notifyWaiters()"). | n/a: ready is private; semaphore/semaphore.go:69 ("ready := make(chan struct{})"). | n/a: entry and channel are paired; semaphore/semaphore.go:70 ("w := waiter{n: n, ready: ready}"). |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Acquire → Release | Requester and holder on the same Weighted instance |
| P-01b | Release → Acquire | Requester and holder on the same Weighted instance |
| P-02a | TryAcquire → Release | Requester and holder competing for capacity |
| P-02b | Release → TryAcquire | Requester and holder competing for capacity |
| P-03a | Acquire → ContextDone | Requester and cancellation owner on the same acquisition |
| P-03b | ContextDone → Acquire | Requester and cancellation owner on the same acquisition |
| P-04a | ContextDone → Release | Cancellation owner and holder at a queued acquisition's handoff |
| P-04b | Release → ContextDone | Cancellation owner and holder at a queued acquisition's handoff |
| P-05a | UV-RepeatAcquire → Release | One request actor and a holder with repeated acquisition pending |
| P-05b | Release → UV-RepeatAcquire | One request actor and a holder with repeated acquisition pending |
| P-06a | UV-RepeatAcquire → ContextDone | One request actor and the first request's context owner |
| P-06b | ContextDone → UV-RepeatAcquire | One request actor and the first request's context owner |
| P-07a | UV-ContextOrder → Release | Cancellation at an in-flight handoff |
| P-07b | Release → UV-ContextOrder | Cancellation at an in-flight handoff |
| P-08a | UV-UnownedRelease → Acquire | Independent releasing actor and requester sharing aggregate weight |
| P-08b | Acquire → UV-UnownedRelease | Independent releasing actor and requester sharing aggregate weight |

## Remembrance semantics

Observed in code. Requests have private queue entries. semaphore/semaphore.go:69 ("ready := make(chan struct{})"); semaphore/semaphore.go:71 ("elem := s.waiters.PushBack(w)"); semaphore/semaphore.go:85 ("s.waiters.Remove(elem)"); semaphore/semaphore.go:157 ("s.waiters.Remove(next)"). Observed in code. Aggregate counter changes at admission, release, grant and rollback. semaphore/semaphore.go:57 ("s.cur += n"); semaphore/semaphore.go:115 ("s.cur += n"); semaphore/semaphore.go:124 ("s.cur -= n"); semaphore/semaphore.go:156 ("s.cur += w.n"); semaphore/semaphore.go:81 ("s.cur -= n"). No ownership ledger or historical queue in the instance fields. semaphore/semaphore.go:30 ("cur     int64"); semaphore/semaphore.go:32 ("waiters list.List"). Observed in code. Detached list elements can remain referenced by the call frame until it exits. No time-based retention policy for a live pending call.

## Lock-discipline annotation

Observed in code. Acquire, its queued cancellation branch, TryAcquire, and Release take the instance mutex. semaphore/semaphore.go:41 ("s.mu.Lock()"); semaphore/semaphore.go:76 ("s.mu.Lock()"); semaphore/semaphore.go:112 ("s.mu.Lock()"); semaphore/semaphore.go:123 ("s.mu.Lock()"). Notification closes a private channel under that mutex. semaphore/semaphore.go:129 ("s.notifyWaiters()"); semaphore/semaphore.go:158 ("close(w.ready)"). Observed in code. Caller-supplied Context.Done precedes lock acquisition and Context.Err is called outside the instance lock. semaphore/semaphore.go:39 ("done := ctx.Done()"); semaphore/semaphore.go:48 ("s.mu.Unlock()"); semaphore/semaphore.go:91 ("s.mu.Unlock()"); semaphore/semaphore.go:101 ("s.Release(n)"). No explicit user callback is invoked in a mutex-held section.

## Catalogue notes

Direct Go library boundary. Request caller, holder, context owner and constructor roles can be played by the same or different goroutines. Constructor calls create a different instance. No service adapter is supplied.

## Event annotations

### NewWeighted
- gate: capacity argument
- upstream_guards: Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.
- coverage:
  - loss: UV-Abandon
  - delay: UV-Abandon
  - duplication: UV-Recreate
  - out-of-order: UV-Recreate
  - contradiction: UV-Recreate
  - commission: UV-Recreate
  - value: UV-Weight

### Acquire
- gate: requested weight, context and semaphore state
- upstream_guards: Go Context interface governs stable Done channel and Err after closure. Custom implementations enter directly; no upstream adapter.
- coverage:
  - loss: UV-Abandon
  - delay: UV-Delay
  - duplication: UV-RepeatAcquire
  - out-of-order: UV-RepeatAcquire
  - contradiction: UV-RepeatAcquire
  - commission: UV-WrongReceiver
  - value: UV-Weight, UV-ForeignContext

### TryAcquire
- gate: requested weight and semaphore state
- upstream_guards: Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.
- coverage:
  - loss: UV-Abandon
  - delay: UV-Delay
  - duplication: UV-RepeatTry
  - out-of-order: UV-RepeatTry
  - contradiction: UV-RepeatTry
  - commission: UV-WrongReceiver
  - value: UV-Weight

### Release
- gate: released weight and semaphore state
- upstream_guards: Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.
- coverage:
  - loss: UV-Abandon
  - delay: UV-Delay
  - duplication: UV-RepeatRelease
  - out-of-order: UV-RepeatRelease
  - contradiction: UV-RepeatRelease
  - commission: UV-UnownedRelease
  - value: UV-WrongReceiver, UV-Weight

### ContextDone
- gate: request phase, channel state and semaphore state
- upstream_guards: Go Context interface governs stable Done channel and Err after closure. Custom implementations enter directly; no upstream adapter.
- coverage:
  - loss: UV-ContextFault
  - delay: UV-Delay
  - duplication: UV-RepeatedDone
  - out-of-order: UV-ContextOrder
  - contradiction: UV-ContextOrder
  - commission: UV-ContextFault
  - value: UV-ForeignContext, UV-ContextFault

### Grant
- gate: queue front and capacity
- upstream_guards: The channel is created and closed within this boundary.
- coverage:
  - loss: n/a: grant is an inline close; semaphore/semaphore.go:158 ("close(w.ready)").
  - delay: n/a: close is inline; receiver scheduling is separate; semaphore/semaphore.go:158 ("close(w.ready)").
  - duplication: n/a: head is first unlinked under the lock; semaphore/semaphore.go:157 ("s.waiters.Remove(next)").
  - out-of-order: n/a: the notifier reads the current head; semaphore/semaphore.go:141 ("if s.size-s.cur < w.n {").
  - contradiction: n/a: notification is called with the mutex held; semaphore/semaphore.go:129 ("s.notifyWaiters()").
  - commission: n/a: ready is private; semaphore/semaphore.go:69 ("ready := make(chan struct{})").
  - value: n/a: entry and channel are paired; semaphore/semaphore.go:70 ("w := waiter{n: n, ready: ready}").

### UV-Abandon
- gate: same as base operation
- upstream_guards: Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-Delay
- gate: same as base operation
- upstream_guards: Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-Recreate
- gate: same as base operation
- upstream_guards: Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-RepeatAcquire
- gate: same as base operation
- upstream_guards: Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-RepeatTry
- gate: same as base operation
- upstream_guards: Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-RepeatRelease
- gate: same as base operation
- upstream_guards: Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-WrongReceiver
- gate: same as base operation
- upstream_guards: Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example., Only direct public calls can target an unintended instance. A private Ready signal belongs to its own Acquire and cannot route to another receiver. semaphore/semaphore.go:69 ("ready := make(chan struct{})"); semaphore/semaphore.go:70 ("w := waiter{n: n, ready: ready}"); semaphore/semaphore.go:158 ("close(w.ready)").

### UV-Weight
- gate: same as base operation
- upstream_guards: Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-ForeignContext
- gate: same as base operation
- upstream_guards: Go Context interface governs stable Done channel and Err after closure. Custom implementations enter directly; no upstream adapter.

### UV-UnownedRelease
- gate: same as base operation
- upstream_guards: Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-ContextFault
- gate: same as base operation
- upstream_guards: Go Context interface governs stable Done channel and Err after closure. Custom implementations enter directly; no upstream adapter.

### UV-RepeatedDone
- gate: same as base operation
- upstream_guards: Go Context interface governs stable Done channel and Err after closure. Custom implementations enter directly; no upstream adapter.

### UV-ContextOrder
- gate: same as base operation
- upstream_guards: Go Context interface governs stable Done channel and Err after closure. Custom implementations enter directly; no upstream adapter.

