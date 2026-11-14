You are the BLIND adversarial pass (Part B) of a domain-behaviour analysis. You have NO access to the implementation. Do NOT read any files, do NOT use any tools, do NOT search any repository — the inputs below are complete and are your ONLY sources. If you catch yourself wanting to look something up, label it an open point instead.

TASK: Here is the event catalogue of a component, and its requirements. For every event — including undesired variants and both orderings of every interaction pair — state in which situations the component should handle, ignore, or reject it, and what should happen. Describe situations in requirement terms. Name states per PA-17 (state naming convention): prefer public API names, name sub-states by their condition, use PascalCase with `_` as separator. If you must assume a lifecycle state the requirements do not name, label it `assumed-state:` with the condition that defines it. You have no access to the implementation. Be concrete. Produce a table keyed by the catalogue's event ids and pair-ordering ids. Prefer one row per id with conditional outcomes. If you split an id into several rows, use an explicit `Situation` column with distinct, nonempty labels. Do not repeat the same situation. End with a coverage checklist: every catalogue event id, listed once, ticked. A missing row must be impossible to miss.

Catalogue headings and fields labelled `observed in code` say what the implementation does, not what it should do. Base each row on the requirements, the contracts and the doctrine lines. When a row's expected behaviour rests only on observed-in-code text, start its behaviour cell with `as-is:`.

<!-- generated:rules key=partb-vocab -->
The disposition vocabulary you must use (from the methods reference): `transition → <target>` | `handle` (stays in the state, does something) | `ignore (documented)` | `ignore (accidental)` | `defer (queued)` | `reject` (a declared refusal signal: error, diagnostic, nack) | `UNSPECIFIED`. Without these definitions a blind pass applies `reject` and `handle` to identical semantics interchangeably (dobby trigger-service, 2026-08-05: four vocabulary-only "divergences").
<!-- /generated:rules -->

The catalogue's event ids are: Admission StateRead CountsRead NameRead Report Result Classify TripDecision Notify Setup Expiry Complete UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 UV-15 UV-16 UV-17 UV-18 UV-19 UV-20 UV-21 UV-22 UV-23 — plus the pair orderings P-01a P-01b P-02a P-02b P-03a P-03b P-04a P-04b P-05a P-05b P-06a P-06b P-07a P-07b P-08a P-08b P-09a P-09b P-10a P-10b P-11a P-11b P-12a P-12b P-13a P-13b P-14a P-14b P-15a P-15b P-16a P-16b P-17a P-17b P-18a P-18b.

=== INPUT 1: EVENT CATALOGUE (code fragments and analysis references removed) ===

# Event catalogue

