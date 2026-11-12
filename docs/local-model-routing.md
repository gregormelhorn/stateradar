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

### Batch semantic checks

Use `jev-batch` to evaluate independent claims and event orderings against
the same source file in one request. Supply a JSON array such as:

```json
[
  {"id": "C1", "kind": "claim", "statement": "The component stays failed.", "line": 12, "fragment": "remains in FAILED"},
  {"id": "O1", "kind": "ordering", "statement": "A disconnect occurs after failure.", "line": 12, "fragment": "remains in FAILED"}
]
```

```bash
python3 tools/local_models.py --ledger "$ledger" jev-batch \
  /path/to/source.md /path/to/checks.json --model jev-1.14.0 > /path/to/review.json
```

Each `line` is a one-based line in the source file and each `fragment` must
occur within three lines of it. Missing fragments, invalid lines, duplicate
IDs and incomplete responses fail. All questions see the same source and
are evaluated independently. Prepare a separate batch for another source.
The response includes the source path and content hash, citation, statement,
model version, choice probabilities, token usage, and cost. Every result
is marked for review. Ordering checks also receive an independently evaluated
`ordering_scope_probability` for whether the fragment contemplates the exact
sequence. The Choice and Noul answers may disagree; preserve both and examine
the source. Confidence and repeatability do not establish correctness. Follow
the requirement-scope rule and raise a question when its conditions require
one. An API error after reservation keeps the reservation until reconciled.
Omit `--model` to use `jev-latest`; pin a specific available version for
comparable measurements.

When comparing prompts, use held-out, independently labelled examples and
repeat both batched and individual calls with the same source and questions.
Measure per-option probabilities and Noul probabilities, elapsed time, and
input tokens. Repeated evaluations can include a changing, irrelevant nonce
in the state to avoid replaying cached responses. The TypeSafe cookbooks on
[parallel questions](https://docs.typesafe.ai/cookbooks/parallel_questions),
[Choice consistency](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook),
[Noul consistency](https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook),
and [feature discovery](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery)
describe these techniques. Feature discovery needs a labelled dataset and a
held-out evaluation; it is not part of the batch command.

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
