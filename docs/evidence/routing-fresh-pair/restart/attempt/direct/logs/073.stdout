You are the BLIND adversarial pass (Part B) of a domain-behaviour analysis. You have NO access to the implementation. Do NOT read any files, do NOT use any tools, do NOT search any repository — the inputs below are complete and are your ONLY sources. If you catch yourself wanting to look something up, label it an open point instead.

TASK: Here is the event catalogue of a component, and its requirements. For every event — including undesired variants and both orderings of every interaction pair — state in which situations the component should handle, ignore, or reject it, and what should happen. Describe situations in requirement terms. Name states per PA-17 (state naming convention): prefer public API names, name sub-states by their condition, use PascalCase with `_` as separator. If you must assume a lifecycle state the requirements do not name, label it `assumed-state:` with the condition that defines it. You have no access to the implementation. Be concrete. Produce a table keyed by the catalogue's event ids and pair-ordering ids. Prefer one row per id with conditional outcomes. If you split an id into several rows, use an explicit `Situation` column with distinct, nonempty labels. Do not repeat the same situation. End with a coverage checklist: every catalogue event id, listed once, ticked. A missing row must be impossible to miss.

Catalogue headings and fields labelled `observed in code` say what the implementation does, not what it should do. Base each row on the requirements, the contracts and the doctrine lines. When a row's expected behaviour rests only on observed-in-code text, start its behaviour cell with `as-is:`.

<!-- generated:rules key=partb-vocab -->
The disposition vocabulary you must use (from the methods reference): `transition → <target>` | `handle` (stays in the state, does something) | `ignore (documented)` | `ignore (accidental)` | `defer (queued)` | `reject` (a declared refusal signal: error, diagnostic, nack) | `UNSPECIFIED`. Without these definitions a blind pass applies `reject` and `handle` to identical semantics interchangeably (dobby trigger-service, 2026-08-05: four vocabulary-only "divergences").
<!-- /generated:rules -->

The catalogue's event ids are: New Purge Resize Add Get Contains Peek ContainsOrAdd PeekOrAdd Remove RemoveOldest GetOldest Keys Values Len Cap CaptureEviction DeliverEviction CallbackReturn CallbackReenter UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 — plus the pair orderings P-01a P-01b P-02a P-02b P-03a P-03b P-04a P-04b P-05a P-05b P-06a P-06b P-07a P-07b P-08a P-08b P-09a P-09b P-10a P-10b P-11a P-11b P-12a P-12b P-13a P-13b P-14a P-14b P-15a P-15b P-16a P-16b P-17a P-17b P-18a P-18b P-19a P-19b P-20a P-20b P-21a P-21b P-22a P-22b P-23a P-23b P-24a P-24b P-25a P-25b P-26a P-26b P-27a P-27b P-28a P-28b P-29a P-29b P-30a P-30b P-31a P-31b P-32a P-32b P-33a P-33b P-34a P-34b P-35a P-35b P-36a P-36b P-37a P-37b P-38a P-38b P-39a P-39b P-40a P-40b P-41a P-41b.

=== INPUT 1: EVENT CATALOGUE (code fragments and analysis references removed) ===

# Event catalogue

