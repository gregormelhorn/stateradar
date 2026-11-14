# As-is validation

## Existing test replay

| Test | Replay and source evidence | Executed outcome |
|---|---|---|
| TestNew | Constructor fills buffer, then Release. channel_rpc_test.go:38 ("p, err := newChannelPool()") | Passed subset, log 029 |
| TestPool_Get_Impl | Idle checkout returns fixture RPC value, followed by Put. channel_rpc_test.go:52 ("conn.(*rpc.Client)") | Passed subset |
| TestPool_Get | One idle take, concurrent takes until active cap, then exhausted Get registers and blocks. channel_rpc_test.go:94 ("err != ErrMaxActiveConnReached"), channel.go:137 ("ret, ok := <-req") | Full suite timed out after 20s, log 009. Expectation conflict Q-16 |
| TestPool_Put | Sequential checkouts followed by returns. Idle fills up to MaxIdle and overflow is delegated to Close. channel_rpc_test.go:121 ("p.Len() != MaxIdleCap") | Passed subset |
| TestPool_UsedCapacity | Prefilled count equals InitialCap. channel_rpc_test.go:134 ("p.Len() != InitialCap") | Passed subset |
| TestPool_Close | Release nils public storage and Factory. Fresh Get errors and Len becomes zero. channel_rpc_test.go:148 ("c.conns != nil"), channel_rpc_test.go:161 ("p.Len() != 0") | Passed subset |
| TestPoolConcurrent | Get, Put and Release issued concurrently. This test does not join all goroutines or assert all outcomes. channel_rpc_test.go:176 ("conn, _ := p.Get()"), channel_rpc_test.go:186 ("p.Put(conn)") | Passed subset. No evidence that all operations return |
| TestPoolWriteRead | Borrowed fixture value can perform RPC. channel_rpc_test.go:197 ("cli.Call"), channel_rpc_test.go:201 ("resp != 2") | Passed subset. RPC implementation outside pool model |
| TestPoolConcurrent2 | Issues concurrent checkout and explicit Close. Wait called; one producer can add work concurrently with the other. channel_rpc_test.go:218 ("p.Close(conn)"), channel_rpc_test.go:234 ("wg.Wait()") | Passed subset. Does not assert ordering or callback outcomes |

The commented TestPoolConcurrent3 is not executable. Fixture starts a real localhost RPC server. Its successful connection type is fixture-specific. No upstream source or tests were edited.

## Executed probes

- `go test -timeout=10s -overlay domain-analysis/channelPool/_probe/window-overlay.json -run ^TestPilot -v .` passed all 11 probes, log 100. Seven original probes also passed with the non-instrumented overlay alone, log 063.
- TestPilotPendingRelease projects no wake, no late-return cleanup, and fresh ErrClosed. P-03a, Q-01 and Q-05.
- TestPilotCloseAdmission projects returned cleanup error, older waiter stays parked, newer Get completes, then Put wakes the original. P-02a, Q-03 and Q-10.
- TestPilotSameCallerAndAbandonment projects separate held resources and two separate pending entries, one completion per Put, including a forwarded value after simulated abandonment. T-01–T-03, Q-04 and Q-16.
- TestPilotPingReturnDuringRelease synchronizes callback entry and resume. Success returns after detach; returned error loops to the closed channel; neither path reaches the cleanup delegate. P-08b, Q-06.
- TestPilotDuplicateOwnership observes one value delivered twice and two delegated Close calls. T-05, Q-11.
- TestPilotDirectPingNil observes a panic on direct Ping with no configured callback. Q-13.
- TestPilotDrainFailureAndRepeat observes ignored returned callback error, continued drain, fresh Get rejects and second Release returns before the first drain completes. P-10b, Q-10 and Q-15.
- TestPilotPingRace ran without detector in log 100. The separate command `go test -race -timeout=15s -overlay domain-analysis/channelPool/_probe/overlay.json -run ^TestPilotPingRace$ .` failed with a data race between channel.go:220 and channel.go:229, log 101. Q-06.
- TestPilotLockedReentry verifies that a callback invoking Len remains blocked for the bounded observation, for both Factory and Close. The same-goroutine lock dependency establishes the deadlock without a timeout claim about arbitrary schedules. Q-08.
- TestPilotAdmissionWindow pauses only after default is selected and before its lock. It exercises below-capacity extra creation and at-capacity queue beside idle, then externally checks Len, newer checkout and delayed delivery to old waiter. P-01a, Q-02.
- TestPilotReleaseAdmissionWindow uses the same pause for Release. Fresh error below capacity and a stranded at-capacity call were observed. P-03a, Q-01.

The overlay has one scheduling hook after Get's select default. Request-count checks synchronize observation under the existing mutex. Noncompletion is asserted over a bounded interval, with the absence of future wake established by the channel producer inventory rather than timing alone. The race run used the original implementation source. The probes use a private fake callback resource, with runtime memory retention measured neither here nor in the existing tests.
