# channelPool — extraction (Step 0 scope, Step 1 extraction)

Routing variant `flash-writes`, point 1: the five `draft-verify` drafts (files in `runs/draft-*.json`, tasks `runs/draft-*.task.txt`) are the extraction. Every kept claim's cited line was re-read by the agent against the file (rule 1); all 146 drafted claims had `citation_check: ok`. Items the drafts missed are marked `added by agent: <why>`. Provenance: channel.go/pool.go claims `observed-in-code`, channel_rpc_test.go claims `observed-in-tests`, README claims `explicit-requirement`.

## Step 0 — Scope statement

* **Machine boundary:** one `channelPool` instance (channel.go), created by `NewChannelPool`, as seen through the `Pool` interface (pool.go:11-21) plus the exported method `Ping` on the concrete type (channel.go:216).
* **Actors:** caller goroutines (Get, Put, Close, Release, Len, Ping); the user-supplied callbacks Factory, Close and Ping (Config, channel.go:26-30); the clock (idle-timeout comparison at Get time only; no timer exists).
* **Excluded:** the connections themselves and the network; logrus; the RPC test server; example/main.go (usage only).
* **Model links:** none (no neighbouring modelled component). The caller's connection lifecycle (borrow, use, return) lives outside this machine; the pool sees only Get/Put/Close.
* **Scope doubts:** see Q-20 (concurrency contract undocumented), Q-17 (degenerate configurations).
* **Temporal behaviour present:** yes (idle timeout, blocking wait for capacity, shutdown, concurrent callers), so rule 6 does not stop the run.

## Configuration parameters held fixed by the abstraction

Ping configured or not (`c.ping != nil`, channel.go:78), `IdleTimeout > 0` (channel.go:115), `MaxIdle`, `MaxCap`, `InitialCap` (validated at channel.go:59).

## Implicit state space (the reachable combinations)

Fields: `conns` (nil | channel holding 0..MaxIdle idle entries), `connReqs` (empty | n waiters), `openingConns` (counter), `factory/close/ping` (nil only after Release, channel.go:225-231).
Behaviourally distinct regions (PA-17 names, conditions in `runs/cells-*.task.json`):
Open_IdleAvailable, Open_IdleFull, Open_NoIdle_BelowCap, Open_NoIdle_AtCap, Open_Waiting_AtCap, Open_Waiting_BelowCap, Open_Waiting_IdleAvailable, Closed.
Open_Waiting_BelowCap is reachable because Close/discard decrement `openingConns` (channel.go:211) without touching `connReqs`; Open_Waiting_IdleAvailable is reachable because Get's `select` (channel.go:109) and its lock (channel.go:131) are separate critical sections. Both are derived from the code (inferred from interleaving), not from a test.

## Items added by the agent (drafts missed them)

* **A1** (added by agent: found while writing the Get cell) — `Get` reads `c.ping` at channel.go:123 without holding `c.mu`, while `Release` writes `c.ping = nil` under the lock (channel.go:229); `c.Ping` re-reads `c.ping` at channel.go:220 and calls it. observed-in-code.
* **A2** (added by agent: the draft raised it as a question only) — `Release` neither reads nor writes `connReqs` (channel.go:224-243); a goroutine blocked at channel.go:137 is not signalled. observed-in-code.
* **A3** (added by agent: pool.go draft listed methods, not the absence) — `Ping` is not part of the `Pool` interface (pool.go:11-21) but is an exported method of `*channelPool` (channel.go:216). observed-in-code.
* **A4** (added by agent: matrix walk) — `Close` (channel.go:202-213) and the discard paths in `Get` (channel.go:118, 125, 144) lower `openingConns` but never read `connReqs`. observed-in-code.
* **A5** (added by agent: matrix walk) — `Put` stamps a handed-off connection with `time.Now()` (channel.go:184), so the idle-timeout check on the waiter path (channel.go:141-147) compares against a just-created timestamp. observed-in-code.
* **A6** (added by agent: pair analysis) — `Get` takes the channel snapshot once (channel.go:104) and keeps selecting on that local variable (channel.go:110) after `Release` replaced `c.conns` with nil. observed-in-code.
* **A7** (added by agent: guard G-04) — the validation at channel.go:59 accepts `MaxCap = 0` and `MaxIdle = 0` (all three zero). observed-in-code.
* **A8** (added by agent: contradiction sweep) — the `Config` comment says InitialCap is "the minimum number of connections in the pool" (channel.go:19); the code only fills at construction (channel.go:82-89) and never replenishes. observed-in-code (comment vs code).
* **A9** (added by agent: contradiction sweep) — TestPool_Get expects `ErrMaxActiveConnReached` from the Get after MaxCap connections are borrowed (channel_rpc_test.go:94); the code blocks on `<-req` (channel.go:137) and returns that error only if `req` is closed (channel.go:139), which no code does. observed-in-tests vs observed-in-code.

