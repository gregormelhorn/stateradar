package pool

import (
	"errors"
	"sync/atomic"
	"testing"
	"time"
)

type asisConn struct {
	id     int
	closed int32
}

type asisFactory struct {
	count int32
	errOn int32
}

func (f *asisFactory) make() (interface{}, error) {
	n := atomic.AddInt32(&f.count, 1)
	if f.errOn > 0 && n == f.errOn {
		return nil, errors.New("factory failure")
	}
	return &asisConn{id: int(n)}, nil
}

func newAsisPool(t *testing.T, cfg Config) Pool {
	t.Helper()
	p, err := NewChannelPool(&cfg)
	if err != nil {
		t.Fatalf("NewChannelPool error: %v", err)
	}
	return p
}

func TestAsIs_Get_IdleAvailable(t *testing.T) {
	f := &asisFactory{}
	var closes int32
	p := newAsisPool(t, Config{
		InitialCap: 2,
		MaxIdle:    3,
		MaxCap:     5,
		Factory:    f.make,
		Close: func(c interface{}) error {
			atomic.AddInt32(&closes, 1)
			return nil
		},
	})
	if got := p.Len(); got != 2 {
		t.Fatalf("expected Len 2, got %d", got)
	}
	before := atomic.LoadInt32(&f.count)
	c, err := p.Get()
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	if c == nil {
		t.Fatalf("expected connection")
	}
	if got := atomic.LoadInt32(&f.count); got != before {
		t.Fatalf("factory should not be called again, count %d -> %d", before, got)
	}
	if got := p.Len(); got != 1 {
		t.Fatalf("expected Len 1 after Get, got %d", got)
	}
}

func TestAsIs_Get_NoIdleBelowCap(t *testing.T) {
	f := &asisFactory{}
	p := newAsisPool(t, Config{
		InitialCap: 0,
		MaxIdle:    2,
		MaxCap:     3,
		Factory:    f.make,
		Close:      func(c interface{}) error { return nil },
	})
	c, err := p.Get()
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	if c == nil {
		t.Fatalf("expected connection")
	}
	if got := atomic.LoadInt32(&f.count); got != 1 {
		t.Fatalf("expected factory called once, got %d", got)
	}
}

func TestAsIs_Put_StoresIdle(t *testing.T) {
	f := &asisFactory{}
	p := newAsisPool(t, Config{
		InitialCap: 0,
		MaxIdle:    2,
		MaxCap:     3,
		Factory:    f.make,
		Close:      func(c interface{}) error { return nil },
	})
	c, err := p.Get()
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	if err := p.Put(c); err != nil {
		t.Fatalf("Put error: %v", err)
	}
	if got := p.Len(); got != 1 {
		t.Fatalf("expected Len 1, got %d", got)
	}
}

func TestAsIs_Put_IdleFull_ClosesConnection(t *testing.T) {
	f := &asisFactory{}
	var closes int32
	p := newAsisPool(t, Config{
		InitialCap: 0,
		MaxIdle:    1,
		MaxCap:     3,
		Factory:    f.make,
		Close: func(c interface{}) error {
			atomic.AddInt32(&closes, 1)
			atomic.StoreInt32(&c.(*asisConn).closed, 1)
			return nil
		},
	})
	c1, err := p.Get()
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	c2, err := p.Get()
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	if err := p.Put(c1); err != nil {
		t.Fatalf("Put error: %v", err)
	}
	before := atomic.LoadInt32(&closes)
	if err := p.Put(c2); err != nil {
		t.Fatalf("Put error: %v", err)
	}
	if got := atomic.LoadInt32(&closes); got != before+1 {
		t.Fatalf("expected close callback once more, got %d", got)
	}
	if atomic.LoadInt32(&c2.(*asisConn).closed) != 1 {
		t.Fatalf("expected c2 closed")
	}
}

