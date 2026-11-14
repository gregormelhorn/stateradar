"""Verify the effective channelPool guards using the pack's proof library."""
from pathlib import Path
import sys

import z3

PACK = Path(__file__).resolve().parents[3] / "pack" / "tools"
sys.path.insert(0, str(PACK))
from guard_proofs import boundary_probe, check_group, render

results = []
details = []

def prove(name, guards, assumptions, samples, evidence):
    results.append(check_group(name, guards, assumptions))
    details.append(f"{name}: {evidence}. Assumptions: {assumptions or 'typed domain only'}.")
    for values, branch in boundary_probe(guards, samples):
        details.append(f"  {values} -> {branch}")

def boolean(name, variable, true, false, evidence):
    flag = z3.Bool(variable)
    prove(name, [(true, flag), (false, z3.Not(flag))], [], [{flag: False}, {flag: True}], evidence)

initial, idle, maximum, count, duration, queue = z3.Ints("initial idle maximum count duration queue")
valid = z3.And(initial >= 0, initial <= idle, idle <= maximum)
prove("G-01 capacities", [("accept", valid), ("reject", z3.Not(valid))], [],
      [{initial: i, idle: j, maximum: k} for i,j,k in [(-1,1,2),(0,1,2),(1,1,2),(2,1,2),(0,1,0),(0,1,1),(0,1,2)]],
      'channel.go:59 ("poolConfig.InitialCap <= poolConfig.MaxIdle")')
boolean("G-02 factory presence", "factory_present", "continue", "reject", 'channel.go:62 ("if poolConfig.Factory == nil")')
boolean("G-03 close presence", "close_present", "continue", "reject", 'channel.go:65 ("if poolConfig.Close == nil")')
boolean("G-04 ping configuration", "ping_configured", "remember", "skip assignment", 'channel.go:78 ("if poolConfig.Ping != nil")')
prove("G-05 active limit", [("queue", count >= maximum), ("check factory", count < maximum)],
      [maximum >= 0], [{count:i, maximum:1} for i in (0,1,2)] + [{count:-1,maximum:0},{count:0,maximum:0},{count:1,maximum:0}],
      'channel.go:133 ("c.openingConns >= c.maxActive"). Count unrestricted because provenance and cleanup can corrupt it')
boolean("G-06 channel snapshot", "snapshot_present", "observe", "reject", 'channel.go:105 ("if conns == nil")')
boolean("G-07 factory admission", "factory_available", "call", "closed", 'channel.go:150 ("if c.factory == nil")')
prove("G-08 idle timeout enable", [("check age", duration > 0), ("skip", duration <= 0)], [],
      [{duration:i} for i in (-1,0,1)], 'channel.go:115 ("timeout > 0"), channel.go:141 ("timeout > 0")')
boolean("G-10 buffered ping decision", "has_ping", "call", "skip", 'channel.go:123 ("if c.ping != nil")')
boolean("G-11 Put nil payload", "put_nil", "reject", "lock", 'channel.go:168 ("if conn == nil")')
boolean("G-12 Put detached", "put_detached", "Close", "check waiters", 'channel.go:174 ("if c.conns == nil")')
prove("G-13 Put queue length", [("handoff", queue > 0), ("idle attempt", queue <= 0)], [queue >= 0],
      [{queue:i} for i in (-1,0,1)], 'channel.go:179 ("len(c.connReqs)"). Negative probe is outside slice domain')
boolean("G-14 Close and Ping payload", "payload_nil", "reject", "delegate path", 'channel.go:203 ("if conn == nil"), channel.go:217 ("if conn == nil")')
boolean("G-15 Close callback", "close_missing", "return nil", "decrement and call", 'channel.go:208 ("if c.close == nil")')
boolean("G-16 Release snapshot", "release_nil", "return", "drain", 'channel.go:234 ("if conns == nil")')
boolean("G-17 request channel receive", "request_ok", "consume", "reject", 'channel.go:138 ("if !ok"). False is structurally unreachable on current producer paths')
boolean("G-18 buffered nil receive", "buffer_nil", "ErrClosed", "check age", 'channel.go:111 ("if wrapConn == nil")')
boolean("G-19 Factory result", "factory_error", "reject", "commit", 'channel.go:84 ("if err != nil"), channel.go:155 ("if err != nil")')
boolean("G-20 Ping result", "ping_error", "discard and retry", "return", 'channel.go:124 ("err != nil"). Effect of injected callback remains open')
prove("G-22 initialization bound", [("iterate", initial < idle), ("exit", initial >= idle)],
      [idle >= 0, initial >= 0], [{initial:i,idle:1} for i in (0,1,2)],
      'channel.go:82 ("i < poolConfig.InitialCap"). Variables stand for loop index and configured initial count in this group')
unproven = [
 "group G-09 idle age comparison: not-formalizable: clock: channel.go:116, 142. Comparing effective deadline against the live clock. Inspection: sample before/equal keeps the resource, later discards.",
 "group G-21 runtime channel readiness: not-formalizable: dynamic-state: channel.go:110, 190. Readiness includes concurrent send and receive, including unbuffered rendezvous. Inspection: ready chooses the channel case, unavailable chooses default.",
 "group G-23 callback outcome effects: not-formalizable: external-call: channel.go:83, 124, 154, 212, 220, 241. Boolean return tests are separately proven. Actual cleanup, health, blocking and panic contracts are external.",
]
output = render(results).rstrip() + "\n" + "\n".join(unproven + ["", *details]) + "\n"
Path(__file__).with_name("guard-results.txt").write_text(output)
print(output, end="")
