# Draft PR reconciliation, 2026-11-15

Compared against main `409faef6e08c9c2490c48e0a67782ec14b6dbc36` after
fetch. Git ancestry alone does not establish functional equivalence.

* PR #11 (`1a40136f1668cc50a1645b7ae315545b75e9e2bc`): provenance labels,
  explicit `as-is:` detection and the relevant pilot instructions are already
  in main. The old branch lacks newer distinct-situation and pair-coverage
  checks; merging it wholesale would risk undoing those checks. Its missing
  zero-count warning and prose pointers are selectively implemented with red
  probes. A prose mention is a pointer, not a judgment of independence.
* PR #12 (`fc677c6a6d8af5c582faf1c5e107a4a8dc4d69d0`): the `draft-cells`
  command, Jev checking, comparison and experimental pilot variant already
  exist in main. Main additionally contains later changes including compact
  output and expanded scope checks. No whole-branch merge is justified by this
  comparison. The variant is not promoted.
* PR #13 (`1ae413373f29c59e03f06c3ad8d9d1c11c1a26c8`): the 107 original
  evidence files did not exist under the archived path on main. Their Git blob
  hashes were verified against the PR commit after copying. The archived
  reachability failure, differing-model cost confound and limits remain intact;
  see `flash-writes-pool-2026-11-13/ARCHIVE.md` and `comparison.md`.

The scope is the listed PR changes and archive; this is not a proof of full
semantic equivalence of every branch in the repository. Raw archived files are
historical records, not regenerated results. The archived blind check on the
current tool is a separate diagnostic, not an alteration of the original run.
