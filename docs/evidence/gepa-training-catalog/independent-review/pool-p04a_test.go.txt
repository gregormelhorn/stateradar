package pool

import (
	"errors"
	"runtime"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

var beforeGetCapacityLock func()

func TestP04aGetWaitsWhileReturnedConnectionIsIdle(t *testing.T) {
	type connection struct{ id int }
	first := &connection{id: 1}
	second := &connection{id: 2}
	created := 0
	p, err := NewChannelPool(&Config{
		InitialCap: 2, MaxIdle: 2, MaxCap: 2,
		Factory: func() (interface{}, error) {
			created++
			switch created {
			case 1:
				return first, nil
			case 2:
				return second, nil
			default:
				return nil, errors.New("unexpected factory invocation")
			}
		},
		Close: func(interface{}) error { return nil },
	})
	if err != nil {
		t.Fatal(err)
	}
	for _, want := range []*connection{first, second} {
		if got, err := p.Get(); got != want || err != nil {
			t.Fatalf("initial Get = (%v, %v), want (%v, nil)", got, err, want)
		}
	}

	type result struct {
		value interface{}
		err   error
	}
	started, resume := make(chan struct{}), make(chan struct{})
	outcome := make(chan result, 1)
	var getPaused atomic.Bool
	beforeGetCapacityLock = func() {
		if getPaused.CompareAndSwap(false, true) {
			close(started)
			<-resume
		}
	}
	go func() {
		value, err := p.Get()
		outcome <- result{value, err}
	}()
	select {
	case <-started:
	case <-time.After(2 * time.Second):
		t.Fatal("first Get did not reach the empty idle-channel branch")
	}
	returnErr := p.Put(first)
	close(resume)
	if returnErr != nil {
		t.Fatalf("first Put: %v", returnErr)
	}

	// Put the other connection back only after the first Get is observably
	// waiting. A Put serves an existing waiter, so observe the schedule via
	// the blocked public call's runtime stack before making the next call.
	deadline := time.Now().Add(2 * time.Second)
	for !getIsWaiting() {
		select {
		case got := <-outcome:
			t.Fatalf("first Get returned early: %+v", got)
		default:
		}
		if time.Now().After(deadline) {
			t.Fatal("first Get did not block with an idle connection")
		}
		time.Sleep(time.Millisecond)
	}
	if got := p.Len(); got != 1 {
		t.Fatalf("idle connections while first Get is waiting = %d, want 1", got)
	}
	if got, err := p.Get(); got != first || err != nil {
		t.Fatalf("later Get = (%v, %v), want (%v, nil)", got, err, first)
	}
	if err := p.Put(second); err != nil {
		t.Fatal(err)
	}
	select {
	case got := <-outcome:
		if got.value != second || got.err != nil {
			t.Fatalf("first Get = (%v, %v), want (%v, nil)", got.value, got.err, second)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("second Put did not wake the first Get")
	}
	beforeGetCapacityLock = nil
	p.Release()
}

func getIsWaiting() bool {
	b := make([]byte, 64*1024)
	n := runtime.Stack(b, true)
	for _, stack := range strings.Split(string(b[:n]), "\n\n") {
		if strings.Contains(strings.SplitN(stack, "\n", 2)[0], "[chan receive") &&
			strings.Contains(stack, "github.com/silenceper/pool.(*channelPool).Get(") &&
			strings.Contains(stack, "TestP04aGetWaitsWhileReturnedConnectionIsIdle.func") {
			return true
		}
	}
	return false
}
