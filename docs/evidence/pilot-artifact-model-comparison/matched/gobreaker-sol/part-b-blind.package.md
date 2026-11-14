You are the BLIND adversarial pass (Part B) of a domain-behaviour analysis. You have NO access to the implementation. Do NOT read any files, do NOT use any tools, do NOT search any repository — the inputs below are complete and are your ONLY sources. If you catch yourself wanting to look something up, label it an open point instead.

TASK: Here is the event catalogue of a component, and its requirements. For every event — including undesired variants and both orderings of every interaction pair — state in which situations the component should handle, ignore, or reject it, and what should happen. Describe situations in requirement terms. Name states per PA-17 (state naming convention): prefer public API names, name sub-states by their condition, use PascalCase with `_` as separator. If you must assume a lifecycle state the requirements do not name, label it `assumed-state:` with the condition that defines it. You have no access to the implementation. Be concrete. Produce a table keyed by the catalogue's event ids and pair-ordering ids. Prefer one row per id with conditional outcomes. If you split an id into several rows, use an explicit `Situation` column with distinct, nonempty labels. Do not repeat the same situation. End with a coverage checklist: every catalogue event id, listed once, ticked. A missing row must be impossible to miss.

Catalogue headings and fields labelled `observed in code` say what the implementation does, not what it should do. Base each row on the requirements, the contracts and the doctrine lines. When a row's expected behaviour rests only on observed-in-code text, start its behaviour cell with `as-is:`.

<!-- generated:rules key=partb-vocab -->
The disposition vocabulary you must use (from the methods reference): `transition → <target>` | `handle` (stays in the state, does something) | `ignore (documented)` | `ignore (accidental)` | `defer (queued)` | `reject` (a declared refusal signal: error, diagnostic, nack) | `UNSPECIFIED`. Without these definitions a blind pass applies `reject` and `handle` to identical semantics interchangeably (dobby trigger-service, 2026-08-05: four vocabulary-only "divergences").
<!-- /generated:rules -->

The catalogue's event ids are: Create Admit State Counts Name Report Return Panic Classify TripPolicy Notify Expiry UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 — plus the pair orderings P-01a P-01b P-02a P-02b P-03a P-03b P-04a P-04b P-05a P-05b P-06a P-06b P-07a P-07b P-08a P-08b P-09a P-09b P-10a P-10b P-11a P-11b P-12a P-12b P-13a P-13b P-14a P-14b P-15a P-15b P-16a P-16b.

=== INPUT 1: EVENT CATALOGUE (code fragments and analysis references removed) ===

# Event catalogue

