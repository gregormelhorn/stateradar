package gobreaker

import (
	"errors"
	"runtime"
	"testing"
	"time"
)

const identityWait = 35 * time.Millisecond

func identityDone(t *testing.T, cb *TwoStepCircuitBreaker) func(bool) {
	t.Helper()
	done, err := cb.Allow()
	if err != nil || done == nil {
		t.Fatalf("Allow: callback present=%v err=%v", done != nil, err)
	}
	return done
}

func identityRejected(t *testing.T, cb *TwoStepCircuitBreaker, want error) {
	t.Helper()
	done, err := cb.Allow()
	if done != nil || err != want {
		t.Fatalf("Allow: callback present=%v err=%v want %v", done != nil, err, want)
	}
}

func identityCounts(t *testing.T, cb interface{ Counts() Counts }, want Counts) {
	t.Helper()
	if got := cb.Counts(); got != want {
		t.Fatalf("counts %+v want %+v", got, want)
	}
}

func identityState(t *testing.T, cb interface{ State() State }, want State) {
	t.Helper()
	if got := cb.State(); got != want {
		t.Fatalf("state %v want %v", got, want)
	}
}

func identityPanic(t *testing.T, fn func(), want interface{}) {
	t.Helper()
	var got interface{}
	func() { defer func() { got = recover() }(); fn() }()
	if got != want {
		t.Fatalf("panic %v want %v", got, want)
	}
}

func identityTrip(Counts) bool { return true }

func identityHalfOpen(t *testing.T, max uint32) *TwoStepCircuitBreaker {
	t.Helper()
	cb := NewTwoStepCircuitBreaker(Settings{Timeout: identityWait, MaxRequests: max, ReadyToTrip: identityTrip})
	identityDone(t, cb)(false)
	time.Sleep(identityWait)
	identityState(t, cb, StateHalfOpen)
	return cb
}

func TestIdentityRepeatedClosedCompletion(t *testing.T) {
	var samples []Counts
	cb := NewTwoStepCircuitBreaker(Settings{ReadyToTrip: func(c Counts) bool { samples = append(samples, c); return false }})
	done := identityDone(t, cb)
	identityCounts(t, cb, Counts{Requests: 1})
	done(true)
	done(true)
	identityCounts(t, cb, Counts{Requests: 1, TotalSuccesses: 2, ConsecutiveSuccesses: 2})
	done(false)
	done(false)
	identityCounts(t, cb, Counts{Requests: 1, TotalSuccesses: 2, TotalFailures: 2, ConsecutiveFailures: 2})
	if len(samples) != 2 || samples[0].TotalFailures != 1 || samples[1].TotalFailures != 2 {
		t.Fatal(samples)
	}
	identityState(t, cb, StateClosed)
}

func TestIdentityRepeatedHalfOpenSuccess(t *testing.T) {
	cb := identityHalfOpen(t, 2)
	done := identityDone(t, cb)
	done(true)
	identityState(t, cb, StateHalfOpen)
	identityCounts(t, cb, Counts{Requests: 1, TotalSuccesses: 1, ConsecutiveSuccesses: 1})
	done(true)
	identityState(t, cb, StateClosed)
	done(true)
	done(false)
	identityCounts(t, cb, Counts{})
}

func TestIdentityAbandonedHalfOpen(t *testing.T) {
	for _, order := range []string{"no report", "late success", "late failure"} {
		t.Run(order, func(t *testing.T) {
			cb := identityHalfOpen(t, 1)
			producer := make(chan func(bool), 1)
			departed := make(chan struct{})
			done := identityDone(t, cb)
			go func() { defer close(departed); producer <- done }()
			<-departed
			time.Sleep(2 * identityWait)
			identityState(t, cb, StateHalfOpen)
			identityRejected(t, cb, ErrTooManyRequests)
			identityCounts(t, cb, Counts{Requests: 1})
			switch order {
			case "no report":
				identityRejected(t, cb, ErrTooManyRequests)
			case "late success":
				(<-producer)(true)
				identityState(t, cb, StateClosed)
				identityCounts(t, cb, Counts{})
				identityDone(t, cb)
			case "late failure":
				(<-producer)(false)
				identityRejected(t, cb, ErrOpenState)
				identityCounts(t, cb, Counts{})
				time.Sleep(identityWait)
				identityDone(t, cb)
				identityState(t, cb, StateHalfOpen)
			}
		})
	}
}

