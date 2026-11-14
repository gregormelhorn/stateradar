package semaphore

import (
	"context"
	"math"
	"strings"
	"testing"
	"time"
)

func numericPanic(t *testing.T, call func()) {
	t.Helper()
	panicked := false
	func() {
		defer func() { panicked = recover() != nil }()
		call()
	}()
	if !panicked {
		t.Error("approved numeric rejection must panic")
	}
}

// Public capacity projection, with a matching release of the probe acquisition.
func numericAvailable(t *testing.T, s *Weighted, free int64) {
	t.Helper()
	if !s.TryAcquire(free) {
		t.Fatalf("expected %d units still available", free)
	}
	if s.TryAcquire(1) {
		t.Fatal("rejected call manufactured capacity")
	}
	s.Release(free)
}

// DR-002; all instance states x NewWeighted / UV-Weight (negative size).
func TestDR002NegativeConstructor(t *testing.T) {
	for _, tc := range []struct {
		name string
		n    int64
	}{{"MinusOne", -1}, {"MinInt64", math.MinInt64}} {
		t.Run(tc.name, func(t *testing.T) { numericPanic(t, func() { NewWeighted(tc.n) }) })
	}
}

// DR-002; NoWaiters and WaitersPending x Acquire / TryAcquire / Release.
// Only negative-weight branches are decided here; queue length is setup only.
func numericNegativeMethod(t *testing.T, method string) {
	for _, tc := range []struct {
		name string
		n    int64
	}{{"MinusOne", -1}, {"MinInt64", math.MinInt64}} {
		for _, setup := range []string{"Empty", "Full", "Queued", "PreCanceled"} {
			t.Run(tc.name+"/"+setup, func(t *testing.T) {
				s := NewWeighted(2)
				held := setup == "Full" || setup == "Queued"
				if held && !s.TryAcquire(2) {
					t.Fatal("setup acquire failed")
				}
				var cancelHead context.CancelFunc
				var head <-chan error
				if setup == "Queued" {
					cancelHead, head = q01Request(t, s, 1, 1)
				}
				ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
				defer cancel()
				if setup == "PreCanceled" {
					cancel()
				}
				numericPanic(t, func() {
					switch method {
					case "Acquire":
						_ = s.Acquire(ctx, tc.n)
					case "TryAcquire":
						s.TryAcquire(tc.n)
					case "Release":
						s.Release(tc.n)
					}
				})
				if head != nil {
					q01Pending(t, head)
					cancelHead()
					q01Result(t, head, context.Canceled)
				}
				free := int64(2)
				if held {
					free = 0
				}
				numericAvailable(t, s, free)
				if held {
					s.Release(2)
					numericAvailable(t, s, 2)
				}
			})
		}
	}
}
func TestDR002NegativeAcquire(t *testing.T)    { numericNegativeMethod(t, "Acquire") }
func TestDR002NegativeTryAcquire(t *testing.T) { numericNegativeMethod(t, "TryAcquire") }
func TestDR002NegativeRelease(t *testing.T)    { numericNegativeMethod(t, "Release") }

// DR-002; NoWaiters x Acquire/TryAcquire/Release; valid arithmetic boundaries.
func TestDR002ZeroAndMaxBoundaries(t *testing.T) {
	t.Run("Zero", func(t *testing.T) {
		s := NewWeighted(0)
		if err := s.Acquire(context.Background(), 0); err != nil {
			t.Fatal(err)
		}
		if !s.TryAcquire(0) {
			t.Fatal("zero must remain valid")
		}
		s.Release(0)
		if s.TryAcquire(1) {
			t.Fatal("zero capacity admitted positive weight")
		}
	})
	t.Run("MaxInt64", func(t *testing.T) {
		s := NewWeighted(math.MaxInt64)
		if err := s.Acquire(context.Background(), math.MaxInt64); err != nil {
			t.Fatal(err)
		}
		if s.TryAcquire(1) {
			t.Fatal("full max-capacity instance admitted more")
		}
		s.Release(math.MaxInt64)
		numericAvailable(t, s, math.MaxInt64)
	})
	t.Run("QueuedMaxInt64", func(t *testing.T) {
		s := NewWeighted(math.MaxInt64)
		if !s.TryAcquire(math.MaxInt64) {
			t.Fatal("setup failed")
		}
		_, waiter := q01Request(t, s, math.MaxInt64, 1)
		s.Release(math.MaxInt64 - 1)
		q01Pending(t, waiter)
		s.Release(1)
		q01Result(t, waiter, nil)
		if s.TryAcquire(1) {
			t.Fatal("queued grant overflowed")
		}
		s.Release(math.MaxInt64)
		numericAvailable(t, s, math.MaxInt64)
	})
}

