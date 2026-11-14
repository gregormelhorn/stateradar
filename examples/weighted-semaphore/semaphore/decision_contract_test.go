package semaphore

import (
	"context"
	"errors"
	"testing"
	"time"
)

var errUnexpectedGrant = errors.New("unexpected grant")

func contractTimeout() <-chan time.Time { return time.After(2 * time.Second) }

// DR-005; WaitersPending x UV-Abandon/ContextDone: cancel, consume error, no release.
func TestDR005CancelPending(t *testing.T) {
	s := NewWeighted(1)
	s.TryAcquire(1)
	cancel, result := q01Request(t, s, 1, 1)
	cancel()
	q01Result(t, result, context.Canceled)
	if s.TryAcquire(1) {
		t.Fatal("cancellation freed another holder")
	}
	s.Release(1)
	numericAvailable(t, s, 1)
}

// DR-005/010; NoWaiters x ContextDone after success: holding remains.
func TestDR005CancelHeld(t *testing.T) {
	s := NewWeighted(1)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	if err := s.Acquire(ctx, 1); err != nil {
		t.Fatal(err)
	}
	cancel()
	if s.TryAcquire(1) {
		t.Fatal("cancellation reclaimed successful acquisition")
	}
	s.Release(1)
	numericAvailable(t, s, 1)
}

// DR-005/008; WaitersPending x UV-Recreate: old queue/holding survives construction.
func TestDR005NewInstanceIndependent(t *testing.T) {
	old := NewWeighted(1)
	old.TryAcquire(1)
	_, result := q01Request(t, old, 1, 1)
	fresh := NewWeighted(1)
	numericAvailable(t, fresh, 1)
	q01Pending(t, result)
	if old.TryAcquire(1) {
		t.Fatal("new instance reset old capacity")
	}
	old.Release(1)
	q01Result(t, result, nil)
	old.Release(1)
	numericAvailable(t, old, 1)
	numericAvailable(t, fresh, 1)
}

// DR-006; NoWaiters x UV-RepeatAcquire: a second held acquisition adds a charge.
func TestDR006RepeatedHeld(t *testing.T) {
	s := NewWeighted(2)
	ctx := context.Background()
	if err := s.Acquire(ctx, 1); err != nil {
		t.Fatal(err)
	}
	if err := s.Acquire(ctx, 1); err != nil {
		t.Fatal(err)
	}
	if s.TryAcquire(1) {
		t.Fatal("repeated acquisition did not charge separately")
	}
	s.Release(1)
	numericAvailable(t, s, 1)
	s.Release(1)
	numericAvailable(t, s, 2)
}

// DR-006; WaitersPending x UV-RepeatAcquire: canceling one leaves the other live.
func TestDR006RepeatedPending(t *testing.T) {
	s := NewWeighted(1)
	s.TryAcquire(1)
	firstCancel, first := q01Request(t, s, 1, 1)
	_, second := q01Request(t, s, 1, 2)
	firstCancel()
	q01Result(t, first, context.Canceled)
	q01Pending(t, second)
	s.Release(1)
	q01Result(t, second, nil)
	if s.TryAcquire(1) {
		t.Fatal("second request was merged or not charged")
	}
	s.Release(1)
	numericAvailable(t, s, 1)
}

// DR-006; WaitersPending x ContextDone: shared Context can cancel separate requests.
func TestDR006SharedContext(t *testing.T) {
	s := NewWeighted(1)
	s.TryAcquire(1)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	first, second := make(chan error, 1), make(chan error, 1)
	go func() { first <- s.Acquire(ctx, 1) }()
	q01Enqueued(t, s, 1)
	go func() { second <- s.Acquire(ctx, 1) }()
	q01Enqueued(t, s, 2)
	cancel()
	q01Result(t, first, context.Canceled)
	q01Result(t, second, context.Canceled)
	if s.TryAcquire(1) {
		t.Fatal("cancellation changed existing holding")
	}
	s.Release(1)
	numericAvailable(t, s, 1)
}

// DR-007; NoWaiters x Release: a different goroutine may discharge the obligation.
func TestDR007TransferredRelease(t *testing.T) {
	s := NewWeighted(1)
	s.TryAcquire(1)
	result := make(chan error, 1)
	go func() { s.Release(1); result <- nil }()
	q01Result(t, result, nil)
	numericAvailable(t, s, 1)
}

// DR-007; NoWaiters x UV-RepeatRelease: document detection limit, not valid caller use.
func TestDR007DuplicateWithinAggregate(t *testing.T) {
	s := NewWeighted(2)
	s.TryAcquire(1)
	s.TryAcquire(1)
	s.Release(1)
	s.Release(1) // Deliberately misattributed second release is not detected.
	numericAvailable(t, s, 2)
	numericPanic(t, func() { s.Release(1) }) // Aggregate over-release remains detected.
	numericAvailable(t, s, 2)
}

// DR-008; NoWaiters x UV-WrongReceiver: no cross-instance transfer or intent inference.
func TestDR008WrongReceiver(t *testing.T) {
	a, b := NewWeighted(1), NewWeighted(1)
	a.TryAcquire(1)
	b.TryAcquire(1)
	b.Release(1)
	if a.TryAcquire(1) {
		t.Fatal("release on B changed A")
	}
	numericAvailable(t, b, 1)
	a.Release(1)
	numericAvailable(t, a, 1)
}

