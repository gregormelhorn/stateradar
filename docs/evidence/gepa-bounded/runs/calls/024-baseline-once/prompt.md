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
{"source": "upstream/once/oncefunc.go", "source_sha256": "0853c1ad885c593d2810e601c495f00abe197b10d12b679f94badf3efe5fa365", "draft": {"model": "deepseek-flash", "finish_reason": "stop", "input_tokens": 1448, "output_tokens": 590, "cost_microdollars": 1143, "reservation_microdollars": 11544}, "verification": {"model": "jev-1.14.0", "input_tokens": 2301, "cost_microdollars": 97, "reservation_microdollars": 392, "error": null}, "claims": {"C1": {"kind": "claim", "statement": "OnceFunc returns a function that invokes f only once, and the returned function may be called concurrently.", "line": 7, "fragment": "returns a function that invokes f only once", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.74, "contradicted": 0.0, "unclear": 0.26}, "confidence": 0.61}}, "C2": {"kind": "claim", "statement": "If f panics, the function returned by OnceFunc will panic with the same value on every call.", "line": 10, "fragment": "will panic with the same value on every call", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}, "confidence": 1.0}}, "C3": {"kind": "claim", "statement": "The wrapper sets d.f to nil after invoking it, to avoid keeping f alive after invoking it.", "line": 24, "fragment": "d.f = nil // Do not keep f alive after invoking it.", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}, "confidence": 1.0}}, "C4": {"kind": "claim", "statement": "The valid flag is set only if f does not panic.", "line": 34, "fragment": "d.valid = true // Set only if f does not panic.", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}, "confidence": 1.0}}, "C5": {"kind": "ordering", "statement": "On the first call, if f panics, the deferred function re-panics immediately so the user gets a complete stack trace into f.", "line": 27, "fragment": "Re-panic immediately so on the first", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}, "confidence": 1.0, "ordering_scope_probability": 0.09}}, "C6": {"kind": "claim", "statement": "If valid is false when the wrapper checks it, the wrapper panics with d.p.", "line": 36, "fragment": "if !d.valid {", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 0.99, "contradicted": 0.0, "unclear": 0.01}, "confidence": 0.98}}, "C7": {"kind": "claim", "statement": "For OnceValue, if f panics, the returned function will panic with the same value on every call.", "line": 45, "fragment": "will panic with the same value on every call", "citation_check": "ok", "jev": {"choice": "supported", "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}, "confidence": 1.0}}}, "questions": ["What observable behavior results from copying the function returned by OnceFunc\u2014does sharing of the internal once state persist across copies?", "Do two separate OnceFunc calls wrapping the same function share any state, or are they independent?", "Can the original function execute again after a panic, or does the implementation permanently prevent re-execution?", "Are mutations to a pointer returned by OnceValue visible through subsequent calls to the same returned function, and is the same pointer returned each time?", "Does reassigning the caller's function variable after constructing OnceFunc change which function the wrapper invokes, given the wrapper captured f at construction?", "After recovering the first OnceFunc panic, does a subsequent call return normally or re-panic?", "Must the application retry an initialization function after every panic, or is retry unspecified by the source?"], "review_required": true}