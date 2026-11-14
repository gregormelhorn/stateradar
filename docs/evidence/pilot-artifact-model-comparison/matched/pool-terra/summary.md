# Channel pool analysis — incomplete

model routing: on (unevaluated, cascade plan stage 3)

This is an unfinished pilot, not a validated complete model. Four draft-verify calls succeeded for README.md, channel.go, pool.go and channel_rpc_test.go; 69 claims had citation checks pass, with 66 supported and 3 unclear Jev judgments. Drafts are retained and are not independently accepted. Their questions still require individual disposition. No seam-contract or Step-8 Jev batches, full matrix, guard proof, sidecar, reachability evidence, or blind pass have been completed. No Part B output was authored by the source-reading agent. Reviewer cross-check was not run.

The full existing Go suite failed by timeout (8 seconds): TestPool_Get blocked in channel.go:137 while channel_rpc_test.go:94 expects ErrMaxActiveConnReached. Selected existing tests passed: `go test -timeout 15s -run TestNew|TestPool_Get_Impl|TestPool_Put|TestPool_UsedCapacity|TestPool_Close|TestPoolWriteRead .` (arguments passed without a shell). The DSC and reachability gates were executed and failed because analysis.json has not been generated. These are incomplete-artifact failures, not evidence of valid analysis. Other mandatory gates and probes remain unrun.

Preliminary questions are in open-questions.md. In particular, release and close do not notify the waiter list in the cited implementation; checked-out resources returned after release encounter a cleared close callback; and the waiter path does not perform the idle path's ping. Their intended outcomes remain human decisions. Claims about races or operational impact still need targeted probes and Step-8 verification.

Counts: states / events / interaction pairs / matrix cells / holes / guard outcomes / findings: not yet established. Open questions: 7 preliminary, not exhaustive.

Ledger: routing.sqlite. Ledger status is recorded separately in ledger-status.json. Failed or skipped calls: no draft-verify failures; all other model calls above were skipped because their prerequisite artifacts are incomplete.

## Ledger status output

```json
{
  "committed_or_reserved_microdollars": 8628,
  "limit_microdollars": 2000000,
  "calls": [
    {
      "id": 1,
      "provider": "deepseek-flash",
      "amount_microdollars": 1452,
      "status": "settled"
    },
    {
      "id": 2,
      "provider": "jev",
      "amount_microdollars": 128,
      "status": "settled"
    },
    {
      "id": 3,
      "provider": "deepseek-flash",
      "amount_microdollars": 3193,
      "status": "settled"
    },
    {
      "id": 4,
      "provider": "jev",
      "amount_microdollars": 332,
      "status": "settled"
    },
    {
      "id": 5,
      "provider": "deepseek-flash",
      "amount_microdollars": 771,
      "status": "settled"
    },
    {
      "id": 6,
      "provider": "jev",
      "amount_microdollars": 59,
      "status": "settled"
    },
    {
      "id": 7,
      "provider": "deepseek-flash",
      "amount_microdollars": 2448,
      "status": "settled"
    },
    {
      "id": 8,
      "provider": "jev",
      "amount_microdollars": 245,
      "status": "settled"
    }
  ]
}
```
