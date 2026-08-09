# Fault-Class Registry Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate all 22 fault entries in `formats/rules.toml` to the layer-separation schema and make `gen_rules` enforce it, atomically.

**Architecture:** One task, one commit — validation and migration must land together or `gen_rules --check` breaks main between them. The red probe runs the new validation against the unmigrated registry first; the selftest's internal broken-registry copies prove each rule fails on its own bad input.

**Tech Stack:** Python 3 stdlib (tomllib), TOML, the existing `tools/gen_rules.py` check/selftest structure.

## Global Constraints

- Closed vocabularies exactly as specified: `level ∈ {matrix, implementation, none}`; `observability ∈ {high, medium, low, n/a}`; `n/a` exactly when `level ∈ {matrix, none}`.
- `precondition` required iff `level == "implementation"`; absent otherwise.
- `none_reason` required iff `level == "none"`; absent otherwise.
- All 22 entries migrate in the same commit as the validation. Zero-warning budget must stay zero.
- `gen_rules` renders into `00-methods-reference.md`, `02-pilot.md`, `AGENTS.md` §5, and `README.md`; the migration must not change any rendered output.
- Red selftest cases live in `gen_rules.py`'s existing `selftest()` function, which builds broken registry copies — never break the real registry on disk.

---

## Entry Values (verbatim from the approved spec)

| Fault | level | observability | precondition / none_reason |
|---|---|---|---|
| F-01 | matrix | n/a | — |
| F-02 | matrix | n/a | — |
| F-03 | implementation | high | precondition = "emitted effects projected by the seam" |
| F-04 | matrix | n/a | — |
| F-05 | implementation | high | precondition = "counter or context variable projected by the suite" |
| F-06 | none | n/a | none_reason = "undocumented entry/exit paths are found by matrix totality (PA-14 round-tripping), not by code mutation" |
| F-07 | implementation | low | precondition = "multi-track suite modeling caller and internal lifecycles separately" |
| F-08 | implementation | high | precondition = "release count or released-state projected" |
| F-09 | implementation | medium | precondition = "seam supports cancel plus a post-cancel resource probe" |
| F-10 | none | n/a | none_reason = "multi-instance aggregate; needs an aggregate harness, not a per-component mutation" |
| F-11 | implementation | medium | precondition = "suite timeout catches the hang deterministically; deterministic callback-reentrancy delivery into a locked component" |
| F-12 | matrix | n/a | — |
| F-13 | implementation | medium | precondition = "clock injection in the seam (delay + absolute due-offset doctrine, v1.24)" |
| F-14 | implementation | high | precondition = "idempotence observable via repeated delivery plus counter" |
| F-15 | matrix | n/a | — |
| F-16 | matrix | n/a | — |
| F-17 | matrix | n/a | — |
| F-18 | implementation | medium | precondition = "payload-effect projection; plausible-but-wrong payload crafting in the seam" |
| F-19 | none | n/a | none_reason = "doctrine-mapping finding, not a mutation operator" |
| F-20 | matrix | n/a | — |
| F-21 | none | n/a | none_reason = "suite property (mirroring test), not a component fault" |
| F-22 | implementation | medium | precondition = "same clock seam as F-13" |

---

### Task 1: Validation, migration, selftests, gates, commit (atomic)

**Files:**
- Modify: `formats/rules.toml` (22 fault entries)
- Modify: `tools/gen_rules.py` (validation + selftest cases)
- Plan: `docs/superpowers/plans/2026-08-09-fault-class-registry-migration.md`

**Interfaces:**
- Consumes: the entry-values table above; the existing `check()` and
  `selftest()` structure in `tools/gen_rules.py`.
- Produces: `--check` green on the migrated registry; `--selftest` green
  with five new red cases.

- [ ] **Step 0: Capture the pre-migration baseline**

A migration that must change nothing outside the registry diffs against a
baseline, never against constants remembered at plan-writing time:

