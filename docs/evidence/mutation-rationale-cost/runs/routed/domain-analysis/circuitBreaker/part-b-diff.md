# Part B comparison

Coverage passed for 35 event IDs and all 30 pair-ordering IDs from 15 pairs. The table contains distinct explicit situations for repeated IDs, and the checklist ticks each ID once. The raw answer was retained. The package included prepared README prose, verbatim event contract comments and the stripped catalogue. The pack reported no kept or removed analysis IDs in the registered families. No implementation code was present.

The disclosed implementation observations limit independence. Configure allocation and normalization, Execute admission and result ownership, Allow callback binding, ReportSuccess/ReportFailure generation binding, the stale-accounting path in RequestResult and ApplySuccess/ApplyFailure, passive Counts, lazy expiry, inline notification and policy, no timer/cancellation, and missing uniqueness or single-shot guards appeared in the catalogue or annotations. Agreement on those points is treated as implementation-fed. The coverage tool flagged 15 rows containing as-is markers; an additional marker in a row's body likewise limits independence. A convergent-hole denotes an independently recognized intent gap only where cited requirements or contracts are missing a rule and the catalogue did not already give the conclusion.

Vocabulary-drift is recorded separately in the notes. The raw disposition `as-is:` is a provenance qualifier and has no vocabulary meaning on its own. Rows below map it only where the behavioral description identifies a concrete effect. Ambiguous receiver cases retain Q-08. A self-transition described as stays maps to handle. The distinction between queuing and a future call taking a fresh sample affects behavior and is a divergence.

