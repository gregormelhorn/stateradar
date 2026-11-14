# Invariants and doctrine

<!-- doc-ids: DOC-01 DOC-02 DOC-03 DOC-04 DOC-05 DOC-06 DOC-07 DOC-08 DOC-09 DOC-10 DOC-11 DOC-12 DOC-13 DOC-14 DOC-15 DOC-16 DOC-17 DOC-18 DOC-19 DOC-20 DOC-21 DOC-22 DOC-23 DOC-24 DOC-25 DOC-26 DOC-27 DOC-28 DOC-29 DOC-30 DOC-31 DOC-32 DOC-33 DOC-34 DOC-35 DOC-36 DOC-37 DOC-38 DOC-39 DOC-40 DOC-41 DOC-42 DOC-43 DOC-44 DOC-45 DOC-46 DOC-47 DOC-48 DOC-49 DOC-50 DOC-51 DOC-52 DOC-53 DOC-54 DOC-55 DOC-56 DOC-57 DOC-58 DOC-59 DOC-60 DOC-61 DOC-62 DOC-63 DOC-64 -->

NAT-Context: non-nil conforming Go Context (DR-009); standard CancelFunc is idempotent. No guarantee is invented for faulty callbacks.
NAT-Usage: releases correspond to actual holdings; misuse within aggregate bounds may be undetectable (DR-007/008).
SYS-Count: 0 <= cur <= size <= MaxInt64 after every valid-boundary operation, including rejected negative/over-release calls (DR-002/003).
SYS-Queue: at a mutex-release boundary, the queue is empty or its head requires more than free capacity (DR-001/012).
SYS-Contract: all normative clauses below hold within their preconditions. They apply in both queue states.
SYS-Isolation: no new instance or foreign receiver cleans this instance (DR-005/008).
SYS-Cancel: before error return, own reservation and queue entry are gone; transient reservation is allowed (DR-010).

Numeric decisions: DR-001 zero FIFO progress; DR-002 negative panic; DR-003 state-preserving over-release panic; DR-004 immediate oversized error with existing pre-canceled priority.

## Doctrine mapping

