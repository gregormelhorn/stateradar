# Extraction — channelPool (silenceper/pool @ 6084537)

CONFIG

```text
Component under analysis:   channelPool (channel.go)
Entry points / public API:  NewChannelPool, Get, Put, Close, Ping, Release, Len (Pool interface, pool.go)
Related tests:              channel_rpc_test.go
Requirements / docs:        README.md, README_ZH_CN.md, doc comments in channel.go and pool.go
Output directory:           domain-analysis/channelPool/
```

## Step 0 — Scope statement

**Machine boundary.** One `channelPool` instance (channel.go:40 ("type channelPool struct")):
its idle-connection channel `conns`, the live-connection counter
`openingConns`, the waiter queue `connReqs`, and the configured callbacks
(`factory`, `close`, `ping`). The machine is the pool, not a connection:
a connection's own protocol state is outside.

**Actors.**

* Pool owner — constructs the pool (`NewChannelPool`) and destroys it (`Release`).
* Worker goroutines (users) — `Get`, `Put`, `Close`, `Ping`, `Len`, any number concurrently.
* Configured seams (callbacks, internal sources): `Factory`, `Close`, `Ping` (channel.go:26-30).
* Clock — idle age compared with `IdleTimeout` on retrieval (channel.go:116 ("wrapConn.t.Add(timeout).Before(time.Now())")).

**Excluded.** The connection objects themselves (rpc/net clients), the
logging library (logrus, channel.go:132 ("log.Debugf")), `example/main.go`
(a usage demo with no behaviour of its own), and multi-pool coordination.

**Model links.** No neighbouring component of this repository is modelled.
The failure semantics of `Factory`, `Close` and `Ping` belong to the user's
callbacks; the library documents no contract for them (seam-contract sweep
below). Cells that depend on them cite this absence, not a local defect.

**Temporal behaviour present.** Lifecycle (open → released), blocking waits
(`<-req`, channel.go:137 ("ret, ok := <-req")), idle timeouts, and
concurrent callers. The analysis proceeds.

## Model routing record (Step 1)

Drafts from `draft-verify` (Flash `deepseek-flash`, Jev `jev-1.14.0`), one per file:

| file | output | claims | citation failures | Jev supported / unclear / contradicted | draft questions |
|---|---|---|---|---|---|
| README.md | `dv-readme.json` | 14 | 0 | 14 / 0 / 0 | 12 |
| pool.go | `dv-pool.json` | 7 | 0 | 7 / 0 / 0 | 9 |
| channel_rpc_test.go | `dv-tests.json` | 34 | 0 | 30 / 4 / 0 | 13 |
| channel.go (run 1) | `dv-channel.stdout` | — | — | rejected: `DeepSeek response incomplete (finish_reason=length)` at the default `--max-tokens` 4096; no Jev call | — |
| channel.go (run 2, `--max-tokens 12000`, same task) | `dv-channel-r2.json` | 78 | 0 | 68 / 8 / 2 | 23 |
| README_ZH_CN.md | not routed | — | — | — | — |

README_ZH_CN.md was not sent: it is Chinese and the provider documents English as
Jev's primary language. I extracted it myself (doctrine sweep below).

Re-read record (rule 1): I read every cited line of every draft claim against the
source. All 133 citations were accurate to the line. Claims kept despite a
non-`supported` Jev answer (rule 2):

* channel.go C59 (`contradicted`): "If c.close is nil, Close returns nil without
  decrementing openingConns" — kept. channel.go:208-211 ("if c.close == nil {" …
  "return nil" … "c.openingConns--") shows the return precedes the decrement. The
  same content as C78 was judged `supported` in the same batch; Jev disagrees with
  itself on identical content.
* channel.go C22 (`contradicted`): "getConns returns the copied conns channel under
  the lock" — dropped as a statement about the lock: channel.go:98-99
  ("c.mu.Unlock()" then "return conns") returns after the unlock. Jev is right; the
  draft statement is wrong. Kept only "getConns returns a snapshot of conns".
* channel.go C7-C10, C21, C58, C75, C76 (`unclear`): kept. C7-C10 interpret field
  names (maxActive, openingConns, connReqs, idleConn) — kept as `inferred` (the names
  carry no doc comment). C21/C58 restate lock sites, verified at channel.go:96 and :206.
  C75/C76 are orderings; see the ordering note below.
* channel_rpc_test.go C3, C15, C31, C32 (`unclear`): kept after re-read
  (channel_rpc_test.go:14-16, :110-118, :224-232, :262-271).

