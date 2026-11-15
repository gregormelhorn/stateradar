Independently examine each proposed observation against source and test evidence. Do not decide domain intent or infer that a timeout alone proves unbounded progress. Return JSON {"cases":[{"id":"...","verdict":"confirmed|refuted|unclear","reason":"...","file":"lru.go|simplelru/lru.go|internal/list.go","line":1,"fragment":"verbatim source line substring"}]}. Do not hide any weak or inconsistent claim.
OBSERVATIONS:
[{"id": "R01", "description": "NewWithEvict(0,nil) returns a non-nil Cache pointer and a non-nil error; callers cannot treat that result as a successfully initialized cache.", "test": "TestReferenceInvalidConstructor", "provenance": "observed-in-code", "citation": {"file": "upstream/simplelru/lru.go", "line": 25, "fragment": "if size <= 0 {"}}, {"id": "R02", "description": "With capacity two, Peek of the oldest key leaves it oldest while Get makes that key most recent; the next Add evicts the respective oldest key and reports the callback.", "test": "TestReferenceGetVersusPeek", "provenance": "observed-in-tests", "citation": {"file": "upstream/simplelru/lru.go", "line": 73, "fragment": "c.evictList.MoveToFront(ent)"}}, {"id": "R03", "description": "Purge invokes eviction callbacks outside the cache lock; a callback may reenter Add and leave a newly added entry after Purge returns.", "test": "TestReferencePurgeReentrantCallback", "provenance": "observed-in-tests", "citation": {"file": "upstream/lru.go", "line": 69, "fragment": "c.lock.Unlock()"}}, {"id": "R04", "description": "With capacity two and one entry, Resize(-1) returns two while one existing entry is actually evicted; it leaves capacity -1 and a later Add immediately evicts its inserted entry.", "test": "TestReferenceNegativeResize", "provenance": "observed-in-tests", "citation": {"file": "upstream/simplelru/lru.go", "line": 157, "fragment": "diff := c.Len() - size"}}, {"id": "R05", "description": "Concurrent Cache.Cap and Cache.Resize access the underlying size without a common lock, producing a race-detector report on the size read and write.", "test": "TestReferenceCapResizeRace", "provenance": "observed-in-tests", "citation": {"file": "upstream/lru.go", "line": 254, "fragment": "return c.lru.Cap()"}}]
TEST SOURCE:
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

