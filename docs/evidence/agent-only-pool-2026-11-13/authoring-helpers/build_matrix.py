#!/usr/bin/env python3
"""Authoring helper for disposition-matrix.md (cell text lives here so that
repeated citations are typed once). Output is the matrix body; the prose
around it is in matrix_head.md / matrix_tail.md."""
import sys
from pathlib import Path

S = ["Open_Idle", "Open_IdleFull", "Open_Empty_BelowCap", "Open_Empty_AtCap",
     "Open_Waiting", "Open_Waiting_BelowCap", "Open_Waiting_IdleStranded",
     "Open_Creating", "Released"]
OPEN_NC = S[:7]          # open, not creating
WAITING = ["Open_Waiting", "Open_Waiting_BelowCap", "Open_Waiting_IdleStranded"]

GET_IDLE = 'channel.go:129 ("return wrapConn.conn, nil")'
GET_CREATE = 'channel.go:154 ("conn, err := c.factory()")'
GET_WAIT = 'channel.go:135 ("c.connReqs = append(c.connReqs, req)")'
GET_BLOCK = 'channel.go:137 ("ret, ok := <-req")'
GET_CLOSED = 'channel.go:106 ("return nil, ErrClosed")'
MU_GET = 'channel.go:131 ("c.mu.Lock()")'
PUT_ENQ = 'channel.go:190 ("case c.conns <- &idleConn{conn: conn, t: time.Now()}:")'
PUT_FULL = 'channel.go:196 ("return c.Close(conn)")'
PUT_HAND = 'channel.go:183 ("req <- connReq{")'
PUT_REL = 'channel.go:176 ("return c.Close(conn)")'
MU_PUT = 'channel.go:172 ("c.mu.Lock()")'
CLOSE_DEC = 'channel.go:211 ("c.openingConns--")'
CLOSE_REL = 'channel.go:208 ("if c.close == nil {")'
MU_CLOSE = 'channel.go:206 ("c.mu.Lock()")'
REL = 'channel.go:238 ("close(conns)")'
REL_AGAIN = 'channel.go:234 ("if conns == nil {")'
MU_REL = 'channel.go:225 ("c.mu.Lock()")'
LEN = 'channel.go:247 ("return len(c.getConns())")'
MU_LEN = 'channel.go:96 ("c.mu.Lock()")'
PING = 'channel.go:220 ("return c.ping(conn)")'
NILREJ = 'channel.go:169 ("connection is nil. rejecting")'
FAC_OK = 'channel.go:159 ("c.openingConns++")'
FAC_ERR = 'channel.go:157 ("return nil, err")'
CLOSEFN = 'channel.go:212 ("return c.close(conn)")'
REL_CLOSEFN = 'channel.go:241 ("closeFun(wrapConn.conn)")'
IDLE_CHECK = 'channel.go:116 ("if wrapConn.t.Add(timeout).Before(time.Now()) {")'
IDLE_DOC = 'channel.go:32 ("IdleTimeout time.Duration")'
UNLOCK_REL = 'channel.go:232 ("c.mu.Unlock()")'

FAC_ONLY = (f"ignore (documented) — Factory runs only inside a creating Get and returns "
            f"synchronously there {GET_CREATE}; no Factory result exists in this state")


def col(default=None, **per):
    out = {}
    for s in S:
        out[s] = per.get(s, default)
        if out[s] is None:
            raise SystemExit(f"missing cell {s}")
    return out


C = {}