// DR-003; NoWaiters x Release (over-release), preserve old capacity after recovery.
func TestDR003OverReleaseEmptyPartialFull(t *testing.T) {
	for _, tc := range []struct {
		name string
		held int64
	}{{"Empty", 0}, {"Partial", 1}, {"Full", 2}} {
		t.Run(tc.name, func(t *testing.T) {
			s := NewWeighted(2)
			if !s.TryAcquire(tc.held) {
				t.Fatal("setup failed")
			}
			numericPanic(t, func() { s.Release(tc.held + 1) })
			numericAvailable(t, s, 2-tc.held)
			s.Release(tc.held)
			numericAvailable(t, s, 2)
		})
	}
}

// DR-003; WaitersPending x Release: reject without granting; valid release progresses.
func TestDR003OverReleaseQueued(t *testing.T) {
	defer func() {
		if p := recover(); p != nil {
			t.Fatalf("valid release after rejected over-release must remain usable: %v", p)
		}
	}()
	s := NewWeighted(1)
	if !s.TryAcquire(1) {
		t.Fatal("setup failed")
	}
	_, waiter := q01Request(t, s, 1, 1)
	numericPanic(t, func() { s.Release(2) })
	q01Pending(t, waiter)
	s.Release(1)
	q01Result(t, waiter, nil)
	if s.TryAcquire(1) {
		t.Fatal("over-release corrupted accounting after grant")
	}
	s.Release(1)
	numericAvailable(t, s, 1)
}

// DR-003; NoWaiters x Release: maximum positive invalid weight cannot corrupt state.
func TestDR003OverReleaseMax(t *testing.T) {
	s := NewWeighted(math.MaxInt64)
	if !s.TryAcquire(1) {
		t.Fatal("setup failed")
	}
	numericPanic(t, func() { s.Release(math.MaxInt64) })
	numericAvailable(t, s, math.MaxInt64-1)
	s.Release(1)
	numericAvailable(t, s, math.MaxInt64)
}

// DR-004; NoWaiters / WaitersPending x Acquire (oversized live request).
// Result must precede cancellation and explain the impossible request.
func TestDR004OversizedImmediateError(t *testing.T) {
	for _, setup := range []string{"Empty", "Queued"} {
		t.Run(setup, func(t *testing.T) {
			s := NewWeighted(2)
			var head <-chan error
			if setup == "Queued" {
				if !s.TryAcquire(2) {
					t.Fatal("setup failed")
				}
				_, head = q01Request(t, s, 1, 1)
			}
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			result := make(chan error, 1)
			go func() { result <- s.Acquire(ctx, 3) }()
			select {
			case err := <-result:
				if err == nil || err == context.Canceled || err == context.DeadlineExceeded {
					t.Fatalf("expected size error, got %v", err)
				}
				if !strings.Contains(err.Error(), "3") || !strings.Contains(err.Error(), "2") {
					t.Fatalf("error must explain requested weight and capacity: %v", err)
				}
			case <-time.After(2 * time.Second):
				t.Fatal("oversized request waited for context cancellation")
			}
			if head != nil {
				q01Pending(t, head)
				s.Release(1)
				q01Result(t, head, nil)
				s.Release(2)
			}
			numericAvailable(t, s, 2)
		})
	}
}

// DR-004 preserves existing pre-canceled handling; Q-10 other races remain open.
func TestDR004PreCanceledOversized(t *testing.T) {
	s := NewWeighted(2)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if err := s.Acquire(ctx, 3); err != context.Canceled {
		t.Fatalf("got %v", err)
	}
	numericAvailable(t, s, 2)
}
