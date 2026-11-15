Inspect the source for significant behavior, edge cases, event ordering and contract limitations. Return JSON with exactly one key findings, an array of at most six entries. Each entry has a unique id, text describing the exact starting conditions, ordered events and observable result, a citation object {line: integer, fragment: exact substring of that line}, and question: either an OPEN: question where intent or source wording is unclear, or an empty string. Include supported ordinary controls as appropriate. Do not assume a surprising behavior is intended. Return JSON only.

REVIEW PARAGRAPH:
Use the reviewed source and any pinned runtime evidence to trace ordinary success and failure, repetition, cancellation, abandonment, deferred work, and reuse. State the initial conditions and order the steps that determine the outcome. Compare both event orders and test intervening operations before treating an earlier event as decisive. Follow each completion from admission through reporting, state refresh, and effect. Check whether an obsolete report can be discarded even when cleanup or error propagation continues. Distinguish rebinding a caller's reference from replacing the value through the captured reference, and use an unchanged reference as a control. Check whether registration actually succeeds after a state observation, and keep notification, suspension, lock reacquisition, and return distinct. Compare notifications before and after registration, and distinguish when a lock is required to change the condition or begin waiting from when it is optional for notification. Preserve controls for copying before and after first use, cleanup after normal and abrupt exit, and valid reuse after earlier waiters return. Qualify exceptional behavior by the documented exclusions, compatibility mode, and whether a prior association is still present. Separate deadline calculation from dispatch and delivery. Compare repeated cancellation, expiry, and reactivation in order, checking the current state and whether earlier work has started, finished, or can overlap later work. For queued work, trace availability checks, enqueue, handoff, and shutdown through later callers and subsequent returns. Check who receives an available resource, what eventually releases the older waiter, and which validation runs on each path. Distinguish invoking cleanup from establishing its effect, and preserving error text from preserving error identity. Cite the branches, tests, and contract language that support each claim, and qualify conclusions by source coverage, version, configuration, and supported input range. Leave intent OPEN where the evidence does not settle transition timing, duplicate or abandoned completion, counter refresh and numeric limits, ownership or copying, exceptional exits, notification analogies, delivery guarantees, queue ordering, validation, or shutdown obligations. Where contract statements appear inconsistent, identify the event order and scope that expose the conflict and leave the intended wording OPEN.
SOURCE:
1: // Copyright 2009 The Go Authors. All rights reserved.
2: // Use of this source code is governed by a BSD-style
3: // license that can be found in the LICENSE file.
4: 
5: // Pipe adapter to connect code expecting an io.Reader
6: // with code expecting an io.Writer.
7: 
8: package io
9: 
10: import (
11: 	"errors"
12: 	"sync"
13: )
14: 
15: // onceError is an object that will only store an error once.
16: type onceError struct {
17: 	sync.Mutex // guards following
18: 	err        error
19: }
20: 
21: func (a *onceError) Store(err error) {
22: 	a.Lock()
23: 	defer a.Unlock()
24: 	if a.err != nil {
25: 		return
26: 	}
27: 	a.err = err
28: }
29: func (a *onceError) Load() error {
30: 	a.Lock()
31: 	defer a.Unlock()
32: 	return a.err
33: }
34: 
35: // ErrClosedPipe is the error used for read or write operations on a closed pipe.
36: var ErrClosedPipe = errors.New("io: read/write on closed pipe")
37: 
38: // A pipe is the shared pipe structure underlying PipeReader and PipeWriter.
39: type pipe struct {
40: 	wrMu sync.Mutex // Serializes Write operations
41: 	wrCh chan []byte
42: 	rdCh chan int
43: 
44: 	once sync.Once // Protects closing done
45: 	done chan struct{}
46: 	rerr onceError
47: 	werr onceError
48: }
49: 
50: func (p *pipe) read(b []byte) (n int, err error) {
51: 	select {
52: 	case <-p.done:
53: 		return 0, p.readCloseError()
54: 	default:
55: 	}
56: 
57: 	select {
58: 	case bw := <-p.wrCh:
59: 		nr := copy(b, bw)
60: 		p.rdCh <- nr
61: 		return nr, nil
62: 	case <-p.done:
63: 		return 0, p.readCloseError()
64: 	}
65: }
66: 
67: func (p *pipe) closeRead(err error) error {
68: 	if err == nil {
69: 		err = ErrClosedPipe
70: 	}
71: 	p.rerr.Store(err)
72: 	p.once.Do(func() { close(p.done) })
73: 	return nil
74: }
75: 
76: func (p *pipe) write(b []byte) (n int, err error) {
77: 	select {
78: 	case <-p.done:
79: 		return 0, p.writeCloseError()
80: 	default:
81: 		p.wrMu.Lock()
82: 		defer p.wrMu.Unlock()
83: 	}
84: 
85: 	for once := true; once || len(b) > 0; once = false {
86: 		select {
87: 		case p.wrCh <- b:
88: 			nw := <-p.rdCh
89: 			b = b[nw:]
90: 			n += nw
91: 		case <-p.done:
92: 			return n, p.writeCloseError()
93: 		}
94: 	}
95: 	return n, nil
96: }
97: 
98: func (p *pipe) closeWrite(err error) error {
99: 	if err == nil {
100: 		err = EOF
101: 	}
102: 	p.werr.Store(err)
103: 	p.once.Do(func() { close(p.done) })
104: 	return nil
105: }
106: 
107: // readCloseError is considered internal to the pipe type.
108: func (p *pipe) readCloseError() error {
109: 	rerr := p.rerr.Load()
110: 	if werr := p.werr.Load(); rerr == nil && werr != nil {
111: 		return werr
112: 	}
113: 	return ErrClosedPipe
114: }
115: 
116: // writeCloseError is considered internal to the pipe type.
117: func (p *pipe) writeCloseError() error {
118: 	werr := p.werr.Load()
119: 	if rerr := p.rerr.Load(); werr == nil && rerr != nil {
120: 		return rerr
121: 	}
122: 	return ErrClosedPipe
123: }
124: 
125: // A PipeReader is the read half of a pipe.
126: type PipeReader struct{ pipe }
127: 
128: // Read implements the standard Read interface:
129: // it reads data from the pipe, blocking until a writer
130: // arrives or the write end is closed.
131: // If the write end is closed with an error, that error is
132: // returned as err; otherwise err is EOF.
133: func (r *PipeReader) Read(data []byte) (n int, err error) {
134: 	return r.pipe.read(data)
135: }
136: 
137: // Close closes the reader; subsequent writes to the
138: // write half of the pipe will return the error [ErrClosedPipe].
139: func (r *PipeReader) Close() error {
140: 	return r.CloseWithError(nil)
141: }
142: 
143: // CloseWithError closes the reader; subsequent writes
144: // to the write half of the pipe will return the error err.
145: //
146: // CloseWithError never overwrites the previous error if it exists
147: // and always returns nil.
148: func (r *PipeReader) CloseWithError(err error) error {
149: 	return r.pipe.closeRead(err)
150: }
151: 
152: // A PipeWriter is the write half of a pipe.
153: type PipeWriter struct{ r PipeReader }
154: 
155: // Write implements the standard Write interface:
156: // it writes data to the pipe, blocking until one or more readers
157: // have consumed all the data or the read end is closed.
158: // If the read end is closed with an error, that err is
159: // returned as err; otherwise err is [ErrClosedPipe].
160: func (w *PipeWriter) Write(data []byte) (n int, err error) {
161: 	return w.r.pipe.write(data)
162: }
163: 
164: // Close closes the writer; subsequent reads from the
165: // read half of the pipe will return no bytes and EOF.
166: func (w *PipeWriter) Close() error {
167: 	return w.CloseWithError(nil)
168: }
169: 
170: // CloseWithError closes the writer; subsequent reads from the
171: // read half of the pipe will return no bytes and the error err,
172: // or EOF if err is nil.
173: //
174: // CloseWithError never overwrites the previous error if it exists
175: // and always returns nil.
176: func (w *PipeWriter) CloseWithError(err error) error {
177: 	return w.r.pipe.closeWrite(err)
178: }
179: 
180: // Pipe creates a synchronous in-memory pipe.
181: // It can be used to connect code expecting an [io.Reader]
182: // with code expecting an [io.Writer].
183: //
184: // Reads and Writes on the pipe are matched one to one
185: // except when multiple Reads are needed to consume a single Write.
186: // That is, each Write to the [PipeWriter] blocks until it has satisfied
187: // one or more Reads from the [PipeReader] that fully consume
188: // the written data.
189: // The data is copied directly from the Write to the corresponding
190: // Read (or Reads); there is no internal buffering.
191: //
192: // It is safe to call Read and Write in parallel with each other or with Close.
193: // Parallel calls to Read and parallel calls to Write are also safe:
194: // the individual calls will be gated sequentially.
195: func Pipe() (*PipeReader, *PipeWriter) {
196: 	pw := &PipeWriter{r: PipeReader{pipe: pipe{
197: 		wrCh: make(chan []byte),
198: 		rdCh: make(chan int),
199: 		done: make(chan struct{}),
200: 	}}}
201: 	return &pw.r, pw
202: }