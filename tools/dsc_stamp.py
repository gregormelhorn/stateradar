#!/usr/bin/env python3
"""Validate, then stamp the manifest at HEAD (the two-commit antidote).

The reconcile manifest bump kept needing a second commit after every
code change to a watched path (dobby session, 2026-08-05: six times).
This tool runs the pack checker first — a stale bump is forbidden —
and only then pins analyzedSha to HEAD with today's date.

Usage:
  python3 tools/dsc_stamp.py <analysis-dir> [--repo .] [--date YYYY-MM-DD]

Exit 0 = checked and stamped; 1 = the check failed, nothing stamped.
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis_dir")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--date", default=None)
    parser.add_argument("--model", default="as-is.machine.mmd")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    adir = repo / args.analysis_dir
    checker = Path(__file__).resolve().parent / "dsc_check.py"

    cmd = [sys.executable, str(checker), str(adir), "--repo", str(repo)]
    if (adir / args.model).is_file():
        cmd += ["--model", args.model]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        print("DSC STAMP: check failed — manifest NOT stamped", file=sys.stderr)
        return 1

    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    manifest_path = adir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["analyzedSha"] = head
    manifest["date"] = args.date or datetime.date.today().isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"DSC STAMP: {args.analysis_dir} pinned at {head[:8]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
