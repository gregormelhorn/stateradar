#!/usr/bin/env python3
"""Run a bounded text task through DeepSeek Flash or a Jev judgment.

Inputs are explicit files. Each request uses an independent session and sends
only the supplied material. Costs are reserved in a local SQLite ledger.
"""

import argparse
import hashlib
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
    response, input_tokens, cost, reserved = _jev_request(budget, payload, key)
    try:
        probability = response["answers"]["judgment"]["noul"]
        model = response["model"]
    except (KeyError, TypeError) as error:
        raise ValueError("Jev response lacks an answer") from error
    if isinstance(probability, bool) or not isinstance(probability, (int, float)) or not 0 <= probability <= 1:
        raise ValueError("Jev returned an invalid probability")
    return {"model": model, "probability": probability, "input_tokens": input_tokens,
            "cost_microdollars": cost, "reservation_microdollars": reserved}


def _jev_request(budget, payload, key):
    estimated_input = len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) + 1000
    reserved = max(1, math.ceil(estimated_input * 0.042))
    ticket = budget.reserve("jev", reserved)
    response = post_json(JEV_URL, payload, key)
    input_tokens = _tokens(_usage(response).get("input_tokens"))
    cost = math.ceil(input_tokens * 0.042)
    budget.settle(ticket, cost)
    return response, input_tokens, cost, reserved


def _citation_error(source_lines, line, fragment):
    """Return why a line/fragment citation fails against the source, or None."""
    if isinstance(line, bool) or not isinstance(line, int) or not 1 <= line <= len(source_lines):
        return "citation line is outside source"
    window = "\n".join(source_lines[max(0, line - 4):min(len(source_lines), line + 3)])
    if not isinstance(fragment, str) or not fragment.strip() or fragment not in window:
        return f"citation fragment missing near line {line}"
    return None


def jev_batch(budget, source, source_ref, checks, key, model="jev-latest"):
    """Evaluate independent cited claims or ordering checks against one source."""
    if not all(isinstance(x, str) and x.strip() for x in (source, source_ref, key, model)):
        raise ValueError("source, source reference, key, and model are required")
    if not isinstance(checks, list) or not checks:
        raise ValueError("checks must be a nonempty list")
    questions = {}
    seen_ids = set()
    source_lines = source.splitlines()
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            raise ValueError("each check must be an object")
        ident, kind = check.get("id"), check.get("kind")
        statement, fragment, line = check.get("statement"), check.get("fragment"), check.get("line")
        if not all(isinstance(x, str) and x.strip() for x in (ident, statement, fragment)):
            raise ValueError("each check requires a nonempty id, statement, and fragment")
        if ident in seen_ids:
            raise ValueError(f"duplicate check id: {ident}")
        seen_ids.add(ident)
        if kind not in ("claim", "ordering"):
            raise ValueError(f"unknown check kind: {kind}")
        error = _citation_error(source_lines, line, fragment)
        if error:
            raise ValueError(f"{ident}: {error}")
        if kind == "ordering":
            instruction = ("Does the cited fragment itself explicitly contemplate this specific event ordering? "
                           "Use the surrounding source only to interpret the fragment. "
                           "A general requirement does not establish an unmentioned ordering. ")
        else:
            instruction = ("Does the cited fragment support this specific claim? "
                           "Use the surrounding source only to interpret the fragment. ")
        questions[f"choice_{index}"] = {
            "type": "choice",
            "instructions": instruction + f"Claim or ordering: {statement}\nCited fragment: {fragment}",
            "criteria": {
                "supported": "The cited fragment explicitly supports the claim or contemplates the specific ordering.",
                "contradicted": "The cited fragment explicitly contradicts the claim or rules out the specific ordering.",
                "unclear": "The cited fragment does not establish either conclusion, or the evidence is insufficient.",
            },
        }
        if kind == "ordering":
            questions[f"scope_{index}"] = {
                "type": "noul",
                "instructions": {
                    "question": "Does the cited fragment explicitly describe or contemplate this particular sequence of events?",
                    "fragment": fragment,
                    "sequence": statement,
                    "scope": "Consider only the fragment. An event missing from the fragment or an unmentioned event ordering is insufficient.",
                },
                "criteria": {
                    "true": "The fragment describes the relevant events and the specific order between them.",
                    "false": "At least one event or its ordering is not described in the fragment.",
                },
            }
    payload = {"model": model, "state": {"source": source}, "questions": questions}
    response, input_tokens, cost, reserved = _jev_request(budget, payload, key)
    answers = response.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(questions):
        raise ValueError("Jev response has missing or unexpected answers; usage was recorded")
    model = response.get("model")
    if not isinstance(model, str) or not model:
        raise ValueError("Jev response lacks a model; usage was recorded")
    results = {}
    for index, check in enumerate(checks):
        answer = answers[f"choice_{index}"]
        if not isinstance(answer, dict):
            raise ValueError("Jev response has an invalid answer; usage was recorded")
        choice = answer.get("choice")
        probabilities = answer.get("probabilities")
        confidence = answer.get("confidence")
        if (answer.get("type") != "choice" or choice not in ("supported", "contradicted", "unclear")
                or not isinstance(probabilities, dict) or set(probabilities) != {"supported", "contradicted", "unclear"}
                or any(isinstance(p, bool) or not isinstance(p, (int, float)) or not 0 <= p <= 1
                       for p in probabilities.values())
                or isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1):
            raise ValueError("Jev response has an invalid choice answer; usage was recorded")
        if abs(sum(probabilities.values()) - 1) > 0.03 or probabilities[choice] < max(probabilities.values()):
            raise ValueError("Jev response has an inconsistent probability distribution; usage was recorded")
        results[check["id"]] = {"kind": check["kind"], "statement": check["statement"],
                                "source": source_ref, "line": check["line"], "fragment": check["fragment"],
                                "choice": choice, "probabilities": probabilities,
                                "confidence": confidence, "review_required": True}
        if check["kind"] == "ordering":
            scope = answers[f"scope_{index}"]
            if not isinstance(scope, dict) or scope.get("type") != "noul":
                raise ValueError("Jev response has an invalid ordering scope answer; usage was recorded")
            probability = scope.get("noul")
            if (isinstance(probability, bool) or not isinstance(probability, (int, float))
                    or not 0 <= probability <= 1):
                raise ValueError("Jev response has an invalid ordering scope probability; usage was recorded")
            results[check["id"]]["ordering_scope_probability"] = probability
    return {"model": model, "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "input_tokens": input_tokens, "cost_microdollars": cost,
            "reservation_microdollars": reserved, "checks": results}


