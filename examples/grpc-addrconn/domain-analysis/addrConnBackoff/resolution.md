# Evaluation decisions for Q-01 through Q-16

All 16 questions are ANSWERED under the owner delegation quoted in each DR.
Answers do not mean implementation complete. DR-001 now has a separately tested late-completion evaluation patch with both
guards; its broad conformance status is partial. Other implementation obligations
remain pending. The F-09 slice covers only local backoff cleanup.
The frozen historical analysis remains unchanged.

## Q-01 — Prevent resurrection and dispose late transports

**Decision (DR-001):** Guard both transport publication and connectivity writes against Shutdown. A late successful transport must be closed outside ac.mu, without publishing it or notifying Ready.

**Rationale:** Both guards are needed: suppressing a notification alone does not release the returned resource.

Status: ANSWERED; implementation partial. Both guards and the idle-transport late-completion scenarios are tested in `../../late-completion/`; full component conformance remains pending.

Evidence: clientconn.go:1027 ("ac.mu.Lock()"); clientconn.go:935 ("func (ac *addrConn) updateConnectivityState")

## Q-02 — Remove cross-object lock inversion

**Decision (DR-002):** Snapshot cc.conns under cc.mu, release that lock, then reset each addrConn. Never acquire an ac lock while holding cc.mu; current ac-to-cc calls remain ordered. Recheck Shutdown in reset.

**Rationale:** A snapshot plus terminal no-op closes the reset/state-update deadlock without making the public API unsafe.

Status: ANSWERED; implementation pending.

Evidence: clientconn.go:844 ("cc.mu.Lock()"); clientconn.go:949 ("ac.cc.handleSubConnStateChange")

## Q-03 — Honor accepted connections and reset generations

**Decision (DR-003):** A SETTINGS-confirmed successful connection starts the next reconnect attempt without the stale pre-success delay. Explicit reset zeroes the failure history and advances a generation; the upcoming or current backoff wait must observe that generation atomically. A reset before wait registration cannot be lost. Subsequent failed attempts resume normal jittered backoff.

**Rationale:** Recomputing a duration alone does not close the channel-generation lost-wakeup window. Success and explicit reset are distinct triggers.

Status: ANSWERED; implementation pending.

Evidence: clientconn.go:975 ("backoffFor := ac.dopts.bs.Backoff(ac.backoffIdx)"); clientconn.go:1128 ("b := ac.resetBackoff"); clientconn.go:1294 ("ac.backoffIdx = 0")

## Q-04 — Require SETTINGS for success-based backoff reset

**Decision (DR-004):** Across On, Hybrid and Off modes, reset failure history only after SETTINGS confirms server acceptance, or on explicit ResetConnectBackoff. Keep Off admission compatibility separately documented.

**Rationale:** TCP acceptance is not proof that the server accepted gRPC. This does not silently remove Off mode.

Status: ANSWERED; implementation pending.

Evidence: clientconn.go:1073 ("if reqHandshake == envconfig.RequireHandshakeHybrid"); clientconn.go:1112 ("ac.backoffIdx = 0")

## Q-05 — Parse explicit on as On

**Decision (DR-005):** The literal on selects RequireHandshakeOn, as does the existing default. Off and Hybrid retain their explicit mappings. Cover the actual environment parser in a fresh process.

**Rationale:** Tests that directly assign the enum cannot detect the parser defect. The owning component is envconfig.

Status: ANSWERED; implementation pending.

Evidence: internal/envconfig/envconfig.go:61 ("case "on":"); internal/envconfig/envconfig.go:63 ("RequireHandshake = RequireHandshakeOn")

## Q-06 — Assign IDLE policy to ClientConn

**Decision (DR-006):** Treat idle timeout and channel-level GOAWAY/no-RPC idleness as ClientConn responsibilities. Keep an explicit model link and an unimplemented owning-model work item; do not add addrConn idle timers to satisfy a channel requirement.

