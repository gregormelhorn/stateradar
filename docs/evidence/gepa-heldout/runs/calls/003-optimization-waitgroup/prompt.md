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
8: 	"internal/race"
9: 	"internal/synctest"
10: 	"sync/atomic"
11: 	"unsafe"
12: )
13: 
14: // A WaitGroup is a counting semaphore typically used to wait
15: // for a group of goroutines or tasks to finish.
16: //
17: // Typically, a main goroutine will start tasks, each in a new
18: // goroutine, by calling [WaitGroup.Go] and then wait for all tasks to
19: // complete by calling [WaitGroup.Wait]. For example:
20: //
21: //	var wg sync.WaitGroup
22: //	wg.Go(task1)
23: //	wg.Go(task2)
24: //	wg.Wait()
25: //
26: // A WaitGroup may also be used for tracking tasks without using Go to
27: // start new goroutines by using [WaitGroup.Add] and [WaitGroup.Done].
28: //
29: // The previous example can be rewritten using explicitly created
30: // goroutines along with Add and Done:
31: //
32: //	var wg sync.WaitGroup
33: //	wg.Add(1)
34: //	go func() {
35: //		defer wg.Done()
36: //		task1()
37: //	}()
38: //	wg.Add(1)
39: //	go func() {
40: //		defer wg.Done()
41: //		task2()
42: //	}()
43: //	wg.Wait()
44: //
45: // This pattern is common in code that predates [WaitGroup.Go].
46: //
47: // A WaitGroup must not be copied after first use.
48: type WaitGroup struct {
49: 	noCopy noCopy
50: 
51: 	// Bits (high to low):
52: 	//   bits[0:32]  counter
53: 	//   bits[32]    flag: synctest bubble membership
54: 	//   bits[33:64] wait count
55: 	state atomic.Uint64
56: 	sema  uint32
57: }
58: 
59: // waitGroupBubbleFlag indicates that a WaitGroup is associated with a synctest bubble.
60: const waitGroupBubbleFlag = 0x8000_0000
61: 
62: // Add adds delta, which may be negative, to the [WaitGroup] task counter.
63: // If the counter becomes zero, all goroutines blocked on [WaitGroup.Wait] are released.
64: // If the counter goes negative, Add panics.
65: //
66: // Callers should prefer [WaitGroup.Go].
67: //
68: // Note that calls with a positive delta that occur when the counter is zero
69: // must happen before a Wait. Calls with a negative delta, or calls with a
70: // positive delta that start when the counter is greater than zero, may happen
71: // at any time.
72: // Typically this means the calls to Add should execute before the statement
73: // creating the goroutine or other event to be waited for.
74: // If a WaitGroup is reused to wait for several independent sets of events,
75: // new Add calls must happen after all previous Wait calls have returned.
76: // See the WaitGroup example.
77: func (wg *WaitGroup) Add(delta int) {
78: 	if race.Enabled {
79: 		if delta < 0 {
80: 			// Synchronize decrements with Wait.
81: 			race.ReleaseMerge(unsafe.Pointer(wg))
82: 		}
83: 		race.Disable()
84: 		defer race.Enable()
85: 	}
86: 	bubbled := false
87: 	if synctest.IsInBubble() {
88: 		// If Add is called from within a bubble, then all Add calls must be made
89: 		// from the same bubble.
90: 		switch synctest.Associate(wg) {
91: 		case synctest.Unbubbled:
92: 		case synctest.OtherBubble:
93: 			// wg is already associated with a different bubble.
94: 			fatal("sync: WaitGroup.Add called from multiple synctest bubbles")
95: 		case synctest.CurrentBubble:
96: 			bubbled = true
97: 			state := wg.state.Or(waitGroupBubbleFlag)
98: 			if state != 0 && state&waitGroupBubbleFlag == 0 {
99: 				// Add has been called from outside this bubble.
100: 				fatal("sync: WaitGroup.Add called from inside and outside synctest bubble")
101: 			}
102: 		}
103: 	}
104: 	state := wg.state.Add(uint64(delta) << 32)
105: 	if state&waitGroupBubbleFlag != 0 && !bubbled {
106: 		// Add has been called from within a synctest bubble (and we aren't in one).
107: 		fatal("sync: WaitGroup.Add called from inside and outside synctest bubble")
108: 	}
109: 	v := int32(state >> 32)
110: 	w := uint32(state & 0x7fffffff)
111: 	if race.Enabled && delta > 0 && v == int32(delta) {
112: 		// The first increment must be synchronized with Wait.
113: 		// Need to model this as a read, because there can be
114: 		// several concurrent wg.counter transitions from 0.
115: 		race.Read(unsafe.Pointer(&wg.sema))
116: 	}
117: 	if v < 0 {
118: 		panic("sync: negative WaitGroup counter")
119: 	}
120: 	if w != 0 && delta > 0 && v == int32(delta) {
121: 		panic("sync: WaitGroup misuse: Add called concurrently with Wait")
122: 	}
123: 	if v > 0 || w == 0 {
124: 		return
125: 	}
126: 	// This goroutine has set counter to 0 when waiters > 0.
127: 	// Now there can't be concurrent mutations of state:
128: 	// - Adds must not happen concurrently with Wait,
129: 	// - Wait does not increment waiters if it sees counter == 0.
130: 	// Still do a cheap sanity check to detect WaitGroup misuse.
131: 	if wg.state.Load() != state {
132: 		panic("sync: WaitGroup misuse: Add called concurrently with Wait")
133: 	}
134: 	// Reset waiters count to 0.
135: 	wg.state.Store(0)
136: 	if bubbled {
137: 		// Adds must not happen concurrently with wait when counter is 0,
138: 		// so we can safely disassociate wg from its current bubble.
139: 		synctest.Disassociate(wg)
140: 	}
141: 	for ; w != 0; w-- {
142: 		runtime_Semrelease(&wg.sema, false, 0)
143: 	}
144: }
145: 
146: // Done decrements the [WaitGroup] task counter by one.
147: // It is equivalent to Add(-1).
148: //
149: // Callers should prefer [WaitGroup.Go].
150: //
151: // In the terminology of [the Go memory model], a call to Done
152: // "synchronizes before" the return of any Wait call that it unblocks.
153: //
154: // [the Go memory model]: https://go.dev/ref/mem
155: func (wg *WaitGroup) Done() {
156: 	wg.Add(-1)
157: }
158: 
159: // Wait blocks until the [WaitGroup] task counter is zero.
160: func (wg *WaitGroup) Wait() {
161: 	if race.Enabled {
162: 		race.Disable()
163: 	}
164: 	for {
165: 		state := wg.state.Load()
166: 		v := int32(state >> 32)
167: 		w := uint32(state & 0x7fffffff)
168: 		if v == 0 {
169: 			// Counter is 0, no need to wait.
170: 			if race.Enabled {
171: 				race.Enable()
172: 				race.Acquire(unsafe.Pointer(wg))
173: 			}
174: 			if w == 0 && state&waitGroupBubbleFlag != 0 && synctest.IsAssociated(wg) {
175: 				// Adds must not happen concurrently with wait when counter is 0,
176: 				// so we can disassociate wg from its current bubble.
177: 				if wg.state.CompareAndSwap(state, 0) {
178: 					synctest.Disassociate(wg)
179: 				}
180: 			}
181: 			return
182: 		}
183: 		// Increment waiters count.
184: 		if wg.state.CompareAndSwap(state, state+1) {
185: 			if race.Enabled && w == 0 {
186: 				// Wait must be synchronized with the first Add.
187: 				// Need to model this is as a write to race with the read in Add.
188: 				// As a consequence, can do the write only for the first waiter,
189: 				// otherwise concurrent Waits will race with each other.
190: 				race.Write(unsafe.Pointer(&wg.sema))
191: 			}
192: 			synctestDurable := false
193: 			if state&waitGroupBubbleFlag != 0 && synctest.IsInBubble() {
194: 				if race.Enabled {
195: 					race.Enable()
196: 				}
197: 				if synctest.IsAssociated(wg) {
198: 					// Add was called within the current bubble,
199: 					// so this Wait is durably blocking.
200: 					synctestDurable = true
201: 				}
202: 				if race.Enabled {
203: 					race.Disable()
204: 				}
205: 			}
206: 			runtime_SemacquireWaitGroup(&wg.sema, synctestDurable)
207: 			isReset := wg.state.Load() != 0
208: 			if race.Enabled {
209: 				race.Enable()
210: 				race.Acquire(unsafe.Pointer(wg))
211: 			}
212: 			if isReset {
213: 				panic("sync: WaitGroup is reused before previous Wait has returned")
214: 			}
215: 			return
216: 		}
217: 	}
218: }
219: 
220: // Go calls f in a new goroutine and adds that task to the [WaitGroup].
221: // When f returns, the task is removed from the WaitGroup.
222: //
223: // The function f must not panic.
224: //
225: // If the WaitGroup is empty, Go must happen before a [WaitGroup.Wait].
226: // Typically, this simply means Go is called to start tasks before Wait is called.
227: // If the WaitGroup is not empty, Go may happen at any time.
228: // This means a goroutine started by Go may itself call Go.
229: // If a WaitGroup is reused to wait for several independent sets of tasks,
230: // new Go calls must happen after all previous Wait calls have returned.
231: //
232: // In the terminology of [the Go memory model], the return from f
233: // "synchronizes before" the return of any Wait call that it unblocks.
234: //
235: // [the Go memory model]: https://go.dev/ref/mem
236: func (wg *WaitGroup) Go(f func()) {
237: 	wg.Add(1)
238: 	go func() {
239: 		defer func() {
240: 			if x := recover(); x != nil {
241: 				// f panicked, which will be fatal because
242: 				// this is a new goroutine.
243: 				//
244: 				// Calling Done will unblock Wait in the main goroutine,
245: 				// allowing it to race with the fatal panic and
246: 				// possibly even exit the process (os.Exit(0))
247: 				// before the panic completes.
248: 				//
249: 				// This is almost certainly undesirable,
250: 				// so instead avoid calling Done and simply panic.
251: 				panic(x)
252: 			}
253: 
254: 			// f completed normally, or abruptly using goexit.
255: 			// Either way, decrement the semaphore.
256: 			wg.Done()
257: 		}()
258: 		f()
259: 	}()
260: }