## Contradictions between code, tests and docs

| # | sources | text | Q |
|---|---|---|---|
| 1 | channel_rpc_test.go:94 vs channel.go:134-139 | test expects an error at capacity; code waits | Q-21 |
| 2 | channel.go:19 vs channel.go:82-89 | InitialCap "minimum" vs initial fill only | Q-23 |
| 3 | README.md:15 ("connection waiting") vs channel.go:137 | waiting exists but is unbounded and `waitTimeOut` (channel.go:46) is unused | Q-02 |
| 4 | channel_rpc_test.go:54 vs :52 | message says poolConn, assertion says *rpc.Client | test quality, outside scope |
| 5 | channel_rpc_test.go:123 vs :121 | message prints 1, assertion uses MaxIdleCap | test quality, outside scope |

## Seam-contract sweep (rule 3: contracts read, not inferred)

| seam | invoked at | contract text available | failure semantics found | status |
|---|---|---|---|---|
| Factory | channel.go:83, 154 | Config comment channel.go:25 ("生成连接的方法") only | none stated: no error, panic, blocking or reentrancy contract. Test factory: channel_rpc_test.go:20-22 (`rpc.DialHTTP` returns error or client) | NAT-01, NAT-04; Q-08, Q-09 |
| Close callback | channel.go:212, 241 | channel.go:27 ("关闭连接的方法") only | none stated; test implementation `nc.Close()` channel_rpc_test.go:23-26 | NAT-01; Q-08, Q-10 |
| Ping callback | channel.go:220 | channel.go:29 ("检查连接是否有效的方法") only | none stated | NAT-01; Q-06 |
| sync.RWMutex (Lock) | channel.go:97, 131, 172, 206, 226 | Go standard library: not reentrant, blocks while held | callback that re-enters the pool under `c.mu` blocks forever | NAT-06 (language contract; the Go library is not in the repository, so no file:line) |
| channel operations | channel.go:110, 137, 183, 190, 238-239 | Go language specification | send on a closed channel panics; receive on a closed channel yields the zero value | NAT-06 |
| logrus Debugf | channel.go:132 | external library, not in repository | not read | `inferred`: no failure path claimed |

NAT candidates: NAT-01 callbacks are safe to call concurrently; NAT-02 callers pass only connections obtained from this pool, each at most once; NAT-03 callers stop using a connection after Put/Close; NAT-04 callbacks return and do not panic; NAT-05 configuration satisfies channel.go:59-67; NAT-06 Go mutex/channel semantics as above; NAT-07 `time.Now()` readings do not go backwards; NAT-08 callers eventually return borrowed connections. NAT-SYS-01: N pool instances share one server and observe its degradation together.

## Startup and shutdown

Startup: `NewChannelPool` validates (channel.go:59-67), presets `openingConns = InitialCap` (channel.go:75), calls the factory InitialCap times (channel.go:82-89), on the first error calls `Release` and returns the error (channel.go:84-86). Shutdown: `Release` (channel.go:224-243). Idempotent: second call returns at channel.go:234.

## Doctrine-line sweep (DOC-1..DOC-12)

| id | source | normative text (closely quoted) |
|---|---|---|
| DOC-1 | README.md:12 | connection type is `interface{}` |
| DOC-2 | README.md:13 | connections exceeding the maximum idle time are closed and discarded |
| DOC-3 | README.md:14 | user `ping`; invalid connections are discarded |
| DOC-4 | README.md:15 | when the pool is full, connection waiting is supported |
| DOC-5 | README.md:46 | Get a connection from the pool |
| DOC-6 | README.md:52 | Put the connection back when no longer in use |
| DOC-7 | README.md:55 | Release all connections when resources need to be destroyed |
| DOC-8 | README.md:58 | Len: number of connections currently in the pool |
| DOC-9 | channel.go:19 | InitialCap is the minimum number of connections in the pool |
| DOC-10 | channel.go:21 | MaxCap is the maximum number of concurrently live connections |
| DOC-11 | channel.go:23 | MaxIdle is the maximum number of idle connections |
| DOC-12 | pool.go:6 | ErrClosed means the pool has been closed |
| DOC-13 | README_ZH_CN.md:13 | channels are used to handle connections "efficiently" |

