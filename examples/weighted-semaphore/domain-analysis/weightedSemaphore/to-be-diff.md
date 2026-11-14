# Approved reconciliation delta

DR-001 removes Acquire_EligibleHeadPending at valid mutex-release boundaries;
G-10 proves preservation of the blocked-head invariant. Retain two queue states
and all 19 event identities: 38 cells. The invocation axis remains prose, not
extra Cartesian grid states: entry/queued/granted/success/error are distinct
lifetime stages. DR-004 removes the oversized off-queue wait. DR-002/003 remove
negative/corrupted counter behavior from valid reachable state space. DR-005..013
replace accidental gaps by explicit obligations, detection limits, Context
preconditions, cancellation checkpoints, FIFO and zero-release semantics.

All 13 decisions are accepted; no domain decision is invented. Two UV-ContextFault
cells lack a guaranteed outcome by DR-009, and two UV-Delay cells specify no time
bound by DR-011. These four cells have explicit untestable-via-seam reasons;
they are not silently counted as behavior passes. Thirty-four cells have
executable observations, supplemented by prior boundary/scenario suites.

The old full pilot remains immutable in docs/evidence/semaphore-pilot/analysis.
Its old diagram is staged here only for the later archive-and-promote step.
