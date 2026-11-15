# Event catalogue

<!-- event-ids: New Purge Resize Add Get Contains Peek ContainsOrAdd PeekOrAdd Remove RemoveOldest GetOldest Keys Values Len Cap CaptureEviction DeliverEviction CallbackReturn CallbackReenter UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| New | external | constructor owner | capacity and optional callback registration; observed-in-code lru.go:42 ("c.lru, err = simplelru.NewLRU(size, onEvicted)"). |
| Purge | external | lifecycle owner | clear request for a selected cache; observed-in-code lru.go:63 ("c.lru.Purge()"). |
| Resize | external | lifecycle owner | change capacity to requested integer; observed-in-code lru.go:189 ("evicted = c.lru.Resize(size)"). |
| Add | external | cache caller | key and value to insert or replace; observed-in-code lru.go:82 ("evicted = c.lru.Add(key, value)"). |
| Get | external | cache caller | read value with recency update; observed-in-code lru.go:97 ("value, ok = c.lru.Get(key)"). |
| Contains | external | cache caller | test membership; observed-in-code lru.go:106 ("containKey := c.lru.Contains(key)"). |
| Peek | external | cache caller | read without recency update; observed-in-code lru.go:115 ("value, ok = c.lru.Peek(key)"). |
| ContainsOrAdd | external | cache caller | test membership or insert key/value; observed-in-code lru.go:127 ("if c.lru.Contains(key) {"). |
| PeekOrAdd | external | cache caller | read or insert key/value; observed-in-code lru.go:150 ("previous, ok = c.lru.Peek(key)"). |
| Remove | external | cache caller | remove selected key; observed-in-code lru.go:172 ("present = c.lru.Remove(key)"). |
| RemoveOldest | external | cache caller | remove oldest entry; observed-in-code lru.go:208 ("key, value, ok = c.lru.RemoveOldest()"). |
| GetOldest | external | cache caller | read oldest entry; observed-in-code lru.go:223 ("key, value, ok = c.lru.GetOldest()"). |
| Keys | external | cache caller | snapshot keys; observed-in-code lru.go:231 ("keys := c.lru.Keys()"). |
| Values | external | cache caller | snapshot values; observed-in-code lru.go:239 ("values := c.lru.Values()"). |
| Len | external | cache caller | read entry count; observed-in-code lru.go:247 ("length := c.lru.Len()"). |
| Cap | external | cache caller | read configured capacity; observed-in-code lru.go:254 ("return c.lru.Cap()"). |
| CaptureEviction | internal | simplelru (internal) | capture key and value from simplelru; observed-in-code lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)"). |
| DeliverEviction | internal | cache invocation (internal) | invoke the registered callback with a captured key and value; observed-in-code lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"). |
| CallbackReturn | external | injected callback | registered function returns control to its invoking cache method; observed-in-code lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"). |
| CallbackReenter | external | injected callback | registered function invokes cache API before returning; observed-in-code lru.go:89 ("c.onEvictedCB(k, v)"). |
| UV-01 | external | constructor owner | constructor omitted or delayed; use before successful publication, including the pointer returned with an error; observed boundary lru.go:97 ("value, ok = c.lru.Get(key)"). |
| UV-02 | external | constructor owner | constructor receives zero, negative, or valid but unintended positive size; a duplicate constructor creates another instance; observed boundary lru.go:42 ("c.lru, err = simplelru.NewLRU(size, onEvicted)"). |
| UV-03 | external | lifecycle owner | Purge omitted/delayed or executed twice; a stale Purge can act after repopulation; observed boundary lru.go:63 ("c.lru.Purge()"). |
| UV-04 | external | lifecycle owner | Resize zero or negative, extreme signed size or valid but unintended positive size; duplicate Resize and competing different sizes; observed boundary lru.go:189 ("evicted = c.lru.Resize(size)"). |
| UV-05 | external | cache caller | caller omits operation, loses interest while waiting, or invokes later using a stale key, value or decision; observed boundary lru.go:96 ("c.lock.Lock()"). |
| UV-06 | external | cache caller | same caller issues a second Get while first is pending or while retaining first value; repeated conditional adds, Add or Remove; observed boundary lru.go:97 ("value, ok = c.lru.Get(key)"). |
| UV-07 | external | cache caller | wrong receiver, distinct from plausible wrong key/value or stale generation on intended receiver; contradictory same-key operations; observed boundary lru.go:82 ("evicted = c.lru.Add(key, value)"). |
| UV-08 | external | cache caller | non-reflexive comparable key such as NaN; observed boundary lru.go:82 ("evicted = c.lru.Add(key, value)"). |
| UV-09 | external | cache caller | interface key with non-comparable dynamic value; observed boundary lru.go:97 ("value, ok = c.lru.Get(key)"). |
| UV-10 | external | injected callback | callback panics or terminates its goroutine before returning; callback waits indefinitely or returns late; observed boundary lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"). |
| UV-11 | external | injected callback | concurrent callbacks can overlap; callback performs duplicate or stale nested work; contradictory nested writes or wrong receiver/payload; observed boundary lru.go:89 ("c.onEvictedCB(k, v)"). |
| UV-12 | external | injected callback | late or aborting callback on either side of Purge or Resize, including captured batch tail; observed boundary lru.go:197 ("c.onEvictedCB(ks[i], vs[i])"). |

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| New: constructor owner | UV-01 | UV-01 | UV-02 | UV-01 | UV-02 | n/a: synchronous direct invocation from lru.go:42 ("c.lru, err = simplelru.NewLRU(size, onEvicted)"). | UV-02 |
| Purge: lifecycle owner | UV-03 | UV-03 | UV-03, UV-04 | UV-03, UV-04 | UV-03, UV-04 | n/a: synchronous direct invocation from lru.go:189 ("evicted = c.lru.Resize(size)"). | UV-04 |
| Resize: lifecycle owner | UV-03 | UV-03 | UV-03, UV-04 | UV-03, UV-04 | UV-03, UV-04 | n/a: synchronous direct invocation from lru.go:189 ("evicted = c.lru.Resize(size)"). | UV-04 |
| Add: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)"). | UV-07, UV-08, UV-09 |
| Get: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)"). | UV-07, UV-08, UV-09 |
| Contains: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)"). | UV-07, UV-08, UV-09 |
| Peek: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)"). | UV-07, UV-08, UV-09 |
| ContainsOrAdd: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)"). | UV-07, UV-08, UV-09 |
| PeekOrAdd: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)"). | UV-07, UV-08, UV-09 |
| Remove: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)"). | UV-07, UV-08, UV-09 |
| RemoveOldest: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)"). | UV-07, UV-08, UV-09 |
| GetOldest: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)"). | UV-07, UV-08, UV-09 |
| Keys: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)"). | UV-07, UV-08, UV-09 |
| Values: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)"). | UV-07, UV-08, UV-09 |
| Len: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)"). | UV-07, UV-08, UV-09 |
| Cap: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)"). | UV-07, UV-08, UV-09 |
| CaptureEviction: simplelru (internal) | n/a: synchronous direct invocation from lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)"). | n/a: synchronous direct invocation from lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)"). | UV-08 | n/a: synchronous direct invocation from lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)"). | n/a: synchronous direct invocation from lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)"). | n/a: synchronous direct invocation from lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)"). | n/a: synchronous direct invocation from lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)"). |
| DeliverEviction: cache invocation (internal) | UV-10, UV-12 | UV-10, UV-12 | UV-08, UV-11 | UV-10, UV-12 | UV-10, UV-12 | n/a: synchronous direct invocation from lru.go:89 ("c.onEvictedCB(k, v)"). | n/a: synchronous direct invocation from lru.go:89 ("c.onEvictedCB(k, v)"). |
| CallbackReturn: injected callback | UV-10 | UV-10, UV-12 | UV-11 | UV-11, UV-12 | UV-11 | n/a: synchronous direct invocation from lru.go:89 ("c.onEvictedCB(k, v)"). | UV-11 |
| CallbackReenter: injected callback | UV-10 | UV-10, UV-12 | UV-11 | UV-11, UV-12 | UV-11 | n/a: synchronous direct invocation from lru.go:89 ("c.onEvictedCB(k, v)"). | UV-11 |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Purge → Add | same receiver; lifecycle owner and independent cache caller |
| P-01b | Add → Purge | same receiver; lifecycle owner and independent cache caller |
| P-02a | Purge → Get | same receiver; lifecycle owner and independent cache caller |
| P-02b | Get → Purge | same receiver; lifecycle owner and independent cache caller |
| P-03a | Purge → Contains | same receiver; lifecycle owner and independent cache caller |
| P-03b | Contains → Purge | same receiver; lifecycle owner and independent cache caller |
| P-04a | Purge → Peek | same receiver; lifecycle owner and independent cache caller |
| P-04b | Peek → Purge | same receiver; lifecycle owner and independent cache caller |
| P-05a | Purge → ContainsOrAdd | same receiver; lifecycle owner and independent cache caller |
| P-05b | ContainsOrAdd → Purge | same receiver; lifecycle owner and independent cache caller |
| P-06a | Purge → PeekOrAdd | same receiver; lifecycle owner and independent cache caller |
| P-06b | PeekOrAdd → Purge | same receiver; lifecycle owner and independent cache caller |
| P-07a | Purge → Remove | same receiver; lifecycle owner and independent cache caller |
| P-07b | Remove → Purge | same receiver; lifecycle owner and independent cache caller |
| P-08a | Purge → RemoveOldest | same receiver; lifecycle owner and independent cache caller |
| P-08b | RemoveOldest → Purge | same receiver; lifecycle owner and independent cache caller |
| P-09a | Purge → GetOldest | same receiver; lifecycle owner and independent cache caller |
| P-09b | GetOldest → Purge | same receiver; lifecycle owner and independent cache caller |
| P-10a | Purge → Keys | same receiver; lifecycle owner and independent cache caller |
| P-10b | Keys → Purge | same receiver; lifecycle owner and independent cache caller |
| P-11a | Purge → Values | same receiver; lifecycle owner and independent cache caller |
| P-11b | Values → Purge | same receiver; lifecycle owner and independent cache caller |
| P-12a | Purge → Len | same receiver; lifecycle owner and independent cache caller |
| P-12b | Len → Purge | same receiver; lifecycle owner and independent cache caller |
| P-13a | Purge → Cap | same receiver; lifecycle owner and independent cache caller |
| P-13b | Cap → Purge | same receiver; lifecycle owner and independent cache caller |
| P-14a | Resize → Add | same receiver; lifecycle owner and independent cache caller |
| P-14b | Add → Resize | same receiver; lifecycle owner and independent cache caller |
| P-15a | Resize → Get | same receiver; lifecycle owner and independent cache caller |
| P-15b | Get → Resize | same receiver; lifecycle owner and independent cache caller |
| P-16a | Resize → Contains | same receiver; lifecycle owner and independent cache caller |
| P-16b | Contains → Resize | same receiver; lifecycle owner and independent cache caller |
| P-17a | Resize → Peek | same receiver; lifecycle owner and independent cache caller |
| P-17b | Peek → Resize | same receiver; lifecycle owner and independent cache caller |
| P-18a | Resize → ContainsOrAdd | same receiver; lifecycle owner and independent cache caller |
| P-18b | ContainsOrAdd → Resize | same receiver; lifecycle owner and independent cache caller |
| P-19a | Resize → PeekOrAdd | same receiver; lifecycle owner and independent cache caller |
| P-19b | PeekOrAdd → Resize | same receiver; lifecycle owner and independent cache caller |
| P-20a | Resize → Remove | same receiver; lifecycle owner and independent cache caller |
| P-20b | Remove → Resize | same receiver; lifecycle owner and independent cache caller |
| P-21a | Resize → RemoveOldest | same receiver; lifecycle owner and independent cache caller |
| P-21b | RemoveOldest → Resize | same receiver; lifecycle owner and independent cache caller |
| P-22a | Resize → GetOldest | same receiver; lifecycle owner and independent cache caller |
| P-22b | GetOldest → Resize | same receiver; lifecycle owner and independent cache caller |
| P-23a | Resize → Keys | same receiver; lifecycle owner and independent cache caller |
| P-23b | Keys → Resize | same receiver; lifecycle owner and independent cache caller |
| P-24a | Resize → Values | same receiver; lifecycle owner and independent cache caller |
| P-24b | Values → Resize | same receiver; lifecycle owner and independent cache caller |
| P-25a | Resize → Len | same receiver; lifecycle owner and independent cache caller |
| P-25b | Len → Resize | same receiver; lifecycle owner and independent cache caller |
| P-26a | Resize → Cap | same receiver; lifecycle owner and independent cache caller |
| P-26b | Cap → Resize | same receiver; lifecycle owner and independent cache caller |
| P-27a | Purge → CallbackReturn | same receiver; lifecycle owner and already running callback |
| P-27b | CallbackReturn → Purge | same receiver; lifecycle owner and already running callback |
| P-28a | Purge → CallbackReenter | same receiver; lifecycle owner and nested cache call |
| P-28b | CallbackReenter → Purge | same receiver; lifecycle owner and nested cache call |
| P-29a | Purge → UV-10 | same receiver; lifecycle owner and callback whose execution stalls or escapes |
| P-29b | UV-10 → Purge | same receiver; lifecycle owner and callback whose execution stalls or escapes |
| P-30a | Resize → CallbackReturn | same receiver; lifecycle owner and already running callback |
| P-30b | CallbackReturn → Resize | same receiver; lifecycle owner and already running callback |
| P-31a | Resize → CallbackReenter | same receiver; lifecycle owner and nested cache call |
| P-31b | CallbackReenter → Resize | same receiver; lifecycle owner and nested cache call |
| P-32a | Resize → UV-10 | same receiver; lifecycle owner and callback whose execution stalls or escapes |
| P-32b | UV-10 → Resize | same receiver; lifecycle owner and callback whose execution stalls or escapes |
| P-33a | Add → CallbackReenter | same receiver or key; independent caller and callback issuing a nested competing method |
| P-33b | CallbackReenter → Add | same receiver or key; independent caller and callback issuing a nested competing method |
| P-34a | Get → CallbackReenter | same receiver or key; independent caller and callback issuing a nested competing method |
| P-34b | CallbackReenter → Get | same receiver or key; independent caller and callback issuing a nested competing method |
| P-35a | ContainsOrAdd → CallbackReenter | same receiver or key; independent caller and callback issuing a nested competing method |
| P-35b | CallbackReenter → ContainsOrAdd | same receiver or key; independent caller and callback issuing a nested competing method |
| P-36a | PeekOrAdd → CallbackReenter | same receiver or key; independent caller and callback issuing a nested competing method |
| P-36b | CallbackReenter → PeekOrAdd | same receiver or key; independent caller and callback issuing a nested competing method |
| P-37a | Remove → CallbackReenter | same receiver or key; independent caller and callback issuing a nested competing method |
| P-37b | CallbackReenter → Remove | same receiver or key; independent caller and callback issuing a nested competing method |
| P-38a | RemoveOldest → CallbackReenter | same receiver or key; independent caller and callback issuing a nested competing method |
| P-38b | CallbackReenter → RemoveOldest | same receiver or key; independent caller and callback issuing a nested competing method |
| P-39a | Cap → CallbackReenter | same receiver or key; independent caller and callback issuing a nested competing method |
| P-39b | CallbackReenter → Cap | same receiver or key; independent caller and callback issuing a nested competing method |
| P-40a | Add → UV-10 | same receiver; independent insert and older callback that can stall or escape |
| P-40b | UV-10 → Add | same receiver; independent insert and older callback that can stall or escape |
| P-41a | New → UV-05 | publication slot; owner constructs replacement and delayed caller might hold an old receiver |
| P-41b | UV-05 → New | publication slot; owner constructs replacement and delayed caller might hold an old receiver |