```bash
{
  python3 tools/gen_rules.py --check
  uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
  python3 tools/check_pack_consistency.py
  python3 tools/run_tool_tests.py
  python3 tools/run_benchmark.py
  python3 tools/benchmark_evidence.py
} > /tmp/registry-migration-baseline.txt 2>&1; echo "baseline rc=$? (expected 0)"
```

Expected: exit 0, and the file holds the current green outputs. The only
fact hardcoded anywhere in this plan is 22 fault classes — the number this
migration itself owns.

- [ ] **Step 1: Add the fault-field validation to `gen_rules.py`**

In the `check()` function, after the existing fault-detector loop
(`for f in reg.get("faults", [])` at ~line 191), add:

```python
    LEVELS = {"matrix", "implementation", "none"}
    OBS = {"high", "medium", "low", "n/a"}
    for f in reg.get("faults", []):
        fid = f.get("id", "?")
        level = f.get("level")
        if level not in LEVELS:
            errors.append(f"fault {fid}: level missing or not in {sorted(LEVELS)}")
        obs = f.get("observability")
        if obs not in OBS:
            errors.append(f"fault {fid}: observability missing or not in {sorted(OBS)}")
        if level in LEVELS:
            if level == "implementation":
                if obs == "n/a":
                    errors.append(f"fault {fid}: implementation class with observability n/a")
                if not f.get("precondition"):
                    errors.append(f"fault {fid}: implementation class without precondition")
            else:
                if obs != "n/a":
                    errors.append(f"fault {fid}: {level} class must have observability n/a")
                if "precondition" in f:
                    errors.append(f"fault {fid}: {level} class must not carry precondition")
            if level == "none" and not f.get("none_reason"):
                errors.append(f"fault {fid}: none class without none_reason")
            if level != "none" and "none_reason" in f:
                errors.append(f"fault {fid}: {level} class must not carry none_reason")
```

- [ ] **Step 2: Red probe — run the validation on the unmigrated registry**

```bash
python3 tools/gen_rules.py --check
```

Expected: nonzero exit with 22+ errors listing missing `level` fields.
This proves the validation works and that migration is required. Paste the
output into the commit body as the red probe.

- [ ] **Step 3: Migrate all 22 fault entries**

In `formats/rules.toml`, append the fields from the Entry Values table to
each `[[faults]]` entry, directly after its `binder` line (or after `name`
where no binder exists). Example shape:

```toml
[[faults]]
id = "F-01"
name = "missing transition"
binder = "missing-transition"
level = "matrix"
observability = "n/a"

[[faults]]
id = "F-05"
name = "corrupt state"
binder = "corrupt-state"
level = "implementation"
observability = "high"
precondition = "counter or context variable projected by the suite"

[[faults]]
id = "F-06"
name = "trap door"
binder = "trap-door"
level = "none"
observability = "n/a"
none_reason = "undocumented entry/exit paths are found by matrix totality (PA-14 round-tripping), not by code mutation"
```

Values come ONLY from the Entry Values table — no reinterpretation.

- [ ] **Step 4: Green check against the baseline, not against constants**

```bash
python3 tools/gen_rules.py --check
python3 tools/check_pack_consistency.py
```

Expected: `RULES REGISTRY: OK` with `0 warnings` — the only count asserted
verbatim is `22 fault classes`, which this migration owns. Every other
number is proven by the Step 6 baseline diff, not stated here.

Also verify no rendered output changed:

```bash
git diff --stat -- prompts/00-methods-reference.md prompts/02-pilot.md AGENTS.md README.md
```

Expected: empty diff.

- [ ] **Step 5: Add five red selftest cases to `selftest()`**

Following the existing pattern in `tools/gen_rules.py`'s `selftest()`
(which copies the registry into a temp dir, mutates the copy, and expects
failure), add cases after the existing red cases. **Every case resolves
its fault entry by `id`, never by index** — an index test stays green
against the wrong class the moment anyone inserts or reorders entries:

