# Extraction

Scope: one channelPool instance, its construction, public Pool calls and synchronous callback invocations. Actors are owner, requester, independent holders, observer and callback implementations. TCP/RPC internals, application cancellation and upstream resource ownership are outside the boundary. No neighboring model was supplied.

## Doctrine lines

- DOC-1 explicit-requirement README.md:12 ("- More versatile, The connection type in the connection pool is `interface{}`, making it more versatile").
- DOC-2 explicit-requirement README.md:13 ("- More configurable, The connection supports setting the maximum idle time, the timeout connection will be closed and discarded, which can avoid the problem of automatic connection failure when idle").
- DOC-3 explicit-requirement README.md:14 ("- Support user setting `ping` method, used to check the connectivity of connection, invalid connection will be discarded").
- DOC-4 explicit-requirement README.md:15 ("- Support connection waiting, When the connection pool is full, support for connection waiting (like the go db connection pool)").
- DOC-5 explicit-requirement README.md:21 ("//factory Specify the method to create the connection").
- DOC-6 explicit-requirement README.md:24 ("//close Specify the method to close the connection").
- DOC-7 explicit-requirement README.md:27 ("//ping Specify the method to detect whether the connection is invalid").
- DOC-8 explicit-requirement README.md:30 ("//Create a connection pool: Initialize the number of connections to 5, the maximum idle connection is 20, and the maximum concurrent connection is 30").
- DOC-9 explicit-requirement README.md:38 ("	//The maximum idle time of the connection, the connection exceeding this time will be closed, which can avoid the problem of automatic failure when connecting to EOF when idle").
- DOC-10 explicit-requirement README.md:46 ("//Get a connection from the connection pool").
- DOC-11 explicit-requirement README.md:52 ("//Put the connection back into the connection pool, when the connection is no longer in use").
- DOC-12 explicit-requirement README.md:55 ("//Release all connections in the connection pool, when resources need to be destroyed").
- DOC-13 explicit-requirement README.md:58 ("//View the number of connections in the current connection pool").

## As-is observations

