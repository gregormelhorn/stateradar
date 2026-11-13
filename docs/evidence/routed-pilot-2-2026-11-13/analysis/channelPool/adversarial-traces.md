# channelPool — Step 6 adversarial traces

Format per trace: (a) sequence, (b) what the code appears to do, with provenance, (c) the domain question, or `none — control trace`. Callers A, B, C are goroutines. Unless stated otherwise: MaxCap = 1, MaxIdle = 1, no Ping, IdleTimeout = 0.

Control traces that rest on cited requirement text carry the scope line with the Jev ordering check (routing rule 5). My scope decisions were written before the Jev calls (`routing/scope-decisions-before-jev.md` in the evidence bundle). Jev runs: `jev-batch` against README.md (CT-A, CT-E, CT-F), channel.go (CT-B, CT-C) and pool.go (CT-D), `--model jev-1.14.0`; all answered, none re-run.

## Systematic traces (one per pair ordering)

### P-01a — Get blocks as a waiter, then Release

(a) 1. A: Get → creates a connection (openingConns 1, Open_AtCapacity). 2. B: Get → Open_AtCapacity × E-GET: waiter queued, B blocks. 3. C: Release → Released. 4. A: Put(conn).
(b) Step 2 blocks at channel.go:137 ("ret, ok := <-req"). Step 3 clears the fields (channel.go:227 ("c.conns = nil")) and closes only the idle channel (channel.go:238); `connReqs` is not touched, so B is never woken. Step 4 goes through channel.go:176 ("return c.Close(conn)") to channel.go:208 ("if c.close == nil {") and returns nil: the connection is not closed. Final: B blocked forever, A's connection open and unowned. Executed in `as-is-tests.md` (T1, T2).
(c) Q-01 (what Release owes blocked waiters), Q-06 (what Release owes checked-out connections).

### P-01b — Release, then Get

(a) 1. C: Release. 2. B: Get.
(b) Released × E-GET: the snapshot is nil, Get returns `ErrClosed` (channel.go:106 ("return nil, ErrClosed")). Same scenario as T-04.
(c) Q-06 (post-release API semantics; the control verdict of T-04 was voided).

### P-02a — Get finds no idle connection, a Put lands before the Get queues itself

(a) Open_AtCapacity, A holds the only connection. 1. B: Get evaluates the `select`: idle channel empty → `default` (channel.go:130). 2. A: Put(conn): takes the lock, no waiter, enqueues into the idle channel (channel.go:190), unlocks. 3. B: takes the lock (channel.go:131), openingConns 1 ≥ MaxCap → queues itself and blocks (channel.go:133-137).
(b) State after step 3: one idle connection and one blocked waiter = Open_Waiting_Stranded. A later Get by C takes the idle connection directly (channel.go:110) ahead of B. B is woken only by a later Put; if every later caller uses Close instead, B waits forever. Inferred from the code structure (the gap between the non-blocking receive and the lock); the interleaving is executed with a scheduler-controlled test in `as-is-tests.md` (T4).
(c) Q-05.

### P-02b — Put first, then Get

(a) 1. A: Put(conn) → Open_IdleAvailable. 2. B: Get.
(b) B receives the idle connection (channel.go:110 ("case wrapConn := <-conns:"), channel.go:129). Open_Empty or Open_AtCapacity afterwards (G-04).
(c) none — control trace.

### P-03a — Get blocks as a waiter, then Close

(a) 1. A: Get → creates (openingConns 1). 2. B: Get → waiter, blocks. 3. A: Close(conn).
(b) Step 3: openingConns 0 and the close callback run under the lock (channel.go:211 ("c.openingConns--")); nothing signals the queued request. State Open_Waiting_Stranded: capacity free, B still blocked. A new Get by C would create a connection (channel.go:154) while B keeps waiting. z3: SYS-3 is not preserved by E-CLOSE with waiters (`invariant-results.txt`). Executed in `as-is-tests.md` (T3).
(c) Q-04.

### P-03b — Close, then Get

(a) 1. A: Get → creates. 2. A: Close(conn) → Open_Empty. 3. B: Get.
(b) B creates a new connection (channel.go:154 ("conn, err := c.factory()")).
(c) none — control trace.

### P-04a — Get has passed the Ping-set check, then Release

(a) Ping configured, one idle connection. 1. A: Get receives the idle connection from its snapshot (channel.go:110) and evaluates `c.ping != nil` as true without the lock (channel.go:123 ("if c.ping != nil {")). 2. B: Release sets `c.ping = nil` under the lock (channel.go:229), closes and drains the idle channel (now empty). 3. A: calls `c.Ping(conn)`, which calls `c.ping(conn)` (channel.go:220).
(b) Unsynchronised read and write of `c.ping` (a data race in the Go memory model). If A's second read sees nil, `c.ping(conn)` is a call of a nil function value: a runtime panic in the caller's goroutine. If it sees the old value, A returns a connection that Release no longer owns and will never close. Executed with the race detector in `as-is-tests.md` (T5).
(c) Q-08 (race and panic), Q-07 (connection handed out during Release).

