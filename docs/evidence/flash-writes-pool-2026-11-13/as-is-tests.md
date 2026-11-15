# As-is tests (routing variant flash-writes, point 3)

Location: /tmp/flash-writes-MBhG/pool-tests (copy of channel.go, pool.go, go.mod, go.sum, channel_rpc_test.go + new asis_test.go). Plan: pool-tests/plan.md; Flash prompt: pool-tests/prompt.md; Flash draft: pool-tests/asis_test.go.draft (578 lines); final: pool-tests/asis_test.go. Go go1.27.3 darwin/arm64, GOFLAGS=-mod=mod.

Tests drafted by Flash: 19 (all plan rows). Tests changed by the agent: 2 (TestAsIs_Close_Twice_ExceedsMaxCap rewritten: the draft borrowed one connection and never reached three live connections; TestAsIs_Get_ConcurrentWithRelease: the draft swallowed panics, now counted and logged). 17 tests unchanged. Draft compiled and vetted clean on first try (`go vet`).

## Commands and outcomes

1. `go test -race -count=1 -timeout 60s -v ./...` → exit 1. The 19 TestAsIs_* tests, TestNew and TestPool_Get_Impl PASS; TestPool_Get hangs and the 60 s alarm fires: `panic: test timed out after 1m0s  running tests: TestPool_Get (59s)`; `FAIL github.com/silenceper/pool 60.781s`. Output: runs/gotest-full.out.
2. `go test -race -count=1 -timeout 60s -v -skip '^TestPool_Get$' ./...` → exit 0, `ok github.com/silenceper/pool 3.005s`, no DATA RACE report. Output: runs/gotest-skip.out.

| test | outcome (command 2) | claim |
|---|---|---|
| TestAsIs_Get_IdleAvailable | PASS | Get from idle |
| TestAsIs_Get_NoIdleBelowCap | PASS | Get creates via factory |
| TestAsIs_Put_StoresIdle | PASS | Put stores |
| TestAsIs_Put_IdleFull_ClosesConnection | PASS | Put closes when idle full |
| TestAsIs_Get_AtCap_BlocksUntilPut | PASS | Get blocks at MaxCap, served by Put |
| TestAsIs_Get_ExpiredIdle_Replaced | PASS | stale idle discarded |
| TestAsIs_Get_PingFails_DiscardsIdle | PASS | ping failure discards |
| TestAsIs_Release_ClosesIdleThenGetErrClosed | PASS | Release then Get returns ErrClosed |
| TestAsIs_Release_Twice | PASS | second Release no-op |
| TestAsIs_Put_AfterRelease_NoClose | PASS | Put after Release: nil, close callback not called (Q-05) |
| TestAsIs_Release_DoesNotWakeWaiter | PASS | waiter stays blocked after Release (Q-01) |
| TestAsIs_Close_DoesNotServeWaiter | PASS | waiter stays blocked after Close; third Get creates (Q-03) |
| TestAsIs_Nil_Rejected | PASS | nil rejected |
| TestAsIs_Close_Twice_ExceedsMaxCap | PASS | double Close lets the live count exceed MaxCap (Q-12) |
| TestAsIs_Len_CountsIdleOnly | PASS | Len = idle |
| TestAsIs_New_FactoryError | PASS | partial fill closed, error returned (Q-19) |
| TestAsIs_New_InvalidConfig | PASS | validations |
| TestAsIs_New_ZeroCapAccepted | PASS | zero capacities accepted (Q-17) |
| TestAsIs_Get_ConcurrentWithRelease | PASS | 200 rounds: 0 panics, no race report (not conclusive; Q-07) |
| existing: TestNew, TestPool_Get_Impl, TestPool_Put, TestPool_UsedCapacity, TestPool_Close, TestPoolConcurrent, TestPoolWriteRead, TestPoolConcurrent2 | PASS | repo tests |
| existing: TestPool_Get | HANGS (command 1), skipped in command 2 | expects ErrMaxActiveConnReached at MaxCap (channel_rpc_test.go:94); the code blocks (Q-21) |
