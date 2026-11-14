# Evaluation event catalogue

<!-- event-ids: NewWeighted Acquire TryAcquire Release ContextDone Grant UV-Abandon UV-Delay UV-Recreate UV-RepeatAcquire UV-RepeatTry UV-RepeatRelease UV-WrongReceiver UV-Weight UV-ForeignContext UV-UnownedRelease UV-ContextFault UV-RepeatedDone UV-ContextOrder -->
<!-- pair-ids: P-01a P-01b P-02a P-02b P-03a P-03b P-04a P-04b P-05a P-05b P-06a P-06b P-07a P-07b P-08a P-08b -->

## NewWeighted

Classification: external. Gate: Independent new instance; negative constructor size panics without touching the existing instance.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## Acquire

Classification: external. Gate: Feasible live request queues when admission is unavailable. Empty queue may instead grant immediately. Negative input panics, pre-canceled Context returns its error, and oversized input returns a size error without queueing.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## TryAcquire

Classification: external. Gate: With no queue, fitting nonnegative weight grants, otherwise false. With a queue, false even when weight fits. Negative weight panics.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## Release

Classification: external. Gate: Valid positive release drains only the eligible FIFO prefix; a blocked tail may remain. Negative/over-release panics before mutation. Zero release changes neither accounting nor queue.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## ContextDone

Classification: internal. Gate: Preclosed acquisition fails; completed success stays held. Pending cancellation removes the entry or rolls back a racing grant. Removing a head notifies its eligible successors; a remaining blocked queue stays pending.

Upstream guard: NAT-Context: supplied Context controls Done; standard CancelFunc is idempotent. See extraction.md callee contracts.

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## Grant

Classification: internal. Gate: Notification reserves and unlinks in FIFO order. This internal event is triggered by release/cancellation, not injected directly. A ready recipient may return or roll back; other queued requests may remain.

Upstream guard: Private channel created with each queue entry; notifyWaiters is called under the mutex. No external injection seam.

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## UV-Abandon

Classification: undesired-variant. Gate: No automatic reclamation on caller disappearance. Pending work needs cancellation and success requires matching release; obligations remain with callers.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## UV-Delay

Classification: undesired-variant. Gate: No fixed latency bound is promised. A delay by itself changes no modeled state; eventual processing follows the original event. Finite tests cannot certify this absence of a bound.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## UV-Recreate

Classification: undesired-variant. Gate: Recreation is independent; no cleanup or capacity transfer reaches the old receiver.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## UV-RepeatAcquire

Classification: undesired-variant. Gate: Independent invocation: can grant again if room and no queue, or append a distinct feasible request. It can self-block; validation and cancellation rules still apply.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## UV-RepeatTry

Classification: undesired-variant. Gate: Each try is independent. Empty queue may charge repeatedly until full; queued predecessors prevent every bypass.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## UV-RepeatRelease

Classification: undesired-variant. Gate: Each call applies to the aggregate. An excess panics without mutation; duplicates covered by other holdings can go undetected. This is a caller-error detection limit, not permission to double-release.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## UV-WrongReceiver

Classification: undesired-variant. Gate: The intended instance sees no call. The actual receiver processes its own accounting; caller intent is not inferred.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## UV-Weight

Classification: undesired-variant. Gate: Negative arguments panic before mutation; oversized Acquire errors and oversized TryAcquire is false. Zero remains valid with FIFO; nonnegative int64 arithmetic stays within size.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## UV-ForeignContext

Classification: undesired-variant. Gate: A preclosed supplied Context rejects, independent of the intended Context. A live supplied Context follows Acquire admission; no identity check or Context substitution.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## UV-UnownedRelease

Classification: undesired-variant. Gate: Release responsibility can transfer. Aggregate accounting cannot distinguish an authorized transfer from a mistaken release while held weight covers it. Excess still panics unchanged.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## UV-ContextFault

Classification: undesired-variant. Gate: Delegates to the supplied Context. Outside NAT-Context no return, recovery or progress outcome is promised; handle denotes delegation, not successful completion.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## UV-RepeatedDone

