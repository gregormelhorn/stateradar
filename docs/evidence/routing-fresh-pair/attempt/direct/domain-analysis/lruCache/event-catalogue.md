# Event catalogue

<!-- event-ids: New Purge Resize Add Get Contains Peek ContainsOrAdd PeekOrAdd Remove RemoveOldest GetOldest Keys Values Len Cap CallbackOutcome EvictionCaptured CallbackDispatch UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 UV-15 UV-16 UV-17 UV-18 UV-19 UV-20 UV-21 -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| New | external | Lifecycle owner | Construct an independent cache with a capacity and optional eviction callback. observed-in-code lru.go:42 ("c.lru, err = simplelru.NewLRU(size, onEvicted)"). |
| Purge | external | Lifecycle owner | Clear the cache. observed-in-code lru.go:63 ("c.lru.Purge()"). |
| Resize | external | Lifecycle owner | Change capacity and report number evicted. observed-in-code lru.go:189 ("evicted = c.lru.Resize(size)"). |
| Add | external | API caller | Add or replace key/value, report eviction. observed-in-code lru.go:82 ("evicted = c.lru.Add(key, value)"). |
| Get | external | API caller | Find a key's value. observed-in-code lru.go:97 ("value, ok = c.lru.Get(key)"). |
| Contains | external | API caller | Check key presence without refreshing recency. observed-in-code lru.go:106 ("containKey := c.lru.Contains(key)"). |
| Peek | external | API caller | Read value without refreshing recency. observed-in-code lru.go:115 ("value, ok = c.lru.Peek(key)"). |
| ContainsOrAdd | external | API caller | Check presence and insert if absent. observed-in-code lru.go:127 ("if c.lru.Contains(key) {"). |
| PeekOrAdd | external | API caller | Read an existing value or insert if absent. observed-in-code lru.go:150 ("previous, ok = c.lru.Peek(key)"). |
| Remove | external | API caller | Remove a key. observed-in-code lru.go:172 ("present = c.lru.Remove(key)"). |
| RemoveOldest | external | API caller | Remove the oldest entry. observed-in-code lru.go:208 ("key, value, ok = c.lru.RemoveOldest()"). |
| GetOldest | external | API caller | Read the oldest entry. observed-in-code lru.go:223 ("key, value, ok = c.lru.GetOldest()"). |
| Keys | external | API caller | Return a slice of keys. observed-in-code lru.go:231 ("keys := c.lru.Keys()"). |
| Values | external | API caller | Return a slice of values. observed-in-code lru.go:239 ("values := c.lru.Values()"). |
| Len | external | API caller | Read entry count. observed-in-code lru.go:247 ("length := c.lru.Len()"). |
| Cap | external | API caller | Read capacity. observed-in-code lru.go:254 ("return c.lru.Cap()"). |
| CallbackOutcome | external | Injected callback | User callback returns, blocks, or exits abnormally. observed-in-code lru.go:197 ("c.onEvictedCB(ks[i], vs[i])"). |
| EvictionCaptured | internal | Internal LRU | Record an evicted key/value. observed-in-code lru.go:54 ("c.evictedKeys = append(c.evictedKeys, k)"). |
| CallbackDispatch | internal | Cache operation | Invoke registered eviction callback with removed key and value. observed-in-code lru.go:89 ("c.onEvictedCB(k, v)"). |
| UV-01 | external | Lifecycle owner | Owner omits initialization, purge or capacity adjustment. Boundary observed-in-code lru.go:42 ("c.lru, err = simplelru.NewLRU(size, onEvicted)"). |
| UV-02 | external | Lifecycle owner | Owner delays purge or resize while calls continue. Boundary observed-in-code lru.go:188 ("c.lock.Lock()"). |
| UV-03 | external | Lifecycle owner | Repeat purge or resize, or construct a second instance. Boundary observed-in-code lru.go:63 ("c.lru.Purge()"). |
| UV-04 | external | Lifecycle owner | Purge or resize arrives after owner abandons a reference or crosses a receiver replacement. Boundary observed-in-code lru.go:63 ("c.lru.Purge()"). |
| UV-05 | external | Lifecycle owner | Concurrent conflicting resize targets or purge and resize. Boundary observed-in-code lru.go:189 ("evicted = c.lru.Resize(size)"). |
| UV-06 | external | Lifecycle owner | Unsolicited purge or resize through a retained cache reference. Boundary observed-in-code lru.go:63 ("c.lru.Purge()"). |
| UV-07 | external | Lifecycle owner | Valid unintended capacity, zero, negative, extreme or wrong receiver configuration. Boundary observed-in-code lru.go:189 ("evicted = c.lru.Resize(size)"). |
| UV-08 | external | API caller | Caller omits a call, uses nil or an unsuccessfully initialized receiver. Boundary observed-in-code lru.go:97 ("value, ok = c.lru.Get(key)"). |
| UV-09 | external | API caller | Caller delayed at cache entry or abandons the wait in an outer wrapper. Boundary observed-in-code lru.go:96 ("c.lock.Lock()"). |
| UV-10 | external | API caller | Repeat a request including a second Get from the same caller while its first is pending or while its first result is still held. Boundary observed-in-code lru.go:97 ("value, ok = c.lru.Get(key)"). |
| UV-11 | external | API caller | Stale action for a reused key, delayed call after purge, or a request routed to the wrong instance. Boundary observed-in-code lru.go:172 ("present = c.lru.Remove(key)"). |
| UV-12 | external | API caller | Concurrent same-key writes, conditional adds, read versus eviction, or removal versus reinsertion. Boundary observed-in-code lru.go:127 ("if c.lru.Contains(key) {"). |
| UV-13 | external | API caller | Unsolicited but well-typed call by another holder of the receiver. Boundary observed-in-code lru.go:82 ("evicted = c.lru.Add(key, value)"). |
| UV-14 | external | API caller | Foreign but well-formed key or value, non-reflexive key, or dynamically unhashable interface key. Boundary observed-in-code lru.go:97 ("value, ok = c.lru.Get(key)"). |
| UV-15 | external | Injected callback | Callback panics or exits its goroutine before completing a notification. Boundary observed-in-code lru.go:197 ("c.onEvictedCB(ks[i], vs[i])"). |
| UV-16 | external | Injected callback | Callback stalls while other operations or purge continue. Boundary observed-in-code lru.go:197 ("c.onEvictedCB(ks[i], vs[i])"). |
| UV-17 | external | Injected callback | Repeated application side effects from distinct evictions of reused keys or caller re-entry. Boundary observed-in-code lru.go:72 ("c.onEvictedCB(ks[i], vs[i])"). |
| UV-18 | external | Injected callback | Notification runs across purge or reinsertion, including success or failure before or after purge. Boundary observed-in-code lru.go:197 ("c.onEvictedCB(ks[i], vs[i])"). |
| UV-19 | external | Injected callback | Concurrent callbacks or conflicting callback re-entry. Boundary observed-in-code lru.go:89 ("c.onEvictedCB(k, v)"). |
| UV-20 | external | Injected callback | Callback invocation with no matching removal. Boundary observed-in-code lru.go:89 ("c.onEvictedCB(k, v)"). |
| UV-21 | external | Injected callback | Callback observes a stale payload generation, or sends that key to a different cache. Boundary observed-in-code lru.go:89 ("c.onEvictedCB(k, v)"). |

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| New: Lifecycle owner | UV-01 | UV-02 | UV-03 | UV-04 | UV-05 | UV-06 | UV-07 |
| Purge: Lifecycle owner | UV-01 | UV-02 | UV-03 | UV-04 | UV-05 | UV-06 | UV-07 |
| Resize: Lifecycle owner | UV-01 | UV-02 | UV-03 | UV-04 | UV-05 | UV-06 | UV-07 |
| Add: API caller | UV-08 | UV-09 | UV-10 | UV-11 | UV-12 | UV-13 | UV-14 |
| Get: API caller | UV-08 | UV-09 | UV-10 | UV-11 | UV-12 | UV-13 | UV-14 |
| Contains: API caller | UV-08 | UV-09 | UV-10 | UV-11 | UV-12 | UV-13 | UV-14 |
| Peek: API caller | UV-08 | UV-09 | UV-10 | UV-11 | UV-12 | UV-13 | UV-14 |
| ContainsOrAdd: API caller | UV-08 | UV-09 | UV-10 | UV-11 | UV-12 | UV-13 | UV-14 |
| PeekOrAdd: API caller | UV-08 | UV-09 | UV-10 | UV-11 | UV-12 | UV-13 | UV-14 |
| Remove: API caller | UV-08 | UV-09 | UV-10 | UV-11 | UV-12 | UV-13 | UV-14 |
| RemoveOldest: API caller | UV-08 | UV-09 | UV-10 | UV-11 | UV-12 | UV-13 | UV-14 |
| GetOldest: API caller | UV-08 | UV-09 | UV-10 | UV-11 | UV-12 | UV-13 | UV-14 |
| Keys: API caller | UV-08 | UV-09 | UV-10 | UV-11 | UV-12 | UV-13 | UV-14 |
| Values: API caller | UV-08 | UV-09 | UV-10 | UV-11 | UV-12 | UV-13 | UV-14 |
| Len: API caller | UV-08 | UV-09 | UV-10 | UV-11 | UV-12 | UV-13 | UV-14 |
| Cap: API caller | UV-08 | UV-09 | UV-10 | UV-11 | UV-12 | UV-13 | UV-14 |
| CallbackOutcome: Injected callback | UV-15 | UV-16 | UV-17 | UV-18 | UV-19 | UV-20 | UV-21 |
| EvictionCaptured: Internal LRU | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56. | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56. | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56. | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56. | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56. | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56. | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56. |
| CallbackDispatch: Cache operation | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91. | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91. | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91. | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91. | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91. | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91. | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91. |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Purge → Add | One cache. A lifecycle owner and an independently acting API caller |
| P-01b | Add → Purge | One cache. A lifecycle owner and an independently acting API caller |
| P-02a | Purge → Get | One cache. A lifecycle owner and an independently acting API caller |
| P-02b | Get → Purge | One cache. A lifecycle owner and an independently acting API caller |
| P-03a | Purge → Contains | One cache. A lifecycle owner and an independently acting API caller |
| P-03b | Contains → Purge | One cache. A lifecycle owner and an independently acting API caller |
| P-04a | Purge → Peek | One cache. A lifecycle owner and an independently acting API caller |
| P-04b | Peek → Purge | One cache. A lifecycle owner and an independently acting API caller |
| P-05a | Purge → ContainsOrAdd | One cache. A lifecycle owner and an independently acting API caller |
| P-05b | ContainsOrAdd → Purge | One cache. A lifecycle owner and an independently acting API caller |
| P-06a | Purge → PeekOrAdd | One cache. A lifecycle owner and an independently acting API caller |
| P-06b | PeekOrAdd → Purge | One cache. A lifecycle owner and an independently acting API caller |
| P-07a | Purge → Remove | One cache. A lifecycle owner and an independently acting API caller |
| P-07b | Remove → Purge | One cache. A lifecycle owner and an independently acting API caller |
| P-08a | Purge → RemoveOldest | One cache. A lifecycle owner and an independently acting API caller |
| P-08b | RemoveOldest → Purge | One cache. A lifecycle owner and an independently acting API caller |
| P-09a | Purge → GetOldest | One cache. A lifecycle owner and an independently acting API caller |
| P-09b | GetOldest → Purge | One cache. A lifecycle owner and an independently acting API caller |
| P-10a | Purge → Keys | One cache. A lifecycle owner and an independently acting API caller |
| P-10b | Keys → Purge | One cache. A lifecycle owner and an independently acting API caller |
| P-11a | Purge → Values | One cache. A lifecycle owner and an independently acting API caller |
| P-11b | Values → Purge | One cache. A lifecycle owner and an independently acting API caller |
| P-12a | Purge → Len | One cache. A lifecycle owner and an independently acting API caller |
| P-12b | Len → Purge | One cache. A lifecycle owner and an independently acting API caller |
| P-13a | Purge → Cap | One cache. A lifecycle owner and an independently acting API caller |
| P-13b | Cap → Purge | One cache. A lifecycle owner and an independently acting API caller |
| P-14a | Purge → CallbackOutcome | One cache. A lifecycle owner and an independently acting callback execution |
| P-14b | CallbackOutcome → Purge | One cache. A lifecycle owner and an independently acting callback execution |
| P-15a | Resize → Add | One cache. A lifecycle owner and an independently acting API caller |
| P-15b | Add → Resize | One cache. A lifecycle owner and an independently acting API caller |
| P-16a | Resize → Get | One cache. A lifecycle owner and an independently acting API caller |
| P-16b | Get → Resize | One cache. A lifecycle owner and an independently acting API caller |
| P-17a | Resize → Contains | One cache. A lifecycle owner and an independently acting API caller |
| P-17b | Contains → Resize | One cache. A lifecycle owner and an independently acting API caller |
| P-18a | Resize → Peek | One cache. A lifecycle owner and an independently acting API caller |
| P-18b | Peek → Resize | One cache. A lifecycle owner and an independently acting API caller |
| P-19a | Resize → ContainsOrAdd | One cache. A lifecycle owner and an independently acting API caller |
| P-19b | ContainsOrAdd → Resize | One cache. A lifecycle owner and an independently acting API caller |
| P-20a | Resize → PeekOrAdd | One cache. A lifecycle owner and an independently acting API caller |
| P-20b | PeekOrAdd → Resize | One cache. A lifecycle owner and an independently acting API caller |
| P-21a | Resize → Remove | One cache. A lifecycle owner and an independently acting API caller |
| P-21b | Remove → Resize | One cache. A lifecycle owner and an independently acting API caller |
| P-22a | Resize → RemoveOldest | One cache. A lifecycle owner and an independently acting API caller |
| P-22b | RemoveOldest → Resize | One cache. A lifecycle owner and an independently acting API caller |
| P-23a | Resize → GetOldest | One cache. A lifecycle owner and an independently acting API caller |
| P-23b | GetOldest → Resize | One cache. A lifecycle owner and an independently acting API caller |
| P-24a | Resize → Keys | One cache. A lifecycle owner and an independently acting API caller |
| P-24b | Keys → Resize | One cache. A lifecycle owner and an independently acting API caller |
| P-25a | Resize → Values | One cache. A lifecycle owner and an independently acting API caller |
| P-25b | Values → Resize | One cache. A lifecycle owner and an independently acting API caller |
| P-26a | Resize → Len | One cache. A lifecycle owner and an independently acting API caller |
| P-26b | Len → Resize | One cache. A lifecycle owner and an independently acting API caller |
| P-27a | Resize → Cap | One cache. A lifecycle owner and an independently acting API caller |
| P-27b | Cap → Resize | One cache. A lifecycle owner and an independently acting API caller |
| P-28a | Resize → CallbackOutcome | One cache. A lifecycle owner and an independently acting callback execution |
| P-28b | CallbackOutcome → Resize | One cache. A lifecycle owner and an independently acting callback execution |
| P-29a | Add → CallbackOutcome | One cache. An API caller and a previously dispatched callback |
| P-29b | CallbackOutcome → Add | One cache. An API caller and a previously dispatched callback |
| P-30a | ContainsOrAdd → CallbackOutcome | One cache. An API caller and a previously dispatched callback |
| P-30b | CallbackOutcome → ContainsOrAdd | One cache. An API caller and a previously dispatched callback |
| P-31a | PeekOrAdd → CallbackOutcome | One cache. An API caller and a previously dispatched callback |
| P-31b | CallbackOutcome → PeekOrAdd | One cache. An API caller and a previously dispatched callback |
| P-32a | Remove → CallbackOutcome | One cache. An API caller and a previously dispatched callback |
| P-32b | CallbackOutcome → Remove | One cache. An API caller and a previously dispatched callback |
| P-33a | RemoveOldest → CallbackOutcome | One cache. An API caller and a previously dispatched callback |
| P-33b | CallbackOutcome → RemoveOldest | One cache. An API caller and a previously dispatched callback |
| P-34a | Get → CallbackOutcome | One cache. An API caller and a previously dispatched callback |
| P-34b | CallbackOutcome → Get | One cache. An API caller and a previously dispatched callback |
| P-35a | Contains → CallbackOutcome | One cache. An API caller and a previously dispatched callback |
| P-35b | CallbackOutcome → Contains | One cache. An API caller and a previously dispatched callback |
| P-36a | Peek → CallbackOutcome | One cache. An API caller and a previously dispatched callback |
| P-36b | CallbackOutcome → Peek | One cache. An API caller and a previously dispatched callback |
| P-37a | GetOldest → CallbackOutcome | One cache. An API caller and a previously dispatched callback |
| P-37b | CallbackOutcome → GetOldest | One cache. An API caller and a previously dispatched callback |
| P-38a | Keys → CallbackOutcome | One cache. An API caller and a previously dispatched callback |
| P-38b | CallbackOutcome → Keys | One cache. An API caller and a previously dispatched callback |
| P-39a | Values → CallbackOutcome | One cache. An API caller and a previously dispatched callback |
| P-39b | CallbackOutcome → Values | One cache. An API caller and a previously dispatched callback |
| P-40a | Len → CallbackOutcome | One cache. An API caller and a previously dispatched callback |
| P-40b | CallbackOutcome → Len | One cache. An API caller and a previously dispatched callback |
| P-41a | Cap → CallbackOutcome | One cache. An API caller and a previously dispatched callback |
| P-41b | CallbackOutcome → Cap | One cache. An API caller and a previously dispatched callback |

