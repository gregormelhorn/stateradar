| id | Situation | Disposition | Expected behaviour (requirement terms) |
|---|---|---|---|
| Configure | Valid settings, new instance intended | handle | Select breaker name, MaxRequests, Interval, Timeout, ReadyToTrip, OnStateChange, IsSuccessful into the instance; instance begins in Closed with empty Counts. |
| Configure | Zero-valued optional fields | handle | Apply documented defaults: MaxRequests 0→1, Timeout ≤0→60s, Interval ≤0→no periodic clear, nil ReadyToTrip→consecutive-failures>5, nil IsSuccessful→non-nil error is failure. |
| Configure | Negative durations supplied | as-is: | Accept the values as typed (gobreaker.go contracts state Interval/Timeout ≤0 use zero semantics; no rejection signal is declared). Open point: no declared refusal signal for invalid settings. |
| Configure | Second construction when one instance intended | ignore (documented) | Requirements give no uniqueness constraint; two independently configured instances are each valid breakers. `as-is:` no dedup. |
| Execute | Closed, within Interval, request admitted | transition → Closed (stays) | Run request synchronously in caller goroutine; classify result; return result/error to caller. |
| Execute | Open, before Timeout elapsed | reject | Return ErrOpenState instantly; request is not run. |
| Execute | Open, Timeout elapsed (expiry observed) | transition → HalfOpen | First qualifying call samples clock, moves to HalfOpen, then admits per MaxRequests. |
| Execute | HalfOpen, admitted requests < MaxRequests | handle | Run request; outcome reported back via internal ApplySuccess/ApplyFailure. |
| Execute | HalfOpen, admitted requests ≥ MaxRequests | reject | Return ErrTooManyRequests instantly; request not run. |
| Execute | Request panics | handle | Treat panic as an error for counting, then re-raise the same panic to the caller. |
| Execute | Nil request function / nil or unconstructed receiver | as-is: | No nil/ownership validation in API; Go runtime fault results. Open point: requirements do not name this. |
| Allow | Closed, within Interval | handle | Return non-nil completion callback bound to receiver and generation; no request run by breaker. |
| Allow | Open, before Timeout | reject | Return error (ErrOpenState) and a callback that must not be treated as admission. |
| Allow | Open, Timeout elapsed | transition → HalfOpen | Move to HalfOpen, then admit per MaxRequests and return callback. |
| Allow | HalfOpen, below MaxRequests | handle | Return non-nil callback; consume one half-open admission slot. |
| Allow | HalfOpen, at/over MaxRequests | reject | Return ErrTooManyRequests. |
| ReportSuccess | Generation current, Closed, success counted | handle | Count as success; do not trip; return. |
| ReportSuccess | HalfOpen, first successes reach threshold | transition → Closed | Count successes; on reaching MaxRequests successes return to Closed and clear Counts; notify observer. |
| ReportSuccess | Stale generation (rollover/expiry) | ignore (documented) | Counts ignores results of requests sent before clearing; discard report. |
| ReportFailure | Generation current, Closed, ReadyToTrip false | handle | Count failure; call ReadyToTrip with copy of Counts; stay Closed. |
| ReportFailure | Generation current, Closed, ReadyToTrip true | transition → Open | Count failure, trip to Open, record expiry = now + Timeout, clear Counts, notify observer. |
| ReportFailure | HalfOpen | transition → Open | Any half-open failure reopens immediately; expiry reset; notify observer. |
| ReportFailure | Stale generation | ignore (documented) | Discard report per Counts-ignores-before-clearing. |
| ReadState | Any state, non-expired Open | handle | Return current state; if Open and expiry passed, first transition to HalfOpen then return HalfOpen. |
| ReadState | Open, expiry sampled equal/after deadline | transition → HalfOpen | Report HalfOpen and notify observer. |
| ReadState | Nil/unconstructed receiver | as-is: | Go runtime fault; no validation. Open point. |
| ReadCounts | Any state | handle | Return snapshot of Counts (Requests, TotalSuccesses, TotalFailures, ConsecutiveSuccesses, ConsecutiveFailures). |
| ReadCounts | Cross-method snapshot not atomic with ReadState | ignore (documented) | No cross-method snapshot protocol; each read returns its own consistent snapshot. |
| ReadName | Any state | handle | Return configured Name; no uniqueness guarantee. |
| ReadName | Nil receiver | as-is: | Runtime fault. Open point. |
| RequestResult | Returns value/error normally | handle | Classify error via IsSuccessful; count success/failure; return result to caller. |
| RequestResult | Returns after generation rollover | ignore (documented) | Result discarded from Counts per Counts-ignores-before-clearing. |
| RequestResult | Never returns / goroutine exits | UNSPECIFIED | No context/deadline in API; breaker holds outstanding occupancy. Open point: requirements silent. |
| Classify | IsSuccessful nil | handle | Use default classifier (non-nil error → failure). |
| Classify | IsSuccessful returns a Boolean | handle | Apply as success (true) or failure (false) count. |
| Classify | Classifier panics/blocks/exits | UNSPECIFIED | No failure/latency guarantee in Settings; result may be misclassified or leak lock-free path. Open point. |
| Classify | Re-enters breaker before committing | UNSPECIFIED | Settings specify neither reentrancy nor panic policy. Open point. |
| TripDecision | ReadyToTrip nil | handle | Use default policy (consecutive failures > 5 → trip). |
| TripDecision | Returns true | transition → Open | Breaker placed into Open as per DOC-13. |
| TripDecision | Returns false | handle | Stay Closed. |
| TripDecision | Policy panics/blocks/re-enters | UNSPECIFIED | No reentrancy/latency guarantee; called under breaker lock. Open point. |
| Notify | OnStateChange nil | ignore (documented) | Supported: state change occurs without notification. |
| Notify | Non-nil, state changed | handle | Invoke observer with (name, state). |
| Notify | Observer panics/blocks/re-enters | UNSPECIFIED | No runtime guarantee; called inside lock path. Open point. |
| Notify | Repeated same-named transitions across cycles/instances | as-is: | No unique id/sequence; consumer must tolerate repeats. |
| ObserveExpiry | Open, now < expiry | handle | Stay Open; admit nothing. |
| ObserveExpiry | Open, now ≥ expiry | transition → HalfOpen | Move to HalfOpen on next observation and notify observer. |
| ObserveExpiry | No qualifying call at deadline | defer (queued) | Transition deferred until next State/admission/read observation; no background timer. |
| ApplySuccess | Generation matches, HalfOpen threshold reached | transition → Closed | Close, clear Counts, notify observer. |
| ApplySuccess | Generation mismatched | ignore (documented) | Discard per Counts-ignores-before-clearing. |
| ApplyFailure | Generation matches, Closed, ReadyToTrip true | transition → Open | Trip to Open, reset expiry, notify observer. |
| ApplyFailure | Generation matches, HalfOpen | transition → Open | Reopen immediately. |
| ApplyFailure | Generation mismatched | ignore (documented) | Discard. |
| UV-01 | Request never returns or goroutine exits | UNSPECIFIED | Breaker keeps outstanding slot; no context cancellation API. Open point. |
| UV-01 | Request panics | handle | Treat as error, re-panic to caller. |
| UV-01 | Submitter abandons interest | ignore (documented) | Result is caller-owned; breaker counts result if/when reported (two-step) or when Execute returns. |
| UV-02 | Slow completion after deadline elapsed | handle | Result applied to current generation if not cleared; if cleared, ignored. |
| UV-02 | Overlapping later request while first pending | handle | Each admission counted independently; no caller identity. |
| UV-03 | Second Execute while first pending | handle | Each admission independent; no per-caller tracking. |
| UV-03 | Execute after return, caller still owns result | handle | New admission; previous result ownership has no effect. |
| UV-04 | Nil request function | as-is: | Runtime fault; no upstream guard. Open point. |
| UV-04 | Call on wrong valid breaker | as-is: | Calls act on the receiver used; no instance-purpose validation. |
| UV-04 | Nil/unconstructed receiver | as-is: | Runtime fault. Open point. |
| UV-05 | Allow arrives late (after Timeout) | handle | Normal half-open admission per MaxRequests. |
| UV-05 | Caller stops before/during submission | defer (queued) | No callback returned → no completion; slot remains occupied (two-step permits no cancellation). |
| UV-05 | Caller stops after receiving callback | ignore (documented) | Outstanding callback may never be invoked; breaks UV-07. |
| UV-06 | Second Allow before first returns | handle | Independent admission subject to MaxRequests when half-open. |
| UV-06 | Second Allow after first while callback held | handle | Independent admission; no lock fairness guarantee. |
| UV-07 | Report omitted after accepted trial | UNSPECIFIED | HalfOpen slot remains consumed; no timeout/reclaim. Open point. |
| UV-08 | Outcome after generation rollover | ignore (documented) | Discard per generation check. |
| UV-08 | Outcome after expiry/state change | ignore (documented) | Discard per Counts-ignores-before-clearing. |
| UV-08 | Outcome after application cancellation | handle | Still counted; no public API invalidates on cancellation alone. |
| UV-09 | Same completion repeated sequentially | ignore (documented) | Second invocation sees mutated generation/state; may double-count if generation matches — open point: no exactly-once guarantee. |
| UV-09 | Contradictory Booleans concurrently | UNSPECIFIED | No exactly-once guarantee; both may apply. Open point. |
| UV-10 | Completion without admission | reject | Caller only obtains non-nil callback from successful Allow; invoking nil callback is a caller runtime fault (as-is: panic). |
| UV-10 | Invoking nil callback | as-is: | Go runtime fault. |
| UV-11 | Wrong Boolean reported | handle | Trusted as reported value; outcome truth not verified. |
| UV-11 | Callback reused for another request | handle | Applied to bound generation/receiver; may mis-count — as-is: not rejected. |
| UV-11 | Misleading ReadyToTrip ratio | handle | Policy's Boolean honored; no verification. |
| UV-12 | Repeated / late / interleaved reads | handle | Each read returns its own snapshot; no dedup or sequencing. |
| UV-13 | Classifier panics | UNSPECIFIED | No panic policy in Settings. Open point. |
| UV-13 | Classifier blocks | UNSPECIFIED | Runs outside mutex but blocks Execute. Open point. |
| UV-14 | Classification finishes after generation change | ignore (documented) | Count discarded per generation. |
| UV-14 | Classifier re-enters breaker | UNSPECIFIED | No reentrancy restriction in Settings. Open point. |
| UV-15 | Policy panics/blocks/exits/re-enters | UNSPECIFIED | Under lock; no reentrancy/failure guarantee. Open point. |
| UV-16 | Observer absent | ignore (documented) | Supported. |
| UV-16 | Observer panics/blocks/exits/re-enters | UNSPECIFIED | No runtime guarantee; runs in lock path. Open point. |
| UV-17 | Repeated same-named transitions | as-is: | No unique id/sequence; consumer must dedupe. |
| UV-17 | Unsolicited invocation outside breaker | ignore (documented) | Outside breaker's contract; owner's responsibility. |
| UV-18 | Equality at deadline | transition → HalfOpen | now ≥ expiry counts as elapsed; HalfOpen on next observation. |
| UV-18 | Deadline elapses without qualifying call | defer (queued) | Deferred to next observation. |
| UV-18 | Clock differs from intended schedule | UNSPECIFIED | No standalone clock injection; delay/out-of-order observed. Open point. |
| UV-20 | Construction omitted | as-is: | Nil receiver → runtime fault; no upstream validation. |
| UV-20 | Two calls to constructor when one intended | ignore (documented) | Each creates an independent instance; no dedup. |
| UV-21 | Negative durations | as-is: | Accept as typed; ≤0 semantics apply (Interval: no clear; Timeout: 60s). |
| UV-21 | Large request limit/interval/timeout | handle | Accepted as-is; no upper bound. |
| P-01a | Execute → ReadState near expiry | handle | Execute admits/returns; subsequent ReadState returns current or post-expiry state; each consistent. |
| P-01b | ReadState → Execute | handle | ReadState may transition to HalfOpen; Execute then admits per HalfOpen. |
| P-02a | Execute → ReadCounts | handle | ReadCounts returns snapshot including or excluding completed Execute per timing. |
| P-02b | ReadCounts → Execute | handle | Independent; ReadCounts snapshot then Execute mutates Counts. |
| P-03a | Allow → ReportSuccess | handle | Callback applies success; threshold→Closed. |
| P-03b | ReportSuccess → Allow | handle | Success committed; new Allow admitted per current state. |
| P-04a | Allow → ReportFailure | handle | Failure applied; may trip Open. |
| P-04b | ReportFailure → Allow | handle | After trip, Allow rejects with ErrOpenState. |
| P-05a | ReportSuccess → ReadState | handle | ReadState reflects post-commit state (possibly Closed). |
| P-05b | ReadState → ReportSuccess | handle | Read may transition HalfOpen; report applies to bound generation. |
| P-06a | ReportFailure → ReadState | handle | ReadState reflects Open and notifies. |
| P-06b | ReadState → ReportFailure | handle | Read transitions if expired; report applies to bound generation (may be stale → ignore). |
| P-07a | ReportSuccess → ReadCounts | handle | Counts include committed success. |
| P-07b | ReadCounts → ReportSuccess | handle | Snapshot then commit; no cross-method atomicity. |
| P-08a | ReportFailure → ReadCounts | handle | Counts include committed failure. |
| P-08b | ReadCounts → ReportFailure | handle | Snapshot then commit. |
| P-09a | ReadState → ReadCounts near expiry | handle | ReadState moves HalfOpen; ReadCounts reflects current Counts. |
| P-09b | ReadCounts → ReadState | handle | Snapshot then HalfOpen transition; documented non-atomic. |
| P-10a | RequestResult → ReadState | handle | Result committed; ReadState reflects updated state. |
| P-10b | ReadState → RequestResult | handle | Observe then commit; no ordering guarantee. |
| P-11a | Classify → ReadState | handle | Classification committed then read reflects. |
| P-11b | ReadState → Classify | handle | Independent; classifier runs outside lock. |
| P-12a | Allow → ReadState at expiry | handle | Allow admitted if HalfOpen; ReadState reflects. |
| P-12b | ReadState → Allow | handle | ReadState may transition HalfOpen; Allow then per HalfOpen. |
| P-13a | Allow → ReadCounts | handle | Counts reflect half-open admission occupancy. |
| P-13b | ReadCounts → Allow | handle | Snapshot then admission counted. |
| P-14a | ReportSuccess → ReportFailure | handle | Independent callbacks applied to own generations; later may change state. |
| P-14b | ReportFailure → ReportSuccess | handle | Independent; success may close early in HalfOpen. |
| P-15a | TripDecision → ReadState | handle | Policy under lock decides; ReadState afterwards sees resulting state. |
| P-15b | ReadState → TripDecision | handle | Read then policy decision; serialized by lock. |

Coverage checklist:
- [x] Configure
- [x] Execute
- [x] Allow
- [x] ReportSuccess
- [x] ReportFailure
- [x] ReadState
- [x] ReadCounts
- [x] ReadName
- [x] RequestResult
- [x] Classify
- [x] TripDecision
- [x] Notify
- [x] ObserveExpiry
- [x] ApplySuccess
- [x] ApplyFailure
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
- [x] UV-20
- [x] UV-21
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