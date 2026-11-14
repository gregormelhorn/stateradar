# Part B diff
Coverage check passed for 30 catalogue events and 56 pair orderings. Each distinct Situation is classified below. The pack listed no retained or removed analysis IDs. No implementation code or residual quoted fragments were found in the dispatched package.
The coverage checker reported no explicit as-is marks. As-is dependencies remain in the descriptions of lazy time reconciliation; stored count reads; fixed Name reads; lack of per-request registry; no refund for missing reports; and mutex-serialized access or callbacks. Agreement on these behaviors is not independent where cited solely from the catalogue. The latter fields were marked observed in code in the package. The public error comments also contain an imprecise over-cap wording at equality.
| ID | Situation | Classification | Evidence, question or scope |
|---|---|---|---|
| Execute | Closed, no failure threshold reached | convergent | Agrees on the observable behavior for this situation. Execute matrix column or Execute pair trace. |
| Execute | Closed, failure counted and `ReadyToTrip` returns true | convergent | Agrees on the observable behavior for this situation. Execute matrix column or Execute pair trace. |
| Execute | Open, `Timeout` not yet elapsed | convergent | Agrees on the observable behavior for this situation. Execute matrix column or Execute pair trace. |
| Execute | Open, `Timeout` elapsed | convergent | Agrees on the observable behavior for this situation. Execute matrix column or Execute pair trace. |
| Execute | HalfOpen, admitted-request count below `MaxRequests` (default 1 when 0) | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. Execute matrix column or Execute pair trace. → Q-04 |
| Execute | HalfOpen, admitted-request count equals/exceeds `MaxRequests` | convergent | Agrees on the observable behavior for this situation. Execute matrix column or Execute pair trace. |
| Execute | Request returns an error judged failure and `ReadyToTrip` true | convergent | Agrees on the observable behavior for this situation. Execute matrix column or Execute pair trace. |
| Execute | Request panics | divergence | Panic bypasses IsSuccessful. The trip or notification panic can replace the original. Execute matrix column or Execute pair trace. → Q-10 |
| Execute | Nil request function supplied | divergence | A nil request invokes the panic path once admitted; current admission already changed Requests. Execute matrix column or Execute pair trace. → Q-08 |
| Execute | Zero-value or wrong receiver used | divergence | A wrong live receiver admits according to its own state. Zero value is a separate initialization issue. Execute matrix column or Execute pair trace. → Q-08 |
| Allow | Closed, below failure threshold | convergent | Agrees on the observable behavior for this situation. Allow matrix column or Allow pair trace. |
| Allow | Closed failure at completion with `ReadyToTrip` true | convergent | Agrees on the observable behavior for this situation. Allow matrix column or Allow pair trace. |
| Allow | Open, `Timeout` not elapsed | convergent | Agrees on the observable behavior for this situation. Allow matrix column or Allow pair trace. |
| Allow | Open, `Timeout` elapsed | convergent | Agrees on the observable behavior for this situation. Allow matrix column or Allow pair trace. |
| Allow | HalfOpen, count below `MaxRequests` | divergence | Allow's docstring expects a report and supplies no exactly-once enforcement; this is a generation budget. Allow matrix column or Allow pair trace. → Q-03 |
| Allow | HalfOpen, budget exhausted | convergent | Agrees on the observable behavior for this situation. Allow matrix column or Allow pair trace. |
| Allow | Nil receiver / wrong receiver | divergence | Expected handling or ordering differs from the cited execution. Allow matrix column or Allow pair trace. → Q-08 |
| StateRead | Closed | convergent | Agrees on the observable behavior for this situation. StateRead matrix column or StateRead pair trace. |
| StateRead | Closed with `Interval` > 0 elapsed since generation start | divergence | State performs reset when it is the first observation after the strict deadline. StateRead matrix column or StateRead pair trace. → Q-02 |
| StateRead | Open with `Timeout` elapsed | convergent | Agrees on the observable behavior for this situation. StateRead matrix column or StateRead pair trace. |
| StateRead | Open with `Timeout` not elapsed | convergent | Agrees on the observable behavior for this situation. StateRead matrix column or StateRead pair trace. |
| StateRead | HalfOpen | convergent | Agrees on the observable behavior for this situation. StateRead matrix column or StateRead pair trace. |
| StateRead | Concurrent observers near a transition | convergent | Agrees on the observable behavior for this situation. StateRead matrix column or StateRead pair trace. |
| StateRead | Zero-value / wrong receiver | divergence | Expected handling or ordering differs from the cited execution. StateRead matrix column or StateRead pair trace. → Q-08 |
| CountsRead | Stable state, no reset pending | convergent | Agrees on the observable behavior for this situation. CountsRead matrix column or CountsRead pair trace. |
| CountsRead | Closed with `Interval` elapsed since last clear | convergent | Agrees on the observable behavior for this situation. CountsRead matrix column or CountsRead pair trace. |
| CountsRead | Open/HalfOpen just after generation advance | convergent | Agrees on the observable behavior for this situation. CountsRead matrix column or CountsRead pair trace. |
| CountsRead | Concurrent with completion accounting | convergent | Agrees on the observable behavior for this situation. CountsRead matrix column or CountsRead pair trace. |
| CountsRead | Zero-value / wrong receiver | divergence | Expected handling or ordering differs from the cited execution. CountsRead matrix column or CountsRead pair trace. → Q-08 |
| NameRead | Configured breaker | convergent | Agrees on the observable behavior for this situation. NameRead matrix column or NameRead pair trace. |
| NameRead | Two-step breaker | convergent | Agrees on the observable behavior for this situation. NameRead matrix column or NameRead pair trace. |
| NameRead | Zero-value breaker | divergence | Expected handling or ordering differs from the cited execution. NameRead matrix column or NameRead pair trace. → Q-08 |
| NameRead | Concurrent with Notify | convergent | Agrees on the observable behavior for this situation. NameRead matrix column or NameRead pair trace. |
| Report | Admitted generation matches current generation, Closed | convergent | Agrees on the observable behavior for this situation. Report matrix column or Report pair trace. |
| Report | Admitted generation matches, HalfOpen success | divergence | Expected handling or ordering differs from the cited execution. Report matrix column or Report pair trace. → Q-04 |
| Report | Admitted generation matches, HalfOpen failure | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. Report matrix column or Report pair trace. → Q-04 |
| Report | Admitted generation differs from current generation (state change or interval clear intervened) | convergent | Agrees on the observable behavior for this situation. Report matrix column or Report pair trace. |
| Report | Generation matches but state has advanced past admission via another path | artefact | Every state change increments generation; this setup is structurally absent before full wrap. The catalogue should make state-change generation updates explicit. Remembrance now explicitly records the generation advance on every enum change. The retained blind package shows the original wording. Report matrix column or Report pair trace. → Q-05 |
| Report | First success on callback | convergent | Agrees on the observable behavior for this situation. Report matrix column or Report pair trace. |
| Report | First failure on callback | convergent | Agrees on the observable behavior for this situation. Report matrix column or Report pair trace. |
| Report | Second invocation on the same callback (duplicate) | divergence | Expected handling or ordering differs from the cited execution. Report matrix column or Report pair trace. → Q-03 |
| Report | Concurrent success and failure on the same callback | divergence | Expected handling or ordering differs from the cited execution. Report matrix column or Report pair trace. → Q-03 |
| Report | Manual invocation without ever receiving the callback (forged) | divergence | Possession of the returned callback is required; there is no underlying forged-report operation that can return a breaker refusal. Report matrix column or Report pair trace. → Q-13 |
| Report | Nil callback invocation | divergence | Expected handling or ordering differs from the cited execution. Report matrix column or Report pair trace. → Q-13 |
| RequestReturn | Returns value+error, generation matches | convergent | Agrees on the observable behavior for this situation. RequestReturn matrix column or RequestReturn pair trace. |
| RequestReturn | Returns after generation change (state change or interval clear) | divergence | Only the accounting is ignored. Classifier still executes and original result is still returned. RequestReturn matrix column or RequestReturn pair trace. → Q-05 |
| RequestReturn | Returns after `Execute` caller abandoned the call | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. RequestReturn matrix column or RequestReturn pair trace. → Q-06 |
| RequestReturn | Never returns (blocked) | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. RequestReturn matrix column or RequestReturn pair trace. → Q-06 |
| RequestReturn | Goroutine exits without return | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. RequestReturn matrix column or RequestReturn pair trace. → Q-06 |
| RequestReturn | Panics inside the request | convergent | Agrees on the observable behavior for this situation. RequestReturn matrix column or RequestReturn pair trace. |
| RequestReturn | Returns duplicated (already returned once) | convergent | Agrees on the observable behavior for this situation. RequestReturn matrix column or RequestReturn pair trace. |
| Classify | Returns true on non-nil error | convergent | Agrees on the observable behavior for this situation. Classify matrix column or Classify pair trace. |
| Classify | Returns false on non-nil error | convergent | Agrees on the observable behavior for this situation. Classify matrix column or Classify pair trace. |
| Classify | Returns true with nil error | convergent | Agrees on the observable behavior for this situation. Classify matrix column or Classify pair trace. |
| Classify | Returns false with nil error | convergent | Agrees on the observable behavior for this situation. Classify matrix column or Classify pair trace. |
| Classify | Nil `IsSuccessful` supplied | convergent | Agrees on the observable behavior for this situation. Classify matrix column or Classify pair trace. |
| Classify | Panics / stalls | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. Classify matrix column or Classify pair trace. → Q-10 |
| Classify | Returns after generation change | divergence | The classifier itself runs and can have effects; the later account write is ignored. Classify matrix column or Classify pair trace. → Q-05 |
| TripPolicy | Called in Closed after a failure | convergent | Agrees on the observable behavior for this situation. TripPolicy matrix column or TripPolicy pair trace. |
| TripPolicy | `ReadyToTrip` nil | convergent | Agrees on the observable behavior for this situation. TripPolicy matrix column or TripPolicy pair trace. |
| TripPolicy | Panics | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. TripPolicy matrix column or TripPolicy pair trace. → Q-10 |
| TripPolicy | Reenters with the same breaker lock held (synchronous callback) | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. TripPolicy matrix column or TripPolicy pair trace. → Q-09 |
| TripPolicy | Invoked outside any failure (forged) | divergence | Expected handling or ordering differs from the cited execution. TripPolicy matrix column or TripPolicy pair trace. → Q-13 |
| TripPolicy | Returns after generation change (stale snapshot) | divergence | Policy runs under the same mutex as the reset; the delivery cannot race a state change after the snapshot. TripPolicy matrix column or TripPolicy pair trace. → Q-05 |
| Notify | State change fires with a registered callback | convergent | Agrees on the observable behavior for this situation. Notify matrix column or Notify pair trace. |
| Notify | State change with nil `OnStateChange` | convergent | Agrees on the observable behavior for this situation. Notify matrix column or Notify pair trace. |
| Notify | Callback panics | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. Notify matrix column or Notify pair trace. → Q-10 |
| Notify | Callback stalls indefinitely | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. Notify matrix column or Notify pair trace. → Q-09 |
| Notify | Reenters a locking breaker method | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. Notify matrix column or Notify pair trace. → Q-09 |
| Notify | Fires repeatedly for same transition (duplicate) | divergence | Expected handling or ordering differs from the cited execution. Notify matrix column or Notify pair trace. → Q-13 |
| Notify | Manual invocation without a transition (forged) | divergence | Expected handling or ordering differs from the cited execution. Notify matrix column or Notify pair trace. → Q-13 |
| Notify | Downstream side effect partial | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. Notify matrix column or Notify pair trace. → Q-12 |
| ReconcileTime | Sample taken while `Timeout` not yet elapsed in Open | convergent | Agrees on the observable behavior for this situation. ReconcileTime matrix column or ReconcileTime pair trace. |
| ReconcileTime | Sample exactly at `Timeout` in Open | divergence | Before is false on equality. ReconcileTime matrix column or ReconcileTime pair trace. → Q-01 |
| ReconcileTime | Sample after many intervals in Closed with `Interval` > 0 | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. ReconcileTime matrix column or ReconcileTime pair trace. → Q-01 |
| ReconcileTime | Concurrent observations of the same expiry | convergent | Agrees on the observable behavior for this situation. ReconcileTime matrix column or ReconcileTime pair trace. |
| ReconcileTime | Observation omitted | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. ReconcileTime matrix column or ReconcileTime pair trace. → Q-01 |
| ReconcileTime | `Interval` <= 0 in Closed | convergent | Agrees on the observable behavior for this situation. ReconcileTime matrix column or ReconcileTime pair trace. |
| ReconcileTime | `Timeout` <= 0 | convergent | Agrees on the observable behavior for this situation. ReconcileTime matrix column or ReconcileTime pair trace. |
| ReconcileTime | Sampled time regresses (clock skew) | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. ReconcileTime matrix column or ReconcileTime pair trace. → Q-01 |
| UV-01 | Caller omits work or ceases calling | divergence | Expected handling or ordering differs from the cited execution. UV-01 matrix column or UV-01 pair trace. → Q-06 |
| UV-02 | First admission delayed across `Timeout`/`Interval` | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-02 matrix column or UV-02 pair trace. → Q-01 |
| UV-03 | Repeated acquisition from same caller while Execute pending | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-03 matrix column or UV-03 pair trace. → Q-07 |
| UV-03 | Repeated acquisition while a returned callback is outstanding | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-03 matrix column or UV-03 pair trace. → Q-07 |
| UV-04 | Admission delivered after withdrawal of demand | divergence | Expected handling or ordering differs from the cited execution. UV-04 matrix column or UV-04 pair trace. → Q-06 |
| UV-04 | Admission delivered against replacement breaker | divergence | Expected handling or ordering differs from the cited execution. UV-04 matrix column or UV-04 pair trace. → Q-08 |
| UV-05 | Concurrent competing acquisitions near HalfOpen budget | convergent | Agrees on the observable behavior for this situation. UV-05 matrix column or UV-05 pair trace. |
| UV-06 | Unsolicited acquisition without matching business demand | convergent | Agrees on the observable behavior for this situation. UV-06 matrix column or UV-06 pair trace. |
| UV-07 | Wrong receiver / zero-value receiver | divergence | Expected handling or ordering differs from the cited execution. UV-07 matrix column or UV-07 pair trace. → Q-08 |
| UV-07 | Unexpected valid constructor settings (e.g., `MaxRequests` negative, `Timeout` negative) | divergence | Negative MaxRequests cannot be supplied as a typed value. Nonpositive signed durations normalize. UV-07 matrix column or UV-07 pair trace. → Q-08 |
| UV-07 | Nil `Execute` function supplied | divergence | Expected handling or ordering differs from the cited execution. UV-07 matrix column or UV-07 pair trace. → Q-08 |
| UV-08 | Observer omits or delays reads | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-08 matrix column or UV-08 pair trace. → Q-01 |
| UV-08 | Observer polls repeatedly | convergent | Agrees on the observable behavior for this situation. UV-08 matrix column or UV-08 pair trace. |
| UV-08 | Sample near a transition | convergent | Agrees on the observable behavior for this situation. UV-08 matrix column or UV-08 pair trace. |
| UV-08 | Concurrent observations | convergent | Agrees on the observable behavior for this situation. UV-08 matrix column or UV-08 pair trace. |
| UV-08 | Read without monitoring trigger | convergent | Agrees on the observable behavior for this situation. UV-08 matrix column or UV-08 pair trace. |
| UV-09 | Report omitted (abandon/cancel/lose callback) | convergent-hole | The described lack of refund agrees with code; omission handling and whether exhaustion can persist are open. UV-09 matrix column or UV-09 pair trace. → Q-06 |
| UV-10 | Late success/failure after interval reset, open expiry, or generation change | convergent | Agrees on the observable behavior for this situation. UV-10 matrix column or UV-10 pair trace. |
| UV-11 | Same success or failure repeated on one callback | divergence | Expected handling or ordering differs from the cited execution. UV-11 matrix column or UV-11 pair trace. → Q-03 |
| UV-12 | Success and failure on same callback concurrently | divergence | Expected handling or ordering differs from the cited execution. UV-12 matrix column or UV-12 pair trace. → Q-03 |
| UV-13 | Callback invoked manually without its normal trigger | divergence | Expected handling or ordering differs from the cited execution. UV-13 matrix column or UV-13 pair trace. → Q-13 |
| UV-13 | Replay of callback-shaped operation | divergence | Expected handling or ordering differs from the cited execution. UV-13 matrix column or UV-13 pair trace. → Q-03 |
| UV-13 | Duplicated `RequestReturn`-style interaction | convergent | Agrees on the observable behavior for this situation. UV-13 matrix column or UV-13 pair trace. |
| UV-14 | Wrong classification value reported | convergent | Agrees on the observable behavior for this situation. UV-14 matrix column or UV-14 pair trace. |
| UV-14 | Report for another request transferred to this callback | divergence | No diagnostic or report identity check occurs. The foreign outcome is accepted as typed when generation matches. UV-14 matrix column or UV-14 pair trace. → Q-13 |
| UV-14 | Completion across owners (transfer across breakers) | divergence | The closure intentionally targets its captured receiver and generation; it has no comparison with the later owner's receiver. UV-14 matrix column or UV-14 pair trace. → Q-13 |
| UV-15 | Request blocks / never returns | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-15 matrix column or UV-15 pair trace. → Q-06 |
| UV-15 | Request exits goroutine without returning | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-15 matrix column or UV-15 pair trace. → Q-06 |
| UV-15 | Returns only after caller demand ends | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-15 matrix column or UV-15 pair trace. → Q-06 |
| UV-16 | Request function panics | convergent | Agrees on the observable behavior for this situation. UV-16 matrix column or UV-16 pair trace. |
| UV-16 | Classifier panics / stalls | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-16 matrix column or UV-16 pair trace. → Q-10 |
| UV-16 | Classifier reenters | divergence | Expected handling or ordering differs from the cited execution. UV-16 matrix column or UV-16 pair trace. → Q-10 |
| UV-16 | Classifier produces no ordinary return | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-16 matrix column or UV-16 pair trace. → Q-06 |
| UV-17 | Trip policy panics / stalls | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-17 matrix column or UV-17 pair trace. → Q-10 |
| UV-17 | Notify panics / stalls | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-17 matrix column or UV-17 pair trace. → Q-10 |
| UV-17 | Policy/notify reenters a locking breaker method | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-17 matrix column or UV-17 pair trace. → Q-09 |
| UV-18 | Downstream side effect partial in Notify | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-18 matrix column or UV-18 pair trace. → Q-12 |
| UV-18 | Notify performs unexpected side effect | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-18 matrix column or UV-18 pair trace. → Q-12 |
| UV-19 | Observation omitted | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-19 matrix column or UV-19 pair trace. → Q-01 |
| UV-19 | Sample exactly at expiry | divergence | Expected handling or ordering differs from the cited execution. UV-19 matrix column or UV-19 pair trace. → Q-01 |
| UV-19 | Sample after many intervals | convergent-hole | Recognizes the behavior or a missing contract; preserve the linked question. UV-19 matrix column or UV-19 pair trace. → Q-01 |
| UV-19 | Same expiry observed from several callers | convergent | Agrees on the observable behavior for this situation. UV-19 matrix column or UV-19 pair trace. |
| P-01a | Execute then Report (earlier issued report then new admission) | divergence | The two exported constructors expose separate API forms. No supported external route obtains a Report for an Execute receiver. P-01a matrix column or P-01a pair trace. → Q-13 |
| P-01b | Report then Execute | divergence | Same structural exclusion in reverse order. P-01b matrix column or P-01b pair trace. → Q-13 |
| P-02a | Allow then Report | convergent | Agrees on the observable behavior for this situation. P-02a matrix column or P-02a pair trace. |
| P-02b | Report then Allow | convergent | Agrees on the observable behavior for this situation. P-02b matrix column or P-02b pair trace. |
| P-03a | StateRead then Report | convergent | Agrees on the observable behavior for this situation. P-03a matrix column or P-03a pair trace. |
| P-03b | Report then StateRead | convergent | Agrees on the observable behavior for this situation. P-03b matrix column or P-03b pair trace. |
| P-04a | CountsRead then Report | convergent | Agrees on the observable behavior for this situation. P-04a matrix column or P-04a pair trace. |
| P-04b | Report then CountsRead | convergent | Agrees on the observable behavior for this situation. P-04b matrix column or P-04b pair trace. |
| P-05a | StateRead then Execute (expiry) | convergent | Agrees on the observable behavior for this situation. P-05a matrix column or P-05a pair trace. |
| P-05b | Execute then StateRead | convergent | Agrees on the observable behavior for this situation. P-05b matrix column or P-05b pair trace. |
| P-06a | StateRead then Allow | convergent | Agrees on the observable behavior for this situation. P-06a matrix column or P-06a pair trace. |
| P-06b | Allow then StateRead | convergent | Agrees on the observable behavior for this situation. P-06b matrix column or P-06b pair trace. |
| P-07a | Execute then RequestReturn | convergent | Agrees on the observable behavior for this situation. P-07a matrix column or P-07a pair trace. |
| P-07b | RequestReturn then Execute | divergence | Expected handling or ordering differs from the cited execution. P-07b matrix column or P-07b pair trace. → Q-07 |
| P-08a | StateRead then RequestReturn | convergent | Agrees on the observable behavior for this situation. P-08a matrix column or P-08a pair trace. |
| P-08b | RequestReturn then StateRead | divergence | Expected handling or ordering differs from the cited execution. P-08b matrix column or P-08b pair trace. → Q-05 |
| P-09a | CountsRead then RequestReturn | convergent | Agrees on the observable behavior for this situation. P-09a matrix column or P-09a pair trace. |
| P-09b | RequestReturn then CountsRead | divergence | Raw return does not imply accounting committed; classifier and mutex remain ahead. P-09b matrix column or P-09b pair trace. → Q-02 |
| P-10a | Classify then Notify (different admitted calls) | divergence | Expected handling or ordering differs from the cited execution. P-10a matrix column or P-10a pair trace. → Q-05 |
| P-10b | Notify then Classify | divergence | Classifier can run during notification; only accounting waits for mutex. P-10b matrix column or P-10b pair trace. → Q-05 |
| P-11a | Execute then Classify | convergent | Agrees on the observable behavior for this situation. P-11a matrix column or P-11a pair trace. |
| P-11b | Classify then Execute | divergence | Expected handling or ordering differs from the cited execution. P-11b matrix column or P-11b pair trace. → Q-05 |
| P-12a | CountsRead then Classify | convergent | Agrees on the observable behavior for this situation. P-12a matrix column or P-12a pair trace. |
| P-12b | Classify then CountsRead | divergence | A completed classifier result can pause before afterRequest locks; Counts can still see pre-accounting state. P-12b matrix column or P-12b pair trace. → Q-02 |
| P-13a | StateRead then Classify (expiry) | convergent | Agrees on the observable behavior for this situation. P-13a matrix column or P-13a pair trace. |
| P-13b | Classify then StateRead | divergence | Expected handling or ordering differs from the cited execution. P-13b matrix column or P-13b pair trace. → Q-05 |
| P-14a | StateRead then Notify | convergent | Agrees on the observable behavior for this situation. P-14a matrix column or P-14a pair trace. |
| P-14b | Notify then StateRead | pass-B-blind-spot | Part A retains an additional outcome under overlap or callback failure. P-14b matrix column or P-14b pair trace. → Q-09 |
| P-15a | Execute then TripPolicy | convergent | Agrees on the observable behavior for this situation. P-15a matrix column or P-15a pair trace. |
| P-15b | TripPolicy then Execute | pass-B-blind-spot | Part A retains an additional outcome under overlap or callback failure. P-15b matrix column or P-15b pair trace. → Q-15 |
| P-16a | Allow then Notify | convergent | Agrees on the observable behavior for this situation. P-16a matrix column or P-16a pair trace. |
| P-16b | Notify then Allow | pass-B-blind-spot | Part A retains an additional outcome under overlap or callback failure. P-16b matrix column or P-16b pair trace. → Q-09 |
| P-17a | NameRead then Notify | convergent | Agrees on the observable behavior for this situation. P-17a matrix column or P-17a pair trace. |
| P-17b | Notify then NameRead | convergent | Agrees on the observable behavior for this situation. P-17b matrix column or P-17b pair trace. |
| P-18a | CountsRead then Execute | convergent | Agrees on the observable behavior for this situation. P-18a matrix column or P-18a pair trace. |
| P-18b | Execute then CountsRead | convergent | Agrees on the observable behavior for this situation. P-18b matrix column or P-18b pair trace. |
| P-19a | CountsRead then Allow | convergent | Agrees on the observable behavior for this situation. P-19a matrix column or P-19a pair trace. |
| P-19b | Allow then CountsRead | divergence | Blind row contradicts itself. Requests already incremented before Allow returns, even though success or failure isn't counted yet. P-19b matrix column or P-19b pair trace. → Q-02 |
| P-20a | CountsRead then Notify | convergent | Agrees on the observable behavior for this situation. P-20a matrix column or P-20a pair trace. |
| P-20b | Notify then CountsRead | pass-B-blind-spot | Part A retains an additional outcome under overlap or callback failure. P-20b matrix column or P-20b pair trace. → Q-09 |
| P-21a | StateRead then TripPolicy | convergent | Agrees on the observable behavior for this situation. P-21a matrix column or P-21a pair trace. |
| P-21b | TripPolicy then StateRead | pass-B-blind-spot | Part A retains an additional outcome under overlap or callback failure. P-21b matrix column or P-21b pair trace. → Q-09 |
| P-22a | CountsRead then TripPolicy | convergent | Agrees on the observable behavior for this situation. P-22a matrix column or P-22a pair trace. |
| P-22b | TripPolicy then CountsRead | pass-B-blind-spot | Part A retains an additional outcome under overlap or callback failure. P-22b matrix column or P-22b pair trace. → Q-09 |
| P-23a | Execute then Notify | convergent | Agrees on the observable behavior for this situation. P-23a matrix column or P-23a pair trace. |
| P-23b | Notify then Execute | pass-B-blind-spot | Part A retains an additional outcome under overlap or callback failure. P-23b matrix column or P-23b pair trace. → Q-15 |
| P-24a | Report then Notify | convergent | Agrees on the observable behavior for this situation. P-24a matrix column or P-24a pair trace. |
| P-24b | Notify then Report | pass-B-blind-spot | Part A retains an additional outcome under overlap or callback failure. P-24b matrix column or P-24b pair trace. → Q-05 |
| P-25a | RequestReturn then Notify | divergence | Expected handling or ordering differs from the cited execution. P-25a matrix column or P-25a pair trace. → Q-05 |
| P-25b | Notify then RequestReturn | divergence | Raw return and classifier can both happen while Notify holds the mutex. P-25b matrix column or P-25b pair trace. → Q-05 |
| P-26a | Classify then TripPolicy | convergent | Agrees on the observable behavior for this situation. P-26a matrix column or P-26a pair trace. |
| P-26b | TripPolicy then Classify | divergence | Expected handling or ordering differs from the cited execution. P-26b matrix column or P-26b pair trace. → Q-05 |
| P-27a | RequestReturn then TripPolicy | divergence | Expected handling or ordering differs from the cited execution. P-27a matrix column or P-27a pair trace. → Q-05 |
| P-27b | TripPolicy then RequestReturn | divergence | Expected handling or ordering differs from the cited execution. P-27b matrix column or P-27b pair trace. → Q-05 |
| P-28a | Report then TripPolicy | convergent | Agrees on the observable behavior for this situation. P-28a matrix column or P-28a pair trace. |
| P-28b | TripPolicy then Report | convergent | Agrees on the observable behavior for this situation. P-28b matrix column or P-28b pair trace. |

