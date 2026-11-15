# channelPool — adversarial traces (Step 6)

Systematic traces P-01a..P-06b (one per pair ordering), free probes T-01..T-15, multi-instance probes M-01..M-03. Jev ordering checks for T-01..T-04 are in runs/jev-batch-control.json (source README.md, model jev-1.14.0).

### P-01a — Put then Release

(a) Sequence: 1. caller A Put(conn) (no waiters, room in idle channel); 2. caller B Release().

(b) Code: Put stores the connection (channel.go:190); Release then closes every idle entry including it (channel.go:238-241). observed-in-code. Cell Open_IdleAvailable x Release.

(c) Question: none — control trace

### P-01b — Release then Put

(a) Sequence: 1. Release() completes; 2. caller A Put(conn) of a borrowed connection.

(b) Code: Put sees conns == nil and calls Close, which returns nil because c.close is nil (channel.go:174-176, 208-210): connection neither stored nor closed. observed-in-code, TestAsIs_Put_AfterRelease_NoClose. Cell Closed x Put is a hole.

(c) Question: Q-05

### P-02a — waiting Get then Release

(a) Sequence: 1. all MaxCap connections borrowed; 2. caller A Get() queues at channel.go:135-137; 3. caller B Release().

(b) Code: Release changes only conns, factory, ping, close (channel.go:225-231); connReqs and the blocked receive are untouched; A stays blocked. observed-in-code, TestAsIs_Release_DoesNotWakeWaiter. Cell Open_Waiting_AtCap x Release.

(c) Question: Q-01

### P-02b — Get misses the idle channel, Release, then Get takes its lock

(a) Sequence: 1. pool at capacity, idle channel empty; 2. caller A Get() runs the select and takes the default branch (channel.go:109, 130); 3. caller B Release() completes; 4. A locks (channel.go:131).

(b) Code: A tests openingConns >= maxActive before it tests factory == nil (channel.go:133, 150): at capacity it queues in a closed pool and blocks forever; below capacity it returns ErrClosed (channel.go:150-153). observed-in-code, inferred from the two critical sections.

(c) Question: Q-01 and Q-07

### P-03a — waiting Get then Close of a borrowed connection

(a) Sequence: 1. at capacity; 2. A Get() queues; 3. B Close(conn) of a borrowed connection.

(b) Code: Close lowers openingConns and calls the callback (channel.go:211-212); connReqs untouched; A stays blocked although a slot is free. observed-in-code, TestAsIs_Close_DoesNotServeWaiter. Cell Open_Waiting_AtCap x Close.

(c) Question: Q-03

### P-03b — Close then Get at capacity

(a) Sequence: 1. at capacity, nobody waiting; 2. B Close(conn); 3. A Get().

(b) Code: Close moves the pool to Open_NoIdle_BelowCap; A creates a connection (channel.go:133, 154-161). observed-in-code. Cell Open_NoIdle_AtCap x Close and Open_NoIdle_BelowCap x Get.

(c) Question: none — control trace

### P-04a — Get misses, Put stores, Get queues

(a) Sequence: 1. at capacity, idle channel empty; 2. A Get() select takes default (channel.go:130); 3. B Put(conn) stores it idle (channel.go:190); 4. A locks and queues (channel.go:131-137).

(b) Code: A is registered as waiter although an idle connection exists (state Open_Waiting_IdleAvailable); it is served only by a later Put, while a later Get takes the idle connection first (channel.go:110). observed-in-code, inferred from the interleaving; not reproduced by a test.

(c) Question: Q-04

### P-04b — Put then Get

(a) Sequence: 1. at capacity; 2. B Put(conn) stores it; 3. A Get().

(b) Code: A takes the idle connection (channel.go:110-129). observed-in-code. Cell Open_IdleAvailable x Get.

(c) Question: none — control trace

### P-05a — Put then Close of the same connection

