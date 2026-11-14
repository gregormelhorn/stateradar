# Event catalogue

<!-- event-ids: New Get Put Close Release Len Factory PingResult CloseResult IdleCheck UV-NoOwner UV-OwnerLate UV-NewAgain UV-OwnerOverlap UV-Config UV-Abandon UV-GetAgain UV-AfterRelease UV-Overlap UV-Unsolicited UV-WrongPool UV-DuplicateResource UV-LateResource UV-ForeignResource UV-ReleaseAgain UV-Observer UV-FactoryError UV-FactoryDelay UV-FactoryValue UV-PingError UV-PingDelay UV-PingValue UV-CloseError UV-CloseDelay UV-CloseValue UV-Aged -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| New | external | Lifecycle owner | Creates configured pool and requests initial resources. channel.go:58 ("func NewChannelPool(poolConfig *Config) (Pool, error) {") |
| Get | external | Request caller | Requests a connection. channel.go:103 ("func (c *channelPool) Get() (interface{}, error) {") |
| Put | external | Resource holder | Returns opaque connection. channel.go:167 ("func (c *channelPool) Put(conn interface{}) error {") |
| Close | external | Resource holder | Requests disposal of a single opaque connection. channel.go:202 ("func (c *channelPool) Close(conn interface{}) error {") |
| Release | external | Lifecycle owner | Requests pool shutdown. channel.go:224 ("func (c *channelPool) Release() {") |
| Len | external | Observer | Reads available count. channel.go:246 ("func (c *channelPool) Len() int {") |
| Factory | internal | Factory callback | Synchronous creation completion supplies a connection and error. channel.go:83 ("conn, err := c.factory()"), channel.go:154 ("conn, err := c.factory()") |
| PingResult | internal | Ping callback | Synchronous connectivity check outcome. channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {") |
| CloseResult | internal | Close callback | Synchronous disposal outcome. channel.go:212 ("return c.close(conn)"), channel.go:241 ("closeFun(wrapConn.conn)") |
| IdleCheck | internal | Clock | Sample connection age during acquisition. channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"), channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {") |
| UV-NoOwner | external | Lifecycle owner | Construction or teardown omitted. channel.go:58 ("func NewChannelPool(poolConfig *Config) (Pool, error) {") |
| UV-OwnerLate | external | Lifecycle owner | Construction or teardown delayed while caller work continues. channel.go:224 ("func (c *channelPool) Release() {") |
| UV-NewAgain | external | Lifecycle owner | Repeated or unsolicited construction with same configuration. channel.go:69 ("c := &channelPool{") |
| UV-OwnerOverlap | external | Lifecycle owner | Teardown overlaps construction of another pool or is issued while old work runs. channel.go:225 ("c.mu.Lock()") |
| UV-Config | external | Lifecycle owner | Nil config, invalid bounds, zero capacity, zero idle capacity, absent callbacks, nonpositive timeout or valid unintended limits. channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {") |
| UV-Abandon | external | Caller or holder | Get result abandoned by caller, or Put/Close omitted or delayed after checkout. channel.go:137 ("ret, ok := <-req") |
| UV-GetAgain | external | Request caller | Second Get while first awaits a resource, or after first returned a resource the same caller still holds. channel.go:133 ("if c.openingConns >= c.maxActive {") |
| UV-AfterRelease | external | Request caller | Fresh Get on an already released pool. channel.go:105 ("if conns == nil {") |
| UV-Overlap | external | Caller, holder and owner | Overlapping Get, Put, Close or Release on a shared pool. channel.go:131 ("c.mu.Lock()") |
| UV-Unsolicited | external | Request caller | Unsolicited Get without an application-level reason. channel.go:103 ("func (c *channelPool) Get() (interface{}, error) {") |
| UV-WrongPool | external | Public caller | Valid public call on an unintended receiver, separately from a wrong resource payload. channel.go:104 ("conns := c.getConns()") |
| UV-DuplicateResource | external | Resource holder | Duplicate Put or Close, or both for one resource. channel.go:168 ("if conn == nil {") |
| UV-LateResource | external | Resource holder | Put or Close after release or before other ownership work completes. channel.go:174 ("if c.conns == nil {") |
| UV-ForeignResource | external | Resource holder | No matching checkout, foreign connection, typed nil or stale payload presented to intended pool. channel.go:203 ("if conn == nil {") |
| UV-ReleaseAgain | external | Lifecycle owner | Second Release after detach or during draining. channel.go:234 ("if conns == nil {") |
| UV-Observer | external | Observer | Late, repeated, unsolicited or overlapping observation. channel.go:247 ("return len(c.getConns())") |
| UV-FactoryError | external | Factory callback | Creation returns error, including a value together with error. channel.go:155 ("if err != nil {") |
| UV-FactoryDelay | external | Factory callback | Slow, blocked, panicking or reentrant creation. channel.go:154 ("conn, err := c.factory()") |
| UV-FactoryValue | external | Factory callback | Nil, typed nil, reused or foreign connection with successful creation. channel.go:161 ("return conn, nil") |
| UV-PingError | external | Ping callback | Connectivity check returns an error. channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {") |
| UV-PingDelay | external | Ping callback | Slow, blocked, panicking or reentrant validation, overlapping release. channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {") |
| UV-PingValue | external | Ping callback | Healthy resource reported invalid or invalid resource reported healthy. channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {") |
| UV-CloseError | external | Close callback | Disposal returns error in direct, overflow, expiry, invalid cleanup or release drain paths. channel.go:212 ("return c.close(conn)") |
| UV-CloseDelay | external | Close callback | Slow, blocked, panicking or reentrant disposal in live or drain phase. channel.go:241 ("closeFun(wrapConn.conn)") |
| UV-CloseValue | external | Close callback | Disposal reports success with resource still live or error after disposing it. channel.go:212 ("return c.close(conn)") |
| UV-Aged | internal | Clock | Idle age below, equal to or beyond timeout, including handoff delivery delayed by scheduling. channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {") |

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| New: Lifecycle owner | UV-NoOwner | UV-OwnerLate | UV-NewAgain | UV-OwnerLate | UV-OwnerOverlap | UV-NewAgain | UV-Config |
| Get: Request caller | UV-Abandon | UV-Abandon | UV-GetAgain | UV-AfterRelease | UV-Overlap | UV-Unsolicited | UV-WrongPool |
| Put: Resource holder | UV-Abandon | UV-Abandon | UV-DuplicateResource | UV-LateResource | UV-Overlap | UV-ForeignResource | UV-ForeignResource, UV-WrongPool |
| Close: Resource holder | UV-Abandon | UV-Abandon | UV-DuplicateResource | UV-LateResource | UV-Overlap | UV-ForeignResource | UV-ForeignResource, UV-WrongPool |
| Release: Lifecycle owner | UV-NoOwner | UV-OwnerLate | UV-ReleaseAgain | UV-OwnerLate | UV-OwnerOverlap, UV-Overlap | UV-OwnerOverlap | UV-WrongPool |
| Len: Observer | n/a: synchronous invocation or observation only, channel.go:247 ("return len(c.getConns())"). | UV-Observer | UV-Observer | UV-Observer | UV-Observer | UV-Observer | UV-WrongPool |
| Factory: Factory callback | UV-FactoryError | UV-FactoryDelay | n/a: synchronous invocation or observation only, channel.go:154 ("conn, err := c.factory()"). | n/a: synchronous invocation or observation only, channel.go:154 ("conn, err := c.factory()"). | UV-FactoryDelay | n/a: synchronous invocation or observation only, channel.go:154 ("conn, err := c.factory()"). | UV-FactoryValue |
| PingResult: Ping callback | UV-PingError | UV-PingDelay | n/a: synchronous invocation or observation only, channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"). | UV-PingDelay | UV-PingDelay | n/a: synchronous invocation or observation only, channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"). | UV-PingValue |
| CloseResult: Close callback | UV-CloseError | UV-CloseDelay | n/a: synchronous invocation or observation only, channel.go:212 ("return c.close(conn)"). | UV-CloseDelay | UV-CloseDelay | n/a: synchronous invocation or observation only, channel.go:212 ("return c.close(conn)"). | UV-CloseValue |
| IdleCheck: Clock | n/a: synchronous invocation or observation only, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"). | UV-Aged | n/a: synchronous invocation or observation only, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"). | UV-Aged | n/a: synchronous invocation or observation only, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"). | n/a: synchronous invocation or observation only, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"). | UV-Aged |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Get → Put | Requester and holder on one pool |
| P-01b | Put → Get | Requester and holder on one pool |
| P-02a | Get → Close | Requester and holder on one pool |
| P-02b | Close → Get | Requester and holder on one pool |
| P-03a | Get → Release | Requester and owner on one pool |
| P-03b | Release → Get | Requester and owner on one pool |
| P-04a | Put → Release | Holder and owner on one pool |
| P-04b | Release → Put | Holder and owner on one pool |
| P-05a | Close → Release | Holder and owner on one pool |
| P-05b | Release → Close | Holder and owner on one pool |
| P-06a | Len → Release | Observer and owner on one pool |
| P-06b | Release → Len | Observer and owner on one pool |
| P-07a | Len → Get | Observer and requester on one pool |
| P-07b | Get → Len | Observer and requester on one pool |
| P-08a | Len → Put | Observer and holder on one pool |
| P-08b | Put → Len | Observer and holder on one pool |
| P-09a | Len → Close | Observer and holder on one pool |
| P-09b | Close → Len | Observer and holder on one pool |
| P-10a | Put → Close | Independently acting holders or cleanup agents for one resource |
| P-10b | Close → Put | Independently acting holders or cleanup agents for one resource |

## Remembrance semantics

Observed in code. Outstanding resource identity and owner are not stored. The idle channel holds up to MaxIdle opaque wrappers, each timed on construction, return or handoff. channel.go:70 ("conns:        make(chan *idleConn, poolConfig.MaxIdle),"), channel.go:88 ("c.conns <- &idleConn{conn: conn, t: time.Now()}"), channel.go:184 ("idleConn: &idleConn{conn: conn, t: time.Now()},"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"). The FIFO slice is unbounded and removes logically via shift and reslice without clearing the tail, preserving a reference to the last copied or removed channel until overwrite or collection. channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:181 ("copy(c.connReqs, c.connReqs[1:])"), channel.go:182 ("c.connReqs = c.connReqs[:l-1]"). Each requester channel has room for one reply. channel.go:134 ("req := make(chan connReq, 1)"). Release detaches and drains the idle buffer, leaves the waiter slice and counter alone, and keeps a local closer while draining. channel.go:226 ("conns := c.conns"), channel.go:230 ("closeFun := c.close"), channel.go:238 ("close(conns)"), channel.go:241 ("closeFun(wrapConn.conn)"). The counter starts at InitialCap, increments on reported creation success, decrements before live disposal outcome, and has no change on return, handoff, failed creation or release. channel.go:75 ("openingConns: poolConfig.InitialCap,"), channel.go:159 ("c.openingConns++"), channel.go:187 ("return nil"), channel.go:211 ("c.openingConns--"), channel.go:231 ("c.close = nil"). Late references resolve through the receiver's current availability and callback fields. channel.go:174 ("if c.conns == nil {"), channel.go:208 ("if c.close == nil {"). Runtime retention cost is unmeasured.

## Lock-discipline annotation

Observed in code. Channel snapshots copy the field under the mutex. channel.go:96 ("c.mu.Lock()"), channel.go:98 ("c.mu.Unlock()"). Get admission, Debugf and post-start Factory execute under the lock. channel.go:131 ("c.mu.Lock()"), channel.go:132 ("log.Debugf("openConn %v %v", c.openingConns, c.maxActive)"), channel.go:154 ("conn, err := c.factory()"), channel.go:160 ("c.mu.Unlock()"). Constructor Factory runs outside the lock before publication. channel.go:83 ("conn, err := c.factory()"), channel.go:91 ("return c, nil"). Put selects delivery or buffering under lock, then releases it before overflow disposal. channel.go:172 ("c.mu.Lock()"), channel.go:183 ("req <- connReq{"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"), channel.go:194 ("c.mu.Unlock()"). Live Close invokes Close under lock. channel.go:206 ("c.mu.Lock()"), channel.go:212 ("return c.close(conn)"). Ping reads and calls the callback outside the lock. channel.go:123 ("if c.ping != nil {"), channel.go:220 ("return c.ping(conn)"). Release detaches under lock and drains with captured callback outside. channel.go:225 ("c.mu.Lock()"), channel.go:232 ("c.mu.Unlock()"), channel.go:241 ("closeFun(wrapConn.conn)"). No reentrancy restrictions in the callback descriptions at channel.go:25 ("//生成连接的方法"), channel.go:27 ("//关闭连接的方法"), or channel.go:29 ("//检查连接是否有效的方法").

## Event annotations

### New
- gate: Configuration content
- upstream_guards: README.md:30 gives example values. Validation is local.
- coverage:
  - loss: UV-NoOwner
  - delay: UV-OwnerLate
  - duplication: UV-NewAgain
  - out-of-order: UV-OwnerLate
  - contradiction: UV-OwnerOverlap
  - commission: UV-NewAgain
  - value: UV-Config

### Get
- gate: Idle readiness, pool availability, active count and validation
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").
- coverage:
  - loss: UV-Abandon
  - delay: UV-Abandon
  - duplication: UV-GetAgain
  - out-of-order: UV-AfterRelease
  - contradiction: UV-Overlap
  - commission: UV-Unsolicited
  - value: UV-WrongPool

### Put
- gate: Nil interface, availability, waiting requests and send readiness
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").
- coverage:
  - loss: UV-Abandon
  - delay: UV-Abandon
  - duplication: UV-DuplicateResource
  - out-of-order: UV-LateResource
  - contradiction: UV-Overlap
  - commission: UV-ForeignResource
  - value: UV-ForeignResource, UV-WrongPool

### Close
- gate: Nil interface and configured close method
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").
- coverage:
  - loss: UV-Abandon
  - delay: UV-Abandon
  - duplication: UV-DuplicateResource
  - out-of-order: UV-LateResource
  - contradiction: UV-Overlap
  - commission: UV-ForeignResource
  - value: UV-ForeignResource, UV-WrongPool

### Release
- gate: Pool availability
- upstream_guards: README.md:55 describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go:18 ("Release()").
- coverage:
  - loss: UV-NoOwner
  - delay: UV-OwnerLate
  - duplication: UV-ReleaseAgain
  - out-of-order: UV-OwnerLate
  - contradiction: UV-OwnerOverlap, UV-Overlap
  - commission: UV-OwnerOverlap
  - value: UV-WrongPool

### Len
- gate: Pool availability and idle depth
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").
- coverage:
  - loss: n/a: synchronous invocation or observation only, channel.go:247 ("return len(c.getConns())").
  - delay: UV-Observer
  - duplication: UV-Observer
  - out-of-order: UV-Observer
  - contradiction: UV-Observer
  - commission: UV-Observer
  - value: UV-WrongPool

### Factory
- gate: Error and construction versus acquisition phase
- upstream_guards: Injected callback contract describes purpose only. No independent callback registration or result ingress.
- coverage:
  - loss: UV-FactoryError
  - delay: UV-FactoryDelay
  - duplication: n/a: synchronous invocation or observation only, channel.go:154 ("conn, err := c.factory()").
  - out-of-order: n/a: synchronous invocation or observation only, channel.go:154 ("conn, err := c.factory()").
  - contradiction: UV-FactoryDelay
  - commission: n/a: synchronous invocation or observation only, channel.go:154 ("conn, err := c.factory()").
  - value: UV-FactoryValue

### PingResult
- gate: Error and callback availability
- upstream_guards: Injected callback contract describes purpose only. No independent callback registration or result ingress.
- coverage:
  - loss: UV-PingError
  - delay: UV-PingDelay
  - duplication: n/a: synchronous invocation or observation only, channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {").
  - out-of-order: UV-PingDelay
  - contradiction: UV-PingDelay
  - commission: n/a: synchronous invocation or observation only, channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {").
  - value: UV-PingValue

### CloseResult
- gate: Error and cleanup phase
- upstream_guards: Injected callback contract describes purpose only. No independent callback registration or result ingress.
- coverage:
  - loss: UV-CloseError
  - delay: UV-CloseDelay
  - duplication: n/a: synchronous invocation or observation only, channel.go:212 ("return c.close(conn)").
  - out-of-order: UV-CloseDelay
  - contradiction: UV-CloseDelay
  - commission: n/a: synchronous invocation or observation only, channel.go:212 ("return c.close(conn)").
  - value: UV-CloseValue

### IdleCheck
- gate: Configured timeout and sampled age
- upstream_guards: No caller-supplied time. channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {")
- coverage:
  - loss: n/a: synchronous invocation or observation only, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {").
  - delay: UV-Aged
  - duplication: n/a: synchronous invocation or observation only, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {").
  - out-of-order: UV-Aged
  - contradiction: n/a: synchronous invocation or observation only, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {").
  - commission: n/a: synchronous invocation or observation only, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {").
  - value: UV-Aged

### UV-NoOwner
- gate: Absent lifecycle call
- upstream_guards: README.md:55 describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go:18 ("Release()").

### UV-OwnerLate
- gate: Lifecycle order
- upstream_guards: README.md:55 describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go:18 ("Release()").

### UV-NewAgain
- gate: Configuration and independent instance
- upstream_guards: README.md:55 describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go:18 ("Release()").

### UV-OwnerOverlap
- gate: Receiver and availability
- upstream_guards: README.md:55 describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go:18 ("Release()").

### UV-Config
- gate: Configuration content
- upstream_guards: README.md:55 describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go:18 ("Release()").

### UV-Abandon
- gate: No cancellation parameter and no deadline for queue
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").

### UV-GetAgain
- gate: Admission and idle readiness, no caller identity
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").

### UV-AfterRelease
- gate: Pool availability
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").

### UV-Overlap
- gate: Idle readiness, count, pending queue and cutoff
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").

### UV-Unsolicited
- gate: Same admission gates as Get
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").

### UV-WrongPool
- gate: Receiver and local state
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").

### UV-DuplicateResource
- gate: Presence of value and local counts
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").

### UV-LateResource
- gate: Availability at commit
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").

### UV-ForeignResource
- gate: Interface nil and callback-specific type requirements
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").

### UV-ReleaseAgain
- gate: Availability
- upstream_guards: README.md:55 describes caller-initiated destruction. No enforced lifecycle-owner check at pool.go:18 ("Release()").

### UV-Observer
- gate: Channel snapshot and length
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").

### UV-FactoryError
- gate: Callback error
- upstream_guards: Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-FactoryDelay
- gate: Callback progress and phase
- upstream_guards: Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-FactoryValue
- gate: Callback result
- upstream_guards: Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-PingError
- gate: Callback error
- upstream_guards: Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-PingDelay
- gate: Callback progress and teardown
- upstream_guards: Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-PingValue
- gate: Callback verdict
- upstream_guards: Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-CloseError
- gate: Phase and callback error
- upstream_guards: Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-CloseDelay
- gate: Phase and callback progress
- upstream_guards: Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-CloseValue
- gate: Callback side effect
- upstream_guards: Injected callback contract describes purpose only. No independent callback registration or result ingress.

### UV-Aged
- gate: Age and timeout
- upstream_guards: Public Pool calls carry no actor, ownership token, or context. pool.go:11 ("type Pool interface {").
