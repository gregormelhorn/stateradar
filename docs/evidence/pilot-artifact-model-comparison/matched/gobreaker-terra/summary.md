# Pilot status — incomplete

model routing: on (unevaluated, cascade plan stage 3)
Scope: one CircuitBreaker instance and TwoStep wrapper. The existing Go suite passed with a 60-second timeout. Four preliminary open questions are recorded; they do not represent a completed inventory.

The three draft-verify calls succeeded; their internal Jev version was jev-1.14.0. One code and one test citation failed automatic fragment checking, and their source locations are corrected in extraction.md. One explicit four-claim Jev batch returned supported for all four; its results require human review and do not settle intent.

Not completed: exhaustive extraction and draft-question disposition; doctrine and seam sweeps; catalogue, full matrix, guard proofs, sidecar and reachability; complete adversarial traces and test replay; all finding verification; blind Part B and classification. No claim of a passing pilot is made. No source, existing test or configuration was changed.

Executed: `go test -timeout 60s ./...` passed (log 011). An exploratory `dsc_check.py --help` failed because that script interpreted --help as an analysis directory (log 024); this was not a pilot gate. Gate results are recorded separately when run. Skipped: blind pass and all remaining model checks because their validated input artifacts were not completed.

Executed incomplete-artifact gates: strict sidecar generation skipped because no matrix exists (log 030); dsc_check failed for missing analysis.json (log 029); reachability failed for missing analysis.json (log 028). Matrix and guard checks could not run because their inputs and scripts were not created. The blind package was not sent. Git status reported only domain-analysis as untracked; git also reported two xcrun cache permission errors (log 032).

Ledger: routing.sqlite
Status output (log 031):
```json
{
  "committed_or_reserved_microdollars": 15423,
  "limit_microdollars": 2000000,
  "calls": [
    {"id": 1, "provider": "deepseek-flash", "amount_microdollars": 2383, "status": "settled"},
    {"id": 2, "provider": "jev", "amount_microdollars": 225, "status": "settled"},
    {"id": 3, "provider": "deepseek-flash", "amount_microdollars": 5966, "status": "settled"},
    {"id": 4, "provider": "jev", "amount_microdollars": 511, "status": "settled"},
    {"id": 5, "provider": "deepseek-flash", "amount_microdollars": 5670, "status": "settled"},
    {"id": 6, "provider": "jev", "amount_microdollars": 513, "status": "settled"},
    {"id": 7, "provider": "jev", "amount_microdollars": 155, "status": "settled"}
  ]
}
```
Failed model calls: none. Skipped model calls: remaining seam, ordering, finding batches and blind pass; their inputs were not completed.
