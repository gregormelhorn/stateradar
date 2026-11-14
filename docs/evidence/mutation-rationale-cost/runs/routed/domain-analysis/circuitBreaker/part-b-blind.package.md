You are the BLIND adversarial pass (Part B) of a domain-behaviour analysis. You have NO access to the implementation. Do NOT read any files, do NOT use any tools, do NOT search any repository — the inputs below are complete and are your ONLY sources. If you catch yourself wanting to look something up, label it an open point instead.

TASK: Here is the event catalogue of a component, and its requirements. For every event — including undesired variants and both orderings of every interaction pair — state in which situations the component should handle, ignore, or reject it, and what should happen. Describe situations in requirement terms. Name states per PA-17 (state naming convention): prefer public API names, name sub-states by their condition, use PascalCase with `_` as separator. If you must assume a lifecycle state the requirements do not name, label it `assumed-state:` with the condition that defines it. You have no access to the implementation. Be concrete. Produce a table keyed by the catalogue's event ids and pair-ordering ids. Prefer one row per id with conditional outcomes. If you split an id into several rows, use an explicit `Situation` column with distinct, nonempty labels. Do not repeat the same situation. End with a coverage checklist: every catalogue event id, listed once, ticked. A missing row must be impossible to miss.

Catalogue headings and fields labelled `observed in code` say what the implementation does, not what it should do. Base each row on the requirements, the contracts and the doctrine lines. When a row's expected behaviour rests only on observed-in-code text, start its behaviour cell with `as-is:`.

<!-- generated:rules key=partb-vocab -->
The disposition vocabulary you must use (from the methods reference): `transition → <target>` | `handle` (stays in the state, does something) | `ignore (documented)` | `ignore (accidental)` | `defer (queued)` | `reject` (a declared refusal signal: error, diagnostic, nack) | `UNSPECIFIED`. Without these definitions a blind pass applies `reject` and `handle` to identical semantics interchangeably (dobby trigger-service, 2026-08-05: four vocabulary-only "divergences").
<!-- /generated:rules -->

The catalogue's event ids are: Configure Execute Allow ReportSuccess ReportFailure ReadState ReadCounts ReadName RequestResult Classify TripDecision Notify ObserveExpiry ApplySuccess ApplyFailure UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 UV-15 UV-16 UV-17 UV-18 UV-20 UV-21 — plus the pair orderings P-01a P-01b P-02a P-02b P-03a P-03b P-04a P-04b P-05a P-05b P-06a P-06b P-07a P-07b P-08a P-08b P-09a P-09b P-10a P-10b P-11a P-11b P-12a P-12b P-13a P-13b P-14a P-14b P-15a P-15b.

=== INPUT 1: EVENT CATALOGUE (code fragments and analysis references removed) ===

# Event catalogue

