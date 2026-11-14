| id | Situation | Disposition | Expected behaviour (requirement terms) |
|---|---|---|---|
| Execute | Closed, no failure threshold reached | `handle` | Run the caller's request; classify the returned error; count success or failure; closed-state counting stays within current `Counts` generation. |
| Execute | Closed, failure counted and `ReadyToTrip` returns true | `transition → Open` | Run request, count failure, then transition to Open; invoke `OnStateChange(Name, Closed, Open)`. |
| Execute | Open, `Timeout` not yet elapsed | `reject` (ErrOpenState) | Return error instantly without running the request; do not call the request function, classifier, or trip policy. |
| Execute | Open, `Timeout` elapsed | `transition → HalfOpen` then `handle` | Transition to HalfOpen, calling `OnStateChange(Name, Open, HalfOpen)`; admit the request (subject to half-open budget) and run it. |
| Execute | HalfOpen, admitted-request count below `MaxRequests` (default 1 when 0) | `handle` | Run request; count result; a failure may transition to Open, a success may transition to Closed. |
| Execute | HalfOpen, admitted-request count equals/exceeds `MaxRequests` | `reject` (ErrTooManyRequests) | Return error instantly without running the request. |
| Execute | Request returns an error judged failure and `ReadyToTrip` true | `transition → Open` | Per requirement: `ReadyToTrip` called with a copy of `Counts`; on true go Open; `OnStateChange` fires. |
| Execute | Request panics | `handle` | Count as a failure (per default `IsSuccessful` = false for non-nil error), evaluate trip policy, then re-panic the same panic value to the caller. |
| Execute | Nil request function supplied | `reject` (declared refusal: nil-argument diagnostic) | Refuse before running; no counter change, no trip-policy call, no `OnStateChange`. Open question: precise signal form (panic vs error) — flag as `UNSPECIFIED` upstream but require a declared refusal. |
| Execute | Zero-value or wrong receiver used | `reject` (declared refusal: invalid-receiver diagnostic) | Refuse; do not admit or mutate another breaker's state. |
| Allow | Closed, below failure threshold | `handle` | Return a callback; caller reports outcome separately; no request is run by the breaker. |
| Allow | Closed failure at completion with `ReadyToTrip` true | `transition → Open` via later `Report` | Reported failure drives the closed-state trip policy; `OnStateChange(Name, Closed, Open)` fires. |
| Allow | Open, `Timeout` not elapsed | `reject` (ErrOpenState) | Return ErrOpenState with no callback; caller must not run work. |
| Allow | Open, `Timeout` elapsed | `transition → HalfOpen` then `handle` | Transition, notify `OnStateChange(Name, Open, HalfOpen)`, then issue a callback if budget permits. |
| Allow | HalfOpen, count below `MaxRequests` | `handle` | Issue callback; caller must report exactly one outcome. |
| Allow | HalfOpen, budget exhausted | `reject` (ErrTooManyRequests) | Return ErrTooManyRequests; no callback issued. |
| Allow | Nil receiver / wrong receiver | `reject` | Declared refusal; no mutation of any breaker. |
| StateRead | Closed | `handle` | Return Closed. |
| StateRead | Closed with `Interval` > 0 elapsed since generation start | `handle` | Return Closed for the closed period; per doctrine the cyclic clear advances the generation at clear time, not on read — record `Counts` cleared only when clear is executed. |
| StateRead | Open with `Timeout` elapsed | `handle` | Return HalfOpen (the read observes/lazily reconciles expiry per lock discipline). |
| StateRead | Open with `Timeout` not elapsed | `handle` | Return Open. |
| StateRead | HalfOpen | `handle` | Return HalfOpen. |
| StateRead | Concurrent observers near a transition | `handle` | Each observer sees a coherent single state consistent with mutex-protected state and expiry reconciliation. |
| StateRead | Zero-value / wrong receiver | `reject` | Declared refusal; no spoofed observation. |
| CountsRead | Stable state, no reset pending | `handle` | Return `Counts` by value with `Requests/TotalSuccesses/TotalFailures/ConsecutiveSuccesses/ConsecutiveFailures` coherent under mutex. |
| CountsRead | Closed with `Interval` elapsed since last clear | `handle` | Return counters reflecting a cleared generation if clear already happened; otherwise a read before clear sees pre-clear counters (per doctrine: clear is separate). |
| CountsRead | Open/HalfOpen just after generation advance | `handle` | Return counters of the current generation (zeroed at state change). |
| CountsRead | Concurrent with completion accounting | `handle` | Mutex-serialized; no torn values. |
| CountsRead | Zero-value / wrong receiver | `reject` | Declared refusal. |
| NameRead | Configured breaker | `handle` | Return `Name` from `Settings`. |
| NameRead | Two-step breaker | `handle` | Return `Name` from `Settings`. |
| NameRead | Zero-value breaker | `handle`/`reject` | Empty name would be returned by an immutable field; require declared refusal per `UV-07` (reject) — doctrine: reject invalid receiver. |
| NameRead | Concurrent with Notify | `handle` | Name is immutable; readers see the same value regardless of transitions. |
| Report | Admitted generation matches current generation, Closed | `handle` | Count success or failure; failure triggers `ReadyToTrip`, success updates consecutive-success. |
| Report | Admitted generation matches, HalfOpen success | `transition → Closed` | Per requirement: HalfOpen state is closed on success; clear counters; `OnStateChange(Name, HalfOpen, Closed)`. |
| Report | Admitted generation matches, HalfOpen failure | `transition → Open` | Clear counters; `OnStateChange(Name, HalfOpen, Open)`. |
| Report | Admitted generation differs from current generation (state change or interval clear intervened) | `ignore (documented)` | Counts ignores results of requests sent before clearing — drop the report. |
| Report | Generation matches but state has advanced past admission via another path | `ignore (documented)` | Do not apply stale outcome against the new generation. |
| Report | First success on callback | `handle` | Standard accounting path. |
| Report | First failure on callback | `handle` | Standard accounting path; may trip. |
| Report | Second invocation on the same callback (duplicate) | `reject` (declared refusal) | Contract requires one report per callback; mechanism unspecified — must be a declared refusal, not silent double-count. |
| Report | Concurrent success and failure on the same callback | `reject` / one wins, other refused | Only one outcome per callback is honoured; the second is a declared refusal signal. |
| Report | Manual invocation without ever receiving the callback (forged) | `reject` | No matching callback issued → refused; no counter mutation. |
| Report | Nil callback invocation | `reject` | Declared refusal. |
| RequestReturn | Returns value+error, generation matches | `handle` | Feed error to `Classify`, then `Report`-equivalent accounting. |
| RequestReturn | Returns after generation change (state change or interval clear) | `ignore (documented)` | Counts ignores results of requests sent before clearing. |
| RequestReturn | Returns after `Execute` caller abandoned the call | `handle` | Breaker has no shutdown/cancellation contract; the return still feeds the current generation accounting if generation matches; caller owns cleanup. |
| RequestReturn | Never returns (blocked) | `UNSPECIFIED` | No prompt-return guarantee; breaker cannot time-bound; document. |
| RequestReturn | Goroutine exits without return | `UNSPECIFIED` | No record produced; same as loss of report. |
| RequestReturn | Panics inside the request | `handle` | Treat as failure, evaluate trip policy, re-panic same value. |
| RequestReturn | Returns duplicated (already returned once) | `UNSPECIFIED` | Not possible from library invocation; caller-side anomaly — flag. |
| Classify | Returns true on non-nil error | `handle` | Counted as success. |
| Classify | Returns false on non-nil error | `handle` | Counted as failure; may trip in Closed. |
| Classify | Returns true with nil error | `handle` | Success. |
| Classify | Returns false with nil error | `handle` | Failure per `IsSuccessful` contract (custom callback value). |
| Classify | Nil `IsSuccessful` supplied | `handle` | Default classifier: false for non-nil error, true for nil. |
| Classify | Panics / stalls | `UNSPECIFIED` | Custom implementation governs; breaker cannot guarantee state; document as upstream hazard. |
| Classify | Returns after generation change | `ignore (documented)` | Counts ignores pre-clear results. |
| TripPolicy | Called in Closed after a failure | `handle` | Called with copy of `Counts`; true ��� Open transition, false → stay Closed. |
| TripPolicy | `ReadyToTrip` nil | `handle` | Default: open when `ConsecutiveFailures > 5`. |
| TripPolicy | Panics | `UNSPECIFIED` | Must not corrupt state; if it panics, mutex must be released and behaviour declared. |
| TripPolicy | Reenters with the same breaker lock held (synchronous callback) | `reject`/`UNSPECIFIED` | Contract has no reentrancy guarantee; must be declared (deadlock hazard). |
| TripPolicy | Invoked outside any failure (forged) | `reject` | No caller path should invoke; must be a declared refusal. |
| TripPolicy | Returns after generation change (stale snapshot) | `ignore (documented)` | Counts snapshot captured before clear is not applied to the new generation. |
| Notify | State change fires with a registered callback | `handle` | Call `OnStateChange(Name, from, to)` synchronously; state transition already applied. |
| Notify | State change with nil `OnStateChange` | `ignore (documented)` | No-op. |
| Notify | Callback panics | `handle`/`UNSPECIFIED` | State already transitioned; panic must propagate or be declared — contract silent; treat state as transitioned (occurred) whichever propagation is chosen. |
| Notify | Callback stalls indefinitely | `UNSPECIFIED` | Sync-on-locked path means other calls block; document. |
| Notify | Reenters a locking breaker method | `UNSPECIFIED` | Deadlock; contract silent; declared refusal of reentrancy required at API level. |
| Notify | Fires repeatedly for same transition (duplicate) | `ignore (accidental)`/`reject` | Must never re-fire for the same state change; duplicate is refused. |
| Notify | Manual invocation without a transition (forged) | `reject` | Refuse; no spoofed transition. |
| Notify | Downstream side effect partial | `handle` | Library has no commit guarantee; caller owns downstream; document. |
| ReconcileTime | Sample taken while `Timeout` not yet elapsed in Open | `handle` | Stay Open. |
| ReconcileTime | Sample exactly at `Timeout` in Open | `transition → HalfOpen` | Per requirement, expiry at Timeout means half-open on observation; boundary included. |
| ReconcileTime | Sample after many intervals in Closed with `Interval` > 0 | `handle` | Advance one clear operationally (single clear); not multiple back-dated clears — must be declared. |
| ReconcileTime | Concurrent observations of the same expiry | `handle` | Exactly one transition to HalfOpen; observers agree. |
| ReconcileTime | Observation omitted | `handle` | Stale-as-of-last-observation; no background timer by contract; document. |
| ReconcileTime | `Interval` <= 0 in Closed | `ignore (documented)` | No closed-state clear. |
| ReconcileTime | `Timeout` <= 0 | `handle` | Use default 60s. |
| ReconcileTime | Sampled time regresses (clock skew) | `UNSPECIFIED` | No monotonicity guarantee; declare. |
| UV-01 | Caller omits work or ceases calling | `ignore (documented)` | No counters, no state change; breaker idle. |
| UV-02 | First admission delayed across `Timeout`/`Interval` | `handle` | For Closed → evaluate Interval lazily; for Open → expiry evaluated at admission (this call may itself trigger HalfOpen). |
| UV-03 | Repeated acquisition from same caller while Execute pending | `handle` | Every acquisition hits the normal gate; HalfOpen budget (`MaxRequests`) caps concurrent admissions. |
| UV-03 | Repeated acquisition while a returned callback is outstanding | `handle` | Same gate; outstanding callback does not exempt caller; budget not refunded. |
| UV-04 | Admission delivered after withdrawal of demand | `reject` (ErrOpenState / ErrTooManyRequests) | Gate evaluates at call time; if breaker is Open/budget exhausted it refuses; no stale prior-demand admission. |
| UV-04 | Admission delivered against replacement breaker | `reject` (invalid-receiver refusal) | Refuse; do not mutate the replacement's state. |
| UV-05 | Concurrent competing acquisitions near HalfOpen budget | `handle` | Exactly `MaxRequests` (default 1) admitted; others `reject` (ErrTooManyRequests); atomic under mutex. |
| UV-06 | Unsolicited acquisition without matching business demand | `handle` | Breaker cannot distinguish demand legitimacy; performs admission normally; caller-side policy. |
| UV-07 | Wrong receiver / zero-value receiver | `reject` (declared refusal) | Refuse; no state mutation. |
| UV-07 | Unexpected valid constructor settings (e.g., `MaxRequests` negative, `Timeout` negative) | `handle` | Apply documented normalizations: `MaxRequests<=0` → 1, `Timeout<=0` → 60s, `Interval<=0` → no clear. Other settings pass through. |
| UV-07 | Nil `Execute` function supplied | `reject` | Declared refusal before mutating state. |
| UV-08 | Observer omits or delays reads | `ignore (documented)` | No observer-driven state change. |
| UV-08 | Observer polls repeatedly | `handle` | Each read is a normal read; expiry reconciliation only. |
| UV-08 | Sample near a transition | `handle` | Reads are mutex-consistent; observe before or after transition consistently. |
| UV-08 | Concurrent observations | `handle` | Mutex-serialized. |
| UV-08 | Read without monitoring trigger | `handle` | Breaker works without observers; document. |
| UV-09 | Report omitted (abandon/cancel/lose callback) | `ignore (documented)` | Counters not decremented (`Requests` not refunded); accounting asymmetry owned by caller; no queued retry. |
| UV-10 | Late success/failure after interval reset, open expiry, or generation change | `ignore (documented)` | Generation mismatch → outcome ignored per "ignores results of requests sent before clearing". |
| UV-11 | Same success or failure repeated on one callback | `reject` (declared refusal) | Second report refused; no double-count. |
| UV-12 | Success and failure on same callback concurrently | `reject` / one wins | Mutex serializes; first applied, second refused; contract requires exactly one outcome. |
| UV-13 | Callback invoked manually without its normal trigger | `reject` | Declared refusal; no state mutation. |
| UV-13 | Replay of callback-shaped operation | `reject` | Refuse; no once-only handle available → return refusal. |
| UV-13 | Duplicated `RequestReturn`-style interaction | `UNSPECIFIED` | Not producible by library; documented hazard. |
| UV-14 | Wrong classification value reported | `handle` | Classifier result is authoritative to the breaker; wrong-but-typed values counted as classified. |
| UV-14 | Report for another request transferred to this callback | `reject` (declared refusal) | No per-request registry → callback does not authenticate source; require caller responsibility; treat foreign outcome as a report on the callback it arrived on; declare `UV-14` upstream reflection in contract. |
| UV-14 | Completion across owners (transfer across breakers) | `reject` | Captured receiver check: if the callback references a different breaker, refuse. |
| UV-15 | Request blocks / never returns | `UNSPECIFIED` | No prompt-return guarantee; the admitted slot persists; document caller responsibility. |
| UV-15 | Request exits goroutine without returning | `UNSPECIFIED` | No accounting produced; caller owns cleanup. |
| UV-15 | Returns only after caller demand ends | `handle` | Still applied if generation matches; else ignored. |
| UV-16 | Request function panics | `handle` | Count failure, evaluate trip policy, re-panic same panic. |
| UV-16 | Classifier panics / stalls | `UNSPECIFIED` | Custom implementation governs; declare. |
| UV-16 | Classifier reenters | `UNSPECIFIED` | No reentrancy guarantee; declared. |
| UV-16 | Classifier produces no ordinary return | `UNSPECIFIED` | No classification; declare refusal to account. |
| UV-17 | Trip policy panics / stalls | `UNSPECIFIED` | Must not corrupt mutex; behaviour declared by contract (silent). |
| UV-17 | Notify panics / stalls | `UNSPECIFIED` | Same; state already transitioned. |
| UV-17 | Policy/notify reenters a locking breaker method | `UNSPECIFIED` | Deadlock hazard; declared. |
| UV-18 | Downstream side effect partial in Notify | `handle` | Library performs no commit/rollback; document. |
| UV-18 | Notify performs unexpected side effect | `handle` | Library is transparent; document. |
| UV-19 | Observation omitted | `handle` | No timer; expiry deferred to next call. |
| UV-19 | Sample exactly at expiry | `transition → HalfOpen` | Boundary inclusive per contract. |
| UV-19 | Sample after many intervals | `handle` | Single clear per observation; not compounding. |
| UV-19 | Same expiry observed from several callers | `handle` | Exactly one transition; others see already-HalfOpen. |
| P-01a | Execute then Report (earlier issued report then new admission) | `handle` | Earlier report is accounted under its captured generation; new Execute evaluates current gate. Independent unless generation changed. |
| P-01b | Report then Execute | `handle` | Report applied first; Execute sees post-report state (may be Open → reject). |
| P-02a | Allow then Report | `handle` | Prior report applied; new Allow evaluates gate at call time. |
| P-02b | Report then Allow | `handle` | Report may transition; Allow observes post-report state. |
| P-03a | StateRead then Report | `handle` | Read reflects pre-report; Report applied if generation matches. |
| P-03b | Report then StateRead | `handle` | Report may trip → StateRead shows Open. |
| P-04a | CountsRead then Report | `handle` | Snapshot is pre-report; Report applied only if generation matches. |
| P-04b | Report then CountsRead | `handle` | Snapshot reflects report if generation matched; else reflects current generation. |
| P-05a | StateRead then Execute (expiry) | `handle` | StateRead observes expiry, may transition to HalfOpen; Execute then admitted under HalfOpen budget or rejected. |
| P-05b | Execute then StateRead | `handle` | Execute may transition Open→HalfOpen on admission; StateRead reflects resulting state coherently. |
| P-06a | StateRead then Allow | `handle` | Read/lazy transition then Allow admitted if budget allows. |
| P-06b | Allow then StateRead | `handle` | Allow admission reflected; StateRead shows current state. |
| P-07a | Execute then RequestReturn | `handle` | New caller gated by current state; return of running request accounted on its generation. |
| P-07b | RequestReturn then Execute | `handle` | Return accounted (may trip); Execute sees resulting state. |
| P-08a | StateRead then RequestReturn | `handle` | Return accounting unaffected by prior read (reads don't advance generation unless expiry). |
| P-08b | RequestReturn then StateRead | `handle` | Read sees post-return state (may show Open if trip). |
| P-09a | CountsRead then RequestReturn | `handle` | Snapshot pre-return; return accounted if generation matches. |
| P-09b | RequestReturn then CountsRead | `handle` | Snapshot post-return. |
| P-10a | Classify then Notify (different admitted calls) | `handle` | Independent; classification accounting for one call proceeds alongside notification of a transition from another. Mutex serializes. |
| P-10b | Notify then Classify | `handle` | Notify completes (or panics), then classification accounted. Reentrancy risk documented. |
| P-11a | Execute then Classify | `handle` | New caller gated; classification of earlier request applied under its generation. |
| P-11b | Classify then Execute | `handle` | Classification may trip → Execute sees Open. |
| P-12a | CountsRead then Classify | `handle` | Snapshot pre-classification. |
| P-12b | Classify then CountsRead | `handle` | Snapshot post-classification. |
| P-13a | StateRead then Classify (expiry) | `handle` | Read may lazily go HalfOpen; classification of a pre-expiry request has generation mismatch → `ignore (documented)`. |
| P-13b | Classify then StateRead | `handle` | Classification may trip; read reflects. |
| P-14a | StateRead then Notify | `handle` | Read reflects pre- or post-transition consistently. |
| P-14b | Notify then StateRead | `handle` | Read shows post-transition state. |
| P-15a | Execute then TripPolicy | `handle` | New caller gated; in-progress trip policy from another failure evaluated under its generation. |
| P-15b | TripPolicy then Execute | `handle` | Trip outcome evaluated first; Execute sees resulting state. |
| P-16a | Allow then Notify | `handle` | Allow issues/refuses per gate; notification for another transition fires independently. |
| P-16b | Notify then Allow | `handle` | Notify completes; Allow applies post-transition state. |
| P-17a | NameRead then Notify | `handle` | Name unchanged by transitions. |
| P-17b | Notify then NameRead | `handle` | Same — immutable name. |
| P-18a | CountsRead then Execute | `handle` | Snapshot pre-admission. |
| P-18b | Execute then CountsRead | `handle` | Snapshot reflects admission (`Requests` incremented). |
| P-19a | CountsRead then Allow | `handle` | Snapshot pre-admission. |
| P-19b | Allow then CountsRead | `handle` | `Requests` not incremented until report; snapshot shows admission not reflected in success/failure but `Requests` reflects admitted pending. |
| P-20a | CountsRead then Notify | `handle` | Snapshot pre-transition. |
| P-20b | Notify then CountsRead | `handle` | Counters cleared at transition; snapshot reflects current generation. |
| P-21a | StateRead then TripPolicy | `handle` | Read may show Closed before a concurrent trip policy opens. |
| P-21b | TripPolicy then StateRead | `handle` | Read shows result of trip (Open). |
| P-22a | CountsRead then TripPolicy | `handle` | Snapshot pre-trip; trip uses its own `Counts` copy per contract. |
| P-22b | TripPolicy then CountsRead | `handle` | Snapshot reflects post-trip generation clear. |
| P-23a | Execute then Notify | `handle` | New caller gated; notification for another transition fires independently; mutex serialized. |
| P-23b | Notify then Execute | `handle` | Notify completes; Execute applies post-transition state. |
| P-24a | Report then Notify | `handle` | Competing reports are serialized; notification fires for whichever transition wins. Second report applied under its generation if matches, else ignored. |
| P-24b | Notify then Report | `handle` | Notify completes; Report applied if generation matches. |
| P-25a | RequestReturn then Notify | `handle` | Return accounted under its generation; notification for another transition fires. |
| P-25b | Notify then RequestReturn | `handle` | Notify completes; return accounted under its generation (may be stale → ignored). |
| P-26a | Classify then TripPolicy | `handle` | Different requests; classification accounted if generation matches; trip policy evaluated on its request's snapshot. |
| P-26b | TripPolicy then Classify | `handle` | Trip outcome applied first; late classification of pre-trip request has generation mismatch → ignored. |
| P-27a | RequestReturn then TripPolicy | `handle` | Return accounted; concurrent trip policy from another failure serialized. |
| P-27b | TripPolicy then RequestReturn | `handle` | If trip advanced generation, stale return ignored; else accounted. |
| P-28a | Report then TripPolicy | `handle` | Report serialized; trip policy from another failure applied after. |
| P-28b | TripPolicy then Report | `handle` | Report applied only if generation still matches; else ignored. |

- [x] Execute
- [x] Allow
- [x] StateRead
- [x] CountsRead
- [x] NameRead
- [x] Report
- [x] RequestReturn
- [x] Classify
- [x] TripPolicy
- [x] Notify
- [x] ReconcileTime
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
- [x] UV-19
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
- [x] P-17a
- [x] P-17b
- [x] P-18a
- [x] P-18b
- [x] P-19a
- [x] P-19b
- [x] P-20a
- [x] P-20b
- [x] P-21a
- [x] P-21b
- [x] P-22a
- [x] P-22b
- [x] P-23a
- [x] P-23b
- [x] P-24a
- [x] P-24b
- [x] P-25a
- [x] P-25b
- [x] P-26a
- [x] P-26b
- [x] P-27a
- [x] P-27b
- [x] P-28a
- [x] P-28b