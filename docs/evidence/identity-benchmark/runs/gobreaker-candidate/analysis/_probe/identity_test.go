package gobreaker_test

import (
	"errors"
	"reflect"
	"testing"
	"time"

	gb "github.com/sony/gobreaker"
)

var identityErr = errors.New("identity")

const identityWindow = 80 * time.Millisecond

func identityAllow(t *testing.T, b *gb.TwoStepCircuitBreaker) func(bool) {
	t.Helper()
	done, err := b.Allow()
	if err != nil || done == nil {
		t.Fatalf("admission: %v", err)
	}
	return done
}

func identityReject(t *testing.T, b *gb.TwoStepCircuitBreaker, want error) {
	t.Helper()
	done, err := b.Allow()
	if done != nil || err != want {
		t.Fatalf("admission: done present=%t, err=%v, want %v", done != nil, err, want)
	}
}

func identityCounts(t *testing.T, got, want gb.Counts) {
	t.Helper()
	if got != want {
		t.Fatalf("counts: got %+v, want %+v", got, want)
	}
}

func identityState(t *testing.T, got, want gb.State) {
	t.Helper()
	if got != want {
		t.Fatalf("state: got %v, want %v", got, want)
	}
}

func identityPanic(t *testing.T, fn func()) (value interface{}) {
	t.Helper()
	defer func() {
		value = recover()
		if value == nil {
			t.Error("expected panic")
		}
	}()
	fn()
	return
}

func identityFailure(n uint32) gb.Counts {
	return gb.Counts{Requests: 1, TotalFailures: n, ConsecutiveFailures: n}
}

func identitySuccess(n uint32) gb.Counts {
	return gb.Counts{Requests: 1, TotalSuccesses: n, ConsecutiveSuccesses: n}
}

func identityBoth(t *testing.T, fn func(*testing.T, bool)) {
	t.Helper()
	for _, tc := range []struct {
		name    string
		success bool
	}{{"success", true}, {"failure", false}} {
		t.Run(tc.name, func(t *testing.T) { fn(t, tc.success) })
	}
}

func identityTrip(gb.Counts) bool { return true }

func TestIdentityWrapperReplacement(t *testing.T) {
	identityBoth(t, func(t *testing.T, success bool) {
		aCalls, bCalls := 0, 0
		a := gb.NewTwoStepCircuitBreaker(gb.Settings{ReadyToTrip: func(gb.Counts) bool { aCalls++; return false }})
		b := gb.NewTwoStepCircuitBreaker(gb.Settings{ReadyToTrip: func(c gb.Counts) bool {
			bCalls++
			identityCounts(t, c, gb.Counts{TotalFailures: 1, ConsecutiveFailures: 1})
			return false
		}})
		done := identityAllow(t, a)
		alias := *a
		*a = *b
		done(success)
		identityCounts(t, alias.Counts(), gb.Counts{Requests: 1})
		want := gb.Counts{TotalFailures: 1, ConsecutiveFailures: 1}
		calls := 1
		if success {
			want, calls = gb.Counts{TotalSuccesses: 1, ConsecutiveSuccesses: 1}, 0
		}
		identityCounts(t, b.Counts(), want)
		identityCounts(t, a.Counts(), want)
		if aCalls != 0 || bCalls != calls {
			t.Fatalf("trip calls A=%d B=%d", aCalls, bCalls)
		}
		identityAllow(t, b)(true)
		if b.Counts().Requests != 1 {
			t.Fatal("B retry did not admit")
		}
	})
}

func TestIdentityWrapperCopyAndRebind(t *testing.T) {
	a := gb.NewTwoStepCircuitBreaker(gb.Settings{})
	b := gb.NewTwoStepCircuitBreaker(gb.Settings{})
	w := a
	alias := *w
	first := identityAllow(t, w)
	second := identityAllow(t, &alias)
	w = b
	first(true)
	second(false)
	want := gb.Counts{Requests: 2, TotalSuccesses: 1, TotalFailures: 1, ConsecutiveFailures: 1}
	identityCounts(t, a.Counts(), want)
	identityCounts(t, alias.Counts(), want)
	identityCounts(t, w.Counts(), gb.Counts{})
}

