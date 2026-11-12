| event id | disposition | situation (requirement terms) | what happens |
|---|---|---|---|
| connect | `transition → CONNECTING_Attempting` on DISCONNECTED; `handle` (stays, no-op) on CONNECTING_Attempting / RECONNECTING_WaitingBackoff; `handle` (stays, no-op) on CONNECTED; `reject` on FAILED | R-01: fresh connect from DISCONNECTED starts attempt; already connecting/reconnecting or connected → no-op; FAILED is permanent (R-05) so connect is a declared refusal | starts attempt; duplicate/overlapping connect returns without side effect; on FAILED raises/refuses, no retry |
| disconnect | `handle` (stays) on DISCONNECTED; `transition → DISCONNECTED_Cancelled` on CONNECTING_Attempting / RECONNECTING_WaitingBackoff; `transition → DISCONNECTED_Idle` on CONNECTED; `handle` (stays, documented no-op) on FAILED | R-02/R-06: calls arriving while connecting cancel and return DISCONNECTED; when already disconnected no-op; FAILED permanent per R-05 — treat as documented ignore, not a transition | cancels pending attempt/backoff timer, returns DISCONNECTED, no error on redundant disconnect |
| connection_succeeds | `transition → CONNECTED_Stable` from CONNECTING_Attempting / RECONNECTING_Attempting | R-03: attempt completes successfully; retry counter reset to zero | enters CONNECTED, retry_count := 0 |
| connection_fails | `transition → RECONNECTING_WaitingBackoff` (with retry_count < max_retries); `transition → FAILED_Terminal` (retry_count >= max_retries) | R-04 retry with exponential backoff + jitter (R-09); R-05 exhaustion → FAILED permanently | increments retry_count, schedules backoff; at limit goes FAILED, no more attempts |
| connection_timeout | `transition → RECONNECTING_WaitingBackoff` (with retry_count < max_retries); `transition → FAILED_Terminal` (retry_count >= max_retries) | R-07: timeout is treated as failure and retried; consumed by the retry path (same as connection_fails) | identical to connection_fails path; timeout does not get its own retry budget |
| backoff_elapsed | `transition → RECONNECTING_Attempting` from RECONNECTING_WaitingBackoff; `ignore (documented)` if arriving in any non-WaitingBackoff state | R-04/R-09: jittered backoff completion just re-attempts; a stale timer after cancellation must not start an attempt | starts next attempt only if still in RECONNECTING_WaitingBackoff; fired timer after disconnect is dropped |
| max_retries_exhausted | `transition → FAILED_Terminal` from CONNECTING_Attempting / RECONNECTING_Attempting / RECONNECTING_WaitingBackoff | R-05: retry limit reached → FAILED, permanent | enters FAILED; all further connect ignored/rejected, no attempts |
| UV-connect-loss | `ignore (accidental)` — nothing observable; no transition | call never arrives; component stays in whatever state it was (typically DISCONNECTED_Idle) | nothing happens; no guard fired because no event |
| UV-connect-delay | `transition → CONNECTING_Attempting` if state at arrival is DISCONNECTED; `handle` (no-op) if CONNECTING/CONNECTED; `reject` if FAILED | same gate as connect, but evaluated at arrival time: delayed call arriving after a disconnect that already happened → start attempt (legitimate late request per R-01) | behaves exactly as a fresh connect at arrival; delayed connect is not distinguished from a real one |
| UV-connect-duplication | `handle` (no-op, documented) for the duplicate on CONNECTING_Attempting / CONNECTED; `reject` on FAILED | R-01 idempotent guard: second connect while connecting/connected is a no-op; on FAILED it is refused like the first | only one attempt exists; duplicate returns without side effect |
| UV-connect-out-of-order | `transition → CONNECTING_Attempting` from DISCONNECTED (late connect after a later disconnect already processed); `handle` (no-op) if currently CONNECTING/CONNECTED; `reject` on FAILED | the disconnect already took effect and left DISCONNECTED; the older connect is still a valid initiation per R-01 — ordering is not a reason to refuse | a new attempt starts; the component does not attempt to "roll back" the disconnect |
| UV-connect-contradiction | `UNSPECIFIED` for the interleaving outcome beyond the last-processed-wins rule: if connect is processed last → as connect row; if disconnect processed last → result is DISCONNECTED and the connect is a no-op on arrival | R-01/R-02/R-06 do not define a tie-break for near-simultaneous calls; only per-call guards apply, evaluated in processing order | outcome determined solely by event processing order; component cannot detect the race |
| UV-connect-commission | `handle` exactly as a legitimate connect (identical gate) | spurious connect with no caller trigger is indistinguishable from a real connect; R-01 gate applies as-is; this is a documented analysability limit | may initiate an attempt the operator never requested; guard on CONNECTING/CONNECTED prevents a second attempt; on FAILED rejected |
| UV-connect-value | `ignore (documented)` — cannot occur as a payload fault | connect() takes no arguments; wrong-instance call is a caller error, outside R-01..R-09 | no handling defined; treated as caller bug, not an event the component processes |
| UV-disconnect-loss | `ignore (accidental)` — nothing observable | call never arrives; component remains connected/connecting as if no disconnect was requested (R-02 never invoked) | no state change; connection persists |
| UV-disconnect-delay | as disconnect row, evaluated at arrival: on CONNECTING/RECONNECTING → cancel to DISCONNECTED; on CONNECTED → DISCONNECTED; on DISCONNECTED → no-op; on FAILED → documented no-op | R-02/R-06 apply to the late-arriving call | if a connection succeeded in the meantime, the delayed disconnect tears it down (last-processed-wins) |
| UV-disconnect-duplication | `handle` (stays, documented no-op) for the second on DISCONNECTED; first call takes the normal transition otherwise | R-02 has no guard, but redundancy on DISCONNECTED is harmless | second disconnect returns without side effect; no error emitted |
| UV-disconnect-out-of-order | as disconnect row: `transition → DISCONNECTED` from CONNECTED or from CONNECTING/RECONNECTING (cancels the later-started attempt); no-op on DISCONNECTED | a disconnect sent earlier but delivered after a later connect is still a valid disconnect request per R-02 — it cancels the now-current attempt/connection | the newer connection/attempt is torn down; R-06 cancellation path used |
| UV-disconnect-contradiction | `UNSPECIFIED` for tie-break beyond processing order: if disconnect processed last → DISCONNECTED (as disconnect row); if connect processed last and a guard permits → attempt started | R-02/R-06 give disconnect no guard and no race arbitration against connect | final state depends on processing order only; both orders are individually well-defined, the pair's winner is not |
| UV-disconnect-commission | `handle` exactly as a legitimate disconnect | spurious disconnect is indistinguishable from an operator disconnect; R-02 "always processes" means it is honoured | may tear down a live connection the operator never asked to drop; documented analysability limit |
| UV-disconnect-value | `ignore (documented)` — cannot occur as a payload fault | disconnect() takes no arguments; wrong-instance is caller error | no handling defined |
| connect ∘ disconnect (connect then disconnect) | connect: `transition → CONNECTING_Attempting`; then disconnect: `transition → DISCONNECTED_Cancelled` | R-01 then R-06: disconnect during CONNECTING cancels the attempt | attempt aborted, backoff/timer cancelled, DISCONNECTED |
| disconnect ∘ connect (disconnect then connect) | disconnect: `transition → DISCONNECTED` (or no-op if already); then connect: `transition → CONNECTING_Attempting` | R-02 then R-01: after disconnecting, a fresh connect is a legitimate initiation | new attempt started from DISCONNECTED |
| connection_succeeds ∘ disconnect (succeeds then disconnect) | succeeds: `transition → CONNECTED_Stable` (retry reset); then disconnect: `transition → DISCONNECTED_Idle` | R-03 then R-02 | connected then gracefully torn down |
| disconnect ∘ connection_succeeds (disconnect during attempt, success arrives late) | disconnect: cancel → DISCONNECTED; then late success: `ignore (documented)` — stale attempt outcome | R-06 cancels the attempt; a completion for a cancelled attempt must not resurrect CONNECTED; R-02 places component in DISCONNECTED | the late success is discarded; state remains DISCONNECTED; retry counter untouched by the stale event |
| connection_fails/connection_timeout ∘ disconnect | failure: `transition → RECONNECTING_WaitingBackoff`; then disconnect: `transition → DISCONNECTED_Cancelled` (cancels timer) | R-04 then R-06 | backoff cancelled, DISCONNECTED, no retry |
| disconnect ∘ connection_fails/connection_timeout (late failure after cancel) | after cancel, the failure outcome of the abandoned attempt is `ignore (documented)` — must not schedule a backoff or increment retry_count for a cancelled attempt | R-06 cancel; R-04 retry only applies to a live attempt | stale failure dropped; no backoff timer created; state stays DISCONNECTED |
| backoff_elapsed ∘ disconnect | backoff: `transition → RECONNECTING_Attempting`; then disconnect: cancel → DISCONNECTED | R-04 then R-06 | attempt cancelled, DISCONNECTED |
| disconnect ∘ backoff_elapsed (stale timer after cancel) | disconnect → DISCONNECTED; then timer: `ignore (documented)` | R-06 cancelled the pending attempt; a timer fired after cancellation must not start an attempt | no attempt; state stays DISCONNECTED |
| max_retries_exhausted ∘ disconnect | exhaustion: `transition → FAILED_Terminal`; then disconnect: `handle` (stays, documented no-op) | R-05 permanent FAILED; R-02 has no path out of FAILED | remains FAILED |
| disconnect ∘ max_retries_exhausted | disconnect → DISCONNECTED_Cancelled; then exhaustion (late) is `ignore (documented)` unless exhaustion is evaluated only on a live retry | R-06 cancelled the attempt so the retry budget is no longer running; R-05 applies to an in-progress retry cycle | remains DISCONNECTED; stale exhaustion does not force FAILED (see open point below) |
| connect ∘ connect (UV-connect-duplication pair) | first: `transition → CONNECTING_Attempting`; second: `handle` (no-op) | R-01 idempotent guard | one attempt only |
| disconnect ∘ disconnect (UV-disconnect-duplication pair) | first: per-state transition to DISCONNECTED; second: `handle` (no-op) | R-02 | single teardown |
| connect ∘ connect after reconnect (read as connect from RECONNECTING_Attempting) | `handle` (no-op) | R-01: already connecting (including reconnecting) → no-op | attempt continues unchanged |
| connect to FAILED ∘ disconnect (FAILED then disconnect) | connect: `reject`; disconnect: `handle` (stays, documented no-op) | R-05 permanence; R-02 cannot leave FAILED because R-05 overrides | remains FAILED; connect refusal is the only observable signal |

