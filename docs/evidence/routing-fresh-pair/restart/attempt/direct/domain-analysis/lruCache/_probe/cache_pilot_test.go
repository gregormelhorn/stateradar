package lru

import (
	"math"
	"runtime"
	"strings"
	"sync"
	"testing"
	"time"
)

func recvPilot[T any](t *testing.T, ch <-chan T) T {
	t.Helper()
	select {
	case v := <-ch:
		return v
	case <-time.After(2 * time.Second):
		t.Fatal("timed out waiting for scheduled result")
		var z T
		return z
	}
}

func TestPilotPurgeThenAdd(t *testing.T) {
	c, _ := New[int, int](1)
	if c.Add(1, 1) || c.Len() != c.Cap() || !c.Contains(1) {
		t.Fatal("empty size-one cache did not become full")
	}

	seen := make(chan int, 2)
	entered := make(chan struct{})
	release := make(chan struct{})
	older := make(chan bool, 1)
	d, _ := NewWithEvict(1, func(k, v int) {
		if k == 1 {
			close(entered)
			<-release
		}
		seen <- k
	})
	d.Add(1, 1)
	go func() { older <- d.Add(2, 2) }()
	recvPilot(t, entered)
	d.Purge()
	if !d.Add(3, 3) && d.Len() == d.Cap() && d.Contains(3) {
		t.Log("purge then add reached full while older callback remained pending")
	} else {
		t.Fatal("purge then add did not leave just the new entry")
	}
	if k := recvPilot(t, seen); k != 2 {
		t.Fatalf("later purge callback got key %d", k)
	}
	select {
	case <-older:
		t.Fatal("earlier add returned before its callback released")
	default:
	}
	close(release)
	if k := recvPilot(t, seen); k != 1 {
		t.Fatalf("older callback got key %d", k)
	}
	if !recvPilot(t, older) {
		t.Fatal("older Add lost its committed eviction result")
	}
}

func TestPilotResizeBoundary(t *testing.T) {
	c, err := New[int, int](0)
	if err == nil || c == nil {
		t.Fatal("zero constructor did not return nonnil unusable receiver and error")
	}
	seen := 0
	d, _ := NewWithEvict(2, func(int, int) { seen++ })
	d.Add(1, 1)
	if got := d.Resize(-2); got != 3 || seen != 1 || d.Len() != 0 || d.Cap() != -2 {
		t.Fatalf("negative resize: count=%d callbacks=%d len=%d cap=%d", got, seen, d.Len(), d.Cap())
	}
	if !d.Add(2, 2) || d.Len() != 0 || seen != 2 {
		t.Fatal("negative-capacity insertion did not immediately evict")
	}
	if got := d.Resize(0); got != 0 || d.Cap() != 0 || !d.Add(3, 3) || d.Len() != 0 {
		t.Fatal("zero resize did not leave immediately evicting cache")
	}
	d.Resize(2)
	d.Add(4, 4)
	min := -int(^uint(0)>>1) - 1
	if got := d.Resize(min); got != 0 || d.Len() != 1 || d.Cap() != min || !d.Contains(4) {
		t.Fatalf("extreme resize: count=%d len=%d cap=%d", got, d.Len(), d.Cap())
	}
}

func TestPilotNaNRemovalAndPurge(t *testing.T) {
	var callbacks []float64
	c, _ := NewWithEvict(1, func(k float64, v int) { callbacks = append(callbacks, k) })
	k := math.NaN()
	c.Add(k, 1)
	if c.Contains(k) || c.Remove(k) || c.Len() != 1 {
		t.Fatal("NaN was not an unfindable listed entry")
	}
	c.Add(1, 2)
	if len(callbacks) != 1 || !math.IsNaN(callbacks[0]) || c.Len() != 1 {
		t.Fatal("capacity eviction did not deliver NaN")
	}
	c.Purge()
	if c.Len() != 0 || len(c.Keys()) != 0 || len(callbacks) != 3 {
		t.Fatal("Purge did not notify for orphaned key")
	}
	c.Purge()
	if len(callbacks) != 4 || !math.IsNaN(callbacks[3]) {
		t.Fatal("second Purge did not notify for orphaned key")
	}
}