func TestIdentityHalfOpenBudget(t *testing.T) {
	cb := identityHalfOpen(t, 2)
	first, second := identityDone(t, cb), identityDone(t, cb)
	first(true)
	identityCounts(t, cb, Counts{Requests: 2, TotalSuccesses: 1, ConsecutiveSuccesses: 1})
	identityRejected(t, cb, ErrTooManyRequests)
	second(true)
	identityState(t, cb, StateClosed)
	identityCounts(t, cb, Counts{})
}

func TestIdentityStaleOpenCompletion(t *testing.T) {
	for _, order := range []string{"during open", "completion first", "state first"} {
		for _, success := range []bool{true, false} {
			label := "/failure"
			if success {
				label = "/success"
			}
			t.Run(order+label, func(t *testing.T) {
				var changes []State
				trips := 0
				timeout := identityWait
				if order == "during open" {
					timeout = time.Hour
				}
				cb := NewTwoStepCircuitBreaker(Settings{Timeout: timeout, ReadyToTrip: func(Counts) bool { trips++; return true },
					OnStateChange: func(_ string, _ State, to State) { changes = append(changes, to) }})
				old := identityDone(t, cb)
				identityDone(t, cb)(false)
				if order != "during open" {
					time.Sleep(timeout)
				}
				identityCounts(t, cb, Counts{})
				if len(changes) != 1 {
					t.Fatal(changes)
				}
				if order == "state first" {
					identityState(t, cb, StateHalfOpen)
				}
				old(success)
				want := StateHalfOpen
				if order == "during open" {
					want = StateOpen
					if len(changes) != 1 {
						t.Fatal(changes)
					}
				} else if len(changes) != 2 || changes[1] != StateHalfOpen {
					t.Fatal(changes)
				}
				identityState(t, cb, want)
				identityCounts(t, cb, Counts{})
				if trips != 1 {
					t.Fatal(trips)
				}
			})
		}
	}
}

func TestIdentityClosedIntervalCompletion(t *testing.T) {
	for _, order := range []string{"completion first", "state first"} {
		for _, success := range []bool{true, false} {
			label := "/failure"
			if success {
				label = "/success"
			}
			t.Run(order+label, func(t *testing.T) {
				notifications, trips := 0, 0
				cb := NewTwoStepCircuitBreaker(Settings{Interval: identityWait, ReadyToTrip: func(Counts) bool { trips++; return false }, OnStateChange: func(string, State, State) { notifications++ }})
				old := identityDone(t, cb)
				time.Sleep(identityWait)
				identityCounts(t, cb, Counts{Requests: 1})
				if order == "state first" {
					identityState(t, cb, StateClosed)
				}
				old(success)
				identityCounts(t, cb, Counts{})
				if notifications != 0 || trips != 0 {
					t.Fatal(notifications, trips)
				}
			})
		}
	}
}

