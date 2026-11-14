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
