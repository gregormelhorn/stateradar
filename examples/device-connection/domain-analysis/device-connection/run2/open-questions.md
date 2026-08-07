# Open Questions — device-connection

## Q-01: Internal events arriving in DISCONNECTED

Q-01
**Status:** OPEN

**Context:** When the component is in DISCONNECTED, there should be no active connection attempt. However, internal events (`connection_succeeds`, `connection_fails`, `connection_timeout`, `backoff_elapsed`, `max_retries_exhausted`) could theoretically arrive from stale or cancelled tasks.

**Cells affected:** DISCONNECTED/{connection_succeeds, connection_fails, connection_timeout, backoff_elapsed, max_retries_exhausted}

**Question:** Should these events be:
1. **ignore (documented)** — silently dropped; the state machine treats them as no-ops because no connection attempt is in progress.
2. **reject** — raise an error or log a warning, as they indicate a bug (stale task callback).
3. **UNSPECIFIED** — leave unspecified and rely on the task cancellation pattern to prevent delivery?

**Recommendation:** Option 1 (ignore documented). Python asyncio task cancellation via `task.cancel()` raises `CancelledError` inside the task, which propagates and prevents normal return. Stale callbacks from properly cancelled tasks cannot fire. However, edge cases exist: if `_attempt_connection` completes between the cancellation request and the next `await`, the success/failure could still fire. Adding explicit state guards before applying connection outcomes would make the component more robust.

---

## Q-02: backoff_elapsed arriving in CONNECTING

Q-02
**Status:** OPEN

**Context:** `backoff_elapsed` represents the completion of `asyncio.sleep(backoff + jitter)` in the retry loop. This only happens after a failure transitions to RECONNECTING. In CONNECTING (before any failure), there is no pending backoff sleep.

**Cells affected:** CONNECTING/backoff_elapsed

**Question:** Is it possible for `backoff_elapsed` to arrive while in CONNECTING? If so, under what conditions?

**Recommendation:** Mark as **ignore (accidental)** — if it occurs, it indicates a logic error (e.g., a stale sleep callback from a previous retry cycle). The code's structure makes this impossible during normal operation.

---

## Q-03: max_retries_exhausted as a discrete event

Q-03
**Status:** OPEN

**Context:** `max_retries_exhausted` is not delivered as a discrete event in the code. The check `retry_count >= max_retries` at `device_connection.py:113` is evaluated inline after incrementing `retry_count`. It is logically coupled to `connection_fails` and `connection_timeout` — exhaustion is the *result* of a failure that pushes the count over the threshold. The matrix includes it as a separate event for completeness, but it may be more accurately modeled as a guard condition on `connection_fails`/`connection_timeout`.

**Cells affected:** CONNECTING/max_retries_exhausted, RECONNECTING/max_retries_exhausted

**Question:** Should `max_retries_exhausted` be:
1. **Removed** as a separate event and folded into a guard on `connection_fails`/`connection_timeout` (G1b).
2. **Retained** as a semantic event representing the exhaustion milestone, even though it co-occurs with the final failure.

**Recommendation:** Option 1. The code never delivers `max_retries_exhausted` independently; it is a condition evaluated at `device_connection.py:113-115`. The guard group G1 already captures this. Retaining it as a separate event creates cells that are structurally unreachable.

---

## Q-04: connect() during RECONNECTING

Q-04
**Status:** OPEN

**Context:** The `connect()` method at `device_connection.py:85` guards against re-entry only for CONNECTED and CONNECTING: `if self.state in (State.CONNECTED, State.CONNECTING): return`. RECONNECTING is not in this guard. Calling `connect()` during RECONNECTING proceeds to set `state = CONNECTING` and create a new `_connect_task`, overwriting the reference to the running retry loop task. The orphaned task continues executing and may fire events on a stale state.

**Cells affected:** RECONNECTING/connect

**Question:** Should `connect()` during RECONNECTING:
1. **Be a no-op** (ignore documented) — add RECONNECTING to the guard tuple. The running retry loop continues.
2. **Reset the retry cycle** — cancel the existing loop, reset `retry_count`, and start fresh. This is what the current code *effectively* does (by overwriting `_connect_task`) but without cancelling the orphan.
3. **Be rejected** — raise an error informing the caller that a connection attempt is in progress.

