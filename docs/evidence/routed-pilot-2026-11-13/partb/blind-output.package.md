You are the BLIND adversarial pass (Part B) of a domain-behaviour analysis. You have NO access to the implementation. Do NOT read any files, do NOT use any tools, do NOT search any repository — the inputs below are complete and are your ONLY sources. If you catch yourself wanting to look something up, label it an open point instead.

TASK: Here is the event catalogue of a component, and its requirements. For every event — including undesired variants and both orderings of every interaction pair — state in which situations the component should handle, ignore, or reject it, and what should happen. Describe situations in requirement terms. Name states per PA-17 (state naming convention): prefer public API names, name sub-states by their condition, use PascalCase with `_` as separator. If you must assume a lifecycle state the requirements do not name, label it `assumed-state:` with the condition that defines it. You have no access to the implementation. Be concrete. Produce a table keyed by the catalogue's event ids. End with a coverage checklist: every catalogue event id, listed once, ticked. A missing row must be impossible to miss.
>
<!-- generated:rules key=partb-vocab -->
The disposition vocabulary you must use (from the methods reference): `transition → <target>` | `handle` (stays in the state, does something) | `ignore (documented)` | `ignore (accidental)` | `defer (queued)` | `reject` (a declared refusal signal: error, diagnostic, nack) | `UNSPECIFIED`. Without these definitions a blind pass applies `reject` and `handle` to identical semantics interchangeably (dobby trigger-service, 2026-08-05: four vocabulary-only "divergences").
<!-- /generated:rules -->

The catalogue's event ids are: get put close_conn ping release len idle_expired ping_failed factory_error handoff UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 — plus the pair orderings P-01a P-01b P-02a P-02b P-03a P-03b P-04a P-04b P-05a P-05b.

=== INPUT 1: EVENT CATALOGUE (verbatim) ===

# Event catalogue — channelPool (silenceper/pool)

<!-- event-ids: get put close_conn ping release len idle_expired ping_failed factory_error handoff UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 -->

Sources:

* **owner** — the code that constructs the pool (`NewChannelPool`) and destroys it (`Release`).
* **user** — worker goroutines that call `Get`, `Put`, `Close`, `Ping`, `Len`. Any number of user goroutines call concurrently; the README and the code comments say nothing about thread safety, and every method takes the pool mutex except `Ping` (channel.go:220).
* **factory / close / ping callbacks** — user-supplied functions from `Config` (seams; no contract documented, channel.go:25-30).
* **clock** — idle age, evaluated only when `Get` takes a connection.
* **pool-internal** — the handoff from `Put` to a waiting `Get`.

Pool creation (`NewChannelPool`) is the initial transition of the machine, not a matrix column (see as-is.machine.mmd).

| id | event | source | classification | payload | produced at | consumed at |
|---|---|---|---|---|---|---|
| get | `Get()` — obtain a connection | user | external | none | caller | channel.go:103 |
| put | `Put(conn)` with a non-nil connection obtained from this pool | user | external | connection | caller | channel.go:167 |
| close_conn | `Close(conn)` — discard one connection obtained from this pool | user | external | connection | caller | channel.go:202 |
| ping | `Ping(conn)` — check one connection | user | external | connection | caller | channel.go:216 |
| release | `Release()` — destroy the pool | owner | external | none | caller | channel.go:224 |
| len | `Len()` — number of idle connections | user | external | none | caller | channel.go:246 |
| idle_expired | a connection taken by `Get` is older than IdleTimeout | clock | internal | connection + age | channel.go:116, channel.go:142 | Get loop |
| ping_failed | the Ping callback returns an error for a connection taken from the idle set | ping callback | internal | connection + error | channel.go:124 | Get loop |
| factory_error | the Factory callback returns an error inside `Get` | factory callback | internal | error | channel.go:154 | Get default branch |
| handoff | `Put` delivers a connection to the oldest waiting `Get` | pool-internal | internal | connection with new timestamp | channel.go:183 | channel.go:137 |
| UV-01 | get, delay: a waiting `Get` waits longer than its caller can tolerate | user | undesired | none | caller | channel.go:137 |
| UV-02 | put, loss: a connection obtained from the pool is never returned by `Put` or `Close` | user | undesired | none (absence) | caller | — |
| UV-03 | put, duplication: the same connection is `Put` twice | user | undesired | connection | caller | channel.go:167 |
| UV-04 | put, contradiction: `Put(c)` and `Close(c)` for the same connection near-simultaneously | user | undesired | connection | caller | channel.go:167, channel.go:202 |
| UV-05 | put, commission: `Put` of a connection that was never obtained from this pool | user | undesired | foreign connection | caller | channel.go:167 |
| UV-06 | put, value: `Put(nil)` | user | undesired | nil | caller | channel.go:168 |
| UV-07 | close_conn, duplication: `Close` twice for the same connection | user | undesired | connection | caller | channel.go:202 |
| UV-08 | close_conn, commission: `Close` of a connection that this pool did not hand out, or that is currently idle in the pool | user | undesired | foreign connection | caller | channel.go:202 |
| UV-09 | close_conn, value: `Close(nil)` | user | undesired | nil | caller | channel.go:203 |
| UV-10 | release, duplication: `Release` called twice (sequentially or concurrently) | owner | undesired | none | caller | channel.go:224 |
| UV-11 | ping, value: `Ping(nil)` | user | undesired | nil | caller | channel.go:217 |
| UV-12 | factory_error source, delay: the Factory callback blocks or is slow | factory callback | undesired | none | callback | channel.go:154 |

