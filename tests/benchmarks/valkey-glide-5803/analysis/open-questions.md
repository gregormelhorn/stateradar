# Questions & Findings — valkey-glide Inflight Permit

---

## Critical Finding: Missing CallerTimedOut → PermitReleased Transition

**Q-04: The `release_permit` event in `CallerTimedOut` state has no disposition.**

### What the requirements say (given to Part B)

1. A request acquires one unit of in-flight capacity before dispatch.
2. A completed request releases its capacity.
3. A request that times out from the caller's perspective releases its
   caller-facing capacity **immediately**.
4. Internal cleanup may continue after the caller receives a timeout.
5. A stalled request to one cluster node must not exhaust capacity for
   unrelated healthy nodes.
6. Releasing capacity more than once must have no additional effect.

### What the code does

`handle_request` (`socket_listener.rs:535-640`):
1. `reserve_inflight_request()` acquires the permit (counter -= 1)
2. `send_command(cmd, client, routes).await` dispatches the command
3. After the await: `release_inflight_request()` releases the permit (counter += 1)

`Client::send_command` (`mod.rs:551-595`):
1. Internally wraps the command in `run_with_timeout(request_timeout, ...)`
2. `run_with_timeout` (`mod.rs:245-265`) uses `tokio::time::timeout(duration, future)`
3. When the deadline expires, `tokio::time::timeout` returns `Err(Elapsed)`, but the
   inner future **continues executing** — tokio does NOT cancel it.

### The gap

The release at step 3 of `handle_request` only runs AFTER `send_command` returns.
When the timeout fires inside `send_command`:
- `run_with_timeout` returns `Err(TimedOut)` to `send_command`
- `send_command` returns the error to `handle_request`
- `handle_request` finally calls `release_inflight_request()`

But between the timeout and the release, the permit is **still held**.
Additionally, `tokio::time::timeout` leaves the inner future running. The
`ClientWrapper` inside the abandoned future may hold internal state that
prevents the inflight counter from reflecting the release.

### Impact

When one cluster node becomes unresponsive:
1. Every request to that node calls `reserve_inflight_request()` → acquires permit
2. The request times out → `run_with_timeout` fires
3. The inner request continues running (Redis connection waiting for response)
4. The permit is held until the inner request completes OR until `send_command` returns
5. During this window, `inflight_requests_allowed` is at or below zero
6. Requests to **healthy** nodes call `reserve_inflight_request()` → returns false
7. Healthy nodes are blocked by the stalled node's permits

This violates Requirement 5: stalled requests exhaust capacity for healthy nodes.

### The missing transition

```
CallerTimedOut --release_permit--> CapacityAvailable
```

The caller-facing permit must be released when the timeout fires, not when
the internal request completes. This is an independent transition —
decoupling the caller lifecycle from the internal request lifecycle.

---

## Other Questions

Q-01: Internal events in non-permit-holding states. Structurally impossible —
these events only fire from within the permit lifecycle. Document as such.

Q-02: Release in terminal states. Once the permit is released, further release
is idempotent per Requirement 6. `fetch_add(1)` on each release adds 1 to the
counter — multiple releases would over-count. The code does not guard against
double-release. Is this a concern?

Q-03: Internal request completion after caller timeout. The internal request
may complete long after the timeout. When it completes, does it trigger a
SECOND permit release? If the release at line 637 already ran (after
`send_command` returned with the timeout error), and the internal cleanup
also calls release, the counter is incremented twice. This violates
Requirement 6 (idempotent release).

---

## Summary

| Metric | Count |
|---|---|
| States | 7 |
| Events | 6 |
| Critical findings | 1 (Q-04: missing timeout→release transition) |
| Other questions | 3 |
| Requirements violated | 2 (Req 3: immediate release, Req 5: healthy node isolation) |