| ID | Situation | Blind disposition | Class | Comparison and question |
|---|---|---|---|---|
| Configure | Valid settings, new instance intended | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| Configure | Zero-valued optional fields | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| Configure | Negative durations supplied | as-is: | convergent | vocabulary-drift. Normalizes durations to defaults; phrase accepts as typed means accepted input, not retained duration (Q-17). |
| Configure | Second construction when one instance intended | ignore (documented) | divergence | Second construction allocates a distinct instance (Q-16). |
| Execute | Closed, within Interval, request admitted | transition → Closed (stays) | convergent | vocabulary-drift. Self-target staying means handle (Q-15). |
| Execute | Open, before Timeout elapsed | reject | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| Execute | Open, Timeout elapsed (expiry observed) | transition → HalfOpen | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| Execute | HalfOpen, admitted requests < MaxRequests | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| Execute | HalfOpen, admitted requests ≥ MaxRequests | reject | pass-B-blind-spot | Instant wording misses mutex delay (Q-06). |
| Execute | Request panics | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| Execute | Nil request function / nil or unconstructed receiver | as-is: | convergent | vocabulary-drift. Runtime fault means handle crash when applicable (Q-08). |
| Allow | Closed, within Interval | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| Allow | Open, before Timeout | reject | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| Allow | Open, Timeout elapsed | transition → HalfOpen | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| Allow | HalfOpen, below MaxRequests | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| Allow | HalfOpen, at/over MaxRequests | reject | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ReportSuccess | Generation current, Closed, success counted | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ReportSuccess | HalfOpen, first successes reach threshold | transition → Closed | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ReportSuccess | Stale generation (rollover/expiry) | ignore (documented) | pass-B-blind-spot | Stale accounting alone is discarded; expiry may still run (Q-09). |
| ReportFailure | Generation current, Closed, ReadyToTrip false | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ReportFailure | Generation current, Closed, ReadyToTrip true | transition → Open | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ReportFailure | HalfOpen | transition → Open | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ReportFailure | Stale generation | ignore (documented) | pass-B-blind-spot | Stale accounting alone is discarded; expiry may still run (Q-09). |
| ReadState | Any state, non-expired Open | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ReadState | Open, expiry sampled equal/after deadline | transition → HalfOpen | divergence | Equality stays Open (Q-05). |
| ReadState | Nil/unconstructed receiver | as-is: | convergent | vocabulary-drift. Nil receiver crashes; zero-value CircuitBreaker.State can return Closed (Q-08). |
| ReadCounts | Any state | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ReadCounts | Cross-method snapshot not atomic with ReadState | ignore (documented) | divergence | Independent snapshots are observed, no documented atomicity contract or ignored call (Q-19). |
| ReadName | Any state | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ReadName | Nil receiver | as-is: | convergent | vocabulary-drift. Nil receiver crashes (Q-08). |
| RequestResult | Returns value/error normally | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| RequestResult | Returns after generation rollover | ignore (documented) | pass-B-blind-spot | Accounting is skipped but classifier and raw return still occur (Q-09). |
| RequestResult | Never returns / goroutine exits | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-04). |
| Classify | IsSuccessful nil | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| Classify | IsSuccessful returns a Boolean | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| Classify | Classifier panics/blocks/exits | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-07). |
| Classify | Re-enters breaker before committing | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-13). |
| TripDecision | ReadyToTrip nil | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| TripDecision | Returns true | transition → Open | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| TripDecision | Returns false | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| TripDecision | Policy panics/blocks/re-enters | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-02). |
| Notify | OnStateChange nil | ignore (documented) | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| Notify | Non-nil, state changed | handle | divergence | Hook receives name plus previous and new state (Q-18). |
| Notify | Observer panics/blocks/re-enters | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-01). |
| Notify | Repeated same-named transitions across cycles/instances | as-is: | convergent | vocabulary-drift. Repeated name payload maps to handle, dedup is open (Q-18). |
| ObserveExpiry | Open, now < expiry | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ObserveExpiry | Open, now ≥ expiry | transition → HalfOpen | divergence | Equality does not advance (Q-05). |
| ObserveExpiry | No qualifying call at deadline | defer (queued) | divergence | No queued event; a fresh call samples time (Q-05). |
| ApplySuccess | Generation matches, HalfOpen threshold reached | transition → Closed | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ApplySuccess | Generation mismatched | ignore (documented) | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ApplyFailure | Generation matches, Closed, ReadyToTrip true | transition → Open | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ApplyFailure | Generation matches, HalfOpen | transition → Open | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| ApplyFailure | Generation mismatched | ignore (documented) | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| UV-01 | Request never returns or goroutine exits | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-04). |
| UV-01 | Request panics | handle | pass-B-blind-spot | Request re-panic can be replaced during accounting (Q-07). |
| UV-01 | Submitter abandons interest | ignore (documented) | divergence | Caller departure alone has no ignore policy or slot cleanup (Q-04). |
| UV-02 | Slow completion after deadline elapsed | handle | convergent-hole | The blind pass flags the same intent gap. (Q-09). |
| UV-02 | Overlapping later request while first pending | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| UV-03 | Second Execute while first pending | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| UV-03 | Execute after return, caller still owns result | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| UV-04 | Nil request function | as-is: | convergent | vocabulary-drift. Nil Execute is a crash only if admitted (Q-08). |
| UV-04 | Call on wrong valid breaker | as-is: | convergent | vocabulary-drift. Valid wrong receiver uses ordinary handle or refusal (Q-08). |
| UV-04 | Nil/unconstructed receiver | as-is: | convergent | vocabulary-drift. Receiver mode and method decide crash versus return (Q-08). |
| UV-05 | Allow arrives late (after Timeout) | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| UV-05 | Caller stops before/during submission | defer (queued) | divergence | No queue; before admission no budget is consumed (Q-04). |
| UV-05 | Caller stops after receiving callback | ignore (documented) | divergence | Callback omission has no documented disposal (Q-04). |
| UV-06 | Second Allow before first returns | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| UV-06 | Second Allow after first while callback held | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| UV-07 | Report omitted after accepted trial | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-04). |
| UV-08 | Outcome after generation rollover | ignore (documented) | pass-B-blind-spot | Expiry may still run (Q-09). |
| UV-08 | Outcome after expiry/state change | ignore (documented) | pass-B-blind-spot | Promotion can be caused by stale report (Q-09). |
| UV-08 | Outcome after application cancellation | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| UV-09 | Same completion repeated sequentially | ignore (documented) | divergence | Duplicate current-generation report can count or close early (Q-03). |
| UV-09 | Contradictory Booleans concurrently | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-03). |
| UV-10 | Completion without admission | reject | divergence | Nil invocation panics without a refusal signal at invocation; a valid closure can report without work (Q-18). |
| UV-10 | Invoking nil callback | as-is: | convergent | vocabulary-drift. Nil invocation maps to handle crash (Q-18). |
| UV-11 | Wrong Boolean reported | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| UV-11 | Callback reused for another request | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| UV-11 | Misleading ReadyToTrip ratio | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| UV-12 | Repeated / late / interleaved reads | handle | pass-B-blind-spot | State may mutate generation or transition while reading (Q-19). |
| UV-13 | Classifier panics | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-07). |
| UV-13 | Classifier blocks | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-04). |
| UV-14 | Classification finishes after generation change | ignore (documented) | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| UV-14 | Classifier re-enters breaker | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-13). |
| UV-15 | Policy panics/blocks/exits/re-enters | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-02). |
| UV-16 | Observer absent | ignore (documented) | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| UV-16 | Observer panics/blocks/exits/re-enters | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-01). |
| UV-17 | Repeated same-named transitions | as-is: | convergent | vocabulary-drift. Duplicate-looking notification maps to handle; ownership unresolved (Q-18). |
| UV-17 | Unsolicited invocation outside breaker | ignore (documented) | pass-B-blind-spot | External invocation is outside the breaker call path, no ignore handler (Q-18). |
| UV-18 | Equality at deadline | transition → HalfOpen | divergence | Equality stays (Q-05). |
| UV-18 | Deadline elapses without qualifying call | defer (queued) | divergence | No queued timer event (Q-05). |
| UV-18 | Clock differs from intended schedule | UNSPECIFIED | convergent-hole | The blind pass flags the same intent gap. (Q-05). |
| UV-20 | Construction omitted | as-is: | convergent | vocabulary-drift. Omitting construction leads to different behavior depending on receiver and method (Q-08). |
| UV-20 | Two calls to constructor when one intended | ignore (documented) | divergence | Second constructor allocates (Q-16). |
| UV-21 | Negative durations | as-is: | convergent | vocabulary-drift. Normalization is a handle path (Q-17). |
| UV-21 | Large request limit/interval/timeout | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-01a | Execute → ReadState near expiry | handle | pass-B-blind-spot | State can run after admission but before result (Q-05). |
| P-01b | ReadState → Execute | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-02a | Execute → ReadCounts | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-02b | ReadCounts → Execute | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-03a | Allow → ReportSuccess | handle | pass-B-blind-spot | At full capacity first Allow rejects (Q-10). |
| P-03b | ReportSuccess → Allow | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-04a | Allow → ReportFailure | handle | pass-B-blind-spot | New Allow can fail before older trial reopens (Q-10). |
| P-04b | ReportFailure → Allow | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-05a | ReportSuccess → ReadState | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-05b | ReadState → ReportSuccess | handle | pass-B-blind-spot | Expiry before report can invalidate it (Q-09). |
| P-06a | ReportFailure → ReadState | handle | divergence | Old report can advance expired Open to HalfOpen; a matched failure opens (Q-09). |
| P-06b | ReadState → ReportFailure | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-07a | ReportSuccess → ReadCounts | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-07b | ReadCounts → ReportSuccess | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-08a | ReportFailure → ReadCounts | handle | divergence | If failure trips, fresh Counts is cleared and omits failure (Q-19). |
| P-08b | ReadCounts → ReportFailure | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-09a | ReadState → ReadCounts near expiry | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-09b | ReadCounts → ReadState | handle | pass-B-blind-spot | Snapshot independence is observed (Q-19). |
| P-10a | RequestResult → ReadState | handle | divergence | Raw return can precede completion lock; reader can observe old state (Q-13). |
| P-10b | ReadState → RequestResult | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-11a | Classify → ReadState | handle | divergence | Classifier return is before accounting and can race a reset (Q-09). |
| P-11b | ReadState → Classify | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-12a | Allow → ReadState at expiry | handle | pass-B-blind-spot | Admission hinges on hook returning after commit (Q-07). |
| P-12b | ReadState → Allow | handle | pass-B-blind-spot | Reader can panic while committing half-open; later Allow can admit (Q-07). |
| P-13a | Allow → ReadCounts | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-13b | ReadCounts → Allow | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-14a | ReportSuccess → ReportFailure | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
| P-14b | ReportFailure → ReportSuccess | handle | divergence | Failure first reopens and makes earlier-generation success stale (Q-10). |
| P-15a | TripDecision → ReadState | handle | pass-B-blind-spot | External reader waits and reentrant reader blocks (Q-02). |
| P-15b | ReadState → TripDecision | handle | convergent | Agrees for the named condition; scope and citations are in the corresponding matrix cell or pair trace. |