## Remembrance semantics

observed-in-code: list removal detaches links and decrements length (internal/list.go:95-104), then the map key is deleted (simplelru/lru.go:175-181). Purge deletes map keys and resets the list length (simplelru/lru.go:38-47, internal/list.go:49-55). Len counts list nodes (simplelru/lru.go:145-148), independently of capacity (simplelru/lru.go:150-165). With non-reflexive keys map deletion can fail. Single notifications reslice without clearing backing slots (lru.go:82-89, lru.go:131-138, lru.go:155-162, lru.go:172-179 and lru.go:208-215). Bulk paths detach the captured slices and allocate new buffers, then invoke user callbacks (lru.go:62-73 and lru.go:188-198). Scratch starts at 16 slots per slice (lru.go:12-15 and lru.go:46-49), can grow with a batch (lru.go:53-55) and has no time-based clearing. A delayed callback has the captured payload, may see a later generation, and is independent of list length. Measured heap retention is open.

## Lock-discipline annotation

observed-in-code: Purge, Add, ContainsOrAdd, PeekOrAdd, Remove, Resize and RemoveOldest call the private capture hook inside the writer lock and invoke user callbacks after release (lru.go:62-73, lru.go:81-90, lru.go:126-139, lru.go:149-163, lru.go:171-180, lru.go:188-199 and lru.go:207-216). Get takes the writer lock to promote recency (lru.go:94-99, simplelru/lru.go:70-76). Contains, Peek, GetOldest, Keys, Values and Len use read locks and call no user code (lru.go:104-117 and lru.go:220-249). Cap has no lock (lru.go:252-255). User re-entry runs after unlock in every dispatch branch. The callback contract is silent on re-entry, concurrency and panic (lru.go:31-33 and simplelru/lru.go:12-13).