<!-- event-ids: Configure Execute Allow ReportSuccess ReportFailure ReadState ReadCounts ReadName RequestResult Classify TripDecision Notify ObserveExpiry ApplySuccess ApplyFailure UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 UV-15 UV-16 UV-17 UV-18 UV-20 UV-21 -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| Configure | external | constructor caller | Settings select a new breaker and its policy, observed-in-code gobreaker.go and gobreaker.go. |
| Execute | external | request submitter | Pass a function for admission and execution, observed-in-code gobreaker.go and gobreaker.go. |
| Allow | external | two-step submitter | Ask for admission and an outcome callback, observed-in-code gobreaker.go and gobreaker.go. |
| ReportSuccess | external | outcome reporter | Report true through the callback returned by Allow, observed-in-code gobreaker.go and gobreaker.go. |
| ReportFailure | external | outcome reporter | Report false through the callback returned by Allow, observed-in-code gobreaker.go and gobreaker.go. |
| ReadState | external | state observer | Request reported state, observed-in-code gobreaker.go. |
| ReadCounts | external | counts observer | Request the counters, observed-in-code gobreaker.go. |
| ReadName | external | name observer | Request the configured name, observed-in-code gobreaker.go. |
| RequestResult | external | injected request | Return a value/error, panic, or fail to return after admission, observed-in-code gobreaker.go and gobreaker.go. |
| Classify | external | injected classifier | Return an error classification for Execute, observed-in-code gobreaker.go. |
| TripDecision | external | injected trip policy | Return a decision after a counted closed failure, observed-in-code gobreaker.go and gobreaker.go. |
| Notify | internal | breaker notification to injected observer | Call the registered state-change observer with name and state pair, observed-in-code gobreaker.go and gobreaker.go. |
| ObserveExpiry | internal | clock sampled by breaker | Compare expiry with sampled time, observed-in-code gobreaker.go and gobreaker.go. |
| ApplySuccess | internal | breaker completion accounting | Apply a successful outcome, observed-in-code gobreaker.go and gobreaker.go. |
| ApplyFailure | internal | breaker completion accounting | Apply a failed outcome, observed-in-code gobreaker.go and gobreaker.go. |
| UV-01 | external | injected request or submitter | Work never returns, exits its goroutine, or panics, or submitter abandons interest. |
| UV-02 | external | request submitter and injected request | Slow completion or submission, later overlapping request, and elapsed deadline while work remains outstanding. |
| UV-03 | external | request submitter | A second Execute from the same caller while the first is pending, or after it returns and the caller still owns its result. |
| UV-04 | external | public caller | Nil request, a call on the wrong valid breaker, or a nil or unconstructed receiver. Receiver selection differs from erroneous report payload. |
| UV-05 | external | two-step submitter | Attempt arrives late, or caller stops before or during submission, or after receiving the completion callback. |
| UV-06 | external | two-step submitter | Same caller issues a second Allow before the first returns, or after the first returns while it still holds its callback. |
| UV-07 | external | outcome reporter | Report omitted after an accepted trial, including logical teardown by caller. |
| UV-08 | external | outcome reporter or long-running request | Outcome after generation rollover, elapsed expiry, or application cancellation. Success and failure are separate outcomes. |
| UV-09 | external | outcome reporter | Same completion repeated sequentially or concurrently with equal or contradictory Booleans. |
| UV-10 | external | outcome reporter or injected callback | Unsolicited completion without admission, including invoking a nil callback returned with rejection. |
| UV-11 | external | outcome reporter or injected classifier/policy | A valid but wrong Boolean, a callback reused for another request, or trip policy using an unintentionally misleading ratio. |
| UV-12 | external | observer | Missing, late, repeated, or interleaved read of state, counts or name. |
| UV-13 | external | injected classifier | Classifier panics, blocks, or exits the goroutine. |
| UV-14 | external | injected classifier | Classification finishes after generation changed, or re-enters the breaker before committing its result. |
| UV-15 | external | injected trip policy | Trip callback panics, blocks, exits, or re-enters mutex-taking methods. |
| UV-16 | external | injected observer | Observer absent, panics, blocks, exits, or re-enters mutex-taking methods. |
| UV-17 | internal | observer callback consumer | Repeated same-named transitions across cycles or instances, or consumer misattributes the notification. Unsolicited callback invocation is possible outside the breaker by whoever owns the function. |
| UV-18 | internal | clock observation | Deadline elapses without a qualifying call, delayed observation, equality at deadline, or clock time differs from intended schedule. |
| UV-20 | external | constructor caller | Construction omitted, or two calls create independently configured instances when one was intended. |
| UV-21 | external | constructor caller | Negative durations or valid but unintended large request limit, interval or timeout. |

