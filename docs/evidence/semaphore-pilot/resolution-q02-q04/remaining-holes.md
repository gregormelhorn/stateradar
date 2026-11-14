# Remaining scope

Q-01 (DR-001), Q-03 (DR-002), Q-04 (DR-003) and Q-02 (DR-004) are accepted.
Q-05 through Q-12 (DR-005 through DR-012) are accepted; their contract/conformance
follow-up is pending. Q-13 remains OPEN in open-questions.md. These decisions
do not approve the earlier recommendations on Release(0).

This slice gives 13 original cells guarded numeric refinements with explicit
test/DR links; 44 are outside it. Other branches of those 13 cells remain open.
The matrix-coverage.json enumerates every original cell, including the old
EligibleHeadPending state; it does not assert that historical state is reachable
in the fixed implementation. Constructor checks apply independently of an
existing instance. No cell is labelled untestable to conceal a missing decision.

DR-001's targeted zero-progress scenarios remain mandatory and run in the same
acceptance command. Full model reconciliation and mutation-registry support
still require their separate prerequisites.
