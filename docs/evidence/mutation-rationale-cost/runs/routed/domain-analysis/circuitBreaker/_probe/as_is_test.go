package gobreaker

import (
	"errors"
	"runtime"
	"sync"
	"testing"
	"time"
)

var probeFault = errors.New("downstream fault")

func probeHalfOpen(t *testing.T, max uint32) *TwoStepCircuitBreaker {
	t.Helper()
	cb := NewTwoStepCircuitBreaker(Settings{
		MaxRequests: max, Timeout: time.Nanosecond,
		ReadyToTrip: func(Counts) bool { return true },
	})
	done, err := cb.Allow()
	if err != nil {
		t.Fatal(err)
	}
	done(false)
	if got := cb.State(); got != StateHalfOpen {
		t.Fatalf("state: %v", got)
	}
	return cb
}

func TestPilotDuplicateDone(t *testing.T) {
	cb := probeHalfOpen(t, 2)
	done, err := cb.Allow()
	if err != nil {
		t.Fatal(err)
	}
	done(true)
	if got := cb.Counts(); got.Requests != 1 || got.TotalSuccesses != 1 {
		t.Fatal(got)
	}
	done(true)
	if got := cb.State(); got != StateClosed {
		t.Fatalf("duplicate left state %v", got)
	}
}

func TestPilotAbandonAndLateReport(t *testing.T) {
	for _, success := range []bool{true, false} {
		var transitions []State
		cb := NewTwoStepCircuitBreaker(Settings{
			Timeout:       time.Nanosecond,
			ReadyToTrip:   func(Counts) bool { return true },
			OnStateChange: func(_ string, _, to State) { transitions = append(transitions, to) },
		})
		trip, err := cb.Allow()
		if err != nil {
			t.Fatal(err)
		}
		trip(false)
		if got := cb.State(); got != StateHalfOpen {
			t.Fatal(got)
		}
		done, err := cb.Allow()
		if err != nil {
			t.Fatal(err)
		}
		for range [2]struct{}{} {
			if _, err := cb.Allow(); err != ErrTooManyRequests {
				t.Fatalf("admission: %v", err)
			}
			if got := cb.State(); got != StateHalfOpen {
				t.Fatalf("abandoned state: %v", got)
			}
		}
		done(success)
		if success {
			if got := cb.State(); got != StateClosed {
				t.Fatal(got)
			}
		} else {
			if len(transitions) != 3 || transitions[2] != StateOpen {
				t.Fatalf("late failure transitions: %v", transitions)
			}
			if got := cb.Counts(); got != (Counts{}) {
				t.Fatal(got)
			}
			if got := cb.State(); got != StateHalfOpen {
				t.Fatal(got)
			}
		}
	}
}

func TestPilotAdmissionOrdering(t *testing.T) {
	cb := probeHalfOpen(t, 1)
	done, err := cb.Allow()
	if err != nil {
		t.Fatal(err)
	}
	if _, err = cb.Allow(); err != ErrTooManyRequests {
		t.Fatal(err)
	}
	done(true)
	if got := cb.State(); got != StateClosed {
		t.Fatalf("ordered success left state %v", got)
	}
	if _, err = cb.Allow(); err != nil {
		t.Fatal(err)
	}
}

func TestPilotExecuteOvertakes(t *testing.T) {
	cb := NewCircuitBreaker(Settings{})
	started, resume, finished := make(chan struct{}), make(chan struct{}), make(chan error, 1)
	go func() {
		_, err := cb.Execute(func() (interface{}, error) {
			close(started)
			<-resume
			return nil, probeFault
		})
		finished <- err
	}()
	<-started
	value, err := cb.Execute(func() (interface{}, error) { return "second", nil })
	if value != "second" || err != nil {
		t.Fatalf("second: %v, %v", value, err)
	}
	if got := cb.Counts(); got.Requests != 2 || got.TotalSuccesses != 1 {
		t.Fatal(got)
	}
	close(resume)
	if err := <-finished; err != probeFault {
		t.Fatal(err)
	}
	if _, err := cb.Execute(func() (interface{}, error) { return value, nil }); err != nil {
		t.Fatal(err)
	}
}

func TestPilotExpiryAndStaleReport(t *testing.T) {
	for _, success := range []bool{true, false} {
		var changes []State
		cb := NewTwoStepCircuitBreaker(Settings{
			Timeout:       time.Nanosecond,
			ReadyToTrip:   func(Counts) bool { return true },
			OnStateChange: func(_ string, _, to State) { changes = append(changes, to) },
		})
		old, err := cb.Allow()
		if err != nil {
			t.Fatal(err)
		}
		trip, err := cb.Allow()
		if err != nil {
			t.Fatal(err)
		}
		trip(false)
		time.Sleep(time.Millisecond)
		if got := cb.Counts(); got != (Counts{}) {
			t.Fatal(got)
		}
		if len(changes) != 1 {
			t.Fatalf("idle notification: %v", changes)
		}
		old(success)
		if len(changes) != 2 || changes[1] != StateHalfOpen {
			t.Fatalf("stale callback observation: %v", changes)
		}
		if got := cb.Counts(); got != (Counts{}) {
			t.Fatal(got)
		}
	}
}