func TestIdentityClassifierAcrossTransition(t *testing.T) {
	for _, order := range []string{"fresh", "request blocked", "classifier blocked"} {
		for _, success := range []bool{true, false} {
			label := "/failure"
			if success {
				label = "/success"
			}
			t.Run(order+label, func(t *testing.T) {
				original, trip := errors.New("original"), errors.New("trip")
				started, release := make(chan struct{}), make(chan struct{})
				calls, classified := 0, 0
				cb := NewCircuitBreaker(Settings{Timeout: time.Hour, ReadyToTrip: func(c Counts) bool { calls++; return order != "fresh" },
					IsSuccessful: func(err error) bool {
						if err == trip {
							return false
						}
						if err != original {
							panic(err)
						}
						classified++
						if order == "classifier blocked" {
							close(started)
							<-release
						}
						return success
					}})
				request := func() (interface{}, error) {
					if order == "request blocked" {
						close(started)
						<-release
					}
					return "result", original
				}
				type pair struct {
					v interface{}
					e error
				}
				var result pair
				if order == "fresh" {
					result.v, result.e = cb.Execute(request)
				} else {
					finished := make(chan pair, 1)
					go func() { v, e := cb.Execute(request); finished <- pair{v, e} }()
					<-started
					cb.Execute(func() (interface{}, error) { return nil, trip })
					close(release)
					result = <-finished
				}
				if result.v != "result" || result.e != original || classified != 1 {
					t.Fatal(result, classified)
				}
				if order != "fresh" {
					identityState(t, cb, StateOpen)
					identityCounts(t, cb, Counts{})
					if calls != 1 {
						t.Fatal(calls)
					}
				} else if success {
					identityCounts(t, cb, Counts{Requests: 1, TotalSuccesses: 1, ConsecutiveSuccesses: 1})
					if calls != 0 {
						t.Fatal(calls)
					}
				} else {
					identityCounts(t, cb, Counts{Requests: 1, TotalFailures: 1, ConsecutiveFailures: 1})
					if calls != 1 {
						t.Fatal(calls)
					}
				}
			})
		}
	}
}

func identityPanicBoundary(t *testing.T, classifier bool) {
	t.Helper()
	for _, order := range []string{"fresh", "stale"} {
		t.Run(order, func(t *testing.T) {
			original, trip := errors.New("original"), errors.New("trip")
			started, release := make(chan struct{}), make(chan struct{})
			calls, classified := 0, 0
			block := func() {
				if order == "stale" {
					close(started)
					<-release
				}
			}
			cb := NewCircuitBreaker(Settings{Timeout: time.Hour,
				ReadyToTrip: func(Counts) bool { calls++; return order == "stale" },
				IsSuccessful: func(err error) bool {
					if err == trip {
						return false
					}
					classified++
					block()
					panic(original)
				}})
			execute := func() {
				cb.Execute(func() (interface{}, error) {
					if classifier {
						return "value", nil
					}
					block()
					panic(original)
				})
			}
			if order == "fresh" {
				identityPanic(t, execute, original)
				identityCounts(t, cb, Counts{Requests: 1, TotalFailures: 1, ConsecutiveFailures: 1})
			} else {
				recovered := make(chan interface{}, 1)
				go func() { defer func() { recovered <- recover() }(); execute() }()
				<-started
				cb.Execute(func() (interface{}, error) { return nil, trip })
				close(release)
				if got := <-recovered; got != original {
					t.Fatal(got)
				}
				identityState(t, cb, StateOpen)
				identityCounts(t, cb, Counts{})
			}
			if calls != 1 || (classifier && classified != 1) || (!classifier && classified != 0) {
				t.Fatal(calls, classified)
			}
		})
	}
}

func TestIdentityRequestPanicBoundary(t *testing.T)    { identityPanicBoundary(t, false) }
func TestIdentityClassifierPanicBoundary(t *testing.T) { identityPanicBoundary(t, true) }

func TestIdentityTripPanicRetry(t *testing.T) {
	first := errors.New("hook")
	var samples []Counts
	class := 0
	cb := NewCircuitBreaker(Settings{ReadyToTrip: func(c Counts) bool {
		samples = append(samples, c)
		if len(samples) == 1 {
			panic(first)
		}
		return false
	},
		IsSuccessful: func(error) bool { class++; return false }})
	identityPanic(t, func() { cb.Execute(func() (interface{}, error) { return nil, errors.New("request") }) }, first)
	identityCounts(t, cb, Counts{Requests: 1, TotalFailures: 2, ConsecutiveFailures: 2})
	if class != 1 || len(samples) != 2 || samples[0].TotalFailures != 1 || samples[1].TotalFailures != 2 {
		t.Fatal(class, samples)
	}
}

