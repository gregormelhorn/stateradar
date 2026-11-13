# channelPool — As-is validation against the existing tests (Step 2)

Test config for all tests that use `newChannelPool()`: InitialCap 5, MaxIdle 10, MaxCap 100, IdleTimeout 20 s, no Ping (channel_rpc_test.go:256-259 ("pconf := Config{InitialCap: InitialCap, MaxCap: MaximumCap, Factory: factory, Close: closeFac, IdleTimeout: time.Second * 20,")). Initial state: Open_Idle with i = 5, o = 5.

Each walk was done on the model first; the "executed" column reports the actual `go test` result recorded in `as-is-tests.md` (run R0).

| Test | Walk through the model | Model accepts? | Executed |
|---|---|---|---|
| TestNew (channel_rpc_test.go:37) | New → Open_Idle; RELEASE → Released | yes | pass |
| TestPool_Get_Impl (channel_rpc_test.go:44) | GET in Open_Idle (i 5→4, stays Open_Idle per GN-1); PUT (i 4→5, stays Open_Idle); RELEASE | yes | pass |
| TestPool_Get (channel_rpc_test.go:59) | GET in Open_Idle (i=4, o=5); Len = 4 ✓; 99 concurrent GETs: 4 from idle → Open_Empty_BelowCap, 95 × (GET → Open_Creating → FACTORY_OK) → o = 100 → Open_Empty_AtCap; Len = 0 ✓; final GET in Open_Empty_AtCap → **transition → Open_Waiting**, blocks with no timeout and no Put ever follows. The test expects `ErrMaxActiveConnReached` (channel_rpc_test.go:93-95 ("if err != ErrMaxActiveConnReached {")). | **no — the model predicts the test hangs.** Classification: undocumented/contradictory behaviour, not a modelling error: the model follows the code (channel.go:137 ("ret, ok := <-req")); the only `ErrMaxActiveConnReached` return (channel.go:139) needs a closed waiter channel and no code closes one. Contradiction C-1 → Q-01. | hangs: killed by `-timeout 60s` (panic: test timed out) |
| TestPool_Put (channel_rpc_test.go:100) | 100 GETs: 5 idle + 95 created → Open_Empty_AtCap (o = 100); 100 PUTs: first 10 enqueue (Open_Empty_AtCap → Open_Idle → … → Open_IdleFull), remaining 90 in Open_IdleFull close (o 100 → 10); Len = 10 ✓; RELEASE | yes | pass |
| TestPool_UsedCapacity (channel_rpc_test.go:130) | New → Open_Idle, Len = 5 ✓ | yes | pass |
| TestPool_Close (channel_rpc_test.go:140) | RELEASE → Released; GET in Released → reject (ErrClosed) ✓; LEN in Released → 0 ✓. The test also asserts internal fields `c.conns == nil`, `c.factory == nil` (channel_rpc_test.go:146-154) — structure, not behaviour. | yes | pass |
| TestPoolConcurrent (channel_rpc_test.go:166) | RELEASE races 100 GET/PUT pairs (pairs P-02, P-03). Gets after Release → reject; Puts after Release → `ignore (accidental)` (conn not closed). The test asserts nothing and returns without waiting for its goroutines. | yes (vacuously: no assertion) | **FAIL under `-race`**: DATA RACE, write of `c.ping` in Release (channel.go:229) vs unlocked read in Get (channel.go:123). The model has this as pair P-08 (Get ping read vs Release). |
| TestPoolWriteRead (channel_rpc_test.go:191) | GET in Open_Idle, then uses the conn; no Put, no Release (UV-01 PUT_LOST, harmless at test scale) | yes | pass |
| TestPoolConcurrent2 (channel_rpc_test.go:206) | 20 × (GET, CLOSE). o starts 5; 5 GETs take idle, the rest create (o ≤ 20 < 100); each CLOSE decrements. No waits. | yes | pass |

## Findings from the replay

* **V-1 (→ Q-01, F-01/F-19 class):** TestPool_Get encodes a behaviour (error at cap) that the code does not implement. Since the model accepts the code's behaviour and rejects the test's expectation, either the test or the waiting behaviour is wrong; only the owner can say which (README.md:15 vs channel.go:13).
* **V-2 (observation):** no test exercises a waiting Get being served by a Put (the hand-off path channel.go:179-187 and channel.go:137-148), idle-timeout expiry, ping, Close after Release, or Put after Release. Those cells are validated only by the as-is tests written for this run (`as-is-tests.md`).
* **V-3 (→ Q-10):** TestPoolConcurrent has no behavioural assertion, but under `-race` it fails: the race detector reports the unsynchronised read of `c.ping` at channel.go:123 against Release's write at channel.go:229. Without `-race` it passes (it returns before its goroutines finish). Recorded as evidence for the P-08 finding; the vacuous-assertion aspect is for 07-test-audit.
