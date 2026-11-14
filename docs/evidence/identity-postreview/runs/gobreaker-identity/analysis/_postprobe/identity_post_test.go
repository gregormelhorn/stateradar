package gobreaker_test

import (
	"errors"
	"testing"
	"time"

	"github.com/sony/gobreaker"
)

func postDone(t *testing.T, breaker *gobreaker.TwoStepCircuitBreaker) func(bool) {
	t.Helper()
	done, err := breaker.Allow()
	if err != nil || done == nil {
		t.Fatalf("Allow: completion present=%t, err=%v", done != nil, err)
	}
	return done
}

func postCounts(t *testing.T, breaker interface{ Counts() gobreaker.Counts }, want gobreaker.Counts) {
	t.Helper()
	if got := breaker.Counts(); got != want {
		t.Fatalf("Counts = %+v, want %+v", got, want)
	}
}

func postPanic(t *testing.T, fn func()) (value interface{}) {
	t.Helper()
	defer func() { value = recover() }()
	fn()
	t.Fatal("expected panic")
	return nil
}

func TestIdentityWrapperCopyAndLocalRebinding(t *testing.T) {
	original := gobreaker.NewTwoStepCircuitBreaker(gobreaker.Settings{})
	local := original
	alias := *original
	done := postDone(t, local)
	distinct := gobreaker.NewTwoStepCircuitBreaker(gobreaker.Settings{})
	alias = *distinct
	local = distinct
	done(true)
	postCounts(t, original, gobreaker.Counts{Requests: 1, TotalSuccesses: 1, ConsecutiveSuccesses: 1})
	postCounts(t, &alias, gobreaker.Counts{})
	postCounts(t, local, gobreaker.Counts{})

	alias = *original
	postDone(t, &alias)
	postCounts(t, original, gobreaker.Counts{Requests: 2, TotalSuccesses: 1, ConsecutiveSuccesses: 1})
}

func TestIdentityOverwriteDuringAdmissionAndRestore(t *testing.T) {
	const timeout = 20 * time.Millisecond
	replacement := gobreaker.NewTwoStepCircuitBreaker(gobreaker.Settings{
		Name: "replacement", Timeout: timeout, ReadyToTrip: func(gobreaker.Counts) bool { return true },
	})
	postDone(t, replacement)(false)
	time.Sleep(timeout)
	if state := replacement.State(); state != gobreaker.StateHalfOpen {
		t.Fatalf("replacement setup: state = %v", state)
	}

	var wrapper *gobreaker.TwoStepCircuitBreaker
	wrapper = gobreaker.NewTwoStepCircuitBreaker(gobreaker.Settings{
		Name: "original", Timeout: timeout, ReadyToTrip: func(gobreaker.Counts) bool { return true },
		OnStateChange: func(_ string, from, to gobreaker.State) {
			if from == gobreaker.StateOpen && to == gobreaker.StateHalfOpen {
				*wrapper = *replacement
			}
		},
	})
	originalAlias := *wrapper
	postDone(t, wrapper)(false)
	time.Sleep(timeout)
	done := postDone(t, wrapper)
	if got := wrapper.Name(); got != "replacement" {
		t.Fatalf("wrapper still names %q", got)
	}
	postCounts(t, &originalAlias, gobreaker.Counts{Requests: 1})
	postCounts(t, replacement, gobreaker.Counts{})
	done(true)
	if state := replacement.State(); state != gobreaker.StateClosed {
		t.Fatalf("replacement after redirected success: state = %v", state)
	}
	postCounts(t, replacement, gobreaker.Counts{})
	postCounts(t, &originalAlias, gobreaker.Counts{Requests: 1})
	if completion, err := originalAlias.Allow(); completion != nil || err != gobreaker.ErrTooManyRequests {
		t.Fatalf("original slot: completion present=%t, err=%v", completion != nil, err)
	}
	*wrapper = originalAlias
	done(true)
	if state := originalAlias.State(); state != gobreaker.StateClosed {
		t.Fatalf("original after restore: state = %v", state)
	}
	postCounts(t, &originalAlias, gobreaker.Counts{})
}

func TestIdentityReplacementExpiryBeforeMismatch(t *testing.T) {
	const timeout = 20 * time.Millisecond
	type transition struct {
		name     string
		from, to gobreaker.State
	}
	var transitions []transition
	wrapper := gobreaker.NewTwoStepCircuitBreaker(gobreaker.Settings{Name: "original"})
	originalAlias := *wrapper
	done := postDone(t, wrapper)
	target := gobreaker.NewTwoStepCircuitBreaker(gobreaker.Settings{
		Name: "target", Timeout: timeout, ReadyToTrip: func(gobreaker.Counts) bool { return true },
		OnStateChange: func(name string, from, to gobreaker.State) {
			transitions = append(transitions, transition{name, from, to})
		},
	})
	postDone(t, target)(false)
	time.Sleep(timeout)
	*wrapper = *target
	postCounts(t, target, gobreaker.Counts{})
	if len(transitions) != 1 {
		t.Fatalf("Counts resolved expiry: transitions = %v", transitions)
	}
	done(false)
	want := transition{"target", gobreaker.StateOpen, gobreaker.StateHalfOpen}
	if len(transitions) != 2 || transitions[1] != want {
		t.Fatalf("report did not resolve target expiry: transitions = %v, want second %v", transitions, want)
	}
	postCounts(t, target, gobreaker.Counts{})
	if state := target.State(); state != gobreaker.StateHalfOpen {
		t.Fatalf("mismatched failure changed target state to %v", state)
	}
	postCounts(t, &originalAlias, gobreaker.Counts{Requests: 1})
}

