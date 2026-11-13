#!/usr/bin/env python3
"""Render the per-claim review and the draft-question dispositions (routing rules 1, 2, 6).
Verdicts are the calling agent's, recorded here; the draft JSON is read unchanged."""
import json, sys
from pathlib import Path
R = Path(__file__).resolve().parent
FILES = ["dv-README", "dv-README_ZH_CN", "dv-channel", "dv-pool", "dv-channel_rpc_test", "dv-example_main"]
# Claims kept despite a Jev 'unclear' (rule 2), or dropped/re-scoped; everything else: accepted after re-reading the cited line.
CLAIM_NOTES = {
 ("dv-channel","C1"): "kept: re-read channel.go:40-50, the field list holds; Jev judged the one-line fragment (the mutex line) against a statement about all fields",
 ("dv-channel","C18"): "kept: re-read channel.go:131-132, Lock then Debugf of both counters holds; the fragment names only the Lock",
 ("dv-channel","C20"): "accepted as a code path; re-read channel.go:137-139 and the whole file: no code closes a request channel, so the path is unreachable as-is (Q-01, Q-03)",
 ("dv-channel","C38"): "kept: re-read channel.go:225-232, all six assignments hold; the fragment names only the Lock",
 ("dv-channel","C11"): "accepted: re-read channel.go:95-99",
 ("dv-channel_rpc_test","C1"): "kept: re-read channel_rpc_test.go:14-18, the five fixture values hold; the fragment is line 14 only",
 ("dv-channel_rpc_test","C6"): "kept: re-read channel_rpc_test.go:262-272, holds",
 ("dv-channel_rpc_test","C8"): "kept: re-read channel_rpc_test.go:37-43, holds (Release is deferred before the error check: a nil pool would panic; test quality, outside scope)",
 ("dv-channel_rpc_test","C19"): "kept: re-read channel_rpc_test.go:166-189, holds; the test waits for nothing and asserts nothing",
 ("dv-channel_rpc_test","C21"): "kept: re-read channel_rpc_test.go:206-235, holds",
 ("dv-example_main","C13"): "dropped: exact duplicate of C12 (same line, same statement)",
 ("dv-example_main","C14"): "kept: re-read example/main.go:46-64, the order New, Get, Put, Len holds",
 ("dv-channel_rpc_test","C13"): "accepted; executed: the asserted error is never returned, the Get blocks (as-is-validation.md)",
}
ANS = "answered by the code; no open behaviour"
Q = {
 "dv-README": ["answered: construction creates InitialCap connections (channel.go:82-89); minimum-vs-initial reading → Q-15",
  "Q-02", "answered: ping runs only on Get's idle path (channel.go:123-124); handoff path → Q-14", "Q-17", "Q-18",
  "answered: validation rejects InitialCap > MaxIdle and MaxIdle > MaxCap (channel.go:59); undocumented → Q-20",
  "answered: Put closes when the idle channel is full (channel.go:196); undocumented → Q-20", "Q-16", "Q-06", "Q-06",
  "Q-03 (ErrMaxActiveConnReached) and Q-17 (factory errors)",
  "answered: the timestamp is set on Put (channel.go:190) and on creation (channel.go:88), consistent with 'maximum idle time' (README.md:13); folded into Q-13",
  "Q-13", "answered: a failed ping leads to Close (channel.go:125), which calls the close callback (channel.go:212)",
  "answered: Get pings and retries, creating a new connection when idle is exhausted (channel.go:123-126, 154); handoff → Q-14",
  "answered: Put does not ping (channel.go:167-198) → Q-14", "Q-20"],
 "dv-README_ZH_CN": ["answered: creates below MaxCap, blocks at MaxCap (channel.go:133-161); waiting semantics → Q-02",
  "answered: three checks with three messages (channel.go:59-67); documentation → Q-20",
  "answered: full → Close (channel.go:196); expiry is not checked on Put, the timestamp is renewed (channel.go:190); folded into Q-13",
  "answered: Get idle path only (channel.go:123); → Q-14", "Q-13", "Q-16", "Q-06 (checked-out connections); usability after Release answered: ErrClosed (channel.go:106)",
  "answered: MaxIdle <= MaxCap is enforced (channel.go:59)", "Q-20", "answered: Ping is optional (channel.go:78, 123); exported Ping with no ping configured → Q-22",
  "answered: yes, on Get below capacity (channel.go:154)", "answered: yes (channel.go:118 → channel.go:212)"],
 "dv-channel": ["Q-01", "Q-01 and Q-03", "answered: no — Put unlocks before calling Close (channel.go:175, 194) and Get calls Close outside the lock (channel.go:110-128, 144 after the unlock at 136); the callback-under-lock issue is Q-09",
  "answered: handed-off connections were counted when created (channel.go:159) and are not double counted; drift through foreign or duplicate Close → Q-10",
  "answered: no — the request channel has buffer 1 (channel.go:134) and receives exactly one send (channel.go:183)",
  "Q-02 (a waiter cannot abandon: no timeout, no cancellation)", "Q-02", "Q-22", "Q-06 (after Release the close callback is nil; counter state after Release is unobservable)",
  "Q-07", "Q-06", "Q-09", "Q-09 (lock discipline) and Q-08 (unlocked read of c.ping)", "Q-20",
  "answered: Put never sends nil (it wraps every connection, channel.go:184, 190), so nil means a closed channel",
  "Q-02 (unbounded waiter queue, Step-5 lint)", "answered: a handoff does not change openingConns; the cap is checked only before creation (channel.go:133) — drift cases → Q-10",
  "Q-16", "answered: waiters normally exist only at capacity; the cases where they exist below capacity → Q-04, Q-05",
  "Q-20 (MaxIdle < 0 is unreachable: InitialCap >= 0 and InitialCap <= MaxIdle, proven in check_guards.py G-01 implication)"],
 "dv-pool": ["answered by the channel.go extraction (this file holds only the interface and ErrClosed)"] * 11,
 "dv-channel_rpc_test": ["Q-03", "outside statechart scope: test message text (channel_rpc_test.go:122-123); recorded under 'outside scope' in summary.md",
  "answered: Release returns nothing (pool.go:18)", "Q-07 (Release racing with Get/Put); the missing assertion is test quality, outside scope",
  "outside scope (test quality); Close-only use is the E-CLOSE path", "Q-03", "Q-07", "Q-12 (connection never returned)",
  "answered: Put pools or hands off, Close closes and decrements (event catalogue)", "answered: only TestPool_Put builds its own Config, with the same values (channel_rpc_test.go:101)",
  "Q-07", "outside scope: RPC fixture"],
 "dv-example_main": ["outside scope: example code quality (example/main.go:52); factory errors → Q-17", "answered: InitialCap idle connections, Len counts idle (channel.go:247) → Q-16",
  "answered: yes, Len counts idle connections including the initial ones", "answered: rejected by validation (channel.go:59)",
  "outside scope: the example continues with a nil pool (example/main.go:47-52)", "Q-12", "Q-13", "answered: yes, unwrapped (channel.go:157); semantics → Q-17",
  "Q-02", "answered: no ordering is required between independent calls", "Q-16", "answered: yes (channel.go:241)"],
}
out = ["### Drafted claims (rule 1, rule 2)", "",
       "| Draft | Claim | Kind | Cited line | Citation | Jev | My review |", "|---|---|---|---|---|---|---|"]
qout = ["### Draft questions carried forward (rule 6)", "", "| Draft | # | Question (abridged) | Disposition |", "|---|---|---|---|"]
for f in FILES:
    d = json.loads((R / f"{f}.json").read_text())
    for cid, c in d["claims"].items():
        j = c["jev"] or {}
        note = CLAIM_NOTES.get((f, cid), "accepted: cited line re-read, claim holds")
        out.append(f"| {f} | {cid} | {c['kind']} | {d['source']}:{c['line']} | {c['citation_check']} | {j.get('choice')} ({j.get('confidence', 0):.2f}) | {note} |")
    qs = Q[f]
    assert len(qs) == len(d["questions"]), (f, len(qs), len(d["questions"]))
    for i, (q, disp) in enumerate(zip(d["questions"], qs), 1):
        qq = q.replace("|", "/")
        qq = qq if len(qq) < 140 else qq[:137] + "..."
        qout.append(f"| {f} | {i} | {qq} | {disp} |")
print("\n".join(out + [""] + qout))
