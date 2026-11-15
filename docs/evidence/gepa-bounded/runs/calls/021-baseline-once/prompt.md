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
[{"id": "once-01", "claim": "Copying the function returned by OnceFunc shares its once state; calling both function values invokes the original function once."}, {"id": "once-02", "claim": "Two separate OnceFunc calls wrapping the same function share one once state."}, {"id": "once-03", "claim": "If the original function panics, repeated calls re-panic with the same value without executing the original function again."}, {"id": "once-04", "claim": "If OnceValue returns a pointer, later mutation of the pointed-to object is visible through subsequent returns of that same pointer."}, {"id": "once-05", "claim": "Reassigning only the caller function variable after constructing OnceFunc changes which function the wrapper invokes."}, {"id": "once-06", "claim": "After recovering the first OnceFunc panic, calling the wrapper again returns normally."}, {"id": "once-07", "claim": "The application must retry an initialization function after every panic."}]
SOURCE:
1: // Copyright 2022 The Go Authors. All rights reserved.
2: // Use of this source code is governed by a BSD-style
3: // license that can be found in the LICENSE file.
4: 
5: package sync
6: 
7: // OnceFunc returns a function that invokes f only once. The returned function
8: // may be called concurrently.
9: //
10: // If f panics, the returned function will panic with the same value on every call.
11: func OnceFunc(f func()) func() {
12: 	// Use a struct so that there's a single heap allocation.
13: 	d := struct {
14: 		f     func()
15: 		once  Once
16: 		valid bool
17: 		p     any
18: 	}{
19: 		f: f,
20: 	}
21: 	return func() {
22: 		d.once.Do(func() {
23: 			defer func() {
24: 				d.f = nil // Do not keep f alive after invoking it.
25: 				d.p = recover()
26: 				if !d.valid {
27: 					// Re-panic immediately so on the first
28: 					// call the user gets a complete stack
29: 					// trace into f.
30: 					panic(d.p)
31: 				}
32: 			}()
33: 			d.f()
34: 			d.valid = true // Set only if f does not panic.
35: 		})
36: 		if !d.valid {
37: 			panic(d.p)
38: 		}
39: 	}
40: }
41: 
42: // OnceValue returns a function that invokes f only once and returns the value
43: // returned by f. The returned function may be called concurrently.
44: //
45: // If f panics, the returned function will panic with the same value on every call.
46: func OnceValue[T any](f func() T) func() T {
47: 	// Use a struct so that there's a single heap allocation.
48: 	d := struct {
49: 		f      func() T
50: 		once   Once
51: 		valid  bool
52: 		p      any
53: 		result T
54: 	}{
55: 		f: f,
56: 	}
57: 	return func() T {
58: 		d.once.Do(func() {
59: 			defer func() {
60: 				d.f = nil
61: 				d.p = recover()
62: 				if !d.valid {
63: 					panic(d.p)
64: 				}
65: 			}()
66: 			d.result = d.f()
67: 			d.valid = true
68: 		})
69: 		if !d.valid {
70: 			panic(d.p)
71: 		}
72: 		return d.result
73: 	}
74: }
75: 
76: // OnceValues returns a function that invokes f only once and returns the values
77: // returned by f. The returned function may be called concurrently.
78: //
79: // If f panics, the returned function will panic with the same value on every call.
80: func OnceValues[T1, T2 any](f func() (T1, T2)) func() (T1, T2) {
81: 	// Use a struct so that there's a single heap allocation.
82: 	d := struct {
83: 		f     func() (T1, T2)
84: 		once  Once
85: 		valid bool
86: 		p     any
87: 		r1    T1
88: 		r2    T2
89: 	}{
90: 		f: f,
91: 	}
92: 	return func() (T1, T2) {
93: 		d.once.Do(func() {
94: 			defer func() {
95: 				d.f = nil
96: 				d.p = recover()
97: 				if !d.valid {
98: 					panic(d.p)
99: 				}
100: 			}()
101: 			d.r1, d.r2 = d.f()
102: 			d.valid = true
103: 		})
104: 		if !d.valid {
105: 			panic(d.p)
106: 		}
107: 		return d.r1, d.r2
108: 	}
109: }
ADVISORY DRAFT (not truth):
{"source": "upstream/once/oncefunc.go", "source_sha256": "0853c1ad885c593d2810e601c495f00abe197b10d12b679f94badf3efe5fa365", "draft": {"model": "deepseek-flash", "finish_reason": "stop", "input_tokens": 1448, "output_tokens": 714, "cost_microdollars": 1292, "reservation_microdollars": 11544}, "verification": {"model": "jev-1.14.0", "input_tokens": 2555, "cost_microdollars": 108, "reservation_microdollars": 440, "error": null}, "claims": {"C1": {"kind": "claim", "statement": "OnceFunc returns a function that invokes f only once and may be called concurrently.", "line": 7, "fragment": "OnceFunc returns a function that invokes f only once.", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.6, "contradicted": 0.0, "unclear": 0.4}, "confidence": 0.4}}, "C2": {"kind": "claim", "statement": "If f panics, the function returned by OnceFunc panics with the same value on every call.", "line": 10, "fragment": "If f panics, the returned function will panic with the same value on every call.", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}, "confidence": 1.0}}, "C3": {"kind": "ordering", "statement": "After f is invoked inside once.Do, the deferred function sets d.f to nil, then recovers into d.p, and if d.valid is false, immediately panics with d.p.", "line": 25, "fragment": "d.p = recover()", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.72, "contradicted": 0.02, "unclear": 0.26}, "confidence": 0.58, "ordering_scope_probability": 0.04}}, "C4": {"kind": "ordering", "statement": "Within once.Do, d.valid is set to true only after d.f returns without panicking.", "line": 34, "fragment": "d.valid = true // Set only if f does not panic.", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.99, "contradicted": 0.0, "unclear": 0.01}, "confidence": 0.98, "ordering_scope_probability": 0.26}}, "C5": {"kind": "claim", "statement": "If d.valid is false when the wrapper resumes after once.Do, the wrapper panics with d.p.", "line": 37, "fragment": "panic(d.p)", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.93, "contradicted": 0.0, "unclear": 0.07}, "confidence": 0.89}}, "C6": {"kind": "claim", "statement": "OnceValue returns a function that invokes f only once and returns the value returned by f, and that returned function may be called concurrently.", "line": 42, "fragment": "OnceValue returns a function that invokes f only once and returns the value", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.73, "contradicted": 0.0, "unclear": 0.27}, "confidence": 0.6}}, "C7": {"kind": "claim", "statement": "If f panics, the function returned by OnceValue panics with the same value on every call.", "line": 45, "fragment": "If f panics, the returned function will panic with the same value on every call.", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}, "confidence": 1.0}}}, "questions": ["Does copying the function value returned by OnceFunc share the same once state, so that calling both copies invokes the original function only once?", "Do two separate OnceFunc calls wrapping the same function share one once state?", "When the original function panics, is the original function re-executed on subsequent calls, or is only the stored panic value re-raised without executing the original function again?", "If OnceValue returns a pointer, are later mutations of the pointed-to object visible through subsequent returns of that same pointer?", "Does reassigning only the caller function variable after constructing OnceFunc change which function the wrapper invokes?", "After recovering the first OnceFunc panic, does calling the wrapper again return normally, or does it panic with the same value again?", "Must the application retry an initialization function after every panic?", "Is the panic value stored for re-panicking on every subsequent call, or is the same stack trace reproduced each time?", "What does 'same value' mean when the recovered panic value itself is mutated after the first call?", "Are OnceValue and OnceValues specified to have identical panic/re-panic behavior to OnceFunc, and is concurrent-call behavior identical across all three?"], "review_required": true}