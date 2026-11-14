# Remaining scope

Q-01 (DR-001), Q-03 (DR-002), Q-04 (DR-003) and Q-02 (DR-004) are accepted.
Q-05 through Q-13 (DR-005 through DR-013) now have completed contract and focused
conformance acceptance in ../contracts-q05-q13. No original domain question
remains OPEN. This does not promote the historical as-is analysis.

This slice gives 13 original cells guarded numeric refinements with explicit
test/DR links; 44 are outside it. Other branches of those 13 cells remain open.
The matrix-coverage.json enumerates every original cell, including the old
EligibleHeadPending state; it does not assert that historical state is reachable
in the fixed implementation. Constructor checks apply independently of an
existing instance. No cell is labelled untestable to conceal a missing decision.

DR-001's targeted zero-progress scenarios remain mandatory and run in the same
acceptance command. Full model reconciliation and mutation-registry support
still require their separate prerequisites.
