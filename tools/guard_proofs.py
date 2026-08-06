#!/usr/bin/env python3
"""Guard-proof procedures for disposition-matrix guard groups (z3).

The pack's method requires, per guard group (PA-1/PA-2, 02-pilot
step 4): pairwise disjointness, coverage (or an explicit else), and
boundary probes for every comparison. Per-run `check_guards.py`
scripts used to reimplement this z3 boilerplate per component — the
same duplication check_matrix.py ended for the matrix checks (v1.23).

This module is the shared procedure. A per-run script contributes only
the component-specific part: typed z3 variables, NAT-domain
assumptions, and the guard expressions. It must never reimplement the
proof loop.

    import sys; sys.path.insert(0, "<pack>/tools")
    import guard_proofs, z3

    retry = z3.Int("retryCount")
    nat = [retry >= 0, retry <= 5]                       # NAT domain
    res = guard_proofs.check_group(
        "reconnect-decision",
        [("retry", retry < 5), ("give-up", retry >= 5)],
        assumptions=nat)
    print(guard_proofs.render([res]))                    # guard-results.txt

Dependencies: tools/requirements-dev.txt (z3-solver). A guard that
cannot be formalized never reaches this module — it gets the
`not-formalizable: <category>` mark instead (PA-3b).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GroupResult:
    name: str
    outcome: str                      # "proven" | "violation"
    findings: list[str] = field(default_factory=list)


def _z3():
    try:
        import z3
        return z3
    except ImportError as exc:
        raise SystemExit(
            "guard_proofs needs z3-solver — install the dev dependencies: "
            "pip install -r tools/requirements-dev.txt "
            "(or: uv run --with-requirements tools/requirements-dev.txt ...)"
        ) from exc


def _witness(model, decls_of_interest) -> str:
    parts = []
    for d in model.decls():
        if not decls_of_interest or d.name() in decls_of_interest:
            parts.append(f"{d.name()}={model[d]}")
    return ", ".join(sorted(parts)) or "<any assignment>"


def check_group(name: str, guards, assumptions=(), has_else: bool = False) -> GroupResult:
    """Prove PA-1 (pairwise disjointness) and PA-2 (coverage) for one
    guard group under the declared NAT assumptions.

    guards: list of (label, z3.BoolRef) pairs.
    assumptions: iterable of z3.BoolRef (the NAT domain).
    has_else: True when the code has an explicit else branch — coverage
    is then discharged by construction and only disjointness is proven.
    """
    z3 = _z3()
    findings: list[str] = []

    # PA-1: every pair unsatisfiable together
    for i in range(len(guards)):
        for j in range(i + 1, len(guards)):
            (la, ga), (lb, gb) = guards[i], guards[j]
            s = z3.Solver()
            s.add(*assumptions)
            s.add(ga, gb)
            if s.check() == z3.sat:
                findings.append(
                    f"PA-1 overlap: {la!r} and {lb!r} both fire "
                    f"(witness: {_witness(s.model(), None)}) — order decides")

    # PA-2: the disjunction covers the domain, or an explicit else exists
    if not has_else:
        s = z3.Solver()
        s.add(*assumptions)
        s.add(z3.Not(z3.Or(*[g for _, g in guards])))
        if s.check() == z3.sat:
            findings.append(
                f"PA-2 gap: no guard fires "
                f"(witness: {_witness(s.model(), None)}) — hole, or add an "
                f"explicit else and pass has_else=True with a citation")

    return GroupResult(name=name,
                       outcome="violation" if findings else "proven",
                       findings=findings)


def boundary_probe(guards, assignments) -> list[tuple[dict, list[str]]]:
    """Evaluate which guard labels fire for concrete assignments —
    below, exactly at, and above every comparison limit (02-pilot
    step 4c). assignments: list of {z3-const: python value} dicts.
    Returns [(assignment, [labels that fire]), ...] for the report.
    """
    z3 = _z3()

    def lift(v):
        if isinstance(v, bool):
            return z3.BoolVal(v)
        if isinstance(v, int):
            return z3.IntVal(v)
        if isinstance(v, float):
            return z3.RealVal(v)
        return v  # already a z3 expr

    rows = []
    for a in assignments:
        subs = [(var, lift(val)) for var, val in a.items()]
        labels = [label for label, g in guards
                  if z3.is_true(z3.simplify(z3.substitute(g, *subs)))]
        rows.append(({str(k): v for k, v in a.items()}, labels))
    return rows


def render(results) -> str:
    """guard-results.txt format: one outcome line per group, findings
    indented. not-formalizable groups are appended by the per-run
    script itself (they never reach z3)."""
    lines = []
    for r in results:
        lines.append(f"group {r.name}: {r.outcome}")
        lines.extend(f"  - {f}" for f in r.findings)
    return "\n".join(lines)