class InvalidDraft(ValueError):
    """A Flash draft that is not the required JSON structure. Keeps the raw text."""

    def __init__(self, message, text):
        self.text = text
        super().__init__(f"Flash draft rejected: {message}; usage was recorded")


DRAFT_INSTRUCTIONS = """You draft source-grounded claims for a StateRadar analysis. You propose; you do not decide.

Task:
{task}

Rules:
- Use only the numbered source below. Do not use outside knowledge.
- Each claim cites ONE source line number and a short fragment copied verbatim from that line.
- kind is "claim" for a statement of behaviour or requirement, "ordering" for a specific sequence of events.
- A general requirement does not establish an ordering it does not mention: put such cases into questions.
- Put every gap, contradiction, ambiguity, or unspecified behaviour into questions. Do not resolve it.
- Answer with JSON only, no prose, exactly in this shape:
{{"claims": [{{"id": "C1", "kind": "claim", "statement": "...", "line": 1, "fragment": "..."}}], "questions": ["..."]}}

Source ({source_ref}), one line per number:
{numbered}
"""


def _parse_draft(text):
    body = text.strip()
    if body.startswith("```"):
        body = body.split("\n", 1)[1] if "\n" in body else ""
        body = body.rsplit("```", 1)[0]
    try:
        draft = json.loads(body)
    except json.JSONDecodeError as error:
        raise InvalidDraft(f"not JSON ({error.msg})", text) from error
    if not isinstance(draft, dict) or not isinstance(draft.get("claims"), list):
        raise InvalidDraft("a claims list is required", text)
    questions = draft.get("questions")
    if not isinstance(questions, list) or not all(isinstance(q, str) and q.strip() for q in questions):
        raise InvalidDraft("a questions list of nonempty strings is required", text)
    seen = set()
    for claim in draft["claims"]:
        if not isinstance(claim, dict):
            raise InvalidDraft("each claim must be an object", text)
        ident = claim.get("id")
        if not all(isinstance(claim.get(k), str) and claim[k].strip() for k in ("id", "statement", "fragment")):
            raise InvalidDraft("each claim requires a nonempty id, statement, and fragment", text)
        if ident in seen:
            raise InvalidDraft(f"duplicate claim id {ident}", text)
        seen.add(ident)
        if claim.get("kind") not in ("claim", "ordering"):
            raise InvalidDraft(f"{ident}: unknown kind {claim.get('kind')!r}", text)
    return draft["claims"], questions