DOC-01 (caller_cleanup): Cancel an abandoned pending request and consume its result. Do not call Release for a failed Acquire; any own reservation is rolled back before error return.
DOC-02 (no_auto_reclaim): Every successful acquisition requires matching release after protected work ends, even if its Context is canceled later. Cancellation does not automatically reclaim a successful holding.
DOC-03 (instance_lifetime): Creating a new semaphore does not cancel pending work or release holdings on an old instance.
DOC-04 (independent_calls): Each invocation is a separate acquisition, including repeat calls from the same logical caller. No deduplication, replacement or reentrant success is provided.
DOC-05 (self_blocking): A caller holding capacity can block itself by awaiting another acquisition before releasing its existing holding.
DOC-06 (shared_context): Independent requests can share a Context, in which case cancellation can affect all of them.
DOC-07 (transferable_release): Release responsibility may transfer to another goroutine. The application must match releases to actually held, not already released capacity.
DOC-08 (aggregate_only): The semaphore checks aggregate holdings, not caller identity. A duplicate release may remain undetected while other holdings cover it; this is a detection limit, not permission to release twice.
DOC-09 (receiver_selection): The caller selects the receiver. Release affects only that instance; release responsibility can transfer but capacity cannot transfer across instances.
DOC-10 (context_selection): The supplied Context governs the request. The semaphore does not infer a different intended Context.
DOC-11 (context_precondition): Acquire requires a non-nil Context conforming to the Go Context contract. Conforming custom implementations are supported, including concurrent-safe methods, stable Done and consistent cancellation errors.
DOC-12 (nil_done_valid): A nil Done channel is valid for a Context that cannot be canceled; it is distinct from a nil Context.
DOC-13 (no_fault_recovery_contract): No automatic substitution, repair, panic recovery or additional progress guarantee is promised for faulty, blocking or reentrant custom Context methods.
DOC-14 (initial_cancel): For a valid nonnegative weight, closed Done at the initial under-lock check causes a Context error without acquisition. Negative weights retain DR-002 panic priority; oversized errors retain DR-004 rules.
DOC-15 (queued_cancel): Processing queued cancellation removes the request or reverses a grant that raced with cleanup before returning the Context error.
DOC-16 (grant_rollback): A queued request receiving a grant checks cancellation again; if cancellation is observed, its grant is returned before error return.
DOC-17 (late_cancel_success): Cancellation after the last applicable checkpoint may coexist with nil return. That success retains its release obligation. Grant notification alone is not successful API return.
DOC-18 (transient_reservation): An error return leaves no own holding or queue entry. Temporary reservations may affect other operations; global state and observations need not be unchanged.
DOC-19 (try_no_queue): TryAcquire obtains the synchronized state, checks once whether admission is permitted, and returns false if not. It does not join the capacity queue or await a future release.
DOC-20 (mutex_wait_allowed): Internal mutex waiting is permitted. Context cancellation does not interrupt mutex acquisition; cancellation is processed at the defined checkpoints.
DOC-21 (no_latency_bound): No fixed return or cancellation-latency bound is promised. A Context deadline does not guarantee that Acquire has already returned at that instant.
DOC-22 (fifo_enqueue): Queued grants follow enqueue order, not wall-clock method-entry order.
DOC-23 (no_bypass): A blocked head cannot be bypassed by later smaller requests or new Acquire/TryAcquire calls, including zero-weight requests. FIFO can leave capacity idle and does not promise progress without required releases.
DOC-24 (return_order): Grant order does not guarantee goroutine execution order or API-return order.
DOC-25 (no_queue_cap): There is no internal waiter-count cap. The application controls incoming work and cancels obsolete requests; the semaphore bounds held capacity, not queue length.
DOC-26 (zero_release_noop): Release(0) is permitted and is a logical no-op for capacity, queue and grants in valid reachable states. Internal mutex waiting remains permitted.
DOC-27 (no_wakeup_api): Release(0) is not a promised wakeup, repair, flush or extra synchronization API. Progress must follow the actual enabling event, including DR-001 head removal.

## Lints
No internal deadline/retry/queue cap is promised (DR-011/012). Caller lifecycle cleanup remains explicit (DR-005). No reset or cross-instance cleanup exists. Context preconditions and unsupported outcomes are documented (DR-009). All old questions have DRs; no new unresolved semantic conflict found.

## Public API doctrine (continuation lines remain in order)

DOC-28: NewWeighted creates a new weighted semaphore with the given — examples/weighted-semaphore/semaphore/semaphore.go:21 ("// NewWeighted creates a new weighted semaphore with the given")

DOC-29: maximum combined weight for concurrent access. — examples/weighted-semaphore/semaphore/semaphore.go:22 ("// maximum combined weight for concurrent access.")

DOC-30: A negative capacity panics (evaluation decision DR-002). — examples/weighted-semaphore/semaphore/semaphore.go:23 ("// A negative capacity panics (evaluation decision DR-002).")

DOC-31: A new instance does not reset or clean up existing instances (DR-005/008). — examples/weighted-semaphore/semaphore/semaphore.go:24 ("// A new instance does not reset or clean up existing instances (DR-005/008).")

DOC-32: Weighted provides a way to bound concurrent access to a resource. — examples/weighted-semaphore/semaphore/semaphore.go:33 ("// Weighted provides a way to bound concurrent access to a resource.")

DOC-33: The callers can request access with a given weight. — examples/weighted-semaphore/semaphore/semaphore.go:34 ("// The callers can request access with a given weight.")

DOC-34: Acquire acquires the semaphore with a weight of n, blocking until resources — examples/weighted-semaphore/semaphore/semaphore.go:42 ("// Acquire acquires the semaphore with a weight of n, blocking until resources")