Sentence-by-sentence check of README.md lines 10-15, 41-59, README_ZH_CN.md lines 8-13 and the Config comments (channel.go:18-33): the drafts' 29+20 claims cover every sentence; the "versatile / efficient" adjectives are DOC-1 / DOC-13. Nothing added.
### Drafted claims — channel.go (observed-in-code)

| id | kind | cite | Jev | statement |
|---|---|---|---|---|
| channel:C1 | claim | channel.go:14 | unclear | The package defines ErrMaxActiveConnReached as an error message used when the max active connection limit is reached via the waiting-request channel path. |
| channel:C2 | claim | channel.go:18 | unclear | Config has InitialCap, MaxCap, MaxIdle, Factory, Close, Ping, and IdleTimeout fields. |
| channel:C3 | claim | channel.go:40 | supported | channelPool stores synchronization via sync.RWMutex, a conns channel of idleConn pointers, factory/close/ping callbacks, idleTimeout and waitTimeOut durations, maxActive and openingConns counters, and a connReqs slice of chan connReq. |
| channel:C4 | claim | channel.go:52 | supported | idleConn wraps a conn interface value and the time t it was recorded. |
| channel:C5 | claim | channel.go:59 | supported | NewChannelPool rejects configurations unless InitialCap <= MaxIdle, MaxCap >= MaxIdle, and InitialCap >= 0, returning error 'invalid capacity settings'. |
| channel:C6 | claim | channel.go:62 | supported | NewChannelPool rejects a nil Factory with error 'invalid factory func settings'. |
| channel:C7 | claim | channel.go:65 | supported | NewChannelPool rejects a nil Close with error 'invalid close func settings'. |
| channel:C8 | claim | channel.go:70 | unclear | NewChannelPool creates the conns channel with capacity MaxIdle, copies factory, close, idleTimeout, and maxActive from config, and sets openingConns to InitialCap. |
| channel:C9 | claim | channel.go:78 | supported | NewChannelPool sets the ping callback only when poolConfig.Ping is non-nil. |
| channel:C10 | claim | channel.go:83 | supported | NewChannelPool pre-fills the pool by calling factory InitialCap times; on factory error it invokes Release and returns a wrapped error. |
| channel:C11 | claim | channel.go:85 | supported | On factory failure during initialization, Release is called before returning the wrapped factory error. |
| channel:C12 | claim | channel.go:88 | supported | Each successfully factory-created initial connection is placed into conns as an idleConn with timestamp time.Now(). |
| channel:C13 | claim | channel.go:96 | unclear | getConns acquires the write lock, copies c.conns to a local, releases the lock, and returns the local channel. |
| channel:C14 | claim | channel.go:105 | supported | Get calls getConns and returns ErrClosed if the returned channel is nil. |
| channel:C15 | ordering | channel.go:108 | supported | Get loops selecting: first on receiving from conns, else defaulting to the slow path that locks c.mu. |
| channel:C16 | claim | channel.go:111 | supported | If a received wrapConn from conns is nil, Get returns ErrClosed. |
| channel:C17 | claim | channel.go:116 | supported | When idleTimeout > 0 and the idleConn timestamp plus timeout is before now, Get closes that connection and continues looping. |
| channel:C18 | claim | channel.go:123 | supported | If c.ping is non-nil, Get pings the connection; on ping error it closes the connection and continues looping. |
| channel:C19 | claim | channel.go:129 | supported | A connection that passes idle-timeout and ping checks is returned to the caller from Get. |
| channel:C20 | claim | channel.go:131 | unclear | In the default branch, Get acquires c.mu, logs openingConns and maxActive, and checks whether openingConns >= maxActive. |
| channel:C21 | claim | channel.go:134 | supported | When openingConns >= maxActive, Get creates a buffered connReq channel of capacity 1, appends it to connReqs, unlocks, then blocks receiving from that request channel. |
| channel:C22 | claim | channel.go:139 | supported | If the waiting request channel is closed (ok false), Get returns ErrMaxActiveConnReached. |
| channel:C23 | claim | channel.go:142 | supported | After receiving a connReq from the waiting channel, if idleTimeout > 0 and its timestamp is expired, Get closes that connection and continues the loop. |
| channel:C24 | claim | channel.go:148 | supported | A waited-for idleConn that is not expired is returned to the caller from Get. |
| channel:C25 | claim | channel.go:150 | supported | If c.factory is nil in the default path, Get unlocks and returns ErrClosed. |
| channel:C26 | claim | channel.go:154 | supported | In the default path below maxActive, Get invokes c.factory while holding c.mu; on error it unlocks and returns the error. |
| channel:C27 | claim | channel.go:159 | supported | On successful factory call in the default path, Get increments openingConns, unlocks, and returns the new connection. |
| channel:C28 | claim | channel.go:169 | supported | Put returns error 'connection is nil. rejecting' when conn is nil. |
| channel:C29 | claim | channel.go:172 | supported | Put acquires c.mu before inspecting conns and connReqs. |
| channel:C30 | claim | channel.go:174 | supported | If c.conns is nil in Put, it unlocks and delegates to Close(conn). |
| channel:C31 | ordering | channel.go:179 | supported | When connReqs is non-empty, Put takes the first waiting request, shifts the slice via copy, shrinks connReqs, sends a new idleConn with current time into the request, unlocks, and returns nil. |
| channel:C32 | ordering | channel.go:190 | supported | When connReqs is empty, Put tries a non-blocking send of a new idleConn into conns; on success it unlocks and returns nil. |
| channel:C33 | claim | channel.go:196 | supported | If the non-blocking send in Put's empty-connReqs branch fails, Put unlocks and calls Close(conn), returning its result. |
| channel:C34 | claim | channel.go:204 | supported | Close returns error 'connection is nil. rejecting' when conn is nil. |
| channel:C35 | claim | channel.go:206 | supported | Close acquires c.mu and defers its release. |
| channel:C36 | claim | channel.go:208 | contradicted | If c.close is nil, Close returns nil without decrementing openingConns. |
| channel:C37 | claim | channel.go:212 | supported | Close decrements openingConns then invokes c.close(conn) under the mutex. |
| channel:C38 | claim | channel.go:218 | supported | Ping returns error 'connection is nil. rejecting' when conn is nil. |
| channel:C39 | claim | channel.go:220 | supported | Ping directly invokes c.ping(conn); it does not acquire c.mu. |
| channel:C40 | claim | channel.go:225 | unclear | Release acquires c.mu, nils conns, factory, ping, and close, saves closeFun locally, then unlocks. |
| channel:C41 | claim | channel.go:234 | supported | Release returns immediately if the saved conns channel was nil. |
| channel:C42 | ordering | channel.go:238 | supported | Release closes the conns channel, then ranges over it calling closeFun on each connection. |
| channel:C43 | claim | channel.go:247 | supported | Len returns len(c.getConns()), which acquires and releases c.mu inside getConns. |
| channel:C44 | claim | channel.go:155 | unclear | Get's factory invocation in the default slow path occurs while c.mu is held, so the factory callback runs under the lock. |
| channel:C45 | claim | channel.go:207 | supported | Close's user-supplied close callback is invoked while c.mu is held (via deferred unlock). |
| channel:C46 | claim | channel.go:241 | supported | Release invokes closeFun on each connection after unlocking c.mu, so the close callback during Release runs without the lock. |
| channel:C47 | claim | channel.go:46 | supported | waitTimeOut is declared as a field but is never assigned or read in this file. |
| channel:C48 | claim | channel.go:86 | supported | Factory's error return in NewChannelPool is wrapped with 'factory is not able to fill the pool'. |

