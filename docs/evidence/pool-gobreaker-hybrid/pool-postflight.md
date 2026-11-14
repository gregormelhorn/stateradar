# Pool postflight

The pilot stopped when the Codex service flagged content as a possible
cybersecurity risk. Its final summary and turn usage were unavailable.
The artifact checks were run independently against the files already
written. All seven exited zero.

The original 8192-token Flash response was incomplete. The steering
agent recovered complete objects from the retained raw response, including
W-06. That object itself gave the complete at-capacity interleaving.
Its line ranges and multi-line strings failed the citation validator.
Codex reread the implementation, corrected the citations, and wrote
P-01a/Q-01 and a probe. The runner rendered 104 matrix cells; reachability
found all four states, including GetWaitingWithIdle via the cited pair.

TestPilotMissedReceive passed twice in the pilot's one run (two cases).
The same two cases passed five repeats under the race detector in a
separate postflight. The independent historical P-04a fixture passed 25
repeats with the detector as well. Running all the pilot probes under
the detector produced a separate race between test scheduling-hook
accesses. That log is not credited as the reference Ping/Release race.
The pilot traced the field race and its deterministic timing-hook
probe demonstrated a nil callback panic for the selected ordering.

The first bounded retry on the same Pool source returned eight proposals
with mechanically valid citations. It missed the exact at-capacity
observation/Put/late waiter schedule. Several rows still needed semantic
review, notably the suggestion that a Put can serve a waiter after Release.
