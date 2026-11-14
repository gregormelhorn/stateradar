You are the BLIND adversarial pass (Part B) of a domain-behaviour analysis. You have NO access to the implementation. Do NOT read any files, do NOT use any tools, do NOT search any repository — the inputs below are complete and are your ONLY sources. If you catch yourself wanting to look something up, label it an open point instead.

TASK: Here is the event catalogue of a component, and its requirements. For every event — including undesired variants and both orderings of every interaction pair — state in which situations the component should handle, ignore, or reject it, and what should happen. Describe situations in requirement terms. Name states per PA-17 (state naming convention): prefer public API names, name sub-states by their condition, use PascalCase with `_` as separator. If you must assume a lifecycle state the requirements do not name, label it `assumed-state:` with the condition that defines it. You have no access to the implementation. Be concrete. Produce a table keyed by the catalogue's event ids and pair-ordering ids. Prefer one row per id with conditional outcomes. If you split an id into several rows, use an explicit `Situation` column with distinct, nonempty labels. Do not repeat the same situation. End with a coverage checklist: every catalogue event id, listed once, ticked. A missing row must be impossible to miss.

Catalogue headings and fields labelled `observed in code` say what the implementation does, not what it should do. Base each row on the requirements, the contracts and the doctrine lines. When a row's expected behaviour rests only on observed-in-code text, start its behaviour cell with `as-is:`.

<!-- generated:rules key=partb-vocab -->
The disposition vocabulary you must use (from the methods reference): `transition → <target>` | `handle` (stays in the state, does something) | `ignore (documented)` | `ignore (accidental)` | `defer (queued)` | `reject` (a declared refusal signal: error, diagnostic, nack) | `UNSPECIFIED`. Without these definitions a blind pass applies `reject` and `handle` to identical semantics interchangeably (dobby trigger-service, 2026-08-05: four vocabulary-only "divergences").
<!-- /generated:rules -->

The catalogue's event ids are: New Get Put Close Release Len Factory PingResult CloseResult IdleCheck UV-NoOwner UV-OwnerLate UV-NewAgain UV-OwnerOverlap UV-Config UV-Abandon UV-GetAgain UV-AfterRelease UV-Overlap UV-Unsolicited UV-WrongPool UV-DuplicateResource UV-LateResource UV-ForeignResource UV-ReleaseAgain UV-Observer UV-FactoryError UV-FactoryDelay UV-FactoryValue UV-PingError UV-PingDelay UV-PingValue UV-CloseError UV-CloseDelay UV-CloseValue UV-Aged — plus the pair orderings P-01a P-01b P-02a P-02b P-03a P-03b P-04a P-04b P-05a P-05b P-06a P-06b P-07a P-07b P-08a P-08b P-09a P-09b P-10a P-10b.

=== INPUT 1: EVENT CATALOGUE (code fragments and analysis references removed) ===

# Event catalogue

