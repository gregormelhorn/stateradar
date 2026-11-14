| Id | Situation | Disposition | Expected behaviour (requirement terms) |
|---|---|---|---|
| Create | Valid Settings, no callbacks | `handle` | New independent instance; defaults per DOC-2, DOC-6, DOC-8, DOC-10, DOC-13/DOC-14, DOC-19 applied at construction; zeroed Counts. |
| Create | Settings with name/interval/timeout/classifier/trip/notify overrides | `handle` | Configured values stored; defaults substituted only where DOC says (0 MaxRequests→1, ≤0 Timeout→60s, nil ReadyToTrip→default, nil IsSuccessful→default). |
| Create | Duplicate / repeated construction | `handle` | Each construction yields a distinct breaker identity (DOC-2); no shared counters. |
| Create | Out-of-order construction (use before construct) | `reject` | Invalid; a distinct breaker must be constructed first (DOC-2). `as-is:` zero-value behaviour is UV-12. |
| Admit | Closed state, below failure threshold | `handle` | Admit request; Execute proceeds (DOC-24). |
| Admit | Open state, timeout not elapsed | `reject` | Return error instantly, ErrOpenState (DOC-25, contract gobreaker.go:25). No request work runs. |
| Admit | Open state, timeout elapsed (Expiry due) | `transition → HalfOpen_AtBudget` | Move to half-open; allow up to MaxRequests (DOC-5/DOC-9). |
| Admit | HalfOpen, admissions below MaxRequests | `handle` | Allow admission. |
| Admit | HalfOpen, admissions at MaxRequests | `reject` | Return ErrTooManyRequests (contract gobreaker.go:23). |
| Admit | MaxRequests 0 setting | `handle` | Treat as 1 per DOC-6. |
| Admit | nil / wrong instance or settings | `reject` | Value handled by UV-07/UV-13/UV-14 rows. |
| State | Any constructed instance | `handle` | Return current state (Closed/Open/HalfOpen), reflecting due expiry (DOC-9). |
| State | Due expiry while Open | `transition → HalfOpen_AtBudget` | Expiry evaluated; state reported as half-open; Notify invoked per DOC-15. |
| State | Called before any Create | `reject` | Invalid use; Create required first (DOC-2). |
| Counts | Closed, no interval elapsed | `handle` | Snapshot of five counters (DOC-20). |
| Counts | Closed, interval elapsed | `transition → Closed_FreshInterval` | Clear counts per DOC-7/DOC-21 before snapshot; prior results ignored (DOC-22). |
| Counts | Open / HalfOpen | `handle` | Return current snapshot; no clearing except on state change (DOC-21). |
| Counts | Called before Create | `reject` | Invalid use (DOC-2). |
| Name | Constructed with Name | `handle` | Return configured Name (DOC-4). |
| Name | Constructed with empty Name | `handle` | Return empty string (Name is whatever configured). |
| Name | Called before Create | `reject` | Invalid use (DOC-2). |
| Report | HalfOpen, report success | `handle` | Success counted (DOC-17). |
| Report | HalfOpen, report failure | `transition → Open` | Failure counts; DOC-21 clears counts on state change; Notify. |
| Report | Report with no state change | `handle` | Update counters only (DOC-16–18). |
| Report | Report after state change / clearing | `ignore (documented)` | "Counts ignores the results of the requests sent before clearing" (DOC-22). |
| Report | Repeated same callback (identical payload) | `ignore (documented)` | Only one outcome may be counted; duplicate ignored per DOC-22 reasoning. |
| Report | Contradictory repeat payload | `reject` | Declared refusal signal: caller error; first outcome stands. |
| Report | nil / wrong continuation | `reject` | Wrong continuation rejected (UV-06). |
| Return | Closed, error classifies as failure | `handle` | Failure counted; ReadyToTrip invoked (DOC-11, DOC-18). |
| Return | Closed, error classifies as success | `handle` | Success counted (DOC-17). |
| Return | Closed, nil error | `handle` | Success counted (default IsSuccessful). |
| Return | ReadyToTrip returns true | `transition → Open` | Breaker opened (DOC-12); Notify (DOC-15). |
| Return | HalfOpen, success under budget | `handle` | Success counted. |
| Return | HalfOpen, failure | `transition → Open` | Immediate open (requirement reading of DOC-16–18 + DOC-21). |
| Return | Stale (pre-clear) result | `ignore (documented)` | Ignored per DOC-22. |
| Return | Execute work abandoned / never returns | `UNSPECIFIED` | Requirements silent on loss; `as-is:` UV-02. |
| Panic | Panic in request | `handle` | Handled as an error (DOC-27) and same panic re-raised. |
| Panic | Panic with nil payload | `handle` | Same re-raise semantics (DOC-27). |
| Panic | Panic after stale admission | `ignore (documented)` | Outcome ignored per DOC-22; panic still re-raised. |
| Classify | IsSuccessful returns valid result | `handle` | True→success, else failure (DOC-16–18). |
| Classify | IsSuccessful nil | `handle` | Default: false for non-nil errors (DOC-19). |
| Classify | IsSuccessful panics / Goexits / blocks | `UNSPECIFIED` | Requirements do not define callback failure; open point. |
| Classify | IsSuccessful re-enters breaker | `UNSPECIFIED` | Reentry not specified (lock-discipline annotation). |
| Classify | Wrong-but-valid classification | `handle` | Breaker trusts configured classifier; outcome per its return. |
| TripPolicy | Closed, failure, ReadyToTrip returns false | `handle` | Stay closed; counters updated. |
| TripPolicy | Closed, failure, ReadyToTrip returns true | `transition → Open` | Open per DOC-12. |
| TripPolicy | ReadyToTrip nil | `handle` | Default: >5 consecutive failures trips (DOC-13/DOC-14). |
| TripPolicy | ReadyToTrip panics / blocks / re-enters | `UNSPECIFIED` | Not defined by requirements. |
| TripPolicy | Called in HalfOpen | `ignore (documented)` | DOC-11 scopes ReadyToTrip to closed-state failures. |
| Notify | State actually changed | `handle` | Invoke configured OnStateChange with state change (DOC-15). |
| Notify | No state change | `ignore (documented)` | DOC-15 says "whenever the state changes"; otherwise not called. |
| Notify | OnStateChange nil | `handle` | No-op (unconfigured). |
| Notify | OnStateChange panics / blocks / re-enters | `UNSPECIFIED` | Not defined; open point. |
| Notify | Duplicate / out-of-order observation | `UNSPECIFIED` | Delivery ordering not specified beyond per-change invocation. |
| Expiry | Open, now strictly before deadline | `ignore (documented)` | No transition yet (DOC-9). |
| Expiry | Open, now at/after deadline | `transition → HalfOpen_AtBudget` | Half-open (DOC-9). |
| Expiry | Closed with interval due | `transition → Closed_FreshInterval` | Clear counts at interval (DOC-7/DOC-21). |
| Expiry | Interval 0 | `ignore (documented)` | No closed-state clearing (DOC-8). |
| Expiry | HalfOpen | `ignore (documented)` | No expiry defined for half-open. |
| Expiry | Timeout ≤0 | `handle` | Use 60s (DOC-10). |
| Expiry | Clock sampled repeatedly / out-of-order | `handle` | Monotonic comparison; `as-is:` strict expiry-before-now. |
| UV-01 | Report omitted, caller abandons work | `UNSPECIFIED` | Requirements silent on missing report; `as-is:` admission slot retained until state change. |
| UV-02 | Slow/blocked/Goexit work, no admission issued | `UNSPECIFIED` | Not covered by requirements. |
| UV-03 | Concurrent Admit while budget exhausted | `reject` | ErrTooManyRequests in HalfOpen at budget; in Closed both admitted (DOC-5). |
| UV-03 | Concurrent Admit, overlapping continuations | `handle` | Each allowance distinct; budget enforced per DOC-5/DOC-6. |
| UV-04 | Repeated identical callback | `ignore (documented)` | Second outcome ignored (DOC-22). |
| UV-04 | Overlapping contradictory callbacks | `reject` | Declared refusal: caller contract violation, first outcome stands. |
| UV-05 | Old work returns after clear | `ignore (documented)` | Ignored per DOC-22 ("results of requests sent before clearing"). |
| UV-05 | Old work reports in new open interval | `ignore (documented)` | Ignored per DOC-22. |
| UV-06 | Wrong boolean / fabricated continuation | `reject` | Caller error; no counter effect. |
| UV-06 | nil callback after rejected admission | `ignore (documented)` | No continuation issued; nothing to call. |
| UV-07 | nil request / nil panic payload | `reject` | Invalid input; DOC-27 keeps panic re-raise for actual panics. |
| UV-08 | Omit/delay refreshing call; read Counts first | `handle` | Read methods themselves refresh on due expiry; results consistent per DOC-7/DOC-9. |
| UV-08 | Sample exactly at deadline | `transition → HalfOpen_AtBudget` | At/after deadline→half-open (DOC-9). |
| UV-09 | IsSuccessful returns wrong-but-valid | `handle` | Trusted per DOC-16–18. |
| UV-09 | IsSuccessful blocks/panics/Goexits/re-enters | `UNSPECIFIED` | Open point. |
| UV-10 | ReadyToTrip unintended but valid decision | `handle` | Trusted per DOC-12. |
| UV-10 | ReadyToTrip blocks/panics/Goexits/re-enters | `UNSPECIFIED` | Open point. |
| UV-11 | OnStateChange blocks/panics/misdelivers | `UNSPECIFIED` | Only "called whenever state changes" required (DOC-15). |
| UV-12 | zero-value/nil receiver, copied breaker | `reject` | Invalid use; DOC-2 requires NewCircuitBreaker. `as-is:` observable behaviour is UV-12. |
| UV-13 | Wrong valid instance / wrong-request payload | `reject` | Caller error; no cross-instance effect. |
| UV-14 | Missing/delayed/duplicate construction | `handle` | Each Create yields new breaker (DOC-2); defaults applied. |
| UV-14 | Valid-but-unintended Settings | `handle` | Settings honoured as given; defaults only where DOC directs. |
| P-01a | Admit then Report; HalfOpen at budget | `reject` | ErrTooManyRequests; existing report still processed. |
| P-01b | Report then Admit; HalfOpen at budget | `reject` | Report may free/transition; remaining admission rejected at budget. |
| P-02a | Admit then prior Return | `handle` | Prior outcome processed (or ignored if stale per DOC-22); admission independent. |
| P-02b | Prior Return then Admit | `handle` | Return updates counters/trip; subsequent admission reflects state (DOC-11/DOC-12). |
| P-03a | Admit then prior Panic | `handle` | Panic re-raised (DOC-27); other admission independent. |
| P-03b | Prior Panic then Admit | `handle` | Panic handled as error (DOC-27); subsequent admission per resulting state. |
| P-04a | State (due expiry) then delayed Report | `transition → HalfOpen_AtBudget`; report `handle` | State refresh transitions; report processed if attributable to current period. |
| P-04b | Delayed Report then State | `handle`; `transition → HalfOpen_AtBudget` | Report then refresh/transition on observation. |
| P-05a | Counts then Report | `handle` | Snapshot unaffected by later report (DOC-20). |
| P-05b | Report then Counts | `handle` | Snapshot reflects report (unless cleared per DOC-21/22). |
| P-06a | State then returning Execute | `handle` | Observer read then completion updates per docs; stale ignored (DOC-22). |
| P-06b | Execute return then State | `handle` | State reflects outcome possibility (trip or not) per DOC-12. |
| P-07a | Counts then Return | `handle` | Snapshot unaffected by later completion. |
| P-07b | Return then Counts | `handle` | Snapshot reflects counted outcome. |
| P-08a | State then Panic | `handle` | Panic handled as error + re-raised (DOC-27). |
| P-08b | Panic then State | `handle` | Observer reflects resulting state. |
| P-09a | Counts then Panic | `handle` | Snapshot unaffected by later panic. |
| P-09b | Panic then Counts | `handle` | Snapshot reflects panic-as-error outcome (DOC-27). |
| P-10a | State (Open due) then Admit | `transition → HalfOpen_AtBudget`; then admission budget applied | Observer drives expiry; following Admit half-open. |
| P-10b | Admit then State (Open due) | `transition → HalfOpen_AtBudget` | Admit triggers half-open; State observes it. |
| P-11a | Counts then Admit (Closed/HalfOpen) | `handle` | Snapshot then admission per state; HalfOpen enforces budget. |
| P-11b | Admit then Counts | `handle` | Admission counted; snapshot reflects it if applicable. |
| P-12a | State then Counts (due expiry) | `transition → HalfOpen_AtBudget`; counts `handle` | Transition clears counts (DOC-21); subsequent Counts shows cleared. |
| P-12b | Counts then State (due expiry) | `transition → HalfOpen_AtBudget`; counts `handle` | First snapshot may be pre-clear; State transitions; later reads cleared. |
| P-13a | Name then Admit | `handle` | Name read (DOC-4) independent of admission. |
| P-13b | Admit then Name | `handle` | Admission then name read; name unchanged. |
| P-14a | Name then Report | `handle` | Name read; report counted per state (DOC-16–18, DOC-22). |
| P-14b | Report then Name | `handle` | Report counted; name read unchanged. |
| P-15a | Name then Return | `handle` | Name read; Execute completion processed per DOC-11–18. |
| P-15b | Return then Name | `handle` | Completion processed; name read unchanged. |
| P-16a | Name then Panic | `handle` | Name read; panic handled as error + re-raised (DOC-27). |
| P-16b | Panic then Name | `handle` | Panic processed; name read unchanged. |

Coverage checklist:

- [x] Create
- [x] Admit
- [x] State
- [x] Counts
- [x] Name
- [x] Report
- [x] Return
- [x] Panic
- [x] Classify
- [x] TripPolicy
- [x] Notify
- [x] Expiry
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
- [x] P-11a
- [x] P-11b
- [x] P-12a
- [x] P-12b
- [x] P-13a
- [x] P-13b
- [x] P-14a
- [x] P-14b
- [x] P-15a
- [x] P-15b
- [x] P-16a
- [x] P-16b
