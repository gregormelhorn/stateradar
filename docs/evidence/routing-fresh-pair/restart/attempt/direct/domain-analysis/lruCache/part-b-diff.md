# Part B comparison

Fresh isolated Codex dispatch used only the inspected package, no implementation files or Part A analysis beyond the catalogue and normative doctrine. Package-only and dispatch inputs matched. Mechanical coverage: 32 event IDs, 82 unique pair-ordering IDs independently counted against 41 catalogue pairs; 114 situations. No missing/repeated situations, no missing or duplicate checklist IDs. See pilot log 088. Blind table itself retained verbatim.

Independence: the coverage tool reports three as-is rows: Scope (the convention table, not an event), CaptureEviction and CallbackReturn. Do not count agreement on those event rows as independent. The catalogue's labelled remembrance and lock sections state buffer ownership, slice retention and callback locking as observations, so agreement about those facts in CaptureEviction, CallbackReturn, CallbackReenter, UV-08/10/11/12 and callback-related pair rows is not independent. No unlabelled source-derived defect conclusion was found in event prose; event descriptions name scenario inputs (such as a late/aborting callback), not a prescribed result. No retained or removed analysis IDs were reported by the pack. No vocabulary drift: bold/as-is wrappers and the assumed-state qualifier preserve the literal vocabulary. B often uses handle over one usable-cache situation; A models guarded occupancy transitions inside it. The table compares actual effects, using this recorded mapping, not the surface verb difference.