**Recommendation:** Option 1. This is the safest interpretation consistent with R-01 ("if already connected or connecting, it is a no-op"). RECONNECTING is an active connection attempt and should be treated the same as CONNECTING for idempotency purposes.

---

## Q-05: Internal events arriving in CONNECTED

Q-05
**Status:** OPEN

**Context:** When the component is CONNECTED, `_connect_loop` has returned (line 109). No connection attempt is in progress. Internal events (`connection_succeeds`, `connection_fails`, `connection_timeout`, `backoff_elapsed`, `max_retries_exhausted`) should not fire.

**Cells affected:** CONNECTED/{connection_succeeds, connection_fails, connection_timeout, backoff_elapsed, max_retries_exhausted}

**Question:** Should these events be:
1. **ignore (documented)** — silently dropped.
2. **reject** — raise an error or log a warning.
3. **UNSPECIFIED** — leave unspecified.

**Recommendation:** Option 1 (ignore documented). Same reasoning as Q-01: the code structure prevents these events in CONNECTED during normal operation. The `_connect_loop` returns after successful connection, so no internal events remain pending.

---

## Q-06: disconnect() from FAILED

Q-06
**Status:** OPEN

**Context:** R-05 states: "When `max_retries` is exhausted, the component enters FAILED state. No further connection attempts are made. The component remains in FAILED state permanently."

The code at `device_connection.py:91-100` (`disconnect()`) has no guard for FAILED. It sets `_should_stop = True`, cancels tasks (which are already None in FAILED), and sets `state = DISCONNECTED`. This allows the component to exit FAILED via `disconnect()`.

**Cells affected:** FAILED/disconnect

**Question:** Which is correct?
1. **Code is correct** — `disconnect()` should reset the component from any state. R-05's "permanently" means no *automatic* recovery, but explicit `disconnect()` is allowed.
2. **Requirement is correct** — `disconnect()` should be a no-op or reject in FAILED. The component must be discarded and recreated. Add FAILED to a guard in `disconnect()`.
3. **Both need adjustment** — `disconnect()` should reset to DISCONNECTED (code behavior) but R-05 should say "remains in FAILED until explicitly disconnected."

**Recommendation:** Option 1. It's reasonable for `disconnect()` to be the explicit escape hatch from FAILED. R-05's "permanently" should be interpreted as "no automatic recovery" rather than "immutable state."

---

## Q-07: Events in FAILED (excluding connect and disconnect)

Q-07
**Status:** OPEN

**Context:** In FAILED state, no connection loop is running (`_connect_loop` has exited at line 114-115). Internal events should not fire.

**Cells affected:** FAILED/{connection_succeeds, connection_fails, connection_timeout, backoff_elapsed, max_retries_exhausted}

**Question:** Should these events be:
1. **ignore (documented)** — silently dropped; FAILED is terminal for connection events.
2. **reject** — should not happen; log a warning.

**Recommendation:** Option 1 (ignore documented). FAILED is a terminal state for connection lifecycle events. The code structure makes these events unreachable in FAILED.

---

## Q-08: TOCTOU race in task cancellation model

Q-08
**Status:** OPEN

**Context:** The component uses `asyncio.Task.cancel()` for cancellation. Python's cancellation is cooperative: it raises `CancelledError` at the next `await`. If a connection attempt completes (success or failure) between the cancellation request and the next `await`, the result is processed AFTER `disconnect()` already set state=DISCONNECTED. This creates a TOCTOU window where stale results can overwrite the disconnected state.

**Affected pairs:** P-02B, P-03B, P-05B (see adversarial-traces.md).

**Question:** Should the component:
1. **Add task-identity checks** — tag each attempt with a generation counter; discard results from stale generations.
2. **Add state guards before applying results** — check `self.state in (CONNECTING, RECONNECTING)` before applying connection_succeeds/connection_fails.
3. **Accept the race** — document that rapid disconnect/reconnect cycles may have undefined behavior.

**Recommendation:** Option 2. Adding a state guard at `device_connection.py:106` and `device_connection.py:111` is the minimal fix: check that the component is still in an appropriate state before applying the outcome.
