package lru_test

import (
	"fmt"
	lru "github.com/hashicorp/golang-lru/v2"
	"reflect"
	"testing"
	"time"
)

func TestReferenceInvalidConstructor(t *testing.T) {
	c, err := lru.NewWithEvict[int, int](0, nil)
	if err == nil || c == nil {
		t.Fatalf("constructor returned c=%v err=%v", c, err)
	}
}
func TestReferenceGetVersusPeek(t *testing.T) {
	for _, useGet := range []bool{false, true} {
		t.Run(fmt.Sprint(useGet), func(t *testing.T) {
			var evicted []int
			c, err := lru.NewWithEvict[int, int](2, func(k, v int) { evicted = append(evicted, k) })
			if err != nil {
				t.Fatal(err)
			}
			c.Add(1, 10)
			c.Add(2, 20)
			if useGet {
				if v, ok := c.Get(1); !ok || v != 10 {
					t.Fatal(v, ok)
				}
			} else {
				if v, ok := c.Peek(1); !ok || v != 10 {
					t.Fatal(v, ok)
				}
			}
			if !c.Add(3, 30) {
				t.Fatal("expected eviction")
			}
			want := 1
			if useGet {
				want = 2
			}
			if !reflect.DeepEqual(evicted, []int{want}) {
				t.Fatal(evicted, want)
			}
		})
	}
}
func TestReferencePurgeReentrantCallback(t *testing.T) {
	var c *lru.Cache[int, int]
	callbacks := 0
	var err error
	c, err = lru.NewWithEvict[int, int](3, func(k, v int) {
		callbacks++
		if callbacks == 1 {
			c.Add(3, 30)
		}
	})
	if err != nil {
		t.Fatal(err)
	}
	c.Add(1, 10)
	c.Add(2, 20)
	done := make(chan struct{})
	go func() { c.Purge(); close(done) }()
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("callback did not return")
	}
	if callbacks != 2 || c.Len() != 1 || !c.Contains(3) {
		t.Fatal(callbacks, c.Len(), c.Keys())
	}
}
func TestReferenceNegativeResize(t *testing.T) {
	var removed []int
	c, err := lru.NewWithEvict[int, int](2, func(k, v int) { removed = append(removed, k) })
	if err != nil {
		t.Fatal(err)
	}
	c.Add(1, 10)
	if n := c.Resize(-1); n != 2 {
		t.Fatal("resize result", n)
	}
	if c.Len() != 0 || c.Cap() != -1 || !reflect.DeepEqual(removed, []int{1}) {
		t.Fatal(c.Len(), c.Cap(), removed)
	}
	if !c.Add(2, 20) || c.Len() != 0 || !reflect.DeepEqual(removed, []int{1, 2}) {
		t.Fatal(c.Len(), removed)
	}
}
