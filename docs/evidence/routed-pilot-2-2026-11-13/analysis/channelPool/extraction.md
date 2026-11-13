# channelPool — Step 0 scope and Step 1 extraction

Pilot prompt: StateRadar `prompts/02-pilot.md` v1.17 (pack a331dae).
Repository: github.com/silenceper/pool at 6084537e520652192f41aebfd88d822c00b9447a.
Model routing: on (Flash drafts via `draft-verify`, Jev checks). Draft outputs and task files: the `routing/` directory of the evidence bundle (outside the repository).

## CONFIG

```text
Component under analysis:   channelPool (channel.go)
Entry points / public API:  NewChannelPool, Pool interface (pool.go): Get, Put, Close, Release, Len;
                            exported but not in the interface: (*channelPool).Ping (reachable only by type assertion)
Related tests:              channel_rpc_test.go
Requirements / docs:        README.md, README_ZH_CN.md, Go doc comments in channel.go and pool.go,
                            example/main.go (usage example)
Output directory:           domain-analysis/channelPool/
```

## Step 0 — Scope statement

**Machine boundary.** One `channelPool` instance after a successful `NewChannelPool`: the idle-connection channel `conns`, the open-connection counter `openingConns`, the waiter queue `connReqs`, the three user callbacks (`factory`, `close`, `ping`), the idle-timeout check, and the mutex `mu` that serialises them (channel.go:40-50). Construction (`NewChannelPool`) is modelled as the initial transition, not as an event on an instance: no caller holds the instance before the constructor returns (channel.go:91 ("return c, nil")).

**Actors.**

* Callers of the `Pool` interface (any number of goroutines): `Get`, `Put`, `Close`, `Release`, `Len`.
* User-supplied callbacks invoked by the pool: `Factory`, `Close`, `Ping` (Config, channel.go:25-30).
* The clock: idle age is compared with `time.Now()` (channel.go:116 ("wrapConn.t.Add(timeout).Before(time.Now())")).
* The remote resource behind the connections (for example a TCP server); it is visible to the pool only through the callbacks' results.

**Excluded.** The connections' own protocol behaviour; the remote server; logrus internals (one `log.Debugf` call, channel.go:132); the example program's server; Go runtime scheduling (PA-19).

**Model links.** No neighbouring component of this repository is modelled. Behaviour that surfaces here but lives elsewhere: (1) connection validity is decided by the user's `Ping` and connection creation by the user's `Factory` — the pool can only react to their results; (2) the waiting caller's lifecycle (a goroutine blocked in `Get`) is a separate track that the pool owns only through `connReqs` (PA-21/PA-24).

**Temporal behaviour present (rule 6 does not apply):** blocking waits (channel.go:137 ("ret, ok := <-req")), idle timeout (channel.go:115-116), lifecycle end (`Release`, channel.go:224), concurrent callers.

## Step 1 — Extraction (with provenance)

### States and context (implicit state space)

The struct carries no state enum. The state is the combination of these fields:

| Field | Meaning | Provenance |
|---|---|---|
| `conns` (buffered chan, cap `MaxIdle`) | idle connections, each with a timestamp; `nil` after Release | observed-in-code channel.go:70 ("conns:        make(chan *idleConn, poolConfig.MaxIdle),"), channel.go:227 ("c.conns = nil") |
| `openingConns` (int) | connections created and not yet closed through the pool (idle + checked out) | observed-in-code channel.go:75 ("openingConns: poolConfig.InitialCap,"), channel.go:159 ("c.openingConns++"), channel.go:211 ("c.openingConns--") |
| `maxActive` (int) | `MaxCap` | observed-in-code channel.go:74 ("maxActive:    poolConfig.MaxCap,") |
| `connReqs` ([]chan connReq) | FIFO queue of blocked `Get` callers, each with a 1-buffered channel | observed-in-code channel.go:134-135 ("c.connReqs = append(c.connReqs, req)") |
| `factory`, `close`, `ping` | user callbacks; all set to `nil` by Release; `ping` is nil when not configured | observed-in-code channel.go:71-79, channel.go:228-231 |
| `idleTimeout` | `IdleTimeout`; `<= 0` disables the expiry check | observed-in-code channel.go:115 ("if timeout := c.idleTimeout; timeout > 0 {") |
| `waitTimeOut` | declared, never assigned or read in the repository | observed-in-code channel.go:46 ("idleTimeout, waitTimeOut time.Duration"); `grep waitTimeOut` finds only this line |
| `mu` (sync.RWMutex) | only `Lock`/`Unlock` are used, never `RLock` | observed-in-code channel.go:41, channel.go:96, 131, 172, 206, 225 |

Behaviourally distinct reachable combinations (PA-17 rule 4; each changes the disposition of at least one event):

| State | Condition | Reachable how |
|---|---|---|
| `Open_IdleAvailable` | `conns != nil`, 0 < idle < MaxIdle, no waiter | construction with `0 < InitialCap < MaxIdle`; Put |
| `Open_IdleFull` | idle == MaxIdle, no waiter | construction with `InitialCap == MaxIdle > 0`; Put |
| `Open_Empty` | idle == 0, openingConns < MaxCap, no waiter | construction with `InitialCap == 0 < MaxCap`; Get of the last idle connection below the cap; Close |
| `Open_AtCapacity` | idle == 0, openingConns >= MaxCap, no waiter | Get creates the MaxCap-th connection; construction with `MaxCap == 0` |
| `Open_AtCapacity_Waiting` | idle == 0, openingConns >= MaxCap, ≥1 waiter | Get in `Open_AtCapacity` (channel.go:133-137) |
| `Open_Waiting_Stranded` | ≥1 waiter while idle > 0 or openingConns < MaxCap | Close while waiters wait (channel.go:211 decrements and wakes nobody); Put racing with a Get between the Get's empty `select` and its `Lock` (channel.go:130-135) — inferred from the code structure, see the traces |
| `Released` | `conns == nil`, callbacks nil | Release (channel.go:225-232) |

Flag combinations not reachable: idle > 0 with `conns == nil` (Release drains the channel it closed, channel.go:238-242 — but see the stale-snapshot race in the catalogue); `MaxIdle == 0` makes `Open_IdleFull` and `Open_Empty` coincide (unbuffered `conns`, every Put without a waiter closes the connection) — noted as a guard boundary, not a separate state.

