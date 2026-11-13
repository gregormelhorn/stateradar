# channelPool — Step 3 event catalogue

<!-- event-ids: E-GET E-PUT E-CLOSE E-RELEASE E-LEN I-IDLE-EXPIRE UV-GET-DELAY UV-GET-STALE UV-PUT-LOSS UV-PUT-DUP UV-PUT-FOREIGN UV-PUT-BROKEN UV-PUT-CLOSE-SAME UV-CLOSE-DUP UV-CLOSE-FOREIGN UV-CLOSE-IDLE UV-FACTORY-ERR UV-FACTORY-SLOW UV-FACTORY-NILCONN UV-CLOSEFN-ERR UV-CLOSEFN-SLOW UV-CB-REENTER -->

Component: one pool instance created by `NewChannelPool` (channel.go). Callers use the `Pool` interface (pool.go:11-21): `Get`, `Put`, `Close`, `Release`, `Len`. The pool calls three user-supplied functions from `Config`: `Factory` (create a connection), `Close` (close a connection), `Ping` (optional validity check) (channel.go:25-30). A connection is an opaque `interface{}` value.

Construction is not a catalogue event: `NewChannelPool` validates the configuration and fills `InitialCap` idle connections before any caller holds the pool; a validation failure or a factory error returns an error and no pool (channel.go:59-67, channel.go:82-89).

## Events