// DR-008; WaitersPending x UV-ForeignContext: only the supplied signal governs the call.
func TestDR008SelectedContext(t *testing.T) {
	s := NewWeighted(1)
	s.TryAcquire(1)
	intended, cancelIntended := context.WithCancel(context.Background())
	defer cancelIntended()
	supplied, cancelSupplied := context.WithCancel(context.Background())
	defer cancelSupplied()
	result := make(chan error, 1)
	go func() { result <- s.Acquire(supplied, 1) }()
	q01Enqueued(t, s, 1)
	cancelIntended()
	<-intended.Done()
	s.Release(1)
	q01Result(t, result, nil)
	s.Release(1)
	numericAvailable(t, s, 1)
	cancelSupplied()
	if err := s.Acquire(supplied, 1); err != context.Canceled {
		t.Fatalf("supplied context not used: %v", err)
	}
	numericAvailable(t, s, 1)
}

// Conforming custom wrapper delegates stable Done/Err to the standard Context.
type contractContext struct{ context.Context }

// DR-009; NoWaiters/WaitersPending x Acquire/ContextDone: custom conforming and nil Done.
func TestDR009ConformingContexts(t *testing.T) {
	s := NewWeighted(1)
	if err := s.Acquire(contractContext{context.Background()}, 1); err != nil {
		t.Fatal(err)
	}
	parent, cancel := context.WithCancel(context.Background())
	defer cancel()
	result := make(chan error, 1)
	go func() { result <- s.Acquire(contractContext{parent}, 1) }()
	q01Enqueued(t, s, 1)
	cancel()
	q01Result(t, result, context.Canceled)
	s.Release(1)
	numericAvailable(t, s, 1)
}

// DR-010; NoWaiters x Acquire: already canceled wins even with available capacity.
func TestDR010PreCanceled(t *testing.T) {
	s := NewWeighted(1)
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if err := s.Acquire(ctx, 1); err != context.Canceled {
		t.Fatalf("got %v", err)
	}
	numericAvailable(t, s, 1)
}

// DR-010; WaitersPending x UV-ContextOrder: real scheduler may choose either valid result.
func TestDR010CancelGrantRace(t *testing.T) {
	for i := 0; i < 20; i++ {
		s := NewWeighted(1)
		s.TryAcquire(1)
		cancel, result := q01Request(t, s, 1, 1)
		start, done := make(chan struct{}), make(chan error, 1)
		go func() { <-start; cancel(); done <- nil }()
		close(start)
		s.Release(1)
		q01Result(t, done, nil)
		// Bound the wait through the common result helper after forwarding the verdict.
		checked := make(chan error, 1)
		go func() {
			err := <-result
			if err == nil {
				s.Release(1)
			}
			checked <- err
		}()
		// Either success with matched release, or cancellation with internal rollback.
		select {
		case err := <-checked:
			if err != nil && err != context.Canceled {
				t.Fatal(err)
			}
		case <-contractTimeout():
			t.Fatal("race failed to finish")
		}
		numericAvailable(t, s, 1)
	}
}

// DR-011; WaitersPending x TryAcquire: false returns without joining the waiter queue.
func TestDR011TryDoesNotQueue(t *testing.T) {
	s := NewWeighted(1)
	s.TryAcquire(1)
	cancel, head := q01Request(t, s, 1, 1)
	result := make(chan error, 1)
	go func() {
		if s.TryAcquire(1) {
			result <- errUnexpectedGrant
		} else {
			result <- nil
		}
	}()
	q01Result(t, result, nil)
	cancel()
	q01Result(t, head, context.Canceled)
	s.Release(1)
	numericAvailable(t, s, 1)
}

// DR-012; WaitersPending x Acquire/TryAcquire/Grant: blocked large head cannot be bypassed.
func TestDR012HeadOfLineFIFO(t *testing.T) {
	s := NewWeighted(3)
	s.TryAcquire(3)
	_, large := q01Request(t, s, 3, 1)
	_, small := q01Request(t, s, 1, 2)
	s.Release(2)
	if s.TryAcquire(1) || s.TryAcquire(0) {
		t.Fatal("try bypassed queued predecessor")
	}
	q01Pending(t, small)
	s.Release(1)
	q01Result(t, large, nil)
	q01Pending(t, small)
	if s.TryAcquire(1) {
		t.Fatal("head grant not fully charged")
	}
	s.Release(3)
	q01Result(t, small, nil)
	s.Release(1)
	numericAvailable(t, s, 3)
}

// DR-013; NoWaiters/WaitersPending x Release(0): no accounting change or queue bypass.
func TestDR013ZeroRelease(t *testing.T) {
	zero := NewWeighted(0)
	zero.Release(0)
	if !zero.TryAcquire(0) || zero.TryAcquire(1) {
		t.Fatal("zero release changed zero capacity")
	}
	s := NewWeighted(2)
	s.Release(0)
	numericAvailable(t, s, 2)
	s.TryAcquire(2)
	cancel, head := q01Request(t, s, 2, 1)
	_, tail := q01Request(t, s, 0, 2)
	s.Release(1)
	s.Release(0)
	if s.TryAcquire(0) || s.TryAcquire(1) {
		t.Fatal("zero release bypassed queue")
	}
	q01Pending(t, head)
	q01Pending(t, tail)
	cancel()
	q01Result(t, head, context.Canceled)
	q01Result(t, tail, nil)
	s.Release(0)
	numericAvailable(t, s, 1)
	s.Release(1)
	numericAvailable(t, s, 2)
}

// DR-012; WaitersPending x Acquire: finite backlog control, not proof of an infinite bound.
func TestDR012Backlog(t *testing.T) {
	s := NewWeighted(1)
	s.TryAcquire(1)
	results := make([]<-chan error, 32)
	for i := range results {
		_, results[i] = q01Request(t, s, 1, i+1)
	}
	for _, result := range results {
		s.Release(1)
		q01Result(t, result, nil)
	}
	s.Release(1)
	numericAvailable(t, s, 1)
}
