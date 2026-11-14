# Approved contract projection

The decision/expected-outcome checkpoint is plan.md, written before adding tests
or API contract comments. Runtime transitions remain unchanged in this step.

- DR-005/006 clarify independent request lifetimes and caller cleanup obligations.
- DR-007/008 clarify aggregate accounting and selected receiver/Context authority.
- DR-009 narrows supported inputs to conforming Contexts; unsupported methods
  are not mapped to invented outcomes or silently tested as supported.
- DR-010 separates internal grant from successful return and makes rollback/net
  accounting explicit at the existing cancellation checkpoints.
- DR-011 clarifies capacity waiting versus mutex waiting without adding a timer.
- DR-012 makes FIFO grant policy explicit, distinguishes return order and keeps
  the existing absence of a queue-count cap.
- DR-013 gives Release(0) a logical-no-op contract after the earlier DR-001 fix.

The diagram projects queue states at valid mutex-release boundaries. The
historical EligibleHeadPending state is not promoted into this projection:
source reasoning and the bounded Q-13 exploration show why the known stranded
zero-head path disappeared after DR-001. This is not a new whole-model
reachability proof or a rewritten/reconciled manifest.

SYS accounting and queue isolation apply at both projected states. SYS-Q01
progress still applies to head removal; DR-010 strengthens its description at
cancellation boundaries. Timeouts, retries, caller attribution and lifecycle
assumptions are explicitly covered by the accepted clauses. No additional
domain question or conflict was discovered during these tests. Complete model
reconciliation remains a distinct follow-up, not an unrecorded semantic choice.