func TestIdentityExecuteBoundReceiver(t *testing.T) {
	for _, mode := range []string{"return", "panic"} {
		t.Run(mode, func(t *testing.T) {
			classifications, trips := 0, 0
			original := gobreaker.NewCircuitBreaker(gobreaker.Settings{
				IsSuccessful: func(error) bool { classifications++; return true },
				ReadyToTrip:  func(gobreaker.Counts) bool { trips++; return false },
			})
			rebound := gobreaker.NewCircuitBreaker(gobreaker.Settings{
				IsSuccessful: func(error) bool { t.Error("rebound classifier ran"); return false },
				ReadyToTrip:  func(gobreaker.Counts) bool { t.Error("rebound trip hook ran"); return false },
			})
			local := original
			run := local.Execute
			marker := errors.New("request marker")
			req := func() (interface{}, error) {
				local = rebound
				if mode == "panic" {
					panic(marker)
				}
				return "original result", marker
			}
			if mode == "panic" {
				if got := postPanic(t, func() { run(req) }); got != marker {
					t.Fatalf("panic = %v, want %v", got, marker)
				}
				if classifications != 0 || trips != 1 {
					t.Fatalf("original hook calls: classifier=%d trip=%d", classifications, trips)
				}
				postCounts(t, original, gobreaker.Counts{Requests: 1, TotalFailures: 1, ConsecutiveFailures: 1})
			} else {
				local = rebound // A bound method retains its receiver even before invocation.
				if got, err := run(req); got != "original result" || err != marker {
					t.Fatalf("Execute = %v, %v", got, err)
				}
				if classifications != 1 || trips != 0 {
					t.Fatalf("original hook calls: classifier=%d trip=%d", classifications, trips)
				}
				postCounts(t, original, gobreaker.Counts{Requests: 1, TotalSuccesses: 1, ConsecutiveSuccesses: 1})
			}
			postCounts(t, local, gobreaker.Counts{})
		})
	}
}

func TestIdentityStoredSettingsFunction(t *testing.T) {
	var originalCalls, replacementCalls int
	success := false
	settings := gobreaker.Settings{IsSuccessful: func(error) bool {
		originalCalls++
		return success
	}}
	breaker := gobreaker.NewCircuitBreaker(settings)
	settings.IsSuccessful = func(error) bool { replacementCalls++; return false }
	marker := errors.New("result marker")
	if _, err := breaker.Execute(func() (interface{}, error) {
		success = true
		return nil, marker
	}); err != marker {
		t.Fatalf("Execute returned error %v, want %v", err, marker)
	}
	if originalCalls != 1 || replacementCalls != 0 {
		t.Fatalf("classifier calls: original=%d replacement=%d", originalCalls, replacementCalls)
	}
	postCounts(t, breaker, gobreaker.Counts{Requests: 1, TotalSuccesses: 1, ConsecutiveSuccesses: 1})
}

func TestIdentityZeroWrapperAndRestore(t *testing.T) {
	wrapper := gobreaker.NewTwoStepCircuitBreaker(gobreaker.Settings{})
	originalAlias := *wrapper
	done := postDone(t, wrapper)
	*wrapper = gobreaker.TwoStepCircuitBreaker{}
	postPanic(t, func() { done(true) })
	postCounts(t, &originalAlias, gobreaker.Counts{Requests: 1})
	*wrapper = originalAlias
	done(true)
	postCounts(t, &originalAlias, gobreaker.Counts{Requests: 1, TotalSuccesses: 1, ConsecutiveSuccesses: 1})
}

func TestIdentityReportingHookOverwriteAndRetry(t *testing.T) {
	marker := errors.New("original trip hook")
	targetCalls := 0
	target := gobreaker.NewTwoStepCircuitBreaker(gobreaker.Settings{
		ReadyToTrip: func(c gobreaker.Counts) bool {
			targetCalls++
			if c != (gobreaker.Counts{TotalFailures: 1, ConsecutiveFailures: 1}) {
				t.Errorf("target hook counts = %+v", c)
			}
			return false
		},
	})
	var wrapper *gobreaker.TwoStepCircuitBreaker
	wrapper = gobreaker.NewTwoStepCircuitBreaker(gobreaker.Settings{
		ReadyToTrip: func(gobreaker.Counts) bool {
			*wrapper = *target
			panic(marker)
		},
	})
	originalAlias := *wrapper
	done := postDone(t, wrapper)
	if got := postPanic(t, func() { done(false) }); got != marker {
		t.Fatalf("panic = %v, want %v", got, marker)
	}
	// Both public reads take a mutex. The report must have unlocked A.
	postCounts(t, &originalAlias, gobreaker.Counts{Requests: 1, TotalFailures: 1, ConsecutiveFailures: 1})
	postCounts(t, target, gobreaker.Counts{})
	if targetCalls != 0 {
		t.Fatalf("target hook ran before retry: %d calls", targetCalls)
	}
	done(false)
	postCounts(t, target, gobreaker.Counts{TotalFailures: 1, ConsecutiveFailures: 1})
	postCounts(t, &originalAlias, gobreaker.Counts{Requests: 1, TotalFailures: 1, ConsecutiveFailures: 1})
	if targetCalls != 1 {
		t.Fatalf("target hook ran %d times", targetCalls)
	}
}
