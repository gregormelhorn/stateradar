#!/usr/bin/env python3
"""Run a bounded text task through DeepSeek Flash or a Jev judgment.

Inputs are explicit files. Each request uses an independent session and sends
only the supplied material. Costs are reserved in a local SQLite ledger.
"""

import argparse
import json
import math
import os
import sys
import tempfile
import urllib.error
from pathlib import Path

from jev_local import post_json
from local_budget import Budget, BudgetExceeded
import part_b_pack

FLASH_URL = "https://api.deepseek.com/chat/completions"
JEV_URL = "https://api.typesafe.ai/v1/systemone"


class IncompleteResponse(ValueError):
    def __init__(self, result):
        self.result = result
        super().__init__(f"DeepSeek response incomplete (finish_reason={result['finish_reason']}); usage was recorded")


def _tokens(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("provider returned invalid token usage")
    return value


def _usage(response):
    if not isinstance(response, dict) or not isinstance(response.get("usage"), dict):
        raise ValueError("provider response lacks token usage; reservation retained")
    return response["usage"]


def flash(budget, prompt, key, max_tokens=4096):
    if not prompt or not key or not 1 <= max_tokens <= 16384:
        raise ValueError("prompt, key, and max_tokens in 1..16384 are required")
    # A deliberately conservative estimate, not a provider-enforced ceiling.
    estimated_input = len(prompt.encode("utf-8")) + 1000
    reserved = math.ceil(estimated_input * 0.3 + max_tokens * 1.2)
    ticket = budget.reserve("deepseek-flash", reserved)
    payload = {"model": "deepseek-flash", "messages": [{"role": "user", "content": prompt}],
               "max_tokens": max_tokens, "thinking": {"type": "disabled"}}
    response = post_json(FLASH_URL, payload, key)
    usage = _usage(response)
    prompt_tokens = _tokens(usage.get("prompt_tokens"))
    output_tokens = _tokens(usage.get("completion_tokens"))
    cost = math.ceil(prompt_tokens * 0.3 + output_tokens * 1.2)
    budget.settle(ticket, cost)
    try:
        choice = response["choices"][0]
        content = choice["message"]["content"]
        model = response["model"]
        finish = choice["finish_reason"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("DeepSeek response lacks an answer") from error
    if not isinstance(content, str) or not content:
        raise ValueError("DeepSeek returned an empty answer")
    result = {"model": model, "text": content, "finish_reason": finish,
              "input_tokens": prompt_tokens, "output_tokens": output_tokens,
              "cost_microdollars": cost, "reservation_microdollars": reserved}
    if finish != "stop":
        raise IncompleteResponse(result)
    return result


def jev(budget, source, question, key):
    if not source or not question or not key:
        raise ValueError("source, question, and key are required")
    payload = {"model": "jev-latest", "state": {"source": source},
               "questions": {"judgment": {"type": "noul", "instructions": question}}}
    estimated_input = len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) + 1000
    reserved = max(1, math.ceil(estimated_input * 0.042))
    ticket = budget.reserve("jev", reserved)
    response = post_json(JEV_URL, payload, key)
    input_tokens = _tokens(_usage(response).get("input_tokens"))
    cost = math.ceil(input_tokens * 0.042)
    budget.settle(ticket, cost)
    try:
        probability = response["answers"]["judgment"]["noul"]
        model = response["model"]
    except (KeyError, TypeError) as error:
        raise ValueError("Jev response lacks an answer") from error
    if isinstance(probability, bool) or not isinstance(probability, (int, float)) or not 0 <= probability <= 1:
        raise ValueError("Jev returned an invalid probability")
    return {"model": model, "probability": probability, "input_tokens": input_tokens,
            "cost_microdollars": cost, "reservation_microdollars": reserved}


def blind(budget, args, key):
    if not args.requirements or not args.contracts:
        raise ValueError("blind pass requires requirements and event contracts")
    pack_root = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory() as temporary:
        package_path = Path(temporary) / "package.md"
        package_args = argparse.Namespace(
            repo=args.repo, analysis_dir=args.analysis,
            requirements=args.requirements + args.contracts,
            contracts=[], out=str(package_path), for_dispatch=False,
        )
        if part_b_pack.assemble(package_args, pack_root) != 0:
            raise ValueError("blind input package failed validation")
        package = package_path.read_text(encoding="utf-8")
        package += ("\nThe coverage checklist must use one exact line per event or pair "
                    "in the form '- [x] EVENT_ID', with no other text on that line.\n")
        try:
            result = flash(budget, package, key, args.max_tokens)
        except IncompleteResponse as error:
            args.output.write_text(error.result["text"], encoding="utf-8")
            raise
        args.output.write_text(result["text"], encoding="utf-8")
        print(json.dumps({k: v for k, v in result.items() if k != "text"}, indent=2))
        check_args = argparse.Namespace(repo=args.repo, analysis_dir=args.analysis, check=str(args.output))
        status = part_b_pack.check(check_args)
        if result["finish_reason"] != "stop":
            print("PART-B: incomplete provider response", file=sys.stderr)
            return 1
        return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--limit-microdollars", type=int, help="initial limit for a new ledger")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    limit_parser = commands.add_parser("set-limit")
    limit_parser.add_argument("amount_microdollars", type=int)
    settle_parser = commands.add_parser("settle")
    settle_parser.add_argument("reservation", type=int)
    settle_parser.add_argument("actual_microdollars", type=int)
    flash_parser = commands.add_parser("flash")
    flash_parser.add_argument("input", type=Path)
    flash_parser.add_argument("--max-tokens", type=int, default=4096)
    jev_parser = commands.add_parser("jev")
    jev_parser.add_argument("input", type=Path)
    jev_parser.add_argument("question")
    blind_parser = commands.add_parser("blind")
    blind_parser.add_argument("analysis")
    blind_parser.add_argument("--repo", default=".")
    blind_parser.add_argument("--requirements", action="append", required=True)
    blind_parser.add_argument("--contracts", action="append", required=True)
    blind_parser.add_argument("--output", type=Path, required=True)
    blind_parser.add_argument("--max-tokens", type=int, default=8192)
    args = parser.parse_args()
    try:
        budget = Budget(args.ledger, args.limit_microdollars)
        if args.command == "status":
            result = {"committed_or_reserved_microdollars": budget.total(), "limit_microdollars": budget.limit,
                      "calls": budget.calls()}
        elif args.command == "set-limit":
            budget.set_limit(args.amount_microdollars)
            result = {"limit_microdollars": budget.limit}
        elif args.command == "settle":
            budget.settle(args.reservation, args.actual_microdollars)
            result = {"committed_or_reserved_microdollars": budget.total()}
        elif args.command == "flash":
            result = flash(budget, args.input.read_text(encoding="utf-8"), os.environ.get("DEEPSEEK_API_KEY"), args.max_tokens)
        elif args.command == "blind":
            return blind(budget, args, os.environ.get("DEEPSEEK_API_KEY"))
        else:
            result = jev(budget, args.input.read_text(encoding="utf-8"), args.question, os.environ.get("TYPESAFE_API_KEY"))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except IncompleteResponse as error:
        print(json.dumps(error.result, ensure_ascii=False, indent=2))
        print(f"LOCAL MODELS: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError, BudgetExceeded, urllib.error.URLError) as error:
        print(f"LOCAL MODELS: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
