# Focused numeric-contract refinement

This is a partial continuation of DR-001, not a full 57-cell resolution.
At the resolution checkpoint, no source implementation had changed. The
subsequent red/green implementation is recorded in deviation-report.md.

- DR-002: negative constructor size or method weight is rejected with panic,
  before state mutation. Zero is allowed. For valid initialization, enforce
  SYS-Numeric: 0 <= cur <= size <= MaxInt64 under every API transition.
- DR-003: Release(n) with n > cur rejects with panic, preserving the counter
  and queue. Check n against cur before subtracting; never compute an invalid
  new counter first. Valid Release still notifies the eligible FIFO prefix.
- DR-004: oversized Acquire returns an explanatory error without waiting on
  Done. Its existing initial Done check is retained (pre-canceled contexts still
  return their context error). Other cancellation races remain Q-10.
- DR-002/003: accepted additions are bounded by size-cur and subtractions by cur;
  these bounds prevent signed overflow for all supported nonnegative int64
  values. Negative Release(MinInt64) cannot wrap the counter before rejection.

Q-05 through Q-13 remain open. This narrows guarded branches of the original
cells; it does not resolve other lifecycle/ownership/cancellation policy.
