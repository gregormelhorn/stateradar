You are the BLIND adversarial pass (Part B) of a domain-behaviour analysis. You have NO access to the implementation. Do NOT read any files, do NOT use any tools, do NOT search any repository — the inputs below are complete and are your ONLY sources. If you catch yourself wanting to look something up, label it an open point instead.

TASK: Here is the event catalogue of a component, and its requirements. For every event — including undesired variants and both orderings of every interaction pair — state in which situations the component should handle, ignore, or reject it, and what should happen. Describe situations in requirement terms. Name states per PA-17 (state naming convention): prefer public API names, name sub-states by their condition, use PascalCase with `_` as separator. If you must assume a lifecycle state the requirements do not name, label it `assumed-state:` with the condition that defines it. You have no access to the implementation. Be concrete. Produce a table keyed by the catalogue's event ids and pair-ordering ids. Prefer one row per id with conditional outcomes. If you split an id into several rows, use an explicit `Situation` column with distinct, nonempty labels. Do not repeat the same situation. End with a coverage checklist: every catalogue event id, listed once, ticked. A missing row must be impossible to miss.

Catalogue headings and fields labelled `observed in code` say what the implementation does, not what it should do. Base each row on the requirements, the contracts and the doctrine lines. When a row's expected behaviour rests only on observed-in-code text, start its behaviour cell with `as-is:`.

<!-- generated:rules key=partb-vocab -->
The disposition vocabulary you must use (from the methods reference): `transition → <target>` | `handle` (stays in the state, does something) | `ignore (documented)` | `ignore (accidental)` | `defer (queued)` | `reject` (a declared refusal signal: error, diagnostic, nack) | `UNSPECIFIED`. Without these definitions a blind pass applies `reject` and `handle` to identical semantics interchangeably (dobby trigger-service, 2026-08-05: four vocabulary-only "divergences").
<!-- /generated:rules -->

The catalogue's event ids are: New Get Put Close Release Len DirectPing FactoryResult CloseResult PingResult IdleAge WaitDelivery DrainDone UV-NewOmitted UV-NewRepeated UV-BadConfig UV-GetOmitted UV-GetAgain UV-AbandonGet UV-LateGet UV-ContendedGet UV-WrongPoolGet UV-ReturnMissing UV-LatePut UV-LateClose UV-BadOwnership UV-WrongPoolPut UV-ReleaseOmitted UV-ReleaseAgain UV-WrongPoolRelease UV-LateRead UV-FactoryFault UV-CloseFault UV-PingFault UV-CallbackDelay — plus the pair orderings P-01a P-01b P-02a P-02b P-03a P-03b P-04a P-04b P-05a P-05b P-06a P-06b P-07a P-07b P-08a P-08b P-09a P-09b P-10a P-10b P-11a P-11b P-12a P-12b P-13a P-13b P-14a P-14b P-15a P-15b P-16a P-16b.

=== INPUT 1: EVENT CATALOGUE (code fragments and analysis references removed) ===

# Event catalogue