### P-04b — Release, then Get with Ping configured

(a) 1. B: Release. 2. A: Get.
(b) Snapshot nil → `ErrClosed` (channel.go:106); Ping never consulted.
(c) none — control trace.

### P-05a — Get is inside Factory, then Release is called

(a) Open_Empty. 1. A: Get takes the lock and calls Factory, which is slow (channel.go:154). 2. B: Release blocks on the lock (channel.go:225). 3. Factory returns; A increments openingConns (channel.go:159), unlocks, returns the connection. 4. B proceeds: Released. 5. A: Put(conn) → nil return, connection not closed.
(b) The connection is created and handed out although Release was called before it existed; Release cannot close it (it is not idle) and later returns cannot close it (close function cleared, channel.go:231 ("c.close = nil")).
(c) Q-07, Q-06, Q-09 (Release is blocked by a user callback).

### P-05b — Release, then Get (no Factory call)

(a) 1. B: Release. 2. A: Get.
(b) `ErrClosed` (channel.go:106); Factory not called.
(c) none — control trace.

### P-06a — Put, then Release (control trace)

(a) 1. A: Put(conn) → idle. 2. B: Release.
(b) Release closes the idle connection with the saved close function (channel.go:241 ("closeFun(wrapConn.conn)")).
(c) none — control trace, resting on DOC-6, README.md:55 ("Release all connections in the connection pool").
cited text contemplates this ordering: no — jev: unclear, scope 0.03.
The scope line is "no": the control verdict is void (requirement-scope rule). The question it raises — does "release all connections" cover only connections that are in the pool at the moment of Release, or every connection the pool created — is folded into Q-06.

### P-06b — Release, then Put

(a) 1. B: Release. 2. A: Put(conn) of a connection it got before.
(b) Released × E-PUT: `Close` → close function nil → returns nil (channel.go:176, channel.go:208); the connection stays open; nobody owns it.
(c) Q-06.

### P-07a — Close, then Release

(a) 1. A: Close(conn). 2. B: Release.
(b) Close decrements and closes (channel.go:211-212); Release closes the idle connections (channel.go:241). Every connection is closed once.
(c) none — control trace.

### P-07b — Release, then Close

(a) 1. B: Release. 2. A: Close(conn).
(b) Returns nil without calling any close function (channel.go:208 ("if c.close == nil {")); the connection stays open. The caller cannot tell (nil error).
(c) Q-06.

### P-08a — Put, then Close of the same connection

(a) MaxIdle 2. 1. A: Put(c1) → idle. 2. B (holding a stale reference to c1): Close(c1).
(b) Close decrements openingConns and closes c1 (channel.go:211-212); c1 stays in the idle channel. The next Get returns the closed c1 unless Ping rejects it (channel.go:123-129). openingConns is one lower than idle + checked-out.
(c) Q-10.

### P-08b — Close, then Put of the same connection

(a) 1. B: Close(c1). 2. A: Put(c1).
(b) c1 is closed and uncounted, then accepted into the idle channel (channel.go:190); same end state as P-08a.
(c) Q-10.

### P-09a — Idle connection expires, then a Get receives it (control trace)

(a) IdleTimeout = 15 s. 1. A: Put(c1) at t = 0. 2. No activity until t = 20 s. 3. B: Get at t = 20 s.
(b) G-02: age 20 s > 15 s → `Close(c1)` and retry (channel.go:116-119 ("wrapConn.t.Add(timeout).Before(time.Now())")); B then creates a new connection. Between t = 15 s and t = 20 s, c1 stays open in the pool.
(c) none — control trace, resting on DOC-2, README.md:13 ("the timeout connection will be closed and discarded").
cited text contemplates this ordering: no — jev: unclear, scope 0.05.
The scope line is "no": the control verdict is void. The question — is closing at the next Get what "will be closed and discarded" promises, or must an expired connection be closed when it expires — is Q-13.

### P-09b — Get receives the connection before it expires

(a) IdleTimeout = 15 s. 1. A: Put(c1) at t = 0. 2. B: Get at t = 10 s. 3. B holds c1 until t = 60 s, then Put(c1).
(b) B receives c1 (age 10 s ≤ 15 s, G-02 keep). Time spent checked out never counts: the Put at t = 60 s stamps a fresh time (channel.go:190).
(c) none — control trace.

## Free probes

