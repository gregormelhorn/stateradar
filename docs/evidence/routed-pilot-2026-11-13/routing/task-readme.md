StateRadar pilot, Step 1 (extraction + doctrine-line sweep) for component channelPool (a Go connection pool, file channel.go) of the silenceper/pool library. The source below is the library's README (requirements/docs).
Extract, each as one claim citing the exact line and a verbatim single-line fragment:
1. Every normative or behavioural sentence (doctrine lines): what the pool must/does do (idle timeout, ping, waiting when full, Put, Release, Len, capacity settings).
2. Every statement about lifecycle events: Get, Put, Release, Len, idle timeout expiry, ping failure, connection waiting.
3. Any ordering statement (what happens when one event happens after/before another) as kind "ordering".
Do not infer behaviour the text does not state. Put anything the text leaves unclear (e.g. what happens to waiters, what happens after Release) into "questions".
