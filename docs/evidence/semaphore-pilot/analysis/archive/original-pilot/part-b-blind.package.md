You are the BLIND adversarial pass (Part B) of a domain-behaviour analysis. You have NO access to the implementation. Do NOT read any files, do NOT use any tools, do NOT search any repository — the inputs below are complete and are your ONLY sources. If you catch yourself wanting to look something up, label it an open point instead.

TASK: Here is the event catalogue of a component, and its requirements. For every event — including undesired variants and both orderings of every interaction pair — state in which situations the component should handle, ignore, or reject it, and what should happen. Describe situations in requirement terms. Name states per PA-17 (state naming convention): prefer public API names, name sub-states by their condition, use PascalCase with `_` as separator. If you must assume a lifecycle state the requirements do not name, label it `assumed-state:` with the condition that defines it. You have no access to the implementation. Be concrete. Produce a table keyed by the catalogue's event ids and pair-ordering ids. Prefer one row per id with conditional outcomes. If you split an id into several rows, use an explicit `Situation` column with distinct, nonempty labels. Do not repeat the same situation. End with a coverage checklist: every catalogue event id, listed once, ticked. A missing row must be impossible to miss.

Catalogue headings and fields labelled `observed in code` say what the implementation does, not what it should do. Base each row on the requirements, the contracts and the doctrine lines. When a row's expected behaviour rests only on observed-in-code text, start its behaviour cell with `as-is:`.

<!-- generated:rules key=partb-vocab -->
The disposition vocabulary you must use (from the methods reference): `transition → <target>` | `handle` (stays in the state, does something) | `ignore (documented)` | `ignore (accidental)` | `defer (queued)` | `reject` (a declared refusal signal: error, diagnostic, nack) | `UNSPECIFIED`. Without these definitions a blind pass applies `reject` and `handle` to identical semantics interchangeably (dobby trigger-service, 2026-08-05: four vocabulary-only "divergences").
<!-- /generated:rules -->

The catalogue's event ids are: NewWeighted Acquire TryAcquire Release ContextDone Grant UV-Abandon UV-Delay UV-Recreate UV-RepeatAcquire UV-RepeatTry UV-RepeatRelease UV-WrongReceiver UV-Weight UV-ForeignContext UV-UnownedRelease UV-ContextFault UV-RepeatedDone UV-ContextOrder — plus the pair orderings P-01a P-01b P-02a P-02b P-03a P-03b P-04a P-04b P-05a P-05b P-06a P-06b P-07a P-07b P-08a P-08b.

=== INPUT 1: EVENT CATALOGUE (code fragments and analysis references removed) ===

# Event catalogue

<!-- event-ids: NewWeighted Acquire TryAcquire Release ContextDone Grant UV-Abandon UV-Delay UV-Recreate UV-RepeatAcquire UV-RepeatTry UV-RepeatRelease UV-WrongReceiver UV-Weight UV-ForeignContext UV-UnownedRelease UV-ContextFault UV-RepeatedDone UV-ContextOrder -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| NewWeighted | external | Constructor caller | Capacity and a new instance. semaphore/semaphore.go. |
| Acquire | external | Request caller | Weighted blocking acquisition request with Context. semaphore/semaphore.go; semaphore/semaphore.go. |
| TryAcquire | external | Request caller | Weighted synchronous try request. semaphore/semaphore.go; semaphore/semaphore.go. |
| Release | external | Holder | Release by weight. semaphore/semaphore.go; semaphore/semaphore.go. |
| ContextDone | external | Context owner | Cancellation or deadline via Done closure. semaphore/semaphore.go; semaphore/semaphore.go; semaphore/semaphore.go. |
| Grant | internal | Semaphore | Private waiter notification via channel close. semaphore/semaphore.go; semaphore/semaphore.go. |
| UV-Abandon | external | Caller or holder | Missing call, caller departure while queued, or omitted release after success. semaphore/semaphore.go. |
| UV-Delay | external | Caller, holder or context owner | Delayed request, release or cancellation past a caller deadline. semaphore/semaphore.go. |
| UV-Recreate | external | Constructor caller | Concurrent constructors or restart mid-operation using a fresh instance. semaphore/semaphore.go. |
| UV-RepeatAcquire | external | Request caller | Second Acquire by the same logical caller while the first is pending or while its successful weight is still held. semaphore/semaphore.go. |
| UV-RepeatTry | external | Request caller | Second TryAcquire or a competing try by the same logical caller. semaphore/semaphore.go. |
| UV-RepeatRelease | external | Holder | Duplicate, stale, simultaneous or early Release. semaphore/semaphore.go. |
| UV-WrongReceiver | external | Caller or holder | Well-typed receiver for another Weighted instance, separate from wrong weight. semaphore/semaphore.go. |
| UV-Weight | external | Caller or holder | Zero, negative, oversized or extreme signed weight/capacity; valid but unintended weight. semaphore/semaphore.go. |
| UV-ForeignContext | external | Request caller | Well-formed Context intended for a different request or lifetime. semaphore/semaphore.go. |
| UV-UnownedRelease | external | Holder | Release of aggregate weight with no matching ownership. semaphore/semaphore.go. |
| UV-ContextFault | external | Context implementation | Nil interface, custom method blocks/panics/reenters, inconsistent Done/Err or premature signal. semaphore/semaphore.go. |
| UV-RepeatedDone | external | Context owner | Repeated cancellation of a standard context. semaphore/semaphore.go. |
| UV-ContextOrder | external | Context owner | Done while mutex acquisition, enqueue, grant or return overlaps. semaphore/semaphore.go. |

