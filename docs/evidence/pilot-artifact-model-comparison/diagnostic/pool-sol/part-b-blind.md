| id | Situation | Disposition | Expected behaviour (requirement terms) |
|---|---|---|---|
| New | Valid capacities (InitialCap ≤ MaxIdle ≤ MaxActive), all three callbacks present, non-negative idle time | transition → Pool_Ready | Construct pool pre-filled with InitialCap connections via Factory; hand out on Get; enforce MaxIdle/MaxActive and idle-time close per DOC-2/DOC-8/DOC-9. |
| New | Callbacks absent or capacities contradictory (e.g. MaxIdle > MaxActive, negative idle time) | reject (declared error/diagnostic) | Refuse construction; never publish a half-configured pool. |
| New | InitialCap = 0 (empty start) with valid bounds | transition → Pool_Ready_Empty | Publish pool that lazily creates up to MaxActive on Get. |
| Get | Pool_Ready, idle resources available, no ping configured | handle | Dequeue one idle resource, return it; count decrements on removal. |
| Get | Pool_Ready, idle resources available, ping configured | handle | Ping candidate; if valid return it; if invalid close and discard it and continue per DOC-3; check idle age and discard if over MaxIdle per DOC-2/DOC-9. |
| Get | Pool_Ready, no idle resource, live count < MaxActive | handle | Create via Factory; on success return it; on error/panic/nil return the error per DOC-5. |
| Get | Pool_Ready, live count = MaxActive (pool full) | handle (waits) | Block/queue the request until a Put delivers or Release terminates it, per DOC-4 connection waiting. |
| Get | Pool_Closed | reject (declared error) | Return ErrClosed; no waiting, no creation. |
| Get | IdleAge evaluation during Get | handle | Sample age against configured MaxIdle; close-and-discard expired candidates; continue scanning per DOC-9. |
| Put | Pool_Ready, resource was checked out from this pool, idle capacity < MaxIdle, waiter queued | transition → WaitDelivery (hand off) | Deliver directly to the waiting Get; do not count it as idle. |
| Put | Pool_Ready, resource valid, idle capacity < MaxIdle, no waiter | handle | Store the resource as idle; keep identity/ownership per DOC-11. |
| Put | Pool_Ready, idle capacity = MaxIdle (idle full) | handle | Close the returned resource via configured Close and drop it (overflow cleanup) so count stays bounded; do not retain. |
| Put | Pool_Closed / released | ignore (documented) | Resource is already orphaned; close it if possible or drop without state change; do not resurrect the pool. |
| Close | Resource was checked out and is being destroyed | handle | Invoke configured Close; on success count decremented; on error report per DOC-6; if waiter queued, create replacement. |
| Close | Resource already idle/in pool | reject (declared error) or ignore (documented) | Refuse to double-close a pooled resource or drop it from idle storage safely once; do not leave dangling entries. |
| Close | Resource nil / unknown / stale | reject (declared error) | Declared refusal; no state change. |
| Release | Pool_Ready (or Pool_Ready_Empty), no in-flight | transition → Pool_Releasing → Pool_Released | Drain all idle resources via Close per DOC-12; terminate waiters with ErrClosed; return after DrainDone. |
| Release | Pool_Releasing (already in progress) | ignore (documented) or defer | Second Release waits for completion or returns immediately; must not double-drain. |
| Release | Pool_Released | ignore (documented) | Idempotent no-op. |
| Len | Pool_Ready / Pool_Ready_Empty | handle | Return current live count (checked-out + idle) per DOC-13. |
| Len | Pool_Releasing / Pool_Released | handle | Return 0 (or remaining) consistently with teardown; must not race or panic. |
| DirectPing | Concrete value exposes Ping, Pool_Ready | handle | Invoke user Ping; report valid/invalid; invalid discarded per DOC-3. |
| DirectPing | Callback absent (structural assertion fails) | reject (declared error) | Adapter reports unsupported; pool unaffected. |
| FactoryResult | Success value | handle | Admit as connection; count increments; return to requester or idle. |
| FactoryResult | Error value | reject | Propagate error to requesting Get; do not count. |
| FactoryResult | nil value or value with error | reject | Treat as failed construction; propagate error; not admitted. |
| FactoryResult | Panic | reject | Recover (defensive) or propagate; pool must not be left with inconsistent count. |
| CloseResult | Success | handle | Connection count decremented; slot freed. |
| CloseResult | Error | handle | Log/report per DOC-6; if resource already unusable, still decrement; do not re-admit. |
| CloseResult | Panic | reject | Recover so pool state stable; do not leave half-decremented count. |
| PingResult | Valid | handle | Return candidate to requester. |
| PingResult | Invalid | handle | Discard candidate (Close → CloseResult) and try next per DOC-3. |
| PingResult | Error / panic | reject | Treat as invalid; discard candidate; continue. |
| IdleAge | Within MaxIdle | handle | Candidate usable. |
| IdleAge | Exceeds MaxIdle | handle | Discard candidate (Close) per DOC-2/DOC-9; continue Get. |
| IdleAge | Negative or invalid config | reject (declaration at New) | Should have been caught at New; at runtime treat as expired. |
| WaitDelivery | Registered waiter present, resource ready | handle (delivers) | Hand resource to earliest waiter; dequeue request. |
| WaitDelivery | Requester abandoned / no waiter | ignore (documented) | Do not deliver; return resource to idle or close. |
| WaitDelivery | Pool released while delivering | reject | Deliver ErrClosed; do not hand out resource. |
| DrainDone | After detachment, all idle closed | handle | Release returns; Pool_Released. |
| DrainDone | Close error during drain | handle | Continue draining per DOC-12; report error; still reach Pool_Released. |
| UV-NewOmitted | Pool never constructed | UNSPECIFIED | Out of scope; component cannot observe. |
| UV-NewRepeated | Second New against same backend | handle (independent) | Each New yields isolated pool; document that accidental duplicate pools are not prevented. |
| UV-BadConfig | Nil config, negative/zero invalid cap, absent callbacks | reject (declared error) | ErrClosed-style config error from New; publish nothing. |
| UV-GetOmitted | No Get issued | UNSPECIFIED | No state effect. |
| UV-GetAgain | Second Get by same caller while first pending/held | handle | If below MaxActive, allow (pool has no caller identity); otherwise queue per DOC-4. |
| UV-AbandonGet | Caller abandons waiter | ignore (documented) | Waiter remains queued (no context support); document leak; later Put delivers to abandoned slot. |
| UV-LateGet | Get during/after Release | reject (declared error) | ErrClosed; no creation. |
| UV-ContendedGet | Put/Close changes availability between failed receive and decision | handle | Retry loop; admission consistent (no double-issue). |
| UV-WrongPoolGet | Get to wrong pool | handle | Served by that pool; pools have no global identity — document. |
| UV-ReturnMissing | Resource never returned | UNSPECIFIED | Leak; pool cannot detect; document. |
| UV-LatePut | Put during/after Release or after requester departure | ignore (documented) | Close resource; do not re-admit to released pool. |
| UV-LateClose | Close after Release or after Put selected overflow cleanup | ignore (documented) | Idempotent guard; no double-close of pooled entry. |
| UV-BadOwnership | Duplicate Put/Close, nil, typed nil, foreign resource | reject (declared error) | Refuse; no state corruption; document lack of ownership tracking. |
| UV-WrongPoolPut | Put/Close to wrong pool | reject (declared error) | Refuse or close orphan; document no cross-pool tracking. |
| UV-ReleaseOmitted | No Release | UNSPECIFIED | Resources remain; documented requirement on caller per DOC-12. |
| UV-ReleaseAgain | Repeat Release | ignore (documented) | Idempotent; second call after Released is no-op; concurrent second waits. |
| UV-WrongPoolRelease | Release wrong instance | handle (that instance) | Releases targeted instance only; document isolation. |
| UV-LateRead | Len during concurrent change or teardown | handle | Snapshot value; never panic; may be stale — document. |
| UV-FactoryFault | Factory error/panic/nil | reject | Propagate; do not count; recover from panic to protect pool. |
| UV-CloseFault | Close error/panic during expiry/overflow/drain | handle | Continue; report error; still free slot; recover panic. |
| UV-PingFault | Absent Ping, invalid result, panic, overlap with Release | reject (invalid → discard) | Treat as invalid connection; discard; during Release stop pinging. |
| UV-CallbackDelay | Callback stalls/re-enters Get/Put/Close/Release/Len | UNSPECIFIED | Requirement is silent; must not deadlock — document as required but unverified by prose. |
| P-01a | Get → Put same holder | handle | Checkout then return: resource re-enters idle or delivered to waiter per DOC-11. |
| P-01b | Put → Get | handle | Return then checkout: normal reuse cycle. |
| P-02a | Get → Close same resource | handle | Checkout then explicit destroy: count decremented; replacement created for next Get if needed. |
| P-02b | Close → Get | reject (Close on pooled) / handle (Get) | Closing a pooled resource refused; Get proceeds from remaining resources. |
| P-03a | Get → Release | handle | Release waits (or errors) for checked-out resources; per DOC-12 drains idle; in-flight Get must get ErrClosed or completed then pool released. |
| P-03b | Release → Get | reject (ErrClosed) | Get after Release refused. |
| P-04a | Put → Release | handle | Put resumes idle, Release then drains it via Close. |
| P-04b | Release → Put | ignore (documented) | Put after Release discarded (resource closed); no resurrection. |
| P-05a | Close → Release | handle | Explicit close decrements; Release drains remaining idle. |
| P-05b | Release → Close | ignore (documented) | Close after Release is no-op; resource already closed by drain. |
| P-06a | Len → Release | handle | Len snapshots before teardown; value stale afterwards. |
| P-06b | Release → Len | handle | Len returns 0 or remaining after release; no panic. |
| P-07a | Put → Close same resource, distinct actors | reject (documented ordering conflict) | Both returning and closing same resource is contradictory; second actor refused. |
| P-07b | Close → Put | reject | Put after explicit close refused; resource not re-admitted. |
| P-08a | PingResult → Release | handle | Result processed; then Release drains. |
| P-08b | Release → PingResult | ignore (documented) | Ping result for released resource discarded. |
| P-09a | FactoryResult → Release | handle | Creation completes; then Release includes it in drain. |
| P-09b | Release → FactoryResult | reject | Factory completion after release → close result immediately; do not admit. |
| P-10a | CloseResult → Release | handle | Close completes; then Release proceeds. |
| P-10b | Release → CloseResult | handle | Drain awaits close results; state consistent. |
| P-11a | Len → Put | handle | Len snapshots; Put returns resource; subsequent Len reflects change. |
| P-11b | Put → Len | handle | Len reflects returned resource (idle+checked-out). |
| P-12a | Len → Get | handle | Snapshot then checkout; Len value becomes stale by one. |
| P-12b | Get → Len | handle | Len reflects checkout. |
| P-13a | DirectPing → Release | handle | Health check then teardown; ping result consistent. |
| P-13b | Release → DirectPing | reject | Ping after release refused/ErrClosed. |
| P-14a | Len → Close | handle | Snapshot then explicit close decrements. |
| P-14b | Close → Len | handle | Len reflects decrement. |
| P-15a | DirectPing → Put same resource | handle | Ping checks resource; Put returns valid resource. |
| P-15b | Put → DirectPing | handle | Returned resource may be pinged later; consistent. |
| P-16a | DirectPing → Close same resource | reject (ordering conflict) | Closing while/during health check overlaps; close wins, ping discarded. |
| P-16b | Close → DirectPing | reject | Ping of closed resource refused/invalid. |