C["GET"] = col(
    Open_Idle=f"transition → Open_Empty_BelowCap — dequeues the oldest idle conn and returns it {GET_IDLE}; guard G-03 closes expired or Ping-failed conns (o−1) and retries; target per GN-1: i = 1 ∧ o < X → Open_Empty_BelowCap, i = 1 ∧ o ≥ X → Open_Empty_AtCap, i ≥ 2 stays Open_Idle",
    Open_IdleFull=f"transition → Open_Idle — dequeues the oldest idle conn {GET_IDLE}; guard G-03 (GN-1)",
    Open_Empty_BelowCap=f"transition → Open_Creating — no idle conn and o < X: calls Factory under the mutex {GET_CREATE} (G-02)",
    Open_Empty_AtCap=f"transition → Open_Waiting — o ≥ X: appends a waiter and blocks with no timeout {GET_WAIT} (G-02; → Q-01, Q-02)",
    Open_Waiting=f"handle — appended as the newest waiter (FIFO), blocks with no timeout {GET_WAIT} (→ Q-02)",
    Open_Waiting_BelowCap=f"transition → Open_Creating — o < X: creates a conn although older waiters still block (barging) {GET_CREATE} (→ Q-03)",
    Open_Waiting_IdleStranded=f"transition → Open_Waiting — takes the stranded idle conn ahead of the waiters {GET_IDLE} (→ Q-04)",
    Open_Creating=f"defer (queued) — the Get blocks on the mutex held by the creating Get before it looks at the idle store {MU_LEN} (getConns, called first by Get) (→ Q-19)",
    Released=f"reject — \"pool is closed\" error {GET_CLOSED} (DOC-13)",
)

C["PUT"] = col(
    Open_Idle=f"transition → Open_IdleFull — enqueues the conn with a fresh timestamp {PUT_ENQ}; target when i+1 = M, otherwise stays Open_Idle (G-04)",
    Open_IdleFull=f"handle — idle store full: closes the conn through Close, o−1 {PUT_FULL} (G-04)",
    Open_Empty_BelowCap=f"transition → Open_Idle — enqueues {PUT_ENQ}; with MaxIdle = 0 the conn is closed instead (G-04)",
    Open_Empty_AtCap=f"transition → Open_Idle — enqueues {PUT_ENQ}; with MaxIdle = 0 the conn is closed instead (G-04)",
    Open_Waiting=f"transition → Open_Empty_AtCap — hands the conn to the oldest waiter with a fresh timestamp {PUT_HAND}; target when the last waiter is served, otherwise stays Open_Waiting (G-04)",
    Open_Waiting_BelowCap=f"transition → Open_Empty_BelowCap — hands the conn to the oldest waiter {PUT_HAND}; target when the last waiter is served, otherwise stays",
    Open_Waiting_IdleStranded=f"transition → Open_Idle — hands the conn to the oldest waiter; the stranded idle conn stays {PUT_HAND}; target when the last waiter is served, otherwise stays (→ Q-04)",
    Open_Creating=f"defer (queued) — blocks on the mutex until Factory returns {MU_PUT} (→ Q-19)",
    Released=f"ignore (accidental) → Q-06 — Put calls Close, which returns nil without closing because Release cleared the Close callback {PUT_REL}; the conn stays open",
)

_close_open = f"handle — o−1, then the Close callback runs under the mutex and its error is returned {CLOSE_DEC}"
C["CLOSE"] = col(
    Open_Idle=_close_open, Open_IdleFull=_close_open, Open_Empty_BelowCap=_close_open,
    Open_Empty_AtCap=f"transition → Open_Empty_BelowCap — o−1 frees capacity {CLOSE_DEC}",
    Open_Waiting=f"transition → Open_Waiting_BelowCap — o−1 and the Close callback; no waiter is woken although capacity is now free {CLOSE_DEC} (→ Q-03)",
    Open_Waiting_BelowCap=f"handle — o−1; the waiters stay blocked {CLOSE_DEC} (→ Q-03)",
    Open_Waiting_IdleStranded=f"handle — o−1; the waiters stay blocked {CLOSE_DEC} (→ Q-04)",
    Open_Creating=f"defer (queued) — blocks on the mutex until Factory returns {MU_CLOSE} (→ Q-19)",
    Released=f"ignore (accidental) → Q-06 — returns nil without calling any close function and without o−1 {CLOSE_REL}",
)

