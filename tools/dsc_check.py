#!/usr/bin/env python3
"""Pack-shipped analysis checker. The agent emits data (analysis.json);
the pack verifies it. Replaces the generic parts of per-run checkers.

Usage:
  python3 tools/dsc_check.py <analysis-dir> [--repo ROOT] [--model FILE.mmd]

Checks: grid totality, disposition vocabulary, hole->Q mapping, DR links,
pair traces, guard outcomes, coverage-table totality, behavioural-DR
reverse coverage, question statuses, Mermaid<->matrix sync, fragment
citations, and manifest staleness (git). Exit 0 = OK, 1 = violations.
"""
from __future__ import annotations
import json, re, subprocess, sys
from functools import lru_cache
from pathlib import Path

VOCAB = {"transition", "handle", "ignore (documented)", "ignore (accidental)",
         "defer (queued)", "reject", "UNSPECIFIED"}
HOLES = {"UNSPECIFIED", "ignore (accidental)"}

# The undesired-variant categories come from the rules registry
# (formats/rules.toml, uv_categories[].key) so the coverage check and
# the 02-pilot checklist cannot drift apart. The literal list is the
# fallback for interpreters without tomllib (< 3.11) or a stripped-down
# vendored copy without the registry.
CATEGORIES = ["loss", "delay", "duplication", "out-of-order", "contradiction",
              "commission", "value"]
_registry = Path(__file__).resolve().parent.parent / "formats" / "rules.toml"
if _registry.exists():
    try:
        import tomllib
        CATEGORIES = [c["key"] for c in
                      tomllib.loads(_registry.read_text(encoding="utf-8"))
                      ["uv_categories"]]
    except ImportError:
        pass
GUARD_OUTCOMES = {"proven", "violation", "not-formalizable"}
NF_REASONS = ("external-call", "dynamic-state", "clock", "unstructured-payload")
Q_STATUS = {"OPEN", "ANSWERED", "RESOLVED", "CONFLICT"}