## Catalogue notes

Constructor calls create independent instances. A request reaches a particular cache by its receiver. Pairs model shared cache state or outputs with distinct actors. CallbackOutcome is the user code's outcome and CallbackDispatch is the cache's internal action. Two caller goroutines can also interleave within the API caller source.

## Event annotations

### New
- gate: payload capacity and callback presence
- upstream_guards: Calls simplelru constructor with supplied size. Its constructor enforces positive size. observed-in-code simplelru/lru.go:25 ("if size <= 0 {").
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-04
  - contradiction: UV-05
  - commission: UV-06
  - value: UV-07

### Purge
- gate: service-side contents and callback presence
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:63.
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-04
  - contradiction: UV-05
  - commission: UV-06
  - value: UV-07

### Resize
- gate: payload capacity and service-side entry count and callback presence
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:189.
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-04
  - contradiction: UV-05
  - commission: UV-06
  - value: UV-07

### Add
- gate: service-side key presence and occupancy, payload key and value
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:82.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Get
- gate: service-side key presence, payload key
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:97.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Contains
- gate: service-side key presence, payload key
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:106.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Peek
- gate: service-side key presence, payload key
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:115.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### ContainsOrAdd
- gate: service-side key presence and occupancy, payload key and value
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:127.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### PeekOrAdd
- gate: service-side key presence and occupancy, payload key and value
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:150.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Remove
- gate: service-side key presence and callback presence, payload key
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:172.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### RemoveOldest
- gate: service-side occupancy and callback presence
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:208.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### GetOldest
- gate: service-side occupancy
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:223.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Keys
- gate: service-side occupancy and recency
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:231.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Values
- gate: service-side occupancy and recency
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:239.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Len
- gate: service-side entry count
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:247.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Cap
- gate: service-side capacity
- upstream_guards: Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go:254.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### CallbackOutcome
- gate: callback control flow and invocation context
- upstream_guards: User function has no error return or stated recovery, timing or re-entry guarantee. observed-in-code lru.go:31-33.
- coverage:
  - loss: UV-15
  - delay: UV-16
  - duplication: UV-17
  - out-of-order: UV-18
  - contradiction: UV-19
  - commission: UV-20
  - value: UV-21

