# Current evaluation scope and abstraction

One Weighted instance: constructor, Acquire, TryAcquire, Release, supplied Context.Done/Err, and private grant notification. External protected work, worker lifetime and other instances are outside the boundary. All semantics come from DR-001..013; this is not an upstream Go decision.

## Reachable combinations

The matrix projects the instance at mutex-release boundaries to queue empty versus blocked head. Capacity has symbolic substates cur=0, 0<cur<size, cur=size with 0<=size<=MaxInt64; size=0 collapses empty/full. G-10 discharges the arithmetic and queue-boundary obligations. Guards retain these data distinctions. No terminal state exists because valid public calls remain available.

Per invocation, before queueing ready/element are absent. A queued request has a linked element and an open ready channel. A notification reserves its weight, detaches its element and closes ready under the mutex. A detached recipient may still be pending before success or cancellation rollback. On cancellation without a grant, the detached element can remain in the local frame with ready open until return. Done can be open or closed at each checkpoint; nil Done is valid and never becomes ready. The select may choose either ready input, so G-11 is explicitly not formalizable as a static exclusive guard. No caller-identity registry or end-of-life tombstone exists.

These invocation substates are handled by guarded notes and scheduled scenarios; the two-state diagram is not a claim that they are identical. `TryAcquire(0)` projects queue emptiness without charging capacity under the valid numeric contract. The old eligible-but-retained head is no longer reachable: first enqueue is unfit, append/non-head removal retain the head, and every head-enabling action drains the eligible prefix. The old oversized off-queue wait and negative corrupted counter were eliminated by DR-002..004.

## Callee contracts

NAT-Context requires a non-nil conforming Context. The retained callee contract in docs/evidence/semaphore-pilot/analysis/contracts-complete.md documents stable Done (nil allowed), concurrent-safe methods, cancellation errors and idempotent CancelFunc. Only its Context/Mutex/List language sections apply; its old semaphore comments are historical. Local runtime source was read for these guarantees; no propagation was inferred from a call site. Faulty custom callbacks are outside DR-009 guarantees, not silently accepted behavior.

The caller owns matching release obligations (NAT-Usage); the semaphore guarantees aggregate accounting, not ownership or intended receiver detection. Tests may inspect queue membership to establish a schedule, but verdicts use only returns, public capacity and public progress. Scheduling hooks live in disposable overlays and do not write component state.

## Coverage limits

Every one of the 38 matrix cells has a coverage entry. 34 have an executable representative guarded scenario; four are explicit untestable-via-seam limits: two faulty-Context outcomes and two absent latency bounds. They are not reported as passed tests. Boundary and race tests remain mandatory to cover guarded alternatives; a primary cell disposition alone does not enumerate those alternatives. Historical blind Part B is retained unchanged and is not presented as a new prediction of the resolved model.

Observed-in-code anchors: examples/weighted-semaphore/semaphore/semaphore.go:35 ("type Weighted struct {"); examples/weighted-semaphore/semaphore/semaphore.go:97 ("elem := s.waiters.PushBack(w)"); examples/weighted-semaphore/semaphore/semaphore.go:113 ("if isFront {"); examples/weighted-semaphore/semaphore/semaphore.go:200 ("close(w.ready)"); examples/weighted-semaphore/semaphore/semaphore.go:89 ("if n > s.size {").