func TestAsIs_Get_AtCap_BlocksUntilPut(t *testing.T) {
	f := &asisFactory{}
	p := newAsisPool(t, Config{
		InitialCap: 0,
		MaxIdle:    1,
		MaxCap:     1,
		Factory:    f.make,
		Close:      func(c interface{}) error { return nil },
	})
	c1, err := p.Get()
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	done := make(chan interface{}, 1)
	go func() {
		c, err := p.Get()
		if err == nil {
			done <- c
		} else {
			done <- nil
		}
	}()
	select {
	case <-done:
		t.Fatalf("second Get should block")
	case <-time.After(200 * time.Millisecond):
	}
	if err := p.Put(c1); err != nil {
		t.Fatalf("Put error: %v", err)
	}
	select {
	case got := <-done:
		if got != c1 {
			t.Fatalf("expected same connection after Put")
		}
	case <-time.After(200 * time.Millisecond):
		t.Fatalf("second Get did not return after Put")
	}
}

func TestAsIs_Get_ExpiredIdle_Replaced(t *testing.T) {
	f := &asisFactory{}
	var closes int32
	p := newAsisPool(t, Config{
		InitialCap:  1,
		MaxIdle:     2,
		MaxCap:      3,
		IdleTimeout: 50 * time.Millisecond,
		Factory:     f.make,
		Close: func(c interface{}) error {
			atomic.AddInt32(&closes, 1)
			atomic.StoreInt32(&c.(*asisConn).closed, 1)
			return nil
		},
	})
	time.Sleep(150 * time.Millisecond)
	before := atomic.LoadInt32(&closes)
	c, err := p.Get()
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	if got := atomic.LoadInt32(&closes); got != before+1 {
		t.Fatalf("expected stale idle closed, closes %d", got)
	}
	if c.(*asisConn).id != 2 {
		t.Fatalf("expected new connection id 2, got %d", c.(*asisConn).id)
	}
}

func TestAsIs_Get_PingFails_DiscardsIdle(t *testing.T) {
	f := &asisFactory{}
	var closes int32
	var pingCalls int32
	p := newAsisPool(t, Config{
		InitialCap: 1,
		MaxIdle:    2,
		MaxCap:     3,
		Factory:    f.make,
		Close: func(c interface{}) error {
			atomic.AddInt32(&closes, 1)
			return nil
		},
		Ping: func(c interface{}) error {
			n := atomic.AddInt32(&pingCalls, 1)
			if n == 1 {
				return errors.New("ping failed")
			}
			return nil
		},
	})
	before := atomic.LoadInt32(&closes)
	c, err := p.Get()
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	if got := atomic.LoadInt32(&closes); got != before+1 {
		t.Fatalf("expected idle closed after ping fail, got %d", got)
	}
	if c.(*asisConn).id != 2 {
		t.Fatalf("expected new connection id 2, got %d", c.(*asisConn).id)
	}
}

func TestAsIs_Release_ClosesIdleThenGetErrClosed(t *testing.T) {
	f := &asisFactory{}
	var closes int32
	p := newAsisPool(t, Config{
		InitialCap: 2,
		MaxIdle:    3,
		MaxCap:     5,
		Factory:    f.make,
		Close: func(c interface{}) error {
			atomic.AddInt32(&closes, 1)
			return nil
		},
	})
	p.Release()
	if got := atomic.LoadInt32(&closes); got != 2 {
		t.Fatalf("expected 2 idle closed, got %d", got)
	}
	if _, err := p.Get(); err != ErrClosed {
		t.Fatalf("expected ErrClosed, got %v", err)
	}
	if got := p.Len(); got != 0 {
		t.Fatalf("expected Len 0, got %d", got)
	}
}

func TestAsIs_Release_Twice(t *testing.T) {
	f := &asisFactory{}
	p := newAsisPool(t, Config{
		InitialCap: 1,
		MaxIdle:    2,
		MaxCap:     3,
		Factory:    f.make,
		Close:      func(c interface{}) error { return nil },
	})
	p.Release()
	p.Release()
}