## Remembrance semantics

No tombstones for reflexive keys; ring count decrements at internal/list.go:102 ("l.len--"), resets at internal/list.go:53 ("l.len = 0"), links clear at internal/list.go:99 ("e.next = nil // avoid memory leaks"), map delete at simplelru/lru.go:178 ("delete(c.items, e.Key)"). Non-reflexive keys use Go equality at simplelru/lru.go:44 ("delete(c.items, k)") and simplelru/lru.go:178 ("delete(c.items, e.Key)"). Single-callback slices truncate at lru.go:85 ("c.evictedKeys, c.evictedVals = c.evictedKeys[:0], c.evictedVals[:0]") without clearing backing slots; batch paths replace the buffers at lru.go:66 ("c.initEvictBuffers()") and lru.go:192 ("c.initEvictBuffers()"). Initial capacity is sixteen (lru.go:47 ("c.evictedKeys = make([]K, 0, DefaultEvictedBufferSize)") and lru.go:48 ("c.evictedVals = make([]V, 0, DefaultEvictedBufferSize)")); batch append can grow at lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)") and lru.go:55 ("c.evictedVals = append(c.evictedVals, v)"); retention cost unmeasured. Capture is owned by the initiating call.

## Lock-discipline annotation

Writer sites: lru.go:62 ("c.lock.Lock()"); lru.go:81 ("c.lock.Lock()"); lru.go:96 ("c.lock.Lock()"); lru.go:126 ("c.lock.Lock()"); lru.go:149 ("c.lock.Lock()"); lru.go:171 ("c.lock.Lock()"); lru.go:188 ("c.lock.Lock()"); lru.go:207 ("c.lock.Lock()"). Reader sites: lru.go:105 ("c.lock.RLock()"); lru.go:114 ("c.lock.RLock()"); lru.go:222 ("c.lock.RLock()"); lru.go:230 ("c.lock.RLock()"); lru.go:238 ("c.lock.RLock()"); lru.go:246 ("c.lock.RLock()"). Cap observation lru.go:254 ("return c.lru.Cap()"). Internal adapter captures under writer lock at lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)") and lru.go:55 ("c.evictedVals = append(c.evictedVals, v)"). Public release and callback sites: lru.go:68 ("c.lock.Unlock()") and lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"); lru.go:87 ("c.lock.Unlock()") and lru.go:89 ("c.onEvictedCB(k, v)"); lru.go:136 ("c.lock.Unlock()") and lru.go:137 ("if c.onEvictedCB != nil && evicted {"); lru.go:160 ("c.lock.Unlock()") and lru.go:161 ("if c.onEvictedCB != nil && evicted {"); lru.go:177 ("c.lock.Unlock()") and lru.go:178 ("if c.onEvictedCB != nil && present {"); lru.go:194 ("c.lock.Unlock()") and lru.go:197 ("c.onEvictedCB(ks[i], vs[i])"); lru.go:213 ("c.lock.Unlock()") and lru.go:214 ("if c.onEvictedCB != nil && ok {"). Registration contract lru.go:31-32; no stated reentrancy, order or failure guarantee.

