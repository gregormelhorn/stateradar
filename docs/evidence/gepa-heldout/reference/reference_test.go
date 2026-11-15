package reference

import (
	"bufio"
	"errors"
	"io"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func TestPipeFirstWriterError(t *testing.T) {
	r, w := io.Pipe()
	first := errors.New("first")
	second := errors.New("second")
	if err := w.CloseWithError(first); err != nil {
		t.Fatal(err)
	}
	if err := w.CloseWithError(second); err != nil {
		t.Fatal(err)
	}
	_, err := r.Read(make([]byte, 1))
	if err != first {
		t.Fatalf("got %v", err)
	}
}
func TestPipePartialWriteClose(t *testing.T) {
	r, w := io.Pipe()
	defer w.Close()
	marker := errors.New("reader closed")
	type result struct {
		n   int
		err error
	}
	done := make(chan result, 1)
	go func() { n, err := w.Write([]byte("abcdef")); done <- result{n, err} }()
	b := make([]byte, 2)
	n, err := r.Read(b)
	if n != 2 || err != nil || string(b) != "ab" {
		t.Fatalf("read %d %q %v", n, b, err)
	}
	r.CloseWithError(marker)
	got := <-done
	if got.n != 2 || got.err != marker {
		t.Fatalf("write %+v", got)
	}
}
func TestPipeZeroWriteHandshake(t *testing.T) {
	r, w := io.Pipe()
	defer r.Close()
	defer w.Close()
	type result struct {
		n   int
		err error
	}
	done := make(chan result, 1)
	go func() { n, err := w.Write(nil); done <- result{n, err} }()
	select {
	case got := <-done:
		t.Fatalf("write completed before read: %+v", got)
	case <-time.After(50 * time.Millisecond):
	}
	n, err := r.Read(nil)
	if n != 0 || err != nil {
		t.Fatalf("read %d %v", n, err)
	}
	if got := <-done; got.n != 0 || got.err != nil {
		t.Fatalf("write result %+v", got)
	}
}
func TestScannerFinalTokenVariants(t *testing.T) {
	for _, nilToken := range []bool{false, true} {
		s := bufio.NewScanner(strings.NewReader("x"))
		s.Split(func([]byte, bool) (int, []byte, error) {
			if nilToken {
				return 0, nil, bufio.ErrFinalToken
			}
			return 0, []byte{}, bufio.ErrFinalToken
		})
		if got := s.Scan(); got == nilToken {
			t.Fatalf("nil=%v first scan=%v", nilToken, got)
		}
		if s.Scan() || s.Err() != nil {
			t.Fatalf("second scan or error: %v", s.Err())
		}
	}
}
func TestScannerLateConfiguration(t *testing.T) {
	for _, configure := range []func(*bufio.Scanner){func(s *bufio.Scanner) { s.Buffer(nil, 32) }, func(s *bufio.Scanner) { s.Split(bufio.ScanBytes) }} {
		s := bufio.NewScanner(strings.NewReader(""))
		if s.Scan() {
			t.Fatal("empty input")
		}
		func() {
			defer func() {
				if recover() == nil {
					t.Error("expected late configuration panic")
				}
			}()
			configure(s)
		}()
	}
}
func TestValueTypedNilAndNil(t *testing.T) {
	var v atomic.Value
	var p *int
	v.Store(p)
	if v.Load() == nil {
		t.Fatal("typed nil disappeared")
	}
	if v.Load().(*int) != nil {
		t.Fatal("expected typed nil pointer")
	}
	func() {
		defer func() {
			if recover() == nil {
				t.Error("Store(nil) must panic")
			}
		}()
		v.Store(nil)
	}()
	if got, ok := v.Load().(*int); !ok || got != nil {
		t.Fatal("panic changed stored typed nil")
	}
}
func TestValueEmptyCompareAndSwap(t *testing.T) {
	var v atomic.Value
	if v.CompareAndSwap("old", "new") || v.Load() != nil {
		t.Fatal("non-nil old changed empty value")
	}
	if !v.CompareAndSwap(nil, "new") || v.Load() != "new" {
		t.Fatal("nil old did not initialize")
	}
}

type errorReader struct{ err error }

func (r errorReader) Read(p []byte) (int, error) { p[0] = 'x'; return 1, r.err }
func TestScannerFinalTokenPreservesPriorError(t *testing.T) {
	marker := errors.New("reader failure")
	s := bufio.NewScanner(errorReader{marker})
	s.Split(func([]byte, bool) (int, []byte, error) { return 0, []byte("x"), bufio.ErrFinalToken })
	if !s.Scan() || s.Text() != "x" || s.Err() != marker {
		t.Fatalf("token=%q err=%v", s.Text(), s.Err())
	}
	if s.Scan() || s.Err() != marker {
		t.Fatalf("final error=%v", s.Err())
	}
}
func TestValueCompareAndSwapMismatchedTypes(t *testing.T) {
	var v atomic.Value
	defer func() {
		if recover() == nil {
			t.Error("mismatched old and new types must panic")
		}
	}()
	v.CompareAndSwap(1, "new")
}
