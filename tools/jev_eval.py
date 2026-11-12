#!/usr/bin/env python3
"""Compare one Jev batch with independently reviewed labels; never route work."""

import argparse
import json
import re
import sys
from pathlib import Path

VERDICTS = ("supported", "contradicted", "unclear")
IDENTITY = ("kind", "statement", "source", "line", "fragment")


def evaluate(labels, batch):
    if not isinstance(labels, dict) or not isinstance(batch, dict):
        raise ValueError("labels and batch must be objects")
    digest = labels.get("source_sha256")
    if (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or batch.get("source_sha256") != digest):
        raise ValueError("source hash missing, invalid, or different")
    expected, observed = labels.get("checks"), batch.get("checks")
    if not isinstance(expected, dict) or not expected or not isinstance(observed, dict):
        raise ValueError("checks must be nonempty objects")
    if set(expected) != set(observed):
        raise ValueError("label and result IDs differ")
    model, tokens, cost = batch.get("model"), batch.get("input_tokens"), batch.get("cost_microdollars")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model missing")
    for value in (tokens, cost):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("invalid token count or cost")
    matrix = {truth: {choice: 0 for choice in VERDICTS} for truth in VERDICTS}
    false_support, unclear = [], []
    for ident in sorted(expected):
        label, result = expected[ident], observed[ident]
        if not isinstance(ident, str) or not ident.strip() or not isinstance(label, dict) or not isinstance(result, dict):
            raise ValueError("invalid check")
        if (label.get("kind") not in ("claim", "ordering")
                or any(not isinstance(label.get(key), str) or not label[key].strip()
                       for key in ("statement", "source", "fragment", "reviewer"))
                or isinstance(label.get("line"), bool) or not isinstance(label.get("line"), int)
                or label["line"] < 1):
            raise ValueError(f"{ident}: invalid label or reviewer")
        if any(label[key] != result.get(key) for key in IDENTITY):
            raise ValueError(f"{ident}: check identity differs")
        truth, choice = label.get("expected"), result.get("choice")
        if truth not in VERDICTS or choice not in VERDICTS:
            raise ValueError(f"{ident}: invalid verdict")
        matrix[truth][choice] += 1
        if choice == "supported" and truth != "supported":
            false_support.append(ident)
        if choice == "unclear":
            unclear.append(ident)
    return {"model": model, "source_sha256": digest, "total": len(expected),
            "exact_matches": sum(matrix[x][x] for x in VERDICTS),
            "confusion_matrix": matrix, "false_support_ids": false_support,
            "unclear_ids": unclear, "input_tokens": tokens, "cost_microdollars": cost,
            "review_required": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("labels", type=Path)
    parser.add_argument("batch", type=Path)
    args = parser.parse_args()
    try:
        labels = json.loads(args.labels.read_text(encoding="utf-8"))
        batch = json.loads(args.batch.read_text(encoding="utf-8"))
        print(json.dumps(evaluate(labels, batch), indent=2))
    except (ValueError, OSError) as error:
        print(f"EVALUATION ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
