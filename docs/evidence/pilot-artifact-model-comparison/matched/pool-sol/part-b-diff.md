# Blind Part B comparison

DeepSeek Flash received the inspected three-input package only, with README prose copied verbatim and source comments copied as contracts. The initial short README section was refused before dispatch. The final package contained no implementation code. Checked all quote-parenthesis occurrences: they were kept README prose only. Contract headers carry source locations by design. No L/G/F/T identifiers reported kept or removed and no domain identifier loss. DOC references are doctrine IDs. Formal coverage passed for 36 events and 20 pair orderings, matching ten pairs in the catalogue. There are 101 situation rows, with distinct repeated-ID situations and one checklist occurrence per ID.

No returned row is marked `as-is:`. Read manually against the package: code-derived agreement is non-independent where it draws from gate/lock/remembrance prose. Reading by blind line, those dependencies are especially 7, 12–19, 21–24, 27–29, 33–35, 36–44, 47–52, 56, 58–60, 63–64, 66–69, 73–82, 84–88, 90, 92–94 and 96–103. In particular the unbounded FIFO, last-slot reference, nil callbacks, unreset count, outside-lock drain and capture, chronology of callback execution and timing of wrappers were visible in labelled catalogue fields. Familiar as-is descriptions in the main event table also disclose synchronous callback delivery, the IdleCheck sampling at acquisition, no caller identity for second Get, and missing queue deadline. Those are known leaks, especially affecting 11–12, 40–47, 53–56, 63–64, 73–78 and 83. Rows calling those outcomes “documented” do not create intent evidence.

Vocabulary drift (rows classified exactly once below):
- 28: vocabulary-drift. Conditional reject/handle is mapped to reject for stated typed nil and handle for foreign; actual handles both on a live pool.
- 48: vocabulary-drift. Qualified reject maps to reject for the named condition; its behaviour cell instead describes handle, so the row is internally ambiguous.
- 57: vocabulary-drift. Qualified reject maps to reject for the stated condition.
- 70: vocabulary-drift. Conditional reject/handle maps to reject after cutoff and handle earlier.
- 71: vocabulary-drift. Conditional reject/handle maps to reject for typed nil and handle otherwise.
- 76: vocabulary-drift. Conditional reject/handle maps to reject for nil outcomes and handle other success.

