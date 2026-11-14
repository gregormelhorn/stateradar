# As-is validation

Upstream: `go test -timeout=10s ./...` passed (log 009).

- TestStateConstants and TestNewCircuitBreaker cover enum/string projection, initial Closed with zero counts, disabled/armed interval, default and negative-duration configuration. observed-in-tests gobreaker_test.go:116 ("assert.Equal(t, State(0), StateClosed)") gobreaker_test.go:123 ("assert.Equal(t, State(100).String(), "unknown state: 100")") gobreaker_test.go:134 ("assert.Equal(t, StateClosed, defaultCB.state)") gobreaker_test.go:147 ("assert.False(t, customCB.expiry.IsZero())") gobreaker_test.go:153 ("assert.Equal(t, time.Duration(60)*time.Second, negativeDurationCB.timeout)").
- TestDefaultCircuitBreaker runs Closed failure/success, trip, Open refusals, strict-after observed timeout, HalfOpen failure and then recovery on success. observed-in-tests gobreaker_test.go:168 ("assert.Equal(t, Counts{5, 0, 5, 0, 5}, defaultCB.counts)") gobreaker_test.go:182 ("assert.Equal(t, StateOpen, defaultCB.State())") gobreaker_test.go:188 ("assert.Equal(t, Counts{0, 0, 0, 0, 0}, defaultCB.counts)") gobreaker_test.go:195 ("assert.Equal(t, StateHalfOpen, defaultCB.State())") gobreaker_test.go:200 ("assert.Equal(t, StateOpen, defaultCB.State())") gobreaker_test.go:211 ("assert.Equal(t, StateClosed, defaultCB.State())").
- TestCustomCircuitBreaker covers policy copy, interval clear, custom trip and notifications, budget refusal with outstanding work, then close after third success. The expiry assertion after custom HalfOpen checks the default instance (Q-14). observed-in-tests gobreaker_test.go:90 ("counts.clear() // no effect on customCB.counts") gobreaker_test.go:234 ("assert.Equal(t, Counts{1, 0, 1, 0, 1}, customCB.counts)") gobreaker_test.go:242 ("assert.Equal(t, StateChange{"cb", StateClosed, StateOpen}, stateChange)") gobreaker_test.go:247 ("assert.True(t, defaultCB.expiry.IsZero())") gobreaker_test.go:259 ("assert.Error(t, succeed(customCB)) // over MaxRequests") gobreaker_test.go:264 ("assert.Equal(t, StateChange{"cb", StateHalfOpen, StateClosed}, stateChange)").
- TestTwoStepCircuitBreaker covers the same lifecycle via Allow and done(bool). observed-in-tests gobreaker_test.go:67 ("if err != nil {") gobreaker_test.go:290 ("assert.Equal(t, StateOpen, tscb.State())") gobreaker_test.go:294 ("assert.Error(t, succeed2Step(tscb))") gobreaker_test.go:303 ("assert.Equal(t, StateHalfOpen, tscb.State())") gobreaker_test.go:319 ("assert.Equal(t, StateClosed, tscb.State())").
- TestPanicInRequest observes panic and one failure. TestGeneration refreshes with State, then an old completion contributes zero. TestCustomIsSuccessful exercises override and default-like classification by private test mutation. TestCircuitBreakerInParallel replays concurrent successful admissions and completions. observed-in-tests gobreaker_test.go:325 ("assert.Panics(t, func() { causePanic(defaultCB) })") gobreaker_test.go:326 ("assert.Equal(t, Counts{1, 0, 1, 0, 1}, defaultCB.counts)") gobreaker_test.go:337 ("assert.Equal(t, StateClosed, customCB.State())") gobreaker_test.go:342 ("assert.Equal(t, Counts{0, 0, 0, 0, 0}, customCB.counts)") gobreaker_test.go:355 ("assert.Equal(t, Counts{5, 5, 0, 5, 0}, cb.counts)") gobreaker_test.go:365 ("assert.Equal(t, StateOpen, cb.State())") gobreaker_test.go:391 ("assert.Equal(t, Counts{total, total, 0, total, 0}, customCB.counts)").

Overlay: `go test -vet=off -overlay domain-analysis/circuitBreaker/_probe/overlay.json -timeout=10s -run ^TestPilot -v .` passed all eight probes (035). The underscore directory keeps Go recursive discovery independent. The white-box expiry edit only schedules the boundary. Assertions use public State, Counts, callback or error. The reentry probe uses a bounded check after entering the callback and leaves the blocked goroutine to test process teardown; the mutex source establishes permanent same-lock wait absent outside intervention. The upstream timer tests perturb expiry and do not establish exact equality behavior.

| Probe | Observed result |
| --- | --- |
| DuplicateCompletion | One admission, two successes close HalfOpen. |
| OmittedCompletionAndSecondAllow | Further admissions refuse until a late matching report closes. |
| StaleCompletionAdvancesOpen | Stale report emits Open to HalfOpen while counters stay clear. |
| CountsDoesNotRefresh | Snapshot retains pre-clear data until State. |
| ExecuteOverlap | Second Execute accounts and returns before first resumes. |
| StateChangePanicKeepsTransition | Notification panics after committed Open and reset. |
| IsSuccessfulAfterExpiry | Classifier runs and original pair returns even when accounting is skipped. |
| NotificationReentry | Reentrant Counts fails to return within the bounded probe. |

| WrapperReassignmentRedirectsReport | A serialized public wrapper assignment redirects old done to a fresh underlying breaker. observed-in-tests domain-analysis/circuitBreaker/_probe/behavior_test.go:177 ("if got := b.Counts(); got.Requests != 0 || got.TotalSuccesses != 1 {"). |
| TripPolicyPanicRepeatsFailure | One admission produces two failures and rethrows the first policy panic. observed-in-tests domain-analysis/circuitBreaker/_probe/behavior_test.go:201 ("if c := b.Counts(); c.Requests != 1 || c.TotalFailures != 2 || calls != 2 {"). |

Expanded overlay passed 10/10 with normal execution (102) and 10/10 under the Go race detector (103).