## Event annotations

### get
- gate: service-side state — idle set non-empty, then `openingConns >= maxActive`, then factory nil; a taken connection is further gated by its age and the Ping callback
- upstream_guards: none — no upstream validation exists; the library is called directly by user code, no rate or concurrency limit upstream of Get
- coverage:
  - loss: n/a: a Get that is never made changes no pool state; a Get that has started cannot be abandoned by its caller (no cancellation parameter, channel.go:103) 
  - delay: UV-01
  - duplication: n/a: a repeated Get is an independent second request; Get carries no request identity to duplicate
  - out-of-order: covered by the base column in the Released rows (a Get after Release is an ordinary Get in state Released) and by pair P-01
  - contradiction: covered by pair P-01 (Get vs Release); concurrent Gets from different users are normal operation serialized by the mutex
  - commission: n/a: Get is only issued by a user call; nothing inside the boundary issues Get spontaneously
  - value: n/a: Get has no payload

### put
- gate: payload content (nil check), then service-side state — conns nil (released), then waiters present, then idle set full
- upstream_guards: none — the pool does not verify that the connection came from this pool or is not already idle; only nil is rejected (channel.go:168)
- coverage:
  - loss: UV-02
  - delay: n/a: a late Put is an ordinary later Put; a Put that arrives after Release is the base column in the Released rows (pair P-02)
  - duplication: UV-03
  - out-of-order: covered by the base column in the Released rows and by pair P-02
  - contradiction: UV-04
  - commission: UV-05
  - value: UV-06

### close_conn
- gate: payload content (nil check), then service-side state — the close callback is nil after Release
- upstream_guards: none — the pool does not verify that the connection came from this pool, is checked out, or was not closed before; only nil is rejected (channel.go:203)
- coverage:
  - loss: n/a: a connection that is neither Put nor Closed is UV-02
  - delay: n/a: a late Close is an ordinary later Close; after Release it is the base column in the Released rows (pair P-03)
  - duplication: UV-07
  - out-of-order: covered by the base column in the Released rows and by pair P-03
  - contradiction: UV-04
  - commission: UV-08
  - value: UV-09

### ping
- gate: payload content (nil check) only; the call goes straight to the ping callback without the mutex and without a nil check of the callback
- upstream_guards: none — callers are not told whether a Ping callback is configured; NewChannelPool accepts a nil Ping (channel.go:78)
- coverage:
  - loss: n/a: Ping is a stateless pass-through; a missing call changes no pool state
  - delay: n/a: Ping holds no lock and changes no state; its latency is the callback's
  - duplication: n/a: stateless pass-through, a repeat changes no pool state
  - out-of-order: covered by the base column in the Released rows (callback cleared by Release) and by pair P-04
  - contradiction: covered by pair P-04 (Ping vs Release)
  - commission: n/a: Ping is only issued by a user call
  - value: UV-11