### Drafted claims — pool.go (observed-in-code)

| id | kind | cite | Jev | statement |
|---|---|---|---|---|
| pool:C1 | claim | pool.go:7 | supported | The exported variable ErrClosed is declared as an error created with errors.New whose text is "pool is closed". |
| pool:C2 | claim | pool.go:12 | supported | The Pool interface declares a method Get that takes no arguments and returns (interface{}, error). |
| pool:C3 | claim | pool.go:14 | supported | The Pool interface declares a method Put that takes one interface{} argument and returns an error. |
| pool:C4 | claim | pool.go:16 | supported | The Pool interface declares a method Close that takes one interface{} argument and returns an error. |
| pool:C5 | claim | pool.go:18 | supported | The Pool interface declares a method Release that takes no arguments and returns nothing. |
| pool:C6 | claim | pool.go:20 | supported | The Pool interface declares a method Len that takes no arguments and returns an int. |
| pool:C7 | claim | pool.go:6 | supported | The comment on ErrClosed states that it is the error for when the connection pool has already been closed. |
| pool:C8 | claim | pool.go:10 | supported | The comment on the Pool interface describes it as having basic methods. |

### Drafted claims — channel_rpc_test.go (observed-in-tests)

| id | kind | cite | Jev | statement |
|---|---|---|---|---|
| test:C1 | claim | channel_rpc_test.go:38 | supported | TestNew calls newChannelPool and reports an error if it fails. |
| test:C2 | claim | channel_rpc_test.go:39 | supported | TestNew defers p.Release(). |
| test:C3 | claim | channel_rpc_test.go:41 | supported | TestNew expects newChannelPool to return no error. |
| test:C4 | claim | channel_rpc_test.go:50 | supported | TestPool_Get_Impl gets a connection and expects no error. |
| test:C5 | claim | channel_rpc_test.go:52 | supported | TestPool_Get_Impl asserts the returned connection type-asserts to *rpc.Client. |
| test:C6 | claim | channel_rpc_test.go:54 | supported | TestPool_Get_Impl's failure message says the connection is not of type poolConn. |
| test:C7 | claim | channel_rpc_test.go:56 | supported | TestPool_Get_Impl puts the connection back into the pool. |
| test:C8 | claim | channel_rpc_test.go:69 | supported | TestPool_Get expects the pool length to equal InitialCap-1 after one Get. |
| test:C9 | ordering | channel_rpc_test.go:76 | supported | TestPool_Get launches MaximumCap-1 goroutines that each call Get, then waits on the WaitGroup. |
| test:C10 | claim | channel_rpc_test.go:82 | supported | TestPool_Get expects each concurrent Get to return no error. |
| test:C11 | claim | channel_rpc_test.go:88 | supported | TestPool_Get expects the pool length to be 0 after acquiring all connections. |
| test:C12 | claim | channel_rpc_test.go:94 | supported | TestPool_Get expects a further Get to return ErrMaxActiveConnReached. |
| test:C13 | claim | channel_rpc_test.go:101 | supported | TestPool_Put configures a pool with InitialCap 5, MaxCap 100, MaxIdle 10, and IdleTimeout 20s. |
| test:C14 | claim | channel_rpc_test.go:111 | supported | TestPool_Put fetches MaximumCap connections with Get into a slice. |
| test:C15 | claim | channel_rpc_test.go:118 | supported | TestPool_Put puts all MaximumCap connections back via Put. |
| test:C16 | claim | channel_rpc_test.go:121 | supported | TestPool_Put expects the pool length to equal MaxIdleCap after putting all back. |
| test:C17 | claim | channel_rpc_test.go:123 | supported | TestPool_Put's failure message formats the expected value as 1, not MaxIdleCap. |
| test:C18 | claim | channel_rpc_test.go:134 | supported | TestPool_UsedCapacity expects Len() to equal InitialCap initially. |
| test:C19 | claim | channel_rpc_test.go:146 | supported | TestPool_Close calls Release and then type-asserts the pool to *channelPool. |
| test:C20 | claim | channel_rpc_test.go:148 | supported | After Release, TestPool_Close expects the conns channel to be nil. |
| test:C21 | claim | channel_rpc_test.go:152 | supported | After Release, TestPool_Close expects c.factory to be nil. |
| test:C22 | claim | channel_rpc_test.go:157 | supported | After Release, TestPool_Close expects Get to return a non-nil error. |
| test:C23 | claim | channel_rpc_test.go:161 | supported | After Release, TestPool_Close expects Len() to be 0. |
| test:C24 | ordering | channel_rpc_test.go:171 | supported | TestPoolConcurrent starts a goroutine that calls p.Release while Get/Put goroutines are launched in a loop of MaximumCap iterations using an unbuffered pipe. |
| test:C25 | claim | channel_rpc_test.go:176 | supported | TestPoolConcurrent does not assert on any Get or Put results or errors. |
| test:C26 | claim | channel_rpc_test.go:183 | supported | TestPoolConcurrent's consumer returns early if the received connection is nil. |
| test:C27 | claim | channel_rpc_test.go:197 | supported | TestPoolWriteRead calls 'Arith.Multiply' with Args{1,2} over the rpc client. |
| test:C28 | claim | channel_rpc_test.go:199 | supported | TestPoolWriteRead expects the call to return no error. |
| test:C29 | claim | channel_rpc_test.go:201 | supported | TestPoolWriteRead expects resp to equal 2. |
| test:C30 | ordering | channel_rpc_test.go:218 | supported | TestPoolConcurrent2 launches 10 goroutines that Get, sleep a random duration, then call p.Close(conn). |
| test:C31 | claim | channel_rpc_test.go:216 | supported | TestPoolConcurrent2 does not assert on Get errors or results; it ignores them. |
| test:C32 | claim | channel_rpc_test.go:229 | unclear | TestPoolConcurrent2 launches a second set of 10 goroutines outside a wrapping goroutine that also Get, sleep, and Close. |
| test:C33 | claim | channel_rpc_test.go:234 | supported | TestPoolConcurrent2 waits on wg after launching goroutines. |
| test:C34 | claim | channel_rpc_test.go:238 | supported | TestPoolConcurrent3 is commented out. |
| test:C35 | claim | channel_rpc_test.go:239 | supported | The commented-out test pool construction line is also commented out. |
| test:C36 | claim | channel_rpc_test.go:257 | supported | newChannelPool builds a Config with InitialCap 5, MaxCap 100, MaxIdle 10, and IdleTimeout 20s, and calls NewChannelPool. |
| test:C37 | claim | channel_rpc_test.go:21 | supported | The factory dials RPC over tcp at the configured address. |
| test:C38 | claim | channel_rpc_test.go:24 | supported | The closeFac closes the value by asserting it to *rpc.Client. |
| test:C39 | claim | channel_rpc_test.go:32 | supported | The init function starts an rpcServer goroutine and sleeps 300ms. |
| test:C40 | claim | channel_rpc_test.go:271 | unclear | rpcServer registers Arith and serves HTTP on the configured address. |
| test:C41 | claim | channel_rpc_test.go:281 | supported | Arith.Multiply writes the product of args.A and args.B into reply and returns nil. |

