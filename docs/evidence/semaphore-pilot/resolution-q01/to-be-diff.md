# DR-001: partial resolution before implementation

Only Q-01 has an owner decision. No conflict with the other answers exists:
there are no other accepted answers. Q-03 still governs invalid signed inputs;
Q-10 still governs other cancellation races; Q-12 still governs general backlog
and scheduling policy; Q-13 still governs the broader Release(0) contract.

The change is a guarded refinement of the original
`Acquire_WaitersPending x ContextDone` cell (P-07a and T-10), not approval of all
other branches in that cell or of the entire 57-cell pilot grid.

- DR-001 removes the valid-input branch that cancels a blocking positive head
  at full capacity and leaves an eligible zero-weight head stranded.
- DR-001 replaces it with notification of the eligible FIFO prefix. If only
  zero requests remain, the queue becomes empty. If a positive blocked tail
  remains, it stays queued. Notifications reserve zero weight for zero requests.
- DR-001 does not permit zero requests to bypass an earlier positive blocker.
- DR-001 adds SYS-Q01: once head removal exposes a live zero-weight FIFO prefix,
  that prefix is notified without another input. Eventual return assumes normal
  goroutine scheduling and no cancellation of those zero requests.
- DR-001 preserves SYS-01 accounting under the existing valid-input assumptions:
  zero grants do not free or consume positive weight. No real-time scheduler
  bound is imposed by the bounded test timeout.

The original as-is diagram and matrix remain in ../analysis. The adjacent
`to-be.machine.mmd` applies only this guarded change. It is not a fully resolved
whole-component model; no global reachability/promotion claim follows from it.
The focused decision matrix gives the distinct approved scenarios that the
broader pilot cell grouped together. The remaining original cell branches are
tracked explicitly in matrix-coverage.json and remaining-holes.md.

This refinement was recorded before the implementation change. Step-04
behavior tests then established the deviation before the fix; see
[deviation-report.md](deviation-report.md) for the completed red/green slice.
