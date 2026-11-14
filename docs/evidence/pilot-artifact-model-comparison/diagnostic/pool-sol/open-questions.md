# Open domain questions

### Q-01 — How should Release settle pending and concurrently admitted Get calls?

**Question:** How should Release settle pending and concurrently admitted Get calls?

**Current behaviour:** Observed in code. Open waiters survive detachment. A Get paused after failed receive also queues after detachment at capacity. Below capacity it returns ErrClosed. A return after detachment cannot wake either waiter.

**Evidence:** channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:137 ("ret, ok := <-req"), channel.go:150 ("if c.factory == nil {"), channel.go:174 ("if c.conns == nil {"), channel.go:227 ("c.conns = nil").

**Options:** wake with ErrClosed | finish admitted requests | keep blocking

**Status:** OPEN — human decision required

**Fault:** F-20

**Trigger:** adversarial trace

### Q-02 — Should Get recheck idle storage before choosing admission?

**Question:** Should Get recheck idle storage before choosing admission?

**Current behaviour:** Observed in code. Put between failed receive and lock can leave an idle connection beside a waiter at capacity. Below capacity Get creates a new resource despite an idle one. A newer Get can take the idle connection first.

**Evidence:** channel.go:110 ("case wrapConn := <-conns:"), channel.go:130 ("default:"), channel.go:131 ("c.mu.Lock()"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:154 ("conn, err := c.factory()"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:").

**Options:** recheck | allow new creation and bypass | serialize admission

**Status:** OPEN — human decision required

**Fault:** F-04

**Trigger:** adversarial trace

### Q-03 — Should Close free capacity for existing waiters before new callers?

**Question:** Should Close free capacity for existing waiters before new callers?

**Current behaviour:** Observed in code. Close decrements before callback success is known and never wakes waiters. A newer Get can open first. A subsequent Put then feeds the older waiter.

**Evidence:** channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:154 ("conn, err := c.factory()"), channel.go:179 ("if l := len(c.connReqs); l > 0 {"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)").

**Options:** wake oldest | preserve current admission | reject while cleanup unconfirmed

**Status:** OPEN — human decision required

**Fault:** F-20

**Trigger:** adversarial trace

### Q-04 — How should an abandoned acquisition be cancelled and its handoff reclaimed?

**Question:** How should an abandoned acquisition be cancelled and its handoff reclaimed?

**Current behaviour:** Observed in code. The pool has no cancellation handshake. With no Put, the goroutine stays blocked. A subsequent Put delivers to it. An outer abandoned buffered result can retain the value, or an unbuffered result send can block its worker.

**Evidence:** channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:137 ("ret, ok := <-req"), channel.go:183 ("req <- connReq{").

**Options:** cancellable API | caller must reclaim | bounded wait

**Status:** OPEN — human decision required

**Fault:** F-09

**Trigger:** adversarial trace

### Q-05 — Who owns checked-out resources after Release, including late Put/Close?

**Question:** Who owns checked-out resources after Release, including late Put/Close?

**Current behaviour:** Observed in code. Release drains the detached idle buffer. Late Put delegates to Close, whose nil callback branch returns success without cleanup. Late Close does the same. Overflow or expiry cleanup can take this branch if detachment intervenes.

**Evidence:** channel.go:174 ("if c.conns == nil {"), channel.go:176 ("return c.Close(conn)"), channel.go:194 ("c.mu.Unlock()"), channel.go:196 ("return c.Close(conn)"), channel.go:208 ("if c.close == nil {"), channel.go:209 ("return nil"), channel.go:227 ("c.conns = nil"), channel.go:231 ("c.close = nil"), channel.go:241 ("closeFun(wrapConn.conn)").

**Options:** caller owns | delegate late cleanup | report refusal

**Status:** OPEN — human decision required

**Fault:** F-07

**Trigger:** step-5 lint

### Q-06 — What should an in-flight Get or Ping do if its result crosses Release?

**Question:** What should an in-flight Get or Ping do if its result crosses Release?

**Current behaviour:** Observed in code. Get can consume detached buffered storage or return a candidate after a successful in-flight Ping. A failed in-flight Ping may skip cleanup and rescan the captured channel. Reads of the Ping field are unsynchronized against its clearing.

**Evidence:** channel.go:110 ("case wrapConn := <-conns:"), channel.go:123 ("if c.ping != nil {"), channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:125 ("c.Close(wrapConn.conn)"), channel.go:129 ("return wrapConn.conn, nil"), channel.go:220 ("return c.ping(conn)"), channel.go:229 ("c.ping = nil"), channel.go:238 ("close(conns)").

**Options:** complete checked-out work | reject and close | synchronize health and teardown

**Status:** OPEN — human decision required

**Fault:** F-15

**Trigger:** adversarial trace

### Q-07 — Which acquisition paths require Ping and replacement after rejection?

**Question:** Which acquisition paths require Ping and replacement after rejection?

**Current behaviour:** Observed in code. Only buffer consumption checks Ping. Factory results and private waiter deliveries bypass it. An expired delivery loops. Ping error on a buffered value closes and loops.

**Evidence:** channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:126 ("continue"), channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {"), channel.go:148 ("return ret.idleConn.conn, nil"), channel.go:161 ("return conn, nil").

**Options:** all paths | idle buffer only | define when resources are revalidated

**Status:** OPEN — human decision required

**Fault:** F-19

**Trigger:** doctrine mapping

### Q-08 — May callbacks re-enter the pool or block indefinitely?

**Question:** May callbacks re-enter the pool or block indefinitely?

**Current behaviour:** Observed in code. Dynamic Factory and ordinary Close run under the mutex. Mutex-taking methods reentered from them block. Constructor and detached drain callbacks run outside this lock. Ping can re-enter lock-taking methods, subject to callback recursion and teardown.

**Evidence:** channel.go:83 ("conn, err := c.factory()"), channel.go:96 ("c.mu.Lock()"), channel.go:131 ("c.mu.Lock()"), channel.go:154 ("conn, err := c.factory()"), channel.go:206 ("c.mu.Lock()"), channel.go:207 ("defer c.mu.Unlock()"), channel.go:220 ("return c.ping(conn)"), channel.go:232 ("c.mu.Unlock()"), channel.go:241 ("closeFun(wrapConn.conn)").

**Options:** forbid and document | invoke unlocked | bounded callback contract

**Status:** OPEN — human decision required

**Fault:** F-11

**Trigger:** step-3 lock-discipline annotation

### Q-09 — What does Factory guarantee on error, nil success, wrong type or panic?

**Question:** What does Factory guarantee on error, nil success, wrong type or panic?

**Current behaviour:** Observed in code. Constructor rolls back buffered resources on error. Dynamic Get returns error without increment. Both accept nil success. A value with error is discarded without cleanup; a panic escapes, and dynamic Factory leaves the mutex locked.

**Evidence:** channel.go:83 ("conn, err := c.factory()"), channel.go:85 ("c.Release()"), channel.go:86 ("return nil, fmt.Errorf(\"factory is not able to fill the pool: %s\", err)"), channel.go:88 ("c.conns <- &idleConn{conn: conn, t: time.Now()}"), channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err"), channel.go:159 ("c.openingConns++"), channel.go:160 ("c.mu.Unlock()"), channel.go:161 ("return conn, nil").

**Options:** require valid value on success | pool validates | callback owns partial failures

**Status:** OPEN — human decision required

**Fault:** F-03

**Trigger:** seam-contract sweep

### Q-10 — When is capacity accounting updated and which Close failures should callers see?

**Question:** When is capacity accounting updated and which Close failures should callers see?

**Current behaviour:** Observed in code. Delegated Close decrements before the callback even if it fails or panics. Get drops returned cleanup errors. Overflow returns them. Release drops returned errors and continues, while panic aborts the remaining drain.

**Evidence:** channel.go:118 ("c.Close(wrapConn.conn)"), channel.go:125 ("c.Close(wrapConn.conn)"), channel.go:144 ("c.Close(ret.idleConn.conn)"), channel.go:196 ("return c.Close(conn)"), channel.go:207 ("defer c.mu.Unlock()"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)"), channel.go:239 ("for wrapConn := range conns {"), channel.go:241 ("closeFun(wrapConn.conn)").

**Options:** decrement on attempt | decrement after success | track failed cleanup

**Status:** OPEN — human decision required

**Fault:** F-05

**Trigger:** seam-contract sweep

### Q-11 — What ownership and exactly-once obligations apply to Put and Close?

**Question:** What ownership and exactly-once obligations apply to Put and Close?

**Current behaviour:** Observed in code. Only a nil interface is rejected. Duplicate and foreign non-nil values can be stored, handed out repeatedly or cause repeated close and negative accounting. Typed nil reaches injected code. Close can target a value still present in idle storage.

**Evidence:** channel.go:168 ("if conn == nil {"), channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:203 ("if conn == nil {"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)").

**Options:** validate ownership | require caller discipline | reject stale returns

**Status:** OPEN — human decision required

**Fault:** F-08

**Trigger:** step-3 checklist

### Q-12 — Which configurations are valid, including nil, zero and negative durations?

**Question:** Which configurations are valid, including nil, zero and negative durations?

**Current behaviour:** Observed in code. Nil Config dereference panics. Zero MaxCap admits no creation and queues from empty. MaxIdle zero uses an unbuffered channel. Non-positive IdleTimeout disables both age checks. Missing Ping is supported for normal Get.

**Evidence:** channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {"), channel.go:70 ("conns:        make(chan *idleConn, poolConfig.MaxIdle),"), channel.go:78 ("if poolConfig.Ping != nil {"), channel.go:115 ("if timeout := c.idleTimeout; timeout > 0 {"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:141 ("if timeout := c.idleTimeout; timeout > 0 {"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:").

**Options:** preserve with documented semantics | reject selected values

**Status:** OPEN — human decision required

**Fault:** F-18

**Trigger:** step-3 checklist

### Q-13 — What is the direct Ping adapter contract?

**Question:** What is the direct Ping adapter contract?

**Current behaviour:** Observed in code. Pool omits Ping, but the concrete method is available through structural assertion. It rejects nil values, otherwise calls the callback even when absent or cleared. The error is returned to the caller directly.

**Evidence:** channel.go:78 ("if poolConfig.Ping != nil {"), channel.go:216 ("func (c *channelPool) Ping(conn interface{}) error {"), channel.go:218 ("return errors.New(\"connection is nil. rejecting\")"), channel.go:220 ("return c.ping(conn)"), channel.go:229 ("c.ping = nil").

**Options:** unsupported error | define optional method | keep outside public interface

**Status:** OPEN — human decision required

**Fault:** F-03

**Trigger:** step-4 matrix walk

### Q-14 — What does Len count and what consistency should concurrent callers expect?

**Question:** What does Len count and what consistency should concurrent callers expect?

**Current behaviour:** Observed in code. Len takes a protected channel-pointer snapshot, then reads occupancy outside the lock. It measures idle entries only, including entries in a snapshot taken before detachment. Fresh calls after detachment return zero.

**Evidence:** channel.go:94 ("// getConns 获取所有连接"), channel.go:97 ("conns := c.conns"), channel.go:98 ("c.mu.Unlock()"), channel.go:227 ("c.conns = nil"), channel.go:247 ("return len(c.getConns())").

**Options:** idle snapshot | live accounting | expose both

**Status:** OPEN — human decision required

**Fault:** F-03

**Trigger:** step-1 extraction

### Q-15 — What does a repeated Release promise while the original drain is running?

**Question:** What does a repeated Release promise while the original drain is running?

**Current behaviour:** Observed in code. Only the first call captures the channel. A repeated Release returns before the first drain completes, and no callback is retried after an earlier drain panic.

**Evidence:** channel.go:226 ("conns := c.conns"), channel.go:227 ("c.conns = nil"), channel.go:232 ("c.mu.Unlock()"), channel.go:234 ("if conns == nil {"), channel.go:235 ("return"), channel.go:241 ("closeFun(wrapConn.conn)").

**Options:** idempotent detach | join first drain | report drain outcome

**Status:** OPEN — human decision required

**Fault:** F-08

**Trigger:** adversarial trace

### Q-16 — What limit, fairness and error apply to waiting and repeated acquisition?

**Question:** What limit, fairness and error apply to waiting and repeated acquisition?

**Current behaviour:** Observed in code. No wait timeout or context is used. Same-caller acquisitions are independent. Saturated Gets append separate entries. ErrMaxActiveConnReached requires closure of a request channel, but the component never closes one. Upstream test expects the error.

**Evidence:** channel.go:46 ("idleTimeout, waitTimeOut time.Duration"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:134 ("req := make(chan connReq, 1)"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:137 ("ret, ok := <-req"), channel.go:139 ("return nil, ErrMaxActiveConnReached"), channel.go:183 ("req <- connReq{"), channel.go:238 ("close(conns)"). Observed in tests, channel_rpc_test.go:94 ("if err != ErrMaxActiveConnReached {").

**Options:** wait with limit | fail immediately | define retry and FIFO guarantees

**Status:** OPEN — human decision required

**Fault:** F-13

**Trigger:** step-5 lint

### Q-17 — When should expiration be checked and when should replacement occur?

**Question:** When should expiration be checked and when should replacement occur?

**Current behaviour:** Observed in code. Age starts at construction, buffer return or direct handoff. The code samples on receive and uses strict Before, with no timer or proactive refill. It retries acquisition after a discarded candidate without explicit retry limit.

**Evidence:** channel.go:88 ("c.conns <- &idleConn{conn: conn, t: time.Now()}"), channel.go:115 ("if timeout := c.idleTimeout; timeout > 0 {"), channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"), channel.go:119 ("continue"), channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {"), channel.go:145 ("continue"), channel.go:184 ("idleConn: &idleConn{conn: conn, t: time.Now()},"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:").

**Options:** lazy expiry | proactive expiry | define deadline and refill

**Status:** OPEN — human decision required

**Fault:** F-13

**Trigger:** doctrine mapping

### Q-18 — Should dequeued request slots and request storage survive completion or Release?

**Question:** Should dequeued request slots and request storage survive completion or Release?

**Current behaviour:** Observed in code. The slice shifts entries and reslices without clearing the former tail. At length one the removed request remains in the old backing slot. Release leaves both queue and counter unchanged. Memory impact remains workload-dependent.

**Evidence:** channel.go:181 ("copy(c.connReqs, c.connReqs[1:])"), channel.go:182 ("c.connReqs = c.connReqs[:l-1]"), channel.go:227 ("c.conns = nil"), channel.go:231 ("c.close = nil"), channel.go:238 ("close(conns)").

**Options:** clear removed slots | retain intentionally | measure retention

**Status:** OPEN — human decision required

**Fault:** F-05

**Trigger:** step-3 checklist

### Q-19 — What should happen when acquisition, return or teardown is omitted?

**Question:** What should happen when acquisition, return or teardown is omitted?

**Current behaviour:** Observed in code. Omitted Get creates no work, omitted Put or Close leaves a checkout untracked, and there is no automatic teardown. Caller can target another instance without detection.

**Evidence:** channel.go:103 ("func (c *channelPool) Get() (interface{}, error) {"), channel.go:129 ("return wrapConn.conn, nil"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:167 ("func (c *channelPool) Put(conn interface{}) error {"), channel.go:202 ("func (c *channelPool) Close(conn interface{}) error {"), channel.go:224 ("func (c *channelPool) Release() {").

**Options:** document caller lifecycle | explicit ownership API | detect wrong receiver

**Status:** OPEN — human decision required

**Fault:** F-12

**Trigger:** step-3 checklist

### Q-20 — Should pools coordinate traffic to a shared degraded backend?

**Question:** Should pools coordinate traffic to a shared degraded backend?

**Current behaviour:** Observed in code. Each instance gates only its own Factory. There is no inter-instance limit, retry clock, reset-on-recovery signal or backoff. Subsequent caller demand can synchronize batches.

**Evidence:** channel.go:69 ("c := &channelPool{"), channel.go:131 ("c.mu.Lock()"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err").

**Options:** caller coordinates | per-pool backoff | shared admission limit

**Status:** OPEN — human decision required

**Fault:** F-10

**Trigger:** multi-instance probes

### Q-21 — Which callback and standard-library failure guarantees does the pool rely on?

**Question:** Which callback and standard-library failure guarantees does the pool rely on?

**Current behaviour:** Observed in code. Callback comments specify only roles. Go function calls return synchronously unless they fail to return. No callback contract promises effects on error, deadline, type, panic or reentry. Debug logging is inside the admission lock and shares any downstream hook latency.

**Evidence:** channel.go:25 ("//生成连接的方法"), channel.go:27 ("//关闭连接的方法"), channel.go:29 ("//检查连接是否有效的方法"), channel.go:132 ("log.Debugf(\"openConn %v %v\", c.openingConns, c.maxActive)"), channel.go:154 ("conn, err := c.factory()"), channel.go:212 ("return c.close(conn)"), channel.go:220 ("return c.ping(conn)"), channel.go:241 ("closeFun(wrapConn.conn)").

**Options:** document callback and logging guarantees | surface failures | bound latency

**Status:** OPEN — human decision required

**Fault:** F-03

**Trigger:** seam-contract sweep

### Q-22 — Which guards should apply when Close, direct Ping and Put overlap for one resource?

**Question:** Which guards should apply when Close, direct Ping and Put overlap for one resource?

**Current behaviour:** Observed in code. Ping and Close can run concurrently on the same value, and neither checks pool membership. Put accepts a previously closed value.

**Evidence:** channel.go:167 ("func (c *channelPool) Put(conn interface{}) error {"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:202 ("func (c *channelPool) Close(conn interface{}) error {"), channel.go:212 ("return c.close(conn)"), channel.go:216 ("func (c *channelPool) Ping(conn interface{}) error {"), channel.go:220 ("return c.ping(conn)").

**Options:** enforce ownership | specify valid call order | delegate to adapter

**Status:** OPEN — human decision required

**Fault:** F-15

**Trigger:** part-B diff