<!-- event-ids: New Purge Resize Add Get Contains Peek ContainsOrAdd PeekOrAdd Remove RemoveOldest GetOldest Keys Values Len Cap CaptureEviction DeliverEviction CallbackReturn CallbackReenter UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| New | external | constructor owner | capacity and optional callback registration; observed-in-code lru.go. |
| Purge | external | lifecycle owner | clear request for a selected cache; observed-in-code lru.go. |
| Resize | external | lifecycle owner | change capacity to requested integer; observed-in-code lru.go. |
| Add | external | cache caller | key and value to insert or replace; observed-in-code lru.go. |
| Get | external | cache caller | read value with recency update; observed-in-code lru.go. |
| Contains | external | cache caller | test membership; observed-in-code lru.go. |
| Peek | external | cache caller | read without recency update; observed-in-code lru.go. |
| ContainsOrAdd | external | cache caller | test membership or insert key/value; observed-in-code lru.go. |
| PeekOrAdd | external | cache caller | read or insert key/value; observed-in-code lru.go. |
| Remove | external | cache caller | remove selected key; observed-in-code lru.go. |
| RemoveOldest | external | cache caller | remove oldest entry; observed-in-code lru.go. |
| GetOldest | external | cache caller | read oldest entry; observed-in-code lru.go. |
| Keys | external | cache caller | snapshot keys; observed-in-code lru.go. |
| Values | external | cache caller | snapshot values; observed-in-code lru.go. |
| Len | external | cache caller | read entry count; observed-in-code lru.go. |
| Cap | external | cache caller | read configured capacity; observed-in-code lru.go. |
| CaptureEviction | internal | simplelru (internal) | capture key and value from simplelru; observed-in-code lru.go. |
| DeliverEviction | internal | cache invocation (internal) | invoke the registered callback with a captured key and value; observed-in-code lru.go. |
| CallbackReturn | external | injected callback | registered function returns control to its invoking cache method; observed-in-code lru.go. |
| CallbackReenter | external | injected callback | registered function invokes cache API before returning; observed-in-code lru.go. |
| UV-01 | external | constructor owner | constructor omitted or delayed; use before successful publication, including the pointer returned with an error; observed boundary lru.go. |
| UV-02 | external | constructor owner | constructor receives zero, negative, or valid but unintended positive size; a duplicate constructor creates another instance; observed boundary lru.go. |
| UV-03 | external | lifecycle owner | Purge omitted/delayed or executed twice; a stale Purge can act after repopulation; observed boundary lru.go. |
| UV-04 | external | lifecycle owner | Resize zero or negative, extreme signed size or valid but unintended positive size; duplicate Resize and competing different sizes; observed boundary lru.go. |
| UV-05 | external | cache caller | caller omits operation, loses interest while waiting, or invokes later using a stale key, value or decision; observed boundary lru.go. |
| UV-06 | external | cache caller | same caller issues a second Get while first is pending or while retaining first value; repeated conditional adds, Add or Remove; observed boundary lru.go. |
| UV-07 | external | cache caller | wrong receiver, distinct from plausible wrong key/value or stale generation on intended receiver; contradictory same-key operations; observed boundary lru.go. |
| UV-08 | external | cache caller | non-reflexive comparable key such as NaN; observed boundary lru.go. |
| UV-09 | external | cache caller | interface key with non-comparable dynamic value; observed boundary lru.go. |
| UV-10 | external | injected callback | callback panics or terminates its goroutine before returning; callback waits indefinitely or returns late; observed boundary lru.go. |
| UV-11 | external | injected callback | concurrent callbacks can overlap; callback performs duplicate or stale nested work; contradictory nested writes or wrong receiver/payload; observed boundary lru.go. |
| UV-12 | external | injected callback | late or aborting callback on either side of Purge or Resize, including captured batch tail; observed boundary lru.go. |