<!-- event-ids: Create Admit State Counts Name Report Return Panic Classify TripPolicy Notify Expiry UV-01 UV-02 UV-03 UV-04 UV-05 UV-06 UV-07 UV-08 UV-09 UV-10 UV-11 UV-12 UV-13 UV-14 -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| Create | external | Lifecycle owner | Construct an instance and configure its policies. observed-in-code gobreaker.go |
| Admit | external | Request initiator | Execute or Allow attempts one new admission. observed-in-code gobreaker.go |
| State | external | Observer | Read the state of an instance. observed-in-code gobreaker.go |
| Counts | external | Observer | Read a snapshot of five counters. observed-in-code gobreaker.go |
| Name | external | Observer | Read the configured name through either wrapper. observed-in-code gobreaker.go |
| Report | external | Continuation holder | Invoke Allow's returned completion callback with a success boolean. observed-in-code gobreaker.go |
| Return | external | Execute request callback | Return a result and an error from admitted request work. observed-in-code gobreaker.go |
| Panic | external | Execute request callback | Panic from admitted work. observed-in-code gobreaker.go |
| Classify | internal | IsSuccessful policy | Classify the error from Execute request work. observed-in-code gobreaker.go |
| TripPolicy | internal | ReadyToTrip policy | Evaluate a copied counter snapshot after a closed failure. observed-in-code gobreaker.go |
| Notify | internal | State change observer | Invoke configured notification with name and old and new modes. observed-in-code gobreaker.go |
| Expiry | internal | Clock sampled during State, admission or completion | Evaluate deadline on an eligible operation. observed-in-code gobreaker.go |
| UV-01 | external | Continuation holder | Omit a report, including after the caller abandons admitted work. A later report may or may not arrive. observed-in-code gobreaker.go |
| UV-02 | external | Execute request owner | Slow, blocked, abandoned or Goexit request work; unissued admission or caller-side cancellation. observed-in-code gobreaker.go |
| UV-03 | external | Request initiator | Same caller executes again while original work is pending, or calls Allow again while first continuation is outstanding. Concurrent Allow can also overlap before the first return. observed-in-code gobreaker.go |
| UV-04 | external | Continuation holder | Repeat the same callback with identical or contradictory payloads, including overlapping calls. observed-in-code gobreaker.go |
| UV-05 | external | Request or continuation holder | Old admitted work returns, panics, or reports after a clear, possibly after the next open interval. observed-in-code gobreaker.go |
| UV-06 | external | Continuation holder | Wrong boolean or continuation, pooled/reassigned wrapper, or fabricated current report; nil callback after rejected admission. observed-in-code gobreaker.go |
| UV-07 | external | Execute request owner | Pass nil request or panic with nil payload. observed-in-code gobreaker.go |
| UV-08 | external | Observer / clock context | Omit or delay a refreshing call, read Counts first, or sample exactly at the deadline; also repeated/out-of-order reads. observed-in-code gobreaker.go |
| UV-09 | external | Injected IsSuccessful | Block, panic, Goexit, re-enter, or return valid but wrong classification, including work already stale. observed-in-code gobreaker.go |
| UV-10 | external | Injected ReadyToTrip | Block, panic, Goexit, re-enter, or return a valid but unintended decision. observed-in-code gobreaker.go |
| UV-11 | external | Injected OnStateChange | Block, panic, Goexit, re-enter, or misdeliver an observation after a state commit. observed-in-code gobreaker.go |
| UV-12 | external | Lifecycle and API owner | Use zero-value or nil receiver, copy a live breaker, replace wrapper or try teardown without an API. observed-in-code gobreaker.go |
| UV-13 | external | API and request owner | Call wrong valid instance or provide a valid callback/payload for the wrong request. observed-in-code gobreaker.go |
| UV-14 | external | Lifecycle owner | Missing, delayed, duplicate or replacement construction, or valid but unintended Settings. observed-in-code gobreaker.go |

## Undesired-coverage (observed in code, not documented intent)

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| Create: Lifecycle owner | UV-14 | UV-14 | UV-14 | UV-14 | UV-14 | UV-14 | UV-14 |
| Admit: Request initiator | UV-02 | UV-02 | UV-03 | UV-03 | UV-03 | UV-03 | UV-07, UV-12, UV-13, UV-14 |
| State: Observer | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-13 |
| Counts: Observer | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-13 |
| Name: Observer | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-13 |
| Report: Continuation holder | UV-01 | UV-05 | UV-04 | UV-05 | UV-04 | UV-06 | UV-06 |
| Return: Execute request callback | UV-02 | UV-05 | UV-03 | UV-05 | UV-05 | UV-03 | UV-07, UV-13 |
| Panic: Execute request callback | UV-02 | UV-05 | UV-03 | UV-05 | UV-05 | UV-03 | UV-07, UV-13 |
| Classify: IsSuccessful policy | UV-09 | UV-09 | UV-09 | UV-05 | UV-09 | UV-09 | UV-09 |
| TripPolicy: ReadyToTrip policy | UV-10 | UV-10 | UV-10 | UV-10 | UV-10 | UV-10 | UV-10 |
| Notify: State change observer | UV-11 | UV-11 | UV-11 | UV-11 | UV-11 | UV-11 | UV-11 |
| Expiry: Clock sampled during State, admission or completion | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 | UV-08 |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Admit → Report | New admission and existing report on same breaker; half-open at budget |
| P-01b | Report → Admit | New admission and existing report on same breaker; half-open at budget |
| P-02a | Admit → Return | New admission and previous Execute return on same breaker |
| P-02b | Return → Admit | New admission and previous Execute return on same breaker |
| P-03a | Admit → Panic | New admission and previous Execute panic on same breaker |
| P-03b | Panic → Admit | New admission and previous Execute panic on same breaker |
| P-04a | State → Report | Observer and delayed report on same breaker |
| P-04b | Report → State | Observer and delayed report on same breaker |
| P-05a | Counts → Report | Snapshot and report on same breaker |
| P-05b | Report → Counts | Snapshot and report on same breaker |
| P-06a | State → Return | Observer and returning Execute on same breaker |
| P-06b | Return → State | Observer and returning Execute on same breaker |
| P-07a | Counts → Return | Snapshot and returning Execute on same breaker |
| P-07b | Return → Counts | Snapshot and returning Execute on same breaker |
| P-08a | State → Panic | Observer and panicking Execute on same breaker |
| P-08b | Panic → State | Observer and panicking Execute on same breaker |
| P-09a | Counts → Panic | Snapshot and panic on same breaker |
| P-09b | Panic → Counts | Snapshot and panic on same breaker |
| P-10a | State → Admit | Independent observer and initiator at an Open expiry |
| P-10b | Admit → State | Independent observer and initiator at an Open expiry |
| P-11a | Counts → Admit | Snapshot and initiator in Closed or HalfOpen |
| P-11b | Admit → Counts | Snapshot and initiator in Closed or HalfOpen |
| P-12a | State → Counts | Independent observers on a breaker with due expiry |
| P-12b | Counts → State | Independent observers on a breaker with due expiry |
| P-13a | Name → Admit | Name observer and initiator sharing one breaker |
| P-13b | Admit → Name | Name observer and initiator sharing one breaker |
| P-14a | Name → Report | Name observer and continuation holder sharing one breaker |
| P-14b | Report → Name | Name observer and continuation holder sharing one breaker |
| P-15a | Name → Return | Name observer and Execute callback sharing one breaker |
| P-15b | Return → Name | Name observer and Execute callback sharing one breaker |
| P-16a | Name → Panic | Name observer and panicking Execute callback sharing one breaker |
| P-16b | Panic → Name | Name observer and panicking Execute callback sharing one breaker |