### External events (Pool interface)

| Event | Behaviour | Provenance |
|---|---|---|
| `NewChannelPool(cfg)` (initial transition) | validates `InitialCap <= MaxIdle && MaxCap >= MaxIdle && InitialCap >= 0`, `Factory != nil`, `Close != nil`; creates `InitialCap` connections; on a factory error calls `Release` and returns an error | observed-in-code channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {"), channel.go:62, 65, 82-89, channel.go:85 ("c.Release()") |
| `Get()` | snapshot `conns` under the lock; if nil → `ErrClosed`; loop: non-blocking receive of an idle connection (discard if expired or ping fails, then retry); else under the lock: at capacity → enqueue a waiter and block; factory nil → `ErrClosed`; else call factory **while holding the lock**, `openingConns++` | observed-in-code channel.go:104-163, channel.go:154 ("conn, err := c.factory()") |
| `Put(conn)` | nil → error; under the lock: released → `Close(conn)` after unlock; a waiter exists → hand the connection to the oldest waiter (fresh timestamp); else non-blocking enqueue; channel full → `Close(conn)` after unlock | observed-in-code channel.go:168-198 |
| `Close(conn)` | nil → error; under the lock (deferred unlock): `close == nil` → return nil; else `openingConns--` and call the user close callback **while holding the lock** | observed-in-code channel.go:203-212, channel.go:207 ("defer c.mu.Unlock()") |
| `Release()` | under the lock: take `conns`, set `conns`, `factory`, `ping`, `close` to nil; after unlock: if `conns` was nil return; `close(conns)`; drain and call the saved close callback on each idle connection | observed-in-code channel.go:225-242 |
| `Len()` | `len(getConns())` — idle connections only; takes the lock | observed-in-code channel.go:247 ("return len(c.getConns())"), channel.go:96 |
| `Ping(conn)` (exported method, not in `Pool`) | nil → error; calls `c.ping(conn)` without a nil check and without the lock | observed-in-code channel.go:217-220 ("return c.ping(conn)") |

### Internal events

| Event | Behaviour | Provenance |
|---|---|---|
| idle age passes `IdleTimeout` | no timer; checked only when `Get` receives the connection (idle path) or a waiter receives a handed-off connection | observed-in-code channel.go:115-116, channel.go:141-142; no goroutine is started anywhere in channel.go (inferred from a full read) |
| waiter delivery (`connReq`) | Put sends one `connReq` into the 1-buffered `req` channel while holding the lock; the waiter receives it after Put unlocks | observed-in-code channel.go:183-186 |
| factory result (conn, err) | err → returned to the Get caller, `openingConns` unchanged; ok → `openingConns++` | observed-in-code channel.go:155-161 |
| close-callback result | returned by `Close`; ignored by Get's discard paths (channel.go:118, 125, 144) and by Release (channel.go:241) | observed-in-code channel.go:212 ("return c.close(conn)"), channel.go:241 ("closeFun(wrapConn.conn)") |
| ping result | error → discard (`Close`) and retry; nil → return the connection | observed-in-code channel.go:124-127 |

### Guards and conditions

Formalised in `check_guards.py`; groups G-01 … G-09 (guard notes in the matrix). Summary:

* G-01 construction validation (channel.go:59-67).
* G-02 idle-expiry decision on the idle path (channel.go:115-116), same expression on the waiter path (channel.go:141-142).
* G-03 ping validity (channel.go:123-124): depends on the user callback — not formalisable (external-call).
* G-04 Get slow path: capacity → wait; factory nil → `ErrClosed`; factory error → error; else create (channel.go:133, 150, 155). The capacity test precedes the released test.
* G-05 waiter wake-up: request channel closed → `ErrMaxActiveConnReached`; expired → discard and retry; else deliver (channel.go:138-148). No code closes a request channel (full read of channel.go; `close(` occurs only at channel.go:238 on `conns`).
* G-06 Put routing (channel.go:168, 174, 179, 189-196).
* G-07 Close routing (channel.go:203, 208).
* G-08 Release routing (channel.go:234).
* G-09 Get entry: nil snapshot → `ErrClosed`; received nil from a closed channel → `ErrClosed` (channel.go:105, 111).

### Actions and side effects

* User `factory` called from Get under `mu` (channel.go:154) and from the constructor without contention (channel.go:83).
* User `close` called from `Close` under `mu` (channel.go:212); `Close` is reached from Get's discard paths (channel.go:118, 125, 144 — all outside the lock), from Put (channel.go:176, 196 — after unlocking), and by callers. Release calls the saved callback outside the lock (channel.go:241).
* User `ping` called from Get outside the lock (channel.go:124 → channel.go:220).
* `log.Debugf` under `mu` (channel.go:132).

### Timeouts, timers, retries, cancellation

* Idle timeout: lazy, see internal events. No background reaper.
* Wait timeout: none. `waitTimeOut` is unused (channel.go:46). A waiter blocks until a Put hands it a connection (channel.go:137).
* Retry: the Get loop retries after each discard (channel.go:119, 126, 145 `continue`); each retry consumes an idle connection or needs a new handoff. No retry of factory errors (channel.go:157).
* Cancellation: none. `Get` takes no context and has no other exit from the wait (channel.go:103, 137).

### Failure modes

* `ErrClosed` ("pool is closed", pool.go:7) from Get after Release (channel.go:106, 112, 152).
* `ErrMaxActiveConnReached` (channel.go:14) only when a request channel is closed (channel.go:138-139) — no code path closes one.
* Factory errors returned unwrapped from Get (channel.go:157); wrapped at construction (channel.go:86).
* `"connection is nil. rejecting"` from Put, Close, Ping (channel.go:169, 204, 218).
* Close-callback errors: see internal events.

### Apparent invariants (candidates; classified in Step 5)

* idle ≤ MaxIdle (channel capacity, channel.go:70).
* openingConns counts idle + checked-out connections, assuming every connection is returned exactly once (inferred from channel.go:159, 211 and the absence of any ownership record).
* waiters exist only when idle == 0 and openingConns ≥ MaxCap (intended reading of channel.go:133-135; not maintained by Close or by the Get/Put race — see Step 5).

### Contradictions between code, tests and docs

1. Test `TestPool_Get` expects `ErrMaxActiveConnReached` from a Get at capacity (channel_rpc_test.go:93-95 ("if err != ErrMaxActiveConnReached {")); the code blocks that Get (channel.go:137). Executed: the test hangs until the test timeout (existing-test replay in `as-is-validation.md`).
2. Config comment calls `InitialCap` the minimum number of connections in the pool (channel.go:19 ("连接池中拥有的最小连接数")); README calls it the initial number (README.md:30 ("Initialize the number of connections to 5")), README_ZH_CN.md:30 ("资源池初始连接数")); code fills it only at construction (channel.go:82-89).
3. `ErrMaxActiveConnReached` is documented as "pool limit exceeded" (channel.go:13 ("连接池超限")) while README promises waiting when full (README.md:15).
4. README "the number of connections in the current connection pool" (README.md:58) vs `Len` returning the idle count only (channel.go:247); the tests assert the idle count (channel_rpc_test.go:69).

