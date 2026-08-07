# Event catalogue — device-connection

<!-- event-ids: connect disconnect connection_succeeds connection_fails connection_timeout backoff_elapsed max_retries_exhausted UV-connect-loss UV-connect-delay UV-connect-duplication UV-connect-out-of-order UV-connect-contradiction UV-connect-commission UV-connect-value UV-disconnect-loss UV-disconnect-delay UV-disconnect-duplication UV-disconnect-out-of-order UV-disconnect-contradiction UV-disconnect-commission UV-disconnect-value -->

| id | name | source | ext/int | payload | produced | consumed |
|---|---|---|---|---|---|---|
| connect | connect request | operator | external | none | caller | DeviceConnection.connect() |
| disconnect | disconnect request | operator | external | none | caller | DeviceConnection.disconnect() |
| connection_succeeds | connection attempt succeeds | system | internal | none | _attempt_connection (line 105) | _connect_loop |
| connection_fails | connection attempt fails (refused) | system | internal | none | _simulate_connect → ConnectionError (line 124) | _connect_loop |
| connection_timeout | connection attempt times out | system | internal | none | asyncio.wait_for → TimeoutError → ConnectionTimeout (line 120-122) | _connect_loop |
| backoff_elapsed | backoff timer expires | system | internal | none | asyncio.sleep in _connect_loop (line 114) | _connect_loop |
| max_retries_exhausted | retry limit reached | system | internal | none | _connect_loop retry_count >= max_retries (line 110) | _connect_loop |
| UV-connect-loss | connect call lost before delivery | operator | external | none | undelivered | n/a |
| UV-connect-delay | connect call delayed in transit | operator | external | none | caller | DeviceConnection.connect() |
| UV-connect-duplication | duplicate connect call | operator | external | none | caller | DeviceConnection.connect() |
| UV-connect-out-of-order | connect arrives after later-sent disconnect | operator | external | none | caller | DeviceConnection.connect() |
| UV-connect-contradiction | connect and disconnect near-simultaneously | operator | external | none | caller | DeviceConnection.connect() / disconnect() |
| UV-connect-commission | spurious connect with no caller trigger | operator | external | none | spurious | DeviceConnection.connect() |
| UV-connect-value | connect with wrong payload | operator | external | none | n/a (connect() takes no arguments) | n/a |
| UV-disconnect-loss | disconnect call lost before delivery | operator | external | none | undelivered | n/a |
| UV-disconnect-delay | disconnect call delayed in transit | operator | external | none | caller | DeviceConnection.disconnect() |
| UV-disconnect-duplication | duplicate disconnect call | operator | external | none | caller | DeviceConnection.disconnect() |
| UV-disconnect-out-of-order | disconnect arrives after later-sent connect | operator | external | none | caller | DeviceConnection.disconnect() |
| UV-disconnect-contradiction | disconnect and connect near-simultaneously | operator | external | none | caller | DeviceConnection.disconnect() / connect() |
| UV-disconnect-commission | spurious disconnect with no caller trigger | operator | external | none | spurious | DeviceConnection.disconnect() |
| UV-disconnect-value | disconnect with wrong payload | operator | external | none | n/a (disconnect() takes no arguments) | n/a |

## Event annotations

### connect
- gate: service-side state (idempotent guard on CONNECTED/CONNECTING; FAILED guard raises)
- upstream_guards: validated upstream (caller ensures device exists)
- coverage:
  - loss: applicable — async call may be dropped before dispatch
  - delay: applicable — async call may be delayed
  - duplication: applicable — caller may retry
  - out-of-order: applicable — may arrive after a later disconnect
  - contradiction: applicable — may race with disconnect
  - commission: applicable — spurious wakeup or callback possible
  - value: n/a: connect() takes no arguments; wrong-instance call is a caller error, not a payload fault

### disconnect
- gate: service-side state (no guard — always processes)
- upstream_guards: validated upstream (caller ensures device exists)
- coverage:
  - loss: applicable — async call may be dropped before dispatch
  - delay: applicable — async call may be delayed
  - duplication: applicable — caller may retry
  - out-of-order: applicable — may arrive after a later connect
  - contradiction: applicable — may race with connect
  - commission: applicable — spurious wakeup or callback possible
  - value: n/a: disconnect() takes no arguments; wrong-instance call is a caller error, not a payload fault

### connection_succeeds
- gate: internal (outcome of _attempt_connection)
- upstream_guards: n/a (internal event)
- coverage: n/a (internal event — UV categories apply to external sources only)

### connection_fails
- gate: internal (outcome of _attempt_connection)
- upstream_guards: n/a (internal event)
- coverage: n/a (internal event)

### connection_timeout
- gate: internal (outcome of _attempt_connection)
- upstream_guards: n/a (internal event)
- coverage: n/a (internal event)

### backoff_elapsed
- gate: internal (asyncio.sleep completion)
- upstream_guards: n/a (internal event)
- coverage: n/a (internal event)

### max_retries_exhausted
- gate: internal (retry_count >= max_retries check)
- upstream_guards: n/a (internal event)
- coverage: n/a (internal event)

### UV-connect-loss
- gate: n/a — event never arrives
- upstream_guards: n/a
- coverage: n/a (the loss itself is the variant)

### UV-connect-delay
- gate: service-side state (same as connect)
- upstream_guards: same as connect
- coverage: n/a (the delay itself is the variant)

### UV-connect-duplication
- gate: service-side state (second connect may hit idempotent guard)
- upstream_guards: same as connect
- coverage: n/a (the duplication itself is the variant)

### UV-connect-out-of-order
- gate: service-side state (connect processed after a later disconnect)
- upstream_guards: same as connect
- coverage: n/a (the out-of-order arrival itself is the variant)

### UV-connect-contradiction
- gate: service-side state (interleaving with disconnect determines outcome)
- upstream_guards: same as connect
- coverage: n/a (the contradiction itself is the variant)

### UV-connect-commission
- gate: service-side state (component cannot distinguish from legitimate connect)
- upstream_guards: same as connect
- coverage: n/a (the spontaneous commission itself is the variant)

### UV-connect-value
- gate: n/a — connect() takes no payload
- upstream_guards: n/a
- coverage: n/a

### UV-disconnect-loss
- gate: n/a — event never arrives
- upstream_guards: n/a
- coverage: n/a

### UV-disconnect-delay
- gate: service-side state (same as disconnect)
- upstream_guards: same as disconnect
- coverage: n/a

### UV-disconnect-duplication
- gate: service-side state (second disconnect is idempotent)
- upstream_guards: same as disconnect
- coverage: n/a

### UV-disconnect-out-of-order
- gate: service-side state (disconnect processed after a later connect)
- upstream_guards: same as disconnect
- coverage: n/a

### UV-disconnect-contradiction
- gate: service-side state (interleaving with connect determines outcome)
- upstream_guards: same as disconnect
- coverage: n/a

### UV-disconnect-commission
- gate: service-side state (component cannot distinguish from legitimate disconnect)
- upstream_guards: same as disconnect
- coverage: n/a

### UV-disconnect-value
- gate: n/a — disconnect() takes no payload
- upstream_guards: n/a
- coverage: n/a
