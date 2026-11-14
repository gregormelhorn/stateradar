# Event catalogue

<!-- event-ids: New Get Put Close Release Len DirectPing FactoryResult CloseResult PingResult IdleAge WaitDelivery DrainDone UV-NewOmitted UV-NewRepeated UV-BadConfig UV-GetOmitted UV-GetAgain UV-AbandonGet UV-LateGet UV-ContendedGet UV-WrongPoolGet UV-ReturnMissing UV-LatePut UV-LateClose UV-BadOwnership UV-WrongPoolPut UV-ReleaseOmitted UV-ReleaseAgain UV-WrongPoolRelease UV-LateRead UV-FactoryFault UV-CloseFault UV-PingFault UV-CallbackDelay -->

| id | classification | source | description, payload and evidence |
|---|---|---|---|
| New | external | configuration caller | Create a pool from capacities, time limit and callbacks. Constructor entry observed in code, channel.go:58 ("func NewChannelPool(poolConfig *Config) (Pool, error) {"). |
| Get | external | borrower | Request a resource and receive a value or error. Pool API entry observed in code, channel.go:103 ("func (c *channelPool) Get() (interface{}, error) {"). |
| Put | external | resource returner | Offer a resource after use. Pool API entry observed in code, channel.go:167 ("func (c *channelPool) Put(conn interface{}) error {"). |
| Close | external | resource closer | Request closure of a supplied resource. Pool API entry observed in code, channel.go:202 ("func (c *channelPool) Close(conn interface{}) error {"). |
| Release | external | lifecycle owner | Request teardown. Pool API entry observed in code, channel.go:224 ("func (c *channelPool) Release() {"). |
| Len | external | observer | Query current count. Pool API entry observed in code, channel.go:246 ("func (c *channelPool) Len() int {"). |
| DirectPing | external | concrete-method adapter | Optional health callback can be requested via a structural interface assertion on the concrete value. It is absent from Pool's declared methods, pool.go:20 ("Len() int"). Method observed in code, channel.go:216 ("func (c *channelPool) Ping(conn interface{}) error {"). |
| FactoryResult | external | injected Factory | Synchronous value or error for a construction or acquisition. Invocation observed in code, channel.go:83 ("conn, err := c.factory()"), channel.go:154 ("conn, err := c.factory()"). |
| CloseResult | external | injected Close | Synchronous completion or error from resource cleanup. Invocation observed in code, channel.go:212 ("return c.close(conn)"), channel.go:241 ("closeFun(wrapConn.conn)"). |
| PingResult | external | injected Ping | Synchronous health result while checking a resource. Invocation observed in code, channel.go:220 ("return c.ping(conn)"). |
| IdleAge | internal | clock sample in Get | Evaluate the age of an acquired candidate using IdleTimeout, a duration. MaxIdle is the maximum count of idle entries. Trigger observed in code, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"), channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {"). |
| WaitDelivery | internal | pool return path | Value sent to a registered acquisition. Producer and consumer observed in code, channel.go:183 ("req <- connReq{"), channel.go:137 ("ret, ok := <-req"). |
| DrainDone | internal | pool teardown path | Finish processing detached idle storage. Completion boundary observed in code, channel.go:239 ("for wrapConn := range conns {"). |
| UV-NewOmitted | external | configuration caller | Construction omitted or deferred. Boundary observed in code, channel.go:58 ("func NewChannelPool(poolConfig *Config) (Pool, error) {"). |
| UV-NewRepeated | external | configuration caller | Duplicate or overlapping construction against the same backend, including an unintended extra pool. Boundary observed in code, channel.go:69 ("c := &channelPool{"). |
| UV-BadConfig | external | configuration caller | Nil configuration, invalid capacities, absent callbacks, zero capacity or unintended idle time including negative. Boundary observed in code, channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {"). |
| UV-GetOmitted | external | borrower | Omitted acquisition or unsolicited acquisition with no application demand. Boundary observed in code, channel.go:103 ("func (c *channelPool) Get() (interface{}, error) {"). |
| UV-GetAgain | external | borrower | Second acquisition by the same caller while the first is pending or while its first resource is held. Boundary observed in code, channel.go:135 ("c.connReqs = append(c.connReqs, req)"). |
| UV-AbandonGet | external | borrower | Caller stops waiting externally, with no later matching return or with a later matching return. Boundary observed in code, channel.go:137 ("ret, ok := <-req"). |
| UV-LateGet | external | borrower and lifecycle owner | Get overlaps or follows Release, including a prior observation of empty or ready storage. Boundary observed in code, channel.go:104 ("conns := c.getConns()"). |
| UV-ContendedGet | external | borrower and resource returner | Put or Close changes availability between Get's failed receive and admission decision. Boundary observed in code, channel.go:131 ("c.mu.Lock()"). |
| UV-WrongPoolGet | external | borrower | Get sent to the wrong pool instance. Boundary observed in code, channel.go:104 ("conns := c.getConns()"). |
| UV-ReturnMissing | external | resource holder | Omit Put or Close after acquisition, leaving resource use and pending requests to be resolved. Boundary observed in code, channel.go:129 ("return wrapConn.conn, nil"). |
| UV-LatePut | external | resource returner | Put overlaps teardown or returns a resource after shutdown or requester departure. Boundary observed in code, channel.go:174 ("if c.conns == nil {"). |
| UV-LateClose | external | resource closer | Close after Release, or after Put selected overflow cleanup. Boundary observed in code, channel.go:208 ("if c.close == nil {"). |
| UV-BadOwnership | external | resource returner or closer | Duplicate Put or Close, nil including typed nil, stale or wrong payload, or contradictory Put and Close for one resource. Boundary observed in code, channel.go:168 ("if conn == nil {"). |
| UV-WrongPoolPut | external | resource returner or closer | Put or Close sent to the wrong pool instance. Boundary observed in code, channel.go:172 ("c.mu.Lock()"). |
| UV-ReleaseOmitted | external | lifecycle owner | Omit or delay Release. Boundary observed in code, channel.go:224 ("func (c *channelPool) Release() {"). |
| UV-ReleaseAgain | external | lifecycle owner | Repeat Release before drain completes or after it returns, including unsolicited teardown. Boundary observed in code, channel.go:234 ("if conns == nil {"). |
| UV-WrongPoolRelease | external | lifecycle owner | Release the wrong instance. Boundary observed in code, channel.go:227 ("c.conns = nil"). |
| UV-LateRead | external | observer | Repeated, stale or wrong-receiver Len during concurrent changes or teardown. Boundary observed in code, channel.go:247 ("return len(c.getConns())"). |
| UV-FactoryFault | external | injected Factory | Factory error, panic, nil success, or value accompanying an error or of unexpected type. Boundary observed in code, channel.go:154 ("conn, err := c.factory()"). |
| UV-CloseFault | external | injected Close | Close error or panic including during expiry, overflow and drain, or success without cleanup. Boundary observed in code, channel.go:212 ("return c.close(conn)"). |
| UV-PingFault | external | injected Ping or concrete-method adapter | Absent callback, delayed or invalid health result, panic, or overlapping call and Release. Boundary observed in code, channel.go:220 ("return c.ping(conn)"). |
| UV-CallbackDelay | external | injected Factory, Close or Ping | Callback stalls or re-enters Get, Put, Close, Release or Len while the original call is in progress. Boundary observed in code, channel.go:207 ("defer c.mu.Unlock()"). |

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| New: configuration caller | UV-NewOmitted | UV-CallbackDelay | UV-NewRepeated | UV-NewRepeated | UV-BadConfig | UV-NewRepeated | UV-BadConfig |
| Get: borrower | UV-GetOmitted | UV-AbandonGet | UV-GetAgain | UV-LateGet | UV-ContendedGet | UV-GetOmitted | UV-WrongPoolGet |
| Put: resource returner | UV-ReturnMissing | UV-LatePut | UV-BadOwnership | UV-LatePut | UV-BadOwnership | UV-BadOwnership | UV-WrongPoolPut, UV-BadOwnership |
| Close: resource closer | UV-ReturnMissing | UV-LateClose | UV-BadOwnership | UV-LateClose | UV-BadOwnership | UV-BadOwnership | UV-WrongPoolPut, UV-BadOwnership |
| Release: lifecycle owner | UV-ReleaseOmitted | UV-ReleaseOmitted | UV-ReleaseAgain | UV-ReleaseAgain | UV-LateGet | UV-ReleaseAgain | UV-WrongPoolRelease |
| Len: observer | n/a: omitting a read has no state effect, channel.go:247 ("return len(c.getConns())"). | UV-LateRead | UV-LateRead | UV-LateRead | UV-LateRead | n/a: an unsolicited read has no state effect, channel.go:247 ("return len(c.getConns())"). | UV-LateRead |
| DirectPing: concrete-method adapter | UV-PingFault | UV-CallbackDelay | UV-PingFault | UV-PingFault | UV-PingFault | UV-PingFault | UV-PingFault |
| FactoryResult: injected Factory | UV-FactoryFault | UV-CallbackDelay | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:154 ("conn, err := c.factory()"). | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:154 ("conn, err := c.factory()"). | UV-FactoryFault | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:154 ("conn, err := c.factory()"). | UV-FactoryFault |
| CloseResult: injected Close | UV-CloseFault | UV-CallbackDelay | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:212 ("return c.close(conn)"). | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:212 ("return c.close(conn)"). | UV-CloseFault | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:212 ("return c.close(conn)"). | UV-CloseFault |
| PingResult: injected Ping | UV-PingFault | UV-CallbackDelay | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:220 ("return c.ping(conn)"). | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:220 ("return c.ping(conn)"). | UV-PingFault | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:220 ("return c.ping(conn)"). | UV-PingFault |
| IdleAge: clock sample in Get | n/a: local time sampling has no delivery channel, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"). | UV-AbandonGet | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"). | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"). | n/a: one observation per branch, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"). | n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"). | UV-BadConfig |
| WaitDelivery: pool return path | UV-ReturnMissing | UV-AbandonGet | n/a: serialized dequeue before send to a private request channel, channel.go:182 ("c.connReqs = c.connReqs[:l-1]"). | UV-LatePut | UV-ContendedGet | n/a: delivery requires registered work, channel.go:179 ("if l := len(c.connReqs); l > 0 {"). | UV-BadOwnership |
| DrainDone: pool teardown path | UV-CloseFault | UV-CallbackDelay | n/a: there is one drain per captured channel, channel.go:234 ("if conns == nil {"). | n/a: the range executes after detachment in the same call, channel.go:239 ("for wrapConn := range conns {"). | UV-LateGet | n/a: requires prior detachment, channel.go:234 ("if conns == nil {"). | n/a: payloadless method or completion signal, channel.go:239 ("for wrapConn := range conns {"). |