DOC-35: are available or ctx is done. On success, returns nil. On cancellation, — examples/weighted-semaphore/semaphore/semaphore.go:43 ("// are available or ctx is done. On success, returns nil. On cancellation,")

DOC-36: returns ctx.Err(). Errors leave no net holding for this request. A negative — examples/weighted-semaphore/semaphore/semaphore.go:44 ("// returns ctx.Err(). Errors leave no net holding for this request. A negative")

DOC-37: weight panics (DR-002). An oversized weight returns a size error without waiting for — examples/weighted-semaphore/semaphore/semaphore.go:45 ("// weight panics (DR-002). An oversized weight returns a size error without waiting for")

DOC-38: cancellation; an already canceled context retains priority (DR-004). — examples/weighted-semaphore/semaphore/semaphore.go:46 ("// cancellation; an already canceled context retains priority (DR-004).")

DOC-39: Each invocation is independent, including repeat calls by one caller; — examples/weighted-semaphore/semaphore/semaphore.go:48 ("// Each invocation is independent, including repeat calls by one caller;")

DOC-40: holding capacity while awaiting another acquisition can self-block (DR-006). — examples/weighted-semaphore/semaphore/semaphore.go:49 ("// holding capacity while awaiting another acquisition can self-block (DR-006).")

DOC-41: A successful call requires matching release after work ends. Later Context — examples/weighted-semaphore/semaphore/semaphore.go:50 ("// A successful call requires matching release after work ends. Later Context")

DOC-42: cancellation does not reclaim that holding (DR-005). Errors leave no own — examples/weighted-semaphore/semaphore/semaphore.go:51 ("// cancellation does not reclaim that holding (DR-005). Errors leave no own")

DOC-43: holding or queue entry, but transient reservations can affect concurrent — examples/weighted-semaphore/semaphore/semaphore.go:52 ("// holding or queue entry, but transient reservations can affect concurrent")

DOC-44: operations. Cancellation after the last check can coexist with success — examples/weighted-semaphore/semaphore/semaphore.go:53 ("// operations. Cancellation after the last check can coexist with success")

DOC-45: (DR-010); the return value determines the release obligation. — examples/weighted-semaphore/semaphore/semaphore.go:54 ("// (DR-010); the return value determines the release obligation.")

DOC-46: ctx must be a non-nil, conforming Context. A nil Done channel is valid; — examples/weighted-semaphore/semaphore/semaphore.go:56 ("// ctx must be a non-nil, conforming Context. A nil Done channel is valid;")

DOC-47: faulty custom methods have no recovery or extra progress guarantee (DR-009). — examples/weighted-semaphore/semaphore/semaphore.go:57 ("// faulty custom methods have no recovery or extra progress guarantee (DR-009).")

DOC-48: The caller selects the correct instance and Context (DR-008). Mutex waits — examples/weighted-semaphore/semaphore/semaphore.go:58 ("// The caller selects the correct instance and Context (DR-008). Mutex waits")

DOC-49: are permitted and no fixed cancellation-latency bound is promised (DR-011). — examples/weighted-semaphore/semaphore/semaphore.go:59 ("// are permitted and no fixed cancellation-latency bound is promised (DR-011).")

DOC-50: Queued grants are FIFO by enqueue order without bypass of a blocked head; — examples/weighted-semaphore/semaphore/semaphore.go:60 ("// Queued grants are FIFO by enqueue order without bypass of a blocked head;")

DOC-51: return order is unspecified. The queue has no internal count cap (DR-012). — examples/weighted-semaphore/semaphore/semaphore.go:61 ("// return order is unspecified. The queue has no internal count cap (DR-012).")

DOC-52: TryAcquire attempts to acquire weight n without joining the capacity queue — examples/weighted-semaphore/semaphore/semaphore.go:135 ("// TryAcquire attempts to acquire weight n without joining the capacity queue")