func TestIdentityPanicReplacement(t *testing.T) {
	for _, order := range []string{"request", "classifier", "retry"} {
		t.Run(order, func(t *testing.T) {
			first, replacement := errors.New("first"), errors.New("replacement")
			calls := 0
			cb := NewCircuitBreaker(Settings{ReadyToTrip: func(Counts) bool {
				calls++
				if order == "retry" && calls == 1 {
					panic(first)
				}
				panic(replacement)
			},
				IsSuccessful: func(error) bool {
					if order == "classifier" {
						panic(first)
					}
					return false
				}})
			identityPanic(t, func() {
				cb.Execute(func() (interface{}, error) {
					if order == "request" {
						panic(first)
					}
					return nil, nil
				})
			}, replacement)
			want := uint32(1)
			if order == "retry" {
				want = 2
			}
			identityCounts(t, cb, Counts{Requests: 1, TotalFailures: want, ConsecutiveFailures: want})
			if calls != int(want) {
				t.Fatal(calls)
			}
		})
	}
}

func TestIdentityTwoStepTripPanic(t *testing.T) {
	hook := errors.New("hook")
	calls := 0
	cb := NewTwoStepCircuitBreaker(Settings{ReadyToTrip: func(Counts) bool {
		calls++
		if calls == 1 {
			panic(hook)
		}
		return false
	}})
	done := identityDone(t, cb)
	identityPanic(t, func() { done(false) }, hook)
	identityCounts(t, cb, Counts{Requests: 1, TotalFailures: 1, ConsecutiveFailures: 1})
	if calls != 1 {
		t.Fatal(calls)
	}
	done(false)
	identityCounts(t, cb, Counts{Requests: 1, TotalFailures: 2, ConsecutiveFailures: 2})
	if calls != 2 {
		t.Fatal(calls)
	}
}

func TestIdentityStateHookPanicAfterCommit(t *testing.T) {
	for _, entry := range []string{"Execute", "Allow"} {
		t.Run(entry, func(t *testing.T) {
			hook := errors.New("hook")
			trips, notifications := 0, 0
			s := Settings{Timeout: time.Hour, ReadyToTrip: func(Counts) bool { trips++; return true }, OnStateChange: func(string, State, State) { notifications++; panic(hook) }}
			if entry == "Execute" {
				cb := NewCircuitBreaker(s)
				identityPanic(t, func() { cb.Execute(func() (interface{}, error) { return nil, errors.New("result") }) }, hook)
				identityState(t, cb, StateOpen)
				identityCounts(t, cb, Counts{})
			} else {
				cb := NewTwoStepCircuitBreaker(s)
				done := identityDone(t, cb)
				identityPanic(t, func() { done(false) }, hook)
				identityState(t, cb, StateOpen)
				done(false)
				done(true)
				identityCounts(t, cb, Counts{})
			}
			if trips != 1 || notifications != 1 {
				t.Fatal(trips, notifications)
			}
		})
	}
}

func TestIdentityStateHookPanicExpires(t *testing.T) {
	for _, secondPanics := range []bool{false, true} {
		label := "second returns"
		if secondPanics {
			label = "second panics"
		}
		t.Run(label, func(t *testing.T) {
			first, second := errors.New("open hook"), errors.New("half-open hook")
			want := first
			if secondPanics {
				want = second
			}
			var notifications []State
			cb := NewCircuitBreaker(Settings{Timeout: identityWait, ReadyToTrip: identityTrip, OnStateChange: func(_ string, _ State, to State) {
				notifications = append(notifications, to)
				if to == StateOpen {
					time.Sleep(identityWait)
					panic(first)
				}
				if secondPanics {
					panic(second)
				}
			}})
			identityPanic(t, func() { cb.Execute(func() (interface{}, error) { return nil, errors.New("result") }) }, want)
			if len(notifications) != 2 || notifications[0] != StateOpen || notifications[1] != StateHalfOpen {
				t.Fatal(notifications)
			}
			identityState(t, cb, StateHalfOpen)
			identityCounts(t, cb, Counts{})
		})
	}
}