## Undesired-coverage (observed in code, not documented intent)

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| Configure: constructor caller | UV-20 | n/a: no independent delivery at this boundary, gobreaker.go. | UV-20 | n/a: no independent delivery at this boundary, gobreaker.go. | n/a: no independent delivery at this boundary, gobreaker.go. | n/a: no independent delivery at this boundary, gobreaker.go. | UV-21 |
| Execute: request submitter | UV-01 | UV-02 | UV-03 | UV-02 | UV-03 | UV-04 | UV-04 |
| Allow: two-step submitter | UV-05 | UV-05 | UV-06 | UV-05 | UV-06 | UV-04 | UV-04 |
| ReportSuccess: outcome reporter | UV-07 | UV-08 | UV-09 | UV-08 | UV-09 | UV-10 | UV-11 |
| ReportFailure: outcome reporter | UV-07 | UV-08 | UV-09 | UV-08 | UV-09 | UV-10 | UV-11 |
| ReadState: state observer | UV-12 | UV-12 | UV-12 | UV-12 | n/a: no independent delivery at this boundary, gobreaker.go. | n/a: no independent delivery at this boundary, gobreaker.go. | UV-04 |
| ReadCounts: counts observer | UV-12 | UV-12 | UV-12 | UV-12 | n/a: no independent delivery at this boundary, gobreaker.go. | n/a: no independent delivery at this boundary, gobreaker.go. | UV-04 |
| ReadName: name observer | UV-12 | UV-12 | UV-12 | UV-12 | n/a: no independent delivery at this boundary, gobreaker.go. | n/a: no independent delivery at this boundary, gobreaker.go. | UV-04 |
| RequestResult: injected request | UV-01 | UV-02 | n/a: no independent delivery at this boundary, gobreaker.go. | UV-08 | n/a: no independent delivery at this boundary, gobreaker.go. | UV-10 | UV-11 |
| Classify: injected classifier | UV-13 | UV-13 | n/a: no independent delivery at this boundary, gobreaker.go. | UV-14 | n/a: no independent delivery at this boundary, gobreaker.go. | UV-10 | UV-11 |
| TripDecision: injected trip policy | UV-15 | UV-15 | n/a: no independent delivery at this boundary, gobreaker.go. | n/a: no independent delivery at this boundary, gobreaker.go. | n/a: no independent delivery at this boundary, gobreaker.go. | UV-10 | UV-11 |
| Notify: breaker notification to injected observer | UV-16 | UV-16 | UV-17 | UV-17 | UV-17 | UV-17 | UV-17 |
| ObserveExpiry: clock sampled by breaker | UV-18 | UV-18 | n/a: no independent delivery at this boundary, gobreaker.go. | UV-18 | n/a: no independent delivery at this boundary, gobreaker.go. | n/a: no independent delivery at this boundary, gobreaker.go. | UV-18 |
| ApplySuccess: breaker completion accounting | n/a: no independent delivery at this boundary, gobreaker.go. | UV-08 | UV-09 | UV-08 | UV-09 | UV-10 | UV-11 |
| ApplyFailure: breaker completion accounting | n/a: no independent delivery at this boundary, gobreaker.go. | UV-08 | UV-09 | UV-08 | UV-09 | UV-10 | UV-11 |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Execute → ReadState | Execute submitter and observer on one breaker |
| P-01b | ReadState → Execute | Execute submitter and observer on one breaker |
| P-02a | Execute → ReadCounts | Execute submitter and counts observer on one breaker |
| P-02b | ReadCounts → Execute | Execute submitter and counts observer on one breaker |
| P-03a | Allow → ReportSuccess | new admission and outstanding successful trial callback |
| P-03b | ReportSuccess → Allow | new admission and outstanding successful trial callback |
| P-04a | Allow → ReportFailure | new admission and outstanding failed trial callback |
| P-04b | ReportFailure → Allow | new admission and outstanding failed trial callback |
| P-05a | ReportSuccess → ReadState | outcome callback and expiry-observing reader |
| P-05b | ReadState → ReportSuccess | outcome callback and expiry-observing reader |
| P-06a | ReportFailure → ReadState | outcome callback and expiry-observing reader |
| P-06b | ReadState → ReportFailure | outcome callback and expiry-observing reader |
| P-07a | ReportSuccess → ReadCounts | outcome callback and counts observer |
| P-07b | ReadCounts → ReportSuccess | outcome callback and counts observer |
| P-08a | ReportFailure → ReadCounts | outcome callback and counts observer |
| P-08b | ReadCounts → ReportFailure | outcome callback and counts observer |
| P-09a | ReadState → ReadCounts | independent readers near expiry |
| P-09b | ReadCounts → ReadState | independent readers near expiry |
| P-10a | RequestResult → ReadState | injected workload return overlapping observer |
| P-10b | ReadState → RequestResult | injected workload return overlapping observer |
| P-11a | Classify → ReadState | injected classifier return overlapping observer |
| P-11b | ReadState → Classify | injected classifier return overlapping observer |
| P-12a | Allow → ReadState | new trial and observer at expiry |
| P-12b | ReadState → Allow | new trial and observer at expiry |
| P-13a | Allow → ReadCounts | new trial and counts observer |
| P-13b | ReadCounts → Allow | new trial and counts observer |
| P-14a | ReportSuccess → ReportFailure | different actors holding independent trial callbacks |
| P-14b | ReportFailure → ReportSuccess | different actors holding independent trial callbacks |
| P-15a | TripDecision → ReadState | policy inside lock and competing reader |
| P-15b | ReadState → TripDecision | policy inside lock and competing reader |

