# Raw evidence: first routed pilot (silenceper/pool, channelPool)

Raw outputs were not edited after the run; this README was written afterwards.

**Blindness caveat.** The operator brief named the primary finding, and
`routing/task-channel.md`, written by the Part-A agent, gives Flash the example
"Release while a Get is waiting". `comparison.md` calls Flash's question 4
independent evidence; it is not. `channelPool/summary.md` counts 4 questions as
added by routing (Q-20..Q-23); in Q-22 and Q-23 the agent's own scope line was
already `no`, so the base scope rule raises them without Jev.

## Versions

| item | version |
|---|---|
| pack (stateradar) | da655aa |
| target repo (silenceper/pool) | 6084537 |
| pilot prompt | v1.16 |
| Jev model | jev-1.14.0 |
| Flash model | deepseek-flash (as recorded in `partb/blind.stdout`) |

## Layout

* `channelPool/` — pilot artefacts (catalogue, matrix, guards, invariants, traces,
  questions, sidecar, manifest, summary) plus the per-run helper scripts
  `check_matrix.py`, `check_guards.py`, `verify_fragments.py`, `merge_sidecar.py`.
* `routing/` — task files, raw stdout/stderr and JSON for every `draft-verify` (`dv-*`)
  and `jev-batch` (`step6-*`, `step8-*`) call, `ledger-status.json`, and `lm.sh`.
* `partb/` — blind-session inputs (requirements, contracts, pre-strip catalogue) and
  raw outputs (`blind-output*.md`, `blind.stdout`, `blind.stderr`).
* `comparison.md` — comparison write-up.

## Commands

All model calls went through the wrapper `routing/lm.sh`:

```bash
python3 <pack>/tools/local_models.py --ledger <tmp>/ledger.db "$@"
```

The `draft-verify` calls were run in parallel, one per source file, in this form
(from the step-1 script; `<file>` ∈ README.md, channel.go, pool.go, channel_rpc_test.go,
`<name>` ∈ readme, channel, pool, tests):

```bash
lm.sh draft-verify pool/<file> routing/task-<name>.md --output routing/dv-<name>.json \
  --model jev-1.14.0 > routing/dv-<name>.stdout 2> routing/dv-<name>.stderr
```

The channel.go re-run added `--max-tokens 12000` (`dv-channel-r2.*`).

The exact argument lists of the `jev-batch` (steps 6 and 8) and `blind` calls were not
recoverable when this folder was assembled; their inputs and outputs are the
`routing/step6-*.json`/`step8-*.json` (input → `*.out.json`) and `partb/` files, and
`channelPool/summary.md` ("Model routing record") lists every call with its result.
Part B was `blind --package-only` twice, then `blind` once.

## Tool/prompt problems reported by the pilot session

Added afterwards from the pilot session's final report; the disposition
column says what the follow-up commit changed.

| # | Problem | Disposition |
|---|---|---|
| 1 | `draft-verify` on `channel.go` (248 lines) was cut off at the default 4096 output tokens; the truncated text went to stdout and no `.draft.txt` was kept. Rule 8 did not say whether a larger budget counts as loosening. | Fixed: default 12000, truncated drafts saved as `<stem>.draft.txt` and not printed; rule 8 allows one re-run with a larger budget. |
| 2 | Hollow check: `gen_analysis_sidecar.py` dropped every `("fragment")`, so `dsc_check`'s fragment verification never ran on a generated sidecar. | Fixed with a red selftest; the selftest's own compound fixture turned out to cite wrong fragments and lines, also fixed. |
| 3 | Hollow check: `check_matrix.py` split trace blocks only on bold headers, so a traces file with `###` headers passed the scope-line check vacuously. | Fixed with red selftests for both header styles. |
| 4 | Rule conflict: rule 3 puts code fragments into catalogue citations, and the catalogue went into the Part-B package verbatim (16 code fragments plus Q-/lint references). Remembrance semantics also tell the blind pass the as-is outcome. | The Part-B catalogue copy now drops fragments, line numbers and analysis ids (Q-, PA-, SYS-, NAT-, DR- always; L-, G-, F-, T- unless the requirements, contracts or quoted doctrine text use them) and keeps quotes only from the Part-B source files, tested on `partb/event-catalogue.pre-strip.md`. Prose conclusions (remembrance, gate, upstream-guard, lock-discipline annotations) cannot be stripped mechanically: rule 7 lists them as known leaks, and roadmap entry 11 records the limit. |
| 5 | `blind` resolves the analysis directory and `--requirements`/`--contracts` against `--repo`, not the working directory. | Documented in rule 7 and the routing doc. |
| 6 | Step 7 named ODC triggers (`part-B diff`, `reviewer cross-check`, `step-8 verification`, `z3 proof`) that `formats/rules.toml` did not contain, so `dsc_check` would reject them. | Fixed: the registry gained `part-B diff`, `reviewer cross-check` and `step-8 verification`, plus `z3 invariant check`, `draft-verify` and `jev check`; the prompt's `z3 proof` became the existing `pairs table + z3 proof` or `z3 invariant check`; the prompt lists the vocabulary exactly, and `check_pack_consistency.py` fails on drift (red first). |
| 7 | `gen_analysis_sidecar.py` does not merge pairs, guard outcomes or ODC fields, and ignored `## Q-nn` question headings. | Headings fixed (red selftest). Merging pairs, guards and ODC fields stays open (roadmap entry 11). |
| 8 | `check_reachability.py` follows transition cells only and takes the first state as initial; the first run was red until guarded changes were written as transitions and terminal states declared. | Not changed in this round; recorded. |
| 9 | Jev judged equivalent claims about the same line differently (C59 and K5 `contradicted`, C78 `supported`; C59 and C78 cite the same fragment, K5 the next line). | Recorded as evaluation input (roadmap entry 11). |
| 10 | `status` reports provider, amount and status only: no tokens, timestamps or step labels. | Open (roadmap entry 11). |
| 11 | `go test` was not permitted on the pilot machine, so as-is validation was a static walk (predicted `TestPool_Get` hang unverified). | Open. |
| 12 | Shell word splitting in the operator's own loops (`zsh`). | Operator error, no tool change. |
| 13 | Found in review, not by the pilot: `extraction.md` wrote the doctrine lines as a table under `### Doctrine-line sweep`; `part_b_pack.py` read only `- DOC-` bullets under `## Doctrine`, so `blind-output.package.md` carries no doctrine block. | Fixed: bullets, numbered items and table rows under any doctrine heading; an extraction that names DOC lines none of which can be passed on is refused (red tests). |
| 14 | Found in review: the draft task for `channel.go` named the race as its example (see the caveat above). | Rule 10: draft tasks are finding-neutral, and task files are kept. |
| 15 | Found in review: all 6 orderings `unclear`, so the provisional 0.5 veto voided every `yes`; the agent's statements added detail the fragments lack. Rule 5 did not forbid re-running with a reworded statement. | Rule 5 now forbids it; the cases are recorded as evaluation input (roadmap entry 11). |

## Excluded

* `ledger.db` — cost ledger (excluded by instruction).
* `routing/step1.sh` — the step-1 driver script; it matched the secret grep
  (`sk-|API_KEY=`), so it was withheld rather than copied. The match appears to be the
  substring `task-` in a file name, but it was not copied without review.
* No file exceeded 2 MB.
