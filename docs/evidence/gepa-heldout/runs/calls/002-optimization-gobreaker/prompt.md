Inspect the source for significant behavior, edge cases, event ordering and contract limitations. Return JSON with exactly one key findings, an array of at most six entries. Each entry has a unique id, text describing the exact starting conditions, ordered events and observable result, a citation object {line: integer, fragment: exact substring of that line}, and question: either an OPEN: question where intent or source wording is unclear, or an empty string. Include supported ordinary controls as appropriate. Do not assume a surprising behavior is intended. Return JSON only.

REVIEW PARAGRAPH:
Use the reviewed source and any pinned runtime evidence to trace ordinary success and failure, repetition, cancellation, abandonment, deferred work, and reuse. State the initial conditions and order the steps that determine the outcome. Compare both event orders and test intervening operations before treating an earlier event as decisive. Follow each completion from admission through reporting, state refresh, and effect. Check whether an obsolete report can be discarded even when cleanup or error propagation continues. Distinguish rebinding a caller's reference from replacing the value through the captured reference, and use an unchanged reference as a control. Check whether registration actually succeeds after a state observation, and keep notification, suspension, lock reacquisition, and return distinct. Compare notifications before and after registration, and distinguish when a lock is required to change the condition or begin waiting from when it is optional for notification. Preserve controls for copying before and after first use, cleanup after normal and abrupt exit, and valid reuse after earlier waiters return. Qualify exceptional behavior by the documented exclusions, compatibility mode, and whether a prior association is still present. Separate deadline calculation from dispatch and delivery. Compare repeated cancellation, expiry, and reactivation in order, checking the current state and whether earlier work has started, finished, or can overlap later work. For queued work, trace availability checks, enqueue, handoff, and shutdown through later callers and subsequent returns. Check who receives an available resource, what eventually releases the older waiter, and which validation runs on each path. Distinguish invoking cleanup from establishing its effect, and preserving error text from preserving error identity. Cite the branches, tests, and contract language that support each claim, and qualify conclusions by source coverage, version, configuration, and supported input range. Leave intent OPEN where the evidence does not settle transition timing, duplicate or abandoned completion, counter refresh and numeric limits, ownership or copying, exceptional exits, notification analogies, delivery guarantees, queue ordering, validation, or shutdown obligations. Where contract statements appear inconsistent, identify the event order and scope that expose the conflict and leave the intended wording OPEN.
SOURCE:
1: // Package gobreaker implements the Circuit Breaker pattern.
2: // See https://msdn.microsoft.com/en-us/library/dn589784.aspx.
3: package gobreaker
4: 
5: import (
6: 	"errors"
7: 	"fmt"
8: 	"sync"
9: 	"time"
10: )
11: 
12: // State is a type that represents a state of CircuitBreaker.
13: type State int
14: 
15: // These constants are states of CircuitBreaker.
16: const (
17: 	StateClosed State = iota
18: 	StateHalfOpen
19: 	StateOpen
20: )
21: 
22: var (
23: 	// ErrTooManyRequests is returned when the CB state is half open and the requests count is over the cb maxRequests
24: 	ErrTooManyRequests = errors.New("too many requests")
25: 	// ErrOpenState is returned when the CB state is open
26: 	ErrOpenState = errors.New("circuit breaker is open")
27: )
28: 
29: // String implements stringer interface.
30: func (s State) String() string {
31: 	switch s {
32: 	case StateClosed:
33: 		return "closed"
34: 	case StateHalfOpen:
35: 		return "half-open"
36: 	case StateOpen:
37: 		return "open"
38: 	default:
39: 		return fmt.Sprintf("unknown state: %d", s)
40: 	}
41: }
42: 
43: // Counts holds the numbers of requests and their successes/failures.
44: // CircuitBreaker clears the internal Counts either
45: // on the change of the state or at the closed-state intervals.
46: // Counts ignores the results of the requests sent before clearing.
47: type Counts struct {
48: 	Requests             uint32
49: 	TotalSuccesses       uint32
50: 	TotalFailures        uint32
51: 	ConsecutiveSuccesses uint32
52: 	ConsecutiveFailures  uint32
53: }
54: 
55: func (c *Counts) onRequest() {
56: 	c.Requests++
57: }
58: 
59: func (c *Counts) onSuccess() {
60: 	c.TotalSuccesses++
61: 	c.ConsecutiveSuccesses++
62: 	c.ConsecutiveFailures = 0
63: }
64: 
65: func (c *Counts) onFailure() {
66: 	c.TotalFailures++
67: 	c.ConsecutiveFailures++
68: 	c.ConsecutiveSuccesses = 0
69: }
70: 
71: func (c *Counts) clear() {
72: 	c.Requests = 0
73: 	c.TotalSuccesses = 0
74: 	c.TotalFailures = 0
75: 	c.ConsecutiveSuccesses = 0
76: 	c.ConsecutiveFailures = 0
77: }
78: 
79: // Settings configures CircuitBreaker:
80: //
81: // Name is the name of the CircuitBreaker.
82: //
83: // MaxRequests is the maximum number of requests allowed to pass through
84: // when the CircuitBreaker is half-open.
85: // If MaxRequests is 0, the CircuitBreaker allows only 1 request.
86: //
87: // Interval is the cyclic period of the closed state
88: // for the CircuitBreaker to clear the internal Counts.
89: // If Interval is less than or equal to 0, the CircuitBreaker doesn't clear internal Counts during the closed state.
90: //
91: // Timeout is the period of the open state,
92: // after which the state of the CircuitBreaker becomes half-open.
93: // If Timeout is less than or equal to 0, the timeout value of the CircuitBreaker is set to 60 seconds.
94: //
95: // ReadyToTrip is called with a copy of Counts whenever a request fails in the closed state.
96: // If ReadyToTrip returns true, the CircuitBreaker will be placed into the open state.
97: // If ReadyToTrip is nil, default ReadyToTrip is used.
98: // Default ReadyToTrip returns true when the number of consecutive failures is more than 5.
99: //
100: // OnStateChange is called whenever the state of the CircuitBreaker changes.
101: //
102: // IsSuccessful is called with the error returned from a request.
103: // If IsSuccessful returns true, the error is counted as a success.
104: // Otherwise the error is counted as a failure.
105: // If IsSuccessful is nil, default IsSuccessful is used, which returns false for all non-nil errors.
106: type Settings struct {
107: 	Name          string
108: 	MaxRequests   uint32
109: 	Interval      time.Duration
110: 	Timeout       time.Duration
111: 	ReadyToTrip   func(counts Counts) bool
112: 	OnStateChange func(name string, from State, to State)
113: 	IsSuccessful  func(err error) bool
114: }
115: 
116: // CircuitBreaker is a state machine to prevent sending requests that are likely to fail.
117: type CircuitBreaker struct {
118: 	name          string
119: 	maxRequests   uint32
120: 	interval      time.Duration
121: 	timeout       time.Duration
122: 	readyToTrip   func(counts Counts) bool
123: 	isSuccessful  func(err error) bool
124: 	onStateChange func(name string, from State, to State)
125: 
126: 	mutex      sync.Mutex
127: 	state      State
128: 	generation uint64
129: 	counts     Counts
130: 	expiry     time.Time
131: }
132: 
133: // TwoStepCircuitBreaker is like CircuitBreaker but instead of surrounding a function
134: // with the breaker functionality, it only checks whether a request can proceed and
135: // expects the caller to report the outcome in a separate step using a callback.
136: type TwoStepCircuitBreaker struct {
137: 	cb *CircuitBreaker
138: }
139: 
140: // NewCircuitBreaker returns a new CircuitBreaker configured with the given Settings.
141: func NewCircuitBreaker(st Settings) *CircuitBreaker {
142: 	cb := new(CircuitBreaker)
143: 
144: 	cb.name = st.Name
145: 	cb.onStateChange = st.OnStateChange
146: 
147: 	if st.MaxRequests == 0 {
148: 		cb.maxRequests = 1
149: 	} else {
150: 		cb.maxRequests = st.MaxRequests
151: 	}
152: 
153: 	if st.Interval <= 0 {
154: 		cb.interval = defaultInterval
155: 	} else {
156: 		cb.interval = st.Interval
157: 	}
158: 
159: 	if st.Timeout <= 0 {
160: 		cb.timeout = defaultTimeout
161: 	} else {
162: 		cb.timeout = st.Timeout
163: 	}
164: 
165: 	if st.ReadyToTrip == nil {
166: 		cb.readyToTrip = defaultReadyToTrip
167: 	} else {
168: 		cb.readyToTrip = st.ReadyToTrip
169: 	}
170: 
171: 	if st.IsSuccessful == nil {
172: 		cb.isSuccessful = defaultIsSuccessful
173: 	} else {
174: 		cb.isSuccessful = st.IsSuccessful
175: 	}
176: 
177: 	cb.toNewGeneration(time.Now())
178: 
179: 	return cb
180: }
181: 
182: // NewTwoStepCircuitBreaker returns a new TwoStepCircuitBreaker configured with the given Settings.
183: func NewTwoStepCircuitBreaker(st Settings) *TwoStepCircuitBreaker {
184: 	return &TwoStepCircuitBreaker{
185: 		cb: NewCircuitBreaker(st),
186: 	}
187: }
188: 
189: const defaultInterval = time.Duration(0) * time.Second
190: const defaultTimeout = time.Duration(60) * time.Second
191: 
192: func defaultReadyToTrip(counts Counts) bool {
193: 	return counts.ConsecutiveFailures > 5
194: }
195: 
196: func defaultIsSuccessful(err error) bool {
197: 	return err == nil
198: }
199: 
200: // Name returns the name of the CircuitBreaker.
201: func (cb *CircuitBreaker) Name() string {
202: 	return cb.name
203: }
204: 
205: // State returns the current state of the CircuitBreaker.
206: func (cb *CircuitBreaker) State() State {
207: 	cb.mutex.Lock()
208: 	defer cb.mutex.Unlock()
209: 
210: 	now := time.Now()
211: 	state, _ := cb.currentState(now)
212: 	return state
213: }
214: 
215: // Counts returns internal counters
216: func (cb *CircuitBreaker) Counts() Counts {
217: 	cb.mutex.Lock()
218: 	defer cb.mutex.Unlock()
219: 
220: 	return cb.counts
221: }
222: 
223: // Execute runs the given request if the CircuitBreaker accepts it.
224: // Execute returns an error instantly if the CircuitBreaker rejects the request.
225: // Otherwise, Execute returns the result of the request.
226: // If a panic occurs in the request, the CircuitBreaker handles it as an error
227: // and causes the same panic again.
228: func (cb *CircuitBreaker) Execute(req func() (interface{}, error)) (interface{}, error) {
229: 	generation, err := cb.beforeRequest()
230: 	if err != nil {
231: 		return nil, err
232: 	}
233: 
234: 	defer func() {
235: 		e := recover()
236: 		if e != nil {
237: 			cb.afterRequest(generation, false)
238: 			panic(e)
239: 		}
240: 	}()
241: 
242: 	result, err := req()
243: 	cb.afterRequest(generation, cb.isSuccessful(err))
244: 	return result, err
245: }
246: 
247: // Name returns the name of the TwoStepCircuitBreaker.
248: func (tscb *TwoStepCircuitBreaker) Name() string {
249: 	return tscb.cb.Name()
250: }
251: 
252: // State returns the current state of the TwoStepCircuitBreaker.
253: func (tscb *TwoStepCircuitBreaker) State() State {
254: 	return tscb.cb.State()
255: }
256: 
257: // Counts returns internal counters
258: func (tscb *TwoStepCircuitBreaker) Counts() Counts {
259: 	return tscb.cb.Counts()
260: }
261: 
262: // Allow checks if a new request can proceed. It returns a callback that should be used to
263: // register the success or failure in a separate step. If the circuit breaker doesn't allow
264: // requests, it returns an error.
265: func (tscb *TwoStepCircuitBreaker) Allow() (done func(success bool), err error) {
266: 	generation, err := tscb.cb.beforeRequest()
267: 	if err != nil {
268: 		return nil, err
269: 	}
270: 
271: 	return func(success bool) {
272: 		tscb.cb.afterRequest(generation, success)
273: 	}, nil
274: }
275: 
276: func (cb *CircuitBreaker) beforeRequest() (uint64, error) {
277: 	cb.mutex.Lock()
278: 	defer cb.mutex.Unlock()
279: 
280: 	now := time.Now()
281: 	state, generation := cb.currentState(now)
282: 
283: 	if state == StateOpen {
284: 		return generation, ErrOpenState
285: 	} else if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {
286: 		return generation, ErrTooManyRequests
287: 	}
288: 
289: 	cb.counts.onRequest()
290: 	return generation, nil
291: }
292: 
293: func (cb *CircuitBreaker) afterRequest(before uint64, success bool) {
294: 	cb.mutex.Lock()
295: 	defer cb.mutex.Unlock()
296: 
297: 	now := time.Now()
298: 	state, generation := cb.currentState(now)
299: 	if generation != before {
300: 		return
301: 	}
302: 
303: 	if success {
304: 		cb.onSuccess(state, now)
305: 	} else {
306: 		cb.onFailure(state, now)
307: 	}
308: }
309: 
310: func (cb *CircuitBreaker) onSuccess(state State, now time.Time) {
311: 	switch state {
312: 	case StateClosed:
313: 		cb.counts.onSuccess()
314: 	case StateHalfOpen:
315: 		cb.counts.onSuccess()
316: 		if cb.counts.ConsecutiveSuccesses >= cb.maxRequests {
317: 			cb.setState(StateClosed, now)
318: 		}
319: 	}
320: }
321: 
322: func (cb *CircuitBreaker) onFailure(state State, now time.Time) {
323: 	switch state {
324: 	case StateClosed:
325: 		cb.counts.onFailure()
326: 		if cb.readyToTrip(cb.counts) {
327: 			cb.setState(StateOpen, now)
328: 		}
329: 	case StateHalfOpen:
330: 		cb.setState(StateOpen, now)
331: 	}
332: }
333: 
334: func (cb *CircuitBreaker) currentState(now time.Time) (State, uint64) {
335: 	switch cb.state {
336: 	case StateClosed:
337: 		if !cb.expiry.IsZero() && cb.expiry.Before(now) {
338: 			cb.toNewGeneration(now)
339: 		}
340: 	case StateOpen:
341: 		if cb.expiry.Before(now) {
342: 			cb.setState(StateHalfOpen, now)
343: 		}
344: 	}
345: 	return cb.state, cb.generation
346: }
347: 
348: func (cb *CircuitBreaker) setState(state State, now time.Time) {
349: 	if cb.state == state {
350: 		return
351: 	}
352: 
353: 	prev := cb.state
354: 	cb.state = state
355: 
356: 	cb.toNewGeneration(now)
357: 
358: 	if cb.onStateChange != nil {
359: 		cb.onStateChange(cb.name, prev, state)
360: 	}
361: }
362: 
363: func (cb *CircuitBreaker) toNewGeneration(now time.Time) {
364: 	cb.generation++
365: 	cb.counts.clear()
366: 
367: 	var zero time.Time
368: 	switch cb.state {
369: 	case StateClosed:
370: 		if cb.interval == 0 {
371: 			cb.expiry = zero
372: 		} else {
373: 			cb.expiry = now.Add(cb.interval)
374: 		}
375: 	case StateOpen:
376: 		cb.expiry = now.Add(cb.timeout)
377: 	default: // StateHalfOpen
378: 		cb.expiry = zero
379: 	}
380: }