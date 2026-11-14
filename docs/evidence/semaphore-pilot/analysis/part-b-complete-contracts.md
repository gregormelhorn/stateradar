| id | Situation | Disposition | Behaviour |
|---|---|---|---|
| NewWeighted | Valid capacity, first construction of an instance | `handle` | Creates a new Weighted with the given maximum combined weight; the instance starts with full capacity available and no waiters. |
| NewWeighted | Capacity is zero or negative | `reject` | Declared contract gives no meaning to a maximum combined weight that cannot admit any positive request; refuse construction (error/panic per declared refusal signal) rather than create an unusable instance. `UNSPECIFIED` which signal the API declares; requirement text only says "given maximum combined weight", implying a valid bound. |
| NewWeighted | Capacity is extremely large (overflow-prone aggregate) | `reject` | `as-is:` no validation at this boundary; requirement expects a usable bound. Treat as caller error; refuse rather than silently wrap the aggregate counter. |
| NewWeighted | Concurrent constructors / restart mid-operation using a fresh instance (UV-Recreate) | `handle` | Each construction yields an independent instance with its own capacity and queue; the old instance's pending acquisitions and held weight are unaffected and not migrated. A caller that abandons the old instance loses its bookkeeping (UV-Abandon on constructor side). |
| Acquire | Capacity available at call time | `handle` | Admits immediately, returns nil, aggregate available weight reduced by n. |
| Acquire | Capacity not available, caller willing to wait | `defer (queued)` | Enqueues a private waiter, blocks until granted or ctx done. |
| Acquire | ctx already done before the request is considered | `reject` | Returns ctx.Err(), semaphore unchanged. |
| Acquire | ctx becomes done while queued | `reject` | Waiter removed from queue, aggregate unchanged, returns ctx.Err(). |
| Acquire | Requested weight exceeds maximum combined weight | `reject` | Can never be satisfied by a conforming instance; refuse with a declared refusal signal instead of blocking forever. `UNSPECIFIED`: contract does not name the error; blocking forever contradicts "blocking until resources are available". |
| Acquire | Requested weight zero or negative (UV-Weight) | `reject` | No meaningful bound is expressed; refuse (error/diagnostic) and leave semaphore unchanged. |
| Acquire | Receiver is a different Weighted than the one intended (UV-WrongReceiver, commission) | `UNSPECIFIED` | The API cannot distinguish intended from unintended receiver; behaviour is that of the receiving instance (admit/queue/reject on its own capacity). Flag as caller-discipline error; no cross-instance detection is required or possible. |
| Acquire | Caller abandons a pending Acquire without cancelling (UV-Abandon) | `reject` | Not a semaphore invocation; the queued request remains pending indefinitely and holds its place. Requirements give no timeout, so nothing is reclaimed. |
| Acquire | Caller departs after success without releasing (UV-Abandon, omitted release) | `UNSPECIFIED` | Weight stays held; no ownership ledger exists to reclaim it. Documented consequence of caller misbehaviour. |
| Acquire | Caller-supplied Context intended for a different request or lifetime (UV-ForeignContext) | `UNSPECIFIED` | The semaphore honours whatever Done/Err that context reports; it cannot detect foreignness. Cancellation of the foreign context will fail this acquisition per DOC-7, which is correct for the context supplied. |
| Acquire | Second Acquire by same logical caller while first pending (UV-RepeatAcquire) | `defer (queued)` | Treated as an independent request; queued separately and may be granted independently. No duplicate suppression — the API has no caller identity. |
| Acquire | Second Acquire by same logical caller while its weight is still held (UV-RepeatAcquire) | `handle` | Treated as an independent request against remaining capacity; admit or queue accordingly. |
| Acquire | Repeated Acquire that would deadlock (same caller holding weight, blocking for more) | `UNSPECIFIED` | No deadlock detection in requirements; documented caller hazard. |
| Acquire | Delayed request past a caller deadline (UV-Delay) | `reject` | If the deadline has passed, returns ctx.Err() and semaphore unchanged. Delay itself is caller-visible blocking, not a semaphore state. |
| TryAcquire | Capacity available | `handle` | Admits synchronously, returns true, aggregate reduced by n. |
| TryAcquire | Capacity not available | `reject` | Returns false, semaphore unchanged (declared refusal: false with unchanged state). |
| TryAcquire | Weight exceeds maximum combined weight | `reject` | Returns false, semaphore unchanged. |
| TryAcquire | Weight zero or negative (UV-Weight) | `reject` | Returns false, semaphore unchanged. |
| TryAcquire | Wrong receiver instance (UV-WrongReceiver) | `UNSPECIFIED` | Evaluated against the receiving instance's capacity only; foreignness undetectable. |
| TryAcquire | Second TryAcquire by same logical caller (UV-RepeatTry) | `handle` | Independent request; may admit further weight or return false. No duplicate suppression. |
| TryAcquire | Competing try by same logical caller while one is in flight | `handle` | Each is evaluated atomically against capacity; both may succeed if capacity permits. No contradiction detected. |
| TryAcquire | Delayed try past caller deadline (UV-Delay) | `reject` | TryAcquire takes no Context; the caller's own deadline is not observable, so the call still evaluates capacity. Report as caller bookkeeping; semaphore outcome per capacity. |
| TryAcquire | Caller abandons before observing the boolean (UV-Abandon) | `UNSPECIFIED` | If admitted, weight is held with no owner record; consequence is the omitted-release case below. |
| Release | Matching held weight, capacity can satisfy front waiters | `handle` | Returns weight to the aggregate and grants queued waiters in order up to capacity. |
| Release | Matching held weight, no waiters fit | `handle` | Returns weight to the aggregate; no grant occurs. |
| Release | Weight larger than any possible held amount / no matching ownership (UV-UnownedRelease) | `reject` | Declared refusal: release without matching ownership is a caller/API contract violation; refuse (diagnostic/panic) rather than silently inflate capacity. Requirements say only "releases the semaphore with a weight of n", presupposing ownership. |
| Release | Duplicate release of the same weight (UV-RepeatRelease) | `reject` | Once the first release has returned the weight, the second has no matching ownership; refuse as unowned, and do not increase capacity beyond the maximum combined weight. |
| Release | Early release before the corresponding Acquire succeeded | `reject` | Same unowned case; do not credit weight the caller never held. |
| Release | Simultaneous releases of the same held weight from two goroutines (UV-RepeatRelease, contradiction) | `reject` | Exactly one can be the matching release; the other is unowned and refused. Requires the accounting to be atomic under the instance lock. |
| Release | Weight zero or negative (UV-Weight) | `reject` | Nonsensical release; refuse and leave aggregate unchanged. |
| Release | Wrong receiver instance (UV-WrongReceiver) | `UNSPECIFIED` | Applied to the receiving instance's ledger; cross-instance ownership cannot be checked because no ownership ledger is required. Release against the wrong instance is an unowned release there and must not exceed that instance's maximum. |
| Release | Delayed release long after success (UV-Delay) | `handle` | Still a valid release of held weight; grant waiters at that later moment. No staleness expiry in requirements. |
| ContextDone | Cancellation observed while request is queued | `handle` | Waiter is removed and the blocked Acquire returns ctx.Err(); semaphore unchanged for that request (DOC-7). |
| ContextDone | Cancellation observed after grant has already happened | `ignore (documented)` | Acquisition already succeeded (nil); the granted weight remains held and must be released normally. A cancelled context after success does not undo the grant. |
| ContextDone | Cancellation observed before the request begins | `reject` | Acquire returns ctx.Err() without enqueueing; semaphore unchanged. |
| ContextDone | Repeated cancellation of a standard context (UV-RepeatedDone) | `ignore (documented)` | Idempotent: subsequent cancels do nothing; only the first transition matters. |
| ContextDone | Done and Err inconsistent (Err nil while Done closed) (UV-ContextFault) | `UNSPECIFIED` | Contract forbids this; behaviour is undefined. Should be treated as caller-supplied contract violation; record as open point, do not invent a recovery. |
| ContextDone | Custom context whose Done/Err blocks, panics or reenters (UV-ContextFault) | `UNSPECIFIED` | No adapter exists; contract violation. Requirement-based expectation: the semaphore must not hold its instance lock while calling user context methods (per lock-discipline annotation), so reentrancy does not corrupt state, but panics propagate to the caller. |
| ContextDone | Nil context interface (UV-ContextFault) | `reject` | Nil Context cannot be consulted; refuse (panic is the Go-idiomatic declared refusal) rather than dereference. |
| ContextDone | Premature signal (Done closed before any work) (UV-ContextFault) | `reject` | Same as pre-call cancellation: Acquire returns ctx.Err(), semaphore unchanged. |
| ContextDone | Foreign context, i.e. intended for a different request/lifetime (UV-ForeignContext) | `UNSPECIFIED` | Cannot be distinguished; cancellation fails whichever request supplied it. |
| ContextDone | Done arriving concurrently with mutex acquisition, enqueue, grant or return (UV-ContextOrder) | `handle` | Must be linearised: the request either is admitted (returns nil, weight held) or is not (returns ctx.Err(), no weight held). No state where weight is charged and the call also reports cancellation, and none where the call returns nil without charging. |
| Grant | Head waiter fits within currently available weight | `handle` | Internal: head waiter is admitted, its private notification closed once, and it becomes the holder of that weight. |
| Grant | Head waiter does not fit, or queue empty | `ignore (documented)` | No grant occurs; no notification is sent. |
| Grant | Notification delivered while the waiter is also being cancelled (UV-ContextOrder) | `handle` | Grant and cancellation must be resolved at a single point under the instance lock: exactly one of grant or cancel wins. If grant wins, weight is held and the caller sees success; if cancel wins, weight is not charged and the waiter is unlinked. |
| UV-Abandon | Queued request whose caller departed, never cancelled | `UNSPECIFIED` | Request stays pending forever and consumes queue position but no weight. Requirements prescribe no reclamation. |
| UV-Abandon | Holder departs after success without releasing | `UNSPECIFIED` | Weight permanently lost; capacity effectively reduced. Documented caller misuse; no ownership recovery. |
| UV-Abandon | Constructor caller abandons a freshly created instance mid-operation | `handle` | Old instance and its state become garbage once unreferenced; new instance is independent. |
| UV-Delay | Cancellation arrives after the grant already succeeded | `ignore (documented)` | Success stands; later release required. |
| UV-Delay | Release arrives long after success | `handle` | Valid release; grants waiters then. |
| UV-Delay | Request arrives after its caller's deadline has already passed, with a live cancelled context | `reject` | Returns ctx.Err(), semaphore unchanged. |
| UV-Delay | Request arrives after deadline, with a context that is not yet observably cancelled | `defer (queued)` | The semaphore has no deadline clock of its own; it queues and blocks until the context reports done. |
| UV-Recreate | Concurrent constructors | `handle` | Independent instances, independent capacities; no sharing or coordination. |
| UV-Recreate | Restart mid-operation with a fresh instance | `handle` | New instance starts at full capacity; in-flight requests on the old instance are unaffected and their releases go to the old instance (a release aimed at the new one is unowned there). |
| UV-Recreate | Caller mixes instances (new instance used for release of old weight) | `reject` | Unowned on the new instance; refuse rather than inflate its capacity beyond maximum. |
| UV-RepeatAcquire | Second Acquire while first is pending, capacity eventually available | `defer (queued)` | Both are queued and may both be granted, each costing weight. No dedup. |
| UV-RepeatAcquire | Second Acquire while first is pending, and total weight at most capacity | `defer (queued)` | Queued behind the first in arrival order; may be granted after it. |
| UV-RepeatAcquire | Second Acquire while first succeeds, needing weight already held by the same caller | `defer (queued)` | Blocks; if unsatisfiable it only returns on cancellation. Documented self-deadlock hazard. |
| UV-RepeatAcquire | Second Acquire after first was cancelled | `handle` | Independent new request; admit or queue per capacity. |
| UV-RepeatTry | Second TryAcquire when capacity remains | `handle` | May succeed; both weights held and both must be released. |
| UV-RepeatTry | Second TryAcquire when capacity exhausted by the first | `reject` | Returns false, semaphore unchanged. |
| UV-RepeatTry | TryAcquire competing concurrently with the same caller's Acquire | `handle` | Try is evaluated atomically: admitted if capacity fits at that instant, else false. No interference with the pending Acquire's reservation. |
| UV-RepeatRelease | Duplicate release of already-released weight | `reject` | Unowned; refused; capacity not inflated. |
| UV-RepeatRelease | Stale release from a previous instance generation | `reject` | Unowned on the current instance; refused. |
| UV-RepeatRelease | Simultaneous identical releases | `reject` | One matches; the other refused; aggregate never exceeds maximum. |
| UV-RepeatRelease | Early release before acquire completed | `reject` | Unowned; refused. |
| UV-WrongReceiver | Acquire/TryAcquire aimed at an unintended Weighted instance | `UNSPECIFIED` | Acts on the receiving instance only; cross-instance detection impossible. Caller error. |
| UV-WrongReceiver | Release aimed at an unintended Weighted instance that happens to have free aggregate headroom | `reject` | Still unowned on that instance; must be refused even if the aggregate would not exceed maximum, since ownership cannot be verified. |
| UV-Weight | Zero weight request | `reject` | No bound expressed; refuse and leave state unchanged. |
| UV-Weight | Negative weight request | `reject` | Would increase available weight; refuse. |
| UV-Weight | Weight greater than maximum combined weight | `reject` | Unsatisfiable; refuse rather than block forever. |
| UV-Weight | Extreme signed weight / overflow-inducing aggregate addition | `reject` | Refuse; do not let the aggregate arithmetic wrap. |
| UV-Weight | Valid but unintended weight | `handle` | Honoured as requested; the API has no notion of intent. Caller-visible consequence. |
| UV-Weight | Zero/negative capacity at construction | `reject` | Instance would be unusable; refuse construction. |
| UV-ForeignContext | Context of a different request passed to Acquire | `UNSPECIFIED` | Honoured as given: cancellation of that context fails this request. Cannot be detected. |
| UV-ForeignContext | Context already cancelled at hand-off | `reject` | Returns its Err; semaphore unchanged. |
| UV-ForeignContext | Context whose lifetime exceeds the request's | `ignore (documented)` | No effect: an uncancelled context simply means the Acquire blocks until capacity. |
| UV-UnownedRelease | Release with no matching ownership when instance has waiters | `reject` | Refused; waiters must not be granted on weight nobody holds; capacity unchanged. |
| UV-UnownedRelease | Release with no matching ownership when instance is at maximum | `reject` | Refused; must never push aggregate above maximum combined weight. |
| UV-UnownedRelease | Release of aggregate weight by a goroutine that never acquired | `reject` | Same unowned case; refuse with declared signal. |
| UV-ContextFault | Nil Context interface | `reject` | Refuse (declared panic) rather than dereference. |
| UV-ContextFault | Custom Done that blocks | `UNSPECIFIED` | Caller contract violation; expectation is that no instance lock is held across the call so state is not corrupted, but the caller's goroutine stalls. |
| UV-ContextFault | Custom Done/Err that reenters the semaphore | `handle` | Must not deadlock: context methods are consulted outside the instance lock, so reentrant Acquire/Release/TryAcquire proceed. |
| UV-ContextFault | Custom Err that panics | `UNSPECIFIED` | Panic propagates to the caller; requirement gives no recovery. Must not leave partially-mutated accounting for a failed request. |
| UV-ContextFault | Inconsistent Done/Err (Err nil after Done closed) | `UNSPECIFIED` | Contract violation; no specified outcome. Open point. |
| UV-ContextFault | Premature Done signal | `reject` | Acquire returns Err, semaphore unchanged. |
| UV-RepeatedDone | Second and later cancellation of a standard context | `ignore (documented)` | Idempotent; only the first closure matters. |
| UV-RepeatedDone | Repeated closes racing with a queued Acquire's wakeup | `handle` | Waiter is removed once; subsequent closures ignored. No double-unlink, no double-charge. |
| UV-ContextOrder | Done after mutex acquisition but before enqueue | `reject` | Request must not be enqueued or charged; Acquire returns ctx.Err(), semaphore unchanged. |
| UV-ContextOrder | Done during enqueue | `handle` | Linearised: either enqueued then immediately cancelled and unlinked (returns Err, unchanged), or observed cancelled first and never enqueued. Never both enqueued and returned as successful. |
| UV-ContextOrder | Done at the same moment as grant | `handle` | Exactly one wins under the lock: grant ⇒ returns nil and weight held; cancel ⇒ returns Err, weight not held and any tentative charge rolled back. |
| UV-ContextOrder | Done during the return path after grant | `ignore (documented)` | Success is already committed; the caller must release the acquired weight. |
| UV-ContextOrder | Done during the return path after cancellation | `ignore (documented)` | Already returning Err; nothing further. |
| UV-ContextOrder | Done while TryAcquire is evaluating capacity | `ignore (documented)` | TryAcquire consults no context; its boolean outcome is per capacity and the caller must reconcile with the cancellation. |
| P-01a | Acquire → Release by the same requester after success (same instance) | `handle` | Success returns nil and charges weight; the later Release returns the weight and may grant waiters. Normal cycle. |
| P-01b | Release → Acquire by the same actor (release of earlier held weight, then a new request) | `handle` | Release credits the aggregate (possibly granting waiters first); the subsequent Acquire sees the reduced-by-release capacity and admits or queues accordingly. An unmatched Release first is `reject` as unowned. |
| P-01b | Release first with no prior ownership, then Acquire | `reject` | The Release is unowned and refused; the Acquire then proceeds on unchanged capacity. |
| P-02a | TryAcquire → Release | `handle` | Successful Try charges weight; the matching Release returns it. If Try returned false, the subsequent Release is unowned and `reject`. |
| P-02b | Release → TryAcquire | `handle` | Release credits capacity; the following TryAcquire is evaluated against post-release capacity and may now return true. If the Release was unowned it is refused and the Try sees unchanged capacity. |
| P-03a | Acquire issued → ContextDone on the same request while queued | `reject` | The queued request is cancelled: unlinked, no weight charged, Acquire returns ctx.Err() (DOC-7). |
| P-03a | Acquire issued → ContextDone after success | `ignore (documented)` | Cancellation is a no-op on a completed acquisition; weight stays held until Release. |
| P-03b | ContextDone (context pre-cancelled) → Acquire | `reject` | Acquire returns ctx.Err() without enqueueing; semaphore unchanged. |
| P-03b | ContextDone → Acquire where cancellation was of an unrelated earlier request | `handle` | The new Acquire is independent; it treats the context as already done and thus `reject`s per DOC-7. If a different fresh context is supplied, admit/queue per capacity. |
| P-04a | ContextDone at handoff, then Release (cancellation wins the handoff) | `reject` | The waiting request is cancelled and no weight is charged; the holder's Release grants the next eligible waiter or simply credits the aggregate. |
| P-04a | ContextDone at handoff, then Release (grant already won) | `handle` | Cancellation is ignored for the already-granted request; the Release is that request's legitimate Release. |
| P-04b | Release at handoff, then ContextDone | `handle` | Release may grant the waiter; the subsequent cancellation must be ignored for the granted request (success stands, weight held and to be released), or must cancel it if grant had not yet occurred, leaving the weight for the next waiter. |
| P-04b | Release first, then ContextDone for a request that was not granted | `reject` | The still-queued request is cancelled, unlinked, unchanged; the released weight goes to the next eligible waiter. |
| P-05a | UV-RepeatAcquire (second request pending) → Release by the holder | `defer (queued)` | The release credits weight; the second request remains queued unless capacity now fits, in which case it is granted. The first request's weight is only returned by its own Release. |
| P-05a | UV-RepeatAcquire → Release where the release is the first request's completion after the second is pending | `handle` | The pending second request is then evaluated against restored capacity and may be granted. |
| P-05b | Release → UV-RepeatAcquire | `defer (queued)` | The release restores capacity; the subsequent repeated Acquire is admitted if it fits, otherwise queued. |
| P-05b | Release (unowned) → UV-RepeatAcquire | `reject` | The release is refused; the repeated Acquire is evaluated against unchanged capacity — admit or queue. |
| P-06a | UV-RepeatAcquire pending → ContextDone on the first request's context | `ignore (documented)` | Cancelling the first request's context does not affect the second request, which has its own request/context. The first request, if still queued, is cancelled and its wait discarded. |
| P-06a | UV-RepeatAcquire pending → ContextDone on the first request's context where the second used the same context | `reject` | Both are cancelled by the shared context: each is unlinked and returns ctx.Err(); semaphore unchanged. |
| P-06b | ContextDone on the first request's context → UV-RepeatAcquire | `reject` | If the repeated Acquire supplies the same (already done) context, it returns ctx.Err() immediately. If it supplies a fresh context, it is admitted or queued per capacity (`handle`). |
| P-07a | UV-ContextOrder (cancellation contending with an in-flight handoff) → Release | `handle` | Whichever won the handoff stands: if grant won, the Release is the legitimate one for that weight; if cancel won, the Release is issued by the failed request and is unowned and therefore `reject`. |
| P-07a | UV-ContextOrder resolved as cancellation → Release | `reject` | The cancelled request holds no weight; its Release is unowned and refused; capacity unchanged. |
| P-07b | Release → UV-ContextOrder (cancellation arriving at an in-flight handoff) | `handle` | The Release may have granted the waiter; the racing cancellation then must be ignored for a granted waiter (success) or must cancel it if grant had not yet been committed, rolling back any tentative charge. Exactly one outcome. |
| P-08a | UV-UnownedRelease → Acquire | `reject` | The unowned Release is refused and does not increase capacity; the subsequent Acquire is evaluated against the true capacity (admit or queue). Must never appear to succeed because of phantom weight. |
| P-08a | UV-UnownedRelease → Acquire where the release would have fit within headroom | `reject` | Still refused: ownership is not established merely by having headroom. Acquire then proceeds on true capacity. |
| P-08b | Acquire → UV-UnownedRelease | `handle` | The Acquire is handled normally (admit/queue/cancel per capacity); the subsequent unowned Release is `reject`ed and leaves capacity untouched. If the Acquire succeeded and the Release happens to be the matching one, it is `handle` instead. |
| P-08b | Acquire failed/queued → UV-UnownedRelease | `reject` | The failed request never held weight, so the following Release is unowned and refused; aggregate unchanged. |

- [x] NewWeighted
- [x] Acquire
- [x] TryAcquire
- [x] Release
- [x] ContextDone
- [x] Grant
- [x] UV-Abandon
- [x] UV-Delay
- [x] UV-Recreate
- [x] UV-RepeatAcquire
- [x] UV-RepeatTry
- [x] UV-RepeatRelease
- [x] UV-WrongReceiver
- [x] UV-Weight
- [x] UV-ForeignContext
- [x] UV-UnownedRelease
- [x] UV-ContextFault
- [x] UV-RepeatedDone
- [x] UV-ContextOrder
- [x] P-01a
- [x] P-01b
- [x] P-02a
- [x] P-02b
- [x] P-03a
- [x] P-03b
- [x] P-04a
- [x] P-04b
- [x] P-05a
- [x] P-05b
- [x] P-06a
- [x] P-06b
- [x] P-07a
- [x] P-07b
- [x] P-08a
- [x] P-08b