### release
- gate: service-side state — conns already nil (released before)
- upstream_guards: none — nothing prevents Release while user goroutines still hold connections or wait; ownership of the call is not enforced (any holder of the Pool may call it)
- coverage:
  - loss: n/a: a pool that is never released stays in its Open state; there is no event to dispose (the idle connections stay open until process exit)
  - delay: n/a: Release is synchronous; overlaps of its unlocked drain phase with user calls are the pairs P-01..P-05
  - duplication: UV-10
  - out-of-order: n/a: Release is the terminal lifecycle command; a second Release is UV-10, and there is no later lifecycle stage for it to arrive stale into
  - contradiction: covered by pairs P-01..P-05 (Release vs user calls)
  - commission: covered by pairs P-01..P-05: an unexpected Release from any holder races with user calls exactly as the owner's Release does
  - value: n/a: Release has no payload

### len
- gate: service-side state — conns nil gives 0
- upstream_guards: none
- coverage:
  - loss: n/a: read-only query, no state change
  - delay: n/a: read-only query; the result is a snapshot and may be stale on return (inferred)
  - duplication: n/a: read-only query
  - out-of-order: covered by the base column in the Released rows and by pair P-05
  - contradiction: covered by pair P-05 (Len vs Release)
  - commission: n/a: only issued by a user call
  - value: n/a: no payload

### idle_expired
- gate: payload content — the stored timestamp of the taken connection plus IdleTimeout versus now; disabled when IdleTimeout <= 0
- upstream_guards: none — expiry is evaluated only inside Get, lazily; no background reaper exists
- coverage:
  - loss: n/a: internal evaluation inside Get, nothing to lose
  - delay: n/a: lazy by design of the code — an expired connection stays idle until a Get takes it (recorded as extraction fact, no timer exists)
  - duplication: n/a: each taken connection is evaluated once per take
  - out-of-order: n/a: evaluated synchronously in the Get that took the connection
  - contradiction: n/a: a single evaluation per take
  - commission: n/a: only evaluated on a connection Get has taken
  - value: n/a: the timestamp is set by the pool itself (channel.go:88, :184, :190); a handed-off connection's age restarts at Put

### ping_failed
- gate: external callback result — the Ping callback's error for a connection taken from the idle set
- upstream_guards: none — evaluated only when a Ping callback is configured (channel.go:123) and only on the idle path, not on the handoff path
- coverage:
  - loss: n/a: internal, synchronous result
  - delay: n/a: a slow Ping callback delays only the calling Get (no lock held, channel.go:220)
  - duplication: n/a: one call per taken connection
  - out-of-order: n/a: synchronous within one Get
  - contradiction: n/a: single result
  - commission: n/a: only produced by a call the pool made
  - value: n/a: any non-nil error discards the connection; the error value is not inspected

### factory_error
- gate: external callback result — non-nil error from the Factory callback
- upstream_guards: none — the factory is called only when no idle connection was ready and openingConns < maxActive (channel.go:133, :150)
- coverage:
  - loss: n/a: internal, synchronous result
  - delay: UV-12
  - duplication: n/a: one call per Get iteration
  - out-of-order: n/a: synchronous under the mutex
  - contradiction: n/a: single result
  - commission: n/a: only produced by a call the pool made
  - value: n/a: any non-nil error is returned to the Get caller unchanged

### handoff
- gate: service-side state — connReqs non-empty when Put holds the mutex
- upstream_guards: none — Put removes the waiter from connReqs before the send (channel.go:180-183), so each waiter channel receives at most one send
- coverage:
  - loss: n/a: the waiter channel has capacity 1 (channel.go:134) and the send happens under the mutex; the waiting Get cannot abandon its receive (no cancellation), so a sent connection is always received
  - delay: n/a: delivery is a buffered send; the waiter wakes when scheduled
  - duplication: n/a: the waiter is removed from the queue before the single send
  - out-of-order: n/a: FIFO — Put always serves connReqs[0] (channel.go:180)
  - contradiction: n/a: one Put per handoff under the mutex
  - commission: n/a: only Put sends on a waiter channel; nothing ever closes one (the `!ok` branch at channel.go:138 has no producer)
  - value: n/a: the connection is the one passed to Put; its timestamp is reset to now (channel.go:184)

## Gate-type summary

| event | gate type | what decides |
|---|---|---|
| get | service-side state | idle set, openingConns vs maxActive, factory nil |
| put | payload content + service-side state | nil; conns nil; waiters; idle set full |
| close_conn | payload content + service-side state | nil; close callback nil (after Release) |
| ping | payload content | nil only |
| release | service-side state | conns nil |
| len | service-side state | conns nil |
| idle_expired | payload content | timestamp + IdleTimeout vs now |
| ping_failed / factory_error | external callback result | callback error |
| handoff | service-side state | connReqs non-empty |

