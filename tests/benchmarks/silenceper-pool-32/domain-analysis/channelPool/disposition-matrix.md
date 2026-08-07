# Disposition matrix — silenceper/pool `channelPool` (to-be)

<!-- states: Active_HasIdle Active_IdleExhausted_UnderCap Active_IdleExhausted_AtCapacity Released -->

Abstraction: four flat leaf states derived from idle availability, capacity,
and terminal release; completeness is relative to the twenty-event catalogue.
<!-- terminal: Released -->

| state | Get | Put | Close | Release | FactoryFail | IdleTimeout | PingFail |
|---|---|---|---|---|---|---|---|
| **Active_HasIdle** | handle | handle | handle | transition →Released | handle | handle | handle |
| **Active_IdleExhausted_UnderCap** | handle | transition →Active_HasIdle | handle DR-006 | transition →Released | handle DR-005 | ignore (documented) `channel.go:148` | ignore (documented) `channel.go:148` |
| **Active_IdleExhausted_AtCapacity** | defer (queued) DR-004; Ping before return | handle | handle DR-006 | transition →Released DR-001; resolve waiters | ignore (documented) DR-005; Factory gate cannot fire at capacity | ignore (documented) `channel.go:132` | ignore (documented) `channel.go:132` |
| **Released** | reject `channel.go:99` | ignore (documented) DR-003 | ignore (documented) `channel.go:202` | ignore (documented) `channel.go:202` | ignore (documented) `channel.go:218` | ignore (documented) `channel.go:218` | ignore (documented) `channel.go:220` |

| state | UV-Get-commission | UV-Get-value | UV-Put-loss | UV-Put-duplication | UV-Put-out-of-order | UV-Put-commission | UV-Close-duplication |
|---|---|---|---|---|---|---|---|
| **Active_HasIdle** | UNSPECIFIED → Q-UV-01 | UNSPECIFIED → Q-UV-01 | ignore (documented) DR-002; NAT caller contract | ignore (documented) DR-002; NAT caller contract | ignore (documented) DR-003; terminal/no-ownership contract | ignore (documented) DR-002; NAT caller contract | ignore (documented) DR-006; NAT caller contract |
| **Active_IdleExhausted_UnderCap** | UNSPECIFIED → Q-UV-01 | UNSPECIFIED → Q-UV-01 | ignore (documented) DR-002; NAT caller contract | ignore (documented) DR-002; NAT caller contract | ignore (documented) DR-003; terminal/no-ownership contract | ignore (documented) DR-002; NAT caller contract | ignore (documented) DR-006; NAT caller contract |
| **Active_IdleExhausted_AtCapacity** | UNSPECIFIED → Q-UV-01 | UNSPECIFIED → Q-UV-01 | ignore (documented) DR-002; NAT caller contract | ignore (documented) DR-002; NAT caller contract | ignore (documented) DR-003; terminal/no-ownership contract | ignore (documented) DR-002; NAT caller contract | ignore (documented) DR-006; NAT caller contract |
| **Released** | UNSPECIFIED → Q-UV-01 | UNSPECIFIED → Q-UV-01 | ignore (documented) DR-002; NAT caller contract | ignore (documented) DR-002; NAT caller contract | ignore (documented) DR-003; terminal/no-ownership contract | ignore (documented) DR-002; NAT caller contract | ignore (documented) DR-006; NAT caller contract |

| state | UV-Close-out-of-order | UV-Close-contradiction | UV-Release-duplication | UV-Release-out-of-order | UV-Release-contradiction | UV-Release-commission |
|---|---|---|---|---|---|---|
| **Active_HasIdle** | ignore (documented) DR-006; NAT caller contract | ignore (documented) DR-006; NAT caller contract | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 |
| **Active_IdleExhausted_UnderCap** | ignore (documented) DR-006; NAT caller contract | ignore (documented) DR-006; NAT caller contract | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 |
| **Active_IdleExhausted_AtCapacity** | ignore (documented) DR-006; NAT caller contract | ignore (documented) DR-006; NAT caller contract | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 |
| **Released** | ignore (documented) DR-006; NAT caller contract | ignore (documented) DR-006; NAT caller contract | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 |
