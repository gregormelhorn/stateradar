# Independent Part B comparison

DeepSeek Flash received only the inspected package in log 059. Coverage passed for 35 events and 32 pair orderings, corresponding to 16 pairs. All 95 situation rows are classified. Repeated IDs have distinct explicit Situation cells. The pack reported no kept or stripped analysis IDs. The prepared requirements contained verbatim README prose. No implementation fragment was sent.

The observed-in-code sections disclosed private handoff, queue and counter retention, callback locks and detached idle drain. No returned row used the `as-is:` marker. Agreement relying on these observations is not independent. Relevant rows include Put's queued delivery, WaitDelivery's registered waiter, UV-GetAgain, UV-AbandonGet, UV-LateRead, P-01a, P-09a and P-10a. Rows with agreement below preserve their requirement scope; a proposed condition does not become a guarantee.

| ID | Blind situation | Classification | Reviewed comparison | Question |
|---|---|---|---|---|
| New | Valid capacities (InitialCap ≤ MaxIdle ≤ MaxActive), all three callbacks present, non-negative idle time | pass-B-blind-spot | Construction matches broadly; optional Ping and callback failures need separate cases. | — |
| New | Callbacks absent or capacities contradictory (e.g. MaxIdle > MaxActive, negative idle time) | divergence | vocabulary-drift: reject (declared error/diagnostic). Maps to reject. Nil configuration panics. Zero capacity and negative timeout are accepted. Ping is optional. | Q-12 |
| New | InitialCap = 0 (empty start) with valid bounds | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| Get | Pool_Ready, idle resources available, no ping configured | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| Get | Pool_Ready, idle resources available, ping configured | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| Get | Pool_Ready, no idle resource, live count < MaxActive | divergence | Factory panic escapes and can strand its lock. Nil success is accepted. Cleanup of a value accompanying error is absent. | Q-09 |
| Get | Pool_Ready, live count = MaxActive (pool full) | divergence | vocabulary-drift: handle (waits). Maps to defer (queued). Release does not settle private waiters. Stale Get can queue or complete, and detached dynamic Factory completion is excluded by the lock. | Q-01 |
| Get | Pool_Closed | convergent | vocabulary-drift: reject (declared error). Maps to reject. Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| Get | IdleAge evaluation during Get | artefact | Configured deadline is IdleTimeout (duration). MaxIdle limits count. | Q-17 |
| Put | Pool_Ready, resource was checked out from this pool, idle capacity < MaxIdle, waiter queued | pass-B-blind-spot | vocabulary-drift: transition → WaitDelivery (hand off). Maps to transition (handoff phase). Handoff irrespective of buffer space. | — |
| Put | Pool_Ready, resource valid, idle capacity < MaxIdle, no waiter | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| Put | Pool_Ready, idle capacity = MaxIdle (idle full) | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| Put | Pool_Closed / released | divergence | Released Close skips the callback. Checked-out values are absent from detached idle drain. | Q-05 |
| Close | Resource was checked out and is being destroyed | divergence | Close decrements before outcome and does not wake waiters. | Q-03 |
| Close | Resource already idle/in pool | divergence | vocabulary-drift: reject (declared error) or ignore (documented). Alternative dispositions are ambiguous. Duplicate, closed or wrong-pool non-nil values pass the local guard. Close does not unlink idle entries. | Q-11 |
| Close | Resource nil / unknown / stale | divergence | vocabulary-drift: reject (declared error). Maps to reject. Duplicate, closed or wrong-pool non-nil values pass the local guard. Close does not unlink idle entries. | Q-11 |
| Release | Pool_Ready (or Pool_Ready_Empty), no in-flight | divergence | vocabulary-drift: transition → Pool_Releasing → Pool_Released. Maps to transition (handoff phase). Release does not settle private waiters. Stale Get can queue or complete, and detached dynamic Factory completion is excluded by the lock. | Q-01 |
| Release | Pool_Releasing (already in progress) | divergence | vocabulary-drift: ignore (documented) or defer. Alternative dispositions are ambiguous. Repeat Release can return before drain completes. Idempotent detachment is observed in code. | Q-15 |
| Release | Pool_Released | divergence | Repeat Release can return before drain completes. Idempotent detachment is observed in code. | Q-15 |
| Len | Pool_Ready / Pool_Ready_Empty | divergence | Len samples idle occupancy. Close decrements the accounting counter only. | Q-14 |
| Len | Pool_Releasing / Pool_Released | pass-B-blind-spot | Fresh Len is exactly zero even before drain completes. | — |
| DirectPing | Concrete value exposes Ping, Pool_Ready | divergence | Concrete Ping exists independent of configuration. It returns the callback result without discarding and can panic when missing. | Q-13 |
| DirectPing | Callback absent (structural assertion fails) | divergence | vocabulary-drift: reject (declared error). Maps to reject. Concrete Ping exists independent of configuration. It returns the callback result without discarding and can panic when missing. | Q-13 |
| FactoryResult | Success value | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| FactoryResult | Error value | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| FactoryResult | nil value or value with error | divergence | Factory panic escapes and can strand its lock. Nil success is accepted. Cleanup of a value accompanying error is absent. | Q-09 |
| FactoryResult | Panic | divergence | Factory panic escapes and can strand its lock. Nil success is accepted. Cleanup of a value accompanying error is absent. | Q-09 |
| CloseResult | Success | pass-B-blind-spot | Decrement precedes callback, and no request is notified. | — |
| CloseResult | Error | divergence | Close decrements before outcome. Error propagation depends on call site. Panic escapes or aborts drain. | Q-10 |
| CloseResult | Panic | divergence | Close decrements before outcome. Error propagation depends on call site. Panic escapes or aborts drain. | Q-10 |
| PingResult | Valid | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| PingResult | Invalid | pass-B-blind-spot | Invalid buffering path found; callback scope differs for new and handed-off values. | — |
| PingResult | Error / panic | divergence | Entered Ping can complete across teardown. Returned error and panic have different effects. | Q-06 |
| IdleAge | Within MaxIdle | artefact | Configured deadline is IdleTimeout (duration). MaxIdle limits count. | Q-17 |
| IdleAge | Exceeds MaxIdle | artefact | Configured deadline is IdleTimeout (duration). MaxIdle limits count. | Q-17 |
| IdleAge | Negative or invalid config | divergence | vocabulary-drift: reject (declaration at New). Maps to reject. Nil configuration panics. Zero capacity and negative timeout are accepted. Ping is optional. | Q-12 |
| WaitDelivery | Registered waiter present, resource ready | convergent | vocabulary-drift: handle (delivers). Maps to handle. Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| WaitDelivery | Requester abandoned / no waiter | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| WaitDelivery | Pool released while delivering | divergence | Release does not settle private waiters. Stale Get can queue or complete, and detached dynamic Factory completion is excluded by the lock. | Q-01 |
| DrainDone | After detachment, all idle closed | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| DrainDone | Close error during drain | divergence | Close decrements before outcome. Error propagation depends on call site. Panic escapes or aborts drain. | Q-10 |
| UV-NewOmitted | Pool never constructed | convergent-hole | No construction occurs. | Q-19 |
| UV-NewRepeated | Second New against same backend | convergent | vocabulary-drift: handle (independent). Maps to handle. Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| UV-BadConfig | Nil config, negative/zero invalid cap, absent callbacks | divergence | vocabulary-drift: reject (declared error). Maps to reject. Nil configuration panics. Zero capacity and negative timeout are accepted. Ping is optional. | Q-12 |
| UV-GetOmitted | No Get issued | convergent-hole | No Get work originates. | Q-19 |
| UV-GetAgain | Second Get by same caller while first pending/held | divergence | Separate duplicate caller orders and fairness after capacity changes remain open. | Q-16 |
| UV-AbandonGet | Caller abandons waiter | convergent-hole | Both identify no cancellation and possible abandoned handoff. Documented intent is unproved. | Q-04 |
| UV-LateGet | Get during/after Release | divergence | vocabulary-drift: reject (declared error). Maps to reject. Release does not settle private waiters. Stale Get can queue or complete, and detached dynamic Factory completion is excluded by the lock. | Q-01 |
| UV-ContendedGet | Put/Close changes availability between failed receive and decision | divergence | At cap the failed observation can lead to a parked request beside an idle value. Below cap it can create unnecessarily. | Q-02 |
| UV-WrongPoolGet | Get to wrong pool | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| UV-ReturnMissing | Resource never returned | convergent-hole | Checkout can remain unreturned. | Q-19 |
| UV-LatePut | Put during/after Release or after requester departure | divergence | Released Close skips the callback. Checked-out values are absent from detached idle drain. | Q-05 |
| UV-LateClose | Close after Release or after Put selected overflow cleanup | divergence | Duplicate, closed or wrong-pool non-nil values pass the local guard. Close does not unlink idle entries. | Q-11 |
| UV-BadOwnership | Duplicate Put/Close, nil, typed nil, foreign resource | divergence | vocabulary-drift: reject (declared error). Maps to reject. Duplicate, closed or wrong-pool non-nil values pass the local guard. Close does not unlink idle entries. | Q-11 |
| UV-WrongPoolPut | Put/Close to wrong pool | divergence | vocabulary-drift: reject (declared error). Maps to reject. Duplicate, closed or wrong-pool non-nil values pass the local guard. Close does not unlink idle entries. | Q-11 |
| UV-ReleaseOmitted | No Release | convergent-hole | No automatic release. | Q-19 |
| UV-ReleaseAgain | Repeat Release | divergence | Repeat Release can return before drain completes. Idempotent detachment is observed in code. | Q-15 |
| UV-WrongPoolRelease | Release wrong instance | convergent | vocabulary-drift: handle (that instance). Maps to handle. Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| UV-LateRead | Len during concurrent change or teardown | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| UV-FactoryFault | Factory error/panic/nil | divergence | Factory panic escapes and can strand its lock. Nil success is accepted. Cleanup of a value accompanying error is absent. | Q-09 |
| UV-CloseFault | Close error/panic during expiry/overflow/drain | divergence | Close decrements before outcome. Error propagation depends on call site. Panic escapes or aborts drain. | Q-10 |
| UV-PingFault | Absent Ping, invalid result, panic, overlap with Release | divergence | vocabulary-drift: reject (invalid → discard). Maps to reject. Entered Ping can complete across teardown. Returned error and panic have different effects. | Q-06 |
| UV-CallbackDelay | Callback stalls/re-enters Get/Put/Close/Release/Len | convergent-hole | Contract is silent. Source shows callback reentry can deadlock. | Q-08 |
| P-01a | Get → Put same holder | divergence | At cap the failed observation can lead to a parked request beside an idle value. Below cap it can create unnecessarily. | Q-02 |
| P-01b | Put → Get | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| P-02a | Get → Close same resource | pass-B-blind-spot | Later caller can create before an older waiter. | — |
| P-02b | Close → Get | divergence | vocabulary-drift: reject (Close on pooled) / handle (Get). Alternative dispositions are ambiguous. Duplicate, closed or wrong-pool non-nil values pass the local guard. Close does not unlink idle entries. | Q-11 |
| P-03a | Get → Release | divergence | Release does not settle private waiters. Stale Get can queue or complete, and detached dynamic Factory completion is excluded by the lock. | Q-01 |
| P-03b | Release → Get | convergent | vocabulary-drift: reject (ErrClosed). Maps to reject. Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| P-04a | Put → Release | pass-B-blind-spot | Can also hand off, race an old receive, or overflow. | — |
| P-04b | Release → Put | divergence | Released Close skips the callback. Checked-out values are absent from detached idle drain. | Q-05 |
| P-05a | Close → Release | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| P-05b | Release → Close | divergence | Released Close skips the callback. Checked-out values are absent from detached idle drain. | Q-05 |
| P-06a | Len → Release | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| P-06b | Release → Len | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| P-07a | Put → Close same resource, distinct actors | divergence | vocabulary-drift: reject (documented ordering conflict). Maps to reject. Duplicate, closed or wrong-pool non-nil values pass the local guard. Close does not unlink idle entries. | Q-11 |
| P-07b | Close → Put | divergence | Duplicate, closed or wrong-pool non-nil values pass the local guard. Close does not unlink idle entries. | Q-11 |
| P-08a | PingResult → Release | pass-B-blind-spot | Failed Ping can skip cleanup if Release wins before Close. | — |
| P-08b | Release → PingResult | divergence | Entered Ping can complete across teardown. Returned error and panic have different effects. | Q-06 |
| P-09a | FactoryResult → Release | divergence | Released Close skips the callback. Checked-out values are absent from detached idle drain. | Q-05 |
| P-09b | Release → FactoryResult | divergence | Release does not settle private waiters. Stale Get can queue or complete, and detached dynamic Factory completion is excluded by the lock. | Q-01 |
| P-10a | CloseResult → Release | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| P-10b | Release → CloseResult | pass-B-blind-spot | Drain drops returned errors and callback panic can stop it. | — |
| P-11a | Len → Put | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| P-11b | Put → Len | divergence | Len samples idle occupancy. Close decrements the accounting counter only. | Q-14 |
| P-12a | Len → Get | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| P-12b | Get → Len | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| P-13a | DirectPing → Release | convergent | Agrees for stated conditions with the corresponding matrix outcome or pair trace. Agreement uses the stated condition only. | — |
| P-13b | Release → DirectPing | divergence | Concrete Ping exists independent of configuration. It returns the callback result without discarding and can panic when missing. | Q-13 |
| P-14a | Len → Close | divergence | Len samples idle occupancy. Close decrements the accounting counter only. | Q-14 |
| P-14b | Close → Len | divergence | Len samples idle occupancy. Close decrements the accounting counter only. | Q-14 |
| P-15a | DirectPing → Put same resource | pass-B-blind-spot | Put has no access to Ping's verdict. | — |
| P-15b | Put → DirectPing | pass-B-blind-spot | Another borrower can consume the value before Ping returns. | — |
| P-16a | DirectPing → Close same resource | divergence | vocabulary-drift: reject (ordering conflict). Maps to reject. Direct Ping and Close have no resource ownership arbitration. | Q-22 |
| P-16b | Close → DirectPing | divergence | Direct Ping and Close have no resource ownership arbitration. | Q-22 |

Counts: pass-B-blind-spot 11, divergence 49, convergent 26, artefact 3, convergent-hole 6.

Feedback for a later pilot: when a catalogue contains independent limits over different units, explicitly name each parameter and unit. Blind readers conflated the age threshold and idle-entry count. The current catalogue clarification identifies parameters only. The historical package is retained unchanged.
