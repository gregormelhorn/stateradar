# As-is validation

Baseline `go test -timeout 20s ./...` passed (log 025). No repository tests were edited.

| Existing scenario | Replay and evidence |
|---|---|
| StateConstants | Three API modes and unknown State formatting. gobreaker_test.go:116 ("assert.Equal(t, State(0), StateClosed)") and gobreaker_test.go:123 ("assert.Equal(t, State(100).String(), \"unknown state: 100\")"). Unknown State is a formatting input. |
| NewCircuitBreaker | Default, custom and negative settings replay Configure into Closed. gobreaker_test.go:134 ("assert.Equal(t, StateClosed, defaultCB.state)"), gobreaker_test.go:147 ("assert.False(t, customCB.expiry.IsZero())"), gobreaker_test.go:152 ("assert.Equal(t, time.Duration(0)*time.Second, negativeDurationCB.interval)"). |
| DefaultCircuitBreaker | Five failures stay, success clears streak, sixth consecutive failure opens; refuses, expires, reopens on trial failure, then closes on success. gobreaker_test.go:180 ("assert.Nil(t, fail(defaultCB)) // 6 consecutive failures"), gobreaker_test.go:195 ("assert.Equal(t, StateHalfOpen, defaultCB.State())"), gobreaker_test.go:211 ("assert.Equal(t, StateClosed, defaultCB.State())"). |
| CustomCircuitBreaker | Expired Closed admission starts fresh counts, ratio trips, hook sees three transition types, third admission saturates cap until result closes. gobreaker_test.go:234 ("assert.Equal(t, Counts{1, 0, 1, 0, 1}, customCB.counts)"), gobreaker_test.go:248 ("assert.Equal(t, StateChange{\"cb\", StateOpen, StateHalfOpen}, stateChange)"), gobreaker_test.go:259 ("assert.Error(t, succeed(customCB)) // over MaxRequests"). Wrong receiver at gobreaker_test.go:247 ("assert.True(t, defaultCB.expiry.IsZero())"), Q-14. |
| TwoStepCircuitBreaker | Same state transitions and count resets via Allow and reports. gobreaker_test.go:290 ("assert.Equal(t, StateOpen, tscb.State())"), gobreaker_test.go:319 ("assert.Equal(t, StateClosed, tscb.State())"). |
| PanicInRequest | Ordinary same-generation request panic increments failure then escapes. gobreaker_test.go:325 ("assert.Panics(t, func() { causePanic(defaultCB) })"). |
| Generation | Late success after Closed reset leaves fresh Counts untouched. gobreaker_test.go:342 ("assert.Equal(t, Counts{0, 0, 0, 0, 0}, customCB.counts)"). |
| CustomIsSuccessful | Classifier records error as success, raw error stays returned; restoring error policy trips. gobreaker_test.go:355 ("assert.Equal(t, Counts{5, 5, 0, 5, 0}, cb.counts)") and gobreaker_test.go:365 ("assert.Equal(t, StateOpen, cb.State())"). |
| CircuitBreakerInParallel | Closed accepts overlapping work; mutex serializes count updates. gobreaker_test.go:391 ("assert.Equal(t, Counts{total, total, 0, total, 0}, customCB.counts)"). |

## Isolated Go overlay

`go test -timeout 15s -count=1 -overlay domain-analysis/circuitBreaker/_probe/overlay.json -run '^TestPilot' -v .` passed all ten probes (log 086). The file under _probe is isolated from recursive upstream discovery. The JSON overlay maps an added virtual test file into the package.

- DuplicateDone confirms early closure on a second callback invocation.
- AbandonAndLateReport confirms repeated refusal, then separate late success and failure branches.
- AdmissionOrdering confirms refusal before the closing report and admission after it, supporting P-03a/b.
- ExecuteOvertakes proves result reordering and a new call after retaining the earlier value.
- ExpiryAndStaleReport observes no idle or Counts notification, then stale callback promotion for both Boolean values.
- StaleClassifierAndReturn stages stale accounting with a channel and verifies original error return.
- CallbackReentry measures no return for 25 ms after entering each callback; the sync.Mutex contract establishes the deadlock mechanism. The intentionally blocked goroutines last only until test-process exit.
- CallbackPanics shows double failure accounting, hook commit survival, and replacement of the request panic.
- Goexit shows an admission without outcome.
- SharedRecoveryWaves generates three four-request failure waves.

`go test -race -timeout 20s -overlay domain-analysis/circuitBreaker/_probe/overlay.json -run '^TestPilot' .` passed (log 095). The full overlay run `go test -race -timeout 30s -overlay domain-analysis/circuitBreaker/_probe/overlay.json ./...` failed (log 091). Upstream TestCustomCircuitBreaker reads its internal Counts directly at gobreaker_test.go:258 ("assert.Equal(t, Counts{3, 2, 0, 2, 0}, customCB.counts)") while succeedLater writes through gobreaker.go:56 ("c.Requests++") and gobreaker.go:289 ("cb.counts.onRequest()") under gobreaker.go:277 ("cb.mutex.Lock()"). The test's sleep provides no synchronization. This is evidence of a test-harness race. The public Counts getter locks at gobreaker.go:217 ("cb.mutex.Lock()").

The final full non-race overlay suite passed (133). The final probe-only race suite passed (134). The late-failure branch now asserts an Open notification directly before the next State visit, which can immediately observe elapsed expiry in this fixture. The added P-03a assertion observes StateClosed after the refused second admission and before the next admission.
