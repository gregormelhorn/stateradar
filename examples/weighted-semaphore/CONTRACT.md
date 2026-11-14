# Weighted semaphore evaluation contract

This is the owner-approved evaluation contract, not an upstream Go contract.
DR-001 through DR-004 retain zero-weight FIFO progress, negative-input panic,
state-preserving over-release rejection and immediate oversized-request errors.
The following clauses complete DR-005 through DR-013.

## DR-005

<!-- clause:caller_cleanup -->
Cancel an abandoned pending request and consume its result. Do not call Release for a failed Acquire; any own reservation is rolled back before error return.

<!-- clause:no_auto_reclaim -->
Every successful acquisition requires matching release after protected work ends, even if its Context is canceled later. Cancellation does not automatically reclaim a successful holding.

<!-- clause:instance_lifetime -->
Creating a new semaphore does not cancel pending work or release holdings on an old instance.

## DR-006

<!-- clause:independent_calls -->
Each invocation is a separate acquisition, including repeat calls from the same logical caller. No deduplication, replacement or reentrant success is provided.

<!-- clause:self_blocking -->
A caller holding capacity can block itself by awaiting another acquisition before releasing its existing holding.

<!-- clause:shared_context -->
Independent requests can share a Context, in which case cancellation can affect all of them.

## DR-007

<!-- clause:transferable_release -->
Release responsibility may transfer to another goroutine. The application must match releases to actually held, not already released capacity.

<!-- clause:aggregate_only -->
The semaphore checks aggregate holdings, not caller identity. A duplicate release may remain undetected while other holdings cover it; this is a detection limit, not permission to release twice.

## DR-008

<!-- clause:receiver_selection -->
The caller selects the receiver. Release affects only that instance; release responsibility can transfer but capacity cannot transfer across instances.

<!-- clause:context_selection -->
The supplied Context governs the request. The semaphore does not infer a different intended Context.

## DR-009

<!-- clause:context_precondition -->
Acquire requires a non-nil Context conforming to the Go Context contract. Conforming custom implementations are supported, including concurrent-safe methods, stable Done and consistent cancellation errors.

<!-- clause:nil_done_valid -->
A nil Done channel is valid for a Context that cannot be canceled; it is distinct from a nil Context.

<!-- clause:no_fault_recovery_contract -->
No automatic substitution, repair, panic recovery or additional progress guarantee is promised for faulty, blocking or reentrant custom Context methods.

## DR-010

<!-- clause:initial_cancel -->
For a valid nonnegative weight, closed Done at the initial under-lock check causes a Context error without acquisition. Negative weights retain DR-002 panic priority; oversized errors retain DR-004 rules.

<!-- clause:queued_cancel -->
Processing queued cancellation removes the request or reverses a grant that raced with cleanup before returning the Context error.

<!-- clause:grant_rollback -->
A queued request receiving a grant checks cancellation again; if cancellation is observed, its grant is returned before error return.

<!-- clause:late_cancel_success -->
Cancellation after the last applicable checkpoint may coexist with nil return. That success retains its release obligation. Grant notification alone is not successful API return.

<!-- clause:transient_reservation -->
An error return leaves no own holding or queue entry. Temporary reservations may affect other operations; global state and observations need not be unchanged.

## DR-011

<!-- clause:try_no_queue -->
TryAcquire obtains the synchronized state, checks once whether admission is permitted, and returns false if not. It does not join the capacity queue or await a future release.

<!-- clause:mutex_wait_allowed -->
Internal mutex waiting is permitted. Context cancellation does not interrupt mutex acquisition; cancellation is processed at the defined checkpoints.

<!-- clause:no_latency_bound -->
No fixed return or cancellation-latency bound is promised. A Context deadline does not guarantee that Acquire has already returned at that instant.

## DR-012

<!-- clause:fifo_enqueue -->
Queued grants follow enqueue order, not wall-clock method-entry order.

<!-- clause:no_bypass -->
A blocked head cannot be bypassed by later smaller requests or new Acquire/TryAcquire calls, including zero-weight requests. FIFO can leave capacity idle and does not promise progress without required releases.

<!-- clause:return_order -->
Grant order does not guarantee goroutine execution order or API-return order.

<!-- clause:no_queue_cap -->
There is no internal waiter-count cap. The application controls incoming work and cancels obsolete requests; the semaphore bounds held capacity, not queue length.

## DR-013

<!-- clause:zero_release_noop -->
Release(0) is permitted and is a logical no-op for capacity, queue and grants in valid reachable states. Internal mutex waiting remains permitted.

<!-- clause:no_wakeup_api -->
Release(0) is not a promised wakeup, repair, flush or extra synchronization API. Progress must follow the actual enabling event, including DR-001 head removal.

## Use

```go
if err := sem.Acquire(ctx, weight); err != nil {
    return err
}
defer sem.Release(weight)
// Perform the protected work.
```

Race tests use bounded waits to detect stalled execution, not to establish latency promises.
Invalid caller behavior is outside the valid-use contract even where detection is limited.