func panicPilot(fn func()) (p any) { defer func() { p = recover() }(); fn(); return }
func TestPilotKeyPanicAndLock(t *testing.T) {
	c, _ := New[any, int](2)
	c.Add("valid", 1)
	p := panicPilot(func() { c.Get([]int{1}) })
	if p == nil || !strings.Contains(p.(error).Error(), "unhashable") {
		t.Fatalf("expected hash panic, got %v", p)
	}
	if c.Cap() != 2 {
		t.Fatal("Cap stopped bypassing stranded lock")
	}
	done := make(chan int, 1)
	go func() { done <- c.Len() }()
	select {
	case <-done:
		t.Fatal("Len unexpectedly acquired lock after recovered hash panic")
	case <-time.After(30 * time.Millisecond):
	}

	d, _ := New[any, int](1)
	d.Add("valid", 1)
	if panicPilot(func() { d.Contains([]int{1}) }) == nil || !d.Contains("valid") {
		t.Fatal("reader panic did not leave other reads possible")
	}
	w := make(chan bool, 1)
	go func() { w <- d.Add("next", 2) }()
	select {
	case <-w:
		t.Fatal("Add unexpectedly acquired lock after recovered reader panic")
	case <-time.After(30 * time.Millisecond):
	}
}
func TestPilotFailedConstructorPanic(t *testing.T) {
	c, err := New[int, int](-1)
	if c == nil || err == nil || panicPilot(func() { c.Get(1) }) == nil {
		t.Fatal("failed receiver use did not panic")
	}
}
func TestPilotCallbackPanicAndGoexit(t *testing.T) {
	for _, mode := range []string{"panic", "goexit"} {
		t.Run(mode, func(t *testing.T) {
			var c *Cache[int, int]
			called := make(chan int, 3)
			c, _ = NewWithEvict(3, func(k, v int) {
				if c.Len() != 0 {
					t.Error("underlying clear/resize did not commit before callback")
				}
				called <- k
				if mode == "panic" {
					panic("callback fault")
				}
				runtime.Goexit()
			})
			c.Add(1, 1)
			c.Add(2, 2)
			c.Add(3, 3)
			finish := make(chan any, 1)
			normal := make(chan bool, 1)
			go func() {
				defer func() { finish <- recover() }()
				if mode == "panic" {
					c.Purge()
				} else {
					c.Resize(0)
				}
				normal <- true
			}()
			v := recvPilot(t, finish)
			if (mode == "panic" && v != "callback fault") || (mode == "goexit" && v != nil) {
				t.Fatalf("wrong escape: %v", v)
			}
			if len(called) != 1 || c.Len() != 0 || len(normal) != 0 {
				t.Fatal("callback tail was not abandoned after commit")
			}
			if mode == "goexit" && c.Cap() != 0 {
				t.Fatal("Resize did not commit before Goexit")
			}
			c.Resize(3)
			c.Add(4, 4)
			if !c.Contains(4) || len(called) != 1 {
				t.Fatal("new matching activity replayed aborted batch or cache unusable")
			}
		})
	}
}
func TestPilotCallbackAfterPurgeFailureAndRecovery(t *testing.T) {
	for _, mode := range []string{"normal", "panic"} {
		t.Run(mode, func(t *testing.T) {
			entered := make(chan struct{})
			release := make(chan struct{})
			result := make(chan any, 1)
			c, _ := NewWithEvict(1, func(k, v int) {
				if k == 1 {
					close(entered)
					<-release
					if mode == "panic" {
						panic("late")
					}
				}
			})
			c.Add(1, 1)
			go func() { result <- panicPilot(func() { c.Add(2, 2) }) }()
			recvPilot(t, entered)
			c.Purge()
			c.Resize(2)
			c.Add(1, 11)
			close(release)
			got := recvPilot(t, result)
			if (mode == "normal" && got != nil) || (mode == "panic" && got != "late") {
				t.Fatalf("unexpected callback outcome %v", got)
			}
			if v, ok := c.Get(1); !ok || v != 11 || c.Len() != 1 {
				t.Fatal("stale callback changed replacement value")
			}
		})
	}
}
func TestPilotGetTwiceSameValue(t *testing.T) {
	c, _ := New[int, *int](1)
	v := 1
	c.Add(1, &v)
	a := make(chan *int, 1)
	b := make(chan *int, 1)
	go func() { v, _ := c.Get(1); a <- v }()
	go func() { v, _ := c.Get(1); b <- v }()
	a1, b1 := recvPilot(t, a), recvPilot(t, b)
	held, ok := c.Get(1)
	c.Purge()
	if a1 != &v || b1 != &v || !ok || held != &v || *held != 1 || c.Len() != 0 {
		t.Fatal("Get created ownership or lost caller's retained value")
	}
}

func TestPilotRaceCapResize(t *testing.T) {
	c, _ := New[int, int](2)
	start := make(chan struct{})
	var wg sync.WaitGroup
	wg.Add(2)
	go func() {
		defer wg.Done()
		<-start
		for j := 0; j < 1000; j++ {
			c.Resize(1 + j%2)
		}
	}()
	go func() {
		defer wg.Done()
		<-start
		for j := 0; j < 1000; j++ {
			_ = c.Cap()
		}
	}()
	close(start)
	wg.Wait()
}
