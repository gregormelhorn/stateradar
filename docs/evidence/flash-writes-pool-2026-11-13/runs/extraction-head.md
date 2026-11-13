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