## Remembrance semantics (observed in code, not documented intent)

observed-in-code gobreaker.go. A caller-held continuation records a generation and retains its wrapper. No individual completion or queue is stored by the breaker. Lifecycle replacement creates an independent instance. A late callback refreshes then compares generation. gobreaker.go. gobreaker.go. observed-in-code gobreaker.go. Requests counts admissions per generation, independent of caller departure. Successful reports update outcome counters until a state change or interval refresh clears all five. A half-open failure goes straight to a state change. Rejection and stale contribution do not increment outcomes. gobreaker.go. gobreaker.go. gobreaker.go. No queue backing store. Retained closure footprint or collection timing is a runtime question. observed-in-code gobreaker.go. Only the current generation is retained, bounded by uint64. Counts use uint32 fields. HalfOpen has no expiry. gobreaker.go. gobreaker.go.

## Lock-discipline annotation (observed in code, not documented intent)

observed-in-code gobreaker.go. State holds the mutex across refresh and synchronous notification. Counts takes it only for the snapshot. Name reads the configured name without locking. gobreaker.go. gobreaker.go. observed-in-code gobreaker.go. Admission holds the mutex across refresh, possible OnStateChange and its count decision. Completion holds it across refresh, ReadyToTrip and OnStateChange. gobreaker.go. gobreaker.go. gobreaker.go. observed-in-code gobreaker.go. Execute invokes request work and classifier after admission unlock and before completion lock. The contracts do not specify same-instance reentry or callback failure and blocking behavior. gobreaker.go. gobreaker.go. gobreaker.go.

## Catalogue notes

The public topologies wrap Execute work directly or issue a continuation through Allow. Read methods exist in both. Reports and Execute results do not share one publicly constructed backing breaker across topologies. A construction targets a new breaker identity. Clock evaluation is internal.

## Event annotations (observed in code, not documented intent)

### Create
- gate (observed in code): Settings values and optional callbacks
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go
- coverage:
  - loss: UV-14
  - delay: UV-14
  - duplication: UV-14
  - out-of-order: UV-14
  - contradiction: UV-14
  - commission: UV-14
  - value: UV-14

### Admit
- gate (observed in code): Service state, sampled deadline and admission count
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go
- coverage:
  - loss: UV-02
  - delay: UV-02
  - duplication: UV-03
  - out-of-order: UV-03
  - contradiction: UV-03
  - commission: UV-03
  - value: UV-07, UV-12, UV-13, UV-14

