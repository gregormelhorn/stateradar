Q-C1
Question: CloseDeadlineExpired in ClosurePending — no caller-visible termination.
After close_timeout expires and close_transport() is called, the code still
awaits connection_lost_waiter. If the transport is stalled and connection_lost()
never fires, callers in recv() and send_context() are blocked indefinitely
despite the configured close_timeout. Requirements R-07 and R-11 are violated.
Current: close_transport() runs at send_context.go:872, sets recv_exc to
TimeoutError, then awaits connection_lost_waiter at send_context.go:874 —
re-entering the wait the timeout was meant to bypass.
Expected: CloseDeadlineExpired must force progress to ClosureObservable,
releasing blocked callers even if TransportLost has not arrived.
ODC: fault F-20 (blocked progress after terminal event; secondary F-07 lifecycle coupling), trigger: step-4 matrix walk
**Status:** OPEN
