You are the BLIND adversarial pass (Part B) of a domain-behaviour analysis. You have NO access to the implementation. Do NOT read any files, do NOT use any tools, do NOT search any repository — the inputs below are complete and are your ONLY sources. If you catch yourself wanting to look something up, label it an open point instead.

TASK: Here is the event catalogue of a component, and its requirements. For every event — including undesired variants and both orderings of every interaction pair — state in which situations the component should handle, ignore, or reject it, and what should happen. Describe situations in requirement terms. Name states per PA-17 (state naming convention): prefer public API names, name sub-states by their condition, use PascalCase with `_` as separator. If you must assume a lifecycle state the requirements do not name, label it `assumed-state:` with the condition that defines it. You have no access to the implementation. Be concrete. Produce a table keyed by the catalogue's event ids and pair-ordering ids. Prefer one row per id with conditional outcomes. If you split an id into several rows, use an explicit `Situation` column with distinct, nonempty labels. Do not repeat the same situation. End with a coverage checklist: every catalogue event id, listed once, ticked. A missing row must be impossible to miss.

Catalogue headings and fields labelled `observed in code` say what the implementation does, not what it should do. Base each row on the requirements, the contracts and the doctrine lines. When a row's expected behaviour rests only on observed-in-code text, start its behaviour cell with `as-is:`.

<!-- generated:rules key=partb-vocab -->
The disposition vocabulary you must use (from the methods reference): `transition → <target>` | `handle` (stays in the state, does something) | `ignore (documented)` | `ignore (accidental)` | `defer (queued)` | `reject` (a declared refusal signal: error, diagnostic, nack) | `UNSPECIFIED`. Without these definitions a blind pass applies `reject` and `handle` to identical semantics interchangeably (dobby trigger-service, 2026-08-05: four vocabulary-only "divergences").
<!-- /generated:rules -->

The catalogue's event ids are: E01 — plus the pair orderings .

=== INPUT 1: EVENT CATALOGUE (code fragments and analysis references removed) ===

<!-- event-ids: E01 -->
# Fictional single-button lamp catalogue
E01: Press is an external request from a user to switch the lamp on. The request contains no payload. The lamp has only the states Off and On. Each press is delivered once. This fictional example is exclusively for testing the blind dispatch path and is not related to any source repository.


=== INPUT 2: REQUIREMENTS (domain-analysis/lruCache/requirements.md) ===

# Fictional lamp requirements
The lamp starts in Off. When Press arrives in Off, the lamp transitions to On and emits a light-on effect. When Press arrives in On, the lamp stays in On and emits no additional effect. This fictional requirement fully specifies this one event and is used solely for a short technical smoke test.


=== INPUT 3: EVENT CONTRACT TEXTS (domain-analysis/lruCache/contracts.txt) ===

# Fictional event contract
Press is an external event with no parameters. The caller sends Press at most once per interaction. The event is delivered to the lamp in the order it is issued. The lamp is a single component with exactly two states: Off and On. The event contract has no additional error cases or unspecified payload fields.


Respond with ONLY the table and the coverage checklist: every catalogue event and pair-ordering id, listed once in the checklist, ticked. A missing row must be impossible to miss.
The coverage checklist must use one exact line per event or pair in the form '- [x] EVENT_ID', with no other text on that line.