## Interaction pairs

| id | ordering | shared entity |
|---|---|---|
| P-01a | Get → Put | same pool, borrower and returning holder |
| P-01b | Put → Get | same pool, borrower and returning holder |
| P-02a | Get → Close | same pool, borrower and resource closer |
| P-02b | Close → Get | same pool, borrower and resource closer |
| P-03a | Get → Release | same pool, borrower and lifecycle owner |
| P-03b | Release → Get | same pool, borrower and lifecycle owner |
| P-04a | Put → Release | same pool and resource, returning holder and lifecycle owner |
| P-04b | Release → Put | same pool and resource, returning holder and lifecycle owner |
| P-05a | Close → Release | same pool and resource, closer and lifecycle owner |
| P-05b | Release → Close | same pool and resource, closer and lifecycle owner |
| P-06a | Len → Release | same pool, observer and lifecycle owner |
| P-06b | Release → Len | same pool, observer and lifecycle owner |
| P-07a | Put → Close | same resource, distinct returner and closer |
| P-07b | Close → Put | same resource, distinct returner and closer |
| P-08a | PingResult → Release | same pool, health callback completion and lifecycle owner |
| P-08b | Release → PingResult | same pool, health callback completion and lifecycle owner |
| P-09a | FactoryResult → Release | same published pool, creation callback completion and lifecycle owner |
| P-09b | Release → FactoryResult | same published pool, creation callback completion and lifecycle owner |
| P-10a | CloseResult → Release | same pool, cleanup callback completion and lifecycle owner |
| P-10b | Release → CloseResult | same pool, cleanup callback completion and lifecycle owner |
| P-11a | Len → Put | same pool, observer and returner |
| P-11b | Put → Len | same pool, observer and returner |
| P-12a | Len → Get | same pool, observer and borrower |
| P-12b | Get → Len | same pool, observer and borrower |
| P-13a | DirectPing → Release | same pool, optional direct health caller and lifecycle owner |
| P-13b | Release → DirectPing | same pool, optional direct health caller and lifecycle owner |
| P-14a | Len → Close | same pool, observer and closer |
| P-14b | Close → Len | same pool, observer and closer |
| P-15a | DirectPing → Put | same resource, health caller and returner |
| P-15b | Put → DirectPing | same resource, health caller and returner |
| P-16a | DirectPing → Close | same resource, health caller and closer |
| P-16b | Close → DirectPing | same resource, health caller and closer |

