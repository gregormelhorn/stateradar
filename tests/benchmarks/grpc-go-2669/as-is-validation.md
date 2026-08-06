# As-is validation — existing tests replayed through the model

Tests read-only from the v1.18.0 clone. Each scenario is walked through
`as-is.machine.mmd`; verdict states whether the model accepts the
observed event/state sequence.

| # | Test | Scenario walked | Model walk | Verdict |
|---|---|---|---|---|
| V-01 | clientconn_state_transition_test.go:48-148 `TestStateTransitions_SingleAddress` case 1 (server sends preface) | Connecting → Ready | Idle —E01→ Connecting_Dialing —E06→ Ready. Balancer notifications: Connecting, Ready | accepted (observed-in-tests clientconn_state_transition_test.go:60-83) |
| V-02 | same, case 2 (connection closed before preface) | Connecting → TransientFailure | Idle —E01→ Connecting_Dialing —E09/E07 (single addr, list exhausted)—E15→ TransientFailure_Backoff. Notifications: Connecting, TransientFailure | accepted (clientconn_state_transition_test.go:84-100) |
| V-03 | same, cases 3-4 (preface then close; server never sends preface) | Connecting → TransientFailure | as V-02, failure at preface wait (clientconn.go:1192-1200) | accepted (clientconn_state_transition_test.go:101-143) |
| V-04 | clientconn_state_transition_test.go:200-265 `TestStateTransitions_ReadyToTransientFailure` | Connecting → Ready → TransientFailure → Connecting | …Ready —E09→ TransientFailure_Backoff —E11 (noBackoff ⇒ ~0s? note: default backoff — timer Backoff(0)≈1s)→ Connecting_Dialing | accepted. Model highlights that the TF→Connecting hop waits `backoffFor` computed at clientconn.go:975 — with default backoff this is ≈1s even after a healthy connection died (Q-03 boundary case) |
| V-05 | clientconn_state_transition_test.go:269-359 `TestStateTransitions_TriesAllAddrsBeforeTransientFailure` | addr1 fails, addr2 succeeds; asserts NO TransientFailure between Connecting and Ready | Connecting_Dialing —E07 (next addr, no TF emitted, On mode)→ Connecting_Dialing —E06→ Ready | accepted. Confirms the On-mode "no per-address TF blip" behaviour that contradicts DOC-7 and the Hybrid path (Q-14) (observed-in-tests clientconn_state_transition_test.go:267-273) |
| V-06 | clientconn_state_transition_test.go:364-454 `TestStateTransitions_MultipleAddrsEntersReady` | Connecting → Ready → TransientFailure → Connecting with 2 addrs | as V-04; after E09 the loop breaks out of addrLoop (success path 1112-1114), TF at 1125, so no second-address attempt precedes TF | accepted |
| V-07 | clientconn_test.go:375-461 `TestCloseConnectionWhenServerPrefaceNotReceived` (On and Hybrid) | no preface within minConnectTimeout ⇒ client closes conn and redials; second conn with preface stays alive | Connecting_Dialing —UV03/UV04 (prefaceTimer fires, clientconn.go:1192-1195 / 1202-1213)→ E07 → E15 → TransientFailure_Backoff → E11 → Connecting_Dialing → E06 → Ready | accepted. Note the test drives `envconfig.RequireHandshake` directly (clientconn_test.go:388-389), so the env-parse defect Q-05 is invisible to it |
| V-08 | clientconn_test.go:463-506 `TestBackoffWhenNoServerPrefaceReceived` | retry intervals strictly increase over 3 cycles | TF_Backoff sleeps `Backoff(backoffIdx)` with `backoffIdx++` per timer fire (clientconn.go:1134-1137) | accepted — monotone under NAT-1 jitter caveat: the test tolerates jitter only because factor 1.6 > 1+0.2·2 does not hold for all pairs; flaky-by-jitter is a runtime concern (unverifiable-runtime), not a model error |
| V-09 | clientconn_test.go:923-959 `TestResetConnectBackoff` | dial fails once; backoffForever blocks retry; ResetConnectBackoff triggers immediate redial | TF_Backoff —E05→ Connecting_Dialing via close(resetBackoff) (clientconn.go:1291-1297, 1138-1139) | accepted |
| V-10 | clientconn_test.go:961-974 `TestBackoffCancel` | Close during backoff/dial does not leak the goroutine | TF_Backoff/Connecting_Dialing —E02→ Shutdown; loop exits at clientconn.go:1140-1142 or 982/1003 | accepted |
| V-11 | clientconn_test.go:977-1131 `TestUpdateAddresses_RetryFromFirstAddr` | UpdateAddresses while Connecting ⇒ next reconnect starts from the top of the list | Connecting_Dialing —E03/E17→ Shutdown (this ac; tryUpdateAddrs false clientconn.go:705-707, wrapper tears down and recreates, balancer_conn_wrappers.go:285-313); the *new* ac starts at addrs[0] | accepted — but only via the wrapper's replace-and-reconnect. The in-place mechanism `tryNextAddrFromStart` (clientconn.go:968,1060,1100) is dead code (Q-10) |
| V-12 | clientconn_test.go:850-876 `TestClientUpdatesParamsAfterGoAway` | GOAWAY too_many_pings doubles keepalive time | E08 handle: `adjustParams` (clientconn.go:954-964) then reconnect cycle | accepted |

No test scenario was found that the model cannot accept. No test
exercises: teardown racing dial completion (Q-01), ResetConnectBackoff
concurrent with a state change (Q-02 deadlock), the health-check
sub-states S3/S6 at addrConn level in clientconn tests (test/healthcheck_test.go
exercises them end-to-end; read-only, not replayed cell by cell here),
or `GRPC_GO_REQUIRE_HANDSHAKE=on` via the actual environment (Q-05).
