#!/usr/bin/env python3
"""Pack self-consistency checker (dogfooding: checks as executed code).

Verifies:
  1. The rules registry (formats/rules.toml): generated blocks in the
     prompts/AGENTS/README match it, and its constraints hold
     (delegated to tools/gen_rules.py --check; the old VOCAB-x2 sync
     check is obsolete by construction — both vocabulary occurrences
     are generated from the registry).
  2. Artifact filenames referenced across prompts are defined by the
     producing prompts (02 or 04).
  3. README version matches the newest (highest) CHANGELOG entry.
Exit code 0 = OK, 1 = violations (printed).
"""
from pathlib import Path
import re, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "prompts"
errors = []

def read(name): return (P / name).read_text(encoding="utf-8")

gr = subprocess.run([sys.executable, str(ROOT / "tools" / "gen_rules.py"),
                     "--check"], capture_output=True, text=True)
sys.stdout.write(gr.stdout)
if gr.returncode != 0:
    errors.append("rules registry check failed (see output above)")

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

# 4. Path existence: every pack-internal file/directory referenced in
#    README, AGENTS, skills/, and docs/ must exist. Consumer-repo paths
#    (domain-analysis/, DR-nnn.yaml, CLAUDE.md, tools/prompt-pack/) are
#    excluded — they live in the consumer's repository.
PACK_ROOTS = {"prompts/", "tools/", "skills/", "commands/", "examples/",
             "formats/", "tests/", ".github/"}
CHECK_FILES = ["README.md", "AGENTS.md"]
for f in sorted((ROOT / "skills").rglob("*.md")):
    CHECK_FILES.append(str(f.relative_to(ROOT)))
for f in sorted((ROOT / "docs").rglob("*.md")):
    if "docs/superpowers/" in str(f):
        continue  # historical design specs, not current docs
    CHECK_FILES.append(str(f.relative_to(ROOT)))
for doc_name in CHECK_FILES:
    doc = (ROOT / doc_name).read_text(encoding="utf-8")
    for m in re.finditer(r"`([a-zA-Z0-9_/.-]+\.[a-z]{1,6})`", doc):
        if "/prompt-pack/" in m.group(1):
            continue  # consumer vendor mountpoint, never in the pack
        p = ROOT / m.group(1)
        if not p.exists() and any(m.group(1).startswith(r) for r in PACK_ROOTS):
            errors.append(f"{doc_name}: backtick path does not exist: {m.group(1)}")
    for m in re.finditer(r"^([a-zA-Z0-9_/.-]+/)\s+", doc, re.M):
        p = ROOT / m.group(1)
        if not p.is_dir() and any(m.group(1).startswith(r) for r in PACK_ROOTS):
            errors.append(f"{doc_name}: layout path does not exist: {m.group(1)}")

if errors:
    print("PACK CONSISTENCY: FAIL")
    for e in errors: print(" -", e)
    sys.exit(1)
print(f"PACK CONSISTENCY: OK ({len(ARTIFACTS)} artifacts, registry, version {rv.group(1)})")
