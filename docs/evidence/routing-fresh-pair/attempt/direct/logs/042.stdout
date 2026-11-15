You are the BLIND adversarial pass (Part B) of a domain-behaviour analysis. You have NO access to the implementation. Do NOT read any files, do NOT use any tools, do NOT search any repository — the inputs below are complete and are your ONLY sources. If you catch yourself wanting to look something up, label it an open point instead.

TASK: Here is the event catalogue of a component, and its requirements. For every event — including undesired variants and both orderings of every interaction pair — state in which situations the component should handle, ignore, or reject it, and what should happen. Describe situations in requirement terms. Name states per PA-17 (state naming convention): prefer public API names, name sub-states by their condition, use PascalCase with `_` as separator. If you must assume a lifecycle state the requirements do not name, label it `assumed-state:` with the condition that defines it. You have no access to the implementation. Be concrete. Produce a table keyed by the catalogue's event ids and pair-ordering ids. Prefer one row per id with conditional outcomes. If you split an id into several rows, use an explicit `Situation` column with distinct, nonempty labels. Do not repeat the same situation. End with a coverage checklist: every catalogue event id, listed once, ticked. A missing row must be impossible to miss.

Catalogue headings and fields labelled `observed in code` say what the implementation does, not what it should do. Base each row on the requirements, the contracts and the doctrine lines. When a row's expected behaviour rests only on observed-in-code text, start its behaviour cell with `as-is:`.

<!-- generated:rules key=partb-vocab -->
The disposition vocabulary you must use (from the methods reference): `transition → <target>` | `handle` (stays in the state, does something) | `ignore (documented)` | `ignore (accidental)` | `defer (queued)` | `reject` (a declared refusal signal: error, diagnostic, nack) | `UNSPECIFIED`. Without these definitions a blind pass applies `reject` and `handle` to identical semantics interchangeably (dobby trigger-service, 2026-08-05: four vocabulary-only "divergences").
<!-- /generated:rules -->

The catalogue's event ids are: New Purge Resize Add Get Contains Peek ContainsOrAdd PeekOrAdd Remove RemoveOldest GetOldest Keys Values Len Cap CallbackOutcome EvictionCaptured CallbackDispatch UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 UV-15 UV-16 UV-17 UV-18 UV-19 UV-20 UV-21 — plus the pair orderings P-01a P-01b P-02a P-02b P-03a P-03b P-04a P-04b P-05a P-05b P-06a P-06b P-07a P-07b P-08a P-08b P-09a P-09b P-10a P-10b P-11a P-11b P-12a P-12b P-13a P-13b P-14a P-14b P-15a P-15b P-16a P-16b P-17a P-17b P-18a P-18b P-19a P-19b P-20a P-20b P-21a P-21b P-22a P-22b P-23a P-23b P-24a P-24b P-25a P-25b P-26a P-26b P-27a P-27b P-28a P-28b P-29a P-29b P-30a P-30b P-31a P-31b P-32a P-32b P-33a P-33b P-34a P-34b P-35a P-35b P-36a P-36b P-37a P-37b P-38a P-38b P-39a P-39b P-40a P-40b P-41a P-41b.

=== INPUT 1: EVENT CATALOGUE (code fragments and analysis references removed) ===

# Event catalogue