<!-- event-ids: New Get Put Close Release Len Factory PingResult CloseResult IdleCheck UV-NoOwner UV-OwnerLate UV-NewAgain UV-OwnerOverlap UV-Config UV-Abandon UV-GetAgain UV-AfterRelease UV-Overlap UV-Unsolicited UV-WrongPool UV-DuplicateResource UV-LateResource UV-ForeignResource UV-ReleaseAgain UV-Observer UV-FactoryError UV-FactoryDelay UV-FactoryValue UV-PingError UV-PingDelay UV-PingValue UV-CloseError UV-CloseDelay UV-CloseValue UV-Aged -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| New | external | Lifecycle owner | Creates configured pool and requests initial resources. channel.go |
| Get | external | Request caller | Requests a connection. channel.go |
| Put | external | Resource holder | Returns opaque connection. channel.go |
| Close | external | Resource holder | Requests disposal of a single opaque connection. channel.go |
| Release | external | Lifecycle owner | Requests pool shutdown. channel.go |
| Len | external | Observer | Reads available count. channel.go |
| Factory | internal | Factory callback | Synchronous creation completion supplies a connection and error. channel.go |
| PingResult | internal | Ping callback | Synchronous connectivity check outcome. channel.go |
| CloseResult | internal | Close callback | Synchronous disposal outcome. channel.go |
| IdleCheck | internal | Clock | Sample connection age during acquisition. channel.go |
| UV-NoOwner | external | Lifecycle owner | Construction or teardown omitted. channel.go |
| UV-OwnerLate | external | Lifecycle owner | Construction or teardown delayed while caller work continues. channel.go |
| UV-NewAgain | external | Lifecycle owner | Repeated or unsolicited construction with same configuration. channel.go |
| UV-OwnerOverlap | external | Lifecycle owner | Teardown overlaps construction of another pool or is issued while old work runs. channel.go |
| UV-Config | external | Lifecycle owner | Nil config, invalid bounds, zero capacity, zero idle capacity, absent callbacks, nonpositive timeout or valid unintended limits. channel.go |
| UV-Abandon | external | Caller or holder | Get result abandoned by caller, or Put/Close omitted or delayed after checkout. channel.go |
| UV-GetAgain | external | Request caller | Second Get while first awaits a resource, or after first returned a resource the same caller still holds. channel.go |
| UV-AfterRelease | external | Request caller | Fresh Get on an already released pool. channel.go |
| UV-Overlap | external | Caller, holder and owner | Overlapping Get, Put, Close or Release on a shared pool. channel.go |
| UV-Unsolicited | external | Request caller | Unsolicited Get without an application-level reason. channel.go |
| UV-WrongPool | external | Public caller | Valid public call on an unintended receiver, separately from a wrong resource payload. channel.go |
| UV-DuplicateResource | external | Resource holder | Duplicate Put or Close, or both for one resource. channel.go |
| UV-LateResource | external | Resource holder | Put or Close after release or before other ownership work completes. channel.go |
| UV-ForeignResource | external | Resource holder | No matching checkout, foreign connection, typed nil or stale payload presented to intended pool. channel.go |
| UV-ReleaseAgain | external | Lifecycle owner | Second Release after detach or during draining. channel.go |
| UV-Observer | external | Observer | Late, repeated, unsolicited or overlapping observation. channel.go |
| UV-FactoryError | external | Factory callback | Creation returns error, including a value together with error. channel.go |
| UV-FactoryDelay | external | Factory callback | Slow, blocked, panicking or reentrant creation. channel.go |
| UV-FactoryValue | external | Factory callback | Nil, typed nil, reused or foreign connection with successful creation. channel.go |
| UV-PingError | external | Ping callback | Connectivity check returns an error. channel.go |
| UV-PingDelay | external | Ping callback | Slow, blocked, panicking or reentrant validation, overlapping release. channel.go |
| UV-PingValue | external | Ping callback | Healthy resource reported invalid or invalid resource reported healthy. channel.go |
| UV-CloseError | external | Close callback | Disposal returns error in direct, overflow, expiry, invalid cleanup or release drain paths. channel.go |
| UV-CloseDelay | external | Close callback | Slow, blocked, panicking or reentrant disposal in live or drain phase. channel.go |
| UV-CloseValue | external | Close callback | Disposal reports success with resource still live or error after disposing it. channel.go |
| UV-Aged | internal | Clock | Idle age below, equal to or beyond timeout, including handoff delivery delayed by scheduling. channel.go |

## Undesired-coverage (observed in code, not documented intent)

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| New: Lifecycle owner | UV-NoOwner | UV-OwnerLate | UV-NewAgain | UV-OwnerLate | UV-OwnerOverlap | UV-NewAgain | UV-Config |
| Get: Request caller | UV-Abandon | UV-Abandon | UV-GetAgain | UV-AfterRelease | UV-Overlap | UV-Unsolicited | UV-WrongPool |
| Put: Resource holder | UV-Abandon | UV-Abandon | UV-DuplicateResource | UV-LateResource | UV-Overlap | UV-ForeignResource | UV-ForeignResource, UV-WrongPool |
| Close: Resource holder | UV-Abandon | UV-Abandon | UV-DuplicateResource | UV-LateResource | UV-Overlap | UV-ForeignResource | UV-ForeignResource, UV-WrongPool |
| Release: Lifecycle owner | UV-NoOwner | UV-OwnerLate | UV-ReleaseAgain | UV-OwnerLate | UV-OwnerOverlap, UV-Overlap | UV-OwnerOverlap | UV-WrongPool |
| Len: Observer | n/a: synchronous invocation or observation only, channel.go. | UV-Observer | UV-Observer | UV-Observer | UV-Observer | UV-Observer | UV-WrongPool |
| Factory: Factory callback | UV-FactoryError | UV-FactoryDelay | n/a: synchronous invocation or observation only, channel.go. | n/a: synchronous invocation or observation only, channel.go. | UV-FactoryDelay | n/a: synchronous invocation or observation only, channel.go. | UV-FactoryValue |
| PingResult: Ping callback | UV-PingError | UV-PingDelay | n/a: synchronous invocation or observation only, channel.go. | UV-PingDelay | UV-PingDelay | n/a: synchronous invocation or observation only, channel.go. | UV-PingValue |
| CloseResult: Close callback | UV-CloseError | UV-CloseDelay | n/a: synchronous invocation or observation only, channel.go. | UV-CloseDelay | UV-CloseDelay | n/a: synchronous invocation or observation only, channel.go. | UV-CloseValue |
| IdleCheck: Clock | n/a: synchronous invocation or observation only, channel.go. | UV-Aged | n/a: synchronous invocation or observation only, channel.go. | UV-Aged | n/a: synchronous invocation or observation only, channel.go. | n/a: synchronous invocation or observation only, channel.go. | UV-Aged |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Get → Put | Requester and holder on one pool |
| P-01b | Put → Get | Requester and holder on one pool |
| P-02a | Get → Close | Requester and holder on one pool |
| P-02b | Close → Get | Requester and holder on one pool |
| P-03a | Get → Release | Requester and owner on one pool |
| P-03b | Release → Get | Requester and owner on one pool |
| P-04a | Put → Release | Holder and owner on one pool |
| P-04b | Release → Put | Holder and owner on one pool |
| P-05a | Close → Release | Holder and owner on one pool |
| P-05b | Release → Close | Holder and owner on one pool |
| P-06a | Len → Release | Observer and owner on one pool |
| P-06b | Release → Len | Observer and owner on one pool |
| P-07a | Len → Get | Observer and requester on one pool |
| P-07b | Get → Len | Observer and requester on one pool |
| P-08a | Len → Put | Observer and holder on one pool |
| P-08b | Put → Len | Observer and holder on one pool |
| P-09a | Len → Close | Observer and holder on one pool |
| P-09b | Close → Len | Observer and holder on one pool |
| P-10a | Put → Close | Independently acting holders or cleanup agents for one resource |
| P-10b | Close → Put | Independently acting holders or cleanup agents for one resource |

