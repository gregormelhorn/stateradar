# channelPool — Event catalogue (Step 3)

<!-- event-ids: GET PUT CLOSE RELEASE LEN PING FACTORY_OK CLOSEFN_OK IDLE_TIMEOUT UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 UV-15 UV-16 UV-17 UV-18 -->

Terms: *idle connection* = a connection held by the pool and not checked out; *checked-out connection* = returned by Get and not yet given back; *MaxIdle*, *MaxCap*, *IdleTimeout*, *InitialCap* = the Config fields (channel.go:18-33); *waiting Get* = a Get blocked because MaxCap live connections exist.

`NewChannelPool` is not a column: it creates the instance, so no state of an existing instance can receive it. Its validation is guard group G-01 and its outcomes are the initial edges of `as-is.machine.mmd`.

## Events

| Id | Event | Source | Class | Payload gist | Produced | Consumed |
|---|---|---|---|---|---|---|
| GET | `Get()` — obtain a connection | caller | external (monitored input) | none; returns (conn, err) | any caller goroutine | channel.go:103 ("func (c *channelPool) Get() (interface{}, error) {") |
| PUT | `Put(conn)` — give back a checked-out connection of this pool | caller | external | the connection | caller | channel.go:167 ("func (c *channelPool) Put(conn interface{}) error {") |
| CLOSE | `Close(conn)` — destroy a checked-out connection of this pool | caller | external | the connection | caller | channel.go:202 ("func (c *channelPool) Close(conn interface{}) error {") |
| RELEASE | `Release()` — shut the pool down | caller | external | none | caller | channel.go:224 ("func (c *channelPool) Release() {") |
| LEN | `Len()` — query the number of connections | caller | external | none; returns int | caller | channel.go:246 ("func (c *channelPool) Len() int {") |
| PING | `Ping(conn)` — validate a connection through the pool (exported method, not part of the `Pool` interface) | caller | external | the connection | caller (needs a type assertion) | channel.go:216 ("func (c *channelPool) Ping(conn interface{}) error {") |
| FACTORY_OK | Factory returned a connection and no error | Factory seam (user function) | internal (delivered result) | (conn, nil) | Factory, called by a Get that found no idle connection while below MaxCap | channel.go:154 ("conn, err := c.factory()") |
| CLOSEFN_OK | Close callback returned nil | Close-callback seam (user function) | internal (delivered result) | nil | Close callback, called by Close, by Put when idle storage is full, by Get when it discards a connection, and by Release for each idle connection | channel.go:212 ("return c.close(conn)"), channel.go:241 ("closeFun(wrapConn.conn)") |
| IDLE_TIMEOUT | An idle connection's idle time passes IdleTimeout (IdleTimeout > 0) | clock | internal (time) | the idle connection's timestamp | passage of time; no timer object exists | read lazily at channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {") |

## Undesired variants

| Id | Variant | Base event | Category (key) | Class | What arrives |
|---|---|---|---|---|---|
| UV-01 | PUT_LOST — a checked-out connection is never given back (neither Put nor Close) | PUT, CLOSE | loss | external | nothing, ever |
| UV-02 | PUT_DELAYED — a checked-out connection is given back only after a long time, while other Gets need one | PUT | delay | external | a Put, late |
| UV-03 | PUT_DUP — the same connection is Put twice | PUT | duplication | external | a second Put of a connection the pool already holds or has handed on |
| UV-04 | CLOSE_DUP — the same connection is Closed twice | CLOSE | duplication | external | a second Close |
| UV-05 | CLOSE_STALE — Close of a connection the caller already gave back with Put (stale reference: the connection is now idle or checked out by someone else) | CLOSE | out-of-order | external | a Close after the matching Put |
| UV-06 | PUT_CLOSE_RACE — Put(conn) and Close(conn) of the same connection at the same time from two goroutines | PUT, CLOSE | contradiction | external | both, concurrently |
| UV-07 | PUT_FOREIGN — Put of a connection that this pool never created | PUT | commission | external | a Put with no matching Get |
| UV-08 | CLOSE_FOREIGN — Close of a connection that this pool never created | CLOSE | commission | external | a Close with no matching Get |
| UV-09 | NIL_CONN — Put, Close or Ping with a nil connection | PUT, CLOSE, PING | value | external | nil payload |
| UV-10 | PUT_BROKEN — Put of a connection that is dead (plausible but unusable payload) | PUT | value | external | a dead connection |
| UV-11 | FACTORY_ERR — Factory returns an error | FACTORY_OK | loss | internal (delivered result) | (_, err) |
| UV-12 | FACTORY_HANG — Factory does not return for a long time | FACTORY_OK | delay | internal (delivered result) | no result yet |
| UV-13 | FACTORY_CONN_AND_ERR — Factory returns a non-nil connection and a non-nil error | FACTORY_OK | contradiction | internal (delivered result) | (conn, err) |
| UV-14 | FACTORY_NIL_CONN — Factory returns (nil, nil) | FACTORY_OK | value | internal (delivered result) | (nil, nil) |
| UV-15 | CLOSEFN_ERR — Close callback returns an error | CLOSEFN_OK | loss | internal (delivered result) | err |
| UV-16 | CLOSEFN_HANG — Close callback does not return for a long time | CLOSEFN_OK | delay | internal (delivered result) | no result yet |
| UV-17 | FACTORY_REENTRY — Factory calls a method of the same pool while it runs | FACTORY_OK | commission | internal (callback-initiated call) | a pool call from inside Factory |
| UV-18 | CLOSEFN_REENTRY — Close callback calls a method of the same pool while it runs | CLOSEFN_OK | commission | internal (callback-initiated call) | a pool call from inside the Close callback |

## Gate-type annotations

| Event | Branches? | Gate |
|---|---|---|
| GET | yes | **service-side state**: pool shut down or not; an idle connection available or not; live-connection count vs MaxCap. Per dequeued idle connection, also **payload content** (its idle timestamp vs IdleTimeout) and a **seam result** (Ping's answer, when Ping is configured). For a creating Get, the Factory result. |
| PUT | yes | **payload**: nil or not (checked first, without the lock). Then **service-side state**: pool shut down or not; a waiting Get exists or not; idle storage full or not. Connection identity is **not** examined. |
| CLOSE | yes | **payload**: nil or not. Then **service-side state**: shut down or not. Identity not examined. |
| RELEASE | yes | **service-side state**: already shut down or not. |
| LEN | no | — (reads the idle count) |
| PING | yes | **payload**: nil or not; otherwise calls the configured Ping without checking that one is configured. |
| FACTORY_OK | yes (with its variants) | **payload content**: error nil or not. Whether the connection value is nil is not examined. |
| CLOSEFN_OK | yes (with its variants) | **payload content**: error nil or not; the caller receives it on Close and on Put-when-full, it is discarded on Get's discard path and in Release. |
| IDLE_TIMEOUT | — | no handler runs when the time passes; the comparison happens when a Get dequeues that connection (gate: payload timestamp vs IdleTimeout, strict "older than"). |

## Remembrance semantics

Entities that end: **connections** (closed or discarded), **waiting Gets** (served), and the **pool** itself (shut down).

* **Ended connection.** The pool keeps no record of connections at all: no identity set, no registry of checked-out connections. It keeps only a live-connection *count*. A closed or discarded connection leaves behind exactly one decrement of that count. A later Put, Close or Ping that references an ended connection is not recognised as such: it resolves exactly like a reference to a live connection of this pool (Put stores it or hands it on, Close decrements the count again and calls the Close callback again). Bound: none (no memory to bound).
* **Checked-out connection.** Leaves behind its share of the live count, until a Put (count unchanged, connection stored or handed on) or a Close (count −1).
* **Served waiting Get.** Its private one-slot channel is removed from the FIFO list when a Put serves it; nothing else is remembered.
* **Shut-down pool.** After Release the pool remembers: that it is shut down (the idle store, Factory, Close callback and Ping references are cleared together), the live-connection count as it was (not reset), and the FIFO list of waiting Gets as it was (not cleared, not signalled). Idle connections present at shutdown are closed with the Close callback captured before clearing. A later Get resolves to the "pool is closed" error; a later Put or Close resolves against the cleared Close callback; a later Release finds the cleared idle store and returns; a later Len reports 0; a later Ping calls the cleared Ping reference. Bound: the instance lives until garbage-collected; nothing expires.

## Upstream-guard annotations

One deployment topology: an in-process library; callers are goroutines of the same process. There is no upstream layer between the caller and the pool.

| Event | Validated upstream | Absent here (not validated by the pool) |
|---|---|---|
| GET | nothing upstream. Construction (NewChannelPool) guarantees: InitialCap ≤ MaxIdle, MaxIdle ≤ MaxCap, InitialCap ≥ 0, Factory and Close callback set (channel.go:59-67) | MaxCap > 0 is not required (MaxCap = 0 is accepted); no deadline or cancellation can be passed |
| PUT | Go type system only (any value is accepted as `interface{}`) | origin (connection from this pool?), duplicate return, liveness of the connection |
| CLOSE | none | origin, duplicate close, whether the connection is currently idle |
| RELEASE | none | — |
| LEN | none | — |
| PING | none | whether a Ping function is configured |
| FACTORY_OK | construction requires a non-nil Factory (channel.go:62-64) | shape of the result ((conn, err) both non-nil; (nil, nil)); bounded run time; no re-entry |
| CLOSEFN_OK | construction requires a non-nil Close callback (channel.go:65-67) | bounded run time; no re-entry |
| IDLE_TIMEOUT | none (Go's `time.Now` carries a monotonic reading — stdlib contract, NAT-6) | IdleTimeout ≤ 0 disables the comparison; no lower bound |

Where an upstream guarantee makes a cell unreachable, the matrix keeps the code's actual handling and the annotation above names the guarantee.

## Lock-discipline annotation

The pool has one mutex (`sync.RWMutex`, used only via `Lock`; channel.go:41). `sync.Mutex` is not reentrant.

| Mutex-held section | Acquired at | Events / callbacks fired inside | Reentrancy contract |
|---|---|---|---|
| idle-store read for Get/Len | channel.go:96 ("c.mu.Lock()") | none | n/a |
| Get, no idle connection | channel.go:131 ("c.mu.Lock()") | debug log; **Factory** (FACTORY_OK, UV-11..UV-14, UV-17) | none documented: Config comment channel.go:25-26 and README.md:21 describe what Factory does, not what it may call. A Factory that calls Get, Put, Close, Release or Len on the same pool blocks forever on this mutex (UV-17); Get locks it first in its idle-store read |
| Put | channel.go:172 ("c.mu.Lock()") | hand-off to a waiting Get (non-blocking send, one-slot channel), enqueue (non-blocking) | no callback runs inside |
| Close | channel.go:206 ("c.mu.Lock()"), released by `defer` (channel.go:207) | **Close callback** (CLOSEFN_OK, UV-15, UV-16, UV-18) | none documented: channel.go:27-28, README.md:24. A Close callback that calls any locking method of the same pool blocks forever when reached via Close, Put-when-full or Get's discard path (UV-18) |
| Release, clearing | channel.go:225 ("c.mu.Lock()") | none — the Close callback for idle connections runs after the unlock (channel.go:232 ("c.mu.Unlock()"), channel.go:241) | a Close callback that re-enters the pool from inside Release does not block |

Ping (channel.go:124, channel.go:220) runs without the mutex. The README states no reentrancy rule for any callback (README.md:17-62): that gap is itself a finding (Q-08).

## Undesired-coverage

Rows = event sources, columns = checklist categories (sidecar keys).

| Event source | loss (F-12) | delay (F-13) | duplication (F-14) | out-of-order (F-15) | contradiction (F-16) | commission (F-17) | value (F-18) |
|---|---|---|---|---|---|---|---|
| Caller (GET, PUT, CLOSE, RELEASE, LEN, PING) | UV-01 | UV-02 | UV-03, UV-04 | UV-05; a Put/Close/Get after Release is the Released row of the base columns (the pool cannot reopen) | UV-06; cross-caller races are pairs P-01..P-05, P-09 | UV-07, UV-08 | UV-09, UV-10 |
| Factory seam | UV-11 | UV-12 | n/a: Factory is called synchronously once per creation and returns once | n/a: the result is returned on the calling goroutine under the mutex; no result can arrive after the creating Get returned | UV-13 | UV-17 | UV-14 |
| Close-callback seam | UV-15 | UV-16 | n/a: called synchronously, returns once per call | n/a: synchronous call; no late result exists | n/a: the callback returns a single error value | UV-18 | n/a: the only result is an error value; its non-nil case is UV-15 |
| Ping seam (used inside GET, and by PING) | n/a: a Ping error is a GET guard input (guard group G-03, branch discard), not a pool-level event; GET cells cover it | n/a: Ping runs without the mutex, so a slow Ping delays only the calling Get; no pool-level event | n/a: synchronous, returns once | n/a: synchronous; no late result | n/a: single error value | n/a: Ping only runs when the pool calls it | n/a: a Ping that wrongly reports a dead connection as healthy cannot be detected by the pool; the effect equals UV-10 on the receiving caller |
| Clock (IDLE_TIMEOUT) | n/a: no timer exists that could fail; idle age is computed from timestamps when a Get dequeues | n/a: the IDLE_TIMEOUT column itself records that nothing happens at expiry time | n/a: a passage of time cannot repeat | n/a: timestamps are compared with the monotonic reading (NAT-6) | n/a: one comparison per dequeued connection | n/a: no timer can fire spuriously | n/a: wall-clock jumps do not affect monotonic comparison (NAT-6) |

## Cross-source interaction pairs

Sources: distinct caller goroutines (each caller is an independent source), the Factory seam, the Close-callback seam, the clock. Shared entities: the pool instance (its idle store, live count, waiter list, shut-down flag) and individual connections.

| Pair | Event A (source) | Event B (source) | Shared entity | a: ordering | b: ordering |
|---|---|---|---|---|---|
| P-01 | GET finding no idle connection at MaxCap (caller 1) | PUT (caller 2) | idle store + waiter list | P-01a: the Get registers as waiting before the Put runs | P-01b: the Put runs after the Get saw no idle connection but before the Get registered as waiting |
| P-02 | GET (caller 1) | RELEASE (caller 2) | pool shut-down flag, idle store | P-02a: Get completes, then Release | P-02b: Release starts while a Get is in progress (Get already saw the pool open) |
| P-03 | PUT of a checked-out connection (caller 1) | RELEASE (caller 2) | that connection | P-03a: Put, then Release | P-03b: Release, then Put |
| P-04 | CLOSE (caller 1) | GET at MaxCap (caller 2) | live-connection count | P-04a: Close, then Get | P-04b: Get registers as waiting, then Close |
| P-05 | PUT(conn) (caller 1) | CLOSE(conn) of the same connection (caller 2) | that connection | P-05a: Put, then Close | P-05b: Close, then Put |
| P-06 | FACTORY_OK (Factory seam, inside a creating Get) | RELEASE (caller) | pool shut-down flag, live count | P-06a: Factory returns, then Release | P-06b: Release is called while Factory runs |
| P-07 | IDLE_TIMEOUT for an idle connection (clock) | GET (caller) | that idle connection | P-07a: the idle time passes, then a Get dequeues it | P-07b: a Get dequeues it just before the idle time passes |
| P-08 | GET validating an idle connection with Ping (caller 1) | RELEASE (caller 2) | the Ping reference | P-08a: Release clears the Ping reference before the Get reads it | P-08b: the Get reads the Ping reference, then Release clears it, then the Get calls Ping |
| P-09 | RELEASE (caller 1) | RELEASE (caller 2) | pool shut-down flag | P-09a: caller 1 first | P-09b: caller 2 first (symmetric; both orderings traced) |

## Event annotations

### GET
- gate: service-side state (shut down; idle connection available; live count vs MaxCap) plus payload timestamp and Ping result per dequeued idle connection
- upstream_guards: none upstream, construction guarantees InitialCap <= MaxIdle <= MaxCap and InitialCap >= 0 (channel.go:59), MaxCap > 0 not required, no deadline or cancellation parameter
- coverage:
  - loss: n/a: a Get that never arrives changes nothing; a blocked Get cannot be abandoned (no cancellation API)
  - delay: n/a: Get takes no deadline; waiting without bound is the GET disposition in the waiting rows
  - duplication: n/a: every Get is an independent request; repeating Get is legitimate use
  - out-of-order: n/a: a Get after Release is the GET cell of row Released
  - contradiction: n/a as a column: concurrent Get with Put/Close/Release are pairs P-01, P-02, P-04, P-08
  - commission: n/a: Get has no trigger other than the caller
  - value: n/a: Get has no payload

### PUT
- gate: payload nil check, then service-side state (shut down; waiting Get exists; idle storage full)
- upstream_guards: Go type system only, origin not checked, duplicate not checked, liveness not checked
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: n/a: a Put after Release is the PUT cell of row Released (the pool cannot reopen)
  - contradiction: UV-06
  - commission: UV-07
  - value: UV-09, UV-10

### CLOSE
- gate: payload nil check, then service-side state (shut down)
- upstream_guards: none, origin not checked, duplicate not checked, idle-membership not checked
- coverage:
  - loss: UV-01
  - delay: n/a: a late Close only delays the decrement; the same as UV-02 for the capacity it holds
  - duplication: UV-04
  - out-of-order: UV-05
  - contradiction: UV-06
  - commission: UV-08
  - value: UV-09

### RELEASE
- gate: service-side state (already shut down or not)
- upstream_guards: none
- coverage:
  - loss: n/a: a pool that is never released lives until the process ends; that is its normal lifetime
  - delay: n/a: Release has no deadline relation
  - duplication: n/a: a second Release is the RELEASE cell of row Released
  - out-of-order: n/a: there is no event after which Release would be stale
  - contradiction: n/a as a column: concurrent Release calls are pair P-09
  - commission: n/a: only the caller triggers it
  - value: n/a: no payload

### LEN
- gate: none (no branch)
- upstream_guards: none
- coverage:
  - loss: n/a: a query that does not arrive changes nothing
  - delay: n/a: no timing relation
  - duplication: n/a: read-only, repeating is harmless by construction
  - out-of-order: n/a: a Len after Release is the LEN cell of row Released
  - contradiction: n/a: read-only
  - commission: n/a: only the caller triggers it
  - value: n/a: no payload

### PING
- gate: payload nil check; no check that a Ping function is configured
- upstream_guards: none, configured Ping not required
- coverage:
  - loss: n/a: a Ping call that does not arrive changes nothing
  - delay: n/a: runs without the mutex, a slow Ping delays only its caller
  - duplication: n/a: repeating a validation is legitimate
  - out-of-order: n/a: a Ping after Release is the PING cell of row Released
  - contradiction: n/a: read-only with respect to the pool
  - commission: n/a: only the caller triggers it
  - value: UV-09

### FACTORY_OK
- gate: payload error nil or not; connection nil-ness not examined
- upstream_guards: non-nil Factory required at construction (channel.go:62), result shape not checked, run time not bounded, re-entry not prevented
- coverage:
  - loss: UV-11
  - delay: UV-12
  - duplication: n/a: synchronous call, one result per call
  - out-of-order: n/a: synchronous; no late result after the creating Get returned
  - contradiction: UV-13
  - commission: UV-17
  - value: UV-14

### CLOSEFN_OK
- gate: payload error nil or not; propagated to Close and Put callers, discarded in Get and Release
- upstream_guards: non-nil Close callback required at construction (channel.go:65), run time not bounded, re-entry not prevented
- coverage:
  - loss: UV-15
  - delay: UV-16
  - duplication: n/a: synchronous call, one result per call
  - out-of-order: n/a: synchronous; no late result
  - contradiction: n/a: single error value
  - commission: UV-18
  - value: n/a: the only result is an error value, its non-nil case is UV-15

### IDLE_TIMEOUT
- gate: payload timestamp vs IdleTimeout, compared only when a Get dequeues the connection
- upstream_guards: none, IdleTimeout <= 0 disables the comparison, monotonic clock assumed (NAT-6)
- coverage:
  - loss: n/a: no timer exists that could fail
  - delay: n/a: the IDLE_TIMEOUT column records the lazy handling itself
  - duplication: n/a: a passage of time cannot repeat
  - out-of-order: n/a: monotonic comparison (NAT-6)
  - contradiction: n/a: one comparison per dequeued connection
  - commission: n/a: no timer can fire spuriously
  - value: n/a: wall-clock jumps do not affect the monotonic comparison (NAT-6)