<!-- event-ids: New Get Put Close Release Len DirectPing FactoryResult CloseResult PingResult IdleAge WaitDelivery DrainDone UV-NewOmitted UV-NewRepeated UV-BadConfig UV-GetOmitted UV-GetAgain UV-AbandonGet UV-LateGet UV-ContendedGet UV-WrongPoolGet UV-ReturnMissing UV-LatePut UV-LateClose UV-BadOwnership UV-WrongPoolPut UV-ReleaseOmitted UV-ReleaseAgain UV-WrongPoolRelease UV-LateRead UV-FactoryFault UV-CloseFault UV-PingFault UV-CallbackDelay -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| New | external | configuration caller | Create a pool from capacities, time limit and callbacks. Constructor entry observed in code, channel.go. |
| Get | external | borrower | Request a resource and receive a value or error. Pool API entry observed in code, channel.go. |
| Put | external | resource returner | Offer a resource after use. Pool API entry observed in code, channel.go. |
| Close | external | resource closer | Request closure of a supplied resource. Pool API entry observed in code, channel.go. |
| Release | external | lifecycle owner | Request teardown. Pool API entry observed in code, channel.go. |
| Len | external | observer | Query current count. Pool API entry observed in code, channel.go. |
| DirectPing | external | concrete-method adapter | Optional health callback can be requested via a structural interface assertion on the concrete value. It is absent from Pool's declared methods, pool.go. Method observed in code, channel.go. |
| FactoryResult | external | injected Factory | Synchronous value or error for a construction or acquisition. Invocation observed in code, channel.go, channel.go. |
| CloseResult | external | injected Close | Synchronous completion or error from resource cleanup. Invocation observed in code, channel.go, channel.go. |
| PingResult | external | injected Ping | Synchronous health result while checking a resource. Invocation observed in code, channel.go. |
| IdleAge | internal | clock sample in Get | Evaluate the age of an acquired candidate. Trigger observed in code, channel.go, channel.go. |
| WaitDelivery | internal | pool return path | Value sent to a registered acquisition. Producer and consumer observed in code, channel.go, channel.go. |
| DrainDone | internal | pool teardown path | Finish processing detached idle storage. Completion boundary observed in code, channel.go. |
| UV-NewOmitted | external | configuration caller | Construction omitted or deferred. Boundary observed in code, channel.go. |
| UV-NewRepeated | external | configuration caller | Duplicate or overlapping construction against the same backend, including an unintended extra pool. Boundary observed in code, channel.go. |
| UV-BadConfig | external | configuration caller | Nil configuration, invalid capacities, absent callbacks, zero capacity or unintended idle time including negative. Boundary observed in code, channel.go. |
| UV-GetOmitted | external | borrower | Omitted acquisition or unsolicited acquisition with no application demand. Boundary observed in code, channel.go. |
| UV-GetAgain | external | borrower | Second acquisition by the same caller while the first is pending or while its first resource is held. Boundary observed in code, channel.go. |
| UV-AbandonGet | external | borrower | Caller stops waiting externally, with no later matching return or with a later matching return. Boundary observed in code, channel.go. |
| UV-LateGet | external | borrower and lifecycle owner | Get overlaps or follows Release, including a prior observation of empty or ready storage. Boundary observed in code, channel.go. |
| UV-ContendedGet | external | borrower and resource returner | Put or Close changes availability between Get's failed receive and admission decision. Boundary observed in code, channel.go. |
| UV-WrongPoolGet | external | borrower | Get sent to the wrong pool instance. Boundary observed in code, channel.go. |
| UV-ReturnMissing | external | resource holder | Omit Put or Close after acquisition, leaving resource use and pending requests to be resolved. Boundary observed in code, channel.go. |
| UV-LatePut | external | resource returner | Put overlaps teardown or returns a resource after shutdown or requester departure. Boundary observed in code, channel.go. |
| UV-LateClose | external | resource closer | Close after Release, or after Put selected overflow cleanup. Boundary observed in code, channel.go. |
| UV-BadOwnership | external | resource returner or closer | Duplicate Put or Close, nil including typed nil, stale or wrong payload, or contradictory Put and Close for one resource. Boundary observed in code, channel.go. |
| UV-WrongPoolPut | external | resource returner or closer | Put or Close sent to the wrong pool instance. Boundary observed in code, channel.go. |
| UV-ReleaseOmitted | external | lifecycle owner | Omit or delay Release. Boundary observed in code, channel.go. |
| UV-ReleaseAgain | external | lifecycle owner | Repeat Release before drain completes or after it returns, including unsolicited teardown. Boundary observed in code, channel.go. |
| UV-WrongPoolRelease | external | lifecycle owner | Release the wrong instance. Boundary observed in code, channel.go. |
| UV-LateRead | external | observer | Repeated, stale or wrong-receiver Len during concurrent changes or teardown. Boundary observed in code, channel.go. |
| UV-FactoryFault | external | injected Factory | Factory error, panic, nil success, or value accompanying an error or of unexpected type. Boundary observed in code, channel.go. |
| UV-CloseFault | external | injected Close | Close error or panic including during expiry, overflow and drain, or success without cleanup. Boundary observed in code, channel.go. |
| UV-PingFault | external | injected Ping or concrete-method adapter | Absent callback, delayed or invalid health result, panic, or overlapping call and Release. Boundary observed in code, channel.go. |
| UV-CallbackDelay | external | injected Factory, Close or Ping | Callback stalls or re-enters Get, Put, Close, Release or Len while the original call is in progress. Boundary observed in code, channel.go. |