## Remembrance semantics (observed in code, not documented intent)

Observed in code. Outstanding resource identity and owner are not stored. The idle channel holds up to MaxIdle opaque wrappers, each timed on construction, return or handoff. channel.go, channel.go. The FIFO slice is unbounded and removes logically via shift and reslice without clearing the tail, preserving a reference to the last copied or removed channel until overwrite or collection. channel.go, channel.go. Each requester channel has room for one reply. channel.go. Release detaches and drains the idle buffer, leaves the waiter slice and counter alone, and keeps a local closer while draining. channel.go, channel.go. The counter starts at InitialCap, increments on reported creation success, decrements before live disposal outcome, and has no change on return, handoff, failed creation or release. channel.go, channel.go. Late references resolve through the receiver's current availability and callback fields. channel.go, channel.go. Runtime retention cost is unmeasured.

## Lock-discipline annotation (observed in code, not documented intent)

Observed in code. Channel snapshots copy the field under the mutex. channel.go, channel.go. Get admission, Debugf and post-start Factory execute under the lock. channel.go, channel.go. Constructor Factory runs outside the lock before publication. channel.go, channel.go. Put selects delivery or buffering under lock, then releases it before overflow disposal. channel.go, channel.go. Live Close invokes Close under lock. channel.go, channel.go. Ping reads and calls the callback outside the lock. channel.go, channel.go. Release detaches under lock and drains with captured callback outside. channel.go, channel.go. No reentrancy restrictions in the callback descriptions at channel.go, or channel.go.

## Event annotations (observed in code, not documented intent)

### New
- gate (observed in code): Configuration content
- upstream_guards (observed in code): README.md gives example values. Validation is local.
- coverage:
  - loss: UV-NoOwner
  - delay: UV-OwnerLate
  - duplication: UV-NewAgain
  - out-of-order: UV-OwnerLate
  - contradiction: UV-OwnerOverlap
  - commission: UV-NewAgain
  - value: UV-Config

### Get
- gate (observed in code): Idle readiness, pool availability, active count and validation
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.
- coverage:
  - loss: UV-Abandon
  - delay: UV-Abandon
  - duplication: UV-GetAgain
  - out-of-order: UV-AfterRelease
  - contradiction: UV-Overlap
  - commission: UV-Unsolicited
  - value: UV-WrongPool

### Put
- gate (observed in code): Nil interface, availability, waiting requests and send readiness
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.
- coverage:
  - loss: UV-Abandon
  - delay: UV-Abandon
  - duplication: UV-DuplicateResource
  - out-of-order: UV-LateResource
  - contradiction: UV-Overlap
  - commission: UV-ForeignResource
  - value: UV-ForeignResource, UV-WrongPool

