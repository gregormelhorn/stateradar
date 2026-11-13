#!/usr/bin/env python3
"""Per-run merge: gen_analysis_sidecar.py derives cells from the matrix only.
This adds what lives elsewhere — pairs (adversarial-traces.md), guard outcomes
(guard-results.txt), ODC fields of questions (open-questions.md) — from those
files' declarations, never hand-typed values. Run after the generator."""
import json, re
from pathlib import Path
A = Path(__file__).resolve().parent
data = json.loads((A / "analysis.json").read_text())
cat = (A / "event-catalogue.md").read_text()
traces = (A / "adversarial-traces.md").read_text()
pairs = []
for pid in sorted(set(re.findall(r"P-\d+[ab]\b", cat))):
    m = re.search(rf"^### ({re.escape(pid)}) — (.+)$", traces, re.M)
    if m:
        pairs.append({"id": pid, "trace": f"adversarial-traces.md#{pid}: {m.group(2)}"})
data["pairs"] = pairs
groups = []
for line in (A / "guard-results.txt").read_text().splitlines():
    m = re.match(r"group (G-\d+) [^:]*: (proven|violation|not-formalizable)(?:: (.*))?$", line)
    if m:
        g = {"id": m.group(1), "outcome": m.group(2)}
        if m.group(3):
            g["reason"] = m.group(3)
        groups.append(g)
data["guardGroups"] = sorted(groups, key=lambda g: g["id"])
oq = (A / "open-questions.md").read_text()
odc = {}
for block in re.split(r"\n(?=## Q-)", oq):
    m = re.match(r"## (Q-\d+)", block)
    if not m:
        continue
    f = re.search(r"\*\*Fault:\*\*\s*(.+)", block)
    t = re.search(r"\*\*Trigger:\*\*\s*(.+)", block)
    odc[m.group(1)] = {"fault": re.findall(r"F-\d{2}", f.group(1)) if f else [], "trigger": t.group(1).strip() if t else ""}
for q in data["questions"]:
    q.update(odc.get(q["id"], {}))
for k in ("pairs", "guardGroups"):
    if data.get(k):
        data.get("completeness", {}).pop(k, None)
if "completeness" in data and not data["completeness"]:
    data.pop("completeness")
(A / "analysis.json").write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
print(f"merged: {len(pairs)} pairs, {len(groups)} guard groups, ODC on {sum(1 for q in data['questions'] if q.get('trigger'))} questions")
