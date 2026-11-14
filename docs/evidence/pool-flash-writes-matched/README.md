# Matched Flash-writes pilot on silenceper/pool

Both sessions used Pool `6084537`, pack `ba14ef0`, English prompt v1.25,
GPT-6.1 Sol medium via ChatGPT login, selective output, Jev 1.14.0 and
Flash for a separate blind Part B. The routed session ran first. The
recorded settings differ only in the drafting strategy.

| Measure | Standard routing | Flash-writes |
| --- | ---: | ---: |
| Codex input + output tokens | 7,100,530 | 8,349,888 (+17.6%) |
| Codex input excluding cache hits | 165,470 | 183,587 (+10.9%) |
| Codex output tokens | 39,956 | 41,117 |
| Runtime | 18:46 | 20:48 |
| Tool calls / retained-log reads | 149 / 9 | 165 / 7 |
| Flash and Jev ledger | $0.018308 | $0.040228 |
| States / events / cells | 6 / 25 / 150 | 4 / 17 / 68 |
| Pair orderings / open questions | 28 / 20 | 30 / 21 |
| Runner acceptance checks | 5/5 | 5/5 |

Both pilots ran behavior probes for the primary Release/waiter finding
and both second-Get cases. Both reported the callback-field data race,
late cleanup and callback effects around Release, lazy idle expiry,
FIFO handoff and caller abandonment.

The reference names the P-04a sequence in T-04 and Q-20. Get misses
the idle channel, Put buffers a returned connection before the capacity
lock, then Get queues with a connection available to a newcomer.
Flash-writes describes priority bypass and both normal Get/Put orders
(P-12a/b), but its delivered traces and questions omit that sequence.
The separately executed [P-04a probe](../pool-p04a/README.md) confirms it.

Flash drafted 68 matrix cells. The steering agent changed 50, including
26 of the 39 Jev-supported cells. It changed 4 of 8 drafted test bodies
and added the race-detector probe. The result does not meet the goal of
lower steering-token usage with preserved findings in this pair.

The original Pool suite timed out in TestPool_Get in both sessions.
Both ran passing focused probes and surfaced a targeted race-detector
failure. The acceptance counts refer to the five pack gates. The Codex
counters are token usage under the ChatGPT login. They do not represent
account charges, and one ordered pair does not estimate run variance.

[Protocol](protocol.md) and [measured counters](measurements.json).
Raw local runs are in `/tmp/stateradar-matched-routing.UtInwG`.