### Close
- gate (observed in code): Nil interface and configured close method
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.
- coverage:
  - loss: UV-Abandon
  - delay: UV-Abandon
  - duplication: UV-DuplicateResource
  - out-of-order: UV-LateResource
  - contradiction: UV-Overlap
  - commission: UV-ForeignResource
  - value: UV-ForeignResource, UV-WrongPool

### Release
- gate (observed in code): Pool availability
- upstream_guards (observed in code): README.md describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go.
- coverage:
  - loss: UV-NoOwner
  - delay: UV-OwnerLate
  - duplication: UV-ReleaseAgain
  - out-of-order: UV-OwnerLate
  - contradiction: UV-OwnerOverlap, UV-Overlap
  - commission: UV-OwnerOverlap
  - value: UV-WrongPool

### Len
- gate (observed in code): Pool availability and idle depth
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.
- coverage:
  - loss: n/a: synchronous invocation or observation only, channel.go.
  - delay: UV-Observer
  - duplication: UV-Observer
  - out-of-order: UV-Observer
  - contradiction: UV-Observer
  - commission: UV-Observer
  - value: UV-WrongPool

### Factory
- gate (observed in code): Error and construction versus acquisition phase
- upstream_guards (observed in code): Injected callback contract describes purpose only. No independent callback registration or result ingress.
- coverage:
  - loss: UV-FactoryError
  - delay: UV-FactoryDelay
  - duplication: n/a: synchronous invocation or observation only, channel.go.
  - out-of-order: n/a: synchronous invocation or observation only, channel.go.
  - contradiction: UV-FactoryDelay
  - commission: n/a: synchronous invocation or observation only, channel.go.
  - value: UV-FactoryValue

### PingResult
- gate (observed in code): Error and callback availability
- upstream_guards (observed in code): Injected callback contract describes purpose only. No independent callback registration or result ingress.
- coverage:
  - loss: UV-PingError
  - delay: UV-PingDelay
  - duplication: n/a: synchronous invocation or observation only, channel.go.
  - out-of-order: UV-PingDelay
  - contradiction: UV-PingDelay
  - commission: n/a: synchronous invocation or observation only, channel.go.
  - value: UV-PingValue

### CloseResult
- gate (observed in code): Error and cleanup phase
- upstream_guards (observed in code): Injected callback contract describes purpose only. No independent callback registration or result ingress.
- coverage:
  - loss: UV-CloseError
  - delay: UV-CloseDelay
  - duplication: n/a: synchronous invocation or observation only, channel.go.
  - out-of-order: UV-CloseDelay
  - contradiction: UV-CloseDelay
  - commission: n/a: synchronous invocation or observation only, channel.go.
  - value: UV-CloseValue

### IdleCheck
- gate (observed in code): Configured timeout and sampled age
- upstream_guards (observed in code): No caller-supplied time. channel.go
- coverage:
  - loss: n/a: synchronous invocation or observation only, channel.go.
  - delay: UV-Aged
  - duplication: n/a: synchronous invocation or observation only, channel.go.
  - out-of-order: UV-Aged
  - contradiction: n/a: synchronous invocation or observation only, channel.go.
  - commission: n/a: synchronous invocation or observation only, channel.go.
  - value: UV-Aged

### UV-NoOwner
- gate (observed in code): Absent lifecycle call
- upstream_guards (observed in code): README.md describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go.

### UV-OwnerLate
- gate (observed in code): Lifecycle order
- upstream_guards (observed in code): README.md describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go.

### UV-NewAgain
- gate (observed in code): Configuration and independent instance
- upstream_guards (observed in code): README.md describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go.

### UV-OwnerOverlap
- gate (observed in code): Receiver and availability
- upstream_guards (observed in code): README.md describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go.

### UV-Config
- gate (observed in code): Configuration content
- upstream_guards (observed in code): README.md describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go.

### UV-Abandon
- gate (observed in code): No cancellation parameter and no deadline for queue
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.

### UV-GetAgain
- gate (observed in code): Admission and idle readiness, no caller identity
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.

### UV-AfterRelease
- gate (observed in code): Pool availability
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.

### UV-Overlap
- gate (observed in code): Idle readiness, count, pending queue and cutoff
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.

### UV-Unsolicited
- gate (observed in code): Same admission gates as Get
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.

### UV-WrongPool
- gate (observed in code): Receiver and local state
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.

### UV-DuplicateResource
- gate (observed in code): Presence of value and local counts
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.

### UV-LateResource
- gate (observed in code): Availability at commit
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.

### UV-ForeignResource
- gate (observed in code): Interface nil and callback-specific type requirements
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.

### UV-ReleaseAgain
- gate (observed in code): Availability
- upstream_guards (observed in code): README.md describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go.

### UV-Observer
- gate (observed in code): Channel snapshot and length
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.

