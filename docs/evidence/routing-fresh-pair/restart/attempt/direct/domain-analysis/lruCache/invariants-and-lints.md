# Invariants and lint findings

## NAT context
- NAT-01: a published Cache has successful construction, is not copied once used, and the caller uses a reflexive, dynamically hashable key for normal cells. RWMutex no-copy contract and simplelru/lru.go:25 ("if size <= 0 {"), simplelru/lru.go:52 ("if ent, ok := c.items[key]; ok {"), internal/list.go:62 ("func (l *LruList[K, V]) Length() int { return l.len }"). 0 ≤ n, normal positive n ≤ cap, and a realizable n+1 fits Go int. UV-01/08/09 deliberately violate receiver or key assumptions; negative resizing is retained as reachable state.
- NAT-02: ordinary callback work originates only through internal removal, carries a copied Go value, and may not return. No ordering, timeout or reentrancy assumption on callback bodies; lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)"), lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)").
- NAT-SYS: no shared-service synchronization modeled: independent map/list per instance (simplelru/lru.go:31 ("evictList: internal.NewList[K, V](),"), simplelru/lru.go:32 ("items:     make(map[K]*internal.Entry[K, V]),")); any shared application resource in callback lies outside the cache.

## SYS checks
| Predicate | Uninitialized | Empty | BelowCapacity | AtCapacity | Disabled | NegativeCapacity |
|---|---|---|---|---|---|---|
| SYS-01: successful positive-size receiver has 0 ≤ Len ≤ Cap after a mutation | precondition false | holds (n=0) | holds; insertion reaches limit | holds normal key; insert evicts one | zero-length observed | negative violates literal n ≤ cap even empty; overflow can keep old entries (Q-02) |
| SYS-02: concurrent public operation observes/writes shared state with no data race | invalid receiver outside normal scope | Cap/Resize violation | same | same | same | same |
| SYS-03: live ring reflects recency; hits/insertions touch only as specified, victims oldest, snapshots oldest first | not initialized | empty misses | holds normal keys | holds normal keys, full miss evicts oldest | new item immediately evicts itself | one removal per miss; retained entries can still be touched after wrap |
| SYS-04: eviction return counts actual removals; registered notification uses removed payload | no valid removal | normal none | normal shrink/removal holds | normal eviction/shrink holds | immediate self-eviction reports true | ordinary negative Resize count can exceed removals; NaN can generate repeated purge notification; callback abort can skip notifications |
| SYS-05: Len projects logical entries and Purge drops all cache entries | not initialized | list count 0; NaN map orphan may survive | count holds for normal keys | count holds for normal keys, NaN breaks list/map agreement | count 0; same orphan risk | ring count remains accurate; retained entries or map orphan possible |

