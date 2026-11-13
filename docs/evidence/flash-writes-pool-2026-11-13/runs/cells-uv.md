<!-- states: Open_IdleAvailable, Open_IdleFull, Open_NoIdle_BelowCap, Open_NoIdle_AtCap, Open_Waiting_AtCap, Open_Waiting_BelowCap, Open_Waiting_IdleAvailable, Closed -->

Drafted by DeepSeek Flash (`draft-cells`); every cell is a proposal until the steering agent has read its cited line. `→ Q-?` and `MISSING` stay until decided.

### Sub-table 1

| State | UV-Conn-nil | UV-Put-dup | UV-Close-dup | UV-Put-foreign | UV-Close-foreign |
|---|---|---|---|---|---|
| **Open_IdleAvailable** | reject channel.go:168 ("if conn == nil {") — Put rejects nil with an error. | reject channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:") — Duplicate put is enqueued again (no duplicate check). | handle channel.go:212 ("return c.close(conn)") — Close called again; decrements openingConns. | handle channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:") — No factory-origin check; foreign connection is enqueued. | handle channel.go:212 ("return c.close(conn)") — No factory-origin check; close callback runs and openingConns decremented. |
| **Open_IdleFull** | reject channel.go:168 ("if conn == nil {") — Put rejects nil with an error. | reject channel.go:196 ("return c.Close(conn)") — Channel full, so duplicate is closed, decrementing openingConns. | handle channel.go:212 ("return c.close(conn)") — Close called again; decrements openingConns. | handle channel.go:196 ("return c.Close(conn)") — Channel full; foreign conn closed and openingConns decremented. | handle channel.go:212 ("return c.close(conn)") — No factory-origin check; close callback runs and openingConns decremented. |
| **Open_NoIdle_BelowCap** | reject channel.go:168 ("if conn == nil {") — Put rejects nil with an error. | handle channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:") — Duplicate put is enqueued; no duplicate check. | handle channel.go:212 ("return c.close(conn)") — Close called again; decrements openingConns. | handle channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:") — No factory-origin check; foreign connection is enqueued. | handle channel.go:212 ("return c.close(conn)") — No factory-origin check; close callback runs and openingConns decremented. |
| **Open_NoIdle_AtCap** | reject channel.go:168 ("if conn == nil {") — Put rejects nil with an error. | handle channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:") — Duplicate put is enqueued; no duplicate check. | handle channel.go:212 ("return c.close(conn)") — Close called again; decrements openingConns. | handle channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:") — No factory-origin check; foreign connection is enqueued. | handle channel.go:212 ("return c.close(conn)") — No factory-origin check; close callback runs and openingConns decremented. |
| **Open_Waiting_AtCap** | reject channel.go:168 ("if conn == nil {") — Put rejects nil with an error. | reject channel.go:183 ("req <- connReq{") — Duplicate handed to first waiting Getter. | handle channel.go:212 ("return c.close(conn)") — Close called again; decrements openingConns. | handle channel.go:183 ("req <- connReq{") — Foreign connection handed to waiting Getter. | handle channel.go:212 ("return c.close(conn)") — No factory-origin check; close callback runs and openingConns decremented. |
| **Open_Waiting_BelowCap** | reject channel.go:168 ("if conn == nil {") — Put rejects nil with an error. | reject channel.go:183 ("req <- connReq{") — Duplicate handed to first waiting Getter. | handle channel.go:212 ("return c.close(conn)") — Close called again; decrements openingConns. | handle channel.go:183 ("req <- connReq{") — Foreign connection handed to waiting Getter. | handle channel.go:212 ("return c.close(conn)") — No factory-origin check; close callback runs and openingConns decremented. |
| **Open_Waiting_IdleAvailable** | reject channel.go:168 ("if conn == nil {") — Put rejects nil with an error. | reject channel.go:183 ("req <- connReq{") — Duplicate handed to first waiting Getter. | handle channel.go:212 ("return c.close(conn)") — Close called again; decrements openingConns. | handle channel.go:183 ("req <- connReq{") — Foreign connection handed to waiting Getter. | handle channel.go:212 ("return c.close(conn)") — No factory-origin check; close callback runs and openingConns decremented. |
| **Closed** | reject channel.go:168 ("if conn == nil {") — Put rejects nil with an error. | reject channel.go:176 ("return c.Close(conn)") — Pool closed, Close returns nil because close is nil. | ignore (documented) channel.go:208 ("if c.close == nil {") — Returns nil without a check that the connection was ever opened. | ignore (documented) channel.go:176 ("return c.Close(conn)") — Close is nil, so returns nil. | ignore (documented) channel.go:208 ("if c.close == nil {") — Returns nil without a factory-origin check. |

## Review list

- Open_NoIdle_AtCap x UV-Put-dup: jev unclear (confidence 0.35)
- Open_Waiting_AtCap x UV-Put-dup: jev unclear (confidence 0.33)
- Open_Waiting_BelowCap x UV-Put-dup: jev unclear (confidence 0.33)
- Open_Waiting_IdleAvailable x UV-Put-dup: jev unclear (confidence 0.44)
- Open_IdleFull x UV-Put-foreign: jev unclear (confidence 0.13)
- Closed x UV-Put-foreign: jev contradicted (confidence 0.35)

## Draft questions

- Put and Close document no factory-origin check, so UV-Put-foreign and UV-Close-foreign are handled without validation; is that intended?
- UV-Close-dup decrements openingConns again on each call (line 212), can drive it negative; is there any duplicate-close guard intended?
- On Closed, UV-Put-foreign and UV-Close-dup rely on c.close being nil (line 208) to return nil; is the nil close-callback the intended signal?
- For UV-Put-dup in Open_Waiting_* states, the duplicate is sent on the waiter channel; is there an intended identity check missing?
