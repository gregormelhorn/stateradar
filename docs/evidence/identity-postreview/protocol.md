# Frozen final-review experiment

Declared before model calls. Compare a generic final review with the same review
plus an English identity paragraph. Use the previous bounded **baseline** final
reports and probe suites on both sides: 29 gobreaker findings and 74 transfer
findings. This tests preservation and incremental benefit, not rediscovery.
Both sides already inherit 8/8 gobreaker and 6/6 recipient-class coverage. The
transfer baseline has partial direct caller-variable-rebinding test coverage.

Four fresh sessions in order: gobreaker generic, gobreaker identity, transfer
identity, transfer generic. Same frozen pack f76591e, source commits/content,
gpt-6.1-sol medium via ChatGPT login, selective output, 900 seconds per session,
$2 provider ledger, Flash draft-verify and Jev 1.14.0. The identity paragraph is
the sole prompt difference within each pair. Correct the previous experiment's
Jev schema hint in the shared task before freezing this protocol. No retuning
between runs. Original model outputs remain immutable.

Enforce exact preservation of every baseline finding and question. New findings
append; qualifications/corrections and supplementary test bindings are separate.
Hash all supplied sources, baseline artifacts, existing probes and validators.
Old overlay entries must survive. The transfer arms must both create and run
TestIdentityCallerVariableRebinding: obtain F's callback using a local pointer,
reassign only that caller variable to a distinct Port/Account, then invoke the
saved callback; observe both accounts and the unchanged original Port. No expected
counter values or oracle enter the prompt. Independently review the test body and
replay all probes three times with the race detector and nonzero discovery.

Report retained benchmark coverage, new/qualified findings, explicit test scope,
lost or changed findings, failed commands/tests, rereads and additions. Count all
metered controller/provider work, including retries, as incremental review cost.
For each strategy also report the original baseline's complete cost plus this
review. Reusing the baseline as an input does not mean it was rerun or charged
twice in this experiment. Common implementation/supervising chat and human time
remain unmetered and are excluded, not zero. Dollar values use the previous
verified rates and explicit $0.04/credit assumption, not invoice debits.

Same-author synthetic transfer cases are not independently held out. One pair
per input, reversed across inputs, is not a repeated or statistically conclusive
comparison. Full-pilot/Part-B gates do not run. Intent questions remain open.
Do not promote a standard prompt solely for preserving rows mechanically or
passing tests. A late qualification must remain visible in the effective finding
assessment; immutable preservation must not conceal a known false claim.