## Undesired-coverage (observed in code, not documented intent)

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| NewWeighted: Constructor caller | UV-Abandon | UV-Abandon | UV-Recreate | UV-Recreate | UV-Recreate | UV-Recreate | UV-Weight |
| Acquire: Request caller | UV-Abandon | UV-Delay | UV-RepeatAcquire | UV-RepeatAcquire | UV-RepeatAcquire | UV-WrongReceiver | UV-Weight, UV-ForeignContext |
| TryAcquire: Request caller | UV-Abandon | UV-Delay | UV-RepeatTry | UV-RepeatTry | UV-RepeatTry | UV-WrongReceiver | UV-Weight |
| Release: Holder | UV-Abandon | UV-Delay | UV-RepeatRelease | UV-RepeatRelease | UV-RepeatRelease | UV-UnownedRelease | UV-WrongReceiver, UV-Weight |
| ContextDone: Context owner | UV-ContextFault | UV-Delay | UV-RepeatedDone | UV-ContextOrder | UV-ContextOrder | UV-ContextFault | UV-ForeignContext, UV-ContextFault |
| Grant: Semaphore | n/a: grant is an inline close; semaphore/semaphore.go. | n/a: close is inline; receiver scheduling is separate; semaphore/semaphore.go. | n/a: head is first unlinked under the lock; semaphore/semaphore.go. | n/a: the notifier reads the current head; semaphore/semaphore.go. | n/a: notification is called with the mutex held; semaphore/semaphore.go. | n/a: ready is private; semaphore/semaphore.go. | n/a: entry and channel are paired; semaphore/semaphore.go. |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Acquire → Release | Requester and holder on the same Weighted instance |
| P-01b | Release → Acquire | Requester and holder on the same Weighted instance |
| P-02a | TryAcquire → Release | Requester and holder competing for capacity |
| P-02b | Release → TryAcquire | Requester and holder competing for capacity |
| P-03a | Acquire → ContextDone | Requester and cancellation owner on the same acquisition |
| P-03b | ContextDone → Acquire | Requester and cancellation owner on the same acquisition |
| P-04a | ContextDone → Release | Cancellation owner and holder at a queued acquisition's handoff |
| P-04b | Release → ContextDone | Cancellation owner and holder at a queued acquisition's handoff |
| P-05a | UV-RepeatAcquire → Release | One request actor and a holder with repeated acquisition pending |
| P-05b | Release → UV-RepeatAcquire | One request actor and a holder with repeated acquisition pending |
| P-06a | UV-RepeatAcquire → ContextDone | One request actor and the first request's context owner |
| P-06b | ContextDone → UV-RepeatAcquire | One request actor and the first request's context owner |
| P-07a | UV-ContextOrder → Release | Cancellation at an in-flight handoff |
| P-07b | Release → UV-ContextOrder | Cancellation at an in-flight handoff |
| P-08a | UV-UnownedRelease → Acquire | Independent releasing actor and requester sharing aggregate weight |
| P-08b | Acquire → UV-UnownedRelease | Independent releasing actor and requester sharing aggregate weight |

