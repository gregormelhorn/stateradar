You are the BLIND adversarial pass (Part B) of a domain-behaviour analysis. You have NO access to the implementation. Do NOT read any files, do NOT use any tools, do NOT search any repository — the inputs below are complete and are your ONLY sources. If you catch yourself wanting to look something up, label it an open point instead.

TASK: Here is the event catalogue of a component, and its requirements. For every event — including undesired variants and both orderings of every interaction pair — state in which situations the component should handle, ignore, or reject it, and what should happen. Describe situations in requirement terms. Name states per PA-17 (state naming convention): prefer public API names, name sub-states by their condition, use PascalCase with `_` as separator. If you must assume a lifecycle state the requirements do not name, label it `assumed-state:` with the condition that defines it. You have no access to the implementation. Be concrete. Produce a table keyed by the catalogue's event ids. End with a coverage checklist: every catalogue event id, listed once, ticked. A missing row must be impossible to miss.

Catalogue headings and fields labelled `observed in code` say what the implementation does, not what it should do. Base each row on the requirements, the contracts and the doctrine lines. When a row's expected behaviour rests only on observed-in-code text, start its behaviour cell with `as-is:`.

<!-- generated:rules key=partb-vocab -->
The disposition vocabulary you must use (from the methods reference): `transition → <target>` | `handle` (stays in the state, does something) | `ignore (documented)` | `ignore (accidental)` | `defer (queued)` | `reject` (a declared refusal signal: error, diagnostic, nack) | `UNSPECIFIED`. Without these definitions a blind pass applies `reject` and `handle` to identical semantics interchangeably (dobby trigger-service, 2026-08-05: four vocabulary-only "divergences").
<!-- /generated:rules -->

The catalogue's event ids are: Get Put Close Ping Release Len UV-Conn-nil UV-Put-dup UV-Close-dup UV-Put-foreign UV-Close-foreign — plus the pair orderings P-01a P-01b P-02a P-02b P-03a P-03b P-04a P-04b P-05a P-05b P-06a P-06b.

=== INPUT 1: EVENT CATALOGUE (code fragments and analysis references removed) ===

# channelPool — event catalogue (Step 3)

<!-- event-ids: Get Put Close Ping Release Len UV-Conn-nil UV-Put-dup UV-Close-dup UV-Put-foreign UV-Close-foreign -->

The component is one connection pool instance (channel.go). Its states are named in the disposition matrix; the situations that define them: `Open_IdleAvailable` (idle connections present, fewer than MaxIdle, nobody waiting), `Open_IdleFull` (MaxIdle idle connections, nobody waiting), `Open_NoIdle_BelowCap` (no idle connection, nobody waiting, fewer open connections than MaxCap), `Open_NoIdle_AtCap` (no idle connection, nobody waiting, MaxCap open connections), `Open_Waiting_AtCap` (callers waiting, no idle connection, MaxCap reached), `Open_Waiting_BelowCap` (callers waiting, no idle connection, fewer than MaxCap open), `Open_Waiting_IdleAvailable` (callers waiting and an idle connection present), `Closed` (after Release).

## Events

| id | source | external/internal | payload gist | produced / consumed |
|---|---|---|---|---|
| Get | application goroutine | external | none | consumed by channel.go |
| Put | application goroutine | external | a connection (interface{}), non-nil | consumed by channel.go |
| Close | application goroutine | external | a connection, non-nil | consumed by channel.go |
| Ping | same-package caller (not in the Pool interface, pool.go) | external | a connection, non-nil | consumed by channel.go; also called by Get at channel.go |
| Release | application goroutine | external | none | consumed by channel.go |
| Len | application goroutine | external | none | consumed by channel.go |
| UV-Conn-nil | application goroutine | external (undesired variant of Put and Close) | nil instead of a connection | channel.go |
| UV-Put-dup | application goroutine | external (undesired variant of Put) | a connection already passed to Put once | channel.go |
| UV-Close-dup | application goroutine | external (undesired variant of Close) | a connection already passed to Close once | channel.go |
| UV-Put-foreign | application goroutine | external (undesired variant of Put) | a connection not created by this pool's Factory, or never borrowed | channel.go |
| UV-Close-foreign | application goroutine | external (undesired variant of Close) | a connection not created by this pool's Factory, or never borrowed | channel.go |

Internal deliveries (not matrix columns; they are results of calls the pool makes, see the abstraction statement of the matrix): hand-over of a connection to a waiting Get (channel.go, consumed at channel.go); return values of the Factory, Close and Ping callbacks (channel.go).