## Undesired-coverage (observed in code, not documented intent)

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| New: configuration caller | UV-NewOmitted | UV-CallbackDelay | UV-NewRepeated | UV-NewRepeated | UV-BadConfig | UV-NewRepeated | UV-BadConfig |
| Get: borrower | UV-GetOmitted | UV-AbandonGet | UV-GetAgain | UV-LateGet | UV-ContendedGet | UV-GetOmitted | UV-WrongPoolGet |
| Put: resource returner | UV-ReturnMissing | UV-LatePut | UV-BadOwnership | UV-LatePut | UV-BadOwnership | UV-BadOwnership | UV-WrongPoolPut, UV-BadOwnership |
| Close: resource closer | UV-ReturnMissing | UV-LateClose | UV-BadOwnership | UV-LateClose | UV-BadOwnership | UV-BadOwnership | UV-WrongPoolPut, UV-BadOwnership |
| Release: lifecycle owner | UV-ReleaseOmitted | UV-ReleaseOmitted | UV-ReleaseAgain | UV-ReleaseAgain | UV-LateGet | UV-ReleaseAgain | UV-WrongPoolRelease |
| Len: observer | n/a: omitting a read has no state effect, channel.go. | UV-LateRead | UV-LateRead | UV-LateRead | UV-LateRead | n/a: an unsolicited read has no state effect, channel.go. | UV-LateRead |
| DirectPing: concrete-method adapter | UV-PingFault | UV-CallbackDelay | UV-PingFault | UV-PingFault | UV-PingFault | UV-PingFault | UV-PingFault |
| FactoryResult: injected Factory | UV-FactoryFault | UV-CallbackDelay | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go. | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go. | UV-FactoryFault | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go. | UV-FactoryFault |
| CloseResult: injected Close | UV-CloseFault | UV-CallbackDelay | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go. | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go. | UV-CloseFault | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go. | UV-CloseFault |
| PingResult: injected Ping | UV-PingFault | UV-CallbackDelay | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go. | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go. | UV-PingFault | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go. | UV-PingFault |
| IdleAge: clock sample in Get | n/a: local time sampling has no delivery channel, channel.go. | UV-AbandonGet | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go. | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go. | n/a: one observation per branch, channel.go. | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go. | UV-BadConfig |
| WaitDelivery: pool return path | UV-ReturnMissing | UV-AbandonGet | n/a: serialized dequeue before send to a private request channel, channel.go. | UV-LatePut | UV-ContendedGet | n/a: delivery requires registered work, channel.go. | UV-BadOwnership |
| DrainDone: pool teardown path | UV-CloseFault | UV-CallbackDelay | n/a: there is one drain per captured channel, channel.go. | n/a: the range executes after detachment in the same call, channel.go. | UV-LateGet | n/a: requires prior detachment, channel.go. | n/a: payloadless method or completion signal, channel.go. |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Get → Put | same pool, borrower and returning holder |
| P-01b | Put → Get | same pool, borrower and returning holder |
| P-02a | Get → Close | same pool, borrower and resource closer |
| P-02b | Close → Get | same pool, borrower and resource closer |
| P-03a | Get → Release | same pool, borrower and lifecycle owner |
| P-03b | Release → Get | same pool, borrower and lifecycle owner |
| P-04a | Put → Release | same pool and resource, returning holder and lifecycle owner |
| P-04b | Release → Put | same pool and resource, returning holder and lifecycle owner |
| P-05a | Close → Release | same pool and resource, closer and lifecycle owner |
| P-05b | Release → Close | same pool and resource, closer and lifecycle owner |
| P-06a | Len → Release | same pool, observer and lifecycle owner |
| P-06b | Release → Len | same pool, observer and lifecycle owner |
| P-07a | Put → Close | same resource, distinct returner and closer |
| P-07b | Close → Put | same resource, distinct returner and closer |
| P-08a | PingResult → Release | same pool, health callback completion and lifecycle owner |
| P-08b | Release → PingResult | same pool, health callback completion and lifecycle owner |
| P-09a | FactoryResult → Release | same published pool, creation callback completion and lifecycle owner |
| P-09b | Release → FactoryResult | same published pool, creation callback completion and lifecycle owner |
| P-10a | CloseResult → Release | same pool, cleanup callback completion and lifecycle owner |
| P-10b | Release → CloseResult | same pool, cleanup callback completion and lifecycle owner |
| P-11a | Len → Put | same pool, observer and returner |
| P-11b | Put → Len | same pool, observer and returner |
| P-12a | Len → Get | same pool, observer and borrower |
| P-12b | Get → Len | same pool, observer and borrower |
| P-13a | DirectPing → Release | same pool, optional direct health caller and lifecycle owner |
| P-13b | Release → DirectPing | same pool, optional direct health caller and lifecycle owner |
| P-14a | Len → Close | same pool, observer and closer |
| P-14b | Close → Len | same pool, observer and closer |
| P-15a | DirectPing → Put | same resource, health caller and returner |
| P-15b | Put → DirectPing | same resource, health caller and returner |
| P-16a | DirectPing → Close | same resource, health caller and closer |
| P-16b | Close → DirectPing | same resource, health caller and closer |

