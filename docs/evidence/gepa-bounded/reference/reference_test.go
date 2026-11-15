package reference
import (
 "context"
 "sync"
 "sync/atomic"
 "testing"
 "time"
 "reference.local/singleflight"
)
func await(t *testing.T, c <-chan struct{}) { t.Helper(); select {case <-c: case <-time.After(2*time.Second):t.Fatal("watchdog, not a domain latency bound")}}
func TestReference(t *testing.T) {
 t.Run("context",func(t *testing.T){
  ctx,cancel:=context.WithCancel(context.Background());defer cancel()
  var stopped atomic.Int32
  stop:=context.AfterFunc(ctx,func(){stopped.Add(1)})
  if !stop()||stop(){t.Fatal("stop return contract")}
  a,b:=make(chan struct{}),make(chan struct{})
  context.AfterFunc(ctx,func(){close(a)});context.AfterFunc(ctx,func(){close(b)})
  cancel();await(t,a);await(t,b)
  if stopped.Load()!=0 {t.Fatal("stopped registration ran")}
  already:=make(chan struct{});context.AfterFunc(ctx,func(){close(already)});await(t,already)
  old,oldCancel:=context.WithCancel(context.Background());defer oldCancel()
  local:=old;entered,release,finished:=make(chan struct{}),make(chan struct{}),make(chan struct{})
  liveStop:=context.AfterFunc(local,func(){close(entered);<-release;close(finished)})
  local,newCancel:=context.WithCancel(context.Background());defer newCancel();_ = local
  oldCancel();await(t,entered)
  returned:=make(chan struct{});go func(){if liveStop(){t.Error("running callback stopped")};close(returned)}()
  await(t,returned);select{case <-finished:t.Fatal("callback finished without release");default:}
  close(release);await(t,finished)
 })
 t.Run("singleflight",func(t *testing.T){
  var g singleflight.Group
  entered,release:=make(chan struct{}),make(chan struct{})
  old:=g.DoChan("key",func()(interface{},error){close(entered);<-release;return "old",nil});await(t,entered)
  g.Forget("key")
  nextEntered,nextRelease:=make(chan struct{}),make(chan struct{})
  next:=g.DoChan("key",func()(interface{},error){close(nextEntered);<-nextRelease;return "new",nil});await(t,nextEntered)
  close(release);if (<-old).Val!="old"{t.Fatal("Forget changed old result")}
  duplicate:=g.DoChan("key",func()(interface{},error){t.Error("old completion deleted replacement");return "wrong",nil})
  close(nextRelease)
  if (<-next).Val!="new"||(<-duplicate).Val!="new"{t.Fatal("replacement identity")}
  select{case _,ok:=<-next:if !ok{t.Fatal("DoChan closed")};t.Fatal("extra result");default:}
  calls:=0
  for i:=0;i<2;i++{g.Do("sequential",func()(interface{},error){calls++;return calls,nil})}
  if calls!=2{t.Fatal("unexpected persistent cache")}
  var g2 singleflight.Group
  groupEntered,groupRelease:=make(chan struct{}),make(chan struct{})
  pending:=g.DoChan("namespace",func()(interface{},error){close(groupEntered);<-groupRelease;return "first-group",nil});await(t,groupEntered)
  val,_,_:=g2.Do("namespace",func()(interface{},error){return "other-group",nil});if val!="other-group"{t.Fatal("group namespace")}
  close(groupRelease);if (<-pending).Val!="first-group"{t.Fatal("group namespace original")}
 })
 t.Run("timer",func(t *testing.T){
  var n atomic.Int32
  entered:=make(chan struct{},2);release:=make(chan struct{});done:=make(chan struct{},2)
  timer:=time.AfterFunc(time.Hour,func(){n.Add(1);entered<-struct{}{};<-release;done<-struct{}{}})
  if timer.C!=nil{t.Fatal("AfterFunc channel")}
  if !timer.Reset(0){t.Fatal("active reset")};await(t,entered)
  if timer.Stop(){t.Fatal("stop running returned true")}
  if timer.Reset(0){t.Fatal("started reset returned true")};await(t,entered)
  if n.Load()!=2{t.Fatal("second execution not scheduled")}
  close(release);await(t,done);await(t,done)
  stopTimer:=time.AfterFunc(time.Hour,func(){t.Error("stopped timer fired")})
  if !stopTimer.Stop()||stopTimer.Stop(){t.Fatal("stop before expiry")}
  old:=make(chan struct{});f:=func(){close(old)};captured:=time.AfterFunc(time.Hour,f)
  f=func(){t.Error("caller reassignment redirected callback")};_ = f
  captured.Reset(0);await(t,old)
 })
 t.Run("once",func(t *testing.T){
  count:=0;f:=func(){count++};wrapped:=sync.OnceFunc(f);copyOf:=wrapped
  f=func(){count+=100};_ = f;wrapped();copyOf();if count!=1{t.Fatal("wrapper copy/caller rebind")}
  same:=func(){count++};sync.OnceFunc(same)();sync.OnceFunc(same)();if count!=3{t.Fatal("independent wrappers")}
  calls:=0;marker:=new(int);panicOnce:=sync.OnceFunc(func(){calls++;panic(marker)})
  for i:=0;i<2;i++{func(){defer func(){if recover()!=marker{t.Error("panic value not retained")}}();panicOnce();t.Error("panic became normal return")}()}
  if calls!=1{t.Fatal("panic retried original function")}
  value:=3;get:=sync.OnceValue(func()*int{return &value});p:=get();*p=9
  if get()!=p||*get()!=9{t.Fatal("pointer result copied object")}
 })
}