### State
- gate (observed in code): Service state and sampled deadline
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go
- coverage:
  - loss: UV-08
  - delay: UV-08
  - duplication: UV-08
  - out-of-order: UV-08
  - contradiction: UV-08
  - commission: UV-08
  - value: UV-13

### Counts
- gate (observed in code): No payload
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go
- coverage:
  - loss: UV-08
  - delay: UV-08
  - duplication: UV-08
  - out-of-order: UV-08
  - contradiction: UV-08
  - commission: UV-08
  - value: UV-13

### Name
- gate (observed in code): No payload
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go
- coverage:
  - loss: UV-08
  - delay: UV-08
  - duplication: UV-08
  - out-of-order: UV-08
  - contradiction: UV-08
  - commission: UV-08
  - value: UV-13

### Report
- gate (observed in code): Payload boolean plus service generation and state
- upstream_guards (observed in code): Only a successful Allow returns a callable completion; caller report cardinality, truth and ownership are undocumented. gobreaker.go
- coverage:
  - loss: UV-01
  - delay: UV-05
  - duplication: UV-04
  - out-of-order: UV-05
  - contradiction: UV-04
  - commission: UV-06
  - value: UV-06

### Return
- gate (observed in code): Payload error plus service generation and state
- upstream_guards (observed in code): Execute invokes request work only following successful admission. The example uses the initialized breaker and propagates HTTP/read errors. The public topology permits arbitrary request functions. gobreaker.go. example/http_breaker.go
- coverage:
  - loss: UV-02
  - delay: UV-05
  - duplication: UV-03
  - out-of-order: UV-05
  - contradiction: UV-05
  - commission: UV-03
  - value: UV-07, UV-13

### Panic
- gate (observed in code): Payload recover value plus service generation and state
- upstream_guards (observed in code): Execute invokes request work only following successful admission. The example uses the initialized breaker and propagates HTTP/read errors. The public topology permits arbitrary request functions. gobreaker.go. example/http_breaker.go
- coverage:
  - loss: UV-02
  - delay: UV-05
  - duplication: UV-03
  - out-of-order: UV-05
  - contradiction: UV-05
  - commission: UV-03
  - value: UV-07, UV-13

### Classify
- gate (observed in code): Payload error, configured classifier and result
- upstream_guards (observed in code): Dispatch is private; no independent public event injection. gobreaker.go
- coverage:
  - loss: UV-09
  - delay: UV-09
  - duplication: UV-09
  - out-of-order: UV-05
  - contradiction: UV-09
  - commission: UV-09
  - value: UV-09

### TripPolicy
- gate (observed in code): Service state and callback result
- upstream_guards (observed in code): Dispatch is private; no independent public event injection. gobreaker.go
- coverage:
  - loss: UV-10
  - delay: UV-10
  - duplication: UV-10
  - out-of-order: UV-10
  - contradiction: UV-10
  - commission: UV-10
  - value: UV-10

### Notify
- gate (observed in code): Distinct state change and configured callback
- upstream_guards (observed in code): Dispatch is private; no independent public event injection. gobreaker.go
- coverage:
  - loss: UV-11
  - delay: UV-11
  - duplication: UV-11
  - out-of-order: UV-11
  - contradiction: UV-11
  - commission: UV-11
  - value: UV-11

### Expiry
- gate (observed in code): Service state and strict expiry-before-now comparison
- upstream_guards (observed in code): Dispatch is private; no independent public event injection. gobreaker.go
- coverage:
  - loss: UV-08
  - delay: UV-08
  - duplication: UV-08
  - out-of-order: UV-08
  - contradiction: UV-08
  - commission: UV-08
  - value: UV-08

### UV-01
- gate (observed in code): Service state and admission budget
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go

### UV-02
- gate (observed in code): Service state, actual callback outcome and generation
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go

### UV-03
- gate (observed in code): Service state and admission budget
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go

### UV-04
- gate (observed in code): Service generation, state, payload and lock order
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go

### UV-05
- gate (observed in code): Service generation after refresh
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go

### UV-06
- gate (observed in code): Payload and continuation identity
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go

### UV-07
- gate (observed in code): Payload and runtime recover behavior
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go

### UV-08
- gate (observed in code): Operation type and strict deadline
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go