<!-- event-ids: Admission StateRead CountsRead NameRead Report Result Classify TripDecision Notify Setup Expiry Complete UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 UV-15 UV-16 UV-17 UV-18 UV-19 UV-20 UV-21 UV-22 UV-23 -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| Admission | external | request caller | Execute or Allow asks permission for one operation. observed-in-code gobreaker.go. |
| StateRead | external | state observer | State reads the breaker state. observed-in-code gobreaker.go. |
| CountsRead | external | metrics observer | Counts reads the current counters. observed-in-code gobreaker.go. |
| NameRead | external | identity observer | Name reads the configured name. observed-in-code gobreaker.go. |
| Report | external | TwoStep completion owner | Invoke the callback returned by Allow with a Boolean outcome. observed-in-code gobreaker.go. |
| Result | external | Execute request function | The admitted request returns value and error, or unwinds via panic. observed-in-code gobreaker.go. |
| Classify | external | IsSuccessful callback | Classify the request error before submitting the result. observed-in-code gobreaker.go. |
| TripDecision | external | ReadyToTrip callback | Policy receives a copy of Counts and returns whether to trip. observed-in-code gobreaker.go. |
| Notify | external | OnStateChange callback | Receive breaker name and previous and next states. observed-in-code gobreaker.go. |
| Setup | external | lifecycle owner | Construct a breaker with Settings, optionally via the TwoStep constructor. observed-in-code gobreaker.go. |
| Expiry | internal | clock observed at boundary | Evaluate elapsed closed interval or open cooldown on eligible calls. observed-in-code gobreaker.go. |
| Complete | internal | completion dispatch | Apply outcome after sampling time and checking the admission generation. observed-in-code gobreaker.go. |
| UV-01 | external | Admission / request caller | Caller never invokes an acquisition. observed-in-code gobreaker.go. |
| UV-02 | external | Admission / request caller | Admission is delayed across a boundary or mutex wait. observed-in-code gobreaker.go. |
| UV-03 | external | Admission / request caller | Same caller makes a second admission while the first is pending or while its operation or report callback remains held. Includes simultaneous admissions. observed-in-code gobreaker.go. |
| UV-04 | external | Admission / request caller | Call uses the wrong initialized breaker, a nil or zero receiver, or passes a nil Execute function. observed-in-code gobreaker.go. |
| UV-05 | external | StateRead / state observer | Observer omits or delays State, Counts or Name. Also covers time passing without an eligible call. observed-in-code gobreaker.go. |
| UV-06 | external | StateRead / state observer | Observer reads repeatedly, concurrently, or at the wrong time. Includes Counts and Name. observed-in-code gobreaker.go. |
| UV-07 | external | Report / TwoStep completion owner | Caller abandons the returned callback or omits a report indefinitely. observed-in-code gobreaker.go. |
| UV-08 | external | Report / TwoStep completion owner | Delayed Execute or TwoStep outcome before or after generation change. Includes classification that crosses the boundary. observed-in-code gobreaker.go. |
| UV-09 | external | Report / TwoStep completion owner | Repeat a report with the same outcome in its original generation or after clearing. observed-in-code gobreaker.go. |
| UV-10 | external | Report / TwoStep completion owner | Concurrent contradictory reports on the same callback. observed-in-code gobreaker.go. |
| UV-11 | external | Report / TwoStep completion owner | Attempt to report with no granted callback, including invoking nil returned on refusal. observed-in-code gobreaker.go. |
| UV-12 | external | Report / TwoStep completion owner | Supply a plausible wrong Boolean or invoke another live operation's callback. observed-in-code gobreaker.go. |
| UV-13 | external | Result / Execute request function | Request hangs, panics, exits its goroutine, or returns after cancellation by its caller. observed-in-code gobreaker.go. |
| UV-14 | external | Result / Execute request function | Request returns a plausible wrong result or error, including typed nil error. observed-in-code gobreaker.go. |
| UV-15 | external | Classify / IsSuccessful callback | IsSuccessful blocks, panics or exits its goroutine. observed-in-code gobreaker.go. |
| UV-16 | external | Classify / IsSuccessful callback | Concurrent invocations use shared caller policy state or classify a plausible error unexpectedly. observed-in-code gobreaker.go. |
| UV-17 | external | TripDecision / ReadyToTrip callback | ReadyToTrip blocks, panics, exits its goroutine or reenters a lock-taking method. observed-in-code gobreaker.go. |
| UV-18 | external | Notify / OnStateChange callback | OnStateChange blocks, panics, exits its goroutine or reenters a lock-taking method. observed-in-code gobreaker.go. |
| UV-19 | external | Notify / OnStateChange callback | Policy or notification crosses an expiry while holding the mutex, or callback reenters by scheduling a separate goroutine. observed-in-code gobreaker.go. |
| UV-20 | external | Notify / OnStateChange callback | User callback refers to the wrong breaker or returns a surprising policy decision. observed-in-code gobreaker.go. |
| UV-21 | external | Setup / lifecycle owner | Owner omits, delays, repeats, replaces, or abandons construction. Includes calls on the old object after replacement. observed-in-code gobreaker.go. |
| UV-22 | external | Setup / lifecycle owner | Use zero or negative durations, very large limits, unintended valid policies or a copied breaker. observed-in-code gobreaker.go. |
| UV-23 | internal | Expiry / clock observed at boundary | Sample before, at, or after deadline, after a long delay, or with a clock anomaly. observed-in-code gobreaker.go. |

