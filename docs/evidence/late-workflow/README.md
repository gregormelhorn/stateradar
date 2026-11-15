# Late-completion Testgen integration

The English Testgen prompt now requires an explicit applicability decision for
each trace in a separate reviewed inventory. `tools/check_late_workflow.py`
checks coverage, citations, contract facts, seam availability, accepted DR links,
profile/cell/order agreement and four-canary prerequisites. Its execution mode
replays complete raw Go evidence, checks current input/source hashes and rejects
partial or stale runs. The normal addrConn runner calls both stages.

## Executed addrConn result

| Check | Result |
|---|---|
| Applicability inventory | 3 applicable scenarios; exact profile/cell/order/DR binding |
| Historical source | Both late windows fail in 5 repetitions; positive ordering passes |
| Corrected evaluation | 3 scenarios x 10 repetitions pass |
| Two guard-removal mutants | Declared target fails in every one of 5 repetitions |
| Four independent canaries | Each isolates its own failure cause in every one of 5 repetitions |
| Weak controls | All 6 variants survive 10 repetitions each |
| Generic dependency control | First weak canary survives; 5 dependents BLOCKED without execution |
| Workflow receipt replay | Raw discovery, trace agreement, input/source hashes and all repetitions pass |
| Existing regressions | Five upstream tests x 5 on each source; backoff 6 cells x 10 on evaluation |

## Scope and second candidate

AddrConn remains a three-scenario DR-001 evaluation with an idle transport,
not a complete matrix or production grpc-go change. The workflow adds no domain
semantics and leaves other accepted-but-unimplemented decisions pending.

Gobreaker is a readiness assessment of the archived source with SHA-256
`09a38e4ec94ee22405cea8a64bce908bfa764a5e8bc65a69016e1cf86bf3b1cc`.
The public `TwoStepCircuitBreaker.Allow`, `State` and `Counts` APIs establish
that an old completion is ignored after a new half-open generation starts.
The current completion then closes the breaker and another request succeeds.
The baseline passes 10/10 race-detector runs; removing the exact generation guard
causes the named stale-completion assertion to fail 5/5 times. No compilation,
crash, timeout or unrelated failure counts as this readiness red.

This is **not applicable** to the v1 terminal/idle-resource oracle: generation
rollover continues the component lifecycle, and this seam owns no resource that
must be released exactly once. No resource, terminal state or semantic decision
was invented to make it fit. The plan records this exclusion with citations.
There is still only one validated adapter for the shared late-completion oracle.
A future generation-isolation profile would require its own contract and probes.

## Evidence and reproduction

- `design.md`: design before implementation.
- `red-plan.txt`: pre-checker permissive scaffold; 13 intended rejection failures,
  plus one missing result-shape error. The error is not counted as detection proof.
- `green-plan.txt`: 15 plan tests pass after implementation.
- `red-execution.txt`: permissive execution scaffold; eight missing rejection
  failures and one missing successful-run count. The rejection failures cover
  stale inputs, missing canary execution, absent discovery, partial observations,
  per-repeat kills, cause isolation, source mismatch and raw/observation drift.
- `green-workflow.txt`: combined selftests (the final full gate log is authoritative
  for the final source).
- `production-rejections.txt`: actual CLI returns exit 2 for an omitted scenario,
  stale checker hash, and incomplete discovery even after updating its content hash.
- `addrconn/`: fresh raw historical/evaluation/full/weak runs, execution receipts,
  source snapshot, workflow receipt and the existing regression/control outputs.
- `gobreaker/`: public-API baseline and guard-removal outputs with a content receipt.
- `full-gates.txt`: full acceptance output; expected historical and mutant reds
  are success conditions, never suppressed failures.

```sh
LATE_EVIDENCE_DIR="$PWD/docs/evidence/late-workflow/addrconn" \
READINESS_EVIDENCE_DIR="$PWD/docs/evidence/late-workflow/gobreaker" \
bash docs/evidence/late-workflow/scripts/full_gates.sh \
  --checkout /path/to/clean/grpc-go-v1.18.0

python tools/check_late_workflow.py \
  examples/grpc-addrconn/late-completion/workflow.json \
  --evidence docs/evidence/late-workflow/addrconn
python tools/check_late_workflow.py \
  examples/gobreaker/late-completion-readiness/workflow.json
```

The gate chain includes all previous oracle, adapter, F-09, canary, mutation,
semaphore, model/sidecar, rules, routing/accounting, finding-benchmark, type and
pack consistency checks. No paid model calls or new blind pilot are needed.

## Evidence boundaries

Completeness is relative to the reviewed scope, not automatic discovery of every
source behavior. A fragment match checks citation integrity, not semantic truth.
The reader checks Go run/pass events, package completion and raw traces; it does
not authenticate arbitrary or malicious evidence producers. The language-neutral
oracle can be reused elsewhere, but another runtime needs its own executed
reader. The current generation reader handles one source and replace-block
mutants. A passing plan alone makes no execution claim; all-excluded plans report
zero applicable scenarios explicitly. Existing matrix checks remain mandatory.
