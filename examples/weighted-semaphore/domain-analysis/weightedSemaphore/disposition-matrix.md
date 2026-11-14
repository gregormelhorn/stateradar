# Disposition matrix

<!-- states: Acquire_NoWaiters Acquire_WaitersPending -->

Abstraction: queue projection at mutex-release boundaries. Each primary disposition describes the representative guarded scenario in cells/state_cells_test.go.txt. Guarded alternatives in the notes are part of the contract and covered by the mandatory decision/scenario suites. This is not an unconditional outcome table for every argument.

| State | NewWeighted | Acquire | TryAcquire | Release | ContextDone |
|---|---|---|---|---|---|
| **Acquire_NoWaiters** | handle (DR-002) | transition → Acquire_WaitersPending (DR-004) | handle (DR-011) | handle (DR-013) | reject (DR-010) |
| **Acquire_WaitersPending** | handle (DR-005) | defer (queued) (DR-012) | reject (DR-012) | transition → Acquire_NoWaiters (DR-001) | transition → Acquire_NoWaiters (DR-010) |

| State | Grant | UV-Abandon | UV-Delay | UV-Recreate | UV-RepeatAcquire |
|---|---|---|---|---|---|
| **Acquire_NoWaiters** | handle (DR-010) | ignore (documented) (DR-005) | handle (DR-011) | handle (DR-005) | transition → Acquire_WaitersPending (DR-006) |
| **Acquire_WaitersPending** | transition → Acquire_NoWaiters (DR-012) | ignore (documented) (DR-005) | handle (DR-011) | handle (DR-008) | defer (queued) (DR-006) |

| State | UV-RepeatTry | UV-RepeatRelease | UV-WrongReceiver | UV-Weight | UV-ForeignContext |
|---|---|---|---|---|---|
| **Acquire_NoWaiters** | handle (DR-006) | handle (DR-003) | ignore (documented) (DR-008) | reject (DR-002) | reject (DR-008) |
| **Acquire_WaitersPending** | reject (DR-006) | transition → Acquire_NoWaiters (DR-007) | ignore (documented) (DR-008) | reject (DR-002) | reject (DR-008) |

| State | UV-UnownedRelease | UV-ContextFault | UV-RepeatedDone | UV-ContextOrder |
|---|---|---|---|---|
| **Acquire_NoWaiters** | handle (DR-007) | handle (DR-009) | ignore (documented) (DR-010) | handle (DR-010) |
| **Acquire_WaitersPending** | transition → Acquire_NoWaiters (DR-007) | handle (DR-009) | transition → Acquire_NoWaiters (DR-005) | transition → Acquire_NoWaiters (DR-010) |

## Guarded cell notes and evidence

### Acquire_NoWaiters × NewWeighted

Independent new instance; negative constructor size panics without touching the existing instance.

Authority: DR-002; resolved Q-03. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:29 ("w := &Weighted{size: n}")

### Acquire_NoWaiters × Acquire

Feasible live request queues when admission is unavailable. Empty queue may instead grant immediately. Negative input panics, pre-canceled Context returns its error, and oversized input returns a size error without queueing.

Authority: DR-004; resolved Q-02. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:97 ("elem := s.waiters.PushBack(w)")

### Acquire_NoWaiters × TryAcquire

With no queue, fitting nonnegative weight grants, otherwise false. With a queue, false even when weight fits. Negative weight panics.

Authority: DR-011; resolved Q-11. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:145 ("success := s.size-s.cur >= n && s.waiters.Len() == 0")

### Acquire_NoWaiters × Release

Valid positive release drains only the eligible FIFO prefix; a blocked tail may remain. Negative/over-release panics before mutation. Zero release changes neither accounting nor queue.

Authority: DR-013; resolved Q-13. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:171 ("s.notifyWaiters()")

### Acquire_NoWaiters × ContextDone

Preclosed acquisition fails; completed success stays held. Pending cancellation removes the entry or rolls back a racing grant. Removing a head notifies its eligible successors; a remaining blocked queue stays pending.

Authority: DR-010; resolved Q-10. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:111 ("s.waiters.Remove(elem)")

### Acquire_NoWaiters × Grant

Notification reserves and unlinks in FIFO order. This internal event is triggered by release/cancellation, not injected directly. A ready recipient may return or roll back; other queued requests may remain.

Authority: DR-010; resolved Q-10. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:200 ("close(w.ready)")

### Acquire_NoWaiters × UV-Abandon

