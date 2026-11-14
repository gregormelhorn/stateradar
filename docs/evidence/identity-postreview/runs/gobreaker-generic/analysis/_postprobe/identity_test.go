package gobreaker_test

import (
	"errors"
	"runtime"
	"testing"
	"time"

	breaker "github.com/sony/gobreaker"
)

const transitionWait = 50 * time.Millisecond

func postAllow(t *testing.T, cb *breaker.TwoStepCircuitBreaker) func(bool) {
	t.Helper()
	done, err := cb.Allow()
	if err != nil || done == nil {
		t.Fatalf("Allow: callback present=%v, error=%v", done != nil, err)
	}
	return done
}

func postCounts(t *testing.T, cb interface{ Counts() breaker.Counts }, want breaker.Counts) {
	t.Helper()
	if got := cb.Counts(); got != want {
		t.Fatalf("Counts=%+v, want %+v", got, want)
	}
}

func postState(t *testing.T, cb interface{ State() breaker.State }, want breaker.State) {
	t.Helper()
	if got := cb.State(); got != want {
		t.Fatalf("State=%v, want %v", got, want)
	}
}

func postRecover(fn func()) (recovered interface{}, returned bool) {
	defer func() { recovered = recover() }()
	fn()
	return nil, true
}

func TestIdentityReassignedClosedFailure(t *testing.T) {
	for _, order := range []string{"same generation", "different generation"} {
		t.Run(order, func(t *testing.T) {
			source := breaker.NewTwoStepCircuitBreaker(breaker.Settings{})
			original := *source
			foreign := postAllow(t, source)
			var samples []breaker.Counts
			var transitions []breaker.State
			target := breaker.NewTwoStepCircuitBreaker(breaker.Settings{
				Timeout: transitionWait,
				ReadyToTrip: func(c breaker.Counts) bool {
					samples = append(samples, c)
					return true
				},
				OnStateChange: func(_ string, _, to breaker.State) {
					transitions = append(transitions, to)
				},
			})
			if order == "different generation" {
				postAllow(t, target)(false)
				time.Sleep(transitionWait)
				postAllow(t, target)(true)
				samples, transitions = nil, nil
			}

			postState(t, target, breaker.StateClosed)
			postCounts(t, target, breaker.Counts{})
			*source = *target
			foreign(false)
			postCounts(t, &original, breaker.Counts{Requests: 1})
			postCounts(t, target, breaker.Counts{})
			if order == "same generation" {
				want := breaker.Counts{TotalFailures: 1, ConsecutiveFailures: 1}
				if len(samples) != 1 || samples[0] != want || len(transitions) != 1 || transitions[0] != breaker.StateOpen {
					t.Fatalf("target trip samples=%+v transitions=%v", samples, transitions)
				}
			} else if len(samples) != 0 || len(transitions) != 0 {
				t.Fatalf("stale report reached target hooks: samples=%+v transitions=%v", samples, transitions)
			}
		})
	}
}

func TestIdentityReassignedHalfOpenTrial(t *testing.T) {
	makeHalfOpen := func(name string, onChange func(string, breaker.State, breaker.State)) *breaker.TwoStepCircuitBreaker {
		return breaker.NewTwoStepCircuitBreaker(breaker.Settings{
			Name: name, MaxRequests: 1, Timeout: transitionWait,
			ReadyToTrip: func(breaker.Counts) bool { return true }, OnStateChange: onChange,
		})
	}
	source := makeHalfOpen("source", nil)
	original := *source
	closedNotifications := 0
	target := makeHalfOpen("target", func(name string, from, to breaker.State) {
		if name != "target" {
			t.Errorf("notification name=%q", name)
		}
		if from == breaker.StateHalfOpen && to == breaker.StateClosed {
			closedNotifications++
		}
	})
	postAllow(t, source)(false)
	postAllow(t, target)(false)
	time.Sleep(transitionWait)
	postState(t, source, breaker.StateHalfOpen)
	postState(t, target, breaker.StateHalfOpen)

	foreign := postAllow(t, source)
	legitimate := postAllow(t, target)
	*source = *target
	foreign(true)
	postState(t, target, breaker.StateClosed)
	postCounts(t, target, breaker.Counts{})
	postCounts(t, &original, breaker.Counts{Requests: 1})
	postState(t, &original, breaker.StateHalfOpen)
	legitimate(false)
	postState(t, target, breaker.StateClosed)
	postCounts(t, target, breaker.Counts{})
	if closedNotifications != 1 {
		t.Fatalf("target close notifications=%d", closedNotifications)
	}

	*source = original
	foreign(true)
	postState(t, &original, breaker.StateClosed)
	postCounts(t, &original, breaker.Counts{})
	postCounts(t, target, breaker.Counts{})
}

func TestIdentityLateHalfOpenSuccessBelowThreshold(t *testing.T) {
	cb := breaker.NewTwoStepCircuitBreaker(breaker.Settings{
		MaxRequests: 2, Timeout: transitionWait,
		ReadyToTrip: func(breaker.Counts) bool { return true },
	})
	postAllow(t, cb)(false)
	time.Sleep(transitionWait)
	first := postAllow(t, cb)
	time.Sleep(transitionWait)
	first(true)
	postState(t, cb, breaker.StateHalfOpen)
	postCounts(t, cb, breaker.Counts{Requests: 1, TotalSuccesses: 1, ConsecutiveSuccesses: 1})
	postAllow(t, cb)(true)
	postState(t, cb, breaker.StateClosed)
	postCounts(t, cb, breaker.Counts{})
}

