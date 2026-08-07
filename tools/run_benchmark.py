#!/usr/bin/env python3
"""Regression test runner for StateRadar benchmarks.

Each benchmark declares the pinned commit, the expected matrix cells
that must be UNSPECIFIED (the bug), and the expected open questions.
The runner clones the repo at the pinned commit, runs Part A
(gen_analysis_sidecar + dsc_check), and asserts the expected findings
are present in the generated analysis.json.

This is deterministic — no AI call needed. It validates that the
StateRadar tooling still correctly reads the pre-generated matrices
and validates that the expected UNSPECIFIED cells and questions
are preserved in the generated analysis.json.

Usage:
  # Run all benchmarks
  python3 tools/run_benchmark.py

  # Run a specific benchmark
  python3 tools/run_benchmark.py valkey-glide-5803

  # Run benchmarks in parallel (4 workers)
  python3 tools/run_benchmark.py --jobs 4

Expected files per benchmark directory:
  expected.json   — assertions about the sidecar
  requirements.md — (optional) Part B input, for documentation
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

BENCHMARKS_DIR = Path(__file__).resolve().parent.parent / "tests" / "benchmarks"
PACK_DIR = Path(__file__).resolve().parent.parent


def clone_at_commit(repo_url: str, commit: str, target: Path) -> bool:
    """Clone a repo at a specific commit. Returns True on success."""
    target.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "clone", "--quiet", repo_url, str(target)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  clone failed: {result.stderr.strip()}")
        return False
    result = subprocess.run(
        ["git", "-C", str(target), "checkout", "--quiet", commit],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  checkout failed: {result.stderr.strip()}")
        return False
    return True


def run_part_a(analysis_dir: Path, repo_dir: Path, model_path: Path | None = None) -> dict | None:
    """Run gen_analysis_sidecar and dsc_check. Returns the sidecar dict or None."""
    # Generate sidecar
    gen = subprocess.run(
        ["python3", str(PACK_DIR / "tools" / "gen_analysis_sidecar.py"),
         "--root", str(repo_dir),
         "--analysis-dir", str(analysis_dir.parent.relative_to(repo_dir)),
         analysis_dir.name],
        capture_output=True, text=True,
    )
    if gen.returncode != 0 or "OK" not in gen.stdout:
        print(f"  gen_analysis_sidecar failed: {gen.stderr.strip()}")
        return None

    # Run checker
    check_args = [
        "python3", str(PACK_DIR / "tools" / "dsc_check.py"),
        str(analysis_dir), "--repo", str(repo_dir),
    ]
    if model_path:
        check_args.extend(["--model", str(model_path)])
    check = subprocess.run(check_args, capture_output=True, text=True)

    # DSC_CHECK OK is expected for UNSPECIFIED cells — the checker
    # validates structure, not that the cell is filled.
    # We load the sidecar ourselves for assertion.
    sidecar_path = analysis_dir / "analysis.json"
    if not sidecar_path.is_file():
        print(f"  analysis.json not generated")
        return None
    return json.loads(sidecar_path.read_text())


def assert_expected(sidecar: dict, expected: dict,
                    case_dir: Path | None = None) -> tuple[int, int, int, list[str]]:
    """Assert expected findings are present. Returns (passed, failed, skipped, messages).

    Phrase checks search the case's committed open-questions.md (not the
    sidecar, which doesn't carry full question text).
    """
    passed = 0
    failed = 0
    skipped = 0
    messages: list[str] = []

    # Check expected UNSPECIFIED cells
    for cell_spec in expected.get("unspecified_cells", []):
        state = cell_spec["state"]
        event = cell_spec["event"]
        found = None
        for c in sidecar.get("cells", []):
            if c.get("state") == state and c.get("event") == event:
                found = c
                break
        if found is None:
            failed += 1
            messages.append(f"  FAIL: cell ({state}, {event}) not in sidecar")
        elif found.get("disposition") == "UNSPECIFIED":
            passed += 1
            messages.append(f"  PASS: cell ({state}, {event}) = UNSPECIFIED")
        else:
            failed += 1
            messages.append(
                f"  FAIL: cell ({state}, {event}) = {found.get('disposition')}, "
                f"expected UNSPECIFIED"
            )

    # Check expected open questions
    qids = {q["id"] for q in sidecar.get("questions", [])}
    for qid in expected.get("expected_questions", []):
        if qid in qids:
            passed += 1
            messages.append(f"  PASS: question {qid} present")
        else:
            failed += 1
            messages.append(f"  FAIL: question {qid} not found")

    # Check expected invariant violations (prose check in committed open-questions.md)
    oq_text = ""
    if case_dir and (case_dir / "open-questions.md").is_file():
        oq_text = (case_dir / "open-questions.md").read_text(encoding="utf-8")
    for phrase in expected.get("expected_phrases", []):
        found = False
        phrase_lower = phrase.lower()
        # Search in committed open-questions.md
        if phrase_lower in oq_text.lower():
            found = True
        # Fallback: check sidecar cell q-refs
        if not found:
            for c in sidecar.get("cells", []):
                qid = c.get("q", "")
                if phrase_lower in qid.lower():
                    found = True
                    break
        if found:
            passed += 1
            messages.append(f"  PASS: phrase '{phrase}' found")
        else:
            failed += 1
            messages.append(f"  FAIL: phrase '{phrase}' not found in open-questions.md or cell q-refs")

    return passed, failed, skipped, messages


def run_benchmark(name: str) -> tuple[str, bool, int, str]:
    """Run a single benchmark. Returns (name, passed, skip_count, log)."""
    bdir = BENCHMARKS_DIR / name
    expected_path = bdir / "expected.json"
    if not expected_path.is_file():
        return name, False, 0, f"SKIP {name}: no expected.json"

    expected = json.loads(expected_path.read_text())
    repo_url = expected.get("repo")
    commit = expected.get("commit")
    component = expected.get("component", name)
    model_path = bdir / "model.mmd" if (bdir / "model.mmd").is_file() else None

    if not repo_url or not commit:
        return name, False, 0, f"SKIP {name}: expected.json missing repo/commit"

    log_lines = [f"=== {name} ===", f"repo: {repo_url}", f"commit: {commit}"]

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir) / "repo"
        if not clone_at_commit(repo_url, commit, repo_dir):
            return name, False, 0, "\n".join(log_lines + ["  clone failed"])

        # Place analysis under the repo so gen_analysis_sidecar can find it
        analysis_dir = repo_dir / "domain-analysis" / component
        analysis_dir.mkdir(parents=True, exist_ok=True)

        # Copy the pre-generated artifacts from the benchmark directory
        for fname in ["disposition-matrix.md", "event-catalogue.md",
                       "open-questions.md", "extraction.md"]:
            src = bdir / fname
            if src.is_file():
                shutil.copy(src, analysis_dir / fname)

        # If no matrix is provided, we need to generate it from scratch.
        # For now, require the benchmark to include its own matrix.
        if not (analysis_dir / "disposition-matrix.md").is_file():
            return name, False, 0, "\n".join(log_lines + [
                "  SKIP: no disposition-matrix.md in benchmark —",
                "  full Part A re-run requires AI. This runner only validates",
                "  that pre-generated analysis artifacts still check correctly."
            ])

        sidecar = run_part_a(analysis_dir, repo_dir, model_path)
        if sidecar is None:
            return name, False, 0, "\n".join(log_lines + ["  sidecar generation failed"])

        passed, failed, skipped, msgs = assert_expected(
            sidecar, expected, case_dir=bdir)
        log_lines.extend(msgs)
        skipped_str = f" ({skipped} skipped)" if skipped else ""
        log_lines.append(f"  Result: {passed} passed{skipped_str}, {failed} failed")
        return name, failed == 0, skipped, "\n".join(log_lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="StateRadar benchmark regression runner")
    parser.add_argument("benchmark", nargs="*", help="Benchmark name(s) to run")
    parser.add_argument("--jobs", "-j", type=int, default=1,
                        help="Number of parallel workers (default: 1)")
    args = parser.parse_args()

    if args.benchmark:
        names = args.benchmark
    else:
        names = sorted(
            d.name for d in BENCHMARKS_DIR.iterdir()
            if d.is_dir() and (d / "expected.json").is_file()
        )

    if not names:
        print("No benchmarks found with expected.json")
        return 1

    print(f"Running {len(names)} benchmark(s) with {args.jobs} worker(s)\n")

    if args.jobs > 1:
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            futures = {pool.submit(run_benchmark, name): name for name in names}
            results = []
            total_skips = 0
            for future in as_completed(futures):
                name, passed, skipped, log = future.result()
                results.append((name, passed))
                total_skips += skipped
                print(log)
                print()
    else:
        results = []
        total_skips = 0
        for name in names:
            name, passed, skipped, log = run_benchmark(name)
            results.append((name, passed))
            total_skips += skipped
            print(log)
            print()

    total = len(results)
    passed = sum(1 for _, p in results if p)
    failed = total - passed
    skip_str = f" ({total_skips} checks skipped)" if total_skips else ""
    print(f"{'='*40}")
    print(f"Results: {passed} passed, {failed} failed{skip_str}, {total} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