### Drafted claims — README.md (explicit-requirement)

| id | kind | cite | Jev | statement |
|---|---|---|---|---|
| readme:C1 | claim | README.md:8 | supported | The pool is a golang universal network connection pool. |
| readme:C2 | claim | README.md:12 | supported | The connection type in the connection pool is interface{}, making it more versatile. |
| readme:C3 | claim | README.md:13 | supported | The connection supports setting the maximum idle time. |
| readme:C4 | claim | README.md:13 | supported | The timeout connection will be closed and discarded. |
| readme:C5 | claim | README.md:13 | supported | Setting the maximum idle time can avoid the problem of automatic connection failure when idle. |
| readme:C6 | claim | README.md:14 | supported | The pool supports user setting a ping method. |
| readme:C7 | claim | README.md:14 | supported | The ping method is used to check the connectivity of connection. |
| readme:C8 | claim | README.md:14 | supported | Invalid connection will be discarded. |
| readme:C9 | claim | README.md:15 | supported | The pool supports connection waiting. |
| readme:C10 | claim | README.md:15 | supported | When the connection pool is full, it supports connection waiting (like the go db connection pool). |
| readme:C11 | claim | README.md:21 | supported | The factory specifies the method to create the connection. |
| readme:C12 | claim | README.md:24 | supported | The close function specifies the method to close the connection. |
| readme:C13 | claim | README.md:27 | supported | The ping function specifies the method to detect whether the connection is invalid. |
| readme:C14 | claim | README.md:30 | supported | InitialCap initializes the number of connections to 5. |
| readme:C15 | claim | README.md:30 | supported | MaxIdle is the maximum idle connection, set to 20. |
| readme:C16 | claim | README.md:30 | supported | MaxCap is the maximum concurrent connection, set to 30. |
| readme:C17 | claim | README.md:38 | supported | IdleTimeout is the maximum idle time of the connection. |
| readme:C18 | claim | README.md:38 | supported | The connection exceeding the idle time will be closed. |
| readme:C19 | claim | README.md:38 | supported | The maximum idle time can avoid the problem of automatic failure when connecting to EOF when idle. |
| readme:C20 | claim | README.md:41 | supported | The pool is created with pool.NewChannelPool(poolConfig). |
| readme:C21 | claim | README.md:46 | supported | Get gets a connection from the connection pool. |
| readme:C22 | claim | README.md:47 | supported | The connection is retrieved from the pool via p.Get(). |
| readme:C23 | claim | README.md:52 | supported | The connection is put back into the connection pool when the connection is no longer in use. |
| readme:C24 | claim | README.md:53 | supported | The connection is returned via p.Put(v). |
| readme:C25 | claim | README.md:55 | supported | Release releases all connections in the connection pool when resources need to be destroyed. |
| readme:C26 | claim | README.md:56 | supported | Release is invoked via p.Release(). |
| readme:C27 | claim | README.md:58 | supported | Len views the number of connections in the current connection pool. |
| readme:C28 | claim | README.md:59 | supported | The current number of connections is obtained via p.Len(). |
| readme:C29 | claim | README.md:66 | supported | The connection pool implementation refers to pool github.com/fatih/pool. |

