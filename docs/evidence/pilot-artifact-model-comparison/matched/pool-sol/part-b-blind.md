| id | Situation | Disposition | Expected behaviour (requirements terms) |
|---|---|---|---|
| New | Valid config, pool not yet alive | transition → `Pool_Ready` | Create the pool with configured initial connections (DOC-8), factory callback (DOC-5); initial creations performed; pool becomes usable for Get. |
| New | Config invalid (nil/invalid bounds/zero capacity/absent callbacks/nonpositive timeout) | reject | Refuse construction with declared error (ErrMaxActiveConnReached domain / config error); no pool published. `assumed-state:` `Pool_Unusable` condition: construction rejected by validation. |
| New | Second New with independent instance / same config | handle | Each New yields an independent pool; existing pool unaffected. Not a duplicate-construction refusal since no single-instance mandate exists. |
| Get | Pool_Ready, idle resource available and valid | handle | Return an idle connection from pool (DOC-10). Age-check via IdleCheck; expired discarded and retried (DOC-2, DOC-9). Ping if configured; invalid discarded and retried (DOC-3). |
| Get | Pool_Ready, below max active, idle empty | handle | Create via Factory, return connection; count increments on success. |
| Get | Pool_Ready, at max concurrent, waiters allowed | defer (queued) | Enqueue waiter, return resource when Put/Close/handoff frees one (DOC-4). |
| Get | Pool_Ready, at max concurrent, no wait capacity | reject | Refuse with ErrMaxActiveConnReached (contract channel.go:13). |
| Get | after Release (UV-AfterRelease) | reject | Refuse with ErrClosed (contract pool.go:6). |
| Get | caller abandons result / no Put (UV-Abandon) | handle | No cancellation in API; waiter entry and checked-out resource unaffected by abandonment; resource remains outstanding; pool cannot recover it (documented limitation). |
| Get | second Get while first awaits or holds (UV-GetAgain) | handle | Both admitted independently per availability/count; no caller identity so treated as distinct requests. |
| Get | overlapping concurrent Gets (UV-Overlap) | handle | Admission by idle readiness/count/queue per each; concurrency-safe per lock discipline; no cross-refusal. |
| Get | unsolicited Get without app reason (UV-Unsolicited) | handle | Indistinguishable from Get; admitted under same gates. |
| Get | wrong receiver pool (UV-WrongPool) | handle | Per-receiver local state; serves from that pool's resources; no cross-pool lookup. |
| Put | Pool_Ready, empty interface nil | reject | Refuse nil connection; no pool change. |
| Put | Pool_Ready, waiter waiting | handle | Deliver connection directly to waiter; count unchanged (handoff). |
| Put | Pool_Ready, room in idle buffer | handle | Enqueue into idle buffer, timed on return (DOC-11, DOC-2). |
| Put | Pool_Ready, idle buffer full | handle | Dispose excess via close callback (overflow path), count decremented before outcome; close error reported/absorbed per contract. |
| Put | after Release (UV-LateResource) | reject | Refuse; pool no longer accepts returns; resource not tracked. |
| Put | duplicate Put of same resource (UV-DuplicateResource) | handle | No ownership stored; treated as fresh arrival → delivered/buffered again; documented limitation (remembrance semantics). |
| Put | foreign / mismatched / typed nil resource (UV-ForeignResource) | reject | Refuse typed nil under interface-nil gate; otherwise no identity so accepted as-is (documented limitation, no matching checkout stored). |
| Put | overlapping Put with Get/Close/Release (UV-Overlap) | handle | Delivery/buffering decided under lock; concurrency-safe. |
| Close | Pool_Ready, valid resource, close callback set | handle | Invoke close (DOC-6); count decremented before outcome; resource disposed. |
| Close | nil interface / close callback absent | reject | Refuse; no disposal, no count change. |
| Close | after Release (UV-LateResource) | handle | Still invokes captured close callback on captured fields; not tied to pool availability; documented limitation. |
| Close | duplicate Close / Close after Put for same resource (UV-DuplicateResource) | handle | No ownership; close invoked again on same value; double-disposal risk documented. |
| Close | foreign / typed nil (UV-ForeignResource) | reject (typed nil) / handle (opaque foreign) | Typed nil refused by interface-nil gate; foreign opaque value has no identity check, close invoked as-is. |
| Close | overlapping with other calls (UV-Overlap) | handle | Live Close under lock per discipline; concurrency-safe serialization. |
| Release | Pool_Ready/alive, first invocation | transition → `Pool_Released` | Detach and drain idle buffer; dispose each via captured close callback (DOC-12); subsequent calls refused. |
| Release | already released / during draining (UV-ReleaseAgain) | reject | Refuse; idle buffer already detached; no double drain. |
| Release | no prior New / never alive (UV-NoOwner) | reject | Refuse; nothing to release. |
| Release | late relative to work in flight (UV-OwnerLate) | handle | Drains idle only; outstanding checkouts unaffected; close-callback drain occurs; documented limitation (waiters untouched). |
| Release | overlapping construct/drain of another pool or overlapping calls (UV-OwnerOverlap) | handle | Per-receiver state; each release affects only its own receiver; concurrency-safe via detach-under-lock. |
| Release | wrong receiver (UV-WrongPool) | handle | Per-receiver local state; only that pool released. |
| Len | Pool_Ready | handle | Return idle buffer depth (DOC-13). |
| Len | after Release | handle | Return 0 / post-detach depth; observer-only, no state change. |
| Len | repeated / overlapping / late observation (UV-Observer) | handle | Snapshot under lock; concurrent observers each get snapshot; no mutation. |
| Len | wrong receiver (UV-WrongPool) | handle | Returns that receiver's depth only. |
| Factory | success, acquisition phase | handle | Connection delivered to requester; count increments. |
| Factory | error, including value+error (UV-FactoryError) | reject | Error propagated to requester as refusal; value discarded; count unchanged. |
| Factory | success but nil/typed nil/reused/foreign value (UV-FactoryValue) | reject | Nil/typed nil refused; value not admitted; count unchanged or rolled back. Reused/foreign not detectable (no identity); accepted—documented limitation. |
| Factory | slow/blocked/reentrant during acquisition (UV-FactoryDelay) | handle | Synchronous call; blocks caller; reentrancy permitted by callback contract; no deadlock adjudication beyond docs. |
| Factory | during construction (pre-publication) | handle | Runs outside lock before pool published; result becomes initial connection. |
| PingResult | healthy | handle | Connection deemed valid, returned to requester (DOC-3, DOC-7). |
| PingResult | error (UV-PingError) | handle | Connection discarded via close; retry acquisition (DOC-3 "invalid connection will be discarded"). |
| PingResult | slow/blocked/reentrant/overlapping release (UV-PingDelay) | handle | Synchronous call outside lock; release drains idle but does not cancel in-flight ping; result still applied per captured fields—documented limitation. |
| PingResult | verdict contradicts reality (UV-PingValue) | reject (when invalid reported healthy) | Pool trusts callback verdict; misuse is caller contract violation; no independent validation available. |
| CloseResult | success | handle | Resource considered disposed; count already decremented. |
| CloseResult | error (UV-CloseError) | handle | Error absorbed on overflow/expiry/release-drain paths; resource not restored; count already decremented (documented). |
| CloseResult | slow/blocked/reentrant in live or drain phase (UV-CloseDelay) | handle | Synchronous; live Close under lock, Release drain outside lock with captured callback; no cancellation. |
| CloseResult | success with live resource / error after disposal (UV-CloseValue) | handle | Callback side effect trusted; pool already committed count decrement; documented limitation. |
| IdleCheck | age below timeout | handle | Connection eligible for handoff (DOC-2, DOC-9). |
| IdleCheck | age equal to timeout | handle | Treated as threshold boundary — eligible or expired per configured comparison; boundary outcome must be consistent (UNSPECIFIED which side; requirement says "exceeding").  |
| IdleCheck | age beyond timeout (UV-Aged) | handle | Close and discard connection; retry acquisition (DOC-2, DOC-9). |
| IdleCheck | handoff delivery delayed by scheduling (UV-Aged) | handle | Age sampled at acquisition; delayed delivery may show expired resource → discard path; documented limitation. |
| UV-NoOwner | absence of New before use, or absence of Release | reject (operations on unowned pool) | Calls requiring an owned pool refused (ErrClosed-like); no implicit construction. |
| UV-OwnerLate | teardown delayed while caller work continues | handle | Outstanding checkouts continue; release drains idle only (documented limitation). |
| UV-NewAgain | repeated/unsolicited construction same config | handle | Independent instances permitted; no single-instance enforcement. |
| UV-OwnerOverlap | teardown overlaps another construction / old work runs | handle | Per-receiver isolation; new pool unaffected by other's drain. |
| UV-Config | nil/invalid/zero/absent/nonpositive | reject | Construction refused (as New invalid-config row). |
| UV-Config | valid but unintended limits | handle | Accepted as configured; pool obeys supplied bounds. |
| UV-Abandon | Get result never Put / Put/Close omitted or delayed | handle | No context/deadline; resource stays outstanding; count not restored by abandonment (documented limitation). |
| UV-GetAgain | second Get while first awaits or holds | handle | Independent admission per gates (as Get row). |
| UV-AfterRelease | Get on released pool | reject | ErrClosed. |
| UV-Overlap | overlapping Get/Put/Close/Release | handle | Per lock discipline; concurrency-safe. |
| UV-Unsolicited | unsolicited Get | handle | Same as Get admission. |
| UV-WrongPool | call on unintended receiver | handle | Per-receiver local state; no cross-pool effect. |
| UV-DuplicateResource | duplicate Put/Close or both | handle | No identity; treated as fresh operations; double-disposal risk documented. |
| UV-LateResource | Put/Close after release or before ownership completes | reject (after release) / handle (in-flight) | Post-release refused; in-flight returns accepted per current availability. |
| UV-ForeignResource | no matching checkout / foreign / typed nil / stale | reject (typed nil) / handle (opaque) | Typed nil refused; opaque values accepted without identity check (documented limitation). |
| UV-ReleaseAgain | second Release after detach or during drain | reject | Refused; no double drain. |
| UV-Observer | late/repeated/unsolicited/overlapping Len | handle | Snapshot under lock; no mutation. |
| UV-FactoryError | creation error incl. value+error | reject | Propagated; value discarded; count unchanged. |
| UV-FactoryDelay | slow/blocked/panicking/reentrant creation | handle | Synchronous; blocks caller; no timeout; documentation silent (UNSPECIFIED on panic recovery). |
| UV-FactoryValue | nil/typed nil/reused/foreign with success | reject (nil/typed nil) / handle (reused/foreign) | Nil refused; reuse/foreign undetectable. |
| UV-PingError | ping returns error | handle | Discard invalid connection; retry (DOC-3). |
| UV-PingDelay | slow/blocked/panicking/reentrant/overlapping release | handle | Synchronous; release does not cancel in-flight ping. |
| UV-PingValue | healthy reported invalid / invalid reported healthy | handle | Trust callback verdict; misuse is caller contract. |
| UV-CloseError | error in direct/overflow/expiry/invalid cleanup/release drain | handle | Absorbed; count already decremented; not restored. |
| UV-CloseDelay | slow/blocked/panicking/reentrant in live/drain | handle | Synchronous; live under lock, drain outside lock. |
| UV-CloseValue | success with live resource / error after disposing | handle | Callback trusted; pool committed. |
| UV-Aged | below/equal/beyond timeout incl. delayed handoff | handle | Below eligible; equal boundary (UNSPECIFIED per requirement wording "exceeding"); beyond discarded; delayed handoff may sample expired → discard. |
| P-01a | Get → Put, same pool | handle | Get admits, Put returns to idle / hands to waiter (P-01a/P-01b symmetric; both admitted). |
| P-01b | Put → Get | handle | Put buffers/delivers, Get serves from buffer or creates. |
| P-02a | Get → Close | handle | Get admits; Close disposes given resource independent of checkout tracking. |
| P-02b | Close → Get | handle | Close disposes; Get proceeds from remaining idle/count. |
| P-03a | Get → Release | handle | Get admits; Release drains idle only; outstanding checkout unaffected (documented limitation). |
| P-03b | Release → Get | reject | Get refused with ErrClosed. |
| P-04a | Put → Release | handle | Put buffers; Release drains and disposes buffered items. |
| P-04b | Release → Put | reject | Put refused post-release; resource remains untracked. |
| P-05a | Close → Release | handle | Close disposes; Release drains remaining idle. |
| P-05b | Release → Close | handle | Release drains idle; subsequent Close still invokes captured callback (documented limitation). |
| P-06a | Len → Release | handle | Len snapshot; Release drains; no interaction requirement. |
| P-06b | Release → Len | handle | Len returns post-detach depth (0). |
| P-07a | Len → Get | handle | Len snapshot; Get admitted per availability. |
| P-07b | Get → Len | handle | Get admits; Len reflects resulting idle depth. |
| P-08a | Len → Put | handle | Len snapshot; Put buffers/hands off. |
| P-08b | Put → Len | handle | Put buffers; Len reflects new depth. |
| P-09a | Len → Close | handle | Len snapshot; Close disposes independent resource. |
| P-09b | Close → Len | handle | Close disposes; Len reflects idle depth (unchanged by direct Close since CheckedOut not in idle). |
| P-10a | Put → Close, independently acting holders/cleanup agents | handle | Both invoked; no ownership → second sees no conflict; double-disposal risk documented. |
| P-10b | Close → Put | handle | Both invoked; Put may re-buffer already-closed resource (documented limitation). |

- [x] New
- [x] Get
- [x] Put
- [x] Close
- [x] Release
- [x] Len
- [x] Factory
- [x] PingResult
- [x] CloseResult
- [x] IdleCheck
- [x] UV-NoOwner
- [x] UV-OwnerLate
- [x] UV-NewAgain
- [x] UV-OwnerOverlap
- [x] UV-Config
- [x] UV-Abandon
- [x] UV-GetAgain
- [x] UV-AfterRelease
- [x] UV-Overlap
- [x] UV-Unsolicited
- [x] UV-WrongPool
- [x] UV-DuplicateResource
- [x] UV-LateResource
- [x] UV-ForeignResource
- [x] UV-ReleaseAgain
- [x] UV-Observer
- [x] UV-FactoryError
- [x] UV-FactoryDelay
- [x] UV-FactoryValue
- [x] UV-PingError
- [x] UV-PingDelay
- [x] UV-PingValue
- [x] UV-CloseError
- [x] UV-CloseDelay
- [x] UV-CloseValue
- [x] UV-Aged
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
- [x] P-10a
- [x] P-10b
