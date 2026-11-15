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
[{"id": "context-01", "claim": "Stopping a registered callback before cancellation returns true on the first stop and false on a second stop."}, {"id": "context-02", "claim": "A false stop result proves that the callback is currently running."}, {"id": "context-03", "claim": "Stopping an already started callback waits until that callback finishes."}, {"id": "context-04", "claim": "Two AfterFunc registrations on the same context operate independently rather than replacing each other."}, {"id": "context-05", "claim": "Registration on an already canceled context still schedules the callback in its own goroutine."}, {"id": "context-06", "claim": "After registration, reassigning only the caller local context variable redirects the registration to the new context."}, {"id": "context-07", "claim": "The application is required to report callback latency above ten milliseconds as an incident."}]
SOURCE:
1: // Copyright 2014 The Go Authors. All rights reserved.
2: // Use of this source code is governed by a BSD-style
3: // license that can be found in the LICENSE file.
4: 
5: // Package context defines the Context type, which carries deadlines,
6: // cancellation signals, and other request-scoped values across API boundaries
7: // and between processes.
8: //
9: // Incoming requests to a server should create a [Context], and outgoing
10: // calls to servers should accept a Context. The chain of function
11: // calls between them must propagate the Context, optionally replacing
12: // it with a derived Context created using [WithCancel], [WithDeadline],
13: // [WithTimeout], or [WithValue].
14: //
15: // A Context may be canceled to indicate that work done on its behalf should stop.
16: // A Context with a deadline is canceled after the deadline passes.
17: // When a Context is canceled, all Contexts derived from it are also canceled.
18: //
19: // The [WithCancel], [WithDeadline], and [WithTimeout] functions take a
20: // Context (the parent) and return a derived Context (the child) and a
21: // [CancelFunc]. Calling the CancelFunc directly cancels the child and its
22: // children, removes the parent's reference to the child, and stops
23: // any associated timers. Failing to call the CancelFunc leaks the
24: // child and its children until the parent is canceled. The go vet tool
25: // checks that CancelFuncs are used on all control-flow paths.
26: //
27: // The [WithCancelCause] function returns a [CancelCauseFunc], which takes
28: // an error and records it as the cancellation cause. [WithDeadlineCause]
29: // and [WithTimeoutCause] take a cause to use when the deadline expires.
30: // Calling [Cause] on the canceled context or any of its children retrieves
31: // the cause. If no cause is specified, Cause(ctx) returns the same value
32: // as ctx.Err().
33: //
34: // Programs that use Contexts should follow these rules to keep interfaces
35: // consistent across packages and enable static analysis tools to check context
36: // propagation:
37: //
38: // Do not store Contexts inside a struct type; instead, pass a Context
39: // explicitly to each function that needs it. This is discussed further in
40: // https://go.dev/blog/context-and-structs. The Context should be the first
41: // parameter, typically named ctx:
42: //
43: //	func DoSomething(ctx context.Context, arg Arg) error {
44: //		// ... use ctx ...
45: //	}
46: //
47: // Do not pass a nil [Context], even if a function permits it. Pass [context.TODO]
48: // if you are unsure about which Context to use.
49: //
50: // Use context Values only for request-scoped data that transits processes and
51: // APIs, not for passing optional parameters to functions.
52: //
53: // The same Context may be passed to functions running in different goroutines;
54: // Contexts are safe for simultaneous use by multiple goroutines.
55: //
56: // See https://go.dev/blog/context for example code for a server that uses
57: // Contexts.
58: package context
59: 
60: import (
61: 	"errors"
62: 	"internal/reflectlite"
63: 	"sync"
64: 	"sync/atomic"
65: 	"time"
66: )
67: 
68: // A Context carries a deadline, a cancellation signal, and other values across
69: // API boundaries.
70: //
71: // Context's methods may be called by multiple goroutines simultaneously.
72: type Context interface {
73: 	// Deadline returns the time when work done on behalf of this context
74: 	// should be canceled. Deadline returns ok==false when no deadline is
75: 	// set. Successive calls to Deadline return the same results.
76: 	Deadline() (deadline time.Time, ok bool)
77: 
78: 	// Done returns a channel that's closed when work done on behalf of this
79: 	// context should be canceled. Done may return nil if this context can
80: 	// never be canceled. Successive calls to Done return the same value.
81: 	// The close of the Done channel may happen asynchronously,
82: 	// after the cancel function returns.
83: 	//
84: 	// WithCancel arranges for Done to be closed when cancel is called;
85: 	// WithDeadline arranges for Done to be closed when the deadline
86: 	// expires; WithTimeout arranges for Done to be closed when the timeout
87: 	// elapses.
88: 	//
89: 	// Done is provided for use in select statements:
90: 	//
91: 	//  // Stream generates values with DoSomething and sends them to out
92: 	//  // until DoSomething returns an error or ctx.Done is closed.
93: 	//  func Stream(ctx context.Context, out chan<- Value) error {
94: 	//  	for {
95: 	//  		v, err := DoSomething(ctx)
96: 	//  		if err != nil {
97: 	//  			return err
98: 	//  		}
99: 	//  		select {
100: 	//  		case <-ctx.Done():
101: 	//  			return ctx.Err()
102: 	//  		case out <- v:
103: 	//  		}
104: 	//  	}
105: 	//  }
106: 	//
107: 	// See https://go.dev/blog/pipelines for more examples of how to use
108: 	// a Done channel for cancellation.
109: 	Done() <-chan struct{}
110: 
111: 	// If Done is not yet closed, Err returns nil.
112: 	// If Done is closed, Err returns a non-nil error explaining why:
113: 	// DeadlineExceeded if the context's deadline passed,
114: 	// or Canceled if the context was canceled for some other reason.
115: 	// After Err returns a non-nil error, successive calls to Err return the same error.
116: 	Err() error
117: 
118: 	// Value returns the value associated with this context for key, or nil
119: 	// if no value is associated with key. Successive calls to Value with
120: 	// the same key returns the same result.
121: 	//
122: 	// Use context values only for request-scoped data that transits
123: 	// processes and API boundaries, not for passing optional parameters to
124: 	// functions.
125: 	//
126: 	// A key identifies a specific value in a Context. Functions that wish
127: 	// to store values in Context typically allocate a key in a global
128: 	// variable then use that key as the argument to context.WithValue and
129: 	// Context.Value. A key can be any type that supports equality;
130: 	// packages should define keys as an unexported type to avoid
131: 	// collisions.
132: 	//
133: 	// Packages that define a Context key should provide type-safe accessors
134: 	// for the values stored using that key:
135: 	//
136: 	// 	// Package user defines a User type that's stored in Contexts.
137: 	// 	package user
138: 	//
139: 	// 	import "context"
140: 	//
141: 	// 	// User is the type of value stored in the Contexts.
142: 	// 	type User struct {...}
143: 	//
144: 	// 	// key is an unexported type for keys defined in this package.
145: 	// 	// This prevents collisions with keys defined in other packages.
146: 	// 	type key int
147: 	//
148: 	// 	// userKey is the key for user.User values in Contexts. It is
149: 	// 	// unexported; clients use user.NewContext and user.FromContext
150: 	// 	// instead of using this key directly.
151: 	// 	var userKey key
152: 	//
153: 	// 	// NewContext returns a new Context that carries value u.
154: 	// 	func NewContext(ctx context.Context, u *User) context.Context {
155: 	// 		return context.WithValue(ctx, userKey, u)
156: 	// 	}
157: 	//
158: 	// 	// FromContext returns the User value stored in ctx, if any.
159: 	// 	func FromContext(ctx context.Context) (*User, bool) {
160: 	// 		u, ok := ctx.Value(userKey).(*User)
161: 	// 		return u, ok
162: 	// 	}
163: 	Value(key any) any
164: }
165: 
166: // Canceled is the error returned by [Context.Err] when the context is canceled
167: // for some reason other than its deadline passing.
168: var Canceled = errors.New("context canceled")
169: 
170: // DeadlineExceeded is the error returned by [Context.Err] when the context is canceled
171: // due to its deadline passing.
172: var DeadlineExceeded error = deadlineExceededError{}
173: 
174: type deadlineExceededError struct{}
175: 
176: func (deadlineExceededError) Error() string   { return "context deadline exceeded" }
177: func (deadlineExceededError) Timeout() bool   { return true }
178: func (deadlineExceededError) Temporary() bool { return true }
179: 
180: // An emptyCtx is never canceled, has no values, and has no deadline.
181: // It is the common base of backgroundCtx and todoCtx.
182: type emptyCtx struct{}
183: 
184: func (emptyCtx) Deadline() (deadline time.Time, ok bool) {
185: 	return
186: }
187: 
188: func (emptyCtx) Done() <-chan struct{} {
189: 	return nil
190: }
191: 
192: func (emptyCtx) Err() error {
193: 	return nil
194: }
195: 
196: func (emptyCtx) Value(key any) any {
197: 	return nil
198: }
199: 
200: type backgroundCtx struct{ emptyCtx }
201: 
202: func (backgroundCtx) String() string {
203: 	return "context.Background"
204: }
205: 
206: type todoCtx struct{ emptyCtx }
207: 
208: func (todoCtx) String() string {
209: 	return "context.TODO"
210: }
211: 
212: // Background returns a non-nil, empty [Context]. It is never canceled, has no
213: // values, and has no deadline. It is typically used by the main function,
214: // initialization, and tests, and as the top-level Context for incoming
215: // requests.
216: func Background() Context {
217: 	return backgroundCtx{}
218: }
219: 
220: // TODO returns a non-nil, empty [Context]. Code should use context.TODO when
221: // it's unclear which Context to use or it is not yet available (because the
222: // surrounding function has not yet been extended to accept a Context
223: // parameter).
224: func TODO() Context {
225: 	return todoCtx{}
226: }
227: 
228: // A CancelFunc tells an operation to abandon its work.
229: // A CancelFunc does not wait for the work to stop.
230: // A CancelFunc may be called by multiple goroutines simultaneously.
231: // After the first call, subsequent calls to a CancelFunc do nothing.
232: type CancelFunc func()
233: 
234: // WithCancel returns a derived context that points to the parent context
235: // but has a new Done channel. The returned context's Done channel is closed
236: // when the returned cancel function is called or when the parent context's
237: // Done channel is closed, whichever happens first.
238: //
239: // Canceling this context releases resources associated with it, so code should
240: // call cancel as soon as the operations running in this [Context] complete.
241: func WithCancel(parent Context) (ctx Context, cancel CancelFunc) {
242: 	c := withCancel(parent)
243: 	return c, func() { c.cancel(true, Canceled, nil) }
244: }
245: 
246: // A CancelCauseFunc behaves like a [CancelFunc] but additionally sets the cancellation cause.
247: // This cause can be retrieved by calling [Cause] on the canceled Context or on
248: // any of its derived Contexts.
249: //
250: // If the context has already been canceled, CancelCauseFunc does not set the cause.
251: // For example, if childContext is derived from parentContext:
252: //   - if parentContext is canceled with cause1 before childContext is canceled with cause2,
253: //     then Cause(parentContext) == Cause(childContext) == cause1
254: //   - if childContext is canceled with cause2 before parentContext is canceled with cause1,
255: //     then Cause(parentContext) == cause1 and Cause(childContext) == cause2
256: type CancelCauseFunc func(cause error)
257: 
258: // WithCancelCause behaves like [WithCancel] but returns a [CancelCauseFunc] instead of a [CancelFunc].
259: // Calling cancel with a non-nil error (the "cause") records that error in ctx;
260: // it can then be retrieved using Cause(ctx).
261: // Calling cancel with nil sets the cause to Canceled.
262: //
263: // Example use:
264: //
265: //	ctx, cancel := context.WithCancelCause(parent)
266: //	cancel(myError)
267: //	ctx.Err() // returns context.Canceled
268: //	context.Cause(ctx) // returns myError
269: func WithCancelCause(parent Context) (ctx Context, cancel CancelCauseFunc) {
270: 	c := withCancel(parent)
271: 	return c, func(cause error) { c.cancel(true, Canceled, cause) }
272: }
273: 
274: func withCancel(parent Context) *cancelCtx {
275: 	if parent == nil {
276: 		panic("cannot create context from nil parent")
277: 	}
278: 	c := &cancelCtx{}
279: 	c.propagateCancel(parent, c)
280: 	return c
281: }
282: 
283: // Cause returns a non-nil error explaining why c was canceled.
284: // The first cancellation of c or one of its parents sets the cause.
285: // If that cancellation happened via a call to CancelCauseFunc(err),
286: // then [Cause] returns err.
287: // Otherwise Cause(c) returns the same value as c.Err().
288: // Cause returns nil if c has not been canceled yet.
289: func Cause(c Context) error {
290: 	err := c.Err()
291: 	if err == nil {
292: 		return nil
293: 	}
294: 	if cc, ok := c.Value(&cancelCtxKey).(*cancelCtx); ok {
295: 		cc.mu.Lock()
296: 		cause := cc.cause
297: 		cc.mu.Unlock()
298: 		if cause != nil {
299: 			return cause
300: 		}
301: 		// The parent cancelCtx doesn't have a cause,
302: 		// so c must have been canceled in some custom context implementation.
303: 	}
304: 	// We don't have a cause to return from a parent cancelCtx,
305: 	// so return the context's error.
306: 	return err
307: }
308: 
309: // AfterFunc arranges to call f in its own goroutine after ctx is canceled.
310: // If ctx is already canceled, AfterFunc calls f immediately in its own goroutine.
311: //
312: // Multiple calls to AfterFunc on a context operate independently;
313: // one does not replace another.
314: //
315: // Calling the returned stop function stops the association of ctx with f.
316: // It returns true if the call stopped f from being run.
317: // If stop returns false,
318: // either the context is canceled and f has been started in its own goroutine;
319: // or f was already stopped.
320: // The stop function does not wait for f to complete before returning.
321: // If the caller needs to know whether f is completed,
322: // it must coordinate with f explicitly.
323: //
324: // If ctx has a "AfterFunc(func()) func() bool" method,
325: // AfterFunc will use it to schedule the call.
326: func AfterFunc(ctx Context, f func()) (stop func() bool) {
327: 	a := &afterFuncCtx{
328: 		f: f,
329: 	}
330: 	a.cancelCtx.propagateCancel(ctx, a)
331: 	return func() bool {
332: 		stopped := false
333: 		a.once.Do(func() {
334: 			stopped = true
335: 		})
336: 		if stopped {
337: 			a.cancel(true, Canceled, nil)
338: 		}
339: 		return stopped
340: 	}
341: }
342: 
343: type afterFuncer interface {
344: 	AfterFunc(func()) func() bool
345: }
346: 
347: type afterFuncCtx struct {
348: 	cancelCtx
349: 	once sync.Once // either starts running f or stops f from running
350: 	f    func()
351: }
352: 
353: func (a *afterFuncCtx) cancel(removeFromParent bool, err, cause error) {
354: 	a.cancelCtx.cancel(false, err, cause)
355: 	if removeFromParent {
356: 		removeChild(a.Context, a)
357: 	}
358: 	a.once.Do(func() {
359: 		go a.f()
360: 	})
361: }
362: 
363: // A stopCtx is used as the parent context of a cancelCtx when
364: // an AfterFunc has been registered with the parent.
365: // It holds the stop function used to unregister the AfterFunc.
366: type stopCtx struct {
367: 	Context
368: 	stop func() bool
369: }
370: 
371: // goroutines counts the number of goroutines ever created; for testing.
372: var goroutines atomic.Int32
373: 
374: // &cancelCtxKey is the key that a cancelCtx returns itself for.
375: var cancelCtxKey int
376: 
377: // parentCancelCtx returns the underlying *cancelCtx for parent.
378: // It does this by looking up parent.Value(&cancelCtxKey) to find
379: // the innermost enclosing *cancelCtx and then checking whether
380: // parent.Done() matches that *cancelCtx. (If not, the *cancelCtx
381: // has been wrapped in a custom implementation providing a
382: // different done channel, in which case we should not bypass it.)
383: func parentCancelCtx(parent Context) (*cancelCtx, bool) {
384: 	done := parent.Done()
385: 	if done == closedchan || done == nil {
386: 		return nil, false
387: 	}
388: 	p, ok := parent.Value(&cancelCtxKey).(*cancelCtx)
389: 	if !ok {
390: 		return nil, false
391: 	}
392: 	pdone, _ := p.done.Load().(chan struct{})
393: 	if pdone != done {
394: 		return nil, false
395: 	}
396: 	return p, true
397: }
398: 
399: // removeChild removes a context from its parent.
400: func removeChild(parent Context, child canceler) {
401: 	if s, ok := parent.(stopCtx); ok {
402: 		s.stop()
403: 		return
404: 	}
405: 	p, ok := parentCancelCtx(parent)
406: 	if !ok {
407: 		return
408: 	}
409: 	p.mu.Lock()
410: 	if p.children != nil {
411: 		delete(p.children, child)
412: 	}
413: 	p.mu.Unlock()
414: }
415: 
416: // A canceler is a context type that can be canceled directly. The
417: // implementations are *cancelCtx and *timerCtx.
418: type canceler interface {
419: 	cancel(removeFromParent bool, err, cause error)
420: 	Done() <-chan struct{}
421: }
422: 
423: // closedchan is a reusable closed channel.
424: var closedchan = make(chan struct{})
425: 
426: func init() {
427: 	close(closedchan)
428: }
429: 
430: // A cancelCtx can be canceled. When canceled, it also cancels any children
431: // that implement canceler.
432: type cancelCtx struct {
433: 	Context
434: 
435: 	mu       sync.Mutex            // protects following fields
436: 	done     atomic.Value          // of chan struct{}, created lazily, closed by first cancel call
437: 	children map[canceler]struct{} // set to nil by the first cancel call
438: 	err      atomic.Value          // set to non-nil by the first cancel call
439: 	cause    error                 // set to non-nil by the first cancel call
440: }
441: 
442: func (c *cancelCtx) Value(key any) any {
443: 	if key == &cancelCtxKey {
444: 		return c
445: 	}
446: 	return value(c.Context, key)
447: }
448: 
449: func (c *cancelCtx) Done() <-chan struct{} {
450: 	d := c.done.Load()
451: 	if d != nil {
452: 		return d.(chan struct{})
453: 	}
454: 	c.mu.Lock()
455: 	defer c.mu.Unlock()
456: 	d = c.done.Load()
457: 	if d == nil {
458: 		d = make(chan struct{})
459: 		c.done.Store(d)
460: 	}
461: 	return d.(chan struct{})
462: }
463: 
464: func (c *cancelCtx) Err() error {
465: 	// An atomic load is ~5x faster than a mutex, which can matter in tight loops.
466: 	if err := c.err.Load(); err != nil {
467: 		// Ensure the done channel has been closed before returning a non-nil error.
468: 		<-c.Done()
469: 		return err.(error)
470: 	}
471: 	return nil
472: }
473: 
474: // propagateCancel arranges for child to be canceled when parent is.
475: // It sets the parent context of cancelCtx.
476: func (c *cancelCtx) propagateCancel(parent Context, child canceler) {
477: 	c.Context = parent
478: 
479: 	done := parent.Done()
480: 	if done == nil {
481: 		return // parent is never canceled
482: 	}
483: 
484: 	select {
485: 	case <-done:
486: 		// parent is already canceled
487: 		child.cancel(false, parent.Err(), Cause(parent))
488: 		return
489: 	default:
490: 	}
491: 
492: 	if p, ok := parentCancelCtx(parent); ok {
493: 		// parent is a *cancelCtx, or derives from one.
494: 		p.mu.Lock()
495: 		if err := p.err.Load(); err != nil {
496: 			// parent has already been canceled
497: 			child.cancel(false, err.(error), p.cause)
498: 		} else {
499: 			if p.children == nil {
500: 				p.children = make(map[canceler]struct{})
501: 			}
502: 			p.children[child] = struct{}{}
503: 		}
504: 		p.mu.Unlock()
505: 		return
506: 	}
507: 
508: 	if a, ok := parent.(afterFuncer); ok {
509: 		// parent implements an AfterFunc method.
510: 		c.mu.Lock()
511: 		stop := a.AfterFunc(func() {
512: 			child.cancel(false, parent.Err(), Cause(parent))
513: 		})
514: 		c.Context = stopCtx{
515: 			Context: parent,
516: 			stop:    stop,
517: 		}
518: 		c.mu.Unlock()
519: 		return
520: 	}
521: 
522: 	goroutines.Add(1)
523: 	go func() {
524: 		select {
525: 		case <-parent.Done():
526: 			child.cancel(false, parent.Err(), Cause(parent))
527: 		case <-child.Done():
528: 		}
529: 	}()
530: }
531: 
532: type stringer interface {
533: 	String() string
534: }
535: 
536: func contextName(c Context) string {
537: 	if s, ok := c.(stringer); ok {
538: 		return s.String()
539: 	}
540: 	return reflectlite.TypeOf(c).String()
541: }
542: 
543: func (c *cancelCtx) String() string {
544: 	return contextName(c.Context) + ".WithCancel"
545: }
546: 
547: // cancel closes c.done, cancels each of c's children, and, if
548: // removeFromParent is true, removes c from its parent's children.
549: // cancel sets c.cause to cause if this is the first time c is canceled.
550: func (c *cancelCtx) cancel(removeFromParent bool, err, cause error) {
551: 	if err == nil {
552: 		panic("context: internal error: missing cancel error")
553: 	}
554: 	if cause == nil {
555: 		cause = err
556: 	}
557: 	c.mu.Lock()
558: 	if c.err.Load() != nil {
559: 		c.mu.Unlock()
560: 		return // already canceled
561: 	}
562: 	c.err.Store(err)
563: 	c.cause = cause
564: 	d, _ := c.done.Load().(chan struct{})
565: 	if d == nil {
566: 		c.done.Store(closedchan)
567: 	} else {
568: 		close(d)
569: 	}
570: 	for child := range c.children {
571: 		// NOTE: acquiring the child's lock while holding parent's lock.
572: 		child.cancel(false, err, cause)
573: 	}
574: 	c.children = nil
575: 	c.mu.Unlock()
576: 
577: 	if removeFromParent {
578: 		removeChild(c.Context, c)
579: 	}
580: }
581: 
582: // WithoutCancel returns a derived context that points to the parent context
583: // and is not canceled when parent is canceled.
584: // The returned context returns no Deadline or Err, and its Done channel is nil.
585: // Calling [Cause] on the returned context returns nil.
586: func WithoutCancel(parent Context) Context {
587: 	if parent == nil {
588: 		panic("cannot create context from nil parent")
589: 	}
590: 	return withoutCancelCtx{parent}
591: }
592: 
593: type withoutCancelCtx struct {
594: 	c Context
595: }
596: 
597: func (withoutCancelCtx) Deadline() (deadline time.Time, ok bool) {
598: 	return
599: }
600: 
601: func (withoutCancelCtx) Done() <-chan struct{} {
602: 	return nil
603: }
604: 
605: func (withoutCancelCtx) Err() error {
606: 	return nil
607: }
608: 
609: func (c withoutCancelCtx) Value(key any) any {
610: 	return value(c, key)
611: }
612: 
613: func (c withoutCancelCtx) String() string {
614: 	return contextName(c.c) + ".WithoutCancel"
615: }
616: 
617: // WithDeadline returns a derived context that points to the parent context
618: // but has the deadline adjusted to be no later than d. If the parent's
619: // deadline is already earlier than d, WithDeadline(parent, d) is semantically
620: // equivalent to parent. The returned [Context.Done] channel is closed when
621: // the deadline expires, when the returned cancel function is called,
622: // or when the parent context's Done channel is closed, whichever happens first.
623: //
624: // Canceling this context releases resources associated with it, so code should
625: // call cancel as soon as the operations running in this [Context] complete.
626: func WithDeadline(parent Context, d time.Time) (Context, CancelFunc) {
627: 	return WithDeadlineCause(parent, d, nil)
628: }
629: 
630: // WithDeadlineCause behaves like [WithDeadline] but also sets the cause of the
631: // returned Context when the deadline is exceeded. The returned [CancelFunc] does
632: // not set the cause.
633: func WithDeadlineCause(parent Context, d time.Time, cause error) (Context, CancelFunc) {
634: 	if parent == nil {
635: 		panic("cannot create context from nil parent")
636: 	}
637: 	if cur, ok := parent.Deadline(); ok && cur.Before(d) {
638: 		// The current deadline is already sooner than the new one.
639: 		return WithCancel(parent)
640: 	}
641: 	c := &timerCtx{
642: 		deadline: d,
643: 	}
644: 	c.cancelCtx.propagateCancel(parent, c)
645: 	dur := time.Until(d)
646: 	if dur <= 0 {
647: 		c.cancel(true, DeadlineExceeded, cause) // deadline has already passed
648: 		return c, func() { c.cancel(false, Canceled, nil) }
649: 	}
650: 	c.mu.Lock()
651: 	defer c.mu.Unlock()
652: 	if c.err.Load() == nil {
653: 		c.timer = time.AfterFunc(dur, func() {
654: 			c.cancel(true, DeadlineExceeded, cause)
655: 		})
656: 	}
657: 	return c, func() { c.cancel(true, Canceled, nil) }
658: }
659: 
660: // A timerCtx carries a timer and a deadline. It embeds a cancelCtx to
661: // implement Done and Err. It implements cancel by stopping its timer then
662: // delegating to cancelCtx.cancel.
663: type timerCtx struct {
664: 	cancelCtx
665: 	timer *time.Timer // Under cancelCtx.mu.
666: 
667: 	deadline time.Time
668: }
669: 
670: func (c *timerCtx) Deadline() (deadline time.Time, ok bool) {
671: 	return c.deadline, true
672: }
673: 
674: func (c *timerCtx) String() string {
675: 	return contextName(c.cancelCtx.Context) + ".WithDeadline(" +
676: 		c.deadline.String() + " [" +
677: 		time.Until(c.deadline).String() + "])"
678: }
679: 
680: func (c *timerCtx) cancel(removeFromParent bool, err, cause error) {
681: 	c.cancelCtx.cancel(false, err, cause)
682: 	if removeFromParent {
683: 		// Remove this timerCtx from its parent cancelCtx's children.
684: 		removeChild(c.cancelCtx.Context, c)
685: 	}
686: 	c.mu.Lock()
687: 	if c.timer != nil {
688: 		c.timer.Stop()
689: 		c.timer = nil
690: 	}
691: 	c.mu.Unlock()
692: }
693: 
694: // WithTimeout returns WithDeadline(parent, time.Now().Add(timeout)).
695: //
696: // Canceling this context releases resources associated with it, so code should
697: // call cancel as soon as the operations running in this [Context] complete:
698: //
699: //	func slowOperationWithTimeout(ctx context.Context) (Result, error) {
700: //		ctx, cancel := context.WithTimeout(ctx, 100*time.Millisecond)
701: //		defer cancel()  // releases resources if slowOperation completes before timeout elapses
702: //		return slowOperation(ctx)
703: //	}
704: func WithTimeout(parent Context, timeout time.Duration) (Context, CancelFunc) {
705: 	return WithDeadline(parent, time.Now().Add(timeout))
706: }
707: 
708: // WithTimeoutCause behaves like [WithTimeout] but also sets the cause of the
709: // returned Context when the timeout expires. The returned [CancelFunc] does
710: // not set the cause.
711: func WithTimeoutCause(parent Context, timeout time.Duration, cause error) (Context, CancelFunc) {
712: 	return WithDeadlineCause(parent, time.Now().Add(timeout), cause)
713: }
714: 
715: // WithValue returns a derived context that points to the parent Context.
716: // In the derived context, the value associated with key is val.
717: //
718: // Use context Values only for request-scoped data that transits processes and
719: // APIs, not for passing optional parameters to functions.
720: //
721: // The provided key must be comparable and should not be of type
722: // string or any other built-in type to avoid collisions between
723: // packages using context. Users of WithValue should define their own
724: // types for keys. To avoid allocating when assigning to an
725: // interface{}, context keys often have concrete type
726: // struct{}. Alternatively, exported context key variables' static
727: // type should be a pointer or interface.
728: func WithValue(parent Context, key, val any) Context {
729: 	if parent == nil {
730: 		panic("cannot create context from nil parent")
731: 	}
732: 	if key == nil {
733: 		panic("nil key")
734: 	}
735: 	if !reflectlite.TypeOf(key).Comparable() {
736: 		panic("key is not comparable")
737: 	}
738: 	return &valueCtx{parent, key, val}
739: }
740: 
741: // A valueCtx carries a key-value pair. It implements Value for that key and
742: // delegates all other calls to the embedded Context.
743: type valueCtx struct {
744: 	Context
745: 	key, val any
746: }
747: 
748: // stringify tries a bit to stringify v, without using fmt, since we don't
749: // want context depending on the unicode tables. This is only used by
750: // *valueCtx.String().
751: func stringify(v any) string {
752: 	switch s := v.(type) {
753: 	case stringer:
754: 		return s.String()
755: 	case string:
756: 		return s
757: 	case nil:
758: 		return "<nil>"
759: 	}
760: 	return reflectlite.TypeOf(v).String()
761: }
762: 
763: func (c *valueCtx) String() string {
764: 	return contextName(c.Context) + ".WithValue(" +
765: 		stringify(c.key) + ", " +
766: 		stringify(c.val) + ")"
767: }
768: 
769: func (c *valueCtx) Value(key any) any {
770: 	if c.key == key {
771: 		return c.val
772: 	}
773: 	return value(c.Context, key)
774: }
775: 
776: func value(c Context, key any) any {
777: 	for {
778: 		switch ctx := c.(type) {
779: 		case *valueCtx:
780: 			if key == ctx.key {
781: 				return ctx.val
782: 			}
783: 			c = ctx.Context
784: 		case *cancelCtx:
785: 			if key == &cancelCtxKey {
786: 				return c
787: 			}
788: 			c = ctx.Context
789: 		case withoutCancelCtx:
790: 			if key == &cancelCtxKey {
791: 				// This implements Cause(ctx) == nil
792: 				// when ctx is created using WithoutCancel.
793: 				return nil
794: 			}
795: 			c = ctx.c
796: 		case *timerCtx:
797: 			if key == &cancelCtxKey {
798: 				return &ctx.cancelCtx
799: 			}
800: 			c = ctx.Context
801: 		case backgroundCtx, todoCtx:
802: 			return nil
803: 		default:
804: 			return c.Value(key)
805: 		}
806: 	}
807: }
ADVISORY DRAFT (not truth):
{"source": "upstream/context/context.go", "source_sha256": "971f00ffa375b79d3f65e6da33cca3a493cc3fce091c589233abfb4283e29b7d", "draft": {"model": "deepseek-flash", "finish_reason": "stop", "input_tokens": 8926, "output_tokens": 667, "cost_microdollars": 3479, "reservation_microdollars": 19396}, "verification": {"model": "jev-1.14.0", "input_tokens": 8203, "cost_microdollars": 345, "reservation_microdollars": 1364, "error": null}, "claims": {"C1": {"kind": "claim", "statement": "AfterFunc calls f in its own goroutine after ctx is canceled.", "line": 309, "fragment": "AfterFunc arranges to call f in its own goroutine after ctx is canceled.", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}, "confidence": 1.0}}, "C2": {"kind": "claim", "statement": "If ctx is already canceled, AfterFunc calls f immediately in its own goroutine.", "line": 310, "fragment": "If ctx is already canceled, AfterFunc calls f immediately in its own goroutine.", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}, "confidence": 1.0}}, "C3": {"kind": "claim", "statement": "Multiple AfterFunc calls on a context operate independently and one does not replace another.", "line": 312, "fragment": "Multiple calls to AfterFunc on a context operate independently;", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.98, "contradicted": 0.0, "unclear": 0.02}, "confidence": 0.97}}, "C4": {"kind": "claim", "statement": "The returned stop function does not wait for f to complete before returning.", "line": 320, "fragment": "The stop function does not wait for f to complete before returning.", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}, "confidence": 1.0}}, "C5": {"kind": "claim", "statement": "Canceling a context releases resources associated with it, so code should call cancel as soon as operations running in the context complete.", "line": 239, "fragment": "Canceling this context releases resources associated with it, so code should", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}, "confidence": 1.0}}, "C6": {"kind": "claim", "statement": "A CancelFunc does not wait for the work to stop.", "line": 229, "fragment": "A CancelFunc does not wait for the work to stop.", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}, "confidence": 1.0}}, "C7": {"kind": "claim", "statement": "The same Context may be passed to functions running in different goroutines and is safe for simultaneous use by multiple goroutines.", "line": 53, "fragment": "The same Context may be passed to functions running in different goroutines;", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.9, "contradicted": 0.0, "unclear": 0.1}, "confidence": 0.85}}}, "questions": ["Does the source establish that stopping a registered callback before cancellation returns true on the first stop and false on a second stop?", "Does the source establish that a false stop result proves the callback is currently running?", "Does the source establish that stopping an already started callback waits until that callback finishes?", "Does the source establish whether two AfterFunc registrations on the same context operate independently rather than replacing each other?", "Does the source establish that registration on an already canceled context still schedules the callback in its own goroutine?", "Does the source establish what happens to a registration if only the caller local context variable is reassigned after registration?", "Does the source specify any requirement for the application to report callback latency above ten milliseconds as an incident?", "Does the source establish that multiple AfterFunc calls on the same context are independent registrations rather than one replacing another?", "Does the source establish that stopping an already started callback does not wait until the callback finishes?", "Does the source establish an ordering between stopping a callback and cancellation that determines the meaning of a false stop result?", "Does the source specify when a callback registered on an already canceled context is scheduled relative to the registration call?"], "review_required": true}