EXECUTED JSON TEST LOGS:
{"Time":"2026-11-15T11:22:57.473157+01:00","Action":"start","Package":"github.com/hashicorp/golang-lru/v2"}
{"Time":"2026-11-15T11:22:57.473386+01:00","Action":"start","Package":"github.com/hashicorp/golang-lru/v2/expirable"}
{"Time":"2026-11-15T11:22:57.473453+01:00","Action":"start","Package":"github.com/hashicorp/golang-lru/v2/internal"}
{"Time":"2026-11-15T11:22:57.473495+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2/internal","Output":"?   \tgithub.com/hashicorp/golang-lru/v2/internal\t[no test files]\n"}
{"Time":"2026-11-15T11:22:57.473528+01:00","Action":"skip","Package":"github.com/hashicorp/golang-lru/v2/internal","Elapsed":0}
{"Time":"2026-11-15T11:22:57.473522+01:00","Action":"start","Package":"github.com/hashicorp/golang-lru/v2/simplelru"}
{"Time":"2026-11-15T11:22:57.795347+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2/expirable","Output":"testing: warning: no tests to run\n"}
{"Time":"2026-11-15T11:22:57.795451+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2/expirable","Output":"PASS\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.068139+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceInvalidConstructor"}
{"Time":"2026-11-15T11:22:58.068207+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceInvalidConstructor","Output":"=== RUN   TestReferenceInvalidConstructor\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.068267+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceInvalidConstructor","Output":"--- PASS: TestReferenceInvalidConstructor (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.06829+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceInvalidConstructor","Elapsed":0}
{"Time":"2026-11-15T11:22:58.0683+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek"}
{"Time":"2026-11-15T11:22:58.068308+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek","Output":"=== RUN   TestReferenceGetVersusPeek\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.068338+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/false"}
{"Time":"2026-11-15T11:22:58.068347+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/false","Output":"=== RUN   TestReferenceGetVersusPeek/false\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.068512+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/false","Output":"--- PASS: TestReferenceGetVersusPeek/false (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.068525+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/false","Elapsed":0}
{"Time":"2026-11-15T11:22:58.068554+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/true"}
{"Time":"2026-11-15T11:22:58.068561+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/true","Output":"=== RUN   TestReferenceGetVersusPeek/true\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.068613+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/true","Output":"--- PASS: TestReferenceGetVersusPeek/true (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.068624+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/true","Elapsed":0}
{"Time":"2026-11-15T11:22:58.068654+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek","Output":"--- PASS: TestReferenceGetVersusPeek (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.068679+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek","Elapsed":0}
{"Time":"2026-11-15T11:22:58.068717+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferencePurgeReentrantCallback"}
{"Time":"2026-11-15T11:22:58.068729+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferencePurgeReentrantCallback","Output":"=== RUN   TestReferencePurgeReentrantCallback\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.068904+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferencePurgeReentrantCallback","Output":"--- PASS: TestReferencePurgeReentrantCallback (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.068912+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferencePurgeReentrantCallback","Elapsed":0}
{"Time":"2026-11-15T11:22:58.068916+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceNegativeResize"}
{"Time":"2026-11-15T11:22:58.06892+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceNegativeResize","Output":"=== RUN   TestReferenceNegativeResize\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069015+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceNegativeResize","Output":"--- PASS: TestReferenceNegativeResize (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069023+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceNegativeResize","Elapsed":0}
{"Time":"2026-11-15T11:22:58.069055+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceInvalidConstructor"}
{"Time":"2026-11-15T11:22:58.069062+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceInvalidConstructor","Output":"=== RUN   TestReferenceInvalidConstructor\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069077+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceInvalidConstructor","Output":"--- PASS: TestReferenceInvalidConstructor (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069084+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceInvalidConstructor","Elapsed":0}
{"Time":"2026-11-15T11:22:58.069095+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek"}
{"Time":"2026-11-15T11:22:58.069099+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek","Output":"=== RUN   TestReferenceGetVersusPeek\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069139+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/false"}
{"Time":"2026-11-15T11:22:58.069151+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/false","Output":"=== RUN   TestReferenceGetVersusPeek/false\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.06916+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/false","Output":"--- PASS: TestReferenceGetVersusPeek/false (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069166+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/false","Elapsed":0}
{"Time":"2026-11-15T11:22:58.069187+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/true"}
{"Time":"2026-11-15T11:22:58.069193+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/true","Output":"=== RUN   TestReferenceGetVersusPeek/true\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069214+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/true","Output":"--- PASS: TestReferenceGetVersusPeek/true (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069232+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/true","Elapsed":0}
{"Time":"2026-11-15T11:22:58.069256+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek","Output":"--- PASS: TestReferenceGetVersusPeek (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069273+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek","Elapsed":0}
{"Time":"2026-11-15T11:22:58.06929+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferencePurgeReentrantCallback"}
{"Time":"2026-11-15T11:22:58.069294+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferencePurgeReentrantCallback","Output":"=== RUN   TestReferencePurgeReentrantCallback\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.06937+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferencePurgeReentrantCallback","Output":"--- PASS: TestReferencePurgeReentrantCallback (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069401+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferencePurgeReentrantCallback","Elapsed":0}
{"Time":"2026-11-15T11:22:58.06941+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceNegativeResize"}
{"Time":"2026-11-15T11:22:58.069416+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceNegativeResize","Output":"=== RUN   TestReferenceNegativeResize\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069425+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceNegativeResize","Output":"--- PASS: TestReferenceNegativeResize (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069432+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceNegativeResize","Elapsed":0}
{"Time":"2026-11-15T11:22:58.069492+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceInvalidConstructor"}
{"Time":"2026-11-15T11:22:58.069515+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceInvalidConstructor","Output":"=== RUN   TestReferenceInvalidConstructor\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069541+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceInvalidConstructor","Output":"--- PASS: TestReferenceInvalidConstructor (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069559+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceInvalidConstructor","Elapsed":0}
{"Time":"2026-11-15T11:22:58.069569+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek"}
{"Time":"2026-11-15T11:22:58.069573+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek","Output":"=== RUN   TestReferenceGetVersusPeek\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069601+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/false"}
{"Time":"2026-11-15T11:22:58.069607+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/false","Output":"=== RUN   TestReferenceGetVersusPeek/false\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069666+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/false","Output":"--- PASS: TestReferenceGetVersusPeek/false (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069674+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/false","Elapsed":0}
{"Time":"2026-11-15T11:22:58.069678+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/true"}
{"Time":"2026-11-15T11:22:58.069686+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/true","Output":"=== RUN   TestReferenceGetVersusPeek/true\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069692+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/true","Output":"--- PASS: TestReferenceGetVersusPeek/true (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069696+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek/true","Elapsed":0}
{"Time":"2026-11-15T11:22:58.069714+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek","Output":"--- PASS: TestReferenceGetVersusPeek (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069725+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceGetVersusPeek","Elapsed":0}
{"Time":"2026-11-15T11:22:58.069735+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferencePurgeReentrantCallback"}
{"Time":"2026-11-15T11:22:58.069739+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferencePurgeReentrantCallback","Output":"=== RUN   TestReferencePurgeReentrantCallback\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069782+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferencePurgeReentrantCallback","Output":"--- PASS: TestReferencePurgeReentrantCallback (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069791+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferencePurgeReentrantCallback","Elapsed":0}
{"Time":"2026-11-15T11:22:58.069807+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceNegativeResize"}
{"Time":"2026-11-15T11:22:58.069813+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceNegativeResize","Output":"=== RUN   TestReferenceNegativeResize\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069843+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceNegativeResize","Output":"--- PASS: TestReferenceNegativeResize (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.069852+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceNegativeResize","Elapsed":0}
{"Time":"2026-11-15T11:22:58.069878+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Output":"PASS\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.341474+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2/simplelru","Output":"testing: warning: no tests to run\n"}
{"Time":"2026-11-15T11:22:58.341535+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2/simplelru","Output":"PASS\n","OutputType":"frame"}
{"Time":"2026-11-15T11:22:58.800688+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2/expirable","Output":"ok  \tgithub.com/hashicorp/golang-lru/v2/expirable\t1.327s [no tests to run]\n"}
{"Time":"2026-11-15T11:22:58.800799+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2/expirable","Elapsed":1.327}
{"Time":"2026-11-15T11:22:59.085811+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Output":"ok  \tgithub.com/hashicorp/golang-lru/v2\t1.612s\n"}
{"Time":"2026-11-15T11:22:59.085905+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2","Elapsed":1.613}
{"Time":"2026-11-15T11:22:59.349796+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2/simplelru","Output":"ok  \tgithub.com/hashicorp/golang-lru/v2/simplelru\t1.876s [no tests to run]\n"}
{"Time":"2026-11-15T11:22:59.349842+01:00","Action":"pass","Package":"github.com/hashicorp/golang-lru/v2/simplelru","Elapsed":1.876}

