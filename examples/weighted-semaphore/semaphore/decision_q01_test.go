package semaphore

import (
	"context"
	"runtime"
	"testing"
	"time"
)

// Scheduling-only barrier: no state mutation or outcome assertions here.
func q01Enqueued(t *testing.T, s *Weighted, count int) {
	t.Helper()
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		s.mu.Lock()
		ready := s.waiters.Len() == count
		s.mu.Unlock()
		if ready {
			return
		}
		runtime.Gosched()
	}
	t.Fatalf("setup did not enqueue %d requests", count)
}
func q01Request(t *testing.T, s *Weighted, n int64, count int) (context.CancelFunc, <-chan error) {
	t.Helper()
	ctx, cancel := context.WithCancel(context.Background())
	t.Cleanup(cancel)
	result := make(chan error, 1)
	go func() { result <- s.Acquire(ctx, n) }()
	q01Enqueued(t, s, count)
	return cancel, result
}
func q01Result(t *testing.T, result <-chan error, want error) {
	t.Helper()
	select {
	case got := <-result:
		if got != want {
			t.Fatalf("Acquire returned %v; want %v", got, want)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("DR-001: eligible zero waiter did not complete without another input")
	}
}
func q01Pending(t *testing.T, result <-chan error) {
	t.Helper()
	select {
	case err := <-result:
		t.Fatalf("FIFO blocker was bypassed: %v", err)
	default:
	}
}

// Matrix: Acquire_WaitersPending x ContextDone; P-07a; DR-001, SYS-Q01/SYS-01.
func TestDR001FullSingleZero(t *testing.T) {
	s := NewWeighted(1)
	if !s.TryAcquire(1) {
		t.Fatal("initial capacity unavailable")
	}
	cancel, head := q01Request(t, s, 1, 1)
	_, zero := q01Request(t, s, 0, 2)
	cancel()
	q01Result(t, head, context.Canceled)
	q01Result(t, zero, nil) // No Release or second input before this observation.
	if s.TryAcquire(1) {
		t.Fatal("zero completion manufactured capacity")
	}
	s.Release(1)
	if !s.TryAcquire(1) {
		t.Fatal("original capacity not restored by matching Release")
	}
	s.Release(1)
}

// Matrix: same cell, guarded branch with a blocked positive tail; DR-001.
func TestDR001FullZeroPrefix(t *testing.T) {
	s := NewWeighted(2)
	if !s.TryAcquire(2) {
		t.Fatal("initial capacity unavailable")
	}
	cancel, head := q01Request(t, s, 1, 1)
	zeros := make([]<-chan error, 3)
	for i := range zeros {
		_, zeros[i] = q01Request(t, s, 0, i+2)
	}
	_, tail := q01Request(t, s, 1, 5)
	cancel()
	q01Result(t, head, context.Canceled)
	for _, zero := range zeros {
		q01Result(t, zero, nil)
	}
	q01Pending(t, tail)
	if s.TryAcquire(1) {
		t.Fatal("zero grants manufactured capacity")
	}
	s.Release(1)
	q01Result(t, tail, nil)
	s.Release(2)
	if !s.TryAcquire(2) {
		t.Fatal("capacity did not recover")
	}
	s.Release(2)
}

// Matrix: same cell, free=1 control adjacent to the free=0 failing boundary; DR-001.
func TestDR001SpareCapacity(t *testing.T) {
	s := NewWeighted(2)
	if !s.TryAcquire(1) {
		t.Fatal("initial capacity unavailable")
	}
	cancel, head := q01Request(t, s, 2, 1)
	_, zero := q01Request(t, s, 0, 2)
	cancel()
	q01Result(t, head, context.Canceled)
	q01Result(t, zero, nil)
	if !s.TryAcquire(1) {
		t.Fatal("zero grant consumed the spare unit")
	}
	if s.TryAcquire(1) {
		t.Fatal("capacity exceeded")
	}
	s.Release(2)
}

// Matrix: same cell, non-head cancellation cannot bypass the retained head; DR-001.
func TestDR001RetainedHeadPreservesFIFO(t *testing.T) {
	s := NewWeighted(1)
	if !s.TryAcquire(1) {
		t.Fatal("initial capacity unavailable")
	}
	cancelHead, head := q01Request(t, s, 1, 1)
	cancelMiddle, middle := q01Request(t, s, 1, 2)
	_, zero := q01Request(t, s, 0, 3)
	cancelMiddle()
	q01Result(t, middle, context.Canceled)
	q01Pending(t, head)
	q01Pending(t, zero)
	if s.TryAcquire(0) {
		t.Fatal("zero try bypassed the retained positive head")
	}
	cancelHead()
	q01Result(t, head, context.Canceled)
	q01Result(t, zero, nil)
	if s.TryAcquire(1) {
		t.Fatal("zero grant changed positive accounting")
	}
	s.Release(1)
}

// Matrix: zero TryAcquire before head cancellation; DR-001 explicitly forbids bypass.
func TestDR001ZeroTryDoesNotBypass(t *testing.T) {
	s := NewWeighted(1)
	if !s.TryAcquire(1) {
		t.Fatal("initial capacity unavailable")
	}
	cancel, head := q01Request(t, s, 1, 1)
	_, zero := q01Request(t, s, 0, 2)
	if s.TryAcquire(0) {
		t.Fatal("zero try bypassed FIFO")
	}
	q01Pending(t, zero)
	cancel()
	q01Result(t, head, context.Canceled)
	q01Result(t, zero, nil)
	s.Release(1)
}