| ID | Blind situation | Classification | Comparison / question |
|---|---|---|---|
| New | Construction with requested capacity and optional callback | convergent-hole | Positive construction agrees; capacity domain and failed receiver semantics fold into Q-11. |
| Purge | Usable receiver, empty or populated | divergence | Clear agrees for normal keys, but NaN entries survive and can be delivered again (Q-04); callback coverage is open (Q-13). |
| Resize | Usable receiver; supported requested capacity | convergent-hole | Positive resize agrees, unsupported sizes/failure disposition remain Q-02/Q-03. |
| Add | Key present or absent | convergent | Normal hit/miss and recency or projection semantics agree under live receiver and supported keys. |
| Get | Key present or absent | convergent | Normal hit/miss and recency or projection semantics agree under live receiver and supported keys. |
| Contains | Key present or absent | convergent | Normal hit/miss and recency or projection semantics agree under live receiver and supported keys. |
| Peek | Key present or absent | divergence | Observed zero-value miss is more specific than contract; Q-14. |
| ContainsOrAdd | Key present or absent | convergent | Normal hit/miss and recency or projection semantics agree under live receiver and supported keys. |
| PeekOrAdd | Key present or absent | divergence | Normal conditional effect agrees; miss value not specified by docs, Q-14. |
| Remove | Key present or absent | divergence | Stored entry removal agrees; explicit-removal callback scope open, Q-13. |
| RemoveOldest | Receiver populated or empty | divergence | Removes oldest as expected; empty signal and explicit callback scope open, Q-13/Q-14. |
| GetOldest | Receiver populated or empty | divergence | Code returns zero/false on empty and does not refresh oldest; exact contract open Q-14. |
| Keys | Any usable receiver | convergent | Normal hit/miss and recency or projection semantics agree under live receiver and supported keys. |
| Values | Any usable receiver | convergent-hole | Independent snapshot agrees; separate Keys pairing gap Q-12. |
| Len | Any usable receiver | convergent | Normal hit/miss and recency or projection semantics agree under live receiver and supported keys. |
| Cap | Any usable receiver | divergence | Expected thread-safe observation; observed read races with Resize write; Q-01. |
| CaptureEviction | Internal capture associated with removal and registered adapter | pass-B-blind-spot | As-is report from catalogue; does not independently derive retention or failed NaN deletion, Q-04/Q-07. |
| DeliverEviction | Registered callback and an eviction to report | convergent-hole | Notification agrees, timing/failure unspecified Q-05/Q-06; explicit removal Q-13. |
| CallbackReturn | An invoked callback returns normally | pass-B-blind-spot | As-is continuation agrees, no independent guarantee for global return order or retained data Q-05/Q-07. |
| CallbackReenter | Active callback invokes a cache API | convergent-hole | Observed reentry has no documented guarantee, Q-05/Q-06. |
| UV-01 | Construction omitted, delayed, unsuccessful, or not yet published | convergent-hole | Missing or failed constructor use unspecified; actual nil-store panic Q-11. |
| UV-02 | Invalid, unintended, or duplicate construction | convergent-hole | Duplicate success allocates separate cache; nonpositive returns real error, no documented policy Q-11. |
| UV-03 | Purge omitted, delayed, repeated, or stale after repopulation | convergent-hole | Repeated clear agrees within reflexive domain; no generation or tail contract Q-06/Q-09 and NaN exception Q-04. |
| UV-04 | Invalid, extreme, repeated, unintended, or competing Resize | convergent-hole | Invalid-domain gap agrees; exact negative count/wrap not found in B, Q-02/Q-03. |
| UV-05 | Omitted operation, abandoned wait, or stale request | convergent-hole | Can only act on received call; cancellation or stale publication gaps Q-08/Q-09. |
| UV-06 | Repeated or overlapping Gets, conditional adds, Adds, or Removes | convergent | Independent reads and retained value semantics match observed model. Q-10 stays open for documentation. |
| UV-07 | Wrong receiver, wrong payload, stale generation, or contradictory same-key calls | convergent-hole | Ordinary valid call uses actual receiver; no policy for wrong/stale intent Q-09. |
| UV-08 | Comparable but non-reflexive key, such as NaN | convergent-hole | Non-reflexive contract unknown; exact orphan and repeat-Purge behavior is Pass A evidence, Q-04. |
| UV-09 | Interface key containing a non-comparable dynamic value | convergent-hole | Panic is not a required response; missing input/failure policy Q-11. |
| UV-10 | Callback panics, terminates its goroutine, waits indefinitely, or returns late | convergent-hole | Callback abort/progress unspecific in both passes, Q-06/Q-08. |
| UV-11 | Overlapping callbacks or duplicate, stale, contradictory, or misdirected nested work | convergent-hole | No promised overlap/reentry ordering; nested valid calls ordinary, Q-05/Q-09. |
| UV-12 | Late or aborting callback around Purge/Resize, including captured tail | convergent-hole | Mutation stays committed; old notification and tail contract remain open Q-06. |
| P-01a | Purge → Add | convergent | Ordered operation effects agree for the valid scenario in P-01a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-01b | Add → Purge | convergent | Ordered operation effects agree for the valid scenario in P-01b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-02a | Purge → Get | convergent | Ordered operation effects agree for the valid scenario in P-02a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-02b | Get → Purge | convergent | Ordered operation effects agree for the valid scenario in P-02b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-03a | Purge → Contains | convergent | Ordered operation effects agree for the valid scenario in P-03a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-03b | Contains → Purge | convergent | Ordered operation effects agree for the valid scenario in P-03b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-04a | Purge → Peek | convergent | Ordered operation effects agree for the valid scenario in P-04a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-04b | Peek → Purge | convergent | Ordered operation effects agree for the valid scenario in P-04b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-05a | Purge → ContainsOrAdd | convergent | Ordered operation effects agree for the valid scenario in P-05a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-05b | ContainsOrAdd → Purge | convergent | Ordered operation effects agree for the valid scenario in P-05b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-06a | Purge → PeekOrAdd | convergent | Ordered operation effects agree for the valid scenario in P-06a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-06b | PeekOrAdd → Purge | convergent | Ordered operation effects agree for the valid scenario in P-06b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-07a | Purge → Remove | convergent | Ordered operation effects agree for the valid scenario in P-07a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-07b | Remove → Purge | convergent | Ordered operation effects agree for the valid scenario in P-07b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-08a | Purge → RemoveOldest | divergence | Empty RemoveOldest signalling not specified by requirement; observed zero pair and false, Q-14. |
| P-08b | RemoveOldest → Purge | convergent | Ordered operation effects agree for the valid scenario in P-08b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-09a | Purge → GetOldest | convergent | Ordered operation effects agree for the valid scenario in P-09a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-09b | GetOldest → Purge | convergent | Ordered operation effects agree for the valid scenario in P-09b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-10a | Purge → Keys | convergent | Ordered operation effects agree for the valid scenario in P-10a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-10b | Keys → Purge | convergent | Ordered operation effects agree for the valid scenario in P-10b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-11a | Purge → Values | convergent | Ordered operation effects agree for the valid scenario in P-11a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-11b | Values → Purge | convergent | Ordered operation effects agree for the valid scenario in P-11b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-12a | Purge → Len | convergent | Ordered operation effects agree for the valid scenario in P-12a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-12b | Len → Purge | convergent | Ordered operation effects agree for the valid scenario in P-12b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-13a | Purge → Cap | convergent | Ordered operation effects agree for the valid scenario in P-13a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-13b | Cap → Purge | convergent | Ordered operation effects agree for the valid scenario in P-13b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-14a | Resize → Add | convergent | Ordered operation effects agree for the valid scenario in P-14a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-14b | Add → Resize | convergent | Ordered operation effects agree for the valid scenario in P-14b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-15a | Resize → Get | convergent | Ordered operation effects agree for the valid scenario in P-15a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-15b | Get → Resize | convergent | Ordered operation effects agree for the valid scenario in P-15b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-16a | Resize → Contains | convergent | Ordered operation effects agree for the valid scenario in P-16a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-16b | Contains → Resize | convergent | Ordered operation effects agree for the valid scenario in P-16b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-17a | Resize → Peek | convergent | Ordered operation effects agree for the valid scenario in P-17a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-17b | Peek → Resize | convergent | Ordered operation effects agree for the valid scenario in P-17b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-18a | Resize → ContainsOrAdd | convergent | Ordered operation effects agree for the valid scenario in P-18a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-18b | ContainsOrAdd → Resize | convergent | Ordered operation effects agree for the valid scenario in P-18b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-19a | Resize → PeekOrAdd | convergent | Ordered operation effects agree for the valid scenario in P-19a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-19b | PeekOrAdd → Resize | convergent | Ordered operation effects agree for the valid scenario in P-19b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-20a | Resize → Remove | convergent | Ordered operation effects agree for the valid scenario in P-20a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-20b | Remove → Resize | convergent | Ordered operation effects agree for the valid scenario in P-20b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-21a | Resize → RemoveOldest | convergent | Ordered operation effects agree for the valid scenario in P-21a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-21b | RemoveOldest → Resize | convergent | Ordered operation effects agree for the valid scenario in P-21b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-22a | Resize → GetOldest | convergent | Ordered operation effects agree for the valid scenario in P-22a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-22b | GetOldest → Resize | divergence | Observed GetOldest does not move victim; docs leave this exact ordering open, Q-14. |
| P-23a | Resize → Keys | convergent | Ordered operation effects agree for the valid scenario in P-23a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-23b | Keys → Resize | convergent | Ordered operation effects agree for the valid scenario in P-23b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-24a | Resize → Values | convergent | Ordered operation effects agree for the valid scenario in P-24a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-24b | Values → Resize | convergent | Ordered operation effects agree for the valid scenario in P-24b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-25a | Resize → Len | convergent | Ordered operation effects agree for the valid scenario in P-25a; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-25b | Len → Resize | convergent | Ordered operation effects agree for the valid scenario in P-25b; cache occupancy movement maps to B's handle on its coarser usable-cache state. |
| P-26a | Resize → Cap | divergence | New cap after ordered Resize agrees; overlapping read is not thread-safe, Q-01. |
| P-26b | Cap → Resize | convergent | Old size if an established order puts Cap before Resize. Overlap separately addressed by Q-01. |
| P-27a | Purge → CallbackReturn | convergent-hole | Committed effects persist; callback tail, failure and progress left open Q-06/Q-08. |
| P-27b | CallbackReturn → Purge | convergent-hole | Committed effects persist; callback tail, failure and progress left open Q-06/Q-08. |
| P-28a | Purge → CallbackReenter | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-28b | CallbackReenter → Purge | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-29a | Purge → UV-10 | convergent-hole | Committed effects persist; callback tail, failure and progress left open Q-06/Q-08. |
| P-29b | UV-10 → Purge | convergent-hole | Committed effects persist; callback tail, failure and progress left open Q-06/Q-08. |
| P-30a | Resize → CallbackReturn | convergent-hole | Committed effects persist; callback tail, failure and progress left open Q-06/Q-08. |
| P-30b | CallbackReturn → Resize | convergent-hole | Committed effects persist; callback tail, failure and progress left open Q-06/Q-08. |
| P-31a | Resize → CallbackReenter | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-31b | CallbackReenter → Resize | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-32a | Resize → UV-10 | convergent-hole | Committed effects persist; callback tail, failure and progress left open Q-06/Q-08. |
| P-32b | UV-10 → Resize | convergent-hole | Committed effects persist; callback tail, failure and progress left open Q-06/Q-08. |
| P-33a | Add → CallbackReenter | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-33b | CallbackReenter → Add | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-34a | Get → CallbackReenter | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-34b | CallbackReenter → Get | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-35a | ContainsOrAdd → CallbackReenter | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-35b | CallbackReenter → ContainsOrAdd | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-36a | PeekOrAdd → CallbackReenter | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-36b | CallbackReenter → PeekOrAdd | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-37a | Remove → CallbackReenter | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-37b | CallbackReenter → Remove | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-38a | RemoveOldest → CallbackReenter | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-38b | CallbackReenter → RemoveOldest | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-39a | Cap → CallbackReenter | convergent-hole | Nested operation on current contents agrees if executed; no reentry/order guarantee Q-05. |
| P-39b | CallbackReenter → Cap | divergence | Ordered size read matches; requirement-level expectation of a thread-safe read fails if overlap with nested Resize, Q-01; nested timing Q-05. |
| P-40a | Add → UV-10 | convergent-hole | Committed effects persist; callback tail, failure and progress left open Q-06/Q-08. |
| P-40b | UV-10 → Add | convergent-hole | Committed effects persist; callback tail, failure and progress left open Q-06/Q-08. |
| P-41a | New → UV-05 | convergent-hole | Independent old/new receivers agree; external publication or stale guard remains Q-09/Q-11. |
| P-41b | UV-05 → New | convergent-hole | Independent old/new receivers agree; external publication or stale guard remains Q-09/Q-11. |

Counts: {"convergent-hole":45,"divergence":11,"convergent":56,"pass-B-blind-spot":2}. Divergences are linked above to open questions. No catalogue artefact required repair; no blind table changes. A reusable review rule is to check separate read-then-mutate sequences as well as compound API calls and to separate an ordinary API outcome from an optional callback obligation. Both classes were already covered by the pilot's interleaving and independent-claim rules; the pack itself was not edited.