## Remembrance semantics (observed in code, not documented intent)

Observed in code. Idle channel and pending request queue are distinct, channel.go, channel.go. A checked-out resource has no identity record. Put slides the queue and reslices without clearing the former last slot, channel.go, channel.go. Release detaches idle storage and leaves pending request storage and accounting untouched, channel.go, channel.go. Counter begins at InitialCap, increments on successful dynamic creation and decrements before delegated Close, channel.go, channel.go. Storage-retention cost depends on runtime reachability and workload.

## Lock-discipline annotation (observed in code, not documented intent)

Observed in code. Published Factory runs under the mutex, channel.go, channel.go. Direct Close calls its callback under the mutex, channel.go, channel.go. Put sends to a private buffered request while holding the mutex, channel.go, channel.go. getConns only snapshots under the mutex, channel.go. Constructor Factory, health checking and detached Release draining invoke callbacks outside the published pool lock, channel.go, channel.go. The callback descriptions state roles only, channel.go, channel.go.

## Catalogue notes

The four primary actor roles are configuration caller, borrower or resource holder, lifecycle owner and configured callback provider. Runtime time samples and private handoffs are internal.

## Event annotations (observed in code, not documented intent)

### New
- gate (observed in code): payload content
- upstream_guards (observed in code): Constructor validates the capacity relation and callback presence locally, channel.go. No upstream config validation is shown.
- coverage:
  - loss: UV-NewOmitted
  - delay: UV-CallbackDelay
  - duplication: UV-NewRepeated
  - out-of-order: UV-NewRepeated
  - contradiction: UV-BadConfig
  - commission: UV-NewRepeated
  - value: UV-BadConfig

### Get
- gate (observed in code): service-side state
- upstream_guards (observed in code): No caller identity, context or ownership token in the public API, pool.go.
- coverage:
  - loss: UV-GetOmitted
  - delay: UV-AbandonGet
  - duplication: UV-GetAgain
  - out-of-order: UV-LateGet
  - contradiction: UV-ContendedGet
  - commission: UV-GetOmitted
  - value: UV-WrongPoolGet

### Put
- gate (observed in code): payload content and service-side state
- upstream_guards (observed in code): Example intends a return after use, README.md ("Put the connection back into the connection pool, when the connection is no longer in use"). No upstream enforcement of receiver, ownership or affinity.
- coverage:
  - loss: UV-ReturnMissing
  - delay: UV-LatePut
  - duplication: UV-BadOwnership
  - out-of-order: UV-LatePut
  - contradiction: UV-BadOwnership
  - commission: UV-BadOwnership
  - value: UV-WrongPoolPut, UV-BadOwnership

### Close
- gate (observed in code): payload content and service-side state
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.
- coverage:
  - loss: UV-ReturnMissing
  - delay: UV-LateClose
  - duplication: UV-BadOwnership
  - out-of-order: UV-LateClose
  - contradiction: UV-BadOwnership
  - commission: UV-BadOwnership
  - value: UV-WrongPoolPut, UV-BadOwnership

### Release
- gate (observed in code): service-side state
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.
- coverage:
  - loss: UV-ReleaseOmitted
  - delay: UV-ReleaseOmitted
  - duplication: UV-ReleaseAgain
  - out-of-order: UV-ReleaseAgain
  - contradiction: UV-LateGet
  - commission: UV-ReleaseAgain
  - value: UV-WrongPoolRelease