func TestIdentityWrapperMismatch(t *testing.T) {
	identityBoth(t, func(t *testing.T, success bool) {
		w := gb.NewTwoStepCircuitBreaker(gb.Settings{})
		b := gb.NewTwoStepCircuitBreaker(gb.Settings{ReadyToTrip: identityTrip})
		done := identityAllow(t, w)
		alias := *w
		identityAllow(t, b)(false)
		*w = *b
		done(success)
		identityReject(t, w, gb.ErrOpenState)
		identityCounts(t, b.Counts(), gb.Counts{})
		identityCounts(t, alias.Counts(), gb.Counts{Requests: 1})
	})
}

func TestIdentityWrapperLazyBoundary(t *testing.T) {
	identityBoth(t, func(t *testing.T, success bool) {
		w := gb.NewTwoStepCircuitBreaker(gb.Settings{})
		var events []gb.State
		b := gb.NewTwoStepCircuitBreaker(gb.Settings{
			ReadyToTrip: identityTrip, Timeout: identityWindow,
			OnStateChange: func(_ string, _, to gb.State) { events = append(events, to) },
		})
		done := identityAllow(t, w)
		alias := *w
		identityAllow(t, b)(false)
		*w = *b
		time.Sleep(2 * identityWindow)
		if len(events) != 1 {
			t.Fatalf("events before completion: %v", events)
		}
		done(success)
		if !reflect.DeepEqual(events, []gb.State{gb.StateOpen, gb.StateHalfOpen}) {
			t.Fatalf("events: %v", events)
		}
		identityCounts(t, b.Counts(), gb.Counts{})
		identityCounts(t, alias.Counts(), gb.Counts{Requests: 1})
		identityAllow(t, b)
		identityCounts(t, b.Counts(), gb.Counts{Requests: 1})
	})
}

func identityWrapperHalfOpen(t *testing.T, success bool) {
	settings := gb.Settings{ReadyToTrip: identityTrip, Timeout: identityWindow}
	w := gb.NewTwoStepCircuitBreaker(settings)
	var events []gb.State
	settings.OnStateChange = func(_ string, _, to gb.State) { events = append(events, to) }
	b := gb.NewTwoStepCircuitBreaker(settings)
	identityAllow(t, w)(false)
	identityAllow(t, b)(false)
	time.Sleep(2 * identityWindow)
	done := identityAllow(t, w)
	alias := *w
	*w = *b
	done(success)
	want := gb.StateOpen
	if success {
		want = gb.StateClosed
	}
	if !reflect.DeepEqual(events, []gb.State{gb.StateOpen, gb.StateHalfOpen, want}) {
		t.Fatalf("events: %v", events)
	}
	identityCounts(t, b.Counts(), gb.Counts{})
	identityCounts(t, alias.Counts(), gb.Counts{Requests: 1})
	identityState(t, alias.State(), gb.StateHalfOpen)
	identityReject(t, &alias, gb.ErrTooManyRequests)
	if success {
		identityAllow(t, b)
	} else {
		identityReject(t, b, gb.ErrOpenState)
	}
}

func TestIdentityWrapperHalfOpenSuccess(t *testing.T) { identityWrapperHalfOpen(t, true) }
func TestIdentityWrapperHalfOpenFailure(t *testing.T) { identityWrapperHalfOpen(t, false) }

func TestIdentityWrapperZero(t *testing.T) {
	identityBoth(t, func(t *testing.T, success bool) {
		w := gb.NewTwoStepCircuitBreaker(gb.Settings{})
		done := identityAllow(t, w)
		alias := *w
		*w = gb.TwoStepCircuitBreaker{}
		identityPanic(t, func() { done(success) })
		identityCounts(t, alias.Counts(), gb.Counts{Requests: 1})
	})
}

func TestIdentityExecuteReceiver(t *testing.T) {
	identityBoth(t, func(t *testing.T, success bool) {
		for _, overwrite := range []bool{false, true} {
			aClass, newClass, aTrip, newTrip := 0, 0, 0, 0
			a := gb.NewCircuitBreaker(gb.Settings{
				IsSuccessful: func(error) bool { aClass++; return success },
				ReadyToTrip:  func(gb.Counts) bool { aTrip++; return false },
			})
			b := gb.NewCircuitBreaker(gb.Settings{
				IsSuccessful: func(error) bool { newClass++; return success },
				ReadyToTrip: func(c gb.Counts) bool {
					newTrip++
					identityCounts(t, c, gb.Counts{TotalFailures: 1, ConsecutiveFailures: 1})
					return false
				},
			})
			w := a
			value, err := w.Execute(func() (interface{}, error) {
				if overwrite {
					*a = *b
				} else {
					w = b
				}
				return "payload", identityErr
			})
			if value != "payload" || err != identityErr {
				t.Fatalf("result: %v %v", value, err)
			}
			want := identityFailure(1)
			failCalls := 1
			if success {
				want, failCalls = identitySuccess(1), 0
			}
			if overwrite {
				want.Requests = 0
				if newClass != 1 || aClass != 0 || newTrip != failCalls || aTrip != 0 {
					t.Fatal("wrong hook recipient after overwrite")
				}
			} else if aClass != 1 || newClass != 0 || aTrip != failCalls || newTrip != 0 {
				t.Fatal("wrong hook recipient after rebinding")
			}
			identityCounts(t, a.Counts(), want)
			identityCounts(t, b.Counts(), gb.Counts{})
		}
	})
}

