# channelPool domain behaviour analysis

model routing: on (unevaluated, cascade plan stage 3)
routing variant: routed
Jev model: jev-1.14.0

Scope is one published channelPool receiver plus its constructor, its public Pool methods and the synchronous callback seams they invoke. Construction failure, request phases and release drain are charted alongside the receiver states. The receiver matrix projects pending and idle work; handoff ownership and in-flight callbacks live in the request/resource tracks and trace guards. The pair reachability extension connects the idle-and-waiting state through an observed ordering.

| Measure | Count |
|---|---:|
| Receiver states | 4 |
| Events | 36 (26 undesired variants) |
| Cross-source pairs / orderings | 10 / 20 |
| Matrix cells | 144 |
| UNSPECIFIED | 0 |
| Accidental ignores | 15 |
| Guard groups proven / violations / not-formalizable | 10 / 0 / 4 |
| Consolidated findings and open questions | 22 / 22 |
| Blind situations classified | 101 (convergent 55, divergence 41, pass-B-blind-spot 4, convergent-hole 1) |

## Findings and coverage

| Applicable case | Trace or variant | Finding and open decision |
|---|---|---|
| Full pool, no later return | Get at capacity; P-03a | Existing TestPool_Get timed out at private receive channel.go:137 ("ret, ok := <-req"). It expects immediate sentinel; README.md:15 says wait. Q-01. |
| Existing and late enqueue crossing shutdown | P-03a/P-03b, UV-AfterRelease | Release closes only idle channel at channel.go:238 ("close(conns)"). An old miss can enqueue after detach at cap. Below cap it returns ErrClosed. Fresh calls always reject. Q-02. |
| Waiter after Close or failed cleanup frees capacity | P-02a/P-02b | Close decrements at channel.go:211 ("c.openingConns--") without wake; later Get can create first. Q-03/Q-10. |
| Admission vs idle work after an unlocked miss | P-01a/P-01b, UV-Overlap | Put can buffer before admission at channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:"). At cap a later Get can take the idle connection first. Below cap the earlier Get can create despite idle inventory. Q-04. |
| Caller departure, with or without later return | T-03, UV-Abandon | No cancellation mechanism. A later handoff at channel.go:183 ("req <- connReq{") removes the queue entry and sends into the abandoned acquisition; absent later input it stays pending. Q-05. |
| Same owner while first Get waits | T-01, UV-GetAgain | Two goroutines enqueue distinct channels at channel.go:135 ("c.connReqs = append(c.connReqs, req)"). Each Put targets one. Q-06. |
| Same owner while first resource held | T-02, UV-GetAgain | Below cap separate acquisition and increment at channel.go:159 ("c.openingConns++"); at cap the caller can wait on itself unless another actor returns a resource. Q-06. |
| Return and overflow disposal across detach | P-04a/P-04b, P-05a/P-05b, T-07 | Nonnil Put/Close may return nil without disposal at channel.go:208 ("if c.close == nil {"). Overflow can lose cleanup in the unlock-to-Close gap. Q-07. |
| Ping success/failure, dispatch and teardown | T-04, T-13, UV-PingDelay | Original implementation race detector identified channel.go:123 ("if c.ping != nil {") and channel.go:229 ("c.ping = nil"). Ordered probe reproduced nil-dispatch panic. A callback already running can return a resource after release or skip cleanup on failure and retry. Q-08/Q-22. |
| Handoff validation | T-09, UV-PingError | Direct delivery skips Ping, confirmed by a probe; channel.go:148 ("return ret.idleConn.conn, nil"). Q-09. |
| Failed disposal or ambiguous physical effect | P-05a, T-14, UV-CloseError/Value | Live Close decrements then surfaces callback result at channel.go:212 ("return c.close(conn)"). Overflow surfaces it, expiry and Ping failure ignore it, Release ignores it and does not decrement. Q-10/Q-21. |
| Re-entry, callback failure and reconfiguration | T-05/T-06, callback variants | Live Factory holds lock at channel.go:154 ("conn, err := c.factory()"), as live Close does at channel.go:212 ("return c.close(conn)"). Release cannot detach while either holds it. Factory can deadlock through Len. Drain callback runs after detach using its captured closer, outside the lock. Q-11/Q-17/Q-21. |
| Wrong receiver vs wrong payload, duplicate return/disposal | P-10a/P-10b, T-11, UV-WrongPool, UV-ForeignResource | No ownership check. Untyped nil rejects, typed nil passes. Repeating Close can decrement twice, while repeating Put can distribute the same resource twice. channel.go:168 ("if conn == nil {"), channel.go:211 ("c.openingConns--"). Q-12. |
| Missing/delayed owner, repeat New and configuration | UV-NoOwner, UV-OwnerLate, UV-NewAgain, UV-Config, T-08 | New allocates independent storage. Nil config panics, zero caps pass, failing setup drains prior successes. channel.go:58 ("func NewChannelPool(poolConfig *Config) (Pool, error) {"), channel.go:85 ("c.Release()"). Q-13/Q-19. |
| Age and request retry limits | T-10, UV-Aged | Strict boundary, equality survives. A delayed handoff can expire after Put returned. No autonomous expiry or loop retry maximum. channel.go:142 ("if ret.idleConn.t.Add(timeout).Before(time.Now()) {"). Q-14. |
| Idle observer and active accounting | P-06–P-09, UV-Observer | Len reads idle length after snapshot, channel.go:247 ("return len(c.getConns())"). Count tracks creation increments and attempted live disposal, not physical liveness. Q-15. |
| Backing storage and queue bounds | T-12, UV-Abandon | Slice removed logically without clearing old tail, channel.go:181 ("copy(c.connReqs, c.connReqs[1:])"), channel.go:182 ("c.connReqs = c.connReqs[:l-1]"). The queue persists across Release and runtime cost is unmeasured. Q-16. |
| Repeat Release during drain | T-06/T-13, UV-ReleaseAgain | Repeat returns while old captured closer blocked. Error is ignored on first drain. channel.go:234 ("if conns == nil {"), channel.go:241 ("closeFun(wrapConn.conn)"). Q-17. |
| Multi-instance shared server | T-15–T-17 | Caller-driven Factory load can synchronize, without a pool backoff or reset signal in the acquisition loop. channel.go:154 ("conn, err := c.factory()"), channel.go:157 ("return nil, err"). Model probes only. Q-18. |
| Fixture readiness | as-is-validation.md | Fixed sleep is a test assumption. channel_rpc_test.go:32 ("time.Sleep(time.Millisecond * 300) // wait until tcp server has been settled"). Q-20. |
| Independent unsolicited callback completion | Factory/PingResult/CloseResult coverage | Inapplicable as a normal event. Callback returns occur synchronously only at invocation sites. channel.go:154 ("conn, err := c.factory()"), channel.go:220 ("return c.ping(conn)"), channel.go:212 ("return c.close(conn)"). Re-entrant side effects remain Q-11. |