{"Time":"2026-11-15T11:23:36.732317+01:00","Action":"start","Package":"github.com/hashicorp/golang-lru/v2"}
{"Time":"2026-11-15T11:23:36.938136+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace"}
{"Time":"2026-11-15T11:23:36.938242+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"=== RUN   TestReferenceCapResizeRace\n","OutputType":"frame"}
{"Time":"2026-11-15T11:23:36.938512+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"==================\n"}
{"Time":"2026-11-15T11:23:36.938535+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"WARNING: DATA RACE\n"}
{"Time":"2026-11-15T11:23:36.93854+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"Write at 0x00c0000a4260 by goroutine 8:\n"}
{"Time":"2026-11-15T11:23:36.938548+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2/simplelru.(*LRU[go.shape.int,go.shape.int]).Resize()\n"}
{"Time":"2026-11-15T11:23:36.938558+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/simplelru/lru.go:164 +0xe0\n"}
{"Time":"2026-11-15T11:23:36.93857+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2.(*Cache[go.shape.int,go.shape.int]).Resize()\n"}
{"Time":"2026-11-15T11:23:36.938574+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/lru.go:189 +0x74\n"}
{"Time":"2026-11-15T11:23:36.938578+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2_test.TestReferenceCapResizeRace.func2()\n"}
{"Time":"2026-11-15T11:23:36.938582+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/stateradar_race_test.go:28 +0xb4\n"}
{"Time":"2026-11-15T11:23:36.938586+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"\n"}
{"Time":"2026-11-15T11:23:36.938595+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"Previous read at 0x00c0000a4260 by goroutine 7:\n"}
{"Time":"2026-11-15T11:23:36.938599+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2/simplelru.(*LRU[go.shape.int,go.shape.int]).Cap()\n"}
{"Time":"2026-11-15T11:23:36.938603+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/simplelru/lru.go:152 +0xcc\n"}
{"Time":"2026-11-15T11:23:36.938607+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2.(*Cache[go.shape.int,go.shape.int]).Cap()\n"}
{"Time":"2026-11-15T11:23:36.938611+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/lru.go:254 +0x9c\n"}
{"Time":"2026-11-15T11:23:36.938614+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2_test.TestReferenceCapResizeRace.func1()\n"}
{"Time":"2026-11-15T11:23:36.938618+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/stateradar_race_test.go:21 +0xa4\n"}
{"Time":"2026-11-15T11:23:36.93865+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"\n"}
{"Time":"2026-11-15T11:23:36.938654+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"Goroutine 8 (running) created at:\n"}
{"Time":"2026-11-15T11:23:36.938664+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2_test.TestReferenceCapResizeRace()\n"}
{"Time":"2026-11-15T11:23:36.938667+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/stateradar_race_test.go:24 +0x27c\n"}
{"Time":"2026-11-15T11:23:36.938673+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  testing.tRunner()\n"}
{"Time":"2026-11-15T11:23:36.938676+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /opt/homebrew/Cellar/go/1.27.3/libexec/src/testing/testing.go:2195 +0x164\n"}
{"Time":"2026-11-15T11:23:36.938679+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  testing.(*T).Run.gowrap1()\n"}
{"Time":"2026-11-15T11:23:36.938682+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /opt/homebrew/Cellar/go/1.27.3/libexec/src/testing/testing.go:2260 +0x34\n"}
{"Time":"2026-11-15T11:23:36.938685+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"\n"}
{"Time":"2026-11-15T11:23:36.938691+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"Goroutine 7 (running) created at:\n"}
{"Time":"2026-11-15T11:23:36.938695+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2_test.TestReferenceCapResizeRace()\n"}
{"Time":"2026-11-15T11:23:36.938698+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/stateradar_race_test.go:17 +0x1ac\n"}
{"Time":"2026-11-15T11:23:36.938701+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  testing.tRunner()\n"}
{"Time":"2026-11-15T11:23:36.938704+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /opt/homebrew/Cellar/go/1.27.3/libexec/src/testing/testing.go:2195 +0x164\n"}
{"Time":"2026-11-15T11:23:36.938707+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  testing.(*T).Run.gowrap1()\n"}
{"Time":"2026-11-15T11:23:36.93871+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /opt/homebrew/Cellar/go/1.27.3/libexec/src/testing/testing.go:2260 +0x34\n"}
{"Time":"2026-11-15T11:23:36.938713+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"==================\n"}
{"Time":"2026-11-15T11:23:36.94231+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"    testing.go:1867: race detected during execution of test\n","OutputType":"error"}
{"Time":"2026-11-15T11:23:36.942321+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"--- FAIL: TestReferenceCapResizeRace (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:23:36.942335+01:00","Action":"fail","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Elapsed":0}
{"Time":"2026-11-15T11:23:36.942367+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Output":"FAIL\n","OutputType":"frame"}
{"Time":"2026-11-15T11:23:36.943168+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Output":"FAIL\tgithub.com/hashicorp/golang-lru/v2\t0.211s\n","OutputType":"frame"}
{"Time":"2026-11-15T11:23:36.943179+01:00","Action":"fail","Package":"github.com/hashicorp/golang-lru/v2","Elapsed":0.211}

{"Time":"2026-11-15T11:23:45.715371+01:00","Action":"start","Package":"github.com/hashicorp/golang-lru/v2"}
{"Time":"2026-11-15T11:23:45.920766+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace"}
{"Time":"2026-11-15T11:23:45.920843+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"=== RUN   TestReferenceCapResizeRace\n","OutputType":"frame"}
{"Time":"2026-11-15T11:23:45.92115+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"==================\n"}
{"Time":"2026-11-15T11:23:45.921168+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"WARNING: DATA RACE\n"}
{"Time":"2026-11-15T11:23:45.921177+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"Write at 0x00c000102240 by goroutine 8:\n"}
{"Time":"2026-11-15T11:23:45.921188+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2/simplelru.(*LRU[go.shape.int,go.shape.int]).Resize()\n"}
{"Time":"2026-11-15T11:23:45.921195+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/simplelru/lru.go:164 +0xe0\n"}
{"Time":"2026-11-15T11:23:45.9212+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2.(*Cache[go.shape.int,go.shape.int]).Resize()\n"}
{"Time":"2026-11-15T11:23:45.921205+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/lru.go:189 +0x74\n"}
{"Time":"2026-11-15T11:23:45.921215+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2_test.TestReferenceCapResizeRace.func2()\n"}
{"Time":"2026-11-15T11:23:45.92122+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/stateradar_race_test.go:28 +0xb4\n"}
{"Time":"2026-11-15T11:23:45.921224+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"\n"}
{"Time":"2026-11-15T11:23:45.921231+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"Previous read at 0x00c000102240 by goroutine 7:\n"}
{"Time":"2026-11-15T11:23:45.921235+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2/simplelru.(*LRU[go.shape.int,go.shape.int]).Cap()\n"}
{"Time":"2026-11-15T11:23:45.921238+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/simplelru/lru.go:152 +0xcc\n"}
{"Time":"2026-11-15T11:23:45.921242+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2.(*Cache[go.shape.int,go.shape.int]).Cap()\n"}
{"Time":"2026-11-15T11:23:45.921246+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/lru.go:254 +0x9c\n"}
{"Time":"2026-11-15T11:23:45.92125+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2_test.TestReferenceCapResizeRace.func1()\n"}
{"Time":"2026-11-15T11:23:45.921254+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/stateradar_race_test.go:21 +0xa4\n"}
{"Time":"2026-11-15T11:23:45.921283+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"\n"}
{"Time":"2026-11-15T11:23:45.921287+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"Goroutine 8 (running) created at:\n"}
{"Time":"2026-11-15T11:23:45.921292+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2_test.TestReferenceCapResizeRace()\n"}
{"Time":"2026-11-15T11:23:45.9213+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/stateradar_race_test.go:24 +0x27c\n"}
{"Time":"2026-11-15T11:23:45.921304+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  testing.tRunner()\n"}
{"Time":"2026-11-15T11:23:45.921307+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /opt/homebrew/Cellar/go/1.27.3/libexec/src/testing/testing.go:2195 +0x164\n"}
{"Time":"2026-11-15T11:23:45.92131+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  testing.(*T).Run.gowrap1()\n"}
{"Time":"2026-11-15T11:23:45.921313+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /opt/homebrew/Cellar/go/1.27.3/libexec/src/testing/testing.go:2260 +0x34\n"}
{"Time":"2026-11-15T11:23:45.921315+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"\n"}
{"Time":"2026-11-15T11:23:45.92132+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"Goroutine 7 (running) created at:\n"}
{"Time":"2026-11-15T11:23:45.921324+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2_test.TestReferenceCapResizeRace()\n"}
{"Time":"2026-11-15T11:23:45.921327+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/stateradar_race_test.go:17 +0x1ac\n"}
{"Time":"2026-11-15T11:23:45.92133+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  testing.tRunner()\n"}
{"Time":"2026-11-15T11:23:45.921333+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /opt/homebrew/Cellar/go/1.27.3/libexec/src/testing/testing.go:2195 +0x164\n"}
{"Time":"2026-11-15T11:23:45.921336+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  testing.(*T).Run.gowrap1()\n"}
{"Time":"2026-11-15T11:23:45.921339+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /opt/homebrew/Cellar/go/1.27.3/libexec/src/testing/testing.go:2260 +0x34\n"}
{"Time":"2026-11-15T11:23:45.921342+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"==================\n"}
{"Time":"2026-11-15T11:23:45.924772+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"    testing.go:1867: race detected during execution of test\n","OutputType":"error"}
{"Time":"2026-11-15T11:23:45.924782+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"--- FAIL: TestReferenceCapResizeRace (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:23:45.924786+01:00","Action":"fail","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Elapsed":0}
{"Time":"2026-11-15T11:23:45.924801+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Output":"FAIL\n","OutputType":"frame"}
{"Time":"2026-11-15T11:23:45.925563+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Output":"FAIL\tgithub.com/hashicorp/golang-lru/v2\t0.210s\n","OutputType":"frame"}
{"Time":"2026-11-15T11:23:45.925595+01:00","Action":"fail","Package":"github.com/hashicorp/golang-lru/v2","Elapsed":0.21}

{"Time":"2026-11-15T11:23:50.426939+01:00","Action":"start","Package":"github.com/hashicorp/golang-lru/v2"}
{"Time":"2026-11-15T11:23:50.643297+01:00","Action":"run","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace"}
{"Time":"2026-11-15T11:23:50.643394+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"=== RUN   TestReferenceCapResizeRace\n","OutputType":"frame"}
{"Time":"2026-11-15T11:23:50.643705+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"==================\n"}
{"Time":"2026-11-15T11:23:50.643726+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"WARNING: DATA RACE\n"}
{"Time":"2026-11-15T11:23:50.643734+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"Write at 0x00c00007e260 by goroutine 8:\n"}
{"Time":"2026-11-15T11:23:50.643742+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2/simplelru.(*LRU[go.shape.int,go.shape.int]).Resize()\n"}
{"Time":"2026-11-15T11:23:50.643756+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/simplelru/lru.go:164 +0xe0\n"}
{"Time":"2026-11-15T11:23:50.643767+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2.(*Cache[go.shape.int,go.shape.int]).Resize()\n"}
{"Time":"2026-11-15T11:23:50.643771+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/lru.go:189 +0x74\n"}
{"Time":"2026-11-15T11:23:50.643776+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2_test.TestReferenceCapResizeRace.func2()\n"}
{"Time":"2026-11-15T11:23:50.64378+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/stateradar_race_test.go:28 +0xb4\n"}
{"Time":"2026-11-15T11:23:50.643783+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"\n"}
{"Time":"2026-11-15T11:23:50.64379+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"Previous read at 0x00c00007e260 by goroutine 7:\n"}
{"Time":"2026-11-15T11:23:50.643795+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2/simplelru.(*LRU[go.shape.int,go.shape.int]).Cap()\n"}
{"Time":"2026-11-15T11:23:50.643799+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/simplelru/lru.go:152 +0xcc\n"}
{"Time":"2026-11-15T11:23:50.643807+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2.(*Cache[go.shape.int,go.shape.int]).Cap()\n"}
{"Time":"2026-11-15T11:23:50.643812+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/lru.go:254 +0x9c\n"}
{"Time":"2026-11-15T11:23:50.643816+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2_test.TestReferenceCapResizeRace.func1()\n"}
{"Time":"2026-11-15T11:23:50.643819+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/stateradar_race_test.go:21 +0xa4\n"}
{"Time":"2026-11-15T11:23:50.643846+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"\n"}
{"Time":"2026-11-15T11:23:50.643849+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"Goroutine 8 (running) created at:\n"}
{"Time":"2026-11-15T11:23:50.643855+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2_test.TestReferenceCapResizeRace()\n"}
{"Time":"2026-11-15T11:23:50.643859+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/stateradar_race_test.go:24 +0x27c\n"}
{"Time":"2026-11-15T11:23:50.643868+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  testing.tRunner()\n"}
{"Time":"2026-11-15T11:23:50.643872+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /opt/homebrew/Cellar/go/1.27.3/libexec/src/testing/testing.go:2195 +0x164\n"}
{"Time":"2026-11-15T11:23:50.643875+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  testing.(*T).Run.gowrap1()\n"}
{"Time":"2026-11-15T11:23:50.643878+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /opt/homebrew/Cellar/go/1.27.3/libexec/src/testing/testing.go:2260 +0x34\n"}
{"Time":"2026-11-15T11:23:50.643884+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"\n"}
{"Time":"2026-11-15T11:23:50.643887+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"Goroutine 7 (running) created at:\n"}
{"Time":"2026-11-15T11:23:50.64389+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  github.com/hashicorp/golang-lru/v2_test.TestReferenceCapResizeRace()\n"}
{"Time":"2026-11-15T11:23:50.643893+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /private/tmp/stateradar-lru-reference-eval/stateradar_race_test.go:17 +0x1ac\n"}
{"Time":"2026-11-15T11:23:50.643896+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  testing.tRunner()\n"}
{"Time":"2026-11-15T11:23:50.6439+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /opt/homebrew/Cellar/go/1.27.3/libexec/src/testing/testing.go:2195 +0x164\n"}
{"Time":"2026-11-15T11:23:50.643903+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"  testing.(*T).Run.gowrap1()\n"}
{"Time":"2026-11-15T11:23:50.643906+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"      /opt/homebrew/Cellar/go/1.27.3/libexec/src/testing/testing.go:2260 +0x34\n"}
{"Time":"2026-11-15T11:23:50.643909+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"==================\n"}
{"Time":"2026-11-15T11:23:50.647403+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"    testing.go:1867: race detected during execution of test\n","OutputType":"error"}
{"Time":"2026-11-15T11:23:50.647424+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Output":"--- FAIL: TestReferenceCapResizeRace (0.00s)\n","OutputType":"frame"}
{"Time":"2026-11-15T11:23:50.647443+01:00","Action":"fail","Package":"github.com/hashicorp/golang-lru/v2","Test":"TestReferenceCapResizeRace","Elapsed":0}
{"Time":"2026-11-15T11:23:50.647482+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Output":"FAIL\n","OutputType":"frame"}
{"Time":"2026-11-15T11:23:50.648218+01:00","Action":"output","Package":"github.com/hashicorp/golang-lru/v2","Output":"FAIL\tgithub.com/hashicorp/golang-lru/v2\t0.221s\n","OutputType":"frame"}
{"Time":"2026-11-15T11:23:50.648257+01:00","Action":"fail","Package":"github.com/hashicorp/golang-lru/v2","Elapsed":0.221}

SOURCE FILES:
FILE lru.go
1: // Copyright IBM Corp. 2014, 2025
2: // SPDX-License-Identifier: MPL-2.0
3: 
4: package lru
5: 
6: import (
7: 	"sync"
8: 
9: 	"github.com/hashicorp/golang-lru/v2/simplelru"
10: )
11: 
12: const (
13: 	// DefaultEvictedBufferSize defines the default buffer size to store evicted key/val
14: 	DefaultEvictedBufferSize = 16
15: )
16: 
17: // Cache is a thread-safe fixed size LRU cache.
18: type Cache[K comparable, V any] struct {
19: 	lru         *simplelru.LRU[K, V]
20: 	evictedKeys []K
21: 	evictedVals []V
22: 	onEvictedCB func(k K, v V)
23: 	lock        sync.RWMutex
24: }
25: 
26: // New creates an LRU of the given size.
27: func New[K comparable, V any](size int) (*Cache[K, V], error) {
28: 	return NewWithEvict[K, V](size, nil)
29: }
30: 
31: // NewWithEvict constructs a fixed size cache with the given eviction
32: // callback.
33: func NewWithEvict[K comparable, V any](size int, onEvicted func(key K, value V)) (c *Cache[K, V], err error) {
34: 	// create a cache with default settings
35: 	c = &Cache[K, V]{
36: 		onEvictedCB: onEvicted,
37: 	}
38: 	if onEvicted != nil {
39: 		c.initEvictBuffers()
40: 		onEvicted = c.onEvicted
41: 	}
42: 	c.lru, err = simplelru.NewLRU(size, onEvicted)
43: 	return
44: }
45: 
46: func (c *Cache[K, V]) initEvictBuffers() {
47: 	c.evictedKeys = make([]K, 0, DefaultEvictedBufferSize)
48: 	c.evictedVals = make([]V, 0, DefaultEvictedBufferSize)
49: }
50: 
51: // onEvicted save evicted key/val and sent in externally registered callback
52: // outside of critical section
53: func (c *Cache[K, V]) onEvicted(k K, v V) {
54: 	c.evictedKeys = append(c.evictedKeys, k)
55: 	c.evictedVals = append(c.evictedVals, v)
56: }
57: 
58: // Purge is used to completely clear the cache.
59: func (c *Cache[K, V]) Purge() {
60: 	var ks []K
61: 	var vs []V
62: 	c.lock.Lock()
63: 	c.lru.Purge()
64: 	if c.onEvictedCB != nil && len(c.evictedKeys) > 0 {
65: 		ks, vs = c.evictedKeys, c.evictedVals
66: 		c.initEvictBuffers()
67: 	}
68: 	c.lock.Unlock()
69: 	// invoke callback outside of critical section
70: 	if c.onEvictedCB != nil {
71: 		for i := 0; i < len(ks); i++ {
72: 			c.onEvictedCB(ks[i], vs[i])
73: 		}
74: 	}
75: }
76: 
77: // Add adds a value to the cache. Returns true if an eviction occurred.
78: func (c *Cache[K, V]) Add(key K, value V) (evicted bool) {
79: 	var k K
80: 	var v V
81: 	c.lock.Lock()
82: 	evicted = c.lru.Add(key, value)
83: 	if c.onEvictedCB != nil && evicted {
84: 		k, v = c.evictedKeys[0], c.evictedVals[0]
85: 		c.evictedKeys, c.evictedVals = c.evictedKeys[:0], c.evictedVals[:0]
86: 	}
87: 	c.lock.Unlock()
88: 	if c.onEvictedCB != nil && evicted {
89: 		c.onEvictedCB(k, v)
90: 	}
91: 	return
92: }
93: 
94: // Get looks up a key's value from the cache.
95: func (c *Cache[K, V]) Get(key K) (value V, ok bool) {
96: 	c.lock.Lock()
97: 	value, ok = c.lru.Get(key)
98: 	c.lock.Unlock()
99: 	return value, ok
100: }
101: 
102: // Contains checks if a key is in the cache, without updating the
103: // recent-ness or deleting it for being stale.
104: func (c *Cache[K, V]) Contains(key K) bool {
105: 	c.lock.RLock()
106: 	containKey := c.lru.Contains(key)
107: 	c.lock.RUnlock()
108: 	return containKey
109: }
110: 
111: // Peek returns the key value (or undefined if not found) without updating
112: // the "recently used"-ness of the key.
113: func (c *Cache[K, V]) Peek(key K) (value V, ok bool) {
114: 	c.lock.RLock()
115: 	value, ok = c.lru.Peek(key)
116: 	c.lock.RUnlock()
117: 	return value, ok
118: }
119: 
120: // ContainsOrAdd checks if a key is in the cache without updating the
121: // recent-ness or deleting it for being stale, and if not, adds the value.
122: // Returns whether found and whether an eviction occurred.
123: func (c *Cache[K, V]) ContainsOrAdd(key K, value V) (ok, evicted bool) {
124: 	var k K
125: 	var v V
126: 	c.lock.Lock()
127: 	if c.lru.Contains(key) {
128: 		c.lock.Unlock()
129: 		return true, false
130: 	}
131: 	evicted = c.lru.Add(key, value)
132: 	if c.onEvictedCB != nil && evicted {
133: 		k, v = c.evictedKeys[0], c.evictedVals[0]
134: 		c.evictedKeys, c.evictedVals = c.evictedKeys[:0], c.evictedVals[:0]
135: 	}
136: 	c.lock.Unlock()
137: 	if c.onEvictedCB != nil && evicted {
138: 		c.onEvictedCB(k, v)
139: 	}
140: 	return false, evicted
141: }
142: 
143: // PeekOrAdd checks if a key is in the cache without updating the
144: // recent-ness or deleting it for being stale, and if not, adds the value.
145: // Returns whether found and whether an eviction occurred.
146: func (c *Cache[K, V]) PeekOrAdd(key K, value V) (previous V, ok, evicted bool) {
147: 	var k K
148: 	var v V
149: 	c.lock.Lock()
150: 	previous, ok = c.lru.Peek(key)
151: 	if ok {
152: 		c.lock.Unlock()
153: 		return previous, true, false
154: 	}
155: 	evicted = c.lru.Add(key, value)
156: 	if c.onEvictedCB != nil && evicted {
157: 		k, v = c.evictedKeys[0], c.evictedVals[0]
158: 		c.evictedKeys, c.evictedVals = c.evictedKeys[:0], c.evictedVals[:0]
159: 	}
160: 	c.lock.Unlock()
161: 	if c.onEvictedCB != nil && evicted {
162: 		c.onEvictedCB(k, v)
163: 	}
164: 	return
165: }
166: 
167: // Remove removes the provided key from the cache.
168: func (c *Cache[K, V]) Remove(key K) (present bool) {
169: 	var k K
170: 	var v V
171: 	c.lock.Lock()
172: 	present = c.lru.Remove(key)
173: 	if c.onEvictedCB != nil && present {
174: 		k, v = c.evictedKeys[0], c.evictedVals[0]
175: 		c.evictedKeys, c.evictedVals = c.evictedKeys[:0], c.evictedVals[:0]
176: 	}
177: 	c.lock.Unlock()
178: 	if c.onEvictedCB != nil && present {
179: 		c.onEvictedCB(k, v)
180: 	}
181: 	return
182: }
183: 
184: // Resize changes the cache size.
185: func (c *Cache[K, V]) Resize(size int) (evicted int) {
186: 	var ks []K
187: 	var vs []V
188: 	c.lock.Lock()
189: 	evicted = c.lru.Resize(size)
190: 	if c.onEvictedCB != nil && evicted > 0 {
191: 		ks, vs = c.evictedKeys, c.evictedVals
192: 		c.initEvictBuffers()
193: 	}
194: 	c.lock.Unlock()
195: 	if c.onEvictedCB != nil && evicted > 0 {
196: 		for i := 0; i < len(ks); i++ {
197: 			c.onEvictedCB(ks[i], vs[i])
198: 		}
199: 	}
200: 	return evicted
201: }
202: 
203: // RemoveOldest removes the oldest item from the cache.
204: func (c *Cache[K, V]) RemoveOldest() (key K, value V, ok bool) {
205: 	var k K
206: 	var v V
207: 	c.lock.Lock()
208: 	key, value, ok = c.lru.RemoveOldest()
209: 	if c.onEvictedCB != nil && ok {
210: 		k, v = c.evictedKeys[0], c.evictedVals[0]
211: 		c.evictedKeys, c.evictedVals = c.evictedKeys[:0], c.evictedVals[:0]
212: 	}
213: 	c.lock.Unlock()
214: 	if c.onEvictedCB != nil && ok {
215: 		c.onEvictedCB(k, v)
216: 	}
217: 	return
218: }
219: 
220: // GetOldest returns the oldest entry
221: func (c *Cache[K, V]) GetOldest() (key K, value V, ok bool) {
222: 	c.lock.RLock()
223: 	key, value, ok = c.lru.GetOldest()
224: 	c.lock.RUnlock()
225: 	return
226: }
227: 
228: // Keys returns a slice of the keys in the cache, from oldest to newest.
229: func (c *Cache[K, V]) Keys() []K {
230: 	c.lock.RLock()
231: 	keys := c.lru.Keys()
232: 	c.lock.RUnlock()
233: 	return keys
234: }
235: 
236: // Values returns a slice of the values in the cache, from oldest to newest.
237: func (c *Cache[K, V]) Values() []V {
238: 	c.lock.RLock()
239: 	values := c.lru.Values()
240: 	c.lock.RUnlock()
241: 	return values
242: }
243: 
244: // Len returns the number of items in the cache.
245: func (c *Cache[K, V]) Len() int {
246: 	c.lock.RLock()
247: 	length := c.lru.Len()
248: 	c.lock.RUnlock()
249: 	return length
250: }
251: 
252: // Cap returns the capacity of the cache
253: func (c *Cache[K, V]) Cap() int {
254: 	return c.lru.Cap()
255: }
FILE simplelru/lru.go
1: // Copyright IBM Corp. 2014, 2026
2: // SPDX-License-Identifier: MPL-2.0
3: 
4: package simplelru
5: 
6: import (
7: 	"errors"
8: 
9: 	"github.com/hashicorp/golang-lru/v2/internal"
10: )
11: 
12: // EvictCallback is used to get a callback when a cache entry is evicted
13: type EvictCallback[K comparable, V any] func(key K, value V)
14: 
15: // LRU implements a non-thread safe fixed size LRU cache
16: type LRU[K comparable, V any] struct {
17: 	size      int
18: 	evictList *internal.LruList[K, V]
19: 	items     map[K]*internal.Entry[K, V]
20: 	onEvict   EvictCallback[K, V]
21: }
22: 
23: // NewLRU constructs an LRU of the given size
24: func NewLRU[K comparable, V any](size int, onEvict EvictCallback[K, V]) (*LRU[K, V], error) {
25: 	if size <= 0 {
26: 		return nil, errors.New("must provide a positive size")
27: 	}
28: 
29: 	c := &LRU[K, V]{
30: 		size:      size,
31: 		evictList: internal.NewList[K, V](),
32: 		items:     make(map[K]*internal.Entry[K, V]),
33: 		onEvict:   onEvict,
34: 	}
35: 	return c, nil
36: }
37: 
38: // Purge is used to completely clear the cache.
39: func (c *LRU[K, V]) Purge() {
40: 	for k, v := range c.items {
41: 		if c.onEvict != nil {
42: 			c.onEvict(k, v.Value)
43: 		}
44: 		delete(c.items, k)
45: 	}
46: 	c.evictList.Init()
47: }
48: 
49: // Add adds a value to the cache.  Returns true if an eviction occurred.
50: func (c *LRU[K, V]) Add(key K, value V) (evicted bool) {
51: 	// Check for existing item
52: 	if ent, ok := c.items[key]; ok {
53: 		c.evictList.MoveToFront(ent)
54: 		ent.Value = value
55: 		return false
56: 	}
57: 
58: 	// Add new item
59: 	ent := c.evictList.PushFront(key, value)
60: 	c.items[key] = ent
61: 
62: 	evict := c.evictList.Length() > c.size
63: 	// Verify size not exceeded
64: 	if evict {
65: 		c.removeOldest()
66: 	}
67: 	return evict
68: }
69: 
70: // Get looks up a key's value from the cache.
71: func (c *LRU[K, V]) Get(key K) (value V, ok bool) {
72: 	if ent, ok := c.items[key]; ok {
73: 		c.evictList.MoveToFront(ent)
74: 		return ent.Value, true
75: 	}
76: 	return
77: }
78: 
79: // Contains checks if a key is in the cache, without updating the recent-ness
80: // or deleting it for being stale.
81: func (c *LRU[K, V]) Contains(key K) (ok bool) {
82: 	_, ok = c.items[key]
83: 	return ok
84: }
85: 
86: // Peek returns the key value (or undefined if not found) without updating
87: // the "recently used"-ness of the key.
88: func (c *LRU[K, V]) Peek(key K) (value V, ok bool) {
89: 	var ent *internal.Entry[K, V]
90: 	if ent, ok = c.items[key]; ok {
91: 		return ent.Value, true
92: 	}
93: 	return
94: }
95: 
96: // Remove removes the provided key from the cache, returning if the
97: // key was contained.
98: func (c *LRU[K, V]) Remove(key K) (present bool) {
99: 	if ent, ok := c.items[key]; ok {
100: 		c.removeElement(ent)
101: 		return true
102: 	}
103: 	return false
104: }
105: 
106: // RemoveOldest removes the oldest item from the cache.
107: func (c *LRU[K, V]) RemoveOldest() (key K, value V, ok bool) {
108: 	if ent := c.evictList.Back(); ent != nil {
109: 		c.removeElement(ent)
110: 		return ent.Key, ent.Value, true
111: 	}
112: 	return
113: }
114: 
115: // GetOldest returns the oldest entry
116: func (c *LRU[K, V]) GetOldest() (key K, value V, ok bool) {
117: 	if ent := c.evictList.Back(); ent != nil {
118: 		return ent.Key, ent.Value, true
119: 	}
120: 	return
121: }
122: 
123: // Keys returns a slice of the keys in the cache, from oldest to newest.
124: func (c *LRU[K, V]) Keys() []K {
125: 	keys := make([]K, c.evictList.Length())
126: 	i := 0
127: 	for ent := c.evictList.Back(); ent != nil; ent = ent.PrevEntry() {
128: 		keys[i] = ent.Key
129: 		i++
130: 	}
131: 	return keys
132: }
133: 
134: // Values returns a slice of the values in the cache, from oldest to newest.
135: func (c *LRU[K, V]) Values() []V {
136: 	values := make([]V, c.evictList.Length())
137: 	i := 0
138: 	for ent := c.evictList.Back(); ent != nil; ent = ent.PrevEntry() {
139: 		values[i] = ent.Value
140: 		i++
141: 	}
142: 	return values
143: }
144: 
145: // Len returns the number of items in the cache.
146: func (c *LRU[K, V]) Len() int {
147: 	return c.evictList.Length()
148: }
149: 
150: // Cap returns the capacity of the cache
151: func (c *LRU[K, V]) Cap() int {
152: 	return c.size
153: }
154: 
155: // Resize changes the cache size.
156: func (c *LRU[K, V]) Resize(size int) (evicted int) {
157: 	diff := c.Len() - size
158: 	if diff < 0 {
159: 		diff = 0
160: 	}
161: 	for i := 0; i < diff; i++ {
162: 		c.removeOldest()
163: 	}
164: 	c.size = size
165: 	return diff
166: }
167: 
168: // removeOldest removes the oldest item from the cache.
169: func (c *LRU[K, V]) removeOldest() {
170: 	if ent := c.evictList.Back(); ent != nil {
171: 		c.removeElement(ent)
172: 	}
173: }
174: 
175: // removeElement is used to remove a given list element from the cache
176: func (c *LRU[K, V]) removeElement(e *internal.Entry[K, V]) {
177: 	c.evictList.Remove(e)
178: 	delete(c.items, e.Key)
179: 	if c.onEvict != nil {
180: 		c.onEvict(e.Key, e.Value)
181: 	}
182: }
FILE internal/list.go
1: // Copyright 2009 The Go Authors. All rights reserved.
2: // Use of this source code is governed by a BSD-style
3: // license that can be found in the LICENSE_list file.
4: 
5: package internal
6: 
7: import "time"
8: 
9: // Entry is an LRU Entry
10: type Entry[K comparable, V any] struct {
11: 	// Next and previous pointers in the doubly-linked list of elements.
12: 	// To simplify the implementation, internally a list l is implemented
13: 	// as a ring, such that &l.root is both the next element of the last
14: 	// list element (l.Back()) and the previous element of the first list
15: 	// element (l.Front()).
16: 	next, prev *Entry[K, V]
17: 
18: 	// The list to which this element belongs.
19: 	list *LruList[K, V]
20: 
21: 	// The LRU Key of this element.
22: 	Key K
23: 
24: 	// The Value stored with this element.
25: 	Value V
26: 
27: 	// The time this element would be cleaned up, optional
28: 	ExpiresAt time.Time
29: 
30: 	// The expiry bucket item was put in, optional
31: 	ExpireBucket uint8
32: }
33: 
34: // PrevEntry returns the previous list element or nil.
35: func (e *Entry[K, V]) PrevEntry() *Entry[K, V] {
36: 	if p := e.prev; e.list != nil && p != &e.list.root {
37: 		return p
38: 	}
39: 	return nil
40: }
41: 
42: // LruList represents a doubly linked list.
43: // The zero Value for LruList is an empty list ready to use.
44: type LruList[K comparable, V any] struct {
45: 	root Entry[K, V] // sentinel list element, only &root, root.prev, and root.next are used
46: 	len  int         // current list Length excluding (this) sentinel element
47: }
48: 
49: // Init initializes or clears list l.
50: func (l *LruList[K, V]) Init() *LruList[K, V] {
51: 	l.root.next = &l.root
52: 	l.root.prev = &l.root
53: 	l.len = 0
54: 	return l
55: }
56: 
57: // NewList returns an initialized list.
58: func NewList[K comparable, V any]() *LruList[K, V] { return new(LruList[K, V]).Init() }
59: 
60: // Length returns the number of elements of list l.
61: // The complexity is O(1).
62: func (l *LruList[K, V]) Length() int { return l.len }
63: 
64: // Back returns the last element of list l or nil if the list is empty.
65: func (l *LruList[K, V]) Back() *Entry[K, V] {
66: 	if l.len == 0 {
67: 		return nil
68: 	}
69: 	return l.root.prev
70: }
71: 
72: // lazyInit lazily initializes a zero List Value.
73: func (l *LruList[K, V]) lazyInit() {
74: 	if l.root.next == nil {
75: 		l.Init()
76: 	}
77: }
78: 
79: // insert inserts e after at, increments l.len, and returns e.
80: func (l *LruList[K, V]) insert(e, at *Entry[K, V]) *Entry[K, V] {
81: 	e.prev = at
82: 	e.next = at.next
83: 	e.prev.next = e
84: 	e.next.prev = e
85: 	e.list = l
86: 	l.len++
87: 	return e
88: }
89: 
90: // insertValue is a convenience wrapper for insert(&Entry{Value: v, ExpiresAt: ExpiresAt}, at).
91: func (l *LruList[K, V]) insertValue(k K, v V, expiresAt time.Time, at *Entry[K, V]) *Entry[K, V] {
92: 	return l.insert(&Entry[K, V]{Value: v, Key: k, ExpiresAt: expiresAt}, at)
93: }
94: 
95: // Remove removes e from its list, decrements l.len
96: func (l *LruList[K, V]) Remove(e *Entry[K, V]) V {
97: 	e.prev.next = e.next
98: 	e.next.prev = e.prev
99: 	e.next = nil // avoid memory leaks
100: 	e.prev = nil // avoid memory leaks
101: 	e.list = nil
102: 	l.len--
103: 
104: 	return e.Value
105: }
106: 
107: // move moves e to next to at.
108: func (l *LruList[K, V]) move(e, at *Entry[K, V]) {
109: 	if e == at {
110: 		return
111: 	}
112: 	e.prev.next = e.next
113: 	e.next.prev = e.prev
114: 
115: 	e.prev = at
116: 	e.next = at.next
117: 	e.prev.next = e
118: 	e.next.prev = e
119: }
120: 
121: // PushFront inserts a new element e with value v at the front of list l and returns e.
122: func (l *LruList[K, V]) PushFront(k K, v V) *Entry[K, V] {
123: 	l.lazyInit()
124: 	return l.insertValue(k, v, time.Time{}, &l.root)
125: }
126: 
127: // PushFrontExpirable inserts a new expirable element e with Value v at the front of list l and returns e.
128: func (l *LruList[K, V]) PushFrontExpirable(k K, v V, expiresAt time.Time) *Entry[K, V] {
129: 	l.lazyInit()
130: 	return l.insertValue(k, v, expiresAt, &l.root)
131: }
132: 
133: // MoveToFront moves element e to the front of list l.
134: // If e is not an element of l, the list is not modified.
135: // The element must not be nil.
136: func (l *LruList[K, V]) MoveToFront(e *Entry[K, V]) {
137: 	if e.list != l || l.root.next == e {
138: 		return
139: 	}
140: 	// see comment in List.Remove about initialization of l
141: 	l.move(e, &l.root)
142: }