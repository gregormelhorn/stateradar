# Adversarial traces

### P-01a — Get → Put

Open at capacity, no idle. G misses receive. P locks, sees no waiters, buffers its resource and returns. G locks without rechecking, appends its waiter and blocks. Later G2 takes the idle resource; G1 only completes on a further Put. Below capacity G creates instead and buffer stays populated.

Observed-in-code evidence: channel.go:110 ("case wrapConn := <-conns:"), channel.go:131 ("c.mu.Lock()"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:154 ("conn, err := c.factory()"), channel.go:179 ("if l := len(c.connReqs); l > 0 {"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:").

Disposition: handle or guarded outcome above → Q-02.

- Reachability: Open → Open_WaitingWithIdle — domain-analysis/channelPool/_probe/window_test.go:34 ("waiter failed to coexist with idle storage")

### P-01b — Put → Get

Open with a held value. P buffers before G attempts receive. G receives that value, then validates age and optional health. With an established waiter, Put handoff precedes any storage attempt independently of cap.

Observed-in-code evidence: channel.go:110 ("case wrapConn := <-conns:"), channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"), channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:179 ("if l := len(c.connReqs); l > 0 {"), channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:").

Disposition: handle or guarded outcome above → Q-07.

### P-02a — Get → Close

At cap G appends. Closer frees one slot even on returned callback error. G remains blocked, G2 can create and complete before G. A later Put is the next wake.

Observed-in-code evidence: channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:137 ("ret, ok := <-req"), channel.go:154 ("conn, err := c.factory()"), channel.go:179 ("if l := len(c.connReqs); l > 0 {"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)").

Disposition: handle or guarded outcome above → Q-03.

### P-02b — Close → Get

Closer decrements on a held connection before G makes its cap decision. If now below cap with no idle, G creates. If closer instead targets a still-buffered value, G may return that same value.

Observed-in-code evidence: channel.go:110 ("case wrapConn := <-conns:"), channel.go:129 ("return wrapConn.conn, nil"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:154 ("conn, err := c.factory()"), channel.go:211 ("c.openingConns--").

Disposition: handle or guarded outcome above → Q-11.

### P-03a — Get → Release

Open_Waiting begins with a registered pending request. R detaches under mutex and drains idle only. Subsequent late Put returns success without cleanup or wake. A checkout already removed may succeed after detachment. In a second schedule, G misses then R detaches before G locks: at cap G appends on released pool, below cap returns ErrClosed.

Observed-in-code evidence: channel.go:110 ("case wrapConn := <-conns:"), channel.go:131 ("c.mu.Lock()"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:137 ("ret, ok := <-req"), channel.go:150 ("if c.factory == nil {"), channel.go:174 ("if c.conns == nil {"), channel.go:209 ("return nil"), channel.go:227 ("c.conns = nil"), channel.go:238 ("close(conns)").

Disposition: handle or guarded outcome above → Q-01.

- Reachability: Open_Waiting → Released_Waiting — domain-analysis/channelPool/_probe/observe_test.go:79 ("pending(t, waiting)")

### P-03b — Release → Get

R detaches before a fresh G snapshots, so G rejects with ErrClosed while drain may still block. A call with an older snapshot follows P-03a.

Observed-in-code evidence: channel.go:104 ("conns := c.getConns()"), channel.go:106 ("return nil, ErrClosed"), channel.go:227 ("c.conns = nil"), channel.go:232 ("c.mu.Unlock()"), channel.go:241 ("closeFun(wrapConn.conn)").

Disposition: reject, ErrClosed; none — control trace.

### P-04a — Put → Release

P holds the lock when buffering or sending while R waits. A buffered value is drained unless a Get holding the old channel wins the receive. A private send committed first may be received after detach. An overflow Put unlocks before Close, so Release may clear its delegate first.

Observed-in-code evidence: channel.go:172 ("c.mu.Lock()"), channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:194 ("c.mu.Unlock()"), channel.go:196 ("return c.Close(conn)"), channel.go:225 ("c.mu.Lock()"), channel.go:231 ("c.close = nil"), channel.go:238 ("close(conns)"), channel.go:241 ("closeFun(wrapConn.conn)").

Disposition: handle or guarded outcome above → Q-05.

### P-04b — Release → Put

R clears the fields. Late P acquires after detachment, delegates to Close and returns nil without cleanup. A nil interface is still rejected up front.

Observed-in-code evidence: channel.go:168 ("if conn == nil {"), channel.go:174 ("if c.conns == nil {"), channel.go:176 ("return c.Close(conn)"), channel.go:208 ("if c.close == nil {"), channel.go:209 ("return nil"), channel.go:231 ("c.close = nil").

Disposition: handle or guarded outcome above → Q-05.

### P-05a — Close → Release

Ordinary Close locks, decrements, invokes callback and returns its success/error before R can detach. If it panics, deferred unlock lets R continue; concurrently checked idle copies may still be drained.

Observed-in-code evidence: channel.go:206 ("c.mu.Lock()"), channel.go:207 ("defer c.mu.Unlock()"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)"), channel.go:225 ("c.mu.Lock()"), channel.go:241 ("closeFun(wrapConn.conn)").

Disposition: handle or guarded outcome above → Q-10.

### P-05b — Release → Close

R detaches, then C with a non-nil checked-out value returns nil without invoking cleanup. R may still be draining unrelated idle entries.

Observed-in-code evidence: channel.go:208 ("if c.close == nil {"), channel.go:209 ("return nil"), channel.go:227 ("c.conns = nil"), channel.go:231 ("c.close = nil"), channel.go:241 ("closeFun(wrapConn.conn)").

Disposition: handle or guarded outcome above → Q-05.

### P-06a — Len → Release

Observer snapshots channel before R. Observer measures length after snapshot outside the lock. It can report pre-drain occupancy after detachment, or see a smaller number if draining ran.

Observed-in-code evidence: channel.go:96 ("c.mu.Lock()"), channel.go:97 ("conns := c.conns"), channel.go:98 ("c.mu.Unlock()"), channel.go:227 ("c.conns = nil"), channel.go:239 ("for wrapConn := range conns {"), channel.go:247 ("return len(c.getConns())").

Disposition: handle or guarded outcome above → Q-14.

### P-06b — Release → Len

R detaches before observer snapshots. Fresh Len returns zero even if drain callback is still active.

Observed-in-code evidence: channel.go:97 ("conns := c.conns"), channel.go:227 ("c.conns = nil"), channel.go:232 ("c.mu.Unlock()"), channel.go:241 ("closeFun(wrapConn.conn)"), channel.go:247 ("return len(c.getConns())").

Disposition: handle, zero; none — control trace.

### P-07a — Put → Close

Returner buffers a value, closer decrements and calls callback without removing its idle wrapper. Later Get can return that same already-closed resource.

Observed-in-code evidence: channel.go:110 ("case wrapConn := <-conns:"), channel.go:129 ("return wrapConn.conn, nil"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)").

Disposition: handle or guarded outcome above → Q-11.

### P-07b — Close → Put

Closer completes, then returner passes the same non-nil resource. Put accepts it for a waiter or storage. The optional buffer ping is a later health check; delivery bypasses it.

Observed-in-code evidence: channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:148 ("return ret.idleConn.conn, nil"), channel.go:179 ("if l := len(c.connReqs); l > 0 {"), channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:211 ("c.openingConns--").

Disposition: handle or guarded outcome above → Q-11.

### P-08a — PingResult → Release

Ping success permits return, with no final lifecycle recheck. Ping error calls Close, which invokes delegate if it takes the mutex before detachment, otherwise skips cleanup. Loop retries with its original channel.

Observed-in-code evidence: channel.go:110 ("case wrapConn := <-conns:"), channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:125 ("c.Close(wrapConn.conn)"), channel.go:126 ("continue"), channel.go:129 ("return wrapConn.conn, nil"), channel.go:206 ("c.mu.Lock()"), channel.go:208 ("if c.close == nil {"), channel.go:229 ("c.ping = nil").

Disposition: handle or guarded outcome above → Q-06.

### P-08b — Release → PingResult

An already-entered Ping runs across R outside mutex. Success hands out the candidate; error takes the no-op cleanup path, then closed-channel receive returns ErrClosed once empty. If detachment races with selecting/invoking the function field, unprotected read can race and nil invocation is possible.

Observed-in-code evidence: channel.go:110 ("case wrapConn := <-conns:"), channel.go:112 ("return nil, ErrClosed"), channel.go:123 ("if c.ping != nil {"), channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:125 ("c.Close(wrapConn.conn)"), channel.go:129 ("return wrapConn.conn, nil"), channel.go:220 ("return c.ping(conn)"), channel.go:229 ("c.ping = nil"), channel.go:238 ("close(conns)").

Disposition: handle or guarded outcome above → Q-06.

### P-09a — FactoryResult → Release

Dynamic Factory holds mutex across callback. On success count increments and Get unlocks, R may detach before the borrower observes the returned value. On returned error unlocks and returns error without increment. Created success is checked out and absent from drain storage; panic strands mutex.

Observed-in-code evidence: channel.go:131 ("c.mu.Lock()"), channel.go:154 ("conn, err := c.factory()"), channel.go:155 ("if err != nil {"), channel.go:156 ("c.mu.Unlock()"), channel.go:159 ("c.openingConns++"), channel.go:160 ("c.mu.Unlock()"), channel.go:161 ("return conn, nil"), channel.go:225 ("c.mu.Lock()"), channel.go:239 ("for wrapConn := range conns {").

Disposition: handle or guarded outcome above → Q-09.

### P-09b — Release → FactoryResult

If R detaches before dynamic Factory could be invoked, its nil guard prevents the call below capacity, or previously captured Get queues at capacity. Completion of already invoked dynamic Factory after detachment is prevented by same mutex. Constructor Factory is unpublished.

Observed-in-code evidence: channel.go:83 ("conn, err := c.factory()"), channel.go:131 ("c.mu.Lock()"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:150 ("if c.factory == nil {"), channel.go:154 ("conn, err := c.factory()"), channel.go:225 ("c.mu.Lock()"), channel.go:228 ("c.factory = nil").

Disposition: handle or guarded outcome above → Q-01.

### P-10a — CloseResult → Release

Ordinary Close result before R: lock serializes callback and detach. A returned error reaches direct caller, and the decrement has occurred. Deferred unlock also runs if callback panics.

Observed-in-code evidence: channel.go:206 ("c.mu.Lock()"), channel.go:207 ("defer c.mu.Unlock()"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)"), channel.go:225 ("c.mu.Lock()").

Disposition: handle or guarded outcome above → Q-10.

### P-10b — Release → CloseResult

R detaches first and uses captured Close on idle items after unlocking. Success continues, errors are discarded and continue, panic can abort the drain. Direct Close initiated after detach skips its callback.

Observed-in-code evidence: channel.go:208 ("if c.close == nil {"), channel.go:209 ("return nil"), channel.go:230 ("closeFun := c.close"), channel.go:231 ("c.close = nil"), channel.go:232 ("c.mu.Unlock()"), channel.go:239 ("for wrapConn := range conns {"), channel.go:241 ("closeFun(wrapConn.conn)").

Disposition: handle or guarded outcome above → Q-10.

### P-11a — Len → Put

Len snapshots idle channel; no queue, subsequent Put can increase idle occupancy or close on overflow. A Len whose snapshot already happened can sample on either side of Put.

Observed-in-code evidence: channel.go:97 ("conns := c.conns"), channel.go:98 ("c.mu.Unlock()"), channel.go:179 ("if l := len(c.connReqs); l > 0 {"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:196 ("return c.Close(conn)"), channel.go:247 ("return len(c.getConns())").

Disposition: handle or guarded outcome above → Q-14.

### P-11b — Put → Len

Put with no waiters and one free idle slot buffers. A later Len includes that entry. A Put serving a waiter changes no idle occupancy.

Observed-in-code evidence: channel.go:179 ("if l := len(c.connReqs); l > 0 {"), channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:247 ("return len(c.getConns())").

Disposition: handle or guarded outcome above → Q-14.

### P-12a — Len → Get

Len can see idle before a subsequent Get consumes one. Creation or enrollment after a failed receive leaves idle count unchanged.

Observed-in-code evidence: channel.go:110 ("case wrapConn := <-conns:"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:159 ("c.openingConns++"), channel.go:247 ("return len(c.getConns())").

Disposition: handle or guarded outcome above → Q-14.

### P-12b — Get → Len

With one ready idle candidate, G removes it before the observation and Len falls by one. Dynamic Get and waiter receive do not directly decrement idle occupancy.

Observed-in-code evidence: channel.go:110 ("case wrapConn := <-conns:"), channel.go:137 ("ret, ok := <-req"), channel.go:154 ("conn, err := c.factory()"), channel.go:247 ("return len(c.getConns())").

Disposition: handle or guarded outcome above → Q-14.

### P-13a — DirectPing → Release

Configured DirectPing is invoked outside lock, then R clears it. A callback that has entered may return either success or error after detachment. No additional disposal occurs in DirectPing.

Observed-in-code evidence: channel.go:217 ("if conn == nil {"), channel.go:220 ("return c.ping(conn)"), channel.go:225 ("c.mu.Lock()"), channel.go:229 ("c.ping = nil").

Disposition: handle or guarded outcome above → Q-13.

### P-13b — Release → DirectPing

After R clears Ping, direct invocation on a non-nil value panics. Nil payload rejects before the call.

Observed-in-code evidence: channel.go:217 ("if conn == nil {"), channel.go:218 ("return errors.New(\"connection is nil. rejecting\")"), channel.go:220 ("return c.ping(conn)"), channel.go:229 ("c.ping = nil").

Disposition: handle or guarded outcome above → Q-13.

### P-14a — Len → Close

Len samples idle independently. Close on a checked-out value decrements the accounting counter but leaves idle occupancy unchanged; even Close on a buffered value does not remove its wrapper.

Observed-in-code evidence: channel.go:206 ("c.mu.Lock()"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)"), channel.go:247 ("return len(c.getConns())").

Disposition: handle or guarded outcome above → Q-14.

### P-14b — Close → Len

Close then Len may report the same occupancy despite the accounting decrement. Len must acquire getConns lock after ordinary Close releases it.

Observed-in-code evidence: channel.go:96 ("c.mu.Lock()"), channel.go:207 ("defer c.mu.Unlock()"), channel.go:211 ("c.openingConns--"), channel.go:247 ("return len(c.getConns())").

Disposition: handle or guarded outcome above → Q-14.

### P-15a — DirectPing → Put

Direct Ping returns a callback outcome to caller. Later Put has no access to that verdict and accepts non-nil value for handoff or idle irrespective of verdict.

Observed-in-code evidence: channel.go:168 ("if conn == nil {"), channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:220 ("return c.ping(conn)").

Disposition: handle or guarded outcome above → Q-22.

### P-15b — Put → DirectPing

Put can return a resource then direct Ping check it independently. Another borrower may consume the resource before the health result. Callback has no pool ownership check.

Observed-in-code evidence: channel.go:110 ("case wrapConn := <-conns:"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:217 ("if conn == nil {"), channel.go:220 ("return c.ping(conn)").

Disposition: handle or guarded outcome above → Q-22.

### P-16a — DirectPing → Close

Direct Ping can remain in callback while Close delegates under its mutex, and both callbacks see the same value. No local arbitration or cancellation.

Observed-in-code evidence: channel.go:206 ("c.mu.Lock()"), channel.go:212 ("return c.close(conn)"), channel.go:220 ("return c.ping(conn)").

Disposition: handle or guarded outcome above → Q-22.

### P-16b — Close → DirectPing

Close then direct Ping still calls configured callback with the non-nil value. Any refusal comes from the callback.

Observed-in-code evidence: channel.go:203 ("if conn == nil {"), channel.go:212 ("return c.close(conn)"), channel.go:217 ("if conn == nil {"), channel.go:220 ("return c.ping(conn)").

Disposition: handle or guarded outcome above → Q-22.

### T-01 — Second Get while first pending

A logical requester starts two goroutines on the same saturated instance. At cap both append different channels. A single Put picks the earlier entry and completes only that request. After Close frees capacity, a later call can complete first.

Observed in code: channel.go:103 ("func (c *channelPool) Get() (interface{}, error) {"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:134 ("req := make(chan connReq, 1)"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:154 ("conn, err := c.factory()"), channel.go:179 ("if l := len(c.connReqs); l > 0 {"), channel.go:183 ("req <- connReq{"). Question: Q-16.

### T-02 — Second Get while first held

Same logical requester retains first value and calls Get again. If capacity remains, a separate idle or newly created value is returned. Once no idle remains at cap, this later call parks independently. No identity is passed to either acquisition.

Observed in code: channel.go:103 ("func (c *channelPool) Get() (interface{}, error) {"), channel.go:110 ("case wrapConn := <-conns:"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:159 ("c.openingConns++"). Question: Q-16.

### T-03 — Abandonment with and without return

Caller abandons its outer wait. With no later Put, Get remains in receive. With a Put, it exits with a value; an abandoned buffered forwarding channel can retain the result, an abandoned unbuffered send blocks outside the pool. Checkout has no automatic cleanup.

Observed in code: channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:137 ("ret, ok := <-req"), channel.go:148 ("return ret.idleConn.conn, nil"), channel.go:183 ("req <- connReq{"). Question: Q-04.

### T-04 — Queue tail after delivery

With one waiter, Put logically removes index zero by reslicing to zero length without zeroing the old slot, then delivers. With multiple waiters copy leaves a duplicate old tail, not necessarily the delivered request. Later append may overwrite a stale slot. Release does not clear either count or slice.

Observed in code: channel.go:179 ("if l := len(c.connReqs); l > 0 {"), channel.go:181 ("copy(c.connReqs, c.connReqs[1:])"), channel.go:182 ("c.connReqs = c.connReqs[:l-1]"), channel.go:183 ("req <- connReq{"), channel.go:227 ("c.conns = nil"), channel.go:231 ("c.close = nil"). Question: Q-18.

### T-05 — Duplicate return

After one checkout, Put same value twice with idle space. Two Gets can receive the same reference. Two explicit Close calls each delegate and decrement. No internal destructor provides deduplication.

Observed in code: channel.go:110 ("case wrapConn := <-conns:"), channel.go:129 ("return wrapConn.conn, nil"), channel.go:168 ("if conn == nil {"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)"). Question: Q-11.

### T-06 — Zero limits and typed nil

All-zero capacities with callbacks construct. Get on empty at zero parks. MaxIdle zero with positive active capacity normally closes a returned resource absent a waiter, although a ready receiver can rendezvous. Typed nil is not a nil interface and can reach an injected callback.

Observed in code: channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {"), channel.go:70 ("conns:        make(chan *idleConn, poolConfig.MaxIdle),"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:168 ("if conn == nil {"), channel.go:179 ("if l := len(c.connReqs); l > 0 {"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:212 ("return c.close(conn)"). Question: Q-12.

### T-07 — Factory outputs and panic

Failed constructor rolls back previous buffered successes, value accompanying error is lost. Failed dynamic Factory returns its error. Nil success can be stored/returned. Dynamic panic skips unlock; ordinary Close panic uses deferred unlock. Reentering from either locked callback blocks on getConns or other mutex methods.

Observed in code: channel.go:83 ("conn, err := c.factory()"), channel.go:85 ("c.Release()"), channel.go:88 ("c.conns <- &idleConn{conn: conn, t: time.Now()}"), channel.go:96 ("c.mu.Lock()"), channel.go:131 ("c.mu.Lock()"), channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err"), channel.go:159 ("c.openingConns++"), channel.go:160 ("c.mu.Unlock()"), channel.go:206 ("c.mu.Lock()"), channel.go:207 ("defer c.mu.Unlock()"), channel.go:212 ("return c.close(conn)"). Question: Q-09.

### T-08 — Partially failed drain and restart

Release detaches then callbacks may return error and continue, or panic and abort the loop. Repeating Release only sees nil channel. New constructs a separate instance; it neither wakes nor transfers waiters from the old one.

Observed in code: channel.go:69 ("c := &channelPool{"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:227 ("c.conns = nil"), channel.go:230 ("closeFun := c.close"), channel.go:234 ("if conns == nil {"), channel.go:239 ("for wrapConn := range conns {"), channel.go:241 ("closeFun(wrapConn.conn)"). Question: Q-15.

### T-09 — Health path differences

A freshly created or handed-off nonexpired value bypasses Ping. A buffered one calls Ping if configured. No Ping configured plus direct adapter call with non-nil payload panics. A buffered invalid candidate calls Close then loops.

Observed in code: channel.go:123 ("if c.ping != nil {"), channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:125 ("c.Close(wrapConn.conn)"), channel.go:126 ("continue"), channel.go:148 ("return ret.idleConn.conn, nil"), channel.go:161 ("return conn, nil"), channel.go:220 ("return c.ping(conn)"). Question: Q-07.

### T-10 — Late close while discarding

A detected expired resource is now outside idle channel. If Release clears delegate before Close acquires mutex, the resource is dropped with no closure. If Close acquires first its decrement happens and returned errors are ignored by the discard caller.

Observed in code: channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"), channel.go:118 ("c.Close(wrapConn.conn)"), channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {"), channel.go:144 ("c.Close(ret.idleConn.conn)"), channel.go:206 ("c.mu.Lock()"), channel.go:208 ("if c.close == nil {"), channel.go:211 ("c.openingConns--"), channel.go:231 ("c.close = nil"). Question: Q-05.

### T-11 — Full-wait underwriting

An open pool is at its active limit with no available idle connection → a borrower calls Get → the borrower can wait for a connection.

- README.md:15 ("- Support connection waiting, When the connection pool is full, support for connection waiting (like the go db connection pool)"). It omits the separate no-idle condition and exact admission boundary.
- cited text contemplates this ordering: no
- jev: supported, scope 0.21

Observed in code: channel.go:110 ("case wrapConn := <-conns:"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:137 ("ret, ok := <-req"). Question: Q-16.

### T-12 — Idle expiry without demand

An idle connection remains in the pool with no borrower → its idle time exceeds the configured maximum → the pool closes it immediately without another Get.

- README.md:13 ("- More configurable, The connection supports setting the maximum idle time, the timeout connection will be closed and discarded, which can avoid the problem of automatic connection failure when idle"). The trigger and immediacy are absent.
- cited text contemplates this ordering: no
- jev: unclear, scope 0.15

Observed in code: channel.go:115 ("if timeout := c.idleTimeout; timeout > 0 {"), channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"), channel.go:118 ("c.Close(wrapConn.conn)"). Question: Q-17.

### T-13 — Release all with checkout and waiter

A borrower holds a checked-out resource while another Get is waiting → owner calls Release → before Release returns, it closes the checked-out resource and settles the pending Get.

- README.md:55 ("//Release all connections in the connection pool, when resources need to be destroyed"). This does not specify ownership or pending calls.
- cited text contemplates this ordering: no
- jev: unclear, scope 0.01

Observed in code: channel.go:137 ("ret, ok := <-req"), channel.go:227 ("c.conns = nil"), channel.go:239 ("for wrapConn := range conns {"), channel.go:241 ("closeFun(wrapConn.conn)"). Question: Q-01.

### T-14 — Wrong receiver versus wrong payload

An ordinary receiver with a foreign compatible connection can accept it via Put or decrement via Close. Sending the same request to the wrong instance changes that instance; no global identity is supplied. Wrong Release closes the targeted pool.

Observed in code: channel.go:103 ("func (c *channelPool) Get() (interface{}, error) {"), channel.go:167 ("func (c *channelPool) Put(conn interface{}) error {"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:202 ("func (c *channelPool) Close(conn interface{}) error {"), channel.go:211 ("c.openingConns--"), channel.go:224 ("func (c *channelPool) Release() {"), channel.go:227 ("c.conns = nil"). Question: Q-11.

### T-15 — Expiration boundary and unsuccessful cleanup

With a positive configured duration, exact timestamp equality survives a sampled age check, as does early sampling. Strictly later discards and loops; returned cleanup failure is ignored and counter already decremented if Close delegated. A waiter handoff timestamps send, not request creation.

Observed in code: channel.go:115 ("if timeout := c.idleTimeout; timeout > 0 {"), channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"), channel.go:118 ("c.Close(wrapConn.conn)"), channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {"), channel.go:144 ("c.Close(ret.idleConn.conn)"), channel.go:184 ("idleConn: &idleConn{conn: conn, t: time.Now()},"), channel.go:211 ("c.openingConns--"). Question: Q-17.

### T-16 — Handoff already sent across release

Put sends and removes requester before Release. Get can consume buffered delivery after teardown and returns if within deadline. With an expired delivery it calls Close and loops with its old idle channel, which may now be closed.

Observed in code: channel.go:137 ("ret, ok := <-req"), channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {"), channel.go:144 ("c.Close(ret.idleConn.conn)"), channel.go:145 ("continue"), channel.go:148 ("return ret.idleConn.conn, nil"), channel.go:182 ("c.connReqs = c.connReqs[:l-1]"), channel.go:183 ("req <- connReq{"), channel.go:227 ("c.conns = nil"), channel.go:238 ("close(conns)"). Question: Q-06.

### M-01 — Three cycles on one backend

Inferred under NAT-06, N pools with empty idle and available local capacity receive one Get each during three externally driven failure/recovery cycles. Failure returns each error without increment and without a pool retry; another application wave can issue N calls in each cycle, 3N total. A successful round increments each local counter; no external reset clears a penalty because there is no penalty state. A held success can reduce later traffic through each local cap. channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err"), channel.go:159 ("c.openingConns++"). Q-20.

### M-02 — Retry timing and dispersion

Inferred. Same seeded application retry timing and N failed callbacks permit aligned subsequent Get waves. Pool does not sample a random delay, retry the Factory error or schedule backoff. Different caller schedules or callback latencies can spread them; no pool-provided bound. channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err"). Q-20.

### M-03 — Partial recovery

Inferred. Shared endpoint can admit one successful Factory in A while B still fails. B returns error and later caller demand can try again; A adds a held resource and can continue local admission up to its own cap. Without a shared budget, partial recovery can receive both waves; no spontaneous redial or recovery reset is modeled. channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err"), channel.go:159 ("c.openingConns++"). Q-20.
