package reference

import (
 "bytes"
 "errors"
 "io"
 "sync"
 "testing"
 "time"
)

func TestOncePanicDone(t *testing.T) {
 var o sync.Once
 marker := errors.New("boom")
 func() { defer func() { if recover() != marker { t.Error("expected panic") } }(); o.Do(func() { panic(marker) }) }()
 ran := false
 o.Do(func() { ran = true })
 if ran { t.Fatal("function ran after panic") }
}
func TestOnceConcurrentWait(t *testing.T) {
 var o sync.Once
 entered, release := make(chan struct{}), make(chan struct{})
 finished := make(chan struct{})
 go func() { o.Do(func() { close(entered); <-release }) }()
 <-entered
 go func() { o.Do(func() { t.Error("second function ran") }); close(finished) }()
 select { case <-finished: t.Fatal("returned before first function completed"); case <-time.After(50*time.Millisecond): }
 close(release)
 select { case <-finished: case <-time.After(time.Second): t.Fatal("waiter did not finish") }
}
func TestBufferEmptyReads(t *testing.T) {
 var b bytes.Buffer
 if n,e:=b.Read(nil); n!=0 || e!=nil { t.Fatal(n,e) }
 if n,e:=b.Read(make([]byte,1)); n!=0 || e!=io.EOF { t.Fatal(n,e) }
}
func TestBufferZeroReadInvalidatesUnread(t *testing.T) {
 b:=bytes.NewBufferString("ab")
 if x,e:=b.ReadByte(); x!='a' || e!=nil {t.Fatal(x,e)}
 if n,e:=b.Read(nil); n!=0 || e!=nil {t.Fatal(n,e)}
 if e:=b.UnreadByte(); e==nil {t.Fatal("expected error after zero read")}
 if x,e:=b.ReadByte(); x!='b' || e!=nil {t.Fatal(x,e)}
 if e:=b.UnreadByte();e!=nil {t.Fatal(e)}
 if x,e:=b.ReadByte(); x!='b' || e!=nil {t.Fatal(x,e)}
}