Evidence: SYS-01 simplelru/lru.go:62 ("evict := c.evictList.Length() > c.size"), simplelru/lru.go:164 ("c.size = size"); SYS-02 lru.go:188 ("c.lock.Lock()"), lru.go:194 ("c.lock.Unlock()"), lru.go:254 ("return c.lru.Cap()"), simplelru/lru.go:152 ("return c.size"), simplelru/lru.go:164 ("c.size = size"); SYS-03 simplelru/lru.go:53 ("c.evictList.MoveToFront(ent)"), simplelru/lru.go:65 ("c.removeOldest()"), simplelru/lru.go:73 ("c.evictList.MoveToFront(ent)"), simplelru/lru.go:127 ("for ent := c.evictList.Back(); ent != nil; ent = ent.PrevEntry() {"), simplelru/lru.go:138 ("for ent := c.evictList.Back(); ent != nil; ent = ent.PrevEntry() {"); SYS-04 simplelru/lru.go:157 ("diff := c.Len() - size"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {"), simplelru/lru.go:170 ("if ent := c.evictList.Back(); ent != nil {"), simplelru/lru.go:180 ("c.onEvict(e.Key, e.Value)"), lru.go:197 ("c.onEvictedCB(ks[i], vs[i])"); SYS-05 simplelru/lru.go:44 ("delete(c.items, k)"), simplelru/lru.go:46 ("c.evictList.Init()"), simplelru/lru.go:147 ("return c.evictList.Length()"), simplelru/lru.go:178 ("delete(c.items, e.Key)"), internal/list.go:102 ("l.len--"). Predicates scoped to one normal receiver unless explicitly evaluated under the variant. SYS-04 separates count mismatch from skipped notification; the public contract does not prescribe all explicit-removal classes (Q-13).

## Doctrine mapping
<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 DOC-5 DOC-6 DOC-7 DOC-8 DOC-9 DOC-10 DOC-11 DOC-12 DOC-13 DOC-14 DOC-15 DOC-16 DOC-17 DOC-18 DOC-19 DOC-20 DOC-21 DOC-22 DOC-23 DOC-24 DOC-25 DOC-26 DOC-27 DOC-28 DOC-29 DOC-30 DOC-31 DOC-32 DOC-33 -->
| Doctrine | Mapping | Target |
|---|---|---|
| DOC-1 | invariant | SYS-01 |
| DOC-2 | invariant | SYS-02 |
| DOC-3 | invariant | SYS-03 |
| DOC-4 | cell | AtCapacity x Add |
| DOC-5 | invariant | SYS-02 |
| DOC-6 | rejected | The example uses expirable.NewLRU, outside the declared Cache boundary. |
| DOC-7 | invariant | SYS-02 |
| DOC-8 | cell | Uninitialized x New |
| DOC-9 | invariant | SYS-04 |
| DOC-10 | cell | AtCapacity x Purge |
| DOC-11 | constraint | SYS-04 |
| DOC-12 | cell | AtCapacity x Get |
| DOC-13 | constraint | SYS-03 |
| DOC-14 | constraint | SYS-03 |
| DOC-15 | constraint | SYS-03 |
| DOC-16 | constraint | SYS-03 |
| DOC-17 | cell | AtCapacity x Remove |
| DOC-18 | cell | AtCapacity x Resize |
| DOC-19 | constraint | SYS-03 |
| DOC-20 | cell | AtCapacity x GetOldest |
| DOC-21 | constraint | SYS-03 |
| DOC-22 | constraint | SYS-03 |
| DOC-23 | invariant | SYS-05 |
| DOC-24 | invariant | SYS-02 |
| DOC-25 | constraint | SYS-03 |
| DOC-26 | constraint | SYS-03 |
| DOC-27 | constraint | SYS-03 |
| DOC-28 | constraint | SYS-03 |
| DOC-29 | constraint | SYS-03 |
| DOC-30 | constraint | SYS-03 |
| DOC-31 | invariant | SYS-05 |
| DOC-32 | invariant | SYS-05 |
| DOC-33 | invariant | SYS-04 |

## Lint and Step 8 review
- Waiting/stopping and cancellation (Q-08, F-13, step-5 lint): no explicit timeout on mutex or callback; no cancellation surface. No source-owned retry or timer. Negative resize can hold the lock beyond useful work (Q-03, F-13, step-5 lint), a bounded integer loop with no practical bound promised. Verified against lru.go:188 ("c.lock.Lock()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {"), simplelru/lru.go:170 ("if ent := c.evictList.Back(); ent != nil {"), lru.go:194 ("c.lock.Unlock()"); do not infer an elapsed time.
- Seam failure and startup (Q-06, F-07, step-5 lint; Q-11, F-06, seam-contract sweep): callback abort escapes after commit and skips batch tail. Invalid store/hash panic happens before unlock; same cache may strand, separately from invalid nil receiver and copied mutex risks. No shutdown method or terminal cache lifecycle; replacement belongs to owner (Q-09, F-18, step-3 checklist). Invocation returns normally, aborts or blocks; callback order/progress is open.
- Overload/retention (Q-04, F-18, adversarial trace; Q-07, F-12, step-3 checklist): normal ring bounded; NaN map orphans can accumulate across bounded-ring use. Boarded buffer length and backing references are separate. Reslice leaves a reference in backing slot; no measurement of garbage collector retention. Independent concurrent callers can hold independent detached batches, with no aggregate bound expressed by cache cap. See simplelru/lru.go:178 ("delete(c.items, e.Key)"), lru.go:85 ("c.evictedKeys, c.evictedVals = c.evictedKeys[:0], c.evictedVals[:0]"), lru.go:65 ("ks, vs = c.evictedKeys, c.evictedVals"), lru.go:66 ("c.initEvictBuffers()").
- Synchronization and return count (Q-01, F-05, step-1 extraction; Q-02, F-03, step-4 matrix walk): real unprotected size read/write; RWMutex ordering applies to locking calls only. Negative resize counter is arithmetic, not observed actual removals. MinInt overflow is not a sentinel mechanism; the ring sentinel is literal root identity (internal/list.go:45 ("root Entry[K, V] // sentinel list element, only &root, root.prev, and root.next are used")). Numeric guard partitions proven separately from violated domain predicates.
- Synchronized reset: no timer/retry limiter or shared source boundary; Purge is an explicit clear and capacity remains unchanged. No reconnect or backoff to reset. Multi-instance probes inapplicable.
- Lifecycle disagreement: mutation and delivery tracks are separate; no fence from clear/resize to outstanding notification (Q-06). Caller completion can invert after the lock (Q-05, F-15, step-3 lock-discipline annotation). Verified lru.go:87 ("c.lock.Unlock()") before lru.go:89 ("c.onEvictedCB(k, v)"), not a same-mutex deadlock. User callback may block independently or recurse by design; there is no concurrency guarantee in its comment.
- Dual cleanup and async transfer: no destructor, lease, callback worker or channel handoff inside Cache. Explicit capacity eviction, Remove and Purge under the same lock do not logically release a normal key twice; Q-04 captures exception for non-reflexive keys. Get is not acquisition of an owned resource (Q-10, F-14, adversarial trace). Caller-held value survives independently.
- User-model gap: result/commit order can differ from callback return order; independent snapshots can span another mutator. Q-05/Q-12 (F-16, adversarial trace). Atomic conditional API observes only after acquisition; separate calls provide no combined decision. A normal false/zero miss is a handled observance, not a refusal.
- Blind findings: Q-13 (F-03, part-B diff) explicit removal classifications; Q-14 (F-03, part-B diff) precise miss returns and oldest-read semantics. Re-read the separate callback/return sites listed in those Qs. These are contract gaps rather than storage bugs for supported keys.