## Remembrance semantics

Observed in code. Idle channel and pending request queue are distinct, channel.go:42 ("conns                    chan *idleConn"), channel.go:49 ("connReqs                 []chan connReq"). A checked-out resource has no identity record. Put slides the queue and reslices without clearing the former last slot, channel.go:181 ("copy(c.connReqs, c.connReqs[1:])"), channel.go:182 ("c.connReqs = c.connReqs[:l-1]"). Release detaches idle storage and leaves pending request storage and accounting untouched, channel.go:227 ("c.conns = nil"), channel.go:238 ("close(conns)"). Counter begins at InitialCap, increments on successful dynamic creation and decrements before delegated Close, channel.go:75 ("openingConns: poolConfig.InitialCap,"), channel.go:159 ("c.openingConns++"), channel.go:211 ("c.openingConns--"). Storage-retention cost depends on runtime reachability and workload.

## Lock-discipline annotation

Observed in code. Published Factory runs under the mutex, channel.go:131 ("c.mu.Lock()"), channel.go:154 ("conn, err := c.factory()"). Direct Close calls its callback under the mutex, channel.go:206 ("c.mu.Lock()"), channel.go:212 ("return c.close(conn)"). Put sends to a private buffered request while holding the mutex, channel.go:134 ("req := make(chan connReq, 1)"), channel.go:183 ("req <- connReq{"). getConns only snapshots under the mutex, channel.go:96 ("c.mu.Lock()"). Constructor Factory, health checking and detached Release draining invoke callbacks outside the published pool lock, channel.go:83 ("conn, err := c.factory()"), channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:232 ("c.mu.Unlock()"), channel.go:241 ("closeFun(wrapConn.conn)"). The callback descriptions state roles only, channel.go:25 ("//生成连接的方法"), channel.go:27 ("//关闭连接的方法"), channel.go:29 ("//检查连接是否有效的方法").

