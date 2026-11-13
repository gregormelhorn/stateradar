#!/usr/bin/env python3
"""Render disposition-matrix.md from the cell table below (agent-authored helper, kept in the evidence)."""
import sys
S = ["Open_IdleAvailable", "Open_IdleFull", "Open_Empty", "Open_AtCapacity", "Open_AtCapacity_Waiting", "Open_Waiting_Stranded", "Released"]
c = lambda line, frag: f'channel.go:{line} ("{frag}")'
c106=c(106,"return nil, ErrClosed"); c110=c(110,"case wrapConn := <-conns:"); c116=c(116,"wrapConn.t.Add(timeout).Before(time.Now())")
c124=c(124,"if err := c.Ping(wrapConn.conn); err != nil {"); c129=c(129,"return wrapConn.conn, nil"); c133=c(133,"if c.openingConns >= c.maxActive {")
c135=c(135,"c.connReqs = append(c.connReqs, req)"); c137=c(137,"ret, ok := <-req"); c154=c(154,"conn, err := c.factory()")
c157=c(157,"return nil, err"); c159=c(159,"c.openingConns++"); c176=c(176,"return c.Close(conn)"); c183=c(183,"req <- connReq{")
c190=c(190,"case c.conns <- &idleConn{conn: conn, t: time.Now()}:"); c196=c(196,"return c.Close(conn)"); c208=c(208,"if c.close == nil {")
c211=c(211,"c.openingConns--"); c212=c(212,"return c.close(conn)"); c227=c(227,"c.conns = nil"); c228=c(228,"c.factory = nil")
c231=c(231,"c.close = nil"); c234=c(234,"if conns == nil {"); c241=c(241,"closeFun(wrapConn.conn)"); c247=c(247,"return len(c.getConns())")
OPEN = S[:6]
M = {s: {} for s in S}
def put(ev, states, text):
    for s in states: M[s][ev] = text
