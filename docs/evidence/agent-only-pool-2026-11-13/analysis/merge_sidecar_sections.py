#!/usr/bin/env python3
"""Merge the sections that tools/gen_analysis_sidecar.py does not derive
(it says so in its completeness block) into analysis.json, mechanically
from their source artefacts — never by hand:

  pairs        <- event-catalogue.md pair ids; trace = the heading in
                  adversarial-traces.md that carries the same id
  guardGroups  <- guard-results.txt ("group G-nn ...: outcome")
  questions    <- fault / trigger fields from open-questions.md

Run after gen_analysis_sidecar.py, before tools/dsc_check.py.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
side = json.loads((HERE / "analysis.json").read_text(encoding="utf-8"))
cat = (HERE / "event-catalogue.md").read_text(encoding="utf-8")
traces = (HERE / "adversarial-traces.md").read_text(encoding="utf-8")
guards = (HERE / "guard-results.txt").read_text(encoding="utf-8")
oq = (HERE / "open-questions.md").read_text(encoding="utf-8")
errors = []

pairs = []
for pid in sorted(set(re.findall(r"P-\d+[ab]\b", cat))):
    m = re.search(rf"^#{{1,6}}\s+({re.escape(pid)}\b.*)$", traces, re.M)
    if not m:
        errors.append(f"pair {pid}: no trace heading in adversarial-traces.md")
        continue
    pairs.append({"id": pid, "trace": m.group(1).strip()})
side["pairs"] = pairs

groups = []
for m in re.finditer(r"^group (G-\d+)[^:]*: (proven|violation|not-formalizable)(.*)$", guards, re.M):
    g = {"id": m.group(1), "outcome": m.group(2)}
    if m.group(2) == "not-formalizable":
        g["reason"] = m.group(3).strip(" :")
    groups.append(g)
side["guardGroups"] = groups

blocks = re.split(r"^### (?=Q-\d+)", oq, flags=re.M)[1:]
odc = {}
for b in blocks:
    qid = b.split()[0]
    f = re.search(r"\*\*Fault:\*\*\s*(.+)", b)
    t = re.search(r"\*\*Trigger:\*\*\s*(.+)", b)
    odc[qid] = ({"fault": re.findall(r"F-\d{2}", f.group(1)) if f else [],
                 "trigger": t.group(1).strip() if t else ""})
for q in side["questions"]:
    if q["id"] in odc:
        q.update(odc[q["id"]])
    else:
        errors.append(f"{q['id']}: no ODC block")

comp = side.get("completeness", {})
for k in ("pairs", "guardGroups"):
    if side.get(k):
        comp.pop(k, None)
if comp:
    side["completeness"] = comp
else:
    side.pop("completeness", None)

(HERE / "analysis.json").write_text(json.dumps(side, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"merged: {len(pairs)} pairs, {len(groups)} guard groups, ODC fields on {len(odc)} questions")
if errors:
    print("MERGE ERRORS:\n - " + "\n - ".join(errors))
    sys.exit(1)