## Remembrance semantics (observed in code, not documented intent)

Observed in code. Requests have private queue entries. semaphore/semaphore.go; semaphore/semaphore.go; semaphore/semaphore.go; semaphore/semaphore.go. Observed in code. Aggregate counter changes at admission, release, grant and rollback. semaphore/semaphore.go; semaphore/semaphore.go; semaphore/semaphore.go; semaphore/semaphore.go; semaphore/semaphore.go. No ownership ledger or historical queue in the instance fields. semaphore/semaphore.go; semaphore/semaphore.go. Observed in code. Detached list elements can remain referenced by the call frame until it exits. No time-based retention policy for a live pending call.

## Lock-discipline annotation (observed in code, not documented intent)

Observed in code. Acquire, its queued cancellation branch, TryAcquire, and Release take the instance mutex. semaphore/semaphore.go; semaphore/semaphore.go; semaphore/semaphore.go; semaphore/semaphore.go. Notification closes a private channel under that mutex. semaphore/semaphore.go; semaphore/semaphore.go. Observed in code. Caller-supplied Context.Done precedes lock acquisition and Context.Err is called outside the instance lock. semaphore/semaphore.go; semaphore/semaphore.go; semaphore/semaphore.go; semaphore/semaphore.go. No explicit user callback is invoked in a mutex-held section.

## Catalogue notes

Direct Go library boundary. Request caller, holder, context owner and constructor roles can be played by the same or different goroutines. Constructor calls create a different instance. No service adapter is supplied.

## Event annotations (observed in code, not documented intent)

### NewWeighted
- gate (observed in code): capacity argument
- upstream_guards (observed in code): Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.
- coverage:
  - loss: UV-Abandon
  - delay: UV-Abandon
  - duplication: UV-Recreate
  - out-of-order: UV-Recreate
  - contradiction: UV-Recreate
  - commission: UV-Recreate
  - value: UV-Weight

### Acquire
- gate (observed in code): requested weight, context and semaphore state
- upstream_guards (observed in code): Go Context interface governs stable Done channel and Err after closure. Custom implementations enter directly; no upstream adapter.
- coverage:
  - loss: UV-Abandon
  - delay: UV-Delay
  - duplication: UV-RepeatAcquire
  - out-of-order: UV-RepeatAcquire
  - contradiction: UV-RepeatAcquire
  - commission: UV-WrongReceiver
  - value: UV-Weight, UV-ForeignContext

### TryAcquire
- gate (observed in code): requested weight and semaphore state
- upstream_guards (observed in code): Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.
- coverage:
  - loss: UV-Abandon
  - delay: UV-Delay
  - duplication: UV-RepeatTry
  - out-of-order: UV-RepeatTry
  - contradiction: UV-RepeatTry
  - commission: UV-WrongReceiver
  - value: UV-Weight

### Release
- gate (observed in code): released weight and semaphore state
- upstream_guards (observed in code): Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.
- coverage:
  - loss: UV-Abandon
  - delay: UV-Delay
  - duplication: UV-RepeatRelease
  - out-of-order: UV-RepeatRelease
  - contradiction: UV-RepeatRelease
  - commission: UV-UnownedRelease
  - value: UV-WrongReceiver, UV-Weight

### ContextDone
- gate (observed in code): request phase, channel state and semaphore state
- upstream_guards (observed in code): Go Context interface governs stable Done channel and Err after closure. Custom implementations enter directly; no upstream adapter.
- coverage:
  - loss: UV-ContextFault
  - delay: UV-Delay
  - duplication: UV-RepeatedDone
  - out-of-order: UV-ContextOrder
  - contradiction: UV-ContextOrder
  - commission: UV-ContextFault
  - value: UV-ForeignContext, UV-ContextFault

