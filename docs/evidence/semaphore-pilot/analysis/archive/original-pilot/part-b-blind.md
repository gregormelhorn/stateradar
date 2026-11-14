| id | Situation | Disposition | Expected behaviour |
|---|---|---|---|
| NewWeighted | Valid capacity, fresh instance | `handle` | Creates a distinct Weighted instance with the given maximum combined weight; concurrent requests against it are bounded by that capacity. |
| NewWeighted | Capacity zero or negative | `UNSPECIFIED` | Requirements name no validation of capacity; contract only says "given maximum combined weight". Refusal semantics are not declared. |
| NewWeighted | Extreme/large capacity (UV-Weight) | `UNSPECIFIED` | No documented bound or overflow contract for capacity. |
| NewWeighted | Same caller constructs two instances (UV-Recreate) | `handle` | Two independent instances exist; each bounds its own concurrent access. They share no capacity or queue. |
| NewWeighted | Restart mid-operation using a fresh instance (UV-Recreate) | `reject` | New instance is separate; pending requests/releases on the old instance do not apply to it. Caller's stale holder/releaser against the old instance is a misrouted act; there is no cross-instance accounting. |
| Acquire | Resources available, weight ≤ capacity | `handle` | Admits immediately, returns nil, semaphore unchanged in the sense that accounted capacity is consumed by n until Release. |
| Acquire | Resources unavailable, ctx not done | `defer (queued)` | Blocks; caller remains queued until capacity is available or ctx is done. |
| Acquire | ctx done while queued | `reject` | Returns ctx.Err(); leaves the semaphore unchanged (no capacity consumed, no queue entry retained). |
| Acquire | First request still pending, same logical caller requests again (UV-RepeatAcquire) | `defer (queued)` | Two independent queued requests; each governed by its own ctx. No caller-identity de-duplication exists in requirements. |
| Acquire | First request already succeeded, same logical caller requests again while weight held (UV-RepeatAcquire) | `defer (queued)` or `handle` | Treated as a new independent request; admits if aggregate capacity allows, otherwise queues. No double-count avoidance on behalf of the caller. |
| Acquire | Caller departs without cancel/release (UV-Abandon) | `defer (queued)` | The queued request remains until its ctx is done or capacity arrives; mere caller departure does not remove the entry (no time-based retention policy). |
| Acquire | Caller cancels late, past its own deadline (UV-Delay) | `reject` | If ctx already done on entry, returns ctx.Err() without admitting. |
| Acquire | Weight zero | `handle` | Vacuous admission: no capacity consumed; returns nil without blocking (zero weight is comparable to "no resources requested"). |
| Acquire | Negative weight (UV-Weight) | `UNSPECIFIED` | Requirements state no declared refusal for negative n; behaviour is not specified by contract text. |
| Acquire | Oversized/extreme weight > capacity (UV-Weight) | `defer (queued)` | Admits only if capacity can ever satisfy it; otherwise blocks forever unless ctx is done. No size refusal declared. |
| Acquire | Context intended for a different request (UV-ForeignContext) | `handle` | Context is not bound to a request identity; whatever Done channel it exposes is honoured for this call. |
| Acquire | Nil Context interface (UV-ContextFault) | `UNSPECIFIED` | Contract does not declare nil-context refusal; the Go Context interface typically forbids nil. |
| Acquire | Custom context method blocks/panics/reenters (UV-ContextFault) | `UNSPECIFIED` | No adapter or guard is required by the boundary; behaviour depends on caller-supplied implementation. |
| Acquire | Context Done overlaps enqueue/handoff (UV-ContextOrder) | `reject` | If cancellation is observed before admission, returns ctx.Err() and leaves semaphore unchanged; if admission already occurred, cancellation after admission is delivered by a later Release path, not by Acquire. |
| TryAcquire | Resources available, weight ≤ capacity | `handle` | Admits synchronously, returns true. |
| TryAcquire | Resources unavailable | `handle` | Returns false; leaves semaphore unchanged. |
| TryAcquire | Second or competing try by same logical caller (UV-RepeatTry) | `handle` | Each try is independent; admits if capacity allows, else returns false. No caller-identity arbitration. |
| TryAcquire | Weight zero | `handle` | Returns true without consuming capacity. |
| TryAcquire | Negative weight (UV-Weight) | `UNSPECIFIED` | No declared refusal. |
| TryAcquire | Oversized weight > capacity (UV-Weight) | `handle` | Returns false; semaphore unchanged. |
| TryAcquire | Caller omitted the call then Hold? (UV-Abandon) | `handle` | No pending state exists to abandon; nothing to reclaim. |
| TryAcquire | Delayed try relative to caller deadline (UV-Delay) | `handle` | TryAcquire has no ctx; deadline is caller-side only. |
| Release | Matching held weight | `handle` | Returns weight to available capacity; queued acquirers may be granted. |
| Release | Duplicate release (UV-RepeatRelease) | `UNSPECIFIED` | No ownership ledger exists; aggregate counter decreases regardless. Contract does not declare a refusal signal. |
| Release | Stale/early release before any acquire (UV-UnownedRelease) | `UNSPECIFIED` | No ownership record; aggregate accounting decrements without matching ownership. No declared refusal. |
| Release | Simultaneous duplicate release (UV-RepeatRelease) | `UNSPECIFIED` | Same as duplicate; only mutex serialises, no rejection. |
| Release | Release weight exceeds outstanding (UV-UnownedRelease) | `UNSPECIFIED` | No declared clamp or error. |
| Release | Weight zero | `handle` | No-op on the counter. |
| Release | Negative weight (UV-Weight) | `UNSPECIFIED` | No declared refusal. |
| Release | Well-typed receiver for another instance (UV-WrongReceiver) | `reject` | Release applies only to the instance it is called on; a release on a different instance is a misrouted act against that instance's accounting. Requirements do not declare conversion between instances. |
| Release | Delayed past holder's own deadline (UV-Delay) | `handle` | Release has no ctx; it applies whenever called. |
| Release | Holder omits release after success (UV-Abandon) | `UNSPECIFIED` | No automatic reclamation; capacity remains consumed indefinitely. Contract does not declare timeouts. |
| ContextDone | Cancellation before admission | `reject` | Pending Acquire returns ctx.Err(); semaphore unchanged. |
| ContextDone | Cancellation after admission (request already granted) | `handle` | Cancellation is observed but admission stands; the caller still must Release the acquired weight. |
| ContextDone | Repeated cancellation on standard context (UV-RepeatedDone) | `ignore (documented)` | Go Context guarantees Done closes once; repeated triggers do not re-fire. |
| ContextDone | Done while enqueue/grant/return overlaps (UV-ContextOrder) | `reject` | Cancellation observed before the queued branch commits removes the entry and returns ctx.Err(); cancellation observed after commit is delivered on the next cancellation check, with admission deciding which side wins atomically under the mutex. |
| ContextDone | Inconsistent Done/Err or premature signal (UV-ContextFault) | `UNSPECIFIED` | Boundary passes through; no adapter normalises. |
| ContextDone | Nil interface (UV-ContextFault) | `UNSPECIFIED` | No guard declared. |
| ContextDone | Custom method blocks/panics/reenters (UV-ContextFault) | `UNSPECIFIED` | Caller-supplied; boundary does not defend. |
| ContextDone | Foreign lifetime context (UV-ForeignContext) | `handle` | Whatever Done the supplied context exposes is honoured for the acquisition it was passed to; no ownership binding. |
| Grant | Head of queue, capacity sufficient | `handle` | Internal: head waiter is signalled (private close) under the mutex; no caller-visible disposition. |
| Grant | Grant after cancellation race (UV-ContextOrder) | `reject` | If the cancelled request's entry was already removed, no grant is issued for it; if grant committed first, the waiter observes admission and must Release. |
| UV-Abandon | Acquirer never calls (no request made) | `ignore (accidental)` | Nothing pending; nothing to reclaim. |
| UV-Abandon | Caller departs while queued with live ctx | `defer (queued)` | Entry remains until ctx done or capacity grants; no time-based eviction. |
| UV-Abandon | Holder omits Release after success | `UNSPECIFIED` | Capacity stays consumed; no automatic reclamation or expiry. |
| UV-Delay | Acquire past deadline (ctx already done) | `reject` | Returns ctx.Err(); semaphore unchanged. |
| UV-Delay | Release past holder deadline | `handle` | Release has no deadline semantics; applies when called. |
| UV-Delay | Cancellation delivered after grant | `handle` | Grant stands; cancellation does not roll back admission. |
| UV-Recreate | Two independent instances created | `handle` | Each bounds its own concurrency; no shared state. |
| UV-Recreate | Restart mid-operation using fresh instance | `reject` | Fresh instance does not inherit pending waiters or held weights; caller must treat old instance as gone. |
| UV-Recreate | Concurrent constructors duplicating intent (UV-Recreate) | `handle` | Duplicate instances are permitted; duplication is a caller-level concern not covered by the contract. |
| UV-RepeatAcquire | Second Acquire while first pending | `defer (queued)` | Independent queued request; no caller-identity de-dup. |
| UV-RepeatAcquire | Second Acquire while weight held | `defer (queued)` or `handle` | Independent request; admits or queues per capacity. |
| UV-RepeatAcquire | Second Acquire after first returned error | `handle` | New request; nothing carries over from the failed first. |
| UV-RepeatTry | Second TryAcquire while first pending/holding | `handle` | Independent; succeeds or fails on current capacity only. |
| UV-RepeatTry | Competing try by same logical caller | `handle` | Independent; no arbitration. |
| UV-RepeatRelease | Duplicate Release | `UNSPECIFIED` | Decrements aggregate again; no declared refusal. |
| UV-RepeatRelease | Stale Release (after previous successful release of same weight) | `UNSPECIFIED` | No ledger; decrements regardless. |
| UV-RepeatRelease | Simultaneous duplicate Release | `UNSPECIFIED` | Serialised by mutex; no rejection. |
| UV-RepeatRelease | Early Release before matching Acquire succeeds | `UNSPECIFIED` | Counts as unowned release; no declared refusal. |
| UV-WrongReceiver | Release on another Weighted instance | `reject` | Applies to the instance called on; no cross-instance conversion. |
| UV-WrongReceiver | TryAcquire on another Weighted instance | `handle` | Applies to the instance called on; no cross-instance accounting. |
| UV-WrongReceiver | Acquire on another Weighted instance | `handle` | Applies to the instance called on; no cross-instance accounting. |
| UV-WrongReceiver | Grant observed by a waiter on another instance | `ignore (accidental)` | Private channels cannot be observed across instances; any spurious delivery is a caller bug, not a component event. |
| UV-Weight | Zero weight Acquire/TryAcquire/Release | `handle` | Vacuous admit (true/nil) and no-op release. |
| UV-Weight | Negative weight any op | `UNSPECIFIED` | No declared refusal. |
| UV-Weight | Oversized weight > capacity Acquire | `defer (queued)` | Blocks until ctx done. |
| UV-Weight | Oversized weight > capacity TryAcquire | `handle` | Returns false; unchanged. |
| UV-Weight | Extreme signed capacity in NewWeighted | `UNSPECIFIED` | No declared bound. |
| UV-Weight | Valid-but-unintended weight (caller mistake) | `handle` | Contract enforces no policy beyond n; caller's intent untracked. |
| UV-ForeignContext | Context from another request passed to Acquire | `handle` | Whatever Done it exposes is honoured; no ownership binding. |
| UV-ForeignContext | Context from another request passed to ContextDone path | `handle` | Same pass-through semantics. |
| UV-ForeignContext | Context whose Err contract is inconsistent | `UNSPECIFIED` | Boundary does not normalise; result depends on implementation. |
| UV-UnownedRelease | Release with no matching ownership | `UNSPECIFIED` | Decrements aggregate; no ledger, no declared refusal. |
| UV-UnownedRelease | Release by non-holder goroutine | `UNSPECIFIED` | No ownership check; same as above. |
| UV-UnownedRelease | Release exceeding outstanding weight | `UNSPECIFIED` | No clamp or error declared. |
| UV-ContextFault | Nil context interface | `UNSPECIFIED` | No declared guard. |
| UV-ContextFault | Custom method panics | `UNSPECIFIED` | Not defended at boundary. |
| UV-ContextFault | Custom method blocks | `UNSPECIFIED` | Boundary inherits the block; no timeout. |
| UV-ContextFault | Custom method reenters semaphore | `UNSPECIFIED` | Not specified; caller-supplied. |
| UV-ContextFault | Premature Done without Err set | `UNSPECIFIED` | Boundary does not validate consistency. |
| UV-ContextFault | Custom context used as foreign lifetime | `handle` | Honoured as supplied. |
| UV-RepeatedDone | Second cancellation on standard context | `ignore (documented)` | Standard context closes Done once; no re-fire. |
| UV-RepeatedDone | Repeated Done with custom context (non-idempotent close) | `UNSPECIFIED` | No defence; caller-supplied. |
| UV-ContextOrder | Done before enqueue | `reject` | Returns ctx.Err(); no entry created. |
| UV-ContextOrder | Done after enqueue, before grant | `reject` | Queued branch removes entry and returns ctx.Err(). |
| UV-ContextOrder | Done concurrent with grant | `reject` or `handle` | Mutex/commit ordering decides: if removal wins, reject with ctx.Err(); if grant wins, admission stands and caller must Release. |
| UV-ContextOrder | Done after grant/return | `handle` | Admission stands; cancellation is a later caller-side condition. |
| P-01a | Acquire then Release on same instance | `handle` | Acquire admits (or queues then admits); subsequent Release returns the weight; semaphore accounting nets out. |
| P-01b | Release then Acquire on same instance | `UNSPECIFIED` | Release precedes any matching Acquire → unowned release; no ledger to reject. A later Acquire is independent and admits per capacity. |
| P-02a | TryAcquire then Release | `handle` | Successful try then matching release balances; unsuccessful try then release is unowned release (`UNSPECIFIED`). |
| P-02b | Release then TryAcquire | `UNSPECIFIED` | Unowned release decrements; TryAcquire then judges on the resulting capacity. |
| P-03a | Acquire then ContextDone (on same acquisition) | `handle` | If admission occurred before cancellation, admission stands; caller must Release. If cancellation arrived before admission, the pending call returns ctx.Err(). |
| P-03b | ContextDone then Acquire | `reject` | Acquire sees ctx already done on entry and returns ctx.Err(); semaphore unchanged. |
| P-04a | ContextDone then Release at handoff | `handle` | If cancellation wins the race, no grant; the Release then belongs to prior holder and is applied normally. If grant already committed, the newly admitted holder must Release; a release by the cancelling actor without admission is an unowned release (`UNSPECIFIED`). |
| P-04b | Release then ContextDone at handoff | `handle` | Release frees capacity and may grant the queued waiter; a subsequent cancellation either arrives too late (grant stands) or cancels a still-queued entry (`reject`). |
| P-05a | UV-RepeatAcquire then Release | `handle` | First or second request may be admitted; Release returns the weight of whichever is holding, decrementing aggregate; the other remains pending (`defer (queued)`). |
| P-05b | Release then UV-RepeatAcquire | `handle` | Release frees capacity; subsequent repeat request admits or queues per resulting capacity, independently of the first. |
| P-06a | UV-RepeatAcquire then ContextDone | `reject` | ContextDone cancels only the request bound to that context; the other request (different or same caller) is unaffected and remains pending/admitted. |
| P-06b | ContextDone then UV-RepeatAcquire | `handle` | First request resolves via ctx.Err(); the repeat Acquire is a new independent request and admits or queues per capacity. |
| P-07a | UV-ContextOrder then Release | `reject` or `handle` | If cancellation removes the queued entry, subsequent Release has no matching grantee; if grant committed, Release matches the admitted holder and balances. |
| P-07b | Release then UV-ContextOrder | `handle` | Release frees capacity and may grant; cancellation overlapping the handoff either loses the race (grant stands, holder must Release) or cancels a still-queued entry with ctx.Err(). |
| P-08a | UV-UnownedRelease then Acquire | `UNSPECIFIED` | Unowned release decrements aggregate; subsequent Acquire judges capacity against the drifted counter. No refusal signal for the unowned release. |
| P-08b | Acquire then UV-UnownedRelease | `UNSPECIFIED` | Acquire consumes n per capacity; a subsequent unowned release decrements aggregate again with no ledger check, so capacity drift is unbounded by contract. |

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