Classification: undesired-variant. Gate: Standard CancelFunc repetition is idempotent. A successful acquisition stays held; a queued call cleans up once. This is upstream Context contract, not a second delivered channel event.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## UV-ContextOrder

Classification: undesired-variant. Gate: After the final applicable check, success may coexist with cancellation. Before a queued final check cancellation rolls the grant back. Temporary reservation may affect other observers.

Upstream guard: Direct boundary call; caller selects receiver/Context (DR-008). Context methods must satisfy NAT-Context (DR-009). Numeric validation is inside this component (DR-002/004).

Provenance: observed-in-code with accepted decision authority; see matrix and traces for fragment anchors.

## Undesired-variant coverage

```json
{
  "NewWeighted": {
    "loss": "UV-Abandon",
    "delay": "UV-Delay",
    "duplication": "UV-Recreate",
    "out-of-order": "UV-Recreate",
    "contradiction": "UV-Recreate",
    "commission": "UV-Recreate",
    "value": "UV-Weight"
  },
  "Acquire": {
    "loss": "UV-Abandon",
    "delay": "UV-Delay",
    "duplication": "UV-RepeatAcquire",
    "out-of-order": "UV-RepeatAcquire",
    "contradiction": "UV-RepeatAcquire",
    "commission": "UV-WrongReceiver",
    "value": "UV-Weight, UV-ForeignContext"
  },
  "TryAcquire": {
    "loss": "UV-Abandon",
    "delay": "UV-Delay",
    "duplication": "UV-RepeatTry",
    "out-of-order": "UV-RepeatTry",
    "contradiction": "UV-RepeatTry",
    "commission": "UV-WrongReceiver",
    "value": "UV-Weight"
  },
  "Release": {
    "loss": "UV-Abandon",
    "delay": "UV-Delay",
    "duplication": "UV-RepeatRelease",
    "out-of-order": "UV-RepeatRelease",
    "contradiction": "UV-RepeatRelease",
    "commission": "UV-UnownedRelease",
    "value": "UV-WrongReceiver, UV-Weight"
  },
  "ContextDone": {
    "loss": "UV-ContextFault",
    "delay": "UV-Delay",
    "duplication": "UV-RepeatedDone",
    "out-of-order": "UV-ContextOrder",
    "contradiction": "UV-ContextOrder",
    "commission": "UV-ContextFault",
    "value": "UV-ForeignContext, UV-ContextFault"
  },
  "Grant": {
    "loss": "n/a: grant is an inline close; examples/weighted-semaphore/semaphore/semaphore.go:200 (\"close(w.ready)\").",
    "delay": "n/a: close is inline; receiver scheduling is separate; examples/weighted-semaphore/semaphore/semaphore.go:200 (\"close(w.ready)\").",
    "duplication": "n/a: head is first unlinked under the lock; examples/weighted-semaphore/semaphore/semaphore.go:199 (\"s.waiters.Remove(next)\").",
    "out-of-order": "n/a: the notifier reads the current head; examples/weighted-semaphore/semaphore/semaphore.go:183 (\"if s.size-s.cur < w.n {\").",
    "contradiction": "n/a: notification is called with the mutex held; examples/weighted-semaphore/semaphore/semaphore.go:108 (\"s.notifyWaiters()\").",
    "commission": "n/a: ready is private; examples/weighted-semaphore/semaphore/semaphore.go:95 (\"ready := make(chan struct{})\").",
    "value": "n/a: entry and channel are paired; examples/weighted-semaphore/semaphore/semaphore.go:96 (\"w := waiter{n: n, ready: ready}\")."
  }
}
```

## Classification table

| Event | Source |
|---|---|
| NewWeighted | external |
| Acquire | external |
| TryAcquire | external |
| Release | external |
| ContextDone | internal |
| Grant | internal |
| UV-Abandon | external |
| UV-Delay | external |
| UV-Recreate | external |
| UV-RepeatAcquire | external |
| UV-RepeatTry | external |
| UV-RepeatRelease | external |
| UV-WrongReceiver | external |
| UV-Weight | external |
| UV-ForeignContext | external |
| UV-UnownedRelease | external |
| UV-ContextFault | internal |
| UV-RepeatedDone | internal |
| UV-ContextOrder | internal |