_rel = f"transition → Released — clears the pool and closes every idle conn with the captured Close callback {REL}; checked-out conns are not closed (→ Q-06)"
_relw = f"transition → Released — closes the idle conns {REL}; the waiting Gets are neither served nor signalled and block forever (→ Q-05)"
C["RELEASE"] = col(
    Open_Idle=_rel, Open_IdleFull=_rel, Open_Empty_BelowCap=_rel, Open_Empty_AtCap=_rel,
    Open_Waiting=_relw, Open_Waiting_BelowCap=_relw, Open_Waiting_IdleStranded=_relw,
    Open_Creating=f"defer (queued) — blocks on the mutex until Factory returns {MU_REL}; the creating Get then returns its new conn from a pool that is being released (→ Q-06)",
    Released=f"ignore (documented) — explicit early return when already released {REL_AGAIN} (observed-in-code: deliberate nil check; no requirement states it → Q-20)",
)

C["LEN"] = col(
    default=f"handle — returns the idle count only; checked-out conns are not counted {LEN} (DOC-7 → Q-15)",
    Open_Creating=f"defer (queued) — reads the idle store under the mutex {MU_LEN} (→ Q-19)",
    Released=f"handle — returns 0, the length of the cleared idle store {LEN}",
)

C["PING"] = col(
    default=f"handle — calls the configured Ping without the mutex {PING}; with no Ping configured this is a nil-function call that panics (→ Q-11)",
    Released=f"handle — calls the Ping reference that Release cleared {PING}: always a nil-function call that panics (→ Q-11)",
)

C["FACTORY_OK"] = col(
    default=FAC_ONLY,
    Open_Creating=f"transition → Open_Empty_AtCap — o+1, unlock, the conn goes to the creating caller {FAC_OK}; target when o+1 ≥ X; other targets per GN-6 (Open_Empty_BelowCap when o+1 < X, Open_Waiting_BelowCap with stranded waiters, Open_Idle when a racing Put left an idle conn)",
)

C["CLOSEFN_OK"] = col(
    default=f"handle — the nil result is returned to the Close or Put caller {CLOSEFN}; o was already decremented before the call",
    Open_Creating=f"defer (queued) — no Close-callback call can start while Factory holds the mutex: Close waits {MU_CLOSE}",
    Released=f"handle — Release's drain calls the captured callback for each idle conn and ignores the result {REL_CLOSEFN}",
)

_idle_hole = f"ignore (accidental) → Q-12 — no timer: the expired conn stays open and counted until a Get dequeues it {IDLE_CHECK} or Release closes it"
_idle_none = f"ignore (documented) — no idle conn exists; the timeout applies to idle conns only {IDLE_DOC} (Config comment: maximum idle time)"
C["IDLE_TIMEOUT"] = col(
    Open_Idle=_idle_hole, Open_IdleFull=_idle_hole, Open_Waiting_IdleStranded=_idle_hole,
    Open_Empty_BelowCap=_idle_none, Open_Empty_AtCap=_idle_none, Open_Waiting=_idle_none,
    Open_Waiting_BelowCap=_idle_none,
    Open_Creating=f"ignore (accidental) → Q-12 — as in Open_Idle when an idle conn exists: no timer {IDLE_CHECK}",
    Released=f"ignore (documented) — Release already closed every idle conn {REL_CLOSEFN}",
)

C["UV-01"] = col(
    default=f"ignore (accidental) → Q-16 — the pool keeps no record of checked-out conns; the lost conn's share of o is never given back {FAC_OK}; at MaxCap every later Get waits forever",
    Released=f"ignore (accidental) → Q-06 — Release does not close checked-out conns {REL}",
)

