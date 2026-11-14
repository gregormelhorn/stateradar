#!/usr/bin/env python3
"""Run the P-04a behavior probe against a clean, pinned Pool source snapshot."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

POOL_SHA = "6084537e520652192f41aebfd88d822c00b9447a"
ANCHOR = "\t\tdefault:\n\t\t\tc.mu.Lock()"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pool_repo", type=Path)
    parser.add_argument("--control", action="store_true",
                        help="recheck the idle channel after the hook; the probe should fail")
    args = parser.parse_args()
    snapshot = subprocess.check_output(["git", "archive", POOL_SHA], cwd=args.pool_repo)
    test = Path(__file__).with_name("p04a_test.go")
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp).resolve()
        with tarfile.open(fileobj=io.BytesIO(snapshot)) as archive:
            archive.extractall(root, filter="data")
        (root / test.name).write_bytes(test.read_bytes())
        channel = root / "channel.go"
        source = channel.read_text()
        if source.count(ANCHOR) != 1:
            raise ValueError("expected one Get capacity-lock anchor")
        hook = ["default:", "\t\t\tif beforeGetCapacityLock != nil { beforeGetCapacityLock() }"]
        if args.control:
            hook.append("\t\t\tif len(conns) > 0 { continue }")
        hook.append("\t\t\tc.mu.Lock()")
        overlay = root / "channel_probe.txt"
        overlay.write_text(source.replace(ANCHOR, "\t\t" + "\n".join(hook)))
        config = root / "overlay.json"
        config.write_text(json.dumps({"Replace": {str(channel): str(overlay)}}))
        return subprocess.call([
            "go", "test", "-race", "-overlay", str(config), "-run",
            "^TestP04aGetWaitsWhileReturnedConnectionIsIdle$", "-count",
            "1" if args.control else "25", "-timeout", "30s", ".",
        ], cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
