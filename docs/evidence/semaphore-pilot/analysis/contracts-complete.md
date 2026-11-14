semaphore/semaphore.go:5
Package semaphore provides a weighted semaphore implementation.

semaphore/semaphore.go:19
NewWeighted creates a new weighted semaphore with the given
maximum combined weight for concurrent access.

semaphore/semaphore.go:26
Weighted provides a way to bound concurrent access to a resource.
The callers can request access with a given weight.

semaphore/semaphore.go:35
Acquire acquires the semaphore with a weight of n, blocking until resources
are available or ctx is done. On success, returns nil. On failure, returns
ctx.Err() and leaves the semaphore unchanged.

semaphore/semaphore.go:109
TryAcquire acquires the semaphore with a weight of n without blocking.
On success, returns true. On failure, returns false and leaves the semaphore unchanged.

semaphore/semaphore.go:121
Release releases the semaphore with a weight of n.

/opt/homebrew/Cellar/go/1.27.3/libexec/src/context/context.go:68
A Context carries a deadline, a cancellation signal, and other values across
API boundaries.

Context's methods may be called by multiple goroutines simultaneously.

/opt/homebrew/Cellar/go/1.27.3/libexec/src/context/context.go:78
Done returns a channel that's closed when work done on behalf of this
context should be canceled. Done may return nil if this context can
never be canceled. Successive calls to Done return the same value.
The close of the Done channel may happen asynchronously,
after the cancel function returns.

WithCancel arranges for Done to be closed when cancel is called;
WithDeadline arranges for Done to be closed when the deadline
expires; WithTimeout arranges for Done to be closed when the timeout
elapses.

Done is provided for use in select statements:

 // Stream generates values with DoSomething and sends them to out
 // until DoSomething returns an error or ctx.Done is closed.
 func Stream(ctx context.Context, out chan<- Value) error {
 	for {
 		v, err := DoSomething(ctx)
 		if err != nil {
 			return err
 		}
 		select {
 		case <-ctx.Done():
 			return ctx.Err()
 		case out <- v:
 		}
 	}
 }

See https://go.dev/blog/pipelines for more examples of how to use
a Done channel for cancellation.

/opt/homebrew/Cellar/go/1.27.3/libexec/src/context/context.go:111
If Done is not yet closed, Err returns nil.
If Done is closed, Err returns a non-nil error explaining why:
DeadlineExceeded if the context's deadline passed,
or Canceled if the context was canceled for some other reason.
After Err returns a non-nil error, successive calls to Err return the same error.

/opt/homebrew/Cellar/go/1.27.3/libexec/src/context/context.go:228
A CancelFunc tells an operation to abandon its work.
A CancelFunc does not wait for the work to stop.
A CancelFunc may be called by multiple goroutines simultaneously.
After the first call, subsequent calls to a CancelFunc do nothing.
