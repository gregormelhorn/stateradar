| Event id | Disposition(s) by situation (requirement terms) | What should happen |
|---|---|---|
| E-GET | **Open_With_Idle** (Len>0, idle connection present): `handle` — take the idle connection. If `IdleTimeout>0` and its age ≥ IdleTimeout (I-IDLE-EXPIRE applies): `handle` — close/discard it ("timeout connection will be closed and discarded") and continue. If `Ping` configured and Ping succeeds: hand it out. If Ping fails: `handle` — discard invalid connection ("invalid connection will be discarded") and continue. **Open_No_Idle_Below_MaxCap**: `handle` — call Factory; on success return the connection and increment open count; increment only on success. **Open_Waiting** (`assumed-state: Open_CapacityReached` — idle empty and open count at MaxCap): `defer (queued)` — enqueue as a waiter (FIFO, unbounded, no expiry; documented "support for connection waiting"). **Released** (`assumed-state: Released` — after Release, idle channel nil): `reject` with ErrClosed ("pool is closed"). | Open: serve from idle/Factory/queue. Released: nil connection + ErrClosed error; no Factory call. |
| E-PUT | **Open + payload nil**: `handle` — nil/error return (nil check only; error signalled). **Open + non-nil + waiter present**: `handle` — hand connection directly to the first waiter (non-blocking); open count unchanged. **Open + non-nil + no waiter + idle below MaxIdle**: `handle` — enqueue into idle channel with timestamp = now. **Open + non-nil + no waiter + idle full (MaxIdle)**: `handle` — not idled; connection closed through Close callback (idle bound respected). **Released**: `ignore (documented)` — nil return, no close callback invoked (callbacks dropped). | Open: nil-check, then handoff→idle→close-if-full. Released: silent no-op nil return. |
| E-CLOSE | **Open + payload nil**: `handle` — nil/error return (nil check only). **Open + non-nil**: `handle` — decrement open count, invoke user Close callback (return its error to caller). No ownership/history check (documented absence). **Released**: `ignore (documented)` — nil return, no close function available. | Open: count decrement + Close callback. Released: silent nil no-op. |
| E-RELEASE | **Open**: `transition → Released` — drop idle channel and callbacks; close all idle connections via saved Close callback after unlocking; leave open count and waiter queue untouched (documented: no coordination with in-flight Gets or held connections). **Released** (`assumed-state: Released`): `ignore (documented)` — return at once. | First Release transitions to Released and drains idle. Second Release immediate no-op. |
| E-LEN | **Open**: `handle` — return current idle count (0..MaxIdle). **Released**: `handle` — return 0 (documented Released row). | Read-only; Open→idle count, Released→0. |
| I-IDLE-EXPIRE | **Open, idle connection received by Get and IdleTimeout>0 and age ≥ IdleTimeout**: `handle` — close it via Close callback and discard, Get continues to next idle/Factory path. **Open, age < IdleTimeout**: `ignore (accidental)` — not expired, connection handed out. **IdleTimeout ≤ 0**: `ignore (documented)` — check disabled. **Released**: `ignore (accidental)` — idle dropped; never evaluated. **Connection still idle, no Get**: `ignore (documented)` — no timer; removal lazy until Get receives it or Release drains it. | Lazy evaluation at receipt only; expired→close+discard. |
| UV-GET-DELAY | **Open_Waiting, no Put arrives**: `UNSPECIFIED` — no deadline/context accepted; block is unbounded (documented absence of wait bound/cancellation). **Open, Factory slow**: `UNSPECIFIED` — delay unbounded by pool; only Fault-Envelope of caller. **Released waiter**: `reject` (ErrClosed for new Gets; queued waiter itself is `UNSPECIFIED` — depends on Put, see P-01a). | No pool-imposed timeout; requirement is silent; label UNSPECIFIED. |
| UV-GET-STALE | **Open, Get began before Release, still holds idle channel**: `handle` — Get completes with the connection it already took; Release does not synchronise (documented absence of coordination). Released-state later use of returned conn goes through Released rows of E-PUT/E-CLOSE. | Stale Get runs to completion; not rejected. |
| UV-PUT-LOSS | **Open, conn never returned**: `ignore (documented)` — open count stays high; pool never reclaims; only MaxCap back-pressure results. **Released**: n/a (no Put arrives). | Pool has no reclamation; count remains until Close/Release. |
| UV-PUT-DUP | **Open, same conn Put twice, no Get between**: first Put `handle`; second Put `handle` (no duplicate check — documented absence) — same value idled twice / handed to a waiter, potentially double-counted in idle. **Released**: second is Released row. | Accepted; no identity tracking; documented unintended use. |
| UV-PUT-FOREIGN | **Open, non-nil foreign conn**: `handle` — accepted and idled/handed out (no ownership check). **Released**: `ignore (documented)`. | Accepted by count; ownership not verified. |
| UV-PUT-BROKEN | **Open, non-nil but dead conn**: `handle` — accepted; only detected later via Ping at next Get (discard) or caller's use. **Released**: ignore (documented). | Accepted; validation delegated to Ping on Get. |
| UV-PUT-CLOSE-SAME | **Open, Put then Close same conn** (see P-08a): Put `handle` idles/hands off; Close `handle` decrements count and calls Close callback on already-returned conn — double release risk (documented absence of duplicate check). **Close then Put** (P-08b): Close decrements; Put idles closed conn — future Ping/use failure. **Released**: Released rows. | Both accepted independently; contradiction not detected by pool. |
| UV-CLOSE-DUP | **Open, same conn Closed twice**: first `handle` decrement+callback; second `handle` decrement again + callback (no duplicate check). **Released**: `ignore (documented)`. | Accepted twice; count skewed; documented absence. |
| UV-CLOSE-FOREIGN | **Open, foreign conn**: `handle` — decrement + Close callback (no ownership check). **Released**: ignore (documented). | Accepted; ownership unverified. |
| UV-CLOSE-IDLE | **Open, conn currently idle inside pool, Closed**: `handle` — count decremented and Close callback invoked; the idle entry is not removed, so a later Get may hand out a closed connection (documented absence of identity tracking). **Released**: ignore (documented). | Accepted; idle entry remains stale until Get/Ping. |
| UV-FACTORY-ERR | **Open, Factory returns error**: `reject` — Get returns (nil, factory error); open count not incremented; waiter not entered. | Error propagated to caller; no count change. |
| UV-FACTORY-SLOW | **Open, Factory blocks**: `UNSPECIFIED` — Get blocks; no deadline. Mutex released before Factory (per lock annotation), so other Gets/Puts not blocked by this Factory. | UNSPECIFIED wait; caller-visible delay only. |
| UV-FACTORY-NILCONN | **Open, Factory returns (nil, nil)**: `UNSPECIFIED` — no documented nil-conn check at Factory; Get would return nil,nil (caller's responsibility). Requirement silent → label UNSPECIFIED (assumed: handle-as-returned). | UNSPECIFIED; requirement does not define. |
| UV-CLOSEFN-ERR | **Open, Close callback returns error**: `handle` — error returned to caller; count already decremented. **Released**: ignore (documented, callback dropped). | Error returned; decrement persists. |
| UV-CLOSEFN-SLOW | **Open, Close callback blocks**: `UNSPECIFIED` — caller caller-visible delay; mutex released before callback (per lock annotation) so pool not wedged. | UNSPECIFIED wait; callback duration unbounded. |
| UV-CB-REENTER | **Open, Factory or Close re-enters a pool method**: `UNSPECIFIED` / deadlock risk — Go mutex non-reentrant; README/doc silent on re-entry (documented absence of contract). Behaviour not specified by requirements. **Ping re-entering**: `handle` — Ping is called outside the mutex, so no deadlock; result is the Ping's own Get. | Reentrancy is UNSPECIFIED by requirement; Ping path tolerated (outside lock). |
| P-01a | Get blocks as waiter (CapacityReached), then Release. Get `defer (queued)`; Release `transition → Released` — waiter queue untouched; the queued Get has no Put to serve it and no cancellation: `UNSPECIFIED` (waiter stays queued indefinitely; documented absence of coordination). | Waiter persists; UNSPECIFIED resolution. |
| P-01b | Release first → `transition → Released`; then Get: `reject` ErrClosed. | Get rejected with ErrClosed. |
| P-02a | Get finds no idle at capacity and Put runs before Get queues itself: Put `handle` — idles the connection (MaxIdle not exceeded); then Get `handle` — takes the fresh idle connection. | Put idles; Get served from idle. |
| P-02b | Put enqueues idles first, then Get takes the idle connection: Put `handle` idle; Get `handle` takes idle. | Same net: connection transferred. (Distinction: no waiter existed so Put idled.) |
| P-03a | Get blocks as waiter, then Close runs: Get `defer (queued)`; Close `handle` — decrement+callback; waiter unaffected (Close does not feed waiters): `UNSPECIFIED` — waiter remains blocked. | Waiter stays; UNSPECIFIED. |
| P-03b | Close first (`handle` decrement+callback), then Get: if now below MaxCap `handle` via Factory; if still at capacity `defer (queued)`. | Get served by Factory or queued. |
| P-04a | Get has received idle conn and Ping is set, then Release: Get proceeds with Ping (outside mutex) and `handle` returns the conn; Release `transition → Released` drops idle channel; the Get already took its conn — accepted (no coordination, documented). | Get completes with conn; released state after. |
| P-04b | Release first (`transition → Released`, Ping/idle dropped), then Get: `reject` ErrClosed — no Ping called. | Get rejected with ErrClosed. |
| P-05a | Get inside Factory, then Release: Release `transition → Released` drops callbacks/idle; Factory returns conn; Get `handle` returns it (count incremented), but pool Released — returned conn will later face Released Put/Close (silent ignore). Documented absence of coordination. | Factory completes, conn delivered; Release had no effect on in-flight Get. |
| P-05b | Release first, then Get: `reject` ErrClosed — Factory never invoked (released check precedes Factory). | Get rejected; no Factory call. |
| P-06a | Put then Release: Put `handle` idles/hands off; Release `transition → Released` closes idle via callback; any idled conn returned by that Put gets closed (drained). | Put effect then drained by Release. |
| P-06b | Release then Put: Put on Released → `ignore (documented)` — nil return, no close callback; connection leaked (caller must Close elsewhere). | Put silently ignored; conn not closed by pool. |
| P-07a | Close then Release: Close `handle` decrement+callback; Release `transition → Released` drains remaining idle. | Close effect then Release drains. |
| P-07b | Release then Close: Close on Released → `ignore (documented)` — nil return, no callback; conn not closed by pool. | Close silently ignored. |
| P-08a | Put then Close on same conn: Put `handle` idle; Close `handle` decrement+callback on idled conn — double-release risk (see UV-PUT-CLOSE-SAME). | Both handled; conn double-accounted. |
| P-08b | Close then Put on same conn: Close `handle` decrement+callback; Put `handle` — idles already-closed conn (accepted, no check). | Put accepted; conn idle but dead; next Get/Ping discards. |
| P-09a | Idle conn expires, then Get receives it: I-IDLE-EXPIRE `handle` — close+discard via callback; Get continues to next idle / Factory / queue. | Expired conn discarded; Get retries. |
| P-09b | Get receives conn, then age would have passed IdleTimeout: I-IDLE-EXPIRE `ignore (accidental)` — age checked at receipt, still fresh; conn handed out. | Conn served; expiration not applied. |

Coverage checklist:

- [x] E-GET
- [x] E-PUT
- [x] E-CLOSE
- [x] E-RELEASE
- [x] E-LEN
- [x] I-IDLE-EXPIRE
- [x] UV-GET-DELAY
- [x] UV-GET-STALE
- [x] UV-PUT-LOSS
- [x] UV-PUT-DUP
- [x] UV-PUT-FOREIGN
- [x] UV-PUT-BROKEN
- [x] UV-PUT-CLOSE-SAME
- [x] UV-CLOSE-DUP
- [x] UV-CLOSE-FOREIGN
- [x] UV-CLOSE-IDLE
- [x] UV-FACTORY-ERR
- [x] UV-FACTORY-SLOW
- [x] UV-FACTORY-NILCONN
- [x] UV-CLOSEFN-ERR
- [x] UV-CLOSEFN-SLOW
- [x] UV-CB-REENTER
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
- [x] P-06a
- [x] P-06b
- [x] P-07a
- [x] P-07b
- [x] P-08a
- [x] P-08b
- [x] P-09a
- [x] P-09b