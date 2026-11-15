package reference

import (
	"os"
	"runtime"
	"strings"
	"sync"
	"testing"
	"testing/synctest"
	"time"
)

func TestCondSignalBeforeWait(t *testing.T) {
	var mu sync.Mutex
	cond := sync.NewCond(&mu)
	cond.Signal()
	started := make(chan struct{})
	returned := make(chan struct{})
	go func() {
		mu.Lock()
		close(started)
		cond.Wait()
		close(returned)
		mu.Unlock()
	}()
	<-started
	mu.Lock()
	mu.Unlock()
	select {
	case <-returned:
		t.Fatal("earlier signal released future waiter")
	case <-time.After(50 * time.Millisecond):
	}
	cond.Signal()
	<-returned
}

func TestWaitGroupPositiveAddWhileActive(t *testing.T) {
	var wg sync.WaitGroup
	wg.Add(1)
	wg.Add(1)
	wg.Done()
	started := make(chan struct{})
	finished := make(chan struct{})
	go func() { close(started); wg.Wait(); close(finished) }()
	<-started
	select {
	case <-finished:
		t.Fatal("Wait returned with a positive counter")
	case <-time.After(50 * time.Millisecond):
	}
	wg.Done()
	<-finished
}

func TestWaitGroupGoPanicNilLegacy(t *testing.T) {
	if !strings.Contains(os.Getenv("GODEBUG"), "panicnil=1") {
		t.Skip("requires GODEBUG=panicnil=1")
	}
	var wg sync.WaitGroup
	wg.Go(func() { panic(nil) })
	wg.Wait()
}

func TestWaitGroupSynctestOutsideWait(t *testing.T) {
	var wg sync.WaitGroup
	synctest.Test(t, func(t *testing.T) {
		wg.Add(1)
		wg.Done()
	})
	defer func() {
		r := recover()
		if _, ok := r.(runtime.Error); !ok {
			t.Fatalf("expected runtime panic from outside Wait; got %#v", r)
		}
		t.Logf("outside Wait panic: %v", r)
	}()
	wg.Wait()
}