## Remembrance semantics (observed in code, not documented intent)

Observed-in-code: admissions consume a counter until a generation reset gobreaker.go and gobreaker.go. Generation is a uint64 gobreaker.go. Request result and returned callback are caller-owned. A retained closure keeps its receiver and generation available gobreaker.go. Breaker stores no per-request history; equality check at gobreaker.go. Lifetime and memory use depend on external references.

## Lock-discipline annotation (observed in code, not documented intent)

Observed-in-code: State gobreaker.go, Counts gobreaker.go, admission gobreaker.go, and completion gobreaker.go take the same mutex. Trip policy gobreaker.go and transition observer gobreaker.go execute in these paths. Request and classifier execute outside the mutex gobreaker.go and gobreaker.go. Settings contracts README.md specify neither reentrancy nor panic policy.

## Catalogue notes

Execute and Allow are alternate public front ends on their respective constructed instances. The internal outcome events describe bookkeeping phases, and do not denote independently callable operations.

## Event annotations (observed in code, not documented intent)

### Configure
- gate (observed in code): payload settings
- upstream_guards (observed in code): Direct Go calls, typed assignments only. No upstream value normalization.
- coverage:
  - loss: UV-20
  - delay: n/a: no independent delivery at this boundary, gobreaker.go.
  - duplication: UV-20
  - out-of-order: n/a: no independent delivery at this boundary, gobreaker.go.
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go.
  - commission: n/a: no independent delivery at this boundary, gobreaker.go.
  - value: UV-21

### Execute
- gate (observed in code): service state for admission
- upstream_guards (observed in code): Direct API has no nil or instance-purpose validation. Example binds its own receiver in example/http_breaker.go.
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-02
  - contradiction: UV-03
  - commission: UV-04
  - value: UV-04

### Allow
- gate (observed in code): service state for admission
- upstream_guards (observed in code): Direct API supplies no caller identity or request lifecycle validation.
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-05
  - contradiction: UV-06
  - commission: UV-04
  - value: UV-04

### ReportSuccess
- gate (observed in code): payload Boolean and service generation and threshold
- upstream_guards (observed in code): Closure binds receiver and generation. No upstream single-shot or result truth guarantee.
- coverage:
  - loss: UV-07
  - delay: UV-08
  - duplication: UV-09
  - out-of-order: UV-08
  - contradiction: UV-09
  - commission: UV-10
  - value: UV-11

### ReportFailure
- gate (observed in code): payload Boolean and service generation and trip policy
- upstream_guards (observed in code): Same caller-side ownership as the success report.
- coverage:
  - loss: UV-07
  - delay: UV-08
  - duplication: UV-09
  - out-of-order: UV-08
  - contradiction: UV-09
  - commission: UV-10
  - value: UV-11

### ReadState
- gate (observed in code): service expiry
- upstream_guards (observed in code): No upstream scheduling or receiver-purpose validation.
- coverage:
  - loss: UV-12
  - delay: UV-12
  - duplication: UV-12
  - out-of-order: UV-12
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go.
  - commission: n/a: no independent delivery at this boundary, gobreaker.go.
  - value: UV-04