(a) Sequence: 1. A Put(conn); 2. B Close(conn) of the same value.

(b) Code: the connection is idle and closed at once: Close lowers openingConns and runs the callback (channel.go:211-212); a later Get hands out a closed connection. observed-in-code, inferred; NAT-02 excludes it.

(c) Question: Q-11 and Q-12

### P-05b — Close then Put of the same connection

(a) Sequence: 1. A Close(conn); 2. B Put(conn).

(b) Code: Put stores or hands over a connection that is closed (channel.go:190, 183) and the counter has already been lowered. observed-in-code, inferred.

(c) Question: Q-11 and Q-12

### P-06a — Get passes the ping test, Release nils the function

(a) Sequence: 1. idle connection present, Ping configured; 2. A Get() evaluates `c.ping != nil` without the lock (channel.go:123); 3. B Release() sets c.ping = nil (channel.go:229); 4. A calls c.Ping (channel.go:124, 220).

(b) Code: c.ping(conn) is a call of a nil function: panic; also a data race on c.ping in any interleaving. observed-in-code; the Go race detector and nil-call semantics are NAT-06; TestAsIs_Get_ConcurrentWithRelease did not reproduce it in 200 rounds.

(c) Question: Q-07

### P-06b — Release then Get with an earlier snapshot

(a) Sequence: 1. A has taken its channel snapshot (channel.go:104); 2. B Release() closes the channel (channel.go:238); 3. A selects.

(b) Code: A receives a buffered connection not yet drained by Release's loop, or nil from the closed channel and returns ErrClosed (channel.go:110-113). observed-in-code.

(c) Question: Q-07

### T-01 — reuse after Put (README.md:52)

(a) Sequence: 1. Get; 2. Put; 3. Get.

(b) Code: The second Get takes the stored connection (channel.go:190, 110-129). observed-in-code, TestPool_Get_Impl (observed-in-tests).

(c) Question: Q-24

DOC-5, DOC-6: README.md:52 "when the connection is no longer in use" names Put but no later Get. Scope line: cited text contemplates this ordering: no. jev: unclear, scope 0.04

### T-02 — idle expiry at Get time (README.md:13)

(a) Sequence: 1. Get, Put; 2. wait longer than IdleTimeout; 3. Get.

(b) Code: The stale idle connection is closed and a new one created (channel.go:115-121); observed-in-tests TestAsIs_Get_ExpiredIdle_Replaced.

(c) Question: Q-24 and Q-16

DOC-2: README.md:13 "the timeout connection will be closed and discarded" gives no moment. Scope line: cited text contemplates this ordering: no. jev: unclear, scope 0.06

### T-03 — waiter served by Put (README.md:15)

(a) Sequence: 1. at capacity; 2. Get waits; 3. Put.

(b) Code: The waiter receives the returned connection (channel.go:179-185); observed-in-tests TestAsIs_Get_AtCap_BlocksUntilPut.

(c) Question: Q-24 and Q-02

DOC-4: README.md:15 "support for connection waiting" gives no served-by rule. Scope line: cited text contemplates this ordering: no. jev: unclear, scope 0.05

### T-04 — Release closes idle connections (README.md:55)

(a) Sequence: 1. idle connections present; 2. Release.

(b) Code: All idle connections go to the close callback (channel.go:238-241); borrowed ones are not touched.

(c) Question: Q-24 and Q-05

DOC-7: README.md:55 "Release all connections" does not say whether borrowed connections count. Scope line: cited text contemplates this ordering: no. jev: unclear, scope 0.14

### T-05 — Get after Release

(a) Sequence: 1. Release; 2. Get.

(b) Code: Get returns ErrClosed (channel.go:105-107, 112); intent evidence is the comment at pool.go:6 only; no requirements file contemplates the ordering, so this is not a control trace.

(c) Question: Q-24

### T-06 — slow Factory while another caller calls Len

