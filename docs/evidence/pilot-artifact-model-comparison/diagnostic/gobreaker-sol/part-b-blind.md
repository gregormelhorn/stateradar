| id | Situation | Disposition | Expected behaviour (requirement terms) |
|---|---|---|---|
| Admission | closed, no interval expiry due, request accepted | handle | Execute runs the request; Allow returns a callback. Counters count the request. |
| Admission | closed, interval expiry due (Interval > 0) | transition → assumed-state:Closed_Cleared | Counts cleared before deciding; cleared counts ignore pre-clear results (DOC-21, DOC-22); then admit. |
| Admission | open, cooldown (Timeout) not elapsed | reject | Declared refusal: ErrOpenState (contract gobreaker.go:25); Execute returns it instantly (DOC-25). |
| Admission | open, cooldown elapsed | transition → HalfOpen_Probe, then handle | State becomes half-open (DOC-9); the call admits up to MaxRequests (≥1, DOC-6). |
| Admission | half-open, admitted probes below MaxRequests | handle | Admit; probe count incremented. |
| Admission | half-open, admitted probes at MaxRequests | reject | Declared refusal: ErrTooManyRequests (contract gobreaker.go:23). |
| Admission | called via Allow on TwoStep breaker | handle | Same admission path; callback returned on success, error on refusal (contract gobreaker.go:262-264). |
| Admission | nil/zero receiver or nil Execute function (UV-04) | reject | Declared refusal: error/panic surfaced immediately, never an admitted request. Verbatim error type unspecified. |
| Admission | two admissions overlap on one instance (UV-03) | handle | Both evaluated under the same lock; no double-counting of one admission; a second admission is a separate counted request. |
| Admission | admission delayed across boundary or mutex wait (UV-02) | handle | Deadline evaluated on the time sampled inside the locked path; outcome reflects that sample, not caller arrival time. |
| Admission | caller never acquires (UV-01) | ignore (documented) | Breaker unchanged; no counters move. |
| StateRead | closed | handle | Returns closed state. |
| StateRead | open, cooldown not elapsed | handle | Returns open. |
| StateRead | open, cooldown elapsed | transition → HalfOpen_Probe, then handle | State read refreshes the state machine: open→half-open on expiry (DOC-9); returns half-open. |
| StateRead | half-open | handle | Returns half-open. |
| StateRead | repeated/concurrent reads (UV-06) | handle | Each read is a pure observation of current state; concurrent reads do not corrupt state. |
| StateRead | no reads occur (UV-05) | ignore (documented) | Time passing alone changes nothing observable; open→half-open only on the next eligible operation (as-is style: expiry is evaluated inline). |
| CountsRead | closed | handle | Returns current snapshot (contract gobreaker.go:215). |
| CountsRead | after interval expiry, before any admission | transition → assumed-state:Closed_Cleared, then handle | Reading must show cleared counts consistent with DOC-21/DOC-22. |
| CountsRead | open or half-open | handle | Returns snapshot of the current counters (half-open requests tally per DOC-5). |
| CountsRead | repeated/concurrent reads (UV-06) | handle | Snapshot per read; no mutation to breaker state. |
| CountsRead | no reads occur (UV-05) | ignore (documented) | Observation omission has no effect on breaker. |
| NameRead | any lifecycle state after Setup | handle | Returns configured Name (DOC-4, contract gobreaker.go:200). |
| NameRead | before/lacking construction or on nil receiver (UV-04) | reject | Declared refusal: panic/error acceptable; no name invented. |
| NameRead | repeated/concurrent reads (UV-06) | handle | Stable immutable value; repetition harmless. |
| NameRead | no reads occur (UV-05) | ignore (documented) | No effect. |
| Report | callback in its own generation, breaker closed | handle | Counts success or failure per payload; if failure in closed, ReadyToTrip consulted (DOC-11). |
| Report | callback in its own generation, breaker half-open, success | handle | Count successes; transitions on policy satisfied by successes (required for closing half-open). |
| Report | callback in its own generation, breaker half-open, failure | transition → Open | Failure in half-open reopens immediately (standard semantics; DOC-21 state change clears Counts). |
| Report | stale generation (state changed or interval cleared since admission) (UV-08) | ignore (documented) | Counts ignores results of requests sent before clearing (DOC-22); no counter moves. |
| Report | duplicate report, same generation (UV-09) | UNSPECIFIED | Requirements never state once-only reporting; no declared refusal defined. |
| Report | concurrent contradictory reports on same callback (UV-10) | UNSPECIFIED | No serialisation or once guarantee declared; last write under lock only. |
| Report | no granted callback invoked, incl. nil (UV-11) | reject | Calling nil / ungranted callback is a caller defect: panic surfaces; breaker unchanged. |
| Report | plausible wrong Boolean or another operation's live callback (UV-12) | UNSPECIFIED | No identity binding declared between callback and operation; counted if generation matches, otherwise ignored per DOC-22. |
| Result | request returns value and nil error | handle | Passed to Classify; nil error per DOC-19 counts as success. |
| Result | request returns error | handle | Passed to Classify (DOC-16); classified outcome recorded. |
| Result | request panics | handle | Treated as error (DOC-27); same panic re-raised after recording. |
| Result | result delayed, generation changed meanwhile (UV-08) | ignore (documented) | Counts ignores pre-clear results (DOC-22). |
| Result | request hangs or exits goroutine (UV-13) | UNSPECIFIED | No cancellation/shutdown contract in requirements; admission remains counted (as-is: no release). |
| Result | plausible wrong result incl. typed-nil error (UV-14) | handle | Treated as provided; typed-nil is a non-nil error (DOC-19) so failure by default. |
| Classify | error non-nil, IsSuccessful returns true | handle | Counted as success (DOC-17). |
| Classify | error non-nil, returns false | handle | Counted as failure (DOC-18). |
| Classify | IsSuccessful nil | handle | Default used: false for all non-nil errors (DOC-19). |
| Classify | classifier delayed, generation changed (UV-08) | ignore (documented) | Outcome ignored per DOC-22. |
| Classify | IsSuccessful blocks/panics/exits (UV-15) | UNSPECIFIED | Requirements give no termination or panic contract for classifier; blocking stalls the request path. |
| Classify | concurrent classifications with shared policy state (UV-16) | UNSPECIFIED | No serialisation guarantee declared; classifier is caller-owned policy. |
| TripDecision | closed failure recorded, policy returns false | handle | Stays closed; Counts retained (unless interval cleared). |
| TripDecision | closed failure, policy returns true | transition → Open | Breaker placed open (DOC-12); Counts cleared (DOC-21); OnStateChange invoked. |
| TripDecision | ReadyToTrip nil | handle | Default policy: true when consecutive failures > 5 (DOC-14). |
| TripDecision | TripDecision blocks/panics/exits/reenters (UV-17) | UNSPECIFIED | No reentry or termination contract; invoked from lock-held path per observed annotation. |
| TripDecision | policy delayed across an expiry (UV-19) | UNSPECIFIED | Requirements silent on policy crossing expiry while locked. |
| TripDecision | policy refers to wrong breaker / surprising decision (UV-20) | handle | Decision accepted at face value; documentation places no constraint on policy. |
| Notify | state actually changes (closed→open, open→half-open, half-open→closed, half-open→open) | handle | OnStateChange called with name, from, to (DOC-15). One call per change. |
| Notify | state update to same state | ignore (documented) | No change ⇒ no notification (DOC-15 "whenever ... changes"). |
| Notify | OnStateChange nil | ignore (documented) | Hook absent; state change proceeds. |
| Notify | callback blocks/panics/exits/reenters (UV-18) | UNSPECIFIED | No termination or reentry contract; lock-held invocation observed. |
| Notify | callback crosses expiry while holding mutex or reenters via separate goroutine (UV-19) | UNSPECIFIED | Requirements silent; reentry into lock-taking methods is undocumented. |
| Notify | callback refers to wrong breaker (UV-20) | handle | Callback is user function; documentation imposes no identity check. |
| Setup | NewCircuitBreaker / NewTwoStepCircuitBreaker with valid Settings | handle | Constructs breaker configured per DOC-2, DOC-3, contract gobreaker.go:140/182. |
| Setup | MaxRequests 0 | handle | Effective max = 1 (DOC-6). |
| Setup | Interval ≤ 0 | handle | No closed-state clearing (DOC-8, contract gobreaker.go:79-105). |
| Setup | Timeout ≤ 0 | handle | Effective timeout = 60 s (DOC-10). |
| Setup | ReadyToTrip nil / IsSuccessful nil | handle | Defaults installed (DOC-13, DOC-19). |
| Setup | construction omitted, delayed, repeated, replaced (UV-21) | UNSPECIFIED | No lifetime contract; using the old object after replacement is permitted only via captured instance. |
| Setup | copied breaker value (UV-22) | UNSPECIFIED | No copy-safety contract declared; behaviour with copied mutex/state unspecified. |
| Expiry | closed, Interval ≤ 0 | ignore (documented) | Never clears on time (DOC-8). |
| Expiry | closed, Interval > 0, elapsed ≥ Interval | transition → assumed-state:Closed_Cleared | Counts cleared (DOC-7, DOC-21); deadline reset. |
| Expiry | closed, elapsed < Interval | ignore (documented) | Counts retained. |
| Expiry | open, elapsed < Timeout | ignore (documented) | Stays open (DOC-9). |
| Expiry | open, elapsed ≥ Timeout | transition → HalfOpen_Probe | Becomes half-open (DOC-9). |
| Expiry | clock anomaly / long delay (UV-23) | UNSPECIFIED | Requirements define elapsed-time semantics but no clock-anomaly contract. |
| Complete | successful completion, generation current | handle | Success recorded; half-open success may close breaker. |
| Complete | failed completion, generation current, closed | handle/transition → Open | Failure recorded; TripDecision decides (DOC-11, DOC-12). |
| Complete | generation stale | ignore (documented) | Discarded per DOC-22. |
| Complete | duplicate completion (UV-09) | UNSPECIFIED | No once contract. |
| Complete | contradictory completions (UV-10) | UNSPECIFIED | Serialised by lock; both applied if generation current. |
| UV-01 | no acquisition (see Admission) | ignore (documented) | No effect. |
| UV-02 | admission delayed across boundary (see Admission) | handle | Deadline from sampled time under lock. |
| UV-03 | overlapping admissions (see Admission) | handle | Each separately counted under lock. |
| UV-04 | wrong/nil/zero receiver, nil Execute (see Admission) | reject | Surfaced error/panic; no admission. |
| UV-05 | observation omitted / time passing (see StateRead) | ignore (documented) | Inline expiry; no side effect. |
| UV-06 | repeated/concurrent reads (see StateRead) | handle | Pure observation. |
| UV-07 | callback abandoned indefinitely (see Report) | UNSPECIFIED | No retention limit or cancellation in surface; admission count retained (as-is). |
| UV-08 | delayed outcome across generation change (see Report/Result/Classify) | ignore (documented) | DOC-22 discard. |
| UV-09 | repeated report same outcome (see Report) | UNSPECIFIED | No once guarantee. |
| UV-10 | concurrent contradictory reports (see Report) | UNSPECIFIED | Both applied under lock if current generation. |
| UV-11 | report without granted callback / nil invoke (see Report) | reject | Panic surfaces; breaker unchanged. |
| UV-12 | wrong Boolean / other operation's callback (see Report) | UNSPECIFIED | Generation check only; no identity binding. |
| UV-13 | request hangs/panics/exits (see Result) | handle for panic; UNSPECIFIED for hang/exit | Panic recorded as error and re-raised (DOC-27); hang has no contract. |
| UV-14 | plausible wrong result / typed-nil error (see Result) | handle | Typed-nil is non-nil ⇒ failure by default (DOC-19). |
| UV-15 | classifier blocks/panics/exits (see Classify) | UNSPECIFIED | No termination contract. |
| UV-16 | concurrent shared-policy classification (see Classify) | UNSPECIFIED | No serialisation guarantee. |
| UV-17 | policy blocks/panics/exits/reenters (see TripDecision) | UNSPECIFIED | No contract; lock-held invocation observed. |
| UV-18 | notify blocks/panics/exits/reenters (see Notify) | UNSPECIFIED | No contract; lock-held invocation observed. |
| UV-19 | policy/notification crossing expiry under mutex (see Notify) | UNSPECIFIED | Requirements silent. |
| UV-20 | wrong-breaker callback / surprising decision (see Notify/TripDecision) | handle | Accepted at face value. |
| UV-21 | construction omitted/delayed/repeated/replaced (see Setup) | UNSPECIFIED | No lifetime contract. |
| UV-22 | zero/negative durations, large limits, copied breaker (see Setup) | handle for durations/limits; UNSPECIFIED for copy | Zero/negative per DOC-6/8/10; copy-safety unspecified. |
| UV-23 | sample before/at/after deadline, long delay, clock anomaly (see Expiry) | handle for deadline orderings; UNSPECIFIED for clock anomaly | Elapsed ≥ threshold triggers transition; anomaly undefined. |
| P-01a | Admission → StateRead | handle | Admission evaluated first, then state read observes resulting state (e.g. half-open or open). |
| P-01b | StateRead → Admission | handle | State read may refresh open→half-open; subsequent admission then admitted as probe (DOC-9). |
| P-02a | Admission → CountsRead | handle | Snapshot observes the admission count. |
| P-02b | CountsRead → Admission | handle | Snapshot precedes the count; admission then increments. |
| P-03a | Admission → Report | handle | TwoStep: new admission evaluated against current counts; later report in its generation applied. |
| P-03b | Report → Admission | handle | Report applied first (may trip/open); subsequent admission observes new state. |
| P-04a | Admission → Result | handle | Admission decides; request run only if admitted (DOC-24). |
| P-04b | Result → Admission | handle | Resolved result recorded before next admission; next admission sees updated counters. |
| P-05a | StateRead → Report | handle | State read may refresh open→half-open; then report of a stale generation discarded (DOC-22). |
| P-05b | Report → StateRead | handle | Report applied in current state; read observes post-report state. |
| P-06a | StateRead → Result | handle | Read refreshes state; result then classified/recorded per current state generation. |
| P-06b | Result → StateRead | handle | Result recorded; read observes any state change. |
| P-07a | CountsRead → Report | handle | Snapshot before report; report then counted (possibly clearing on state change). |
| P-07b | Report → CountsRead | handle | Report may change state ⇒ clears counts (DOC-21); snapshot reflects cleared counts. |
| P-08a | CountsRead → Result | handle | Snapshot before completion; completion then updates counts. |
| P-08b | Result → CountsRead | handle | Completion applied first; snapshot observes updated counts. |
| P-09a | StateRead → CountsRead | handle | State refreshed first (possibly transition ⇒ clear); counts read after clearing. |
| P-09b | CountsRead → StateRead | handle | Raw counters observed; state read may then transition and clear them (DOC-21). |
| P-10a | Admission → Classify | handle | Admission decides; classification runs only for admitted request. |
| P-10b | Classify → Admission | handle | Classification of prior request records outcome before next admission sees counters. |
| P-11a | StateRead → Classify | handle | Read may transition state; classifier then runs for its request and is discarded if generation stale (DOC-22). |
| P-11b | Classify → StateRead | handle | Classification result recorded/ignored per generation; read observes state after. |
| P-12a | CountsRead → Classify | handle | Snapshot before classification; classification may update counts afterwards. |
| P-12b | Classify → CountsRead | handle | Classified outcome recorded before snapshot. |
| P-13a | Admission → TripDecision | handle | Admission under lock precedes policy evaluation on a later failure. |
| P-13b | TripDecision → Admission | handle | Policy decides (may open/clear); next admission observes resulting state (reject if open, DOC-25). |
| P-14a | StateRead → TripDecision | handle | Read refreshes state; policy evaluated only on closed-state failure (DOC-11). |
| P-14b | TripDecision → StateRead | handle | Policy may open/clear; read observes open state. |
| P-15a | CountsRead → TripDecision | handle | Snapshot precedes policy; policy receives its own copy of Counts (DOC-11). |
| P-15b | TripDecision → CountsRead | handle | Policy may open ⇒ clear counts; snapshot observes cleared counts (DOC-21). |
| P-16a | Admission → Notify | handle | Admission first; a state change (e.g. to half-open) then notifies (DOC-15). |
| P-16b | Notify → Admission | handle | Notification completes before admission proceeds under lock; admission sees new state. |
| P-17a | StateRead → Notify | handle | Read may cause open→half-open transition ⇒ notification fires (DOC-15). |
| P-17b | Notify → StateRead | handle | Notification completes; read observes the notified state. |
| P-18a | CountsRead → Notify | handle | Snapshot before state change; notification then fires and counts are cleared (DOC-21). |
| P-18b | Notify → CountsRead | handle | Notification first (state change cleared counts); snapshot observes cleared counts. |

Coverage checklist:
- [x] Admission
- [x] StateRead
- [x] CountsRead
- [x] NameRead
- [x] Report
- [x] Result
- [x] Classify
- [x] TripDecision
- [x] Notify
- [x] Setup
- [x] Expiry
- [x] Complete
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
- [x] UV-20
- [x] UV-21
- [x] UV-22
- [x] UV-23
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
