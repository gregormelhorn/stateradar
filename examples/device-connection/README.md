# Synthetic Device Connection Manager

A stateful component that manages the lifecycle of a single device
connection. Used as a StateRadar demonstration example.

## Requirements

### R-01 — Connection initiation
Calling `connect()` initiates a connection attempt. If already
connected or connecting, it is a no-op.

### R-02 — Graceful disconnect
Calling `disconnect()` cancels any pending connection attempt and
returns the component to DISCONNECTED state.

### R-03 — Successful connection
When a connection attempt succeeds, the component enters CONNECTED
state and the retry counter resets to zero.

### R-04 — Connection failure and retry
When a connection attempt fails (network error or timeout), the
component retries up to `max_retries` attempts with exponential
backoff between attempts. The backoff includes random jitter.

### R-05 — Retry exhaustion
When `max_retries` is exhausted, the component enters FAILED state.
No further connection attempts are made. The component remains in
FAILED state permanently.

### R-06 — Disconnect during connection
Calling `disconnect()` during CONNECTING or RECONNECTING cancels
the connection attempt and returns to DISCONNECTED.

### R-07 — Connection timeout
If a connection attempt does not complete within `connect_timeout`,
it is treated as a failure and retried.

### R-08 — Min uptime
A connection that survives for at least `min_uptime` is considered
stable. The retry counter has already been reset on successful
connect.

### R-09 — Backoff jitter
Retry backoff includes random jitter to prevent thundering herd
when multiple instances share the same device.
