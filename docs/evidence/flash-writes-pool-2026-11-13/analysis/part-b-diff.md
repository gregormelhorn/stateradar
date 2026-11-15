# channelPool — Part B diff (blind pass vs matrix)

Blind run: `local_models.py blind` (Flash `deepseek-flash`, finish_reason stop, 6094 in / 3406 out tokens), inputs README.md, README_ZH_CN.md, blind-inputs/contracts.md (doc comments copied verbatim, headed by file:line) and the catalogue. Package: runs/blind.package.md (inspected before the real run: `--package-only` first). Table: runs/blind-table.md (saved from runs/blind.json). The inputs did not change between the two runs.

## Package inspection
* No implementation code in the package. The only code is the README usage block (requirements prose). Every `(` followed by a quote in the package is inside that README block (4 hits).
* Ids: stderr names two removed ids (`G-01`, `G-02`); no id was kept (no L-/G-/F-/T- id remains; checked by grep). Known loss: the two guard-group ids in the coverage table (they referenced analysis guards); no domain term is lost.
* Known leaks (the catalogue states code facts outside the labelled sections; Part B's agreement on these rows is not independent): UV table description "nil connection (explicitly rejected in code)"; event table Ping row "not in the Pool interface"; the pairs table orderings for P-02b, P-04a, P-06a, P-06b name implementation steps (first look versus lock, ping field, channel snapshot); implementation names appear in prose (`c.mu`, `openingConns`, `conns`). Labelled sections (gate, remembrance, upstream guard, lock discipline, event annotations, coverage) carry the label "observed in code, not documented intent".
* PART-B COVERAGE: OK (11 events, 12 pair orderings); the pairs table has 12 orderings (P-01a..P-06b): count confirmed. Every id has one row in the table (checked above).
* PART-B INDEPENDENCE line: absent. Part B marked 0 rows with `as-is:` (grep: 0 occurrences of the marker). Part B did write "as-is" in prose in the rows Put (e-g), Close (c-e), Ping (d), Release (b, c), UV-Conn-nil and P-06a; the agent treats Part B's agreement on those rows as not independent.
* Vocabulary drift: none (every disposition word is in the closed vocabulary; several rows give two values, "handle/UNSPECIFIED").

## Row classification (23 rows)

| row | class | observation | closing |
|---|---|---|---|
| Get | divergence | blind proposes `defer (queued)` for the Waiting states; matrix labels them `handle`/`transition` | fold into Q-02 (Part-B fold paragraph) |
| Put | convergent-hole | UNSPECIFIED for Closed, nil, duplicate, foreign; matrix holes | Q-05, Q-11, Q-13; (IdleFull close rests on the code comment at channel.go:195, which Part B did not receive) |
| Close | convergent-hole | UNSPECIFIED after Release, nil, duplicate, foreign | Q-05, Q-10, Q-12, Q-14 |
| Ping | artefact | blind reads DOC-3 into Ping ("invalid connections must be discarded") although Ping only returns the callback's verdict; convergent-hole on the unconfigured case (Q-06) | catalogue repaired after the run: Ping payload gist now says it returns the verdict and Get decides (Part B was not re-run) |
| Release | convergent-hole | borrowed connections, waiters, second Release UNSPECIFIED | Q-05, Q-01, Q-24 (second Release) |
| Len | convergent-hole | definition of "in the pool" and Len after Release UNSPECIFIED | Q-18 (Part-B fold) |
| UV-Conn-nil | divergence | blind: UNSPECIFIED; matrix: `reject` on code evidence | fold into Q-24 (Part-B fold 1) |
| UV-Put-dup | convergent-hole | UNSPECIFIED | Q-11 |
| UV-Close-dup | convergent-hole | UNSPECIFIED | Q-12 |
| UV-Put-foreign | convergent-hole | UNSPECIFIED | Q-13 |
| UV-Close-foreign | convergent-hole | UNSPECIFIED | Q-14 |
| P-01a | divergence | blind: no requirement that Release closes the just-returned connection; matrix control trace rests on code only | fold into Q-24 (Part-B fold 2) |
| P-01b | convergent-hole | Put after Release UNSPECIFIED | Q-05 |
| P-02a | convergent-hole | queued waiters on Release UNSPECIFIED | Q-01 |
| P-02b | convergent-hole | Get with an earlier first look vs Release UNSPECIFIED | Q-01, Q-07 |
| P-03a | convergent-hole | waiter wake on freed capacity UNSPECIFIED | Q-03 |
| P-03b | divergence | blind: no rule for Get after Close at capacity; matrix control trace | fold into Q-03 (Part-B fold) |
| P-04a | convergent-hole | visibility of a racing Put UNSPECIFIED (not independent: the catalogue ordering text names the lock step) | Q-04 |
| P-04b | divergence | blind: no preference of idle over creating stated; matrix control trace | fold into Q-24 (Part-B fold 3) |
| P-05a | convergent-hole | Put then Close of one connection UNSPECIFIED | Q-11, Q-12 |
| P-05b | convergent-hole | Close then Put UNSPECIFIED | Q-11, Q-12 |
| P-06a | convergent-hole | Get past the closed check vs Release UNSPECIFIED (not independent: the ordering text names the ping field); the nil-function call is not visible to Part B | Q-07 |
| P-06b | convergent-hole | stale-snapshot Get vs Release UNSPECIFIED | Q-07 |

Counts: {'divergence': 5, 'convergent-hole': 17, 'artefact': 1}. Every divergence is closed as a fold into an existing question; no new question was needed. Pass-B blind spot: none recorded (Part B never saw the code comment at channel.go:195 or the code-level evidence for `ignore (documented)` on a second Release; that is by design).

Recurring class (rule: classes, not single findings): the blind pass answers `UNSPECIFIED` wherever the only evidence is code; control traces that rest on code alone therefore diverge. Not folded back into the prompt after one component.
