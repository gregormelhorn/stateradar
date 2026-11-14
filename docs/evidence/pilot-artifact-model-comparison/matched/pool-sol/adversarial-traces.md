# Adversarial traces

Sequences are as-is observations from cited code, with observable assertions added where executed. Callback progress and actor schedules are assumptions unless witnessed by the probe.

### P-01a — Get then Put

Open initially empty at cap, with one held connection. A snapshots channel.go:104 ("conns := c.getConns()") and misses channel.go:130 ("default:"). B locks, sees no requests and buffers the return channel.go:179 ("if l := len(c.connReqs); l > 0 {"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"). A locks and does not reread idle readiness. At capacity A queues, leaving idle alongside a waiter; C can take it before A, then return it to A. Below capacity A runs Factory and can return a new item while the returned idle item stays stored. channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:154 ("conn, err := c.factory()"), channel.go:183 ("req <- connReq{"). Verdict: transition to mixed at capacity, handle below it. Q-04.

- Reachability: Open → Open_IdleAndWaiting — domain-analysis/channelPool/_probe/pool_probe_test.go:159 ("expected idle value alongside waiter")

### P-01b — Put then Get

At capacity B puts into empty idle storage with no waiter, then A calls Get and consumes it before admission. channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:110 ("case wrapConn := <-conns:"). With a prior waiter B directs its value to that waiter and later A may enqueue. channel.go:183 ("req <- connReq{"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"). Verdict: handle or defer. Q-04 on priority.

### P-02a — Get then Close

At cap A waits, then B closes the held connection. Close locks, decrements, and returns callback outcome without sending. Next caller can allocate ahead of A. Same when closer returns error; the count has already changed. channel.go:137 ("ret, ok := <-req"), channel.go:206 ("c.mu.Lock()"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)"), channel.go:154 ("conn, err := c.factory()"). Verdict: waiter remains pending. Q-03, Q-10.

### P-02b — Close then Get

B closes first. A sees new count if it reaches admission after unlock and creates below cap; a slow close delays admission. channel.go:207 ("defer c.mu.Unlock()"), channel.go:211 ("c.openingConns--"), channel.go:131 ("c.mu.Lock()"), channel.go:154 ("conn, err := c.factory()"). Verdict: handle. Q-10 for failed disposal freeing capacity.

### P-03a — Get then Release

A snapshots open channel and misses, then B detaches and closes it before A obtains the admission lock. At capacity it enqueues after detach; below capacity it returns ErrClosed. If A had already queued before B, it also remains pending. If A had instead received an idle value before B, inactive Ping can allow return, or Ping can overlap as T-04. If a closed channel is read before admission the nil wrapper rejects. channel.go:104 ("conns := c.getConns()"), channel.go:111 ("if wrapConn == nil {"), channel.go:131 ("c.mu.Lock()"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:150 ("if c.factory == nil {"), channel.go:227 ("c.conns = nil"), channel.go:238 ("close(conns)"). Verdict: defer or reject depending on interleaving; prior checkout can complete. Q-02, Q-08.

### P-03b — Release then Get

Owner completes detach then A begins a fresh Get. Snapshot reads nil, returning ErrClosed. channel.go:97 ("conns := c.conns"), channel.go:106 ("return nil, ErrClosed"). Verdict: reject. none — control trace based on code.

### P-04a — Put then Release

B Put locks and commits before owner detach: idle storage can be drained, or an already committed private handoff can be received afterward. At overflow B unlocks before Close and owner may disable the closer in that gap. channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:194 ("c.mu.Unlock()"), channel.go:196 ("return c.Close(conn)"), channel.go:227 ("c.conns = nil"), channel.go:241 ("closeFun(wrapConn.conn)"). Verdict: dispose buffered value, retain handoff, or skip overflow cleanup. Q-07, Q-08, Q-10.

### P-04b — Release then Put

Owner detaches first. B Put locks, sees nil, unlocks and calls Close; Close takes lock and returns nil without invoking cleanup. Nil input still rejects. channel.go:168 ("if conn == nil {"), channel.go:174 ("if c.conns == nil {"), channel.go:176 ("return c.Close(conn)"), channel.go:208 ("if c.close == nil {"), channel.go:209 ("return nil"). Verdict: accidental ignore for nonnil. Q-07.

### P-05a — Close then Release

B starts live Close and holds mutex through its callback including returned error. Release waits until unlock, then drains only idle. Callback success or failure commits decrement before detach. channel.go:206 ("c.mu.Lock()"), channel.go:207 ("defer c.mu.Unlock()"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)"), channel.go:225 ("c.mu.Lock()"), channel.go:241 ("closeFun(wrapConn.conn)"). Verdict: handle. Q-10, Q-11.

### P-05b — Release then Close

Owner detaches then B closes a checked-out value. Only the drain possesses captured closer. B sees nil and returns nil. channel.go:208 ("if c.close == nil {"), channel.go:209 ("return nil"), channel.go:230 ("closeFun := c.close"), channel.go:241 ("closeFun(wrapConn.conn)"). Verdict: accidental ignore. Q-07.

### P-06a — Len then Release

Observer snapshots before detach. Len may sample while the old buffer still contains entries or after drain removed them. channel.go:97 ("conns := c.conns"), channel.go:98 ("c.mu.Unlock()"), channel.go:238 ("close(conns)"), channel.go:239 ("for wrapConn := range conns {"), channel.go:247 ("return len(c.getConns())"). Verdict: handle snapshot. Q-15.

### P-06b — Release then Len

Owner detaches first then observer snapshots. Len reports zero even if old drain remains in progress. channel.go:227 ("c.conns = nil"), channel.go:241 ("closeFun(wrapConn.conn)"), channel.go:247 ("return len(c.getConns())"). Verdict: handle. none — control trace based on code.

### P-07a — Len then Get

Observer can sample depth before a buffered Get consumes one, or snapshot then pause until after consumption. channel.go:97 ("conns := c.conns"), channel.go:110 ("case wrapConn := <-conns:"), channel.go:247 ("return len(c.getConns())"). Verdict: handle. Q-15.

### P-07b — Get then Len

Successful buffered Get completes and observer takes length afterward. Idle count excludes the checked-out value. Later concurrent returns could intervene. channel.go:110 ("case wrapConn := <-conns:"), channel.go:247 ("return len(c.getConns())"). Verdict: handle. Q-15 on concurrent guarantees.

### P-08a — Len then Put

Observer samples before holder commits Put, or length read overlaps send after snapshot. channel.go:98 ("c.mu.Unlock()"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:247 ("return len(c.getConns())"). Verdict: handle. Q-15.

### P-08b — Put then Len

B buffers before observer reads, so depth includes the value unless another Get removed it. If B handed off instead, depth is unchanged. channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:247 ("return len(c.getConns())"). Verdict: handle. Q-15.

### P-09a — Len then Close

Observer samples idle depth and B closes a held value. Close does not remove idle elements and may hold liveness lock after the snapshot. channel.go:97 ("conns := c.conns"), channel.go:206 ("c.mu.Lock()"), channel.go:211 ("c.openingConns--"), channel.go:247 ("return len(c.getConns())"). Verdict: handle. Q-15.

### P-09b — Close then Len

Close finishes then observer samples; active count change is invisible to Len. If callback still runs before Len’s lock, Len waits. channel.go:96 ("c.mu.Lock()"), channel.go:206 ("c.mu.Lock()"), channel.go:211 ("c.openingConns--"), channel.go:247 ("return len(c.getConns())"). Verdict: handle. Q-11, Q-15.

### P-10a — Put then Close

B puts value into idle store, then independent actor closes same value. Close decrements but does not revoke idle wrapper. A later Get can retrieve the closed value absent effective Ping. channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:211 ("c.openingConns--"), channel.go:123 ("if c.ping != nil {"), channel.go:129 ("return wrapConn.conn, nil"). Verdict: handle, with ownership conflict. Q-12.

### P-10b — Close then Put

Independent actor closes value, then holder returns it. After Close releases mutex, Put has no ownership check and can buffer or transfer it. channel.go:207 ("defer c.mu.Unlock()"), channel.go:212 ("return c.close(conn)"), channel.go:168 ("if conn == nil {"), channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"). Verdict: handle. Q-12.

### T-01 — Second call while first pending

At cap hold one value, call Get in one goroutine until queued, call it again from a second goroutine owned by the same caller. Each appends an independent request. One return completes the first only and a second return can complete the second. No request increments active count. channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:180 ("req := c.connReqs[0]"), channel.go:183 ("req <- connReq{"). Q-06.

### T-02 — Second call while still holding

With one value held, caller can call Get sequentially. Below cap a second value can be created and counted. At cap the caller can block itself if only it can return the first, unless another goroutine returns it. A single handoff completes only that request. channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:137 ("ret, ok := <-req"), channel.go:159 ("c.openingConns++"), channel.go:183 ("req <- connReq{"). Q-06.

### T-03 — Abandon wrapper before result

Application stops waiting on its own reply. Without Put, private Get remains pending. With Put, its entry is removed and the resource flows to the abandoned wrapper. If wrapper uses buffered result storage it can receive a value nobody will return. With unbuffered result storage, wrapper's send can block. Pool receives no cancellation. channel.go:137 ("ret, ok := <-req"), channel.go:181 ("copy(c.connReqs, c.connReqs[1:])"), channel.go:182 ("c.connReqs = c.connReqs[:l-1]"), channel.go:183 ("req <- connReq{"), channel.go:148 ("return ret.idleConn.conn, nil"). Q-05.

### T-04 — Ping success and failure around Release

Before detach valid result is returned, invalid result closes then retries. After dequeue, delay inside callback; Release detaches. Success can return after cutoff. Failure calls suppressed Close, then retries receive until detached channel closes, may take another old buffered item, or may take the miss branch if detach preceded channel close. Between Ping availability check and dispatch, nil callback panics. The mutex protects Release writes only. channel.go:123 ("if c.ping != nil {"), channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:125 ("c.Close(wrapConn.conn)"), channel.go:129 ("return wrapConn.conn, nil"), channel.go:220 ("return c.ping(conn)"), channel.go:225 ("c.mu.Lock()"), channel.go:229 ("c.ping = nil"), channel.go:238 ("close(conns)"). Q-08.

### T-05 — Factory before and after detach

Live Get is paused inside Factory. Release cannot acquire its mutex. On success the counter commits before unlock and before detach, although caller can observe success later. Error does not increment and is returned even if Release detaches before caller observes it. A live Factory cannot start after detach on same receiver; a prior miss can instead enqueue if at cap. Startup Factory is before publication and failure drains initial successes. A new receiver may create independently after old release. channel.go:83 ("conn, err := c.factory()"), channel.go:85 ("c.Release()"), channel.go:131 ("c.mu.Lock()"), channel.go:150 ("if c.factory == nil {"), channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err"), channel.go:159 ("c.openingConns++"), channel.go:160 ("c.mu.Unlock()"), channel.go:225 ("c.mu.Lock()"). Q-13.

### T-06 — Closer phases and re-entry

Live Close succeeds or fails while holding the mutex. A recursive Len waits on same mutex and prevents callback return. Drain Close runs after detach outside lock and can safely read Len. Its error is ignored and panic exits drain. Concurrent repeat Release returns while the callback is paused. channel.go:96 ("c.mu.Lock()"), channel.go:206 ("c.mu.Lock()"), channel.go:207 ("defer c.mu.Unlock()"), channel.go:212 ("return c.close(conn)"), channel.go:230 ("closeFun := c.close"), channel.go:232 ("c.mu.Unlock()"), channel.go:234 ("if conns == nil {"), channel.go:241 ("closeFun(wrapConn.conn)"). Q-11.

### T-07 — Overflow cleanup gap

Fill idle channel, then Put an additional value. It selects default, unlocks, and pauses before Close. Release drains the old buffer and clears closer; deferred overflow Close returns nil without closing the extra value. channel.go:193 ("default:"), channel.go:194 ("c.mu.Unlock()"), channel.go:196 ("return c.Close(conn)"), channel.go:208 ("if c.close == nil {"), channel.go:231 ("c.close = nil"), channel.go:241 ("closeFun(wrapConn.conn)"). Q-07.

### T-08 — Constructor faults

Nil configuration panics. A configuration of zero for all limits passes and first Get queues with no source of a legitimate Put. Factory error on the second startup attempt drains first success. A value with error is excluded from rollback. channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {"), channel.go:70 ("conns:        make(chan *idleConn, poolConfig.MaxIdle),"), channel.go:83 ("conn, err := c.factory()"), channel.go:85 ("c.Release()"), channel.go:86 ("return nil, fmt.Errorf("factory is not able to fill the pool: %s", err)"), channel.go:88 ("c.conns <- &idleConn{conn: conn, t: time.Now()}"), channel.go:133 ("if c.openingConns >= c.maxActive {"). Q-13.

### T-09 — Invalid handoff

With Ping configured and one pending Get, return a broken but nonnil value before expiry. Handoff only checks age then returns it. An identical value buffered before Get would reach validation. channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {"), channel.go:148 ("return ret.idleConn.conn, nil"), channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"). Q-09.

### T-10 — Clock and retry

On positive configured idle timeout age equal to limit survives, while greater age attempts Close and retries; nonpositive disables. A waiter delayed after send can expire before taking the result. Bursts of newly supplied invalid or already expired values can keep the loop going. channel.go:108 ("for {"), channel.go:115 ("if timeout := c.idleTimeout; timeout > 0 {"), channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"), channel.go:118 ("c.Close(wrapConn.conn)"), channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {"), channel.go:144 ("c.Close(ret.idleConn.conn)"). Q-14.

### T-11 — Late return with fresh pool

After release, start replacement pool with same configuration. Sending old receiver’s value to old pool silently skips disposal; sending it to new receiver is accepted by payload check and may lead to callback mismatch. New does not reopen old receiver. channel.go:69 ("c := &channelPool{"), channel.go:168 ("if conn == nil {"), channel.go:174 ("if c.conns == nil {"), channel.go:183 ("req <- connReq{"), channel.go:208 ("if c.close == nil {"). Q-12.

### T-12 — Counter and backing slice

After two enqueues, Put shifts the second to the first active slot without clearing the copy at the old tail. Subsequent dequeue leaves the last channel outside the slice length. Counting does not track pending work, abandoned handoff outcomes, release drain, or failed live closure. Runtime allocator retention needs measurement. channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:181 ("copy(c.connReqs, c.connReqs[1:])"), channel.go:182 ("c.connReqs = c.connReqs[:l-1]"), channel.go:183 ("req <- connReq{"), channel.go:211 ("c.openingConns--"), channel.go:241 ("closeFun(wrapConn.conn)"). Q-16.

### T-13 — Drain steals or shares old channel

A Get has old channel snapshot, owner detaches and closes the channel. Both can receive buffered values afterward. If A receives one, it is excluded from drain; Ping can be nil or already started. Captured closer errors are ignored and panic can strand remaining work. channel.go:104 ("conns := c.getConns()"), channel.go:110 ("case wrapConn := <-conns:"), channel.go:123 ("if c.ping != nil {"), channel.go:226 ("conns := c.conns"), channel.go:238 ("close(conns)"), channel.go:239 ("for wrapConn := range conns {"), channel.go:241 ("closeFun(wrapConn.conn)"). Q-17.

### T-14 — Callback error and physical effect

Overflow/direct Close can report an error after decrement. Expiry and Ping cleanup ignore it while retrying. Release captures and invokes callback per idle item without retry or counter changes. Physical effect is callback specific. channel.go:118 ("c.Close(wrapConn.conn)"), channel.go:125 ("c.Close(wrapConn.conn)"), channel.go:196 ("return c.Close(conn)"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)"), channel.go:241 ("closeFun(wrapConn.conn)"). Q-10.

### T-15 — Shared-fate demand over three cycles

Suppose N instances share a server and each begins empty, below local cap. In each of three failure/recovery cycles one simultaneous Get per instance attempts N dials. During failures each call returns an error, and success increments only its local count. If external callers retry once per cycle, 3N total attempts across cycles. No pool signal resets a retry counter. channel.go:131 ("c.mu.Lock()"), channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err"), channel.go:159 ("c.openingConns++"). Q-18.

### T-16 — Backoff dispersion

N callers use identical external retry schedule while the server fails. Three aligned attempts per caller give N attempts per slot. Pool has neither random seed nor backoff. Dispersion requires caller or callback policy; no automatic convergence or divergence from the pool. channel.go:108 ("for {"), channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err"). Q-18.

### T-17 — Degraded recovery herd

A recovers first and creates successfully. B sees failure then retries through its caller. On renewed failure, A can discard invalid idle via Ping then immediately attempt Factory, while B retries from its caller. Coincident demand can produce up to one concurrent Factory per instance and as many repeated attempts as callers issue. channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:125 ("c.Close(wrapConn.conn)"), channel.go:126 ("continue"), channel.go:131 ("c.mu.Lock()"), channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err"). Q-18.

### T-18 — Requirement scopes

- O1. Open pool at capacity with no idle connection, no release, and a holder who will later put a connection → a requester calls Get before that Put → Get queues and stays pending until the holder Put hands its exact resource to that requester. README.md:15 ("When the connection pool is full, support for connection waiting"). cited text contemplates this ordering: no. jev: unclear, scope 0.01. Q-01 and Q-04.
- O2. Open pool with one idle value and no competing calls → owner invokes Release while the closer succeeds → that value is disposed synchronously before Release returns, and a subsequent Len reports zero. README.md:55 ("Release all connections in the connection pool, when resources need to be destroyed"). cited text contemplates this ordering: no. jev: unclear, scope 0.01. Q-17.
- O3. Pool already configured with Ping and a queued requester → a holder puts a physically invalid connection directly into the pending request slot → Get calls Ping and discards the connection before returning a usable value. README.md:14 ("invalid connection will be discarded"). cited text contemplates this ordering: no. jev: unclear, scope 0.01. Q-09.