def draft_verify(budget, source, source_ref, task, flash_key, jev_key, model="jev-latest", max_tokens=4096):
    """Flash drafts cited claims, code checks the citations, Jev judges the citable ones.

    Nothing is accepted automatically. Claims with failed citations are kept with the
    reason and never sent to Jev; every draft question is carried forward.
    """
    if not all(isinstance(x, str) and x.strip() for x in (source, source_ref, task, flash_key, jev_key)):
        raise ValueError("source, source reference, task, and both API keys are required")
    source_lines = source.splitlines()
    numbered = "\n".join(f"{number}: {text}" for number, text in enumerate(source_lines, 1))
    prompt = DRAFT_INSTRUCTIONS.format(task=task.strip(), source_ref=source_ref, numbered=numbered)
    drafted = flash(budget, prompt, flash_key, max_tokens)
    claims, questions = _parse_draft(drafted["text"])
    results, citable = {}, []
    for claim in claims:
        entry = {key: claim.get(key) for key in ("kind", "statement", "line", "fragment")}
        error = _citation_error(source_lines, claim.get("line"), claim["fragment"])
        entry["citation_check"] = error or "ok"
        entry["jev"] = None
        results[claim["id"]] = entry
        if not error:
            citable.append({key: claim[key] for key in ("id", "kind", "statement", "line", "fragment")})
    verification = None
    if citable:
        verification = jev_batch(budget, source, source_ref, citable, jev_key, model)
        for ident, judged in verification["checks"].items():
            results[ident]["jev"] = {key: judged[key] for key in judged
                                     if key in ("choice", "probabilities", "confidence", "ordering_scope_probability")}
        verification = {key: verification[key] for key in ("model", "input_tokens", "cost_microdollars",
                                                           "reservation_microdollars")}
    draft_meta = {key: drafted[key] for key in drafted if key != "text"}
    return {"source": source_ref, "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "draft": draft_meta, "verification": verification, "claims": results,
            "questions": questions, "review_required": True}


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
    batch_parser = commands.add_parser("jev-batch")
    batch_parser.add_argument("input", type=Path, help="UTF-8 source shared by the checks")
    batch_parser.add_argument("checks", type=Path, help="JSON array of checks")
    batch_parser.add_argument("--model", default="jev-latest", help="TypeSafe model name or alias")
    draft_parser = commands.add_parser("draft-verify", help="Flash drafts cited claims; Jev judges them")
    draft_parser.add_argument("input", type=Path, help="UTF-8 source the claims must cite")
    draft_parser.add_argument("task", type=Path, help="UTF-8 file with the bounded drafting task")
    draft_parser.add_argument("--output", type=Path, required=True, help="JSON result file")
    draft_parser.add_argument("--model", default="jev-latest", help="TypeSafe model name or alias")
    draft_parser.add_argument("--max-tokens", type=int, default=4096)
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
        elif args.command == "draft-verify":
            flash_key, jev_key = os.environ.get("DEEPSEEK_API_KEY"), os.environ.get("TYPESAFE_API_KEY")
            missing = [name for name, value in (("DEEPSEEK_API_KEY", flash_key), ("TYPESAFE_API_KEY", jev_key)) if not value]
            if missing:
                raise ValueError(f"draft-verify needs {' and '.join(missing)}")
            try:
                result = draft_verify(budget, args.input.read_text(encoding="utf-8"), str(args.input),
                                      args.task.read_text(encoding="utf-8"), flash_key, jev_key,
                                      args.model, args.max_tokens)
            except InvalidDraft as error:
                args.output.with_suffix(".draft.txt").write_text(error.text, encoding="utf-8")
                raise
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        elif args.command == "jev-batch":
            result = jev_batch(budget, args.input.read_text(encoding="utf-8"), str(args.input),
                               json.loads(args.checks.read_text(encoding="utf-8")), os.environ.get("TYPESAFE_API_KEY"), args.model)
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
