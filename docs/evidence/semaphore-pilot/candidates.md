# Candidate scout: golang.org/x/sync

Scope: pinned v0.17.0 / 04914c200cb38d4ea960ee6a4c314a028c632991.
Read-only scout, three candidates inspected; other packages and generated files
excluded. Citations below are relative to this upstream checkout. No historical
issue or expected-finding data was supplied to the pilot.

## Ranked shortlist

Scores are proposed, on a 0–3 scale in the order temporal richness / hole
likelihood / pain evidence / seam quality / boundedness. State estimates are
preliminary abstractions, not pilot conclusions.

1. **Weighted semaphore** — `semaphore/semaphore.go`. Observed in code:
   capacity/current weight and waiter list (27–32), context cancellation (39–49,
   75–104), queued acquisition (69–72), nonblocking admission (111–119), release
   and waiter notification (122–160). Estimated 4–6 aggregate states, 4 event
   families, no owned timer/retry, three cancellation observation branches.
   Proposed seam: public Acquire/TryAcquire/Release results, held weight and
   pending/completed requests; synchronization hooks may schedule races but
   assertions use public effects. Risks to examine neutrally: competing calls,
   context lifetime, input-domain and queue contracts. Scores **3/2/0/2/3**.
   Config: component `semaphore/semaphore.go`, API `Weighted`, tests
   `semaphore/semaphore_test.go` and `semaphore/semaphore_example_test.go`,
   requirements README plus public contract comments, output
   `domain-analysis/weightedSemaphore`.
2. **Singleflight per-key call** — `singleflight/singleflight.go`. Observed in
   code: inflight record (55–69), lazily initialized map (71–76), duplicate wait
   (91–106), channel delivery entry (117–130), Forget (207–214). Estimated four
   per-key phases, five event families, no timer or cancellation API.
   Proposed seam: callback invocation counts, return values/channel delivery and
   key-specific requests. Panic/Goexit handling expands the boundary. Scores
   **3/2/0/2/2**. Config: component `singleflight/singleflight.go`, API Group
   Do/DoChan/Forget, tests `singleflight/singleflight_test.go`, requirements public
   comments plus README, output `domain-analysis/singleflight`.
3. **Errgroup** — `errgroup/errgroup.go`. Observed in code: context and optional
   semaphore (25–34), WithContext/Wait cancellation (43–60), bounded launch
   (63–100), TryGo (104–131), limit mutation (134–152). Estimated five combined
   phases, six event families, no owned timer/retry, context cancellation on
   first error/Wait. Proposed seam: task completion/error, admission and derived
   context results. Caller/task lifetimes make the first boundary less compact.
   Scores **3/2/0/2/2**. Config: component `errgroup/errgroup.go`, API Group and
   WithContext, tests `errgroup/errgroup_test.go`, requirements public comments
   plus README, output `domain-analysis/errgroup`.

## Recommended first pilot

Choose Weighted: one small implementation with public outcome probes and
meaningful temporal behavior. This is a new local evaluation component, not a
claim that public upstream code was absent from model training. The goal is a
complete method cycle, not a new model-cost tournament. User decisions apply
to this evaluation's contract; they are not upstream maintainer approval.

## Looks stateful, not worth it

README links and pure formatting/error-string helpers do not own temporal
behavior. They are supporting context rather than candidate boundaries.

## Coverage and history limits

`rg -n 'mu.Lock|waiters|ctx.Done|Forget|SetLimit|panic\('` over the three source
files produced the signals cited above. `git log --oneline --since=2025-11-14
-- semaphore` returned no entries in the shallow pinned checkout. This is not
proof of low churn: history is unavailable, so all pain scores are unknown/0.
No other packages or older/deleted analyses were inspected for pilot findings.