I,F,E,A,W,X,R = S
# ---- E-GET
put("E-GET",[I],f"transition → Open_Empty {c129} when the last idle connection is taken below the cap; otherwise stays (idle remains) or → Open_AtCapacity (at the cap); expired (G-02) or ping-failed (G-03) connections are discarded via Close first")
put("E-GET",[F],f"transition → Open_IdleAvailable {c110} (MaxIdle ≥ 2; G-02/G-03 discards first)")
put("E-GET",[E],f"transition → Open_AtCapacity {c154} when this creation reaches MaxCap; otherwise stays; Factory runs while holding mu, openingConns++ (channel.go:159) (G-04)")
put("E-GET",[A],f"transition → Open_AtCapacity_Waiting {c135}; blocks with no timeout or cancellation (channel.go:137) → Q-02, Q-03")
put("E-GET",[W],f"handle — queues one more waiter {c135} (FIFO, unbounded) → Q-02")
put("E-GET",[X],f"handle — the new Get takes an idle connection {c110} or creates one below the cap (channel.go:154) ahead of the queued waiters → Q-04")
put("E-GET",[R],f"reject — ErrClosed {c106}")
# ---- E-PUT
put("E-PUT",[I],f"transition → Open_IdleFull {c190} when idle reaches MaxIdle; otherwise stays; enqueued with a fresh timestamp (G-06)")
put("E-PUT",[F],f"handle — idle channel full: Close after unlock {c196} (openingConns--, Close callback)")
put("E-PUT",[E],f"transition → Open_IdleAvailable {c190} (MaxIdle ≥ 1; MaxIdle == 0 closes it)")
put("E-PUT",[A],f"transition → Open_IdleAvailable {c190} (openingConns unchanged)")
put("E-PUT",[W],f"transition → Open_AtCapacity {c183} when the last waiter is served; otherwise stays; the connection goes to the oldest waiter with a fresh timestamp, no Ping (G-06)")
put("E-PUT",[X],f"transition → Open_Empty {c183} when the last waiter is served and no idle connection remains; with idle connections → Open_IdleAvailable; otherwise stays (G-06)")
put("E-PUT",[R],f"ignore (accidental) → Q-06 — Put calls Close {c176}, which returns nil because Release cleared the close function (channel.go:208); the connection is neither pooled nor closed")
# ---- E-CLOSE
put("E-CLOSE",[I,F,E],f"handle — openingConns-- and Close callback while holding mu {c211}")
put("E-CLOSE",[A],f"transition → Open_Empty {c211}")
put("E-CLOSE",[W],f"transition → Open_Waiting_Stranded {c211}; the decrement wakes no waiter → Q-04")
put("E-CLOSE",[X],f"handle — {c211}; waiters stay blocked → Q-04")
put("E-CLOSE",[R],f"ignore (accidental) → Q-06 — returns nil without calling any close function {c208}")
# ---- E-RELEASE
put("E-RELEASE",[I,F,E,A],f"transition → Released {c227}; idle connections closed via the saved close function (channel.go:241); checked-out connections untouched → Q-06")
put("E-RELEASE",[W,X],f"transition → Released {c227}; queued waiters are not woken and stay blocked (channel.go:137) → Q-01")
put("E-RELEASE",[R],f"ignore (documented) {c234} — the second Release returns at once")
# ---- E-LEN
put("E-LEN",OPEN,f"handle — returns the idle count, taking mu {c247} → Q-16")
put("E-LEN",[R],f"handle — returns 0 (length of a nil channel) {c247}")
# ---- I-IDLE-EXPIRE
put("I-IDLE-EXPIRE",[I,F,X],f"ignore (accidental) → Q-13 — no timer; the connection stays open until a Get receives it {c116} or Release drains it")
put("I-IDLE-EXPIRE",[E,A,W],f"ignore (documented) {c116} — inferred: no idle connection exists in this state; the expiry check applies only to a received idle connection")
put("I-IDLE-EXPIRE",[R],f"ignore (documented) {c241} — idle connections were closed by Release")
# ---- UV-GET-DELAY
put("UV-GET-DELAY",[I,F,E,A],f"ignore (documented) {c137} — inferred: no Get waits in this state; waiting happens only at this line")
put("UV-GET-DELAY",[W,X],f"ignore (accidental) → Q-02 — no wait timeout or cancellation {c137}; waitTimeOut is never used (channel.go:46)")
put("UV-GET-DELAY",[R],f"ignore (accidental) → Q-01 — waiters stranded by Release stay blocked {c137}")
# ---- UV-GET-STALE
put("UV-GET-STALE",OPEN,f"ignore (documented) {c227} — inferred: no Release has happened, so no Get holds a stale idle channel")
put("UV-GET-STALE",[R],"UNSPECIFIED → Q-07 — timing decides: the Get may receive a connection Release is draining and return it live, receive nil and return ErrClosed (channel.go:112), or reach the slow path before the channel is closed, where at capacity it waits forever (channel.go:133 precedes channel.go:150); a Ping check that passed races the nil assignment (channel.go:229) → Q-08")
# ---- UV-PUT-LOSS
put("UV-PUT-LOSS",OPEN,f"ignore (accidental) → Q-12 — no ownership record; openingConns stays incremented {c159}, the capacity slot is lost for the pool's lifetime")
put("UV-PUT-LOSS",[R],"ignore (accidental) → Q-06 — the connection is never closed by the pool")
# ---- UV-PUT-DUP
put("UV-PUT-DUP",[I,E,A],f"handle — both Puts enqueue the same connection {c190}; two later Gets receive it → Q-11")
put("UV-PUT-DUP",[F],f"handle — the duplicate is closed via Close {c196} while the first copy stays idle: the pool holds a closed connection and openingConns is one too low → Q-11")
put("UV-PUT-DUP",[W,X],f"handle — both copies are handed to waiters {c183}: two callers share one connection → Q-11")
put("UV-PUT-DUP",[R],"ignore (accidental) → Q-06")
# ---- UV-PUT-FOREIGN
put("UV-PUT-FOREIGN",[I,E,A],f"handle — accepted into the idle channel {c190} without openingConns++ → Q-10")
put("UV-PUT-FOREIGN",[F],f"handle — closed via Close {c196}, decrementing openingConns for a connection never counted → Q-10")
put("UV-PUT-FOREIGN",[W,X],f"handle — handed to the oldest waiter {c183} → Q-10")
put("UV-PUT-FOREIGN",[R],"ignore (accidental) → Q-06")
# ---- UV-PUT-BROKEN
put("UV-PUT-BROKEN",[I,E,A],f"handle — enqueued {c190}; the next Get discards it when Ping is configured (channel.go:124), otherwise returns it")
put("UV-PUT-BROKEN",[F],f"handle — closed via Close {c196}")
put("UV-PUT-BROKEN",[W,X],f"handle — handed to a waiter without a Ping check {c183}; only the expiry check runs (channel.go:141) → Q-14")
put("UV-PUT-BROKEN",[R],"ignore (accidental) → Q-06")
# ---- UV-PUT-CLOSE-SAME
put("UV-PUT-CLOSE-SAME",OPEN,f"handle — both run: Close decrements and closes it {c211} while Put pools it (channel.go:190) or hands it to a waiter (channel.go:183); a closed connection stays in circulation → Q-10")
put("UV-PUT-CLOSE-SAME",[R],"ignore (accidental) → Q-06")
# ---- UV-CLOSE-DUP
put("UV-CLOSE-DUP",[I,F,E,X],f"handle — second decrement and second Close callback {c211}; openingConns falls below the true count and can go negative, allowing creation beyond MaxCap → Q-10")
put("UV-CLOSE-DUP",[A],f"transition → Open_Empty {c211} (capacity reopened by a phantom decrement) → Q-10")
put("UV-CLOSE-DUP",[W],f"transition → Open_Waiting_Stranded {c211} → Q-10")
put("UV-CLOSE-DUP",[R],"ignore (accidental) → Q-06")
# ---- UV-CLOSE-FOREIGN
put("UV-CLOSE-FOREIGN",[I,F,E,X],f"handle — decrements for a connection never counted and closes it {c211} → Q-10")
put("UV-CLOSE-FOREIGN",[A],f"transition → Open_Empty {c211} → Q-10")
put("UV-CLOSE-FOREIGN",[W],f"transition → Open_Waiting_Stranded {c211} → Q-10")
put("UV-CLOSE-FOREIGN",[R],"ignore (accidental) → Q-06")
# ---- UV-CLOSE-IDLE
put("UV-CLOSE-IDLE",[I,F,X],f"handle — decrements and closes it {c211} while it stays in the idle channel; a later Get returns it unless Ping rejects it → Q-10")
put("UV-CLOSE-IDLE",[E,A,W],f"ignore (documented) {c110} — inferred: no idle connection exists in this state")
put("UV-CLOSE-IDLE",[R],"ignore (accidental) → Q-06")
# ---- UV-FACTORY-ERR
put("UV-FACTORY-ERR",[I,F],f"reject — reached only after every idle connection was discarded below the cap (G-04); the error is returned unwrapped, openingConns unchanged {c157} → Q-17")
put("UV-FACTORY-ERR",[E],f"reject — the factory error is returned unwrapped, openingConns unchanged, no retry {c157} → Q-17")
put("UV-FACTORY-ERR",[A,W],f"ignore (documented) {c133} — the factory is not invoked at capacity; the Get waits instead")
put("UV-FACTORY-ERR",[X],f"reject — a new Get below the cap gets the factory error {c157}; the queued waiters stay blocked → Q-17")
put("UV-FACTORY-ERR",[R],f"ignore (documented) {c228} — no factory after Release; Get returns ErrClosed before any factory call (channel.go:152)")
# ---- UV-FACTORY-SLOW
put("UV-FACTORY-SLOW",[I,F,E,X],f"handle — the factory runs while Get holds mu {c154}; Put, Close, Len, Release and other Gets block until it returns → Q-09")
put("UV-FACTORY-SLOW",[A,W],f"ignore (documented) {c133} — the factory is not invoked at capacity")
put("UV-FACTORY-SLOW",[R],f"ignore (documented) {c228}")
# ---- UV-FACTORY-NILCONN
put("UV-FACTORY-NILCONN",[I,F,E,X],f"handle — Get returns (nil, nil) and openingConns++ {c159}; Put(nil) and Close(nil) reject the value (channel.go:169, channel.go:204), so the slot is never released → Q-19")
put("UV-FACTORY-NILCONN",[A,W],f"ignore (documented) {c133} — the factory is not invoked at capacity")
put("UV-FACTORY-NILCONN",[R],f"ignore (documented) {c228}")
# ---- UV-CLOSEFN-ERR
put("UV-CLOSEFN-ERR",OPEN,f"handle — openingConns was decremented before the callback {c211}; the error is returned by Close and by an overflowing Put (channel.go:196), dropped by Get's discard paths (channel.go:118) → Q-18")
put("UV-CLOSEFN-ERR",[R],f"ignore (documented) {c231} — no close function after Release, so Close invokes no callback (Release drops callback errors, channel.go:241)")
# ---- UV-CLOSEFN-SLOW
put("UV-CLOSEFN-SLOW",OPEN,f"handle — the callback runs under mu with a deferred unlock {c212}; every other pool operation blocks until it returns → Q-09")
put("UV-CLOSEFN-SLOW",[R],f"ignore (documented) {c231}")
# ---- UV-CB-REENTER
put("UV-CB-REENTER",[I,F,E,X],f"handle — a Factory (channel.go:154) or Close callback (channel.go:212) that calls a pool method waits for mu held by its own call chain {c154}: deadlock of that caller and of every later pool operation → Q-09")
put("UV-CB-REENTER",[A,W],f"handle — the Close callback calls back into the pool while Close holds mu {c212}: deadlock → Q-09")
put("UV-CB-REENTER",[R],f"ignore (documented) {c231} — callbacks are cleared; Release runs the saved close function outside the lock (channel.go:241)")

