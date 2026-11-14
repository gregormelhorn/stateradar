# As-is validation

| Upstream test | Statechart walk and coverage |
|---|---|
| TestWeighted | Repeated entering → fast or queued → granted → success → Release. Concurrent workers, including a zero-weight worker. semaphore/semaphore_test.go:41 ("HammerWeighted(sem, int64(i), loops)"). |
| TestWeightedPanic | No waiters and no charge → Release subtracts and panics after unlock. Recovery checked only for panic presence. semaphore/semaphore_test.go:56 ("w.Release(1)"). |
| TestWeightedTryAcquire | Empty queue and held charge → fit true, then shortage false; Release restores capacity and cycle repeats. semaphore/semaphore_test.go:75 ("want := []bool{true, false, true, false}"). |
| TestWeightedAcquire | Same capacity transitions; shortage queues then context deadline removes the waiter. semaphore/semaphore_test.go:89 ("ctx, cancel := context.WithTimeout(ctx, 10*time.Millisecond)"). |
| TestWeightedDoesntBlockIfTooBig | Oversized call may use off-queue wait or see already-canceled context at entry; ordinary callers progress. Goroutine launch does not force off-queue blocking before others. semaphore/semaphore_test.go:121 ("go sem.Acquire(ctx, n+1)"). |
| TestLargeAcquireDoesntStarve | Large head waits while releases accumulate; smaller requests cannot bypass; drain admits head. semaphore/semaphore_test.go:167 ("sem.Acquire(ctx, n)"). |
| TestAllocCancelDoesntStarve | Cancel oversized-relative-to-free but feasible head below capacity; small request succeeds through rescan or direct admission after removal. The large call's return value is not asserted. semaphore/semaphore_test.go:195 ("go cancel()"). |
| TestWeightedAcquireCanceled | Cancel before release; remove-first or grant/rollback; full capacity remains available afterwards. Preclosed entry also refuses when it fits. semaphore/semaphore_test.go:216 ("cancel()"); semaphore/semaphore_test.go:228 ("if !sem.TryAcquire(2) {"); semaphore/semaphore_test.go:234 ("if err := sem.Acquire(ctx, 1); err != context.Canceled {"). |
| Example_workerPool | Caller acquires before each launch; worker defers release; final size-weight acquisition joins or admits after workers release, before printing. No explicit release is required for this example's final private instance use. semaphore/semaphore_example_test.go:40 ("defer sem.Release(1)"); semaphore/semaphore_example_test.go:49 ("if err := sem.Acquire(ctx, int64(maxWorkers)); err != nil {"). |

Executed upstream: `go test -timeout=30s ./semaphore` passed (log 012).
Executed overlay: `go test -timeout=30s -overlay domain-analysis/weightedSemaphore/_probe/overlay.json -run ^TestPilot -count=5 -v ./semaphore` passed all three probes in each of five repetitions (log 052). Queue inspection is scheduling-only; the assertions use return values, panic recovery, and public TryAcquire/Release. The zero-head probe supports the pair reachability edge. No upstream file changed. 

Executed upstream race run: `go test -race -timeout=45s ./semaphore` passed (log 100). This records one clean execution; the source replay did not use race-detector silence as synchronization proof.
Executed full repository: `go test -timeout=30s ./...` passed (log 117).
Executed final race overlay: `go test -race -timeout=45s -overlay domain-analysis/weightedSemaphore/_probe/overlay.json -run ^TestPilot -count=5 -v ./semaphore` passed all five probes in each of five repetitions (log 111). The scheduling Context wrapper delays the first call before mutex admission; the second acquires before the first, and the first succeeds only after Release. The completed-cancellation probe verifies that the successful charge survives cancellation and is restored by explicit Release.
