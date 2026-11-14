# As-is validation

The upstream command `go test -timeout 20s ./...` passed (pilot log 010).

| Existing test | Replay and evidence |
|---|---|
| TestStateConstants | Three enum values and labels; unknown enum formatting is outside instance state (gobreaker_test.go:116-123). |
| TestNewCircuitBreaker | Construction initializes Closed with empty counts, defaults and configured durations, normalizes negatives (gobreaker_test.go:128-158). |
| TestDefaultCircuitBreaker | Five failures stay Closed, success resets streak; sixth consecutive failure opens and clears; refusal before timeout; State after timeout enters HalfOpen; failure reopens; success later closes (gobreaker_test.go:164-213). |
| TestCustomCircuitBreaker | Closed refresh clears; trip ratio uses copied counters; OnStateChange reports transitions; third pending success consumes last HalfOpen slot, another call refuses; completion closes (gobreaker_test.go:219-264). The expiry assertion reads defaultCB (gobreaker_test.go:247 ("assert.True(t, defaultCB.expiry.IsZero())")). |
| TestTwoStepCircuitBreaker | Allow/false and Allow/true replay default counts and all three states (gobreaker_test.go:271-321). |
| TestPanicInRequest | Ordinary nonnil request panic escapes and counts as one failure (gobreaker_test.go:325-326). |
| TestGeneration | State refresh clears first; later return is ignored for counting (gobreaker_test.go:337-342). |
| TestCustomIsSuccessful | Classifier changes accounting while request errors still return (gobreaker_test.go:345-365). |
| TestCircuitBreakerInParallel | Ten callers finish 100,000 successful admissions in the same Closed generation (gobreaker_test.go:369-391). |

## As-is probes

`go test -timeout 10s -overlay domain-analysis/circuitBreaker/_probe/overlay.json -run '^TestPilot' -v .` passed seven tests (log 077).

- TestPilotDuplicateAndMissing covers HalfOpen capacity, duplicate successes, and stale contradictory failure.
- TestPilotStaleCompletionRefresh covers Open → HalfOpen from a stale report and raw Counts leaving it untouched. The assertion at _probe/pilot_test.go:82 checks whether the hook fired before any State call.
- TestPilotPolicyPanicAccounting observes two failure increments for one Execute when policy panics.
- TestPilotNotifyPanicPrecedence observes replacement panic and committed state.
- TestPilotNotifyReentry observes lack of return in a bounded window, backed by same-mutex lock sites. The goroutine stays blocked until the test process exits.
- TestPilotClassifierWindow holds the classifier outside the lock, refreshes a Closed interval through State and verifies stale accounting.
- TestPilotGoexit observes an admitted request with no counted outcome after goroutine exit.

The expanded overlay run passed nine tests (log 104). TestPilotSecondExecuteCompletesFirst observes two separate admissions from one logical caller and the later result returning before the first. TestPilotRecoveryNotificationPanicBeforeAdmission observes the state commit, panic propagation and zero admissions when the recovery hook fails before admission commits.

## Race-detector runs

- `go test -race -timeout 20s -overlay domain-analysis/circuitBreaker/_probe/overlay.json -run '^TestPilot' .` passed (log 115).
- `go test -race -timeout 30s ./...` failed (log 116). TestCustomCircuitBreaker reads private counts directly at gobreaker_test.go:258 ("assert.Equal(t, Counts{3, 2, 0, 2, 0}, customCB.counts)") while succeedLater writes Requests through gobreaker.go:56 ("c.Requests++") gobreaker.go:289 ("cb.counts.onRequest()"). A sleep at gobreaker_test.go:257 ("time.Sleep(time.Duration(50) * time.Millisecond)") does not establish a happens-before edge. The public Counts takes the same mutex as admission (gobreaker.go:217 ("cb.mutex.Lock()") gobreaker.go:277 ("cb.mutex.Lock()")). This is an upstream test access race. The existing test was preserved.