func TestIdentityAdmissionHookPanic(t *testing.T) {
	for _, entry := range []string{"Execute", "Allow"} {
		t.Run(entry, func(t *testing.T) {
			hook := errors.New("hook")
			calls, class := 0, 0
			s := Settings{Timeout: identityWait, ReadyToTrip: identityTrip, IsSuccessful: func(err error) bool { class++; return err == nil }, OnStateChange: func(_ string, _ State, to State) {
				if to == StateHalfOpen {
					panic(hook)
				}
			}}
			if entry == "Execute" {
				cb := NewCircuitBreaker(s)
				cb.Execute(func() (interface{}, error) { return nil, errors.New("trip") })
				time.Sleep(identityWait)
				req := func() (interface{}, error) { calls++; return 17, nil }
				identityPanic(t, func() { cb.Execute(req) }, hook)
				identityCounts(t, cb, Counts{})
				if calls != 0 || class != 1 {
					t.Fatal(calls, class)
				}
				v, e := cb.Execute(req)
				if v != 17 || e != nil || calls != 1 || class != 2 {
					t.Fatal(v, e, calls, class)
				}
				identityState(t, cb, StateClosed)
			} else {
				cb := NewTwoStepCircuitBreaker(s)
				identityDone(t, cb)(false)
				time.Sleep(identityWait)
				identityPanic(t, func() { cb.Allow() }, hook)
				identityCounts(t, cb, Counts{})
				identityDone(t, cb)(true)
				identityState(t, cb, StateClosed)
			}
		})
	}
}

func TestIdentityStaleOpenHookPanic(t *testing.T) {
	for _, success := range []bool{true, false} {
		label := "failure"
		if success {
			label = "success"
		}
		t.Run(label, func(t *testing.T) {
			hook := errors.New("hook")
			notifications := 0
			cb := NewTwoStepCircuitBreaker(Settings{Timeout: identityWait, ReadyToTrip: identityTrip, OnStateChange: func(_ string, _ State, to State) {
				if to == StateHalfOpen {
					notifications++
					panic(hook)
				}
			}})
			stale := identityDone(t, cb)
			identityDone(t, cb)(false)
			time.Sleep(identityWait)
			identityPanic(t, func() { stale(success) }, hook)
			identityState(t, cb, StateHalfOpen)
			stale(success)
			identityCounts(t, cb, Counts{})
			if notifications != 1 {
				t.Fatal(notifications)
			}
			identityDone(t, cb)(true)
			identityState(t, cb, StateClosed)
		})
	}
}

func TestIdentityExecuteGoexit(t *testing.T) {
	for _, order := range []string{"request", "classifier"} {
		t.Run(order, func(t *testing.T) {
			trip := errors.New("trip")
			cb := NewCircuitBreaker(Settings{Timeout: identityWait, ReadyToTrip: identityTrip, IsSuccessful: func(err error) bool {
				if err == trip {
					return false
				}
				runtime.Goexit()
				return false
			}})
			cb.Execute(func() (interface{}, error) { return nil, trip })
			time.Sleep(identityWait)
			finished := make(chan struct{})
			returned := make(chan struct{}, 1)
			go func() {
				defer close(finished)
				cb.Execute(func() (interface{}, error) {
					if order == "request" {
						runtime.Goexit()
					}
					return "value", nil
				})
				returned <- struct{}{}
			}()
			<-finished
			if len(returned) != 0 {
				t.Fatal("Execute returned")
			}
			identityState(t, cb, StateHalfOpen)
			identityCounts(t, cb, Counts{Requests: 1})
			_, err := cb.Execute(func() (interface{}, error) { t.Error("rejected request ran"); return nil, nil })
			if err != ErrTooManyRequests {
				t.Fatal(err)
			}
		})
	}
}