func TestIdentityRepeatedClosed(t *testing.T) {
	b := gb.NewTwoStepCircuitBreaker(gb.Settings{ReadyToTrip: func(gb.Counts) bool { return false }})
	done := identityAllow(t, b)
	copyDone := done
	done(true)
	copyDone(false)
	done(false)
	want := identityFailure(2)
	want.TotalSuccesses = 1
	identityCounts(t, b.Counts(), want)
}

func TestIdentityRepeatedHalfOpen(t *testing.T) {
	b := gb.NewTwoStepCircuitBreaker(gb.Settings{MaxRequests: 2, ReadyToTrip: identityTrip, Timeout: identityWindow})
	identityAllow(t, b)(false)
	time.Sleep(2 * identityWindow)
	done := identityAllow(t, b)
	done(true)
	identityState(t, b.State(), gb.StateHalfOpen)
	identityCounts(t, b.Counts(), identitySuccess(1))
	done(true)
	identityState(t, b.State(), gb.StateClosed)
	done(false)
	identityCounts(t, b.Counts(), gb.Counts{})
}

func TestIdentityAbandonedHalfOpen(t *testing.T) {
	identityBoth(t, func(t *testing.T, success bool) {
		b := gb.NewTwoStepCircuitBreaker(gb.Settings{ReadyToTrip: identityTrip, Timeout: identityWindow})
		identityAllow(t, b)(false)
		time.Sleep(2 * identityWindow)
		done := identityAllow(t, b)
		time.Sleep(2 * identityWindow)
		identityReject(t, b, gb.ErrTooManyRequests)
		identityState(t, b.State(), gb.StateHalfOpen)
		identityCounts(t, b.Counts(), gb.Counts{Requests: 1})
		done(success)
		identityCounts(t, b.Counts(), gb.Counts{})
		if success {
			identityState(t, b.State(), gb.StateClosed)
			identityAllow(t, b)
		} else {
			identityReject(t, b, gb.ErrOpenState)
		}
	})
}

func TestIdentityStaleHalfOpen(t *testing.T) {
	identityBoth(t, func(t *testing.T, success bool) {
		var events []gb.State
		b := gb.NewTwoStepCircuitBreaker(gb.Settings{
			ReadyToTrip: identityTrip, MaxRequests: 2, Timeout: identityWindow,
			OnStateChange: func(_ string, _, to gb.State) { events = append(events, to) },
		})
		identityAllow(t, b)(false)
		time.Sleep(2 * identityWindow)
		first, second := identityAllow(t, b), identityAllow(t, b)
		first(false)
		second(success)
		identityReject(t, b, gb.ErrOpenState)
		identityCounts(t, b.Counts(), gb.Counts{})
		if !reflect.DeepEqual(events, []gb.State{gb.StateOpen, gb.StateHalfOpen, gb.StateOpen}) {
			t.Fatalf("events: %v", events)
		}
	})
}

func TestIdentityClosedExpiry(t *testing.T) {
	identityBoth(t, func(t *testing.T, success bool) {
		for _, mode := range []string{"before", "expiry-by-State", "expiry-by-done"} {
			t.Run(mode, func(t *testing.T) {
				trips, events := 0, 0
				b := gb.NewTwoStepCircuitBreaker(gb.Settings{
					Interval:      identityWindow,
					ReadyToTrip:   func(gb.Counts) bool { trips++; return false },
					OnStateChange: func(string, gb.State, gb.State) { events++ },
				})
				done := identityAllow(t, b)
				if mode != "before" {
					time.Sleep(2 * identityWindow)
					identityCounts(t, b.Counts(), gb.Counts{Requests: 1})
					if mode == "expiry-by-State" {
						identityState(t, b.State(), gb.StateClosed)
						identityCounts(t, b.Counts(), gb.Counts{})
					}
				}
				done(success)
				want := gb.Counts{}
				tripCalls := 0
				if mode == "before" {
					if success {
						want = identitySuccess(1)
					} else {
						want, tripCalls = identityFailure(1), 1
					}
				}
				identityCounts(t, b.Counts(), want)
				if events != 0 || trips != tripCalls {
					t.Fatalf("events=%d trips=%d", events, trips)
				}
			})
		}
	})
}

