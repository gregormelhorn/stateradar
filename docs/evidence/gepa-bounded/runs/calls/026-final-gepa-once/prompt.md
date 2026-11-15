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
IMMUTABLE BASELINE:
{"findings": [{"id": "once-01", "verdict": "supported", "line": 22, "fragment": "d.once.Do(func() {", "reason": "Both copies refer to the same returned closure and use its captured d.once, so invoking both executes the original function only once.", "question": ""}, {"id": "once-02", "verdict": "contradicted", "line": 13, "fragment": "d := struct {", "reason": "Each OnceFunc call creates its own d with its own Once field, even when both calls receive the same f.", "question": ""}, {"id": "once-03", "verdict": "supported", "line": 10, "fragment": "If f panics, the returned function will panic with the same value on every call.", "reason": "The wrapper invokes f only once, saves the recovered panic value in d.p, and uses that value for subsequent panics.", "question": ""}, {"id": "once-04", "verdict": "supported", "line": 72, "fragment": "return d.result", "reason": "The wrapper stores f's result once and returns it directly. A stored pointer still points to the same object, so later mutations are visible through it.", "question": ""}, {"id": "once-05", "verdict": "contradicted", "line": 19, "fragment": "f: f,", "reason": "OnceFunc stores the function value supplied at construction and invokes that stored value. Reassigning the caller's variable does not change the stored value.", "question": ""}, {"id": "once-06", "verdict": "contradicted", "line": 10, "fragment": "will panic with the same value on every call.", "reason": "The contract requires a panic on every call after f panics, including calls made after the caller recovers the first panic.", "question": ""}, {"id": "once-07", "verdict": "unspecified", "line": 7, "fragment": "OnceFunc returns a function that invokes f only once.", "reason": "The contract governs calls to the returned wrapper and leaves application retry policy unspecified.", "question": "OPEN: Must the application retry an initialization function after every panic, or is retry unspecified by the source?"}], "corrections": []}
REVIEW INSTRUCTIONS:
Keep ordinary success, failure, cancellation, and repeated-call controls, including actions created after cancellation. Trace each distinct creation through use and cleanup. Cite where references are captured or resolved later, state the starting objects and event order, and attribute each check and effect to the object it reaches. Distinguish return values, their causes, and when deferred work starts or finishes. Where permitted, test unchanged identity, copying, replacement, wrapper or key mutation, and caller-local rebinding separately. Verify identity with evidence beyond matching generation values and account for stable captures and identity guards. Cite documented exclusions and mark unanswered policy questions OPEN.