## Catalogue notes

Owner and caller describe roles; pair classes include equivalent variants through context. Replacement publication belongs to owner wiring. Same-role concurrent callers are covered in free traces.

## Event annotations

### New
- gate: payload: requested capacity and callback presence
- upstream_guards: No application guard supplied; local boundary lru.go:42 ("c.lru, err = simplelru.NewLRU(size, onEvicted)").
- coverage:
  - loss: UV-01
  - delay: UV-01
  - duplication: UV-02
  - out-of-order: UV-01
  - contradiction: UV-02
  - commission: n/a: synchronous direct invocation from lru.go:42 ("c.lru, err = simplelru.NewLRU(size, onEvicted)").
  - value: UV-02

### Purge
- gate: service: entries and callback registration
- upstream_guards: No application guard supplied; local boundary lru.go:63 ("c.lru.Purge()").
- coverage:
  - loss: UV-03
  - delay: UV-03
  - duplication: UV-03, UV-04
  - out-of-order: UV-03, UV-04
  - contradiction: UV-03, UV-04
  - commission: n/a: synchronous direct invocation from lru.go:189 ("evicted = c.lru.Resize(size)").
  - value: UV-04

### Resize
- gate: payload and service: requested size and current length
- upstream_guards: No application guard supplied; local boundary lru.go:189 ("evicted = c.lru.Resize(size)").
- coverage:
  - loss: UV-03
  - delay: UV-03
  - duplication: UV-03, UV-04
  - out-of-order: UV-03, UV-04
  - contradiction: UV-03, UV-04
  - commission: n/a: synchronous direct invocation from lru.go:189 ("evicted = c.lru.Resize(size)").
  - value: UV-04

