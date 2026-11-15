# Bounded pair: blocked on incomplete blind-run accounting

The reference set was frozen before either arm, reviewed by a separate AI
session, and executed against golang-lru commit
`2bb29091a6c341aba625d23fea354c4fbaef5d6f`. The four behavioral test groups
passed three times under the race detector. Three separate runs of the fifth
probe reported a concurrent `Cap`/`Resize` data race. The two domain questions
in `reference/cases.json` remain open; no human review or domain decision took
place. This is one public component and the reference is not an exhaustive
oracle.

The direct pilot started, created an event catalogue, then attempted the required
fresh blind Part B. Its child CLI was the older `codex` on PATH, instead of the
application runtime CLI. The model request was rejected with HTTP 400
`model_not_found` (see `attempt/direct/blind-output/046.jsonl`). There is no
completed usage record for that request. As required by the protocol, the
controller was stopped and the routed arm was not started. The direct catalogue
fields check passed, while the remaining gates failed on incomplete artifacts;
this is not a completed pilot and does not support a quality or cost comparison.
The reserve component was not inspected.

Reference review and model smoke have estimated costs of $0.087924 and
$0.0727692 respectively. The stopped direct arm reported a partial estimated
$0.2786296. Their known subtotal is $0.4393228, excluding any unreported
in-flight or failed-request cost and the supervising session. It is a
rate-based estimate, not a billing statement. Unknown usage is not zero.

After the stop, the runner was fixed to pass `CODEX_APP_RUNTIME_CLI_PATH` to
both tool servers, and to stop upon a terminal blind failure with unknown usage.
`recovery-red.txt` and `recovery-green.txt` preserve the before/after tests;
`all-tests.txt` records the combined tests. The isolated no-model-call preflight
passed again. No paid rerun was made while the original attempt's total remained
unknown. The original runner hash is preserved in `attempt/experiment.json`;
the runner in this change includes the recovery fix.
