# grpc-go — addrConn reconnect/backoff lifecycle

**Fix:** [PR #2669](https://github.com/grpc/grpc-go/pull/2669) "client: reset backoff to 0 after a connection is established" (linked issues #2663, #2636)
**Commit analyzed:** v1.18.0 (buggy; the fix landed later)
**Date:** 2026-08-07
**Pack version:** v1.36 (02-pilot v1.15 — first pilot with ODC fields, SHARD categories, and the guard_proofs library)
**Oracle:** Confirmed — **Q-03** matches the fixed defect exactly.
**Defect class:** F-18 subtle value fault (stale `backoffFor`) — ODC trigger: step-1 extraction + adversarial traces (P-02a, T-05)

## Oracle comparison (written after the freeze, by the grader — the
## analysis agents never saw the fix, the PR, or the issues)

Part A, frozen before any fix was consulted, recorded as Q-03: the
sleep duration `backoffFor` is computed once per `resetTransport`
iteration (clientconn.go:975) and consumed at the TransientFailure
sleep (clientconn.go:1129). After a connection is established and
later dies, the loop resumes with the **stale** accumulated value — up
to MaxDelay (120s) of dead air before the first reconnect attempt,
although `backoffIdx` was reset at success-at-death
(clientconn.go:1084, 1112). PR #2669's one-line core is `backoffFor =
0` after a connection is established — precisely the missing half.

That also answers the design question this benchmark was chosen for —
whether "Ready + BackoffReset" is one atomic transition obligation or
two independent effects. In v1.18.0 it was two half-effects: the
cross-connection memory (`backoffIdx`) reset on success, the
loop-local sleep value (`backoffFor`) did not. The blind pass (Part B)
derived the atomic obligation independently from the backoff doc's
"reset ⇒ behave like a fresh connection" and flagged the same cells
(P-02a fold, E09 fold into Q-03) — convergent-hole.

ODC note: F-18 (subtle value fault) is one of the two SHARD-derived
fault classes added to the catalogue in pack v1.35/02-v1.14. The
class *classified* the oracle finding; the *detector* was step-1
extraction plus the interaction-pair traces (the category checklist
independently probed the same seam via P-02a).

## Scope and freeze discipline

Strict symbol scope: `addrConn` + its methods in clientconn.go;
balancer/resolver/transport as callee contracts. Requirements: the two
upstream gRPC contract documents (connectivity semantics, connection
backoff). Part A ran with no web access, no issues/PRs, no git
history beyond the shallow v1.18.0 checkout; Part B ran with zero
tool use on the catalogue + requirements only. Findings Q-01..Q-16
describe the frozen tree; apart from Q-03 (fixed by #2669) they are
**unverified against current grpc-go** and may have been fixed since.

## Result counts

7 states × 26 events (17 base + 9 undesired variants) = 182 cells;
7 interaction pairs (14 orderings, all traced); 12 guard groups
(9 proven, 1 z3 violation = G-05 terminal-guard gap backing Q-01,
2 not-formalizable); 20 doctrine lines, all mapped; 16 findings, all
carried as OPEN questions with ODC fields. Part B: 40/40 rows —
26 convergent, 11 convergent-hole, 2 divergences (folded into Q-11,
Q-03), 3 catalogue artefact repairs, 1 pass-B blind spot (E05).

Harness yield: this pilot exposed two pack defects, fixed same day —
check_matrix accepted only `.py:` citations (language neutrality
silently broken), and part_b_pack --check misread finer-grained blind
tables as duplicates.
