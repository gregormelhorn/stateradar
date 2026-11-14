# Incremental controller accounting

The previous exec runner lost all controller usage when no `turn.completed`
arrived and skipped its final artifact checks after failure. The observed red
probes in `red.txt` demonstrate missing checkpoints during execution, service
failure and timeout, and the absence of an abort-audit orchestration seam.
`green.txt` records the repaired behavioral probes plus cumulative-counter and
cost-completeness checks. The tests use an actual child process and an isolated
fake session store, with no paid calls.

Implementation: keep the fresh CLI session, tail only its exact rollout ID,
atomically persist cumulative usage, never sum cumulative snapshots, and run
artifact checks from the failure finalizer. Final counters and partial counters
have separate files and explicit completeness. Source format is local and
version dependent; unknown usage is not zero cost.

The initial live format probe used Codex 0.167.0-alpha.4.1 through the existing
ChatGPT login. It returned `OK`; its final CLI usage matched its persisted
`token_count`: input 19153, cached input 10240, output 5. This is a transport
probe, not a pilot or quality result. At the documented rates and $0.04/credit
assumption it represents $0.018900, outside the subsequent pilot's own ledger.

Protocol reference: https://learn.chatgpt.com/docs/app-server documents
`thread/tokenUsage/updated`; that alternative transport is not introduced here.
Pricing reference: https://learn.chatgpt.com/docs/pricing#token-rates, captured
2026-11-14. Complete pilot costs remain estimates rather than billing receipts.

A second observed red probe (`child-red.txt`) found that killing the controller
process group alone leaves a command running in its own group. The finalizer
now stops the controller's live descendant tree before artifact audits; the
behavioral test checks the detached child is no longer running. This prevents
a timed-out command from continuing to mutate evidence during verification.