func TestIdentityStateObserverNotificationPanic(t *testing.T) {
	hookPanic := errors.New("half-open notification")
	notifications := 0
	cb := breaker.NewTwoStepCircuitBreaker(breaker.Settings{
		Timeout: transitionWait, MaxRequests: 1,
		ReadyToTrip: func(breaker.Counts) bool { return true },
		OnStateChange: func(_ string, from, to breaker.State) {
			if from == breaker.StateOpen && to == breaker.StateHalfOpen {
				notifications++
				panic(hookPanic)
			}
		},
	})
	postAllow(t, cb)(false)
	time.Sleep(transitionWait)
	postCounts(t, cb, breaker.Counts{})
	if notifications != 0 {
		t.Fatalf("Counts triggered %d notifications", notifications)
	}
	var stateReturned bool
	p, returned := postRecover(func() { cb.State(); stateReturned = true })
	if p != hookPanic || returned || stateReturned {
		t.Fatalf("State: panic=%v returned=%v stateReturned=%v", p, returned, stateReturned)
	}
	postCounts(t, cb, breaker.Counts{})
	postState(t, cb, breaker.StateHalfOpen)
	if notifications != 1 {
		t.Fatalf("retry replayed notification, count=%d", notifications)
	}
	postAllow(t, cb)(true)
	postState(t, cb, breaker.StateClosed)
}

func TestIdentityReadyToTripGoexit(t *testing.T) {
	reqErr := errors.New("request failure")
	var samples []breaker.Counts
	cb := breaker.NewCircuitBreaker(breaker.Settings{
		ReadyToTrip: func(c breaker.Counts) bool {
			samples = append(samples, c)
			runtime.Goexit()
			return true
		},
	})
	finished := make(chan struct{})
	returned := make(chan struct{}, 1)
	go func() {
		defer close(finished)
		cb.Execute(func() (interface{}, error) { return nil, reqErr })
		returned <- struct{}{}
	}()
	<-finished
	want := breaker.Counts{Requests: 1, TotalFailures: 1, ConsecutiveFailures: 1}
	if len(returned) != 0 || len(samples) != 1 || samples[0] != want {
		t.Fatalf("returned=%t hook samples=%+v", len(returned) != 0, samples)
	}
	postState(t, cb, breaker.StateClosed)
	postCounts(t, cb, want)
	value, err := cb.Execute(func() (interface{}, error) { return 17, nil })
	if value != 17 || err != nil {
		t.Fatalf("subsequent Execute returned (%v, %v)", value, err)
	}
	postCounts(t, cb, breaker.Counts{Requests: 2, TotalFailures: 1, TotalSuccesses: 1, ConsecutiveSuccesses: 1})
}

func TestIdentityNilPanicBoundary(t *testing.T) {
	var typedNil *int
	for _, scenario := range []struct {
		name  string
		value interface{}
	}{
		{name: "nil interface", value: nil},
		{name: "typed nil", value: typedNil},
	} {
		for _, origin := range []string{"request", "classifier"} {
			t.Run(scenario.name+"/"+origin, func(t *testing.T) {
				runtimePanic, controlReturned := postRecover(func() { panic(scenario.value) })
				if controlReturned || (scenario.name == "typed nil" && runtimePanic != scenario.value) {
					t.Fatalf("standalone panic: value=%#v returned=%v", runtimePanic, controlReturned)
				}
				classifications, trips := 0, 0
				cb := breaker.NewCircuitBreaker(breaker.Settings{
					ReadyToTrip:  func(breaker.Counts) bool { trips++; return false },
					IsSuccessful: func(error) bool { classifications++; panic(scenario.value) },
				})
				var result interface{}
				var err error
				p, returned := postRecover(func() {
					result, err = cb.Execute(func() (interface{}, error) {
						if origin == "request" {
							panic(scenario.value)
						}
						return 17, nil
					})
				})
				wantClasses := 0
				if origin == "classifier" {
					wantClasses = 1
				}
				if classifications != wantClasses {
					t.Fatalf("classifications=%d, want %d", classifications, wantClasses)
				}
				if runtimePanic == nil {
					if !returned || p != nil || result != nil || err != nil || trips != 0 {
						t.Fatalf("nil recovery: returned=%v panic=%#v pair=(%v, %v) trips=%d", returned, p, result, err, trips)
					}
					postCounts(t, cb, breaker.Counts{Requests: 1})
					t.Log("standalone recover returned nil; Execute returned a zero pair without reporting")
					return
				}
				if returned || p == nil || trips != 1 {
					t.Fatalf("non-nil recovery: returned=%v panic=%#v trips=%d", returned, p, trips)
				}
				if scenario.name == "typed nil" && p != scenario.value {
					t.Fatalf("typed-nil panic changed to %#v", p)
				}
				if scenario.name == "nil interface" {
					if got, ok := p.(error); !ok || got.Error() != runtimePanic.(error).Error() {
						t.Fatalf("runtime panic changed: got %#v, control %#v", p, runtimePanic)
					}
				}
				postCounts(t, cb, breaker.Counts{Requests: 1, TotalFailures: 1, ConsecutiveFailures: 1})
				t.Logf("standalone recover returned %T; Execute recorded failure and rethrew", runtimePanic)
			})
		}
	}
}
