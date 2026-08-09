#!/usr/bin/env python3
"""
Deterministic generator for golden-mini implementation variant files from a
component-local binding file (mutant-generation.json).

Usage:
  python3 tools/gen_mutant_variants.py <analysis-dir>
  python3 tools/gen_mutant_variants.py --check <analysis-dir>

Behavior:
- Loads tests/golden-mini/domain-analysis/mini/mutant-generation.json
- Resolves component root from workingDirectory relative to the config file
- Validates 1:1 id/path against fault-mutants.json for each binding
- Supports only mode = "replace-block" with exact single-match requirement
- In generate mode: writes variant files; prints GENERATED lines and summary
- In check mode: compares would-be output to tracked files; prints OK/DRIFT
- BLOCKED when a binding declares requiresProjection not found in projections

Exit codes:
- 0 when no drift/blocked/errors
- 1 otherwise
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"CONFIG ERROR: missing file {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"CONFIG ERROR: cannot parse {path}: {e}", file=sys.stderr)
        sys.exit(1)


def find_block(lines: List[str], match_block: List[str]) -> Tuple[int, int]:
    """
    Contiguous line-window equality (no stripping beyond newline):
    Return (start, end_exclusive) indices where match_block occurs exactly once.
    Raise ValueError with message 'matches=N' when N != 1.
    """
    n = len(lines)
    m = len(match_block)
    matches = []
    for i in range(0, n - m + 1):
        if lines[i:i + m] == match_block:
            matches.append(i)
    if len(matches) != 1:
        raise ValueError(f"matches={len(matches)}")
    start = matches[0]
    return start, start + m


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("analysis_dir", help="Path to component analysis dir (contains mutant-generation.json)")
    ap.add_argument("--check", action="store_true", help="Check mode: do not write; compare generated to tracked files")
    args = ap.parse_args(argv)

    analysis_dir = Path(args.analysis_dir).resolve()
    gen_cfg_path = analysis_dir / "mutant-generation.json"
    fm_path = analysis_dir / "fault-mutants.json"

    cfg = load_json(gen_cfg_path)
    fm = load_json(fm_path)

    # Resolve component root from workingDirectory relative to config location
    wd = cfg.get("workingDirectory")
    if not isinstance(wd, str):
        print("CONFIG ERROR: workingDirectory must be a string", file=sys.stderr)
        return 1
    component_root = (gen_cfg_path.parent / wd).resolve()

    source_rel = cfg.get("source")
    if not isinstance(source_rel, str):
        print("CONFIG ERROR: source must be a string", file=sys.stderr)
        return 1
    source_path = (component_root / source_rel).resolve()
    if not source_path.is_file():
        print(f"CONFIG ERROR: source file missing: {source_path}", file=sys.stderr)
        return 1

    # Build fault-mutants id→variant map
    mutants = fm.get("mutants")
    if not isinstance(mutants, list):
        print("CONFIG ERROR: fault-mutants.json: mutants must be a list", file=sys.stderr)
        return 1
    id_to_variant: Dict[str, str] = {}
    for i, m in enumerate(mutants):
        if not isinstance(m, dict):
            print(f"CONFIG ERROR: fault-mutants.json mutant {i}: must be object", file=sys.stderr)
            return 1
        mid = m.get("id")
        var = m.get("variant")
        if not isinstance(mid, str) or not isinstance(var, str):
            print(f"CONFIG ERROR: fault-mutants.json mutant {i}: id/variant must be strings", file=sys.stderr)
            return 1
        id_to_variant[mid] = var

    # Projections catalog (for BLOCKED checks)
    projections = cfg.get("projections", {})
    if not isinstance(projections, dict):
        print("CONFIG ERROR: projections must be an object when present", file=sys.stderr)
        return 2
    # Validate projection canaries (provenBy must resolve to a known mutant id when present)
    for pname, pval in projections.items():
        if not isinstance(pval, dict):
            print(f"CONFIG ERROR: projection {pname}: must be an object", file=sys.stderr)
            return 2
        if 'provenBy' in pval:
            pb = pval.get('provenBy')
            if not isinstance(pb, str) or not pb or pb not in {m.get('id') for m in mutants if isinstance(m, dict)}:
                print(f"CONFIG ERROR: projection {pname}: provenBy {pb!r} not found in fault-mutants.json", file=sys.stderr)
                return 2

    bindings = cfg.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        print("CONFIG ERROR: bindings must be a non-empty array", file=sys.stderr)
        return 1

    # Duplicate binding IDs and duplicate output paths are hard failures.
    seen_ids: Dict[str, int] = {}
    seen_variants: Dict[str, int] = {}
    duplicate_error = False
    for b in bindings:
        if not isinstance(b, dict):
            continue
        bid = b.get("id")
        bvar = b.get("variant")
        if isinstance(bid, str) and bid:
            seen_ids[bid] = seen_ids.get(bid, 0) + 1
        if isinstance(bvar, str) and bvar:
            seen_variants[bvar] = seen_variants.get(bvar, 0) + 1
    for bid, count in seen_ids.items():
        if count > 1:
            print(f"CONFIG ERROR: duplicate binding id {bid} (occurrences={count})", file=sys.stderr)
            duplicate_error = True
    for bvar, count in seen_variants.items():
        if count > 1:
            print(f"CONFIG ERROR: duplicate output path {bvar} (occurrences={count})", file=sys.stderr)
            duplicate_error = True
    if duplicate_error:
        print("MUTANT GENERATION: FAIL (checked=0 drift=0 blocked=0 errors=1)"
              if args.check else
              "MUTANT GENERATION: FAIL (generated=0 drift=0 blocked=0 errors=1)")
        return 2

    # Load pristine source once
    source_text = source_path.read_text(encoding="utf-8")
    # Keep both keepends and stripped variants for robust matching
    src_lines_keep = source_text.splitlines(keepends=True)
    src_lines_stripped = [l[:-1] if l.endswith("\n") else l for l in src_lines_keep]

    generated = 0
    checked = 0
    drift = 0
    blocked = 0
    config_errors = 0

    for b in bindings:
        if not isinstance(b, dict):
            print("CONFIG ERROR: binding: not an object", file=sys.stderr)
            config_errors += 1
            continue
        mid = b.get("id")
        variant_rel = b.get("variant")
        mode = b.get("mode")
        fault = b.get("fault")
        binder = b.get("binder")
        cell = b.get("cell")
        requires_proj = b.get("requiresProjection")
        match_block = b.get("match")
        replace_block = b.get("replace")

        # Basic field validation
        required_fields = [("id", mid), ("variant", variant_rel), ("mode", mode), ("fault", fault), ("binder", binder), ("cell", cell)]
        missing = [name for name, val in required_fields if not isinstance(val, str) or not val]
        if missing:
            print(f"CONFIG ERROR: binding {mid or '?'}: missing/invalid fields {missing}", file=sys.stderr)
            config_errors += 1
            continue
        if mode != "replace-block":
            print(f"CONFIG ERROR: binding {mid}: unsupported mode {mode}", file=sys.stderr)
            config_errors += 1
            continue
        if not isinstance(match_block, list) or not all(isinstance(x, str) for x in match_block):
            print(f"CONFIG ERROR: binding {mid}: match must be string array", file=sys.stderr)
            config_errors += 1
            continue
        if not isinstance(replace_block, list) or not all(isinstance(x, str) for x in replace_block):
            print(f"CONFIG ERROR: binding {mid}: replace must be string array", file=sys.stderr)
            config_errors += 1
            continue

        # ID/path agreement with fault-mutants.json
        fm_variant_rel = id_to_variant.get(mid)
        if fm_variant_rel is None:
            print(f"CONFIG ERROR: binding {mid}: not found in fault-mutants.json", file=sys.stderr)
            config_errors += 1
            continue
        if fm_variant_rel != variant_rel:
            print(f"CONFIG ERROR: binding {mid}: variant path mismatch vs fault-mutants.json ({variant_rel} != {fm_variant_rel})", file=sys.stderr)
            config_errors += 1
            continue

        # BLOCKED projection check
        if requires_proj:
            if not isinstance(requires_proj, str) or not requires_proj:
                print(f"CONFIG ERROR: binding {mid}: requiresProjection must be a non-empty string when present", file=sys.stderr)
                config_errors += 1
                continue
            if requires_proj not in projections:
                print(f"BLOCKED {mid} projection {requires_proj} undeclared")
                blocked += 1
                if args.check:
                    checked += 1
                continue

        # Perform replace-block on pristine source lines (compare on stripped)
        match_lines_stripped = match_block[:]
        try:
            start, end = find_block(src_lines_stripped, match_lines_stripped)
        except ValueError as e:
            print(f"CONFIG ERROR: binding {mid}: {str(e)} in source {source_rel}", file=sys.stderr)
            config_errors += 1
            continue

        # Build replacement with newline endings (assume consistent \n endings)
        replace_keep = [s + "\n" for s in replace_block]
        new_lines = src_lines_keep[:start] + replace_keep + src_lines_keep[end:]
        generated_text = "".join(new_lines)

        variant_path = (component_root / variant_rel).resolve()
        if args.check:
            checked += 1
            if not variant_path.is_file():
                print(f"DRIFT {mid} {variant_rel} (missing tracked file)")
                drift += 1
            else:
                tracked = variant_path.read_text(encoding="utf-8")
                if tracked != generated_text:
                    print(f"DRIFT {mid} {variant_rel}")
                    drift += 1
                else:
                    print(f"OK {fault} {mid}")
        else:
            ensure_parent_dir(variant_path)
            variant_path.write_text(generated_text, encoding="utf-8", newline="\n")
            print(f"GENERATED {fault} {mid} -> {variant_rel}")
            generated += 1

    # Report unbound mutants (hand-authored variants like F-04)
    bound_ids = {b.get('id') for b in bindings if isinstance(b, dict)}
    for mid, var in id_to_variant.items():
        if mid not in bound_ids:
            print(f"UNBOUND {mid} {var} (hand-authored)")

    # Summary
    verdict = 'OK' if (drift == 0 and blocked == 0 and config_errors == 0) else 'FAIL'
    if args.check:
        print(f"MUTANT GENERATION: {verdict} (checked={checked} drift={drift} blocked={blocked} errors={config_errors})")
    else:
        print(f"MUTANT GENERATION: {verdict} (generated={generated} drift={drift} blocked={blocked} errors={config_errors})")

    if config_errors > 0:
        return 2
    return 0 if (drift == 0 and blocked == 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