### T-01 — Get when the pool is full waits (control trace)

(a) MaxCap 1. 1. A: Get → creates. 2. B: Get.
(b) Open_AtCapacity × E-GET → Open_AtCapacity_Waiting; B blocks (channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:137).
(c) none — control trace, resting on DOC-4, README.md:15 ("When the connection pool is full, support for connection waiting").
cited text contemplates this ordering: yes — jev: supported, scope 0.58.
The verdict covers that B waits. How long it waits, and whether it can give up ("like the go db connection pool"), is outside the cited ordering: Q-02.

### T-02 — Put into a full idle store closes the connection (control trace)

(a) MaxCap 3, MaxIdle 1. 1. A, B: Get → two connections. 2. A: Put(c1) → idle full. 3. B: Put(c2).
(b) Open_IdleFull × E-PUT: c2 is closed (channel.go:196 ("return c.Close(conn)")), openingConns 1. The idle store being full closes c2 although openingConns (2) is below MaxCap (3).
(c) none — control trace, resting on DOC-20, channel.go:195 ("连接池已满，直接关闭该连接").
cited text contemplates this ordering: yes — jev: supported, scope 0.30.
Jev's choice backs the ordering but its scope probability is below 0.5, so under routing rule 4 the ordering is not source-backed while my line says yes: the control verdict is void. Raised as Q-23, which cites both my scope line and the Jev result. (Content of the doubt: "the pool is full" can mean the idle store or MaxCap.)

### T-03 — Ping reports an idle connection invalid (control trace)

(a) Ping configured; the remote side has dropped the idle connection c1. 1. A: Get.
(b) G-03: Ping returns an error → `Close(c1)` (decrement, close callback) and retry (channel.go:124-126 ("if err := c.Ping(wrapConn.conn); err != nil {")); A then gets the next idle connection or a new one.
(c) none — control trace, resting on DOC-19, channel.go:122 ("判断是否失效，失效则丢弃").
cited text contemplates this ordering: yes — jev: supported, scope 0.31.
Not source-backed under routing rule 4 (scope below 0.5) while my line says yes: the control verdict is void. Raised as Q-24, citing both.

### T-04 — Get after Release returns ErrClosed (control trace)

(a) 1. B: Release. 2. A: Get.
(b) `ErrClosed` (channel.go:106 ("return nil, ErrClosed")).
(c) none — control trace, resting on DOC-12, pool.go:6 ("ErrClosed 连接池已经关闭Error").
cited text contemplates this ordering: no — jev: unclear, scope 0.02.
Void. The doc comment names the error but no operation or ordering; what each operation should do after Release is folded into Q-06.

### T-05 — Duplicate Close at capacity

(a) MaxCap 1. 1. A: Get → c1 (openingConns 1). 2. A: Close(c1). 3. A: Close(c1) again. 4. B: Get. 5. C: Get.
(b) Step 3 decrements to −1 (channel.go:211). Steps 4 and 5 both create connections (−1 < 1, then 0 < 1): two live connections with MaxCap 1. z3 witness for the general case in `invariant-results.txt`. Executed in `as-is-tests.md` (T6).
(c) Q-10.

### T-06 — Duplicate Put hands one connection to two callers

(a) MaxIdle 2. 1. A: Get → c1. 2. A: Put(c1). 3. A: Put(c1). 4. B: Get. 5. C: Get.
(b) Both Puts enqueue c1 (channel.go:190); B and C both receive c1. Executed in `as-is-tests.md` (T7).
(c) Q-11.

### T-07 — Factory calls back into the pool

(a) Factory implemented as `func() { p.Len(); return dial() }`. 1. A: Get in Open_Empty.
(b) Get holds `mu` while calling Factory (channel.go:154); `Len` → `getConns` → `mu.Lock()` (channel.go:96) on the same goroutine: deadlock. Every later Get, Put, Close, Release and Len blocks too. Executed in `as-is-tests.md` (T8).
(c) Q-09.

### T-08 — Slow Factory stalls unrelated callers

(a) Factory takes 2 s. 1. A: Get in Open_Empty. 2. B (holding a connection): Put. 3. C: Len.
(b) B and C block for the 2 s on `mu` (channel.go:172, channel.go:96). Executed in `as-is-tests.md` (T9).
(c) Q-09.

### T-09 — Factory returns (nil, nil)

(a) MaxCap 2. 1. A: Get → (nil, nil), openingConns 1. 2. A: Put(nil) → error "connection is nil. rejecting" (channel.go:169). 3. A: Close(nil) → same error (channel.go:204). Repeat once more.
(b) openingConns reaches 2 with zero usable connections: Open_AtCapacity forever; every later Get waits forever (channel.go:137).
(c) Q-19, Q-02.

