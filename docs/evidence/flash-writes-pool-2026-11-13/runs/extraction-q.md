
## Draft questions carried forward (routing rule 6)

`→ Q-nn` = ends as or folds into that question; `answered: file:line` = sources settle what the code does (intent, where the requirements are silent, sits in the Q named after it); `outside scope: why` = never about the component's own behaviour.

### channel.go (25)
| draft | disposition |
|---|---|
| q1 waitTimeOut purpose | → Q-02 |
| q2 Put send to req may block | answered: channel.go:134 (req has capacity 1), channel.go:180-183 (req removed from connReqs before the single send) |
| q3 Release and pending connReqs | → Q-01 |
| q4 expired handed-off conn, no replacement | answered: channel.go:144-145 (`continue` re-enters the loop, creates via channel.go:154); freed capacity not offered to other waiters → Q-03 |
| q5 no ping on waiter path | → Q-15 |
| q6 Close without lock on waiter path | answered: channel.go:136 (unlock before wait), channel.go:206 (Close locks itself) |
| q7 nil ret.idleConn | answered: channel.go:183-185 (only producer sets non-nil); the closed-channel case returns earlier at channel.go:138-140 |
| q8 no check between test and factory | answered: channel.go:131-159 (one critical section); factory under lock → Q-08 |
| q9 factory returns nil, nil | → Q-09 |
| q10 slice shift retains references | outside scope: GC/memory retention is runtime behaviour (PA-19), not a state transition |
| q11 Close with nil close func | → Q-05 |
| q12 Release ignores close errors | → Q-10 |
| q13 Put/Release race relies on mutex | answered: channel.go:172-176 and 225-232 (both under c.mu); unlocked readers in Get → Q-07 |
| q14 Get receive outside mutex, closed channel | answered: channel.go:110-113 (closed channel yields nil → ErrClosed); overlap with Release → Q-07 |
| q15 MaxCap 0 | → Q-17 |
| q16 `!ok` branch unreachable | → Q-02 |
| q17 RWMutex used as Mutex | outside scope: lock kind is performance (PA-19) |
| q18 factory error, no retry | answered: channel.go:155-158 (error returned to caller); retry/backoff intent → Q-22 |
| q19 callback concurrency contract | → Q-08 |
| q20 factory in flight during Release | → Q-08 |
| q21 openingConns vs idle | answered: channel.go:159 (++), channel.go:211 (--), channel.go:75: counts open connections (idle and borrowed); idle = len(conns) |
| q22 openingConns after constructor failure | → Q-19 |
| q23 no cancellation for waiters | → Q-02 |
| q24 two Puts to one req | answered: channel.go:180-183 (req dequeued before send) |
| q25 how maxActive is kept | answered: channel.go:133 and 159 (same critical section); bypass by foreign Put → Q-13 |

### pool.go (8)
q1 Get behaviour → Q-02, Q-21; q2 Put → Q-05, Q-11, Q-13; q3 Close → Q-10, Q-12, Q-14; q4 Release/ErrClosed → Q-01, Q-05; q5 Len → Q-18; q6 which methods return ErrClosed → answered: channel.go:106, 112, 152 (Get only); q7 other errors → answered: channel.go:14, 86, 169, 205 (ErrMaxActiveConnReached is never produced, see Q-02); q8 Chinese comment → outside scope: comment text carries no constraint beyond its gloss (pool.go:6, 10).

### channel_rpc_test.go (15)
q1 message poolConn → outside scope: test message text; q2 Close vs Put → answered: channel.go:167-213, intent Q-10/Q-12; q3 Len → Q-18; q4 error after Release → answered: channel.go:106 (ErrClosed); q5 TestPoolConcurrent without asserts → outside scope: test quality (listed in summary.md); q6 nil conn from pipe → answered: channel_rpc_test.go:176-186 (Get can return nil with ErrClosed after Release); q7 ordering of Release vs Get/Put → Q-01, Q-07 and pairs P-01..P-03; q8 commented-out signature → outside scope: commented code; q9 TestPoolConcurrent2 without asserts → outside scope: test quality; q10 wg.Add in goroutine → outside scope: test synchronisation; q11 message prints 1 → outside scope: test message; q12 is ErrMaxActiveConnReached reached → Q-21; q13 model after Release → answered: channel.go:226-231, intent Q-05; q14 TestPoolWriteRead no Put → outside scope: test hygiene; q15 zero config → Q-17.

### README.md (24)
q1 Get at capacity → Q-02, Q-21; q2 wait duration → Q-02; q3 timeout configurable → Q-02; q4 Get validates by ping → answered: channel.go:123-128; waiter path → Q-15; q5 when ping is called → answered: channel.go:123 (idle path of Get only), never in Put; → Q-15; q6 ping error → answered: channel.go:125-127 (closed, discarded, loop); q7 no Ping configured → answered: channel.go:123 (skipped); q8 InitialCap minimum? → Q-23; q9, q10, q11 idle beyond MaxIdle → answered: channel.go:189-196 (Put closes the connection; comment "连接池已满，直接关闭该连接"); q12 IdleTimeout when checked → Q-16; q13 expired on Get → answered: channel.go:115-120; q14 Get error returns nil conn → answered: channel.go:106, 112, 139, 152, 157 (nil with error); factory nil,nil → Q-09; q15 Release vs borrowed → answered: channel.go:226-241 (only idle entries touched); leak on later Put → Q-05; q16 usable after Release → answered: channel.go:106 (Get: ErrClosed); Put → Q-05; q17 Len → Q-18; q18 MaxCap hard limit → answered: channel.go:133, 159; bypass → Q-13; q19 factory error at creation → answered: channel.go:83-87 (all-or-nothing) → Q-19; q20 thread-safe → Q-20; q21 NewChannelPool errors → answered: channel.go:59-67, 86; q22 reopen after Release → answered: channel.go:228 (factory nil: no); q23 Put vs waiting Get ordering → answered: channel.go:179-185 (oldest waiter first); a later Get vs hand-off → Q-04; q24 never Put → answered: no tracking of borrowed connections (NAT-08); contract text → Q-20.

### README_ZH_CN.md (14)
q1, q2 → Q-02; q3 → answered: channel.go:189-196; q4 → Q-05; q5 → Q-15; q6 → Q-16; q7 → answered: timestamps are written only when a connection is stored (channel.go:184, 190), borrowed connections are not timed; q8 → answered: channel.go:123; q9 → Q-18; q10 → Q-20; q11 → answered: channel.go:59-67; q12 → answered: channel.go:125-127 (loop continues; caller never sees the failure); q13 → answered: channel.go:189-196; q14 → answered: channel.go:108-129.