func TestIdentityReassignedReceiver(t *testing.T) {
	for _, order := range []string{"equal", "different"} {
		t.Run(order, func(t *testing.T) {
			cb := NewTwoStepCircuitBreaker(Settings{})
			oldValue := *cb
			old := identityDone(t, cb)
			target := NewTwoStepCircuitBreaker(Settings{ReadyToTrip: identityTrip, Timeout: time.Hour})
			if order == "different" {
				identityDone(t, target)(false)
			}
			*cb = *target
			old(true)
			if order == "equal" {
				identityCounts(t, target, Counts{TotalSuccesses: 1, ConsecutiveSuccesses: 1})
			} else {
				identityState(t, target, StateOpen)
				identityCounts(t, target, Counts{})
			}
			identityCounts(t, &oldValue, Counts{Requests: 1})
		})
	}
}

func TestIdentityTripHookAcrossExpiry(t *testing.T) {
	for _, opens := range []bool{false, true} {
		label := "false"
		if opens {
			label = "true"
		}
		t.Run(label, func(t *testing.T) {
			cb := NewCircuitBreaker(Settings{Interval: identityWait, Timeout: identityWait,
				ReadyToTrip: func(c Counts) bool {
					if c.TotalFailures != 1 {
						t.Errorf("hook counts %+v", c)
					}
					time.Sleep(2 * identityWait)
					return opens
				}})
			cb.Execute(func() (interface{}, error) { return nil, errors.New("failure") })
			if opens {
				identityCounts(t, cb, Counts{})
				identityState(t, cb, StateHalfOpen)
			} else {
				identityCounts(t, cb, Counts{Requests: 1, TotalFailures: 1, ConsecutiveFailures: 1})
				identityState(t, cb, StateClosed)
				identityCounts(t, cb, Counts{})
			}
		})
	}
}

func TestIdentityTripPanicAfterInterval(t *testing.T) {
	hook := errors.New("trip")
	calls := 0
	cb := NewCircuitBreaker(Settings{Interval: 100 * time.Millisecond, ReadyToTrip: func(c Counts) bool {
		calls++
		if c.TotalFailures != 1 {
			t.Errorf("counts %+v", c)
		}
		time.Sleep(100 * time.Millisecond)
		panic(hook)
	}})
	identityPanic(t, func() { cb.Execute(func() (interface{}, error) { return nil, errors.New("request") }) }, hook)
	if calls != 1 {
		t.Fatal(calls)
	}
	identityCounts(t, cb, Counts{})
	identityState(t, cb, StateClosed)
}

func TestIdentityHalfOpenNotificationPanic(t *testing.T) {
	for _, success := range []bool{true, false} {
		for _, mode := range []string{"Execute", "Allow"} {
			label := mode + "/failure"
			if success {
				label = mode + "/success"
			}
			t.Run(label, func(t *testing.T) {
				open, hook := errors.New("open"), errors.New("hook")
				var transitions []State
				var tripCalls int
				s := Settings{Timeout: identityWait, ReadyToTrip: func(Counts) bool { tripCalls++; return true },
					OnStateChange: func(_ string, from, to State) {
						transitions = append(transitions, to)
						if from == StateHalfOpen {
							panic(hook)
						}
					}}
				want := StateOpen
				if success {
					want = StateClosed
				}
				if mode == "Execute" {
					cb := NewCircuitBreaker(s)
					cb.Execute(func() (interface{}, error) { return nil, open })
					time.Sleep(identityWait)
					identityState(t, cb, StateHalfOpen)
					identityPanic(t, func() {
						cb.Execute(func() (interface{}, error) {
							if success {
								return 1, nil
							}
							return 1, open
						})
					}, hook)
					if len(transitions) != 3 || transitions[2] != want {
						t.Fatal(transitions)
					}
					identityCounts(t, cb, Counts{})
				} else {
					cb := NewTwoStepCircuitBreaker(s)
					identityDone(t, cb)(false)
					time.Sleep(identityWait)
					identityState(t, cb, StateHalfOpen)
					done := identityDone(t, cb)
					identityPanic(t, func() { done(success) }, hook)
					if len(transitions) != 3 || transitions[2] != want {
						t.Fatal(transitions)
					}
					if success {
						done(false)
						done(true)
					}
					identityCounts(t, cb, Counts{})
				}
				if tripCalls != 1 {
					t.Fatal(tripCalls)
				}
			})
		}
	}
}

