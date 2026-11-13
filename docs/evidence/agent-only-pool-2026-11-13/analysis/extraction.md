# channelPool — Extraction (Step 0 + Step 1)

Repository: github.com/silenceper/pool @ 6084537. Pack: stateradar a331dae, prompt 02-pilot v1.17.
Model routing: not configured (agent-only run; routing OFF by instruction). Every step below is done by the pilot agent itself.

## CONFIG

```text
Component under analysis:   channelPool (channel.go)
Entry points / public API:  NewChannelPool, Pool interface (pool.go:11-21): Get, Put, Close, Release, Len;
                            exported method channelPool.Ping (not in the interface)
Related tests:              channel_rpc_test.go
Requirements / docs:        README.md, README_ZH_CN.md, doc comments in channel.go / pool.go
Output directory:           domain-analysis/channelPool/
```

## Step 0 — Scope statement

**Machine boundary.** One `channelPool` instance (channel.go:40-50) from the moment `NewChannelPool` publishes it to its caller until the process drops it. The machine is the pool's bookkeeping: the idle queue `conns` (buffered channel, capacity MaxIdle), the live-connection counter `openingConns`, the FIFO waiter list `connReqs`, the callback slots `factory` / `close` / `ping`, and the mutex `mu`.

**Actors.**
* Caller goroutines (any number, concurrent): `Get`, `Put`, `Close`, `Release`, `Len`, `Ping`.
* User-supplied seams invoked by the pool: `Factory` (create), `Close` callback (destroy), `Ping` (validate) — Config fields channel.go:25-30.
* The clock: `time.Now()` is read at `Put`/construction (timestamp) and at `Get` (idle-age check). There is no timer or background goroutine.

**Excluded.** The connection objects themselves (their protocol, their own failure), the network, the logrus logger (channel.go:132, debug output only), the example program (example/main.go, a usage demo), the `Pool` interface's other possible implementations (none exist in the repo).

**Model links.** None: no neighbouring component of this repository is modelled. Behaviour that surfaces here but belongs to the user is the callback contracts (Factory/Close/Ping); cells that depend on them cite the NAT assumptions, not a local defect.

Scope doubts go to the open questions (Q-11: whether `Ping` — exported, but not part of `Pool` — is public API).

## Step 1 — Extraction

### State variables (observed-in-code)

| Variable | Meaning | Where |
|---|---|---|
| `conns chan *idleConn` | idle queue, FIFO, capacity MaxIdle; `nil` after Release | channel.go:42 ("conns                    chan *idleConn"), set channel.go:70, nil-ed channel.go:227 |
| `openingConns int` | count of live connections the pool believes exist (idle + checked out) | channel.go:48, init channel.go:75 ("openingConns: poolConfig.InitialCap"), ++ channel.go:159, -- channel.go:211 |
| `maxActive int` | MaxCap | channel.go:74 ("maxActive:    poolConfig.MaxCap") |
| `connReqs []chan connReq` | FIFO list of blocked Get callers (each a 1-buffered channel) | channel.go:49, append channel.go:135, pop channel.go:179-182 |
| `factory / close / ping` | callbacks; all three set to nil by Release | channel.go:228-231 |
| `idleTimeout` | max idle age; `<= 0` disables the check | channel.go:73, read channel.go:115, channel.go:141 |
| `waitTimeOut` | declared, never assigned or read | channel.go:46 ("idleTimeout, waitTimeOut time.Duration"); grep: no other occurrence |
| `mu sync.RWMutex` | only `Lock`/`Unlock` are used (no RLock anywhere) | channel.go:41 |

Abbreviations used throughout: i = len(conns) (idle count), M = cap(conns) = MaxIdle, o = openingConns, X = maxActive = MaxCap, w = len(connReqs).

### Reachable state combinations

Implicit state = (conns nil?, i vs 0 vs M, o vs X, w vs 0, mutex held by a creating Get?). Dispositions differ on: i ≥ 1 (Get takes idle), i = M (Put closes), o ≥ X (Get waits), w ≥ 1 (Put hands off), mutex held during factory (others block), conns nil (Released).