Coverage checklist

- [x] New
- [x] Get
- [x] Put
- [x] Close
- [x] Release
- [x] Len
- [x] DirectPing
- [x] FactoryResult
- [x] CloseResult
- [x] PingResult
- [x] IdleAge
- [x] WaitDelivery
- [x] DrainDone
- [x] UV-NewOmitted
- [x] UV-NewRepeated
- [x] UV-BadConfig
- [x] UV-GetOmitted
- [x] UV-GetAgain
- [x] UV-AbandonGet
- [x] UV-LateGet
- [x] UV-ContendedGet
- [x] UV-WrongPoolGet
- [x] UV-ReturnMissing
- [x] UV-LatePut
- [x] UV-LateClose
- [x] UV-BadOwnership
- [x] UV-WrongPoolPut
- [x] UV-ReleaseOmitted
- [x] UV-ReleaseAgain
- [x] UV-WrongPoolRelease
- [x] UV-LateRead
- [x] UV-FactoryFault
- [x] UV-CloseFault
- [x] UV-PingFault
- [x] UV-CallbackDelay
- [x] P-01a
- [x] P-01b
- [x] P-02a
- [x] P-02b
- [x] P-03a
- [x] P-03b
- [x] P-04a
- [x] P-04b
- [x] P-05a
- [x] P-05b
- [x] P-06a
- [x] P-06b
- [x] P-07a
- [x] P-07b
- [x] P-08a
- [x] P-08b
- [x] P-09a
- [x] P-09b
- [x] P-10a
- [x] P-10b
- [x] P-11a
- [x] P-11b
- [x] P-12a
- [x] P-12b
- [x] P-13a
- [x] P-13b
- [x] P-14a
- [x] P-14b
- [x] P-15a
- [x] P-15b
- [x] P-16a
- [x] P-16b
