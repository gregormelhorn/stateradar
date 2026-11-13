# channelPool — event catalogue (Step 3)

<!-- event-ids: Get Put Close Ping Release Len UV-Conn-nil UV-Put-dup UV-Close-dup UV-Put-foreign UV-Close-foreign -->

The component is one connection pool instance (channel.go). Its states are named in the disposition matrix; the situations that define them: `Open_IdleAvailable` (idle connections present, fewer than MaxIdle, nobody waiting), `Open_IdleFull` (MaxIdle idle connections, nobody waiting), `Open_NoIdle_BelowCap` (no idle connection, nobody waiting, fewer open connections than MaxCap), `Open_NoIdle_AtCap` (no idle connection, nobody waiting, MaxCap open connections), `Open_Waiting_AtCap` (callers waiting, no idle connection, MaxCap reached), `Open_Waiting_BelowCap` (callers waiting, no idle connection, fewer than MaxCap open), `Open_Waiting_IdleAvailable` (callers waiting and an idle connection present), `Closed` (after Release).

## Events

| id | source | external/internal | payload gist | produced / consumed |
|---|---|---|---|---|
| Get | application goroutine | external | none | consumed by channel.go:103 |
| Put | application goroutine | external | a connection (interface{}), non-nil | consumed by channel.go:167 |
| Close | application goroutine | external | a connection, non-nil | consumed by channel.go:202 |
| Ping | same-package caller (not in the Pool interface, pool.go:11-21) | external | a connection, non-nil; returns the Ping callback's verdict only; the caller (Get) decides on discarding | consumed by channel.go:216; also called by Get at channel.go:124 |
| Release | application goroutine | external | none | consumed by channel.go:224 |
| Len | application goroutine | external | none | consumed by channel.go:246 |
| UV-Conn-nil | application goroutine | external (undesired variant of Put and Close) | nil instead of a connection | channel.go:168, 204 |
| UV-Put-dup | application goroutine | external (undesired variant of Put) | a connection already passed to Put once | channel.go:167 |
| UV-Close-dup | application goroutine | external (undesired variant of Close) | a connection already passed to Close once | channel.go:202 |
| UV-Put-foreign | application goroutine | external (undesired variant of Put) | a connection not created by this pool's Factory, or never borrowed | channel.go:167 |
| UV-Close-foreign | application goroutine | external (undesired variant of Close) | a connection not created by this pool's Factory, or never borrowed | channel.go:202 |

Internal deliveries (not matrix columns; they are results of calls the pool makes, see the abstraction statement of the matrix): hand-over of a connection to a waiting Get (channel.go:183, consumed at channel.go:137); return values of the Factory, Close and Ping callbacks (channel.go:83, 154, 212, 124).

## Gate-type annotation

Get, Release, Len branch on service-side state only. Put, Close and Ping branch first on payload content (nil connection, channel.go:168, 204, 217) and then on service-side state (conns nil, waiters present, idle channel full; close or ping function nil). No branch inspects the connection's identity or health except Get (idle age and Ping callback).

## Remembrance semantics

Ended connections (closed, discarded, handed out and returned) leave nothing behind except the counter `openingConns` and, for idle ones, nothing at all: there is no set of borrowed or closed connections, no tombstone, no generation. A late or repeated reference to an ended connection (Put or Close of a connection already closed or already stored) is indistinguishable from a live one and receives normal handling. Ended waiters (served) are removed from the queue (channel.go:179-182); a waiter cannot leave the queue by itself.

## Lock-discipline annotation

| section | lines | callbacks / events fired inside |
|---|---|---|
| getConns | channel.go:96-99 | none |
| Get slow path | channel.go:131-161 | Factory callback at channel.go:154 and logrus Debugf at channel.go:132 run while `c.mu` is held |
| Put | channel.go:172-198 | channel send to a waiter at channel.go:183 and non-blocking send at channel.go:190 while locked; `Close` (which locks) is called only after unlocking (channel.go:175-176, 194-196) |
| Close | channel.go:206-212 | the Close callback at channel.go:212 runs while `c.mu` is held (deferred unlock) |
| Release | channel.go:226-232 | none inside; the Close callback is called after unlocking (channel.go:241) |
| Ping | channel.go:216-221 | takes no lock; calls the Ping callback |
| Len | channel.go:246-248 | via getConns |

Reentrancy contract: no comment or README text says whether Factory, Close or Ping callbacks may call back into the pool (Config comments channel.go:25-30 are silent). A Factory or Close callback that calls any public method that locks `c.mu` blocks forever (Go mutex is not reentrant, NAT-06): documented nowhere (finding, Q-08). The Ping callback is invoked without the lock at channel.go:124 and channel.go:220.

## Undesired variants