| Leaf state | Condition | Reachable how |
|---|---|---|
| Open_Idle | conns≠nil, 1 ≤ i < M, w = 0 | Put with no waiter (channel.go:190); construction with 0 < InitialCap < MaxIdle |
| Open_IdleFull | i = M ≥ 1, w = 0 | Put fills the last slot; construction with InitialCap = MaxIdle ≥ 1 |
| Open_Empty_BelowCap | i = 0, o < X, w = 0 | construction with InitialCap = 0 < MaxCap; Gets drain idle |
| Open_Empty_AtCap | i = 0, o ≥ X, w = 0 | Gets create up to X (channel.go:159) |
| Open_Waiting | i = 0, o ≥ X, w ≥ 1 | Get at cap appends a waiter (channel.go:135) |
| Open_Waiting_BelowCap | i = 0, o < X, w ≥ 1 | Close / discard decrements o (channel.go:211) without waking a waiter — inferred from the absence of any wake-up in Close (channel.go:202-213) |
| Open_Waiting_IdleStranded | i ≥ 1, w ≥ 1 | a Put enqueues to idle in the window between a Get's empty `select` (channel.go:130 "default:") and its `c.mu.Lock()` (channel.go:131); that Get then registers as a waiter. inferred, confirmed by as-is test T10 |
| Open_Creating | a Get holds `mu` while `factory()` runs | channel.go:131 lock … channel.go:154 factory … channel.go:160 unlock |
| Released | conns = nil, factory = close = ping = nil | Release (channel.go:224-243); also construction failure (channel.go:85), but that instance is never returned |

Not reachable: conns≠nil with factory = nil (both nil-ed together under the lock, channel.go:226-228). i > M (channel capacity). Combinations with M = 0: Open_Idle and Open_IdleFull do not exist; Put with no waiter always closes (unbuffered send in a `select` with `default`).

### External events (caller API)

| Event | Provenance |
|---|---|
| NewChannelPool(cfg) — validates (channel.go:59 "if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {"), requires Factory (channel.go:62) and Close (channel.go:65), pre-fills InitialCap conns (channel.go:82-89); on factory error releases and returns error (channel.go:84-86) | observed-in-code |
| Get() | channel.go:103-164 |
| Put(conn) | channel.go:167-199 |
| Close(conn) | channel.go:202-213 |
| Release() | channel.go:224-243 |
| Len() | channel.go:246-248 |
| Ping(conn) — exported on `*channelPool`, not part of `Pool` | channel.go:216-221; pool.go:11-21 |

### Internal events

| Event | Provenance |
|---|---|
| factory result (conn, err) — synchronous, under `mu` | channel.go:154 ("conn, err := c.factory()") |
| idle conn's age passes IdleTimeout — no timer; noticed lazily when a Get dequeues it | channel.go:115-121; no goroutine or timer in the file (inferred from reading all 248 lines) |
| ping result — synchronous, no lock held | channel.go:123-127 |
| close-callback result — synchronous, under `mu` when reached via Close | channel.go:206-212; outside `mu` in Release (channel.go:241) |
| hand-off to a waiter (connReq delivered) | send channel.go:183 ("req <- connReq{"), receive channel.go:137 ("ret, ok := <-req") |

### Transitions, guards, actions (observed-in-code)

* **Get, pool released before Get starts:** `conns == nil` → `ErrClosed` (channel.go:105-106).
* **Get, idle available:** dequeue oldest (channel.go:110). Guard chain: closed channel yields nil → `ErrClosed` (channel.go:111-112); `idleTimeout > 0` and `t+timeout < now` → `c.Close(conn)` (o−1, close callback) and loop (channel.go:115-120); ping configured and ping error → `c.Close(conn)` and loop (channel.go:123-126); else return conn (channel.go:129). Boundary: `Before` is strict, so age = timeout is *not* expired.
* **Get, idle empty:** lock (channel.go:131). `o >= X` → append waiter, unlock, block on the waiter channel with **no timeout** (channel.go:133-137). Else `factory == nil` → `ErrClosed` (channel.go:150-152). Else call factory **under the lock** (channel.go:154); error → return it, o unchanged (channel.go:155-157); success → o+1, return conn (channel.go:159-161).
* **Get, woken waiter:** `!ok` → `ErrMaxActiveConnReached` (channel.go:138-139) — no code ever closes a waiter channel (grep: no `close(req` anywhere), so this branch is unreachable (inferred). Expired hand-off → `c.Close`, loop (channel.go:141-146). Else return (channel.go:148). The waiter path does **not** ping (compare channel.go:123 vs channel.go:141-148).
* **Put:** nil → error "connection is nil. rejecting" (channel.go:168-169), before the lock. Lock. `conns == nil` → unlock, `return c.Close(conn)` (channel.go:174-176). Waiters → pop oldest, send `{conn, now}`, unlock, return nil (channel.go:179-187). Else non-blocking enqueue with timestamp now (channel.go:190); idle full → unlock, `return c.Close(conn)` (channel.go:193-196). Put never changes o (a returned conn stays live).
* **Close:** nil → error (channel.go:203-204). Lock (held to the end, channel.go:206-207). `close == nil` (only after Release) → return nil **without calling any close function and without o−1** (channel.go:208-209). Else o−1 and call the close callback under the lock, return its error (channel.go:211-212). No identity check: any value decrements o. No waiter is woken.
* **Ping:** nil → error (channel.go:217-218); else `c.ping(conn)` with no nil check and no lock (channel.go:220).
* **Release:** under lock: capture conns, set conns/factory/ping/close to nil, unlock (channel.go:225-232). `conns == nil` → return (channel.go:234-235, idempotent). Close the channel, drain it, call the captured close function on every idle conn, errors ignored (channel.go:238-242). Waiters (`connReqs`) and o are untouched; checked-out conns are not closed.
* **Len:** `len(c.getConns())` = idle count; 0 after Release (len of nil channel) (channel.go:247).

