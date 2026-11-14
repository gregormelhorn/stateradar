# Invariants and lint findings

NAT predicates are proposed environment assumptions. SYS predicates are obligations under review; an outcome that depends on an open interpretation retains a Q.

- NAT-01. Constructor receives a non-nil Config, with integer capacities satisfying 0 ≤ InitialCap ≤ MaxIdle ≤ MaxCap. The numeric condition is enforced. Config nonnil is unguarded. channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {"). Q-12.
- NAT-02. Callers return a checked-out resource to its original pool at most once and do not concurrently dispose of it. Based on example use at README.md:46–53. Boundary does not enforce it. Q-11.
- NAT-03. Factory produces usable values on success and owns partial failure. Close and Ping return without blocking indefinitely and observe caller type requirements. Roles documented at channel.go:25, 27 and 29. Stronger contracts absent. Q-21.
- NAT-04. The effective system time sample is the deadline reference for elapsed idle age. Code uses strict Before. channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"). Q-17.
- NAT-05. A private request is registered once per invocation and has one authorized matching send. Mutex serializes queue mutation. channel.go:134 ("req := make(chan connReq, 1)"), channel.go:182 ("c.connReqs = c.connReqs[:l-1]"), channel.go:183 ("req <- connReq{").
- NAT-06. N pools sharing a backend may see a common failure/recovery signal at nearly the same time. This is an environment scenario. See M-01 to M-03.

| Obligation | Initializing | Open | Open_Waiting | Open_WaitingWithIdle | Released | Released_Waiting |
|---|---|---|---|---|---|---|
| SYS-01 Idle occupancy ≤ MaxIdle | Holds during validated fill | Holds channel bound | Holds | Holds | Public occupancy zero, old buffer bounded | Same |
| SYS-02 An expired candidate is discarded and closed | Consumption not published | Normally invokes Close and loops | Handoff checks age | Both receive paths check age | Captured candidate can skip actual close | Same |
| SYS-03 Configured health prevents invalid checkout | No Ping during fill | Buffered path only | New and handoff paths bypass | Same, available buffer can Ping | In-flight success can return | Same |
| SYS-04 Release settles outstanding work and owned resources | Rollback drains buffered successes, cleanup failures open | Detaches and drains idle; checkout, callback errors and old views open | Waiters remain | Waiters remain, buffer drains or races capture | Repeat releases do not join active drain | Waiters remain blocked |
| SYS-05 Len reports current idle occupancy | Structurally inaccessible before publication | Yes at len sample | Yes | Yes | Fresh snapshot zero | Fresh snapshot zero |
| SYS-06 Active accounting corresponds to live owned resources | Preset count is a fill target | Conditional on callback and caller discipline | Close failure can free count | Same | Counter retained with resources drained or checked out | Same |
| SYS-07 Each returned resource belongs to one borrower | No borrower before publication | Duplicate Put can create two lends | Foreign Put can be delivered | Both outcomes | Stale handouts may complete | Same |

Evidence for SYS-01 and SYS-05: channel.go:70 ("conns:        make(chan *idleConn, poolConfig.MaxIdle),"), channel.go:88 ("c.conns <- &idleConn{conn: conn, t: time.Now()}"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:247 ("return len(c.getConns())"). SYS-02 and SYS-03: channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"), channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {"), channel.go:148 ("return ret.idleConn.conn, nil"), channel.go:161 ("return conn, nil"), channel.go:208 ("if c.close == nil {"). Q-05, Q-06, Q-07, Q-17. SYS-04: channel.go:137 ("ret, ok := <-req"), channel.go:227 ("c.conns = nil"), channel.go:234 ("if conns == nil {"), channel.go:238 ("close(conns)"), channel.go:241 ("closeFun(wrapConn.conn)"). Q-01, Q-05, Q-10, Q-15. SYS-06 and SYS-07: channel.go:75 ("openingConns: poolConfig.InitialCap,"), channel.go:159 ("c.openingConns++"), channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:211 ("c.openingConns--"). Q-10, Q-11.

## Doctrine mapping

<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 DOC-5 DOC-6 DOC-7 DOC-8 DOC-9 DOC-10 DOC-11 DOC-12 DOC-13 -->

| ID | Kind | Target |
|---|---|---|
| DOC-1 | structural | Pool API shape is checked against pool.go declarations and model review |
| DOC-2 | invariant | SYS-02 |
| DOC-3 | invariant | SYS-03 |
| DOC-4 | cell | Open x Get |
| DOC-5 | cell | Initializing x FactoryResult |
| DOC-6 | cell | Open x Close |
| DOC-7 | cell | Open x PingResult |
| DOC-8 | rejected | The numbers are an illustrative configuration. The general capacity relation is proven by G-01 |
| DOC-9 | invariant | SYS-02 |
| DOC-10 | cell | Open x Get |
| DOC-11 | cell | Open x Put |
| DOC-12 | invariant | SYS-04 |
| DOC-13 | invariant | SYS-05 |

DOC-3 is violated under a universal configured-Ping obligation; exact requirement coverage across direct handoff and creation is open in Q-07. DOC-12 leaves scope of “all connections in the connection pool” open; drains attached idle values but has no checked-out registry or waiter settlement. Q-01, Q-05. DOC-13 is ambiguous about occupancy relative to checkout. Q-14.

## Lint sweep

| Lint | As-is finding or inspected outcome | Fault | Trigger |
|---|---|---|---|
| Waiting without a timeout | Private receive blocks without timer or cancellation, channel.go:137 ("ret, ok := <-req"). Q-16 | F-13 | step-5 lint |
| Retries without max | Discard loops continue as input permits, channel.go:119 ("continue"), channel.go:126 ("continue"), channel.go:145 ("continue"). Factory returned errors stop. Q-17 | F-13 | step-5 lint |
| External failure outcome | Close failures are discarded on expiry/drain, channel.go:118 ("c.Close(wrapConn.conn)"), channel.go:241 ("closeFun(wrapConn.conn)"). Panic impacts differ. Q-09, Q-10 | F-03 | step-5 lint |
| Cancellation | Caller departure has no synchronization with private receive, channel.go:137 ("ret, ok := <-req"), channel.go:183 ("req <- connReq{"). Q-04 | F-09 | step-5 lint |
| Terminal/error diagnosis | Sentinels are literal error objects. Stale post-detachment waiting and late cleanup acknowledge without a diagnostic, channel.go:139 ("return nil, ErrMaxActiveConnReached"), channel.go:209 ("return nil"). Q-01, Q-05 | F-20 | step-5 lint |
| Startup/shutdown | Constructor has no nil-input guard. Release only drains captured buffer; it leaves request and counter storage. channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {"), channel.go:227 ("c.conns = nil"), channel.go:238 ("close(conns)"). Q-01, Q-12, Q-18 | F-07 | step-5 lint |
| Unbounded queue / overload | Queue append has no bound, idle buffer has a bound and calls Close on overflow. channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:196 ("return c.Close(conn)"). Q-16 | F-13 | step-5 lint |
| Synchronized reset | No recovery-triggered reset or backoff. Shared caller waves are possible on a common backend. channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err"). Q-20 | F-10 | multi-instance probes |
| Lifecycle disagreement | Separate request and teardown tracks. Release has no request settlement, while Close frees count without waking requests. channel.go:137 ("ret, ok := <-req"), channel.go:211 ("c.openingConns--"), channel.go:238 ("close(conns)"). Q-01, Q-03 | F-07 | step-5 lint |
| Dual cleanup | No finalizer in this component. Explicit Close and Release draining can both close a wrapper kept idle after Close. channel.go:212 ("return c.close(conn)"), channel.go:241 ("closeFun(wrapConn.conn)"). Q-11 | F-08 | step-5 lint |
| Async cancellation isolation | Successful Put hands ownership to blocked Get independently of external caller departure. channel.go:137 ("ret, ok := <-req"), channel.go:183 ("req <- connReq{"). Q-04 | F-09 | step-5 lint |
| User-model gap | Closed, deferred and late no-op cleanup depend on lock order and pre-lock observations. See P-01a, P-03a and P-04b. Q-01, Q-02, Q-05 | F-04 | step-5 lint |
| Reentry | Factory and Close callback under the same lock that Len and other methods take. channel.go:96 ("c.mu.Lock()"), channel.go:154 ("conn, err := c.factory()"), channel.go:206 ("c.mu.Lock()"), channel.go:212 ("return c.close(conn)"). Q-08 | F-11 | step-3 lock-discipline annotation |