No automatic reclamation on caller disappearance. Pending work needs cancellation and success requires matching release; obligations remain with callers.

Authority: DR-005; resolved Q-05. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:66 ("done := ctx.Done()")

### Acquire_NoWaiters × UV-Delay

No fixed latency bound is promised. A delay by itself changes no modeled state; eventual processing follows the original event. Finite tests cannot certify this absence of a bound.

Authority: DR-011; resolved Q-11. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:68 ("s.mu.Lock()")

### Acquire_NoWaiters × UV-Recreate

Recreation is independent; no cleanup or capacity transfer reaches the old receiver.

Authority: DR-005; resolved Q-05. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:29 ("w := &Weighted{size: n}")

### Acquire_NoWaiters × UV-RepeatAcquire

Independent invocation: can grant again if room and no queue, or append a distinct feasible request. It can self-block; validation and cancellation rules still apply.

Authority: DR-006; resolved Q-06. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:97 ("elem := s.waiters.PushBack(w)")

### Acquire_NoWaiters × UV-RepeatTry

Each try is independent. Empty queue may charge repeatedly until full; queued predecessors prevent every bypass.

Authority: DR-006; resolved Q-06. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:145 ("success := s.size-s.cur >= n && s.waiters.Len() == 0")

### Acquire_NoWaiters × UV-RepeatRelease

Each call applies to the aggregate. An excess panics without mutation; duplicates covered by other holdings can go undetected. This is a caller-error detection limit, not permission to double-release.

Authority: DR-003; resolved Q-04. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:166 ("if n > s.cur {")

### Acquire_NoWaiters × UV-WrongReceiver

The intended instance sees no call. The actual receiver processes its own accounting; caller intent is not inferred.

Authority: DR-008; resolved Q-08. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:161 ("func (s *Weighted) Release(n int64) {")

### Acquire_NoWaiters × UV-Weight

Negative arguments panic before mutation; oversized Acquire errors and oversized TryAcquire is false. Zero remains valid with FIFO; nonnegative int64 arithmetic stays within size.

Authority: DR-002; resolved Q-03. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:64 ("panic("semaphore: negative weight")")

### Acquire_NoWaiters × UV-ForeignContext

A preclosed supplied Context rejects, independent of the intended Context. A live supplied Context follows Acquire admission; no identity check or Context substitution.

Authority: DR-008; resolved Q-08. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:66 ("done := ctx.Done()")

### Acquire_NoWaiters × UV-UnownedRelease

Release responsibility can transfer. Aggregate accounting cannot distinguish an authorized transfer from a mistaken release while held weight covers it. Excess still panics unchanged.

Authority: DR-007; resolved Q-07. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:166 ("if n > s.cur {")

### Acquire_NoWaiters × UV-ContextFault

Delegates to the supplied Context. Outside NAT-Context no return, recovery or progress outcome is promised; handle denotes delegation, not successful completion.

Authority: DR-009; resolved Q-09. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:66 ("done := ctx.Done()")

### Acquire_NoWaiters × UV-RepeatedDone

Standard CancelFunc repetition is idempotent. A successful acquisition stays held; a queued call cleans up once. This is upstream Context contract, not a second delivered channel event.

Authority: DR-010; resolved Q-10. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:66 ("done := ctx.Done()")

### Acquire_NoWaiters × UV-ContextOrder

After the final applicable check, success may coexist with cancellation. Before a queued final check cancellation rolls the grant back. Temporary reservation may affect other observers.

Authority: DR-010; resolved Q-10. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:120 ("case <-ready:")

### Acquire_WaitersPending × NewWeighted

Independent new instance; negative constructor size panics without touching the existing instance.

Authority: DR-005; resolved Q-05. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:29 ("w := &Weighted{size: n}")

### Acquire_WaitersPending × Acquire

Feasible live request queues when admission is unavailable. Empty queue may instead grant immediately. Negative input panics, pre-canceled Context returns its error, and oversized input returns a size error without queueing.

Authority: DR-012; resolved Q-12. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:97 ("elem := s.waiters.PushBack(w)")

### Acquire_WaitersPending × TryAcquire

With no queue, fitting nonnegative weight grants, otherwise false. With a queue, false even when weight fits. Negative weight panics.

Authority: DR-012; resolved Q-12. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:145 ("success := s.size-s.cur >= n && s.waiters.Len() == 0")

### Acquire_WaitersPending × Release