## Remembrance semantics

* **Released pool.** Release leaves a pool object with conns, factory, ping and close set to nil (channel.go:227-231). It keeps `openingConns` at its last value and keeps `connReqs` unchanged (no line touches them in Release, channel.go:224-243). The pool is not reusable: no method restores conns. Late references resolve as follows: Get → `ErrClosed` (channel.go:105-106); Put and Close → return nil without calling any close callback (channel.go:174-176, :208-209) — the connection is neither kept nor closed; Len → 0; Ping → calls the nil callback (panic, channel.go:220); Release → returns at channel.go:234-235.
* **Waiters.** A waiter is an entry in `connReqs` (a channel of capacity 1). It ends when a Put serves it (removed before the send, channel.go:180-182). Nothing else removes or closes an entry: not Release, not Close, not an expiry. A waiter that exists at Release stays in `connReqs` forever and its Get stays blocked at channel.go:137. Bound: none (the slice grows with every waiting Get; no cap).
* **Connections.** The pool remembers idle connections only (with their timestamp) in `conns`, bounded by MaxIdle. A checked-out connection is remembered only as a count in `openingConns`; the pool keeps no identity of it. A late Put or Close for a connection therefore cannot be checked against anything: duplicates and foreign connections are accepted (UV-03, UV-05, UV-07, UV-08). After Release, checked-out connections are never closed by the pool.
* **Expired connections.** An idle connection past IdleTimeout remains in `conns` and counted in `openingConns` until a Get takes it and discards it (or Release closes it). Len counts it.

## Lock discipline

| critical section | lock site | callbacks or events inside | reentrancy contract |
|---|---|---|---|
| getConns | channel.go:96 | none | — |
| Get default branch | channel.go:131 | **Factory callback** (channel.go:154) runs with `mu` held; on success `openingConns++` | Not documented anywhere (README, Config comment channel.go:25). A factory that calls any pool method (Get, Put, Close, Len, Release) deadlocks: all take `mu` (sync.RWMutex is not reentrant). |
| Put | channel.go:172 | handoff send to a waiter (buffered, does not block) | Close is called after unlock (channel.go:175-176, :194-196) |
| Close | channel.go:206 + defer unlock | **Close callback** (channel.go:212) runs with `mu` held | Not documented (channel.go:27). A close callback that calls a pool method deadlocks. Release's drain calls the same callback without the lock (channel.go:241), so the deadlock depends on the path. |
| Release | channel.go:225 | none under the lock; the drain and close callbacks run after unlock (channel.go:232-242) | — |
| Ping | no lock | Ping callback | — |

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| user (get) | n/a: no state change; no cancellation exists  | UV-01 | n/a: independent request | Released rows + P-01 | P-01 | n/a: user-issued only | n/a: no payload |
| user (put) | UV-02 | n/a: later Put; after Release see P-02 | UV-03 | Released rows + P-02 | UV-04 | UV-05 | UV-06 |
| user (close_conn) | n/a: see UV-02 | n/a: later Close; after Release see P-03 | UV-07 | Released rows + P-03 | UV-04 | UV-08 | UV-09 |
| user (ping) | n/a: stateless | n/a: no lock, no state | n/a: stateless | Released rows + P-04 | P-04 | n/a: user-issued only | UV-11 |
| owner (release) | n/a: no event; pool stays open | n/a: synchronous; overlaps are P-01..P-05 | UV-10 | n/a: terminal command; repeat is UV-10 | P-01..P-05 | P-01..P-05 | n/a: no payload |
| user (len) | n/a: read-only | n/a: read-only | n/a: read-only | Released rows + P-05 | P-05 | n/a: user-issued only | n/a: no payload |
| factory callback (factory_error) | n/a: synchronous result | UV-12 | n/a: one call per iteration | n/a: synchronous | n/a: single result | n/a: pool-initiated only | n/a: error not inspected |

## Interaction pairs

Cross-source pairs between the **owner** (Release) and the **user** goroutines, on the shared entity "the pool instance" (and, for Put/Close, the connection the user holds). Both orderings get an id.

