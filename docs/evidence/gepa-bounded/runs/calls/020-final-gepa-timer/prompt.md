Analyze the supplied component and claim inventory using only the supplied source.
Do not use tools, external knowledge as a contract, repository history, or web.
Assess whether each exact claim follows, is contradicted, or remains unspecified
by the source/contract. Preserve ordinary controls and explicit scope. Application
policy absent from the component contract must remain an OPEN question.
Draft/Jev advice is fallible; verify every proposed verdict against the source.
Return only JSON: {"findings":[{"id":"case ID","verdict":"supported|contradicted|unspecified",
"line":1,"fragment":"exact nonempty source line fragment","reason":"brief source-grounded explanation",
"question":"OPEN: ... for unspecified; otherwise empty string"}],"corrections":[]}.
Include every claim exactly once. Cite the supplied source's original line numbers.
When reviewing, preserve the immutable baseline as evidence: return the same full
inventory and list every changed verdict in corrections as {"id":...,"before":...,"after":...}.
Do not silently change or drop a prior question. A review may correct a wrong
verdict with source evidence; mechanical retention must not preserve false claims.

INVENTORY:
[{"id": "timer-01", "claim": "A timer returned by AfterFunc has a nil C field."}, {"id": "timer-02", "claim": "Stop on an already running AfterFunc callback waits for that callback to finish."}, {"id": "timer-03", "claim": "Reset after the AfterFunc callback has started returns false and schedules another execution."}, {"id": "timer-04", "claim": "A callback scheduled by Reset cannot overlap the previous callback."}, {"id": "timer-05", "claim": "Stop before a far-future AfterFunc expires can return true and prevent that scheduled execution."}, {"id": "timer-06", "claim": "Reassigning only the caller function variable after AfterFunc registration changes which function that timer will invoke."}, {"id": "timer-07", "claim": "The application must retry a timed-out operation exactly three times."}]
SOURCE:
1: // Copyright 2009 The Go Authors. All rights reserved.
2: // Use of this source code is governed by a BSD-style
3: // license that can be found in the LICENSE file.
4: 
5: package time
6: 
7: import (
8: 	"unsafe"
9: )
10: 
11: // Sleep pauses the current goroutine for at least the duration d.
12: // A negative or zero duration causes Sleep to return immediately.
13: func Sleep(d Duration)
14: 
15: // syncTimer returns c as an unsafe.Pointer, for passing to newTimer.
16: func syncTimer(c chan Time) unsafe.Pointer {
17: 	return *(*unsafe.Pointer)(unsafe.Pointer(&c))
18: }
19: 
20: // when is a helper function for setting the 'when' field of a runtimeTimer.
21: // It returns what the time will be, in nanoseconds, Duration d in the future.
22: // If d is negative, it is ignored. If the returned value would be less than
23: // zero because of an overflow, MaxInt64 is returned.
24: func when(d Duration) int64 {
25: 	if d <= 0 {
26: 		return runtimeNano()
27: 	}
28: 	t := runtimeNano() + int64(d)
29: 	if t < 0 {
30: 		// N.B. runtimeNano() and d are always positive, so addition
31: 		// (including overflow) will never result in t == 0.
32: 		t = 1<<63 - 1 // math.MaxInt64
33: 	}
34: 	return t
35: }
36: 
37: // These functions are pushed to package time from package runtime.
38: 
39: // The arg cp is a chan Time, but the declaration in runtime uses a pointer,
40: // so we use a pointer here too. This keeps some tools that aggressively
41: // compare linknamed symbol definitions happier.
42: //
43: //go:linkname newTimer
44: func newTimer(when, period int64, f func(any, uintptr, int64), arg any, cp unsafe.Pointer) *Timer
45: 
46: //go:linkname stopTimer
47: func stopTimer(*Timer) bool
48: 
49: //go:linkname resetTimer
50: func resetTimer(t *Timer, when, period int64) bool
51: 
52: // Note: The runtime knows the layout of struct Timer, since newTimer allocates it.
53: // The runtime also knows that Ticker and Timer have the same layout.
54: // There are extra fields after the channel, reserved for the runtime
55: // and inaccessible to users.
56: 
57: // The Timer type represents a single event.
58: // When the Timer expires, the current time will be sent on C,
59: // unless the Timer was created by [AfterFunc].
60: // A Timer must be created with [NewTimer] or AfterFunc.
61: type Timer struct {
62: 	C         <-chan Time
63: 	initTimer bool
64: }
65: 
66: // Stop prevents the [Timer] from firing.
67: // It returns true if the call stops the timer, false if the timer has already
68: // expired or been stopped.
69: //
70: // For a func-based timer created with [AfterFunc](d, f),
71: // if t.Stop returns false, then the timer has already expired
72: // and the function f has been started in its own goroutine;
73: // Stop does not wait for f to complete before returning.
74: // If the caller needs to know whether f is completed,
75: // it must coordinate with f explicitly.
76: //
77: // For a chan-based timer created with NewTimer(d), as of Go 1.23,
78: // any receive from t.C after Stop has returned is guaranteed to block
79: // rather than receive a stale time value from before the Stop;
80: // if the program has not received from t.C already and the timer is
81: // running, Stop is guaranteed to return true.
82: // Before Go 1.23, the only safe way to use Stop was insert an extra
83: // <-t.C if Stop returned false to drain a potential stale value.
84: // See the [NewTimer] documentation for more details.
85: func (t *Timer) Stop() bool {
86: 	if !t.initTimer {
87: 		panic("time: Stop called on uninitialized Timer")
88: 	}
89: 	return stopTimer(t)
90: }
91: 
92: // NewTimer creates a new Timer that will send
93: // the current time on its channel after at least duration d.
94: //
95: // Before Go 1.23, the garbage collector did not recover
96: // timers that had not yet expired or been stopped, so code often
97: // immediately deferred t.Stop after calling NewTimer, to make
98: // the timer recoverable when it was no longer needed.
99: // As of Go 1.23, the garbage collector can recover unreferenced
100: // timers, even if they haven't expired or been stopped.
101: // The Stop method is no longer necessary to help the garbage collector.
102: // (Code may of course still want to call Stop to stop the timer for other reasons.)
103: //
104: // Before Go 1.23, the channel associated with a Timer was
105: // asynchronous (buffered, capacity 1), which meant that
106: // stale time values could be received even after [Timer.Stop]
107: // or [Timer.Reset] returned.
108: // As of Go 1.23, the channel is synchronous (unbuffered, capacity 0),
109: // eliminating the possibility of those stale values.
110: func NewTimer(d Duration) *Timer {
111: 	c := make(chan Time, 1)
112: 	t := newTimer(when(d), 0, sendTime, c, syncTimer(c))
113: 	t.C = c
114: 	return t
115: }
116: 
117: // Reset changes the timer to expire after duration d.
118: // It returns true if the timer had been active, false if the timer had
119: // expired or been stopped.
120: //
121: // For a func-based timer created with [AfterFunc](d, f), Reset either reschedules
122: // when f will run, in which case Reset returns true, or schedules f
123: // to run again, in which case it returns false.
124: // When Reset returns false, Reset neither waits for the prior f to
125: // complete before returning nor does it guarantee that the subsequent
126: // goroutine running f does not run concurrently with the prior
127: // one. If the caller needs to know whether the prior execution of
128: // f is completed, it must coordinate with f explicitly.
129: //
130: // For a chan-based timer created with NewTimer, as of Go 1.23,
131: // any receive from t.C after Reset has returned is guaranteed not
132: // to receive a time value corresponding to the previous timer settings;
133: // if the program has not received from t.C already and the timer is
134: // running, Reset is guaranteed to return true.
135: // Before Go 1.23, the only safe way to use Reset was to call [Timer.Stop]
136: // and explicitly drain the timer first.
137: // See the [NewTimer] documentation for more details.
138: func (t *Timer) Reset(d Duration) bool {
139: 	if !t.initTimer {
140: 		panic("time: Reset called on uninitialized Timer")
141: 	}
142: 	w := when(d)
143: 	return resetTimer(t, w, 0)
144: }
145: 
146: // sendTime does a non-blocking send of the current time on c.
147: func sendTime(c any, seq uintptr, delta int64) {
148: 	// delta is how long ago the channel send was supposed to happen.
149: 	// The current time can be arbitrarily far into the future, because the runtime
150: 	// can delay a sendTime call until a goroutine tries to receive from
151: 	// the channel. Subtract delta to go back to the old time that we
152: 	// used to send.
153: 	select {
154: 	case c.(chan Time) <- Now().Add(Duration(-delta)):
155: 	default:
156: 	}
157: }
158: 
159: // After waits for the duration to elapse and then sends the current time
160: // on the returned channel.
161: // It is equivalent to [NewTimer](d).C.
162: //
163: // Before Go 1.23, this documentation warned that the underlying
164: // [Timer] would not be recovered by the garbage collector until the
165: // timer fired, and that if efficiency was a concern, code should use
166: // NewTimer instead and call [Timer.Stop] if the timer is no longer needed.
167: // As of Go 1.23, the garbage collector can recover unreferenced,
168: // unstopped timers. There is no reason to prefer NewTimer when After will do.
169: func After(d Duration) <-chan Time {
170: 	return NewTimer(d).C
171: }
172: 
173: // AfterFunc waits for the duration to elapse and then calls f
174: // in its own goroutine. It returns a [Timer] that can
175: // be used to cancel the call using its Stop method.
176: // The returned Timer's C field is not used and will be nil.
177: func AfterFunc(d Duration, f func()) *Timer {
178: 	return newTimer(when(d), 0, goFunc, f, nil)
179: }
180: 
181: func goFunc(arg any, seq uintptr, delta int64) {
182: 	go arg.(func())()
183: }
IMMUTABLE BASELINE:
{"findings": [{"id": "timer-01", "verdict": "supported", "line": 176, "fragment": "The returned Timer's C field is not used and will be nil.", "reason": "AfterFunc explicitly documents that the returned timer has a nil C field.", "question": ""}, {"id": "timer-02", "verdict": "contradicted", "line": 73, "fragment": "Stop does not wait for f to complete before returning.", "reason": "Stop returns without waiting for the running AfterFunc callback to finish.", "question": ""}, {"id": "timer-03", "verdict": "supported", "line": 123, "fragment": "to run again, in which case it returns false.", "reason": "Once the scheduled callback has started, that timer setting has expired. Reset schedules another execution and returns false.", "question": ""}, {"id": "timer-04", "verdict": "contradicted", "line": 126, "fragment": "goroutine running f does not run concurrently with the prior", "reason": "When Reset returns false, its contract explicitly allows for overlap by withholding any guarantee against concurrent execution.", "question": ""}, {"id": "timer-05", "verdict": "supported", "line": 67, "fragment": "It returns true if the call stops the timer", "reason": "AfterFunc documents Stop as a way to cancel the pending call. A successful Stop before expiry returns true and prevents that scheduled execution.", "question": ""}, {"id": "timer-06", "verdict": "contradicted", "line": 178, "fragment": "return newTimer(when(d), 0, goFunc, f, nil)", "reason": "AfterFunc passes the function value at registration, and goFunc invokes that stored argument. Reassigning the caller's variable leaves the stored value unchanged.", "question": ""}, {"id": "timer-07", "verdict": "unspecified", "line": 173, "fragment": "AfterFunc waits for the duration to elapse and then calls f", "reason": "The component specifies timer and callback behavior and leaves application retry policy unspecified.", "question": "OPEN: What retry count, if any, does the application require for a timed-out operation?"}], "corrections": []}
REVIEW INSTRUCTIONS:
Keep ordinary success, failure, cancellation, and repeated-call controls, including actions created after cancellation. Trace each distinct creation through use and cleanup. Cite where references are captured or resolved later, state the starting objects and event order, and attribute each check and effect to the object it reaches. Distinguish return values, their causes, and when deferred work starts or finishes. Where permitted, test unchanged identity, copying, replacement, wrapper or key mutation, and caller-local rebinding separately. Verify identity with evidence beyond matching generation values and account for stable captures and identity guards. Cite documented exclusions and mark unanswered policy questions OPEN.