## Gate-type annotation (observed in code, not documented intent)

Get, Release, Len branch on service-side state only. Put, Close and Ping branch first on payload content (nil connection, channel.go) and then on service-side state (conns nil, waiters present, idle channel full; close or ping function nil). No branch inspects the connection's identity or health except Get (idle age and Ping callback).

## Remembrance semantics (observed in code, not documented intent)

Ended connections (closed, discarded, handed out and returned) leave nothing behind except the counter `openingConns` and, for idle ones, nothing at all: there is no set of borrowed or closed connections, no tombstone, no generation. A late or repeated reference to an ended connection (Put or Close of a connection already closed or already stored) is indistinguishable from a live one and receives normal handling. Ended waiters (served) are removed from the queue (channel.go); a waiter cannot leave the queue by itself.

## Lock-discipline annotation (observed in code, not documented intent)

| section | lines | callbacks / events fired inside |
|---|---|---|
| getConns | channel.go | none |
| Get slow path | channel.go | Factory callback at channel.go and logrus Debugf at channel.go run while `c.mu` is held |
| Put | channel.go | channel send to a waiter at channel.go and non-blocking send at channel.go while locked; `Close` (which locks) is called only after unlocking (channel.go) |
| Close | channel.go | the Close callback at channel.go runs while `c.mu` is held (deferred unlock) |
| Release | channel.go | none inside; the Close callback is called after unlocking (channel.go) |
| Ping | channel.go | takes no lock; calls the Ping callback |
| Len | channel.go | via getConns |

Reentrancy contract: no comment or README text says whether Factory, Close or Ping callbacks may call back into the pool (Config comments channel.go are silent). A Factory or Close callback that calls any public method that locks `c.mu` blocks forever (Go mutex is not reentrant): documented nowhere (finding). The Ping callback is invoked without the lock at channel.go and channel.go.

## Undesired variants

| id | base event | category | description |
|---|---|---|---|
| UV-Conn-nil | Put, Close | value | nil connection (explicitly rejected in code) |
| UV-Put-dup | Put | duplication | the same connection offered to Put twice |
| UV-Close-dup | Close | duplication | the same connection passed to Close twice |
| UV-Put-foreign | Put | commission and value | a connection the pool did not create or that was never borrowed |
| UV-Close-foreign | Close | commission and value | same, for Close |

## Undesired-coverage (observed in code, not documented intent)

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| caller: Get | n/a: a call that never arrives is not observable by the pool | n/a: a late Get is an ordinary Get; timing is runtime | n/a: two Gets are two legal calls | n/a: Get after Release is the state Closed times Get | n/a: simultaneous Get and Release or Put are pairs P-02, P-04, P-06 | n/a: every Get is a legal call | n/a: Get has no payload |
| caller: Put | n/a: a connection never returned leaks capacity; the pool cannot observe it (caller obligation) | n/a: a late Put is the same event; after Release it is the state Closed times Put | UV-Put-dup | n/a: Put after Release is the state Closed times Put | n/a: simultaneous Put with Release or Close is pairs P-01, P-05 | UV-Put-foreign | UV-Conn-nil, UV-Put-foreign |
| caller: Close | n/a: a connection never closed leaks capacity | n/a: late Close is the same event | UV-Close-dup | n/a: Close after Release is the state Closed times Close | n/a: simultaneous Close with Get or Put is pairs P-03, P-05 | UV-Close-foreign | UV-Conn-nil, UV-Close-foreign |
| caller: Ping | n/a: Ping is not in the Pool interface; only same-package code calls it | n/a: same | n/a: repeated Ping is harmless | n/a: Ping after Release is the state Closed times Ping | n/a: simultaneous Ping and Release is pair P-06 | n/a: no legitimate trigger exists outside the package | n/a: nil is covered by UV-Conn-nil only for Put and Close; Ping(nil) is rejected at channel.go |
| caller: Release | n/a: a Release that never comes leaves the pool open; not observable | n/a: late Release is the same event | n/a: second Release is the cell Closed times Release | n/a: not applicable, Release is the last event | n/a: simultaneous Release with Get or Put is pairs P-01, P-02, P-06 | n/a: every Release is a legal call | n/a: Release has no payload |
| caller: Len | n/a: not observable | n/a: late Len is the same event | n/a: repeated Len is harmless | n/a: Len after Release is the state Closed times Len | n/a: Len has no side effects | n/a: every Len is a legal call | n/a: Len has no payload |
| Factory callback | n/a: a factory error is the return value of a call the pool makes (a branch of Get and NewChannelPool, guard), not an event delivered to the machine; outcome questions | n/a: a slow factory is a duration inside the call; effect (blocking under the lock) is lock-discipline, probe in the traces | n/a: one result per call | n/a: results are synchronous return values | n/a: one result per call | n/a: results exist only as return values | n/a: a nil connection with nil error is a plausible wrong payload, handled as a guard branch of Get |
| Close callback | n/a: a close error is the return value of a call the pool makes (Close, Release, Put, Get discards), not a delivered event | n/a: a slow close callback is a duration under the lock (lock-discipline) | n/a: one result per call | n/a: synchronous return value | n/a: one result per call | n/a: results exist only as return values | n/a: the result is an error value only |
| Ping callback | n/a: an invalid-connection verdict is the return value of a call the pool makes (guard in Get) | n/a: a slow ping is a duration outside the lock | n/a: one result per call | n/a: synchronous return value | n/a: one result per call | n/a: results exist only as return values | n/a: the result is an error value only |
| clock | n/a: the pool has no timer, the clock is read only inside Get | n/a: a delayed Get sees an expired connection (guard) | n/a: not applicable | n/a: non-monotonic readings are excluded by | n/a: single reader | n/a: no timer fires | n/a: no payload |

