# Preliminary open questions — incomplete

Q-01: What must happen to pending Get calls when Release runs, and who owns a connection returned after shutdown? Requests wait at channel.go:137 ("ret, ok := <-req"); Release clears the pool without draining that queue (observed-in-code, channel.go:224-242). Options: wake with error; specify another completion mechanism. Status: OPEN. Fault: F-12; trigger: adversarial trace.

Q-02: May Factory and Close callbacks re-enter pool methods, and what are their blocking and failure contracts? Both can run under mu (observed-in-code, channel.go:154 ("conn, err := c.factory()"), channel.go:212 ("return c.close(conn)")). Options: explicitly prohibit reentry; permit it with defined synchronization. Status: OPEN. Fault: F-13; trigger: step-3 lock-discipline annotation.

Q-03: Should a handed-off connection receive the same Ping validation as an idle-channel connection? The idle path calls Ping (observed-in-code, channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {")); the waiter path returns after its age check (channel.go:148 ("return ret.idleConn.conn, nil")). Status: OPEN. Fault: F-18; trigger: step-1 extraction.

Q-04: What should a second Get from the same caller do while its first request is pending or its first connection remains held? The queue records channels, without caller identity (observed-in-code, channel.go:135 ("c.connReqs = append(c.connReqs, req)")). Status: OPEN. Fault: F-14; trigger: step-3 checklist.

These are preliminary; model draft questions and other findings have not been consolidated.