## Undesired-coverage (observed in code, not documented intent)

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| Admission: request caller | UV-01 | UV-02 | UV-03 | UV-02 | UV-03 | UV-04 | UV-04 |
| StateRead: state observer | UV-05 | UV-05 | UV-06 | UV-06 | UV-06 | UV-06 | UV-04 |
| CountsRead: metrics observer | UV-05 | UV-05 | UV-06 | UV-06 | UV-06 | UV-06 | UV-04 |
| NameRead: identity observer | UV-05 | UV-05 | UV-06 | UV-06 | UV-06 | UV-06 | UV-04 |
| Report: TwoStep completion owner | UV-07 | UV-08 | UV-09 | UV-08 | UV-10 | UV-11 | UV-12 |
| Result: Execute request function | UV-13 | UV-13 | n/a: one Go invocation has one ordinary return. gobreaker.go | UV-08 | n/a: one invocation has one ordinary return or panic. gobreaker.go | n/a: execution follows successful admission. gobreaker.go | UV-14 |
| Classify: IsSuccessful callback | UV-15 | UV-15 | n/a: one call per normal return. gobreaker.go | UV-08 | UV-16 | n/a: invocation follows normal request return. gobreaker.go | UV-16 |
| TripDecision: ReadyToTrip callback | UV-17 | UV-17 | n/a: one call per current closed failure. gobreaker.go | UV-19 | UV-17 | n/a: invocation follows current closed failure. gobreaker.go | UV-20 |
| Notify: OnStateChange callback | UV-18 | UV-18 | n/a: one synchronous call per setState change. gobreaker.go | UV-19 | UV-18 | n/a: same-state update returns before hook. gobreaker.go | UV-20 |
| Setup: lifecycle owner | UV-21 | UV-21 | UV-21 | UV-21 | UV-21 | UV-21 | UV-22 |
| Expiry: clock observed at boundary | UV-05 | UV-23 | n/a: one check per operation; clearing replaces the deadline. gobreaker.go | UV-23 | n/a: one stored state selects deadline kind. gobreaker.go | n/a: evaluation is inline on an eligible operation. gobreaker.go | UV-23 |
| Complete: completion dispatch | UV-07 | UV-08 | UV-09 | UV-08 | UV-10 | n/a: private method with causal callers. gobreaker.go | UV-12 |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Admission → StateRead | observer samples recovery before or after admission |
| P-01b | StateRead → Admission | observer samples recovery before or after admission |
| P-02a | Admission → CountsRead | snapshot before or after admission commit |
| P-02b | CountsRead → Admission | snapshot before or after admission commit |
| P-03a | Admission → Report | TwoStep contenders, completion versus next admission |
| P-03b | Report → Admission | TwoStep contenders, completion versus next admission |
| P-04a | Admission → Result | Execute contenders, result versus next admission |
| P-04b | Result → Admission | Execute contenders, result versus next admission |
| P-05a | StateRead → Report | TwoStep observer versus report across deadline |
| P-05b | Report → StateRead | TwoStep observer versus report across deadline |
| P-06a | StateRead → Result | Execute observer versus returned result across deadline |
| P-06b | Result → StateRead | Execute observer versus returned result across deadline |
| P-07a | CountsRead → Report | TwoStep metrics versus report or generation reset |
| P-07b | Report → CountsRead | TwoStep metrics versus report or generation reset |
| P-08a | CountsRead → Result | Execute metrics versus completion |
| P-08b | Result → CountsRead | Execute metrics versus completion |
| P-09a | StateRead → CountsRead | state refresh versus raw counter observation |
| P-09b | CountsRead → StateRead | state refresh versus raw counter observation |
| P-10a | Admission → Classify | Execute contender versus classification delay |
| P-10b | Classify → Admission | Execute contender versus classification delay |
| P-11a | StateRead → Classify | state refresh while classifier is running |
| P-11b | Classify → StateRead | state refresh while classifier is running |
| P-12a | CountsRead → Classify | raw count while classifier is running |
| P-12b | Classify → CountsRead | raw count while classifier is running |
| P-13a | Admission → TripDecision | contender versus locked policy |
| P-13b | TripDecision → Admission | contender versus locked policy |
| P-14a | StateRead → TripDecision | state observation versus locked policy |
| P-14b | TripDecision → StateRead | state observation versus locked policy |
| P-15a | CountsRead → TripDecision | raw snapshot versus locked policy |
| P-15b | TripDecision → CountsRead | raw snapshot versus locked policy |
| P-16a | Admission → Notify | contender versus locked notification |
| P-16b | Notify → Admission | contender versus locked notification |
| P-17a | StateRead → Notify | state observer versus locked notification |
| P-17b | Notify → StateRead | state observer versus locked notification |
| P-18a | CountsRead → Notify | raw snapshot versus locked notification |
| P-18b | Notify → CountsRead | raw snapshot versus locked notification |

## Remembrance semantics (observed in code, not documented intent)