<!-- event-ids: New Purge Resize Add Get Contains Peek ContainsOrAdd PeekOrAdd Remove RemoveOldest GetOldest Keys Values Len Cap CallbackOutcome EvictionCaptured CallbackDispatch UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 UV-15 UV-16 UV-17 UV-18 UV-19 UV-20 UV-21 -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| New | external | Lifecycle owner | Construct an independent cache with a capacity and optional eviction callback. observed-in-code lru.go. |
| Purge | external | Lifecycle owner | Clear the cache. observed-in-code lru.go. |
| Resize | external | Lifecycle owner | Change capacity and report number evicted. observed-in-code lru.go. |
| Add | external | API caller | Add or replace key/value, report eviction. observed-in-code lru.go. |
| Get | external | API caller | Find a key's value. observed-in-code lru.go. |
| Contains | external | API caller | Check key presence without refreshing recency. observed-in-code lru.go. |
| Peek | external | API caller | Read value without refreshing recency. observed-in-code lru.go. |
| ContainsOrAdd | external | API caller | Check presence and insert if absent. observed-in-code lru.go. |
| PeekOrAdd | external | API caller | Read an existing value or insert if absent. observed-in-code lru.go. |
| Remove | external | API caller | Remove a key. observed-in-code lru.go. |
| RemoveOldest | external | API caller | Remove the oldest entry. observed-in-code lru.go. |
| GetOldest | external | API caller | Read the oldest entry. observed-in-code lru.go. |
| Keys | external | API caller | Return a slice of keys. observed-in-code lru.go. |
| Values | external | API caller | Return a slice of values. observed-in-code lru.go. |
| Len | external | API caller | Read entry count. observed-in-code lru.go. |
| Cap | external | API caller | Read capacity. observed-in-code lru.go. |
| CallbackOutcome | external | Injected callback | User callback returns, blocks, or exits abnormally. observed-in-code lru.go. |
| EvictionCaptured | internal | Internal LRU | Record an evicted key/value. observed-in-code lru.go. |
| CallbackDispatch | internal | Cache operation | Invoke registered eviction callback with removed key and value. observed-in-code lru.go. |
| UV-01 | external | Lifecycle owner | Owner omits initialization, purge or capacity adjustment. Boundary observed-in-code lru.go. |
| UV-02 | external | Lifecycle owner | Owner delays purge or resize while calls continue. Boundary observed-in-code lru.go. |
| UV-03 | external | Lifecycle owner | Repeat purge or resize, or construct a second instance. Boundary observed-in-code lru.go. |
| UV-04 | external | Lifecycle owner | Purge or resize arrives after owner abandons a reference or crosses a receiver replacement. Boundary observed-in-code lru.go. |
| UV-05 | external | Lifecycle owner | Concurrent conflicting resize targets or purge and resize. Boundary observed-in-code lru.go. |
| UV-06 | external | Lifecycle owner | Unsolicited purge or resize through a retained cache reference. Boundary observed-in-code lru.go. |
| UV-07 | external | Lifecycle owner | Valid unintended capacity, zero, negative, extreme or wrong receiver configuration. Boundary observed-in-code lru.go. |
| UV-08 | external | API caller | Caller omits a call, uses nil or an unsuccessfully initialized receiver. Boundary observed-in-code lru.go. |
| UV-09 | external | API caller | Caller delayed at cache entry or abandons the wait in an outer wrapper. Boundary observed-in-code lru.go. |
| UV-10 | external | API caller | Repeat a request including a second Get from the same caller while its first is pending or while its first result is still held. Boundary observed-in-code lru.go. |
| UV-11 | external | API caller | Stale action for a reused key, delayed call after purge, or a request routed to the wrong instance. Boundary observed-in-code lru.go. |
| UV-12 | external | API caller | Concurrent same-key writes, conditional adds, read versus eviction, or removal versus reinsertion. Boundary observed-in-code lru.go. |
| UV-13 | external | API caller | Unsolicited but well-typed call by another holder of the receiver. Boundary observed-in-code lru.go. |
| UV-14 | external | API caller | Foreign but well-formed key or value, non-reflexive key, or dynamically unhashable interface key. Boundary observed-in-code lru.go. |
| UV-15 | external | Injected callback | Callback panics or exits its goroutine before completing a notification. Boundary observed-in-code lru.go. |
| UV-16 | external | Injected callback | Callback stalls while other operations or purge continue. Boundary observed-in-code lru.go. |
| UV-17 | external | Injected callback | Repeated application side effects from distinct evictions of reused keys or caller re-entry. Boundary observed-in-code lru.go. |
| UV-18 | external | Injected callback | Notification runs across purge or reinsertion, including success or failure before or after purge. Boundary observed-in-code lru.go. |
| UV-19 | external | Injected callback | Concurrent callbacks or conflicting callback re-entry. Boundary observed-in-code lru.go. |
| UV-20 | external | Injected callback | Callback invocation with no matching removal. Boundary observed-in-code lru.go. |
| UV-21 | external | Injected callback | Callback observes a stale payload generation, or sends that key to a different cache. Boundary observed-in-code lru.go. |