Valid positive release drains only the eligible FIFO prefix; a blocked tail may remain. Negative/over-release panics before mutation. Zero release changes neither accounting nor queue.

Authority: DR-001; resolved Q-01. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:171 ("s.notifyWaiters()")

### Acquire_WaitersPending × ContextDone

Preclosed acquisition fails; completed success stays held. Pending cancellation removes the entry or rolls back a racing grant. Removing a head notifies its eligible successors; a remaining blocked queue stays pending.

Authority: DR-010; resolved Q-10. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:111 ("s.waiters.Remove(elem)")

### Acquire_WaitersPending × Grant

Notification reserves and unlinks in FIFO order. This internal event is triggered by release/cancellation, not injected directly. A ready recipient may return or roll back; other queued requests may remain.

Authority: DR-012; resolved Q-12. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:200 ("close(w.ready)")

### Acquire_WaitersPending × UV-Abandon

No automatic reclamation on caller disappearance. Pending work needs cancellation and success requires matching release; obligations remain with callers.

Authority: DR-005; resolved Q-05. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:66 ("done := ctx.Done()")

### Acquire_WaitersPending × UV-Delay

No fixed latency bound is promised. A delay by itself changes no modeled state; eventual processing follows the original event. Finite tests cannot certify this absence of a bound.

Authority: DR-011; resolved Q-11. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:68 ("s.mu.Lock()")

### Acquire_WaitersPending × UV-Recreate

Recreation is independent; no cleanup or capacity transfer reaches the old receiver.

Authority: DR-008; resolved Q-08. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:29 ("w := &Weighted{size: n}")

### Acquire_WaitersPending × UV-RepeatAcquire

Independent invocation: can grant again if room and no queue, or append a distinct feasible request. It can self-block; validation and cancellation rules still apply.

Authority: DR-006; resolved Q-06. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:97 ("elem := s.waiters.PushBack(w)")

### Acquire_WaitersPending × UV-RepeatTry

Each try is independent. Empty queue may charge repeatedly until full; queued predecessors prevent every bypass.

Authority: DR-006; resolved Q-06. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:145 ("success := s.size-s.cur >= n && s.waiters.Len() == 0")

### Acquire_WaitersPending × UV-RepeatRelease

Each call applies to the aggregate. An excess panics without mutation; duplicates covered by other holdings can go undetected. This is a caller-error detection limit, not permission to double-release.

Authority: DR-007; resolved Q-07. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:166 ("if n > s.cur {")

### Acquire_WaitersPending × UV-WrongReceiver

The intended instance sees no call. The actual receiver processes its own accounting; caller intent is not inferred.

Authority: DR-008; resolved Q-08. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:161 ("func (s *Weighted) Release(n int64) {")

### Acquire_WaitersPending × UV-Weight

Negative arguments panic before mutation; oversized Acquire errors and oversized TryAcquire is false. Zero remains valid with FIFO; nonnegative int64 arithmetic stays within size.

Authority: DR-002; resolved Q-03. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:64 ("panic("semaphore: negative weight")")

### Acquire_WaitersPending × UV-ForeignContext

A preclosed supplied Context rejects, independent of the intended Context. A live supplied Context follows Acquire admission; no identity check or Context substitution.

Authority: DR-008; resolved Q-08. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:66 ("done := ctx.Done()")

### Acquire_WaitersPending × UV-UnownedRelease

Release responsibility can transfer. Aggregate accounting cannot distinguish an authorized transfer from a mistaken release while held weight covers it. Excess still panics unchanged.

Authority: DR-007; resolved Q-07. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:166 ("if n > s.cur {")

### Acquire_WaitersPending × UV-ContextFault

Delegates to the supplied Context. Outside NAT-Context no return, recovery or progress outcome is promised; handle denotes delegation, not successful completion.

Authority: DR-009; resolved Q-09. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:66 ("done := ctx.Done()")

### Acquire_WaitersPending × UV-RepeatedDone

Standard CancelFunc repetition is idempotent. A successful acquisition stays held; a queued call cleans up once. This is upstream Context contract, not a second delivered channel event.

Authority: DR-005; resolved Q-05. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:66 ("done := ctx.Done()")

### Acquire_WaitersPending × UV-ContextOrder

After the final applicable check, success may coexist with cancellation. Before a queued final check cancellation rolls the grant back. Temporary reservation may affect other observers.

Authority: DR-010; resolved Q-10. Provenance: observed-in-code.

examples/weighted-semaphore/semaphore/semaphore.go:120 ("case <-ready:")