(a) Sequence: 1. at least one Get is inside the Factory callback (channel.go:154) and takes long; 2. another caller calls Len.

(b) Code: Len blocks at c.mu (channel.go:97) until the factory returns: every call waits behind the callback. observed-in-code, NAT-06.

(c) Question: Q-08

### T-07 — Close callback calls back into the pool (deliberate NAT-01 violation)

(a) Sequence: 1. Close(conn) runs the callback under c.mu (channel.go:212); 2. the callback calls Put or Len.

(b) Code: The inner call blocks on c.mu for ever: deadlock. observed-in-code, NAT-06. No test.

(c) Question: Q-08

### T-08 — Factory returns nil without error

(a) Sequence: 1. Get, Factory returns (nil, nil).

(b) Code: Get returns (nil, nil) and counts a connection (channel.go:154-161); the caller cannot return it (Put(nil) is rejected).

(c) Question: Q-09

### T-09 — Ping callback fails for every idle connection

(a) Sequence: 1. several idle connections; 2. Get.

(b) Code: Each failing connection goes to Close (callback result dropped, channel.go:125); the loop ends when the channel is empty and a new connection is created (channel.go:131-161).

(c) Question: Q-10

### T-10 — two Releases

(a) Sequence: 1. Release; 2. Release.

(b) Code: The second returns at channel.go:234; no panic (TestAsIs_Release_Twice). observed-in-code, observed-in-tests.

(c) Question: none — control trace

### T-11 — factory fails during pre-fill (restart mid-operation)

(a) Sequence: 1. NewChannelPool InitialCap 3; 2. factory fails on call 3.

(b) Code: Release closes the two created connections and an error is returned (channel.go:83-87); TestAsIs_New_FactoryError.

(c) Question: Q-19

### T-12 — MaxCap 0

(a) Sequence: 1. NewChannelPool with MaxCap 0, MaxIdle 0; 2. Get.

(b) Code: Construction succeeds (guard G-04, TestAsIs_New_ZeroCapAccepted); Get queues at once (channel.go:133-137) and blocks for ever.

(c) Question: Q-17

### T-13 — Put hands a connection to a waiter long after it was borrowed

(a) Sequence: 1. at capacity; 2. waiter queued; 3. Put of a connection whose underlying link has died.

(b) Code: The waiter receives it without a ping (channel.go:141-148); the idle check compares against the hand-over time (channel.go:184).

(c) Question: Q-15

### T-14 — Len after expiry

(a) Sequence: 1. idle connections expire; 2. Len.

(b) Code: Len counts the expired entries (channel.go:247); they leave only when Get meets them.

(c) Question: Q-16

### T-15 — Put of a foreign connection at capacity

(a) Sequence: 1. pool full of borrowed connections (openingConns = MaxCap); 2. Put(foreign).

(b) Code: The foreign connection is stored idle or handed on (channel.go:183, 190); more than MaxCap connections now exist (SYS-02).

(c) Question: Q-13

### M-01 — startup herd (N pools, one server)

(a) Sequence: N pools call NewChannelPool at the same moment with InitialCap k.

(b) Code: Each opens k connections at once (channel.go:82-89), N times k on the server; no spacing. inferred (NAT-SYS-01).

(c) Question: Q-22

### M-02 — idle-expiry herd, 3 cycles

(a) Sequence: Pools created together; their idle connections share creation time; IdleTimeout t elapses.

(b) Code: All stale connections are discarded and replaced by the next Gets (channel.go:115-121, 154); replacements again share timestamps, so every cycle repeats the burst. inferred.

(c) Question: Q-22

### M-03 — degraded recovery herd

(a) Sequence: The server fails; callers retry Get in loops.

(b) Code: Get returns the factory error at once (channel.go:155-158) with no backoff or limit: the retry rate is the callers'; when the server recovers partially, each pool's Gets open connections up to MaxCap each. inferred.

(c) Question: Q-22
