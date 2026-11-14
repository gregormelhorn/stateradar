# Resolved evaluation model

The current reconciled model follows all thirteen accepted owner decisions. It retains 19 events, projects two valid queue states and contains 38 cells. There are 34 executable representative cell scenarios, four explicit contract limits, 16 named pair-ordering scenarios, and 14 retained adversarial trace identities. No OPEN question or unresolved implementation deviation remains.

The approved candidate was promoted after committed-source preconditions passed. See extraction.md for the guard abstraction and coverage limits; matrix-coverage.json and scenario-coverage.json bind the tests. Full decision and upstream regression acceptance remains mandatory via verify_q01.py. The original blind analysis and its historical source/manifest remain unchanged.

## Reconciliation — 2026-11-14

Promoted `to-be.machine.mmd` to `as-is.machine.mmd` after all preconditions passed on committed candidate **0b7502b4915de4996e71fbd56baa55b4377dbcfe**. Manifest and sidecar pin that source/test revision. The subsequent artifact-only reconciliation commit changes no watched source or test, so the anchor remains fresh.

Archived the historical diagram, approved delta and resolved deviation report under `archive/2026-11-14/`. Active decisions retain the canonical owner attribution and scope; a checker compares all thirteen copies to their accepted records. Historical source and all 52 retained artifacts remain unchanged. The previous preflight block is resolved.

Citation refresh: the generic `refresh_citations.py` reported **0** because its matcher recognizes Python paths, not these Go paths. This was not treated as a Go refresh. Current Go and contract anchors were rebuilt from their fragments during candidate preparation, and **193 structured citation occurrences** are verified by the current checker (including decision, doctrine, trace and coverage anchors). The separate active-Markdown scan is recorded in `evidence/markdown-citations.txt`; it has zero unresolved anchors. No blanket line-number offset was used.

Executed preconditions and post-promotion results are in `evidence/`: the full decision/upstream suite, 32 ordinary and six scheduled groups x 50 with race detection, four faulty implementation overlays, 340 cell and 160 pair-ordering executions, seven artifact red probes, the deliberately wrong-cell red probe, guard proofs and the historical reproduction (seven gates, upstream race suite, ten probes x five). The full pack and nine accounting tests also pass. No model/API calls were required.

```text
DSC CHECK: OK (2 states x 19 events, 38 cells, 11 guard groups)
REACHABILITY CHECK: OK (2/2 states reachable from 'Acquire_NoWaiters', 0 terminal)
```

Questions remaining OPEN: **none**. Open implementation deviations: **zero**. The four contract limits are documented coverage exclusions, not passed behavioral tests or newly resolved questions. The matrix is a guarded abstraction; finite tests do not establish every scheduler interleaving or a fixed latency guarantee.

**The component is in steady state; the standing instruction governs further changes; a stale manifest calls this prompt again.**