_late_wait = f"ignore (accidental) → Q-02 — the waiting Gets block for the whole delay; no wait timeout exists (the waitTimeOut field is never used) {GET_BLOCK}"
C["UV-02"] = col(
    Open_Idle=f"handle — a late Put is an ordinary Put; no Get is waiting {PUT_ENQ}",
    Open_IdleFull=f"handle — an ordinary Put into a full idle store: closed, o−1 {PUT_FULL}",
    Open_Empty_BelowCap=f"transition → Open_Idle — an ordinary Put {PUT_ENQ}",
    Open_Empty_AtCap=f"transition → Open_Idle — an ordinary Put {PUT_ENQ}; Gets that arrived before it are waiting (→ Q-02)",
    Open_Waiting=_late_wait, Open_Waiting_BelowCap=_late_wait, Open_Waiting_IdleStranded=_late_wait,
    Open_Creating=f"defer (queued) — blocks on the mutex {MU_PUT}",
    Released=f"ignore (accidental) → Q-06 — as PUT after Release: not closed {PUT_REL}",
)

C["UV-03"] = col(
    Open_Idle=f"handle — the conn is enqueued a second time; two Gets can receive the same conn (no identity check) {PUT_ENQ} (→ Q-09)",
    Open_IdleFull=f"handle — closes the conn and decrements o although the first copy is still idle or in use {PUT_FULL} (→ Q-09)",
    Open_Empty_BelowCap=f"transition → Open_Idle — enqueued again {PUT_ENQ} (→ Q-09)",
    Open_Empty_AtCap=f"transition → Open_Idle — enqueued again {PUT_ENQ} (→ Q-09)",
    Open_Waiting=f"handle — handed to a waiter while the first copy is idle or in use {PUT_HAND} (→ Q-09)",
    Open_Waiting_BelowCap=f"handle — handed to a waiter while the first copy is in use {PUT_HAND} (→ Q-09)",
    Open_Waiting_IdleStranded=f"handle — handed to a waiter while the first copy may sit in the idle store {PUT_HAND} (→ Q-09)",
    Open_Creating=f"defer (queued) — blocks on the mutex {MU_PUT}",
    Released=f"ignore (accidental) → Q-06 — as PUT after Release {PUT_REL}",
)

_dup = f"handle — o−1 again and the Close callback runs again; o now undercounts the live conns, so the pool can later exceed MaxCap {CLOSE_DEC} (→ Q-09)"
C["UV-04"] = col(
    Open_Idle=_dup, Open_IdleFull=_dup, Open_Empty_BelowCap=_dup,
    Open_Empty_AtCap=f"transition → Open_Empty_BelowCap — o−1 again {CLOSE_DEC} (→ Q-09)",
    Open_Waiting=f"transition → Open_Waiting_BelowCap — o−1 again; no waiter woken {CLOSE_DEC} (→ Q-09, Q-03)",
    Open_Waiting_BelowCap=_dup, Open_Waiting_IdleStranded=_dup,
    Open_Creating=f"defer (queued) — blocks on the mutex {MU_CLOSE}",
    Released=f"ignore (accidental) → Q-06 — returns nil, nothing closed {CLOSE_REL}",
)

_stale_idle = f"handle — closes a conn that is still in the idle store and decrements o; a later Get can receive the closed conn, and discarding it decrements o a second time {CLOSE_DEC} (→ Q-09)"
_stale_out = f"handle — closes a conn that another caller now holds, o−1 {CLOSE_DEC} (→ Q-09)"
C["UV-05"] = col(
    Open_Idle=_stale_idle, Open_IdleFull=_stale_idle, Open_Waiting_IdleStranded=_stale_idle,
    Open_Empty_BelowCap=_stale_out,
    Open_Empty_AtCap=f"transition → Open_Empty_BelowCap — closes a conn another caller holds, o−1 {CLOSE_DEC} (→ Q-09)",
    Open_Waiting=f"transition → Open_Waiting_BelowCap — closes the conn a waiter received, o−1, no waiter woken {CLOSE_DEC} (→ Q-09)",
    Open_Waiting_BelowCap=_stale_out,
    Open_Creating=f"defer (queued) — blocks on the mutex {MU_CLOSE}",
    Released=f"ignore (accidental) → Q-06 — returns nil, nothing closed {CLOSE_REL}",
)

_race = f"handle — the mutex serializes the two calls; Put first then Close behaves as UV-05, Close first then Put stores or hands on a closed conn {MU_PUT} (→ Q-09)"
C["UV-06"] = col(
    default=_race,
    Open_Creating=f"defer (queued) — both block on the mutex {MU_PUT}",
    Released=f"ignore (accidental) → Q-06 — both return nil, nothing closed {PUT_REL}",
)

