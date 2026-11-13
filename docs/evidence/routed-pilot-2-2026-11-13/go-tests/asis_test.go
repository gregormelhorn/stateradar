package pool

// As-is tests for the routed StateRadar pilot (channelPool). Each test
// demonstrates current behaviour claimed by a finding or open question; a
// PASS means the as-is behaviour was observed, not that it is correct.
// Tests that would block forever run the call in a goroutine and report
// "still blocked after <d>" instead of hanging.

import (
	"errors"
	"fmt"
	"runtime"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

type fconn struct {
	id     int
	closed int32
	broken int32
}

type harness struct {
	mu        sync.Mutex
	next      int
	created   []*fconn
	closes    map[*fconn]int
	pings     int32
	factoryFn func() (interface{}, error)
	closeErr  error
}

func newHarness() *harness { return &harness{closes: map[*fconn]int{}} }

func (h *harness) factory() (interface{}, error) {
	if h.factoryFn != nil {
		return h.factoryFn()
	}
	h.mu.Lock()
	defer h.mu.Unlock()
	h.next++
	c := &fconn{id: h.next}
	h.created = append(h.created, c)
	return c, nil
}

func (h *harness) close(v interface{}) error {
	c := v.(*fconn)
	atomic.StoreInt32(&c.closed, 1)
	h.mu.Lock()
	h.closes[c]++
	h.mu.Unlock()
	return h.closeErr
}

func (h *harness) closeCount(c *fconn) int {
	h.mu.Lock()
	defer h.mu.Unlock()
	return h.closes[c]
}

func (h *harness) totalCloses() int {
	h.mu.Lock()
	defer h.mu.Unlock()
	n := 0
	for _, v := range h.closes {
		n += v
	}
	return n
}

func (h *harness) cfg(initial, maxIdle, maxCap int) *Config {
	return &Config{InitialCap: initial, MaxIdle: maxIdle, MaxCap: maxCap, Factory: h.factory, Close: h.close}
}

func mustPool(t *testing.T, c *Config) *channelPool {
	t.Helper()
	p, err := NewChannelPool(c)
	if err != nil {
		t.Fatalf("NewChannelPool: %v", err)
	}
	return p.(*channelPool)
}

func openCount(p *channelPool) int {
	p.mu.Lock()
	defer p.mu.Unlock()
	return p.openingConns
}

func waiters(p *channelPool) int {
	p.mu.Lock()
	defer p.mu.Unlock()
	return len(p.connReqs)
}

// blocked reports whether f is still running after d.
func blocked(f func(), d time.Duration) bool {
	done := make(chan struct{})
	go func() { f(); close(done) }()
	select {
	case <-done:
		return false
	case <-time.After(d):
		return true
	}
}

func waitFor(cond func() bool, d time.Duration) bool {
	deadline := time.Now().Add(d)
	for time.Now().Before(deadline) {
		if cond() {
			return true
		}
		time.Sleep(time.Millisecond)
	}
	return cond()
}

const blockWindow = 300 * time.Millisecond

// T1 (Q-01): Release does not wake a Get blocked at capacity.
func TestAsIs_T1_ReleaseStrandsWaiter(t *testing.T) {
	h := newHarness()
	p := mustPool(t, h.cfg(0, 1, 1))
	if _, err := p.Get(); err != nil {
		t.Fatal(err)
	}
	var res error = errors.New("unset")
	waiterDone := make(chan struct{})
	go func() { _, res = p.Get(); close(waiterDone) }()
	if !waitFor(func() bool { return waiters(p) == 1 }, time.Second) {
		t.Fatal("waiter never queued")
	}
	p.Release()
	select {
	case <-waiterDone:
		t.Fatalf("AS-IS NOT OBSERVED: waiter returned after Release with %v", res)
	case <-time.After(blockWindow):
		t.Logf("AS-IS: waiter still blocked %v after Release; connReqs=%d", blockWindow, waiters(p))
	}
}

// T2 (Q-06): Put after Release returns nil and does not close the connection.
func TestAsIs_T2_PutAfterReleaseDoesNotClose(t *testing.T) {
	h := newHarness()
	p := mustPool(t, h.cfg(0, 1, 2))
	v, _ := p.Get()
	p.Release()
	err := p.Put(v)
	if err != nil || h.closeCount(v.(*fconn)) != 0 {
		t.Fatalf("AS-IS NOT OBSERVED: err=%v closes=%d", err, h.closeCount(v.(*fconn)))
	}
	t.Logf("AS-IS: Put after Release returned %v; close callback calls for the connection: %d", err, h.closeCount(v.(*fconn)))
}

// T3 (Q-04): Close at capacity does not wake a waiter; a new Get overtakes it.
func TestAsIs_T3_CloseDoesNotWakeWaiter(t *testing.T) {
	h := newHarness()
	p := mustPool(t, h.cfg(0, 1, 1))
	c1, _ := p.Get()
	waiterDone := make(chan struct{})
	go func() { p.Get(); close(waiterDone) }()
	if !waitFor(func() bool { return waiters(p) == 1 }, time.Second) {
		t.Fatal("waiter never queued")
	}
	if err := p.Close(c1); err != nil {
		t.Fatal(err)
	}
	select {
	case <-waiterDone:
		t.Fatal("AS-IS NOT OBSERVED: waiter woke after Close")
	case <-time.After(blockWindow):
	}
	newGetBlocked := blocked(func() { p.Get() }, blockWindow)
	t.Logf("AS-IS: after Close openingConns=%d, waiter still blocked after %v, waiters=%d; a new Get blocked=%v (created a connection ahead of the waiter)",
		openCount(p), blockWindow, waiters(p), newGetBlocked)
	if newGetBlocked {
		t.Fatal("AS-IS NOT OBSERVED: new Get did not overtake")
	}
}

// T4 (Q-05): Get/Put interleaving leaves a waiter queued while a connection is idle (statistical).
func TestAsIs_T4_GetPutRaceStrandsWaiter(t *testing.T) {
	const iterations = 3000
	hits, queuedNormally := 0, 0
	for i := 0; i < iterations; i++ {
		h := newHarness()
		p := mustPool(t, h.cfg(0, 1, 1))
		c1, _ := p.Get()
		var wg sync.WaitGroup
		bDone := make(chan struct{})
		wg.Add(1)
		go func() { p.Get(); close(bDone) }()
		go func() { defer wg.Done(); runtime.Gosched(); p.Put(c1) }()
		wg.Wait()
		settled := waitFor(func() bool {
			select {
			case <-bDone:
				return true
			default:
				return waiters(p) == 1
			}
		}, time.Second)
		if !settled {
			t.Fatal("iteration did not settle")
		}
		select {
		case <-bDone:
		default:
			p.mu.Lock()
			idle := len(p.conns)
			p.mu.Unlock()
			if idle == 1 {
				hits++
			} else {
				queuedNormally++
			}
			p.Put(&fconn{id: -1}) // unblock B
			<-bDone
		}
		p.Release()
	}
	t.Logf("AS-IS (statistical): stranded waiter with an idle connection observed in %d of %d iterations (waiter queued with no idle connection: %d)", hits, iterations, queuedNormally)
}

// T5 (Q-08): unlocked read of c.ping in Get races with Release.
func TestAsIs_T5_PingFieldRace(t *testing.T) {
	var panics int32
	for i := 0; i < 200; i++ {
		h := newHarness()
		c := h.cfg(1, 1, 1)
		c.Ping = func(interface{}) error { return nil }
		p := mustPool(t, c)
		var wg sync.WaitGroup
		wg.Add(2)
		go func() {
			defer wg.Done()
			defer func() {
				if r := recover(); r != nil {
					atomic.AddInt32(&panics, 1)
				}
			}()
			p.Get()
		}()
		go func() { defer wg.Done(); p.Release() }()
		wg.Wait()
	}
	t.Logf("AS-IS: Get with Ping concurrent with Release, 200 iterations; recovered nil-function panics: %d (the race detector reports the c.ping access if the interleaving occurred)", panics)
}

// T6 (Q-10): duplicate Close drives openingConns negative and allows more than MaxCap live connections.
func TestAsIs_T6_DuplicateCloseExceedsMaxCap(t *testing.T) {
	h := newHarness()
	p := mustPool(t, h.cfg(0, 1, 1))
	c1, _ := p.Get()
	p.Close(c1)
	p.Close(c1)
	afterClose := openCount(p)
	var g2, g3 interface{}
	b2 := blocked(func() { g2, _ = p.Get() }, blockWindow)
	b3 := blocked(func() { g3, _ = p.Get() }, blockWindow)
	live := 0
	for _, c := range h.created {
		if atomic.LoadInt32(&c.closed) == 0 {
			live++
		}
	}
	t.Logf("AS-IS: openingConns after double Close=%d; two Gets blocked=%v,%v; live connections=%d with MaxCap=1 (%v, %v)", afterClose, b2, b3, live, g2, g3)
	if afterClose != -1 || b2 || b3 || live != 2 {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T7 (Q-11): duplicate Put hands one connection to two callers.
func TestAsIs_T7_DuplicatePutDoubleHandout(t *testing.T) {
	h := newHarness()
	p := mustPool(t, h.cfg(0, 2, 2))
	c1, _ := p.Get()
	p.Put(c1)
	p.Put(c1)
	x, _ := p.Get()
	y, _ := p.Get()
	t.Logf("AS-IS: two Gets after a duplicate Put returned the same connection: %v (ids %d, %d)", x == y && x == c1, x.(*fconn).id, y.(*fconn).id)
	if !(x == y && x == c1) {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T8 (Q-09): a Factory that calls back into the pool deadlocks the pool.
func TestAsIs_T8_FactoryReentrancyDeadlock(t *testing.T) {
	h := newHarness()
	var p *channelPool
	h.factoryFn = func() (interface{}, error) { p.Len(); return &fconn{id: 99}, nil }
	p = mustPool(t, h.cfg(0, 1, 2))
	getBlocked := blocked(func() { p.Get() }, blockWindow)
	lenBlocked := blocked(func() { p.Len() }, blockWindow)
	t.Logf("AS-IS: Get with a re-entrant Factory blocked=%v after %v; an unrelated Len blocked=%v", getBlocked, blockWindow, lenBlocked)
	if !getBlocked || !lenBlocked {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T9 (Q-09): a slow Factory stalls Len (and every other mutex user).
func TestAsIs_T9_SlowFactoryBlocksLen(t *testing.T) {
	h := newHarness()
	h.factoryFn = func() (interface{}, error) { time.Sleep(500 * time.Millisecond); return &fconn{id: 1}, nil }
	p := mustPool(t, h.cfg(0, 1, 2))
	go p.Get()
	time.Sleep(50 * time.Millisecond)
	start := time.Now()
	p.Len()
	d := time.Since(start)
	t.Logf("AS-IS: Len took %v while a Get was inside a 500ms Factory", d.Round(time.Millisecond))
	if d < 300*time.Millisecond {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T10 (Q-14): a connection handed to a waiter is not pinged.
func TestAsIs_T10_HandoffSkipsPing(t *testing.T) {
	h := newHarness()
	c := h.cfg(0, 1, 1)
	c.Ping = func(v interface{}) error {
		atomic.AddInt32(&h.pings, 1)
		if atomic.LoadInt32(&v.(*fconn).broken) == 1 {
			return errors.New("broken")
		}
		return nil
	}
	p := mustPool(t, c)
	c1, _ := p.Get()
	var got interface{}
	done := make(chan struct{})
	go func() { got, _ = p.Get(); close(done) }()
	waitFor(func() bool { return waiters(p) == 1 }, time.Second)
	atomic.StoreInt32(&c1.(*fconn).broken, 1)
	p.Put(c1)
	<-done
	pingsHandoff := atomic.LoadInt32(&h.pings)
	t.Logf("AS-IS: waiter received the broken connection: %v; Ping calls on the handoff path: %d", got == c1, pingsHandoff)
	if got != c1 || pingsHandoff != 0 {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T11 (Q-20, Q-02): MaxCap 0 is accepted and every Get waits forever.
func TestAsIs_T11_MaxCapZero(t *testing.T) {
	h := newHarness()
	p, err := NewChannelPool(h.cfg(0, 0, 0))
	if err != nil {
		t.Fatalf("AS-IS NOT OBSERVED: rejected: %v", err)
	}
	b := blocked(func() { p.Get() }, blockWindow)
	t.Logf("AS-IS: NewChannelPool(MaxCap=0) err=%v; Get blocked after %v: %v", err, blockWindow, b)
	if !b {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T12 (Q-06): Close after Release returns nil without calling the close callback.
func TestAsIs_T12_CloseAfterRelease(t *testing.T) {
	h := newHarness()
	p := mustPool(t, h.cfg(0, 1, 2))
	v, _ := p.Get()
	p.Release()
	err := p.Close(v)
	t.Logf("AS-IS: Close after Release returned %v; close callback calls: %d", err, h.closeCount(v.(*fconn)))
	if err != nil || h.closeCount(v.(*fconn)) != 0 {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T13 (Q-07): a Get inside Factory returns a connection after Release was called; the later Put closes nothing.
func TestAsIs_T13_GetInsideFactoryDuringRelease(t *testing.T) {
	h := newHarness()
	gate := make(chan struct{})
	entered := make(chan struct{})
	h.factoryFn = func() (interface{}, error) { close(entered); <-gate; return &fconn{id: 7}, nil }
	p := mustPool(t, h.cfg(0, 1, 2))
	var got interface{}
	var gerr error
	getDone := make(chan struct{})
	go func() { got, gerr = p.Get(); close(getDone) }()
	<-entered
	relDone := make(chan struct{})
	go func() { p.Release(); close(relDone) }()
	releaseBlocked := blocked(func() { <-relDone }, 100*time.Millisecond)
	close(gate)
	<-getDone
	<-relDone
	perr := p.Put(got)
	t.Logf("AS-IS: Release blocked while Factory ran: %v; Get returned conn=%v err=%v after Release was called; Put afterwards returned %v, close calls=%d",
		releaseBlocked, got != nil, gerr, perr, h.closeCount(got.(*fconn)))
	if got == nil || gerr != nil || !releaseBlocked || h.closeCount(got.(*fconn)) != 0 {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T14 (Q-13): expired idle connections are closed only when a Get receives them.
func TestAsIs_T14_LazyIdleExpiry(t *testing.T) {
	h := newHarness()
	c := h.cfg(2, 2, 4)
	c.IdleTimeout = 50 * time.Millisecond
	p := mustPool(t, c)
	time.Sleep(200 * time.Millisecond)
	before := h.totalCloses()
	v, err := p.Get()
	after := h.totalCloses()
	t.Logf("AS-IS: 150ms past IdleTimeout, close calls before Get=%d, after Get=%d; Get returned a new connection id=%d err=%v", before, after, v.(*fconn).id, err)
	if before != 0 || after != 2 {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T15 (Q-15): InitialCap is not maintained as a minimum.
func TestAsIs_T15_InitialCapNotMaintained(t *testing.T) {
	h := newHarness()
	p := mustPool(t, h.cfg(2, 2, 4))
	a, _ := p.Get()
	b, _ := p.Get()
	p.Close(a)
	p.Close(b)
	t.Logf("AS-IS: after two Gets and two Closes with InitialCap=2: openingConns=%d, Len=%d, factory calls=%d", openCount(p), p.Len(), len(h.created))
	if openCount(p) != 0 || p.Len() != 0 || len(h.created) != 2 {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T16 (Q-19): Factory returning (nil, nil) consumes capacity permanently.
func TestAsIs_T16_FactoryNilConn(t *testing.T) {
	h := newHarness()
	h.factoryFn = func() (interface{}, error) { return nil, nil }
	p := mustPool(t, h.cfg(0, 1, 1))
	v, err := p.Get()
	perr := p.Put(v)
	cerr := p.Close(v)
	b := blocked(func() { p.Get() }, blockWindow)
	t.Logf("AS-IS: Get returned (%v, %v); openingConns=%d; Put(nil)=%v; Close(nil)=%v; next Get blocked=%v", v, err, openCount(p), perr, cerr, b)
	if v != nil || err != nil || perr == nil || cerr == nil || !b {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T17 (Q-22): the exported Ping panics when no Ping function is configured.
func TestAsIs_T17_ExportedPingWithoutPing(t *testing.T) {
	h := newHarness()
	p := mustPool(t, h.cfg(0, 1, 1))
	var rec interface{}
	func() {
		defer func() { rec = recover() }()
		p.Ping(&fconn{id: 5})
	}()
	t.Logf("AS-IS: Ping with no Ping function configured panicked: %v", rec)
	if rec == nil {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T18 (Q-23): Put into a full idle store closes the connection although openingConns < MaxCap.
func TestAsIs_T18_PutFullIdleBelowCap(t *testing.T) {
	h := newHarness()
	p := mustPool(t, h.cfg(0, 1, 3))
	c1, _ := p.Get()
	c2, _ := p.Get()
	p.Put(c1)
	p.Put(c2)
	t.Logf("AS-IS: second Put with MaxIdle=1 closed the connection: close calls=%d; openingConns=%d < MaxCap=3", h.closeCount(c2.(*fconn)), openCount(p))
	if h.closeCount(c2.(*fconn)) != 1 || openCount(p) != 1 {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T19 (Q-16): Len counts idle connections only.
func TestAsIs_T19_LenCountsIdleOnly(t *testing.T) {
	h := newHarness()
	p := mustPool(t, h.cfg(2, 2, 5))
	p.Get()
	t.Logf("AS-IS: with 2 open connections (1 idle, 1 checked out) Len=%d, openingConns=%d", p.Len(), openCount(p))
	if p.Len() != 1 || openCount(p) != 2 {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T20 (Q-12, Q-02): lost connections are never reclaimed; the next Get waits forever.
func TestAsIs_T20_LostConnections(t *testing.T) {
	h := newHarness()
	p := mustPool(t, h.cfg(0, 1, 2))
	p.Get()
	p.Get() // both dropped by the caller
	b := blocked(func() { p.Get() }, blockWindow)
	t.Logf("AS-IS: after 2 lost connections with MaxCap=2, openingConns=%d, third Get blocked after %v: %v", openCount(p), blockWindow, b)
	if !b {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T21 (Q-18): a Close-callback error on Get's discard path is dropped.
func TestAsIs_T21_CloseErrorDroppedOnDiscard(t *testing.T) {
	h := newHarness()
	h.closeErr = errors.New("close failed")
	c := h.cfg(1, 1, 2)
	c.IdleTimeout = 30 * time.Millisecond
	p := mustPool(t, c)
	time.Sleep(80 * time.Millisecond)
	v, err := p.Get()
	t.Logf("AS-IS: Get discarded the expired connection (close calls=%d, callback error dropped) and returned id=%d err=%v; openingConns=%d", h.totalCloses(), v.(*fconn).id, err, openCount(p))
	if err != nil || h.totalCloses() != 1 || openCount(p) != 1 {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T22 (Q-17, Q-21): a Factory error is returned at once, unwrapped, without retry; the count is unchanged.
func TestAsIs_T22_FactoryErrorFailFast(t *testing.T) {
	h := newHarness()
	sentinel := errors.New("dial refused")
	var calls int32
	h.factoryFn = func() (interface{}, error) { atomic.AddInt32(&calls, 1); return nil, sentinel }
	p := mustPool(t, h.cfg(0, 1, 2))
	start := time.Now()
	_, err := p.Get()
	d := time.Since(start)
	t.Logf("AS-IS: Get returned the factory error itself=%v after %v; factory calls=%d; openingConns=%d", err == sentinel, d.Round(time.Microsecond), calls, openCount(p))
	if err != sentinel || calls != 1 || openCount(p) != 0 {
		t.Fatal("AS-IS NOT OBSERVED")
	}
}

// T23 (Q-24): a Ping failure closes the connection via the Close callback and Get continues with the next one.
func TestAsIs_T23_PingFailureDiscard(t *testing.T) {
	h := newHarness()
	c := h.cfg(2, 2, 4)
	c.Ping = func(v interface{}) error {
		if v.(*fconn).id == 1 {
			return errors.New("dead")
		}
		return nil
	}
	p := mustPool(t, c)
	v, err := p.Get()
	t.Logf("AS-IS: Get returned id=%d err=%v; close calls for id 1=%d; openingConns=%d", v.(*fconn).id, err, h.closeCount(h.created[0]), openCount(p))
	if v.(*fconn).id != 2 || h.closeCount(h.created[0]) != 1 || openCount(p) != 1 {
		t.Fatal(fmt.Sprintf("AS-IS NOT OBSERVED: got %v", v))
	}
}