### Drafted claims — README_ZH_CN.md (explicit-requirement)

| id | kind | cite | Jev | statement |
|---|---|---|---|---|
| readme-zh:C1 | claim | README_ZH_CN.md:5 | supported | The connection pool is implemented in Golang. |
| readme-zh:C2 | claim | README_ZH_CN.md:10 | supported | The connection type inside the pool is interface{}, making it more general. |
| readme-zh:C3 | claim | README_ZH_CN.md:11 | supported | There is a maximum idle time for connections; connections exceeding it are closed and discarded, which can avoid automatic invalidation during idle. |
| readme-zh:C4 | claim | README_ZH_CN.md:12 | supported | The pool supports a user-set ping method to check connection connectivity; invalid connections are discarded. |
| readme-zh:C5 | claim | README_ZH_CN.md:13 | supported | Channels are used to handle connections in the pool, described as efficient. |
| readme-zh:C6 | claim | README_ZH_CN.md:20 | supported | The factory field is the method for creating connections, returning net.Dial to tcp 127.0.0.1:4000 in the example. |
| readme-zh:C7 | claim | README_ZH_CN.md:23 | supported | The close field is the method for closing a connection, calling Close on the net.Conn in the example. |
| readme-zh:C8 | claim | README_ZH_CN.md:26 | supported | The ping field is a method for checking connections, as shown commented out. |
| readme-zh:C9 | claim | README_ZH_CN.md:28 | supported | A connection pool is created with InitialCap 5, MaxIdle 20, and MaxCap 30 in the example. |
| readme-zh:C10 | claim | README_ZH_CN.md:30 | supported | The InitialCap configuration field is the initial number of connections in the resource pool. |
| readme-zh:C11 | claim | README_ZH_CN.md:31 | supported | The MaxIdle configuration field is the maximum number of idle connections. |
| readme-zh:C12 | claim | README_ZH_CN.md:32 | supported | The MaxCap configuration field is the maximum number of concurrent connections. |
| readme-zh:C13 | claim | README_ZH_CN.md:37 | supported | The IdleTimeout configuration field is the maximum idle time; connections exceeding this time are closed, which can avoid idle EOF and automatic invalidation. |
| readme-zh:C14 | claim | README_ZH_CN.md:39 | supported | A pool is created via pool.NewChannelPool using the poolConfig. |
| readme-zh:C15 | claim | README_ZH_CN.md:41 | supported | An error from pool.NewChannelPool is printed. |
| readme-zh:C16 | claim | README_ZH_CN.md:45 | supported | A connection is obtained from the pool via p.Get. |
| readme-zh:C17 | claim | README_ZH_CN.md:51 | supported | A connection is returned to the pool via p.Put. |
| readme-zh:C18 | claim | README_ZH_CN.md:54 | supported | All connections in the pool are released via p.Release. |
| readme-zh:C19 | claim | README_ZH_CN.md:57 | supported | The current number of connections is viewed via p.Len. |
| readme-zh:C20 | claim | README_ZH_CN.md:64 | supported | The pool is implemented with reference to fatih/pool, changing and adding some existing features. |
## Draft questions carried forward (routing rule 6)

