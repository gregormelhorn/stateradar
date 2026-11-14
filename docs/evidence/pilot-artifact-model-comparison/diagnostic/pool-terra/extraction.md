# Partial extraction

Scope: one channelPool, its Pool methods, caller-owned connections and injected callbacks. Network service behavior is outside the boundary.

- Construction validates capacity and callbacks (observed-in-code, channel.go:59 ("if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {"), channel.go:62 ("if poolConfig.Factory == nil {")). The inequalities imply MaxIdle >= 0.
- Get queues a buffered request at capacity and waits (observed-in-code, channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:137 ("ret, ok := <-req")). IdleTimeout checks returned connection age; it is not a timer on this wait.
- Put serves the first queued request or buffers or closes the connection (observed-in-code, channel.go:179 ("if l := len(c.connReqs); l > 0 {"), channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:")).
- Release clears callbacks and channel under mu and drains the saved channel afterwards (observed-in-code, channel.go:227 ("c.conns = nil"), channel.go:238 ("close(conns)"), channel.go:241 ("closeFun(wrapConn.conn)")). It does not iterate connReqs or decrement openingConns on this path.
- Factory and Close callbacks can run with mu held (observed-in-code, channel.go:131 ("c.mu.Lock()"), channel.go:154 ("conn, err := c.factory()"), channel.go:206 ("c.mu.Lock()"), channel.go:212 ("return c.close(conn)")). A callback waiting for a method that acquires the same mutex cannot complete.
- Callback declarations do not specify blocking, reentrancy, ownership, or failure guarantees (observed-in-code, channel.go:26 ("Factory func() (interface{}, error)"), channel.go:28 ("Close func(interface{}) error"), channel.go:30 ("Ping func(interface{}) error")).

README doctrine candidates: expiry closes and discards connections (README.md:13); ping-invalid connections are discarded (README.md:14); full pools support waiting (README.md:15). Full doctrine mapping remains to be reviewed.

Draft files preserve model questions and claims. They are not a reviewed extraction; questions and two unclear test-file judgments still require individual review.