## Executed verification

| Check | Result |
|---|---|
| Canonical catalogue renderer | PILOT CATALOGUE: OK (037); round-trip identity OK (126). |
| Stage 1 matrix wrapper | CHECK MATRIX: OK (4 rows x 36 events) (065). |
| Guard script | 10 proven, 0 violations and 4 runtime-dependent groups marked not-formalizable (073). Full assignments in guard-results.txt. |
| Strict sidecar generator | OK channelPool: 4 states x 36 events = 144 cells, 22 questions, DRs [] (116). |
| Stage 2 matrix wrapper | CHECK MATRIX: OK (4 rows x 36 events) (118). |
| DSC with Mermaid | DSC CHECK: OK (4 states x 36 events, 144 cells, 14 guard groups) (119). Initial failure (080) required explicit leaf-to-Released edges for inherited release behaviour. |
| Reachability | REACHABILITY CHECK: OK (4/4 states reachable from 'Open', 1 terminal) (120). P-01a is the probe-backed edge into Open_IdleAndWaiting. |
| Part B coverage | PART-B COVERAGE: OK (36 events, 20 pair orderings) (121). 101 distinct situation rows classified. Code-derived catalogue dependencies and vocabulary drift are recorded in part-b-diff.md. |
| Original Go suite | FAIL, timeout after 8s at TestPool_Get (015). |
| Remaining eight original tests | PASS under bounded targeted selection (038). |
| Overlay scheduling probes | PASS, first eight (052) and expanded set of twelve (100). First eight also passed with race instrumentation (095). |
| Original-source race probe | FAIL with data race, Get read channel.go:123 against Release write channel.go:229 (101). |
| Tracked workspace status | Only domain-analysis/ untracked (122). Git printed sandbox cache warnings. |

