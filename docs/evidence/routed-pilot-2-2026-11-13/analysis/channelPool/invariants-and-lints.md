# channelPool — Step 5 invariants and lint findings

Executed checks: `check_guards.py` (guard groups, `guard-results.txt`) and `check_invariants.py` (SYS step checks with z3, `invariant-results.txt`). Outputs pasted in `summary.md`.

## NAT — assumptions about the environment

| Id | Predicate / assumption | Source | Status |
|---|---|---|---|
| NAT-1 | `Factory` returns within bounded time | no contract text (channel.go:25, README.md:21) | unstated; Q-09 |
| NAT-2 | the `Close` callback returns within bounded time | no contract text (channel.go:27, README.md:24) | unstated; Q-09 |
| NAT-3 | `Factory` and `Close` never call methods of the same pool | no contract text | unstated; Q-09 |
| NAT-4 | every connection a caller got from `Get` is returned exactly once, by `Put` or `Close`, to the same pool; no other value is passed | README.md:52 states the Put half only ("Put the connection back into the connection pool, when the connection is no longer in use") | partly stated; Q-10, Q-11, Q-12 |
| NAT-5 | `Factory` returns a non-nil connection whenever its error is nil | no contract text | unstated; Q-19 |
| NAT-6 | the `*Config` passed to `NewChannelPool` is non-nil | no contract text; the constructor dereferences it at channel.go:59 | unstated; Q-20 |
| NAT-7 | `Ping` is safe to call from many goroutines at once (it runs outside the mutex) | no contract text (channel.go:29) | unstated; recorded, no finding depends on it |
| NAT-8 | Go channel semantics: a closed buffered channel yields its remaining values, then nil; `len` of a nil channel is 0 | Go language specification (external) | language contract |
| NAT-SYS-1 | when N pool instances (N processes) share one remote server, a server restart or overload is observed by all N near-simultaneously | multi-instance assumption (02-pilot Step 5) | environment assumption used by M-01 … M-03 |

## SYS — obligations (proposed predicates)

Every SYS line is `proposed` unless a doctrine line states it; the doctrine source is named.

| Id | Predicate | Doctrine | As-is |
|---|---|---|---|
| SYS-1 | in every Open state, 0 ≤ openingConns ≤ MaxCap | DOC-9 | holds under NAT-4; **violated** without it (z3: E-CLOSE of a foreign or duplicate value steps 0 → −1; a phantom decrement then a create gives 2 live connections with MaxCap 1) |
| SYS-2 | openingConns = idle + checked-out | proposed | holds under NAT-4, NAT-5; **violated** by UV-PUT-FOREIGN (z3) and UV-FACTORY-NILCONN |
| SYS-3 | a waiter exists only while idle = 0 and openingConns ≥ MaxCap | proposed (reading of DOC-4: waiting happens "when the connection pool is full") | **violated**: E-CLOSE with waiters steps into Open_Waiting_Stranded (z3 witness); the Get/Put race reaches it too (trace P-02a) |
| SYS-4 | after Release no Get remains blocked | proposed | **violated**: Release leaves `connReqs` untouched (channel.go:225-232) |
| SYS-5 | after Release, every connection the pool created is closed exactly once | DOC-6 | **violated** for connections checked out at Release: their later Put/Close close nothing (channel.go:208) |
| SYS-6 | a connection is held by at most one caller at a time | proposed | holds under NAT-4; **violated** by UV-PUT-DUP |
| SYS-7 | when Ping is configured, every connection Get returns passed Ping after it was last returned to the pool | DOC-3, DOC-19 | **violated** on the handoff path (channel.go:141-148 has no Ping) |
| SYS-8 | when IdleTimeout > 0, Get never returns a connection whose idle age exceeds IdleTimeout | DOC-18 | holds (G-02 on the idle path, G-05 on the handoff path) |
| SYS-9 | after a successful construction, idle = openingConns = InitialCap | DOC-8 | holds (channel.go:75, 82-89) |
| SYS-10 | idle ≤ MaxIdle | DOC-10 | holds (channel capacity, channel.go:70) |
| SYS-11 | while Open, openingConns ≥ InitialCap (reading of "minimum number of connections") | DOC-11 | **violated**: nothing replenishes below InitialCap (Get, Close, Put never create to restore a minimum) |
| SYS-12 | no user callback runs while `mu` is held | proposed | **violated**: Factory under mu (channel.go:154), Close callback under mu (channel.go:212) |
| SYS-13 | once Release has started, Get hands out no connection | proposed | **violated**: Get inside Factory completes after Release is called (P-05a); a stale Get can receive a connection Release is draining (UV-GET-STALE) |
| SYS-14 | every shared field is accessed under `mu` | proposed | **violated**: `c.ping` read at channel.go:123 without the lock, written at channel.go:229 under it |
| SYS-15 | an idle connection whose age exceeds IdleTimeout is closed within bounded time | DOC-2 (reading "will be closed and discarded") | **violated**: closing waits for the next Get or Release (no timer) |

