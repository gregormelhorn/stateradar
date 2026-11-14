# Reconcile preflight — 2026-11-14

**BLOCKED(reconcile): the full promotion prerequisites are not yet present.**
No model, sidecar, manifest, component source or test was changed by this run.
Checked source/pack revision: `fd7395c8af3a19eaed38d6df13d1c4e1afc095e1`.

The prior recommendation to proceed directly to Stage 06 was premature. All
thirteen decisions and their focused contract/scenario acceptance are complete,
but that is not yet a complete updated matrix with cell-by-cell acceptance.
This is a missing analysis/test-generation deliverable, not a new unanswered
domain question or a demonstrated runtime regression.

## Executed checks

| Command / purpose | Exit | Result |
| --- | --- | --- |
| `python examples/weighted-semaphore/verify_q01.py --output-dir /tmp/semaphore-reconcile-preflight-results` | 0 | 32 ordinary and 6 scheduled groups x 50 with race detector; upstream regression suite; four faulty overlays detected; contract/guard checks pass. |
| Full pack gate set (`/tmp/stateradar-main-full-gates.sh`) | 0 | Type checking, consistency, registry, deterministic and routing selftests, tool regressions, golden sidecar/reachability pass. |
| `python tools/selftest/test_pilot_accounting.py` | 0 | Nine accounting tests pass. |
| `python docs/evidence/semaphore-pilot/reproduce.py --source-repo /tmp/stateradar-third-sync --output /tmp/semaphore-reconcile-historical` | 0 | Frozen upstream analysis: 7/7 gates, upstream race tests and 10 observations x 5 pass. |
| `python tools/dsc_check.py docs/evidence/semaphore-pilot/analysis --repo examples/weighted-semaphore --model as-is.machine.mmd` | 1 | 57 citation failures against current source; the upstream SHA is not a revision in the evaluation repository. |
| `python tools/dsc_check.py docs/evidence/semaphore-pilot/contracts-q05-q13 --repo . --model to-be.machine.mmd` | 2 | Candidate has no analysis.json sidecar. |

All Python commands used the repository `.venv/bin/python`. Full output is
retained beside this report. The historical check is green only against its
pinned original source; it must not be presented as current-model acceptance.
All 52 archived pilot artifact hashes remain unchanged.

## Concrete missing prerequisites

1. The historical sidecar has 3 states, 19 events, 57 cells, 13 historical OPEN
   questions and no behavioural DR links. The active decision register correctly
   has 13 resolved questions. These are different revisions, not contradictory
   current owner answers.
2. The approved focused projections have no complete replacement disposition
   matrix or sidecar. The numeric coverage explicitly contains 13 guarded
   refinements and 44 cells outside that slice. The final contract suite maps
   clauses/events to tests, and explicitly does not claim a one-test-per-cell
   suite. Passing it cannot fill the missing cell proof silently.
3. The old model includes the stranded eligible head, oversized off-queue wait
   and corrupted-counter paths removed by DR-001..004. The current supported
   queue-boundary projection needs its full reachability/guard evidence before
   those paths can be retired from the active analysis.

## Required continuation before promotion

- Finish the approved to-be matrix and its guarded outcomes from DR-001..013,
  keeping unsupported Context behavior explicitly outside the accepted input
  precondition. Account for every retained state/event cell and every removed
  historical state, with evidence rather than a header/count change.
- Complete and execute cell-level coverage plus scenarios for that matrix;
  reuse existing behavior tests where they actually establish the cell outcome.
  Add missing behavioral cases openly in the Stage-04 work, not inside a
  supposedly artifact-only reconciliation. Demonstrate checker failure paths.
- Refresh citations by content using the pack tools, connect each behavioural
  DR, emit the candidate analysis.json and verify it against current source.
- Then rerun Stage 06: preserve the historical archive, promote only after all
  prerequisites pass, and stamp the evaluation repository SHA with correct
  repository-relative watch paths. Verify dsc_check and all other gates again.

The governing [Stage-06 prompt](../../../../prompts/06-reconcile.md), Step 0,
says: “If a precondition fails: stop and report. Do not promote.” It also states
that there is no reconcile-lite. Accordingly, no archive move, citation rewrite,
manifest stamp or as-is promotion has been performed. Updating only the SHA
would turn a known incomplete analysis into a misleading freshness signal.

## Subsequent resolution

The block above describes the preflight at fd7395c and remains historical evidence.
The [current evaluation analysis](../../../../examples/weighted-semaphore/domain-analysis/weightedSemaphore/summary.md)
now supplies the missing matrix, cell acceptance and sidecar. All preconditions
were rerun on committed candidate 0b7502b4915de4996e71fbd56baa55b4377dbcfe before
Stage-06 promotion. No historical pilot artifact or blind prediction was rewritten.
