
<!-- terminal: Released -->

## Guard notes

Proof outcomes from `check_guards.py` (output in `guard-results.txt`).

* **G-01 construction validation** (channel.go:59-67), initial transition: invalid capacity / nil Factory / nil Close / valid. **proven** (disjoint, covering). Boundaries: InitialCap = MaxIdle−1, MaxIdle, MaxIdle+1; MaxCap = MaxIdle−1, MaxIdle, MaxIdle+1; InitialCap = −1, 0, 1. Implication proven: a valid configuration has MaxIdle ≥ 0 and MaxCap ≥ InitialCap ≥ 0 (no negative channel capacity). MaxCap = 0 is valid (every Get waits; Q-20).
* **G-02 idle-expiry decision** (channel.go:115-116, same predicate on the waiter path channel.go:141-142): discard ⇔ IdleTimeout > 0 ∧ age > IdleTimeout. **proven**. Boundaries: age = IdleTimeout keeps the connection (strict `Before`); IdleTimeout ≤ 0 never discards.
* **G-03 ping validity** (channel.go:123-124): **not-formalizable: external-call** — the branch depends on the user's Ping result. Inspection: Ping set and error → Close and retry; Ping set and nil → return; Ping nil → return without check. Unproven.
* **G-04 Get slow path** (channel.go:133, 150, 155): wait (openingConns ≥ MaxCap) / ErrClosed (below cap, factory nil) / factory error / create. **proven**. Boundaries: openingConns = MaxCap−1 creates, = MaxCap waits, = MaxCap+1 waits (reachable only through counter drift, Q-10). Ordering note (finding, not a PA-1 violation): the capacity test precedes the released test, so in the Release window a Get at capacity waits instead of returning ErrClosed (Q-07).
* **G-05 waiter wake-up** (channel.go:138-148): request channel closed / handed connection expired / deliver. **proven** (disjoint, covering). Inspection: no code closes a request channel, so the first branch (`ErrMaxActiveConnReached`) is unreachable as-is (Q-01, Q-03).
* **G-06 Put routing** (channel.go:168, 174, 179, 189-196): nil / released / waiter present / idle not full / idle full. **proven** under NAT 0 ≤ idle ≤ MaxIdle, waiters ≥ 0. Boundaries: idle = MaxIdle−1 enqueues, = MaxIdle closes; waiters = 0 enqueues, = 1 hands off. MaxIdle = 0: every Put without a waiter closes.
* **G-07 Close routing** (channel.go:203, 208): nil / released / close. **proven**.
* **G-08 Release routing** (channel.go:234): already released / release. **proven**.
* **G-09 Get entry** (channel.go:105, 111): nil snapshot / received nil from a closed channel / proceed. **proven**.

## Counts

7 states × 22 events = 154 cells. Holes: see `summary.md` (counted by `analysis.json`).
