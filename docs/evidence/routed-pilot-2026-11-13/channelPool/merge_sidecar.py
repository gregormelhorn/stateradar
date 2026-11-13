#!/usr/bin/env python3
"""Merge the sections gen_analysis_sidecar.py cannot derive (pairs from
adversarial-traces.md, guard outcomes from guard-results.txt, ODC fields
from open-questions.md) into analysis.json. Parses the artifacts; no
hand-typed outcomes."""
import json, re
from pathlib import Path
here = Path(__file__).resolve().parent
d = json.loads((here / "analysis.json").read_text())
traces = (here / "adversarial-traces.md").read_text()
cat = (here / "event-catalogue.md").read_text()
pairs = sorted(set(re.findall(r"P-\d+[ab]", cat)))
d["pairs"] = []
for p in pairs:
    hdr = re.search(r"^\*\*(T-[^ ]+) — [^\n]*\(pair " + p + r"\)\*\*$", traces, re.M)
    d["pairs"].append({"id": p, "trace": hdr.group(1) if hdr else ""})
groups = []
for line in (here / "guard-results.txt").read_text().splitlines():
    m = re.match(r"group (G-\d+)[^:]*: (proven|violation|not-formalizable)(?:: (.*))?$", line)
    if m:
        g = {"id": m.group(1), "outcome": m.group(2)}
        if m.group(3):
            g["reason"] = m.group(3)
        groups.append(g)
d["guardGroups"] = groups
oq = (here / "open-questions.md").read_text()
blocks = re.split(r"\n(?=Q-\d+ — )", oq)
odc = {}
for b in blocks:
    m = re.match(r"(Q-\d+) — ", b)
    if not m:
        continue
    f = re.search(r"^Fault: (.*)$", b, re.M)
    t = re.search(r"^Trigger: ([^(\n]*)", b, re.M)
    odc[m.group(1)] = {"fault": re.findall(r"F-\d{2}", f.group(1)) if f else [],
                       "trigger": t.group(1).strip() if t else ""}
for q in d["questions"]:
    q.update(odc.get(q["id"], {}))
for k in ("pairs", "guardGroups"):
    d.get("completeness", {}).pop(k, None)
if not d.get("completeness"):
    d.pop("completeness", None)
(here / "analysis.json").write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print("pairs", [(p["id"], p["trace"]) for p in d["pairs"]])
print("guards", [(g["id"], g["outcome"]) for g in groups])
print("questions with ODC", sum(1 for q in d["questions"] if q.get("fault")))