Observed-in-code. Generation and counters are stored per instance gobreaker.go. Reset increments generation and clears all counters gobreaker.go gobreaker.go. Admission counts once gobreaker.go and reports do not release that admission count gobreaker.go. Old reports compare only generation gobreaker.go. Execute stack and retained Allow callback keep their captured values gobreaker.go gobreaker.go. No per-request history, queue, retention limit for caller-held closures, cancellation or shutdown entry point appears in the public surface gobreaker.go.

## Lock-discipline annotation (observed in code, not documented intent)

Observed-in-code. State, Counts, admission and completion acquire the same mutex gobreaker.go gobreaker.go gobreaker.go gobreaker.go. ReadyToTrip and OnStateChange are invoked from lock-held paths gobreaker.go gobreaker.go. The Settings docs describe invocation gobreaker.go gobreaker.go and give no reentry contract. Execute request and IsSuccessful run between the admission unlock and completion lock gobreaker.go gobreaker.go. Name reads the immutable configured name gobreaker.go.

## Catalogue notes

Setup belongs to the lifecycle before the active grid. Execute and Allow are alternate entry points on separately constructed public types. Source labels distinguish actors whose work can overlap on one instance. Omission rows describe consequences of absent stimuli.

## Event annotations (observed in code, not documented intent)

### Admission
- gate (observed in code): service-side state, current time and admitted request count
- upstream_guards (observed in code): No production caller validation supplied. Allow delegates to the same admission path gobreaker.go
- coverage:
  - loss: UV-01
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-02
  - contradiction: UV-03
  - commission: UV-04
  - value: UV-04

### StateRead
- gate (observed in code): service-side state and time
- upstream_guards (observed in code): No caller validation supplied gobreaker.go
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-06
  - contradiction: UV-06
  - commission: UV-06
  - value: UV-04

### CountsRead
- gate (observed in code): service-side snapshot
- upstream_guards (observed in code): No caller validation supplied gobreaker.go
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-06
  - contradiction: UV-06
  - commission: UV-06
  - value: UV-04

### NameRead
- gate (observed in code): service-side immutable setting
- upstream_guards (observed in code): No caller validation supplied gobreaker.go
- coverage:
  - loss: UV-05
  - delay: UV-05
  - duplication: UV-06
  - out-of-order: UV-06
  - contradiction: UV-06
  - commission: UV-06
  - value: UV-04

### Report
- gate (observed in code): payload Boolean and service-side generation, state and recovery counts
- upstream_guards (observed in code): Only successful Allow returns a callback. No once or truth guarantee gobreaker.go
- coverage:
  - loss: UV-07
  - delay: UV-08
  - duplication: UV-09
  - out-of-order: UV-08
  - contradiction: UV-10
  - commission: UV-11
  - value: UV-12

### Result
- gate (observed in code): payload outcome and service-side admission generation
- upstream_guards (observed in code): Execute invokes request only after admission. No guarantee on user code returning gobreaker.go
- coverage:
  - loss: UV-13
  - delay: UV-13
  - duplication: n/a: one Go invocation has one ordinary return. gobreaker.go
  - out-of-order: UV-08
  - contradiction: n/a: one invocation has one ordinary return or panic. gobreaker.go
  - commission: n/a: execution follows successful admission. gobreaker.go
  - value: UV-14

### Classify
- gate (observed in code): payload error and callback outcome
- upstream_guards (observed in code): Constructor supplies default when nil. User termination and serialization guarantees absent gobreaker.go
- coverage:
  - loss: UV-15
  - delay: UV-15
  - duplication: n/a: one call per normal return. gobreaker.go
  - out-of-order: UV-08
  - contradiction: UV-16
  - commission: n/a: invocation follows normal request return. gobreaker.go
  - value: UV-16

### TripDecision
- gate (observed in code): payload Counts and policy Boolean
- upstream_guards (observed in code): Constructor supplies default when nil. User termination guarantee absent gobreaker.go
- coverage:
  - loss: UV-17
  - delay: UV-17
  - duplication: n/a: one call per current closed failure. gobreaker.go
  - out-of-order: UV-19
  - contradiction: UV-17
  - commission: n/a: invocation follows current closed failure. gobreaker.go
  - value: UV-20

### Notify
- gate (observed in code): service-side state change and callback presence
- upstream_guards (observed in code): Constructor copies hook. User termination and reentry guarantees absent gobreaker.go
- coverage:
  - loss: UV-18
  - delay: UV-18
  - duplication: n/a: one synchronous call per setState change. gobreaker.go
  - out-of-order: UV-19
  - contradiction: UV-18
  - commission: n/a: same-state update returns before hook. gobreaker.go
  - value: UV-20

