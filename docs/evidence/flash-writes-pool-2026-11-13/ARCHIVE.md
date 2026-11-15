# Archived flash-writes experiment

These 107 original files were copied byte-for-byte from the branch
`flash-writes-pilot-evidence`, commit `1ae413373f29c59e03f06c3ad8d9d1c11c1a26c8`
([original draft PR #13](https://github.com/gregormelhorn/stateradar/pull/13)).
Their Git blob hashes were compared with that commit. This note was added later;
it is not part of the original run. The component and pack revisions are in
`analysis/manifest.json`.

Read `comparison.md` as a historical result: the pre-registered criteria were
not met because the reachability gate failed, and the cost comparison changed
steering models. The stored `runs/reach.out` is red; do not treat the archived
artifacts as a complete passing pilot. The direct comparison uses previously
exposed components and does not establish a general quality or cost advantage.
The transcript timing/cost calculation remains dependent on its stated
external session transcript; this archive does not add that missing transcript.

After import, the current blind-coverage checker was run on the archived
catalogue and blind table. It reported 11 events and 12 pair orderings covered,
zero explicitly marked `as-is:` rows, and nine rows mentioning `as-is` in prose.
Those nine are reading pointers, not nine proven leaks, and the zero is not
proof of independence. This post-import diagnostic does not change the original
output or the historical red reachability result.
