# Q-13 post-fix investigation (proposal, not a decision)

The initial pilot observed Release(0) waking a stranded zero-weight waiter.
That was the DR-001 head-cancellation defect. The current source now rescans
on head removal even at full capacity. Q-13 remains OPEN pending owner choice.

## Source reasoning

Reviewed evaluation source: examples/weighted-semaphore/semaphore/semaphore.go
SHA-256: 35673ccc70d17df304df62919442aa3cee0ba32193ef7e4a8d1e254a5098b08c

Under valid initialization and the accepted numeric contracts, at mutex-release
boundaries either the queue is empty or its head needs more weight than is free.
A direct acquisition cannot bypass a queued head. Enqueue preserves that
condition. A positive release or grant rollback runs the notifier; so does
removal of the head, including when free capacity is zero after DR-001. Removing
a non-head leaves the blocked head unchanged. The notifier drains the eligible
prefix until the queue is empty or the next head does not fit.

Consequently, subtracting zero creates no new capacity and finds no eligible
queued head that was left behind. That is a source-level reasoning argument,
not a mechanically verified implementation proof. Internal locking can still
affect scheduling; no timing or extra synchronization guarantee follows.

## Executed bounded model

Commands from the pack root:

```sh
.venv/bin/python docs/evidence/semaphore-pilot/resolution-q02-q04/q13-investigation/explore.py --old-head-guard
.venv/bin/python docs/evidence/semaphore-pilot/resolution-q02-q04/q13-investigation/explore.py
```

The first exits 1, the second 0. Retained output:

- old-guard-red.txt: 2,516 reachable abstract states, 296 where Release(0)
  changes the queue; the shortest reported trace reproduces the known case.
- fixed-guard.txt: 2,220 reachable abstract states, zero such changes.

Capacities range from 0 to 4 and queue length is bounded at 4 for exploration.
The bound is not an API limit. Weights cover every feasible value for each
capacity. The model explores enqueue, immediate grants, valid release and
queued cancellation. Granted-call rollback has the same aggregate effect as
release. Failed tries and rejected invalid/oversized inputs are state no-ops.

This is a manually translated aggregate/queue model, not execution of Go or a
full model of request identity, Context methods, scheduler fairness, memory
ordering or every concurrent interleaving. The old-guard variant changes only
the head-cancellation condition in this model, not all upstream semantics.
The existing DR-001 red/green Go tests independently cover the original defect.

## Revised proposed contract

Permit Release(0) as a logical no-op for capacity, queue and grants in valid
reachable states. Do not advertise it as a wakeup, flush, repair or synchronization
operation. Progress must follow from the actual enabling event as in DR-001.
Retain the internal notification call unless a separately tested optimization
justifies changing it. No runtime change or Q-13 acceptance is claimed here.
