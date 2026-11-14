# Matched Pool routing comparison

Use the same pack tree and Pool 6084537 in fresh isolated checkouts. Use
GPT-6.1 Sol medium via ChatGPT login, English pilot v1.25, Jev 1.14.0,
Flash for blind Part B, one ledger per session, selective output and a
40-minute limit per arm. Run routed first, then flash-writes. The only
brief change is routing variant. Neither arm sees previous findings or
the separate P-04a fixture.

Check all five acceptance gates externally. Record the primary
Release-and-waiter finding and executed probe, the Get-miss/Put/Get-queues
interleaving (match semantics, not local pair IDs), and both repeated Get
cases. Also compare the Ping/Release race and idle expiry, callback
failure, and waiter handoff/cancellation findings. Report differences and
scope of findings separately from aggregate state and cell counts. Check
written questions remain open.

Measure duration, Codex input/output including cache counters, retained-log
read attempts and Flash/Jev settled/reserved amounts separately. The old
25% dollar criterion needs comparable steering-model pricing. ChatGPT
login counters by themselves give token usage, not billed dollars.