### Setup
- gate (observed in code): payload configuration
- upstream_guards (observed in code): Zero and negative duration handling in constructor. No caller validation supplied gobreaker.go
- coverage:
  - loss: UV-21
  - delay: UV-21
  - duplication: UV-21
  - out-of-order: UV-21
  - contradiction: UV-21
  - commission: UV-21
  - value: UV-22

### Expiry
- gate (observed in code): service-side deadline and sampled time
- upstream_guards (observed in code): Clock sampled from time.Now under mutex for State, admission, and completion gobreaker.go
- coverage:
  - loss: UV-05
  - delay: UV-23
  - duplication: n/a: one check per operation; clearing replaces the deadline. gobreaker.go
  - out-of-order: UV-23
  - contradiction: n/a: one stored state selects deadline kind. gobreaker.go
  - commission: n/a: evaluation is inline on an eligible operation. gobreaker.go
  - value: UV-23

### Complete
- gate (observed in code): payload success and service-side generation and state
- upstream_guards (observed in code): Private dispatch from Execute or Allow only gobreaker.go
- coverage:
  - loss: UV-07
  - delay: UV-08
  - duplication: UV-09
  - out-of-order: UV-08
  - contradiction: UV-10
  - commission: n/a: private method with causal callers. gobreaker.go
  - value: UV-12

### UV-01
- gate (observed in code): service-side state, current time and admitted request count
- upstream_guards (observed in code): No production caller validation supplied. Allow delegates to the same admission path gobreaker.go

### UV-02
- gate (observed in code): service-side state, current time and admitted request count
- upstream_guards (observed in code): No production caller validation supplied. Allow delegates to the same admission path gobreaker.go

### UV-03
- gate (observed in code): service-side state, current time and admitted request count
- upstream_guards (observed in code): No production caller validation supplied. Allow delegates to the same admission path gobreaker.go

### UV-04
- gate (observed in code): service-side state, current time and admitted request count
- upstream_guards (observed in code): No production caller validation supplied. Allow delegates to the same admission path gobreaker.go

### UV-05
- gate (observed in code): service-side state and time
- upstream_guards (observed in code): No caller validation supplied gobreaker.go

### UV-06
- gate (observed in code): service-side state and time
- upstream_guards (observed in code): No caller validation supplied gobreaker.go

### UV-07
- gate (observed in code): payload Boolean and service-side generation, state and recovery counts
- upstream_guards (observed in code): Only successful Allow returns a callback. No once or truth guarantee gobreaker.go

### UV-08
- gate (observed in code): payload Boolean and service-side generation, state and recovery counts
- upstream_guards (observed in code): Only successful Allow returns a callback. No once or truth guarantee gobreaker.go

### UV-09
- gate (observed in code): payload Boolean and service-side generation, state and recovery counts
- upstream_guards (observed in code): Only successful Allow returns a callback. No once or truth guarantee gobreaker.go

### UV-10
- gate (observed in code): payload Boolean and service-side generation, state and recovery counts
- upstream_guards (observed in code): Only successful Allow returns a callback. No once or truth guarantee gobreaker.go

### UV-11
- gate (observed in code): payload Boolean and service-side generation, state and recovery counts
- upstream_guards (observed in code): Only successful Allow returns a callback. No once or truth guarantee gobreaker.go

### UV-12
- gate (observed in code): payload Boolean and service-side generation, state and recovery counts
- upstream_guards (observed in code): Only successful Allow returns a callback. No once or truth guarantee gobreaker.go

### UV-13
- gate (observed in code): payload outcome and service-side admission generation
- upstream_guards (observed in code): Execute invokes request only after admission. No guarantee on user code returning gobreaker.go

### UV-14
- gate (observed in code): payload outcome and service-side admission generation
- upstream_guards (observed in code): Execute invokes request only after admission. No guarantee on user code returning gobreaker.go

### UV-15
- gate (observed in code): payload error and callback outcome
- upstream_guards (observed in code): Constructor supplies default when nil. User termination and serialization guarantees absent gobreaker.go

### UV-16
- gate (observed in code): payload error and callback outcome
- upstream_guards (observed in code): Constructor supplies default when nil. User termination and serialization guarantees absent gobreaker.go