DOC-53: or awaiting a future release. It may wait for the internal mutex (DR-011). — examples/weighted-semaphore/semaphore/semaphore.go:136 ("// or awaiting a future release. It may wait for the internal mutex (DR-011).")

DOC-54: On success, returns true. On failure, returns false and leaves the semaphore unchanged. — examples/weighted-semaphore/semaphore/semaphore.go:137 ("// On success, returns true. On failure, returns false and leaves the semaphore unchanged.")

DOC-55: A negative weight panics before mutation (DR-002). — examples/weighted-semaphore/semaphore/semaphore.go:138 ("// A negative weight panics before mutation (DR-002).")

DOC-56: Existing queued requests cannot be bypassed, including by weight zero (DR-012). — examples/weighted-semaphore/semaphore/semaphore.go:139 ("// Existing queued requests cannot be bypassed, including by weight zero (DR-012).")

DOC-57: Release releases the semaphore with a weight of n. — examples/weighted-semaphore/semaphore/semaphore.go:153 ("// Release releases the semaphore with a weight of n.")

DOC-58: Negative weights or release above the aggregate held weight panic without — examples/weighted-semaphore/semaphore/semaphore.go:154 ("// Negative weights or release above the aggregate held weight panic without")

DOC-59: changing the instance (evaluation decisions DR-002 and DR-003). — examples/weighted-semaphore/semaphore/semaphore.go:155 ("// changing the instance (evaluation decisions DR-002 and DR-003).")

DOC-60: Responsibility may transfer between goroutines, but the application must — examples/weighted-semaphore/semaphore/semaphore.go:156 ("// Responsibility may transfer between goroutines, but the application must")

DOC-61: match releases to held, not already released capacity on this instance. — examples/weighted-semaphore/semaphore/semaphore.go:157 ("// match releases to held, not already released capacity on this instance.")

DOC-62: Aggregate accounting does not detect every duplicate release (DR-007/008). — examples/weighted-semaphore/semaphore/semaphore.go:158 ("// Aggregate accounting does not detect every duplicate release (DR-007/008).")

DOC-63: Release(0) is a logical no-op for capacity, queue and grants in valid reachable — examples/weighted-semaphore/semaphore/semaphore.go:159 ("// Release(0) is a logical no-op for capacity, queue and grants in valid reachable")

DOC-64: states, not a wakeup, repair or extra synchronization operation (DR-013). — examples/weighted-semaphore/semaphore/semaphore.go:160 ("// states, not a wakeup, repair or extra synchronization operation (DR-013).")

The historical upstream issue-title rule is outside this runtime boundary. The former unconditional Context-error and unchanged-state prose is superseded by DR-004 and DR-010; the old claim is not retained as a current obligation.

## State-by-state obligations

| Obligation | Acquire_NoWaiters | Acquire_WaitersPending | Evidence |
|---|---|---|---|
| SYS-Count | fitting admission/release keep count in range | queueing leaves count; prefix grants and rollback keep count in range | G-01/03/04/05/06/10; numeric and race suites |
| SYS-Queue | append only if head cannot fit | enqueue at tail; head removal rescans; non-head removal retains blocked head | G-06/08/10; DR-001 and DR-012 suites |
| SYS-Isolation | foreign operations cannot clean held capacity | foreign operations cannot remove waiters | DR-005/008 suites; both UV-WrongReceiver cells |
| SYS-Cancel | initial rejection has no own charge; completed success persists | remove or reverse own grant before error return | G-02/07/09; DR-010 schedule suite |
| SYS-Contract | public numeric/instance/admission rules apply | same rules plus FIFO, cleanup and rollback | 34 cell scenarios plus mandatory DR boundary suites |

This is a guarded queue projection. An empty queue is not an idle-resource assertion: holders and in-flight granted recipients may exist. An inductive proof establishes the two queue states at mutex-release boundaries, not every program counter. Finite tests are conformance evidence, not a proof of all concurrent schedules.