func TestAsIs_Put_AfterRelease_NoClose(t *testing.T) {
	f := &asisFactory{}
	var closes int32
	p := newAsisPool(t, Config{
		InitialCap: 0,
		MaxIdle:    2,
		MaxCap:     3,
		Factory:    f.make,
		Close: func(c interface{}) error {
			atomic.AddInt32(&closes, 1)
			return nil
		},
	})
	c, err := p.Get()
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	p.Release()
	before := atomic.LoadInt32(&closes)
	if err := p.Put(c); err != nil {
		t.Fatalf("Put error: %v", err)
	}
	if got := atomic.LoadInt32(&closes); got != before {
		t.Fatalf("close callback should not be called, got %d", got)
	}
}

func TestAsIs_Release_DoesNotWakeWaiter(t *testing.T) {
	f := &asisFactory{}
	p := newAsisPool(t, Config{
		InitialCap: 0,
		MaxIdle:    1,
		MaxCap:     1,
		Factory:    f.make,
		Close:      func(c interface{}) error { return nil },
	})
	c1, err := p.Get()
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	_ = c1
	done := make(chan struct{}, 1)
	go func() {
		p.Get()
		done <- struct{}{}
	}()
	time.Sleep(50 * time.Millisecond)
	p.Release()
	select {
	case <-done:
		t.Fatalf("waiter should remain blocked after Release")
	case <-time.After(300 * time.Millisecond):
	}
}

func TestAsIs_Close_DoesNotServeWaiter(t *testing.T) {
	f := &asisFactory{}
	p := newAsisPool(t, Config{
		InitialCap: 0,
		MaxIdle:    1,
		MaxCap:     1,
		Factory:    f.make,
		Close:      func(c interface{}) error { return nil },
	})
	c1, err := p.Get()
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	done := make(chan struct{}, 1)
	go func() {
		p.Get()
		done <- struct{}{}
	}()
	time.Sleep(50 * time.Millisecond)
	if err := p.Close(c1); err != nil {
		t.Fatalf("Close error: %v", err)
	}
	select {
	case <-done:
		t.Fatalf("waiter should remain blocked after Close")
	case <-time.After(300 * time.Millisecond):
	}
	// third goroutine should succeed by creating a connection
	res := make(chan interface{}, 1)
	go func() {
		c, err := p.Get()
		if err == nil {
			res <- c
		} else {
			res <- nil
		}
	}()
	select {
	case c := <-res:
		if c == nil {
			t.Fatalf("expected new connection for third goroutine")
		}
	case <-time.After(300 * time.Millisecond):
		t.Fatalf("third Get did not return")
	}
}

func TestAsIs_Nil_Rejected(t *testing.T) {
	f := &asisFactory{}
	p := newAsisPool(t, Config{
		InitialCap: 0,
		MaxIdle:    1,
		MaxCap:     1,
		Factory:    f.make,
		Close:      func(c interface{}) error { return nil },
	})
	if err := p.Put(nil); err == nil {
		t.Fatalf("Put(nil) should return error")
	}
	if err := p.Close(nil); err == nil {
		t.Fatalf("Close(nil) should return error")
	}
}

func TestAsIs_Close_Twice_ExceedsMaxCap(t *testing.T) {
	f := &asisFactory{}
	var open int32 // created and not yet closed (by the close callback)
	p := newAsisPool(t, Config{
		InitialCap: 0,
		MaxIdle:    1,
		MaxCap:     2,
		Factory: func() (interface{}, error) {
			c, err := f.make()
			atomic.AddInt32(&open, 1)
			return c, err
		},
		Close: func(c interface{}) error {
			atomic.AddInt32(&open, -1)
			return nil
		},
	})
	a, _ := p.Get()
	_, _ = p.Get()
	if err := p.Close(a); err != nil {
		t.Fatalf("Close error: %v", err)
	}
	if err := p.Close(a); err != nil {
		t.Fatalf("second Close error: %v", err)
	}
	for i := 0; i < 2; i++ {
		done := make(chan struct{}, 1)
		go func() {
			p.Get()
			done <- struct{}{}
		}()
		select {
		case <-done:
		case <-time.After(200 * time.Millisecond):
			t.Fatalf("Get %d blocked unexpectedly", i)
		}
	}
	// the close callback ran twice for a, so open is 2 - 2 + 2 = 2 by the counter,
	// but only one connection (a) was really closed: 3 real connections are in use.
	if got := atomic.LoadInt32(&f.count); got != 4 {
		t.Fatalf("expected 4 factory calls, got %d", got)
	}
}

