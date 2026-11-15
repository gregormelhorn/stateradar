package lru_test

import (
	lru "github.com/hashicorp/golang-lru/v2"
	"sync"
	"testing"
)

func TestReferenceCapResizeRace(t *testing.T) {
	c, err := lru.New[int, int](2)
	if err != nil {
		t.Fatal(err)
	}
	var wg sync.WaitGroup
	wg.Add(2)
	start := make(chan struct{})
	go func() {
		defer wg.Done()
		<-start
		for i := 0; i < 10000; i++ {
			_ = c.Cap()
		}
	}()
	go func() {
		defer wg.Done()
		<-start
		for i := 0; i < 10000; i++ {
			c.Resize(2 + i%2)
		}
	}()
	close(start)
	wg.Wait()
}