def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__); return 2
    adir = Path(args[0])
    repo = Path(args[args.index("--repo") + 1]) if "--repo" in args else None
    model = adir / args[args.index("--model") + 1] if "--model" in args else None
    errors: list[str] = []
    E = errors.append

    sidecar = adir / "analysis.json"
    if not sidecar.is_file():
        print(f"DSC CHECK: no analysis.json in {adir}")
        print("  Emit the sidecar (02-pilot step 4 / 06-reconcile step 4) —")
        print("  tools/gen_analysis_sidecar.py generates it from the disposition matrix.")
        return 2
    data = json.loads(sidecar.read_text(encoding="utf-8"))

    # Contract validation: execute the schema, do not just ship it.
    # Degrading to structural-only checks is a real reduction in coverage,
    # so it must be chosen (--allow-no-schema), never silently inherited
    # from whichever interpreter happened to run the checker.
    schema_path = Path(__file__).resolve().parent.parent / "formats" / "analysis.schema.json"
    if schema_path.exists():
        try:
            import jsonschema
            v = jsonschema.Draft202012Validator(json.loads(schema_path.read_text()))
            for err in sorted(v.iter_errors(data), key=str):
                E(f"schema: {'/'.join(str(x) for x in err.path) or '<root>'}: {err.message}")
        except ImportError:
            if "--allow-no-schema" not in args:
                print("DSC CHECK: FAIL\n - jsonschema is not installed, so the sidecar "
                      "contract cannot be validated.\n   Install it (uv run --with jsonschema "
                      "python3 tools/dsc_check.py ...) or\n   pass --allow-no-schema to accept "
                      "structural checks only.")
                return 1
            print("note: jsonschema not installed - structural checks only", file=sys.stderr)
    states = data["states"]
    events = [e["id"] for e in data["events"]]
    qids = {q["id"] for q in data.get("questions", [])}

    # Grid totality + vocabulary + targets
    seen: dict[tuple[str, str], int] = {}
    for c in data["cells"]:
        key = (c["state"], c["event"])
        seen[key] = seen.get(key, 0) + 1
        if c["disposition"] not in VOCAB:
            E(f"cell {key}: unknown disposition {c['disposition']!r}")
        if c["disposition"] == "transition" and c.get("target") not in states:
            E(f"cell {key}: transition target {c.get('target')!r} is not a state")
        if c["disposition"] in HOLES and c.get("q") not in qids:
            E(f"cell {key}: hole without a valid Q reference")
        if c["disposition"] in {"ignore (documented)", "reject", "defer (queued)"}:
            if not (c.get("dr") or c.get("citation")):
                E(f"cell {key}: {c['disposition']} needs a DR or a citation")
            # PA-18 terminal states: auto-generated cells carry a sentinel
            # citation and don't need a real file:line reference.
            elif (c.get("citation", {}).get("fragment") == "terminal state declaration"
                  and not c.get("dr")):
                pass  # auto-generated terminal state cell — implicit citation
    for s in states:
        for ev in events:
            n = seen.get((s, ev), 0)
            if n != 1:
                E(f"grid: ({s}, {ev}) has {n} cells, expected exactly 1")

    # Asserted absence: an empty or missing section is only OK when the
    # sidecar says so with a reason.  Silence used to read as success —
    # an agent that skipped guard proofs, pair traces, and the coverage
    # table got a green check (the exact failure the pack exists to stop).
    completeness = data.get("completeness", {})
    for section in ("pairs", "guardGroups", "coverage"):
        if data.get(section):
            continue
        stated = completeness.get(section)
        if not stated:
            E(f"{section}: empty or absent, and completeness.{section} does not "
              f"say why — assert the absence (count: 0, reason: ...) or emit the section")

    # Pairs, guard groups, coverage table, questions
    for p in data.get("pairs", []):
        if not p.get("trace"):
            E(f"pair {p.get('id')}: no trace")
    for g in data.get("guardGroups", []):
        if g.get("outcome") not in GUARD_OUTCOMES:
            E(f"guard group {g.get('id')}: outcome {g.get('outcome')!r} invalid")
            continue
        if g["outcome"] == "not-formalizable":
            reason = g.get("reason") or ""
            if not reason.startswith(NF_REASONS):
                E(f"guard group {g.get('id')}: not-formalizable needs a reason "
                  f"starting with one of {NF_REASONS} — the outcome is a "
                  f"judgment call, the category makes it reviewable")
    for src, cats in data.get("coverage", {}).items():
        for cat in CATEGORIES:
            v = cats.get(cat)
            if v is None or v == [] or v == "":
                E(f"coverage: {src}/{cat} is empty (variant ids or 'n/a: reason')")
    for q in data.get("questions", []):
        if q.get("status", "").split(" ")[0] not in Q_STATUS:
            E(f"question {q.get('id')}: status {q.get('status')!r} invalid")

    # Question lifecycle: a RESOLVED question must have a DR link in at
    # least one cell.  An answered question without a recorded decision
    # is a decision that can be lost (gobreaker #72, 2026-08-06).
    for q in data.get("questions", []):
        if q.get("status", "").startswith("RESOLVED"):
            linked = any(
                c.get("q") == q["id"] and c.get("dr")
                for c in data["cells"]
            )
            if not linked:
                E(f"question {q['id']}: RESOLVED but no cell links a DR — "
                  f"add a decision record reference to the cell")

    # ODC fields (fault/trigger) on questions.
    # When present, validate fault ids against the catalogue and trigger
    # against the closed vocabulary in formats/rules.toml [vocab].odc_triggers.
    if any(q.get("fault") or q.get("trigger") for q in data.get("questions", [])):
        try:
            import tomllib
            reg = tomllib.loads(_registry.read_text())
            fault_ids = {f["id"] for f in reg.get("faults", [])}
            trigger_vocab = set(reg.get("vocab", {}).get("odc_triggers", []))
        except Exception:
            fault_ids = set()
            trigger_vocab = set()
        for q in data.get("questions", []):
            for f_id in q.get("fault", []):
                if f_id not in fault_ids:
                    E(f"question {q['id']}: unknown fault class {f_id}")
            trigger = q.get("trigger", "")
            if trigger and trigger not in trigger_vocab:
                E(f"question {q['id']}: trigger {trigger!r} not in ODC trigger vocabulary")

    # R-GATE-TYPE + R-UPSTREAM-GUARD: presence check on base events
    # (undesired variants inherit from their base event).
    for ev in data.get("events", []):
        if ev.get("undesired"):
            continue  # UV events inherit gate/guard from their base
        if not ev.get("gate"):
            E(f"event {ev['id']}: missing gate-type annotation (R-GATE-TYPE)")
        if not ev.get("upstream_guards"):
            E(f"event {ev['id']}: missing upstream-guard annotation (R-UPSTREAM-GUARD)")

    # PA-22 doctrine-line mapping. The doc-ids declaration in
    # invariants-and-lints.md is the universe; every declared DOC-n
    # must map (sidecar docLines) to an existing cell, an invariant/
    # constraint, or an explicit rejection with a reason. An unmapped
    # doctrine line is an error; a mapped hole cell is a finding the
    # hole→Q machinery already carries, not a checker failure.
    inv_path = adir / "invariants-and-lints.md"
    if inv_path.is_file():
        inv_text = inv_path.read_text(encoding="utf-8")
        decl = re.search(r"<!-- doc-ids: (.+?) -->", inv_text)
        if decl:
            declared = decl.group(1).split()
            mapped = {d.get("id"): d for d in data.get("docLines", [])}
            for did in declared:
                d = mapped.get(did)
                if d is None:
                    E(f"doctrine: {did} declared but not mapped "
                      f"(docLines) — an unmapped doctrine line is an error (PA-22)")
                    continue
                kind = d.get("mapping")
                tgt = d.get("target", "")
                if kind == "cell":
                    m = re.fullmatch(r"(.+?)\s+x\s+(\S+)", tgt)
                    if not m or m.group(1).strip() not in states \
                            or m.group(2).strip() not in events:
                        E(f"doctrine: {did} maps to cell {tgt!r} which is "
                          f"not in the grid")
                elif kind in ("invariant", "constraint"):
                    if not re.match(r"(SYS|NAT)", tgt):
                        E(f"doctrine: {did} maps to {kind} {tgt!r} — "
                          f"expected a SYS-/NAT- id")
                elif kind == "guard":
                    if not re.match(r"G-\d", tgt):
                        E(f"doctrine: {did} maps to guard {tgt!r} — "
                          f"expected a G-nn guard-group id")
                elif kind in ("rejected", "structural"):
                    if len(tgt) < 10:
                        E(f"doctrine: {did} {kind} without a reviewable "
                          f"reason")
                else:
                    E(f"doctrine: {did} has unknown mapping {kind!r}")
            for did in mapped:
                if did not in declared:
                    E(f"doctrine: {did} mapped but not declared in doc-ids")

    # Behavioural-DR reverse coverage
    cited = {c.get("dr") for c in data["cells"] if c.get("dr")}
    for dr in data.get("behaviouralDrs", []):
        if dr not in cited:
            E(f"behavioural {dr}: cited by no matrix cell")

    # Mermaid <-> matrix sync.  State ids may carry spaces (compound row
    # labels, 'fam leaf'); a \w+ pattern silently never matched them, so
    # the check was dead for exactly the most complex matrices.  Mermaid
    # ends the edge at ':' (the label) — everything before it is the id.
    if model and model.exists():
        text = model.read_text(encoding="utf-8")
        # Track the enclosing 'state fam { ... }' container so edges written
        # with bare leaf names resolve to the matrix's 'fam leaf' labels.
        def qualify(name: str, fam: str | None) -> str:
            """A bare leaf inside 'state fam { ... }' is the matrix's 'fam leaf'."""
            name = name.strip()
            if fam and name != "[*]" and f"{fam} {name}" in states:
                return f"{fam} {name}"
            return name

        def expand(name: str) -> set[str]:
            """A container stands for every leaf row beneath it."""
            leaves = {s for s in states if s.startswith(f"{name} ")}
            return leaves or {name}

        edges: set[tuple[str, str]] = set()
        containers: list[str] = []
        stack: list[str] = []
        for line in text.splitlines():
            opened = re.match(r"\s*state\s+\"?([\w -]+?)\"?\s*(?:as\s+(\w+)\s*)?\{", line)
            if opened:
                fam = (opened.group(2) or opened.group(1)).strip()
                stack.append(fam)
                containers.append(fam)
                continue
            if line.strip() == "}":
                if stack:
                    stack.pop()
                continue
            # Allow hyphens in state names (e.g. Closed_Idle, Open_Unstable).
            # The previous class [^:\-\n] excluded hyphens, silently dropping
            # every hyphenated state from the diagram (recws, 2026-08-06).
            m = re.match(r"\s*([^:\n]+?)\s*-->\s*([^:\n]+?)\s*(?::|$)", line)
            if m:
                enclosing = stack[-1] if stack else None
                edges.add((qualify(m.group(1), enclosing), qualify(m.group(2), enclosing)))
        mstates = {a for a, _ in edges} | {b for _, b in edges}
        mstates = {s for s in mstates if s != "[*]"}
        # A container covers its leaves, for presence and edge inheritance.
        for container in containers:
            mstates |= expand(container)
        inherited = {(a, b) for src, dst in edges
                     for a in expand(src) for b in expand(dst)}
        edges |= inherited
        missing = set(states) - mstates
        if missing:
            E(f"model sync: states missing from diagram: {sorted(missing)}")
        for c in data["cells"]:
            if c["disposition"] == "transition" and c["state"] in states:
                if (c["state"], c["target"]) not in edges and c["state"] != c["target"]:
                    E(f"model sync: no edge {c['state']} --> {c['target']} for cell ({c['state']}, {c['event']})")

    # Fragment citations (file reads cached: the profiler, not the compiler)
    @lru_cache(maxsize=None)
    def _lines(path: str) -> tuple[str, ...] | None:
        f = repo / path
        if not f.exists():
            return None
        return tuple(f.read_text(encoding="utf-8", errors="replace").splitlines())

    if repo:
        for c in data["cells"]:
            cit = c.get("citation")
            if not cit:
                continue
            cached = _lines(cit["file"])
            if cached is None:
                E(f"citation: {cit['file']} does not exist"); continue
            lines = list(cached)
            lo = max(0, cit["line"] - 4); hi = min(len(lines), cit["line"] + 3)
            window = "\n".join(lines[lo:hi])
            if cit.get("fragment") and cit["fragment"] not in window:
                E(f"citation: fragment {cit['fragment']!r} not near {cit['file']}:{cit['line']}")

    # Referential integrity: every cited DR exists as a decision file.
    ddir = adir / "decisions"
    if ddir.is_dir():
        have = {f.stem for f in ddir.glob("DR-*.yaml")}
        for dr in sorted(cited | set(data.get("behaviouralDrs", []))):
            if dr not in have:
                E(f"decisions: {dr} is cited but {dr}.yaml does not exist")

    # Staleness (manifest + git).  Key discipline: an empty or
    # wrongly-cased watchPaths runs the diff UNFILTERED and false-stales
    # everything — fail loudly instead (dobby session, 2026-08-05).
    mf = adir / "manifest.json"
    m: dict = {}
    if mf.exists():
        m = json.loads(mf.read_text(encoding="utf-8"))
        for key in ("component", "watchPaths", "analyzedSha"):
            if key not in m:
                E(f"manifest: required key {key!r} missing")
        if "watch_paths" in m and "watchPaths" not in m:
            E("manifest: key is 'watch_paths' (snake_case) — the pack key is "
              "camelCase 'watchPaths'; rename it (empty lookups skip the path filter)")
        if "watchPaths" in m and not m["watchPaths"]:
            E("manifest: watchPaths is empty — the staleness diff would run unfiltered")
    if repo and mf.exists() and m.get("watchPaths") and "watch_paths" not in m:
        sha = m.get("analyzedSha", "WORKTREE")
        if sha != "WORKTREE":
            try:
                out = subprocess.run(
                    ["git", "-C", str(repo), "diff", "--name-only", f"{sha}..HEAD", "--"]
                    + m.get("watchPaths", []),
                    capture_output=True, text=True, check=True).stdout.strip()
                if out:
                    E("stale: watched paths changed since analyzedSha:\n  " + out.replace("\n", "\n  "))
            except subprocess.CalledProcessError as ex:
                E(f"staleness check failed: {ex.stderr.strip()}")

    if errors:
        print("DSC CHECK: FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print(f"DSC CHECK: OK ({len(states)} states x {len(events)} events, "
          f"{len(data['cells'])} cells, {len(data.get('guardGroups', []))} guard groups)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