func TestPilotStaleClassifierAndReturn(t *testing.T) {
	entered, resume, finished := make(chan struct{}), make(chan struct{}), make(chan error, 1)
	cb := NewCircuitBreaker(Settings{
		ReadyToTrip: func(Counts) bool { return true },
		IsSuccessful: func(err error) bool {
			if err == probeFault {
				close(entered)
				<-resume
				return true
			}
			return false
		},
	})
	go func() {
		_, err := cb.Execute(func() (interface{}, error) { return 7, probeFault })
		finished <- err
	}()
	<-entered
	_, err := cb.Execute(func() (interface{}, error) { return nil, nil })
	if err != nil {
		t.Fatal(err)
	}
	if got := cb.State(); got != StateOpen {
		t.Fatal(got)
	}
	close(resume)
	if err := <-finished; err != probeFault {
		t.Fatal(err)
	}
	if got := cb.Counts(); got != (Counts{}) {
		t.Fatal(got)
	}
}

func TestPilotCallbackReentry(t *testing.T) {
	for _, hook := range []string{"notification", "policy"} {
		t.Run(hook, func(t *testing.T) {
			var cb *CircuitBreaker
			entered, returned := make(chan struct{}), make(chan struct{})
			reenter := func() { close(entered); cb.Counts() }
			settings := Settings{ReadyToTrip: func(Counts) bool { return true }}
			if hook == "notification" {
				settings.OnStateChange = func(string, State, State) { reenter() }
			} else {
				settings.ReadyToTrip = func(Counts) bool { reenter(); return true }
			}
			cb = NewCircuitBreaker(settings)
			go func() {
				_, _ = cb.Execute(func() (interface{}, error) { return nil, probeFault })
				close(returned)
			}()
			<-entered
			select {
			case <-returned:
				t.Fatal("callback unexpectedly returned")
			case <-time.After(25 * time.Millisecond):
			}
		})
	}
}

func TestPilotCallbackPanics(t *testing.T) {
	observePanic := func(f func()) (caught interface{}) {
		defer func() { caught = recover() }()
		f()
		return nil
	}
	cb := NewCircuitBreaker(Settings{ReadyToTrip: func(Counts) bool { panic("policy") }})
	if got := observePanic(func() { _, _ = cb.Execute(func() (interface{}, error) { return nil, probeFault }) }); got != "policy" {
		t.Fatal(got)
	}
	if got := cb.Counts(); got.TotalFailures != 2 {
		t.Fatalf("policy retried accounting: %v", got)
	}
	if got := observePanic(func() { _, _ = cb.Execute(func() (interface{}, error) { panic("request") }) }); got != "policy" {
		t.Fatal(got)
	}

	cb = NewCircuitBreaker(Settings{IsSuccessful: func(error) bool { panic("classifier") }})
	if got := observePanic(func() { _, _ = cb.Execute(func() (interface{}, error) { return 7, nil }) }); got != "classifier" {
		t.Fatal(got)
	}
	if got := cb.Counts(); got.TotalFailures != 1 {
		t.Fatal(got)
	}

	cb = NewCircuitBreaker(Settings{
		ReadyToTrip:   func(Counts) bool { return true },
		OnStateChange: func(string, State, State) { panic("notification") },
	})
	if got := observePanic(func() { _, _ = cb.Execute(func() (interface{}, error) { panic("request") }) }); got != "notification" {
		t.Fatal(got)
	}
	if got := cb.State(); got != StateOpen {
		t.Fatal(got)
	}
	if got := cb.Counts(); got != (Counts{}) {
		t.Fatal(got)
	}
}

func TestPilotGoexit(t *testing.T) {
	cb := NewCircuitBreaker(Settings{})
	exited := make(chan struct{})
	go func() {
		defer close(exited)
		_, _ = cb.Execute(func() (interface{}, error) { runtime.Goexit(); return nil, nil })
	}()
	<-exited
	if got := cb.Counts(); got != (Counts{Requests: 1}) {
		t.Fatal(got)
	}
}

func TestPilotSharedRecoveryWaves(t *testing.T) {
	const n = 4
	cb := make([]*TwoStepCircuitBreaker, n)
	for i := range cb {
		cb[i] = probeHalfOpen(t, 1)
	}
	for cycle := 0; cycle < 3; cycle++ {
		start := make(chan struct{})
		var wg sync.WaitGroup
		arrivals := make(chan struct{}, n)
		for _, instance := range cb {
			wg.Add(1)
			go func(b *TwoStepCircuitBreaker) {
				defer wg.Done()
				<-start
				done, err := b.Allow()
				if err != nil {
					t.Error(err)
					return
				}
				arrivals <- struct{}{}
				done(false)
			}(instance)
		}
		close(start)
		wg.Wait()
		if got := len(arrivals); got != n {
			t.Fatalf("cycle %d admitted %d", cycle, got)
		}
	}
}