`→ Q-nn` = ends as or folds into that question; `answered: file:line` = sources settle what the code does (intent, where the requirements are silent, sits in the Q named after it); `outside scope: why` = never about the component's own behaviour.

### channel.go (25)
| draft | disposition |
|---|---|
| q1 waitTimeOut purpose | → Q-02 |
| q2 Put send to req may block | answered: channel.go:134 (req has capacity 1), channel.go:180-183 (req removed from connReqs before the single send) |
| q3 Release and pending connReqs | → Q-01 |
| q4 expired handed-off conn, no replacement | answered: channel.go:144-145 (`continue` re-enters the loop, creates via channel.go:154); freed capacity not offered to other waiters → Q-03 |
| q5 no ping on waiter path | → Q-15 |
| q6 Close without lock on waiter path | answered: channel.go:136 (unlock before wait), channel.go:206 (Close locks itself) |
| q7 nil ret.idleConn | answered: channel.go:183-185 (only producer sets non-nil); the closed-channel case returns earlier at channel.go:138-140 |
| q8 no check between test and factory | answered: channel.go:131-159 (one critical section); factory under lock → Q-08 |
| q9 factory returns nil, nil | → Q-09 |
| q10 slice shift retains references | outside scope: GC/memory retention is runtime behaviour (PA-19), not a state transition |
| q11 Close with nil close func | → Q-05 |
| q12 Release ignores close errors | → Q-10 |
| q13 Put/Release race relies on mutex | answered: channel.go:172-176 and 225-232 (both under c.mu); unlocked readers in Get → Q-07 |
| q14 Get receive outside mutex, closed channel | answered: channel.go:110-113 (closed channel yields nil → ErrClosed); overlap with Release → Q-07 |
| q15 MaxCap 0 | → Q-17 |
| q16 `!ok` branch unreachable | → Q-02 |
| q17 RWMutex used as Mutex | outside scope: lock kind is performance (PA-19) |
| q18 factory error, no retry | answered: channel.go:155-158 (error returned to caller); retry/backoff intent → Q-22 |
| q19 callback concurrency contract | → Q-08 |
| q20 factory in flight during Release | → Q-08 |
| q21 openingConns vs idle | answered: channel.go:159 (++), channel.go:211 (--), channel.go:75: counts open connections (idle and borrowed); idle = len(conns) |
| q22 openingConns after constructor failure | → Q-19 |
| q23 no cancellation for waiters | → Q-02 |
| q24 two Puts to one req | answered: channel.go:180-183 (req dequeued before send) |
| q25 how maxActive is kept | answered: channel.go:133 and 159 (same critical section); bypass by foreign Put → Q-13 |