### UV-09
- gate (observed in code): Callback control flow, result and generation
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go

### UV-10
- gate (observed in code): Callback control flow and result
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go

### UV-11
- gate (observed in code): Callback control flow
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go

### UV-12
- gate (observed in code): Receiver validity and per-object lifetime
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go

### UV-13
- gate (observed in code): Receiver identity or payload supplied by caller
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go

### UV-14
- gate (observed in code): Settings values, callback availability and object identity
- upstream_guards (observed in code): No public caller identity or client-side validation is specified. The example uses the initialized instance. example/http_breaker.go



=== INPUT 2b: DOCTRINE LINES (from the extraction) ===

- DOC-1 explicit-requirement README.md ("The struct `CircuitBreaker` is a state machine to prevent sending requests that are likely to fail.")
- DOC-2 explicit-requirement README.md ("The function `NewCircuitBreaker` creates a new `CircuitBreaker`.")
- DOC-3 explicit-requirement README.md ("You can configure `CircuitBreaker` by the struct `Settings`:")
- DOC-4 explicit-requirement README.md ("- `Name` is the name of the `CircuitBreaker`.")
- DOC-5 explicit-requirement README.md ("- `MaxRequests` is the maximum number of requests allowed to pass through") README.md ("when the `CircuitBreaker` is half-open.")
- DOC-6 explicit-requirement README.md ("If `MaxRequests` is 0, `CircuitBreaker` allows only 1 request.")
- DOC-7 explicit-requirement README.md ("- `Interval` is the cyclic period of the closed state") README.md ("for `CircuitBreaker` to clear the internal `Counts`, described later in this section.")
- DOC-8 explicit-requirement README.md ("If `Interval` is 0, `CircuitBreaker` doesn't clear the internal `Counts` during the closed state.")
- DOC-9 explicit-requirement README.md ("- `Timeout` is the period of the open state,") README.md ("after which the state of `CircuitBreaker` becomes half-open.")
- DOC-10 explicit-requirement README.md ("If `Timeout` is 0, the timeout value of `CircuitBreaker` is set to 60 seconds.")
- DOC-11 explicit-requirement README.md ("- `ReadyToTrip` is called with a copy of `Counts` whenever a request fails in the closed state.")
- DOC-12 explicit-requirement README.md ("If `ReadyToTrip` returns true, `CircuitBreaker` will be placed into the open state.")
- DOC-13 explicit-requirement README.md ("If `ReadyToTrip` is `nil`, default `ReadyToTrip` is used.")
- DOC-14 explicit-requirement README.md ("Default `ReadyToTrip` returns true when the number of consecutive failures is more than 5.")
- DOC-15 explicit-requirement README.md ("- `OnStateChange` is called whenever the state of `CircuitBreaker` changes.")
- DOC-16 explicit-requirement README.md ("- `IsSuccessful` is called with the error returned from a request.")
- DOC-17 explicit-requirement README.md ("If `IsSuccessful` returns true, the error is counted as a success.")
- DOC-18 explicit-requirement README.md ("Otherwise the error is counted as a failure.")
- DOC-19 explicit-requirement README.md ("If `IsSuccessful` is nil, default `IsSuccessful` is used, which returns false for all non-nil errors.")
- DOC-20 explicit-requirement README.md ("The struct `Counts` holds the numbers of requests and their successes/failures:")
- DOC-21 explicit-requirement README.md ("`CircuitBreaker` clears the internal `Counts` either") README.md ("on the change of the state or at the closed-state intervals.")
- DOC-22 explicit-requirement README.md ("`Counts` ignores the results of the requests sent before clearing.")
- DOC-23 explicit-requirement README.md ("`CircuitBreaker` can wrap any function to send a request:")
- DOC-24 explicit-requirement README.md ("The method `Execute` runs the given request if `CircuitBreaker` accepts it.")
- DOC-25 explicit-requirement README.md ("`Execute` returns an error instantly if `CircuitBreaker` rejects the request.")
- DOC-26 explicit-requirement README.md ("Otherwise, `Execute` returns the result of the request.")
- DOC-27 explicit-requirement README.md ("If a panic occurs in the request, `CircuitBreaker` handles it as an error") README.md ("and causes the same panic again.")

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
