// Copyright 2017 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

// Package semaphore provides a weighted semaphore implementation.
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
// returns ctx.Err(). Errors leave the semaphore unchanged. A negative weight panics
// (DR-002). An oversized weight returns a size error without waiting for
// cancellation; an already canceled context retains priority (DR-004).
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

// TryAcquire acquires the semaphore with a weight of n without blocking.
// On success, returns true. On failure, returns false and leaves the semaphore unchanged.
// A negative weight panics before mutation (DR-002).
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
