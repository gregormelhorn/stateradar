# Predeclared bounded comparison

Recorded before new model calls on 2026-11-14.

## Scope and fixed settings

Compare `routed` then `matrix` sequentially on sony/gobreaker commit
`27b8e2cfc65aacd09abb3968455e4b01df4a83fa`. Both use the same committed pack
revision (the reconciled mutation/rationale revision recorded in experiment.json),
`gpt-6.1-sol`, medium reasoning, signed-in ChatGPT authentication, selective tool
output, a fresh isolated source checkout and ledger, and 2700 seconds per arm.
The runner ignores user configuration; no Fast mode is requested. Jev is pinned
to `jev-1.14.0`; the existing Flash model and $2 provider ledger limit are
unchanged. No prompt tuning or intervention between arms. No extra Flash
schedule sweep; the matrix renderer is the single treatment difference.

The independent review checks four known controls: stale completion accounting,
duplicate done, abandoned HalfOpen allowance, and OnStateChange reentry. Controls
and prior analyses never enter pilot inputs. Inspect additional findings and
question coverage separately. A probe that demonstrates behavior is not an owner
decision about intended behavior. The existing component is a regression screen,
not a new held-out generalization claim. Semaphore is the deterministic regression
fixture. No fresh Pool attempt is included; its prior service cutoff and missing
controller usage are not repaired or estimated from another run.

## Completion and cost

Run all runner acceptance gates, including strict sidecar generation, reachability,
source anchor audit and catalogue reproduction. The matrix arm additionally must
reproduce its matrix from retained fields. Review behavior probes and findings,
not only green structural gates. Every tool error and repair inside the controller
session counts, including failed routing calls. No unmetered manual artifact repair
will turn an incomplete arm into a success. A stopped or red arm remains incomplete;
any future continuation must have separately captured usage and be added to cost.

Read `cost-estimate.json`, `usage-checkpoint.json`, routing ledger status and tool
logs. Missing controller usage or unsettled reservations make total cost unknown.
Report Codex credits and the combined rate-based USD equivalent including all
Flash/Jev calls. Official Standard rates checked on 2026-11-14 at
https://learn.chatgpt.com/docs/pricing are 50 / 2.5 / 250 credits per million
uncached input / cached input / output for Sol. The runner's conversion of
$0.04 per credit is an explicit assumption, not an invoice or marginal subscription
charge. Effective billed dollars require the user's actual plan or agreement.
No separate cache-write cost is added; cached input is already part of input.

Common implementation work, the supervising chat and human review are outside
per-arm metering and must be reported as excluded, not silently called free.
Within-arm retries and corrections are included. Report tool rereads, failed
commands, elapsed time, four control outcomes and all gates alongside cost. With
one run per arm and fixed order, cache/order and stochastic effects remain; this
can reject a bad candidate but cannot establish a reliable universal winner.
Keep the routed default unless checked quality and complete costs support change.
