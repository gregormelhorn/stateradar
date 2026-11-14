# Part B diff

The first fresh Flash answer omitted Result (log 063) and is preserved in part-b-blind.incomplete.md. The second fresh Flash answer used the same inspected package and passed coverage (log 066). Mechanical check confirms 35 distinct event IDs, 36 pair ordering IDs matching 18 catalogue pairs, and one checklist tick per ID. Repeated IDs have distinct Situation values. The classifier below uses the full 135 situations.

No kept L-, G-, F- or T- ids and no removed domain terms were reported by the pack. Manual package review found no implementation fragments. The README examples and signatures were excluded from the prepared prose, and verbatim event contracts were retained.

Part B marked Result as-is. Also treat the following agreement as non-independent where it uses catalogue prose: Admission/UV-02/UV-03 lock sampling, attribution and admission counting; StateRead/UV-05/UV-06 and Expiry inline observation; Report/Complete/UV-07–UV-12 generation capture, admission retention and absent report guards; Classify/UV-15/UV-16 unlocked execution; TripDecision/Notify/UV-17–UV-19 lock-held invocation; Setup/UV-21 instance and lifecycle notes; pairs whose explanation repeats these same facts. Pair descriptions cue the classifier window and locked callback order. No as-is agreement on these effects is treated as independent confirmation.

