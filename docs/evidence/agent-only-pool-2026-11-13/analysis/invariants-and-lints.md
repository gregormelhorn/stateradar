# channelPool — Invariants and lint findings (Step 5)

Notation as in `disposition-matrix.md`: i idle count, M MaxIdle, o openingConns, X MaxCap, w waiting Gets, T IdleTimeout.

## NAT — assumptions about the environment

| Id | Predicate | Provenance | Status |
|---|---|---|---|
| NAT-1 | Factory returns either (conn ≠ nil, nil) or (_, err ≠ nil) and never (conn ≠ nil, err ≠ nil) or (nil, nil) | inferred (Go convention); no contract text: channel.go:25-26, README.md:21 | unconfirmed → Q-07 |
| NAT-2 | Factory, Close callback and Ping return in bounded time | inferred; no contract text | unconfirmed → Q-08 |
| NAT-3 | Factory and Close callback never call methods of the same pool | inferred; no contract text (README.md:17-62 states no reentrancy rule) | unconfirmed → Q-08 |
| NAT-4 | Every conn obtained from Get is given back exactly once, by Put (still usable) or by Close (to destroy), and not after Release | explicit-requirement for Put only: README.md:52 ("Put the connection back into the connection pool, when the connection is no longer in use"); "exactly once" and "not after Release" are inferred | partly documented → Q-09, Q-06 |
| NAT-5 | Callers pass only conns that this pool created | inferred | unconfirmed → Q-09 |
| NAT-6 | `time.Now()` values carry a monotonic reading and `Time.Before` compares it, so wall-clock jumps do not affect idle-age decisions | Go standard library `time` package documentation (not repository text) | assumed |
| NAT-7 | Config after validation: 0 ≤ InitialCap ≤ MaxIdle ≤ MaxCap (channel.go:59); Factory and Close callback non-nil (channel.go:62-67) | observed-in-code | holds by construction |

### NAT-SYS — multi-instance assumption

| Id | Predicate | Use |
|---|---|---|
| NAT-SYS-1 | N > 1 pools (in one or many processes) share one server. When the server restarts or drops connections, every pool's idle conns die at the same moment, and pools started together (deploy) pre-fill InitialCap conns at the same moment, so their idle timestamps and expiries line up. | adversarial traces M-01..M-03 |

## SYS — obligations, checked state by state

Legend: ✓ holds in that state (under the NAT assumptions); ✗ violated (reachable); — not applicable.

| Id | Predicate | Source |
|---|---|---|
| SYS-1 | o equals the number of live conns the pool created and not yet destroyed, and o ≤ X | DOC-8 (README.md:30, channel.go:21) |
| SYS-2 | i ≤ M | DOC-9 (channel.go:23) |
| SYS-3 | w ≥ 1 ⇒ i = 0 ∧ o ≥ X (no Get waits while an idle conn or free capacity exists) | inferred from DOC-4 (README.md:15: waiting happens "when the connection pool is full") |
| SYS-4 | Released ⇒ w = 0 (no Get stays blocked after Release) | inferred from DOC-6 / DOC-13 (README.md:55, pool.go:6) |
| SYS-5 | After Release, every conn the pool created ends closed (idle ones by Release, checked-out ones when given back) | DOC-6 (README.md:55 "Release all connections"), DOC-14 (channel.go:201) |
| SYS-6 | T > 0 ⇒ Get never returns a conn whose idle age exceeds T | DOC-2, DOC-11 |
| SYS-7 | Ping configured ⇒ every conn Get returns from the pool's store or a hand-off passed Ping after its last idle period | DOC-3 (README.md:14) |
| SYS-8 | A conn is held by at most one caller at a time | inferred (pool semantics) |
| SYS-9 | o ≥ InitialCap while the pool is open (InitialCap as minimum) | DOC-10 (channel.go:19) — contradicted by README.md:30 ("Initialize the number of connections") |
| SYS-10 | A waiting Get returns once a conn becomes available or capacity frees while the pool is open (progress) | inferred from DOC-4 |

