# Open questions (preliminary; not exhaustive)

All questions remain open. These are evidence-backed candidates, not a completed matrix-to-question reconciliation.

## Q-01 — Capacity and waiter lifecycle
Question: Should full-capacity Get wait indefinitely, return an error, or support cancellation? What happens to waiters when a resource is closed or the pool released? Current behaviour: Get waits on req (observed-in-code, channel.go:137 ("ret, ok := <-req")); Put sends to a waiter (channel.go:183 ("req <- connReq{")); Release does not walk the waiter list (channel.go:223-243). The test expects an error (observed-in-tests, channel_rpc_test.go:94 ("if err != ErrMaxActiveConnReached {")); README.md:15 describes waiting. Proposed: define a bounded, cancellable waiter lifecycle and release result. Status: OPEN. Fault: F-12. Trigger: step-1 extraction.

## Q-02 — Released checked-out resources and callbacks
Question: Who closes a resource returned after Release, and should callback failure change accounting? Current behaviour: Release clears c.close (observed-in-code, channel.go:231 ("c.close = nil")); subsequent Close returns nil (channel.go:208 ("if c.close == nil {")). Close decrements before callback (channel.go:211 ("c.openingConns--")). Proposed: specify ownership and failure semantics. Status: OPEN. Fault: F-12. Trigger: step-1 extraction.

## Q-03 — Callback reentrancy and synchronization
Question: May factory and close callbacks reenter the pool, block, or fail during concurrent Release? Current behaviour: Get invokes factory while holding mu (channel.go:131 ("c.mu.Lock()"), channel.go:154 ("conn, err := c.factory()")); Close invokes close while holding mu (channel.go:206 ("c.mu.Lock()"), channel.go:212 ("return c.close(conn)")). Reentry into methods taking the same mutex would block. Proposed: document or change the callback contract after a human decision. Status: OPEN. Fault: F-13. Trigger: step-3 lock-discipline annotation.

## Q-04 — Validation on handoff
Question: Must a connection handed to a waiting Get be pinged, and how are timeout and validation failures handled? Current behaviour: idle-channel path checks ping (channel.go:123 ("if c.ping != nil {")); waiter path returns directly (channel.go:148 ("return ret.idleConn.conn, nil")). Proposed: clarify whether validation applies uniformly. Status: OPEN. Fault: F-18. Trigger: step-1 extraction.

## Q-05 — Duplicate and foreign resources
Question: Are repeated Put, Close, or values from another pool supported, and how should counts and ownership behave? Current behaviour: no identity validation is visible before Put or Close (channel.go:167 ("func (c *channelPool) Put(conn interface{}) error {"), channel.go:211 ("c.openingConns--")). Proposed: specify ownership and exactly-once release. Status: OPEN. Fault: F-14. Trigger: step-3 checklist.

## Q-06 — Construction and capacities
Question: What should nil configuration, zero maximum capacity, partial initialization failure and malformed callback results mean? Current behaviour: zero capacities pass the inequality (channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {")); a nil config is dereferenced there. Proposed: specify valid capacity and callback outcomes. Status: OPEN. Fault: F-18. Trigger: step-1 extraction.

## Q-07 — Concurrent shutdown and access
Question: Which overlapping Get, Put, Ping and Release outcomes are permitted, including access to captured channel and callback references? Current behaviour: Get captures the channel under the mutex (channel.go:104 ("conns := c.getConns()")); Release clears references under the mutex and closes the captured channel later (channel.go:227 ("c.conns = nil"), channel.go:238 ("close(conns)")). Ping reads c.ping without acquiring that mutex (channel.go:220 ("return c.ping(conn)")). Proposed: specify synchronization, resource ownership and results for each ordering. Status: OPEN. Fault: F-15. Trigger: adversarial trace.
