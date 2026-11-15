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
[{"id": "singleflight-01", "claim": "Forget cancels the already running function for that key."}, {"id": "singleflight-02", "claim": "After Forget and a new call under the same key, completion of the old call removes the new call from duplicate suppression."}, {"id": "singleflight-03", "claim": "A duplicate DoChan while the original call is pending receives the original result without running its own function."}, {"id": "singleflight-04", "claim": "After a successful call finishes, subsequent calls with that key permanently reuse the cached result."}, {"id": "singleflight-05", "claim": "The DoChan result channel is closed after its result is delivered."}, {"id": "singleflight-06", "claim": "The same key used concurrently in two distinct Group instances shares a single execution."}, {"id": "singleflight-07", "claim": "Application-level errors must be cached for thirty seconds before another request is allowed."}]
SOURCE:
1: // Copyright 2013 The Go Authors. All rights reserved.
2: // Use of this source code is governed by a BSD-style
3: // license that can be found in the LICENSE file.
4: 
5: // Package singleflight provides a duplicate function call suppression
6: // mechanism.
7: package singleflight // import "golang.org/x/sync/singleflight"
8: 
9: import (
10: 	"bytes"
11: 	"errors"
12: 	"fmt"
13: 	"runtime"
14: 	"runtime/debug"
15: 	"sync"
16: )
17: 
18: // errGoexit indicates the runtime.Goexit was called in
19: // the user given function.
20: var errGoexit = errors.New("runtime.Goexit was called")
21: 
22: // A panicError is an arbitrary value recovered from a panic
23: // with the stack trace during the execution of given function.
24: type panicError struct {
25: 	value interface{}
26: 	stack []byte
27: }
28: 
29: // Error implements error interface.
30: func (p *panicError) Error() string {
31: 	return fmt.Sprintf("%v\n\n%s", p.value, p.stack)
32: }
33: 
34: func (p *panicError) Unwrap() error {
35: 	err, ok := p.value.(error)
36: 	if !ok {
37: 		return nil
38: 	}
39: 
40: 	return err
41: }
42: 
43: func newPanicError(v interface{}) error {
44: 	stack := debug.Stack()
45: 
46: 	// The first line of the stack trace is of the form "goroutine N [status]:"
47: 	// but by the time the panic reaches Do the goroutine may no longer exist
48: 	// and its status will have changed. Trim out the misleading line.
49: 	if line := bytes.IndexByte(stack[:], '\n'); line >= 0 {
50: 		stack = stack[line+1:]
51: 	}
52: 	return &panicError{value: v, stack: stack}
53: }
54: 
55: // call is an in-flight or completed singleflight.Do call
56: type call struct {
57: 	wg sync.WaitGroup
58: 
59: 	// These fields are written once before the WaitGroup is done
60: 	// and are only read after the WaitGroup is done.
61: 	val interface{}
62: 	err error
63: 
64: 	// These fields are read and written with the singleflight
65: 	// mutex held before the WaitGroup is done, and are read but
66: 	// not written after the WaitGroup is done.
67: 	dups  int
68: 	chans []chan<- Result
69: }
70: 
71: // Group represents a class of work and forms a namespace in
72: // which units of work can be executed with duplicate suppression.
73: type Group struct {
74: 	mu sync.Mutex       // protects m
75: 	m  map[string]*call // lazily initialized
76: }
77: 
78: // Result holds the results of Do, so they can be passed
79: // on a channel.
80: type Result struct {
81: 	Val    interface{}
82: 	Err    error
83: 	Shared bool
84: }
85: 
86: // Do executes and returns the results of the given function, making
87: // sure that only one execution is in-flight for a given key at a
88: // time. If a duplicate comes in, the duplicate caller waits for the
89: // original to complete and receives the same results.
90: // The return value shared indicates whether v was given to multiple callers.
91: func (g *Group) Do(key string, fn func() (interface{}, error)) (v interface{}, err error, shared bool) {
92: 	g.mu.Lock()
93: 	if g.m == nil {
94: 		g.m = make(map[string]*call)
95: 	}
96: 	if c, ok := g.m[key]; ok {
97: 		c.dups++
98: 		g.mu.Unlock()
99: 		c.wg.Wait()
100: 
101: 		if e, ok := c.err.(*panicError); ok {
102: 			panic(e)
103: 		} else if c.err == errGoexit {
104: 			runtime.Goexit()
105: 		}
106: 		return c.val, c.err, true
107: 	}
108: 	c := new(call)
109: 	c.wg.Add(1)
110: 	g.m[key] = c
111: 	g.mu.Unlock()
112: 
113: 	g.doCall(c, key, fn)
114: 	return c.val, c.err, c.dups > 0
115: }
116: 
117: // DoChan is like Do but returns a channel that will receive the
118: // results when they are ready.
119: //
120: // The returned channel will not be closed.
121: func (g *Group) DoChan(key string, fn func() (interface{}, error)) <-chan Result {
122: 	ch := make(chan Result, 1)
123: 	g.mu.Lock()
124: 	if g.m == nil {
125: 		g.m = make(map[string]*call)
126: 	}
127: 	if c, ok := g.m[key]; ok {
128: 		c.dups++
129: 		c.chans = append(c.chans, ch)
130: 		g.mu.Unlock()
131: 		return ch
132: 	}
133: 	c := &call{chans: []chan<- Result{ch}}
134: 	c.wg.Add(1)
135: 	g.m[key] = c
136: 	g.mu.Unlock()
137: 
138: 	go g.doCall(c, key, fn)
139: 
140: 	return ch
141: }
142: 
143: // doCall handles the single call for a key.
144: func (g *Group) doCall(c *call, key string, fn func() (interface{}, error)) {
145: 	normalReturn := false
146: 	recovered := false
147: 
148: 	// use double-defer to distinguish panic from runtime.Goexit,
149: 	// more details see https://golang.org/cl/134395
150: 	defer func() {
151: 		// the given function invoked runtime.Goexit
152: 		if !normalReturn && !recovered {
153: 			c.err = errGoexit
154: 		}
155: 
156: 		g.mu.Lock()
157: 		defer g.mu.Unlock()
158: 		c.wg.Done()
159: 		if g.m[key] == c {
160: 			delete(g.m, key)
161: 		}
162: 
163: 		if e, ok := c.err.(*panicError); ok {
164: 			// In order to prevent the waiting channels from being blocked forever,
165: 			// needs to ensure that this panic cannot be recovered.
166: 			if len(c.chans) > 0 {
167: 				go panic(e)
168: 				select {} // Keep this goroutine around so that it will appear in the crash dump.
169: 			} else {
170: 				panic(e)
171: 			}
172: 		} else if c.err == errGoexit {
173: 			// Already in the process of goexit, no need to call again
174: 		} else {
175: 			// Normal return
176: 			for _, ch := range c.chans {
177: 				ch <- Result{c.val, c.err, c.dups > 0}
178: 			}
179: 		}
180: 	}()
181: 
182: 	func() {
183: 		defer func() {
184: 			if !normalReturn {
185: 				// Ideally, we would wait to take a stack trace until we've determined
186: 				// whether this is a panic or a runtime.Goexit.
187: 				//
188: 				// Unfortunately, the only way we can distinguish the two is to see
189: 				// whether the recover stopped the goroutine from terminating, and by
190: 				// the time we know that, the part of the stack trace relevant to the
191: 				// panic has been discarded.
192: 				if r := recover(); r != nil {
193: 					c.err = newPanicError(r)
194: 				}
195: 			}
196: 		}()
197: 
198: 		c.val, c.err = fn()
199: 		normalReturn = true
200: 	}()
201: 
202: 	if !normalReturn {
203: 		recovered = true
204: 	}
205: }
206: 
207: // Forget tells the singleflight to forget about a key.  Future calls
208: // to Do for this key will call the function rather than waiting for
209: // an earlier call to complete.
210: func (g *Group) Forget(key string) {
211: 	g.mu.Lock()
212: 	delete(g.m, key)
213: 	g.mu.Unlock()
214: }
ADVISORY DRAFT (not truth):
{"source": "upstream/singleflight/singleflight.go", "source_sha256": "3ab234a431a14594f1bc46e76d9d35928fa18d05947801e167df1015834719a8", "draft": {"model": "deepseek-flash", "finish_reason": "stop", "input_tokens": 2551, "output_tokens": 607, "cost_microdollars": 1494, "reservation_microdollars": 12636}, "verification": {"model": "jev-1.14.0", "input_tokens": 3011, "cost_microdollars": 127, "reservation_microdollars": 500, "error": null}, "claims": {"C1": {"kind": "claim", "statement": "Forget does not cancel an already running function for that key; it only deletes the key from the map so future calls will call the function rather than wait for the earlier call.", "line": 208, "fragment": "Future calls", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.78, "contradicted": 0.0, "unclear": 0.22}, "confidence": 0.67}}, "C2": {"kind": "claim", "statement": "After the call completes, doCall only deletes the map entry if the stored entry is still the same call, so completion of the old call does not remove a new call from duplicate suppression.", "line": 159, "fragment": "if g.m[key] == c {", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.97, "contradicted": 0.0, "unclear": 0.03}, "confidence": 0.96}}, "C3": {"kind": "claim", "statement": "A duplicate DoChan call while the original is pending receives the original result without running its own function; its channel is appended to the pending call's chans.", "line": 129, "fragment": "c.chans = append(c.chans, ch)", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.96, "contradicted": 0.0, "unclear": 0.04}, "confidence": 0.94}}, "C4": {"kind": "claim", "statement": "After a call finishes and is removed, subsequent calls with that key do not permanently reuse a cached result; a call is deleted from the map on completion (unless replaced).", "line": 160, "fragment": "delete(g.m, key)", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.98, "contradicted": 0.0, "unclear": 0.02}, "confidence": 0.97}}, "C5": {"kind": "claim", "statement": "The DoChan result channel is not closed after delivery.", "line": 120, "fragment": "The returned channel will not be closed.", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}, "confidence": 1.0}}, "C6": {"kind": "claim", "statement": "Distinct Group instances have separate maps, so the same key used concurrently in two distinct Group instances does not share a single execution.", "line": 75, "fragment": "m  map[string]*call", "citation_check": "ok", "jev": {"choice": "unclear", "probabilities": {"supported": 0.32, "contradicted": 0.0, "unclear": 0.68}, "confidence": 0.52}}, "C7": {"kind": "claim", "statement": "The source does not require application-level errors to be cached for thirty seconds before another request is allowed.", "line": 160, "fragment": "delete(g.m, key)", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.51, "contradicted": 0.04, "unclear": 0.45}, "confidence": 0.26}}}, "questions": ["Does Forget cancel an already running function for that key, or only affect future calls as stated in the comment?", "After Forget and a new call under the same key, does completion of the old call remove the new call from duplicate suppression, given the g.m[key] == c check?", "Is the DoChan result channel ever closed, including on panic or Goexit paths?", "Must application-level errors be cached for thirty seconds before another request is allowed, or is that entirely an application-policy decision?", "Is sharing a single execution across distinct Group instances intended, or is per-Group isolation the intended namespace behavior?", "What should happen to pending DoChan channels when the function panics or invokes runtime.Goexit?"], "review_required": true}