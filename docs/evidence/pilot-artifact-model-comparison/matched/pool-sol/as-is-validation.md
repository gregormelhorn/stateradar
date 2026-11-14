# As-is validation

| Existing test | Scenario and model result |
|---|---|
| TestNew | Initialize, publish, defer Release. channel_rpc_test.go:39 ("defer p.Release()"). Accepted on successful Factory. |
| TestPool_Get_Impl | Get first idle RPC client and Put it back. channel_rpc_test.go:52 ("_, ok := conn.(*rpc.Client)"). Accepted. |
| TestPool_Get | Idle depth falls by one, parallel acquisitions fill active count. Final Get queues and blocks instead of asserted immediate error. channel_rpc_test.go:94 ("if err != ErrMaxActiveConnReached {"). Q-01. |
| TestPool_Put | Fill to MaximumCap then return values until idle buffer reaches MaxIdle. Overflow takes disposal path. channel_rpc_test.go:121 ("if p.Len() != MaxIdleCap {"). Accepted. |
| TestPool_UsedCapacity | Initial idle depth equals number precreated. channel_rpc_test.go:134 ("if p.Len() != InitialCap {"). Accepted. |
| TestPool_Close | Quiescent Release clears captured fields, fresh Get errors, fresh Len zero. channel_rpc_test.go:148 ("if c.conns != nil {"), channel_rpc_test.go:156 ("_, err := p.Get()"). Accepted. |
| TestPoolConcurrent | Exercises Release racing with Get/Put. No join and no concurrent outcome assertion. channel_rpc_test.go:171 ("p.Release()"), channel_rpc_test.go:186 ("p.Put(conn)"). Compatible, incomplete oracle. |
| TestPoolWriteRead | Acquires usable RPC client and exercises it externally. channel_rpc_test.go:197 ("err := cli.Call("Arith.Multiply", Args{1, 2}, &resp)"). Accepted. |
| TestPoolConcurrent2 | Get and delayed Close. channel_rpc_test.go:218 ("p.Close(conn)"). Compatible. Goroutines add work concurrently with Wait, so completion of every participant is not established by this replay. |
| Commented TestPoolConcurrent3 | No executable scenario. channel_rpc_test.go:238 ("//func TestPoolConcurrent3(t *testing.T) {"). |

Full original Go suite, `go test -timeout=8s ./...`, timed out in TestPool_Get at the pending receive. Log 015.stdout. The other eight executable scenarios passed the bounded selection in log 038.stdout. Source and existing tests remained intact.

Probes under `_probe` are injected with a Go overlay. The copied implementation adds pauses only after the idle miss, after the Ping presence check, and after overflow releases the mutex. Waiting queue length is used to place the schedule. Assertions use API outcomes, values or callback counts. The overlay manifest uses checkout-local absolute paths as required by Go.

| Probe | Observed |
|---|---|
| WaitersAfterCloseAndRelease | First waiter remains pending after Close and then Release/late Put. Later Get creates a different resource and fresh Get after release rejects. |
| AcquisitionOrders | Same owner queues twice using separate goroutines. Two Puts resolve one request each, FIFO. Sequential Gets can hold two separate values below limit. |
| MissThenPut | At cap one waiter and one idle value coexist. Later Get takes the value first, then Put wakes waiter. Below cap Factory creates and leaves idle entry buffered. |
| MissThenRelease | At cap old miss queues after detach. Below cap returns ErrClosed. |
| PingRelease | In-flight success returns value after Release. Failure returns ErrClosed and the dequeued value was not closed by either path. |
| PingDispatchAfterRelease | Pausing in the split Ping read produces a recovered nil-function panic. This controlled ordering is distinct from an unsynchronized race-detector observation. |
| OverflowThenRelease | Put returns nil with callback count zero when detach intervenes. |
| CloseErrorFreesAdmission | Live Close returns its error and a later Get still allocates. |

`go test -timeout=8s -overlay=domain-analysis/channelPool/_probe/overlay.json -run '^TestProbe' -v .` passed all 8 top-level probes (log 052.stdout). Pending observations are bounded assertions combined with the static receive/send/close analysis.

Additional bounded schedule probes in log 100.stdout bring the passing total to 12. AbandonedWrapper confirms later handoff reaches the wrapper result slot and does not restore pool capacity. RepeatReleaseWhileDraining confirms the repeat and Len can finish while the first Close callback is blocked, and the first call ignores its error. HandoffSkipsPing confirms the callback count stays zero for direct delivery. LiveFactoryReentry confirms no result within the bounded window when Factory calls Len on the same receiver.

The original-source race probe, `go test -race -timeout=8s -overlay=domain-analysis/channelPool/_probe/overlay-original.json -run '^TestPingReleaseRaceOriginal$' -count=1 .`, failed as an observed data race (log 101.stdout). That overlay adds the test file only. The race detector identifies channel.go:123 and channel.go:229. The scheduling probe for a nil call separately uses the instrumented copy and synchronizes the intended event order. The original eight scheduling probes also passed using the race-enabled instrumented build (log 095.stdout).
