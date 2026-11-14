package semaphore

import (
	"context"
	"runtime"
	"testing"
	"time"
)

func pilotQueue(t *testing.T, s *Weighted, count int) {
	t.Helper()
	limit := time.After(time.Second)
	for {
		s.mu.Lock()
		ready := s.waiters.Len() == count
		s.mu.Unlock()
		if ready {
			return
		}
		select {
		case <-limit:
			t.Fatalf("waiter count did not reach %d", count)
		default:
			runtime.Gosched()
		}
	}
}

func pilotResult(t *testing.T, result <-chan error) error {
	t.Helper()
	select {
	case err := <-result:
		return err
	case <-time.After(time.Second):
		t.Fatal("Acquire did not finish")
		return nil
	}
}

func TestPilotZeroWaiterAfterHeadCancel(t *testing.T) {
	s := NewWeighted(1)
	if !s.TryAcquire(1) {
		t.Fatal("initial acquisition failed")
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	head := make(chan error, 1)
	go func() { head <- s.Acquire(ctx, 1) }()
	pilotQueue(t, s, 1)
	zeroCtx, stopZero := context.WithCancel(context.Background())
	defer stopZero()
	zero := make(chan error, 1)
	go func() { zero <- s.Acquire(zeroCtx, 0) }()
	pilotQueue(t, s, 2)
	cancel()
	if err := pilotResult(t, head); err != context.Canceled {
		t.Fatalf("head returned %v", err)
	}
	if s.TryAcquire(0) {
		t.Fatal("TryAcquire(0) bypassed the queued zero request")
	}
	select {
	case err := <-zero:
		t.Fatalf("zero waiter returned before notification: %v", err)
	default:
	}
	s.Release(0)
	if err := pilotResult(t, zero); err != nil {
		t.Fatalf("zero waiter returned %v", err)
	}
	s.Release(1)
}

func TestPilotRecoveredOverRelease(t *testing.T) {
	s := NewWeighted(1)
	func() {
		defer func() {
			if recover() == nil {
				t.Fatal("over-release did not panic")
			}
		}()
		s.Release(1)
	}()
	if !s.TryAcquire(2) {
		t.Fatal("recovered instance did not admit above configured capacity")
	}
}

func TestPilotRepeatedAcquire(t *testing.T) {
	s := NewWeighted(2)
	if !s.TryAcquire(2) {
		t.Fatal("initial acquisition failed")
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	a, b := make(chan error, 1), make(chan error, 1)
	go func() { a <- s.Acquire(ctx, 1) }()
	pilotQueue(t, s, 1)
	go func() { b <- s.Acquire(ctx, 1) }()
	pilotQueue(t, s, 2)
	s.Release(1)
	if err := pilotResult(t, a); err != nil {
		t.Fatalf("first acquisition returned %v", err)
	}
	select {
	case err := <-b:
		t.Fatalf("second acquisition returned before a second handoff: %v", err)
	default:
	}
	s.Release(1)
	if err := pilotResult(t, b); err != nil {
		t.Fatalf("second acquisition returned %v", err)
	}
	s.Release(2)
	if err := s.Acquire(ctx, 1); err != nil {
		t.Fatal(err)
	}
	if err := s.Acquire(ctx, 1); err != nil {
		t.Fatal(err)
	}
	if s.TryAcquire(1) {
		t.Fatal("second held acquisition consumed no capacity")
	}
	s.Release(2)
}

type pilotContext struct {
	context.Context
	entered chan struct{}
	proceed chan struct{}
}

func (c pilotContext) Done() <-chan struct{} {
	close(c.entered)
	<-c.proceed
	return c.Context.Done()
}

func TestPilotLaterInvocationAdmitsFirst(t *testing.T) {
	s := NewWeighted(1)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	entered, proceed := make(chan struct{}), make(chan struct{})
	first := make(chan error, 1)
	go func() { first <- s.Acquire(pilotContext{ctx, entered, proceed}, 1) }()
	select {
	case <-entered:
	case <-time.After(time.Second):
		t.Fatal("first call did not reach the scheduling gate")
	}
	if err := s.Acquire(context.Background(), 1); err != nil {
		t.Fatal(err)
	}
	close(proceed)
	pilotQueue(t, s, 1)
	select {
	case err := <-first:
		t.Fatalf("first invocation finished while second still holds: %v", err)
	default:
	}
	s.Release(1)
	if err := pilotResult(t, first); err != nil {
		t.Fatal(err)
	}
	s.Release(1)
}

func TestPilotClosedContextAfterAdmission(t *testing.T) {
	s := NewWeighted(1)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	if err := s.Acquire(ctx, 1); err != nil {
		t.Fatal(err)
	}
	cancel()
	if s.TryAcquire(1) {
		t.Fatal("cancellation reclaimed a completed acquisition")
	}
	s.Release(1)
	if !s.TryAcquire(1) {
		t.Fatal("explicit release did not restore capacity")
	}
	s.Release(1)
}