| id | first | second | shared entity |
|---|---|---|---|
| P-01a | get (in progress: waiting at channel.go:137, or inside the factory call) | release | pool / waiter queue |
| P-01b | release | get | pool |
| P-02a | put | release | pool / connection |
| P-02b | release | put (connection checked out before Release) | pool / connection |
| P-03a | close_conn | release | pool / connection |
| P-03b | release | close_conn (connection checked out before Release) | pool / connection |
| P-04a | ping | release | ping callback |
| P-04b | release | ping | ping callback |
| P-05a | len | release | idle set |
| P-05b | release | len | idle set |

Same-source races between user goroutines (Put vs Close of one connection, duplicate Put) are the undesired variants UV-03, UV-04, UV-07.


=== INPUT 2: REQUIREMENTS (/tmp/routed-pilot-EsX9/partb/requirements.md) ===

# pool
[![PkgGoDev](https://pkg.go.dev/badge/github.com/silenceper/pool)](https://pkg.go.dev/github.com/silenceper/pool)
[![Go Report Card](https://goreportcard.com/badge/github.com/silenceper/pool)](https://goreportcard.com/report/github.com/silenceper/pool)


[中文文档](./README_ZH_CN.md)

A golang universal network connection pool.

## Feature：

- More versatile, The connection type in the connection pool is `interface{}`, making it more versatile
- More configurable, The connection supports setting the maximum idle time, the timeout connection will be closed and discarded, which can avoid the problem of automatic connection failure when idle
- Support user setting `ping` method, used to check the connectivity of connection, invalid connection will be discarded
- Support connection waiting, When the connection pool is full, support for connection waiting (like the go db connection pool)

## Basic Usage:

```go

//factory Specify the method to create the connection
factory := func() (interface{}, error) { return net.Dial("tcp", "127.0.0.1:4000") }

//close Specify the method to close the connection
close := func(v interface{}) error { return v.(net.Conn).Close() }

//ping Specify the method to detect whether the connection is invalid
//ping := func(v interface{}) error { return nil }

//Create a connection pool: Initialize the number of connections to 5, the maximum idle connection is 20, and the maximum concurrent connection is 30
poolConfig := &pool.Config{
	InitialCap: 5,
	MaxIdle:   20,
	MaxCap:     30,
	Factory:    factory,
	Close:      close,
	//Ping:       ping,
	//The maximum idle time of the connection, the connection exceeding this time will be closed, which can avoid the problem of automatic failure when connecting to EOF when idle
	IdleTimeout: 15 * time.Second,
}
p, err := pool.NewChannelPool(poolConfig)
if err != nil {
	fmt.Println("err=", err)
}

//Get a connection from the connection pool
v, err := p.Get()

//do something
//conn=v.(net.Conn)

//Put the connection back into the connection pool, when the connection is no longer in use
p.Put(v)

//Release all connections in the connection pool, when resources need to be destroyed
p.Release()

//View the number of connections in the current connection pool
current := p.Len()


```


#### Remarks:
The connection pool implementation refers to pool [https://github.com/fatih/pool](https://github.com/fatih/pool) , thanks.


## License

The MIT License (MIT) - see LICENSE for more details


=== INPUT 3: EVENT CONTRACT TEXTS (/tmp/routed-pilot-EsX9/partb/contracts.md) ===

## pool.go:6

//ErrClosed 连接池已经关闭Error

## pool.go:10

// Pool 基本方法

## channel.go:13

//ErrMaxActiveConnReached 连接池超限

## channel.go:17

// Config 连接池相关配置

## channel.go:19

//连接池中拥有的最小连接数

## channel.go:21

//最大并发存活连接数

## channel.go:23

//最大空闲连接

## channel.go:25

//生成连接的方法

## channel.go:27

//关闭连接的方法

## channel.go:29

//检查连接是否有效的方法

## channel.go:31

//连接最大空闲时间，超过该事件则将失效

## channel.go:39

// channelPool 存放连接信息

## channel.go:57

// NewChannelPool 初始化连接

## channel.go:94

// getConns 获取所有连接

## channel.go:102

// Get 从pool中取一个连接

## channel.go:166

// Put 将连接放回pool中

## channel.go:201

// Close 关闭单条连接

## channel.go:215

// Ping 检查单条连接是否有效

## channel.go:223

// Release 释放连接池中所有连接

## channel.go:245

// Len 连接池中已有的连接


Respond with ONLY the table and the coverage checklist: every catalogue event id, listed once, ticked. A missing row must be impossible to miss.
The coverage checklist must use one exact line per event or pair in the form '- [x] EVENT_ID', with no other text on that line.