```python
    def fault_by_id(reg, fid):
        return next(f for f in reg["faults"] if f["id"] == fid)

    # red: implementation class without precondition
    broken = _load_tmp(tmp)
    fault_by_id(broken, "F-03").pop("precondition", None)
    expect("implementation without precondition", True, _write_check(tmp, broken),
           "without precondition")

    # red: implementation class with observability n/a
    broken = _load_tmp(tmp)
    fault_by_id(broken, "F-03")["observability"] = "n/a"
    expect("implementation with n/a observability", True, _write_check(tmp, broken),
           "observability n/a")

    # red: matrix class with real observability
    broken = _load_tmp(tmp)
    fault_by_id(broken, "F-01")["observability"] = "high"
    expect("matrix class with observability high", True, _write_check(tmp, broken),
           "must have observability n/a")

    # red: none class without none_reason
    broken = _load_tmp(tmp)
    fault_by_id(broken, "F-06").pop("none_reason", None)
    expect("none class without none_reason", True, _write_check(tmp, broken),
           "without none_reason")

    # red: bad level value
    broken = _load_tmp(tmp)
    fault_by_id(broken, "F-01")["level"] = "both"
    expect("bad level value", True, _write_check(tmp, broken), "not in")

    # red: bad observability value
    broken = _load_tmp(tmp)
    fault_by_id(broken, "F-01")["observability"] = "extreme"
    expect("bad observability value", True, _write_check(tmp, broken), "not in")

    # red: non-implementation class carrying precondition
    broken = _load_tmp(tmp)
    fault_by_id(broken, "F-01")["precondition"] = "leftover from a bad migration"
    expect("matrix class carrying precondition", True, _write_check(tmp, broken),
           "must not carry precondition")

    # red: non-none class carrying none_reason
    broken = _load_tmp(tmp)
    fault_by_id(broken, "F-01")["none_reason"] = "leftover from a bad migration"
    expect("matrix class carrying none_reason", True, _write_check(tmp, broken),
           "must not carry none_reason")
```

Use the selftest's ACTUAL helper names — read them in the file first and
adapt; the snippets show intent, not copy-paste API.

- [ ] **Step 6: Full gate set, proven by baseline diff**

```bash
{
  python3 tools/gen_rules.py --check
  python3 tools/gen_rules.py --selftest
  uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
  python3 tools/check_pack_consistency.py
  python3 tools/run_tool_tests.py
  python3 tools/run_benchmark.py
  python3 tools/benchmark_evidence.py
} > /tmp/registry-migration-after.txt 2>&1; echo "after rc=$? (expected 0)"

diff /tmp/registry-migration-baseline.txt /tmp/registry-migration-after.txt
git diff --check
git status --short
```

Expected: `after rc=0`. The diff shows ONLY additions from the new
selftest red cases and the migration itself — every benchmark, artifact,
and evidence line identical to the baseline. Any other difference is a
finding, not something to reconcile silently.

- [ ] **Step 7: Commit**

```bash
git add formats/rules.toml tools/gen_rules.py \
  docs/superpowers/plans/2026-08-09-fault-class-registry-migration.md
git commit -m "Migrate fault registry to layer-separation schema" \
  -m "All 22 fault entries gain level/observability(/precondition|none_reason); gen_rules enforces closed vocabularies and conditional requirements; eight red selftest cases prove the rules fail on bad input.

Evidence:
- Red probe: gen_rules --check on the unmigrated registry failed listing 22 missing-level errors
- gen_rules --check: RULES REGISTRY: OK (0 warnings, 22 fault classes)
- gen_rules --selftest: OK with 8 new red cases
- Rendered output unchanged (empty diff on 00/02/AGENTS/README)
- Baseline diff: every gate output identical to the pre-migration baseline except the new selftest cases
- git diff --check: OK"
```

- [ ] **Step 8: Stop**

No release, tag, or push without explicit instruction. The next artifact is
the addrConn behavioral suite (separate spec).

## Execution Handoff

Execute only Task 1. The addrConn suite and F-08 operator are separate
specs and need their own approval cycle.
