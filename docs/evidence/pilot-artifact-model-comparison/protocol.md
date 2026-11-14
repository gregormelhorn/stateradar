# Catalogue workflow and controller comparison

Frozen before live pilot execution, 2026-11-14.

Compare GPT-6.1 Sol and GPT-6.1 Terra on Pool and gobreaker, using the same
committed pack, prompt v1.29, routed workflow, selective output, medium
effort, ChatGPT login, Jev 1.14.0, no companion claims, $2 provider ledger
and 2700-second wall limit per pilot. Pool order: Sol then Terra;
gobreaker order: Terra then Sol. Components may run concurrently; two Pool
pilots may not (the upstream tests use port 7777).

Source SHAs: Pool `6084537e520652192f41aebfd88d822c00b9447a`, gobreaker
`27b8e2cfc65aacd09abb3968455e4b01df4a83fa`. No findings or external control
tests enter the pilot inputs. Keep all failed calls and artifacts. Never
repair a blind response or retry a service safety refusal to evade it.

Acceptance: complete pilot, exact catalogue regeneration, matrix, guards,
sidecar, reachability, blind coverage; inspect findings against the
established behavior controls, including the historical Pool P-04a
interleaving (IDs may differ), Release/Close waiters, repeated Get,
abandonment, retention and callback boundaries; gobreaker stale completion,
duplicate done, abandoned half-open allowance and callback reentry.
Count extra reads, failed commands, blind dispatches and artifact repairs.
A low-cost incomplete or materially incomplete analysis is not a winner.

Cost: complete controller usage including its own repair turns, plus all
settled Flash/Jev calls (failures included). Codex standard credit rates per
million input/cached input/output: Sol 50/2.5/250, Terra 25/1.25/125,
verified at https://learn.chatgpt.com/docs/pricing on 2026-11-14.
Input usage includes cached input: subtract it before pricing uncached
input; reasoning is already included in output. Convert credits at an
explicit assumed $0.04/credit for a comparable dollar equivalent, not an
observed account debit. Report credits and provider ledger separately.
Provider ledger amounts are price estimates, not invoices; Flash cache
and off-peak adjustments may reduce actual debit. Supervising implementation
and external audit costs are not metered by this runner and are excluded.
Model availability smoke is separate from pilot totals. No missing
controller usage is replaced by zero.

The earlier three-way runs used a different pack and are historical
context, not matched evidence for the model change or artifact savings.
One run per model/component is a screening experiment, not a reliability
rate estimate.


## Execution correction

The first Terra/gobreaker pilot stopped after eight successful commands:
the controller's read-only sandbox declaration contradicted the requested
artifact writes. It explicitly declined to write analysis. This is a
configuration failure, not evidence of missing analysis capability.
Retain the initial `8b8e854` runs as diagnostic work, including their costs.
The matched comparison restarts on a single corrected pack using Codex
`workspace-write` inside each disposable checkout. The command server's
macOS sandbox and credential restrictions remain in force. Existing
processes finish so their completed usage can be retained; no partial
usage is silently treated as free. No safety refusal is being bypassed.
