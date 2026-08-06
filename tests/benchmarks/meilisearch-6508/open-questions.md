Q-D1
Question: Permit::drop(self) sends two release signals (explicit + implicit Drop).
Every explicit permit.drop().await produces two signals — one from Permit::drop(self)
at L52-55, one from Drop for Permit at L62-67. The scheduler processes each
independently: two decrements, two waiter grants per logical release. Combined
with the missing searches_running re-increment (issue #6577), actual running
searches can exceed the configured parallelism.
Current: explicit drop sends signal; Drop impl sends second signal via spawned
task. saturating_sub masks the counter effect but does not prevent double grant.
Expected: exactly one release signal per permit. Idempotent second path.
**Status:** OPEN

Q-D2
Question: Cancelled waiting callers never leave the scheduler admission population.
The queue stores oneshot::Sender<Permit> entries. A cancelled caller drops its
receiver; the scheduler retains the sender. No code path prunes dead entries
before they affect capacity enforcement, random eviction, permit selection,
or the searches_waiting metric. A live request can be evicted while a cancelled
waiter remains in the queue.
Current: queue.len() used for capacity (L166), eviction (L166), selection (L131),
and metric (L173) without filtering for liveness.
Expected: WaitingCallerCancelled must trigger QueueEntryCeasesToBeEligible,
removing the admission claim before it affects any scheduler decision.
**Status:** OPEN

Q-D3
Question: Failed permit delivery wastes the freed slot for an entire scheduler turn.
When a dead recipient is selected (L150: channel.send returns Err), the slot is
lost until the next release signal. No same-turn retry or alternate selection.
Current: let _ = channel.send(...) ignores failure. Dead waiter already swap_removed.
Expected: continue selection immediately after failed delivery, or prune dead
entries before selection.
**Status:** OPEN
