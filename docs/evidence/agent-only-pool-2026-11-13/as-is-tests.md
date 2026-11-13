# As-is tests — channelPool (silenceper/pool @ 6084537), agent-only run

Scratch copy: `/tmp/agent-only-9yFc/pool-tests` (rsync of the pool checkout without `.git` and `domain-analysis/`). The pool working tree `/tmp/agent-only-9yFc/pool` was not modified apart from `domain-analysis/`.
Test file: `pool-tests/asis_test.go` (final version; earlier versions kept as `go-outputs/asis_test.go.v1`, `.v2`).
Go: go1.27.3 darwin/arm64. Raw outputs: `go-outputs/R*.txt`.

Convention: each as-is test asserts the CURRENT behaviour that a finding or open question claims. **PASS = the claimed behaviour was observed.** Exception: T11 is expected to FAIL under `-race`; the race report is the evidence.

## Runs

| Run | Command (in pool-tests) | Exact outcome | Raw output |
|---|---|---|---|
| R0 | `go test -race -count=1 -timeout 60s ./...` (repository tests only) | `panic: test timed out after 1m0s` — running tests: `TestPool_Get (1m0s)`; goroutine blocked at `channel.go:137`; `FAIL github.com/silenceper/pool 60.853s`; exit 1 | R0-repo-tests-full.txt |
| R0b | `go test -race -count=1 -timeout 60s -v -skip '^TestPool_Get$' ./...` (repository tests only) | 7 PASS, `--- FAIL: TestPoolConcurrent` with `WARNING: DATA RACE` (write `channel.go:229` in Release, previous read `channel.go:123` in Get) and `testing.go:1867: race detected during execution of test`; exit 1 | R0-repo-tests-skip-TestPool_Get.txt |
| R0c | `go test -count=1 -timeout 60s -v -run '^TestPoolConcurrent$' .` (no -race) | `--- PASS: TestPoolConcurrent`; exit 0 | R0c-TestPoolConcurrent-norace.txt |
| R1 | `go test -race -count=1 -timeout 60s -v -skip '^TestPool_Get$' ./...` with asis_test.go v1 | T1–T9, T12–T18 PASS; **T10 FAIL** `claim not observed in 20 runs`; **T11 PASS** (no race reported); TestPoolConcurrent FAIL (race); exit 1 | R1-asis-skip-TestPool_Get.txt |
| R2 | `go test -race -count=1 -timeout 60s -v -run 'TestAsIs_T1[01]_' ./...` with v2 (T10 re-ordered, T11 without synchronization before Release) | T10 FAIL `claim not observed in 50 runs (served=50)`; T11 FAIL `WARNING: DATA RACE` `channel.go:229` / `channel.go:123`, `race detected during execution of test`; exit 1 | R2-asis-T10-T11-v2.txt |
| R3 | `go test -race -count=1 -timeout 60s -v -run 'TestAsIs_T10_' ./...` with v3 (stress loop) | `observed: 3 stranded waiter(s) with an idle conn present in 1040 runs (served=1037)`; PASS; exit 0 | R3-asis-T10-v3-race.txt |
| R4 | `go test -race -count=1 -timeout 60s -v -skip '^TestPool_Get$' ./...` (final file) | all as-is tests PASS except T11 FAIL (race detected, expected); all repository tests PASS incl. TestPoolConcurrent (see note); `FAIL github.com/silenceper/pool 3.782s`; exit 1 | R4-final-skip-TestPool_Get.txt |
| R5 | `go test -race -count=1 -timeout 60s ./...` (final file, full) | `--- FAIL: TestAsIs_T11_PingReadRacesRelease`; then `panic: test timed out after 1m0s`, running tests: `TestPool_Get (57s)`; `FAIL github.com/silenceper/pool 60.712s`; exit 1 | R5-final-full.txt |

Note on R4: TestPoolConcurrent passed although R0b reported the same race in it. inferred: the race detector reports a given racing pair of code locations once per process, and T11 (same pair `channel.go:229` / `channel.go:123`) ran earlier in the same process. Not verified further.

Note on T10 v1/v2: both tried to force the P-01b interleaving by holding `p.mu` from the test. v1 failed because `Get` locks the mutex first in `getConns` (channel.go:96, channel.go:104), so it queued before reaching its `select`. v2 failed because, after the unlock, the running Get re-acquired the free mutex at channel.go:131 before the woken Put could. Both were test-design errors, not evidence against the claim; v3 (stress loop of real concurrent calls) observed the state. The v1 failure also exposed a modelling error, corrected in Step 8 (see summary.md).

## Tests and outcomes (final file, run R4 unless stated)