## Undesired-coverage (observed in code, not documented intent)

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| New: constructor owner | UV-01 | UV-01 | UV-02 | UV-01 | UV-02 | n/a: synchronous direct invocation from lru.go. | UV-02 |
| Purge: lifecycle owner | UV-03 | UV-03 | UV-03, UV-04 | UV-03, UV-04 | UV-03, UV-04 | n/a: synchronous direct invocation from lru.go. | UV-04 |
| Resize: lifecycle owner | UV-03 | UV-03 | UV-03, UV-04 | UV-03, UV-04 | UV-03, UV-04 | n/a: synchronous direct invocation from lru.go. | UV-04 |
| Add: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go. | UV-07, UV-08, UV-09 |
| Get: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go. | UV-07, UV-08, UV-09 |
| Contains: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go. | UV-07, UV-08, UV-09 |
| Peek: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go. | UV-07, UV-08, UV-09 |
| ContainsOrAdd: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go. | UV-07, UV-08, UV-09 |
| PeekOrAdd: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go. | UV-07, UV-08, UV-09 |
| Remove: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go. | UV-07, UV-08, UV-09 |
| RemoveOldest: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go. | UV-07, UV-08, UV-09 |
| GetOldest: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go. | UV-07, UV-08, UV-09 |
| Keys: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go. | UV-07, UV-08, UV-09 |
| Values: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go. | UV-07, UV-08, UV-09 |
| Len: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go. | UV-07, UV-08, UV-09 |
| Cap: cache caller | UV-05 | UV-05 | UV-06 | UV-05, UV-07 | UV-07 | n/a: synchronous direct invocation from lru.go. | UV-07, UV-08, UV-09 |
| CaptureEviction: simplelru (internal) | n/a: synchronous direct invocation from lru.go. | n/a: synchronous direct invocation from lru.go. | UV-08 | n/a: synchronous direct invocation from lru.go. | n/a: synchronous direct invocation from lru.go. | n/a: synchronous direct invocation from lru.go. | n/a: synchronous direct invocation from lru.go. |
| DeliverEviction: cache invocation (internal) | UV-10, UV-12 | UV-10, UV-12 | UV-08, UV-11 | UV-10, UV-12 | UV-10, UV-12 | n/a: synchronous direct invocation from lru.go. | n/a: synchronous direct invocation from lru.go. |
| CallbackReturn: injected callback | UV-10 | UV-10, UV-12 | UV-11 | UV-11, UV-12 | UV-11 | n/a: synchronous direct invocation from lru.go. | UV-11 |
| CallbackReenter: injected callback | UV-10 | UV-10, UV-12 | UV-11 | UV-11, UV-12 | UV-11 | n/a: synchronous direct invocation from lru.go. | UV-11 |

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

## Remembrance semantics (observed in code, not documented intent)

No tombstones for reflexive keys; ring count decrements at internal/list.go, resets at internal/list.go, links clear at internal/list.go, map delete at simplelru/lru.go. Non-reflexive keys use Go equality at simplelru/lru.go and simplelru/lru.go. Single-callback slices truncate at lru.go without clearing backing slots; batch paths replace the buffers at lru.go and lru.go. Initial capacity is sixteen (lru.go and lru.go); batch append can grow at lru.go and lru.go; retention cost unmeasured. Capture is owned by the initiating call.

## Lock-discipline annotation (observed in code, not documented intent)

Writer sites: lru.go; lru.go; lru.go; lru.go; lru.go; lru.go; lru.go; lru.go. Reader sites: lru.go; lru.go; lru.go; lru.go; lru.go; lru.go. Cap observation lru.go. Internal adapter captures under writer lock at lru.go and lru.go. Public release and callback sites: lru.go and lru.go; lru.go and lru.go; lru.go and lru.go; lru.go and lru.go; lru.go and lru.go; lru.go and lru.go; lru.go and lru.go. Registration contract lru.go; no stated reentrancy, order or failure guarantee.

## Catalogue notes

Owner and caller describe roles; pair classes include equivalent variants through context. Replacement publication belongs to owner wiring. Same-role concurrent callers are covered in free traces.

## Event annotations (observed in code, not documented intent)

### New
- gate (observed in code): payload: requested capacity and callback presence
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-01
  - delay: UV-01
  - duplication: UV-02
  - out-of-order: UV-01
  - contradiction: UV-02
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-02

### Purge
- gate (observed in code): service: entries and callback registration
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-03
  - delay: UV-03
  - duplication: UV-03, UV-04
  - out-of-order: UV-03, UV-04
  - contradiction: UV-03, UV-04
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-04

### Resize
- gate (observed in code): payload and service: requested size and current length
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-03
  - delay: UV-03
  - duplication: UV-03, UV-04
  - out-of-order: UV-03, UV-04
  - contradiction: UV-03, UV-04
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-04

### Add
- gate (observed in code): payload and service: key membership, length, capacity and callback registration
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-07, UV-08, UV-09

### Get
- gate (observed in code): payload and service: key membership
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-07, UV-08, UV-09

