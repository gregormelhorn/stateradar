# Local model routing

The implemented commands support bounded drafting, a draft-and-verify chain,
batched semantic checks and offline evaluation. They do not automatically
accept a draft or route difficult cases to a stronger model. The next pilot
and its evaluation criteria are in the [model cascade
plan](plan-model-cascade.md); broader project work is in the
[roadmap](roadmap.md).

This optional workflow sends supplied text to DeepSeek and TypeSafe. Set
`DEEPSEEK_API_KEY` and `TYPESAFE_API_KEY` in the environment. Each pilot uses
a separate SQLite ledger stored outside the repository. The default ledger
limit is $2, expressed as 2,000,000 microdollars.

```bash
mkdir -p "$HOME/.local/state/stateradar"
ledger="$HOME/.local/state/stateradar/example-pilot.sqlite"
python3 tools/local_models.py --ledger "$ledger" status
python3 tools/local_models.py --ledger "$ledger" flash /path/to/task-and-source.txt
python3 tools/local_models.py --ledger "$ledger" jev /path/to/source.txt \
  'Does the source explicitly describe the specified event ordering?' --model jev-1.14.0
```

A new ledger takes its limit from `--limit-microdollars` on the first call
(default 2,000,000). The flag only sets the initial limit: passing a different
value to an existing ledger fails, so change it with `set-limit`.

The Flash input must include the task and the source excerpts needed to do it.
Each invocation is a fresh text-only call. Flash cannot browse the repo or
execute tools through this interface. A calling agent prepares inputs, checks
citations and results, runs the deterministic checkers, and carries forward
every uncertainty and question. Jev returns a probability; it does not
establish a domain decision.

### Batch semantic checks

Use `jev-batch` to evaluate independent claims and event orderings against the
same source file in one request. Supply a JSON array such as:

```json
[
  {"id": "C1", "kind": "claim", "statement": "The component stays failed.", "line": 12, "fragment": "remains in FAILED"},
  {"id": "O1", "kind": "ordering", "statement": "A disconnect occurs after failure.", "line": 12, "fragment": "remains in FAILED"}
]
```

```bash
python3 tools/local_models.py --ledger "$ledger" jev-batch \
  /path/to/source.md /path/to/checks.json --model jev-1.14.0 --output /path/to/batch.json
```

For shorter tool results, add `--summary` with `--output`. Stdout carries
the artifact path, usage, and counts by choice. The output file keeps every
judgment and its citation. For `flash`, use `--output draft.json` to save
the draft and print usage. If Flash truncates the draft, the command exits
with an error and keeps it at `draft.json.partial.json`.

Each `line` is a one-based integer line in the source file. Each `fragment` is
a single line of at least four non-space characters that occurs on a line
within three lines of it, the pack-wide citation window. The `draft-verify`
prompt asks Flash for the cited line itself; the check accepts the window.
Missing fragments, invalid lines, duplicate IDs and incomplete responses fail.
All questions see the same source and are evaluated independently. Prepare a
separate batch for another source. The response includes the source path and
content hash, citation, statement, model version, choice probabilities, token
usage, and cost. Every result is marked for review. Ordering checks also
receive an independently evaluated `ordering_scope_probability` for whether
the fragment establishes every material condition, actor, event, order and
outcome in the asserted sequence. Paraphrases count when they preserve the
meaning. Surrounding text cannot supply missing evidence. The Choice and
Noul answers may disagree; preserve both and examine the source. Confidence
and repeatability do not establish correctness. Follow the requirement-scope rule and raise a
question when its conditions require one. An API error after reservation keeps
the reservation until reconciled. Omit `--model` to use `jev-latest`; pin a
specific available version for comparable measurements.

### Draft and verify

`draft-verify` chains the two models for one source file. Flash receives the
task and the numbered source and must answer with JSON: a `claims` list (`id`,
`kind` = `claim` or `ordering`, `statement`, `line`, `fragment`) and a
`questions` list. Code rejects a draft that is not this structure, and a draft
cut off at the output budget (`finish_reason=length`); either way the raw text
is saved next to the output with the extension replaced (`--output
review.json` gives `review.draft.txt`) and is not printed. The default output
budget is 12000 tokens: 4096 truncated a 248-line source, whose complete draft
then took about 5,200, so 12000 leaves headroom (the ledger reserves 1.2 times
the budget for output). Each claim's citation is then checked against the
source with the same rule as `jev-batch`. Claims that fail keep their reason
in `citation_check` and are never sent to Jev. The citable claims go to Jev in
one batch.