func TestIdentityExecuteDepartedWaiter(t *testing.T) {
	for _, order := range []string{"no result", "success", "failure", "stale success", "stale failure"} {
		t.Run(order, func(t *testing.T) {
			closedFailure, lateFailure := errors.New("open"), errors.New("late")
			cb := NewCircuitBreaker(Settings{Timeout: identityWait, ReadyToTrip: identityTrip})
			cb.Execute(func() (interface{}, error) { return nil, closedFailure })
			time.Sleep(identityWait)
			identityState(t, cb, StateHalfOpen)
			started := make(chan struct{})
			type pair struct {
				value interface{}
				err   error
			}
			producer := make(chan pair, 1)
			delivered := make(chan pair, 1)
			cancelWait := make(chan struct{})
			waiterGone := make(chan bool, 1)
			workerGone := make(chan struct{})
			var worker *CircuitBreaker = cb
			stale := order == "stale success" || order == "stale failure"
			if stale {
				worker = NewCircuitBreaker(Settings{Timeout: time.Hour, ReadyToTrip: identityTrip})
			}
			go func() {
				defer close(workerGone)
				v, e := worker.Execute(func() (interface{}, error) {
					close(started)
					reply, ok := <-producer
					if !ok {
						runtime.Goexit()
					}
					return reply.value, reply.err
				})
				delivered <- pair{v, e}
			}()
			<-started
			go func() {
				select {
				case <-delivered:
					waiterGone <- false
				case <-cancelWait:
					waiterGone <- true
				}
			}()
			close(cancelWait)
			if !<-waiterGone {
				t.Fatal("waiter consumed result before cancellation")
			}
			if order == "no result" {
				time.Sleep(2 * identityWait)
				identityState(t, cb, StateHalfOpen)
				identityCounts(t, cb, Counts{Requests: 1})
				_, err := cb.Execute(func() (interface{}, error) { t.Error("rejected body ran"); return nil, nil })
				if err != ErrTooManyRequests {
					t.Fatal(err)
				}
				close(producer)
				<-workerGone
				if len(delivered) != 0 {
					t.Fatal("unexpected result")
				}
				return
			}
			if stale {
				worker.Execute(func() (interface{}, error) { return nil, closedFailure })
			}
			reply := pair{value: "late"}
			if order == "failure" || order == "stale failure" {
				reply.err = lateFailure
			}
			producer <- reply
			<-workerGone
			if len(delivered) != 1 {
				t.Fatal("missing buffered result")
			}
			if got := <-delivered; got != reply {
				t.Fatal(got, reply)
			}
			identityCounts(t, worker, Counts{})
			if stale {
				identityState(t, worker, StateOpen)
			} else if order == "success" {
				identityState(t, worker, StateClosed)
			} else {
				_, err := worker.Execute(func() (interface{}, error) { t.Error("rejected body ran"); return nil, nil })
				if err != ErrOpenState {
					t.Fatal(err)
				}
			}
		})
	}
}
