BLIND PASS (Part B) — channelPool. Inputs were complete (real catalogue, requirements and contract text; no placeholders), so I carried out the dispatch. I read no files and used no tools.

States (PA-17). No lifecycle state names exist in the public API except the one implied by `ErrClosed` ("pool is closed"). All the others are assumed:
- `assumed-state: Open_IdleAvailable`: the pool has not been released and at least one idle connection is held.
- `assumed-state: Open_NoIdle_BelowMaxCap`: not released, no idle connection, live count < MaxCap.
- `assumed-state: Open_NoIdle_AtMaxCap`: not released, no idle connection, live count = MaxCap, no waiting Get.
- `assumed-state: Open_AtMaxCap_Waiting`: as above, plus at least one waiting Get.
- `assumed-state: Open_IdleFull`: not released, idle count = MaxIdle. This is a sub-condition of Open_IdleAvailable.
- `Closed`: after Release(). The name comes from the public error `ErrClosed`.

## Disposition table

| Id | Situation (requirement terms) | Disposition | What should happen / open point |
|---|---|---|---|
| GET | Open_IdleAvailable, connection not expired, Ping passes or is not configured | handle | Hand out an idle connection (DOC-15). |
| GET | Open_IdleAvailable, dequeued connection idle longer than IdleTimeout (IdleTimeout > 0) | handle | Close and discard it (DOC-2, DOC-11). The live count drops by 1 (inferred from DOC-8). Then try the next idle connection, or create one. What happens to a Close-callback error on this path is UNSPECIFIED. |
| GET | Open_IdleAvailable, Ping configured and it reports the connection invalid | handle | Discard the connection (DOC-3) and continue as above. Live count −1 (inferred). |
| GET | Open_NoIdle_BelowMaxCap | handle | Call Factory, live count +1, return the connection (inferred). |
| GET | Open_NoIdle_AtMaxCap / Open_AtMaxCap_Waiting | defer (queued) → Open_AtMaxCap_Waiting | Wait for a connection, "like the go db connection pool" (DOC-4). Three points are UNSPECIFIED: (a) when, if ever, `ErrMaxActiveConnReached` (DOC-12, "pool limit exceeded") is returned instead of waiting, which contradicts DOC-4; (b) whether waiting is bounded or has a timeout; (c) whether waiters are served FIFO. |
| GET | Closed | reject | Return `ErrClosed` (DOC-13). |
| GET | MaxCap = 0 accepted at construction | UNSPECIFIED | No requirement covers it. Per DOC-8 a pool with a maximum of 0 live connections can never serve. Proposal: refuse at construction. |
| PUT | Open, a waiting Get exists | handle | Hand the connection straight to the waiting Get (DOC-4, by analogy with go db). If it was the last waiter, → Open_NoIdle_AtMaxCap. Live count unchanged. |
| PUT | Open, no waiter, idle store not full | handle → Open_IdleAvailable | Store the connection as idle (DOC-5, DOC-16) and record its idle start for DOC-2. |
| PUT | Open_IdleFull, no waiter | handle | Inferred from DOC-9 (MaxIdle is a maximum): close the surplus connection through the Close callback and drop the live count by 1. Whether the callback's error is returned to the caller is UNSPECIFIED. |
| PUT | Closed | UNSPECIFIED | Proposal: close the connection (DOC-6 intent) and return `ErrClosed`. The catalogue says the Close callback is cleared at Release, so the requirements do not say what a post-release Put does. |
| CLOSE | Open, a checked-out connection | handle | Close the single connection (DOC-14) through the Close callback, live count −1, return the callback's error (inferred). Capacity is freed for waiters (see P-04b). |
| CLOSE | Closed | UNSPECIFIED | Proposal: close the connection through the callback anyway, or reject with `ErrClosed`. The catalogue says the callback reference has been cleared. |
| RELEASE | Open (any sub-state) | transition → Closed | Close every idle connection (DOC-6). Three points are UNSPECIFIED: (a) whether "all connections" includes checked-out ones; (b) whether waiting Gets are woken (proposal: with `ErrClosed`) or left blocked forever; (c) whether the live count is reset. |
| RELEASE | Closed | UNSPECIFIED | Proposal: ignore (idempotent no-op). No connection may be closed twice. |
| LEN | Open | handle | Return "the number of connections in the current pool" (DOC-7). UNSPECIFIED: idle count versus live count. The contract text "连接池中已有的连接" (the connections the pool already has) fits either. |
| LEN | Closed | handle | Proposal: return 0. All connections were released. Checked-out connections make this ambiguous. |
| PING | Open, Ping configured, non-nil connection | handle | Run the configured Ping and return its result ("check whether a single connection is valid"). |
| PING | Ping not configured | UNSPECIFIED | Proposal: return nil or a declared error. It must not panic. |
| PING | Closed | UNSPECIFIED | Proposal: reject with `ErrClosed`, or run the user Ping. It must not panic, although the catalogue says the reference is cleared. |
| FACTORY_OK | Inside a creating Get, Open | handle | Return the connection to the Get caller, live count +1, the connection is checked out (inferred). |
| FACTORY_OK | Release happened while Factory ran | see P-06b | — |
| CLOSEFN_OK | Inside Close, Put-when-full, Get discard, or Release | handle | The connection has ended and the live count drops by 1. Close and Put-when-full return nil to the caller (inferred). |
| IDLE_TIMEOUT | Open, connection idle, IdleTimeout > 0 | handle | The connection "will be closed and discarded" (DOC-2) and is "invalid" (DOC-11). It must never be handed out. Live count −1. UNSPECIFIED: proactive closing at expiry versus lazy checking at the next Get. The requirement is satisfied either way, but lazy checking keeps expired connections open and holding resources. Also UNSPECIFIED: whether to replenish when the pool falls below InitialCap, because DOC-10 calls it a "minimum" and that contradicts "initial". |
| IDLE_TIMEOUT | IdleTimeout ≤ 0 | UNSPECIFIED | Proposal: ignore (documented). Timeout disabled. |
| IDLE_TIMEOUT | Closed | ignore (documented) | The idle connections were already closed by Release (DOC-6). |
| UV-01 | PUT_LOST, any Open state | UNSPECIFIED | The pool cannot detect it. Capacity leaks permanently, and once leaks reach MaxCap every Get waits forever (DOC-4 offers no bound). The requirements specify no leak detection or reclamation. This is a question for the owner. |
| UV-02 | PUT_DELAYED, Open_AtMaxCap_Waiting | defer (queued) for the Gets, then handle | Waiting Gets stay queued. The late Put serves a waiter as in the PUT row. Starvation bound and fairness are UNSPECIFIED. |
| UV-03 | PUT_DUP, Open | UNSPECIFIED | Proposal: reject (declared error). Risk: the same connection is stored twice and handed to two callers, and the idle count no longer reflects live connections. No requirement covers identity. |
| UV-04 | CLOSE_DUP, Open | UNSPECIFIED | Proposal: reject or ignore the second Close. Risk: the live count is decremented twice, so the pool exceeds MaxCap (violates DOC-8), and the Close callback runs twice on one connection. |
| UV-05 | CLOSE_STALE, Open | UNSPECIFIED | Proposal: reject. Risk: an idle connection, or one now owned by another caller, is closed under that caller, and the count becomes inconsistent. |
| UV-06 | PUT_CLOSE_RACE, Open | UNSPECIFIED | It must be concurrency-safe with exactly one outcome: stored, or closed with count −1, never both. Proposal: the first to act wins and the other is rejected. |
| UV-07 | PUT_FOREIGN, Open | UNSPECIFIED | Proposal: reject. Risk: the idle count exceeds the live count and a foreign connection is handed out. |
| UV-08 | CLOSE_FOREIGN, Open | UNSPECIFIED | Proposal: reject. Risk: the live count drops for a connection the pool never counted, so the pool exceeds MaxCap. |
| UV-09 | NIL_CONN on Put, Close or Ping | UNSPECIFIED | Proposal: reject with a declared "nil connection" error. A nil must never be stored or handed out. |
| UV-10 | PUT_BROKEN, Open | handle | Store the connection like any Put. DOC-3 places detection at Get time: with Ping configured it is discarded at the next Get (live count −1). Without Ping it is handed out (DOC-3 does not cover this case). Whether Put should validate is UNSPECIFIED. |
| UV-11 | FACTORY_ERR in a creating Get | reject | Get returns the Factory error to its caller and the live count stays unchanged (inferred). No retry is specified. Whether a waiting Get is woken by the freed slot is UNSPECIFIED. |
| UV-12 | FACTORY_HANG | UNSPECIFIED | The creating Get blocks, since no deadline exists. Whether other pool operations (Put, Close, Len, Release) are blocked meanwhile is UNSPECIFIED. Proposal: only the creating caller blocks. |
| UV-13 | FACTORY_CONN_AND_ERR | UNSPECIFIED | Proposal: treat it as an error (Go convention), close the returned connection to avoid a leak, return the error, and leave the count unchanged. |
| UV-14 | FACTORY_NIL_CONN | UNSPECIFIED | Proposal: reject with a declared error. Do not hand out nil and do not count it as live. |
| UV-15 | CLOSEFN_ERR | UNSPECIFIED | Proposal: on Close and Put-when-full, return the error to the caller. On Get discard and Release, swallow or log it. Whether the connection counts as ended (count −1) despite the error is UNSPECIFIED. Proposal: yes. |
| UV-16 | CLOSEFN_HANG | UNSPECIFIED | The calling operation blocks. Whether the whole pool blocks is UNSPECIFIED. Proposal: only the caller blocks. |
| UV-17 | FACTORY_REENTRY | UNSPECIFIED | No requirement or contract states a reentrancy rule. Proposal: either document it as forbidden or make it safe. It must not deadlock silently. |
| UV-18 | CLOSEFN_REENTRY | UNSPECIFIED | Same as UV-17, for the Close callback, on all four call paths. |

