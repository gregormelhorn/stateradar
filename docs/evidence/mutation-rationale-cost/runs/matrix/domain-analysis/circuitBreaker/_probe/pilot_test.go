package gobreaker

import (
	"errors"
	"runtime"
	"testing"
	"time"
)

func pilotAllow(t *testing.T, cb *TwoStepCircuitBreaker) func(bool) {
	t.Helper()
	done, err := cb.Allow()
	if err != nil {
		t.Fatal(err)
	}
	return done
}

func pilotHalfOpen(t *testing.T, max uint32) *TwoStepCircuitBreaker {
	t.Helper()
	cb := NewTwoStepCircuitBreaker(Settings{
		MaxRequests: max, Timeout: time.Nanosecond,
		ReadyToTrip: func(Counts) bool { return true },
	})
	pilotAllow(t, cb)(false)
	return cb
}

func TestPilotDuplicateAndAbandoned(t *testing.T) {
	cb := pilotHalfOpen(t, 2)
	first := pilotAllow(t, cb)
	first(true)
	first(true)
	if got := cb.State(); got != StateClosed {
		t.Fatalf("duplicate success state = %v", got)
	}
	cb = pilotHalfOpen(t, 1)
	_ = pilotAllow(t, cb)
	if cb.State() != StateHalfOpen {
		t.Fatal("abandonment changed mode")
	}
	if _, err := cb.Allow(); err != ErrTooManyRequests {
		t.Fatalf("after abandonment: %v", err)
	}
}

func TestPilotStaleReportReconcilesOpen(t *testing.T) {
	var changes []State
	cb := NewTwoStepCircuitBreaker(Settings{
		Timeout: time.Nanosecond, ReadyToTrip: func(Counts) bool { return true },
		OnStateChange: func(_ string, _ State, to State) { changes = append(changes, to) },
	})
	stale := pilotAllow(t, cb)
	pilotAllow(t, cb)(false)
	stale(false)
	if len(changes) != 2 || changes[1] != StateHalfOpen {
		t.Fatalf("state notifications before any new call: %v", changes)
	}
	h := pilotAllow(t, cb)
	if _, err := cb.Allow(); err != ErrTooManyRequests {
		t.Fatalf("second half-open admission: %v", err)
	}
	if got := cb.Counts(); got.Requests != 1 || got.TotalFailures != 0 {
		t.Fatalf("counts: %+v", got)
	}
	h(true)
}

func TestPilotSameCallerWhilePending(t *testing.T) {
	cb := NewCircuitBreaker(Settings{})
	entered, release, returned := make(chan struct{}), make(chan struct{}), make(chan error, 1)
	defer close(release)
	go func() {
		_, err := cb.Execute(func() (interface{}, error) { close(entered); <-release; return nil, nil })
		returned <- err
	}()
	<-entered
	if _, err := cb.Execute(func() (interface{}, error) { return nil, nil }); err != nil {
		t.Fatal(err)
	}
	if got := cb.Counts(); got.Requests != 2 || got.TotalSuccesses != 1 {
		t.Fatalf("counts before first returns: %+v", got)
	}
	closeSignal := false
	select {
	case <-returned:
		closeSignal = true
	default:
	}
	if closeSignal {
		t.Fatal("first request completed while blocked")
	}
}

func TestPilotReentryBounded(t *testing.T) {
	for _, which := range []string{"notify", "trip"} {
		t.Run(which, func(t *testing.T) {
			var cb *CircuitBreaker
			entered, returned := make(chan struct{}), make(chan struct{})
			reenter := func() { close(entered); cb.State(); close(returned) }
			st := Settings{ReadyToTrip: func(Counts) bool { return true }}
			if which == "trip" {
				st.ReadyToTrip = func(Counts) bool { reenter(); return true }
			} else {
				st.OnStateChange = func(string, State, State) { reenter() }
			}
			cb = NewCircuitBreaker(st)
			go cb.Execute(func() (interface{}, error) { return nil, errors.New("fault") })
			select {
			case <-entered:
			case <-time.After(time.Second):
				t.Fatal("callback did not start")
			}
			select {
			case <-returned:
				t.Fatal("same-goroutine State reentry returned")
			case <-time.After(30 * time.Millisecond):
			}
		})
	}
}

func TestPilotTripPanicDoubleAccounting(t *testing.T) {
	calls := 0
	cb := NewCircuitBreaker(Settings{ReadyToTrip: func(Counts) bool { calls++; panic("policy") }})
	func() {
		defer func() {
			if got := recover(); got != "policy" {
				t.Fatalf("panic = %v", got)
			}
		}()
		cb.Execute(func() (interface{}, error) { return nil, errors.New("request") })
	}()
	if got := cb.Counts(); got.Requests != 1 || got.TotalFailures != 2 || calls != 2 {
		t.Fatalf("counts=%+v calls=%d", got, calls)
	}
}

func TestPilotNotificationPanicReplacesRequestPanic(t *testing.T) {
	cb := NewCircuitBreaker(Settings{
		ReadyToTrip:   func(Counts) bool { return true },
		OnStateChange: func(string, State, State) { panic("notification") },
	})
	func() {
		defer func() {
			if got := recover(); got != "notification" {
				t.Fatalf("panic = %v", got)
			}
		}()
		cb.Execute(func() (interface{}, error) { panic("request") })
	}()
	if cb.State() != StateOpen || cb.Counts() != (Counts{}) {
		t.Fatal("transition did not commit")
	}
}

func TestPilotGoexitAbandonsAdmission(t *testing.T) {
	cb := NewCircuitBreaker(Settings{})
	exited := make(chan struct{})
	go func() {
		defer close(exited)
		cb.Execute(func() (interface{}, error) { runtime.Goexit(); return nil, nil })
	}()
	<-exited
	if got := cb.Counts(); got.Requests != 1 || got.TotalFailures != 0 || got.TotalSuccesses != 0 {
		t.Fatalf("counts: %+v", got)
	}
}

func TestPilotAllowThenStateAtOpenExpiry(t *testing.T) {
	cb := NewTwoStepCircuitBreaker(Settings{Timeout: time.Second, ReadyToTrip: func(Counts) bool { return true }})
	pilotAllow(t, cb)(false)
	// Advance only the stored expiry to schedule the next public observation.
	cb.cb.mutex.Lock()
	cb.cb.expiry = time.Now().Add(-time.Second)
	cb.cb.mutex.Unlock()
	first := pilotAllow(t, cb)
	if got := cb.State(); got != StateHalfOpen {
		t.Fatalf("state = %v", got)
	}
	if _, err := cb.Allow(); err != ErrTooManyRequests {
		t.Fatalf("second admission after open expiry = %v", err)
	}
	first(true)
	if cb.State() != StateClosed {
		t.Fatal("admitted trial success did not close")
	}
}

func TestPilotSameOwnerOutstandingBelowBudget(t *testing.T) {
	cb := pilotHalfOpen(t, 2)
	first := pilotAllow(t, cb)
	second := pilotAllow(t, cb)
	first(true)
	if got := cb.Counts(); got.Requests != 2 || got.TotalSuccesses != 1 {
		t.Fatalf("first report accounted as %+v", got)
	}
	if _, err := cb.Allow(); err != ErrTooManyRequests {
		t.Fatalf("reported slot was refunded: %v", err)
	}
	second(true)
	if cb.State() != StateClosed {
		t.Fatal("second distinct success did not close")
	}
}