## Undesired-coverage (observed in code, not documented intent)

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
| EvictionCaptured: Internal LRU | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go. | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go. | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go. | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go. | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go. | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go. | n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go. |
| CallbackDispatch: Cache operation | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go. | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go. | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go. | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go. | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go. | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go. | n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go. |

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

## Remembrance semantics (observed in code, not documented intent)

observed-in-code: list removal detaches links and decrements length (internal/list.go), then the map key is deleted (simplelru/lru.go). Purge deletes map keys and resets the list length (simplelru/lru.go, internal/list.go). Len counts list nodes (simplelru/lru.go), independently of capacity (simplelru/lru.go). With non-reflexive keys map deletion can fail. Single notifications reslice without clearing backing slots (lru.go and lru.go). Bulk paths detach the captured slices and allocate new buffers, then invoke user callbacks (lru.go and lru.go). Scratch starts at 16 slots per slice (lru.go and lru.go), can grow with a batch (lru.go) and has no time-based clearing. A delayed callback has the captured payload, may see a later generation, and is independent of list length. Measured heap retention is open.

## Lock-discipline annotation (observed in code, not documented intent)

observed-in-code: Purge, Add, ContainsOrAdd, PeekOrAdd, Remove, Resize and RemoveOldest call the private capture hook inside the writer lock and invoke user callbacks after release (lru.go and lru.go). Get takes the writer lock to promote recency (lru.go, simplelru/lru.go). Contains, Peek, GetOldest, Keys, Values and Len use read locks and call no user code (lru.go and lru.go). Cap has no lock (lru.go). User re-entry runs after unlock in every dispatch branch. The callback contract is silent on re-entry, concurrency and panic (lru.go and simplelru/lru.go).

## Catalogue notes

Constructor calls create independent instances. A request reaches a particular cache by its receiver. Pairs model shared cache state or outputs with distinct actors. CallbackOutcome is the user code's outcome and CallbackDispatch is the cache's internal action. Two caller goroutines can also interleave within the API caller source.

## Event annotations (observed in code, not documented intent)

### New
- gate (observed in code): payload capacity and callback presence
- upstream_guards (observed in code): Calls simplelru constructor with supplied size. Its constructor enforces positive size. observed-in-code simplelru/lru.go.
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-04
  - contradiction: UV-05
  - commission: UV-06
  - value: UV-07

### Purge
- gate (observed in code): service-side contents and callback presence
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-04
  - contradiction: UV-05
  - commission: UV-06
  - value: UV-07

### Resize
- gate (observed in code): payload capacity and service-side entry count and callback presence
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-04
  - contradiction: UV-05
  - commission: UV-06
  - value: UV-07

### Add
- gate (observed in code): service-side key presence and occupancy, payload key and value
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Get
- gate (observed in code): service-side key presence, payload key
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Contains
- gate (observed in code): service-side key presence, payload key
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Peek
- gate (observed in code): service-side key presence, payload key
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### ContainsOrAdd
- gate (observed in code): service-side key presence and occupancy, payload key and value
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### PeekOrAdd
- gate (observed in code): service-side key presence and occupancy, payload key and value
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Remove
- gate (observed in code): service-side key presence and callback presence, payload key
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### RemoveOldest
- gate (observed in code): service-side occupancy and callback presence
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### GetOldest
- gate (observed in code): service-side occupancy
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Keys
- gate (observed in code): service-side occupancy and recency
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Values
- gate (observed in code): service-side occupancy and recency
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Len
- gate (observed in code): service-side entry count
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### Cap
- gate (observed in code): service-side capacity
- upstream_guards (observed in code): Direct Go method call. No upstream wrapper at this boundary. No caller identity or generation field. observed-in-code lru.go.
- coverage:
  - loss: UV-08
  - delay: UV-09
  - duplication: UV-10
  - out-of-order: UV-11
  - contradiction: UV-12
  - commission: UV-13
  - value: UV-14

