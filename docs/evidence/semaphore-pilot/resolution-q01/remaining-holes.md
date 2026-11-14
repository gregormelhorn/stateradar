# Remaining scope

Q-01 is accepted as DR-001. Q-02 through Q-13 remain OPEN, with their original
options and proposals preserved in open-questions.md. Acceptance of Q-01 is not
acceptance of those other recommendations.

The original 57-cell grid is an as-is evidence artifact. Only a guarded subcase
of `Acquire_WaitersPending x ContextDone` is decided here, including the P-07a
ordering and T-10 boundary control. Other branches in that cell still depend
on Q-10; aliases and invalid-weight cases still depend on Q-03/Q-12/Q-13.
They have not been relabelled as approved transitions to make a complete grid.

This is a partial DR-by-DR implementation, not a completed full Step-03/04/06
cycle. matrix-coverage.json enumerates all original cells and identifies the
one partially covered cell without calling the remainder untestable. A full
cell suite and reconciliation remain pending their own decisions/preconditions.