### Add
- gate: payload and service: key membership, length, capacity and callback registration
- upstream_guards: No application guard supplied; local boundary lru.go:82 ("evicted = c.lru.Add(key, value)").
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)").
  - value: UV-07, UV-08, UV-09

### Get
- gate: payload and service: key membership
- upstream_guards: No application guard supplied; local boundary lru.go:97 ("value, ok = c.lru.Get(key)").
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)").
  - value: UV-07, UV-08, UV-09

### Contains
- gate: payload and service: key membership
- upstream_guards: No application guard supplied; local boundary lru.go:106 ("containKey := c.lru.Contains(key)").
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)").
  - value: UV-07, UV-08, UV-09

### Peek
- gate: payload and service: key membership
- upstream_guards: No application guard supplied; local boundary lru.go:115 ("value, ok = c.lru.Peek(key)").
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)").
  - value: UV-07, UV-08, UV-09

### ContainsOrAdd
- gate: payload and service: membership, length, capacity and callback registration
- upstream_guards: No application guard supplied; local boundary lru.go:127 ("if c.lru.Contains(key) {").
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)").
  - value: UV-07, UV-08, UV-09

### PeekOrAdd
- gate: payload and service: membership, length, capacity and callback registration
- upstream_guards: No application guard supplied; local boundary lru.go:150 ("previous, ok = c.lru.Peek(key)").
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)").
  - value: UV-07, UV-08, UV-09

