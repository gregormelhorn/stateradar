Inspect the source for significant behavior, edge cases, event ordering and contract limitations. Return JSON with exactly one key findings, an array of at most six entries. Each entry has a unique id, text describing the exact starting conditions, ordered events and observable result, a citation object {line: integer, fragment: exact substring of that line}, and question: either an OPEN: question where intent or source wording is unclear, or an empty string. Include supported ordinary controls as appropriate. Do not assume a surprising behavior is intended. Return JSON only.

REVIEW PARAGRAPH:
Examine ordinary success and failure as well as repeated operations, deferred work, cancellation and both event orderings. Trace state, object identity and effects across each lifecycle boundary. Compare contract language with behavior, including its exclusions and the possibility that a valid statement applies only to a narrower situation. Retain correct controls. Cite evidence and leave unanswered intent or contradictory requirements as OPEN questions.

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