### SYS check, state by state

| State | SYS-1 | SYS-2 | SYS-3 | SYS-4 | SYS-5 | SYS-6 | SYS-7 | SYS-8 | SYS-10 | SYS-11 | SYS-12 | SYS-13 | SYS-14 | SYS-15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Open_IdleAvailable | NAT-4 | NAT-4 | ✓ (no waiter) | n/a | n/a | NAT-4 | ✓ idle path | ✓ | ✓ | ✗ after Gets/Closes | ✗ (Factory fallback, Close) | n/a | ✗ (Get ping read) | ✗ |
| Open_IdleFull | NAT-4 | NAT-4 | ✓ | n/a | n/a | NAT-4 | ✓ | ✓ | ✓ (= MaxIdle) | ✓ if MaxIdle ≥ InitialCap | ✗ (Close) | n/a | ✗ | ✗ |
| Open_Empty | NAT-4 | NAT-4 | ✓ | n/a | n/a | NAT-4 | ✓ | ✓ | ✓ | ✗ possible | ✗ (Factory) | n/a | ✓ (no idle path) | ✓ (no idle) |
| Open_AtCapacity | NAT-4 | NAT-4 | ✓ | n/a | n/a | NAT-4 | ✓ | ✓ | ✓ | ✓ | ✗ (Close) | n/a | ✓ | ✓ |
| Open_AtCapacity_Waiting | NAT-4 | NAT-4 | ✓ (definition) | n/a | n/a | ✗ UV-PUT-DUP | ✗ handoff | ✓ | ✓ | ✓ | ✗ (Close) | n/a | ✓ | ✓ |
| Open_Waiting_Stranded | NAT-4 | NAT-4 | **✗ (definition)** | n/a | n/a | ✗ UV-PUT-DUP | ✗ handoff | ✓ | ✓ | ✗ possible | ✗ | n/a | ✗ | ✗ if idle > 0 |
| Released | n/a | n/a | n/a | **✗** (stranded waiters) | **✗** (checked-out connections) | n/a | n/a | n/a | ✓ (0) | n/a | ✓ (callbacks cleared) | **✗** (UV-GET-STALE, P-05a) | ✗ (race at the transition) | ✓ (drained) |

SYS-9 is checked at the initial transition only (✓).

## Doctrine mapping

<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 DOC-5 DOC-6 DOC-7 DOC-8 DOC-9 DOC-10 DOC-11 DOC-12 DOC-13 DOC-14 DOC-15 DOC-16 DOC-17 DOC-18 DOC-19 DOC-20 -->

| DOC | Mapping | Target |
|---|---|---|
| DOC-1 | structural | the connection is an opaque interface{} value throughout the model; no event or guard inspects it (catalogue: Payload gist column) |
| DOC-2 | cell | Open_IdleAvailable x I-IDLE-EXPIRE |
| DOC-3 | invariant | SYS-7 |
| DOC-4 | cell | Open_AtCapacity x E-GET |
| DOC-5 | cell | Open_Empty x E-PUT |
| DOC-6 | invariant | SYS-5 |
| DOC-7 | cell | Open_IdleAvailable x E-LEN |
| DOC-8 | invariant | SYS-9 |
| DOC-9 | invariant | SYS-1 |
| DOC-10 | invariant | SYS-10 |
| DOC-11 | invariant | SYS-11 |
| DOC-12 | cell | Released x E-GET |
| DOC-13 | cell | Open_AtCapacity_Waiting x UV-GET-DELAY |
| DOC-14 | rejected | performance and implementation-technique statement (a channel, "efficient"); prescribes no observable behaviour; outside the statechart (PA-19) |
| DOC-15 | rejected | attribution of the design origin (fatih/pool); not a behavioural obligation of this component |
| DOC-16 | cell | Open_IdleAvailable x E-CLOSE |
| DOC-17 | cell | Open_IdleAvailable x E-GET |
| DOC-18 | guard | G-02 |
| DOC-19 | invariant | SYS-7 |
| DOC-20 | cell | Open_IdleFull x E-PUT |

PA-22 result per mapped line:

