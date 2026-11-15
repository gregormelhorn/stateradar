Inspect the source for significant behavior, edge cases, event ordering and contract limitations. Return JSON with exactly one key findings, an array of at most six entries. Each entry has a unique id, text describing the exact starting conditions, ordered events and observable result, a citation object {line: integer, fragment: exact substring of that line}, and question: either an OPEN: question where intent or source wording is unclear, or an empty string. Include supported ordinary controls as appropriate. Do not assume a surprising behavior is intended. Return JSON only.

REVIEW PARAGRAPH:
Examine ordinary success and failure as well as repeated operations, deferred work, cancellation and both event orderings. Trace state, object identity and effects across each lifecycle boundary. Compare contract language with behavior, including its exclusions and the possibility that a valid statement applies only to a narrower situation. Retain correct controls. Cite evidence and leave unanswered intent or contradictory requirements as OPEN questions.

SOURCE:
1: // Copyright 2013 The Go Authors. All rights reserved.
2: // Use of this source code is governed by a BSD-style
3: // license that can be found in the LICENSE file.
4: 
5: package bufio
6: 
7: import (
8: 	"bytes"
9: 	"errors"
10: 	"io"
11: 	"unicode/utf8"
12: )
13: 
14: // Scanner provides a convenient interface for reading data such as
15: // a file of newline-delimited lines of text. Successive calls to
16: // the [Scanner.Scan] method will step through the 'tokens' of a file, skipping
17: // the bytes between the tokens. The specification of a token is
18: // defined by a split function of type [SplitFunc]; the default split
19: // function breaks the input into lines with line termination stripped. [Scanner.Split]
20: // functions are defined in this package for scanning a file into
21: // lines, bytes, UTF-8-encoded runes, and space-delimited words. The
22: // client may instead provide a custom split function.
23: //
24: // Scanning stops unrecoverably at EOF, the first I/O error, or a token too
25: // large to fit in the [Scanner.Buffer]. When a scan stops, the reader may have
26: // advanced arbitrarily far past the last token. Programs that need more
27: // control over error handling or large tokens, or must run sequential scans
28: // on a reader, should use [bufio.Reader] instead.
29: type Scanner struct {
30: 	r            io.Reader // The reader provided by the client.
31: 	split        SplitFunc // The function to split the tokens.
32: 	maxTokenSize int       // Maximum size of a token; modified by tests.
33: 	token        []byte    // Last token returned by split.
34: 	buf          []byte    // Buffer used as argument to split.
35: 	start        int       // First non-processed byte in buf.
36: 	end          int       // End of data in buf.
37: 	err          error     // Sticky error.
38: 	empties      int       // Count of successive empty tokens.
39: 	scanCalled   bool      // Scan has been called; buffer is in use.
40: 	done         bool      // Scan has finished.
41: }
42: 
43: // SplitFunc is the signature of the split function used to tokenize the
44: // input. The arguments are an initial substring of the remaining unprocessed
45: // data and a flag, atEOF, that reports whether the [Reader] has no more data
46: // to give. The return values are the number of bytes to advance the input
47: // and the next token to return to the user, if any, plus an error, if any.
48: //
49: // Scanning stops if the function returns an error, in which case some of
50: // the input may be discarded. If that error is [ErrFinalToken], scanning
51: // stops with no error. A non-nil token delivered with [ErrFinalToken]
52: // will be the last token, and a nil token with [ErrFinalToken]
53: // immediately stops the scanning.
54: //
55: // Otherwise, the [Scanner] advances the input. If the token is not nil,
56: // the [Scanner] returns it to the user. If the token is nil, the
57: // Scanner reads more data and continues scanning; if there is no more
58: // data--if atEOF was true--the [Scanner] returns. If the data does not
59: // yet hold a complete token, for instance if it has no newline while
60: // scanning lines, a [SplitFunc] can return (0, nil, nil) to signal the
61: // [Scanner] to read more data into the slice and try again with a
62: // longer slice starting at the same point in the input.
63: //
64: // The function is never called with an empty data slice unless atEOF
65: // is true. If atEOF is true, however, data may be non-empty and,
66: // as always, holds unprocessed text.
67: type SplitFunc func(data []byte, atEOF bool) (advance int, token []byte, err error)
68: 
69: // Errors returned by Scanner.
70: var (
71: 	ErrTooLong         = errors.New("bufio.Scanner: token too long")
72: 	ErrNegativeAdvance = errors.New("bufio.Scanner: SplitFunc returns negative advance count")
73: 	ErrAdvanceTooFar   = errors.New("bufio.Scanner: SplitFunc returns advance count beyond input")
74: 	ErrBadReadCount    = errors.New("bufio.Scanner: Read returned impossible count")
75: )
76: 
77: const (
78: 	// MaxScanTokenSize is the maximum size used to buffer a token
79: 	// unless the user provides an explicit buffer with [Scanner.Buffer].
80: 	// The actual maximum token size may be smaller as the buffer
81: 	// may need to include, for instance, a newline.
82: 	MaxScanTokenSize = 64 * 1024
83: 
84: 	startBufSize = 4096 // Size of initial allocation for buffer.
85: )
86: 
87: // NewScanner returns a new [Scanner] to read from r.
88: // The split function defaults to [ScanLines].
89: func NewScanner(r io.Reader) *Scanner {
90: 	return &Scanner{
91: 		r:            r,
92: 		split:        ScanLines,
93: 		maxTokenSize: MaxScanTokenSize,
94: 	}
95: }
96: 
97: // Err returns the first non-EOF error that was encountered by the [Scanner].
98: func (s *Scanner) Err() error {
99: 	if s.err == io.EOF {
100: 		return nil
101: 	}
102: 	return s.err
103: }
104: 
105: // Bytes returns the most recent token generated by a call to [Scanner.Scan].
106: // The underlying array may point to data that will be overwritten
107: // by a subsequent call to Scan. It does no allocation.
108: func (s *Scanner) Bytes() []byte {
109: 	return s.token
110: }
111: 
112: // Text returns the most recent token generated by a call to [Scanner.Scan]
113: // as a newly allocated string holding its bytes.
114: func (s *Scanner) Text() string {
115: 	return string(s.token)
116: }
117: 
118: // ErrFinalToken is a special sentinel error value. It is intended to be
119: // returned by a Split function to indicate that the scanning should stop
120: // with no error. If the token being delivered with this error is not nil,
121: // the token is the last token.
122: //
123: // The value is useful to stop processing early or when it is necessary to
124: // deliver a final empty token (which is different from a nil token).
125: // One could achieve the same behavior with a custom error value but
126: // providing one here is tidier.
127: // See the emptyFinalToken example for a use of this value.
128: var ErrFinalToken = errors.New("final token")
129: 
130: // Scan advances the [Scanner] to the next token, which will then be
131: // available through the [Scanner.Bytes] or [Scanner.Text] method. It returns false when
132: // there are no more tokens, either by reaching the end of the input or an error.
133: // After Scan returns false, the [Scanner.Err] method will return any error that
134: // occurred during scanning, except that if it was [io.EOF], [Scanner.Err]
135: // will return nil.
136: // Scan panics if the split function returns too many empty
137: // tokens without advancing the input. This is a common error mode for
138: // scanners.
139: func (s *Scanner) Scan() bool {
140: 	if s.done {
141: 		return false
142: 	}
143: 	s.scanCalled = true
144: 	// Loop until we have a token.
145: 	for {
146: 		// See if we can get a token with what we already have.
147: 		// If we've run out of data but have an error, give the split function
148: 		// a chance to recover any remaining, possibly empty token.
149: 		if s.end > s.start || s.err != nil {
150: 			advance, token, err := s.split(s.buf[s.start:s.end], s.err != nil)
151: 			if err != nil {
152: 				if err == ErrFinalToken {
153: 					s.token = token
154: 					s.done = true
155: 					// When token is not nil, it means the scanning stops
156: 					// with a trailing token, and thus the return value
157: 					// should be true to indicate the existence of the token.
158: 					return token != nil
159: 				}
160: 				s.setErr(err)
161: 				return false
162: 			}
163: 			if !s.advance(advance) {
164: 				return false
165: 			}
166: 			s.token = token
167: 			if token != nil {
168: 				if s.err == nil || advance > 0 {
169: 					s.empties = 0
170: 				} else {
171: 					// Returning tokens not advancing input at EOF.
172: 					s.empties++
173: 					if s.empties > maxConsecutiveEmptyReads {
174: 						panic("bufio.Scan: too many empty tokens without progressing")
175: 					}
176: 				}
177: 				return true
178: 			}
179: 		}
180: 		// We cannot generate a token with what we are holding.
181: 		// If we've already hit EOF or an I/O error, we are done.
182: 		if s.err != nil {
183: 			// Shut it down.
184: 			s.start = 0
185: 			s.end = 0
186: 			return false
187: 		}
188: 		// Must read more data.
189: 		// First, shift data to beginning of buffer if there's lots of empty space
190: 		// or space is needed.
191: 		if s.start > 0 && (s.end == len(s.buf) || s.start > len(s.buf)/2) {
192: 			copy(s.buf, s.buf[s.start:s.end])
193: 			s.end -= s.start
194: 			s.start = 0
195: 		}
196: 		// Is the buffer full? If so, resize.
197: 		if s.end == len(s.buf) {
198: 			// Guarantee no overflow in the multiplication below.
199: 			const maxInt = int(^uint(0) >> 1)
200: 			if len(s.buf) >= s.maxTokenSize || len(s.buf) > maxInt/2 {
201: 				s.setErr(ErrTooLong)
202: 				return false
203: 			}
204: 			newSize := len(s.buf) * 2
205: 			if newSize == 0 {
206: 				newSize = startBufSize
207: 			}
208: 			newSize = min(newSize, s.maxTokenSize)
209: 			newBuf := make([]byte, newSize)
210: 			copy(newBuf, s.buf[s.start:s.end])
211: 			s.buf = newBuf
212: 			s.end -= s.start
213: 			s.start = 0
214: 		}
215: 		// Finally we can read some input. Make sure we don't get stuck with
216: 		// a misbehaving Reader. Officially we don't need to do this, but let's
217: 		// be extra careful: Scanner is for safe, simple jobs.
218: 		for loop := 0; ; {
219: 			n, err := s.r.Read(s.buf[s.end:len(s.buf)])
220: 			if n < 0 || len(s.buf)-s.end < n {
221: 				s.setErr(ErrBadReadCount)
222: 				break
223: 			}
224: 			s.end += n
225: 			if err != nil {
226: 				s.setErr(err)
227: 				break
228: 			}
229: 			if n > 0 {
230: 				s.empties = 0
231: 				break
232: 			}
233: 			loop++
234: 			if loop > maxConsecutiveEmptyReads {
235: 				s.setErr(io.ErrNoProgress)
236: 				break
237: 			}
238: 		}
239: 	}
240: }
241: 
242: // advance consumes n bytes of the buffer. It reports whether the advance was legal.
243: func (s *Scanner) advance(n int) bool {
244: 	if n < 0 {
245: 		s.setErr(ErrNegativeAdvance)
246: 		return false
247: 	}
248: 	if n > s.end-s.start {
249: 		s.setErr(ErrAdvanceTooFar)
250: 		return false
251: 	}
252: 	s.start += n
253: 	return true
254: }
255: 
256: // setErr records the first error encountered.
257: func (s *Scanner) setErr(err error) {
258: 	if s.err == nil || s.err == io.EOF {
259: 		s.err = err
260: 	}
261: }
262: 
263: // Buffer controls memory allocation by the Scanner.
264: // It sets the initial buffer to use when scanning
265: // and the maximum size of buffer that may be allocated during scanning.
266: // The contents of the buffer are ignored.
267: //
268: // The maximum token size must be less than the larger of max and cap(buf).
269: // If max <= cap(buf), [Scanner.Scan] will use this buffer only and do no allocation.
270: //
271: // By default, [Scanner.Scan] uses an internal buffer and sets the
272: // maximum token size to [MaxScanTokenSize].
273: //
274: // Buffer panics if it is called after scanning has started.
275: func (s *Scanner) Buffer(buf []byte, max int) {
276: 	if s.scanCalled {
277: 		panic("Buffer called after Scan")
278: 	}
279: 	s.buf = buf[0:cap(buf)]
280: 	s.maxTokenSize = max
281: }
282: 
283: // Split sets the split function for the [Scanner].
284: // The default split function is [ScanLines].
285: //
286: // Split panics if it is called after scanning has started.
287: func (s *Scanner) Split(split SplitFunc) {
288: 	if s.scanCalled {
289: 		panic("Split called after Scan")
290: 	}
291: 	s.split = split
292: }
293: 
294: // Split functions
295: 
296: // ScanBytes is a split function for a [Scanner] that returns each byte as a token.
297: func ScanBytes(data []byte, atEOF bool) (advance int, token []byte, err error) {
298: 	if atEOF && len(data) == 0 {
299: 		return 0, nil, nil
300: 	}
301: 	return 1, data[0:1], nil
302: }
303: 
304: var errorRune = []byte(string(utf8.RuneError))
305: 
306: // ScanRunes is a split function for a [Scanner] that returns each
307: // UTF-8-encoded rune as a token. The sequence of runes returned is
308: // equivalent to that from a range loop over the input as a string, which
309: // means that erroneous UTF-8 encodings translate to U+FFFD = "\xef\xbf\xbd".
310: // Because of the Scan interface, this makes it impossible for the client to
311: // distinguish correctly encoded replacement runes from encoding errors.
312: func ScanRunes(data []byte, atEOF bool) (advance int, token []byte, err error) {
313: 	if atEOF && len(data) == 0 {
314: 		return 0, nil, nil
315: 	}
316: 
317: 	// Fast path 1: ASCII.
318: 	if data[0] < utf8.RuneSelf {
319: 		return 1, data[0:1], nil
320: 	}
321: 
322: 	// Fast path 2: Correct UTF-8 decode without error.
323: 	_, width := utf8.DecodeRune(data)
324: 	if width > 1 {
325: 		// It's a valid encoding. Width cannot be one for a correctly encoded
326: 		// non-ASCII rune.
327: 		return width, data[0:width], nil
328: 	}
329: 
330: 	// We know it's an error: we have width==1 and implicitly r==utf8.RuneError.
331: 	// Is the error because there wasn't a full rune to be decoded?
332: 	// FullRune distinguishes correctly between erroneous and incomplete encodings.
333: 	if !atEOF && !utf8.FullRune(data) {
334: 		// Incomplete; get more bytes.
335: 		return 0, nil, nil
336: 	}
337: 
338: 	// We have a real UTF-8 encoding error. Return a properly encoded error rune
339: 	// but advance only one byte. This matches the behavior of a range loop over
340: 	// an incorrectly encoded string.
341: 	return 1, errorRune, nil
342: }
343: 
344: // dropCR drops a terminal \r from the data.
345: func dropCR(data []byte) []byte {
346: 	if len(data) > 0 && data[len(data)-1] == '\r' {
347: 		return data[0 : len(data)-1]
348: 	}
349: 	return data
350: }
351: 
352: // ScanLines is a split function for a [Scanner] that returns each line of
353: // text, stripped of any trailing end-of-line marker. The returned line may
354: // be empty. The end-of-line marker is one optional carriage return followed
355: // by one mandatory newline. In regular expression notation, it is `\r?\n`.
356: // The last non-empty line of input will be returned even if it has no
357: // newline.
358: func ScanLines(data []byte, atEOF bool) (advance int, token []byte, err error) {
359: 	if atEOF && len(data) == 0 {
360: 		return 0, nil, nil
361: 	}
362: 	if i := bytes.IndexByte(data, '\n'); i >= 0 {
363: 		// We have a full newline-terminated line.
364: 		return i + 1, dropCR(data[0:i]), nil
365: 	}
366: 	// If we're at EOF, we have a final, non-terminated line. Return it.
367: 	if atEOF {
368: 		return len(data), dropCR(data), nil
369: 	}
370: 	// Request more data.
371: 	return 0, nil, nil
372: }
373: 
374: // isSpace reports whether the character is a Unicode white space character.
375: // We avoid dependency on the unicode package, but check validity of the implementation
376: // in the tests.
377: func isSpace(r rune) bool {
378: 	if r <= '\u00FF' {
379: 		// Obvious ASCII ones: \t through \r plus space. Plus two Latin-1 oddballs.
380: 		switch r {
381: 		case ' ', '\t', '\n', '\v', '\f', '\r':
382: 			return true
383: 		case '\u0085', '\u00A0':
384: 			return true
385: 		}
386: 		return false
387: 	}
388: 	// High-valued ones.
389: 	if '\u2000' <= r && r <= '\u200a' {
390: 		return true
391: 	}
392: 	switch r {
393: 	case '\u1680', '\u2028', '\u2029', '\u202f', '\u205f', '\u3000':
394: 		return true
395: 	}
396: 	return false
397: }
398: 
399: // ScanWords is a split function for a [Scanner] that returns each
400: // space-separated word of text, with surrounding spaces deleted. It will
401: // never return an empty string. The definition of space is set by
402: // unicode.IsSpace.
403: func ScanWords(data []byte, atEOF bool) (advance int, token []byte, err error) {
404: 	// Skip leading spaces.
405: 	start := 0
406: 	for width := 0; start < len(data); start += width {
407: 		var r rune
408: 		r, width = utf8.DecodeRune(data[start:])
409: 		if !isSpace(r) {
410: 			break
411: 		}
412: 	}
413: 	// Scan until space, marking end of word.
414: 	for width, i := 0, start; i < len(data); i += width {
415: 		var r rune
416: 		r, width = utf8.DecodeRune(data[i:])
417: 		if isSpace(r) {
418: 			return i + width, data[start:i], nil
419: 		}
420: 	}
421: 	// If we're at EOF, we have a final, non-empty, non-terminated word. Return it.
422: 	if atEOF && len(data) > start {
423: 		return len(data), data[start:], nil
424: 	}
425: 	// Request more data.
426: 	return start, nil, nil
427: }