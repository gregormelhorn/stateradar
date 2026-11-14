# Focused invariants and limits

For every original instance state (Acquire_NoWaiters, Acquire_WaitersPending,
Acquire_EligibleHeadPending), DR-002/003 add SYS-Numeric: a rejected numeric
operation does not change aggregate weight or the queue; valid arithmetic
preserves 0 <= cur <= size <= MaxInt64. Constructor validation establishes the
base case. Initial state is obtained through NewWeighted, never field mutation.
The historical EligibleHeadPending state's global reachability is not asserted.

DR-001 zero-weight progress remains mandatory. DR-004 removes the unfulfillable
oversized wait for live conforming contexts. A pre-canceled context keeps its
existing error priority. Mutex timing, broken custom contexts, caller ownership,
cleanup and general scheduling policy remain Q-05..Q-13. No new timeout, retry,
queue cap, lifecycle/reset or ownership policy is introduced. Overflow proof
uses the supported nonnegative domain, not a claim that arbitrary invalid
caller histories are safe. Public APIs must reject attempts to leave that domain.