| State | SYS-1 | SYS-2 | SYS-3 | SYS-4 | SYS-5 | SYS-6 | SYS-7 | SYS-8 | SYS-9 | SYS-10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Open_Idle | ✓ (✗ under UV-03/04/05/07/08) | ✓ | ✓ (w = 0) | — | — | ✓ | ✓ | ✓ (✗ under UV-03) | ✗ (expiry/Close lower o, never replenished) | — |
| Open_IdleFull | ✓ (✗ under UV-03/04/05/07/08) | ✓ | ✓ | — | — | ✓ | ✓ | ✓ (✗ under UV-03) | ✗ | — |
| Open_Empty_BelowCap | ✓ (✗ under UV-04/05/08) | ✓ | ✓ | — | — | ✓ | ✓ | ✓ | ✗ (InitialCap = 0 trivially ✓) | — |
| Open_Empty_AtCap | ✓ (✗ under UV-04/05/08) | ✓ | ✓ | — | — | ✓ | ✓ | ✓ | ✓ when X ≥ InitialCap | — |
| Open_Waiting | ✓ | ✓ | ✓ | — | — | ✓ (hand-off checks age, channel.go:142) | ✗ hand-off skips Ping (channel.go:141-148) | ✓ | ✓ | ✓ only while Puts keep coming; no bound |
| Open_Waiting_BelowCap | ✓ | ✓ | **✗** (o < X) | — | — | ✓ | ✗ | ✓ | ✗ possible | **✗** (capacity free, waiters blocked) |
| Open_Waiting_IdleStranded | ✓ | ✓ | **✗** (i ≥ 1) | — | — | ✓ | ✗ | ✓ | ✓ | **✗** (idle conn exists, waiters blocked) |
| Open_Creating | ✓ (o+1 happens after Factory returns) | ✓ | ✓ unless entered from Open_Waiting_BelowCap | — | — | ✓ | ✓ | ✓ | ✗ possible | — |
| Released | — (o frozen, not meaningful) | ✓ (i = 0) | — | **✗** when entered from Open_Waiting* | **✗** Put/Close after Release close nothing (channel.go:176, channel.go:208-209) | — | — | — | — | **✗** blocked Gets never return |

Violations (findings): SYS-1 under caller misuse (→ Q-09) and UV-14 (→ Q-07); SYS-3 and SYS-10 in Open_Waiting_BelowCap (→ Q-03) and Open_Waiting_IdleStranded (→ Q-04); SYS-4 (→ Q-05); SYS-5 (→ Q-06); SYS-7 on the hand-off path (→ Q-13); SYS-8 under UV-03 (→ Q-09); SYS-9 (→ Q-14).

## Doctrine mapping

<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 DOC-5 DOC-6 DOC-7 DOC-8 DOC-9 DOC-10 DOC-11 DOC-12 DOC-13 DOC-14 DOC-15 DOC-16 DOC-17 DOC-18 -->

| DOC | mapping | target |
|---|---|---|
| DOC-1 | structural | connections are opaque values: no cell inspects them, the catalogue gate annotations state that identity and content are never examined (enforced by the event definitions in event-catalogue.md) |
| DOC-2 | cell | Open_Idle x IDLE_TIMEOUT |
| DOC-3 | invariant | SYS-7 |
| DOC-4 | cell | Open_Empty_AtCap x GET |
| DOC-5 | constraint | NAT-4 |
| DOC-6 | invariant | SYS-5 |
| DOC-7 | cell | Open_Idle x LEN |
| DOC-8 | invariant | SYS-1 |
| DOC-9 | invariant | SYS-2 |
| DOC-10 | invariant | SYS-9 |
| DOC-11 | guard | G-03 |
| DOC-12 | cell | Open_Waiting x GET |
| DOC-13 | cell | Released x GET |
| DOC-14 | cell | Released x CLOSE |
| DOC-15 | cell | Open_Idle x GET |
| DOC-16 | cell | Open_Empty_BelowCap x PUT |
| DOC-17 | rejected | implementation remark about efficiency (channels); prescribes no observable behaviour |
| DOC-18 | rejected | attribution to fatih/pool; prescribes no behaviour of this component |

## PA-22: requirements against cells

| DOC | Cell / target | Disposition there | Verdict |
|---|---|---|---|
| DOC-2 | Open_Idle x IDLE_TIMEOUT (and Open_IdleFull, Open_Waiting_IdleStranded, Open_Creating) | ignore (accidental) → Q-12 | **violated as to timing**: the README says timed-out conns are closed and discarded, the code does that only when a Get dequeues them; until then they stay open (as-is test T13). The discard itself is implemented (G-03, Open_Idle x GET). |
| DOC-3 | SYS-7 | ✗ on hand-off | **violated** on the waiter path → Q-13 |
| DOC-4 | Open_Empty_AtCap x GET | transition → Open_Waiting | implemented; "like the go db connection pool" (cancellable, bounded waits) is not → Q-02 |
| DOC-6 | SYS-5; Released x PUT / CLOSE | ignore (accidental) → Q-06 | **violated** for checked-out conns |
| DOC-7 | Open_Idle x LEN | handle (idle count) | ambiguous wording → Q-15 |
| DOC-8 | SYS-1 | ✗ under misuse | holds only under NAT-4/NAT-5 → Q-09 |
| DOC-10 | SYS-9 | ✗ | contradicts README.md:30 → Q-14 |
| DOC-12 | Open_Waiting x GET (the error a full pool would report) | handle (wait) | **unimplemented**: the error is declared, the only return of it is unreachable (G-07) → Q-01 |
| DOC-13 | Released x GET | reject (ErrClosed) | implemented |
| DOC-14 | Released x CLOSE | ignore (accidental) → Q-06 | **violated**: Close closes nothing after Release |
| DOC-15, DOC-16 | Open_Idle x GET, Open_Empty_BelowCap x PUT | handle / transition | implemented |