## Upstream-guard annotation (observed in code, not documented intent)

The pool is a library; callers are application code outside this repository. Upstream of the boundary nothing validates arguments (the README usage, README.md, shows Get paired with Put and Release at shutdown). Validations present at the boundary: nil connection (channel.go), configuration (channel.go), closed pool (channel.go). Absent at the boundary: origin check, duplicate check, borrowed-connection tracking, caller identity, cancellation, deadline.

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

## Event annotations (observed in code, not documented intent)

### Get
- gate (observed in code): service-side state only: conns nil or open, idle entries, openingConns against maxActive, factory nil, waiters
- upstream_guards (observed in code): none upstream of this boundary (library API), absent here: cancellation, deadline, caller identity
- coverage:
  - loss: n/a: a call that never arrives is not observable by the pool
  - delay: n/a: timing is runtime
  - duplication: n/a: two Gets are two legal calls
  - out-of-order: n/a: Get after Release is the state Closed times Get
  - contradiction: n/a: simultaneous Get with Release or Put are pairs P-02, P-04, P-06
  - commission: n/a: every Get is a legal call
  - value: n/a: Get has no payload

### Put
- gate (observed in code): payload content first (nil), then service-side state (conns nil, waiters present, idle channel full)
- upstream_guards (observed in code): none upstream of this boundary, absent here: origin check, duplicate check, borrowed-connection tracking; present: nil check at channel.go
- coverage:
  - loss: n/a: a connection never returned leaks capacity and is not observable (caller obligation)
  - delay: n/a: a late Put is the same event; after Release it is the state Closed times Put
  - duplication: UV-Put-dup
  - out-of-order: n/a: Put after Release is the state Closed times Put
  - contradiction: n/a: simultaneous Put with Release or Close are pairs P-01, P-05
  - commission: UV-Put-foreign
  - value: UV-Conn-nil, UV-Put-foreign

### Close
- gate (observed in code): payload content first (nil), then service-side state (close function nil)
- upstream_guards (observed in code): none upstream of this boundary, absent here: origin check, duplicate check, borrowed-connection tracking; present: nil check at channel.go
- coverage:
  - loss: n/a: a connection never closed leaks capacity
  - delay: n/a: a late Close is the same event
  - duplication: UV-Close-dup
  - out-of-order: n/a: Close after Release is the state Closed times Close
  - contradiction: n/a: simultaneous Close with Get or Put are pairs P-03, P-05
  - commission: UV-Close-foreign
  - value: UV-Conn-nil, UV-Close-foreign

### Ping
- gate (observed in code): payload content first (nil), then service-side state (ping function nil)
- upstream_guards (observed in code): none upstream of this boundary, not part of the Pool interface; present: nil check at channel.go
- coverage:
  - loss: n/a: Ping is called only by same-package code
  - delay: n/a: same
  - duplication: n/a: repeated Ping is harmless
  - out-of-order: n/a: Ping after Release is the state Closed times Ping
  - contradiction: n/a: simultaneous Ping and Release is pair P-06
  - commission: n/a: no legitimate trigger exists outside the package
  - value: n/a: nil is rejected at channel.go and is not a separate column for Ping