| Phase or context | Observed-in-code evidence |
|---|---|
| Construction | Dereferences config, validates ordered nonnegative caps and required Factory/Close, creates bounded idle channel and initializes accounting from requested initial size. channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {"), channel.go:62 ("if poolConfig.Factory == nil {"), channel.go:65 ("if poolConfig.Close == nil {"), channel.go:70 ("conns:        make(chan *idleConn, poolConfig.MaxIdle),"), channel.go:75 ("openingConns: poolConfig.InitialCap,"). Optional Ping independently enabled when supplied. channel.go:78 ("if poolConfig.Ping != nil {"). Fill synchronously calls Factory and timestamps values before publication, rolls back earlier successes on returned error. channel.go:83 ("conn, err := c.factory()"), channel.go:85 ("c.Release()"), channel.go:86 ("return nil, fmt.Errorf("factory is not able to fill the pool: %s", err)"), channel.go:88 ("c.conns <- &idleConn{conn: conn, t: time.Now()}"), channel.go:91 ("return c, nil"). Q-13. |
| Published receiver | Idle channel and Factory/Close are nonnil, Ping optional. Idle length may be zero to MaxIdle. Count can be below or at cap in ordinary arithmetic. Foreign or duplicate Close can drive it negative. The guard proof also samples above-cap counter values without presuming their ordinary reachability. Wait queue can be absent or nonempty with either empty or nonempty idle channel. Mixed state confirmed in P-01a; waiters can persist when count falls under cap after Close. channel.go:70 ("conns:        make(chan *idleConn, poolConfig.MaxIdle),"), channel.go:78 ("if poolConfig.Ping != nil {"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:211 ("c.openingConns--"). |
| Get snapshot and idle receive | Mutex protects snapshot acquisition only. channel.go:96 ("c.mu.Lock()"), channel.go:97 ("conns := c.conns"), channel.go:98 ("c.mu.Unlock()"), channel.go:104 ("conns := c.getConns()"), channel.go:110 ("case wrapConn := <-conns:"). Closed/no wrapper rejects. Idle value may expire, fail Ping or return. channel.go:112 ("return nil, ErrClosed"), channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"), channel.go:118 ("c.Close(wrapConn.conn)"), channel.go:123 ("if c.ping != nil {"), channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:129 ("return wrapConn.conn, nil"). Cleanup error ignored in loop. |
| Get admission and wait | Miss precedes lock. Capacity check precedes availability check. At capacity creates a private one-buffer reply channel and waits outside mutex. Only a closed reply channel produces max sentinel. channel.go:130 ("default:"), channel.go:131 ("c.mu.Lock()"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:134 ("req := make(chan connReq, 1)"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:137 ("ret, ok := <-req"), channel.go:139 ("return nil, ErrMaxActiveConnReached"), channel.go:150 ("if c.factory == nil {"). No normal path closes that channel. Below capacity Factory runs under mutex, increments only on nil error. channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err"), channel.go:159 ("c.openingConns++"), channel.go:160 ("c.mu.Unlock()"). |
| Handoff and retry | Reply payload timestamp checked if enabled; too old closes and retries. Successful direct delivery returns without Ping. channel.go:141 ("if timeout := c.idleTimeout; timeout > 0 {"), channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {"), channel.go:144 ("c.Close(ret.idleConn.conn)"), channel.go:145 ("continue"), channel.go:148 ("return ret.idleConn.conn, nil"), channel.go:184 ("idleConn: &idleConn{conn: conn, t: time.Now()},"). No wait timeout or cancellation in Pool.Get, and no background expiry or factory retry documented in this component; loops follow expired or invalid resource observations. channel.go:108 ("for {"), channel.go:137 ("ret, ok := <-req"), channel.go:157 ("return nil, err"). |
| Put and Close | Nil interface rejected. Under lock Put prefers FIFO head, shifts references and sends buffered reply. Otherwise sends idle or unlocks and attempts overflow cleanup. channel.go:168 ("if conn == nil {"), channel.go:174 ("if c.conns == nil {"), channel.go:179 ("if l := len(c.connReqs); l > 0 {"), channel.go:181 ("copy(c.connReqs, c.connReqs[1:])"), channel.go:182 ("c.connReqs = c.connReqs[:l-1]"), channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:194 ("c.mu.Unlock()"), channel.go:196 ("return c.Close(conn)"). Close locks, checks callback, decrements before invoking it, defers unlock and returns error. channel.go:203 ("if conn == nil {"), channel.go:206 ("c.mu.Lock()"), channel.go:207 ("defer c.mu.Unlock()"), channel.go:208 ("if c.close == nil {"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)"). |
| Drain and detached | Detach swaps idle channel and callbacks to nil under lock. Captured channel can remain open until owner closes it; once closed, buffered values can be read by earlier Get snapshots and the drainer. Close errors are discarded and the old counter/FIFO unchanged, including waiters appended by earlier Get misses. Repeat Release returns on nil channel. channel.go:225 ("c.mu.Lock()"), channel.go:226 ("conns := c.conns"), channel.go:227 ("c.conns = nil"), channel.go:228 ("c.factory = nil"), channel.go:229 ("c.ping = nil"), channel.go:230 ("closeFun := c.close"), channel.go:231 ("c.close = nil"), channel.go:232 ("c.mu.Unlock()"), channel.go:234 ("if conns == nil {"), channel.go:238 ("close(conns)"), channel.go:239 ("for wrapConn := range conns {"), channel.go:241 ("closeFun(wrapConn.conn)"). Fresh Len returns zero, older snapshots can still sample the detached buffer. channel.go:247 ("return len(c.getConns())"). |
| Ownership combinations | Idle entries, held resources, private delivered-but-unconsumed results and closers in progress are distinct. Pool stores no caller or lease identity. An application can abandon its own waiter independently; a later Put can still deliver. The only queue consumer other than waiting receivers is Put, and Release has no corresponding sweep. channel.go:137 ("ret, ok := <-req"), channel.go:148 ("return ret.idleConn.conn, nil"), channel.go:180 ("req := c.connReqs[0]"), channel.go:183 ("req <- connReq{"), channel.go:238 ("close(conns)"), channel.go:241 ("closeFun(wrapConn.conn)"). |

## Seam contract sweep

| Seam | Documented guarantee, gaps and review |
|---|---|
| Factory | S1 supported, creates a connection per channel.go:25 ("//生成连接的方法") and README.md:21. S4 unclear, no ownership contract for returning a value together with an error. No maximum delay, panic/re-entry or cleanup guarantee. NAT-02 candidate; Q-11/Q-13/Q-21. Error handling at channel.go:85 ("c.Release()") and channel.go:157 ("return nil, err") describes this caller only. |
| Close | S2 supported, closes connection per channel.go:27 ("//关闭连接的方法") and README.md:24. S5 unclear, no guarantee of remaining live on error or of no partial disposal. No deadline or re-entry statement. NAT-02 candidate; Q-10/Q-11/Q-21. Call-site distinction at channel.go:212 ("return c.close(conn)") and channel.go:241 ("closeFun(wrapConn.conn)"). |
| Ping | S3 supported, checks connection per channel.go:29 ("//检查连接是否有效的方法") and README.md:27. S6 unclear, no timing, panic or re-entrancy guarantee. Preserves distinction between returned error and independently known physical status. NAT-02 candidate; Q-08/Q-09/Q-21. |
| Stdlib mutex | `sync/rwmutex.go:141-143` says Lock blocks until the lock is available. `sync/rwmutex.go:31-32` gives Unlock→later Lock synchronization. Those guarantees apply only where both actors participate. They do not order unsynchronized reads at channel.go:123 ("if c.ping != nil {") and channel.go:220 ("return c.ping(conn)") against channel.go:229 ("c.ping = nil"). |
| Channel and time language/runtime primitives | Buffered values can be received after close and before the closed-and-empty zero-value receive. Nil channel len is zero. Make capacity and send gates are G-01/G-05/G-06. time.Now and Time.Before sample and compare time. No elapsed-time guarantee for scheduling around either check. G-04/G-14 and Q-14. |
| Debugf | Under the admission lock, invokes logrus channel.go:132 ("log.Debugf("openConn %v %v", c.openingConns, c.maxActive)"). Logging is a diagnostic seam. Pool contract specifies no logger-hook execution limits or re-entry guarantees. Lifecycle effect depends on the configured logger; Q-11/Q-21. |
| Example/test callbacks | README factory and closer illustrate TCP and concrete-type assertion. Test factory uses rpc.DialHTTP, channel_rpc_test.go:21 ("return rpc.DialHTTP("tcp", address)"). Test closer asserts *rpc.Client then invokes Close, channel_rpc_test.go:24 ("nc := v.(*rpc.Client)"). These are sample topologies, no general callback error/timeout guarantee. Q-20/Q-21. |

## Routed draft review

All 56 accepted formatted draft claims had verified fragments. I reread README.md, pool.go and channel_rpc_test.go. The single unclear test draft claim C19 is retained as test implementation evidence: channel_rpc_test.go:263 ("arith := new(Arith)"), channel_rpc_test.go:264 ("rpc.Register(arith)"), channel_rpc_test.go:265 ("rpc.HandleHTTP()"), channel_rpc_test.go:267 ("l, e := net.Listen("tcp", address)") and channel_rpc_test.go:271 ("go http.Serve(l, nil)"). The draft's cited line alone establishes only HTTP RPC handler registration. The test's immediate-error claim is the assertion, separate from executed behavior.

Flash's channel.go draft was malformed JSON and is retained raw. I extracted that file directly. Other drafts lacked the in-operation readiness miss, split Ping read, overflow release gap, counter drift after failed disposal, queue backing references, exact post-release cutoff conditions and finite validation of the test contradiction. These are in the extraction, traces and test replay. No draft alone sets provenance.

| Draft | Draft question numbers → disposition |
|---|---|
| README.md | 1→Q-09, 2→Q-09/Q-10, 3→Q-01, 4→Q-01/Q-05, 5→Q-13, 6→Q-13, 7→Q-07/Q-10, 8→Q-14, 9→Q-13/Q-14, 10→Q-13, 11→Q-07, 12→Q-12, 13→Q-15, 14→Q-09/Q-22, 15→Q-10/Q-14, 16→Q-07, 17→Q-15. |
| pool.go | 1→Q-01/Q-07/Q-15 (interface behavior specified by concrete code), 2→Q-01/Q-02, 3→Q-07/Q-17, 4→Q-15, 5→Q-01/Q-13, 6→Q-07/Q-12, 7→Q-10/Q-12, 8→Q-07/Q-12, 9→Q-02/Q-04/Q-08. |
| channel_rpc_test.go | 1→Q-07, 2→Q-07/Q-10, 3→Q-07, 4→Q-03, 5→Q-12, 6→Q-14, 7→Q-15, 8→Q-01/Q-02, 9→Q-15, 10→Q-02, 11→Q-13, 12→Q-13/Q-15, 13→Q-13, 14→Q-20. |

Each fold retains the triggering condition and effect in the linked question, matrix or trace. Directly observed answers about nil checks, timestamp writes, startup errors and callback calls settle the as-is observations only.

## Finding verification

Each Step-8 check and its accepted source fragment survives in claims-channel.result.json and claims-tests.result.json. The 31 supported channel checks match the source on reread. The test claim T1 is supported as an assertion only. The six unclear and one contradicted channel checks retain distinct manual dispositions.

| Check | Manual adjudication after reread |
|---|---|
| C11 (unclear) | Keep success after detach, Q-08. channel.go:129 ("return wrapConn.conn, nil") returns without another lifecycle field read. TestProbePingRelease ordered callback entry, Release completion and success. |
| C18 (unclear) | Keep handoff skip, Q-09. channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {") begins age-only guard and channel.go:148 ("return ret.idleConn.conn, nil") returns. The Ping site at channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {") is in a different branch. |
| C19 (unclear) | Keep observed window, Q-04. channel.go:130 ("default:") precedes channel.go:131 ("c.mu.Lock()"), and Put commits at channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"). Two probe cap subcases confirm externally observed outcomes. |
| C28 (unclear) | Keep absent wake, Q-02. channel.go:226 ("conns := c.conns") captures only idle channel, channel.go:238 ("close(conns)") closes it, channel.go:241 ("closeFun(wrapConn.conn)") ends the drain. There is no close of the separately allocated channels at channel.go:134 ("req := make(chan connReq, 1)"). |
| C30 (unclear) | Keep repeat completion while first drain active, Q-17. Detach at channel.go:227 ("c.conns = nil") precedes channel.go:232 ("c.mu.Unlock()"), and return branch channel.go:234 ("if conns == nil {") does not join channel.go:241 ("closeFun(wrapConn.conn)"). |
| C32 (contradicted) | Narrow wording to nil-config dereference (Q-13). For a nonnil malformed configuration arithmetic validation does return an error at channel.go:60 ("return nil, errors.New("invalid capacity settings")"). A nil argument faults at the first field access in channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {"). |
| C38 (unclear) | Keep as conditional on recovery, Q-11. channel.go:131 ("c.mu.Lock()") acquires, channel.go:154 ("conn, err := c.factory()") invokes callback, and both unlock sites channel.go:156 ("c.mu.Unlock()"), channel.go:160 ("c.mu.Unlock()") are after callback return. Contrast Close's deferred channel.go:207 ("defer c.mu.Unlock()"). |

ErrClosed and the max-active sentinel are literal errors.New values, not computed values. pool.go:7 ("ErrClosed = errors.New("pool is closed")"), channel.go:14 ("ErrMaxActiveConnReached = errors.New("MaxActiveConnReached")"). The max-active value is behind the closed-waiter branch. Verified findings distinguish exposed API discrepancies (Q-01), reproduced scheduling behaviors (Q-02/Q-03/Q-04/Q-07/Q-08), policy gaps (e.g. Q-06/Q-09/Q-15), and unmeasured runtime retention (Q-16). No requirement-scope verdict changed a source observation.

The additional Go race run independently reports an actual data race at the buffered Get Ping presence read and the Release write. Q-08 is verified as an implementation data race, separate from shutdown intent and the ordered nil-dispatch probe.

Concrete seam review followed the test's actual callees. Installed Go `net/rpc/client.go:239-241` documents DialHTTP default path without a deadline, and `:247-266` implements dial, CONNECT response handling and attempt to close the failed handshake. `:281-282` documents the already-shutting-down ErrShutdown return, and `:283-291` marks closing before invoking the codec. Codec Close failure does not roll back that flag. That test topology therefore cannot assume every nonnil error means no physical close. `github.com/sirupsen/logrus@v1.8.3/hooks.go:3-10` documents synchronous enabled hooks and possible blocking. `hooks.go:26-32` returns the first hook error, and `entry.go:280-283` emits it on stderr, leaving no error return to Pool.Get. An enabled hook that reenters Len encounters the already-held pool lock. This additional configuration was inspected, separate from the present Go fixture.

Jev R1/R2 (RPC), L1/L2 (logrus) and M1/M2 (RWMutex) all supported the cited guarantees. The reviewed source and batch files preserve the precise claims.

### Readable questions from the rejected Flash draft

The raw channel.go response could be read despite its malformed claim ID. No rejected claim was imported on model authority. All visible questions are dispositioned in original order.

| Raw question | Disposition |
|---|---|
| 1. Partial construction rollback | Q-13 and Q-10. Prior buffered results drain synchronously, errors from disposal are discarded. |
| 2. Opening count on Release | Q-15 and Q-17. Releases do not decrement the count. |
| 3. Nil captured closer | answered: channel.go:225-235. Successful construction supplies the closer. One Release atomically detaches both fields, and next Release returns on nil channel before invoking it. |
| 4. Abandoned Get / blocked send | Q-05. A fresh private channel has room for its only normal send. Application departure still leaves a possible orphan result. |
| 5. Nil wrapper | answered: channel.go:88, 110-112, 190 and 238. Normal producer sites construct nonnil wrappers. Closed-and-empty receive gives nil. |
| 6. Idle close accounting | Q-10 and Q-15. Count spans buffered and checked-out resources and is decremented before disposal result. |
| 7–8. Handoff skips Ping and caller validity | Q-09 and Q-12. |
| 9. Put after detach | Q-07. |
| 10. Put and Get different paths | Q-04, P-01a/P-01b. Idle receive and handoff may overlap. |
| 11. Nil Factory ErrClosed | Q-02. Post-miss availability can follow at-cap admission. |
| 12. Retry bounds | Q-14. |
| 13. Request channel closure | Q-01, Q-02 and Q-05. No normal closure found. |
| 14. On-demand Factory error and accounting | Q-13 and Q-03. Error path leaves count and waiters unchanged. |
| 15. ErrClosed definition | answered: pool.go:7. |
| 16. Pool declaration | answered: pool.go:11-20. |
| 17. Direct Ping can panic | Q-08 and Q-22. |
| 18. Close nil callback and count | Q-07, Q-10 and Q-15. |
| 19. Get/Put on closed channel | Q-02, Q-07 and Q-08. Put send shares the detach mutex and checks conns after locking. A prior Get snapshot can receive a buffered item or the closed zero value. |
| 20. Age timestamp | Q-14. Construction, buffering and handoff stamp separate events. |
| 21. MaxIdle full | Q-07 and Q-10. The channel capacity remains bounded. Overflow disposal depends on close availability and result. |
| 22. Held or queued ownership at Release | Q-02/Q-05/Q-07. |
| 23. Unused waitTimeOut | Q-01. Declared at channel.go:46 ("idleTimeout, waitTimeOut time.Duration") but has no wait-site reference. |
| 24–25. Nil handoff wrapper and producers | answered: channel.go:183-185. The sole producer constructs a nonnil idleConn, and the false receive branch would return before dereferencing. |
| 26. Release idempotence | Q-17. Snapshot, detach and repeated-release check are ordered by the same mutex. |
| 27. Wait timeout | Q-01/Q-05. |
| 28. Delayed handoff drop | Q-14. Put already returned nil; later stale receive closes and retries without notifying it. |
| 29. Len semantics | Q-15. |