### Remove
- gate: payload and service: membership and callback registration
- upstream_guards: No application guard supplied; local boundary lru.go:172 ("present = c.lru.Remove(key)").
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)").
  - value: UV-07, UV-08, UV-09

### RemoveOldest
- gate: service: length and callback registration
- upstream_guards: No application guard supplied; local boundary lru.go:208 ("key, value, ok = c.lru.RemoveOldest()").
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)").
  - value: UV-07, UV-08, UV-09

### GetOldest
- gate: service: length
- upstream_guards: No application guard supplied; local boundary lru.go:223 ("key, value, ok = c.lru.GetOldest()").
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)").
  - value: UV-07, UV-08, UV-09

### Keys
- gate: service: list contents
- upstream_guards: No application guard supplied; local boundary lru.go:231 ("keys := c.lru.Keys()").
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)").
  - value: UV-07, UV-08, UV-09

### Values
- gate: service: list contents
- upstream_guards: No application guard supplied; local boundary lru.go:239 ("values := c.lru.Values()").
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)").
  - value: UV-07, UV-08, UV-09

### Len
- gate: service: list length
- upstream_guards: No application guard supplied; local boundary lru.go:247 ("length := c.lru.Len()").
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)").
  - value: UV-07, UV-08, UV-09

### Cap
- gate: service: capacity
- upstream_guards: No application guard supplied; local boundary lru.go:254 ("return c.lru.Cap()").
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go:97 ("value, ok = c.lru.Get(key)").
  - value: UV-07, UV-08, UV-09

