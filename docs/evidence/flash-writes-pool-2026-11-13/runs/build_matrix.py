import json,re,sys
R="/tmp/flash-writes-MBhG/runs"; A="/tmp/flash-writes-MBhG/pool/domain-analysis/channelPool"
src=open("/tmp/flash-writes-MBhG/pool/channel.go").read().splitlines()
drafts={}
order=[]
for k in("base","uv"):
    d=json.load(open(f"{R}/cells-{k}.json"))
    ev=[e["id"] for e in d["task"]["events"]]; order.append(ev)
    states=[s["name"] for s in d["task"]["states"]]
    for c in d["cells"]: drafts[(c["state"],c["event"])]=c
def txt(c):
    head=c["disposition"]+(f" → {c['target']}" if c.get("target") else "")
    return head,f' channel.go:{c["line"]} ("{c["fragment"]}")',c["note"]
ov={}
def O(s,e,disp,line,frag,note,target=None,q=None):
    head=disp+(f" → {target}" if target else "")
    if q: head+=f" → {q}"
    ov[(s,e)]=f'{head} channel.go:{line} ("{frag}") — {note}'
CA="c.openingConns--"
O("Open_IdleAvailable","Put","transition",190,"case c.conns <- &idleConn{conn: conn, t: time.Now()}:","stores the connection as idle; becomes Open_IdleFull when the channel fills, otherwise stays",target="Open_IdleFull")
O("Open_NoIdle_AtCap","Close","transition",211,CA,"count falls below maxActive; waiters are not involved (none here)",target="Open_NoIdle_BelowCap")
O("Open_Waiting_AtCap","Get","handle",135,"c.connReqs = append(c.connReqs, req)","another waiter is queued and blocks at channel.go:137 with no timeout or cancel (Q-02)")
O("Open_Waiting_AtCap","Put","transition",183,"req <- connReq{","hands the connection to the oldest waiter without ping check (Q-15); becomes Open_NoIdle_AtCap when the last waiter is served, otherwise stays",target="Open_NoIdle_AtCap")
O("Open_Waiting_AtCap","Close","transition",211,CA,"count falls below maxActive; queued waiters are not signalled (Q-03)",target="Open_Waiting_BelowCap")
O("Open_Waiting_AtCap","Release","transition",227,"c.conns = nil","pool becomes Closed; queued waiters stay blocked at channel.go:137, never signalled (Q-01)",target="Closed")
O("Open_Waiting_BelowCap","Put","transition",183,"req <- connReq{","hands the connection to the oldest waiter without ping check (Q-15); becomes Open_NoIdle_BelowCap when the last waiter is served, otherwise stays",target="Open_NoIdle_BelowCap")
O("Open_Waiting_BelowCap","Close","handle",211,CA,"count is decremented; queued waiters are not signalled although capacity exists (Q-03)")
O("Open_Waiting_BelowCap","Get","transition",159,"c.openingConns++","openingConns < maxActive, so Get creates a connection via the factory under c.mu without queueing behind the waiters (Q-03); becomes Open_Waiting_AtCap when the count reaches maxActive",target="Open_Waiting_AtCap")
O("Open_Waiting_BelowCap","Release","transition",227,"c.conns = nil","pool becomes Closed; queued waiters stay blocked, never signalled (Q-01)",target="Closed")
O("Open_Waiting_IdleAvailable","Get","transition",129,"return wrapConn.conn, nil","takes an idle connection although waiters are queued (Q-04); becomes Open_Waiting_AtCap when the last idle connection is taken, otherwise stays",target="Open_Waiting_AtCap")
O("Open_Waiting_IdleAvailable","Put","transition",183,"req <- connReq{","hands the connection to the oldest waiter, idle connections stay idle (Q-04); becomes Open_IdleAvailable when the last waiter is served, otherwise stays",target="Open_IdleAvailable")
O("Open_Waiting_IdleAvailable","Release","transition",227,"c.conns = nil","pool becomes Closed; queued waiters stay blocked, never signalled (Q-01)",target="Closed")
O("Closed","Put","ignore (accidental)",176,"return c.Close(conn)","Put hands the connection to Close, which returns nil without calling the close callback (channel.go:208-210): the connection is neither stored nor closed",q="Q-05")
O("Closed","Close","ignore (accidental)",209,"return nil","c.close is nil after Release, so the connection is not closed and openingConns is not changed",q="Q-05")
O("Closed","Ping","handle crash:",220,"return c.ping(conn)","c.ping is nil after Release, so the call panics",q="Q-06")
# UV
nilcell=lambda s:f'reject channel.go:168 ("if conn == nil {{") — Put returns "connection is nil. rejecting"; Close does the same (channel.go:204)'
for s in states:
    ov[(s,"UV-Conn-nil")]=nilcell(s)