### Grant
- gate (observed in code): queue front and capacity
- upstream_guards (observed in code): The channel is created and closed within this boundary.
- coverage:
  - loss: n/a: grant is an inline close; semaphore/semaphore.go.
  - delay: n/a: close is inline; receiver scheduling is separate; semaphore/semaphore.go.
  - duplication: n/a: head is first unlinked under the lock; semaphore/semaphore.go.
  - out-of-order: n/a: the notifier reads the current head; semaphore/semaphore.go.
  - contradiction: n/a: notification is called with the mutex held; semaphore/semaphore.go.
  - commission: n/a: ready is private; semaphore/semaphore.go.
  - value: n/a: entry and channel are paired; semaphore/semaphore.go.

### UV-Abandon
- gate (observed in code): same as base operation
- upstream_guards (observed in code): Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-Delay
- gate (observed in code): same as base operation
- upstream_guards (observed in code): Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-Recreate
- gate (observed in code): same as base operation
- upstream_guards (observed in code): Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-RepeatAcquire
- gate (observed in code): same as base operation
- upstream_guards (observed in code): Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-RepeatTry
- gate (observed in code): same as base operation
- upstream_guards (observed in code): Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-RepeatRelease
- gate (observed in code): same as base operation
- upstream_guards (observed in code): Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-WrongReceiver
- gate (observed in code): same as base operation
- upstream_guards (observed in code): Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-Weight
- gate (observed in code): same as base operation
- upstream_guards (observed in code): Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-ForeignContext
- gate (observed in code): same as base operation
- upstream_guards (observed in code): Go Context interface governs stable Done channel and Err after closure. Custom implementations enter directly; no upstream adapter.

### UV-UnownedRelease
- gate (observed in code): same as base operation
- upstream_guards (observed in code): Direct Go method, no upstream validation required by the boundary. Example caller discipline is local to the example.

### UV-ContextFault
- gate (observed in code): same as base operation
- upstream_guards (observed in code): Go Context interface governs stable Done channel and Err after closure. Custom implementations enter directly; no upstream adapter.

### UV-RepeatedDone
- gate (observed in code): same as base operation
- upstream_guards (observed in code): Go Context interface governs stable Done channel and Err after closure. Custom implementations enter directly; no upstream adapter.

### UV-ContextOrder
- gate (observed in code): same as base operation
- upstream_guards (observed in code): Go Context interface governs stable Done channel and Err after closure. Custom implementations enter directly; no upstream adapter.



=== INPUT 2: REQUIREMENTS (README.md) ===

# Go Sync

[![Go Reference](https://pkg.go.dev/badge/golang.org/x/sync.svg)](https://pkg.go.dev/golang.org/x/sync)

This repository provides Go concurrency primitives in addition to the
ones provided by the language and "sync" and "sync/atomic" packages.

## Report Issues / Send Patches

This repository uses Gerrit for code changes. To learn how to submit changes to
this repository, see https://go.dev/doc/contribute.

The git repository is https://go.googlesource.com/sync.

The main issue tracker for the sync repository is located at
https://go.dev/issues. Prefix your issue with "x/sync:" in the
subject line, so it is easy to find.


=== INPUT 3: EVENT CONTRACT TEXTS (domain-analysis/weightedSemaphore/contracts.md) ===

semaphore/semaphore.go:5
Package semaphore provides a weighted semaphore implementation.

semaphore/semaphore.go:19
NewWeighted creates a new weighted semaphore with the given
maximum combined weight for concurrent access.

semaphore/semaphore.go:26
Weighted provides a way to bound concurrent access to a resource.
The callers can request access with a given weight.

semaphore/semaphore.go:35
Acquire acquires the semaphore with a weight of n, blocking until resources
are available or ctx is done. On success, returns nil. On failure, returns
ctx.Err() and leaves the semaphore unchanged.

semaphore/semaphore.go:109
TryAcquire acquires the semaphore with a weight of n without blocking.
On success, returns true. On failure, returns false and leaves the semaphore unchanged.

semaphore/semaphore.go:121
Release releases the semaphore with a weight of n.


Respond with ONLY the table and the coverage checklist: every catalogue event and pair-ordering id, listed once in the checklist, ticked. A missing row must be impossible to miss.
The coverage checklist must use one exact line per event or pair in the form '- [x] EVENT_ID', with no other text on that line.
