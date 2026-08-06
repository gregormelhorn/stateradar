# Examples

Reference runs of the pack — what a complete StateRadar analysis
looks like (statechart, disposition matrix, open questions).

## Device Connection (synthetic)

`device-connection/` — a 130 LOC Python component built for this
purpose. It manages the lifecycle of a single device (connect,
disconnect, retry with backoff, timeout, terminal failure). The
analysis finds a lifecycle disagreement: `disconnect()` exits the
FAILED state (contradicting the requirement that FAILED is terminal),
and reconnection from ex-FAILED state hangs because `retry_count`
is not reset.

This example demonstrates the full Part A + Part B workflow on a
component small enough to read in two minutes. It also serves as
a CONVERGENCE.md calibration candidate — run the pilot twice in
independent sessions to measure cross-run divergence.

## Real components

Before publishing any real run here: analysis artifacts describe the
internals of the analyzed system in detail (architecture, event flows,
failure behaviour). Review disclosure implications — IP, security,
confidentiality — before committing a real component's analysis.
The synthetic device-connection example is the safe default for
public demonstrations.
