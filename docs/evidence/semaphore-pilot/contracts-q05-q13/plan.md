# Contract/conformance checkpoint before implementation

All Q-01..Q-13 have accepted DRs. This step implements the outstanding Q-05..Q-13
contracts and tests, preserving the prior numeric/progress acceptance suites.
Runtime behavior is expected to conform already; any red original-code test is
a deviation, not a reason to weaken a test. Tests are hardened with deliberately
faulty disposable overlays, followed by green runs of the unmodified logic.

## Approved outcomes

- DR-005: cancel and consume abandoned pending results; success holds weight
  until matching release even after cancellation. New instances do not clean old ones.
- DR-006: repeated pending/held acquisitions are independent and can self-block.
- DR-007: release responsibility can transfer; only aggregate accounting is checked.
- DR-008: receiver and Context selection are caller responsibilities.
- DR-009: conforming non-nil Context required; nil Done is valid. Invalid methods
  carry no recovery/latency guarantee and are not assigned invented outcomes.
- DR-010: initial and queued-grant cancellation checkpoints; rollback before
  error return; success after the last check may survive cancellation. Temporary
  reservation is observable; net own-accounting is the obligation.
- DR-011: no capacity-queue waiting in TryAcquire; mutex waits permitted, no fixed
  time bound. Absence of a time bound is a contract, not a finite-test theorem.
- DR-012: enqueue-order FIFO grants without bypass; return order unspecified;
  no internal queue cap. Finite tests cannot prove unbounded queue size.
- DR-013: Release(0) has no capacity/queue/grant effect in valid reachable states.

## Seam

Ordinary cases assert public return values, errors, completion channels and
capacity via TryAcquire/Release. The existing read-only queue-length barrier
establishes enqueue order. No test writes the counter, queue or ready channels.
For exact concurrency checkpoints, a separate disposable Go compiler overlay
adds scheduling callbacks at reviewed source anchors. Hooks only pause/resume
execution, and never choose branches or mutate component state. Assertions
remain at the public API. The installed/runtime source gets no test hooks.
A dedicated overlay suite runs separately; it is never silently skipped.
Tests use bounded timeouts solely to fail stalled execution, not as API promises.
