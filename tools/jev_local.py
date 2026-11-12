#!/usr/bin/env python3
"""Ask Jev one bounded question about a supplied source passage.

Results are advisory. The caller retains the source and decides what to do
with the returned probability.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def post_json(url, payload, key):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def evaluate(source, question, key):
    payload = {
        "model": "jev-latest",
        "state": {"source": source},
        "questions": {
            "ordering": {"type": "noul", "instructions": question},
        },
    }
    response = post_json("https://api.typesafe.ai/v1/systemone", payload, key)
    try:
        probability = response["answers"]["ordering"]["noul"]
        input_tokens = response["usage"]["input_tokens"]
        model = response["model"]
    except (KeyError, TypeError) as error:
        raise ValueError("Jev response lacks an answer, model, or token usage") from error
    if isinstance(probability, bool) or not isinstance(probability, (int, float)) or not 0 <= probability <= 1:
        raise ValueError("Jev returned an invalid probability")
    if isinstance(input_tokens, bool) or not isinstance(input_tokens, int) or input_tokens < 0:
        raise ValueError("Jev returned invalid token usage")
    return {"model": model, "probability": probability, "input_tokens": input_tokens}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="UTF-8 source passage to send to Jev")
    parser.add_argument("question", help="A single yes/no question about the passage")
    args = parser.parse_args()
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        parser.error("TYPESAFE_API_KEY is not set")
    try:
        result = evaluate(args.source.read_text(encoding="utf-8"), args.question, key)
    except (OSError, ValueError, urllib.error.URLError) as error:
        print(f"Jev request failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
