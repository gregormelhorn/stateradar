from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "pack" / "tools"))
from guard_proofs import boundary_probe, check_group, render
from z3 import And, Bool, Int, Not, Or

initial, idle, cap = Int("initial"), Int("idle"), Int("cap")
count, pending, i, duration, age_delta = (Int(var) for var in ("count","pending","i","duration","age_delta"))
config, factory, closer, payload, available, ping = (Bool(var) for var in ("config","factory","closer","payload","available","ping"))
valid = And(initial >= 0, initial <= idle, idle <= cap)
def branches(label, decision, otherwise):
    return [(label, decision), (otherwise, Not(decision))]

groups = [
    ("G-01 New bounds", branches("accept bounds", valid,"invalid bounds"), [],
     [{initial:x,idle:2,cap:3} for x in (-1,0,1,2,3)] +
     [{initial:0,idle:x,cap:3} for x in (2,3,4)], "All integer bounds, before any allocation"),
    ("G-02 New callback presence", [("nil config",Not(config)),("missing factory",And(config,Not(factory))),
       ("missing closer",And(config,factory,Not(closer))),("continue",And(config,factory,closer))], [],
     [{config:a,factory:b,closer:c} for a,b,c in [(False,True,True),(True,False,True),(True,True,False),(True,True,True)]], "After capacity validation for nonnil config"),
    ("G-03 Get admission after miss", [("queue",count>=cap),("closed",And(count<cap,Not(factory))),
        ("create",And(count<cap,factory))], [cap>=0],
     [{count:n,cap:1,factory:f} for n in (0,1,2) for f in (True,False)] +
     [{count:n,cap:0,factory:True} for n in (-1,0,1)], "Mutex-held count, valid configured cap. No assumed lower bound on count"),
    ("G-04 Age decision at sampled time", [("disabled",duration<=0),("expired",And(duration>0,age_delta>0)),
         ("eligible",And(duration>0,age_delta<=0))], [],
     [{duration:d,age_delta:a} for d in (-1,0,1) for a in (-1,0,1)], "Integer duration and ordering of sampled time relative to computed deadline. Runtime sampling is separate"),
    ("G-05 Put waiter priority", branches("handoff",pending>0,"try idle send"),[pending>=0],
     [{pending:x} for x in (0,1,2)], "Length of mutex-protected slice. Negative length structurally unavailable"),
    ("G-09 Constructor iteration", branches("create next",i<initial,"finished"),[initial>=0,i>=0],
     [{i:x,initial:1} for x in (0,1,2)], "Valid config, no early factory error, nonnegative index"),
    ("G-10 Put nil and pool availability", [("reject",Not(payload)),("closed",And(payload,Not(available))),
         ("live",And(payload,available))],[],
     [{payload:p,available:a} for p,a in ((False,False),(True,False),(True,True))], "Interface nilness is a Boolean, distinct from typed nil"),
    ("G-11 Close and callback availability", [("reject",Not(payload)),("nil closer",And(payload,Not(closer))),
          ("invoke",And(payload,closer))],[],
     [{payload:p,closer:c} for p,c in ((False,False),(True,False),(True,True))], "Callback presence sampled under mutex"),
    ("G-12 Ping dispatch gate", branches("validate",ping,"skip"),[],
     [{ping:True},{ping:False}], "One observed callback presence flag. Later dispatch reads it independently"),
    ("G-13 Release snapshot", branches("drain",available,"return"),[],
     [{available:True},{available:False}], "Captured channel presence under mutex")
]

lines = []
for name, guards, assumptions, probes, domain in groups:
    lines.append(render([check_group(name, guards, assumptions)]))
    lines.append(f"  assumptions: {domain}")
    lines.extend(f"  {assignment}: {selected}" for assignment, selected in boundary_probe(guards, probes))
lines.extend([
    "group G-06 channel select readiness: not-formalizable: dynamic-state: channel service can change between select and the following lock. P-01a",
    "group G-07 callback physical result: not-formalizable: external-call: callback contracts give no resource-effect predicate. Q-21",
    "group G-08 requester completion: not-formalizable: dynamic-state: pending receive only progresses after send or close. Q-02",
    "group G-14 sampled clock ordering: not-formalizable: clock: scheduler and actual sampled time unavailable. Q-14",
])
out = "\n".join(lines) + "\n"
Path(__file__).with_name("guard-results.txt").write_text(out)
print(out, end="")