### Behaviour that cannot be determined from the sources

* Whether waiting Gets should be bounded or cancellable ("like the go db connection pool", README.md:15).
* What Release should do with checked-out connections and with blocked waiters.
* Whether callbacks may block or call back into the pool (no contract text, channel.go:25-30).

### Seam-contract sweep (R-SEAM-CONTRACT)

| Seam | Contract text read | Failure semantics stated | NAT candidate |
|---|---|---|---|
| `Config.Factory` (user) | channel.go:25 ("//生成连接的方法": "the method that creates a connection"); README.md:21 ("//factory Specify the method to create the connection") | none: no statement on errors, blocking, nil results, reentrancy | NAT-1 returns promptly; NAT-3 does not call pool methods; NAT-5 non-nil conn when err == nil — all unproven assumptions, no contract to cite |
| `Config.Close` (user) | channel.go:27 ("//关闭连接的方法"); README.md:24 ("//close Specify the method to close the connection") | none | NAT-2 returns promptly; NAT-3 |
| `Config.Ping` (user, optional) | channel.go:29 ("//检查连接是否有效的方法"); README.md:27 ("//ping Specify the method to detect whether the connection is invalid") | non-nil error means invalid (README.md:27 and the discard code channel.go:124-126) | NAT-7 safe for concurrent calls (called outside the lock by many Gets) — unproven |
| Go channel `conns` | Go spec (receive from a closed channel yields buffered values, then the zero value; `close` of a closed channel panics; `len` of a nil channel is 0) | language contract, not in the repository | NAT-8 |
| `logrus.Debugf` | module source not in the repository; not read | not read — any claim about it is unproven inference | none raised; no finding depends on it |

A drafted claim about a seam's failure behaviour stays `inferred` (routing rule 3): none of the drafts made a seam-failure claim beyond the call sites.

## Doctrine lines

Normative sentences from README.md, README_ZH_CN.md and the Go doc comments. Each line keeps its source quote; the English rendering of Chinese quotes is mine.

- DOC-1 — README.md:12 ("The connection type in the connection pool is `interface{}`, making it more versatile"); README_ZH_CN.md:10 ("连接池中连接类型为`interface{}`，使得更加通用").
- DOC-2 — README.md:13 ("the timeout connection will be closed and discarded"); README.md:38 ("the connection exceeding this time will be closed"); README_ZH_CN.md:11 ("超时的连接将关闭丢弃"); README_ZH_CN.md:36 ("超过该时间的连接 将会关闭"); channel.go:31 ("连接最大空闲时间，超过该事件则将失效": "maximum idle time; beyond it the connection becomes invalid").
- DOC-3 — README.md:14 ("Support user setting `ping` method, used to check the connectivity of connection, invalid connection will be discarded"); README_ZH_CN.md:12 ("无效的连接将丢弃").
- DOC-4 — README.md:15 ("When the connection pool is full, support for connection waiting (like the go db connection pool)").
- DOC-5 — README.md:52 ("Put the connection back into the connection pool, when the connection is no longer in use"); README_ZH_CN.md:50 ("将连接放回连接池中"); channel.go:166 ("将连接放回pool中": "put the connection back into the pool").
- DOC-6 — README.md:55 ("Release all connections in the connection pool, when resources need to be destroyed"); README_ZH_CN.md:53 ("释放连接池中的所有连接"); channel.go:223 ("释放连接池中所有连接": "release all connections in the pool").
- DOC-7 — README.md:58 ("View the number of connections in the current connection pool"); README_ZH_CN.md:56 ("查看当前连接中的数量"); channel.go:245 ("连接池中已有的连接": "the connections already in the pool").
- DOC-8 — README.md:30 ("Initialize the number of connections to 5, the maximum idle connection is 20, and the maximum concurrent connection is 30"); README_ZH_CN.md:28 ("初始化5，最大空闲连接是20，最大并发连接30"); README_ZH_CN.md:30 ("资源池初始连接数": "initial number of connections of the resource pool").
- DOC-9 — channel.go:21 ("最大并发存活连接数": "maximum number of concurrently live connections"); README_ZH_CN.md:32 ("最大并发连接数").
- DOC-10 — channel.go:23 ("最大空闲连接": "maximum idle connections"); README_ZH_CN.md:31 ("最大空闲连接数").
- DOC-11 — channel.go:19 ("连接池中拥有的最小连接数": "the minimum number of connections the pool holds").
- DOC-12 — pool.go:6 ("ErrClosed 连接池已经关闭Error": "error: the pool has been closed").
- DOC-13 — channel.go:13 ("ErrMaxActiveConnReached 连接池超限": "error: the pool limit is exceeded").
- DOC-14 — README_ZH_CN.md:13 ("使用channel处理池中的连接，高效": "uses a channel to handle the connections in the pool, efficient").
- DOC-15 — README.md:66 ("The connection pool implementation refers to pool"); README_ZH_CN.md:64 ("该连接池参考").
- DOC-16 — channel.go:201 ("关闭单条连接": "close a single connection").
- DOC-17 — channel.go:102 ("从pool中取一个连接": "take one connection from the pool"); README.md:46 ("Get a connection from the connection pool"); README_ZH_CN.md:44 ("从连接池中取得一个连接").
- DOC-18 — channel.go:114 ("判断是否超时，超时则丢弃": "check whether it timed out; if so, discard it"); channel.go:117 ("丢弃并关闭该连接": "discard and close the connection").
- DOC-19 — channel.go:122 ("判断是否失效，失效则丢弃，如果用户没有设定 ping 方法，就不检查": "check whether it is invalid; if so discard it; if the user set no ping method, do not check").
- DOC-20 — channel.go:195 ("连接池已满，直接关闭该连接": "the pool is full; close the connection directly").