### UV-17
- gate (observed in code): payload Counts and policy Boolean
- upstream_guards (observed in code): Constructor supplies default when nil. User termination guarantee absent gobreaker.go

### UV-18
- gate (observed in code): service-side state change and callback presence
- upstream_guards (observed in code): Constructor copies hook. User termination and reentry guarantees absent gobreaker.go

### UV-19
- gate (observed in code): service-side state change and callback presence
- upstream_guards (observed in code): Constructor copies hook. User termination and reentry guarantees absent gobreaker.go

### UV-20
- gate (observed in code): service-side state change and callback presence
- upstream_guards (observed in code): Constructor copies hook. User termination and reentry guarantees absent gobreaker.go

### UV-21
- gate (observed in code): payload configuration
- upstream_guards (observed in code): Zero and negative duration handling in constructor. No caller validation supplied gobreaker.go

### UV-22
- gate (observed in code): payload configuration
- upstream_guards (observed in code): Zero and negative duration handling in constructor. No caller validation supplied gobreaker.go

### UV-23
- gate (observed in code): service-side deadline and sampled time
- upstream_guards (observed in code): Clock sampled from time.Now under mutex for State, admission, and completion gobreaker.go



=== INPUT 2b: DOCTRINE LINES (from the extraction) ===

- DOC-1 explicit-requirement README.md ("The struct `CircuitBreaker` is a state machine to prevent sending requests that are likely to fail.")
- DOC-2 explicit-requirement README.md ("The function `NewCircuitBreaker` creates a new `CircuitBreaker`.")
- DOC-3 explicit-requirement README.md ("You can configure `CircuitBreaker` by the struct `Settings`:")
- DOC-4 explicit-requirement README.md ("`Name` is the name of the `CircuitBreaker`.")
- DOC-5 explicit-requirement README.md ("`MaxRequests` is the maximum number of requests allowed to pass through when the `CircuitBreaker` is half-open.")
- DOC-6 explicit-requirement README.md ("If `MaxRequests` is 0, `CircuitBreaker` allows only 1 request.")
- DOC-7 explicit-requirement README.md ("`Interval` is the cyclic period of the closed state for `CircuitBreaker` to clear the internal `Counts`, described later in this section.")
- DOC-8 explicit-requirement README.md ("If `Interval` is 0, `CircuitBreaker` doesn't clear the internal `Counts` during the closed state.")
- DOC-9 explicit-requirement README.md ("`Timeout` is the period of the open state, after which the state of `CircuitBreaker` becomes half-open.")
- DOC-10 explicit-requirement README.md ("If `Timeout` is 0, the timeout value of `CircuitBreaker` is set to 60 seconds.")
- DOC-11 explicit-requirement README.md ("`ReadyToTrip` is called with a copy of `Counts` whenever a request fails in the closed state.")
- DOC-12 explicit-requirement README.md ("If `ReadyToTrip` returns true, `CircuitBreaker` will be placed into the open state.")
- DOC-13 explicit-requirement README.md ("If `ReadyToTrip` is `nil`, default `ReadyToTrip` is used.")
- DOC-14 explicit-requirement README.md ("Default `ReadyToTrip` returns true when the number of consecutive failures is more than 5.")
- DOC-15 explicit-requirement README.md ("`OnStateChange` is called whenever the state of `CircuitBreaker` changes.")
- DOC-16 explicit-requirement README.md ("`IsSuccessful` is called with the error returned from a request.")
- DOC-17 explicit-requirement README.md ("If `IsSuccessful` returns true, the error is counted as a success.")
- DOC-18 explicit-requirement README.md ("Otherwise the error is counted as a failure.")
- DOC-19 explicit-requirement README.md ("If `IsSuccessful` is nil, default `IsSuccessful` is used, which returns false for all non-nil errors.")
- DOC-20 explicit-requirement README.md ("The struct `Counts` holds the numbers of requests and their successes/failures:")
- DOC-21 explicit-requirement README.md ("`CircuitBreaker` clears the internal `Counts` either on the change of the state or at the closed-state intervals.")
- DOC-22 explicit-requirement README.md ("`Counts` ignores the results of the requests sent before clearing.")
- DOC-23 explicit-requirement README.md ("`CircuitBreaker` can wrap any function to send a request:")
- DOC-24 explicit-requirement README.md ("The method `Execute` runs the given request if `CircuitBreaker` accepts it.")
- DOC-25 explicit-requirement README.md ("`Execute` returns an error instantly if `CircuitBreaker` rejects the request.")
- DOC-26 explicit-requirement README.md ("Otherwise, `Execute` returns the result of the request.")
- DOC-27 explicit-requirement README.md ("If a panic occurs in the request, `CircuitBreaker` handles it as an error and causes the same panic again.")

