# Open domain questions

### Q-01

**Question:** At active capacity, must Get wait, time out, or fail immediately?

**Current behaviour:** observed-in-code unless otherwise labeled. README.md:15 describes waiting. The test expects a sentinel at channel_rpc_test.go:94 ("if err != ErrMaxActiveConnReached {"). A real Get waits at channel.go:137 ("ret, ok := <-req").

**Options:** wait until handoff  /  bounded wait  /  immediate refusal

**Status:** OPEN — human decision required

**Fault:** F-13

**Trigger:** step-2 test replay

### Q-02

**Question:** Who completes queued Get calls during or after Release?

**Current behaviour:** observed-in-code unless otherwise labeled. Release detaches idle storage and clears callbacks. channel.go:227 ("c.conns = nil"), channel.go:231 ("c.close = nil"). The queue is neither signaled nor emptied. channel.go:238 ("close(conns)"), channel.go:241 ("closeFun(wrapConn.conn)"). An in-flight miss can still append at capacity after detach, while below capacity it reaches the factory-nil check. channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:150 ("if c.factory == nil {"). The sentinel requires a closed request channel. channel.go:138 ("if !ok {"), channel.go:139 ("return nil, ErrMaxActiveConnReached").

**Options:** wake with ErrClosed  /  drain with a deadline  /  require an empty queue before Release

**Status:** OPEN — human decision required

**Fault:** F-07

**Trigger:** adversarial trace

### Q-03

**Question:** Should Close or a failed cleanup that frees active capacity advance older waiters?

**Current behaviour:** observed-in-code unless otherwise labeled. Close decrements without waking the FIFO. channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)"). A later Get may allocate first. channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:154 ("conn, err := c.factory()"), channel.go:159 ("c.openingConns++").

**Options:** wake oldest on capacity change  /  wait for Put only  /  reject disposal while waiters exist

**Status:** OPEN — human decision required

**Fault:** F-07

**Trigger:** adversarial trace

### Q-04

**Question:** What priority applies when Put makes idle work available after Get misses its first receive?