### ReadCounts
- gate (observed in code): none beyond receiver and synchronization
- upstream_guards (observed in code): No upstream freshness or receiver-purpose validation.
- coverage:
  - loss: UV-12
  - delay: UV-12
  - duplication: UV-12
  - out-of-order: UV-12
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go.
  - commission: n/a: no independent delivery at this boundary, gobreaker.go.
  - value: UV-04

### ReadName
- gate (observed in code): none
- upstream_guards (observed in code): Name has no uniqueness guarantee. Wrapper delegates at gobreaker.go.
- coverage:
  - loss: UV-12
  - delay: UV-12
  - duplication: UV-12
  - out-of-order: UV-12
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go.
  - commission: n/a: no independent delivery at this boundary, gobreaker.go.
  - value: UV-04

### RequestResult
- gate (observed in code): payload error and request execution path
- upstream_guards (observed in code): A synchronous call returns at most once normally. User function behavior is otherwise unconstrained.
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: n/a: no independent delivery at this boundary, gobreaker.go.
  - out-of-order: UV-08
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go.
  - commission: UV-10
  - value: UV-11

### Classify
- gate (observed in code): payload error
- upstream_guards (observed in code): Configured classifier defaults if nil. No caller-side result or runtime validation.
- coverage:
  - loss: UV-13
  - delay: UV-13
  - duplication: n/a: no independent delivery at this boundary, gobreaker.go.
  - out-of-order: UV-14
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go.
  - commission: UV-10
  - value: UV-11

### TripDecision
- gate (observed in code): payload count snapshot and policy result
- upstream_guards (observed in code): Default is supplied if nil. Call and commit occur under the same breaker lock.
- coverage:
  - loss: UV-15
  - delay: UV-15
  - duplication: n/a: no independent delivery at this boundary, gobreaker.go.
  - out-of-order: n/a: no independent delivery at this boundary, gobreaker.go.
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go.
  - commission: UV-10
  - value: UV-11

### Notify
- gate (observed in code): service callback presence and state change
- upstream_guards (observed in code): No upstream reentrancy or runtime guarantee. Missing hook is supported.
- coverage:
  - loss: UV-16
  - delay: UV-16
  - duplication: UV-17
  - out-of-order: UV-17
  - contradiction: UV-17
  - commission: UV-17
  - value: UV-17

### ObserveExpiry
- gate (observed in code): service state and time
- upstream_guards (observed in code): Clock provides time when invoked. The API exposes no standalone clock-event injection.
- coverage:
  - loss: UV-18
  - delay: UV-18
  - duplication: n/a: no independent delivery at this boundary, gobreaker.go.
  - out-of-order: UV-18
  - contradiction: n/a: no independent delivery at this boundary, gobreaker.go.
  - commission: n/a: no independent delivery at this boundary, gobreaker.go.
  - value: UV-18

### ApplySuccess
- gate (observed in code): service generation, state and threshold
- upstream_guards (observed in code): Completion source and generation are captured at admission.
- coverage:
  - loss: n/a: no independent delivery at this boundary, gobreaker.go.
  - delay: UV-08
  - duplication: UV-09
  - out-of-order: UV-08
  - contradiction: UV-09
  - commission: UV-10
  - value: UV-11

### ApplyFailure
- gate (observed in code): service generation and trip policy
- upstream_guards (observed in code): Completion source and generation are captured at admission.
- coverage:
  - loss: n/a: no independent delivery at this boundary, gobreaker.go.
  - delay: UV-08
  - duplication: UV-09
  - out-of-order: UV-08
  - contradiction: UV-09
  - commission: UV-10
  - value: UV-11

### UV-01
- gate (observed in code): payload execution
- upstream_guards (observed in code): Request runs in caller goroutine. No context in Execute.

### UV-02
- gate (observed in code): service generation and admission
- upstream_guards (observed in code): Direct API supplies no deadline for the workload.

