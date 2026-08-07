# Event Catalogue — device-connection

Component: `DeviceConnection` (`examples/device-connection/device_connection.py`)

## Event classification

| Event ID | Source | Gate type | Upstream guards | Description |
|---|---|---|---|---|
| `connect` | external | `entry` | none | Caller invokes `connect()` (`device_connection.py:84`). |
| `disconnect` | external | `entry` | none | Caller invokes `disconnect()` (`device_connection.py:91`). |
| `connection_succeeds` | internal | `delivery` | state ∈ {CONNECTING, RECONNECTING} | `_attempt_connection()` returns without raising (`device_connection.py:106`). |
| `connection_fails` | internal | `delivery` | state ∈ {CONNECTING, RECONNECTING} | `_attempt_connection()` raises `ConnectionError` (`device_connection.py:111,122-123`). |
| `connection_timeout` | internal | `delivery` | state ∈ {CONNECTING, RECONNECTING} | `_attempt_connection()` raises `ConnectionTimeout` (`device_connection.py:111,114-115`). |
| `backoff_elapsed` | internal | `delivery` | state = RECONNECTING | `asyncio.sleep(backoff + jitter)` completes in `_connect_loop` (`device_connection.py:120`). |
| `max_retries_exhausted` | internal | `delivery` | state ∈ {CONNECTING, RECONNECTING} | `retry_count >= max_retries` check after increment (`device_connection.py:112-114`). |

## Event annotations

### connect
- gate: Caller entry — no internal precondition beyond FAILED rejection.
- upstream_guards: none
- coverage:
  - loss: n/a: direct synchronous call; loss means caller never invokes, which is outside the component boundary.
  - delay: n/a: synchronous call with no timeout semantics at the boundary.
  - duplication: UV-connect-dup — caller invokes `connect()` twice in rapid succession.
  - out-of-order: n/a: single caller; ordering relative to other events is covered by interaction pairs.
  - contradiction: UV-connect-contra — `connect()` and `disconnect()` called simultaneously from separate coroutines.
  - commission: UV-connect-commission — spurious `connect()` call when already CONNECTED (no-op path).
  - value: n/a: `connect()` takes no parameters that could carry a foreign session or stale epoch.

### disconnect
- gate: Caller entry — no internal precondition.
- upstream_guards: none
- coverage:
  - loss: n/a: direct synchronous call; loss means caller never invokes, outside the component boundary.
  - delay: n/a: synchronous call with no timeout semantics at the boundary.
  - duplication: UV-disconnect-dup — caller invokes `disconnect()` twice in rapid succession.
  - out-of-order: n/a: single caller; ordering covered by interaction pairs.
  - contradiction: UV-disconnect-contra — `disconnect()` and `connect()` called simultaneously from separate coroutines.
  - commission: UV-disconnect-commission — spurious `disconnect()` call when already DISCONNECTED.
  - value: n/a: `disconnect()` takes no parameters.

### connection_succeeds
- gate: Delivered as the successful outcome of an asynchronous connection attempt. The gate is the completion of `_attempt_connection()` without exception.
- upstream_guards: state ∈ {CONNECTING, RECONNECTING}
- coverage:
  - loss: UV-conn-succeeds-loss — the success callback is lost (task cancelled, event loop stopped).
  - delay: UV-conn-succeeds-delay — the success arrives after `disconnect()` has already cancelled the task.
  - duplication: UV-conn-succeeds-dup — the success event fires twice (unlikely given single-task pattern, but task resurrection or double-completion is a UV).
  - out-of-order: UV-conn-succeeds-stale — a stale success from a previously cancelled `_connect_task` arrives after a new `connect()` has been issued.
  - contradiction: n/a: success and failure cannot co-occur on the same attempt.
  - commission: n/a: success requires a preceding connection attempt.
  - value: n/a: success has no payload carrying entity identity.

### connection_fails
- gate: Delivered as the failure outcome of an asynchronous connection attempt.
- upstream_guards: state ∈ {CONNECTING, RECONNECTING}
- coverage:
  - loss: UV-conn-fails-loss — the failure callback is lost (task cancelled, exception swallowed).
  - delay: UV-conn-fails-delay — the failure arrives after `disconnect()` has already cancelled the task.
  - duplication: UV-conn-fails-dup — the failure event fires twice.
  - out-of-order: UV-conn-fails-stale — a stale failure from a cancelled task arrives out of order.
  - contradiction: n/a: success and failure cannot co-occur on the same attempt.
  - commission: n/a: failure requires a preceding connection attempt.
  - value: n/a: failure carries no entity-identifying payload.

### connection_timeout
- gate: Delivered as the timeout outcome of an asynchronous connection attempt.
- upstream_guards: state ∈ {CONNECTING, RECONNECTING}
- coverage:
  - loss: UV-conn-timeout-loss — the timeout is swallowed or the task is cancelled before the timeout fires.
  - delay: UV-conn-timeout-delay — the timeout fires late, after a new connection has already been initiated.
  - duplication: UV-conn-timeout-dup — the timeout fires twice.
  - out-of-order: UV-conn-timeout-stale — a stale timeout from a cancelled task arrives out of order.
  - contradiction: n/a: timeout and success cannot co-occur on the same attempt.
  - commission: n/a: timeout requires a preceding connection attempt.
  - value: n/a: timeout carries no entity-identifying payload.

### backoff_elapsed
- gate: Delivered when `asyncio.sleep(backoff + jitter)` completes in the retry loop.
- upstream_guards: state = RECONNECTING
- coverage:
  - loss: UV-backoff-loss — the sleep is interrupted by task cancellation before completing.
  - delay: UV-backoff-delay — the sleep takes longer than expected (e.g., event loop congestion).
  - duplication: n/a: a single sleep completion is atomic.
  - out-of-order: n/a: backoff is sequential within the loop; ordering violation requires loop corruption.
  - contradiction: n/a: no simultaneous contradictory event possible for a timer completion.
  - commission: UV-backoff-commission — a spurious wakeup from `asyncio.sleep` (theoretical; Python asyncio does not spurious-wake).
  - value: n/a: backoff carries no payload.

### max_retries_exhausted
- gate: Internal check `retry_count >= max_retries` after increment in `_connect_loop`.
- upstream_guards: state ∈ {CONNECTING, RECONNECTING}
- coverage:
  - loss: n/a: this is a synchronous check, not a delivered event; it cannot be lost.
  - delay: n/a: synchronous check.
  - duplication: n/a: synchronous check evaluated once per failure.
  - out-of-order: n/a: synchronous check in the same control flow.
  - contradiction: n/a: synchronous check cannot contradict itself.
  - commission: n/a: requires a preceding failure and increment; cannot occur spontaneously.
  - value: UV-maxretries-value — `max_retries` is misconfigured (0 or negative) or `retry_count` is corrupted, causing premature or skipped exhaustion.