* DOC-2 → the cell is `ignore (accidental)` (Q-13): the "will be closed" reading is **violated** in time (lazy closing); SYS-15 records it.
* DOC-3, DOC-19 → SYS-7 **violated** on the handoff path (Q-14).
* DOC-4 → `transition → Open_AtCapacity_Waiting`: implemented; "like the go db connection pool" (cancellable, bounded waiting) is not implemented (Q-02).
* DOC-6 → SYS-5 **violated** for checked-out connections (Q-06).
* DOC-7 → `handle` returning the idle count; whether "number of connections" means idle or all is open (Q-16).
* DOC-11 → SYS-11 **violated** under the "minimum" reading; contradicts DOC-8 (Q-15).
* DOC-13 → the error is documented, but the cell where it would apply (a Get waiting at capacity) is `ignore (accidental)`: the error is never returned (Q-03).
* DOC-12, DOC-16, DOC-17, DOC-20, DOC-5 → implemented by their cells (reject ErrClosed; handle; handle; handle with Close; transition).
* DOC-8, DOC-9, DOC-10, DOC-18 → their invariants or guard hold (DOC-9 only under NAT-4).

## Lint findings (Step 5 checklist)

| # | Lint | Finding | Provenance | Q |
|---|---|---|---|---|
| L-1 | waiting states without timeout | `Open_AtCapacity_Waiting` / `Open_Waiting_Stranded`: a waiter blocks with no timeout; `waitTimeOut` is declared and never used | observed-in-code channel.go:137 ("ret, ok := <-req"), channel.go:46 ("idleTimeout, waitTimeOut time.Duration") | Q-02 |
| L-2 | retries without a maximum | none: the Get loop retries only after consuming an idle connection or a handoff; factory errors are not retried | observed-in-code channel.go:119, 126, 145, 157 | — |
| L-3 | invoked external operations without an explicit failure outcome | Close-callback errors are dropped on Get's discard paths and in Release | observed-in-code channel.go:118 ("c.Close(wrapConn.conn)"), channel.go:241 ("closeFun(wrapConn.conn)") | Q-18 |
| L-4 | externally initiated operations without cancellation handling | `Get` has no context and no way to abandon a wait | observed-in-code channel.go:103 ("func (c *channelPool) Get() (interface{}, error) {") | Q-02 |
| L-5 | terminal or error states without documented meaning or diagnostic | `ErrMaxActiveConnReached` is documented but unreachable; `Released` has `ErrClosed` for Get but silent nil returns for Put/Close | observed-in-code channel.go:139, channel.go:208 | Q-03, Q-06 |
| L-6 | undefined startup or shutdown behaviour | shutdown with blocked waiters or checked-out connections is undefined; partial construction failure releases the pool (startup defined in code, not in docs) | observed-in-code channel.go:225-242, channel.go:84-86 | Q-01, Q-06, Q-17 |
| L-7 | unbounded queues or buffers, unhandled overload | the waiter queue `connReqs` has no bound | observed-in-code channel.go:135 ("c.connReqs = append(c.connReqs, req)") | Q-02 |
| L-8 | synchronized reset points | no counter or delay is reset by an external event (no backoff exists). Related multi-instance effect: pools started together expire their initial connections together (same IdleTimeout, timestamps from construction) and recreate them on the same Get wave | observed-in-code channel.go:88 ("c.conns <- &idleConn{conn: conn, t: time.Now()}") | Q-21 |
| L-9 | lifecycle disagreement (PA-21) | `openingConns` and `connReqs` are shared by the caller lifecycle (checked-out connections, blocked Gets) and the pool lifecycle (Release). Release (pool terminal) triggers no cleanup in the caller tracks: waiters stay blocked, checked-out connections are never closed. Close (caller track) triggers no wake-up in the waiter track | observed-in-code channel.go:211, 225-232 | Q-01, Q-04, Q-06 |
| L-10 | dual ownership cleanup (PA-23) | a connection has two caller release paths (Put, Close) plus Get's internal discard; no record makes them exclusive: Put+Close, Close+Close, Put+Put all apply twice | observed-in-code channel.go:183, 190, 211 | Q-10, Q-11 |
| L-11 | async cancellation isolation (PA-24) | the request channel handed to a waiter is the only link between Put (sender) and Get (receiver). The sender side's terminal event (Release) sends nothing to the receiver side; the receiver cannot cancel at all | observed-in-code channel.go:134-137, channel.go:225-232 | Q-01, Q-02 |
| L-12 | user-model gap | dispositions reachable only under concurrency: `Open_Waiting_Stranded` (Close or Put racing a Get), `Released × UV-GET-STALE` (Get racing Release), `Released × E-GET` for a Get that was already waiting. A single-threaded reading of the API never sees them; traces P-01 … P-05 are their documentation | adversarial-traces.md | Q-04, Q-05, Q-07 |

**Multi-instance assumption.** NAT-SYS-1 applies: the pool's factory connects to a shared remote resource. The pool has no backoff, jitter or retry; the multi-instance probes M-01 … M-03 model the aggregate.
