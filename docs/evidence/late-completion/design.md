# Late completion feature: executable scenario contract

Scope: a reusable language-neutral oracle for one operation already started,
a terminal boundary action, and completion delivered in either ordering. The
component adapter emits observations; it never chooses the behavioral verdict.
A profile declares terminal/accepted states, the emitted acceptance effect,
scenario IDs, matrix-cell references and the ordering. An adapter must verify
actual test discovery and complete trace collection before invoking the oracle.

The observation contract contains actual projected state, transport publication,
logical resource close count, cumulative emitted effects, resource identity,
and independent parent lifetime. Four coordinates must be observed separately:
terminality, publication, absence of new acceptance effects, and resource release.
The positive control completes before termination: accepted state, publication,
acceptance effect and live resource must all be seen before cleanup. This rules
out an always-terminal/always-closed observer. Exact order, stable identity,
monotonic effects/releases and cardinality are structural requirements; malformed
or incomplete evidence is BLOCKED, never a behavioral kill. The weak oracle
checks only the immediate post-termination state, with the same executed traces.

Reference: grpc-go v1.18.0, a02b0774206b209466313a0b525d2c738fe407eb.
Accepted DR-001 already requires an under-lock publication guard and a terminal
connectivity guard; late transport Close must occur outside ac.mu. The scoped
model is a trace contract, not a new total addrConn matrix or full Part A/B pilot:
- publication: Connecting/unpublished -> Shutdown -> completion stays Shutdown,
  no publication/Ready; returned transport closed exactly once;
- notification: Connecting/published -> Shutdown (drain closes idle transport)
  -> delayed notification stays Shutdown, no new Ready, no repeated close;
- positive: Connecting/unpublished -> Ready/published/live -> Shutdown/closed.
The adapter uses an idle fake transport (no streams), real addrConn methods and
real ClientConn lifetime. It substitutes the transport factory, holds checkpoints
AFTER the actual createTransport checks and before Ready, and observes the actual
ClientConn notification seam. Close reenters getState to detect closing under the
lock. Parent cancellation and emergency cleanup happen only after observations.
This proves the caller's lifecycle obligations, not the transport implementation.

Build sequence: observed red oracle selftests; historical failing traces before
DR-001 patch; patched green control; independently corrupt state/effect/release
via four canaries; remove publication and terminal guards via two F-04 mutants.
The general mutant runner gates mutants transitively on all four canaries.
A whole-process timeout remains BLOCKED. No domain latency bound is inferred.
All historical analyses remain unchanged. Other DRs are outside this increment.