## Catalogue notes

The four primary actor roles are configuration caller, borrower or resource holder, lifecycle owner and configured callback provider. Runtime time samples and private handoffs are internal.

## Event annotations

### New
- gate: payload content
- upstream_guards: Constructor validates the capacity relation and callback presence locally, channel.go:59 ("poolConfig.InitialCap <= poolConfig.MaxIdle"). No upstream config validation is shown.
- coverage:
  - loss: UV-NewOmitted
  - delay: UV-CallbackDelay
  - duplication: UV-NewRepeated
  - out-of-order: UV-NewRepeated
  - contradiction: UV-BadConfig
  - commission: UV-NewRepeated
  - value: UV-BadConfig

### Get
- gate: service-side state
- upstream_guards: No caller identity, context or ownership token in the public API, pool.go:12 ("Get() (interface{}, error)").
- coverage:
  - loss: UV-GetOmitted
  - delay: UV-AbandonGet
  - duplication: UV-GetAgain
  - out-of-order: UV-LateGet
  - contradiction: UV-ContendedGet
  - commission: UV-GetOmitted
  - value: UV-WrongPoolGet

### Put
- gate: payload content and service-side state
- upstream_guards: Example intends a return after use, README.md:52 ("Put the connection back into the connection pool, when the connection is no longer in use"). No upstream enforcement of receiver, ownership or affinity.
- coverage:
  - loss: UV-ReturnMissing
  - delay: UV-LatePut
  - duplication: UV-BadOwnership
  - out-of-order: UV-LatePut
  - contradiction: UV-BadOwnership
  - commission: UV-BadOwnership
  - value: UV-WrongPoolPut, UV-BadOwnership

### Close
- gate: payload content and service-side state
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.
- coverage:
  - loss: UV-ReturnMissing
  - delay: UV-LateClose
  - duplication: UV-BadOwnership
  - out-of-order: UV-LateClose
  - contradiction: UV-BadOwnership
  - commission: UV-BadOwnership
  - value: UV-WrongPoolPut, UV-BadOwnership

### Release
- gate: service-side state
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.
- coverage:
  - loss: UV-ReleaseOmitted
  - delay: UV-ReleaseOmitted
  - duplication: UV-ReleaseAgain
  - out-of-order: UV-ReleaseAgain
  - contradiction: UV-LateGet
  - commission: UV-ReleaseAgain
  - value: UV-WrongPoolRelease

### Len
- gate: service-side state
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.
- coverage:
  - loss: n/a: omitting a read has no state effect, channel.go:247 ("return len(c.getConns())").
  - delay: UV-LateRead
  - duplication: UV-LateRead
  - out-of-order: UV-LateRead
  - contradiction: UV-LateRead
  - commission: n/a: an unsolicited read has no state effect, channel.go:247 ("return len(c.getConns())").
  - value: UV-LateRead