### Release
- gate (observed in code): service-side state only (conns nil or open)
- upstream_guards (observed in code): none upstream of this boundary, absent here: caller identity, drain of borrowed connections
- coverage:
  - loss: n/a: a Release that never comes is not observable
  - delay: n/a: a late Release is the same event
  - duplication: n/a: a second Release is the cell Closed times Release
  - out-of-order: n/a: Release is the last event
  - contradiction: n/a: simultaneous Release with Get or Put are pairs P-01, P-02, P-06
  - commission: n/a: every Release is a legal call
  - value: n/a: Release has no payload

### Len
- gate (observed in code): service-side state only (conns nil or open)
- upstream_guards (observed in code): none upstream of this boundary, nothing to validate
- coverage:
  - loss: n/a: not observable
  - delay: n/a: a late Len is the same event
  - duplication: n/a: repeated Len is harmless
  - out-of-order: n/a: Len after Release is the state Closed times Len
  - contradiction: n/a: Len has no side effects
  - commission: n/a: every Len is a legal call
  - value: n/a: Len has no payload


=== INPUT 2b: DOCTRINE LINES (from the extraction) ===

| DOC-1 | README.md | connection type is `interface{}` |
| DOC-2 | README.md | connections exceeding the maximum idle time are closed and discarded |
| DOC-3 | README.md | user `ping`; invalid connections are discarded |
| DOC-4 | README.md | when the pool is full, connection waiting is supported |
| DOC-5 | README.md | Get a connection from the pool |
| DOC-6 | README.md | Put the connection back when no longer in use |
| DOC-7 | README.md | Release all connections when resources need to be destroyed |
| DOC-8 | README.md | Len: number of connections currently in the pool |
| DOC-9 | channel.go | InitialCap is the minimum number of connections in the pool |
| DOC-10 | channel.go | MaxCap is the maximum number of concurrently live connections |
| DOC-11 | channel.go | MaxIdle is the maximum number of idle connections |
| DOC-12 | pool.go | ErrClosed means the pool has been closed |
| DOC-13 | README_ZH_CN.md | channels are used to handle connections "efficiently" |

=== INPUT 2: REQUIREMENTS (README.md) ===

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


=== INPUT 2: REQUIREMENTS (README_ZH_CN.md) ===

# pool
[![PkgGoDev](https://pkg.go.dev/badge/github.com/silenceper/pool)](https://pkg.go.dev/github.com/silenceper/pool)
[![Go Report Card](https://goreportcard.com/badge/github.com/silenceper/pool)](https://goreportcard.com/report/github.com/silenceper/pool)

Golang 实现的连接池


## 功能：

- 连接池中连接类型为`interface{}`，使得更加通用
- 连接的最大空闲时间，超时的连接将关闭丢弃，可避免空闲时连接自动失效问题
- 支持用户设定 ping 方法，检查连接的连通性，无效的连接将丢弃
- 使用channel处理池中的连接，高效

## 基本用法

```go

//factory 创建连接的方法
factory := func() (interface{}, error) { return net.Dial("tcp", "127.0.0.1:4000") }

//close 关闭连接的方法
close := func(v interface{}) error { return v.(net.Conn).Close() }

//ping 检测连接的方法
//ping := func(v interface{}) error { return nil }

//创建一个连接池： 初始化5，最大空闲连接是20，最大并发连接30
poolConfig := &pool.Config{
	InitialCap: 5,//资源池初始连接数
	MaxIdle:   20,//最大空闲连接数
	MaxCap:     30,//最大并发连接数
	Factory:    factory,
	Close:      close,
	//Ping:       ping,
	//连接最大空闲时间，超过该时间的连接 将会关闭，可避免空闲时连接EOF，自动失效的问题
	IdleTimeout: 15 * time.Second,
}
p, err := pool.NewChannelPool(poolConfig)
if err != nil {
	fmt.Println("err=", err)
}

//从连接池中取得一个连接
v, err := p.Get()

//do something
//conn=v.(net.Conn)

//将连接放回连接池中
p.Put(v)

//释放连接池中的所有连接
p.Release()

//查看当前连接中的数量
current := p.Len()


```


#### 注:
该连接池参考 [https://github.com/fatih/pool](https://github.com/fatih/pool) 实现，改变以及增加原有的一些功能。


## License

The MIT License (MIT) - see LICENSE for more details


=== INPUT 3: EVENT CONTRACT TEXTS (blind-inputs/contracts.md) ===

# Contract text of the pool's events (doc comments copied verbatim from the source, headed by file:line)

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

## channel.go:57

// NewChannelPool 初始化连接

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
