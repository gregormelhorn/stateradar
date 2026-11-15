Independently classify each check using ONLY whether its quoted fragment explicitly supports, contradicts, or leaves unclear the exact statement. Surrounding source may clarify meaning, but cannot add unquoted material conditions, actors, events, ordering or outcomes. For ordering, every material detail must be contemplated by the fragment; an unmentioned ordering is unclear. Treat code comments as quoted statements, not automatically as runtime behavior. A call site does not establish the callee error contract. Do not decide domain policy. You receive no proposed labels or Jev results. Return JSON {"cases":[{"id":"...","verdict":"supported|contradicted|unclear","reason":"..."}]} with every id exactly once.
CHECKS:
[{"id": "B01", "kind": "claim", "statement": "At the start of Buffer.Read, lastRead is assigned opInvalid.", "line": 337, "fragment": "b.lastRead = opInvalid"}, {"id": "B02", "kind": "claim", "statement": "At the start of Buffer.Read, lastRead is assigned opRead.", "line": 337, "fragment": "b.lastRead = opInvalid"}, {"id": "B03", "kind": "claim", "statement": "The cited assignment guarantees that the buffer can never contain unread bytes.", "line": 337, "fragment": "b.lastRead = opInvalid"}, {"id": "B04", "kind": "ordering", "statement": "After a ReadByte succeeds, Read(nil) occurs and then UnreadByte succeeds.", "line": 337, "fragment": "b.lastRead = opInvalid"}, {"id": "B05", "kind": "claim", "statement": "Buffer.ReadByte returns io.EOF when no byte is available.", "line": 373, "fragment": "If no byte is available, it returns error [io.EOF]."}]
SOURCE:
1: // Copyright 2009 The Go Authors. All rights reserved.
2: // Use of this source code is governed by a BSD-style
3: // license that can be found in the LICENSE file.
4: 
5: package bytes
6: 
7: // Simple byte buffer for marshaling data.
8: 
9: import (
10: 	"errors"
11: 	"io"
12: 	"unicode/utf8"
13: )
14: 
15: // smallBufferSize is an initial allocation minimal capacity.
16: const smallBufferSize = 64
17: 
18: // A Buffer is a variable-sized buffer of bytes with [Buffer.Read] and [Buffer.Write] methods.
19: // The zero value for Buffer is an empty buffer ready to use.
20: type Buffer struct {
21: 	buf      []byte // contents are the bytes buf[off : len(buf)]
22: 	off      int    // read at &buf[off], write at &buf[len(buf)]
23: 	lastRead readOp // last read operation, so that Unread* can work correctly.
24: 
25: 	// Copying and modifying a non-zero Buffer is prone to error,
26: 	// but we cannot employ the noCopy trick used by WaitGroup and Mutex,
27: 	// which causes vet's copylocks checker to report misuse, as vet
28: 	// cannot reliably distinguish the zero and non-zero cases.
29: 	// See #26462, #25907, #47276, #48398 for history.
30: }
31: 
32: // The readOp constants describe the last action performed on
33: // the buffer, so that UnreadRune and UnreadByte can check for
34: // invalid usage. opReadRuneX constants are chosen such that
35: // converted to int they correspond to the rune size that was read.
36: type readOp int8
37: 
38: // Don't use iota for these, as the values need to correspond with the
39: // names and comments, which is easier to see when being explicit.
40: const (
41: 	opRead      readOp = -1 // Any other read operation.
42: 	opInvalid   readOp = 0  // Non-read operation.
43: 	opReadRune1 readOp = 1  // Read rune of size 1.
44: 	opReadRune2 readOp = 2  // Read rune of size 2.
45: 	opReadRune3 readOp = 3  // Read rune of size 3.
46: 	opReadRune4 readOp = 4  // Read rune of size 4.
47: )
48: 
49: // ErrTooLarge is passed to panic if memory cannot be allocated to store data in a buffer.
50: var ErrTooLarge = errors.New("bytes.Buffer: too large")
51: var errNegativeRead = errors.New("bytes.Buffer: reader returned negative count from Read")
52: 
53: const maxInt = int(^uint(0) >> 1)
54: 
55: // Bytes returns a slice of length b.Len() holding the unread portion of the buffer.
56: // The slice is valid for use only until the next buffer modification (that is,
57: // only until the next call to a method like [Buffer.Read], [Buffer.Write], [Buffer.Reset], or [Buffer.Truncate]).
58: // The slice aliases the buffer content at least until the next buffer modification,
59: // so immediate changes to the slice will affect the result of future reads.
60: func (b *Buffer) Bytes() []byte { return b.buf[b.off:] }
61: 
62: // AvailableBuffer returns an empty buffer with b.Available() capacity.
63: // This buffer is intended to be appended to and
64: // passed to an immediately succeeding [Buffer.Write] call.
65: // The buffer is only valid until the next write operation on b.
66: func (b *Buffer) AvailableBuffer() []byte { return b.buf[len(b.buf):] }
67: 
68: // String returns the contents of the unread portion of the buffer
69: // as a string. If the [Buffer] is a nil pointer, it returns "<nil>".
70: //
71: // To build strings more efficiently, see the [strings.Builder] type.
72: func (b *Buffer) String() string {
73: 	if b == nil {
74: 		// Special case, useful in debugging.
75: 		return "<nil>"
76: 	}
77: 	return string(b.buf[b.off:])
78: }
79: 
80: // Peek returns the next n bytes without advancing the buffer.
81: // If Peek returns fewer than n bytes, it also returns [io.EOF].
82: // The slice is only valid until the next call to a read or write method.
83: // The slice aliases the buffer content at least until the next buffer modification,
84: // so immediate changes to the slice will affect the result of future reads.
85: func (b *Buffer) Peek(n int) ([]byte, error) {
86: 	if b.Len() < n {
87: 		return b.buf[b.off:], io.EOF
88: 	}
89: 	return b.buf[b.off : b.off+n], nil
90: }
91: 
92: // empty reports whether the unread portion of the buffer is empty.
93: func (b *Buffer) empty() bool { return len(b.buf) <= b.off }
94: 
95: // Len returns the number of bytes of the unread portion of the buffer;
96: // b.Len() == len(b.Bytes()).
97: func (b *Buffer) Len() int { return len(b.buf) - b.off }
98: 
99: // Cap returns the capacity of the buffer's underlying byte slice, that is, the
100: // total space allocated for the buffer's data.
101: func (b *Buffer) Cap() int { return cap(b.buf) }
102: 
103: // Available returns how many bytes are unused in the buffer.
104: func (b *Buffer) Available() int { return cap(b.buf) - len(b.buf) }
105: 
106: // Truncate discards all but the first n unread bytes from the buffer
107: // but continues to use the same allocated storage.
108: // It panics if n is negative or greater than the length of the buffer.
109: func (b *Buffer) Truncate(n int) {
110: 	if n == 0 {
111: 		b.Reset()
112: 		return
113: 	}
114: 	b.lastRead = opInvalid
115: 	if n < 0 || n > b.Len() {
116: 		panic("bytes.Buffer: truncation out of range")
117: 	}
118: 	b.buf = b.buf[:b.off+n]
119: }
120: 
121: // Reset resets the buffer to be empty,
122: // but it retains the underlying storage for use by future writes.
123: // Reset is the same as [Buffer.Truncate](0).
124: func (b *Buffer) Reset() {
125: 	b.buf = b.buf[:0]
126: 	b.off = 0
127: 	b.lastRead = opInvalid
128: }
129: 
130: // tryGrowByReslice is an inlineable version of grow for the fast-case where the
131: // internal buffer only needs to be resliced.
132: // It returns the index where bytes should be written and whether it succeeded.
133: func (b *Buffer) tryGrowByReslice(n int) (int, bool) {
134: 	if l := len(b.buf); n <= cap(b.buf)-l {
135: 		b.buf = b.buf[:l+n]
136: 		return l, true
137: 	}
138: 	return 0, false
139: }
140: 
141: // grow grows the buffer to guarantee space for n more bytes.
142: // It returns the index where bytes should be written.
143: // If the buffer can't grow it will panic with ErrTooLarge.
144: func (b *Buffer) grow(n int) int {
145: 	m := b.Len()
146: 	// If buffer is empty, reset to recover space.
147: 	if m == 0 && b.off != 0 {
148: 		b.Reset()
149: 	}
150: 	// Try to grow by means of a reslice.
151: 	if i, ok := b.tryGrowByReslice(n); ok {
152: 		return i
153: 	}
154: 	if b.buf == nil && n <= smallBufferSize {
155: 		b.buf = make([]byte, n, smallBufferSize)
156: 		return 0
157: 	}
158: 	c := cap(b.buf)
159: 	if n <= c/2-m {
160: 		// We can slide things down instead of allocating a new
161: 		// slice. We only need m+n <= c to slide, but
162: 		// we instead let capacity get twice as large so we
163: 		// don't spend all our time copying.
164: 		copy(b.buf, b.buf[b.off:])
165: 	} else if c > maxInt-c-n {
166: 		panic(ErrTooLarge)
167: 	} else {
168: 		// Add b.off to account for b.buf[:b.off] being sliced off the front.
169: 		b.buf = growSlice(b.buf[b.off:], b.off+n)
170: 	}
171: 	// Restore b.off and len(b.buf).
172: 	b.off = 0
173: 	b.buf = b.buf[:m+n]
174: 	return m
175: }
176: 
177: // Grow grows the buffer's capacity, if necessary, to guarantee space for
178: // another n bytes. After Grow(n), at least n bytes can be written to the
179: // buffer without another allocation.
180: // If n is negative, Grow will panic.
181: // If the buffer can't grow it will panic with [ErrTooLarge].
182: func (b *Buffer) Grow(n int) {
183: 	if n < 0 {
184: 		panic("bytes.Buffer.Grow: negative count")
185: 	}
186: 	m := b.grow(n)
187: 	b.buf = b.buf[:m]
188: }
189: 
190: // Write appends the contents of p to the buffer, growing the buffer as
191: // needed. The return value n is the length of p; err is always nil. If the
192: // buffer becomes too large, Write will panic with [ErrTooLarge].
193: func (b *Buffer) Write(p []byte) (n int, err error) {
194: 	b.lastRead = opInvalid
195: 	m, ok := b.tryGrowByReslice(len(p))
196: 	if !ok {
197: 		m = b.grow(len(p))
198: 	}
199: 	return copy(b.buf[m:], p), nil
200: }
201: 
202: // WriteString appends the contents of s to the buffer, growing the buffer as
203: // needed. The return value n is the length of s; err is always nil. If the
204: // buffer becomes too large, WriteString will panic with [ErrTooLarge].
205: func (b *Buffer) WriteString(s string) (n int, err error) {
206: 	b.lastRead = opInvalid
207: 	m, ok := b.tryGrowByReslice(len(s))
208: 	if !ok {
209: 		m = b.grow(len(s))
210: 	}
211: 	return copy(b.buf[m:], s), nil
212: }
213: 
214: // MinRead is the minimum slice size passed to a [Buffer.Read] call by
215: // [Buffer.ReadFrom]. As long as the [Buffer] has at least MinRead bytes beyond
216: // what is required to hold the contents of r, [Buffer.ReadFrom] will not grow the
217: // underlying buffer.
218: const MinRead = 512
219: 
220: // ReadFrom reads data from r until EOF and appends it to the buffer, growing
221: // the buffer as needed. The return value n is the number of bytes read. Any
222: // error except io.EOF encountered during the read is also returned. If the
223: // buffer becomes too large, ReadFrom will panic with [ErrTooLarge].
224: func (b *Buffer) ReadFrom(r io.Reader) (n int64, err error) {
225: 	b.lastRead = opInvalid
226: 	for {
227: 		i := b.grow(MinRead)
228: 		b.buf = b.buf[:i]
229: 		m, e := r.Read(b.buf[i:cap(b.buf)])
230: 		if m < 0 {
231: 			panic(errNegativeRead)
232: 		}
233: 
234: 		b.buf = b.buf[:i+m]
235: 		n += int64(m)
236: 		if e == io.EOF {
237: 			return n, nil // e is EOF, so return nil explicitly
238: 		}
239: 		if e != nil {
240: 			return n, e
241: 		}
242: 	}
243: }
244: 
245: // growSlice grows b by n, preserving the original content of b.
246: // If the allocation fails, it panics with ErrTooLarge.
247: func growSlice(b []byte, n int) []byte {
248: 	defer func() {
249: 		if recover() != nil {
250: 			panic(ErrTooLarge)
251: 		}
252: 	}()
253: 	// TODO(http://golang.org/issue/51462): We should rely on the append-make
254: 	// pattern so that the compiler can call runtime.growslice. For example:
255: 	//	return append(b, make([]byte, n)...)
256: 	// This avoids unnecessary zero-ing of the first len(b) bytes of the
257: 	// allocated slice, but this pattern causes b to escape onto the heap.
258: 	//
259: 	// Instead use the append-make pattern with a nil slice to ensure that
260: 	// we allocate buffers rounded up to the closest size class.
261: 	c := len(b) + n // ensure enough space for n elements
262: 	if c < 2*cap(b) {
263: 		// The growth rate has historically always been 2x. In the future,
264: 		// we could rely purely on append to determine the growth rate.
265: 		c = 2 * cap(b)
266: 	}
267: 	b2 := append([]byte(nil), make([]byte, c)...)
268: 	i := copy(b2, b)
269: 	return b2[:i]
270: }
271: 
272: // WriteTo writes data to w until the buffer is drained or an error occurs.
273: // The return value n is the number of bytes written; it always fits into an
274: // int, but it is int64 to match the [io.WriterTo] interface. Any error
275: // encountered during the write is also returned.
276: func (b *Buffer) WriteTo(w io.Writer) (n int64, err error) {
277: 	b.lastRead = opInvalid
278: 	if nBytes := b.Len(); nBytes > 0 {
279: 		m, e := w.Write(b.buf[b.off:])
280: 		if m > nBytes {
281: 			panic("bytes.Buffer.WriteTo: invalid Write count")
282: 		}
283: 		b.off += m
284: 		n = int64(m)
285: 		if e != nil {
286: 			return n, e
287: 		}
288: 		// all bytes should have been written, by definition of
289: 		// Write method in io.Writer
290: 		if m != nBytes {
291: 			return n, io.ErrShortWrite
292: 		}
293: 	}
294: 	// Buffer is now empty; reset.
295: 	b.Reset()
296: 	return n, nil
297: }
298: 
299: // WriteByte appends the byte c to the buffer, growing the buffer as needed.
300: // The returned error is always nil, but is included to match [bufio.Writer]'s
301: // WriteByte. If the buffer becomes too large, WriteByte will panic with
302: // [ErrTooLarge].
303: func (b *Buffer) WriteByte(c byte) error {
304: 	b.lastRead = opInvalid
305: 	m, ok := b.tryGrowByReslice(1)
306: 	if !ok {
307: 		m = b.grow(1)
308: 	}
309: 	b.buf[m] = c
310: 	return nil
311: }
312: 
313: // WriteRune appends the UTF-8 encoding of Unicode code point r to the
314: // buffer, returning the number of bytes written and a nil error. The nil
315: // error is included to match [bufio.Writer]'s WriteRune. The buffer is grown
316: // as needed; if it becomes too large, WriteRune will panic with [ErrTooLarge].
317: func (b *Buffer) WriteRune(r rune) (n int, err error) {
318: 	// Compare as uint32 to correctly handle negative runes.
319: 	if uint32(r) < utf8.RuneSelf {
320: 		b.WriteByte(byte(r))
321: 		return 1, nil
322: 	}
323: 	b.lastRead = opInvalid
324: 	m, ok := b.tryGrowByReslice(utf8.UTFMax)
325: 	if !ok {
326: 		m = b.grow(utf8.UTFMax)
327: 	}
328: 	b.buf = utf8.AppendRune(b.buf[:m], r)
329: 	return len(b.buf) - m, nil
330: }
331: 
332: // Read reads the next len(p) bytes from the buffer or until the buffer
333: // is drained. The return value n is the number of bytes read. If the
334: // buffer has no data to return, err is [io.EOF] (unless len(p) is zero);
335: // otherwise it is nil.
336: func (b *Buffer) Read(p []byte) (n int, err error) {
337: 	b.lastRead = opInvalid
338: 	if b.empty() {
339: 		// Buffer is empty, reset to recover space.
340: 		b.Reset()
341: 		if len(p) == 0 {
342: 			return 0, nil
343: 		}
344: 		return 0, io.EOF
345: 	}
346: 	n = copy(p, b.buf[b.off:])
347: 	b.off += n
348: 	if n > 0 {
349: 		b.lastRead = opRead
350: 	}
351: 	return n, nil
352: }
353: 
354: // Next returns a slice containing the next n bytes from the buffer,
355: // advancing the buffer as if the bytes had been returned by [Buffer.Read].
356: // If there are fewer than n bytes in the buffer, Next returns the entire buffer.
357: // The slice is only valid until the next call to a read or write method.
358: func (b *Buffer) Next(n int) []byte {
359: 	b.lastRead = opInvalid
360: 	m := b.Len()
361: 	if n > m {
362: 		n = m
363: 	}
364: 	data := b.buf[b.off : b.off+n]
365: 	b.off += n
366: 	if n > 0 {
367: 		b.lastRead = opRead
368: 	}
369: 	return data
370: }
371: 
372: // ReadByte reads and returns the next byte from the buffer.
373: // If no byte is available, it returns error [io.EOF].
374: func (b *Buffer) ReadByte() (byte, error) {
375: 	if b.empty() {
376: 		// Buffer is empty, reset to recover space.
377: 		b.Reset()
378: 		return 0, io.EOF
379: 	}
380: 	c := b.buf[b.off]
381: 	b.off++
382: 	b.lastRead = opRead
383: 	return c, nil
384: }
385: 
386: // ReadRune reads and returns the next UTF-8-encoded
387: // Unicode code point from the buffer.
388: // If no bytes are available, the error returned is io.EOF.
389: // If the bytes are an erroneous UTF-8 encoding, it
390: // consumes one byte and returns U+FFFD, 1.
391: func (b *Buffer) ReadRune() (r rune, size int, err error) {
392: 	if b.empty() {
393: 		// Buffer is empty, reset to recover space.
394: 		b.Reset()
395: 		return 0, 0, io.EOF
396: 	}
397: 	c := b.buf[b.off]
398: 	if c < utf8.RuneSelf {
399: 		b.off++
400: 		b.lastRead = opReadRune1
401: 		return rune(c), 1, nil
402: 	}
403: 	r, n := utf8.DecodeRune(b.buf[b.off:])
404: 	b.off += n
405: 	b.lastRead = readOp(n)
406: 	return r, n, nil
407: }
408: 
409: // UnreadRune unreads the last rune returned by [Buffer.ReadRune].
410: // If the most recent read or write operation on the buffer was
411: // not a successful [Buffer.ReadRune], UnreadRune returns an error.  (In this regard
412: // it is stricter than [Buffer.UnreadByte], which will unread the last byte
413: // from any read operation.)
414: func (b *Buffer) UnreadRune() error {
415: 	if b.lastRead <= opInvalid {
416: 		return errors.New("bytes.Buffer: UnreadRune: previous operation was not a successful ReadRune")
417: 	}
418: 	if b.off >= int(b.lastRead) {
419: 		b.off -= int(b.lastRead)
420: 	}
421: 	b.lastRead = opInvalid
422: 	return nil
423: }
424: 
425: var errUnreadByte = errors.New("bytes.Buffer: UnreadByte: previous operation was not a successful read")
426: 
427: // UnreadByte unreads the last byte returned by the most recent successful
428: // read operation that read at least one byte. If a write has happened since
429: // the last read, if the last read returned an error, or if the read read zero
430: // bytes, UnreadByte returns an error.
431: func (b *Buffer) UnreadByte() error {
432: 	if b.lastRead == opInvalid {
433: 		return errUnreadByte
434: 	}
435: 	b.lastRead = opInvalid
436: 	if b.off > 0 {
437: 		b.off--
438: 	}
439: 	return nil
440: }
441: 
442: // ReadBytes reads until the first occurrence of delim in the input,
443: // returning a slice containing the data up to and including the delimiter.
444: // If ReadBytes encounters an error before finding a delimiter,
445: // it returns the data read before the error and the error itself (often [io.EOF]).
446: // ReadBytes returns err != nil if and only if the returned data does not end in
447: // delim.
448: func (b *Buffer) ReadBytes(delim byte) (line []byte, err error) {
449: 	slice, err := b.readSlice(delim)
450: 	// return a copy of slice. The buffer's backing array may
451: 	// be overwritten by later calls.
452: 	line = append(line, slice...)
453: 	return line, err
454: }
455: 
456: // readSlice is like ReadBytes but returns a reference to internal buffer data.
457: func (b *Buffer) readSlice(delim byte) (line []byte, err error) {
458: 	i := IndexByte(b.buf[b.off:], delim)
459: 	end := b.off + i + 1
460: 	if i < 0 {
461: 		end = len(b.buf)
462: 		err = io.EOF
463: 	}
464: 	line = b.buf[b.off:end]
465: 	b.off = end
466: 	b.lastRead = opRead
467: 	return line, err
468: }
469: 
470: // ReadString reads until the first occurrence of delim in the input,
471: // returning a string containing the data up to and including the delimiter.
472: // If ReadString encounters an error before finding a delimiter,
473: // it returns the data read before the error and the error itself (often [io.EOF]).
474: // ReadString returns err != nil if and only if the returned data does not end
475: // in delim.
476: func (b *Buffer) ReadString(delim byte) (line string, err error) {
477: 	slice, err := b.readSlice(delim)
478: 	return string(slice), err
479: }
480: 
481: // NewBuffer creates and initializes a new [Buffer] using buf as its
482: // initial contents. The new [Buffer] takes ownership of buf, and the
483: // caller should not use buf after this call. NewBuffer is intended to
484: // prepare a [Buffer] to read existing data. It can also be used to set
485: // the initial size of the internal buffer for writing. To do that,
486: // buf should have the desired capacity but a length of zero.
487: //
488: // In most cases, new([Buffer]) (or just declaring a [Buffer] variable) is
489: // sufficient to initialize a [Buffer].
490: func NewBuffer(buf []byte) *Buffer { return &Buffer{buf: buf} }
491: 
492: // NewBufferString creates and initializes a new [Buffer] using string s as its
493: // initial contents. It is intended to prepare a buffer to read an existing
494: // string.
495: //
496: // In most cases, new([Buffer]) (or just declaring a [Buffer] variable) is
497: // sufficient to initialize a [Buffer].
498: func NewBufferString(s string) *Buffer {
499: 	return &Buffer{buf: []byte(s)}
500: }