**Rationale:** Moving the obligation to its actual owner does not claim it is implemented there.

Status: ANSWERED; implementation pending.

Evidence: clientconn.go:670 ("func (ac *addrConn) connect() error")

## Q-07 — Allow health recovery over an existing transport

**Decision (DR-007):** Allow TransientFailure_ServerUnhealthy directly to Ready on a valid current-generation SERVING report. No artificial Connecting notification. Document the health extension to the older transition table.

**Rationale:** No network reconnection occurred; a synthetic Connecting step would misrepresent the operation.

Status: ANSWERED; implementation pending.

Evidence: clientconn.go:1262 ("if ac.transport != newTr"); clientconn.go:1270 ("ac.updateConnectivityState(connectivity.Ready)")

## Q-08 — Separate missing first health status from stable watches

**Decision (DR-008):** Bound the first valid health response using a configurable first-verdict timeout, defaulting in this evaluation to the existing getMinConnectTimeout() duration. Expiry cancels that health attempt, releases its transport and enters ordinary reconnect/backoff. After a valid SERVING or NOT_SERVING status, silence alone is permitted; no heartbeat timeout or forced reconnect for stable NOT_SERVING. Keep the existing health client retry/backoff for ordinary stream failures. An unexpected terminal helper return while its context is live is a monitoring failure: remove Ready eligibility and restart monitoring with bounded backoff and the first-verdict timeout. UNIMPLEMENTED retains the explicitly documented healthy fallback; canceled or stale generations cannot change the active instance.

**Rationale:** The callee retries ordinary stream errors itself. Blindly recycling on each stream error duplicates policy; stable watch silence is not the same as a missing initial verdict. New timeout and unexpected-return behavior are evaluation policy, not a claimed upstream requirement.

Status: ANSWERED; implementation pending.

Evidence: health/client.go:54 ("func clientHealthCheck"); health/client.go:91 ("if status.Code(err) == codes.Unimplemented"); health/client.go:97 ("if err != nil"); clientconn.go:1275 ("err := ac.cc.dopts.healthCheckFunc")

## Q-09 — Ignore mutations on a terminal addrConn

**Decision (DR-009):** After Shutdown, resetConnectBackoff is a no-op. tryUpdateAddrs returns true without changing the address list, preserving the wrapper convention that an update to a retired instance does not recreate it. connect continues returning errConnClosing. The wrapper handles an empty address list as teardown; direct empty updates to live instances are rejected without mutation.

**Rationale:** Returning false is not sufficient to promise recreation: the wrapper explicitly declines replacement when the old state is Shutdown. Preserve terminality without mutating dead context.

Status: ANSWERED; implementation pending.

Evidence: clientconn.go:698 ("if ac.state == connectivity.Shutdown"); balancer_conn_wrappers.go:299 ("if acState == connectivity.Shutdown"); balancer_conn_wrappers.go:281 ("if len(addrs) <= 0")

## Q-10 — Remove the unused restart signal

**Decision (DR-010):** Remove tryNextAddrFromStart and its unreachable branches after verifying that no producer fires it. Preserve address-update replacement and its tested restart-from-first-address behavior.

**Rationale:** An unproduced signal is not a useful alternate mechanism. Do not introduce in-place restart semantics as cleanup.

Status: ANSWERED; implementation pending.

Evidence: clientconn.go:968 ("tryNextAddrFromStart := grpcsync.NewEvent()"); clientconn.go:1060 ("if tryNextAddrFromStart.HasFired()")

## Q-11 — Give local teardown explicit resource ownership

**Decision (DR-011):** Local teardown always cancels its owned dial/backoff/health activity, independently of parent ClientConn cancellation. A canceled backoff worker eventually exits and stops its timer; no fixed completion latency is promised. If a transport exists, detach it under lock; call GracefulClose for errConnDrain and Close for non-drain reasons outside ac.mu. Graceful drain may retain active RPCs; abrupt close terminates them. Late transports follow DR-001.

