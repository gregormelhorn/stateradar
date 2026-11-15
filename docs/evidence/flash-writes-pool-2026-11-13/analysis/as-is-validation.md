# channelPool — as-is validation (Step 2)

Existing tests (channel_rpc_test.go) and the 19 as-is tests (pool-tests/asis_test.go) replayed through as-is.machine.mmd and the matrix. Outcomes of the real runs are in ../../../as-is-tests.md (outside the repo: /tmp/flash-writes-MBhG/as-is-tests.md).

| test | path through the model | accepted? | provenance |
|---|---|---|---|
| TestNew (:37-43) | [*] → Open_IdleAvailable (InitialCap 5 < MaxIdle 10) | yes | observed-in-tests channel_rpc_test.go:38 |
| TestPool_Get_Impl (:44-57) | IdleAvailable × Get, × Put | yes | channel_rpc_test.go:48-56 |
| TestPool_Get (:59-98) | Get → IdleAvailable; 99 further Gets drain idle, create up to MaxCap = 100 (NoIdle_BelowCap → NoIdle_AtCap); the 101st Get is cell Open_NoIdle_AtCap × Get = wait. The test expects ErrMaxActiveConnReached (:94) | **no**: the model (code) waits; the test hangs (as-is run: timeout after 60 s, goroutine blocked at channel.go:137) | contradiction between observed-in-tests and observed-in-code, not a modelling error: Q-21 |
| TestPool_Put (:100-128) | 100 Gets, then 100 Puts: IdleAvailable → IdleFull; the Puts beyond MaxIdle hit Open_IdleFull × Put (close); Len = MaxIdle | yes | channel_rpc_test.go:121 |
| TestPool_UsedCapacity (:130-138) | Len in Open_IdleAvailable = InitialCap | yes | channel_rpc_test.go:134 |
| TestPool_Close (:140-164) | Release → Closed; Get → reject; Len → 0 | yes | channel_rpc_test.go:144-163 |
| TestPoolConcurrent (:166-189) | Release racing Get/Put; no assertions | accepted as far as it observes nothing; exercises pairs P-01, P-02, P-06 | channel_rpc_test.go:170-188 |
| TestPoolWriteRead (:191-204) | Get from IdleAvailable | yes | channel_rpc_test.go:194 |
| TestPoolConcurrent2 (:206-235) | Get/Close interleavings (Open_* states) | yes, no assertions | channel_rpc_test.go:216-231 |
| TestAsIs_* (19) | each plan row names its cell(s); all pass | yes | pool-tests/plan.md |

Undocumented behaviour found by replay: none beyond Q-21. Test-quality observations (outside the statechart; listed in summary.md): the failure messages at :54 and :123 do not match their assertions; TestPoolConcurrent and TestPoolConcurrent2 assert nothing; `wg.Add(1)` is called inside a goroutine at :213-214; TestPoolWriteRead never returns its connection.
