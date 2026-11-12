StateRadar pilot, Step 1 (extraction) for component channelPool in channel.go (Go connection pool, silenceper/pool). Extract, each as one claim citing the exact line and a verbatim single-line fragment from that line:
1. States and state variables: conns channel (nil vs non-nil), openingConns counter, maxActive, connReqs wait queue, factory/close/ping nil-ness after Release.
2. Events (public methods Get, Put, Close, Ping, Release, Len, NewChannelPool) and internal events (idle timeout expiry, ping failure, factory error, wait-queue handoff).
3. Transitions, guards and conditions (every if/select branch with its condition), actions and side effects (counter increments/decrements, channel close, callbacks invoked).
4. Timeouts, waiting/blocking behaviour, failure modes, which mutex is held where, and apparent invariants (e.g. relation between openingConns and live connections).
Use kind "ordering" for claims about what happens when one call races or follows another (e.g. Release while a Get is waiting).
Do not decide whether behaviour is correct. Put every unclear or suspicious behaviour into "questions".