### UV-FactoryError
- gate (observed in code): Callback error
- upstream_guards (observed in code): Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-FactoryDelay
- gate (observed in code): Callback progress and phase
- upstream_guards (observed in code): Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-FactoryValue
- gate (observed in code): Callback result
- upstream_guards (observed in code): Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-PingError
- gate (observed in code): Callback error
- upstream_guards (observed in code): Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-PingDelay
- gate (observed in code): Callback progress and teardown
- upstream_guards (observed in code): Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-PingValue
- gate (observed in code): Callback verdict
- upstream_guards (observed in code): Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-CloseError
- gate (observed in code): Phase and callback error
- upstream_guards (observed in code): Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-CloseDelay
- gate (observed in code): Phase and callback progress
- upstream_guards (observed in code): Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-CloseValue
- gate (observed in code): Callback side effect
- upstream_guards (observed in code): Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-Aged
- gate (observed in code): Age and timeout
- upstream_guards (observed in code): Public Pool calls carry no actor, ownership token, or context. pool.go.



=== INPUT 2b: DOCTRINE LINES (from the extraction) ===

- DOC-1 explicit-requirement README.md ("- More versatile, The connection type in the connection pool is `interface{}`, making it more versatile").
- DOC-2 explicit-requirement README.md ("- More configurable, The connection supports setting the maximum idle time, the timeout connection will be closed and discarded, which can avoid the problem of automatic connection failure when idle").
- DOC-3 explicit-requirement README.md ("- Support user setting `ping` method, used to check the connectivity of connection, invalid connection will be discarded").
- DOC-4 explicit-requirement README.md ("- Support connection waiting, When the connection pool is full, support for connection waiting (like the go db connection pool)").
- DOC-5 explicit-requirement README.md ("//factory Specify the method to create the connection").
- DOC-6 explicit-requirement README.md ("//close Specify the method to close the connection").
- DOC-7 explicit-requirement README.md ("//ping Specify the method to detect whether the connection is invalid").
- DOC-8 explicit-requirement README.md ("//Create a connection pool: Initialize the number of connections to 5, the maximum idle connection is 20, and the maximum concurrent connection is 30").
- DOC-9 explicit-requirement README.md ("	//The maximum idle time of the connection, the connection exceeding this time will be closed, which can avoid the problem of automatic failure when connecting to EOF when idle").
- DOC-10 explicit-requirement README.md ("//Get a connection from the connection pool").
- DOC-11 explicit-requirement README.md ("//Put the connection back into the connection pool, when the connection is no longer in use").
- DOC-12 explicit-requirement README.md ("//Release all connections in the connection pool, when resources need to be destroyed").
- DOC-13 explicit-requirement README.md ("//View the number of connections in the current connection pool").

=== INPUT 2: REQUIREMENTS (domain-analysis/channelPool/requirements-prose.md) ===

# pool
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
//do something
//Put the connection back into the connection pool, when the connection is no longer in use
//Release all connections in the connection pool, when resources need to be destroyed
//View the number of connections in the current connection pool

#### Remarks:
The connection pool implementation refers to pool [https://github.com/fatih/pool](https://github.com/fatih/pool) , thanks.

## License
The MIT License (MIT) - see LICENSE for more details


=== INPUT 3: EVENT CONTRACT TEXTS (domain-analysis/channelPool/contracts.md) ===

### channel.go:13
	//ErrMaxActiveConnReached 连接池超限

### channel.go:17
// Config 连接池相关配置

### channel.go:19
	//连接池中拥有的最小连接数

### channel.go:21
	//最大并发存活连接数

### channel.go:23
	//最大空闲连接

### channel.go:25
	//生成连接的方法

### channel.go:27
	//关闭连接的方法

### channel.go:29
	//检查连接是否有效的方法

### channel.go:31
	//连接最大空闲时间，超过该事件则将失效

### channel.go:57
// NewChannelPool 初始化连接

### channel.go:102
// Get 从pool中取一个连接

### channel.go:166
// Put 将连接放回pool中

### channel.go:201
// Close 关闭单条连接

### channel.go:215
// Ping 检查单条连接是否有效

### channel.go:223
// Release 释放连接池中所有连接

### channel.go:245
// Len 连接池中已有的连接

### pool.go:6
	//ErrClosed 连接池已经关闭Error

### pool.go:10
// Pool 基本方法


Respond with ONLY the table and the coverage checklist: every catalogue event and pair-ordering id, listed once in the checklist, ticked. A missing row must be impossible to miss.
The coverage checklist must use one exact line per event or pair in the form '- [x] EVENT_ID', with no other text on that line.
