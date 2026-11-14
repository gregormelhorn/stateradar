// Copyright 2017 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// Package semaphore provides a weighted semaphore implementation.
// This evaluation copy follows the accepted decisions in CONTRACT.md.
package semaphore // import "golang.org/x/sync/semaphore"

import (
	"container/list"
	"context"
	"fmt"
	"sync"
)

type waiter struct {
	n     int64
	ready chan<- struct{} // Closed when semaphore acquired.
}

// NewWeighted creates a new weighted semaphore with the given
// maximum combined weight for concurrent access.
// A negative capacity panics (evaluation decision DR-002).
// A new instance does not reset or clean up existing instances (DR-005/008).
func NewWeighted(n int64) *Weighted {
	if n < 0 {
		panic("semaphore: negative capacity")
	}
	w := &Weighted{size: n}
	return w
}

// Weighted provides a way to bound concurrent access to a resource.
// The callers can request access with a given weight.
type Weighted struct {
	size    int64
	cur     int64
	mu      sync.Mutex
	waiters list.List
}

// Acquire acquires the semaphore with a weight of n, blocking until resources
// are available or ctx is done. On success, returns nil. On cancellation,
// returns ctx.Err(). Errors leave no net holding for this request. A negative
// weight panics (DR-002). An oversized weight returns a size error without waiting for
// cancellation; an already canceled context retains priority (DR-004).
//
// Each invocation is independent, including repeat calls by one caller;
// holding capacity while awaiting another acquisition can self-block (DR-006).
// A successful call requires matching release after work ends. Later Context
// cancellation does not reclaim that holding (DR-005). Errors leave no own
// holding or queue entry, but transient reservations can affect concurrent
// operations. Cancellation after the last check can coexist with success
// (DR-010); the return value determines the release obligation.
//
// ctx must be a non-nil, conforming Context. A nil Done channel is valid;
// faulty custom methods have no recovery or extra progress guarantee (DR-009).
// The caller selects the correct instance and Context (DR-008). Mutex waits
// are permitted and no fixed cancellation-latency bound is promised (DR-011).
// Queued grants are FIFO by enqueue order without bypass of a blocked head;
// return order is unspecified. The queue has no internal count cap (DR-012).
func (s *Weighted) Acquire(ctx context.Context, n int64) error {
	if n < 0 {
		panic("semaphore: negative weight")
	}
	done := ctx.Done()

	s.mu.Lock()
	select {
	case <-done:
		// ctx becoming done has "happened before" acquiring the semaphore,
		// whether it became done before the call began or while we were
		// waiting for the mutex. We prefer to fail even if we could acquire
		// the mutex without blocking.
		s.mu.Unlock()
		return ctx.Err()
	default:
	}
	if s.size-s.cur >= n && s.waiters.Len() == 0 {
		// Since we hold s.mu and haven't synchronized since checking done, if
		// ctx becomes done before we return here, it becoming done must have
		// "happened concurrently" with this call - it cannot "happen before"
		// we return in this branch. So, we're ok to always acquire here.
		s.cur += n
		s.mu.Unlock()
		return nil
	}

	if n > s.size {
		// DR-004: this request can never fit; do not enqueue or await Done.
		s.mu.Unlock()
		return fmt.Errorf("semaphore: requested weight %d exceeds capacity %d", n, s.size)
	}

	ready := make(chan struct{})
	w := waiter{n: n, ready: ready}
	elem := s.waiters.PushBack(w)
	s.mu.Unlock()

	select {
	case <-done:
		s.mu.Lock()
		select {
		case <-ready:
			// Acquired the semaphore after we were canceled.
			// Pretend we didn't and put the tokens back.
			s.cur -= n
			s.notifyWaiters()
		default:
			isFront := s.waiters.Front() == elem
			s.waiters.Remove(elem)
			// Notify the new front even at capacity: it may request zero tokens.
			if isFront {
				s.notifyWaiters()
			}
		}
		s.mu.Unlock()
		return ctx.Err()

	case <-ready:
		// Acquired the semaphore. Check that ctx isn't already done.
		// We check the done channel instead of calling ctx.Err because we
		// already have the channel, and ctx.Err is O(n) with the nesting
		// depth of ctx.
		select {
		case <-done:
			s.Release(n)
			return ctx.Err()
		default:
		}
		return nil
	}
}

// TryAcquire attempts to acquire weight n without joining the capacity queue
// or awaiting a future release. It may wait for the internal mutex (DR-011).
// On success, returns true. On failure, returns false and leaves the semaphore unchanged.
// A negative weight panics before mutation (DR-002).
// Existing queued requests cannot be bypassed, including by weight zero (DR-012).
func (s *Weighted) TryAcquire(n int64) bool {
	if n < 0 {
		panic("semaphore: negative weight")
	}
	s.mu.Lock()
	success := s.size-s.cur >= n && s.waiters.Len() == 0
	if success {
		s.cur += n
	}
	s.mu.Unlock()
	return success
}

// Release releases the semaphore with a weight of n.
// Negative weights or release above the aggregate held weight panic without
// changing the instance (evaluation decisions DR-002 and DR-003).
// Responsibility may transfer between goroutines, but the application must
// match releases to held, not already released capacity on this instance.
// Aggregate accounting does not detect every duplicate release (DR-007/008).
// Release(0) is a logical no-op for capacity, queue and grants in valid reachable
// states, not a wakeup, repair or extra synchronization operation (DR-013).
func (s *Weighted) Release(n int64) {
	if n < 0 {
		panic("semaphore: negative weight")
	}
	s.mu.Lock()
	if n > s.cur {
		s.mu.Unlock()
		panic("semaphore: released more than held")
	}
	s.cur -= n
	s.notifyWaiters()
	s.mu.Unlock()
}

func (s *Weighted) notifyWaiters() {
	for {
		next := s.waiters.Front()
		if next == nil {
			break // No more waiters blocked.
		}

		w := next.Value.(waiter)
		if s.size-s.cur < w.n {
			// Not enough tokens for the next waiter.  We could keep going (to try to
			// find a waiter with a smaller request), but under load that could cause
			// starvation for large requests; instead, we leave all remaining waiters
			// blocked.
			//
			// Consider a semaphore used as a read-write lock, with N tokens, N
			// readers, and one writer.  Each reader can Acquire(1) to obtain a read
			// lock.  The writer can Acquire(N) to obtain a write lock, excluding all
			// of the readers.  If we allow the readers to jump ahead in the queue,
			// the writer will starve — there is always one token available for every
			// reader.
			break
		}

		s.cur += w.n
		s.waiters.Remove(next)
		close(w.ready)
	}
}
