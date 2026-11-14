gobreaker.go:23
	// ErrTooManyRequests is returned when the CB state is half open and the requests count is over the cb maxRequests

gobreaker.go:25
	// ErrOpenState is returned when the CB state is open

gobreaker.go:43
// Counts holds the numbers of requests and their successes/failures.
// CircuitBreaker clears the internal Counts either
// on the change of the state or at the closed-state intervals.
// Counts ignores the results of the requests sent before clearing.

gobreaker.go:79
// Settings configures CircuitBreaker:
//
// Name is the name of the CircuitBreaker.
//
// MaxRequests is the maximum number of requests allowed to pass through
// when the CircuitBreaker is half-open.
// If MaxRequests is 0, the CircuitBreaker allows only 1 request.
//
// Interval is the cyclic period of the closed state
// for the CircuitBreaker to clear the internal Counts.
// If Interval is less than or equal to 0, the CircuitBreaker doesn't clear internal Counts during the closed state.
//
// Timeout is the period of the open state,
// after which the state of the CircuitBreaker becomes half-open.
// If Timeout is less than or equal to 0, the timeout value of the CircuitBreaker is set to 60 seconds.
//
// ReadyToTrip is called with a copy of Counts whenever a request fails in the closed state.
// If ReadyToTrip returns true, the CircuitBreaker will be placed into the open state.
// If ReadyToTrip is nil, default ReadyToTrip is used.
// Default ReadyToTrip returns true when the number of consecutive failures is more than 5.
//
// OnStateChange is called whenever the state of the CircuitBreaker changes.
//
// IsSuccessful is called with the error returned from a request.
// If IsSuccessful returns true, the error is counted as a success.
// Otherwise the error is counted as a failure.
// If IsSuccessful is nil, default IsSuccessful is used, which returns false for all non-nil errors.

gobreaker.go:133
// TwoStepCircuitBreaker is like CircuitBreaker but instead of surrounding a function
// with the breaker functionality, it only checks whether a request can proceed and
// expects the caller to report the outcome in a separate step using a callback.

gobreaker.go:140
// NewCircuitBreaker returns a new CircuitBreaker configured with the given Settings.

gobreaker.go:182
// NewTwoStepCircuitBreaker returns a new TwoStepCircuitBreaker configured with the given Settings.

gobreaker.go:200
// Name returns the name of the CircuitBreaker.

gobreaker.go:205
// State returns the current state of the CircuitBreaker.

gobreaker.go:215
// Counts returns internal counters

gobreaker.go:223
// Execute runs the given request if the CircuitBreaker accepts it.
// Execute returns an error instantly if the CircuitBreaker rejects the request.
// Otherwise, Execute returns the result of the request.
// If a panic occurs in the request, the CircuitBreaker handles it as an error
// and causes the same panic again.

gobreaker.go:247
// Name returns the name of the TwoStepCircuitBreaker.

gobreaker.go:252
// State returns the current state of the TwoStepCircuitBreaker.

gobreaker.go:257
// Counts returns internal counters

gobreaker.go:262
// Allow checks if a new request can proceed. It returns a callback that should be used to
// register the success or failure in a separate step. If the circuit breaker doesn't allow
// requests, it returns an error.
