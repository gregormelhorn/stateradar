# gobreaker — Traditional Review + Statechart Comparison

**Date:** 2026-08-06
**Method:** Combined (traditional review + statechart cross-check)

## Findings

- **R3:** OnStateChange callback under mutex → deadlock risk (confirmed by issue #37)
- **R2:** State() getter mutates internal state (surprising API contract)
- **Stale done() callback:** TwoStepCircuitBreaker.Allow() done() silently dropped when generation changes. Issue #122 filed.
- **Reviewer cross-check:** 17 findings from traditional review, 7 structural from statechart — complementary.