```bash
python3 tools/local_models.py --ledger "$ledger" draft-verify \
  docs/requirements.md /path/to/task.md --output /path/to/draft-review.json \
  --model jev-1.14.0
```

The result records the source path and hash, the Flash and Jev usage, every
claim with its citation check and Jev judgment, and every draft question. The
command prints a summary (counts, citation failures, Jev choices, usage); the
full result is only in the output file. If Jev fails after the draft was paid
for, the result is still written, with the error in `verification.error` and
no Jev judgments, and the command exits 1. Everything is marked for review;
nothing is accepted. `prompts/02-pilot.md` ("Model routing") says which pilot
steps use this command and how the calling agent consolidates the result,
including the rule that an ordering counts as source-backed only when Jev's
choice is `supported` and its scope probability is at least 0.5. That cut-off
is provisional and uncalibrated: it can only turn an ordering into a question
and never accepts one. The command needs both API keys. Every command that
takes `--output` checks before any request that the output is not a directory
and its directory is writable.

### Draft matrix cells

`draft-cells` drafts disposition-matrix cells (the 02-pilot routing variant
`flash-writes`, roadmap entry 11 item 2). The task file is JSON written by the
steering agent: `states` (each a `name` and the `condition` that defines it),
`events` (each an `id` and a `gist`) and optional `notes`; names and ids are
one word, and rule 10 of the routing section (finding-neutral tasks) applies
to all of it. Flash must answer with one cell per state and event (`state`,
`event`, `disposition`, `target` for a transition, `line`, `fragment`, `note`)
plus `questions`. Code checks each cell: known state and event, the closed
disposition vocabulary of `formats/rules.toml`, a transition target among the
states, no target on other dispositions, the citation rule of `jev-batch`, and
one cell per pair; it lists the pairs without a cell. Every matrix tool splits
table rows on `|`, so a fragment with a `|` is cut to its longest verbatim
piece without one (refused if that piece is too short) and a note's `|`
becomes `/`. Every clean cell goes to one Jev batch as a claim that names the
state with its condition, the event with its gist and the drafted outcome. The
default output budget is 16384 tokens, the Flash maximum; split the events
across task files when a draft is cut off.

The result JSON holds every cell with its problems and Jev judgment, the
missing pairs, the draft questions and the usage. The command also writes a
matrix block next to the JSON (`cells.json` gives `cells.md`): the 02-pilot
cell form in sub-tables of eight events, then a review list (cells with
problems, cells Jev did not judge `supported`, missing pairs) and the draft
questions. A hole or a cell with a problem carries `→ Q-?` (a cell with a
problem also loses its citation), and a missing cell reads `MISSING`, so
`dsc_check.py` fails until the agent has decided each. Nothing is accepted:
the agent checks every cell against the source. A draft that is not the
required JSON, or is cut off, is kept as `cells.draft.txt`. The command needs
both API keys.

`python3 tools/draft_cells.py compare cells.json … --sidecar analysis.json`
needs no key: it compares the drafts with the run's final sidecar and counts
each drafted cell as unchanged, changed (disposition, target or citation) or
dropped, split by Jev's choice, and lists the final cells no draft held.
Add `--output compare.json` to keep all rows in the report file and print
aggregate counts.

```bash
python3 tools/local_models.py --ledger "$ledger" draft-cells \
  pool/channel.go /path/to/cells-task.json --output /path/to/cells.json \
  --model jev-1.14.0
```

### Evaluate a batch against reviewed examples

