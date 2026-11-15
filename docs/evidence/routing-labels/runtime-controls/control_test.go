package controls

import (
	"bytes"
	"io"
	"sync/atomic"
	"testing"
)

func TestBufferEmptyReadByte(t *testing.T) {
	var b bytes.Buffer
	if _, err := b.ReadByte(); err != io.EOF {
		t.Fatalf("got %v, want EOF", err)
	}
}
func TestValueSwapWithoutStore(t *testing.T) {
	var v atomic.Value
	if old := v.Swap(7); old != nil {
		t.Fatalf("old value: %v", old)
	}
	if got := v.Load(); got != 7 {
		t.Fatalf("got %v, want 7", got)
	}
}
