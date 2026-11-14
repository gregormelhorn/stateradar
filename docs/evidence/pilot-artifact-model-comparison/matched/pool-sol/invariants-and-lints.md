# Invariants and lints

NAT-01. Holders return a resource once after use to its owning pool. README.md:52 supplies “when … no longer in use”. Identity and exactly-once are inferred environmental assumptions, since pool.go:14 ("Put(interface{}) error") carries no identity token. Q-12.

NAT-02. Callbacks run synchronously and report outcome with an opaque error or value. channel.go:26 ("Factory func() (interface{}, error)"), channel.go:28 ("Close func(interface{}) error"), channel.go:30 ("Ping func(interface{}) error"). Their physical effects, progress and re-entry obligations are unresolved in Q-11 and Q-21.

NAT-SYS. Shared external service failure may synchronize externally issued calls. README.md:22 shows a fixed shared address. T-15–T-17 vary caller retry timing. Q-18.

| Predicate (proposed unless required below) | Open | Open_Waiting | Open_IdleAndWaiting | Released |
|---|---|---|---|---|
| SYS-01. Representation remains opaque at Pool boundary | satisfied | satisfied | satisfied | satisfied |
| SYS-02. Observed age beyond configured limit causes disposal and discard | discard and attempt close | handoff age checked | both branches checked | stale handoff can attempt disabled Close, Q-07 and Q-14 |
| SYS-03. Invalid value is discarded when configured validation detects it | idle checked, fresh creation bypasses | handoff skips validation, Q-09 | only idle path checks, Q-09 | validation can overlap detach, Q-08 |
| SYS-04. Full pool supports waiting | enqueue after miss | queue continues | queue may coexist with idle work, Q-04 | in-flight enqueue and no wake, Q-02 |
| SYS-05. Factory creates new connections | initialization and later miss | only below cap under lock | following a miss below cap | same-receiver Factory disabled, Q-13 |
| SYS-06. Close requests single disposal | callback under lock | same | same | only captured drain closer survives, late Close skips, Q-07 |
| SYS-07. Initial population and idle/active bounds respect config | initial fill, bounded idle | pending unbounded, count gate applies after miss | idle bounded and same count gate | retained count and waiters, no active creation, Q-10 and Q-16 |
| SYS-08. Get produces a resource or a defined error under progress assumptions | can defer | Close alone cannot finish it | subsequent caller may bypass waiter | fresh Get rejects, earlier Get can wait permanently, Q-01–Q-04 |
| SYS-09. Release disposes resources within defined ownership scope | makes old idle storage drainable | pending and held resources unresolved | pending entries and handoff ownership unresolved | captured drain best effort, Q-02, Q-07, Q-17 |
| SYS-10. Len projects idle-channel depth | current or captured idle count | normally zero | available entries visible | fresh snapshots zero, older may retain channel, Q-15 |
| SYS-11. Reported accounting equals physically live resources | violated on close error or duplicate Close | same | same | unchanged by drain, Q-10 and Q-12 |

Evidence by predicate (observed-in-code): SYS-01 pool.go:12 ("Get() (interface{}, error)"); SYS-02 channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {"), channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {"); SYS-03 channel.go:124 ("if err := c.Ping(wrapConn.conn); err != nil {"), channel.go:148 ("return ret.idleConn.conn, nil"); SYS-04 channel.go:135 ("c.connReqs = append(c.connReqs, req)"); SYS-05 channel.go:154 ("conn, err := c.factory()"); SYS-06 channel.go:212 ("return c.close(conn)"); SYS-07 channel.go:70 ("conns:        make(chan *idleConn, poolConfig.MaxIdle),"), channel.go:133 ("if c.openingConns >= c.maxActive {"); SYS-08 channel.go:106 ("return nil, ErrClosed"), channel.go:137 ("ret, ok := <-req"); SYS-09 channel.go:241 ("closeFun(wrapConn.conn)"); SYS-10 channel.go:247 ("return len(c.getConns())"); SYS-11 channel.go:159 ("c.openingConns++"), channel.go:211 ("c.openingConns--").

<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 DOC-5 DOC-6 DOC-7 DOC-8 DOC-9 DOC-10 DOC-11 DOC-12 DOC-13 -->

## Doctrine mapping

| ID | Mapping | Target |
|---|---|---|
| DOC-1 | invariant | SYS-01 |
| DOC-2 | invariant | SYS-02 |
| DOC-3 | invariant | SYS-03 |
| DOC-4 | invariant | SYS-04 |
| DOC-5 | invariant | SYS-05 |
| DOC-6 | invariant | SYS-06 |
| DOC-7 | invariant | SYS-03 |
| DOC-8 | invariant | SYS-07 |
| DOC-9 | invariant | SYS-02 |
| DOC-10 | invariant | SYS-08 |
| DOC-11 | constraint | NAT-01 |
| DOC-12 | invariant | SYS-09 |
| DOC-13 | invariant | SYS-10 |

DOC-8 sets example values, not global defaults. DOC-12 leaves ownership, close-error semantics and the exact point of shutdown unclear. DOC-3 describes invalidity handling, but does not set the timing or all acquisition routes. The missing handoff check maps to Open_Waiting × Get/Put and Q-09. DOC-2 and DOC-9 do not state that an idle timer must wake autonomously.

## Lint results

| Lint | Evidence and disposition |
|---|---|
| Waiting or stopping without timeout | Q-01 and Q-17. Bare receive channel.go:137 ("ret, ok := <-req") and synchronous drain channel.go:241 ("closeFun(wrapConn.conn)"). |
| Retries without maximum | Q-14. Get loops after discards. channel.go:108 ("for {"), channel.go:126 ("continue"). Factory error itself terminates that attempt. |
| External operation failure | Q-10, Q-11, Q-13 and Q-21. Detail in seam sweep and T-04–T-06, T-14. |
| Cancellation and lifecycle disagreement | Q-02, Q-03, Q-05 and Q-07. Owner, pending Get and holder tracks can terminate independently. P-02a, P-03a and T-03. |
| Terminal diagnostic and startup/shutdown | Q-01, Q-02, Q-07, Q-13 and Q-17. Fresh closed Get has an error. Late nonnil resource disposal and repeated Release can silently return. |
| Unbounded queue or overload | Q-16. Pending slice grows at channel.go:135 ("c.connReqs = append(c.connReqs, req)"). Idle is bounded by channel.go:70 ("conns:        make(chan *idleConn, poolConfig.MaxIdle),"). |
| Synchronized resets | No pool-level retry reset observed. Shared-fate demand is contingent and analyzed in Q-18 and T-15–T-17. |
| Dual ownership cleanup | No destructor is attached to the Pool interface. Explicit holder Close and idle drain can both dispose if caller first returns and then closes the same value. P-10, Q-12 (F-08 also applies). |
| Async cancellation isolation | Application can abandon the wrapper independently of the blocked Get goroutine. T-03, Q-05 (F-09 also applies). |
| User-model legibility | Q-03 and Q-04. Earlier waiter remains pending after later creation or available idle return. Q-08 and Q-15 cover observations crossing detach. |