Classifier and guard results are model evidence. The scope of the Go runtime checks is the bounded probes and selected RPC cases. The retention cost and multi-instance traffic remain unmeasured. No behavioural DRs were decided. The optional conventional-review cross-check was not run.

## Routing failures and ledger

- channel.go draft-verify Flash returned malformed JSON, `Expecting ',' delimiter` (024). Raw response retained. The chain skipped Jev for this draft, while all readable draft questions were dispositioned and extraction performed directly.
- Initial blind package using the README Feature section was rejected as too short (042), before any provider call. Replaced with a verbatim prose-only extract spanning README sections and inspected complete package before sending.
- Initial channel.go Step 8 batch failed citation prevalidation on C3's short fragment (057). Corrected C3 and C1 to the actual observing lines, then ran all 38 claims (067). No first result existed.
- The three answered ordering checks were all `unclear`, scope 0.01. Each assertion was outside the cited prose's exact scope and is linked to its question in T-18.
- No provider transport failure or budget exhaustion. Additional seam checks R1/R2, L1/L2 and M1/M2 completed. No companion-claim routing used.

Ledger file `routing.sqlite`
`local_models.py --ledger ../routing.sqlite status` (124)

```json
{
  "committed_or_reserved_microdollars": 18026,
  "limit_microdollars": 2000000,
  "calls": [
    {
      "id": 1,
      "provider": "deepseek-flash",
      "amount_microdollars": 2242,
      "status": "settled"
    },
    {
      "id": 2,
      "provider": "jev",
      "amount_microdollars": 193,
      "status": "settled"
    },
    {
      "id": 3,
      "provider": "deepseek-flash",
      "amount_microdollars": 869,
      "status": "settled"
    },
    {
      "id": 4,
      "provider": "jev",
      "amount_microdollars": 70,
      "status": "settled"
    },
    {
      "id": 5,
      "provider": "deepseek-flash",
      "amount_microdollars": 4157,
      "status": "settled"
    },
    {
      "id": 6,
      "provider": "deepseek-flash",
      "amount_microdollars": 2730,
      "status": "settled"
    },
    {
      "id": 7,
      "provider": "jev",
      "amount_microdollars": 249,
      "status": "settled"
    },
    {
      "id": 8,
      "provider": "deepseek-flash",
      "amount_microdollars": 6596,
      "status": "settled"
    },
    {
      "id": 9,
      "provider": "jev",
      "amount_microdollars": 125,
      "status": "settled"
    },
    {
      "id": 10,
      "provider": "jev",
      "amount_microdollars": 88,
      "status": "settled"
    },
    {
      "id": 11,
      "provider": "jev",
      "amount_microdollars": 94,
      "status": "settled"
    },
    {
      "id": 12,
      "provider": "jev",
      "amount_microdollars": 327,
      "status": "settled"
    },
    {
      "id": 13,
      "provider": "jev",
      "amount_microdollars": 130,
      "status": "settled"
    },
    {
      "id": 14,
      "provider": "jev",
      "amount_microdollars": 37,
      "status": "settled"
    },
    {
      "id": 15,
      "provider": "jev",
      "amount_microdollars": 119,
      "status": "settled"
    }
  ]
}
```