Ordering claims (rule 4): every drafted `ordering` claim except README C14 has
scope probability < 0.5 (range 0.03-0.34); they are therefore not source-backed.
None of them is used as a requirement; the orderings they describe are code
observations re-cited below, and the open ones enter Step 7 as questions
(channel.go C76 → Q-01; C77 → Q-04; C75 → Q-07). README C14 (`supported`, scope 0.79)
"When the connection pool is full, a connection waits" is used only for the
steady-state waiting doctrine DOC-4 and never for a race (rule 2 of AGENTS §4).

Items the drafts missed (rule 3) — found in my own pass:

* The lost wake-up on `Close`: channel.go:211 ("c.openingConns--") frees capacity
  but never signals `connReqs` (no draft named it).
* The enqueue race: the `select … default` at channel.go:130 ("default:") runs
  without the mutex; a `Put` between that check and channel.go:131 ("c.mu.Lock()")
  puts a connection into `conns`, and the `Get` still enqueues as a waiter.
* `Put` after `Release` never closes the connection: channel.go:176 ("return
  c.Close(conn)") reaches channel.go:208-209 with `c.close == nil` → returns nil
  (the draft stated the return, not the leak).
* `Ping` after `Release`, or with no `Ping` configured, calls a nil function:
  channel.go:220 ("return c.ping(conn)") — panic.
* `TestPool_Get` expects `ErrMaxActiveConnReached` at channel_rpc_test.go:94, but no
  code path closes a `req` channel (see as-is-validation.md).
* The handoff path skips `Ping`: channel.go:141-148 checks only idle timeout.
* `NewChannelPool` sets `openingConns` to InitialCap before the fill loop
  (channel.go:75 ("openingConns: poolConfig.InitialCap,")); a fill failure leaves the
  counter overstated, but the pool is released and discarded anyway.
* README_ZH_CN.md does not list connection waiting as a feature (contradiction with
  README.md:15).
* Factory runs under the pool mutex (channel.go:131 ("c.mu.Lock()") … :154
  ("conn, err := c.factory()")): the draft question asked the reverse; draft claim
  C44 is the correct one.

Draft questions (rule 6): all 57 are carried into Step 7. The fold table is in
open-questions.md, section "Draft-question disposition".

## Step 1 — Extraction

### State variables (implicit states)

| id | variable | domain | provenance |
|---|---|---|---|
| V-1 | `conns` | non-nil buffered channel (cap MaxIdle) / nil after Release | observed-in-code channel.go:70 ("conns:        make(chan *idleConn, poolConfig.MaxIdle),"), channel.go:227 ("c.conns = nil") |
| V-2 | `len(conns)` idle count | 0..MaxIdle | observed-in-code channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:") |
| V-3 | `openingConns` | integer, initial InitialCap; ++ on factory create, -- on Close | observed-in-code channel.go:75 ("openingConns: poolConfig.InitialCap,"), channel.go:159 ("c.openingConns++"), channel.go:211 ("c.openingConns--") |
| V-4 | `maxActive` | MaxCap, immutable | observed-in-code channel.go:74 ("maxActive:    poolConfig.MaxCap,") |
| V-5 | `connReqs` | FIFO of waiter channels (cap 1 each) | observed-in-code channel.go:134-135 ("req := make(chan connReq, 1)", "c.connReqs = append(c.connReqs, req)") |
| V-6 | `factory`, `ping`, `close` nil-ness | set at construction; all nil after Release | observed-in-code channel.go:228-231 ("c.factory = nil", "c.ping = nil", "c.close = nil") |
| V-7 | `idleTimeout` | 0 = never expire; >0 = lazy expiry on retrieval | observed-in-code channel.go:115 ("if timeout := c.idleTimeout; timeout > 0 {") |
| V-8 | `waitTimeOut` | declared, never assigned or read | observed-in-code channel.go:46 ("idleTimeout, waitTimeOut time.Duration") |

Reachable combinations (the real state space), as modelled in Step 2:

| state | conns | idle | openingConns vs maxActive | connReqs | reachable via |
|---|---|---|---|---|---|
| Open_Idle | non-nil | > 0 | any | empty | construction with InitialCap>0; Put with no waiters |
| Open_Empty_BelowCap | non-nil | 0 | < | empty | construction with InitialCap=0, MaxCap>0; Get drains idle |
| Open_Empty_AtCap | non-nil | 0 | >= | empty | Get creates up to MaxCap; construction with MaxCap=0 (valid config) |
| Open_Waiting | non-nil | 0 | >= | non-empty | Get at cap enqueues (channel.go:133-137) |
| Open_Waiting_CapacityFree | non-nil | > 0 or 0 | < or >= | non-empty | Close / idle expiry decrements while waiters exist (no wake-up); enqueue race (idle > 0 with waiters) |
| Released | nil | 0 | any (not reset) | empty | Release with no waiters |
| Released_WaitersStranded | nil | 0 | any | non-empty, never drained | Release while waiters exist |

The combination `conns == nil` with `factory != nil` is not reachable after
construction: Release clears both under one lock (channel.go:225-232).

### Events

External (owner): `NewChannelPool` (creation, channel.go:58), `Release` (channel.go:224).
External (user): `Get` (channel.go:103), `Put` (channel.go:167), `Close` (channel.go:202),
`Ping` (channel.go:216), `Len` (channel.go:246).
Internal: idle expiry detected on retrieval (channel.go:116, :142), ping failure on
retrieval (channel.go:124), factory error (channel.go:155), handoff delivered to a
waiter (channel.go:183 ("req <- connReq{")).

### Transitions, guards, actions (observed-in-code)

* NewChannelPool validates `InitialCap <= MaxIdle && MaxCap >= MaxIdle && InitialCap >= 0`
  (channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle")), Factory non-nil
  (channel.go:62), Close non-nil (channel.go:65); Ping optional (channel.go:78). It calls
  the factory InitialCap times (channel.go:82); on a factory error it calls Release and
  returns an error (channel.go:85 ("c.Release()")).
* Get: snapshot `conns` under lock (channel.go:95-99); nil → ErrClosed (channel.go:105-106).
  Loop: non-blocking receive (channel.go:110 ("case wrapConn := <-conns:")); nil value
  (closed channel) → ErrClosed (channel.go:111-112); expired → Close + loop
  (channel.go:116-119); ping error → Close + loop (channel.go:123-126); else return the
  connection (channel.go:129). Default branch under lock (channel.go:131): at cap → enqueue
  waiter, unlock, block on `<-req` (channel.go:133-137); closed req → ErrMaxActiveConnReached
  (channel.go:138-139); handed-off connection expired → Close + loop (channel.go:141-145);
  else return it (channel.go:148). Below cap: factory nil → ErrClosed (channel.go:150-152);
  factory called under the lock (channel.go:154); error → returned (channel.go:155-157);
  success → `openingConns++`, return (channel.go:159-161).
* Put: nil → error (channel.go:168-169); under lock: conns nil → unlock, `Close(conn)`
  (channel.go:174-176); waiters → pop the first, send the connection with a fresh
  timestamp, unlock, return nil (channel.go:179-187); else non-blocking send into conns
  (channel.go:190-192); full → unlock, `Close(conn)` (channel.go:193-196).
* Close: nil → error (channel.go:203-204); under lock with defer unlock (channel.go:206-207);
  `close == nil` → return nil, no decrement (channel.go:208-209); else `openingConns--` and
  invoke the close callback under the lock (channel.go:211-212).
* Ping: nil → error (channel.go:217-218); else call `c.ping` without lock and without a
  nil check (channel.go:220).
* Release: under lock snapshot conns, set conns/factory/ping/close to nil, unlock
  (channel.go:225-232); conns already nil → return (channel.go:234-235); close the channel
  and close every buffered connection with the saved callback, outside the lock
  (channel.go:238-242). `connReqs` is not touched; `openingConns` is not reset.
* Len: `len(getConns())` — the idle count; 0 after Release (len of a nil channel)
  (channel.go:247 ("return len(c.getConns())")).

### Timeouts and timers

* Idle timeout: lazy, evaluated only when Get retrieves a connection (channel.go:115-121,
  :141-147). No background reaper. `IdleTimeout == 0` disables the check (inferred from
  `timeout > 0`, channel.go:115).
* Wait timeout: none. `waitTimeOut` is declared (channel.go:46) but never assigned
  (constructor channel.go:69-76 omits it) or read. A waiter blocks until a Put hands off.

### Retry behaviour

The Get loop re-tries after discarding an expired or failed connection (`continue`,
channel.go:119, :126, :145). No bound on iterations; each iteration consumes one idle
connection or one handoff, so the loop is bounded by the supply (inferred).

### Cancellation paths

None. Get takes no context and has no timeout (channel.go:103 ("func (c *channelPool) Get() (interface{}, error) {")).
A blocked waiter cannot be cancelled by its caller or by Release.

### Failure modes

* Factory error during fill → pool released, constructor error (channel.go:84-86).
* Factory error during Get → error returned, counter unchanged (channel.go:155-157).
* Close callback error → returned to the caller of Close/Put (channel.go:212, :196).
  When Get discards an expired or failed connection, the Close error is dropped
  (channel.go:118 ("c.Close(wrapConn.conn)") has no error check).
* Ping on a pool without Ping callback, or after Release → nil-function call (channel.go:220).

### Lock discipline (input to Step 3)

`mu` is a `sync.RWMutex` (channel.go:41) used only through `Lock` (no RLock anywhere).
User callbacks invoked while `mu` is held: `factory` (channel.go:154), `close`
(channel.go:212, and via Close from Put channel.go:176/:196 — after unlock).
Callbacks invoked without the lock: `ping` (channel.go:220), `close` in Release's drain
(channel.go:241). No documentation states whether callbacks may call pool methods.

### Apparent invariants (inferred, checked in Step 5)

* openingConns = idle + checked-out connections (holds only under correct usage).
* openingConns <= maxActive.
* connReqs non-empty ⇒ no idle connection and no free capacity (violated; Step 5).

### Seam-contract sweep

| seam | invoked at | contract found | NAT candidate |
|---|---|---|---|
| `Config.Factory` | channel.go:83, :154 | Comment only: "生成连接的方法" (method that creates connections), channel.go:25. No error, blocking or timeout semantics documented. | NAT-1: factory returns within bounded time (unproven; it runs under the mutex) |
| `Config.Close` | channel.go:212, :241 | Comment only: "关闭连接的方法" (method that closes connections), channel.go:27. No idempotency, error, or reentrancy contract. | NAT-2: close is safe to call once per connection; reentrancy unknown |
| `Config.Ping` | channel.go:124, :220 | Comment only: "检查连接是否有效的方法" (method that checks validity), channel.go:29. | NAT-3: ping does not call pool methods (unproven) |
| `logrus.Debugf` | channel.go:132 | third-party logger, never returns an error | none |

The failure semantics of the three callbacks are not documented anywhere in the
repository. Every claim about their failure behaviour below stays `inferred`.

### Contradictions

* README.md:15 ("Support connection waiting") vs README_ZH_CN.md:10-13: the Chinese
  feature list has no waiting feature (it lists "使用channel处理池中的连接，高效").
* channel.go:19 comment "连接池中拥有的最小连接数" (minimum number of connections the
  pool holds) vs code: InitialCap is only an initial fill; Gets and expiries reduce idle
  below it and nothing refills (channel.go:82-89 is the only fill site).
* channel_rpc_test.go:93-94 expects `ErrMaxActiveConnReached` from the (MaxCap+1)-th
  Get vs code: the Get blocks at channel.go:137, since no code closes `req`.
* channel_rpc_test.go:146-149 reads `c.conns`, and `c.factory` after Release; consistent
  with code (channel.go:227-228).

### Behaviour I cannot determine

* What Len is meant to count (idle vs live) — README.md:58 "the number of connections in
  the current connection pool".
* Whether Release should close checked-out connections ("Release all connections",
  README.md:55).
* What a blocked waiter should experience on Release (no source).

### Doctrine-line sweep

Normative sentences from README.md, README_ZH_CN.md and the contract doc comments:

| id | source | text (quoted or translated) |
|---|---|---|
| DOC-1 | README.md:12 | "The connection type in the connection pool is `interface{}`, making it more versatile" |
| DOC-2 | README.md:13 | "the timeout connection will be closed and discarded" (idle time) |
| DOC-3 | README.md:14 | "invalid connection will be discarded" (ping) |
| DOC-4 | README.md:15 | "When the connection pool is full, support for connection waiting (like the go db connection pool)" |
| DOC-5 | README.md:52 | "Put the connection back into the connection pool, when the connection is no longer in use" |
| DOC-6 | README.md:55 | "Release all connections in the connection pool, when resources need to be destroyed" |
| DOC-7 | README.md:58 | "View the number of connections in the current connection pool" |
| DOC-8 | README.md:30, channel.go:21 | "the maximum concurrent connection is 30" / MaxCap "最大并发存活连接数" (max concurrent live connections) |
| DOC-9 | README.md:38, channel.go:31 | "the connection exceeding this time will be closed" / IdleTimeout "超过该事件则将失效" |
| DOC-10 | pool.go:6 | ErrClosed "连接池已经关闭Error" (error: pool already closed) |
| DOC-11 | channel.go:13 | ErrMaxActiveConnReached "连接池超限" (pool limit exceeded) |
| DOC-12 | channel.go:19 | InitialCap "连接池中拥有的最小连接数" (minimum number of connections the pool holds) |
| DOC-13 | channel.go:23 | MaxIdle "最大空闲连接" (maximum idle connections) |
| DOC-14 | channel.go:201 | Close "关闭单条连接" (closes a single connection) |
| DOC-15 | channel.go:223 | Release "释放连接池中所有连接" (releases all connections in the pool) |
| DOC-16 | README_ZH_CN.md:13 | "使用channel处理池中的连接，高效" (uses a channel for the pool's connections; efficient) |

README_ZH_CN.md:11-12 restate DOC-2 and DOC-3; they are folded into those lines.
Every DOC line is mapped in invariants-and-lints.md.
