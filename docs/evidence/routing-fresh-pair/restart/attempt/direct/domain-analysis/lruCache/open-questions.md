# Open domain questions

## Q-01

**Question:** Can Cap run concurrently with Resize under the thread-safe promise?

**Fault:** F-05

**Trigger:** step-1 extraction

**Current behaviour:** observed-in-code unless stated otherwise. Verified bug: read lru.go:254 ("return c.lru.Cap()") and simplelru/lru.go:152 ("return c.size") bypass the lock protecting write lru.go:188 ("c.lock.Lock()"), simplelru/lru.go:164 ("c.size = size"), lru.go:194 ("c.lock.Unlock()"). Other readers acquire the same mutex; Cap acquires none. Race probe is separate from integer tearing or stale-value speculation.

**Options:** synchronize Cap; explicitly restrict concurrent Resize/Cap.

**Proposed:** Keep the decision open until the intended API scope is confirmed.

**Status:** OPEN — human decision required.

## Q-02

**Question:** Which Resize sizes are accepted, and what does its count mean?

**Fault:** F-03

**Trigger:** step-4 matrix walk

**Current behaviour:** observed-in-code unless stated otherwise. API contract issue: constructor rejects nonpositive simplelru/lru.go:25 ("if size <= 0 {"); Resize zero empties, then new keys immediately evict simplelru/lru.go:62 ("evict := c.evictList.Length() > c.size"). Ordinary negative can return more evictions than occurred (simplelru/lru.go:157 ("diff := c.Len() - size"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {"), simplelru/lru.go:170 ("if ent := c.evictList.Back(); ent != nil {"), simplelru/lru.go:165 ("return diff")), assign negative size (simplelru/lru.go:164 ("c.size = size")), and let each new insert evict one. MinInt can wrap and clamp diff to zero, leaving old entries in a negative-capacity cache (simplelru/lru.go:157 ("diff := c.Len() - size"), simplelru/lru.go:158 ("if diff < 0 {")).

**Options:** reject nonpositive; document zero as disabled and reject negatives; define a supported negative meaning.

**Proposed:** Keep the decision open until the intended API scope is confirmed.

**Status:** OPEN — human decision required.

## Q-03

**Question:** What upper work bound should Resize observe on an unsupported negative size?

**Fault:** F-13

**Trigger:** step-5 lint

**Current behaviour:** observed-in-code unless stated otherwise. Progress concern: negative size with representable positive difference can loop long past depletion while holding the mutex (lru.go:188 ("c.lock.Lock()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {"), simplelru/lru.go:170 ("if ent := c.evictList.Back(); ent != nil {"), lru.go:194 ("c.lock.Unlock()")). An overflowed difference is a separate branch in Q-02. No wall time bound was tested.

**Options:** reject invalid size; clamp work to actual length; document operation bound.

**Proposed:** Keep the decision open until the intended API scope is confirmed.

**Status:** OPEN — human decision required.

## Q-04

**Question:** Which comparable keys may be stored, and must Purge release all of them?

**Fault:** F-18

**Trigger:** adversarial trace

**Current behaviour:** observed-in-code unless stated otherwise. Verified scope-qualified bug: NaN fails lookup and delete under equality. A removal unlinks but leaves map entry (simplelru/lru.go:177 ("c.evictList.Remove(e)"), simplelru/lru.go:178 ("delete(c.items, e.Key)"), internal/list.go:102 ("l.len--")); Purge ranges that entry, calls adapter and cannot delete it (simplelru/lru.go:40 ("for k, v := range c.items {"), simplelru/lru.go:42 ("c.onEvict(k, v.Value)"), simplelru/lru.go:44 ("delete(c.items, k)")), then reports empty ring (simplelru/lru.go:46 ("c.evictList.Init()"), internal/list.go:53 ("l.len = 0")). A second Purge can report the same logically removed NaN; orphan accumulation possible with bounded Len; retained bytes unmeasured.

**Options:** exclude non-reflexive keys explicitly; refuse them; support distinct semantics and reliably clear.

**Proposed:** Keep the decision open until the intended API scope is confirmed.

**Status:** OPEN — human decision required.

## Q-05

**Question:** What ordering, overlap, reentrancy and concurrency obligations apply to callback delivery?

**Fault:** F-15

**Trigger:** step-3 lock-discipline annotation

**Current behaviour:** observed-in-code unless stated otherwise. Documentation gap: adapter stores under writer lock (lru.go:81 ("c.lock.Lock()"), lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)"), lru.go:55 ("c.evictedVals = append(c.evictedVals, v)")), but external callback calls after unlock (lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)")). Later caller can commit and finish first; nested calls can see newer state and trigger recursive callbacks. Purge delivery order follows map traversal (simplelru/lru.go:40 ("for k, v := range c.items {")); Resize selects oldest per iteration (simplelru/lru.go:161 ("for i := 0; i < diff; i++ {"), simplelru/lru.go:170 ("if ent := c.evictList.Back(); ent != nil {")). No same-mutex callback deadlock on valid paths; user synchronization may still deadlock.

**Options:** document synchronous per-caller delivery and concurrency; serialize callbacks with defined reentrancy; define weaker guarantees.

**Proposed:** Keep the decision open until the intended API scope is confirmed.

**Status:** OPEN — human decision required.

## Q-06

**Question:** What happens to pending callbacks across Purge/Resize and after callback panic or Goexit?

**Fault:** F-07

**Trigger:** step-5 lint

**Current behaviour:** observed-in-code unless stated otherwise. API/documentation gap: owner can clear, resize or refill while an older captured callback runs; normal return resumes batch, panic/Goexit escapes and skips tail, storage already committed (lru.go:65 ("ks, vs = c.evictedKeys, c.evictedVals"), lru.go:68 ("c.lock.Unlock()"), lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"), lru.go:190 ("if c.onEvictedCB != nil && evicted > 0 {"), lru.go:194 ("c.lock.Unlock()"), lru.go:197 ("c.onEvictedCB(ks[i], vs[i])")). No retry, compensating action or replay; old and later matching keys have no generation fence. Duplicate Purge clears current contents, not a remembered generation.

**Options:** document commit-before-callback and partial notification; isolate each callback; define a generation/order fence.

**Proposed:** Keep the decision open until the intended API scope is confirmed.

**Status:** OPEN — human decision required.

## Q-07

**Question:** What references may remain after a removal and for how long?

**Fault:** F-12

**Trigger:** step-3 checklist

**Current behaviour:** observed-in-code unless stated otherwise. Unverifiable-runtime cost: single callback reslices without clearing the backing key/value slots (lru.go:84 ("k, v = c.evictedKeys[0], c.evictedVals[0]"), lru.go:85 ("c.evictedKeys, c.evictedVals = c.evictedKeys[:0], c.evictedVals[:0]")); subsequent single operations can overwrite slot zero. A batch detaches storage and replaces cache slices (lru.go:65 ("ks, vs = c.evictedKeys, c.evictedVals"), lru.go:66 ("c.initEvictBuffers()")); empty Purge does not replace them (lru.go:64 ("if c.onEvictedCB != nil && len(c.evictedKeys) > 0 {")). Pending callbacks can hold detached batches until return or unwind. Separate NaN map retention Q-04.

**Options:** permit bounded slot retention; clear slots; specify and measure retention.

**Proposed:** Keep the decision open until the intended API scope is confirmed.

**Status:** OPEN — human decision required.

## Q-08

**Question:** What progress/cancellation guarantee applies when an owner or caller stops waiting?

**Fault:** F-13

**Trigger:** step-5 lint

**Current behaviour:** observed-in-code unless stated otherwise. Documentation gap: lock wait lacks context/deadline (lru.go:96 ("c.lock.Lock()"), lru.go:97 ("value, ok = c.lru.Get(key)")); blocking callback holds up its invocation after unlock (lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)")). There is no receiver-side cancellation signal, pending lookup queue or late response replay; dropping interest does not undo issued work. Callback publication or resources outside the caller are outside the seam.

**Options:** document synchronous blocking/non-cancellable semantics; add separately designed cancellation or deadline contract.

**Proposed:** Keep the decision open until the intended API scope is confirmed.

**Status:** OPEN — human decision required.

## Q-09

**Question:** Should a delayed or wrong-instance operation be distinguishable from a valid one after replacement/repopulation?

**Fault:** F-18

**Trigger:** step-3 checklist

**Current behaviour:** observed-in-code unless stated otherwise. Design question: each pointer still names a separate receiver, no generation tag or caller identity (lru.go:35 ("c = &Cache[K, V]{"), lru.go:42 ("c.lru, err = simplelru.NewLRU(size, onEvicted)"), lru.go:82 ("evicted = c.lru.Add(key, value)")). Stale key/value on correct receiver differs from correct payload on wrong receiver. A callback can perform either case; setup has no topology-specific fence.

**Options:** caller owns publication and generation checks; provide an explicit stale-reference fence.

**Proposed:** Keep the decision open until the intended API scope is confirmed.

**Status:** OPEN — human decision required.

## Q-10

**Question:** What does a repeated Get guarantee while the first is pending or the first value is still held?

**Fault:** F-14

**Trigger:** adversarial trace

**Current behaviour:** observed-in-code unless stated otherwise. Design observation: both lookups acquire/commit independently (lru.go:96 ("c.lock.Lock()"), lru.go:97 ("value, ok = c.lru.Get(key)"), lru.go:98 ("c.lock.Unlock()")); each hit updates recency and returns the stored value (simplelru/lru.go:73 ("c.evictList.MoveToFront(ent)"), simplelru/lru.go:74 ("return ent.Value, true")). No lease, caller association, second allocation, wait entry or handoff. Holding a returned pointer does not pin the cache entry. Repeated writes follow ordinary keyed semantics (simplelru/lru.go:52 ("if ent, ok := c.items[key]; ok {"), simplelru/lru.go:54 ("ent.Value = value")).

**Options:** document independent lookup semantics; define a new ownership contract if needed.

**Proposed:** Keep the decision open until the intended API scope is confirmed.

**Status:** OPEN — human decision required.

## Q-11

**Question:** How should invalid receivers, bad keys and copied Cache values fail?

**Fault:** F-06

**Trigger:** seam-contract sweep

**Current behaviour:** observed-in-code unless stated otherwise. API trap: NewWithEvict allocates receiver before inner error (lru.go:35 ("c = &Cache[K, V]{"), lru.go:42 ("c.lru, err = simplelru.NewLRU(size, onEvicted)"), simplelru/lru.go:26 ("return nil, errors.New("must provide a positive size")")). Nil store or dynamic unhashable key can panic while the mutex is held; no deferred unlock on writer Get (lru.go:96 ("c.lock.Lock()"), lru.go:97 ("value, ok = c.lru.Get(key)"), lru.go:98 ("c.lock.Unlock()")) or reader Contains (lru.go:105 ("c.lock.RLock()"), lru.go:106 ("containKey := c.lru.Contains(key)"), lru.go:107 ("c.lock.RUnlock()")). RWMutex contract forbids copy-after-first-use; no wrapper protection. Callback escape is separate and does not strand the lock (Q-06).

**Options:** require successful split result and safe keys; make invalid inputs fail without lock poisoning; specify by category.

**Proposed:** Keep the decision open until the intended API scope is confirmed.

**Status:** OPEN — human decision required.

## Q-12

**Question:** Are independent snapshots or observed absence allowed to become stale before the next call?

**Fault:** F-16

**Trigger:** adversarial trace

**Current behaviour:** observed-in-code unless stated otherwise. User-model gap: compound API is one locked transaction (lru.go:126 ("c.lock.Lock()"), lru.go:127 ("if c.lru.Contains(key) {"), lru.go:131 ("evicted = c.lru.Add(key, value)"), lru.go:149 ("c.lock.Lock()"), lru.go:150 ("previous, ok = c.lru.Peek(key)"), lru.go:155 ("evicted = c.lru.Add(key, value)")); composing separate reads/writes does not give that property. Keys/Values take independent read locks (lru.go:230 ("c.lock.RLock()"), lru.go:232 ("c.lock.RUnlock()"), lru.go:238 ("c.lock.RLock()"), lru.go:240 ("c.lock.RUnlock()")). Concurrent callers can observe different epochs. This does not assert a memory race on the locked operations.

**Options:** document per-call consistency; add a separately specified compound snapshot.

**Proposed:** Keep the decision open until the intended API scope is confirmed.

**Status:** OPEN — human decision required.

## Q-13

**Question:** Which explicit removals count as notified evictions?

**Fault:** F-03

**Trigger:** part-B diff

**Current behaviour:** Observed-in-code: Remove uses removeElement and callback (simplelru/lru.go:99 ("if ent, ok := c.items[key]; ok {"), simplelru/lru.go:180 ("c.onEvict(e.Key, e.Value)"), lru.go:178 ("if c.onEvictedCB != nil && present {")); RemoveOldest likewise (simplelru/lru.go:108 ("if ent := c.evictList.Back(); ent != nil {"), lru.go:214 ("if c.onEvictedCB != nil && ok {")); Purge notifies for iterated entries (simplelru/lru.go:42 ("c.onEvict(k, v.Value)"), lru.go:72 ("c.onEvictedCB(ks[i], vs[i])")). The callback contract says evicted, while explicit removals do not document notification. Part B leaves the classification open.

**Options:** document all removals as notifications; reserve notification for capacity eviction; specify by API.

**Proposed:** Document it after agreeing on the API contract.

**Status:** OPEN — human decision required.

## Q-14

**Question:** What are the exact miss and oldest-read contracts?

**Fault:** F-03

**Trigger:** part-B diff

**Current behaviour:** Observed-in-code: Get and Peek use named zero-value returns on miss (simplelru/lru.go:76 ("return"), simplelru/lru.go:93 ("return")); PeekOrAdd miss returns unnamed initial value plus its flags (lru.go:150 ("previous, ok = c.lru.Peek(key)"), lru.go:155 ("evicted = c.lru.Add(key, value)"), lru.go:164 ("return")); RemoveOldest empty uses named zero/false (simplelru/lru.go:112 ("return")). GetOldest reads Back and returns without touch (simplelru/lru.go:117 ("if ent := c.evictList.Back(); ent != nil {"), simplelru/lru.go:118 ("return ent.Key, ent.Value, true")). Part B does not derive those precise zero-value and recency guarantees from the comments.

**Options:** document zero values and no touch; make miss value unspecified but flags authoritative; specify return per operation.

**Proposed:** Document it after agreeing on the API contract.

**Status:** OPEN — human decision required.