type identityResult struct {
	value interface{}
	err   error
}

func TestIdentityDepartedExecute(t *testing.T) {
	identityBoth(t, func(t *testing.T, success bool) {
		for _, stale := range []bool{false, true} {
			b := gb.NewCircuitBreaker(gb.Settings{ReadyToTrip: func(c gb.Counts) bool { return stale && c.Requests == 2 }})
			started, release, leave, left := make(chan struct{}), make(chan struct{}), make(chan struct{}), make(chan struct{})
			results := make(chan identityResult, 1)
			requestErr := identityErr
			if success {
				requestErr = nil
			}
			go func() {
				select {
				case <-leave:
					close(left)
				case <-results:
				}
			}()
			go func() {
				value, err := b.Execute(func() (interface{}, error) { close(started); <-release; return "payload", requestErr })
				results <- identityResult{value, err}
			}()
			<-started
			close(leave)
			<-left
			identityCounts(t, b.Counts(), gb.Counts{Requests: 1})
			if stale {
				_, _ = b.Execute(func() (interface{}, error) { return nil, identityErr })
			}
			close(release)
			got := <-results
			if got.value != "payload" || got.err != requestErr {
				t.Fatalf("result: %+v", got)
			}
			want := gb.Counts{}
			if !stale {
				if success {
					want = identitySuccess(1)
				} else {
					want = identityFailure(1)
				}
			}
			identityCounts(t, b.Counts(), want)
		}
	})
}

func TestIdentityClassifierOrdering(t *testing.T) {
	identityBoth(t, func(t *testing.T, success bool) {
		for _, boundaryDuringClassifier := range []bool{false, true} {
			entered, release := make(chan struct{}), make(chan struct{})
			classifiedAt := make(chan gb.State, 1)
			results := make(chan identityResult, 1)
			tripErr := errors.New("trip")
			var b *gb.CircuitBreaker
			b = gb.NewCircuitBreaker(gb.Settings{
				ReadyToTrip: identityTrip,
				IsSuccessful: func(err error) bool {
					if err == tripErr {
						return false
					}
					_ = b.Counts()
					classifiedAt <- b.State()
					if boundaryDuringClassifier {
						close(entered)
						<-release
					}
					return success
				},
			})
			go func() {
				value, err := b.Execute(func() (interface{}, error) {
					if !boundaryDuringClassifier {
						close(entered)
						<-release
					}
					return "payload", identityErr
				})
				results <- identityResult{value, err}
			}()
			<-entered
			_, _ = b.Execute(func() (interface{}, error) { return nil, tripErr })
			identityState(t, b.State(), gb.StateOpen)
			close(release)
			got := <-results
			if got.value != "payload" || got.err != identityErr {
				t.Fatalf("result: %+v", got)
			}
			want := gb.StateOpen
			if boundaryDuringClassifier {
				want = gb.StateClosed
			}
			identityState(t, <-classifiedAt, want)
			identityCounts(t, b.Counts(), gb.Counts{})
		}
	})
}

func TestIdentityRequestAndClassifierPanic(t *testing.T) {
	for _, classifierPanic := range []bool{false, true} {
		for _, stale := range []bool{false, true} {
			tripErr := errors.New("trip")
			classifications := 0
			b := gb.NewCircuitBreaker(gb.Settings{
				ReadyToTrip: func(c gb.Counts) bool { return stale && c.Requests == 2 },
				IsSuccessful: func(err error) bool {
					if err == tripErr {
						return false
					}
					classifications++
					panic("original")
				},
			})
			panicValue := identityPanic(t, func() {
				_, _ = b.Execute(func() (interface{}, error) {
					if stale {
						_, _ = b.Execute(func() (interface{}, error) { return nil, tripErr })
					}
					if !classifierPanic {
						panic("original")
					}
					return nil, identityErr
				})
			})
			if panicValue != "original" {
				t.Fatalf("panic: %v", panicValue)
			}
			wantCalls := 0
			if classifierPanic {
				wantCalls = 1
			}
			if classifications != wantCalls {
				t.Fatalf("classifier calls=%d", classifications)
			}
			want := identityFailure(1)
			if stale {
				want = gb.Counts{}
			}
			identityCounts(t, b.Counts(), want)
		}
	}
}