=== INPUT 2: REQUIREMENTS (domain-analysis/circuitBreaker/requirements-prose.md) ===

gobreaker
=========

[![GoDoc](https://godoc.org/github.com/sony/gobreaker?status.svg)](https://godoc.org/github.com/sony/gobreaker)

[gobreaker][repo-url] implements the [Circuit Breaker pattern](https://msdn.microsoft.com/en-us/library/dn589784.aspx) in Go.

Installation
------------


Usage
-----

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

Example


=== INPUT 3: EVENT CONTRACT TEXTS (domain-analysis/circuitBreaker/event-contracts.md) ===

gobreaker.go:23

ErrTooManyRequests is returned when the CB state is half open and the requests count is over the cb maxRequests

gobreaker.go:25

ErrOpenState is returned when the CB state is open

gobreaker.go:29

String implements stringer interface.

gobreaker.go:43-46

Counts holds the numbers of requests and their successes/failures.
CircuitBreaker clears the internal Counts either
on the change of the state or at the closed-state intervals.
Counts ignores the results of the requests sent before clearing.

gobreaker.go:79-105

Settings configures CircuitBreaker:

Name is the name of the CircuitBreaker.

MaxRequests is the maximum number of requests allowed to pass through
when the CircuitBreaker is half-open.
If MaxRequests is 0, the CircuitBreaker allows only 1 request.

Interval is the cyclic period of the closed state
for the CircuitBreaker to clear the internal Counts.
If Interval is less than or equal to 0, the CircuitBreaker doesn't clear internal Counts during the closed state.

Timeout is the period of the open state,
after which the state of the CircuitBreaker becomes half-open.
If Timeout is less than or equal to 0, the timeout value of the CircuitBreaker is set to 60 seconds.

ReadyToTrip is called with a copy of Counts whenever a request fails in the closed state.
If ReadyToTrip returns true, the CircuitBreaker will be placed into the open state.
If ReadyToTrip is nil, default ReadyToTrip is used.
Default ReadyToTrip returns true when the number of consecutive failures is more than 5.

OnStateChange is called whenever the state of the CircuitBreaker changes.

IsSuccessful is called with the error returned from a request.
If IsSuccessful returns true, the error is counted as a success.
Otherwise the error is counted as a failure.
If IsSuccessful is nil, default IsSuccessful is used, which returns false for all non-nil errors.

gobreaker.go:116

CircuitBreaker is a state machine to prevent sending requests that are likely to fail.

gobreaker.go:133-135

TwoStepCircuitBreaker is like CircuitBreaker but instead of surrounding a function
with the breaker functionality, it only checks whether a request can proceed and
expects the caller to report the outcome in a separate step using a callback.

gobreaker.go:140

NewCircuitBreaker returns a new CircuitBreaker configured with the given Settings.

gobreaker.go:182

NewTwoStepCircuitBreaker returns a new TwoStepCircuitBreaker configured with the given Settings.

gobreaker.go:200

Name returns the name of the CircuitBreaker.

gobreaker.go:205

State returns the current state of the CircuitBreaker.

gobreaker.go:215

Counts returns internal counters

gobreaker.go:223-227

Execute runs the given request if the CircuitBreaker accepts it.
Execute returns an error instantly if the CircuitBreaker rejects the request.
Otherwise, Execute returns the result of the request.
If a panic occurs in the request, the CircuitBreaker handles it as an error
and causes the same panic again.

gobreaker.go:247

Name returns the name of the TwoStepCircuitBreaker.

gobreaker.go:252

State returns the current state of the TwoStepCircuitBreaker.

gobreaker.go:257

Counts returns internal counters

gobreaker.go:262-264

Allow checks if a new request can proceed. It returns a callback that should be used to
register the success or failure in a separate step. If the circuit breaker doesn't allow
requests, it returns an error.


Respond with ONLY the table and the coverage checklist: every catalogue event and pair-ordering id, listed once in the checklist, ticked. A missing row must be impossible to miss.
The coverage checklist must use one exact line per event or pair in the form '- [x] EVENT_ID', with no other text on that line.
