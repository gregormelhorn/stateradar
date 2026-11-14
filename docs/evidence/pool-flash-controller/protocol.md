# Flash as the Pool pilot controller

Use Pool 6084537, selective command output, the unchanged v1.25 prompt
from ba14ef0 for the first controller run, then a revised English prompt
in a clean checkout. Flash steers the whole Part A with Jev as a narrow
verifier. A separate, fresh Codex medium session handles Part B from
the inspected blind package. The existing Codex reference uses Flash
for Part B, so the controller and blind provider both change against
that reference. Keep the blind provider identical across the Flash
before/after pair.

Score the findings by semantics, and differentiate explicit trace,
open decision and executed behavior. Inspect the five independent
runner gates and report upstream test failures separately. Compare at
least Release and waiting acquisition, the narrow Get/Put scheduling
window, second Get pending and held, abandonment and handoff, retained
queue storage, Close and capacity, callback teardown, Ping/Release race,
idle expiry, and wrong receiver/payload. Verify the blind package and
track coverage, divergences and any corrections.

Report actual provider usage counters and published DeepSeek rates
by request timestamp. The controller billing estimate uses real cache
hits, misses and output, including reported reasoning. The provider's
account invoice and Codex's plan marginal price are unavailable.
Report local Flash/Jev ledger estimates and blind Codex tokens separately.
Retain failures and provider reservations. Compare end-to-end time and
read-log calls, noting model-specific tokenization and single-run scope.
