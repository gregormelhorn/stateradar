# As-is validation against the existing tests — channelPool

Every test in channel_rpc_test.go walked through as-is.machine.mmd. The tests were
**not executed** in this run: the environment's permission policy refused `go test`
on the downloaded repository. The walk is static.

Common configuration: InitialCap 5, MaxIdle 10, MaxCap 100, IdleTimeout 20 s
(channel_rpc_test.go:14-16 ("InitialCap = 5"), channel_rpc_test.go:257 ("pconf := Config{InitialCap: InitialCap, MaxCap: MaximumCap")). Start state: Open_Idle (5 idle, openingConns 5).

| test | walk | result |
|---|---|---|
| TestNew (channel_rpc_test.go:37) | [*] → Open_Idle; Release → Released | accepted |
| TestPool_Get_Impl (:44) | Open_Idle × get (handle) → Open_Idle (4 idle) × put → Open_Idle; Release | accepted |
| TestPool_Get (:59) | get → 4 idle (Len 4, asserted :69); 99 concurrent gets: 4 from idle, 95 created (handle in Open_Empty_BelowCap) → openingConns 100 → Open_Empty_AtCap; Len 0 (asserted :88). Then get at :93 → **Open_Empty_AtCap × get = transition → Open_Waiting**: the Get blocks at channel.go:137 ("ret, ok := <-req"). The test expects `ErrMaxActiveConnReached` (channel_rpc_test.go:94 ("if err != ErrMaxActiveConnReached {")). | **not accepted** — the model predicts the test blocks until the Go test timeout. Either a modelling error or undocumented/changed behaviour. Re-read: no statement in channel.go closes a `req` channel; the only producer of `ErrMaxActiveConnReached` is channel.go:138-139 behind `!ok`. I keep the model (observed-in-code) and record the contradiction → Q-09 (wait timeout / error contract) and Q-19 (test oracle). Not verified by execution. |
| TestPool_Put (:100) | 100 gets (5 idle + 95 created, openingConns 100, Open_Empty_AtCap); 100 puts: the first 10 fill the idle set (Open_Idle), the next 90 overflow → Close (openingConns 10); Len 10 (asserted :121); Release | accepted |
| TestPool_UsedCapacity (:130) | Len in Open_Idle = 5 (asserted :134) | accepted |
| TestPool_Close (:140) | Release → Released; asserts conns nil (:148), factory nil (:152), Get error (:156-157 → Released × get = reject ErrClosed), Len 0 (:161) | accepted (the test reads the unexported fields `conns`, `factory` — structure-bound assertions, Q-19) |
| TestPoolConcurrent (:166) | Release concurrently with 100 Get goroutines and 100 Put goroutines (P-01, P-02). Gets after Release → reject; a Put after Release → Released × put (ignore (accidental), Q-04). The test function returns without waiting for its goroutines and asserts nothing. | accepted vacuously — no assertion constrains any path (Q-19) |
| TestPoolWriteRead (:191) | get, then an RPC call on the connection; never Put or Release | accepted (pool left open; out of the model's scope) |
| TestPoolConcurrent2 (:206) | 20 goroutines: get, sleep, Close (close_conn). Open_Idle → Open_Empty_BelowCap (gets create) → close_conn decrements. Never reaches the cap (20 < 100). No assertion. | accepted vacuously (Q-19) |
| TestPoolConcurrent3 (:238-254) | commented out | not walked |

Observed-in-tests behaviour that the model must and does accept: ErrClosed on Get after
Release; Len 0 after Release; idle set bounded by MaxIdle; Put overflow closes.

Behaviour present in the model but untested: waiting and handoff (Open_Waiting ×
put), Release with waiters (Q-01), Close with waiters (Q-02), idle expiry, Ping
failure, factory errors, Put/Close after Release, Ping after Release.