| Blind line | ID | Situation | Classification | Comparison |
|---|---|---|---|---|
| 3 | New | Valid config, pool not yet alive | convergent | Pool_Ready maps to the first published Open state. New on a separate receiver is handle at receiver level. |
| 4 | New | Config invalid (nil/invalid bounds/zero capacity/absent callbacks/nonpositive timeout) | divergence | Nil config panics; zero limits and nonpositive idle timeout pass; invalid bounds and absent mandatory callbacks have config errors, not the max sentinel. Reasoned fold into Q-13. |
| 5 | New | Second New with independent instance / same config | convergent | Separate construction leaves old receiver alone. |
| 6 | Get | Pool_Ready, idle resource available and valid | convergent | Buffered validation and retry align, within ordinary serial acquisition. |
| 7 | Get | Pool_Ready, below max active, idle empty | convergent | Live creation below cap commits only after success. |
| 8 | Get | Pool_Ready, at max concurrent, waiters allowed | divergence | Put hands off, whereas Close only changes admission count and does not wake. Reasoned fold into Q-03. |
| 9 | Get | Pool_Ready, at max concurrent, no wait capacity | divergence | No queue cap and no reachable close of the private channel to emit the sentinel. Reasoned fold into Q-01. |
| 10 | Get | after Release (UV-AfterRelease) | convergent | Fresh Get snapshots nil and rejects. |
| 11 | Get | caller abandons result / no Put (UV-Abandon) | divergence | Abandonment is unobserved; a subsequent Put can commit into abandoned caller work. Reasoned fold into Q-05. |
| 12 | Get | second Get while first awaits or holds (UV-GetAgain) | convergent | Both acquisition orders independent. Handle includes queueing under the stated admission gates. |
| 13 | Get | overlapping concurrent Gets (UV-Overlap) | divergence | Mutex admission does not recheck the channel. At-cap miss race permits queued and idle together. Reasoned fold into Q-04. |
| 14 | Get | unsolicited Get without app reason (UV-Unsolicited) | convergent | No application reason input. |
| 15 | Get | wrong receiver pool (UV-WrongPool) | convergent | Receiver-local selection. |
| 16 | Put | Pool_Ready, empty interface nil | convergent | Nil-interface reject branch. |
| 17 | Put | Pool_Ready, waiter waiting | convergent | Handoff matches; matrix transition when last waiter leaves. |
| 18 | Put | Pool_Ready, room in idle buffer | convergent | Timestamp and idle buffer match. |
| 19 | Put | Pool_Ready, idle buffer full | convergent | Disposition matches; overflow error policy itself remains open in Q-10. |
| 20 | Put | after Release (UV-LateResource) | divergence | Nonnil return reports nil without disposal. Reasoned fold into Q-07. |
| 21 | Put | duplicate Put of same resource (UV-DuplicateResource) | convergent | Duplicate return can admit twice. |
| 22 | Put | foreign / mismatched / typed nil resource (UV-ForeignResource) | divergence | Only a nil interface rejects; typed nil can enter idle or handoff. Reasoned fold into Q-12. |
| 23 | Put | overlapping Put with Get/Close/Release (UV-Overlap) | divergence | Overflow unlock permits Release before Close and skips disposal. Reasoned fold into Q-07. |
| 24 | Close | Pool_Ready, valid resource, close callback set | convergent | A live callback is invoked after decrement, with physical effect callback-dependent. |
| 25 | Close | nil interface / close callback absent | divergence | An absent closer results in nil for a nonnil payload. Reasoned fold into Q-07. |
| 26 | Close | after Release (UV-LateResource) | divergence | The captured closer is private to Release drain. Reasoned fold into Q-07. |
| 27 | Close | duplicate Close / Close after Put for same resource (UV-DuplicateResource) | convergent | No revocation or duplicate detection. |
| 28 | Close | foreign / typed nil (UV-ForeignResource) | divergence | Typed-nil Close is invoked, subject to callback behavior. Reasoned fold into Q-12. |
| 29 | Close | overlapping with other calls (UV-Overlap) | convergent | Ordinary execution serializes guarded effects, reentry in Q-11. |
| 30 | Release | Pool_Ready/alive, first invocation | divergence | Fresh Get rejects, late Put/Close can report nil and competing operations retain old snapshots. Reasoned fold into Q-07. |
| 31 | Release | already released / during draining (UV-ReleaseAgain) | divergence | Repeated Release returns without refusal, even during earlier drain. Reasoned fold into Q-17. |
| 32 | Release | no prior New / never alive (UV-NoOwner) | divergence | A missing New is no call on a published receiver, and an omitted Release has no diagnostic. Reasoned fold into Q-19. |
| 33 | Release | late relative to work in flight (UV-OwnerLate) | convergent | Observed buffer-only drain and untouched waiters agree. Intent unresolved. |
| 34 | Release | overlapping construct/drain of another pool or overlapping calls (UV-OwnerOverlap) | convergent | Detach lifecycle and receiver isolation agree. |
| 35 | Release | wrong receiver (UV-WrongPool) | convergent | Actual receiver is detached. |
| 36 | Len | Pool_Ready | convergent | Depth projection agrees. README leaves precise count policy open. |
| 37 | Len | after Release | convergent | Fresh snapshot length zero. |
| 38 | Len | repeated / overlapping / late observation (UV-Observer) | divergence | Channel pointer is taken under lock; length is sampled afterward. Reasoned fold into Q-15. |
| 39 | Len | wrong receiver (UV-WrongPool) | convergent | Actual receiver is sampled. |
| 40 | Factory | success, acquisition phase | convergent | Success and increment align. |
| 41 | Factory | error, including value+error (UV-FactoryError) | divergence | On-demand error unchanged, startup formats error and rolls back earlier values. Reasoned fold into Q-13. |
| 42 | Factory | success but nil/typed nil/reused/foreign value (UV-FactoryValue) | divergence | Successful nil or typed-nil result is passed through. Reasoned fold into Q-13. |
| 43 | Factory | slow/blocked/reentrant during acquisition (UV-FactoryDelay) | divergence | Callback contract is silent and callback invoking a lock-taking method can self-deadlock. Reasoned fold into Q-11. |
| 44 | Factory | during construction (pre-publication) | convergent | Matches constructor before publication. |
| 45 | PingResult | healthy | convergent | Buffered validation success aligns. |
| 46 | PingResult | error (UV-PingError) | convergent | Ordinary pre-cutoff invalidation and retry align. |
| 47 | PingResult | slow/blocked/reentrant/overlapping release (UV-PingDelay) | divergence | Ping is reread unsafely, and cleanup after cutoff can be skipped. Reasoned fold into Q-08. |
| 48 | PingResult | verdict contradicts reality (UV-PingValue) | divergence | The prose says to trust verdict, but disposition asserts refusal for invalid-as-healthy. No validation can reject it. Reasoned fold into Q-21. |
| 49 | CloseResult | success | divergence | Only live Close decrements count. Drain bypasses accounting. Reasoned fold into Q-10. |
| 50 | CloseResult | error (UV-CloseError) | divergence | Overflow returns callback error and Release does not decrement. Reasoned fold into Q-10. |
| 51 | CloseResult | slow/blocked/reentrant in live or drain phase (UV-CloseDelay) | pass-B-blind-spot | Blind distinguishes lock phase but misses live Close reentry blocking the caller and owner. Q-11. |
| 52 | CloseResult | success with live resource / error after disposal (UV-CloseValue) | divergence | Drain leaves accounting unchanged; live Close has already decremented. Reasoned fold into Q-10. |
| 53 | IdleCheck | age below timeout | convergent | Below threshold proceeds. |
| 54 | IdleCheck | age equal to timeout | divergence | Strict Before accepts equality; intent about exact sampling around the boundary remains open. Reasoned fold into Q-14. |
| 55 | IdleCheck | age beyond timeout (UV-Aged) | convergent | Samples beyond timeout and attempts disposal. |
| 56 | IdleCheck | handoff delivery delayed by scheduling (UV-Aged) | convergent | Delayed handoff can exceed deadline. |
| 57 | UV-NoOwner | absence of New before use, or absence of Release | divergence | Missing lifecycle input produces no refusal. Prior construction is an application obligation. Reasoned fold into Q-19. |
| 58 | UV-OwnerLate | teardown delayed while caller work continues | convergent | Delayed owner teardown follows buffer-only drain. |
| 59 | UV-NewAgain | repeated/unsolicited construction same config | convergent | Separate instance per New. |
| 60 | UV-OwnerOverlap | teardown overlaps another construction / old work runs | convergent | Distinct receivers are independent. |
| 61 | UV-Config | nil/invalid/zero/absent/nonpositive | divergence | Zero limits and nonpositive timeout accepted; nil config panics. Reasoned fold into Q-13. |
| 62 | UV-Config | valid but unintended limits | convergent | Valid unintended parameters accepted as given. |
| 63 | UV-Abandon | Get result never Put / Put/Close omitted or delayed | divergence | Pending acquisition may receive a later Put via abandoned work, without cancellation. Reasoned fold into Q-05. |
| 64 | UV-GetAgain | second Get while first awaits or holds | convergent | Same-owner independent admission plus queue guard. |
| 65 | UV-AfterRelease | Get on released pool | convergent | Fresh call reliably ErrClosed. |
| 66 | UV-Overlap | overlapping Get/Put/Close/Release | divergence | Synchronized individual commits still allow mixed idle/pending state and later completion first. Reasoned fold into Q-04. |
| 67 | UV-Unsolicited | unsolicited Get | convergent | Admission uses same public path. |
| 68 | UV-WrongPool | call on unintended receiver | convergent | Receiver local operations. |
| 69 | UV-DuplicateResource | duplicate Put/Close or both | convergent | No ownership check. |
| 70 | UV-LateResource | Put/Close after release or before ownership completes | divergence | Post-detach nonnil Put and Close return nil without disposal. Reasoned fold into Q-07. |
| 71 | UV-ForeignResource | no matching checkout / foreign / typed nil / stale | divergence | Typed nil crosses the nil-interface check. Reasoned fold into Q-12. |
| 72 | UV-ReleaseAgain | second Release after detach or during drain | divergence | Repeat is a silent return. Reasoned fold into Q-17. |
| 73 | UV-Observer | late/repeated/unsolicited/overlapping Len | convergent | Observer has no mutating effect, with sampling qualification in Q-15. |
| 74 | UV-FactoryError | creation error incl. value+error | convergent | Factory error refuses acquisition, value discarded and live count unchanged. Startup error form expanded in Q-13. |
| 75 | UV-FactoryDelay | slow/blocked/panicking/reentrant creation | convergent-hole | Both record panic policy as unspecified. Code calls Factory while holding the mutex and panic can bypass unlock. Q-11. |
| 76 | UV-FactoryValue | nil/typed nil/reused/foreign with success | divergence | Nil and typed-nil successes passed through. Reasoned fold into Q-13. |
| 77 | UV-PingError | ping returns error | convergent | Ordinary pre-detach validation error retries. |
| 78 | UV-PingDelay | slow/blocked/panicking/reentrant/overlapping release | divergence | Missing Ping synchronization can panic and failure can skip cleanup. Reasoned fold into Q-08. |
| 79 | UV-PingValue | healthy reported invalid / invalid reported healthy | convergent | Decision consumes the supplied verdict. |
| 80 | UV-CloseError | error in direct/overflow/expiry/invalid cleanup/release drain | divergence | Direct and overflow errors surface; Release drain ignores error and count. Reasoned fold into Q-10. |
| 81 | UV-CloseDelay | slow/blocked/panicking/reentrant in live/drain | pass-B-blind-spot | Blind describes lock phase but misses interruption of drain and independent repeat completion. Q-17. |
| 82 | UV-CloseValue | success with live resource / error after disposing | divergence | Release drain leaves accounting unchanged. Reasoned fold into Q-10. |
| 83 | UV-Aged | below/equal/beyond timeout incl. delayed handoff | divergence | Strict Before accepts equality; time of handoff observation may be delayed. Reasoned fold into Q-14. |
| 84 | P-01a | Get → Put, same pool | pass-B-blind-spot | Blind misses the at-cap idle/wait coexistence and below-cap unnecessary creation windows. Q-04. |
| 85 | P-01b | Put → Get | convergent | A committed idle return can be consumed. |
| 86 | P-02a | Get → Close | divergence | An earlier Get at cap stays pending after Close and later callers can create first. Reasoned fold into Q-03. |
| 87 | P-02b | Close → Get | convergent | Count can affect later admission. |
| 88 | P-03a | Get → Release | divergence | A prior Get can remain queued indefinitely or enqueue after detach, rather than uniformly complete admission. Reasoned fold into Q-02. |
| 89 | P-03b | Release → Get | convergent | Fresh Get rejected after cutoff. |
| 90 | P-04a | Put → Release | divergence | Drain works for buffered Put; previous handoff still delivers and overflow cleanup can be skipped. Reasoned fold into Q-07. |
| 91 | P-04b | Release → Put | divergence | No refusal signal for nonnil late Put. Reasoned fold into Q-07. |
| 92 | P-05a | Close → Release | convergent | Live Close commits before the owner detaches. |
| 93 | P-05b | Release → Close | divergence | After detach public Close cannot invoke captured callback. Reasoned fold into Q-07. |
| 94 | P-06a | Len → Release | pass-B-blind-spot | Blind lacks snapshot-detach-length sampling window. Q-15. |
| 95 | P-06b | Release → Len | convergent | New Len snapshot is zero. |
| 96 | P-07a | Len → Get | convergent | Observation then acquisition has compatible effects. |
| 97 | P-07b | Get → Len | convergent | Len reflects resulting idle depth under serial ordering. |
| 98 | P-08a | Len → Put | convergent | Serial observation and return match. |
| 99 | P-08b | Put → Len | convergent | Ordinary return yields matching depth. |
| 100 | P-09a | Len → Close | convergent | Held resource disposal independent of idle length. |
| 101 | P-09b | Close → Len | convergent | Direct Close does not remove idle entries. |
| 102 | P-10a | Put → Close, independently acting holders/cleanup agents | convergent | Two operations can dispose the same value. |
| 103 | P-10b | Close → Put | convergent | Put can reintroduce a closed value. |

Counts: convergent 55, divergence 41, pass-B-blind-spot 4, convergent-hole 1.

Feedback for the next prompt revision: repeated conditional disposition rows can hide differences inside otherwise valid situations. Separate refusal signals, callback effects and follow-up scheduling in the comparison. The shipped pilot prompt was outside this run's authorized output directory.