**Current behaviour:** observed-in-code unless otherwise labeled. The channel select precedes the mutex and the branch never rechecks readiness. channel.go:110 ("case wrapConn := <-conns:"), channel.go:130 ("default:"), channel.go:131 ("c.mu.Lock()"), channel.go:133 ("if c.openingConns >= c.maxActive {"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"). Below capacity it may create despite idle availability. At capacity it may enqueue next to ready work and a later Get can take it first.

**Options:** recheck and consume  /  allow creation below the limit, require recheck at limit  /  permit current ordering

**Status:** OPEN — human decision required

**Fault:** F-16

**Trigger:** adversarial trace

### Q-05

**Question:** Who owns a pending acquisition after an application caller abandons its wrapper?

**Current behaviour:** observed-in-code unless otherwise labeled. The Pool API has no context. pool.go:12 ("Get() (interface{}, error)"). The private wait entry persists until Put shifts it. channel.go:137 ("ret, ok := <-req"), channel.go:182 ("c.connReqs = c.connReqs[:l-1]"), channel.go:183 ("req <- connReq{"). Without a later Put the goroutine waits. With a later Put it can return into an abandoned wrapper or block sending on that wrapper's reply channel.

**Options:** add cancellation with handoff recovery  /  require caller to drain  /  use bounded wait

**Status:** OPEN — human decision required

**Fault:** F-09

**Trigger:** step-5 lint

### Q-06

**Question:** May the same caller hold two resources or queue two Gets?

**Current behaviour:** observed-in-code unless otherwise labeled. There is no caller identity. Separate calls each take idle, create below capacity, or append a private request. channel.go:103 ("func (c *channelPool) Get() (interface{}, error) {"), channel.go:110 ("case wrapConn := <-conns:"), channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:159 ("c.openingConns++"). One Put targets one queue head. channel.go:180 ("req := c.connReqs[0]"), channel.go:183 ("req <- connReq{").

**Options:** independent calls  /  enforce one outstanding acquisition with an owner token  /  explicit caller policy

**Status:** OPEN — human decision required

**Fault:** F-14

**Trigger:** step-3 checklist

### Q-07

**Question:** Who disposes a checked-out or overflow resource when Release detaches before cleanup?

**Current behaviour:** observed-in-code unless otherwise labeled. Late Put delegates to Close, which returns nil with no callback. channel.go:174 ("if c.conns == nil {"), channel.go:176 ("return c.Close(conn)"), channel.go:208 ("if c.close == nil {"), channel.go:209 ("return nil"). The full-buffer branch unlocks before calling Close. channel.go:194 ("c.mu.Unlock()"), channel.go:196 ("return c.Close(conn)"). Release's captured closer only drains the detached idle channel. channel.go:230 ("closeFun := c.close"), channel.go:241 ("closeFun(wrapConn.conn)").

**Options:** holder disposes  /  pool retains disposer for late returns  /  reject and report outstanding ownership

**Status:** OPEN — human decision required

**Fault:** F-07

**Trigger:** adversarial trace

### Q-08

**Question:** Can Ping race with Release, and may a dequeued connection return after the cutoff?

**Current behaviour:** observed-in-code unless otherwise labeled. The availability check and call read c.ping separately, without the mutex. channel.go:123 ("if c.ping != nil {"), channel.go:220 ("return c.ping(conn)"). Release writes nil under its own lock. channel.go:225 ("c.mu.Lock()"), channel.go:229 ("c.ping = nil"). The uninstrumented race probe reported this unsynchronized read/write. A separate ordered probe reproduced nil dispatch panic. A callback already running may succeed and return the resource, or fail and attempt cleanup after Close is disabled before retrying the detached channel. channel.go:125 ("c.Close(wrapConn.conn)"), channel.go:126 ("continue"), channel.go:129 ("return wrapConn.conn, nil"), channel.go:208 ("if c.close == nil {"), channel.go:238 ("close(conns)").

**Options:** synchronize callback snapshot and cutoff  /  allow in-flight success and define failure cleanup  /  wait for in-flight validation

**Status:** OPEN — human decision required

**Fault:** F-15

**Trigger:** step-8 verification

### Q-09

**Question:** Which delivery paths must Ping validate?

**Current behaviour:** observed-in-code unless otherwise labeled. README.md:14 promises invalid connection discard. Idle delivery checks Ping. channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"). Queued delivery returns without it, as does new creation. channel.go:148 ("return ret.idleConn.conn, nil"), channel.go:161 ("return conn, nil").

**Options:** all delivery paths  /  idle reuse including handoff  /  idle buffer only

**Status:** OPEN — human decision required

**Fault:** F-06

**Trigger:** doctrine mapping

### Q-10

**Question:** What should each caller observe when disposal fails, and when is capacity freed?

**Current behaviour:** observed-in-code unless otherwise labeled. Direct and overflow Close surface callback error, after the decrement. channel.go:196 ("return c.Close(conn)"), channel.go:211 ("c.openingConns--"), channel.go:212 ("return c.close(conn)"). Expiry and invalidation discard the error, then retry. channel.go:118 ("c.Close(wrapConn.conn)"), channel.go:125 ("c.Close(wrapConn.conn)"), channel.go:144 ("c.Close(ret.idleConn.conn)"). Release ignores close errors and accounting. channel.go:241 ("closeFun(wrapConn.conn)"). The callback contract does not guarantee disposal on an error. channel.go:27 ("//关闭连接的方法").

**Options:** decrement on confirmed disposal  /  track indeterminate disposition  /  document best effort and surface errors

**Status:** OPEN — human decision required

**Fault:** F-05

**Trigger:** seam-contract sweep

### Q-11

**Question:** Which callbacks may re-enter the pool, block, or panic?

**Current behaviour:** observed-in-code unless otherwise labeled. Live Factory and Close run under the non-reentrant lock. channel.go:131 ("c.mu.Lock()"), channel.go:154 ("conn, err := c.factory()"), channel.go:206 ("c.mu.Lock()"), channel.go:212 ("return c.close(conn)"). Factory manually unlocks and a recovered panic can strand the mutex. channel.go:156 ("c.mu.Unlock()"), channel.go:160 ("c.mu.Unlock()"). Live Close defers unlock. channel.go:207 ("defer c.mu.Unlock()"). Constructor Factory and Release drain are outside that lock. channel.go:83 ("conn, err := c.factory()"), channel.go:232 ("c.mu.Unlock()"), channel.go:241 ("closeFun(wrapConn.conn)"). Panics escape all callback paths.

**Options:** forbid and document re-entry and panic  /  move callback work outside lock with a reservation  /  define recovery and bounds

**Status:** OPEN — human decision required

**Fault:** F-11

**Trigger:** step-3 lock-discipline annotation

### Q-12

**Question:** What validity and ownership guarantees should opaque payloads and receivers carry?

**Current behaviour:** observed-in-code unless otherwise labeled. Put and Close reject nil interfaces only. channel.go:168 ("if conn == nil {"), channel.go:203 ("if conn == nil {"). A typed nil or foreign resource can be buffered or handed off. channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"). Duplicate Close decrements again and duplicate Put may create multiple references; a wrong receiver uses its own state. channel.go:174 ("if c.conns == nil {"), channel.go:211 ("c.openingConns--"). The README sample asserts net.Conn at README.md:25.

**Options:** track resource identity  /  document caller provenance and exactly-once return  /  validate supplied values

**Status:** OPEN — human decision required

**Fault:** F-18

**Trigger:** step-3 checklist

### Q-13

**Question:** How should constructor configuration and callback failures be reported and cleaned up?

**Current behaviour:** observed-in-code unless otherwise labeled. Nil Config dereferences at channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {"). Invalid ordering and absent mandatory callbacks reject. channel.go:60 ("return nil, errors.New("invalid capacity settings")"), channel.go:63 ("return nil, errors.New("invalid factory func settings")"), channel.go:66 ("return nil, errors.New("invalid close func settings")"). Zero caps and nonpositive idle timeout are accepted. channel.go:70 ("conns:        make(chan *idleConn, poolConfig.MaxIdle),"), channel.go:115 ("if timeout := c.idleTimeout; timeout > 0 {"). On initialization error prior idle successes drain and the error is formatted; a nonnil value plus error is discarded. channel.go:83 ("conn, err := c.factory()"), channel.go:85 ("c.Release()"), channel.go:86 ("return nil, fmt.Errorf("factory is not able to fill the pool: %s", err)"). Live Factory propagates the error and does not commit accounting. channel.go:155 ("if err != nil {"), channel.go:157 ("return nil, err"), channel.go:159 ("c.openingConns++"). Neither path validates nil or duplicate success. channel.go:88 ("c.conns <- &idleConn{conn: conn, t: time.Now()}"), channel.go:161 ("return conn, nil").

**Options:** validate nil and result shapes  /  define zero configurations  /  document callback ownership on error

**Status:** OPEN — human decision required

**Fault:** F-02

**Trigger:** step-1 extraction

### Q-14

**Question:** Is idle expiry lazy, and what timestamps and retry bounds should apply?

**Current behaviour:** observed-in-code unless otherwise labeled. Initial and returned values are timestamped. channel.go:88 ("c.conns <- &idleConn{conn: conn, t: time.Now()}"), channel.go:184 ("idleConn: &idleConn{conn: conn, t: time.Now()},"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"). Get checks strict Before only when positive timeout, including a delayed handoff. channel.go:115 ("if timeout := c.idleTimeout; timeout > 0 {"), channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"), channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {"). Equality survives and there is no timer or loop maximum in channel.go:108 ("for {").

**Options:** lazy expiry with documented bounds  /  background reap  /  treat handoff as already checked out

**Status:** OPEN — human decision required

**Fault:** F-13

**Trigger:** step-1 extraction

### Q-15

**Question:** What does Len guarantee during overlap and what does MaxCap count?

**Current behaviour:** observed-in-code unless otherwise labeled. Len samples current idle channel length after a lock-protected snapshot. channel.go:97 ("conns := c.conns"), channel.go:98 ("c.mu.Unlock()"), channel.go:247 ("return len(c.getConns())"). A dequeue, Put or detach can intervene. Accounting represents reported creates minus attempted live closes, independent of idle depth, and can disagree with physical liveness. channel.go:75 ("openingConns: poolConfig.InitialCap,"), channel.go:159 ("c.openingConns++"), channel.go:211 ("c.openingConns--").

**Options:** document snapshot and accounting  /  expose separate counts  /  require linearized observation

**Status:** OPEN — human decision required

**Fault:** F-03

**Trigger:** step-5 lint

### Q-16

**Question:** What bounds should apply to pending work and retained waiter references?

**Current behaviour:** observed-in-code unless otherwise labeled. Enqueue is an unbounded append and removal reslices after shifting without clearing the former last slot. channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:181 ("copy(c.connReqs, c.connReqs[1:])"), channel.go:182 ("c.connReqs = c.connReqs[:l-1]"). Shutdown keeps the slice. channel.go:225 ("c.mu.Lock()"), channel.go:232 ("c.mu.Unlock()"). Runtime retention size and lifetime are unmeasured.

**Options:** cap queue and clear tail  /  bound via caller contract  /  measure and publish limits

**Status:** OPEN — human decision required

**Fault:** F-13

**Trigger:** step-5 lint

### Q-17

**Question:** When should repeat Release complete, and what remains owned if draining blocks or panics?

**Current behaviour:** observed-in-code unless otherwise labeled. First Release captures callback and detaches under mutex. channel.go:226 ("conns := c.conns"), channel.go:230 ("closeFun := c.close"). A second Release takes the nil snapshot and returns while the first drain may still run; a drain panic aborts the remaining loop. channel.go:234 ("if conns == nil {"), channel.go:238 ("close(conns)"), channel.go:241 ("closeFun(wrapConn.conn)").

**Options:** join the active release  /  document detach-only repeat semantics  /  surface drain status

**Status:** OPEN — human decision required

**Fault:** F-07

**Trigger:** adversarial trace

### Q-18

**Question:** Who should bound aggregate factory load and recovery attempts?

**Current behaviour:** observed-in-code unless otherwise labeled. Each pool locks locally, calls Factory for its own demand and returns errors. channel.go:131 ("c.mu.Lock()"), channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err"). No shared retry/backoff is visible at that seam.

**Options:** delegate dispersion to callers  /  coordinate capacity externally  /  specify per-pool retry policy

**Status:** OPEN — human decision required

**Fault:** F-10

**Trigger:** multi-instance probes

### Q-19

**Question:** What lifecycle-owner and call-origin guarantees are required?

**Current behaviour:** observed-in-code unless otherwise labeled. Release accepts no owner token. pool.go:18 ("Release()"). Construction has no existing receiver. channel.go:58 ("func NewChannelPool(poolConfig *Config) (Pool, error) {"). Repeated construction creates separate storage. channel.go:70 ("conns:        make(chan *idleConn, poolConfig.MaxIdle),"). Application-intent checks are absent from Pool. pool.go:11 ("type Pool interface {").

**Options:** document owner duties  /  require ownership tokens at a wrapper  /  allow all callers

**Status:** OPEN — human decision required

**Fault:** F-17

**Trigger:** step-3 checklist

### Q-20

**Question:** What startup readiness guarantee should the RPC fixture establish?

**Current behaviour:** observed-in-code unless otherwise labeled. Fixture only pauses a fixed interval. channel_rpc_test.go:32 ("time.Sleep(time.Millisecond * 300) // wait until tcp server has been settled"). A listen error panics at channel_rpc_test.go:269 ("panic(e)"). This is a test-boundary assumption.

**Options:** record test precondition  /  require explicit fixture readiness

**Status:** OPEN — human decision required

**Fault:** F-21

**Trigger:** step-2 test replay

### Q-21

**Question:** What contract governs callback verdict, side effects, error, timeout and ownership?

**Current behaviour:** observed-in-code unless otherwise labeled. Factory, Close and Ping document purpose only. channel.go:25 ("//生成连接的方法"), channel.go:27 ("//关闭连接的方法"), channel.go:29 ("//检查连接是否有效的方法"). The API cannot tell whether disposal physically completed, Ping was accurate, or Factory allocated before returning error.

**Options:** specify failure and progress per callback  /  constrain concrete implementations  /  document opaque outcomes

**Status:** OPEN — human decision required

**Fault:** F-20

**Trigger:** seam-contract sweep

### Q-22

**Question:** How should a nil Ping invocation behave on the concrete receiver?

**Current behaviour:** observed-in-code unless otherwise labeled. Ping is outside the declared Pool interface (pool.go:11 ("type Pool interface {")). No callback is installed when omitted, and invoking Ping on a nonnil value calls the nil function. channel.go:78 ("if poolConfig.Ping != nil {"), channel.go:220 ("return c.ping(conn)"). A public interface caller cannot invoke it directly; an expanded interface can.

**Options:** make direct call defined  /  keep it outside supported use and document contract

**Status:** OPEN — human decision required

**Fault:** F-06

**Trigger:** step-8 verification