Checked sentence by sentence against README.md, README_ZH_CN.md, channel.go and pool.go comments (routing rule 3). Descriptive comments that state no obligation (Config field descriptions of Factory/Close/Ping at channel.go:25-29, "getConns 获取所有连接" at channel.go:94, "Pool 基本方法" at pool.go:10, the README badges and licence lines) are not doctrine lines. The mapping of every DOC-n is in `invariants-and-lints.md`.

## Model routing record for Step 1 (draft-verify)

Six `draft-verify` calls (one per requirements, doc, code, test, or example file), `--model jev-1.14.0`, task files in `routing/task-*.txt` (finding-neutral, rule 10). All six drafts finished (`finish_reason=stop`), no draft was rejected, no citation check failed (133 claims, 0 failures). Jev choices: 124 `supported`, 9 `unclear`, 0 `contradicted`.

Every drafted claim was read against its cited line before use (rule 1). The per-claim review and the disposition of every draft question (rule 6) follow, generated from the draft JSON by `routing/review_drafts.py` (evidence bundle) with my verdicts.

### Items the drafts missed (rule 3: my own pass)

1. `c.ping` is read in Get without the lock (channel.go:123 ("if c.ping != nil {")) while Release writes it under the lock (channel.go:229 ("c.ping = nil")) — a data race on a field (Q-08).
2. `Close` decrements `openingConns` and wakes no waiter (channel.go:211); waiters stay blocked although capacity is free (Q-04).
3. A Get that finds the idle channel empty and a Put that runs before that Get takes the lock leave the Get queued as a waiter while a connection sits idle (channel.go:130-135 vs channel.go:189-190) (Q-05).
4. The handoff path skips the ping check (channel.go:141-148) (Q-14).
5. There is no ownership record: duplicate or foreign Put/Close change `openingConns` or the idle set (channel.go:159, 190, 211) (Q-10, Q-11).
6. The capacity test precedes the released test in the Get slow path (channel.go:133 before channel.go:150) (Q-07).
7. A factory that returns `(nil, nil)` produces a counted connection that Put and Close reject (channel.go:159, 169, 204) (Q-19).
8. The Config comment calls `InitialCap` a minimum (channel.go:19) — contradiction with the README (Q-15).
9. A Get blocked in a slow factory blocks Release, Put, Close and Len, because all take `mu` (channel.go:154 with channel.go:96, 172, 206, 225) (Q-09).
10. Release does not reset `openingConns` or `connReqs` (channel.go:225-232).
11. The draft of channel.go recorded no doctrine-relevant code comments (channel.go:114, 117, 122, 195); added as DOC-18 … DOC-20.
12. Test fixture facts the test draft missed: TestPool_Put's message prints 1 while asserting `MaxIdleCap` (channel_rpc_test.go:121-123, outside scope); TestPoolWriteRead never returns its connection (channel_rpc_test.go:194).
### Drafted claims (rule 1, rule 2)