| Test | Finding / question | Claimed as-is behaviour | Outcome (exact log line) |
|---|---|---|---|
| T1 TestAsIs_T1_ReleaseLeavesWaiterBlocked | Q-05, SYS-4, T-02 | a waiting Get stays blocked after Release, and after a later Put | PASS — `observed: waiting Get still blocked 600ms after Release and after a Put` |
| T2 TestAsIs_T2_CloseDoesNotWakeWaiter | Q-03, SYS-3/10, P-04b | Close frees capacity without waking the waiter; a new Get creates ahead of it | PASS — `observed: waiter blocked after Close; a new Get created conn id=2 ahead of it (created=2)` |
| T3 TestAsIs_T3_PutAfterReleaseDoesNotClose | Q-06, SYS-5, P-03b | Put after Release returns nil and does not close the conn | PASS — `observed: Put after Release -> err=nil, conn closed=0, close calls=0` |
| T4 TestAsIs_T4_CloseAfterReleaseDoesNotClose | Q-06, DOC-14 | Close after Release returns nil, no close function called | PASS — `observed: Close after Release -> err=nil, close calls=0` |
| T5 TestAsIs_T5_DoubleCloseExceedsMaxCap | Q-09, SYS-1, T-03 | double Close lets the pool exceed MaxCap | PASS — `observed: MaxCap=2, live conns=3, openingConns=2` |
| T6 TestAsIs_T6_ForeignCloseExceedsMaxCap | Q-09, UV-08 | Close of a foreign conn lets the pool exceed MaxCap | PASS — `observed: MaxCap=1, two pool conns live after a foreign Close` |
| T7 TestAsIs_T7_DuplicatePutSameConnToTwoGets | Q-09, SYS-8, T-04 | duplicate Put hands one conn to two Gets | PASS — `observed: both Gets returned conn id=1` |
| T8 TestAsIs_T8_FactoryConnAndErrLeaksConn | Q-07, UV-13, T-05 | Factory (conn, err): Get returns (nil, err), conn never closed | PASS — `observed: Get -> (nil, "dial half-failed"); factory's conn never closed` |
| T9 TestAsIs_T9_FactoryNilNilLosesSlot | Q-07, UV-14, T-06 | Factory (nil, nil): Get returns (nil, nil), nil cannot be Put/Closed, next Get blocks | PASS — `observed: Get -> (nil, nil); Put(nil) -> "connection is nil. rejecting"; Close(nil) -> "connection is nil. rejecting"; next Get blocked` |
| T10 TestAsIs_T10_WaiterStrandedWithIdleConn | Q-04, SYS-3, P-01b | a Get can be registered as waiter while an idle conn exists | PASS — `observed: 3 stranded waiter(s) with an idle conn present in 558 runs (served=555)` (R3: 3 in 1040) |
| T11 TestAsIs_T11_PingReadRacesRelease | Q-10, P-08 | unsynchronized read of `c.ping` in Get vs write in Release | FAIL as expected — `race detected during execution of test` (R2 output shows `WARNING: DATA RACE` at `channel.go:229` and `channel.go:123`). The nil-function panic was not forced. |
| T12 TestAsIs_T12_PingMethodNilPanics | Q-11, G-09, T-09 | `Ping` panics with no Ping configured and after Release | PASS — `observed panics: no Ping configured: runtime error: invalid memory address or nil pointer dereference; after Release: runtime error: invalid memory address or nil pointer dereference` |
| T13 TestAsIs_T13_LazyIdleExpiry | Q-12, DOC-2, T-10 | expired idle conns stay open until a Get dequeues them | PASS — `observed: 100ms past expiry closes=0, Len=2; first Get closed 2 and created a new conn` |
| T14 TestAsIs_T14_ReentrantCallbacksDeadlock | Q-08, UV-17/18, T-08 | re-entrant Close callback or Factory deadlocks | PASS — `observed: Close callback calling Len deadlocks Close; Factory calling Len deadlocks Get` |
| T15 TestAsIs_T15_SlowFactoryBlocksPut | Q-19, T-07 | Put waits while another Get's Factory runs | PASS — `observed: Put blocked 352ms while another Get's Factory ran` |
| T16 TestAsIs_T16_BelowInitialCapNotReplenished | Q-14, SYS-9, T-12 | pool drops below InitialCap and is not replenished | PASS — `observed: InitialCap=3, Len=0, openingConns=0, no conn created` |
| T17 TestAsIs_T17_MaxCapZeroAcceptedGetBlocks | Q-01, G-01, T-14 | MaxCap = 0 accepted; Get blocks | PASS — `observed: NewChannelPool accepted MaxCap=0; Get blocked 300ms` |
| T18 TestAsIs_T18_HandOffSkipsPing | Q-13, SYS-7, T-11 | a conn handed to a waiter skips Ping | PASS — `observed: waiter received the dead conn; Ping calls=0` |
| (repo) TestPool_Get | Q-01, C-1, T-01 | Get at MaxCap blocks instead of returning ErrMaxActiveConnReached | hangs: R0 and R5 `panic: test timed out after 1m0s` with TestPool_Get running |

Questions without an as-is test: Q-02 (no timeout — covered indirectly by T1, T2, T17 blocking), Q-15 (Len counts idle only — asserted by the repository's TestPool_Get line 69 before it hangs, and TestPool_Put), Q-16 (nothing happens by construction), Q-17 (error discarding not exercised), Q-18 (multi-instance, inferred only).