C["UV-07"] = col(
    Open_Idle=f"handle — stored like an own conn; o is not incremented, so a later discard of it decrements o for a conn never counted {PUT_ENQ} (→ Q-09)",
    Open_IdleFull=f"handle — closes the foreign conn and decrements o {PUT_FULL} (→ Q-09)",
    Open_Empty_BelowCap=f"transition → Open_Idle — stored like an own conn {PUT_ENQ} (→ Q-09)",
    Open_Empty_AtCap=f"transition → Open_Idle — stored like an own conn {PUT_ENQ} (→ Q-09)",
    Open_Waiting=f"handle — handed to a waiter {PUT_HAND} (→ Q-09)",
    Open_Waiting_BelowCap=f"handle — handed to a waiter {PUT_HAND} (→ Q-09)",
    Open_Waiting_IdleStranded=f"handle — handed to a waiter {PUT_HAND} (→ Q-09)",
    Open_Creating=f"defer (queued) — blocks on the mutex {MU_PUT}",
    Released=f"ignore (accidental) → Q-06 — returns nil, not closed {PUT_REL}",
)

_foreign = f"handle — o−1 for a conn that was never counted, and the Close callback runs {CLOSE_DEC} (→ Q-09)"
C["UV-08"] = col(
    Open_Idle=_foreign, Open_IdleFull=_foreign, Open_Empty_BelowCap=_foreign,
    Open_Empty_AtCap=f"transition → Open_Empty_BelowCap — o−1 for a conn never counted {CLOSE_DEC} (→ Q-09)",
    Open_Waiting=f"transition → Open_Waiting_BelowCap — o−1 for a conn never counted; no waiter woken {CLOSE_DEC} (→ Q-09)",
    Open_Waiting_BelowCap=_foreign, Open_Waiting_IdleStranded=_foreign,
    Open_Creating=f"defer (queued) — blocks on the mutex {MU_CLOSE}",
    Released=f"ignore (accidental) → Q-06 — returns nil, nothing closed {CLOSE_REL}",
)

C["UV-09"] = col(default=f"reject — error \"connection is nil. rejecting\", checked before the mutex {NILREJ} (Close and Ping check the same before any other step)")

C["UV-10"] = col(
    Open_Idle=f"handle — stored without validation {PUT_ENQ}; a later Get discards it only if Ping is configured (G-03)",
    Open_IdleFull=f"handle — idle store full: closed, o−1 {PUT_FULL}",
    Open_Empty_BelowCap=f"transition → Open_Idle — stored without validation {PUT_ENQ}",
    Open_Empty_AtCap=f"transition → Open_Idle — stored without validation {PUT_ENQ}",
    Open_Waiting=f"handle — handed straight to a waiter, which does not run Ping {PUT_HAND} (→ Q-13)",
    Open_Waiting_BelowCap=f"handle — handed straight to a waiter, which does not run Ping {PUT_HAND} (→ Q-13)",
    Open_Waiting_IdleStranded=f"handle — handed straight to a waiter, which does not run Ping {PUT_HAND} (→ Q-13)",
    Open_Creating=f"defer (queued) — blocks on the mutex {MU_PUT}",
    Released=f"ignore (accidental) → Q-06 — returns nil, not closed {PUT_REL}",
)

