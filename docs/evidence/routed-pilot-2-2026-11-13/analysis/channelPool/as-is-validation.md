# channelPool — Step 2 model validation against the existing tests

Each test of channel_rpc_test.go is walked through `as-is.machine.mmd` / `disposition-matrix.md`. The suite was also executed (read-only, in a scratch copy outside the repository) to confirm the walk: `go test -race -count=1 -timeout 60s -v ./...` with Go 1.27.3 (raw output in the evidence bundle, `existing-tests.txt` and `existing-tests-skip-get.txt`).

Fixture: InitialCap 5, MaxIdle 10, MaxCap 100, IdleTimeout 20 s, no Ping (observed-in-tests channel_rpc_test.go:257 ("pconf := Config{InitialCap: InitialCap, MaxCap: MaximumCap, Factory: factory, Close: closeFac, IdleTimeout: time.Second * 20,")).

| Test | Walk through the model | Model accepts? | Executed result |
|---|---|---|---|
| TestNew (channel_rpc_test.go:37) | [*] → Open_IdleAvailable (5 idle < 10); deferred E-RELEASE → Released | yes | PASS |
| TestPool_Get_Impl (channel_rpc_test.go:44) | Open_IdleAvailable × E-GET handle (idle 4) → E-PUT handle (idle 5) → E-RELEASE | yes | PASS |
| TestPool_Get (channel_rpc_test.go:59) | E-GET from idle (idle 4, Len 4 = InitialCap−1 ✓ line 69); 99 concurrent E-GET: 4 from idle, 95 created → openingConns 100 = MaxCap, Open_AtCapacity, Len 0 ✓ (line 88); final E-GET in Open_AtCapacity → transition → Open_AtCapacity_Waiting, blocks at channel.go:137 ("ret, ok := <-req") with no timeout. The test expects `ErrMaxActiveConnReached` (channel_rpc_test.go:94 ("if err != ErrMaxActiveConnReached {")) | **no — the test asserts behaviour the model (and code) does not have** | **hang: `panic: test timed out after 1m0s`, goroutine in `(*channelPool).Get` at channel.go:137 called from channel_rpc_test.go:93** |
| TestPool_Put (channel_rpc_test.go:100) | 100 × E-GET (5 idle + 95 created → Open_AtCapacity); 100 × E-PUT: first 10 → Open_IdleAvailable … Open_IdleFull, remaining 90 → Open_IdleFull × E-PUT handle (Close, openingConns−−); Len 10 = MaxIdleCap ✓ | yes | PASS (with `-skip '^TestPool_Get$'`) |
| TestPool_UsedCapacity (channel_rpc_test.go:130) | construction → Open_IdleAvailable, Len 5 | yes | PASS |
| TestPool_Close (channel_rpc_test.go:140) | E-RELEASE → Released; asserts the internal fields `conns` and `factory` are nil (structure-bound, observed-in-tests channel_rpc_test.go:148 ("if c.conns != nil {")); Released × E-GET reject (ErrClosed) ✓; Released × E-LEN handle → 0 ✓ | yes | PASS |
| TestPoolConcurrent (channel_rpc_test.go:166) | E-RELEASE concurrently with 100 E-GET/E-PUT pairs; the test returns without waiting or asserting (channel_rpc_test.go:170-188). Outcomes per interleaving: Released × E-GET reject, Released × UV-GET-STALE UNSPECIFIED, Released × E-PUT ignore (accidental) | accepts any outcome (no assertion) | PASS (vacuous: goroutines still running at return) |
| TestPoolWriteRead (channel_rpc_test.go:191) | E-GET, RPC call; the connection is never returned and the pool never released (channel_rpc_test.go:194) → UV-PUT-LOSS ignore (accidental) | yes | PASS |
| TestPoolConcurrent2 (channel_rpc_test.go:206) | 20 × (E-GET, sleep, E-CLOSE) below the cap; no assertion | yes | PASS |

Findings from the replay:

1. **TestPool_Get asserts undocumented-and-unimplemented behaviour** (`ErrMaxActiveConnReached` at capacity). As-is the Get blocks forever; the executed suite hangs until the test timeout, so the remaining six tests never run in a plain `go test ./...`. Modelling error or undocumented behaviour? Neither: the model reproduces the code; the test contradicts the code and README.md:15 ("When the connection pool is full, support for connection waiting"). Raised as Q-03 (provenance: observed-in-tests channel_rpc_test.go:94, observed-in-code channel.go:137, executed).
2. TestPool_Close asserts internal fields (`c.conns`, `c.factory`), not behaviour through the seam (F-21, structure-bound) — test quality, recorded under "outside scope" in `summary.md`.
3. TestPoolConcurrent and TestPoolConcurrent2 assert nothing; their PASS carries no information about the Release race (Q-07).
4. No test exercises: Ping, IdleTimeout expiry, Put/Close after Release, Close while waiters wait, factory errors, or callbacks. The race detector reported no race in the passing tests (0 `DATA RACE` lines) because no test runs Get with a configured Ping concurrently with Release (Q-08 has its own as-is test).
