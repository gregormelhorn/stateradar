| event id | disposition | requirement-terms description |
|---|---|---|
| get | `handle` (may `transition → Error_Closed`-equivalent refusal via `ErrClosed`) | In `Open_IdleAvailable`, returns an idle connection after age/Ping validation. In `Open_MaxActive` with waiters allowed, `defer (queued)` as a waiter until `handoff`; in `Open_MaxActive` without wait capacity it yields `ErrMaxActiveConnReached` (`reject`). In `Open_BelowMaxActive`, invokes Factory; on success `handle`, on `factory_error` propagates the error (`reject`). After `release`, `reject` with `ErrClosed`. |
| put | `handle` | In `Open_WaiterWaiting`, `transition → Open_Handoff` delivering to oldest waiter (timestamp reset). In `Open_IdleNotFull`, stores connection idle (`handle`). In `Open_IdleFull`, closes connection via close callback and discards (`handle`, documented behaviour). After `release` (state `Released`), `ignore (documented)` — returns without keeping or closing (remembrance semantics). `Put(nil)` is `reject` (UV-06). |
| close_conn | `handle` | In `Open_*`, invokes the close callback and discards the connection (pool keeps no identity, so accepted). After `release`, `ignore (documented)` — returns nil without calling a close callback. `Close(nil)` is `reject` (UV-09). |
| ping | `handle` (stateless pass-through) / `reject` on nil | In `Open_*`, forwards to the ping callback without the mutex. In `Released`, callback is nil → panic is the literal outcome; per requirement terms this is `reject` (a declared refusal — nil callback not a documented contract) — flagged open point: requirements do not name Ping-after-Release, so this cell is `UNSPECIFIED` on the desired side, with observed Panic noted. `Ping(nil)` → `reject` (UV-11). |
| release | `transition → Released` / `ignore (documented)` on repeat | In `Open_*`, drains idle connections (close callback), clears conns/factory/ping/close → `Released`. Second call in `Released` → `ignore (documented)` (returns immediately, UV-10). Waiters in `connReqs` are not removed — `assumed-state: Released_WithOrphanWaiters` (condition: Release observed while connReqs non-empty); waiters remain blocked. |
| len | `handle` (read-only snapshot) | In `Open_*` returns count of idle connections (including expired ones not yet reaped). In `Released` returns 0 (`handle` — declared constant). |
| idle_expired | `handle` (discard) | Only when `Get` takes an idle connection whose stored timestamp + IdleTimeout < now (and IdleTimeout > 0): connection is closed via close callback and Get loops. Disabled when IdleTimeout <= 0 → never fires. Expiry is lazy: an expired connection remains idle and counted in `Len` until taken. |
| ping_failed | `handle` (discard) | Only on the idle path when a Ping callback is configured; the taken connection is discarded (close callback) and Get loops to retry. Not evaluated on the handoff path. Error value is not inspected. |
| factory_error | `handle` (propagate as refusal) | Returned to the `Get` caller unchanged; `openingConns` is not incremented. Factory runs under the mutex — reentrant pool calls deadlock (documented hazard). In `assumed-state: Open_BelowMaxActive` only. |
| handoff | `handle` (internal delivery) | When `Put` observes `connReqs` non-empty: removes `connReqs[0]`, sends connection with reset timestamp on the capacity-1 channel, delivers to waiting `Get`. FIFO. Cannot be lost (no cancellation; buffered send under mutex). Nothing closes waiter channels. |
| UV-01 | `UNSPECIFIED` (no cancellation) | A waiting `Get` beyond caller tolerance has no declared timeout/cancellation parameter; the caller cannot abandon the wait. Desired per requirements (silent): waiting supported, but no bound. Flagged as open point — requirements name "support connection waiting" but define no per-Get deadline. |
| UV-02 | `ignore (accidental)` / resource leak | A checked-out connection never returned is only remembered as a count in `openingConns`; the pool cannot detect the absence. On `Release`, such connections are never closed by the pool. Desired: not addressed by requirements (documented open point). |
| UV-03 | `handle` (accepted, no dedup) | Second `Put` of an already-idle connection is accepted: stored as a second idle entry (or handed off), pool keeps no identity → duplicate reference. Desired: requirements are silent (open point) — should ideally be `reject`, currently `UNSPECIFIED`. |
| UV-04 | `ignore (accidental)` | `Put(c)` and `Close(c)` near-simultaneously: both proceed; whichever runs last determines outcome; the pool does not detect the contradiction. Desired per requirements: undefined (open point). |
| UV-05 | `handle` (accepted, no provenance check) | Foreign connection accepted as idle, bounded only by MaxIdle. Desired: requirements silent (open point). |
| UV-06 | `reject` (nil check) | `Put(nil)` rejected at the documented nil gate. |
| UV-07 | `handle` (accepted) | Second `Close` of the same connection invokes the close callback again; no identity tracking to refuse. Desired: silent (open point). |
| UV-08 | `handle` (accepted) | `Close` of a connection the pool did not hand out, or of a currently-idle connection, is accepted — the close callback is invoked and the connection is not removed from the idle set. Desired: silent (open point); double-close/eviction hazard. |
| UV-09 | `reject` (nil check) | `Close(nil)` rejected at the documented nil gate. |
| UV-10 | `ignore (documented)` | Second `Release` (sequential or concurrent) returns immediately because `conns` is nil. `Released`. |
| UV-11 | `reject` (nil check) | `Ping(nil)` rejected at the documented nil gate; the callback is not called. |
| UV-12 | `UNSPECIFIED` / `defer (queued)`-side-effect | A blocking Factory holds the mutex, so every other `Get`/`Put`/`Close`/`Len`/`Release` blocks → whole pool stalls. No timeout exists. Desired: requirements are silent on callback latency (open point); the effect is `defer (queued)` for concurrent callers (they block at the mutex, unbounded). |
| P-01a | `UNSPECIFIED` (`transition → Released` mid-Get, waiter orphaned by second call) | `Get` in progress (waiting or inside the factory) then `Release`: if waiting, the waiter remains in `connReqs` after Release and blocks forever (`assumed-state: Released_WithOrphanWaiters`); if inside the factory under the mutex, Release blocks until the factory returns, then `openingConns` remains at its last value and the created connection is leaked (never closed). Requirements name neither outcome; both are open points. |
| P-01b | `reject` | `Release` then `Get`: `transition → Released` already applied; the `Get` refuses with `ErrClosed` (`reject`). Clear, documented. |
| P-02a | `handle` | `Put` then `Release`: the `Put` is served normally (idle store or handoff), then Release drains/closes whatever is idle. Consistent, documented behaviour. |
| P-02b | `ignore (documented)` | `Release` then `Put` of a connection checked out before Release: Put returns silently, leaving the connection neither kept nor closed → leak. Documented remembrance semantics (open point on resource recovery). |
| P-03a | `handle` | `Close` then `Release`: close callback runs on the user's connection; Release then drains remaining idle ones. Consistent. |
| P-03b | `ignore (documented)` | `Release` then `Close` of a pre-Release checked-out connection: returns nil without calling the close callback → leak. Documented. |
| P-04a | `handle` (no lock) | `Ping` then `Release`: ping callback (user's own function object) runs on the checked-out connection; Release clears the pool's reference. No interference — Ping holds no lock. Consistent. |
| P-04b | `reject` (panic) / `UNSPECIFIED` | `Release` then `Ping`: the pool's ping field is nil, so the call panics. Desired per requirements: undefined — flagged open point (a nil-callback guard is the natural requirement). |
| P-05a | `handle` | `Len` then `Release`: Len returns the idle-set snapshot before Release drains. Consistent. |
| P-05b | `handle` | `Release` then `Len`: returns 0 (declared constant for `Released`). Consistent. |

Coverage checklist:

- [x] get
- [x] put
- [x] close_conn
- [x] ping
- [x] release
- [x] len
- [x] idle_expired
- [x] ping_failed
- [x] factory_error
- [x] handoff
- [x] UV-01
- [x] UV-02
- [x] UV-03
- [x] UV-04
- [x] UV-05
- [x] UV-06
- [x] UV-07
- [x] UV-08
- [x] UV-09
- [x] UV-10
- [x] UV-11
- [x] UV-12
- [x] P-01a
- [x] P-01b
- [x] P-02a
- [x] P-02b
- [x] P-03a
- [x] P-03b
- [x] P-04a
- [x] P-04b
- [x] P-05a
- [x] P-05b