#!/usr/bin/env python3
"""Pack self-consistency checker (dogfooding: checks as executed code).

Verifies:
  1. The seven-value disposition vocabulary appears in both 00 and 02.
  2. Artifact filenames referenced across prompts are defined by the
     producing prompts (02 or 04).
  3. README version matches the newest (highest) CHANGELOG entry.
Exit code 0 = OK, 1 = violations (printed).
"""
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "prompts"
errors = []

def read(name): return (P / name).read_text(encoding="utf-8")

VOCAB = ["transition", "handle", "ignore (documented)", "ignore (accidental)",
         "defer (queued)", "reject", "UNSPECIFIED"]
for fname in ("00-methods-reference.md", "02-pilot.md"):
    text = read(fname)
    for v in VOCAB:
        if v not in text:
            errors.append(f"{fname}: disposition value '{v}' missing")

ARTIFACTS = {  # filename -> prompts that define/produce it
    "disposition-matrix.md": ["02-pilot.md"],
    "open-questions.md": ["02-pilot.md"],
    "event-catalogue.md": ["02-pilot.md"],
    "adversarial-traces.md": ["02-pilot.md"],
    "invariants-and-lints.md": ["02-pilot.md"],
    "part-b-diff.md": ["02-pilot.md"],
    "check_matrix.py": ["02-pilot.md"],
    "check_guards.py": ["02-pilot.md"],
    "guard-results.txt": ["02-pilot.md"],
    "analysis.json": ["02-pilot.md"],
    "manifest.json": ["06-reconcile.md"],
    "to-be.machine.mmd": ["03-resolution.md"],
    "matrix-coverage.json": ["04-testgen.md"],
    "deviation-report.md": ["04-testgen.md"],
    "seam.md": ["04-testgen.md"],
    "test-coverage-map.md": ["07-test-audit.md"],
    "coverage-diff-report.md": ["07-test-audit.md"],
    "check_test_coverage.py": ["07-test-audit.md"],
}
all_texts = {f.name: f.read_text(encoding="utf-8") for f in sorted(P.glob("*.md"))}
for artifact, producers in ARTIFACTS.items():
    if not any(artifact in all_texts[p] for p in producers):
        errors.append(f"artifact '{artifact}' not defined in {producers}")
    for fname, text in all_texts.items():
        if artifact in text and artifact not in "".join(all_texts[p] for p in producers):
            errors.append(f"{fname} references undefined artifact '{artifact}'")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
rv = re.search(r"\*\*Version (\d+\.\d+)", readme)
# Newest = the highest version anywhere in the file, not the first
# entry. A mis-ordered CHANGELOG must not silence this check (the
# v1.20.3/v1.20.2 entries sat above v1.24 and did exactly that).
entries = [(int(m.group(1)), int(m.group(2))) for m in
           re.finditer(r"^## v(\d+)\.(\d+)", changelog, re.M)]
cv = max(entries) if entries else None
if not rv or not cv:
    errors.append("could not parse versions from README/CHANGELOG")
elif tuple(int(p) for p in rv.group(1).split(".")) != cv:
    errors.append(f"version mismatch: README {rv.group(1)} vs CHANGELOG {cv[0]}.{cv[1]}")

if errors:
    print("PACK CONSISTENCY: FAIL")
    for e in errors: print(" -", e)
    sys.exit(1)
print(f"PACK CONSISTENCY: OK ({len(ARTIFACTS)} artifacts, vocab x2, version {rv.group(1)})")