### DirectPing
- gate: payload content and service-side state
- upstream_guards: Adapter must obtain interface exposing Ping. That assertion does not establish configuration, channel.go:78 ("if poolConfig.Ping != nil {").
- coverage:
  - loss: UV-PingFault
  - delay: UV-CallbackDelay
  - duplication: UV-PingFault
  - out-of-order: UV-PingFault
  - contradiction: UV-PingFault
  - commission: UV-PingFault
  - value: UV-PingFault

### FactoryResult
- gate: payload content
- upstream_guards: Caller supplies the callback. Error result is typed. No stronger upstream lifecycle, panic, timing or reentrancy guarantee is documented.
- coverage:
  - loss: UV-FactoryFault
  - delay: UV-CallbackDelay
  - duplication: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:154 ("conn, err := c.factory()").
  - out-of-order: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:154 ("conn, err := c.factory()").
  - contradiction: UV-FactoryFault
  - commission: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:154 ("conn, err := c.factory()").
  - value: UV-FactoryFault

### CloseResult
- gate: payload content
- upstream_guards: Caller supplies the callback. Error result is typed. No stronger upstream lifecycle, panic, timing or reentrancy guarantee is documented.
- coverage:
  - loss: UV-CloseFault
  - delay: UV-CallbackDelay
  - duplication: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:212 ("return c.close(conn)").
  - out-of-order: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:212 ("return c.close(conn)").
  - contradiction: UV-CloseFault
  - commission: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:212 ("return c.close(conn)").
  - value: UV-CloseFault

### PingResult
- gate: payload content
- upstream_guards: Caller supplies the callback. Error result is typed. No stronger upstream lifecycle, panic, timing or reentrancy guarantee is documented.
- coverage:
  - loss: UV-PingFault
  - delay: UV-CallbackDelay
  - duplication: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:220 ("return c.ping(conn)").
  - out-of-order: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:220 ("return c.ping(conn)").
  - contradiction: UV-PingFault
  - commission: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:220 ("return c.ping(conn)").
  - value: UV-PingFault

### IdleAge
- gate: service-side state
- upstream_guards: No injected pool clock. Time is sampled by Get, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {").
- coverage:
  - loss: n/a: local time sampling has no delivery channel, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {").
  - delay: UV-AbandonGet
  - duplication: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {").
  - out-of-order: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {").
  - contradiction: n/a: one observation per branch, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {").
  - commission: n/a: synchronous result has no autonomous or duplicate delivery after the invocation returns, channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {").
  - value: UV-BadConfig

### WaitDelivery
- gate: service-side state
- upstream_guards: Only Put produces delivery in this component, channel.go:183 ("req <- connReq{"). No requester identifier in payload, channel.go:36 ("idleConn *idleConn").
- coverage:
  - loss: UV-ReturnMissing
  - delay: UV-AbandonGet
  - duplication: n/a: serialized dequeue before send to a private request channel, channel.go:182 ("c.connReqs = c.connReqs[:l-1]").
  - out-of-order: UV-LatePut
  - contradiction: UV-ContendedGet
  - commission: n/a: delivery requires registered work, channel.go:179 ("if l := len(c.connReqs); l > 0 {").
  - value: UV-BadOwnership

### DrainDone
- gate: service-side state
- upstream_guards: Only the first successful detachment can drain its captured channel, channel.go:227 ("c.conns = nil"), channel.go:234 ("if conns == nil {").
- coverage:
  - loss: UV-CloseFault
  - delay: UV-CallbackDelay
  - duplication: n/a: there is one drain per captured channel, channel.go:234 ("if conns == nil {").
  - out-of-order: n/a: the range executes after detachment in the same call, channel.go:239 ("for wrapConn := range conns {").
  - contradiction: UV-LateGet
  - commission: n/a: requires prior detachment, channel.go:234 ("if conns == nil {").
  - value: n/a: payloadless method or completion signal, channel.go:239 ("for wrapConn := range conns {").

### UV-NewOmitted
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-NewRepeated
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-BadConfig
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-GetOmitted
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-GetAgain
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-AbandonGet
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-LateGet
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-ContendedGet
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-WrongPoolGet
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-ReturnMissing
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-LatePut
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-LateClose
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-BadOwnership
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-WrongPoolPut
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-ReleaseOmitted
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-ReleaseAgain
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-WrongPoolRelease
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-LateRead
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-FactoryFault
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-CloseFault
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-PingFault
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.

### UV-CallbackDelay
- gate: observed service state and/or payload as for base event
- upstream_guards: No deployment-wide upstream guarantee. Tests and example are representative callers only.