## Lint findings (Step-5 checklist)

| # | Checklist item | Finding | Provenance | → |
|---|---|---|---|---|
| L-01 | waiting states without timeout | Open_Waiting, Open_Waiting_BelowCap, Open_Waiting_IdleStranded: a waiting Get blocks with no timeout; the `waitTimeOut` field is declared and never used. Open_Creating: Factory runs under the mutex with no timeout. | channel.go:137 ("ret, ok := <-req"); channel.go:46; channel.go:154 | Q-02, Q-08 |
| L-02 | retries without a maximum | none: the Get loop retries only after discarding a conn (each retry consumes an idle conn or ends in create/wait); Factory errors are not retried | channel.go:119, channel.go:126, channel.go:145 | — |
| L-03 | invoked external operations without an explicit failure outcome | Close-callback errors are discarded on Get's discard path and in Release; a Factory result with both a conn and an error drops the conn; no outcome for hanging callbacks | channel.go:118, channel.go:241, channel.go:155-157 | Q-17, Q-07, Q-08 |
| L-04 | externally initiated operations without cancellation handling | Get cannot be cancelled (no context, no deadline) | channel.go:103 | Q-02 |
| L-05 | terminal or error states without documented meaning | Released: only Get's outcome is documented (ErrClosed, pool.go:6); Put, Close, Ping after Release are not. `ErrMaxActiveConnReached` is documented but unreachable. | pool.go:6; channel.go:13-14; channel.go:138-139 | Q-06, Q-11, Q-01 |
| L-06 | undefined startup or shutdown behaviour | Shutdown with waiting Gets, with checked-out conns, or with a Factory call in flight is undefined (P-02, P-03, P-06). Startup accepts MaxCap = 0, which makes every Get wait forever (G-01 probe). | channel.go:224-243; channel.go:59 | Q-05, Q-06, Q-01 |
| L-07 | unbounded queues or buffers, unhandled overload | the waiter list grows without bound (append, no limit); at MaxCap every extra Get parks a goroutine forever if no Put comes | channel.go:135 | Q-02 |
| L-08 | synchronized reset points | no external event resets a limit or delay (the pool has no backoff or retry counter). Related aggregate risk: conns pre-filled together (InitialCap) or re-created together after a server restart carry the same timestamp and expire together; the next Gets re-dial together with no jitter, and Factory errors are not backed off | channel.go:82-89; channel.go:116; channel.go:155-157 | Q-18 |
| L-09 | lifecycle disagreement (PA-21) | `openingConns` and the waiter list are shared by the caller lifecycle (checked-out conns, waiting Gets) and the pool lifecycle (Release). Release, the pool's terminal transition, triggers no cleanup in the caller tracks: waiting Gets stay blocked, checked-out conns are never closed. Close (capacity freed) triggers no transition in the waiter track. | channel.go:224-243; channel.go:202-213 | Q-05, Q-06, Q-03 |
| L-10 | dual ownership cleanup (PA-23) | a conn has two explicit end paths, Put (back to the pool, maybe closed when full) and Close (destroy), plus Release's drain. Nothing enforces exactly one logical release per conn: double Close, Close after Put, and racing Put/Close each decrement or store it twice | channel.go:167-213 | Q-09 |
| L-11 | async cancellation isolation (PA-24) | the waiter's one-slot channel stays in the pool's list (sender side) with no way for the receiver to leave; the receiver side cannot cancel, and the pool's terminal event (Release) sends no synchronization to it | channel.go:134-137; channel.go:224-243 | Q-05, Q-02 |
| L-12 | user-model gap | (a) Open_Creating `defer (queued)` cells: Put, Close, Len, Release and every Get block while another goroutine's Factory runs — visible only under concurrency (→ Q-19). (b) Barging: in Open_Waiting_BelowCap and Open_Waiting_IdleStranded a new Get is served before older waiters (→ Q-03, Q-04). (c) Released x GET reject for a Get that started before Release (P-02b) and the wait-forever outcome of the same race at MaxCap (→ Q-05). | matrix cells cited there | Q-19, Q-03, Q-04, Q-05 |
