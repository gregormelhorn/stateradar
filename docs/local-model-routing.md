# Local model routing

This optional workflow sends supplied text to DeepSeek and TypeSafe. Set
`DEEPSEEK_API_KEY` and `TYPESAFE_API_KEY` in the environment. Each pilot
uses a separate SQLite ledger stored outside the repository. The default
ledger limit is $2, expressed as 2,000,000 microdollars.

```bash
mkdir -p "$HOME/.local/state/stateradar"
ledger="$HOME/.local/state/stateradar/example-pilot.sqlite"
python3 tools/local_models.py --ledger "$ledger" status
python3 tools/local_models.py --ledger "$ledger" flash /path/to/task-and-source.txt
python3 tools/local_models.py --ledger "$ledger" jev /path/to/source.txt \
  'Does the source explicitly describe the specified event ordering?'
```

The Flash input must include the task and the source excerpts needed to do
it. Each invocation is a fresh text-only call. Flash cannot browse the repo
or execute tools through this interface. A calling agent prepares inputs,
checks citations and results, runs the deterministic checkers, and carries
forward every uncertainty and question. Jev returns a probability; it does
not establish a domain decision.

For Part B, put requirements and normative event contract text in separate
files. Select their contents before running the command. The catalogue lives
in the analysis directory. The call receives only the assembled package and
no tools or conversation history. The command checks the returned table with
the existing Part-B coverage checker and returns a failure for missing rows,
missing checklist ticks, or truncated output.

```bash
python3 tools/local_models.py --ledger "$ledger" blind domain-analysis/component \
  --repo /path/to/repo --requirements docs/requirements.md \
  --contracts docs/event-contracts.md --output /path/to/blind-output.md
```

The calling agent must review the catalogue and supplied files for suitable
blind inputs and follow `prompts/02-pilot.md` for the diff, divergence
classification, and questions. The coverage checker checks row presence,
not whether the predictions are correct.

## Accounting and recovery

The tool reserves an estimated maximum before each request using byte length,
the requested output limit, and peak published prices. It records usage after
a response. Flash input is charged at the peak cache-miss rate in this
estimate even when the provider reports a cache hit. Jev output is free at
the current listed price. Rates are $0.30 per million Flash input tokens,
$1.20 per million Flash output tokens, and $0.042 per million Jev input
tokens. Update the implementation when provider prices change.

The reservation is an estimate, not a provider-enforced spending cap. If
actual usage exceeds it, the ledger records the actual amount and blocks
future calls when the limit is exceeded. Timeouts, invalid usage responses,
and interrupted calls retain their reservations, since their actual costs
are unknown. Concurrent calls to one ledger reserve using SQLite transactions.
The ledger covers only calls through these tools. The main agent or any
other provider has separate billing, so the proposed $3 for strong-model
review is a planning allowance and is not enforced here. Failed requests
and provider billing changes may also make the ledger differ from an invoice.

Inspect reservations with `status`. After checking the provider's usage,
reconcile an uncertain call with `settle CALL_ID ACTUAL_MICRODOLLARS`.
Change the limit deliberately with `set-limit MICRODOLLARS`.

```bash
python3 tools/local_models.py --ledger "$ledger" status
python3 tools/local_models.py --ledger "$ledger" settle 1 1200
python3 tools/local_models.py --ledger "$ledger" set-limit 3000000
```

The ledger includes no prompt text, but its database is local task data.
Prices and usage figures are estimates in US dollars. An output ending for
any reason other than `stop` may be incomplete and must be reviewed.