### CaptureEviction
- gate: service: registered adapter and removal path
- upstream_guards: No application guard supplied; local boundary lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)").
- coverage:
  - loss: n/a: synchronous direct invocation from lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)").
  - delay: n/a: synchronous direct invocation from lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)").
  - duplication: UV-08
  - out-of-order: n/a: synchronous direct invocation from lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)").
  - contradiction: n/a: synchronous direct invocation from lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)").
  - commission: n/a: synchronous direct invocation from lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)").
  - value: n/a: synchronous direct invocation from lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)").

### DeliverEviction
- gate: service: registered callback and captured work
- upstream_guards: No application guard supplied; local boundary lru.go:72 ("c.onEvictedCB(ks[i], vs[i])").
- coverage:
  - loss: UV-10, UV-12
  - delay: UV-10, UV-12
  - duplication: UV-08, UV-11
  - out-of-order: UV-10, UV-12
  - contradiction: UV-10, UV-12
  - commission: n/a: synchronous direct invocation from lru.go:89 ("c.onEvictedCB(k, v)").
  - value: n/a: synchronous direct invocation from lru.go:89 ("c.onEvictedCB(k, v)").

### CallbackReturn
- gate: service: active invocation and remaining batch
- upstream_guards: No application guard supplied; local boundary lru.go:72 ("c.onEvictedCB(ks[i], vs[i])").
- coverage:
  - loss: UV-10
  - delay: UV-10, UV-12
  - duplication: UV-11
  - out-of-order: UV-11, UV-12
  - contradiction: UV-11
  - commission: n/a: synchronous direct invocation from lru.go:89 ("c.onEvictedCB(k, v)").
  - value: UV-11