func TestIdentityTripHookRetry(t *testing.T) {
	calls := 0
	settings := gb.Settings{ReadyToTrip: func(c gb.Counts) bool {
		calls++
		identityCounts(t, c, identityFailure(uint32(calls)))
		if calls == 1 {
			panic("first")
		}
		return false
	}}
	a := gb.NewTwoStepCircuitBreaker(settings)
	done := identityAllow(t, a)
	if got := identityPanic(t, func() { done(false) }); got != "first" {
		t.Fatalf("panic: %v", got)
	}
	identityCounts(t, a.Counts(), identityFailure(1))
	calls = 0
	b := gb.NewCircuitBreaker(settings)
	got := identityPanic(t, func() { _, _ = b.Execute(func() (interface{}, error) { return nil, identityErr }) })
	if got != "first" || calls != 2 {
		t.Fatalf("panic=%v calls=%d", got, calls)
	}
	identityCounts(t, b.Counts(), identityFailure(2))
	identityState(t, b.State(), gb.StateClosed)
}

func TestIdentityTripHookReplacementPanic(t *testing.T) {
	calls := 0
	b := gb.NewCircuitBreaker(gb.Settings{ReadyToTrip: func(gb.Counts) bool {
		calls++
		if calls == 1 {
			panic("first")
		}
		panic("second")
	}})
	got := identityPanic(t, func() { _, _ = b.Execute(func() (interface{}, error) { return nil, identityErr }) })
	if got != "second" || calls != 2 {
		t.Fatalf("panic=%v calls=%d", got, calls)
	}
	identityCounts(t, b.Counts(), identityFailure(2))
}

func TestIdentityCompletionHookPanic(t *testing.T) {
	for _, tc := range []struct {
		name     string
		from, to gb.State
		success  bool
	}{
		{"closed-open", gb.StateClosed, gb.StateOpen, false},
		{"half-open-open", gb.StateHalfOpen, gb.StateOpen, false},
		{"half-open-closed", gb.StateHalfOpen, gb.StateClosed, true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			for _, direct := range []bool{true, false} {
				armed, calls := false, 0
				st := gb.Settings{
					ReadyToTrip: identityTrip, Timeout: identityWindow,
					OnStateChange: func(_ string, from, to gb.State) {
						if armed && from == tc.from && to == tc.to {
							calls++
							panic("transition")
						}
					},
				}
				tripReq := func() (interface{}, error) { return nil, identityErr }
				var counts func() gb.Counts
				var state func() gb.State
				var complete func()
				if direct {
					b := gb.NewCircuitBreaker(st)
					counts, state = b.Counts, b.State
					if tc.from == gb.StateHalfOpen {
						_, _ = b.Execute(tripReq)
						time.Sleep(2 * identityWindow)
						identityState(t, state(), tc.from)
					}
					complete = func() {
						_, _ = b.Execute(func() (interface{}, error) {
							if tc.success {
								return nil, nil
							}
							return tripReq()
						})
					}
				} else {
					b := gb.NewTwoStepCircuitBreaker(st)
					counts, state = b.Counts, b.State
					if tc.from == gb.StateHalfOpen {
						identityAllow(t, b)(false)
						time.Sleep(2 * identityWindow)
						identityState(t, state(), tc.from)
					}
					done := identityAllow(t, b)
					complete = func() { done(tc.success) }
				}
				armed = true
				if got := identityPanic(t, complete); got != "transition" {
					t.Fatalf("panic: %v", got)
				}
				identityCounts(t, counts(), gb.Counts{})
				identityState(t, state(), tc.to)
				if calls != 1 {
					t.Fatalf("notifications=%d", calls)
				}
			}
		})
	}
}

