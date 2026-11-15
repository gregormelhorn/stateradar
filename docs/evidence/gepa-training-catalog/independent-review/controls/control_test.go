package independent

import (
 "sync"
 "testing"
 "testing/synctest"
)

func TestInsideWaitClearsBeforeOutside(t *testing.T) {
 var wg sync.WaitGroup
 synctest.Test(t,func(t *testing.T) { wg.Add(1); wg.Done(); wg.Wait() })
 wg.Wait()
}

func TestSignalWithoutHoldingLock(t *testing.T) {
 var mu sync.Mutex
 c:=sync.NewCond(&mu)
 ready:=make(chan struct{})
 done:=make(chan struct{})
 go func() { mu.Lock(); close(ready); c.Wait(); mu.Unlock(); close(done) }()
 <-ready
 mu.Lock(); mu.Unlock()
 c.Signal()
 <-done
}

func TestDefaultPanicNilRecoverIsNonNil(t *testing.T) {
 defer func(){ if recover()==nil {t.Fatal("expected non-nil runtime panic value")} }()
 panic(nil)
}