`assumed-state:` CONNECTING_Attempting — a connect attempt is in flight (R-01, R-03, R-07 boundary; requirements name no separate CONNECTING sub-state). `assumed-state:` RECONNECTING_WaitingBackoff — a failed/timed-out attempt is awaiting a jittered backoff before the next try (R-04, R-09). `assumed-state:` RECONNECTING_Attempting — a retry attempt is in flight after a backoff (R-04). `assumed-state:` CONNECTED_Stable — connected and retry counter already reset; min_uptime (R-08) only qualifies "stable" and introduces no additional transition or guard. `assumed-state:` FAILED_Terminal — permanent failure state (R-05), named FAILED in requirements; it is the same public state, listed here only to fix the "terminal / no transitions out" condition. `assumed-state:` DISCONNECTED_Idle / DISCONNECTED_Cancelled — the requirements' DISCONNECTED state, split only to distinguish the "same state, different cause" paths reachable via R-02 (idle already-disconnected vs cancelled-pending-attempt); both are the public DISCONNECTED state and are not distinguishable through the API.

Open points (labelled, not looked up): (1) Late outcome events (`connection_succeeds`, `connection_fails`, `connection_timeout`, `backoff_elapsed`, `max_retries_exhausted`) carry no attempt identity in the catalogue payloads, so "ignore stale outcome after cancel" is asserted from requirement intent (R-02/R-06) rather than from an observable discriminator; a blind pass cannot confirm whether the component distinguishes them. (2) The `disconnect ∘ max_retries_exhausted` ordering in FAILED vs DISCONNECTED depends on whether exhaustion is evaluated only over a live retry cycle — requirements do not say. (3) `connect` on FAILED is declared `reject` because R-05 says "no further connection attempts are made" and the catalogue annotation says the FAILED guard raises; whether "raises" is the public refusal signal is an implementation detail not visible here. (4) R-08 min_uptime and R-09 jitter scope (per-device vs per-instance) do not alter any disposition, so no state was invented for them.