### UV-03
- gate (observed in code): service admission
- upstream_guards (observed in code): No caller identity. A completed Execute returns the payload, with no release API.

### UV-04
- gate (observed in code): receiver and function validity
- upstream_guards (observed in code): Go types do not enforce instance ownership or construction.

### UV-05
- gate (observed in code): service admission
- upstream_guards (observed in code): No context and no teardown operation are supplied.

### UV-06
- gate (observed in code): service admission
- upstream_guards (observed in code): No caller identity or lock fairness guarantee.

### UV-07
- gate (observed in code): service occupancy
- upstream_guards (observed in code): Public contract expects a report and supplies no cancellation API.

### UV-08
- gate (observed in code): service generation
- upstream_guards (observed in code): No public API invalidates a report on application cancellation alone.

### UV-09
- gate (observed in code): payload Boolean and service generation
- upstream_guards (observed in code): No public contract specifies an exactly-once guarantee.

### UV-10
- gate (observed in code): capability presence
- upstream_guards (observed in code): A non-nil callback must come from successful Allow. A caller can invoke nil in Go.

### UV-11
- gate (observed in code): payload Boolean or counts
- upstream_guards (observed in code): Outcome truth is not independently verified.

### UV-12
- gate (observed in code): service snapshot and expiry
- upstream_guards (observed in code): Public calls have no snapshot protocol spanning methods.

### UV-13
- gate (observed in code): payload error and callback runtime
- upstream_guards (observed in code): No failure or latency guarantee in Settings.

### UV-14
- gate (observed in code): service generation at completion
- upstream_guards (observed in code): No reentrancy restriction in Settings.

### UV-15
- gate (observed in code): service lock and callback execution
- upstream_guards (observed in code): No failure, latency or reentrancy guarantee in Settings.

### UV-16
- gate (observed in code): service lock and hook presence
- upstream_guards (observed in code): Optional hook. No failure, latency or reentrancy guarantee in Settings.

### UV-17
- gate (observed in code): payload name and state pair
- upstream_guards (observed in code): No unique identifier or event sequence number.

### UV-18
- gate (observed in code): service state and clock
- upstream_guards (observed in code): No caller can deliver clock payload directly.

### UV-20
- gate (observed in code): receiver identity
- upstream_guards (observed in code): Creation allocates a fresh instance.

### UV-21
- gate (observed in code): payload settings
- upstream_guards (observed in code): Constructor receives values after Go type checking.



=== INPUT 2b: DOCTRINE LINES (from the extraction) ===