## Pair orderings

| Id | Ordering | Disposition | What should happen / open point |
|---|---|---|---|
| P-01a | Get registers as waiting, then Put | handle | Put hands the connection to the waiting Get (DOC-4). The Get returns it. Nothing is stored idle. Cited text contemplates this ordering: yes (DOC-4, waiting when full). |
| P-01b | Put runs after Get saw no idle connection but before it registered as waiting | UNSPECIFIED | Proposal: the Get must still obtain that connection; no wake-up may be lost. Failure mode: the Get waits forever while an idle connection sits in the store. Cited text contemplates this ordering: no. |
| P-02a | Get completes, then Release | transition → Closed | Release closes the idle connections (DOC-6). The handed-out connection stays with its caller, and its later Put or Close falls under the Closed row (UNSPECIFIED there). |
| P-02b | Release starts while a Get is in progress (Get already saw the pool open) | UNSPECIFIED | Proposal: the Get returns either `ErrClosed` or a valid connection, never one Release has already closed, and never panics. Cited text contemplates this ordering: no. |
| P-03a | Put, then Release | handle, then transition → Closed | The connection becomes idle, then Release closes it (DOC-6). It is closed exactly once. |
| P-03b | Release, then Put | UNSPECIFIED | Same as the PUT/Closed row. Proposal: close the connection and return `ErrClosed`. |
| P-04a | Close, then Get at the former MaxCap | handle | Close frees a slot. The Get creates a new connection through Factory (DOC-8). |
| P-04b | Get registers as waiting, then Close | UNSPECIFIED | Proposal (go db analogy, DOC-4): the freed capacity wakes the waiter, which creates a new connection. Failure mode: the waiter blocks forever although capacity exists. Cited text contemplates this ordering: no. DOC-4 talks only about waiting, not about which events end it. |
| P-05a | Put(conn), then Close(conn) | UNSPECIFIED | Same as UV-05. Proposal: reject the Close. |
| P-05b | Close(conn), then Put(conn) | UNSPECIFIED | Proposal: reject the Put. Risk: a closed connection is stored and handed out, and the count no longer matches the stored connections. |
| P-06a | Factory returns, then Release | transition → Closed | The new connection is checked out by its caller. Release closes only the idle connections. The caller's later Put falls under the Closed row. |
| P-06b | Release is called while Factory runs | UNSPECIFIED | Proposal: when Factory returns after Closed, the Get returns `ErrClosed` and closes the new connection; it is neither handed out nor leaked. Whether Release has to wait for Factory is UNSPECIFIED. |
| P-07a | The idle time passes, then a Get dequeues the connection | handle | Close and discard it (DOC-2), live count −1, continue with the next idle connection or create one. Cited text contemplates this ordering: yes. |
| P-07b | A Get dequeues the connection just before the idle time passes | handle | The connection is still valid and is handed out. Equality is not expired, because DOC-11 says "超过" (exceeding), which reads as strict. Proposal: the owner confirms the boundary. |
| P-08a | Release clears the Ping reference before the Get reads it | UNSPECIFIED | Proposal: the Get returns `ErrClosed`, or a connection validated by the configured Ping. It must never panic on a missing Ping. Cited text contemplates this ordering: no. |
| P-08b | The Get reads the Ping reference, Release clears it, then the Get calls Ping | UNSPECIFIED | Proposal: Ping runs on the reference already read. The Get then returns `ErrClosed`, or returns the connection, which the caller's later Put will close. It must never panic. |
| P-09a | Release by caller 1 first, then caller 2 | transition → Closed, then UNSPECIFIED | The first Release closes all idle connections. The second should be a no-op (proposal). Every connection is closed exactly once, never twice. |
| P-09b | Release by caller 2 first, then caller 1 | transition → Closed, then UNSPECIFIED | Symmetric to P-09a. |