### T-10 — Broken connection handed to a waiter without Ping

(a) Ping configured, MaxCap 1. 1. A: Get → c1. 2. B: Get → waits. 3. The remote side drops c1. 4. A: Put(c1).
(b) Put hands c1 to B (channel.go:183); B's wake-up path checks only expiry (channel.go:141-148), never Ping. B receives a broken connection. A Get on the idle path would have pinged it (channel.go:123). Executed in `as-is-tests.md` (T10).
(c) Q-14.

### T-11 — Stale Get at capacity in the Release window

(a) Open_AtCapacity. 1. A: Get takes its snapshot (channel.go:104). 2. B: Release clears the fields and unlocks (channel.go:232) but has not yet closed the idle channel (channel.go:238). 3. A: `select` on the still-open empty channel → `default`; takes the lock; openingConns ≥ MaxCap → queues itself (channel.go:133-137).
(b) The capacity test precedes the released test (channel.go:133 before channel.go:150; z3 G-04 ordering witness): A waits on a released pool forever. Narrow window; inferred from the code, not executed.
(c) Q-07.

### T-12 — MaxCap = 0 accepted (NAT violation by configuration)

(a) Config InitialCap 0, MaxIdle 0, MaxCap 0. 1. A: Get.
(b) Validation passes (G-01 witness). openingConns 0 ≥ 0 → A waits forever; no Put can ever arrive. Executed in `as-is-tests.md` (T11).
(c) Q-20.

### T-13 — Callers lose connections

(a) MaxCap 2. 1. A: Get → c1; A drops c1 (no Put, no Close). 2. B: Get → c2; B drops it. 3. C: Get.
(b) openingConns stays 2 (channel.go:159); C waits forever. No detection, no reclaim.
(c) Q-12, Q-02.

### T-14 — Close-callback error on the discard path

(a) IdleTimeout 1 s; the close callback returns an error. 1. A: Put(c1). 2. 2 s later B: Get.
(b) Get discards c1 via `Close` (channel.go:118); the callback's error is dropped; openingConns was decremented before the callback (channel.go:211). B gets a new connection; nobody learns that closing c1 failed.
(c) Q-18.

### T-15 — Expired idle connections are never closed while traffic is absent

(a) IdleTimeout 15 s, InitialCap 5. 1. Construction at t = 0. 2. No Get until t = 3600 s.
(b) Five connections stay open for an hour although expired after 15 s; the remote side may close them meanwhile. They are closed at the first Get after t = 15 s, one per receive (channel.go:116-119), or at Release.
(c) Q-13.

## Multi-instance probes

NAT-SYS-1: N processes each run one pool against the same remote server (InitialCap 5, MaxCap 30, IdleTimeout 15 s, as in the README example).

### M-01 — Shared-fate reset over three failure/recovery cycles

(a) Cycle k = 1..3: the server restarts; every pooled connection of every instance dies at the same moment; traffic resumes.
(b) No pool state is reset by the server event: there is no counter, cooldown or backoff to reset (lint L-8). Without Ping, each instance hands out its dead idle connections first (channel.go:129), so the first callers fail and typically Close them (decrement). With Ping, each Get discards dead connections and calls Factory (channel.go:154). Per cycle the aggregate dial load is up to N × (connections needed by the first traffic wave), all at the moment traffic resumes; a Factory error is returned at once with no retry or delay (channel.go:157), so the callers' own retry policy sets the herd size. Nothing in the pool decorrelates the instances, and the cycles repeat identically (no damping, no amplification from the pool itself).
(c) Q-21.

### M-02 — Expiry dispersion

(a) N instances deployed together; the construction timestamps of the 5 initial connections are equal within milliseconds across instances (channel.go:88).
(b) If traffic is quiet for more than 15 s, all N × 5 initial connections expire together; the first Get on each instance discards them and dials anew (G-02, channel.go:154): a synchronised reconnect wave. Later Puts stamp times from traffic (channel.go:190), which disperses the timestamps; the pool adds no jitter.
(c) Q-21.

### M-03 — Degraded-recovery herd with a slow server

(a) The server recovers partially and accepts connections slowly (each dial takes seconds). Instance A's Get calls Factory; instance B's Get calls Factory; the dials fail again.
(b) Inside each instance the slow Factory runs under `mu` (channel.go:154), so each instance dials at most once at a time — this serialises the instance's load on the server — but every Put, Close, Len and Release of that instance stalls for the dial's duration (T-08). Callers with their own deadlines give up and retry, which queues more Gets behind the mutex; when the server fails again each queued Get's Factory error returns at once (channel.go:157). Per instance the server sees at most one concurrent dial; in aggregate N.
(c) Q-21, Q-09.
