# GEPA training catalog and fixed-prompt baseline

## Result

Twelve source-backed cases on five components have been reviewed in a separate
AI session, including historical misses/overgeneralizations and controls. The
same general task and fixed prompt used in the previous discovery experiment
were run twice per component, with no case inventory, reference tests or prior
reports in the model inputs. No GEPA optimization was run in this work.

A separate reviewer assessed every one of the 60 returned findings against
source and references. There are **7 fully credited, 9 partial and 8 missing**
case observations out of 24 (12 cases x two calls). At finding level, the
reviewer marked **8 false, 4 uncertain and 48 valid**. These are different
units: a finding can cover multiple cases, and a partly correct case can be
contained in a finding that also makes a false broader claim. A partial is not
a full hit. All model responses, judgments and their reasons are retained.

| Case | First / second fresh call | Meaning |
|---|---|---|
| G01 | found / missing | Gobreaker wrapper overwrite redirects completion |
| G02 | missing / missing | Local caller-variable rebinding does not redirect |
| C01 | partial / partial | Cond condition-lock obligation vs optional notification lock |
| C02 | found / found | Signal before registration is not a saved permit |
| W01 | missing / missing | Legacy `panicnil=1` changes nil recover path |
| W02 | found / found | Non-nil recover re-panics before Done; panic excluded by contract |
| W03 | missing / partial | Outside-bubble Wait in the exact retained-association sequence |
| W04 | missing / partial | Owning-bubble Wait disassociates before later outside Wait |
| T01 | partial / partial | Repeated Stop contradiction and OPEN wording question |
| T02 | partial / partial | Reset after expiry and overlapping callback execution |
| P01 | partial / missing | Get/Put idle-miss, queue, bypass and later wake sequence |
| P02 | found / found | Put hands to the first already-enrolled waiter |

The timer partials contain the correct repeated-Stop or overlapping-callback
observation, but their encompassing findings also make an unqualified claim that
Stop/Reset after expiration returns false. The reference probe demonstrates a
counter-ordering with an intervening rearm and a true return. The reviewer
interpreted these if-statements as universal when they did not exclude rearm;
this is a deliberately strict, attributed interpretation, not proof that every
reader must understand them that way. The previous discovery experiment had
accepted similar abbreviated wording; its historical reviews are unchanged.
Both model outputs did retain the repeated-Stop wording question as OPEN.

Other concrete review findings: both Gobreaker outputs contain an unconditional
accounting assertion that omits the generation gate; one WaitGroup output
assumes observing a positive counter guarantees waiter registration despite a
possible failed CAS, and another incorrectly says outside Wait returns in the
retained-bubble state. Pool statements saying an entry is "closed" or an error
is "wrapped" were marked uncertain where the callback can fail or `fmt.Errorf`
uses `%s` rather than `%w`. These are reviewed assertions, not owner decisions.

The stable examples make this a **plausible training signal**, particularly
P01 and the timer rearm scope, but the sample is too small to establish rates or
a GEPA benefit. A new optimization should keep an independently prepared,
previously unexposed component set for selection and final evaluation; these
12 cases have all been exposed and are training/regression material only.

## Review and evidence

[Catalog](catalog.json) contains complete starting conditions, expected
observations, question status, previous-run provenance, and exact hashed
source/test/output anchors. In particular, the earlier historical Gobreaker
runs 004 and 008 used separate GEPA proposal paragraphs, not the fixed seed;
the separate review caught and corrected the initial misattribution before
freezing. The Pool cases were narrowed to an open pool, valid connections, no
expiry/interfering operations, and the first or sole waiting Get; P01 explicitly
permits its described later Get. Pool's combined input and original file/line
mapping are in `pool-source/`.

The separate reviewer was Codex session `/root/independent_review`, not a human;
its [12 case decisions](independent-review/review.json), independently authored
controls and complete raw race-test outputs are retained. The reviewer replayed
14 named tests/subtests five times each, including Gobreaker rebinding, timer,
Cond, WaitGroup and Pool cases. The Pool recheck mutant fails at the specified
assertion, demonstrating sensitivity; this is a test-only altered source, not a
new normative decision. Three further Gobreaker controls ran five times in an
archive of the pinned source. The first independent B05 run failed due to a bad
fixture path; `gepa-independent-b05.jsonl` retains that failure and the
corrected run is recorded separately. The timed Cond probe observes bounded
nonreturn; the notify-list callee supplies the stronger source explanation.

The fresh outputs were graded in the separate session and key disputed judgments
were checked again by the experiment operator. This is not an independent human
second review; labels and intent questions remain reviewable. The six-finding
output limit also affects which behaviors can appear, so an omitted case does
not by itself prove the model could not answer a direct question about it.

The fixed-prompt model received source and task instructions only. Pool's source
input combines two pinned files and preserves a line map; it does not include
previous analyses. Ten Codex calls completed with full recorded usage and no
repair. Their total rate-equivalent cost is **$0.35819**, using the recorded
$0.04/credit assumption. It is not an account debit; reviewing and supervision
were not metered. [Protocol](protocol.md), [raw outputs and reviews](runs/),
[recomputed results](runs/assessment.json), and [independent review](independent-review/)
are retained. No messages were sent to upstream owners.

## Verification and limitations

`tools/gepa_training_catalog.py` checks exact hashed source fragments, complete
case inventory and attributed separate-review coverage. `tools/verify_gepa_training.py`
replays source mapping, named test discovery, the intended Pool red control,
review completeness, frozen inputs, exact model prompts, forbidden tool events,
call usage and all scores. It validates review records, not semantic entailment.
The catalog, review gate, evidence, mapping, prompt and archive mechanisms were
first exercised with permissive stubs or omitted inputs and observed red; their
red and green outputs are archived alongside this file.

Deterministic replay, without new model calls:

```sh
.venv/bin/python tools/selftest/test_gepa_training_catalog.py
.venv/bin/python tools/selftest/test_gepa_training_evidence.py
.venv/bin/python tools/selftest/test_gepa_training_archive.py
.venv/bin/python tools/verify_gepa_training.py
```

This work does not change StateRadar domain rules, standard model routing or
blind Part B. The benchmark author and reviewer are separate AI sessions, not
independent humans, and several cases were prior GEPA test cases. No broad
reliability or unseen-component result is claimed.
