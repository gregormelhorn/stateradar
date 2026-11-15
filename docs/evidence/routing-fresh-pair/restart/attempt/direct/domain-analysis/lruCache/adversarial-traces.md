# Adversarial traces

Each A/B ordering denotes ordered *effects* unless the trace explicitly splits a lock wait, observation, or callback delivery. All behavior is observed-in-code unless marked otherwise; assumptions and probes are identified. Numbers are scenarios, not timing promises.

### P-01a — Purge → Add

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Add targets key 1; new value 11 for writes.
2. Purge commits/observes before Add. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: insert 1=11 without eviction; len=1. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:82 ("evicted = c.lru.Add(key, value)"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).
Variant: start AtCapacity with capacity one, A has already evicted key 1 and its callback waits. B Purges key 2 → Empty, then independent Add of key 3 → AtCapacity; B finishes before A. The older callback later returns and A reports its original eviction. Q-05/Q-06. Source: lru.go:63 ("c.lru.Purge()"), lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)").
- Reachability: AtCapacity → AtCapacity — domain-analysis/lruCache/_probe/cache_pilot_test.go:45 ("d.Len() == d.Cap() && d.Contains(3)")

### P-01b — Add → Purge

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Add targets key 1; new value 11 for writes.
2. Add commits/observes before Purge. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: replace 1 with 11, then Purge empties. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:82 ("evicted = c.lru.Add(key, value)"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-02a — Purge → Get

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Get targets key 1; new value 11 for writes.
2. Purge commits/observes before Get. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns zero,false. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:97 ("value, ok = c.lru.Get(key)"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-02b — Get → Purge

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Get targets key 1; new value 11 for writes.
2. Get commits/observes before Purge. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns 10,true and touches, then Purge empties. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:97 ("value, ok = c.lru.Get(key)"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-03a — Purge → Contains

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Contains targets key 1; new value 11 for writes.
2. Purge commits/observes before Contains. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns false. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:106 ("containKey := c.lru.Contains(key)"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-03b — Contains → Purge

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Contains targets key 1; new value 11 for writes.
2. Contains commits/observes before Purge. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns true, then Purge empties. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:106 ("containKey := c.lru.Contains(key)"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-04a — Purge → Peek

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Peek targets key 1; new value 11 for writes.
2. Purge commits/observes before Peek. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns zero,false. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:115 ("value, ok = c.lru.Peek(key)"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-04b — Peek → Purge

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Peek targets key 1; new value 11 for writes.
2. Peek commits/observes before Purge. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns 10,true without touch, then Purge empties. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:115 ("value, ok = c.lru.Peek(key)"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-05a — Purge → ContainsOrAdd

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller ContainsOrAdd targets key 1; new value 11 for writes.
2. Purge commits/observes before ContainsOrAdd. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns false,false and inserts 1=11. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:127 ("if c.lru.Contains(key) {"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-05b — ContainsOrAdd → Purge

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller ContainsOrAdd targets key 1; new value 11 for writes.
2. ContainsOrAdd commits/observes before Purge. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns true,false and preserves 10, then Purge empties. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:127 ("if c.lru.Contains(key) {"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-06a — Purge → PeekOrAdd

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller PeekOrAdd targets key 1; new value 11 for writes.
2. Purge commits/observes before PeekOrAdd. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns zero,false,false and inserts 1=11. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:150 ("previous, ok = c.lru.Peek(key)"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-06b — PeekOrAdd → Purge

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller PeekOrAdd targets key 1; new value 11 for writes.
2. PeekOrAdd commits/observes before Purge. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns 10,true,false, then Purge empties. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:150 ("previous, ok = c.lru.Peek(key)"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-07a — Purge → Remove

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Remove targets key 1; new value 11 for writes.
2. Purge commits/observes before Remove. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns false. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:172 ("present = c.lru.Remove(key)"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-07b — Remove → Purge

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Remove targets key 1; new value 11 for writes.
2. Remove commits/observes before Purge. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: removes 1 and returns true; Purge clears 2. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:172 ("present = c.lru.Remove(key)"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-08a — Purge → RemoveOldest

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller RemoveOldest.
2. Purge commits/observes before RemoveOldest. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns zero pair,false. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:208 ("key, value, ok = c.lru.RemoveOldest()"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-08b — RemoveOldest → Purge

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller RemoveOldest.
2. RemoveOldest commits/observes before Purge. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: removes oldest 1=10; Purge clears 2. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:208 ("key, value, ok = c.lru.RemoveOldest()"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-09a — Purge → GetOldest

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller GetOldest.
2. Purge commits/observes before GetOldest. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns zero pair,false. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:223 ("key, value, ok = c.lru.GetOldest()"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-09b — GetOldest → Purge

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller GetOldest.
2. GetOldest commits/observes before Purge. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: reads oldest 1=10; Purge clears both. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:223 ("key, value, ok = c.lru.GetOldest()"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-10a — Purge → Keys

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Keys.
2. Purge commits/observes before Keys. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns []. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:231 ("keys := c.lru.Keys()"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-10b — Keys → Purge

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Keys.
2. Keys commits/observes before Purge. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns [1,2]; Purge does not mutate the prior slice. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:231 ("keys := c.lru.Keys()"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-11a — Purge → Values

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Values.
2. Purge commits/observes before Values. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns []. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:239 ("values := c.lru.Values()"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-11b — Values → Purge

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Values.
2. Values commits/observes before Purge. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns [10,20]; Purge does not mutate the prior slice. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:239 ("values := c.lru.Values()"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-12a — Purge → Len

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Len.
2. Purge commits/observes before Len. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns 0. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:247 ("length := c.lru.Len()"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-12b — Len → Purge

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Len.
2. Len commits/observes before Purge. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns 2; final count is 0. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:247 ("length := c.lru.Len()"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-13a — Purge → Cap

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Cap.
2. Purge commits/observes before Cap. Owner holds writer lock; Cap has no lock or recheck.
3. Observed: returns 2. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:254 ("return c.lru.Cap()"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-13b — Cap → Purge

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests clear; independent caller Cap.
2. Cap commits/observes before Purge. Owner holds writer lock; Cap has no lock or recheck.
3. Observed: returns 2 even though Purge clears both. Evidence: lru.go:63 ("c.lru.Purge()"), lru.go:254 ("return c.lru.Cap()"), simplelru/lru.go:46 ("c.evictList.Init()").
Verdict: none — control trace (code replay).

### P-14a — Resize → Add

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Add targets key 1; new value 11 for writes.
2. Resize commits/observes before Add. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: 1 absent after shrink; insert 1=11 evicts 2. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:82 ("evicted = c.lru.Add(key, value)"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-14b — Add → Resize

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Add targets key 1; new value 11 for writes.
2. Add commits/observes before Resize. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: replace 1=11 and touch; shrink evicts 2. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:82 ("evicted = c.lru.Add(key, value)"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-15a — Resize → Get

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Get targets key 1; new value 11 for writes.
2. Resize commits/observes before Get. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns zero,false after 1 evicted. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:97 ("value, ok = c.lru.Get(key)"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-15b — Get → Resize

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Get targets key 1; new value 11 for writes.
2. Get commits/observes before Resize. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns 10,true and touches; shrink evicts 2 instead. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:97 ("value, ok = c.lru.Get(key)"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-16a — Resize → Contains

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Contains targets key 1; new value 11 for writes.
2. Resize commits/observes before Contains. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns false. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:106 ("containKey := c.lru.Contains(key)"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-16b — Contains → Resize

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Contains targets key 1; new value 11 for writes.
2. Contains commits/observes before Resize. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns true without touch, then shrink evicts 1. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:106 ("containKey := c.lru.Contains(key)"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-17a — Resize → Peek

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Peek targets key 1; new value 11 for writes.
2. Resize commits/observes before Peek. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns zero,false. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:115 ("value, ok = c.lru.Peek(key)"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-17b — Peek → Resize

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Peek targets key 1; new value 11 for writes.
2. Peek commits/observes before Resize. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns 10,true without touch, then shrink evicts 1. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:115 ("value, ok = c.lru.Peek(key)"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-18a — Resize → ContainsOrAdd

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller ContainsOrAdd targets key 1; new value 11 for writes.
2. Resize commits/observes before ContainsOrAdd. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: miss inserts 1=11 and evicts 2. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:127 ("if c.lru.Contains(key) {"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-18b — ContainsOrAdd → Resize

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller ContainsOrAdd targets key 1; new value 11 for writes.
2. ContainsOrAdd commits/observes before Resize. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: hit preserves value and recency; shrink evicts 1. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:127 ("if c.lru.Contains(key) {"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-19a — Resize → PeekOrAdd

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller PeekOrAdd targets key 1; new value 11 for writes.
2. Resize commits/observes before PeekOrAdd. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: miss inserts 1=11 and evicts 2. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:150 ("previous, ok = c.lru.Peek(key)"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-19b — PeekOrAdd → Resize

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller PeekOrAdd targets key 1; new value 11 for writes.
2. PeekOrAdd commits/observes before Resize. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns 10,true,false; shrink evicts 1. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:150 ("previous, ok = c.lru.Peek(key)"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-20a — Resize → Remove

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Remove targets key 1; new value 11 for writes.
2. Resize commits/observes before Remove. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns false because 1 already evicted. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:172 ("present = c.lru.Remove(key)"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-20b — Remove → Resize

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Remove targets key 1; new value 11 for writes.
2. Remove commits/observes before Resize. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns true; shrink evicts zero. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:172 ("present = c.lru.Remove(key)"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-21a — Resize → RemoveOldest

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller RemoveOldest.
2. Resize commits/observes before RemoveOldest. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: removes surviving 2; final len=0. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:208 ("key, value, ok = c.lru.RemoveOldest()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-21b — RemoveOldest → Resize

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller RemoveOldest.
2. RemoveOldest commits/observes before Resize. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: removes 1; shrink evicts zero and keeps 2. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:208 ("key, value, ok = c.lru.RemoveOldest()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-22a — Resize → GetOldest

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller GetOldest.
2. Resize commits/observes before GetOldest. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns 2=20,true. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:223 ("key, value, ok = c.lru.GetOldest()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-22b — GetOldest → Resize

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller GetOldest.
2. GetOldest commits/observes before Resize. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns 1=10,true without touch; shrink evicts 1. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:223 ("key, value, ok = c.lru.GetOldest()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: Q-14 — no-touch behavior is observed, but the comment does not state its effect on resize victim selection.

### P-23a — Resize → Keys

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Keys.
2. Resize commits/observes before Keys. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns [2]. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:231 ("keys := c.lru.Keys()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-23b — Keys → Resize

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Keys.
2. Keys commits/observes before Resize. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns [1,2] before shrink. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:231 ("keys := c.lru.Keys()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-24a — Resize → Values

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Values.
2. Resize commits/observes before Values. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns [20]. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:239 ("values := c.lru.Values()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-24b — Values → Resize

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Values.
2. Values commits/observes before Resize. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns [10,20] before shrink. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:239 ("values := c.lru.Values()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-25a — Resize → Len

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Len.
2. Resize commits/observes before Len. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns 1. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:247 ("length := c.lru.Len()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-25b — Len → Resize

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Len.
2. Len commits/observes before Resize. Each operation acquires its mutex mode before observing state, so it acts on the contents at acquisition; no stale pre-lock gate.
3. Observed: returns 2 before shrink; final count 1. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:247 ("length := c.lru.Len()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: none — control trace (code replay).

### P-26a — Resize → Cap

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Cap.
2. Resize commits/observes before Cap. Owner holds writer lock; Cap has no lock or recheck.
3. Observed: returns 1 if completed before read; concurrent overlap is a data race. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:254 ("return c.lru.Cap()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: Q-01 — ordered outcomes hold only when ordered by the environment; overlap violates thread safety.

### P-26b — Cap → Resize

1. Start AtCapacity (cap=2, keys [1,2] oldest first, vals [10,20], no callback). Owner requests size 1; independent caller Cap.
2. Cap commits/observes before Resize. Owner holds writer lock; Cap has no lock or recheck.
3. Observed: returns 2 if completed before write; concurrent overlap is a data race. Evidence: lru.go:189 ("evicted = c.lru.Resize(size)"), lru.go:254 ("return c.lru.Cap()"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {").
Verdict: Q-01 — ordered outcomes hold only when ordered by the environment; overlap violates thread safety.

### P-27a — Purge → CallbackReturn

1. Start capacity 2 with callback registered; Add(1), Add(2), Add(3) commits eviction of 1; its callback enters and pauses after writer unlock (lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)")).
2. Independent Purge clears both current entries before the older callback returns. Cache owner can acquire the writer lock; the callback and owner remain independent. lru.go:63 ("c.lru.Purge()").
3. Normal return resumes old call or its batch; owner never drains/revokes it. With no later input, committed state and any pending work remain as observed; no worker takes it over. lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"), lru.go:194 ("c.lock.Unlock()"), lru.go:197 ("c.onEvictedCB(ks[i], vs[i])").
Verdict: Q-06.

### P-27b — CallbackReturn → Purge

1. Start capacity 2 with callback registered; Add(1), Add(2), Add(3) commits eviction of 1; its callback enters and pauses after writer unlock (lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)")).
2. Old callback returns before independent Purge. Cache owner can acquire the writer lock; the callback and owner remain independent. lru.go:63 ("c.lru.Purge()").
3. Normal return resumes old call or its batch; owner never drains/revokes it. With no later input, committed state and any pending work remain as observed; no worker takes it over. lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"), lru.go:194 ("c.lock.Unlock()"), lru.go:197 ("c.onEvictedCB(ks[i], vs[i])").
Verdict: Q-06.

### P-28a — Purge → CallbackReenter

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let Purge make its observation/commit before CallbackReenter. An ordinary nested method takes its own mutex and computes its guard then. lru.go:63 ("c.lru.Purge()").
3. Observed: nested Add(3,33) runs on the cleared receiver and leaves key 3. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-28b — CallbackReenter → Purge

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let CallbackReenter make its observation/commit before Purge. An ordinary nested method takes its own mutex and computes its guard then. lru.go:63 ("c.lru.Purge()").
3. Observed: then Purge removes the nested addition. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-29a — Purge → UV-10

1. Start capacity 2 with callback registered; Add(1), Add(2), Add(3) commits eviction of 1; its callback enters and pauses after writer unlock (lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)")).
2. Independent Purge clears both current entries before the older callback stalls, panics or Goexits. Cache owner can acquire the writer lock; the callback and owner remain independent. lru.go:63 ("c.lru.Purge()").
3. Stall keeps old invocation pending; panic/Goexit escapes it and skips any remaining captured batch. New positive input or matching reinsertion does not replay dropped payloads. With no later input, committed state and any pending work remain as observed; no worker takes it over. lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"), lru.go:194 ("c.lock.Unlock()"), lru.go:197 ("c.onEvictedCB(ks[i], vs[i])").
Verdict: Q-06 and Q-08.

### P-29b — UV-10 → Purge

1. Start capacity 2 with callback registered; Add(1), Add(2), Add(3) commits eviction of 1; its callback enters and pauses after writer unlock (lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)")).
2. Old callback either waits, panics or Goexits before independent Purge. Cache owner can acquire the writer lock; the callback and owner remain independent. lru.go:63 ("c.lru.Purge()").
3. Stall keeps old invocation pending; panic/Goexit escapes it and skips any remaining captured batch. New positive input or matching reinsertion does not replay dropped payloads. With no later input, committed state and any pending work remain as observed; no worker takes it over. lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"), lru.go:194 ("c.lock.Unlock()"), lru.go:197 ("c.onEvictedCB(ks[i], vs[i])").
Verdict: Q-06 and Q-08.

### P-30a — Resize → CallbackReturn

1. Start capacity 2 with callback registered; Add(1), Add(2), Add(3) commits eviction of 1; its callback enters and pauses after writer unlock (lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)")).
2. Independent Resize shrinks to 1 before the older callback returns. Cache owner can acquire the writer lock; the callback and owner remain independent. lru.go:189 ("evicted = c.lru.Resize(size)").
3. Normal return resumes old call or its batch; owner never drains/revokes it. With no later input, committed state and any pending work remain as observed; no worker takes it over. lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"), lru.go:194 ("c.lock.Unlock()"), lru.go:197 ("c.onEvictedCB(ks[i], vs[i])").
Verdict: Q-06.

### P-30b — CallbackReturn → Resize

1. Start capacity 2 with callback registered; Add(1), Add(2), Add(3) commits eviction of 1; its callback enters and pauses after writer unlock (lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)")).
2. Old callback returns before independent Resize. Cache owner can acquire the writer lock; the callback and owner remain independent. lru.go:189 ("evicted = c.lru.Resize(size)").
3. Normal return resumes old call or its batch; owner never drains/revokes it. With no later input, committed state and any pending work remain as observed; no worker takes it over. lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"), lru.go:194 ("c.lock.Unlock()"), lru.go:197 ("c.onEvictedCB(ks[i], vs[i])").
Verdict: Q-06.

### P-31a — Resize → CallbackReenter

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let Resize make its observation/commit before CallbackReenter. An ordinary nested method takes its own mutex and computes its guard then. lru.go:189 ("evicted = c.lru.Resize(size)").
3. Observed: nested Add(3,33) applies cap=1 and may evict surviving key 2. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-31b — CallbackReenter → Resize

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let CallbackReenter make its observation/commit before Resize. An ordinary nested method takes its own mutex and computes its guard then. lru.go:189 ("evicted = c.lru.Resize(size)").
3. Observed: then Resize(1) preserves newest key 3. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-32a — Resize → UV-10

1. Start capacity 2 with callback registered; Add(1), Add(2), Add(3) commits eviction of 1; its callback enters and pauses after writer unlock (lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)")).
2. Independent Resize shrinks to 1 before the older callback stalls, panics or Goexits. Cache owner can acquire the writer lock; the callback and owner remain independent. lru.go:189 ("evicted = c.lru.Resize(size)").
3. Stall keeps old invocation pending; panic/Goexit escapes it and skips any remaining captured batch. New positive input or matching reinsertion does not replay dropped payloads. With no later input, committed state and any pending work remain as observed; no worker takes it over. lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"), lru.go:194 ("c.lock.Unlock()"), lru.go:197 ("c.onEvictedCB(ks[i], vs[i])").
Verdict: Q-06 and Q-08.

### P-32b — UV-10 → Resize

1. Start capacity 2 with callback registered; Add(1), Add(2), Add(3) commits eviction of 1; its callback enters and pauses after writer unlock (lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)")).
2. Old callback either waits, panics or Goexits before independent Resize. Cache owner can acquire the writer lock; the callback and owner remain independent. lru.go:189 ("evicted = c.lru.Resize(size)").
3. Stall keeps old invocation pending; panic/Goexit escapes it and skips any remaining captured batch. New positive input or matching reinsertion does not replay dropped payloads. With no later input, committed state and any pending work remain as observed; no worker takes it over. lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"), lru.go:194 ("c.lock.Unlock()"), lru.go:197 ("c.onEvictedCB(ks[i], vs[i])").
Verdict: Q-06 and Q-08.

### P-33a — Add → CallbackReenter

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let Add make its observation/commit before CallbackReenter. An ordinary nested method takes its own mutex and computes its guard then. lru.go:82 ("evicted = c.lru.Add(key, value)").
3. Observed: nested Add(3,33) overwrites caller's key 3 value 30. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-33b — CallbackReenter → Add

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let CallbackReenter make its observation/commit before Add. An ordinary nested method takes its own mutex and computes its guard then. lru.go:82 ("evicted = c.lru.Add(key, value)").
3. Observed: then caller Add(3,30) replaces 33. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-34a — Get → CallbackReenter

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let Get make its observation/commit before CallbackReenter. An ordinary nested method takes its own mutex and computes its guard then. lru.go:97 ("value, ok = c.lru.Get(key)").
3. Observed: caller Get(3) can return 30 before nested replaces it with 33. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-34b — CallbackReenter → Get

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let CallbackReenter make its observation/commit before Get. An ordinary nested method takes its own mutex and computes its guard then. lru.go:97 ("value, ok = c.lru.Get(key)").
3. Observed: then caller Get(3) returns 33 and touches. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-35a — ContainsOrAdd → CallbackReenter

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let ContainsOrAdd make its observation/commit before CallbackReenter. An ordinary nested method takes its own mutex and computes its guard then. lru.go:127 ("if c.lru.Contains(key) {").
3. Observed: caller finds key 3 with 30; nested Add replaces it with 33. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-35b — CallbackReenter → ContainsOrAdd

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let CallbackReenter make its observation/commit before ContainsOrAdd. An ordinary nested method takes its own mutex and computes its guard then. lru.go:127 ("if c.lru.Contains(key) {").
3. Observed: then membership hit preserves nested value 33. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-36a — PeekOrAdd → CallbackReenter

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let PeekOrAdd make its observation/commit before CallbackReenter. An ordinary nested method takes its own mutex and computes its guard then. lru.go:150 ("previous, ok = c.lru.Peek(key)").
3. Observed: caller returns 30 on hit; nested Add replaces it with 33. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-36b — CallbackReenter → PeekOrAdd

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let CallbackReenter make its observation/commit before PeekOrAdd. An ordinary nested method takes its own mutex and computes its guard then. lru.go:150 ("previous, ok = c.lru.Peek(key)").
3. Observed: then hit returns 33 without recency change. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-37a — Remove → CallbackReenter

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let Remove make its observation/commit before CallbackReenter. An ordinary nested method takes its own mutex and computes its guard then. lru.go:172 ("present = c.lru.Remove(key)").
3. Observed: caller Remove(3) unlinks it; nested Add reinserts as 33. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-37b — CallbackReenter → Remove

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let CallbackReenter make its observation/commit before Remove. An ordinary nested method takes its own mutex and computes its guard then. lru.go:172 ("present = c.lru.Remove(key)").
3. Observed: then Remove removes the replacement 33. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-38a — RemoveOldest → CallbackReenter

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let RemoveOldest make its observation/commit before CallbackReenter. An ordinary nested method takes its own mutex and computes its guard then. lru.go:208 ("key, value, ok = c.lru.RemoveOldest()").
3. Observed: oldest key 2 removed first; nested Add touches key 3. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-38b — CallbackReenter → RemoveOldest

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let CallbackReenter make its observation/commit before RemoveOldest. An ordinary nested method takes its own mutex and computes its guard then. lru.go:208 ("key, value, ok = c.lru.RemoveOldest()").
3. Observed: nested Add(2,22) makes key 2 newest; RemoveOldest removes key 3. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05.

### P-39a — Cap → CallbackReenter

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let Cap make its observation/commit before CallbackReenter. An ordinary nested method takes its own mutex and computes its guard then. lru.go:254 ("return c.lru.Cap()").
3. Observed: Cap returns 2 before nested Resize(1); overlapping read/write is unprotected. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05 and Q-01.

### P-39b — CallbackReenter → Cap

1. Start cap=2 and keys [2,3] after earlier Add evicted 1. User callback for 1 can invoke another operation after lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)"). Other notifications return normally; nested Add targets 3=33 unless stated.
2. Let CallbackReenter make its observation/commit before Cap. An ordinary nested method takes its own mutex and computes its guard then. lru.go:254 ("return c.lru.Cap()").
3. Observed: Cap returns 1 after synchronized completion of nested Resize(1); an overlap is still unprotected. Earlier results retain their original return value even if callback subsequently changes the store.
Verdict: Q-05 and Q-01.

### P-40a — Add → UV-10

1. Start capacity 2 with callback registered; Add(1), Add(2), Add(3) commits eviction of 1; its callback enters and pauses after writer unlock (lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)")).
2. Independent Add clears both current entries before the older callback stalls, panics or Goexits. Cache owner can acquire the writer lock; the callback and owner remain independent. lru.go:82 ("evicted = c.lru.Add(key, value)").
3. Stall keeps old invocation pending; panic/Goexit escapes it and skips any remaining captured batch. New positive input or matching reinsertion does not replay dropped payloads. With no later input, committed state and any pending work remain as observed; no worker takes it over. lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"), lru.go:194 ("c.lock.Unlock()"), lru.go:197 ("c.onEvictedCB(ks[i], vs[i])").
Verdict: Q-06 and Q-08.

### P-40b — UV-10 → Add

1. Start capacity 2 with callback registered; Add(1), Add(2), Add(3) commits eviction of 1; its callback enters and pauses after writer unlock (lru.go:87 ("c.lock.Unlock()"), lru.go:89 ("c.onEvictedCB(k, v)")).
2. Old callback either waits, panics or Goexits before independent Add. Cache owner can acquire the writer lock; the callback and owner remain independent. lru.go:82 ("evicted = c.lru.Add(key, value)").
3. Stall keeps old invocation pending; panic/Goexit escapes it and skips any remaining captured batch. New positive input or matching reinsertion does not replay dropped payloads. With no later input, committed state and any pending work remain as observed; no worker takes it over. lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"), lru.go:194 ("c.lock.Unlock()"), lru.go:197 ("c.onEvictedCB(ks[i], vs[i])").
Verdict: Q-06 and Q-08.

### P-41a — New → UV-05

1. Old receiver has key 1=10. Owner calls New(2) to create unrelated empty cache; independent caller holds old reference and plans Get(1).
2. New allocates fresh empty store, then the delayed Get(1) on retained receiver still returns 10,true; Get on the newly selected receiver misses. lru.go:35 ("c = &Cache[K, V]{"), lru.go:42 ("c.lru, err = simplelru.NewLRU(size, onEvicted)"), simplelru/lru.go:32 ("items:     make(map[K]*internal.Entry[K, V]),"), lru.go:97 ("value, ok = c.lru.Get(key)").
3. Publication and memory ordering of the reference belong to caller wiring. Cache has no restart fence or migration.
Verdict: Q-09.

### P-41b — UV-05 → New

1. Old receiver has key 1=10. Owner calls New(2) to create unrelated empty cache; independent caller holds old reference and plans Get(1).
2. Get(1) returns 10,true on old receiver, then New allocates fresh empty store. lru.go:35 ("c = &Cache[K, V]{"), lru.go:42 ("c.lru, err = simplelru.NewLRU(size, onEvicted)"), simplelru/lru.go:32 ("items:     make(map[K]*internal.Entry[K, V]),"), lru.go:97 ("value, ok = c.lru.Get(key)").
3. Publication and memory ordering of the reference belong to caller wiring. Cache has no restart fence or migration.
Verdict: Q-09.

### T-01 — Below capacity and at capacity, simultaneous conditional insertion

Capacity 2 empty: A/B issue ContainsOrAdd(1,10/20); no map observation precedes acquisition. First locked observation misses, first inserts with no eviction, later acquired call sees hit and preserves it. Full [1,2]: A/B issue PeekOrAdd(3,30/31); first locked miss inserts and evicts 1, later hits 3 and returns stored value. External normal completion may invert only if first uses enabled eviction callback. No duplicate admission. lru.go:126 ("c.lock.Lock()"), lru.go:127 ("if c.lru.Contains(key) {"), lru.go:131 ("evicted = c.lru.Add(key, value)"), lru.go:149 ("c.lock.Lock()"), lru.go:150 ("previous, ok = c.lru.Peek(key)"), lru.go:155 ("evicted = c.lru.Add(key, value)"), lru.go:160 ("c.lock.Unlock()"), lru.go:161 ("if c.onEvictedCB != nil && evicted {"). Q-05/Q-12.

### T-02 — Observed absence before caller's later write

A Contains(3) misses and unlocks; B adds 3=30; A Add(3,31) acquires lock, rechecks and overwrites B. Below capacity increases by one only once; at capacity B evicts one before A replaces. No conditional behavior attaches to A's prior result. lru.go:106 ("containKey := c.lru.Contains(key)"), lru.go:107 ("c.lock.RUnlock()"), lru.go:81 ("c.lock.Lock()"), simplelru/lru.go:52 ("if ent, ok := c.items[key]; ok {"), simplelru/lru.go:62 ("evict := c.evictList.Length() > c.size"). Q-12.

### T-03 — Cap observation during Resize

A starts Cap read, B acquires writer, computes diff under lock and writes size. A does not acquire or recheck; no happens-before provided for this read/store. TestPilotRaceCapResize triggers race detector. lru.go:254 ("return c.lru.Cap()"), simplelru/lru.go:152 ("return c.size"), lru.go:188 ("c.lock.Lock()"), simplelru/lru.go:164 ("c.size = size"). Q-01.

### T-04 — Second Get while the first is pending

Same client starts two goroutines Get(1); an in-flight writer may delay first and second. Upon each writer-lock acquisition recheck current membership; if no intervening mutation both return same value and touch; if Purge or replacement gets between, second misses or returns replacement independently. No caller token, wait entry or release-driven handoff; one eventual state change can affect both independently. lru.go:96 ("c.lock.Lock()"), lru.go:97 ("value, ok = c.lru.Get(key)"), lru.go:98 ("c.lock.Unlock()"), simplelru/lru.go:73 ("c.evictList.MoveToFront(ent)"), simplelru/lru.go:74 ("return ent.Value, true"). Q-10.

### T-05 — Second Get while holding first result

A Get(1) holds returned pointer; second Get sees same pointer in absence of writes. Purge then removes cache membership; A's old pointer remains usable; a later Get misses until repopulation. No new capacity consumption or pin. simplelru/lru.go:74 ("return ent.Value, true"), simplelru/lru.go:44 ("delete(c.items, k)"), simplelru/lru.go:46 ("c.evictList.Init()"). Q-10.

### T-06 — Abort after commit: both sides of teardown

Before later Purge, earlier Add callback can panic or Goexit and caller never returns normally; independent owner then clears. After later Purge or Resize, older callback can also panic/Goexit while owner mutation persists; on normal return it resumes original status or batch. For batch initiated by Purge/Resize itself, callback only runs after respective commit; first abort loses remaining delivery, no later matching call replays it. Without new input it stays lost; matching add schedules only new removals. lru.go:68 ("c.lock.Unlock()"), lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"), lru.go:194 ("c.lock.Unlock()"), lru.go:197 ("c.onEvictedCB(ks[i], vs[i])"). Q-06.

### T-07 — Interest is lost while waiting

A invokes Get while B holds writer in long negative resize. A's external observer abandons result. B still writes size/unlocks; A reacquires, observes resulting entries, and returns to its own goroutine. With no later calls no auto cleanup occurs; later matching Add after negative capacity can self-evict. No Cache-owned result queue. lru.go:96 ("c.lock.Lock()"), lru.go:97 ("value, ok = c.lru.Get(key)"), lru.go:99 ("return value, ok"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {"), simplelru/lru.go:164 ("c.size = size"). Q-03/Q-08.

### T-08 — Normal vs wrapped negative Resize

One entry, resize -2: three iterations, one removal, reported 3, cap=-2. Then a fresh insert self-evicts. Restore positive and add one; resize MinInt: signed diff wraps negative, clamps to zero, retains old item while writing MinInt. Constructor rejects nonpositive, so this is mutation-only. simplelru/lru.go:25 ("if size <= 0 {"), simplelru/lru.go:62 ("evict := c.evictList.Length() > c.size"), simplelru/lru.go:157 ("diff := c.Len() - size"), simplelru/lru.go:158 ("if diff < 0 {"), simplelru/lru.go:161 ("for i := 0; i < diff; i++ {"), simplelru/lru.go:164 ("c.size = size"). Q-02/Q-03.

### T-09 — Non-reflexive key and repeat Purge

Add NaN, Get/Remove miss though count is 1; Add ordinary key at cap=1 evicts NaN from ring, map delete fails. Purge visits both map entries then resets ring. Second Purge visits retained NaN again, including when no new insertion occurs. simplelru/lru.go:60 ("c.items[key] = ent"), simplelru/lru.go:72 ("if ent, ok := c.items[key]; ok {"), simplelru/lru.go:178 ("delete(c.items, e.Key)"), simplelru/lru.go:40 ("for k, v := range c.items {"), simplelru/lru.go:44 ("delete(c.items, k)"), simplelru/lru.go:46 ("c.evictList.Init()"). Q-04.

### T-10 — Break NAT: dynamically unhashable and use after failed constructor

Recover from Get of interface holding []int after acquiring writer: Cap still returns, Len blocks. Repeat through Contains under RLock: other readers can finish before an attempted writer, writer blocks. Failed constructor returns nonnil outer nil-store pointer; use panics before normal unlock. lru.go:42 ("c.lru, err = simplelru.NewLRU(size, onEvicted)"), lru.go:96 ("c.lock.Lock()"), lru.go:97 ("value, ok = c.lru.Get(key)"), lru.go:98 ("c.lock.Unlock()"), lru.go:105 ("c.lock.RLock()"), lru.go:106 ("containKey := c.lru.Contains(key)"), lru.go:107 ("c.lock.RUnlock()"). Q-11.

### T-11 — Wrong receiver vs wrong payload after replacement

Owner publishes new receiver; A stores a correct key/value on retained old receiver: new remains unchanged. B targets correct new receiver with plausible stale value; Add writes it. No generation or owner identity. lru.go:35 ("c = &Cache[K, V]{"), lru.go:82 ("evicted = c.lru.Add(key, value)"), simplelru/lru.go:54 ("ent.Value = value"). Q-09.

### T-12 — Reset and backing storage

Explicit removal or capacity eviction copies key/value then truncates buffers. No later input leaves the element slot untouched; empty Purge does not replace buffers; next single capture can overwrite its first slot, batch detach installs fresh buffers. Pending batch locals remain through callback, including during reentrant updates. List decrements independently; no byte cost conclusion. lru.go:64 ("if c.onEvictedCB != nil && len(c.evictedKeys) > 0 {"), lru.go:65 ("ks, vs = c.evictedKeys, c.evictedVals"), lru.go:66 ("c.initEvictBuffers()"), lru.go:84 ("k, v = c.evictedKeys[0], c.evictedVals[0]"), lru.go:85 ("c.evictedKeys, c.evictedVals = c.evictedKeys[:0], c.evictedVals[:0]"), simplelru/lru.go:177 ("c.evictList.Remove(e)"). Q-07.

### T-13 — Snapshots can straddle mutation

A takes Keys [1,2], releases RLock. B purges and adds 3. A Values reads [30] under separate RLock; caller cannot safely zip these slices. Each remains a valid independent snapshot. lru.go:230 ("c.lock.RLock()"), lru.go:232 ("c.lock.RUnlock()"), lru.go:238 ("c.lock.RLock()"), lru.go:240 ("c.lock.RUnlock()"). Q-12.

### T-14 — README boundary control

Starting condition: successful size-128 cache, no overlapping operations → one caller makes 256 sequential distinct adds of the example keys → count after all adds is 128. Cited text contemplates this ordering: yes — README.md:24-29 shows this very loop and length assertion; no callback or concurrency claim. none — control trace.

### Multi-instance applicability

No shared external cache service, queue, or reconnect/backoff resource exists in this component. Construction allocates a per-instance map and list. Callback may use an application-shared resource but no such topology/contract is supplied. simplelru/lru.go:31 ("evictList: internal.NewList[K, V](),"), simplelru/lru.go:32 ("items:     make(map[K]*internal.Entry[K, V]),"), lru.go:33 ("func NewWithEvict[K comparable, V any](size int, onEvicted func(key K, value V)) (c *Cache[K, V], err error) {"). The three aggregate probes are inapplicable.
