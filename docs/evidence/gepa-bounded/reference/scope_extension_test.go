package reference
import("testing";"time")
func TestRearmedWhilePriorCallbackRuns(t *testing.T){
 entered,release,done:=make(chan struct{}),make(chan struct{}),make(chan struct{})
 timer:=time.AfterFunc(0,func(){close(entered);<-release;close(done)})
 defer timer.Stop()
 defer func(){close(release);select{case <-done:case <-time.After(2*time.Second):t.Error("cleanup watchdog")}}()
 select{case <-entered:case <-time.After(2*time.Second):t.Fatal("start watchdog")}
 if timer.Reset(time.Hour){t.Fatal("expired timer reset must return false")}
 if !timer.Reset(time.Hour){t.Fatal("intervening reset makes the next reset active even while the old callback runs")}
 if !timer.Stop(){t.Fatal("new scheduled execution should be stoppable")}
}

func TestRepeatedStopFalseBeforeCallback(t *testing.T){
 timer:=time.AfterFunc(time.Hour,func(){t.Error("stopped callback ran")})
 if !timer.Stop(){t.Fatal("first Stop should prevent the pending callback")}
 if timer.Stop(){t.Fatal("second Stop must return false although the callback was prevented")}
}