| id | base event | category | description |
|---|---|---|---|
| UV-Conn-nil | Put, Close | value | nil connection (explicitly rejected in code) |
| UV-Put-dup | Put | duplication | the same connection offered to Put twice |
| UV-Close-dup | Close | duplication | the same connection passed to Close twice |
| UV-Put-foreign | Put | commission and value | a connection the pool did not create or that was never borrowed |
| UV-Close-foreign | Close | commission and value | same, for Close |

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| caller: Get | n/a: a call that never arrives is not observable by the pool | n/a: a late Get is an ordinary Get; timing is runtime (PA-19) | n/a: two Gets are two legal calls | n/a: Get after Release is the state Closed times Get | n/a: simultaneous Get and Release or Put are pairs P-02, P-04, P-06 | n/a: every Get is a legal call | n/a: Get has no payload |
| caller: Put | n/a: a connection never returned leaks capacity; the pool cannot observe it (caller obligation NAT-08) | n/a: a late Put is the same event; after Release it is the state Closed times Put | UV-Put-dup | n/a: Put after Release is the state Closed times Put | n/a: simultaneous Put with Release or Close is pairs P-01, P-05 | UV-Put-foreign | UV-Conn-nil, UV-Put-foreign |
| caller: Close | n/a: a connection never closed leaks capacity (NAT-08) | n/a: late Close is the same event | UV-Close-dup | n/a: Close after Release is the state Closed times Close | n/a: simultaneous Close with Get or Put is pairs P-03, P-05 | UV-Close-foreign | UV-Conn-nil, UV-Close-foreign |
| caller: Ping | n/a: Ping is not in the Pool interface; only same-package code calls it | n/a: same | n/a: repeated Ping is harmless | n/a: Ping after Release is the state Closed times Ping | n/a: simultaneous Ping and Release is pair P-06 | n/a: no legitimate trigger exists outside the package | n/a: nil is covered by UV-Conn-nil only for Put and Close; Ping(nil) is rejected at channel.go:217 |
| caller: Release | n/a: a Release that never comes leaves the pool open; not observable | n/a: late Release is the same event | n/a: second Release is the cell Closed times Release | n/a: not applicable, Release is the last event | n/a: simultaneous Release with Get or Put is pairs P-01, P-02, P-06 | n/a: every Release is a legal call | n/a: Release has no payload |
| caller: Len | n/a: not observable | n/a: late Len is the same event | n/a: repeated Len is harmless | n/a: Len after Release is the state Closed times Len | n/a: Len has no side effects | n/a: every Len is a legal call | n/a: Len has no payload |
| Factory callback | n/a: a factory error is the return value of a call the pool makes (a branch of Get and NewChannelPool, guard G-02), not an event delivered to the machine; outcome questions | n/a: a slow factory is a duration inside the call; effect (blocking under the lock) is lock-discipline, probe in the traces | n/a: one result per call | n/a: results are synchronous return values | n/a: one result per call | n/a: results exist only as return values | n/a: a nil connection with nil error is a plausible wrong payload, handled as a guard branch of Get |
| Close callback | n/a: a close error is the return value of a call the pool makes (Close, Release, Put, Get discards), not a delivered event | n/a: a slow close callback is a duration under the lock (lock-discipline) | n/a: one result per call | n/a: synchronous return value | n/a: one result per call | n/a: results exist only as return values | n/a: the result is an error value only |
| Ping callback | n/a: an invalid-connection verdict is the return value of a call the pool makes (guard in Get) | n/a: a slow ping is a duration outside the lock | n/a: one result per call | n/a: synchronous return value | n/a: one result per call | n/a: results exist only as return values | n/a: the result is an error value only |
| clock | n/a: the pool has no timer, the clock is read only inside Get | n/a: a delayed Get sees an expired connection (guard G-01) | n/a: not applicable | n/a: non-monotonic readings are excluded by NAT-07 | n/a: single reader | n/a: no timer fires | n/a: no payload |

## Upstream-guard annotation

The pool is a library; callers are application code outside this repository. Upstream of the boundary nothing validates arguments (the README usage, README.md:44-59, shows Get paired with Put and Release at shutdown). Validations present at the boundary: nil connection (channel.go:168, 204, 217), configuration (channel.go:59-67), closed pool (channel.go:106, 174). Absent at the boundary: origin check, duplicate check, borrowed-connection tracking, caller identity, cancellation, deadline.

## Interaction pairs

Pairs of events from different callers that reference the same pool or the same connection and can arrive near-simultaneously. Both orderings are listed.

