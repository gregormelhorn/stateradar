# Part B comparison

Independent Flash request received only the inspected catalogue, prose and copied contract text. Mechanically checked 26 event IDs and 32 pair-ordering IDs from 16 shared-entity pairs. Distinct situations reuse IDs, with one checklist tick per ID. The package emitted no kept or removed analysis-ID notices. The code file references in the contract section are provenance labels on docstrings. Source fragments were stripped from the catalogue; the remaining quote-parens were README prose.

Part B marked these five IDs as depending on as-is evidence: Create, Return, Expiry, UV-01, UV-12. Where the mark is mid-cell, it still counts. Other exposed as-is outcomes include the classification and refresh trigger in the event table, state commit preceding notification in UV-11, and lack of repeated-report validation or storage implied by the annotations. In the annotated sections, the late-report refresh order, fixed-width counters, lifecycle replacement, per-generation budget, retention, absence of a HalfOpen expiry and under-lock callback details are already reported. Agreement on any of these observations, and on cross-topology pair exclusions, is dependent. A matching proposition from a requirement is credited only within its scope. The unsupported `HalfOpen_AtBudget` name conflates a due timeout with admission consumption, folded into Q-12. Use one conditional row where possible while retaining distinct guards.

| Blind line | ID | Situation | Class | Comparison |
| --- | --- | --- | --- | --- |
| 3 | Create | Valid Settings, no callbacks | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 4 | Create | Settings with name/interval/timeout/classifier/trip/notify overrides | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 5 | Create | Duplicate / repeated construction | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 6 | Create | Out-of-order construction (use before construct) | divergence | No universal refusal: zero core readers can return values and zero wrapper dereferences nil. → Q-08 |
| 7 | Admit | Closed state, below failure threshold | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 8 | Admit | Open state, timeout not elapsed | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 9 | Admit | Open state, timeout elapsed (Expiry due) | divergence | Budget can exceed one. The refresh and first admission do not necessarily reach the cap. → Q-12 |
| 10 | Admit | HalfOpen, admissions below MaxRequests | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 11 | Admit | HalfOpen, admissions at MaxRequests | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 12 | Admit | MaxRequests 0 setting | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 13 | Admit | nil / wrong instance or settings | divergence | Wrong valid receiver is used; nil request panics if admitted; valid settings are constructor policy. → Q-07 |
| 14 | State | Any constructed instance | convergent | State refreshes on due Open expiry; separate row covers that guard. |
| 15 | State | Due expiry while Open | divergence | State refresh alone admits zero probes and therefore leaves HalfOpen below any positive budget. → Q-12 |
| 16 | State | Called before any Create | divergence | Zero core State can return Closed; nil and zero-wrapper cases can panic. → Q-08 |
| 17 | Counts | Closed, no interval elapsed | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 18 | Counts | Closed, interval elapsed | divergence | Counts is a lock-protected snapshot and does not clear a due interval. → Q-01 |
| 19 | Counts | Open / HalfOpen | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 20 | Counts | Called before Create | divergence | Zero core Counts returns zero counters; nil or zero-wrapper references can panic. → Q-08 |
| 21 | Name | Constructed with Name | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 22 | Name | Constructed with empty Name | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 23 | Name | Called before Create | divergence | Zero core Name returns empty; nil or zero-wrapper references can panic. → Q-08 |
| 24 | Report | HalfOpen, report success | divergence | A current success reaching threshold closes and clears; under threshold it stays. → Q-12 |
| 25 | Report | HalfOpen, report failure | divergence | HalfOpen failure opens and clears directly, without a failure increment. → Q-12 |
| 26 | Report | Report with no state change | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 27 | Report | Report after state change / clearing | divergence | Stale accounting is ignored but can itself refresh a due Open mode. → Q-04 |
| 28 | Report | Repeated same callback (identical payload) | divergence | Generation validity does not deduplicate reports. → Q-03 |
| 29 | Report | Contradictory repeat payload | divergence | There is no declared refusal. Order determines whether the later conflicting callback remains current. → Q-03 |
| 30 | Report | nil / wrong continuation | divergence | Valid wrong callback acts on its target; nil invocation faults in caller. → Q-07 |
| 31 | Return | Closed, error classifies as failure | convergent | A trip decision is a distinct listed situation. |
| 32 | Return | Closed, error classifies as success | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 33 | Return | Closed, nil error | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 34 | Return | ReadyToTrip returns true | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 35 | Return | HalfOpen, success under budget | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 36 | Return | HalfOpen, failure | convergent | Agrees on reopening; threshold source for HalfOpen is as-is and the failure takes the reset path. |
| 37 | Return | Stale (pre-clear) result | divergence | Outcome accounting is suppressed; classification and possible expiry effects still occur. → Q-04 |
| 38 | Return | Execute work abandoned / never returns | convergent-hole | Both expose an unresolved contract → Q-02. |
| 39 | Panic | Panic in request | convergent | Matches under ordinary request panic and successful reporting. |
| 40 | Panic | Panic with nil payload | divergence | Nil-panic recovery depends on toolchain/runtime setting; blanket same-panic guarantee is under-specified. → Q-08 |
| 41 | Panic | Panic after stale admission | divergence | No contribution, but stale panic can refresh and re-raise or encounter a failing hook. → Q-04 |
| 42 | Classify | IsSuccessful returns valid result | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 43 | Classify | IsSuccessful nil | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 44 | Classify | IsSuccessful panics / Goexits / blocks | convergent-hole | Both expose an unresolved contract → Q-06. |
| 45 | Classify | IsSuccessful re-enters breaker | convergent-hole | Both expose an unresolved contract → Q-05. |
| 46 | Classify | Wrong-but-valid classification | pass-B-blind-spot | Configured decisions are used. The boundary has no semantic validation of valid but mistaken values (Q-07). |
| 47 | TripPolicy | Closed, failure, ReadyToTrip returns false | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 48 | TripPolicy | Closed, failure, ReadyToTrip returns true | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 49 | TripPolicy | ReadyToTrip nil | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 50 | TripPolicy | ReadyToTrip panics / blocks / re-enters | convergent-hole | Both expose an unresolved contract → Q-06. |
| 51 | TripPolicy | Called in HalfOpen | divergence | An ordinary invocation is structurally prevented by state dispatch. No externally delivered TripPolicy is ignored. → Q-12 |
| 52 | Notify | State actually changed | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 53 | Notify | No state change | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 54 | Notify | OnStateChange nil | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 55 | Notify | OnStateChange panics / blocks / re-enters | convergent-hole | Both expose an unresolved contract → Q-05. |
| 56 | Notify | Duplicate / out-of-order observation | convergent-hole | Both expose an unresolved contract → Q-06. |
| 57 | Expiry | Open, now strictly before deadline | convergent | Equivalent staying outcome for the clock guard; no independent clock message exists. |
| 58 | Expiry | Open, now at/after deadline | divergence | Equality stays Open and a refresh enters HalfOpen with zero admissions. → Q-01 |
| 59 | Expiry | Closed with interval due | divergence | Clear is lazy and does not change the stored mode or notify. → Q-01 |
| 60 | Expiry | Interval 0 | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 61 | Expiry | HalfOpen | divergence | Closed-state and Open timing text gives HalfOpen no expiry, but no documented ignore or missing-report recovery is specified. → Q-02 |
| 62 | Expiry | Timeout ≤0 | convergent | Agrees for nonpositive Timeout using the contract; README names only zero. |
| 63 | Expiry | Clock sampled repeatedly / out-of-order | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 64 | UV-01 | Report omitted, caller abandons work | convergent-hole | Both expose an unresolved contract → Q-02. |
| 65 | UV-02 | Slow/blocked/Goexit work, no admission issued | convergent-hole | Both expose an unresolved contract → Q-02. |
| 66 | UV-03 | Concurrent Admit while budget exhausted | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 67 | UV-03 | Concurrent Admit, overlapping continuations | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 68 | UV-04 | Repeated identical callback | divergence | Same-generation repetitions count. → Q-03 |
| 69 | UV-04 | Overlapping contradictory callbacks | divergence | No refusal signal; current values apply in acquisition order. → Q-03 |
| 70 | UV-05 | Old work returns after clear | divergence | Counts are immune to old outcomes, but classification/refresh may still run. → Q-04 |
| 71 | UV-05 | Old work reports in new open interval | divergence | A report during due Open can advance to HalfOpen and notify. → Q-04 |
| 72 | UV-06 | Wrong boolean / fabricated continuation | divergence | Wrong but valid payload or closure may produce effects; public dispatch cannot fabricate a closure without acquisition. → Q-07 |
| 73 | UV-06 | nil callback after rejected admission | convergent | Semantically no continuation is issued; the caller can still call the nil value and panic, Q-08. |
| 74 | UV-07 | nil request / nil panic payload | divergence | An admitted nil request panics; nil panic is runtime-sensitive. → Q-08 |
| 75 | UV-08 | Omit/delay refreshing call; read Counts first | divergence | Counts and Name do not refresh. → Q-01 |
| 76 | UV-08 | Sample exactly at deadline | divergence | Strict Before excludes equality. → Q-01 |
| 77 | UV-09 | IsSuccessful returns wrong-but-valid | pass-B-blind-spot | Configured decisions are used. The boundary has no semantic validation of valid but mistaken values (Q-07). |
| 78 | UV-09 | IsSuccessful blocks/panics/Goexits/re-enters | convergent-hole | Both expose an unresolved contract → Q-06. |
| 79 | UV-10 | ReadyToTrip unintended but valid decision | pass-B-blind-spot | Configured decisions are used. The boundary has no semantic validation of valid but mistaken values (Q-07). |
| 80 | UV-10 | ReadyToTrip blocks/panics/Goexits/re-enters | convergent-hole | Both expose an unresolved contract → Q-06. |
| 81 | UV-11 | OnStateChange blocks/panics/misdelivers | convergent-hole | Both expose an unresolved contract → Q-06. |
| 82 | UV-12 | zero-value/nil receiver, copied breaker | divergence | No common rejection result; invalid forms can panic or return partial zero-value results. → Q-08 |
| 83 | UV-13 | Wrong valid instance / wrong-request payload | divergence | Wrong valid receiver actually selects the other instance. Request result validation is caller-owned. → Q-07 |
| 84 | UV-14 | Missing/delayed/duplicate construction | divergence | Missing construction produces no new object. Replacement cannot invalidate retained old callbacks. → Q-13 |
| 85 | UV-14 | Valid-but-unintended Settings | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 86 | P-01a | Admit then Report; HalfOpen at budget | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 87 | P-01b | Report then Admit; HalfOpen at budget | divergence | A final success before second admission closes, so admission succeeds. A failure instead changes the rejection error to ErrOpenState. → Q-15 |
| 88 | P-02a | Admit then prior Return | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 89 | P-02b | Prior Return then Admit | divergence | The resulting Open mode produces ErrOpenState; an unqualified handle understates the guarded rejection. → Q-15 |
| 90 | P-03a | Admit then prior Panic | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 91 | P-03b | Prior Panic then Admit | divergence | If pending panic opens the breaker first, the next admission rejects with ErrOpenState. → Q-16 |
| 92 | P-04a | State (due expiry) then delayed Report | divergence | vocabulary-drift: compound disposition maps to the transition for the state-changing operation, with the second operation handled conditionally. In this ordering old report is stale after observer refresh; HalfOpen starts below budget. → Q-04 |
| 93 | P-04b | Delayed Report then State | divergence | vocabulary-drift: compound disposition maps to the transition for the state-changing operation, with the second operation handled conditionally. The old report itself refreshes before accounting, so State only observes and stale contribution is skipped. → Q-04 |
| 94 | P-05a | Counts then Report | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 95 | P-05b | Report then Counts | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 96 | P-06a | State then returning Execute | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 97 | P-06b | Execute return then State | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 98 | P-07a | Counts then Return | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 99 | P-07b | Return then Counts | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 100 | P-08a | State then Panic | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 101 | P-08b | Panic then State | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 102 | P-09a | Counts then Panic | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 103 | P-09b | Panic then Counts | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 104 | P-10a | State (Open due) then Admit | divergence | vocabulary-drift: compound disposition maps to the transition for the state-changing operation, with the second operation handled conditionally. State alone leaves HalfOpen below budget; subsequent admission consumes the first slot. → Q-12 |
| 105 | P-10b | Admit then State (Open due) | divergence | Admission at due expiry can leave HalfOpen below budget when setting exceeds one. → Q-12 |
| 106 | P-11a | Counts then Admit (Closed/HalfOpen) | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 107 | P-11b | Admit then Counts | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 108 | P-12a | State then Counts (due expiry) | divergence | vocabulary-drift: compound disposition maps to the transition for the state-changing operation, with the second operation handled conditionally. Pair A stress case starts due Closed with pre-clear data; refresh is Closed to Closed. Even when Open, refresh alone does not fill budget. → Q-01 |
| 109 | P-12b | Counts then State (due expiry) | divergence | vocabulary-drift: compound disposition maps to the transition for the state-changing operation, with the second operation handled conditionally. Pair A stress case starts due Closed and Counts is definitely pre-clear; when Open its own transition still starts below budget. → Q-01 |
| 110 | P-13a | Name then Admit | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 111 | P-13b | Admit then Name | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 112 | P-14a | Name then Report | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 113 | P-14b | Report then Name | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 114 | P-15a | Name then Return | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 115 | P-15b | Return then Name | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 116 | P-16a | Name then Panic | convergent | Same observable behavior under the stated guard and ordinary callback return. |
| 117 | P-16b | Panic then Name | convergent | Same observable behavior under the stated guard and ordinary callback return. |
