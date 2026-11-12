# Event catalogue — channelPool (silenceper/pool)

<!-- event-ids: get put close_conn ping release len idle_expired ping_failed factory_error handoff UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 -->

Sources:

* **owner** — the code that constructs the pool (`NewChannelPool`) and destroys it (`Release`).
* **user** — worker goroutines that call `Get`, `Put`, `Close`, `Ping`, `Len`. Any number of user goroutines call concurrently; the README and the code comments say nothing about thread safety, and every method takes the pool mutex except `Ping` (channel.go:220 ("return c.ping(conn)")).
* **factory / close / ping callbacks** — user-supplied functions from `Config` (seams; no contract documented, channel.go:25-30).
* **clock** — idle age, evaluated only when `Get` takes a connection.
* **pool-internal** — the handoff from `Put` to a waiting `Get`.

Pool creation (`NewChannelPool`) is the initial transition of the machine, not a matrix column (see as-is.machine.mmd).

| id | event | source | classification | payload | produced at | consumed at |
|---|---|---|---|---|---|---|
| get | `Get()` — obtain a connection | user | external | none | caller | channel.go:103 ("func (c *channelPool) Get() (interface{}, error) {") |
| put | `Put(conn)` with a non-nil connection obtained from this pool | user | external | connection | caller | channel.go:167 ("func (c *channelPool) Put(conn interface{}) error {") |
| close_conn | `Close(conn)` — discard one connection obtained from this pool | user | external | connection | caller | channel.go:202 ("func (c *channelPool) Close(conn interface{}) error {") |
| ping | `Ping(conn)` — check one connection | user | external | connection | caller | channel.go:216 ("func (c *channelPool) Ping(conn interface{}) error {") |
| release | `Release()` — destroy the pool | owner | external | none | caller | channel.go:224 ("func (c *channelPool) Release() {") |
| len | `Len()` — number of idle connections | user | external | none | caller | channel.go:246 ("func (c *channelPool) Len() int {") |
| idle_expired | a connection taken by `Get` is older than IdleTimeout | clock | internal | connection + age | channel.go:116, channel.go:142 | Get loop |
| ping_failed | the Ping callback returns an error for a connection taken from the idle set | ping callback | internal | connection + error | channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {") | Get loop |
| factory_error | the Factory callback returns an error inside `Get` | factory callback | internal | error | channel.go:154 ("conn, err := c.factory()") | Get default branch |
| handoff | `Put` delivers a connection to the oldest waiting `Get` | pool-internal | internal | connection with new timestamp | channel.go:183 ("req <- connReq{") | channel.go:137 ("ret, ok := <-req") |
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
  - loss: n/a: a Get that is never made changes no pool state; a Get that has started cannot be abandoned by its caller (no cancellation parameter, channel.go:103) — recorded as lint L-4
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
  - loss: n/a: a pool that is never released stays in its Open state; there is no event to dispose (the idle connections stay open until process exit — lint L-5)
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
  - value: n/a: the timestamp is set by the pool itself (channel.go:88, :184, :190); a handed-off connection's age restarts at Put (Q-07)

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
| getConns | channel.go:96 ("c.mu.Lock()") | none | — |
| Get default branch | channel.go:131 ("c.mu.Lock()") | **Factory callback** (channel.go:154) runs with `mu` held; on success `openingConns++` | Not documented anywhere (README, Config comment channel.go:25). A factory that calls any pool method (Get, Put, Close, Len, Release) deadlocks: all take `mu` (sync.RWMutex is not reentrant). Finding → Q-12 |
| Put | channel.go:172 ("c.mu.Lock()") | handoff send to a waiter (buffered, does not block) | Close is called after unlock (channel.go:175-176, :194-196) |
| Close | channel.go:206 ("c.mu.Lock()") + defer unlock | **Close callback** (channel.go:212) runs with `mu` held | Not documented (channel.go:27). A close callback that calls a pool method deadlocks. Release's drain calls the same callback without the lock (channel.go:241), so the deadlock depends on the path. Finding → Q-12 |
| Release | channel.go:225 ("c.mu.Lock()") | none under the lock; the drain and close callbacks run after unlock (channel.go:232-242) | — |
| Ping | no lock | Ping callback | — |

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| user (get) | n/a: no state change; no cancellation exists (lint L-4) | UV-01 | n/a: independent request | Released rows + P-01 | P-01 | n/a: user-issued only | n/a: no payload |
| user (put) | UV-02 | n/a: later Put; after Release see P-02 | UV-03 | Released rows + P-02 | UV-04 | UV-05 | UV-06 |
| user (close_conn) | n/a: see UV-02 | n/a: later Close; after Release see P-03 | UV-07 | Released rows + P-03 | UV-04 | UV-08 | UV-09 |
| user (ping) | n/a: stateless | n/a: no lock, no state | n/a: stateless | Released rows + P-04 | P-04 | n/a: user-issued only | UV-11 |
| owner (release) | n/a: no event; pool stays open (L-5) | n/a: synchronous; overlaps are P-01..P-05 | UV-10 | n/a: terminal command; repeat is UV-10 | P-01..P-05 | P-01..P-05 | n/a: no payload |
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