### pool.go (8)
q1 Get behaviour → Q-02, Q-21; q2 Put → Q-05, Q-11, Q-13; q3 Close → Q-10, Q-12, Q-14; q4 Release/ErrClosed → Q-01, Q-05; q5 Len → Q-18; q6 which methods return ErrClosed → answered: channel.go:106, 112, 152 (Get only); q7 other errors → answered: channel.go:14, 86, 169, 205 (ErrMaxActiveConnReached is never produced, see Q-02); q8 Chinese comment → outside scope: comment text carries no constraint beyond its gloss (pool.go:6, 10).

### channel_rpc_test.go (15)
q1 message poolConn → outside scope: test message text; q2 Close vs Put → answered: channel.go:167-213, intent Q-10/Q-12; q3 Len → Q-18; q4 error after Release → answered: channel.go:106 (ErrClosed); q5 TestPoolConcurrent without asserts → outside scope: test quality (listed in summary.md); q6 nil conn from pipe → answered: channel_rpc_test.go:176-186 (Get can return nil with ErrClosed after Release); q7 ordering of Release vs Get/Put → Q-01, Q-07 and pairs P-01..P-03; q8 commented-out signature → outside scope: commented code; q9 TestPoolConcurrent2 without asserts → outside scope: test quality; q10 wg.Add in goroutine → outside scope: test synchronisation; q11 message prints 1 → outside scope: test message; q12 is ErrMaxActiveConnReached reached → Q-21; q13 model after Release → answered: channel.go:226-231, intent Q-05; q14 TestPoolWriteRead no Put → outside scope: test hygiene; q15 zero config → Q-17.

### README.md (24)
q1 Get at capacity → Q-02, Q-21; q2 wait duration → Q-02; q3 timeout configurable → Q-02; q4 Get validates by ping → answered: channel.go:123-128; waiter path → Q-15; q5 when ping is called → answered: channel.go:123 (idle path of Get only), never in Put; → Q-15; q6 ping error → answered: channel.go:125-127 (closed, discarded, loop); q7 no Ping configured → answered: channel.go:123 (skipped); q8 InitialCap minimum? → Q-23; q9, q10, q11 idle beyond MaxIdle → answered: channel.go:189-196 (Put closes the connection; comment "连接池已满，直接关闭该连接"); q12 IdleTimeout when checked → Q-16; q13 expired on Get → answered: channel.go:115-120; q14 Get error returns nil conn → answered: channel.go:106, 112, 139, 152, 157 (nil with error); factory nil,nil → Q-09; q15 Release vs borrowed → answered: channel.go:226-241 (only idle entries touched); leak on later Put → Q-05; q16 usable after Release → answered: channel.go:106 (Get: ErrClosed); Put → Q-05; q17 Len → Q-18; q18 MaxCap hard limit → answered: channel.go:133, 159; bypass → Q-13; q19 factory error at creation → answered: channel.go:83-87 (all-or-nothing) → Q-19; q20 thread-safe → Q-20; q21 NewChannelPool errors → answered: channel.go:59-67, 86; q22 reopen after Release → answered: channel.go:228 (factory nil: no); q23 Put vs waiting Get ordering → answered: channel.go:179-185 (oldest waiter first); a later Get vs hand-off → Q-04; q24 never Put → answered: no tracking of borrowed connections (NAT-08); contract text → Q-20.

### README_ZH_CN.md (14)
q1, q2 → Q-02; q3 → answered: channel.go:189-196; q4 → Q-05; q5 → Q-15; q6 → Q-16; q7 → answered: timestamps are written only when a connection is stored (channel.go:184, 190), borrowed connections are not timed; q8 → answered: channel.go:123; q9 → Q-18; q10 → Q-20; q11 → answered: channel.go:59-67; q12 → answered: channel.go:125-127 (loop continues; caller never sees the failure); q13 → answered: channel.go:189-196; q14 → answered: channel.go:108-129.
