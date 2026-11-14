from pathlib import Path
import sys

import z3

adir = Path(__file__).resolve().parent
sys.path.insert(0, str(adir.parents[2] / "pack" / "tools"))
from guard_proofs import boundary_probe, check_group, render

size, cur, n, head, length = z3.Ints("size cur n head length")
done, ready, front = z3.Bools("done ready front")
free = size - cur
fit = z3.And(free >= n, length == 0)
nat = [size >= 0, cur >= 0, cur <= size, n >= 0, length >= 0, head >= 0, head <= size]
groups = [
    ("G-01 locked entry Done", [("reject", done), ("continue", z3.Not(done))],
     [{done: value} for value in (False, True)]),
    ("G-02 fast / oversized / enqueue", [("fast", fit), ("oversized", z3.And(z3.Not(fit), n > size)), ("enqueue", z3.And(z3.Not(fit), n <= size))],
     [{size: 3, cur: 1, n: weight, length: count} for weight in (1, 2, 3, 4) for count in (0, 1)]),
    ("G-03 try", [("admit", fit), ("false", z3.Not(fit))],
     [{size: 3, cur: 1, n: weight, length: count} for weight in (1, 2, 3) for count in (0, 1)]),
    ("G-04 release", [("panic", cur - n < 0), ("notify", cur - n >= 0)],
     [{cur: 2, n: weight} for weight in (1, 2, 3)]),
    ("G-05 notify", [("empty", length == 0), ("stop", z3.And(length > 0, free < head)), ("grant", z3.And(length > 0, free >= head))],
     [{size: 3, cur: 1, head: weight, length: count} for weight in (1, 2, 3) for count in (0, 1)]),
    ("G-06 cancellation cleanup", [("rollback", ready), ("unlink", z3.Not(ready))],
     [{ready: value} for value in (False, True)]),
    ("G-07 canceled head rescan", [("notify", z3.And(front, free > 0)), ("skip", z3.Not(z3.And(front, free > 0)))],
     [{size: 2, cur: charge, front: at_front} for charge in (3, 2, 1) for at_front in (False, True)]),
    ("G-08 granted receiver Done", [("rollback", done), ("success", z3.Not(done))],
     [{done: value} for value in (False, True)]),
]
results = [check_group(name, branches, nat) for name, branches, _ in groups]
lines = ["NAT-01: nonnegative capacity, outstanding charge in [0,size], nonnegative input and queue length, 0 <= head <= size. Integer arithmetic within representable range.", render(results)]
for name, branches, points in groups:
    lines.append(name + " boundary probes (NAT-01; free=-1 intentionally outside NAT):")
    lines.extend(f"  {inputs} => {labels}" for inputs, labels in boundary_probe(branches, points))
lines += [
    "group G-09 initial queued select: not-formalizable: dynamic-state: Done and ready can both become available before select evaluates; scheduler selects either ready case. G-06 and G-08 prove the sampled subdecisions.",
    "  Explicit readiness cases: neither waits, Done only cancels, ready only checks Done, both allow either branch. Both cancellation continuations roll back an already granted charge.",
]
report = "\n".join(lines) + "\n"
(adir / "guard-results.txt").write_text(report)
print(report, end="")
sys.exit(any(result.outcome == "violation" for result in results))
