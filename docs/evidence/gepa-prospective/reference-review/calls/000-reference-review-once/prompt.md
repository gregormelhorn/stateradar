Independently check each proposed behavior against the cited source and the supplied executable test. No domain decisions. A finite timeout proves only bounded nonreturn and may miss an unscheduled thread. Return JSON {"cases":[{"id":"...","verdict":"confirmed|refuted|unclear","reason":"...","line":1,"fragment":"exact source substring"}]}. Assess every case.
CANDIDATE OBSERVATIONS:
[{"id": "O01", "question_required": false, "description": "On a fresh sync.Once, if the first function panics, the panic propagates; after recovery, a later Do returns without calling its function.", "test": "TestOncePanicDone"}, {"id": "O02", "question_required": false, "description": "When the first Do function has started and is blocked, a concurrent Do cannot return until the first function finishes, and the second function is not called.", "test": "TestOnceConcurrentWait"}]
SOURCE:
1: // Copyright 2009 The Go Authors. All rights reserved.
2: // Use of this source code is governed by a BSD-style
3: // license that can be found in the LICENSE file.
4: 
5: package sync
6: 
7: import (
8: 	"sync/atomic"
9: )
10: 
11: // Once is an object that will perform exactly one action.
12: //
13: // A Once must not be copied after first use.
14: //
15: // In the terminology of [the Go memory model],
16: // the return from f “synchronizes before”
17: // the return from any call of once.Do(f).
18: //
19: // [the Go memory model]: https://go.dev/ref/mem
20: type Once struct {
21: 	_ noCopy
22: 
23: 	// done indicates whether the action has been performed.
24: 	// It is first in the struct because it is used in the hot path.
25: 	// The hot path is inlined at every call site.
26: 	// Placing done first allows more compact instructions on some architectures (amd64/386),
27: 	// and fewer instructions (to calculate offset) on other architectures.
28: 	done atomic.Bool
29: 	m    Mutex
30: }
31: 
32: // Do calls the function f if and only if Do is being called for the
33: // first time for this instance of [Once]. In other words, given
34: //
35: //	var once Once
36: //
37: // if once.Do(f) is called multiple times, only the first call will invoke f,
38: // even if f has a different value in each invocation. A new instance of
39: // Once is required for each function to execute.
40: //
41: // Do is intended for initialization that must be run exactly once. Since f
42: // is niladic, it may be necessary to use a function literal to capture the
43: // arguments to a function to be invoked by Do:
44: //
45: //	config.once.Do(func() { config.init(filename) })
46: //
47: // Because no call to Do returns until the one call to f returns, if f causes
48: // Do to be called, it will deadlock.
49: //
50: // If f panics, Do considers it to have returned; future calls of Do return
51: // without calling f.
52: func (o *Once) Do(f func()) {
53: 	// Note: Here is an incorrect implementation of Do:
54: 	//
55: 	//	if o.done.CompareAndSwap(false, true) {
56: 	//		f()
57: 	//	}
58: 	//
59: 	// Do guarantees that when it returns, f has finished.
60: 	// This implementation would not implement that guarantee:
61: 	// given two simultaneous calls, the winner of the cas would
62: 	// call f, and the second would return immediately, without
63: 	// waiting for the first's call to f to complete.
64: 	// This is why the slow path falls back to a mutex, and why
65: 	// the o.done.Store must be delayed until after f returns.
66: 
67: 	if !o.done.Load() {
68: 		// Outlined slow-path to allow inlining of the fast-path.
69: 		o.doSlow(f)
70: 	}
71: }
72: 
73: func (o *Once) doSlow(f func()) {
74: 	o.m.Lock()
75: 	defer o.m.Unlock()
76: 	if !o.done.Load() {
77: 		defer o.done.Store(true)
78: 		f()
79: 	}
80: }
REFERENCE TEST SOURCE:
package reference

import (
 "bytes"
 "errors"
 "io"
 "sync"
 "testing"
 "time"
)

func TestOncePanicDone(t *testing.T) {
 var o sync.Once
 marker := errors.New("boom")
 func() { defer func() { if recover() != marker { t.Error("expected panic") } }(); o.Do(func() { panic(marker) }) }()
 ran := false
 o.Do(func() { ran = true })
 if ran { t.Fatal("function ran after panic") }
}
func TestOnceConcurrentWait(t *testing.T) {
 var o sync.Once
 entered, release := make(chan struct{}), make(chan struct{})
 finished := make(chan struct{})
 go func() { o.Do(func() { close(entered); <-release }) }()
 <-entered
 go func() { o.Do(func() { t.Error("second function ran") }); close(finished) }()
 select { case <-finished: t.Fatal("returned before first function completed"); case <-time.After(50*time.Millisecond): }
 close(release)
 select { case <-finished: case <-time.After(time.Second): t.Fatal("waiter did not finish") }
}
func TestBufferEmptyReads(t *testing.T) {
 var b bytes.Buffer
 if n,e:=b.Read(nil); n!=0 || e!=nil { t.Fatal(n,e) }
 if n,e:=b.Read(make([]byte,1)); n!=0 || e!=io.EOF { t.Fatal(n,e) }
}
func TestBufferZeroReadInvalidatesUnread(t *testing.T) {
 b:=bytes.NewBufferString("ab")
 if x,e:=b.ReadByte(); x!='a' || e!=nil {t.Fatal(x,e)}
 if n,e:=b.Read(nil); n!=0 || e!=nil {t.Fatal(n,e)}
 if e:=b.UnreadByte(); e==nil {t.Fatal("expected error after zero read")}
 if x,e:=b.ReadByte(); x!='b' || e!=nil {t.Fatal(x,e)}
 if e:=b.UnreadByte();e!=nil {t.Fatal(e)}
 if x,e:=b.ReadByte(); x!='b' || e!=nil {t.Fatal(x,e)}
}