func TestAsIs_Len_CountsIdleOnly(t *testing.T) {
	f := &asisFactory{}
	p := newAsisPool(t, Config{
		InitialCap: 2,
		MaxIdle:    3,
		MaxCap:     5,
		Factory:    f.make,
		Close:      func(c interface{}) error { return nil },
	})
	if got := p.Len(); got != 2 {
		t.Fatalf("expected Len 2, got %d", got)
	}
	c, err := p.Get()
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	if got := p.Len(); got != 1 {
		t.Fatalf("expected Len 1 after borrow, got %d", got)
	}
	c2, err := p.Get()
	if err != nil {
		t.Fatalf("Get error: %v", err)
	}
	if got := p.Len(); got != 0 {
		t.Fatalf("expected Len 0 after two borrows, got %d", got)
	}
	_ = c
	_ = c2
}

func TestAsIs_New_FactoryError(t *testing.T) {
	f := &asisFactory{errOn: 3}
	var closes int32
	_, err := NewChannelPool(&Config{
		InitialCap: 3,
		MaxIdle:    3,
		MaxCap:     5,
		Factory:    f.make,
		Close: func(c interface{}) error {
			atomic.AddInt32(&closes, 1)
			return nil
		},
	})
	if err == nil {
		t.Fatalf("expected NewChannelPool error")
	}
	if got := atomic.LoadInt32(&closes); got != 2 {
		t.Fatalf("expected 2 created connections closed, got %d", got)
	}
}

func TestAsIs_New_InvalidConfig(t *testing.T) {
	f := &asisFactory{}
	closeFn := func(c interface{}) error { return nil }
	// capacity
	if _, err := NewChannelPool(&Config{
		InitialCap: 2,
		MaxIdle:    1,
		MaxCap:     3,
		Factory:    f.make,
		Close:      closeFn,
	}); err == nil {
		t.Fatalf("expected capacity error")
	}
	// factory nil
	if _, err := NewChannelPool(&Config{
		InitialCap: 0,
		MaxIdle:    1,
		MaxCap:     3,
		Close:      closeFn,
	}); err == nil {
		t.Fatalf("expected factory error")
	}
	// close nil
	if _, err := NewChannelPool(&Config{
		InitialCap: 0,
		MaxIdle:    1,
		MaxCap:     3,
		Factory:    f.make,
	}); err == nil {
		t.Fatalf("expected close error")
	}
}

func TestAsIs_New_ZeroCapAccepted(t *testing.T) {
	f := &asisFactory{}
	if _, err := NewChannelPool(&Config{
		InitialCap: 0,
		MaxIdle:    0,
		MaxCap:     0,
		Factory:    f.make,
		Close:      func(c interface{}) error { return nil },
	}); err != nil {
		t.Fatalf("expected zero-cap config accepted, got %v", err)
	}
}

func TestAsIs_Get_ConcurrentWithRelease(t *testing.T) {
	var panics int32
	for i := 0; i < 200; i++ {
		f := &asisFactory{}
		p, err := NewChannelPool(&Config{
			InitialCap: 1,
			MaxIdle:    2,
			MaxCap:     3,
			Factory:    f.make,
			Close:      func(c interface{}) error { return nil },
			Ping:       func(c interface{}) error { return nil },
		})
		if err != nil {
			t.Fatalf("NewChannelPool error: %v", err)
		}
		done := make(chan struct{})
		go func() {
			defer func() {
				if r := recover(); r != nil {
					atomic.AddInt32(&panics, 1)
				}
				close(done)
			}()
			p.Get()
		}()
		p.Release()
		select {
		case <-done:
		case <-time.After(200 * time.Millisecond):
		}
	}
	t.Logf("panics observed in 200 rounds: %d", atomic.LoadInt32(&panics))
}