dupput={ "Open_IdleAvailable":(190,"case c.conns <- &idleConn{conn: conn, t: time.Now()}:","the same connection is stored a second time; no duplicate check"),
 "Open_IdleFull":(196,"return c.Close(conn)","channel is full, so the connection is closed through Close (count decremented) although it may still be idle"),
 "Open_NoIdle_BelowCap":(190,"case c.conns <- &idleConn{conn: conn, t: time.Now()}:","the same connection is stored a second time; no duplicate check"),
 "Open_NoIdle_AtCap":(190,"case c.conns <- &idleConn{conn: conn, t: time.Now()}:","the same connection is stored a second time; no duplicate check"),
 "Open_Waiting_AtCap":(183,"req <- connReq{","the connection is handed to a waiter although another holder may still have it"),
 "Open_Waiting_BelowCap":(183,"req <- connReq{","the connection is handed to a waiter although another holder may still have it"),
 "Open_Waiting_IdleAvailable":(183,"req <- connReq{","the connection is handed to a waiter although another holder may still have it")}
for s,(l,f,n) in dupput.items(): O(s,"UV-Put-dup","ignore (accidental)",l,f,n,q="Q-11")
O("Closed","UV-Put-dup","ignore (accidental)",176,"return c.Close(conn)","Put after Release leaves the connection untouched",q="Q-05")
for s in states[:-1]:
    O(s,"UV-Close-dup","ignore (accidental)",212,"return c.close(conn)","a second Close decrements openingConns again and invokes the close callback again; no duplicate check",q="Q-12")
O("Closed","UV-Close-dup","ignore (accidental)",209,"return nil","Close returns nil without any effect",q="Q-05")
for s,(l,f,n) in dupput.items():
    O(s,"UV-Put-foreign","ignore (accidental)",l,f,n.replace("the same connection is stored a second time; no duplicate check","a connection not created by this pool is stored; openingConns is not incremented").replace("although another holder may still have it","; it was never counted in openingConns").replace("although it may still be idle","; openingConns is decremented for a connection that was never counted"),q="Q-13")
O("Closed","UV-Put-foreign","ignore (accidental)",176,"return c.Close(conn)","Put after Release leaves the connection untouched",q="Q-05")
for s in states[:-1]:
    O(s,"UV-Close-foreign","ignore (accidental)",212,"return c.close(conn)","openingConns is decremented and the close callback is invoked for a connection that was never counted; no origin check",q="Q-14")
O("Closed","UV-Close-foreign","ignore (accidental)",209,"return nil","Close returns nil without any effect",q="Q-05")
def cell(s,e):
    if (s,e) in ov: t=ov[(s,e)]
    else:
        h,c,n=txt(drafts[(s,e)]); t=h+c+(f" — {n}" if n else "")
    if e=="Ping" and s!="Closed": t+=" (Ping unconfigured: c.ping is nil and the call panics → Q-06)"
    return t.replace("handle crash: channel","handle crash: Ping function is nil and the call panics → Q-06 channel") if t.startswith("handle crash:") else t
bad=0
for (s,e),t in list(ov.items())+[]:
    m=re.search(r'channel\.go:(\d+) \("(.*?)"\)',t)
    ln=int(m.group(1)); w="\n".join(src[max(0,ln-4):ln+3])
    if m.group(2) not in w: print("FRAG MISSING",s,e,ln,m.group(2)); bad+=1
for k,c in drafts.items():
    ln=c["line"]; w="\n".join(src[max(0,ln-4):ln+3])
    if c["fragment"] not in w: print("DRAFT FRAG",k); bad+=1
out=["# channelPool — disposition matrix (as-is)","",
"Abstraction: completeness is relative to (1) regions of the field space (idle count, waiter queue, openingConns against maxActive, conns nil or not) as the 8 states below, (2) one public call run to completion per cell, with the Get loop (idle-timeout discard, ping discard, factory outcome) folded into the Get cell as guards G-01/G-02, (3) the configuration fixed at construction (Ping configured, IdleTimeout > 0, MaxIdle >= 1), and (4) callbacks Factory/Close/Ping treated as seam calls whose results are guard branches, not matrix events (see Q-08..Q-10). Count-level changes inside a state are not separate states. A guarded state change is written as the transition with the staying branch in the cell text.","",
"Provenance: every cell cites channel.go (observed-in-code). Cells drafted by DeepSeek Flash (`draft-cells`, runs/cells-base.json, runs/cells-uv.json) and checked by the agent against channel.go; cells the agent corrected or re-decided are listed in `summary.md` through `draft_cells.py compare`.","",
"<!-- states: "+", ".join(states)+" -->","<!-- terminal: Closed -->",""]
for i,ev in enumerate(order,1):
    out+=[f"### Sub-table {i}","","| State | "+" | ".join(ev)+" |","|---|"+"---|"*len(ev)]
    for s in states: out.append(f"| **{s}** | "+" | ".join(cell(s,e) for e in ev)+" |")
    out.append("")
open(f"{A}/disposition-matrix.md","w").write("\n".join(out))
print("bad",bad,"cells",len(states)*sum(map(len,order)))
