# Q-05 through Q-13: completed contracts and focused conformance

All thirteen original questions now have owner decisions. DR-013 accepts the
post-fix logical-no-op contract for Release(0). The remaining nine decisions are
implemented in the evaluation [CONTRACT.md](../../../../examples/weighted-semaphore/CONTRACT.md)
and public API comments, and exercised by ordinary and scheduled behavior tests.

No additional runtime fix was needed: the existing implementation conforms to
the tested decisions. A Go scanner comparison found the runtime token stream
unchanged (632 tokens, excluding comments). Upstream tests, previous decision
tests and all archived pilot hashes are unchanged. See [audit.txt](audit.txt).

## Acceptance

Run from the pack root with the documented Go/Python dependencies:

```sh
.venv/bin/python examples/weighted-semaphore/verify_q01.py --output-dir /tmp/semaphore-contract-results
```

The existing CI entry point now includes these contracts, exact discovery,
scheduling scenarios and four intentionally faulty overlays. It passed:

- **32 ordinary groups x 50 = 1,600 group passes**, checking all 66 ordinary
  test/subtest names and exact repetition counts.
- **6 scheduled groups x 50 = 300 group passes**.
- Both suites run with the Go race detector: **1,900 group executions total**.
- Unchanged upstream plus decision regression suite with the race detector.
- All original and numeric guard checks; exact contract text, DR links and
  reverse test coverage for 27 clauses across nine decisions.
- Four faulty overlays fail their intended named behavior tests, with completed
  Go failure events rather than compile failures/timeouts/crashes.

The full [acceptance output](acceptance.txt) and [fault assertions](fault-probes.txt)
are retained. [Pack gates](pack-gates.txt) and the additional nine
[accounting selftests](accounting-tests.txt) pass. The frozen upstream baseline
also reproduces independently: [7/7 original artifact gates and all original
observation probes](historical-reproduction.txt). Those observations describe
the historical baseline, not conformance of the modified evaluation copy.

## Decision coverage

| Decision | Behavior checked | Limits |
| --- | --- | --- |
| DR-005 | Pending cancellation, holding after later cancellation, independent new instances | Caller cleanup obligations are also normative documentation. |
| DR-006 | Separate repeated held/pending acquisitions, cancel one vs shared Context, self-blocking setup | No caller identity is invented. |
| DR-007 | Release from another goroutine; duplicate release can pass aggregate checks; aggregate over-release still fails | Deliberate caller misuse demonstrates a detection limit, not permitted usage. |
| DR-008 | Wrong receiver affects only itself; only the supplied Context governs the call | Intent cannot be inferred from arguments. |
| DR-009 | Conforming custom Context and valid nil Done channel | Faulty Context behavior is outside the precondition, not assigned a fake guarantee. |
| DR-010 | Pre-cancel, live cancellation/grant races, both rollback branches, late success and visible temporary reservation | Deterministic checkpoints use the scheduling-only overlay described below. |
| DR-011 | TryAcquire returns without queueing; cancellation before mutex acquisition is checked | No finite test proves an absence of all latency bounds. |
| DR-012 | Head-of-line blocking, no TryAcquire bypass, FIFO grants, reverse API-return order, 32-request backlog | Finite backlog is a control, not proof of an infinite bound. |
| DR-013 | Zero release with empty, held and blocked-queue states, including zero capacity | DR-001 tests continue to require progress without a rescue Release(0). |

`contracts.json` links each clause and original event ID to its tests and DR.
`check_contracts.py` rejects missing/drifted normative text and missing test/DR
coverage. Its observed failure paths are retained in [contract-red.txt](contract-red.txt)
and [coverage-red.txt](coverage-red.txt). This is focused contract/scenario
coverage, not a claim of a newly generated one-test-per-original-cell suite.
The old 57-cell analysis remains frozen; whole-model reconciliation is separate.

## Scheduling seam and failure probes

The regular tests assert public results, returned errors, completions and
capacity via TryAcquire/Release. The existing private queue-length observation
is used only to establish enqueue order; no counter or queue field is written.

`examples/weighted-semaphore/schedule/run.py` makes a disposable Go compiler
overlay. Exact source anchors insert pause/resume callbacks at the initial
check, cancellation selection, grant receipt and final queued-success check.
Hooks never choose branches or modify component state. The test controls only
when execution continues. One test also holds the existing mutex as a scheduling
barrier. Runtime source has no added hooks. Hook tests are separate, mandatory,
exactly counted tests; no Skip path exists.

Fault overlays separately omit either rollback, permit TryAcquire to bypass the
queue, or charge weight on Release(0). Each is rejected by the intended test.
These are local sensitivity probes, not a new generic fault-registry or
whole-program mutation-coverage claim. The unchanged original logic passes.

No timing bound, scheduler-fairness proof, unsupported-Context recovery,
upstream release or completed whole-component reconciliation is claimed.