### Len
- gate (observed in code): service-side state
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.
- coverage:
  - loss: n/a: omitting a read has no state effect, channel.go.
  - delay: UV-LateRead
  - duplication: UV-LateRead
  - out-of-order: UV-LateRead
  - contradiction: UV-LateRead
  - commission: n/a: an unsolicited read has no state effect, channel.go.
  - value: UV-LateRead

### DirectPing
- gate (observed in code): payload content and service-side state
- upstream_guards (observed in code): Adapter must obtain interface exposing Ping. That assertion does not establish configuration, channel.go.
- coverage:
  - loss: UV-PingFault
  - delay: UV-CallbackDelay
  - duplication: UV-PingFault
  - out-of-order: UV-PingFault
  - contradiction: UV-PingFault
  - commission: UV-PingFault
  - value: UV-PingFault

### FactoryResult
- gate (observed in code): payload content
- upstream_guards (observed in code): Caller supplies the callback. Error result is typed. No stronger upstream lifecycle, panic, timing or reentrancy guarantee is documented.
- coverage:
  - loss: UV-FactoryFault
  - delay: UV-CallbackDelay
  - duplication: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go.
  - out-of-order: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go.
  - contradiction: UV-FactoryFault
  - commission: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go.
  - value: UV-FactoryFault

### CloseResult
- gate (observed in code): payload content
- upstream_guards (observed in code): Caller supplies the callback. Error result is typed. No stronger upstream lifecycle, panic, timing or reentrancy guarantee is documented.
- coverage:
  - loss: UV-CloseFault
  - delay: UV-CallbackDelay
  - duplication: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go.
  - out-of-order: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go.
  - contradiction: UV-CloseFault
  - commission: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go.
  - value: UV-CloseFault

### PingResult
- gate (observed in code): payload content
- upstream_guards (observed in code): Caller supplies the callback. Error result is typed. No stronger upstream lifecycle, panic, timing or reentrancy guarantee is documented.
- coverage:
  - loss: UV-PingFault
  - delay: UV-CallbackDelay
  - duplication: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go.
  - out-of-order: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go.
  - contradiction: UV-PingFault
  - commission: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go.
  - value: UV-PingFault

### IdleAge
- gate (observed in code): service-side state
- upstream_guards (observed in code): No injected pool clock. Time is sampled by Get, channel.go.
- coverage:
  - loss: n/a: local time sampling has no delivery channel, channel.go.
  - delay: UV-AbandonGet
  - duplication: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go.
  - out-of-order: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go.
  - contradiction: n/a: one observation per branch, channel.go.
  - commission: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go.
  - value: UV-BadConfig

### WaitDelivery
- gate (observed in code): service-side state
- upstream_guards (observed in code): Only Put produces delivery in this component, channel.go. No requester identifier in payload, channel.go.
- coverage:
  - loss: UV-ReturnMissing
  - delay: UV-AbandonGet
  - duplication: n/a: serialized dequeue before send to a private request channel, channel.go.
  - out-of-order: UV-LatePut
  - contradiction: UV-ContendedGet
  - commission: n/a: delivery requires registered work, channel.go.
  - value: UV-BadOwnership

### DrainDone
- gate (observed in code): service-side state
- upstream_guards (observed in code): Only the first successful detachment can drain its captured channel, channel.go, channel.go.
- coverage:
  - loss: UV-CloseFault
  - delay: UV-CallbackDelay
  - duplication: n/a: there is one drain per captured channel, channel.go.
  - out-of-order: n/a: the range executes after detachment in the same call, channel.go.
  - contradiction: UV-LateGet
  - commission: n/a: requires prior detachment, channel.go.
  - value: n/a: payloadless method or completion signal, channel.go.

### UV-NewOmitted
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-NewRepeated
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-BadConfig
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-GetOmitted
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-GetAgain
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-AbandonGet
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-LateGet
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-ContendedGet
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-WrongPoolGet
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-ReturnMissing
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-LatePut
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-LateClose
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-BadOwnership
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-WrongPoolPut
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-ReleaseOmitted
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-ReleaseAgain
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-WrongPoolRelease
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-LateRead
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-FactoryFault
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-CloseFault
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-PingFault
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-CallbackDelay
- gate (observed in code): observed service state and/or payload as for base event
- upstream_guards (observed in code): No deployment-wide upstream guarantee. Tests and example are representative callers only.



