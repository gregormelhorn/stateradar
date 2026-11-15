For each check, judge only whether the quoted fragment explicitly supports, contradicts, or leaves unclear the exact statement. Context may identify the subject but cannot add missing event ordering, conditions or callee error contracts. Treat comments as comments, not guaranteed runtime behavior. Return JSON {"cases":[{"id":"...","choice":"supported|contradicted|unclear","reason":"..."}]} exactly once per check.
CHECKS:
[{"id": "A01", "kind": "claim", "statement": "The zero value of Value returns nil from Load.", "line": 12, "fragment": "The zero value for a Value returns nil from [Value.Load]."}, {"id": "A02", "kind": "claim", "statement": "The zero value of Value never returns nil from Load.", "line": 12, "fragment": "The zero value for a Value returns nil from [Value.Load]."}, {"id": "A03", "kind": "claim", "statement": "After Swap has initialized Value, Load is still guaranteed to return nil.", "line": 12, "fragment": "The zero value for a Value returns nil from [Value.Load]."}, {"id": "A04", "kind": "claim", "statement": "According to the quoted Load comment, Load returns nil if Store has never been called.", "line": 27, "fragment": "It returns nil if there has been no call to Store for this Value."}, {"id": "A05", "kind": "ordering", "statement": "Swap initializes Value, then Load is called, and Load must return nil because Store has never run.", "line": 27, "fragment": "It returns nil if there has been no call to Store for this Value."}]
SOURCE:
1: // Copyright 2014 The Go Authors. All rights reserved.
2: // Use of this source code is governed by a BSD-style
3: // license that can be found in the LICENSE file.
4: 
5: package atomic
6: 
7: import (
8: 	"unsafe"
9: )
10: 
11: // A Value provides an atomic load and store of a consistently typed value.
12: // The zero value for a Value returns nil from [Value.Load].
13: // Once [Value.Store] has been called, a Value must not be copied.
14: //
15: // A Value must not be copied after first use.
16: type Value struct {
17: 	v any
18: }
19: 
20: // efaceWords is interface{} internal representation.
21: type efaceWords struct {
22: 	typ  unsafe.Pointer
23: 	data unsafe.Pointer
24: }
25: 
26: // Load returns the value set by the most recent Store.
27: // It returns nil if there has been no call to Store for this Value.
28: func (v *Value) Load() (val any) {
29: 	vp := (*efaceWords)(unsafe.Pointer(v))
30: 	typ := LoadPointer(&vp.typ)
31: 	if typ == nil || typ == unsafe.Pointer(&firstStoreInProgress) {
32: 		// First store not yet completed.
33: 		return nil
34: 	}
35: 	data := LoadPointer(&vp.data)
36: 	vlp := (*efaceWords)(unsafe.Pointer(&val))
37: 	vlp.typ = typ
38: 	vlp.data = data
39: 	return
40: }
41: 
42: var firstStoreInProgress byte
43: 
44: // Store sets the value of the [Value] v to val.
45: // All calls to Store for a given Value must use values of the same concrete type.
46: // Store of an inconsistent type panics, as does Store(nil).
47: func (v *Value) Store(val any) {
48: 	if val == nil {
49: 		panic("sync/atomic: store of nil value into Value")
50: 	}
51: 	vp := (*efaceWords)(unsafe.Pointer(v))
52: 	vlp := (*efaceWords)(unsafe.Pointer(&val))
53: 	for {
54: 		typ := LoadPointer(&vp.typ)
55: 		if typ == nil {
56: 			// Attempt to start first store.
57: 			// Disable preemption so that other goroutines can use
58: 			// active spin wait to wait for completion.
59: 			runtime_procPin()
60: 			if !CompareAndSwapPointer(&vp.typ, nil, unsafe.Pointer(&firstStoreInProgress)) {
61: 				runtime_procUnpin()
62: 				continue
63: 			}
64: 			// Complete first store.
65: 			StorePointer(&vp.data, vlp.data)
66: 			StorePointer(&vp.typ, vlp.typ)
67: 			runtime_procUnpin()
68: 			return
69: 		}
70: 		if typ == unsafe.Pointer(&firstStoreInProgress) {
71: 			// First store in progress. Wait.
72: 			// Since we disable preemption around the first store,
73: 			// we can wait with active spinning.
74: 			continue
75: 		}
76: 		// First store completed. Check type and overwrite data.
77: 		if typ != vlp.typ {
78: 			panic("sync/atomic: store of inconsistently typed value into Value")
79: 		}
80: 		StorePointer(&vp.data, vlp.data)
81: 		return
82: 	}
83: }
84: 
85: // Swap stores new into Value and returns the previous value. It returns nil if
86: // the Value is empty.
87: //
88: // All calls to Swap for a given Value must use values of the same concrete
89: // type. Swap of an inconsistent type panics, as does Swap(nil).
90: func (v *Value) Swap(new any) (old any) {
91: 	if new == nil {
92: 		panic("sync/atomic: swap of nil value into Value")
93: 	}
94: 	vp := (*efaceWords)(unsafe.Pointer(v))
95: 	np := (*efaceWords)(unsafe.Pointer(&new))
96: 	for {
97: 		typ := LoadPointer(&vp.typ)
98: 		if typ == nil {
99: 			// Attempt to start first store.
100: 			// Disable preemption so that other goroutines can use
101: 			// active spin wait to wait for completion.
102: 			runtime_procPin()
103: 			if !CompareAndSwapPointer(&vp.typ, nil, unsafe.Pointer(&firstStoreInProgress)) {
104: 				runtime_procUnpin()
105: 				continue
106: 			}
107: 			// Complete first store.
108: 			StorePointer(&vp.data, np.data)
109: 			StorePointer(&vp.typ, np.typ)
110: 			runtime_procUnpin()
111: 			return nil
112: 		}
113: 		if typ == unsafe.Pointer(&firstStoreInProgress) {
114: 			// First store in progress. Wait.
115: 			// Since we disable preemption around the first store,
116: 			// we can wait with active spinning.
117: 			continue
118: 		}
119: 		// First store completed. Check type and overwrite data.
120: 		if typ != np.typ {
121: 			panic("sync/atomic: swap of inconsistently typed value into Value")
122: 		}
123: 		op := (*efaceWords)(unsafe.Pointer(&old))
124: 		op.typ, op.data = np.typ, SwapPointer(&vp.data, np.data)
125: 		return old
126: 	}
127: }
128: 
129: // CompareAndSwap executes the compare-and-swap operation for the [Value].
130: //
131: // All calls to CompareAndSwap for a given Value must use values of the same
132: // concrete type. CompareAndSwap of an inconsistent type panics, as does
133: // CompareAndSwap(old, nil).
134: func (v *Value) CompareAndSwap(old, new any) (swapped bool) {
135: 	if new == nil {
136: 		panic("sync/atomic: compare and swap of nil value into Value")
137: 	}
138: 	vp := (*efaceWords)(unsafe.Pointer(v))
139: 	np := (*efaceWords)(unsafe.Pointer(&new))
140: 	op := (*efaceWords)(unsafe.Pointer(&old))
141: 	if op.typ != nil && np.typ != op.typ {
142: 		panic("sync/atomic: compare and swap of inconsistently typed values")
143: 	}
144: 	for {
145: 		typ := LoadPointer(&vp.typ)
146: 		if typ == nil {
147: 			if old != nil {
148: 				return false
149: 			}
150: 			// Attempt to start first store.
151: 			// Disable preemption so that other goroutines can use
152: 			// active spin wait to wait for completion.
153: 			runtime_procPin()
154: 			if !CompareAndSwapPointer(&vp.typ, nil, unsafe.Pointer(&firstStoreInProgress)) {
155: 				runtime_procUnpin()
156: 				continue
157: 			}
158: 			// Complete first store.
159: 			StorePointer(&vp.data, np.data)
160: 			StorePointer(&vp.typ, np.typ)
161: 			runtime_procUnpin()
162: 			return true
163: 		}
164: 		if typ == unsafe.Pointer(&firstStoreInProgress) {
165: 			// First store in progress. Wait.
166: 			// Since we disable preemption around the first store,
167: 			// we can wait with active spinning.
168: 			continue
169: 		}
170: 		// First store completed. Check type and overwrite data.
171: 		if typ != np.typ {
172: 			panic("sync/atomic: compare and swap of inconsistently typed value into Value")
173: 		}
174: 		// Compare old and current via runtime equality check.
175: 		// This allows value types to be compared, something
176: 		// not offered by the package functions.
177: 		// CompareAndSwapPointer below only ensures vp.data
178: 		// has not changed since LoadPointer.
179: 		data := LoadPointer(&vp.data)
180: 		var i any
181: 		(*efaceWords)(unsafe.Pointer(&i)).typ = typ
182: 		(*efaceWords)(unsafe.Pointer(&i)).data = data
183: 		if i != old {
184: 			return false
185: 		}
186: 		return CompareAndSwapPointer(&vp.data, data, np.data)
187: 	}
188: }
189: 
190: // Disable/enable preemption, implemented in runtime.
191: func runtime_procPin() int
192: func runtime_procUnpin()