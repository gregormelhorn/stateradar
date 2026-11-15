Inspect the source for significant behavior, edge cases, event ordering and contract limitations. Return JSON with exactly one key findings, an array of at most six entries. Each entry has a unique id, text describing the exact starting conditions, ordered events and observable result, a citation object {line: integer, fragment: exact substring of that line}, and question: either an OPEN: question where intent or source wording is unclear, or an empty string. Include supported ordinary controls as appropriate. Do not assume a surprising behavior is intended. Return JSON only.

REVIEW PARAGRAPH:
Use the reviewed source and any pinned runtime evidence to trace ordinary success and failure, repetition, cancellation, abandonment, deferred work, and reuse. State the initial conditions and order the steps that determine the outcome. Compare both event orders and test intervening operations before treating an earlier event as decisive. Follow each completion from admission through reporting, state refresh, and effect. Check whether an obsolete report can be discarded even when cleanup or error propagation continues. Distinguish rebinding a caller's reference from replacing the value through the captured reference, and use an unchanged reference as a control. Check whether registration actually succeeds after a state observation, and keep notification, suspension, lock reacquisition, and return distinct. Compare notifications before and after registration, and distinguish when a lock is required to change the condition or begin waiting from when it is optional for notification. Preserve controls for copying before and after first use, cleanup after normal and abrupt exit, and valid reuse after earlier waiters return. Qualify exceptional behavior by the documented exclusions, compatibility mode, and whether a prior association is still present. Separate deadline calculation from dispatch and delivery. Compare repeated cancellation, expiry, and reactivation in order, checking the current state and whether earlier work has started, finished, or can overlap later work. For queued work, trace availability checks, enqueue, handoff, and shutdown through later callers and subsequent returns. Check who receives an available resource, what eventually releases the older waiter, and which validation runs on each path. Distinguish invoking cleanup from establishing its effect, and preserving error text from preserving error identity. Cite the branches, tests, and contract language that support each claim, and qualify conclusions by source coverage, version, configuration, and supported input range. Leave intent OPEN where the evidence does not settle transition timing, duplicate or abandoned completion, counter refresh and numeric limits, ownership or copying, exceptional exits, notification analogies, delivery guarantees, queue ordering, validation, or shutdown obligations. Where contract statements appear inconsistent, identify the event order and scope that expose the conflict and leave the intended wording OPEN.
SOURCE:
1: // Copyright 2011 The Go Authors. All rights reserved.
2: // Use of this source code is governed by a BSD-style
3: // license that can be found in the LICENSE file.
4: 
5: package sync
6: 
7: import (
8: 	"sync/atomic"
9: 	"unsafe"
10: )
11: 
12: // Cond implements a condition variable, a rendezvous point
13: // for goroutines waiting for or announcing the occurrence
14: // of an event.
15: //
16: // Each Cond has an associated Locker L (often a [*Mutex] or [*RWMutex]),
17: // which must be held when changing the condition and
18: // when calling the [Cond.Wait] method.
19: //
20: // A Cond must not be copied after first use.
21: //
22: // In the terminology of [the Go memory model], Cond arranges that
23: // a call to [Cond.Broadcast] or [Cond.Signal] “synchronizes before” any Wait call
24: // that it unblocks.
25: //
26: // For many simple use cases, users will be better off using channels than a
27: // Cond (Broadcast corresponds to closing a channel, and Signal corresponds to
28: // sending on a channel).
29: //
30: // For more on replacements for [sync.Cond], see [Roberto Clapis's series on
31: // advanced concurrency patterns], as well as [Bryan Mills's talk on concurrency
32: // patterns].
33: //
34: // [the Go memory model]: https://go.dev/ref/mem
35: // [Roberto Clapis's series on advanced concurrency patterns]: https://blogtitle.github.io/categories/concurrency/
36: // [Bryan Mills's talk on concurrency patterns]: https://drive.google.com/file/d/1nPdvhB0PutEJzdCq5ms6UI58dp50fcAN/view
37: type Cond struct {
38: 	noCopy noCopy
39: 
40: 	// L is held while observing or changing the condition
41: 	L Locker
42: 
43: 	notify  notifyList
44: 	checker copyChecker
45: }
46: 
47: // NewCond returns a new Cond with Locker l.
48: func NewCond(l Locker) *Cond {
49: 	return &Cond{L: l}
50: }
51: 
52: // Wait atomically unlocks c.L and suspends execution
53: // of the calling goroutine. After later resuming execution,
54: // Wait locks c.L before returning. Unlike in other systems,
55: // Wait cannot return unless awoken by [Cond.Broadcast] or [Cond.Signal].
56: //
57: // Because c.L is not locked while Wait is waiting, the caller
58: // typically cannot assume that the condition is true when
59: // Wait returns. Instead, the caller should Wait in a loop:
60: //
61: //	c.L.Lock()
62: //	for !condition() {
63: //	    c.Wait()
64: //	}
65: //	... make use of condition ...
66: //	c.L.Unlock()
67: func (c *Cond) Wait() {
68: 	c.checker.check()
69: 	t := runtime_notifyListAdd(&c.notify)
70: 	c.L.Unlock()
71: 	runtime_notifyListWait(&c.notify, t)
72: 	c.L.Lock()
73: }
74: 
75: // Signal wakes one goroutine waiting on c, if there is any.
76: //
77: // It is allowed but not required for the caller to hold c.L
78: // during the call.
79: //
80: // Signal() does not affect goroutine scheduling priority; if other goroutines
81: // are attempting to lock c.L, they may be awoken before a "waiting" goroutine.
82: func (c *Cond) Signal() {
83: 	c.checker.check()
84: 	runtime_notifyListNotifyOne(&c.notify)
85: }
86: 
87: // Broadcast wakes all goroutines waiting on c.
88: //
89: // It is allowed but not required for the caller to hold c.L during the call.
90: // The time it takes to run Broadcast is proportional to the number of waiting goroutines;
91: // be aware that holding the lock across a call to Broadcast
92: // will extend the amount of time that the lock is held.
93: func (c *Cond) Broadcast() {
94: 	c.checker.check()
95: 	runtime_notifyListNotifyAll(&c.notify)
96: }
97: 
98: // copyChecker holds back pointer to itself to detect object copying.
99: type copyChecker uintptr
100: 
101: func (c *copyChecker) check() {
102: 	// Check if c has been copied in three steps:
103: 	// 1. The first comparison is the fast-path. If c has been initialized and not copied, this will return immediately. Otherwise, c is either not initialized, or has been copied.
104: 	// 2. Ensure c is initialized. If the CAS succeeds, we're done. If it fails, c was either initialized concurrently and we simply lost the race, or c has been copied.
105: 	// 3. Do step 1 again. Now that c is definitely initialized, if this fails, c was copied.
106: 	if uintptr(*c) != uintptr(unsafe.Pointer(c)) &&
107: 		!atomic.CompareAndSwapUintptr((*uintptr)(c), 0, uintptr(unsafe.Pointer(c))) &&
108: 		uintptr(*c) != uintptr(unsafe.Pointer(c)) {
109: 		panic("sync.Cond is copied")
110: 	}
111: }
112: 
113: // noCopy may be added to structs which must not be copied
114: // after the first use.
115: //
116: // See https://golang.org/issues/8005#issuecomment-190753527
117: // for details.
118: //
119: // Note that it must not be embedded, due to the Lock and Unlock methods.
120: type noCopy struct{}
121: 
122: // Lock is a no-op used by -copylocks checker from `go vet`.
123: func (*noCopy) Lock()   {}
124: func (*noCopy) Unlock() {}