### CallbackReenter
- gate: payload and service: nested operation, receiver, active outer invocation
- upstream_guards: No application guard supplied; local boundary lru.go:89 ("c.onEvictedCB(k, v)").
- coverage:
  - loss: UV-10
  - delay: UV-10, UV-12
  - duplication: UV-11
  - out-of-order: UV-11, UV-12
  - contradiction: UV-11
  - commission: n/a: synchronous direct invocation from lru.go:89 ("c.onEvictedCB(k, v)").
  - value: UV-11

### UV-01
- gate: payload or service state depending on the concrete variant above
- upstream_guards: No application guard supplied; local boundary lru.go:97 ("value, ok = c.lru.Get(key)").

### UV-02
- gate: payload or service state depending on the concrete variant above
- upstream_guards: No application guard supplied; local boundary lru.go:42 ("c.lru, err = simplelru.NewLRU(size, onEvicted)").

### UV-03
- gate: payload or service state depending on the concrete variant above
- upstream_guards: No application guard supplied; local boundary lru.go:63 ("c.lru.Purge()").

### UV-04
- gate: payload or service state depending on the concrete variant above
- upstream_guards: No application guard supplied; local boundary lru.go:189 ("evicted = c.lru.Resize(size)").

### UV-05
- gate: payload or service state depending on the concrete variant above
- upstream_guards: No application guard supplied; local boundary lru.go:96 ("c.lock.Lock()").

### UV-06
- gate: payload or service state depending on the concrete variant above
- upstream_guards: No application guard supplied; local boundary lru.go:97 ("value, ok = c.lru.Get(key)").

### UV-07
- gate: payload or service state depending on the concrete variant above
- upstream_guards: No application guard supplied; local boundary lru.go:82 ("evicted = c.lru.Add(key, value)").

### UV-08
- gate: payload or service state depending on the concrete variant above
- upstream_guards: No application guard supplied; local boundary lru.go:82 ("evicted = c.lru.Add(key, value)").

### UV-09
- gate: payload or service state depending on the concrete variant above
- upstream_guards: No application guard supplied; local boundary lru.go:97 ("value, ok = c.lru.Get(key)").

### UV-10
- gate: payload or service state depending on the concrete variant above
- upstream_guards: No application guard supplied; local boundary lru.go:72 ("c.onEvictedCB(ks[i], vs[i])").

### UV-11
- gate: payload or service state depending on the concrete variant above
- upstream_guards: No application guard supplied; local boundary lru.go:89 ("c.onEvictedCB(k, v)").

### UV-12
- gate: payload or service state depending on the concrete variant above
- upstream_guards: No application guard supplied; local boundary lru.go:197 ("c.onEvictedCB(ks[i], vs[i])").

