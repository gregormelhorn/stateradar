# As-is tests — channelPool (second routed pilot)

Scratch copy: `$W/pool-tests` (copy of the pool clone at 6084537, `.git` and the analysis directory removed; `channel.go`, `pool.go` and the existing tests unchanged). Added file: `asis_test.go` (package `pool`, white-box only for observation: it reads `openingConns`, `connReqs` and `conns` under the pool's own mutex). Go 1.27.3 darwin/arm64. Fake connections (`*fconn`) and counting callbacks; no network except the existing tests' RPC fixture.

A PASS means the as-is behaviour claimed by the finding was observed. It does not mean the behaviour is correct.

## Commands and overall outcomes

| # | Command (in `$W/pool-tests`) | UTC start → end | Outcome |
|---|---|---|---|
| R1 | `go test -race -count=1 -timeout 60s ./...` (the required command) | 2026-11-13T01:13:59Z → 2026-11-13T01:15:01Z | **FAIL**: `TestAsIs_T5_PingFieldRace` fails with `testing.go:1867: race detected during execution of test`; then `panic: test timed out after 1m0s` in the existing `TestPool_Get` (blocked at channel.go:137); `FAIL github.com/silenceper/pool 60.768s`; `? github.com/silenceper/pool/example [no test files]`. Raw: `asis-run-required.txt` |
| R2 | same with `-v` | 2026-11-13T01:15:14Z → 01:16:16Z | identical result with per-test logs: T1–T4 and T6–T23 PASS, T5 FAIL (race), TestNew and TestPool_Get_Impl PASS, `panic: test timed out after 1m0s` in TestPool_Get, `FAIL … 60.713s`. Raw: `asis-run-required-v.txt` |
| R3 | `go test -race -count=1 -timeout 60s -v -skip '^TestPool_Get$' ./...` | 2026-11-13T01:16:16Z → 01:16:22Z | T1–T4, T6–T23 PASS; T5 FAIL (race); all seven remaining existing tests PASS; `FAIL github.com/silenceper/pool 6.111s`. Raw: `asis-run-skip-get-v.txt` |
| R0 | existing suite before adding `asis_test.go`: `go test -race -count=1 -timeout 60s -v ./...` | 2026-11-13T00:46:30Z → 00:47:43Z | `TestPool_Get`: `panic: test timed out after 1m0s`, goroutine in `(*channelPool).Get` at channel.go:137 called from channel_rpc_test.go:93; rc 1. Raw: `existing-tests.txt` (and `existing-tests-skip-get.txt`: with `-skip`, all 8 others PASS, `ok … 1.943s`) |

`go vet ./...` reported one issue outside the component: `example/main.go:18:2: misuse of unbuffered os.Signal channel as argument to signal.Notify`.

## Per test (outcome lines quoted from R3; R2 identical except T4's count and timings)

| Test | Claim (question) | Observed (exact log line) | Result |
|---|---|---|---|
| existing `TestPool_Get` | a Get at capacity blocks; the test expects `ErrMaxActiveConnReached` (Q-03) | `panic: test timed out after 1m0s` — goroutine `[chan receive]` in `(*channelPool).Get` channel.go:137 from channel_rpc_test.go:93 | hang until timeout (R0, R1, R2) |
| T1 | Release leaves a blocked Get blocked (Q-01) | `AS-IS: waiter still blocked 300ms after Release; connReqs=1` | PASS |
| T2 | Put after Release returns nil, closes nothing (Q-06) | `AS-IS: Put after Release returned <nil>; close callback calls for the connection: 0` | PASS |
| T3 | Close at capacity wakes no waiter; a new Get overtakes it (Q-04) | `AS-IS: after Close openingConns=1, waiter still blocked after 300ms, waiters=1; a new Get blocked=false (created a connection ahead of the waiter)` — note: the printed `openingConns=1` is read after the overtaking Get created its connection (Close had brought it to 0) | PASS |
| T4 | Get/Put interleaving strands a waiter next to an idle connection (Q-05) | `AS-IS (statistical): stranded waiter with an idle connection observed in 25 of 3000 iterations (waiter queued with no idle connection: 0)` (R2: 14 of 3000) | PASS (statistical, interleaving observed) |
| T5 | unlocked read of `c.ping` races with Release (Q-08) | `AS-IS: Get with Ping concurrent with Release, 200 iterations; recovered nil-function panics: 0 …` then `WARNING: DATA RACE` — `Write at … by goroutine 6022: (*channelPool).Release() channel.go:229` / `Previous read at … by goroutine 6021: (*channelPool).Get() channel.go:123`; `testing.go:1867: race detected during execution of test` | **FAIL — race detected** (the as-is race, reported by the detector); no nil-function panic in 200 iterations |
| T6 | duplicate Close: count negative, more than MaxCap live (Q-10) | `AS-IS: openingConns after double Close=-1; two Gets blocked=false,false; live connections=2 with MaxCap=1 (&{2 0 0}, &{3 0 0})` | PASS |
| T7 | duplicate Put hands one connection to two callers (Q-11) | `AS-IS: two Gets after a duplicate Put returned the same connection: true (ids 1, 1)` | PASS |
| T8 | re-entrant Factory deadlocks the pool (Q-09) | `AS-IS: Get with a re-entrant Factory blocked=true after 300ms; an unrelated Len blocked=true` | PASS (deadlock observed for 300 ms; goroutines left blocked) |
| T9 | slow Factory stalls Len (Q-09) | `AS-IS: Len took 450ms while a Get was inside a 500ms Factory` | PASS |
| T10 | handoff to a waiter skips Ping (Q-14) | `AS-IS: waiter received the broken connection: true; Ping calls on the handoff path: 0` | PASS |
| T11 | MaxCap 0 accepted; Get waits forever (Q-20, Q-02) | `AS-IS: NewChannelPool(MaxCap=0) err=<nil>; Get blocked after 300ms: true` | PASS |
| T12 | Close after Release returns nil, no callback (Q-06) | `AS-IS: Close after Release returned <nil>; close callback calls: 0` | PASS |
| T13 | Get inside Factory returns a connection after Release was called; Release waits; later Put closes nothing (Q-07, Q-09) | `AS-IS: Release blocked while Factory ran: true; Get returned conn=true err=<nil> after Release was called; Put afterwards returned <nil>, close calls=0` | PASS |
| T14 | idle expiry is lazy (Q-13) | `AS-IS: 150ms past IdleTimeout, close calls before Get=0, after Get=2; Get returned a new connection id=3 err=<nil>` | PASS |
| T15 | InitialCap not maintained (Q-15) | `AS-IS: after two Gets and two Closes with InitialCap=2: openingConns=0, Len=0, factory calls=2` | PASS |
| T16 | Factory `(nil, nil)` consumes capacity permanently (Q-19) | `AS-IS: Get returned (<nil>, <nil>); openingConns=1; Put(nil)=connection is nil. rejecting; Close(nil)=connection is nil. rejecting; next Get blocked=true` | PASS |
| T17 | exported Ping panics without a Ping function (Q-22) | `AS-IS: Ping with no Ping function configured panicked: runtime error: invalid memory address or nil pointer dereference` | PASS |
| T18 | Put into a full idle store closes although below MaxCap (Q-23) | `AS-IS: second Put with MaxIdle=1 closed the connection: close calls=1; openingConns=1 < MaxCap=3` | PASS |
| T19 | Len counts idle only (Q-16) | `AS-IS: with 2 open connections (1 idle, 1 checked out) Len=1, openingConns=2` | PASS |
| T20 | lost connections never reclaimed (Q-12, Q-02) | `AS-IS: after 2 lost connections with MaxCap=2, openingConns=2, third Get blocked after 300ms: true` | PASS |
| T21 | Close-callback error dropped on the discard path (Q-18) | `AS-IS: Get discarded the expired connection (close calls=1, callback error dropped) and returned id=2 err=<nil>; openingConns=1` | PASS |
| T22 | Factory error fail-fast, unwrapped, no retry (Q-17, Q-21) | `AS-IS: Get returned the factory error itself=true after 3µs; factory calls=1; openingConns=0` | PASS |
| T23 | Ping failure: close via callback, decrement, next connection (Q-24) | `AS-IS: Get returned id=2 err=<nil>; close calls for id 1=1; openingConns=1` | PASS |

## Not executed

* Q-25 (expiry at exactly `age == IdleTimeout`): wall-clock equality cannot be produced deterministically without changing the code; covered only by the z3 boundary probe of G-02 (`guard-results.txt`).
* T-11 of the traces (stale Get at capacity in the window between Release's unlock and `close(conns)`): the window is a few instructions wide and needs a scheduler hook; not attempted.
* Q-21 aggregate multi-instance behaviour: only the per-instance precondition (no retry, no delay after a Factory error) is executed (T22).
* Leaked goroutines: T1, T3, T8, T11, T16, T20 leave goroutines blocked by design; the test binary exits normally in R3.