**Rationale:** The transport lifetime is derived from cc.ctx, so the old NAT-5 inference from ac.cancel is invalid. Distinguish graceful drain from abrupt teardown and never call reentrant close callbacks under ac.mu. The current no-transport backoff path already satisfies this contract and is the F-09 slice.

Status: ANSWERED; implementation pending.

Evidence: clientconn.go:1187 ("transport.NewClientTransport(connectCtx, ac.cc.ctx"); clientconn.go:1337 ("ac.cancel()"); clientconn.go:1140 ("case <-acctx.Done():"); internal/transport/http2_client.go:795 ("func (t *http2Client) GracefulClose")

## Q-12 — Scope attempt cleanup to one attempt

**Decision (DR-012):** Restructure per-attempt ownership so its cancel is released on every exit path at the end of that attempt; use an attempt-scoped helper/defer or equivalently proven explicit cleanup. Do not accumulate deferred closures in the long-lived reconnect loop.

**Rationale:** A helper with bounded lifetime is easier to audit than deleting the defer while assuming every early return is covered. Active health monitoring retains ownership until that attempt ends.

Status: ANSWERED; implementation pending.

Evidence: clientconn.go:1012 ("hctx, hcancel := context.WithCancel(ac.ctx)"); clientconn.go:1013 ("defer hcancel()")

## Q-13 — Keep explicit resets immediate and document herd risk

**Decision (DR-013):** Do not add hidden jitter to the immediate ResetConnectBackoff API. Retain ordinary backoff jitter; document fleet reset coordination and rate limiting as operator/caller responsibilities.

**Rationale:** Changing immediate reset timing would silently change the public promise. No claim that all synchronized retry risk is eliminated.

Status: ANSWERED; implementation pending.

Evidence: clientconn.go:833 ("ResetConnectBackoff wakes up all subchannels"); internal/backoff/backoff.go:73 ("grpcrand.Float64()")

## Q-14 — Report failure per exhausted address-list pass

**Decision (DR-014):** Use the same per-list-pass TransientFailure policy in all handshake modes. Individual failed addresses remain Connecting while alternatives remain. Document the chosen subchannel-level interpretation and its deviation from a literal per-address reading.

**Rationale:** This agrees with the explicit existing multi-address test and avoids mode-dependent output noise.

Status: ANSWERED; implementation pending.

Evidence: clientconn_state_transition_test.go:269 ("func (s) TestStateTransitions_TriesAllAddrsBeforeTransientFailure"); clientconn.go:1097 ("ac.updateConnectivityState(connectivity.TransientFailure)")

## Q-15 — Scope ResetConnectBackoff to backoff, not health status

**Decision (DR-015):** Reset the retry history in every live state and wake a real backoff wait. Do not recycle a live transport merely because its health status is NOT_SERVING. Document that immediate reconnection applies to backoff-TF, not health-TF; health recovery follows DR-008.

**Rationale:** A health verdict is not a dial-backoff timer. The broad old API prose needs explicit qualification for this substate.

Status: ANSWERED; implementation pending.

Evidence: clientconn.go:1070 ("<-reconnect.Done()"); clientconn.go:1291 ("func (ac *addrConn) resetConnectBackoff")

## Q-16 — Retain server-directed keepalive floor with saturation

**Decision (DR-016):** Keep the nondecreasing keepalive floor for the lifetime of its owning ClientConn, with no automatic decay. Double using saturating duration arithmetic capped at the largest representable positive duration; never overflow to a negative or shorter interval. Record this as a ClientConn model obligation.

**Rationale:** Accepting the ratchet must not accept integer overflow. The owning object is ClientConn, not addrConn.

Status: ANSWERED; implementation pending.

Evidence: clientconn.go:957 ("v := 2 * ac.dopts.copts.KeepaliveParams.Time")
