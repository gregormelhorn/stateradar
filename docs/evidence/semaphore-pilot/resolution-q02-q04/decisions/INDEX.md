# Accepted decisions

DR-001 / Q-01 remains in ../.. / resolution-q01/decisions.

- DR-002: Q-03 — Reject negative arguments before mutation.
- DR-003: Q-04 — Keep state unchanged after over-release panic.
- DR-004: Q-02 — Reject an impossible oversized acquisition promptly.

- DR-005: Q-05 — Explicit cancellation and release; no automatic reclamation.
  Contract and focused conformance acceptance complete; see ../../contracts-q05-q13/README.md.

- DR-006: Q-06 — Independent repeated acquisitions; self-blocking is possible.
  Contract and focused conformance acceptance complete; see ../../contracts-q05-q13/README.md.

- DR-007: Q-07 — Transferable release responsibility; aggregate accounting only.
  Contract and focused conformance acceptance complete; see ../../contracts-q05-q13/README.md.

- DR-008: Q-08 — Caller selects the instance and Context; no semantic-mismatch detection.
  Contract and focused conformance acceptance complete; see ../../contracts-q05-q13/README.md.

- DR-009: Q-09 — Require a conforming non-nil Context; no automatic repair/recovery.
  Contract and focused conformance acceptance complete; see ../../contracts-q05-q13/README.md.

- DR-010: Q-10 — Defined cancellation checkpoints and rollback of own holdings; transient reservations permitted.
  Contract and focused conformance acceptance complete; see ../../contracts-q05-q13/README.md.

- DR-011: Q-11 — No capacity-queue wait for TryAcquire; mutex waits allowed, no fixed latency bound.
  Contract and focused conformance acceptance complete; see ../../contracts-q05-q13/README.md.

- DR-012: Q-12 — FIFO grants without bypass; return order unspecified, no internal queue cap.
  Contract and focused conformance acceptance complete; see ../../contracts-q05-q13/README.md.

- DR-013: Q-13 — Release(0) is a logical no-op, not a wakeup/synchronization API.
  Contract and focused conformance acceptance complete; see ../../contracts-q05-q13/README.md.

All thirteen original questions have owner decisions and implemented contract/
focused conformance acceptance. Whole-model reconciliation remains separate.