Classified 178 situations. artefact 1, convergent 86, convergent-hole 32, divergence 51, pass-B-blind-spot 8.

## Vocabulary drift

- Execute — Open, `Timeout` not yet elapsed. vocabulary-drift `reject (ErrOpenState)`. Maps to reject when it describes a declared error/diagnostic.
- Execute — Open, `Timeout` elapsed. vocabulary-drift `transition → HalfOpen then handle`. The named transition is the first lifecycle effect; the later operation is a separate handling phase.
- Execute — HalfOpen, admitted-request count equals/exceeds `MaxRequests`. vocabulary-drift `reject (ErrTooManyRequests)`. Maps to reject when it describes a declared error/diagnostic.
- Execute — Nil request function supplied. vocabulary-drift `reject (declared refusal: nil-argument diagnostic)`. Maps to reject when it describes a declared error/diagnostic. Q-08.
- Execute — Zero-value or wrong receiver used. vocabulary-drift `reject (declared refusal: invalid-receiver diagnostic)`. Maps to reject when it describes a declared error/diagnostic. Q-08.
- Allow — Closed failure at completion with `ReadyToTrip` true. vocabulary-drift `transition → Open via later Report`. The named transition is the first lifecycle effect; the later operation is a separate handling phase.
- Allow — Open, `Timeout` not elapsed. vocabulary-drift `reject (ErrOpenState)`. Maps to reject when it describes a declared error/diagnostic.
- Allow — Open, `Timeout` elapsed. vocabulary-drift `transition → HalfOpen then handle`. The named transition is the first lifecycle effect; the later operation is a separate handling phase.
- Allow — HalfOpen, budget exhausted. vocabulary-drift `reject (ErrTooManyRequests)`. Maps to reject when it describes a declared error/diagnostic.
- NameRead — Zero-value breaker. vocabulary-drift `handle/reject`. No unique mapping; retain the question on the situation. Q-08.
- Report — Second invocation on the same callback (duplicate). vocabulary-drift `reject (declared refusal)`. Maps to reject when it describes a declared error/diagnostic. Q-03.
- Report — Concurrent success and failure on the same callback. vocabulary-drift `reject / one wins, other refused`. No unique mapping; retain the question on the situation. Q-03.
- TripPolicy — Reenters with the same breaker lock held (synchronous callback). vocabulary-drift `reject/UNSPECIFIED`. No unique mapping; retain the question on the situation. Q-09.
- Notify — Callback panics. vocabulary-drift `handle/UNSPECIFIED`. No unique mapping; retain the question on the situation. Q-10.
- Notify — Fires repeatedly for same transition (duplicate). vocabulary-drift `ignore (accidental)/reject`. No unique mapping; retain the question on the situation. Q-13.
- UV-04 — Admission delivered after withdrawal of demand. vocabulary-drift `reject (ErrOpenState / ErrTooManyRequests)`. Maps to reject when it describes a declared error/diagnostic. Q-06.
- UV-04 — Admission delivered against replacement breaker. vocabulary-drift `reject (invalid-receiver refusal)`. Maps to reject when it describes a declared error/diagnostic. Q-08.
- UV-07 — Wrong receiver / zero-value receiver. vocabulary-drift `reject (declared refusal)`. Maps to reject when it describes a declared error/diagnostic. Q-08.
- UV-11 — Same success or failure repeated on one callback. vocabulary-drift `reject (declared refusal)`. Maps to reject when it describes a declared error/diagnostic. Q-03.
- UV-12 — Success and failure on same callback concurrently. vocabulary-drift `reject / one wins`. No unique mapping; retain the question on the situation. Q-03.
- UV-14 — Report for another request transferred to this callback. vocabulary-drift `reject (declared refusal)`. Maps to reject when it describes a declared error/diagnostic. Q-13.