| ID | Situation | Classification | Comparison |
|---|---|---|---|
| Admission | closed, no interval expiry due, request accepted | convergent | Observed branch agrees in the stated situation. |
| Admission | closed, interval expiry due (Interval > 0) | convergent | Both clear and admit after expiry. The inferred substate maps to a guard action within Closed; exact equality remains open. Fold → Q-05. |
| Admission | open, cooldown (Timeout) not elapsed | divergence | Correct sentinel before expiry; instantaneous return across a held lock is unestablished. Fold → Q-07. |
| Admission | open, cooldown elapsed | convergent | Observed branch agrees in the stated situation. vocabulary-drift: transition → HalfOpen_Probe, then handle maps to transition → HalfOpen, with admission as its action. |
| Admission | half-open, admitted probes below MaxRequests | convergent | Observed branch agrees in the stated situation. |
| Admission | half-open, admitted probes at MaxRequests | convergent | Observed branch agrees in the stated situation. |
| Admission | called via Allow on TwoStep breaker | convergent | Observed branch agrees in the stated situation. |
| Admission | nil/zero receiver or nil Execute function (UV-04) | divergence | An admitted nil function consumes an admission and can panic; wrong valid receiver uses its own state. Fold → Q-13. |
| Admission | two admissions overlap on one instance (UV-03) | convergent | Observed branch agrees in the stated situation. |
| Admission | admission delayed across boundary or mutex wait (UV-02) | convergent | Observed branch agrees in the stated situation. Fold → Q-07. |
| Admission | caller never acquires (UV-01) | divergence | Omission is a hole concerning absent caller/lifecycle behavior; no documented ignore covers it. Fold → Q-16. |
| StateRead | closed | convergent | Observed branch agrees in the stated situation. |
| StateRead | open, cooldown not elapsed | convergent | Observed branch agrees in the stated situation. |
| StateRead | open, cooldown elapsed | convergent | Observed branch agrees in the stated situation. vocabulary-drift: transition → HalfOpen_Probe, then handle maps to transition → HalfOpen, with State return as its action. |
| StateRead | half-open | convergent | Observed branch agrees in the stated situation. |
| StateRead | repeated/concurrent reads (UV-06) | divergence | State may mutate generation and notify when its read refreshes expiry. Fold → Q-22. |
| StateRead | no reads occur (UV-05) | divergence | Catalogue already describes inline expiry. The prose does not settle idle passage. Fold → Q-05. |
| CountsRead | closed | convergent | Observed branch agrees in the stated situation. |
| CountsRead | after interval expiry, before any admission | divergence | Counts returns the stored snapshot; it does not clear on a read. Fold → Q-22. vocabulary-drift: transition → assumed-state:Closed_Cleared, then handle maps to transition claim mapped to proposed refresh, which differs from observed handle snapshot. |
| CountsRead | open or half-open | convergent | Observed branch agrees in the stated situation. |
| CountsRead | repeated/concurrent reads (UV-06) | convergent | Observed branch agrees in the stated situation. |
| CountsRead | no reads occur (UV-05) | divergence | Omission has no separate documented disposition; another eligible event may still refresh. Fold → Q-16. |
| NameRead | any lifecycle state after Setup | convergent | Observed branch agrees in the stated situation. |
| NameRead | before/lacking construction or on nil receiver (UV-04) | divergence | An invalid receiver can panic; there is no refusal signal. Fold → Q-13. |
| NameRead | repeated/concurrent reads (UV-06) | convergent | Observed branch agrees in the stated situation. |
| NameRead | no reads occur (UV-05) | divergence | No incoming read and no documented ignore contract. Fold → Q-16. |
| Report | callback in its own generation, breaker closed | pass-B-blind-spot | Failure may trip and clear, which the row does not state. Fold → Q-17. |
| Report | callback in its own generation, breaker half-open, success | pass-B-blind-spot | The exact threshold and distinct reports remain implicit in the blind row. Fold → Q-17. |
| Report | callback in its own generation, breaker half-open, failure | convergent | Observed branch agrees in the stated situation. |
| Report | stale generation (state changed or interval cleared since admission) (UV-08) | pass-B-blind-spot | Outcome counters are discarded; the row misses refresh-before-filter. Agreement on counting only. Fold → Q-06. |
| Report | duplicate report, same generation (UV-09) | convergent-hole | Part B also leaves this intent open. Fold → Q-04. |
| Report | concurrent contradictory reports on same callback (UV-10) | convergent-hole | The implementation can apply both Boolean outcomes, rather than last-write replacement. Fold → Q-04. |
| Report | no granted callback invoked, incl. nil (UV-11) | divergence | The nil function panics at the caller before any breaker event; no refusal signal at invocation. Fold → Q-13. |
| Report | plausible wrong Boolean or another operation's live callback (UV-12) | convergent-hole | Part B also leaves this intent open. Fold → Q-12. |
| Result | request returns value and nil error | convergent | Observed branch agrees in the stated situation. |
| Result | request returns error | convergent | Observed branch agrees in the stated situation. |
| Result | request panics | divergence | Ordinary request panic behavior agrees; hook failure can replace the panic, which the unconditional wording omits. Fold → Q-19. |
| Result | result delayed, generation changed meanwhile (UV-08) | pass-B-blind-spot | Counters discard stale result; classifier still runs and completion may refresh first. Fold → Q-06. |
| Result | request hangs or exits goroutine (UV-13) | convergent-hole | Part B also leaves this intent open. Fold → Q-11. |
| Result | plausible wrong result incl. typed-nil error (UV-14) | convergent | Observed branch agrees in the stated situation. |
| Classify | error non-nil, IsSuccessful returns true | convergent | Observed branch agrees in the stated situation. |
| Classify | error non-nil, returns false | convergent | Observed branch agrees in the stated situation. |
| Classify | IsSuccessful nil | convergent | Observed branch agrees in the stated situation. |
| Classify | classifier delayed, generation changed (UV-08) | pass-B-blind-spot | The classifier can still run; only its outcome accounting is filtered. Fold → Q-06. |
| Classify | IsSuccessful blocks/panics/exits (UV-15) | convergent-hole | Part B also leaves this intent open. Fold → Q-10. |
| Classify | concurrent classifications with shared policy state (UV-16) | convergent-hole | Part B also leaves this intent open. Fold → Q-10. |
| TripDecision | closed failure recorded, policy returns false | convergent | Observed branch agrees in the stated situation. |
| TripDecision | closed failure, policy returns true | convergent | Observed branch agrees in the stated situation. |
| TripDecision | ReadyToTrip nil | convergent | Observed branch agrees in the stated situation. |
| TripDecision | TripDecision blocks/panics/exits/reenters (UV-17) | convergent-hole | Part B also leaves this intent open. Fold → Q-08. |
| TripDecision | policy delayed across an expiry (UV-19) | convergent-hole | Part B also leaves this intent open. Fold → Q-08. |
| TripDecision | policy refers to wrong breaker / surprising decision (UV-20) | convergent | Observed branch agrees in the stated situation. |
| Notify | state actually changes (closed→open, open→half-open, half-open→closed, half-open→open) | convergent | Observed branch agrees in the stated situation. |
| Notify | state update to same state | convergent | Observed branch agrees in the stated situation. |
| Notify | OnStateChange nil | convergent | Observed branch agrees in the stated situation. |
| Notify | callback blocks/panics/exits/reenters (UV-18) | convergent-hole | Part B also leaves this intent open. Fold → Q-09. |
| Notify | callback crosses expiry while holding mutex or reenters via separate goroutine (UV-19) | convergent-hole | Part B also leaves this intent open. Fold → Q-01. |
| Notify | callback refers to wrong breaker (UV-20) | convergent | Observed branch agrees in the stated situation. |
| Setup | NewCircuitBreaker / NewTwoStepCircuitBreaker with valid Settings | convergent | Observed branch agrees in the stated situation. |
| Setup | MaxRequests 0 | convergent | Observed branch agrees in the stated situation. |
| Setup | Interval ≤ 0 | convergent | Observed branch agrees in the stated situation. |
| Setup | Timeout ≤ 0 | convergent | Observed branch agrees in the stated situation. |
| Setup | ReadyToTrip nil / IsSuccessful nil | convergent | Observed branch agrees in the stated situation. |
| Setup | construction omitted, delayed, repeated, replaced (UV-21) | convergent-hole | Part B also leaves this intent open. Fold → Q-16. |
| Setup | copied breaker value (UV-22) | convergent-hole | Part B also leaves this intent open. Fold → Q-20. |
| Expiry | closed, Interval ≤ 0 | convergent | Observed branch agrees in the stated situation. |
| Expiry | closed, Interval > 0, elapsed ≥ Interval | divergence | Closed clearing stays in Closed, and equality does not clear. Fold → Q-05. |
| Expiry | closed, elapsed < Interval | convergent | Observed branch agrees in the stated situation. Fold → Q-05. |
| Expiry | open, elapsed < Timeout | convergent | Observed branch agrees in the stated situation. Fold → Q-05. |
| Expiry | open, elapsed ≥ Timeout | divergence | The blind ≥ guard changes the exact-equality outcome. Fold → Q-05. |
| Expiry | clock anomaly / long delay (UV-23) | convergent-hole | Part B also leaves this intent open. Fold → Q-05. |
| Complete | successful completion, generation current | pass-B-blind-spot | HalfOpen success at threshold is a state transition. Fold → Q-17. |
| Complete | failed completion, generation current, closed | convergent | Both branches are preserved in the matrix cell. Fold → Q-17. vocabulary-drift: handle/transition → Open maps to conditional handle if policy false or transition → Open if true. |
| Complete | generation stale | pass-B-blind-spot | The discard claim is accurate for outcome counters; pre-filter state changes are omitted. Fold → Q-06. |
| Complete | duplicate completion (UV-09) | convergent-hole | Part B also leaves this intent open. Fold → Q-04. |
| Complete | contradictory completions (UV-10) | convergent-hole | Part B also leaves this intent open. Fold → Q-04. |
| UV-01 | no acquisition (see Admission) | divergence | Observed branch agrees in the stated situation. Fold → Q-16. |
| UV-02 | admission delayed across boundary (see Admission) | convergent | Observed branch agrees in the stated situation. Fold → Q-07. |
| UV-03 | overlapping admissions (see Admission) | convergent | Observed branch agrees in the stated situation. |
| UV-04 | wrong/nil/zero receiver, nil Execute (see Admission) | divergence | Observed branch agrees in the stated situation. Fold → Q-13. |
| UV-05 | observation omitted / time passing (see StateRead) | divergence | Inline expiry is from the catalogue; documentation does not cover all omission timings. Fold → Q-05. |
| UV-06 | repeated/concurrent reads (see StateRead) | divergence | Counts and Name read; repeated State can clear or enter HalfOpen. Fold → Q-22. |
| UV-07 | callback abandoned indefinitely (see Report) | convergent-hole | Part B also leaves this intent open. Fold → Q-03. |
| UV-08 | delayed outcome across generation change (see Report/Result/Classify) | convergent | Observed branch agrees in the stated situation. Fold → Q-06. |
| UV-09 | repeated report same outcome (see Report) | convergent-hole | Part B also leaves this intent open. Fold → Q-04. |
| UV-10 | concurrent contradictory reports (see Report) | convergent-hole | Part B also leaves this intent open. Fold → Q-04. |
| UV-11 | report without granted callback / nil invoke (see Report) | divergence | Observed branch agrees in the stated situation. Fold → Q-13. |
| UV-12 | wrong Boolean / other operation's callback (see Report) | convergent-hole | Part B also leaves this intent open. Fold → Q-12. |
| UV-13 | request hangs/panics/exits (see Result) | pass-B-blind-spot | Ordinary panic is covered; no contract for stall or Goexit, and callback panic precedence remains open. Fold → Q-11. vocabulary-drift: handle for panic; UNSPECIFIED for hang/exit maps to conditional handle for panic and UNSPECIFIED for hang/exit. |
| UV-14 | plausible wrong result / typed-nil error (see Result) | convergent | Observed branch agrees in the stated situation. |
| UV-15 | classifier blocks/panics/exits (see Classify) | convergent-hole | Part B also leaves this intent open. Fold → Q-10. |
| UV-16 | concurrent shared-policy classification (see Classify) | convergent-hole | Part B also leaves this intent open. Fold → Q-10. |
| UV-17 | policy blocks/panics/exits/reenters (see TripDecision) | convergent-hole | Part B also leaves this intent open. Fold → Q-08. |
| UV-18 | notify blocks/panics/exits/reenters (see Notify) | convergent-hole | Part B also leaves this intent open. Fold → Q-09. |
| UV-19 | policy/notification crossing expiry under mutex (see Notify) | convergent-hole | Part B also leaves this intent open. Fold → Q-01. |
| UV-20 | wrong-breaker callback / surprising decision (see Notify/TripDecision) | convergent | Observed branch agrees in the stated situation. |
| UV-21 | construction omitted/delayed/repeated/replaced (see Setup) | convergent-hole | Part B also leaves this intent open. Fold → Q-16. |
| UV-22 | zero/negative durations, large limits, copied breaker (see Setup) | convergent-hole | Part B also leaves this intent open. Fold → Q-20. vocabulary-drift: handle for durations/limits; UNSPECIFIED for copy maps to conditional handle for settings and UNSPECIFIED for copy. |
| UV-23 | sample before/at/after deadline, long delay, clock anomaly (see Expiry) | divergence | The stated ≥ includes equality where observed guard stays. Fold → Q-05. vocabulary-drift: handle for deadline orderings; UNSPECIFIED for clock anomaly maps to conditional deadline handling and UNSPECIFIED clock behavior. |
| P-01a | Admission → StateRead | convergent | Observed branch agrees in the stated situation. |
| P-01b | StateRead → Admission | convergent | Observed branch agrees in the stated situation. |
| P-02a | Admission → CountsRead | convergent | Observed branch agrees in the stated situation. |
| P-02b | CountsRead → Admission | convergent | Observed branch agrees in the stated situation. |
| P-03a | Admission → Report | divergence | A contender can reject at full capacity before the earlier success closes. Fold → Q-03. |
| P-03b | Report → Admission | divergence | A successful current report at cap can close, enabling a later call; the row discusses only trip/Open. Fold → Q-03. |
| P-04a | Admission → Result | convergent | Observed branch agrees in the stated situation. |
| P-04b | Result → Admission | divergence | User result and accounting are separate; later admission can win before accounting. Fold → Q-23. |
| P-05a | StateRead → Report | convergent | Observed branch agrees in the stated situation. |
| P-05b | Report → StateRead | divergence | An old report can itself refresh Open and discard its outcome before State reads. Fold → Q-06. |
| P-06a | StateRead → Result | divergence | State can clear, then classifier runs but cannot count stale outcome. Fold → Q-06. |
| P-06b | Result → StateRead | divergence | A result can be classified then discarded as it triggers refresh. Fold → Q-06. |
| P-07a | CountsRead → Report | convergent | Observed branch agrees in the stated situation. |
| P-07b | Report → CountsRead | convergent | Observed branch agrees in the stated situation. |
| P-08a | CountsRead → Result | convergent | Observed branch agrees in the stated situation. |
| P-08b | Result → CountsRead | divergence | Result can precede snapshot without accounting having committed. Fold → Q-23. |
| P-09a | StateRead → CountsRead | convergent | Observed branch agrees in the stated situation. |
| P-09b | CountsRead → StateRead | convergent | Observed branch agrees in the stated situation. |
| P-10a | Admission → Classify | convergent | Observed branch agrees in the stated situation. |
| P-10b | Classify → Admission | divergence | Classifier may have started without committing, and later admission can refuse first. Fold → Q-23. |
| P-11a | StateRead → Classify | convergent | Observed branch agrees in the stated situation. |
| P-11b | Classify → StateRead | divergence | State can obtain the lock while classifier is still running. Fold → Q-23. |
| P-12a | CountsRead → Classify | convergent | Observed branch agrees in the stated situation. |
| P-12b | Classify → CountsRead | divergence | Counts can snapshot while classifier is paused. Fold → Q-23. |
| P-13a | Admission → TripDecision | convergent | Observed branch agrees in the stated situation. |
| P-13b | TripDecision → Admission | divergence | A caller must wait for the callback lock and samples time afterward. Fold → Q-07. |
| P-14a | StateRead → TripDecision | convergent | Observed branch agrees in the stated situation. |
| P-14b | TripDecision → StateRead | convergent | Observed branch agrees in the stated situation. |
| P-15a | CountsRead → TripDecision | convergent | Observed branch agrees in the stated situation. |
| P-15b | TripDecision → CountsRead | convergent | Observed branch agrees in the stated situation. |
| P-16a | Admission → Notify | divergence | When admission itself discovers expiry, notification precedes that admission's count commit. Fold → Q-01. |
| P-16b | Notify → Admission | convergent | Observed branch agrees in the stated situation. |
| P-17a | StateRead → Notify | convergent | Observed branch agrees in the stated situation. |
| P-17b | Notify → StateRead | convergent | Observed branch agrees in the stated situation. |
| P-18a | CountsRead → Notify | convergent | Observed branch agrees in the stated situation. |
| P-18b | Notify → CountsRead | convergent | Observed branch agrees in the stated situation. |

## Feedback classes

Clarify when a pair arrow denotes callback entry, completion commit or observable return. Keep a time refresh within the same modeled state as a guard action and specify equality explicitly in the analysis. Keep the catalogue's existing state/clock gates and distinguish generation reset from the public enum. These proposals are recorded here because the run allows analysis artifacts only.