- DOC-1 — explicit-requirement README.md ("[gobreaker][repo-url] implements the [Circuit Breaker pattern](https://msdn.microsoft.com/en-us/library/dn589784.aspx) in Go.")
- DOC-2 — explicit-requirement README.md ("The struct `CircuitBreaker` is a state machine to prevent sending requests that are likely to fail.")
- DOC-3 — explicit-requirement README.md ("The function `NewCircuitBreaker` creates a new `CircuitBreaker`.")
- DOC-4 — explicit-requirement README.md ("You can configure `CircuitBreaker` by the struct `Settings`:")
- DOC-5 — explicit-requirement README.md ("`Name` is the name of the `CircuitBreaker`.")
- DOC-6 — explicit-requirement README.md ("`MaxRequests` is the maximum number of requests allowed to pass through when the `CircuitBreaker` is half-open.")
- DOC-7 — explicit-requirement README.md (" If `MaxRequests` is 0, `CircuitBreaker` allows only 1 request.")
- DOC-8 — explicit-requirement README.md ("`Interval` is the cyclic period of the closed state for `CircuitBreaker` to clear the internal `Counts`, described later in this section.")
- DOC-9 — explicit-requirement README.md (" If `Interval` is 0, `CircuitBreaker` doesn't clear the internal `Counts` during the closed state.")
- DOC-10 — explicit-requirement README.md ("`Timeout` is the period of the open state, after which the state of `CircuitBreaker` becomes half-open.")
- DOC-11 — explicit-requirement README.md (" If `Timeout` is 0, the timeout value of `CircuitBreaker` is set to 60 seconds.")
- DOC-12 — explicit-requirement README.md ("`ReadyToTrip` is called with a copy of `Counts` whenever a request fails in the closed state.")
- DOC-13 — explicit-requirement README.md (" If `ReadyToTrip` returns true, `CircuitBreaker` will be placed into the open state.")
- DOC-14 — explicit-requirement README.md (" If `ReadyToTrip` is `nil`, default `ReadyToTrip` is used.")
- DOC-15 — explicit-requirement README.md (" Default `ReadyToTrip` returns true when the number of consecutive failures is more than 5.")
- DOC-16 — explicit-requirement README.md ("`OnStateChange` is called whenever the state of `CircuitBreaker` changes.")
- DOC-17 — explicit-requirement README.md ("`IsSuccessful` is called with the error returned from a request.")
- DOC-18 — explicit-requirement README.md (" If `IsSuccessful` returns true, the error is counted as a success.")
- DOC-19 — explicit-requirement README.md (" Otherwise the error is counted as a failure.")
- DOC-20 — explicit-requirement README.md (" If `IsSuccessful` is nil, default `IsSuccessful` is used, which returns false for all non-nil errors.")
- DOC-21 — explicit-requirement README.md ("The struct `Counts` holds the numbers of requests and their successes/failures:")
- DOC-22 — explicit-requirement README.md ("`CircuitBreaker` clears the internal `Counts` either on the change of the state or at the closed-state intervals.")
- DOC-23 — explicit-requirement README.md ("`Counts` ignores the results of the requests sent before clearing.")
- DOC-24 — explicit-requirement README.md ("`CircuitBreaker` can wrap any function to send a request:")
- DOC-25 — explicit-requirement README.md ("The method `Execute` runs the given request if `CircuitBreaker` accepts it.")
- DOC-26 — explicit-requirement README.md ("`Execute` returns an error instantly if `CircuitBreaker` rejects the request.")
- DOC-27 — explicit-requirement README.md ("Otherwise, `Execute` returns the result of the request.")
- DOC-28 — explicit-requirement README.md ("If a panic occurs in the request, `CircuitBreaker` handles it as an error and causes the same panic again.")

=== INPUT 2: REQUIREMENTS (domain-analysis/circuitBreaker/requirements-prose.md) ===

The struct `CircuitBreaker` is a state machine to prevent sending requests that are likely to fail.
The function `NewCircuitBreaker` creates a new `CircuitBreaker`.

You can configure `CircuitBreaker` by the struct `Settings`:

- `Name` is the name of the `CircuitBreaker`.

- `MaxRequests` is the maximum number of requests allowed to pass through
  when the `CircuitBreaker` is half-open.
  If `MaxRequests` is 0, `CircuitBreaker` allows only 1 request.

- `Interval` is the cyclic period of the closed state
  for `CircuitBreaker` to clear the internal `Counts`, described later in this section.
  If `Interval` is 0, `CircuitBreaker` doesn't clear the internal `Counts` during the closed state.

- `Timeout` is the period of the open state,
  after which the state of `CircuitBreaker` becomes half-open.
  If `Timeout` is 0, the timeout value of `CircuitBreaker` is set to 60 seconds.

- `ReadyToTrip` is called with a copy of `Counts` whenever a request fails in the closed state.
  If `ReadyToTrip` returns true, `CircuitBreaker` will be placed into the open state.
  If `ReadyToTrip` is `nil`, default `ReadyToTrip` is used.
  Default `ReadyToTrip` returns true when the number of consecutive failures is more than 5.

- `OnStateChange` is called whenever the state of `CircuitBreaker` changes.

- `IsSuccessful` is called with the error returned from a request.
  If `IsSuccessful` returns true, the error is counted as a success.
  Otherwise the error is counted as a failure.
  If `IsSuccessful` is nil, default `IsSuccessful` is used, which returns false for all non-nil errors.

The struct `Counts` holds the numbers of requests and their successes/failures:

