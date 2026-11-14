# As-is validation

| Existing test | Replay |
|---|---|
| TestStateConstants | The diagram projects the public enum and adds a half-open budget condition. observed-in-tests gobreaker_test.go:116 ("assert.Equal(t, State(0), StateClosed)"). |
| TestNewCircuitBreaker | Construction starts closed and establishes configured or default state data. observed-in-tests gobreaker_test.go:126 ("func TestNewCircuitBreaker(t *testing.T) {"). |
| TestDefaultCircuitBreaker | Closed counts outcomes, sixth consecutive failure opens, Open rejects, State observes expiry, half-open failure reopens and success closes. observed-in-tests gobreaker_test.go:195 ("assert.Equal(t, StateHalfOpen, defaultCB.State())"). |
| TestCustomCircuitBreaker | Closed interval clears, custom failure ratio opens, timeout permits half-open, third pending admission saturates, fourth rejects, and third success closes. observed-in-tests gobreaker_test.go:259 ("assert.Error(t, succeed(customCB))"). Line 247 reads defaultCB expiry, so it supplies no custom expiry assertion. |
| TestTwoStepCircuitBreaker | Allow and report follow the same state path with no classifier. observed-in-tests gobreaker_test.go:307 ("assert.Nil(t, fail2Step(tscb))"). |
| TestPanicInRequest | Request panic is rethrown with one failure in the tested closed path. observed-in-tests gobreaker_test.go:325 ("assert.Panics(t, func() { causePanic(defaultCB) })"). |
| TestGeneration | State clears the interval before late completion, which does not alter refreshed counts. observed-in-tests gobreaker_test.go:342 ("assert.Equal(t, Counts{0, 0, 0, 0, 0}, customCB.counts)"). |
| TestCustomIsSuccessful | Error classified as success remains a success in counts; replacing test policy restores the default interpretation. observed-in-tests gobreaker_test.go:355 ("assert.Equal(t, Counts{5, 5, 0, 5, 0}, cb.counts)"). |
| TestCircuitBreakerInParallel | Concurrent Execute calls contribute serialized updates without loss in the tested window. observed-in-tests gobreaker_test.go:391 ("assert.Equal(t, Counts{total, total, 0, total, 0}, customCB.counts)"). |

Baseline `go test -timeout=15s ./...` passed (log 011). Overlay `go test -timeout=10s -count=1 -overlay domain-analysis/circuitBreaker/overlay.json -run ^TestPilot -v .` passed all seven probes and two reentry subtests (log 057). Controlled request scheduling uses channels. The half-open probes use a one-nanosecond timeout and a nanosecond-scale clock dependency. The reentry probe confirms no return in a 30 ms window after the callback entered. The mutex contract and held-lock call establish why reentry cannot complete. Blocked goroutines are local to the probe test process.

Expanded bounded overlay passed all nine probes (log 108). TestPilotAllowThenStateAtOpenExpiry schedules a past deadline under the mutex with no other goroutine and then asserts exclusively through Allow and State. TestPilotSameOwnerOutstandingBelowBudget observes two independent outstanding callbacks, a refused third admission after a success, and closure only after the second report.

The full race-detector run failed in existing TestCustomCircuitBreaker (log 105). Its direct unlocked read at gobreaker_test.go:258 ("assert.Equal(t, Counts{3, 2, 0, 2, 0}, customCB.counts)") races with the admitted goroutine increment in the locked section gobreaker.go:277-289. The test uses a sleep to order the access. The production Counts entry acquires the same mutex as admission. This is a test finding, outside the public statechart; no source or test was edited.

Final probe-only run with -race passed all nine cases in log 117. The stale-report probe observed the HalfOpen notification before making a new API call.