`tools/jev_eval.py` compares one saved `jev-batch` result (its `--output` file
or redirected stdout) with independently reviewed labels. It does not read
`draft-verify` output, which nests the judgments under `claims`. It runs
locally and makes no provider calls. The labels use the same source hash and
check identity as the batch, plus an attributed reviewer and the expected
verdict. For example, if the saved batch was produced from the exact source
and check shown below, a label file has this shape (replace the example hash
with the batch's actual `source_sha256`):

```json
{
  "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "checks": {
    "C1": {
      "kind": "claim", "statement": "The component stays failed.",
      "source": "/path/to/source.md", "line": 12,
      "fragment": "remains in FAILED", "expected": "supported",
      "reviewer": "attributed independent reviewer"
    }
  }
}
```

```bash
python3 tools/jev_eval.py /path/to/labels.json /path/to/batch.json
```

The reviewer must decide labels independently of the model result. The tool
checks attribution is present, but cannot establish reviewer independence or
whether a label is correct. It requires identical case IDs, source hashes and
check identities and refuses empty or mismatched datasets. It reports the
confusion matrix, exact matches, IDs judged supported against a non-supported
label, unclear IDs, and the batch's reported input tokens and estimated cost.
It does not evaluate the separate ordering-scope probability, choose a
threshold, or include the costs of any other calls. Review all judgments and
keep any unresolved domain question open. See [the cascade
plan](plan-model-cascade.md) for dataset and end-to-end evaluation
requirements.

When comparing prompts, use held-out, independently labelled examples and
repeat both batched and individual calls with the same source and questions.
Measure per-option probabilities and Noul probabilities, elapsed time, and
input tokens. Repeated evaluations can include a changing, irrelevant nonce in
the state to avoid replaying cached responses. The TypeSafe cookbooks on
[parallel questions](https://docs.typesafe.ai/cookbooks/parallel_questions),
[Choice
consistency](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook),
[Noul
consistency](https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook),
and [feature
discovery](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery)
describe these techniques. Feature discovery needs a labelled dataset and a
held-out evaluation; it is not part of the batch command.

For Part B, put requirements and normative event contract text in separate
files. Select their contents before running the command. `blind` takes only
prepared `.md`, `.txt` or `.rst` files: requirements may select one section
with `FILE.md:PATTERN`, contracts are whole files of verbatim docstrings or
schema descriptions. It refuses source files and `FILE:Class` specs, so the
blind pass never receives implementation code. Run it once with
`--package-only` to write `<output stem>.package.md` without any call, read
the package, then run it without the flag. The real run requires that package,
sends exactly it, and refuses if the inputs have changed since. The analysis
directory, `--requirements` and `--contracts` resolve against `--repo` unless
absolute. The catalogue lives in the analysis directory; the package carries
it with code fragments, line numbers and analysis ids removed, because pilot
rule 3 puts code into those fragments; file names stay, and so does a quote
cited from a Part B source: the `--requirements` and `--contracts` files, or a
prose file (`.md`, `.txt`, `.rst`, `.adoc`) that a doctrine line cites,
matched by exact path relative to `--repo`. A quote from a file of the
analysis directory is removed. A code fragment never crosses a table cell (a
table row starts with a single `|`, so catalogue tables need leading bars; on
it a lone unescaped `|` is a cell bar, while `\|` and `||` are code, and
elsewhere every `|` is code such as `a || b`): it ends where its quotes
balance before a boundary, otherwise at the last quote-paren before the next
citation (a file the catalogue cites with a fragment, or one under `--repo` by
path or base name), a cell bar or the end of the line. Two backstops refuse
the package, so nothing is sent: a cited file name followed, within 80
characters of the same clause (spellings such as `line 7`, `(line 7)` or
`#L7`; never past a cell bar, a `;` or a `)` that closes an earlier
parenthesis, so a quote after the citation's own `;` or `)` is a known gap
that the agent's own reading covers), by a quote-paren with straight, single
or typographic quotes after stripping (put each fragment on one line after
`file:N` or `file:N-M`, where an en- or em-dash range in a citation counts as
`-`, escape each `|` of a fragment in a table cell as `\|`, rephrase a
parenthesised prose quote that follows a code file name, and rebuild), and a
table row (catalogue or doctrine) whose number of cell bars or whose line
count changed. Further line numbers of the same file go with a citation: colon
items, ranges and a list ending in `and`/`or` (`channel.go:136, 151 or 160`)
are always stripped, a bare run (`channel.go:10, 20`) only where it ends the
clause, so ", 3 callers" stays; a prose count joined by `and`/`or`
(`channel.go:12, 2 and 3 callers`) goes with it, the safe direction, and so
does a count before a parenthesis (`channel.go:12, 5 (five) callers`). Known
leaks: a run that ends in a dash or a slash, and a run whose last number is a
prose count (`channel.go:12, 13, 3 callers` keeps 13). A bare number in prose
("unlock at 136") is not recognised. Q-, PA-, SYS-, NAT- and DR- ids are
always removed. An L-, G-, F- or T- id stays only when the requirements, the
contracts or the quoted text of a doctrine line use it (a doctrine line's
gloss is Part A's and does not count), so a domain term such as `T-1` that the
requirements use survives; every other id of those families is removed,
including a domain term the sources never use. The command names on stderr
each id it kept and each it removed, for the agent to check; a removed domain
term is recorded in `part-b-diff.md` as a known loss, and the inputs are never
edited to restore it. Prose that states an as-is conclusion cannot be removed
mechanically, and the pilot lists it as a known leak. Doctrine lines from
`extraction.md` travel too, stripped the same way: bullets, numbered items or
table rows under a heading that names doctrine. An extraction that names DOC
lines none of which sits under such a heading is refused, and so is a
catalogue whose event ids would not survive the stripping. A truncated blind
output is saved to `<output stem>.partial.md`, never to `--output`, and is not
printed. The call receives only the assembled package and no tools or
conversation history. The command checks the returned table with the existing
Part-B coverage checker, whose report goes to stderr so that stdout stays one
JSON document, and returns a failure for missing rows, missing checklist
ticks, or truncated output. It does not check the disposition vocabulary, and
it only requires pair rows when the catalogue carries `P-` ids.

```bash
blind_args=(blind domain-analysis/component --repo /path/to/repo \
  --requirements docs/requirements.md --contracts docs/event-contracts.md \
  --output /path/to/blind-output.md)
python3 tools/local_models.py --ledger "$ledger" "${blind_args[@]}" --package-only
# read /path/to/blind-output.package.md, then send exactly that package:
python3 tools/local_models.py --ledger "$ledger" "${blind_args[@]}"
```

The exact package sent to Flash is kept next to the output with the extension
replaced (`blind-output.md` gives `blind-output.package.md`), as the record of
what the blind pass saw. If `blind` fails, the Part-A agent never writes the
table itself; it dispatches a fresh blind session. The calling agent must
review the catalogue and supplied files for suitable blind inputs and follow
`prompts/02-pilot.md` for the diff, divergence classification, and questions.
The coverage checker checks row presence, not whether the predictions are
correct.

## Pilot runner output

`tools/run_sol_pilot.py` runs the pilot on macOS through the signed-in Codex
CLI. It requires the two routing provider keys and a local clone of the
pinned Pool or gobreaker source. It defaults to one analysis with selective
output.

```bash
python3 tools/run_sol_pilot.py --component-repo /path/to/pool \
  --output /tmp/stateradar-pool-run
```
Ordinary output up to 12,000 characters per stream is returned in full.
For longer documents, follow the supplied
`read_more.next_stdout` or `read_more.next_stderr` command and then each
returned `next` to read contiguous pages. Long Go test timeout and race
reports show the relevant stacks and their positions in the full log.
Both streams are retained for every command.

For targeted evidence, use the command tool with
`["read-log", "012", "function", "Put"]`,
`["read-log", "012", "rows", "GetAgain"]`,
`["read-log", "012", "lines", "20", "45"]`, or
`["read-log", "012", "find", "generation"]`.
Append `.stderr` to the log ID to select stderr. Every command result carries
`line_counts` for the retained streams. A line range may end beyond EOF and
returns the available lines; its start must exist and its requested width
must not exceed 100 lines. A range starting at line 1 of an empty stream
returns an empty result with `total_lines: 0`. The response includes the actual
total line count. The canonical routing command also accepts `--help` without
making a provider call or creating a ledger.

Use `--output-mode standard` or `--output-mode compact` for one run in
the corresponding comparison format. Use `--output-mode compare` for
the standard/compact pair. `--compact-first` can be used alone as
shorthand for the pair in reverse order.

## Structured matrix and hybrid pilots

Use `--routing-variant routed` for standard routing. The `matrix` variant
keeps that routing and adds the structured matrix workflow and its two
postflight gates. The `hybrid` variant additionally asks Flash for concurrent
schedules. All three use the same selective output by default.

Use `--routing-variant hybrid` with the Codex runner. Flash proposes
bounded concurrent schedules against one implementation file per call.
Every candidate includes cited ordered steps and observable outcomes.
The tool marks fragment or shape problems, and the pilot reviews every
candidate against the source before using it. For example:

```sh
python3 tools/local_models.py --ledger /tmp/pilot.sqlite flash-windows \
  /path/to/component.go --output /tmp/windows.json
```

The full run retains the raw provider answer and the candidate review.
In both `matrix` and `hybrid`, Codex writes the matrix fields and uses `tools/hybrid_pilot.py` to render
them. The renderer checks totality, vocabulary, question IDs, source
fragments and round trips through the sidecar parser. The runner checks
matrix identity and regenerates the sidecar before running the five pack
gates. Jev continues to verify cited claims and requirement scope.

## Provider limits (checked 2026-11-12)

From the TypeSafe and DeepSeek documentation:

* Jev accepts at most 64k tokens per request (source plus all questions) and
  32k per question (source plus one question). A larger request fails with
  HTTP 400 `max_tokens_exceeded`; split the source into excerpts instead of
  enabling the slower long-context mode. English is Jev's primary language;
  checks over other languages are less accurate.
* `jev-latest` and `jev-preview` currently resolve to `jev-1.14.0`. Aliases
  move with releases, so pin the versioned ID for comparable measurements.
  The response's `model` field records the version that answered.
* There is no batch endpoint: `jev-batch` sends all questions for one source
  in one request. TypeSafe's parallel-questions cookbook reports the same
  answers as separate calls at a fraction of the input cost; this is not
  measured for StateRadar.
* `deepseek-flash` is the current Flash model name; DeepSeek serves it as
  DeepSeek-V4.1-Flash-1017. Off-peak rates are half the peak rates used for
  the reservation below.
* Both clients retry HTTP 429, 503 and 529 up to three times, with a
  120-second timeout per attempt. A numeric `Retry-After` is honoured up to
  60 seconds; an absent, non-finite or HTTP-date value falls back to
  exponential backoff (1, 2, 4 s). Other errors fail at once. A retried
  request stays within the same ledger reservation.
* The cookbook thresholds (for example 0.7 in the SDE cascade, 0.8 for
  citation auto-acceptance) are calibrated on the vendor's data. They are not
  StateRadar acceptance rules; see the [cascade plan](plan-model-cascade.md).

## Accounting and recovery

The tool reserves an estimated maximum before each request using byte length,
the requested output limit, and peak published prices. It records usage after
a response. Flash input is charged at the peak cache-miss rate in this
estimate even when the provider reports a cache hit. Jev output is free at the
current listed price. Rates are $0.30 per million Flash input tokens, $1.20
per million Flash output tokens, and $0.042 per million Jev input tokens.
Update the implementation when provider prices change.

The reservation is an estimate, not a provider-enforced spending cap. If
actual usage exceeds it, the ledger records the actual amount and blocks
future calls when the limit is exceeded. Timeouts, invalid usage responses,
and interrupted calls retain their reservations, since their actual costs are
unknown. Concurrent calls to one ledger reserve using SQLite transactions. The
ledger covers only calls through these tools. The main agent or any other
provider has separate billing, so any budget for strong-model review is not
enforced here. Failed requests and provider billing changes may also make the
ledger differ from an invoice.

A failed request reports its reservation id, and for an HTTP error the start
of the provider's error body (for example `max_tokens_exceeded`). If the
provider answered but the ledger could not record it (a locked database), the
answer is printed (in `draft-verify`, kept as
`verification.unrecorded_response` with a `question_claims` map to claim ids)
and the error names the exact `settle` command. If Jev answers but the answer
fails validation, `draft-verify` records its settled tokens and cost next to
the error. Inspect reservations with `status`. After checking the provider's
usage, reconcile an uncertain call with `settle CALL_ID ACTUAL_MICRODOLLARS`.
Change the limit deliberately with `set-limit MICRODOLLARS`.

```bash
python3 tools/local_models.py --ledger "$ledger" status
python3 tools/local_models.py --ledger "$ledger" settle 1 1200
python3 tools/local_models.py --ledger "$ledger" set-limit 3000000
```

The ledger includes no prompt text, but its database is local task data.
Prices and usage figures are estimates in US dollars. An output ending for any
reason other than `stop` may be incomplete and must be reviewed.


### Predictable pilot artifacts and controller comparison

The pilot runner defaults to `--routing-variant routed` with selective
output. Matrix rendering and the Flash schedule sweep remain explicit
variants. `--model gpt-6.1-sol` is the reference; `--model gpt-6.1-terra`
is an experimental controller using the same ChatGPT login and medium
reasoning effort. The experiment manifest records the selected model.
Model choice does not change the provider ledger or pilot instructions.

Prompt v1.29 requires reviewed `catalogue-fields.json`, rendered by
`tools/pilot_artifacts.py catalogue FIELDS OUTPUT`. The runner verifies
that the catalogue still matches those fields. Coverage omissions,
unknown UV references, and inconsistent UV prefixes fail before writing.
`pilot_artifacts.py citations SOURCE LINE [LINE ...]` copies exact source
lines as JSON without judging the associated claim.

Blind coverage accepts distinct situations for the same event, with an
explicit Situation column; duplicate or missing situation labels fail.
The checklist still ticks each event and pair ordering exactly once.
A Part-A controller never edits a blind response to make it pass.

The controller runs with `--sandbox workspace-write` in the disposable
component checkout, matching its artifact-writing task. The pilot command
server still applies its macOS sandbox and restricts credentials to routing
commands. A read-only controller setting conflicts with authorized artifact
creation even when the external command server can perform writes.

The [matched Sol/Terra screen](evidence/pilot-artifact-model-comparison/README.md)
did not support changing the default controller: Terra stopped incomplete
on both components. Sol's Pool artifacts passed local checks after a service
cutoff, but its final controller cost is missing. Treat the reported dollar
figures as cost equivalents under the stated credit conversion, and include
failed attempts and fallback work before claiming savings.

### Usage checkpoints and interrupted pilots

The runner now keeps its fresh Codex session on disk rather than using
`--ephemeral`. Authentication still uses the existing ChatGPT login and
`--ignore-user-config`. Prompts and tool transcripts therefore also remain in
Codex's local session storage. The supervisor reads only the rollout whose ID
was emitted by its own child; it does not inspect unrelated chat contents.

`usage-history.jsonl` records changed cumulative counters from local
`event_msg/token_count` records. `usage-checkpoint.json` is atomically replaced
while the controller runs. This local format was verified with Codex
0.167.0-alpha.4.1 and is version dependent. Missing, malformed or unavailable
records yield an explicit unknown/partial result, never a fabricated zero.
The documented app-server also exposes `thread/tokenUsage/updated`, but this
implementation retains the existing CLI configuration and tool isolation.

A successful final `turn.completed` supplies `usage.json`; failed runs keep
only partial checkpoints. An in-flight failed request may have unreported
cost even when a checkpoint exists. `cost-estimate.json` combines reported
Codex usage with the settled Flash/Jev ledger, using the dated standard-speed
rates and an explicit $0.04/credit assumption. Its total stays null when the
controller usage is incomplete or provider reservations remain outstanding.
These are rate-based estimates, not account debits. Supervising-chat work and
human review remain outside the measurement.

The runner now executes artifact gates even after controller failure and
writes `phase-status.json`. A failed controller with passing artifacts is
still not a completed run. Recovery starts from the retained evidence and
failed gates, with human decisions left open. It does not automatically retry
a service refusal, resume a paid run, or approve domain semantics.

A third pinned fixture is available as `--component semaphore` using the
`golang.org/x/sync` v0.17.0 checkout. The boundary is one weighted semaphore;
public API comments supplement the repository README as contract evidence.

Completion also requires `pilot_artifacts.py audit ANALYSIS --repo REPO`:
all pilot phase deliverables must be nonempty; manifest component and source
HEAD must match; watch paths must exist inside the repository; and the sidecar
must repeat that identity. `WORKTREE`, missing manifests and stale sidecars
cannot satisfy a finished pilot. These checks supplement the six existing
semantic/catalogue gates rather than replacing them.