### Timeouts and timers

* Idle timeout: checked only at dequeue time (lazy), channel.go:115, channel.go:141. No reaper.
* Wait timeout: none. `waitTimeOut` field is dead (channel.go:46). A Get at cap waits until a Put hands it a conn.
* No timeout on factory, ping or close callbacks.

### Retry behaviour

* The Get loop retries after discarding an expired or ping-failed idle conn (`continue`, channel.go:119, channel.go:126, channel.go:145). Bounded by the number of idle conns plus creation; no counter. Factory errors are not retried: returned to the caller (channel.go:155-157).

### Cancellation paths

* None. `Get` takes no context; a blocked waiter cannot cancel (channel.go:137). Release does not wake waiters.

### Failure modes

* Factory error → error to the Get caller; at construction → whole construction fails and already created conns are closed via Release (channel.go:84-86).
* Close-callback error → returned by Close and by Put-when-full; ignored in the Get discard path (channel.go:118, channel.go:125, channel.go:144: return value unused) and in Release (channel.go:241).
* Ping error → conn discarded (o−1), Get loops.

### Lock discipline (feeds Step 3)

| Critical section | Calls made while `mu` is held |
|---|---|
| getConns channel.go:96-98 | none |
| Get default branch channel.go:131-161 | `log.Debugf` (channel.go:132), **user Factory** (channel.go:154) |
| Put channel.go:172-197 | non-blocking sends only (waiter channel has buffer 1, channel.go:134; enqueue is in a `select` with `default`) |
| Close channel.go:206-213 | **user Close callback** (channel.go:212, lock released by `defer`) |
| Release channel.go:225-232 | none (close callback called after unlock, channel.go:241) |

`sync.Mutex` is not reentrant. A Factory or Close callback that calls any pool method that locks `mu` (Get default branch, Put, Close, Release, Len) deadlocks. No doc states a reentrancy contract (Config comments channel.go:25-30 say only what each function does).

### Apparent invariants (candidates for Step 5)

* o counts live conns; o ≤ X (channel.go:21 comment "最大并发存活连接数", max concurrent live connections).
* i ≤ M (channel capacity).
* A Get never returns a conn idle longer than IdleTimeout (both paths check).
* With Ping configured, a conn returned by Get passed ping — holds on the idle path only.

### Contradictions between code, tests and docs

| # | Contradiction | Sources |
|---|---|---|
| C-1 | Test expects `Get` at cap to return `ErrMaxActiveConnReached`; code blocks forever (no waiter channel is ever closed). The error's comment "连接池超限" (pool limit exceeded) suggests an error return; README says the pool waits. | channel_rpc_test.go:93-95 ("if err != ErrMaxActiveConnReached {"); channel.go:13-14; channel.go:137-139; README.md:15 |
| C-2 | InitialCap is commented as the *minimum* number of conns ("连接池中拥有的最小连接数"); README calls it the initial number. Code never replenishes: expiry/Close drop below it. | channel.go:19; README.md:30; channel.go:115-120 |
| C-3 | README: Release "Release all connections in the connection pool"; code closes only idle conns; checked-out conns returned later are not closed (Close is a no-op once `close == nil`). | README.md:55; channel.go:223; channel.go:208-209 |
| C-4 | Close's comment "关闭单条连接" (close a single connection); after Release it closes nothing and returns nil. | channel.go:201; channel.go:208-209 |
| C-5 | README promises waiting "like the go db connection pool"; database/sql waits are cancellable by context — no cancellation or timeout here, and `waitTimeOut` exists unused. | README.md:15; channel.go:46; channel.go:137 |
| C-6 | Ping configured: README says invalid conns are discarded; a conn handed to a waiter is returned without ping. | README.md:14; channel.go:141-148 |