Coverage checklist:
- [x] connect
- [x] disconnect
- [x] connection_succeeds
- [x] connection_fails
- [x] connection_timeout
- [x] backoff_elapsed
- [x] max_retries_exhausted
- [x] UV-connect-loss
- [x] UV-connect-delay
- [x] UV-connect-duplication
- [x] UV-connect-out-of-order
- [x] UV-connect-contradiction
- [x] UV-connect-commission
- [x] UV-connect-value
- [x] UV-disconnect-loss
- [x] UV-disconnect-delay
- [x] UV-disconnect-duplication
- [x] UV-disconnect-out-of-order
- [x] UV-disconnect-contradiction
- [x] UV-disconnect-commission
- [x] UV-disconnect-value
- [x] connect ∘ disconnect
- [x] disconnect ∘ connect
- [x] connection_succeeds ∘ disconnect
- [x] disconnect ∘ connection_succeeds
- [x] connection_fails ∘ disconnect
- [x] disconnect ∘ connection_fails
- [x] connection_timeout ∘ disconnect
- [x] disconnect ∘ connection_timeout
- [x] backoff_elapsed ∘ disconnect
- [x] disconnect ∘ backoff_elapsed
- [x] max_retries_exhausted ∘ disconnect
- [x] disconnect ∘ max_retries_exhausted
- [x] connect ∘ connect
- [x] disconnect ∘ disconnect