| pair | events | entity | orderings |
|---|---|---|---|
| P-01a | Put then Release | the pool and the returned connection | Put completes before Release starts |
| P-01b | Release then Put | same | Release completes before Put starts |
| P-02a | waiting Get then Release | a queued waiter and the pool | the waiter is queued, then Release |
| P-02b | Release then Get at capacity | the pool | Release completes, then a Get whose first look at the pool predates it |
| P-03a | waiting Get then Close of a borrowed connection | a queued waiter and a borrowed connection | the waiter is queued, then another caller Closes a connection |
| P-03b | Close of a borrowed connection then Get at capacity | same | Close completes, then Get |
| P-04a | Get (idle channel empty) then Put | an empty idle channel | Get finds the channel empty, Put stores a connection, then Get takes its lock |
| P-04b | Put then Get | same | Put stores a connection before Get looks |
| P-05a | Put then Close of the same connection | one connection | the same connection is returned and then closed by two holders |
| P-05b | Close then Put of the same connection | same | closed first, then returned |
| P-06a | Get (ping configured) then Release | the ping function field | Get has read the ping field when Release runs |
| P-06b | Release then Get (ping configured) | same | Release completes, then Get with a channel snapshot taken earlier |

## Event annotations

### Get
- gate: service-side state only: conns nil or open, idle entries, openingConns against maxActive, factory nil, waiters
- upstream_guards: none upstream of this boundary (library API), absent here: cancellation, deadline, caller identity
- coverage:
  - loss: n/a: a call that never arrives is not observable by the pool
  - delay: n/a: timing is runtime (PA-19)
  - duplication: n/a: two Gets are two legal calls
  - out-of-order: n/a: Get after Release is the state Closed times Get
  - contradiction: n/a: simultaneous Get with Release or Put are pairs P-02, P-04, P-06
  - commission: n/a: every Get is a legal call
  - value: n/a: Get has no payload

### Put
- gate: payload content first (nil), then service-side state (conns nil, waiters present, idle channel full)
- upstream_guards: none upstream of this boundary, absent here: origin check, duplicate check, borrowed-connection tracking; present: nil check at channel.go:168
- coverage:
  - loss: n/a: a connection never returned leaks capacity and is not observable (caller obligation NAT-08)
  - delay: n/a: a late Put is the same event; after Release it is the state Closed times Put
  - duplication: UV-Put-dup
  - out-of-order: n/a: Put after Release is the state Closed times Put
  - contradiction: n/a: simultaneous Put with Release or Close are pairs P-01, P-05
  - commission: UV-Put-foreign
  - value: UV-Conn-nil, UV-Put-foreign

### Close
- gate: payload content first (nil), then service-side state (close function nil)
- upstream_guards: none upstream of this boundary, absent here: origin check, duplicate check, borrowed-connection tracking; present: nil check at channel.go:204
- coverage:
  - loss: n/a: a connection never closed leaks capacity (NAT-08)
  - delay: n/a: a late Close is the same event
  - duplication: UV-Close-dup
  - out-of-order: n/a: Close after Release is the state Closed times Close
  - contradiction: n/a: simultaneous Close with Get or Put are pairs P-03, P-05
  - commission: UV-Close-foreign
  - value: UV-Conn-nil, UV-Close-foreign

### Ping
- gate: payload content first (nil), then service-side state (ping function nil)
- upstream_guards: none upstream of this boundary, not part of the Pool interface; present: nil check at channel.go:217
- coverage:
  - loss: n/a: Ping is called only by same-package code
  - delay: n/a: same
  - duplication: n/a: repeated Ping is harmless
  - out-of-order: n/a: Ping after Release is the state Closed times Ping
  - contradiction: n/a: simultaneous Ping and Release is pair P-06
  - commission: n/a: no legitimate trigger exists outside the package
  - value: n/a: nil is rejected at channel.go:217 and is not a separate column for Ping

### Release
- gate: service-side state only (conns nil or open)
- upstream_guards: none upstream of this boundary, absent here: caller identity, drain of borrowed connections
- coverage:
  - loss: n/a: a Release that never comes is not observable
  - delay: n/a: a late Release is the same event
  - duplication: n/a: a second Release is the cell Closed times Release
  - out-of-order: n/a: Release is the last event
  - contradiction: n/a: simultaneous Release with Get or Put are pairs P-01, P-02, P-06
  - commission: n/a: every Release is a legal call
  - value: n/a: Release has no payload

### Len
- gate: service-side state only (conns nil or open)
- upstream_guards: none upstream of this boundary, nothing to validate
- coverage:
  - loss: n/a: not observable
  - delay: n/a: a late Len is the same event
  - duplication: n/a: repeated Len is harmless
  - out-of-order: n/a: Len after Release is the state Closed times Len
  - contradiction: n/a: Len has no side effects
  - commission: n/a: every Len is a legal call
  - value: n/a: Len has no payload