### Contains
- gate (observed in code): payload and service: key membership
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-07, UV-08, UV-09

### Peek
- gate (observed in code): payload and service: key membership
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-07, UV-08, UV-09

### ContainsOrAdd
- gate (observed in code): payload and service: membership, length, capacity and callback registration
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-07, UV-08, UV-09

### PeekOrAdd
- gate (observed in code): payload and service: membership, length, capacity and callback registration
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-07, UV-08, UV-09

### Remove
- gate (observed in code): payload and service: membership and callback registration
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-07, UV-08, UV-09

### RemoveOldest
- gate (observed in code): service: length and callback registration
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-07, UV-08, UV-09

### GetOldest
- gate (observed in code): service: length
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-07, UV-08, UV-09

### Keys
- gate (observed in code): service: list contents
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-07, UV-08, UV-09

### Values
- gate (observed in code): service: list contents
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-07, UV-08, UV-09

### Len
- gate (observed in code): service: list length
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-07, UV-08, UV-09

### Cap
- gate (observed in code): service: capacity
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05, UV-07
  - contradiction: UV-07
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-07, UV-08, UV-09

### CaptureEviction
- gate (observed in code): service: registered adapter and removal path
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: n/a: synchronous direct invocation from lru.go.
  - delay: n/a: synchronous direct invocation from lru.go.
  - duplication: UV-08
  - out-of-order: n/a: synchronous direct invocation from lru.go.
  - contradiction: n/a: synchronous direct invocation from lru.go.
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: n/a: synchronous direct invocation from lru.go.

### DeliverEviction
- gate (observed in code): service: registered callback and captured work
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-10, UV-12
  - delay: UV-10, UV-12
  - duplication: UV-08, UV-11
  - out-of-order: UV-10, UV-12
  - contradiction: UV-10, UV-12
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: n/a: synchronous direct invocation from lru.go.

### CallbackReturn
- gate (observed in code): service: active invocation and remaining batch
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-10
  - delay: UV-10, UV-12
  - duplication: UV-11
  - out-of-order: UV-11, UV-12
  - contradiction: UV-11
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-11

### CallbackReenter
- gate (observed in code): payload and service: nested operation, receiver, active outer invocation
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.
- coverage:
  - loss: UV-10
  - delay: UV-10, UV-12
  - duplication: UV-11
  - out-of-order: UV-11, UV-12
  - contradiction: UV-11
  - commission: n/a: synchronous direct invocation from lru.go.
  - value: UV-11

### UV-01
- gate (observed in code): payload or service state depending on the concrete variant above
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.

### UV-02
- gate (observed in code): payload or service state depending on the concrete variant above
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.

### UV-03
- gate (observed in code): payload or service state depending on the concrete variant above
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.

### UV-04
- gate (observed in code): payload or service state depending on the concrete variant above
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.

### UV-05
- gate (observed in code): payload or service state depending on the concrete variant above
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.

### UV-06
- gate (observed in code): payload or service state depending on the concrete variant above
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.

### UV-07
- gate (observed in code): payload or service state depending on the concrete variant above
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.

### UV-08
- gate (observed in code): payload or service state depending on the concrete variant above
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.

### UV-09
- gate (observed in code): payload or service state depending on the concrete variant above
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.

### UV-10
- gate (observed in code): payload or service state depending on the concrete variant above
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.

### UV-11
- gate (observed in code): payload or service state depending on the concrete variant above
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.

### UV-12
- gate (observed in code): payload or service state depending on the concrete variant above
- upstream_guards (observed in code): No application guard supplied; local boundary lru.go.



=== INPUT 2b: DOCTRINE LINES (from the extraction) ===