### EvictionCaptured
- gate: service-side removal and callback configuration
- upstream_guards: Produced by the cache removal flow. observed-in-code lru.go:83-89.
- coverage:
  - loss: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56.
  - delay: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56.
  - duplication: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56.
  - out-of-order: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56.
  - contradiction: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56.
  - commission: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56.
  - value: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go:175-181 and lru.go:51-56.

### CallbackDispatch
- gate: service-side callback configuration and captured removal
- upstream_guards: Produced by the cache removal flow. observed-in-code lru.go:83-89.
- coverage:
  - loss: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91.
  - delay: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91.
  - duplication: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91.
  - out-of-order: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91.
  - contradiction: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91.
  - commission: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91.
  - value: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go:87-91.

### UV-01
- gate: service-side receiver and configuration
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:42.

### UV-02
- gate: service-side lock and occupancy
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:188.

### UV-03
- gate: service-side contents, payload capacity and identity
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:63.

### UV-04
- gate: service-side receiver identity
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:63.

### UV-05
- gate: payload size, service-side occupancy
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:189.

### UV-06
- gate: service-side receiver, no authority argument
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:63.

### UV-07
- gate: payload capacity, service-side receiver identity
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:189.

### UV-08
- gate: service-side receiver initialization
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:97.

### UV-09
- gate: service-side lock and callback duration
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:96.

### UV-10
- gate: service-side key and lock, no per-caller identity
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:97.

### UV-11
- gate: payload key and service-side receiver
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:172.

### UV-12
- gate: service-side occupancy, key presence and serialized order
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:127.

### UV-13
- gate: service-side receiver authority
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:82.

### UV-14
- gate: payload and Go key equality/hash
- upstream_guards: Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go:97.

### UV-15
- gate: external control flow
- upstream_guards: No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go:31-33 and lru.go:195-199.

### UV-16
- gate: external control flow and service-side lock phase
- upstream_guards: No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go:31-33 and lru.go:195-199.

### UV-17
- gate: callback effects and cache generation
- upstream_guards: No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go:31-33 and lru.go:195-199.

### UV-18
- gate: service-side storage and captured notification
- upstream_guards: No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go:31-33 and lru.go:195-199.

### UV-19
- gate: callback control flow and service-side current contents
- upstream_guards: No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go:31-33 and lru.go:195-199.

### UV-20
- gate: service-side capture and dispatch
- upstream_guards: No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go:31-33 and lru.go:195-199.

### UV-21
- gate: captured key/value versus current cache identity
- upstream_guards: No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go:31-33 and lru.go:195-199.