C["UV-11"] = col(
    default=FAC_ONLY,
    Open_Creating=f"transition → Open_Empty_BelowCap — unlocks and returns the error to the creating caller, o unchanged, no retry {FAC_ERR} (GN-6 for stranded waiters)",
)
C["UV-12"] = col(
    default=FAC_ONLY,
    Open_Creating=f"ignore (accidental) → Q-08 — no timeout; the mutex stays held, so Put, Close, Release, Len and every Get (all lock in getConns first) block as long as Factory runs {GET_CREATE}",
)
C["UV-13"] = col(
    default=FAC_ONLY,
    Open_Creating=f"ignore (accidental) → Q-07 — returns (nil, err); the conn Factory returned is dropped without the Close callback {FAC_ERR}",
)
C["UV-14"] = col(
    default=FAC_ONLY,
    Open_Creating=f"ignore (accidental) → Q-07 — no nil check: o+1 and (nil, nil) goes to the caller, who cannot Put or Close nil, so the slot is lost {FAC_OK}",
)
C["UV-15"] = col(
    default=f"handle — o is already decremented; the error reaches Close and Put callers but is discarded when Get discards an expired or Ping-failed conn {CLOSEFN} (→ Q-17)",
    Open_Creating=f"defer (queued) — no Close-callback call can start while Factory holds the mutex {MU_CLOSE}",
    Released=f"handle — Release ignores the error for each idle conn {REL_CLOSEFN} (→ Q-17)",
)
C["UV-16"] = col(
    default=f"ignore (accidental) → Q-08 — the callback runs under the mutex: Put, Close, Release, Len and every Get block until it returns {CLOSEFN}",
    Open_Creating=f"defer (queued) — no Close-callback call can start while Factory holds the mutex {MU_CLOSE}",
    Released=f"ignore (documented) — Release runs the callback after unlocking, so only the Release caller waits {UNLOCK_REL}",
)
C["UV-17"] = col(
    default=FAC_ONLY,
    Open_Creating=f"defer (queued) — the re-entrant call waits for the mutex its own Factory holds: deadlock (every locking method, Get included via getConns) {MU_GET} (→ Q-08)",
)
C["UV-18"] = col(
    default=f"defer (queued) — reached via Close, Put-when-full or Get's discard path, the callback runs under the mutex; a re-entrant locking call waits for it forever: deadlock {MU_CLOSE} (→ Q-08)",
    Open_Creating=f"defer (queued) — the callback cannot start while Factory holds the mutex {MU_CLOSE}",
    Released=f"handle — from Release's drain the callback runs unlocked; re-entrant calls see the released pool {UNLOCK_REL}",
)

NAMES = {
    "UV-01": "PUT_LOST", "UV-02": "PUT_DELAYED", "UV-03": "PUT_DUP", "UV-04": "CLOSE_DUP",
    "UV-05": "CLOSE_STALE", "UV-06": "PUT_CLOSE_RACE", "UV-07": "PUT_FOREIGN",
    "UV-08": "CLOSE_FOREIGN", "UV-09": "NIL_CONN", "UV-10": "PUT_BROKEN",
    "UV-11": "FACTORY_ERR", "UV-12": "FACTORY_HANG", "UV-13": "FACTORY_CONN_AND_ERR",
    "UV-14": "FACTORY_NIL_CONN", "UV-15": "CLOSEFN_ERR", "UV-16": "CLOSEFN_HANG",
    "UV-17": "FACTORY_REENTRY", "UV-18": "CLOSEFN_REENTRY",
}
TABLES = [
    ("Base events", ["GET", "PUT", "CLOSE", "RELEASE", "LEN", "PING", "FACTORY_OK", "CLOSEFN_OK", "IDLE_TIMEOUT"]),
    ("Undesired variants, caller", [f"UV-0{i}" for i in range(1, 10)]),
    ("Undesired variants, caller value + seams", ["UV-10"] + [f"UV-{i}" for i in range(11, 19)]),
]

out = []
for title, evs in TABLES:
    out.append(f"### Sub-table: {title}\n")
    out.append("| State | " + " | ".join(f"{e} {NAMES[e]}" if e in NAMES else e for e in evs) + " |")
    out.append("|---" * (len(evs) + 1) + "|")
    for s in S:
        out.append(f"| **{s}** | " + " | ".join(C[e][s] for e in evs) + " |")
    out.append("")
Path(sys.argv[1]).write_text("\n".join(out), encoding="utf-8")
print(f"{len(S)} states x {sum(len(e) for _, e in TABLES)} events written")