=== INPUT 2b: DOCTRINE LINES (from the extraction) ===

- DOC-1 — explicit-requirement README.md ("More versatile, The connection type in the connection pool is `interface{}`, making it more versatile")
- DOC-2 — explicit-requirement README.md ("More configurable, The connection supports setting the maximum idle time, the timeout connection will be closed and discarded, which can avoid the problem of automatic connection failure when idle")
- DOC-3 — explicit-requirement README.md ("Support user setting `ping` method, used to check the connectivity of connection, invalid connection will be discarded")
- DOC-4 — explicit-requirement README.md ("Support connection waiting, When the connection pool is full, support for connection waiting (like the go db connection pool)")
- DOC-5 — explicit-requirement README.md ("factory Specify the method to create the connection")
- DOC-6 — explicit-requirement README.md ("close Specify the method to close the connection")
- DOC-7 — explicit-requirement README.md ("ping Specify the method to detect whether the connection is invalid")
- DOC-8 — explicit-requirement README.md ("Create a connection pool: Initialize the number of connections to 5, the maximum idle connection is 20, and the maximum concurrent connection is 30")
- DOC-9 — explicit-requirement README.md ("The maximum idle time of the connection, the connection exceeding this time will be closed, which can avoid the problem of automatic failure when connecting to EOF when idle")
- DOC-10 — explicit-requirement README.md ("Get a connection from the connection pool")
- DOC-11 — explicit-requirement README.md ("Put the connection back into the connection pool, when the connection is no longer in use")
- DOC-12 — explicit-requirement README.md ("Release all connections in the connection pool, when resources need to be destroyed")
- DOC-13 — explicit-requirement README.md ("View the number of connections in the current connection pool")

=== INPUT 2: REQUIREMENTS (domain-analysis/channelPool/requirements-prose.txt) ===

A golang universal network connection pool.

## Feature：

- More versatile, The connection type in the connection pool is `interface{}`, making it more versatile

- More configurable, The connection supports setting the maximum idle time, the timeout connection will be closed and discarded, which can avoid the problem of automatic connection failure when idle

- Support user setting `ping` method, used to check the connectivity of connection, invalid connection will be discarded

- Support connection waiting, When the connection pool is full, support for connection waiting (like the go db connection pool)

## Basic Usage:

//factory Specify the method to create the connection

//close Specify the method to close the connection

//ping Specify the method to detect whether the connection is invalid

//Create a connection pool: Initialize the number of connections to 5, the maximum idle connection is 20, and the maximum concurrent connection is 30

	//The maximum idle time of the connection, the connection exceeding this time will be closed, which can avoid the problem of automatic failure when connecting to EOF when idle

//Get a connection from the connection pool

//Put the connection back into the connection pool, when the connection is no longer in use

//Release all connections in the connection pool, when resources need to be destroyed

//View the number of connections in the current connection pool


=== INPUT 3: EVENT CONTRACT TEXTS (domain-analysis/channelPool/event-contracts.txt) ===

channel.go:13
//ErrMaxActiveConnReached 连接池超限

channel.go:17
// Config 连接池相关配置

channel.go:19
//连接池中拥有的最小连接数

channel.go:21
//最大并发存活连接数

channel.go:23
//最大空闲连接

channel.go:25
//生成连接的方法

channel.go:27
//关闭连接的方法

channel.go:29
//检查连接是否有效的方法

channel.go:31
//连接最大空闲时间，超过该事件则将失效

channel.go:57
// NewChannelPool 初始化连接

channel.go:102
// Get 从pool中取一个连接

channel.go:166
// Put 将连接放回pool中

channel.go:201
// Close 关闭单条连接

channel.go:215
// Ping 检查单条连接是否有效

channel.go:223
// Release 释放连接池中所有连接

channel.go:245
// Len 连接池中已有的连接

pool.go:6
//ErrClosed 连接池已经关闭Error

pool.go:10
// Pool 基本方法


Respond with ONLY the table and the coverage checklist: every catalogue event and pair-ordering id, listed once in the checklist, ticked. A missing row must be impossible to miss.
The coverage checklist must use one exact line per event or pair in the form '- [x] EVENT_ID', with no other text on that line.
