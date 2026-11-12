#!/usr/bin/env python3
"""Ask Jev one bounded question about a supplied source passage (metered).

Results are advisory. The caller retains the source and decides what to do
with the returned probability.
"""

import argparse
import json
import math
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


# TypeSafe documents 429 (rate limit) and 529 (overloaded) as retryable with
# exponential backoff and Retry-After; DeepSeek uses 429 and 503. Other errors
# fail at once. Its cookbooks use a 120 s client timeout for batched requests.
RETRY_STATUSES = {429, 503, 529}
MAX_RETRIES = 3
TIMEOUT_SECONDS = 120


def _retry_delay(error, attempt):
    header = error.headers.get("Retry-After") if error.headers else None
    try:
        seconds = float(header)
    except (TypeError, ValueError):
        seconds = math.nan  # absent, or an HTTP date: use backoff
    if not math.isfinite(seconds):
        return min(2.0 ** attempt, 30.0)
    return min(max(seconds, 0.0), 60.0)


def post_json(url, payload, key):
    data = json.dumps(payload).encode("utf-8")
    for attempt in range(MAX_RETRIES + 1):
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in RETRY_STATUSES or attempt == MAX_RETRIES:
                raise
            time.sleep(_retry_delay(error, attempt))


def main():
    from local_budget import Budget, BudgetExceeded
    from local_models import jev

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True, help="budget ledger")
    parser.add_argument("--limit-microdollars", type=int)
    parser.add_argument("source", type=Path, help="UTF-8 source passage to send to Jev")
    parser.add_argument("question", help="A single yes/no question about the passage")
    args = parser.parse_args()
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        parser.error("TYPESAFE_API_KEY is not set")
    try:
        budget = Budget(args.ledger, args.limit_microdollars)
        result = jev(budget, args.source.read_text(encoding="utf-8"), args.question, key)
    except (OSError, ValueError, BudgetExceeded, urllib.error.URLError, sqlite3.Error) as error:
        print(f"Jev request failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