| Draft | Claim | Kind | Cited line | Citation | Jev | My review |
|---|---|---|---|---|---|---|
| dv-README | C1 | claim | README.md:8 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C2 | claim | README.md:12 | ok | supported (0.82) | accepted: cited line re-read, claim holds |
| dv-README | C3 | claim | README.md:13 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C4 | claim | README.md:13 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C5 | claim | README.md:13 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C6 | claim | README.md:14 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C7 | claim | README.md:14 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C8 | claim | README.md:15 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C9 | claim | README.md:21 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C10 | claim | README.md:24 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C11 | claim | README.md:27 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C12 | claim | README.md:30 | ok | supported (0.80) | accepted: cited line re-read, claim holds |
| dv-README | C13 | claim | README.md:30 | ok | supported (0.98) | accepted: cited line re-read, claim holds |
| dv-README | C14 | claim | README.md:30 | ok | supported (0.96) | accepted: cited line re-read, claim holds |
| dv-README | C15 | claim | README.md:38 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C16 | claim | README.md:38 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C17 | claim | README.md:41 | ok | supported (0.94) | accepted: cited line re-read, claim holds |
| dv-README | C18 | claim | README.md:47 | ok | supported (0.98) | accepted: cited line re-read, claim holds |
| dv-README | C19 | claim | README.md:52 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C20 | claim | README.md:55 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README | C21 | claim | README.md:58 | ok | supported (0.91) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C1 | claim | README_ZH_CN.md:5 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C2 | claim | README_ZH_CN.md:10 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C3 | claim | README_ZH_CN.md:11 | ok | supported (0.98) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C4 | claim | README_ZH_CN.md:12 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C5 | claim | README_ZH_CN.md:13 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C6 | claim | README_ZH_CN.md:19 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C7 | claim | README_ZH_CN.md:22 | ok | supported (0.76) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C8 | claim | README_ZH_CN.md:25 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C9 | claim | README_ZH_CN.md:30 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C10 | claim | README_ZH_CN.md:31 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C11 | claim | README_ZH_CN.md:32 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C12 | claim | README_ZH_CN.md:33 | ok | supported (0.79) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C13 | claim | README_ZH_CN.md:34 | ok | supported (0.92) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C14 | claim | README_ZH_CN.md:35 | ok | supported (0.55) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C15 | claim | README_ZH_CN.md:36 | ok | supported (0.94) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C16 | claim | README_ZH_CN.md:37 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C17 | claim | README_ZH_CN.md:39 | ok | supported (0.86) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C18 | claim | README_ZH_CN.md:45 | ok | supported (0.91) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C19 | claim | README_ZH_CN.md:51 | ok | supported (0.92) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C20 | claim | README_ZH_CN.md:54 | ok | supported (0.94) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C21 | claim | README_ZH_CN.md:57 | ok | supported (0.86) | accepted: cited line re-read, claim holds |
| dv-README_ZH_CN | C22 | claim | README_ZH_CN.md:64 | ok | supported (0.74) | accepted: cited line re-read, claim holds |
| dv-channel | C1 | claim | channel.go:41 | ok | unclear (0.55) | kept: re-read channel.go:40-50, the field list holds; Jev judged the one-line fragment (the mutex line) against a statement about all fields |
| dv-channel | C2 | claim | channel.go:70 | ok | supported (0.98) | accepted: cited line re-read, claim holds |
| dv-channel | C3 | claim | channel.go:59 | ok | supported (0.97) | accepted: cited line re-read, claim holds |
| dv-channel | C4 | claim | channel.go:62 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-channel | C5 | claim | channel.go:65 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-channel | C6 | claim | channel.go:75 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-channel | C7 | claim | channel.go:78 | ok | supported (0.97) | accepted: cited line re-read, claim holds |
| dv-channel | C8 | claim | channel.go:83 | ok | supported (0.67) | accepted: cited line re-read, claim holds |
| dv-channel | C9 | claim | channel.go:85 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-channel | C10 | claim | channel.go:88 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-channel | C11 | claim | channel.go:96 | ok | supported (0.24) | accepted: re-read channel.go:95-99 |
| dv-channel | C12 | claim | channel.go:105 | ok | supported (0.98) | accepted: cited line re-read, claim holds |
| dv-channel | C13 | claim | channel.go:108 | ok | supported (0.28) | accepted: cited line re-read, claim holds |
| dv-channel | C14 | claim | channel.go:111 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-channel | C15 | claim | channel.go:116 | ok | supported (0.98) | accepted: cited line re-read, claim holds |
| dv-channel | C16 | claim | channel.go:124 | ok | supported (0.96) | accepted: cited line re-read, claim holds |
| dv-channel | C17 | claim | channel.go:129 | ok | supported (0.97) | accepted: cited line re-read, claim holds |
| dv-channel | C18 | claim | channel.go:131 | ok | unclear (0.35) | kept: re-read channel.go:131-132, Lock then Debugf of both counters holds; the fragment names only the Lock |
| dv-channel | C19 | claim | channel.go:133 | ok | supported (0.96) | accepted: cited line re-read, claim holds |
| dv-channel | C20 | claim | channel.go:138 | ok | supported (0.85) | accepted as a code path; re-read channel.go:137-139 and the whole file: no code closes a request channel, so the path is unreachable as-is (Q-01, Q-03) |
| dv-channel | C21 | claim | channel.go:142 | ok | supported (0.98) | accepted: cited line re-read, claim holds |
| dv-channel | C22 | claim | channel.go:148 | ok | supported (0.96) | accepted: cited line re-read, claim holds |
| dv-channel | C23 | claim | channel.go:150 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-channel | C24 | claim | channel.go:154 | ok | supported (0.33) | accepted: cited line re-read, claim holds |
| dv-channel | C25 | claim | channel.go:159 | ok | supported (0.49) | accepted: cited line re-read, claim holds |
| dv-channel | C26 | claim | channel.go:169 | ok | supported (0.98) | accepted: cited line re-read, claim holds |
| dv-channel | C27 | claim | channel.go:172 | ok | supported (0.86) | accepted: cited line re-read, claim holds |
| dv-channel | C28 | claim | channel.go:176 | ok | supported (0.88) | accepted: cited line re-read, claim holds |
| dv-channel | C29 | claim | channel.go:179 | ok | supported (0.74) | accepted: cited line re-read, claim holds |
| dv-channel | C30 | claim | channel.go:190 | ok | supported (0.82) | accepted: cited line re-read, claim holds |
| dv-channel | C31 | claim | channel.go:196 | ok | supported (0.77) | accepted: cited line re-read, claim holds |
| dv-channel | C32 | claim | channel.go:203 | ok | supported (0.68) | accepted: cited line re-read, claim holds |
| dv-channel | C33 | claim | channel.go:206 | ok | supported (0.35) | accepted: cited line re-read, claim holds |
| dv-channel | C34 | claim | channel.go:208 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-channel | C35 | claim | channel.go:211 | ok | supported (0.86) | accepted: cited line re-read, claim holds |
| dv-channel | C36 | claim | channel.go:218 | ok | supported (0.76) | accepted: cited line re-read, claim holds |
| dv-channel | C37 | claim | channel.go:220 | ok | supported (0.56) | accepted: cited line re-read, claim holds |
| dv-channel | C38 | claim | channel.go:225 | ok | unclear (0.43) | kept: re-read channel.go:225-232, all six assignments hold; the fragment names only the Lock |
| dv-channel | C39 | claim | channel.go:234 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-channel | C40 | claim | channel.go:238 | ok | supported (0.97) | accepted: cited line re-read, claim holds |
| dv-channel | C41 | claim | channel.go:241 | ok | supported (0.76) | accepted: cited line re-read, claim holds |
| dv-channel | C42 | claim | channel.go:247 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-channel | C43 | ordering | channel.go:118 | ok | supported (0.55) | accepted: cited line re-read, claim holds |
| dv-channel | C44 | ordering | channel.go:137 | ok | supported (0.94) | accepted: cited line re-read, claim holds |
| dv-channel | C45 | ordering | channel.go:144 | ok | supported (0.74) | accepted: cited line re-read, claim holds |
| dv-channel | C46 | ordering | channel.go:183 | ok | supported (0.91) | accepted: cited line re-read, claim holds |
| dv-channel | C47 | ordering | channel.go:239 | ok | supported (0.58) | accepted: cited line re-read, claim holds |
| dv-pool | C1 | claim | pool.go:7 | ok | supported (0.98) | accepted: cited line re-read, claim holds |
| dv-pool | C2 | claim | pool.go:11 | ok | supported (0.70) | accepted: cited line re-read, claim holds |
| dv-pool | C3 | claim | pool.go:12 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-pool | C4 | claim | pool.go:14 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-pool | C5 | claim | pool.go:16 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-pool | C6 | claim | pool.go:18 | ok | supported (0.97) | accepted: cited line re-read, claim holds |
| dv-pool | C7 | claim | pool.go:20 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C1 | claim | channel_rpc_test.go:14 | ok | unclear (0.25) | kept: re-read channel_rpc_test.go:14-18, the five fixture values hold; the fragment is line 14 only |
| dv-channel_rpc_test | C2 | claim | channel_rpc_test.go:21 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C3 | claim | channel_rpc_test.go:24 | ok | supported (0.86) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C4 | claim | channel_rpc_test.go:32 | ok | supported (0.92) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C5 | claim | channel_rpc_test.go:257 | ok | supported (0.67) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C6 | claim | channel_rpc_test.go:267 | ok | unclear (0.58) | kept: re-read channel_rpc_test.go:262-272, holds |
| dv-channel_rpc_test | C7 | claim | channel_rpc_test.go:281 | ok | supported (0.68) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C8 | ordering | channel_rpc_test.go:38 | ok | unclear (0.31) | kept: re-read channel_rpc_test.go:37-43, holds (Release is deferred before the error check: a nil pool would panic; test quality, outside scope) |
| dv-channel_rpc_test | C9 | claim | channel_rpc_test.go:41 | ok | supported (0.74) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C10 | ordering | channel_rpc_test.go:52 | ok | supported (0.35) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C11 | ordering | channel_rpc_test.go:69 | ok | supported (0.80) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C12 | ordering | channel_rpc_test.go:76 | ok | supported (0.62) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C13 | claim | channel_rpc_test.go:94 | ok | supported (0.98) | accepted; executed: the asserted error is never returned, the Get blocks (as-is-validation.md) |
| dv-channel_rpc_test | C14 | ordering | channel_rpc_test.go:121 | ok | supported (0.30) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C15 | ordering | channel_rpc_test.go:126 | ok | supported (0.82) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C16 | ordering | channel_rpc_test.go:134 | ok | supported (0.94) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C17 | ordering | channel_rpc_test.go:148 | ok | supported (0.37) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C18 | claim | channel_rpc_test.go:157 | ok | supported (0.94) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C19 | ordering | channel_rpc_test.go:168 | ok | unclear (0.67) | kept: re-read channel_rpc_test.go:166-189, holds; the test waits for nothing and asserts nothing |
| dv-channel_rpc_test | C20 | ordering | channel_rpc_test.go:197 | ok | supported (0.83) | accepted: cited line re-read, claim holds |
| dv-channel_rpc_test | C21 | ordering | channel_rpc_test.go:216 | ok | unclear (0.68) | kept: re-read channel_rpc_test.go:206-235, holds |
| dv-channel_rpc_test | C22 | claim | channel_rpc_test.go:238 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-example_main | C1 | claim | example/main.go:38 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-example_main | C2 | claim | example/main.go:39 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-example_main | C3 | claim | example/main.go:40 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-example_main | C4 | claim | example/main.go:31 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-example_main | C5 | claim | example/main.go:34 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-example_main | C6 | claim | example/main.go:44 | ok | supported (0.82) | accepted: cited line re-read, claim holds |
| dv-example_main | C7 | claim | example/main.go:46 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-example_main | C8 | claim | example/main.go:48 | ok | supported (0.96) | accepted: cited line re-read, claim holds |
| dv-example_main | C9 | claim | example/main.go:52 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-example_main | C10 | claim | example/main.go:58 | ok | supported (1.00) | accepted: cited line re-read, claim holds |
| dv-example_main | C11 | claim | example/main.go:64 | ok | supported (0.92) | accepted: cited line re-read, claim holds |
| dv-example_main | C12 | claim | example/main.go:61 | ok | supported (0.97) | accepted: cited line re-read, claim holds |
| dv-example_main | C13 | claim | example/main.go:61 | ok | supported (0.96) | dropped: exact duplicate of C12 (same line, same statement) |
| dv-example_main | C14 | ordering | example/main.go:46 | ok | unclear (0.73) | kept: re-read example/main.go:46-64, the order New, Get, Put, Len holds |

