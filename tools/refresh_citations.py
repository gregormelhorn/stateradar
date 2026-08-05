#!/usr/bin/env python3
"""Refresh file:line citations in analysis artifacts after code moved.

The 06-reconcile step 3 duty: every `observed-in-code` citation must
re-resolve at HEAD. Implementations shift lines constantly (dobby
trigger-service: 183 citations drifted after one DR implementation
pass). Hand-refreshing is the error-prone path; this tool does it
mechanically and reports what it cannot resolve.

Strategy, per citation `file.py:LINE`:
1. Content anchor: the old file's text at LINE is located in the new
   file (exact match; unique match wins). Language-agnostic.
2. Method map (Python fallback): the citation's owning `def` in the
   old file gives the offset; the same `def`'s line in the new file
   plus the offset wins.
3. Unresolved citations are listed — they are findings for the human,
   never silently dropped or guessed.

Usage:
  python3 tools/refresh_citations.py <analysis-dir> \
      [--from-sha SHA] [--to-sha SHA] [--repo .] [--dry-run]

Defaults: --from-sha = the manifest's analyzedSha, --to-sha = HEAD.
Artifacts scanned: extraction.md, disposition-matrix.md,
event-catalogue.md, adversarial-traces.md, invariants-and-lints.md.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ARTIFACTS = (
    "extraction.md",
    "disposition-matrix.md",
    "event-catalogue.md",
    "adversarial-traces.md",
    "invariants-and-lints.md",
)

CITE_RE = re.compile(r"([A-Za-z_][\w/]*\.py):(\d+)(?:-(\d+))?")


def _git_show(repo: Path, sha: str, path: str) -> list[str] | None:
    r = subprocess.run(
        ["git", "-C", str(repo), "show", f"{sha}:{path}"],
        capture_output=True, text=True,
    )
    return r.stdout.splitlines() if r.returncode == 0 else None


def _method_map(lines: list[str]) -> list[tuple[str, int, int]]:
    """Python `def` boundaries: (name, start, end)."""
    defs = []
    for i, line in enumerate(lines):
        m = re.match(r"\s*(?:async )?def (\w+)", line)
        if m:
            defs.append((m.group(1), i + 1))
    return [
        (name, start, (defs[j + 1][1] - 1 if j + 1 < len(defs) else len(lines)))
        for j, (name, start) in enumerate(defs)
    ]


def _content_anchor(old_lines: list[str], new_lines: list[str], line: int) -> int | None:
    """Find the old line's content in the new file; unique match wins."""
    if line < 1 or line > len(old_lines):
        return None
    needle = old_lines[line - 1].strip()
    if not needle:
        return None
    hits = [i + 1 for i, text in enumerate(new_lines) if text.strip() == needle]
    return hits[0] if len(hits) == 1 else None


def _method_anchor(
    old_lines: list[str], new_lines: list[str], line: int
) -> int | None:
    """Python def-map fallback: owning method + offset."""
    old_map = _method_map(old_lines)
    new_map = {name: (s, e) for name, s, e in _method_map(new_lines)}
    for name, start, end in old_map:
        if start <= line <= end and name in new_map:
            return new_map[name][0] + (line - start)
    return None


def refresh_file(
    artifact: Path, old_getter, new_getter, *, dry_run: bool
) -> tuple[int, list[str]]:
    """Refresh all citations in one artifact. Returns (count, unresolved)."""
    text = artifact.read_text(encoding="utf-8")
    refreshed = 0
    unresolved: list[str] = []
    cache: dict[str, tuple[list[str] | None, list[str] | None]] = {}

    def sources(path: str) -> tuple[list[str] | None, list[str] | None]:
        if path not in cache:
            cache[path] = (old_getter(path), new_getter(path))
        return cache[path]

    def replace(m: re.Match) -> str:
        nonlocal refreshed
        path, l1, l2 = m.group(1), int(m.group(2)), m.group(3)
        old_lines, new_lines = sources(path)
        if not old_lines or not new_lines:
            unresolved.append(f"{path}:{l1} (source unavailable)")
            return m.group(0)
        new_l1 = _content_anchor(old_lines, new_lines, l1)
        if new_l1 is None:
            new_l1 = _method_anchor(old_lines, new_lines, l1)
        if new_l1 is None:
            unresolved.append(f"{path}:{l1}")
            return m.group(0)
        refreshed += 1
        if l2:
            old_span = int(l2) - l1
            return f"{path}:{new_l1}-{new_l1 + old_span}"
        return f"{path}:{new_l1}"

    updated = CITE_RE.sub(replace, text)
    if not dry_run and updated != text:
        artifact.write_text(updated, encoding="utf-8")
    return refreshed, unresolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis_dir", help="e.g. domain-analysis/trigger-service")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--from-sha", default=None)
    parser.add_argument("--to-sha", default="HEAD")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    adir = repo / args.analysis_dir

    # Citations use bare basenames ("service.py:522"); resolve them
    # against the repo's src tree (language-agnostic best effort).
    src_index: dict[str, str] = {}
    src_root = repo / "src"
    if src_root.is_dir():
        for dirpath, _, files in __import__("os").walk(src_root):
            for f in files:
                src_index.setdefault(f, str(Path(dirpath, f).relative_to(repo)))

    def resolve(path: str) -> str:
        if (repo / path).is_file():
            return path
        return src_index.get(Path(path).name, path)

    from_sha = args.from_sha
    if from_sha is None:
        manifest_path = adir / "manifest.json"
        if not manifest_path.is_file():
            print("REFRESH: no manifest.json and no --from-sha", file=sys.stderr)
            return 2
        from_sha = json.loads(manifest_path.read_text())["analyzedSha"]

    old_getter = lambda p: _git_show(repo, from_sha, resolve(p))  # noqa: E731
    new_getter = (
        (lambda p: _git_show(repo, args.to_sha, resolve(p)))
        if args.to_sha != "WORKTREE"
        else (
            lambda p: (repo / resolve(p)).read_text().splitlines()
            if (repo / resolve(p)).is_file()
            else None
        )
    )

    total = 0
    all_unresolved: list[str] = []
    for name in ARTIFACTS:
        artifact = adir / name
        if not artifact.is_file():
            continue
        count, unresolved = refresh_file(artifact, old_getter, new_getter, dry_run=args.dry_run)
        total += count
        all_unresolved.extend(f"{name}: {u}" for u in unresolved)
        if count:
            print(f"{name}: {count} citations refreshed")

    print(f"REFRESH: {total} citations refreshed "
          f"({'dry run' if args.dry_run else 'written'})")
    if all_unresolved:
        print(f"REFRESH: {len(all_unresolved)} UNRESOLVED — human review needed:")
        for u in all_unresolved:
            print(" -", u)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
