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


## Mutation and rationale reconciliation — 2026-11-14

Refreshed the manifest and sidecar to source/test commit **9b3723e4c7f8778bc8c2eb25bc9bed0b0dfe2dda**.
This is an evidence refresh of the existing as-is model: no new behavior,
decision or diagram promotion. No artifact became superseded, so the prior
archive remains unchanged. All 13 decisions and 52 historical artifacts remain
intact. Test-fragment citations affected by the two added representative
scenarios were re-resolved by exact content; no blanket offset was used.
The current checker verifies 232 structured citation occurrences, including
38 cell reasons with accepted decision evidence and the standard CancelFunc
callee guarantee. The earlier count of 193 describes the prior reconciliation.

The committed-source staleness signal was observed before refreshing. Full
current-model, decision, pack, mutation and accounting acceptance is retained
in `docs/evidence/mutation-rationale-cost/`. Generic matrix mutation now kills
41 supported changes; source mutation kills four named faults. Four contract
limits and two queued cells without supported matrix operators remain outside
that mutation denominator. No OPEN question or implementation deviation remains.

```text
DSC CHECK: OK (2 states x 19 events, 38 cells, 11 guard groups)
REACHABILITY CHECK: OK (2/2 states reachable from 'Acquire_NoWaiters', 0 terminal)
```

**The component is in steady state; the standing instruction governs further changes; a stale manifest calls this prompt again.**


## F-09 observability reconciliation — 2026-11-15

Refreshed the manifest and sidecar to tested source/test commit **0df22e08d74cb266a1f0b3c54c2ef0e7979a9997**.
The as-is behavior, all thirteen accepted decisions and source digest remain
unchanged. This is an evidence refresh, with no model promotion or superseded
artifact to archive. The new weak test and comparison runner are watched.

The standalone F-09 omitted-unlink mutant survives the deliberately weak
result-only suite and is killed by the full cancellation cell. An executed
capacity canary proves the public projection before the slice evaluates F-09.
P-06b adds an existing DR-010 capacity assertion before a blocking call, so the
mutant now produces a completed failure instead of a truncated suite. All
existing assertions remain. Five source mutants and 41 matrix mutants are
killed; four contract limits and two unsupported queued matrix cells remain.

Observed stale-manifest output and full acceptance are retained in
`docs/evidence/semaphore-f09/`. The existing citation fragments remain in place:
zero citation line changes are needed; the added assertion is below the
referenced `TestStatePairs` declaration. The checker revalidates the current
structured citations. All 52 historical semaphore artifacts remain unchanged.
No OPEN questions or implementation deviations were added or resolved.

```text
DSC CHECK: OK (2 states x 19 events, 38 cells, 11 guard groups)
REACHABILITY CHECK: OK (2/2 states reachable from 'Acquire_NoWaiters', 0 terminal)
```

**The component is in steady state; the standing instruction governs further changes; a stale manifest calls this prompt again.**