### CallbackOutcome
- gate (observed in code): callback control flow and invocation context
- upstream_guards (observed in code): User function has no error return or stated recovery, timing or re-entry guarantee. observed-in-code lru.go.
- coverage:
  - loss: UV-15
  - delay: UV-16
  - duplication: UV-17
  - out-of-order: UV-18
  - contradiction: UV-19
  - commission: UV-20
  - value: UV-21

### EvictionCaptured
- gate (observed in code): service-side removal and callback configuration
- upstream_guards (observed in code): Produced by the cache removal flow. observed-in-code lru.go.
- coverage:
  - loss: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go.
  - delay: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go.
  - duplication: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go.
  - out-of-order: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go.
  - contradiction: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go.
  - commission: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go.
  - value: n/a: synchronous internal append has no independent producer. observed-in-code simplelru/lru.go and lru.go.

### CallbackDispatch
- gate (observed in code): service-side callback configuration and captured removal
- upstream_guards (observed in code): Produced by the cache removal flow. observed-in-code lru.go.
- coverage:
  - loss: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go.
  - delay: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go.
  - duplication: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go.
  - out-of-order: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go.
  - contradiction: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go.
  - commission: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go.
  - value: n/a: direct dispatch occurs on the initiating call stack. User outcome has its own coverage. observed-in-code lru.go.

### UV-01
- gate (observed in code): service-side receiver and configuration
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-02
- gate (observed in code): service-side lock and occupancy
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-03
- gate (observed in code): service-side contents, payload capacity and identity
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-04
- gate (observed in code): service-side receiver identity
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-05
- gate (observed in code): payload size, service-side occupancy
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-06
- gate (observed in code): service-side receiver, no authority argument
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-07
- gate (observed in code): payload capacity, service-side receiver identity
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-08
- gate (observed in code): service-side receiver initialization
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-09
- gate (observed in code): service-side lock and callback duration
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-10
- gate (observed in code): service-side key and lock, no per-caller identity
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-11
- gate (observed in code): payload key and service-side receiver
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-12
- gate (observed in code): service-side occupancy, key presence and serialized order
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-13
- gate (observed in code): service-side receiver authority
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-14
- gate (observed in code): payload and Go key equality/hash
- upstream_guards (observed in code): Public Go calls accept supplied receiver and arguments. No upstream admission or identity service. observed-in-code lru.go.

### UV-15
- gate (observed in code): external control flow
- upstream_guards (observed in code): No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go and lru.go.

### UV-16
- gate (observed in code): external control flow and service-side lock phase
- upstream_guards (observed in code): No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go and lru.go.

### UV-17
- gate (observed in code): callback effects and cache generation
- upstream_guards (observed in code): No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go and lru.go.

### UV-18
- gate (observed in code): service-side storage and captured notification
- upstream_guards (observed in code): No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go and lru.go.

### UV-19
- gate (observed in code): callback control flow and service-side current contents
- upstream_guards (observed in code): No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go and lru.go.

### UV-20
- gate (observed in code): service-side capture and dispatch
- upstream_guards (observed in code): No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go and lru.go.

### UV-21
- gate (observed in code): captured key/value versus current cache identity
- upstream_guards (observed in code): No documented ordering, re-entry, timeout or panic policy. observed-in-code lru.go and lru.go.



=== INPUT 2b: DOCTRINE LINES (from the extraction) ===

- DOC-1 explicit-requirement README.md ("This provides the `lru` package which implements a fixed-size") continued by "thread safe LRU cache. It is based on the cache in Groupcache." Fixed-size clause.
- DOC-2 explicit-requirement README.md ("thread safe LRU cache. It is based on the cache in Groupcache."). Thread-safety clause.
- DOC-3 explicit-requirement README.md ("This provides the `lru` package which implements a fixed-size"). LRU clause, scoped to normal access and eviction.
- DOC-4 observed-in-code API documentation doc.go. The preceding line claims all caches take locks while operating.
- DOC-5 observed-in-code API documentation simplelru/lru.go. Constructor size is subject to its positive-size check.

=== INPUT 2: REQUIREMENTS (domain-analysis/lruCache/blind-requirements.md) ===

golang-lru
==========