## Open points to raise as questions (requirements are silent or contradictory)
1. DOC-4 (waiting) versus DOC-12 (`ErrMaxActiveConnReached`): when is each one used? Is waiting bounded?
2. DOC-10: is InitialCap only the starting count, or a minimum the pool maintains after discards?
3. DOC-7: does Len count idle connections or live connections?
4. Release and checked-out connections: are they included in "release all connections" (DOC-6)? Are waiting Gets woken?
5. What do Put, Close, Ping and Release do after Closed?
6. Connection identity: should duplicate, foreign, stale or nil connections be rejected? (UV-03 to UV-09)
7. Should freed capacity from Close or a discard wake waiters? (P-04b, UV-11)
8. Callbacks: are reentrancy and run-time limits documented as forbidden, or made safe? (UV-12, UV-16 to UV-18)
9. Factory result shapes (conn+err, nil+nil), and how Close-callback errors affect the live count.
10. Is expiry proactive or lazy (DOC-2)? Is the IdleTimeout boundary strict?

## Coverage checklist
- [x] GET
- [x] PUT
- [x] CLOSE
- [x] RELEASE
- [x] LEN
- [x] PING
- [x] FACTORY_OK
- [x] CLOSEFN_OK
- [x] IDLE_TIMEOUT
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
- [x] UV-13
- [x] UV-14
- [x] UV-15
- [x] UV-16
- [x] UV-17
- [x] UV-18
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

27 of 27 events and 18 of 18 pair orderings covered.