T1 = ["E-GET","E-PUT","E-CLOSE","E-RELEASE","E-LEN","I-IDLE-EXPIRE","UV-GET-DELAY"]
T2 = ["UV-GET-STALE","UV-PUT-LOSS","UV-PUT-DUP","UV-PUT-FOREIGN","UV-PUT-BROKEN","UV-PUT-CLOSE-SAME","UV-CLOSE-DUP","UV-CLOSE-FOREIGN"]
T3 = ["UV-CLOSE-IDLE","UV-FACTORY-ERR","UV-FACTORY-SLOW","UV-FACTORY-NILCONN","UV-CLOSEFN-ERR","UV-CLOSEFN-SLOW","UV-CB-REENTER"]
assert sorted(T1+T2+T3) == sorted({e for s in S for e in M[s]}), "column set"
for s in S:
    assert len(M[s]) == 22, (s, len(M[s]), sorted(set(T1+T2+T3)-set(M[s])))
out = sys.stdout
head = open(sys.argv[1]).read()
tail = open(sys.argv[2]).read()
out.write(head)
for n, T in enumerate([T1, T2, T3], 1):
    out.write(f"\n### Sub-table {n}\n\n| State | " + " | ".join(T) + " |\n|" + "---|" * (len(T)+1) + "\n")
    for s in S:
        out.write(f"| **{s}** | " + " | ".join(M[s][e] for e in T) + " |\n")
out.write(tail)