- DOC-1 [explicit-requirement] README.md: fixed-size.
- DOC-2 [explicit-requirement] README.md: thread safe LRU cache.
- DOC-3 [explicit-requirement] README.md: LRU cache.
- DOC-4 [explicit-requirement] README.md: sequential example: 256 distinct adds to size 128 leave 128 entries.
- DOC-5 [explicit-requirement] doc.go: All caches in this package take locks while operating, and are therefore thread-safe for consumers..
- DOC-6 [explicit-requirement] README.md: expiration example is for the expirable cache.
- DOC-7 [explicit-requirement] lru.go: Cache is a thread-safe fixed size LRU cache..
- DOC-8 [explicit-requirement] lru.go: New creates an LRU of the given size..
- DOC-9 [explicit-requirement] lru.go: Constructs a fixed size cache with the given eviction callback..
- DOC-10 [explicit-requirement] lru.go: Purge is used to completely clear the cache..
- DOC-11 [explicit-requirement] lru.go: Add adds a value to the cache. Returns true if an eviction occurred..
- DOC-12 [explicit-requirement] lru.go: Get looks up a key's value from the cache..
- DOC-13 [explicit-requirement] lru.go: Contains checks if a key is in the cache, without updating the recent-ness or deleting it for being stale..
- DOC-14 [explicit-requirement] lru.go: Peek returns the key value without updating the recently used-ness of the key..
- DOC-15 [explicit-requirement] lru.go: ContainsOrAdd tests without touching recency on hit; otherwise adds and returns found/eviction flags..
- DOC-16 [explicit-requirement] lru.go: PeekOrAdd tests without touching recency on hit; otherwise adds and returns value/found/eviction..
- DOC-17 [explicit-requirement] lru.go: Remove removes the provided key from the cache..
- DOC-18 [explicit-requirement] lru.go: Resize changes the cache size..
- DOC-19 [explicit-requirement] lru.go: RemoveOldest removes the oldest item from the cache..
- DOC-20 [explicit-requirement] lru.go: GetOldest returns the oldest entry.
- DOC-21 [explicit-requirement] lru.go: Keys returns a slice of the keys in the cache, from oldest to newest..
- DOC-22 [explicit-requirement] lru.go: Values returns a slice of the values in the cache, from oldest to newest..
- DOC-23 [explicit-requirement] lru.go: Len returns the number of items in the cache..
- DOC-24 [explicit-requirement] lru.go: Cap returns the capacity of the cache.
- DOC-25 [explicit-requirement] simplelru/lru_interface.go: Add eviction flag and recency update.
- DOC-26 [explicit-requirement] simplelru/lru_interface.go: Get returns value/found and updates recency.
- DOC-27 [explicit-requirement] simplelru/lru_interface.go: Contains does not update recency.
- DOC-28 [explicit-requirement] simplelru/lru_interface.go: Peek does not update recency.
- DOC-29 [explicit-requirement] simplelru/lru_interface.go: Remove key and RemoveOldest.
- DOC-30 [explicit-requirement] simplelru/lru_interface.go: GetOldest and oldest-to-newest snapshots.
- DOC-31 [explicit-requirement] simplelru/lru_interface.go: Len and Cap projections.
- DOC-32 [explicit-requirement] simplelru/lru_interface.go: Clears all cache entries..
- DOC-33 [explicit-requirement] simplelru/lru_interface.go: Resizes cache, returning number evicted.

=== INPUT 2: REQUIREMENTS (domain-analysis/lruCache/requirements-prose.md) ===

golang-lru
==========

This provides the `lru` package which implements a fixed-size
thread safe LRU cache. It is based on the cache in Groupcache.

Documentation
=============

Full docs are available on [Go Packages](https://pkg.go.dev/github.com/hashicorp/golang-lru/v2)


=== INPUT 3: EVENT CONTRACT TEXTS (domain-analysis/lruCache/contracts.txt) ===

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

doc.go:22
All caches in this package take locks while operating, and are therefore
thread-safe for consumers.

simplelru/lru.go:12
EvictCallback is used to get a callback when a cache entry is evicted

simplelru/lru.go:23
NewLRU constructs an LRU of the given size

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


Respond with ONLY the table and the coverage checklist: every catalogue event and pair-ordering id, listed once in the checklist, ticked. A missing row must be impossible to miss.
The coverage checklist must use one exact line per event or pair in the form '- [x] EVENT_ID', with no other text on that line.