| Id | Name | Source | Class (PA-4) | Payload gist | Produced / consumed |
|---|---|---|---|---|---|
| E-GET | `Get()` | caller (any goroutine) | external — monitored input | none; returns a connection or an error | produced by callers; consumed by channel.go:103-164 |
| E-PUT | `Put(conn)` | caller | external — monitored input | a connection previously returned by `Get` of this pool | channel.go:167-199 |
| E-CLOSE | `Close(conn)` | caller (also called internally by Get's discard paths and by Put) | external — monitored input | a connection to close and stop counting | channel.go:202-213 |
| E-RELEASE | `Release()` | caller (also called by the constructor on a factory error) | external — monitored input | none | channel.go:224-243 |
| E-LEN | `Len()` | caller | external — monitored input | none; returns an int | channel.go:246-248 |
| I-IDLE-EXPIRE | idle age of a pooled connection passes `IdleTimeout` (`IdleTimeout > 0`) | clock | internal | the pooled connection and its last-return timestamp | no producer (no timer); evaluated when Get receives the connection, channel.go:115-116 |

## Undesired variants

Each variant is an undesired form of the base event named in its row; it inherits that event's class.

| Id | Base event | Category (key) | Variant |
|---|---|---|---|
| UV-GET-DELAY | E-GET | delay | a Get blocked waiting for a connection stays blocked longer than its caller can tolerate |
| UV-GET-STALE | E-GET | out-of-order | a Get that began before a Release (it already holds the pool's idle channel) continues after Release started |
| UV-PUT-LOSS | E-PUT | loss | the caller never returns a connection it got (neither Put nor Close) |
| UV-PUT-DUP | E-PUT | duplication | the same connection is Put twice without a Get in between |
| UV-PUT-FOREIGN | E-PUT | commission | Put of a connection this pool never handed out (no matching Get) |
| UV-PUT-BROKEN | E-PUT | value | Put of a connection that is no longer usable (remote end gone) |
| UV-PUT-CLOSE-SAME | E-PUT | contradiction | the same connection is both Put and Closed (two callers, or one caller doing both) |
| UV-CLOSE-DUP | E-CLOSE | duplication | the same connection is Closed twice |
| UV-CLOSE-FOREIGN | E-CLOSE | commission | Close of a connection this pool never handed out |
| UV-CLOSE-IDLE | E-CLOSE | value | Close of a connection that is currently idle inside the pool (it was Put before) |
| UV-FACTORY-ERR | E-GET | loss | the `Factory` callback invoked by Get returns an error |
| UV-FACTORY-SLOW | E-GET | delay | the `Factory` callback invoked by Get blocks for a long time |
| UV-FACTORY-NILCONN | E-GET | value | the `Factory` callback returns a nil connection with a nil error |
| UV-CLOSEFN-ERR | E-CLOSE | loss | the `Close` callback returns an error |
| UV-CLOSEFN-SLOW | E-CLOSE | delay | the `Close` callback blocks for a long time |
| UV-CB-REENTER | E-GET | commission | a `Factory` or `Close` callback calls a method of the same pool (re-entrant call) |

## Gate-type annotation

* **E-GET** — gate: service-side state. Branches on: pool released or not (nil idle channel); an idle connection present or not; for an idle connection, its age against `IdleTimeout` and the `Ping` result; with no idle connection, the open-connection count against `MaxCap`; then the `Factory` result. The payload is empty.
* **E-PUT** — gate: payload (nil connection → error) then service-side state: released; a waiting Get exists; idle channel full.
* **E-CLOSE** — gate: payload (nil → error) then service-side state: released (no close function any more). The connection's identity is never checked: the pool does not record which connections it handed out.
* **E-RELEASE** — gate: service-side state (already released or not).
* **E-LEN** — no branching; returns the number of idle connections (0 after Release).
* **I-IDLE-EXPIRE** — gate: service-side state: only examined when a Get receives that connection (idle path or handoff).

## Remembrance semantics

Provenance of every line in this section: observed in code (not a requirement).

* **Connections handed out.** The pool remembers no identity of a handed-out connection, only the count of open connections (created minus closed through the pool). A late `Put` or `Close` is resolved purely by the current pool state, never by the connection's history: any non-nil value is accepted.
* **Idle connections.** Each is remembered with the time it entered the pool (creation for the initial fill, otherwise the time of the `Put`). Bound: at most `MaxIdle` entries. An idle connection that ages past `IdleTimeout` is not removed until a Get receives it or Release drains it.
* **Waiting Gets.** Each blocked Get is one entry in a FIFO queue, with no bound and no expiry. An entry leaves the queue only when a Put hands it a connection.
* **Released pool.** Release drops the idle channel and the three callbacks; it keeps the open-connection count and the waiter queue untouched. A late `Get` resolves to `ErrClosed` ("pool is closed", pool.go:7); a late `Put` or `Close` resolves to a nil return without calling any close function; a late `Release` returns at once; a late `Len` returns 0. The released state is never left.

## Upstream-guard annotation

Provenance of every line in this section: observed in code (not a requirement).

One deployment topology: the pool is a library inside one process; callers are that process's goroutines.

* **E-GET** — upstream: none in this repository; no context or deadline is passed. Absent here: no wait bound, no cancellation.
* **E-PUT / E-CLOSE** — upstream: none; the pool trusts the caller to return each connection it got exactly once, and only to the pool it came from. Absent here: ownership check, duplicate check. Present here: nil check (channel.go:168, channel.go:203).
* **E-RELEASE** — upstream: none. Absent here: coordination with in-flight Gets or with connections still held by callers.
* **E-LEN** — upstream: none.
* **Callbacks** — upstream: `NewChannelPool` requires non-nil `Factory` and `Close` (channel.go:62, channel.go:65); `Ping` is optional (channel.go:78). Nothing constrains what a callback does (duration, re-entry, nil results).
* **Configuration** — upstream: `NewChannelPool` requires `InitialCap <= MaxIdle <= MaxCap` and `InitialCap >= 0` (channel.go:59). `MaxCap == 0` and `IdleTimeout <= 0` are accepted.

## Lock-discipline annotation

The pool has one mutex `mu` (a `sync.RWMutex` used only through `Lock`). Go mutexes are not re-entrant.

| Critical section | What fires inside it | Lock site |
|---|---|---|
| `getConns` (start of Get, inside Len) | nothing external | channel.go:96 |
| Get slow path | debug log; enqueue of a waiter; **the user `Factory` callback** | lock channel.go:131; unlock channel.go:136, channel.go:151, channel.go:156, channel.go:160; factory call channel.go:154 |
| Put | handoff of the connection to a waiter (non-blocking, buffered); enqueue into the idle channel | lock channel.go:172; unlock before any Close call, channel.go:175, channel.go:194 |
| Close | decrement of the open count; **the user `Close` callback** | channel.go:206 with deferred unlock channel.go:207; callback channel.go:212 |
| Release | reading and clearing the fields only; the saved close function runs after the unlock | channel.go:225-232; callbacks at channel.go:241 |

Observed in code (provenance only): the `Factory` callback runs while the mutex is held — the Get slow path takes the lock before calling it and releases it only after it returns. The `Close` callback runs while the mutex is held — `Close` takes the lock and defers the unlock to its own end.

Outside any lock: the `Ping` callback (channel.go:124 → channel.go:220) and Get's own discard calls to `Close`.

Reentrancy contract: the README and the Go doc comments say nothing about whether `Factory` or `Close` may call pool methods or may block (README.md:21-27, channel.go:25-30). A `Factory` or `Close` callback that calls `Get`, `Put`, `Close`, `Release` or `Len` of the same pool waits for the mutex held by its own call chain. A `Ping` callback is not under the mutex.

## Undesired-coverage

Rows: external event sources (the caller-facing events, with the callbacks they invoke). A cell names the variant ids, or `n/a: <reason>`.

| Source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| E-GET (with Factory, Ping) | UV-FACTORY-ERR | UV-GET-DELAY, UV-FACTORY-SLOW | n/a: a Get carries no identity; concurrent Gets are independent requests, each served or queued separately | UV-GET-STALE | n/a: a Get has no payload; simultaneous Gets cannot contradict each other; Get against Release is covered by the pairs P-01, P-04, P-05 | UV-CB-REENTER | UV-FACTORY-NILCONN |
| E-PUT | UV-PUT-LOSS | n/a: Put has no deadline and the idle timestamp is taken at the Put itself, so a late Put changes nothing but the timestamp | UV-PUT-DUP | n/a as a separate column: a Put after Release is the Released row of E-PUT; Put against Release is pair P-06 | UV-PUT-CLOSE-SAME | UV-PUT-FOREIGN | UV-PUT-BROKEN |
| E-CLOSE (with the Close callback) | UV-CLOSEFN-ERR | UV-CLOSEFN-SLOW | UV-CLOSE-DUP | n/a as a separate column: a Close after Release is the Released row of E-CLOSE; Close against Release is pair P-07 | UV-PUT-CLOSE-SAME | UV-CLOSE-FOREIGN | UV-CLOSE-IDLE |
| E-RELEASE | n/a: a Release that never comes leaves the pool open, which is the normal Open behaviour | n/a: Release has no deadline and does not wait for anything but the mutex | n/a as a separate column: a second Release is the Released row of E-RELEASE | n/a: ordering against other callers is covered by the pairs P-01, P-04 … P-07 | n/a: two concurrent Releases serialise on the mutex; the second is the Released row of E-RELEASE | n/a: Release is only called by callers and by the constructor on a factory error | n/a: Release has no payload |
| E-LEN | n/a: a read-only query; omitting it changes no state | n/a: Len waits only for the mutex; the waiting is caused by UV-FACTORY-SLOW and UV-CLOSEFN-SLOW | n/a: read-only, idempotent | n/a: read-only; the value after Release is the Released row of E-LEN | n/a: read-only | n/a: read-only | n/a: no payload |
| I-IDLE-EXPIRE (clock) | n/a: the expiry is not delivered by any timer, so it cannot be lost; I-IDLE-EXPIRE itself is the column | n/a: the expiry is evaluated lazily; its lateness is the I-IDLE-EXPIRE disposition | n/a: a connection expires once | n/a: expiry against Get is pair P-09 | n/a: a single clock | n/a: the clock fires nothing | n/a: the comparison uses the monotonic clock reading of time.Now; a wrong clock value is outside the statechart (PA-19) |

Ping callback (invoked by E-GET outside the mutex): its failure is the documented discard path of E-GET (README.md:14); a slow Ping delays only its own Get; a re-entrant Ping does not deadlock (not under the mutex); a Ping that accepts a dead connection is a user-callback defect outside the pool. No separate variant column.

## Event annotations

### E-GET
- gate: service-side state (released, idle present, idle age vs IdleTimeout, Ping result, open count vs MaxCap, Factory result)
- upstream_guards: none in this repository, no deadline or context accepted
- coverage:
  - loss: UV-FACTORY-ERR
  - delay: UV-GET-DELAY, UV-FACTORY-SLOW
  - duplication: n/a: a Get carries no identity; concurrent Gets are independent requests
  - out-of-order: UV-GET-STALE
  - contradiction: n/a: no payload; Get against Release is covered by pairs P-01, P-04, P-05
  - commission: UV-CB-REENTER
  - value: UV-FACTORY-NILCONN

### E-PUT
- gate: payload (nil) then service-side state (released, waiter present, idle channel full)
- upstream_guards: none; caller trusted to return each connection exactly once to its own pool, nil check only (channel.go:168)
- coverage:
  - loss: UV-PUT-LOSS
  - delay: n/a: no deadline; the idle timestamp is taken at the Put itself
  - duplication: UV-PUT-DUP
  - out-of-order: n/a: Put after Release is the Released row of E-PUT; Put against Release is pair P-06
  - contradiction: UV-PUT-CLOSE-SAME
  - commission: UV-PUT-FOREIGN
  - value: UV-PUT-BROKEN

### E-CLOSE
- gate: payload (nil) then service-side state (released: no close function)
- upstream_guards: none; no ownership check, nil check only (channel.go:203)
- coverage:
  - loss: UV-CLOSEFN-ERR
  - delay: UV-CLOSEFN-SLOW
  - duplication: UV-CLOSE-DUP
  - out-of-order: n/a: Close after Release is the Released row of E-CLOSE; Close against Release is pair P-07
  - contradiction: UV-PUT-CLOSE-SAME
  - commission: UV-CLOSE-FOREIGN
  - value: UV-CLOSE-IDLE

### E-RELEASE
- gate: service-side state (already released or not)
- upstream_guards: none; no coordination with in-flight Gets or held connections
- coverage:
  - loss: n/a: a missing Release leaves the pool in normal Open behaviour
  - delay: n/a: no deadline; waits only for the mutex
  - duplication: n/a: a second Release is the Released row of E-RELEASE
  - out-of-order: n/a: covered by pairs P-01, P-04, P-05, P-06, P-07
  - contradiction: n/a: concurrent Releases serialise on the mutex; the second is the Released row
  - commission: n/a: only callers and the constructor call Release
  - value: n/a: no payload

### E-LEN
- gate: none (returns the idle count)
- upstream_guards: none
- coverage:
  - loss: n/a: read-only query
  - delay: n/a: waits only for the mutex, caused by UV-FACTORY-SLOW and UV-CLOSEFN-SLOW
  - duplication: n/a: read-only, idempotent
  - out-of-order: n/a: the value after Release is the Released row of E-LEN
  - contradiction: n/a: read-only
  - commission: n/a: read-only
  - value: n/a: no payload

### I-IDLE-EXPIRE
- gate: service-side state (examined only when a Get receives the connection)
- upstream_guards: none; IdleTimeout <= 0 disables the check (channel.go:115)
- coverage:
  - loss: n/a: no timer delivers the expiry, so it cannot be lost
  - delay: n/a: lazy evaluation is the I-IDLE-EXPIRE disposition itself
  - duplication: n/a: a connection expires once
  - out-of-order: n/a: expiry against Get is pair P-09
  - contradiction: n/a: single clock
  - commission: n/a: the clock fires nothing
  - value: n/a: monotonic clock reading; wrong clock values are outside the statechart (PA-19)

## Cross-source interaction pairs

Pairs of external events from different sources on the same entity (the pool, or one connection), both orderings.

| Pair | Events (sources) | Entity | Ordering a | Ordering b |
|---|---|---|---|---|
| P-01 | E-GET (caller A, blocking at capacity) × E-RELEASE (caller B) | pool | P-01a: Get blocks as a waiter, then Release | P-01b: Release, then Get |
| P-02 | E-GET (caller A) × E-PUT (caller B) at capacity | pool | P-02a: Get finds no idle connection, Put runs before the Get queues itself, then the Get queues | P-02b: Put enqueues first, then Get takes the idle connection |
| P-03 | E-GET (caller A, blocking) × E-CLOSE (caller B) at capacity | pool | P-03a: Get blocks as a waiter, then Close | P-03b: Close, then Get |
| P-04 | E-GET with a configured Ping (caller A) × E-RELEASE (caller B) | pool (ping function, idle channel) | P-04a: Get has received an idle connection and checked that Ping is set, then Release | P-04b: Release, then Get |
| P-05 | E-GET creating a connection (caller A, inside Factory) × E-RELEASE (caller B) | pool | P-05a: Get is inside Factory, then Release is called | P-05b: Release, then Get |
| P-06 | E-PUT (caller A) × E-RELEASE (caller B) | connection / pool | P-06a: Put, then Release | P-06b: Release, then Put |
| P-07 | E-CLOSE (caller A) × E-RELEASE (caller B) | connection / pool | P-07a: Close, then Release | P-07b: Release, then Close |
| P-08 | E-PUT (caller A) × E-CLOSE (caller B) on the same connection | connection | P-08a: Put, then Close | P-08b: Close, then Put |
| P-09 | I-IDLE-EXPIRE (clock) × E-GET (caller) | idle connection | P-09a: the idle connection expires, then a Get receives it | P-09b: a Get receives it, then its age would have passed IdleTimeout |