### Draft questions carried forward (rule 6)

| Draft | # | Question (abridged) | Disposition |
|---|---|---|---|
| dv-README | 1 | Is the pool an ordering when NewChannelPool initializes InitialCap connections—does it create them at construction time? | answered: construction creates InitialCap connections (channel.go:82-89); minimum-vs-initial reading → Q-15 |
| dv-README | 2 | What happens on Get when the pool is full and connection waiting is supported—does Get block, and for how long or with what timeout? | Q-02 |
| dv-README | 3 | When is the ping method invoked—on Get, on Put, periodically, or elsewhere? | answered: ping runs only on Get's idle path (channel.go:123-124); handoff path → Q-14 |
| dv-README | 4 | What happens when Factory returns an error during initialization or on Get? | Q-17 |
| dv-README | 5 | What happens when Close returns an error during Release or idle-timeout discard? | Q-18 |
| dv-README | 6 | Is InitialCap bounded by MaxIdle or MaxCap, and what happens if InitialCap exceeds either? | answered: validation rejects InitialCap > MaxIdle and MaxIdle > MaxCap (channel.go:59); undocumented → Q-20 |
| dv-README | 7 | How does MaxIdle interact with MaxCap—what happens when idle connections exceed MaxIdle but total is below MaxCap? | answered: Put closes when the idle channel is full (channel.go:196); undocumented → Q-20 |
| dv-README | 8 | Is Len counting idle connections, total connections, or checked-out connections? | Q-16 |
| dv-README | 9 | Does Release wait for checked-out connections to be Put back, or close everything immediately? | Q-06 |
| dv-README | 10 | What happens to a connection Put back after Release was called? | Q-06 |
| dv-README | 11 | What error does Get return and when (e.g., pool exhausted, factory error)? | Q-03 (ErrMaxActiveConnReached) and Q-17 (factory errors) |
| dv-README | 12 | Is the IdleTimeout measured from creation, from last Put, or from last use? | answered: the timestamp is set on Put (channel.go:190) and on creation (channel.go:88), consistent with 'maximum idle time' (README.md:13); folded into Q-13 |
| dv-README | 13 | Are idle connections proactively swept at IdleTimeout, or only checked lazily on Get? | Q-13 |
| dv-README | 14 | When a ping check fails, is the invalid connection closed via the Close function before being discarded? | answered: a failed ping leads to Close (channel.go:125), which calls the close callback (channel.go:212) |
| dv-README | 15 | Does Get validate a connection with ping before returning it, and if invalid, does it create a new one? | answered: Get pings and retries, creating a new connection when idle is exhausted (channel.go:123-126, 154); handoff → Q-14 |
| dv-README | 16 | Does Put validate the connection (e.g., via ping) before returning it to the pool? | answered: Put does not ping (channel.go:167-198) → Q-14 |
| dv-README | 17 | Is the zero value of Config valid, and what defaults apply for unspecified parameters? | Q-20 |
| dv-README_ZH_CN | 1 | What happens when Get is called and no idle connection is available — does it create a new connection via Factory up to MaxCap, or block,... | answered: creates below MaxCap, blocks at MaxCap (channel.go:133-161); waiting semantics → Q-02 |
| dv-README_ZH_CN | 2 | What error does NewChannelPool return when the config is invalid, and which invalid conditions are checked? | answered: three checks with three messages (channel.go:59-67); documentation → Q-20 |
| dv-README_ZH_CN | 3 | What does Put do if the pool is already at MaxIdle or the connection has exceeded IdleTimeout? | answered: full → Close (channel.go:196); expiry is not checked on Put, the timestamp is renewed (channel.go:190); folded into Q-13 |
| dv-README_ZH_CN | 4 | Is the Ping function invoked on Get, on Put, on both, or on a background schedule? | answered: Get idle path only (channel.go:123); → Q-14 |
| dv-README_ZH_CN | 5 | When is the IdleTimeout check performed — on Get, on Put, by a background goroutine, or otherwise? | Q-13 |
| dv-README_ZH_CN | 6 | What does Len count — idle connections only, checked-out connections, or both? | Q-16 |
| dv-README_ZH_CN | 7 | Does Release close all checked-out connections as well as idle ones, and does the pool remain usable afterward? | Q-06 (checked-out connections); usability after Release answered: ErrClosed (channel.go:106) |
| dv-README_ZH_CN | 8 | What is the exact relationship between MaxCap (maximum concurrent connections) and MaxIdle (maximum idle connections) — must MaxIdle be <... | answered: MaxIdle <= MaxCap is enforced (channel.go:59) |
| dv-README_ZH_CN | 9 | What happens when IdleTimeout is zero or unset — is the idle-timeout feature disabled or is some default applied? | Q-20 |
| dv-README_ZH_CN | 10 | Is the Ping field optional, and what is the behaviour when it is nil? | answered: Ping is optional (channel.go:78, 123); exported Ping with no ping configured → Q-22 |
| dv-README_ZH_CN | 11 | Does the factory function ever get called after initialization, e.g., on Get when the pool is empty? | answered: yes, on Get below capacity (channel.go:154) |
| dv-README_ZH_CN | 12 | Does the close function get called for idle connections discarded due to IdleTimeout? | answered: yes (channel.go:118 → channel.go:212) |
| dv-channel | 1 | What happens to blocked Get waiters when Release is called? connReqs are not closed in Release, so it is unclear whether waiters ever unb... | Q-01 |
| dv-channel | 2 | ErrMaxActiveConnReached is returned when a waiter's request channel is closed, but no code in this file closes request channels; under wh... | Q-01 and Q-03 |
| dv-channel | 3 | Close acquires mu.Lock and is called from Put (line 176, 196) which has already unlocked, and from Get (lines 118, 125, 144); is Close ev... | answered: no — Put unlocks before calling Close (channel.go:175, 194) and Get calls Close outside the lock (channel.go:110-128, 144 after the unlock at 136); the callback-under-lock issue is Q-09 |
| dv-channel | 4 | Close decrements openingConns unconditionally even when called on connections that were never counted (e.g., expired connections from wai... | answered: handed-off connections were counted when created (channel.go:159) and are not double counted; drift through foreign or duplicate Close → Q-10 |
| dv-channel | 5 | Put sends a connReq to a waiter channel of capacity 1 while holding mu; could this block if the waiter is not ready, and what is the cons... | answered: no — the request channel has buffer 1 (channel.go:134) and receives exactly one send (channel.go:183) |
| dv-channel | 6 | Put pops connReqs[0] and serves it; if the waiter has already abandoned (e.g., timed out), what happens to the delivered connection? | Q-02 (a waiter cannot abandon: no timeout, no cancellation) |
| dv-channel | 7 | waitTimeOut is declared but never used in this file; is waiting on request channels unbounded or is there supposed to be a timeout? | Q-02 |
| dv-channel | 8 | c.ping may be nil (when Config.Ping is nil), but Ping (line 220) calls c.ping without a nil check; is calling Ping when unconfigured a ni... | Q-22 |
| dv-channel | 9 | Close returns nil without decrementing openingConns when c.close is nil (line 208); does that leak the openingConns counter? | Q-06 (after Release the close callback is nil; counter state after Release is unobservable) |
| dv-channel | 10 | Release closes conns while Get may concurrently receive from it via a previously obtained channel reference; is receiving from a closed c... | Q-07 |
| dv-channel | 11 | Release does not wait for in-flight Get/Put calls; are connections held by callers leaked on Release? | Q-06 |
| dv-channel | 12 | Get calls factory while holding mu.Lock; if the user factory blocks or calls back into the pool, does that deadlock? | Q-09 |
| dv-channel | 13 | Get calls c.Ping and c.Close (via Close) while not holding mu in the receive branch, but Ping and Close may interact with user code; what... | Q-09 (lock discipline) and Q-08 (unlocked read of c.ping) |
| dv-channel | 14 | If c.idleTimeout is zero or negative, are connections never considered expired; is that the intended semantics? | Q-20 |
| dv-channel | 15 | When Get receives a nil from conns it returns ErrClosed; can conns ever deliver a non-nil zero value other than nil that is not an idleCo... | answered: Put never sends nil (it wraps every connection, channel.go:184, 190), so nil means a closed channel |
| dv-channel | 16 | Is there any cap on the length of connReqs, or can waiters accumulate unboundedly? | Q-02 (unbounded waiter queue, Step-5 lint) |
| dv-channel | 17 | Does Get need to re-check maxActive between serving a waiter and returning the connection, or can a served connection exceed the intended... | answered: a handoff does not change openingConns; the cap is checked only before creation (channel.go:133) — drift cases → Q-10 |
| dv-channel | 18 | Len calls getConns which locks mu; if Release has set conns to nil, len(nil) is 0, but is that an accurate count of active connections he... | Q-16 |
| dv-channel | 19 | Put when waiting requests exist does not verify that the pool is full (openingConns >= maxActive); can this hand back connections that sh... | answered: waiters normally exist only at capacity; the cases where they exist below capacity → Q-04, Q-05 |
| dv-channel | 20 | Is the config check on line 59 missing validation that MaxCap > 0 and MaxIdle >= 0, and what happens if MaxCap is less than InitialCap (a... | Q-20 (MaxIdle < 0 is unreachable: InitialCap >= 0 and InitialCap <= MaxIdle, proven in check_guards.py G-01 implication) |
| dv-pool | 1 | The file contains only an interface and an error; there is no implementation of channelPool, so no states, struct fields, counters, chann... | answered by the channel.go extraction (this file holds only the interface and ErrClosed) |
| dv-pool | 2 | What states does a channelPool hold (open, closed, draining, etc.) and how are they represented? | answered by the channel.go extraction (this file holds only the interface and ErrClosed) |
| dv-pool | 3 | Which concrete type implements Pool and where is it defined? | answered by the channel.go extraction (this file holds only the interface and ErrClosed) |
| dv-pool | 4 | What external events (public functions/methods) trigger transitions in channelPool, and what guards select each branch? | answered by the channel.go extraction (this file holds only the interface and ErrClosed) |
| dv-pool | 5 | What actions/side effects occur on Get, Put, Close, Release, and Len, and does any call into user-supplied functions? | answered by the channel.go extraction (this file holds only the interface and ErrClosed) |
| dv-pool | 6 | Are there timeouts, timers, retries, or loop limits in Get/Put/Close/Release? | answered by the channel.go extraction (this file holds only the interface and ErrClosed) |
| dv-pool | 7 | What waiting and cancellation paths exist when the pool is empty or closed? | answered by the channel.go extraction (this file holds only the interface and ErrClosed) |
| dv-pool | 8 | Which errors are returned (including ErrClosed) and under what conditions? | answered by the channel.go extraction (this file holds only the interface and ErrClosed) |
| dv-pool | 9 | Where are mutexes acquired and released, and which calls occur while held? | answered by the channel.go extraction (this file holds only the interface and ErrClosed) |
| dv-pool | 10 | What apparent invariants hold for the pool (e.g., capacity, channel non-nil, closed flag consistency)? | answered by the channel.go extraction (this file holds only the interface and ErrClosed) |
| dv-pool | 11 | Does any specific ordering of events result in a determined outcome that this file specifies? | answered by the channel.go extraction (this file holds only the interface and ErrClosed) |
| dv-channel_rpc_test | 1 | What should happen (or be asserted) when TestPool_Get's concurrent Get goroutines return errors? The errors are only reported, not the fi... | Q-03 |
| dv-channel_rpc_test | 2 | In TestPool_Put, the error message reports 'Expecting %d' with value 1 but asserts MaxIdleCap; is the expected value 1 or MaxIdleCap? | outside statechart scope: test message text (channel_rpc_test.go:122-123); recorded under 'outside scope' in summary.md |
| dv-channel_rpc_test | 3 | TestPool_Close does not check the error from p.Release; is Release expected to return an error? | answered: Release returns nothing (pool.go:18) |
| dv-channel_rpc_test | 4 | TestPoolConcurrent does not assert any outcome and has no WaitGroup; how is completion and correctness determined? | Q-07 (Release racing with Get/Put); the missing assertion is test quality, outside scope |
| dv-channel_rpc_test | 5 | TestPoolConcurrent2 does not assert any outcome and does not defer Release; is pool release required or verified? | outside scope (test quality); Close-only use is the E-CLOSE path |
| dv-channel_rpc_test | 6 | What is the expected pool Len after TestPool_Get's maximum-capacity concurrent Gets complete with errors potentially suppressed? | Q-03 |
| dv-channel_rpc_test | 7 | What happens to connections when the Get/Put pipe goroutines in TestPoolConcurrent receive nil from Get errors? Is that behavior specified? | Q-07 |
| dv-channel_rpc_test | 8 | Does TestPoolWriteRead need to Put or Close the conn? It does not, so is leaking the conn acceptable? | Q-12 (connection never returned) |
| dv-channel_rpc_test | 9 | What is the behavior of p.Close(conn) versus p.Put(conn)? Only Close is used in TestPoolConcurrent2 and Put in others. | answered: Put pools or hands off, Close closes and decrements (event catalogue) |
| dv-channel_rpc_test | 10 | Does newChannelPool's config ever get varied across tests, or is IdleTimeout 20s and MaxIdle 10 always used? | answered: only TestPool_Put builds its own Config, with the same values (channel_rpc_test.go:101) |
| dv-channel_rpc_test | 11 | What is the expected return value of p.Get after p.Release in TestPoolConcurrent where Release races with Get calls? | Q-07 |
| dv-channel_rpc_test | 12 | Is the rpc server's Arith.Multiply expected to be called through the HTTP registration only, and does that affect the pool connection type? | outside scope: RPC fixture |
| dv-example_main | 1 | Does the example check or handle the error returned by p.Get()? | outside scope: example code quality (example/main.go:52); factory errors → Q-17 |
| dv-example_main | 2 | What does p.Len() report as the connection count after Get followed by Put? | answered: InitialCap idle connections, Len counts idle (channel.go:247) → Q-16 |
| dv-example_main | 3 | Is the connection count from Len affected by the initial capacity of 2? | answered: yes, Len counts idle connections including the initial ones |
| dv-example_main | 4 | What does the pool do if the initial capacity exceeds MaxCap or MaxIdle? | answered: rejected by validation (channel.go:59) |
| dv-example_main | 5 | Does NewChannelPool return an error in the example, and how does the program behave afterward? | outside scope: the example continues with a nil pool (example/main.go:47-52) |
| dv-example_main | 6 | What happens if Put is not called for a connection obtained via Get? | Q-12 |
| dv-example_main | 7 | What happens to a pooled connection when its idle time exceeds the 15-second IdleTimeout? | Q-13 |
| dv-example_main | 8 | Does the factory's net.Dial error propagate to Get's error? | answered: yes, unwrapped (channel.go:157); semantics → Q-17 |
| dv-example_main | 9 | Is the expected behaviour of Get when the pool is at MaxCap specified? | Q-02 |
| dv-example_main | 10 | Is the sequence of operations (Get then Put then Len) required by the pool or merely chosen by the example? | answered: no ordering is required between independent calls |
| dv-example_main | 11 | What does Len count exactly—total connections, idle connections, or in-use connections? | Q-16 |
| dv-example_main | 12 | Would p.Release(), if uncommented, close connections using the configured close function? | answered: yes (channel.go:241) |