### Behaviour that cannot be determined from the sources

* Whether a factory may return `(conn, err)` both non-nil, or `(nil, nil)` (Config comment channel.go:25-26 only "生成连接的方法").
* Whether callbacks may block, panic, or call back into the pool.
* Whether `Len` is meant to count idle or all connections (README.md:58 "View the number of connections in the current connection pool"; TestPool_Get asserts the idle count, channel_rpc_test.go:69).

### Doctrine-line sweep (DOC-n)

Every normative sentence from README.md, README_ZH_CN.md and the doc comments. Lines that say the same thing in both languages share one DOC id (both sources listed).

| DOC | Sentence (quoted or translated) | Source |
|---|---|---|
| DOC-1 | "The connection type in the connection pool is `interface{}`" | README.md:12; README_ZH_CN.md:10 |
| DOC-2 | "the timeout connection will be closed and discarded" (max idle time) | README.md:13; README.md:38; README_ZH_CN.md:11 |
| DOC-3 | "Support user setting `ping` method … invalid connection will be discarded" | README.md:14; README_ZH_CN.md:12 |
| DOC-4 | "When the connection pool is full, support for connection waiting (like the go db connection pool)" | README.md:15 |
| DOC-5 | "Put the connection back into the connection pool, when the connection is no longer in use" | README.md:52; README_ZH_CN.md:50 |
| DOC-6 | "Release all connections in the connection pool, when resources need to be destroyed" | README.md:55; README_ZH_CN.md:53; channel.go:223 ("释放连接池中所有连接") |
| DOC-7 | "View the number of connections in the current connection pool" (Len) | README.md:58; README_ZH_CN.md:56; channel.go:245 |
| DOC-8 | MaxCap = "maximum concurrent connection" / "最大并发存活连接数" (max concurrent live conns) | README.md:30; channel.go:21 |
| DOC-9 | MaxIdle = "maximum idle connection" / "最大空闲连接" | README.md:30; channel.go:23 |
| DOC-10 | InitialCap = "Initialize the number of connections" vs "连接池中拥有的最小连接数" (minimum conns in the pool) | README.md:30; channel.go:19 |
| DOC-11 | IdleTimeout = "连接最大空闲时间，超过该事件则将失效" (max idle time; beyond it the conn is invalid) | channel.go:31 |
| DOC-12 | ErrMaxActiveConnReached = "连接池超限" (pool limit exceeded) | channel.go:13 |
| DOC-13 | ErrClosed = "连接池已经关闭Error" (pool already closed) | pool.go:6 |
| DOC-14 | Close: "关闭单条连接" (close one connection) | channel.go:201 |
| DOC-15 | Get: "从pool中取一个连接" (take a connection from the pool) | channel.go:102 |
| DOC-16 | Put: "将连接放回pool中" (put the connection back into the pool) | channel.go:166 |
| DOC-17 | "使用channel处理池中的连接，高效" (connections handled by a channel, efficient) | README_ZH_CN.md:13 |
| DOC-18 | "The connection pool implementation refers to pool fatih/pool" | README.md:66; README_ZH_CN.md:64 |

Step 5 maps each line.

### Seam-contract sweep

| Seam | Contract text found | Failure semantics recorded | NAT candidate |
|---|---|---|---|
| Factory `func() (interface{}, error)` | channel.go:25 comment "生成连接的方法" (method that creates a connection); README.md:21 "Specify the method to create the connection" | none stated: no statement on blocking, on `(conn, err)` both non-nil, on `(nil, nil)`, on panics, on reentrancy | NAT-1 (result shape), NAT-2 (bounded time), NAT-3 (no reentry) — all unconfirmed by any contract → Q-07, Q-08 |
| Close callback `func(interface{}) error` | channel.go:27 "关闭连接的方法"; README.md:24 | none stated | NAT-2, NAT-3 → Q-08 |
| Ping `func(interface{}) error` | channel.go:29 "检查连接是否有效的方法" (method that checks whether a conn is valid); README.md:27 "detect whether the connection is invalid" | non-nil error = invalid (inferred from the README wording and channel.go:124) | NAT-2 |
| `time.Now` / `Time.Before` | Go standard library: `time.Now` carries a monotonic reading and comparisons between two such values use it | monotonic, not affected by wall-clock jumps (stdlib contract, not repository text) | NAT-6 |
| logrus `Debugf` | external library; debug-level output only | not modelled | — |

Missing error handling at a call site is not taken as evidence: e.g. the discarded close-callback error at channel.go:118 is recorded as "error value unused", not as "close never fails".