`CircuitBreaker` clears the internal `Counts` either
on the change of the state or at the closed-state intervals.
`Counts` ignores the results of the requests sent before clearing.

`CircuitBreaker` can wrap any function to send a request:

The method `Execute` runs the given request if `CircuitBreaker` accepts it.
`Execute` returns an error instantly if `CircuitBreaker` rejects the request.
Otherwise, `Execute` returns the result of the request.
If a panic occurs in the request, `CircuitBreaker` handles it as an error
and causes the same panic again.


=== INPUT 3: EVENT CONTRACT TEXTS (domain-analysis/circuitBreaker/event-contracts.md) ===

gobreaker.go:23
	// ErrTooManyRequests is returned when the CB state is half open and the requests count is over the cb maxRequests

gobreaker.go:25
	// ErrOpenState is returned when the CB state is open

gobreaker.go:43
// Counts holds the numbers of requests and their successes/failures.
// CircuitBreaker clears the internal Counts either
// on the change of the state or at the closed-state intervals.
// Counts ignores the results of the requests sent before clearing.

gobreaker.go:79
// Settings configures CircuitBreaker:
//
// Name is the name of the CircuitBreaker.
//
// MaxRequests is the maximum number of requests allowed to pass through
// when the CircuitBreaker is half-open.
// If MaxRequests is 0, the CircuitBreaker allows only 1 request.
//
// Interval is the cyclic period of the closed state
// for the CircuitBreaker to clear the internal Counts.
// If Interval is less than or equal to 0, the CircuitBreaker doesn't clear internal Counts during the closed state.
//
// Timeout is the period of the open state,
// after which the state of the CircuitBreaker becomes half-open.
// If Timeout is less than or equal to 0, the timeout value of the CircuitBreaker is set to 60 seconds.
//
// ReadyToTrip is called with a copy of Counts whenever a request fails in the closed state.
// If ReadyToTrip returns true, the CircuitBreaker will be placed into the open state.
// If ReadyToTrip is nil, default ReadyToTrip is used.
// Default ReadyToTrip returns true when the number of consecutive failures is more than 5.
//
// OnStateChange is called whenever the state of the CircuitBreaker changes.
//
// IsSuccessful is called with the error returned from a request.
// If IsSuccessful returns true, the error is counted as a success.
// Otherwise the error is counted as a failure.
// If IsSuccessful is nil, default IsSuccessful is used, which returns false for all non-nil errors.

gobreaker.go:133
// TwoStepCircuitBreaker is like CircuitBreaker but instead of surrounding a function
// with the breaker functionality, it only checks whether a request can proceed and
// expects the caller to report the outcome in a separate step using a callback.

gobreaker.go:140
// NewCircuitBreaker returns a new CircuitBreaker configured with the given Settings.

gobreaker.go:182
// NewTwoStepCircuitBreaker returns a new TwoStepCircuitBreaker configured with the given Settings.

gobreaker.go:200
// Name returns the name of the CircuitBreaker.

gobreaker.go:205
// State returns the current state of the CircuitBreaker.

gobreaker.go:215
// Counts returns internal counters

gobreaker.go:223
// Execute runs the given request if the CircuitBreaker accepts it.
// Execute returns an error instantly if the CircuitBreaker rejects the request.
// Otherwise, Execute returns the result of the request.
// If a panic occurs in the request, the CircuitBreaker handles it as an error
// and causes the same panic again.

gobreaker.go:247
// Name returns the name of the TwoStepCircuitBreaker.

gobreaker.go:252
// State returns the current state of the TwoStepCircuitBreaker.

gobreaker.go:257
// Counts returns internal counters

gobreaker.go:262
// Allow checks if a new request can proceed. It returns a callback that should be used to
// register the success or failure in a separate step. If the circuit breaker doesn't allow
// requests, it returns an error.


Respond with ONLY the table and the coverage checklist: every catalogue event and pair-ordering id, listed once in the checklist, ticked. A missing row must be impossible to miss.
The coverage checklist must use one exact line per event or pair in the form '- [x] EVENT_ID', with no other text on that line.