This provides the `lru` package which implements a fixed-size
thread safe LRU cache. It is based on the cache in Groupcache.

Documentation
=============

Full docs are available on [Go Packages](https://pkg.go.dev/github.com/hashicorp/golang-lru/v2)


=== INPUT 3: EVENT CONTRACT TEXTS (domain-analysis/lruCache/blind-contracts.txt) ===

lru.go:17
Cache is a thread-safe fixed size LRU cache.

lru.go:26
New creates an LRU of the given size.

lru.go:31
NewWithEvict constructs a fixed size cache with the given eviction
callback.

lru.go:58
Purge is used to completely clear the cache.

lru.go:77
Add adds a value to the cache. Returns true if an eviction occurred.

lru.go:94
Get looks up a key's value from the cache.

lru.go:102
Contains checks if a key is in the cache, without updating the
recent-ness or deleting it for being stale.

lru.go:111
Peek returns the key value (or undefined if not found) without updating
the "recently used"-ness of the key.

lru.go:120
ContainsOrAdd checks if a key is in the cache without updating the
recent-ness or deleting it for being stale, and if not, adds the value.
Returns whether found and whether an eviction occurred.

lru.go:143
PeekOrAdd checks if a key is in the cache without updating the
recent-ness or deleting it for being stale, and if not, adds the value.
Returns whether found and whether an eviction occurred.

lru.go:167
Remove removes the provided key from the cache.

lru.go:184
Resize changes the cache size.

lru.go:203
RemoveOldest removes the oldest item from the cache.

lru.go:220
GetOldest returns the oldest entry

lru.go:228
Keys returns a slice of the keys in the cache, from oldest to newest.

lru.go:236
Values returns a slice of the values in the cache, from oldest to newest.

lru.go:244
Len returns the number of items in the cache.

lru.go:252
Cap returns the capacity of the cache

simplelru/lru.go:12
EvictCallback is used to get a callback when a cache entry is evicted

simplelru/lru.go:23
NewLRU constructs an LRU of the given size

simplelru/lru.go:96
Remove removes the provided key from the cache, returning if the
key was contained.

simplelru/lru_interface.go:9
Adds a value to the cache, returns true if an eviction occurred and
updates the "recently used"-ness of the key.

simplelru/lru_interface.go:13
Returns key's value from the cache and
updates the "recently used"-ness of the key. #value, isFound

simplelru/lru_interface.go:17
Checks if a key exists in cache without updating the recent-ness.

simplelru/lru_interface.go:20
Returns key's value without updating the "recently used"-ness of the key.

simplelru/lru_interface.go:23
Removes a key from the cache.

simplelru/lru_interface.go:26
Removes the oldest entry from cache.

simplelru/lru_interface.go:29
Returns the oldest entry from the cache. #key, value, isFound

simplelru/lru_interface.go:32
Returns a slice of the keys in the cache, from oldest to newest.

simplelru/lru_interface.go:35
Values returns a slice of the values in the cache, from oldest to newest.

simplelru/lru_interface.go:38
Returns the number of items in the cache.

simplelru/lru_interface.go:41
Returns the capacity of the cache.

simplelru/lru_interface.go:44
Clears all cache entries.

simplelru/lru_interface.go:47
Resizes cache, returning number evicted

internal/list.go:42
LruList represents a doubly linked list.
The zero Value for LruList is an empty list ready to use.

internal/list.go:49
Init initializes or clears list l.

internal/list.go:57
NewList returns an initialized list.

internal/list.go:60
Length returns the number of elements of list l.
The complexity is O(1).

internal/list.go:64
Back returns the last element of list l or nil if the list is empty.

internal/list.go:95
Remove removes e from its list, decrements l.len

internal/list.go:121
PushFront inserts a new element e with value v at the front of list l and returns e.

internal/list.go:133
MoveToFront moves element e to the front of list l.
If e is not an element of l, the list is not modified.
The element must not be nil.


Respond with ONLY the table and the coverage checklist: every catalogue event and pair-ordering id, listed once in the checklist, ticked. A missing row must be impossible to miss.
The coverage checklist must use one exact line per event or pair in the form '- [x] EVENT_ID', with no other text on that line.
