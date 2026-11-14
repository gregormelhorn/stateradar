# Executed evidence

All commands used the repository Python environment and local Go 1.27.3. No model calls or runtime implementation edits were made.

- `candidate-acceptance.txt`: verify.py, including seven artifact mutations, old-head-guard semantic counterexample and source-drift rejection, wrong-cell behavioral red, 340 cell and 160 pair executions, sidecar/reachability and 52 retained hashes.
- `decision-acceptance.txt`: verify_q01.py; 32 ordinary groups and six scheduled groups, each repeated 50 times with race detection; upstream regressions; four behavioral fault overlays.
- `pack-gates.txt`: full pack commands listed in pack-gates-command.txt. The separately recorded accounting suite is also mandatory in CI.
- `accounting-tests.txt`: nine accounting tests.
- `historical-reproduction.txt`: unchanged upstream pilot, seven gates plus upstream race tests and ten probes repeated five times.

The original full historical analysis and its manifest are not rewritten. The candidate current manifest deliberately uses WORKTREE until the source/tests are committed. The subsequent reconciliation records its pinned source commit and reruns preconditions at that commit.

`head-*.txt` repeats all preconditions on candidate commit 0b7502b4915de4996e71fbd56baa55b4377dbcfe before promotion. `post-*.txt` repeats current-model, full decision, pack and accounting acceptance after promotion. All exit 0; expected red probes are required and checked by their runners. `citation-refresh.txt` records the generic helper's zero Go matches; `markdown-citations.txt` records 154 verified active prose anchors, separately from the 193 structured occurrences.