func TestIdentityAdmissionHookPanic(t *testing.T) {
	for _, mode := range []string{"state", "execute", "allow"} {
		t.Run(mode, func(t *testing.T) {
			calls := 0
			st := gb.Settings{ReadyToTrip: identityTrip, Timeout: identityWindow,
				OnStateChange: func(_ string, _, to gb.State) {
					if to == gb.StateHalfOpen {
						calls++
						panic("entry")
					}
				},
			}
			req := func() (interface{}, error) { return nil, identityErr }
			var first, retry func()
			var state func() gb.State
			var counts func() gb.Counts
			if mode == "allow" {
				b := gb.NewTwoStepCircuitBreaker(st)
				identityAllow(t, b)(false)
				state, counts = b.State, b.Counts
				first = func() { _, _ = b.Allow() }
				retry = func() { identityAllow(t, b); identityCounts(t, counts(), gb.Counts{Requests: 1}) }
			} else {
				b := gb.NewCircuitBreaker(st)
				_, _ = b.Execute(req)
				state, counts = b.State, b.Counts
				first = func() {
					_, _ = b.Execute(func() (interface{}, error) { t.Error("request ran before admission"); return nil, nil })
				}
				if mode == "state" {
					first = func() { _ = b.State() }
				}
				retry = func() {
					_, err := b.Execute(func() (interface{}, error) { identityCounts(t, counts(), gb.Counts{Requests: 1}); return nil, nil })
					if err != nil {
						t.Fatalf("retry error: %v", err)
					}
				}
			}
			time.Sleep(2 * identityWindow)
			if got := identityPanic(t, first); got != "entry" {
				t.Fatalf("panic: %v", got)
			}
			identityCounts(t, counts(), gb.Counts{})
			identityState(t, state(), gb.StateHalfOpen)
			retry()
			if calls != 1 {
				t.Fatalf("notifications=%d", calls)
			}
		})
	}
}

func TestIdentityStaleHookPanic(t *testing.T) {
	identityBoth(t, func(t *testing.T, success bool) {
		calls := 0
		b := gb.NewTwoStepCircuitBreaker(gb.Settings{
			ReadyToTrip: identityTrip, Timeout: identityWindow,
			OnStateChange: func(_ string, _, to gb.State) {
				if to == gb.StateHalfOpen {
					calls++
					panic("entry")
				}
			},
		})
		stale, trip := identityAllow(t, b), identityAllow(t, b)
		trip(false)
		time.Sleep(2 * identityWindow)
		if got := identityPanic(t, func() { stale(success) }); got != "entry" {
			t.Fatalf("panic: %v", got)
		}
		identityCounts(t, b.Counts(), gb.Counts{})
		identityState(t, b.State(), gb.StateHalfOpen)
		identityAllow(t, b)
		if calls != 1 {
			t.Fatalf("notifications=%d", calls)
		}
	})
}

func TestIdentitySettingsCallbacks(t *testing.T) {
	captured := false
	var events []gb.State
	st := gb.Settings{
		IsSuccessful: func(error) bool { return !captured },
		ReadyToTrip:  func(c gb.Counts) bool { identityCounts(t, c, identityFailure(1)); return captured },
		OnStateChange: func(_ string, _, to gb.State) {
			if !captured {
				t.Error("closure did not see changed variable")
			}
			events = append(events, to)
		},
	}
	b := gb.NewCircuitBreaker(st)
	st.IsSuccessful = func(error) bool { t.Error("replacement classifier used"); return true }
	st.ReadyToTrip = func(gb.Counts) bool { t.Error("replacement predicate used"); return false }
	st.OnStateChange = func(string, gb.State, gb.State) { t.Error("replacement notifier used") }
	captured = true
	_, _ = b.Execute(func() (interface{}, error) { return nil, identityErr })
	identityState(t, b.State(), gb.StateOpen)
	if !reflect.DeepEqual(events, []gb.State{gb.StateOpen}) {
		t.Fatalf("events: %v", events)
	}
}

func TestIdentityTwoStepBypassesClassifier(t *testing.T) {
	calls := 0
	st := gb.Settings{IsSuccessful: func(error) bool { calls++; return false }}
	two := gb.NewTwoStepCircuitBreaker(st)
	identityAllow(t, two)(true)
	identityCounts(t, two.Counts(), identitySuccess(1))
	if calls != 0 {
		t.Fatalf("classifier called by Allow")
	}
	b := gb.NewCircuitBreaker(st)
	_, _ = b.Execute(func() (interface{}, error) { return nil, nil })
	identityCounts(t, b.Counts(), identityFailure(1))
	if calls != 1 {
		t.Fatalf("classifier calls=%d", calls)
	}
}
