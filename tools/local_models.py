#!/usr/bin/env python3
"""Run a bounded text task through DeepSeek Flash or a Jev judgment.

Inputs are explicit files. Each request uses an independent session and sends
only the supplied material. Costs are reserved in a local SQLite ledger.
"""

import argparse
import contextlib
import hashlib
import http.client
import json
import math
import os
import sqlite3
import sys
import tempfile
import urllib.error
from pathlib import Path
from collections.abc import Mapping
from typing import Any, Literal, NotRequired, TypedDict

from jev_local import post_json
from local_budget import Budget, BudgetExceeded
import part_b_pack

FLASH_URL = "https://api.deepseek.com/chat/completions"
JEV_URL = "https://api.typesafe.ai/v1/systemone"

# Provider responses are parsed JSON and arrive as Any: each function below
# validates the fields it reads. The TypedDicts describe what this module
# returns and writes, which callers and the selftests rely on.

CheckKind = Literal["claim", "ordering"]
Choice = Literal["supported", "contradicted", "unclear"]


class FlashResult(TypedDict):
    model: str
    text: str
    finish_reason: str
    input_tokens: int
    output_tokens: int
    cost_microdollars: int
    reservation_microdollars: int


class DraftMeta(TypedDict):
    """A FlashResult without its text, as draft-verify records it."""
    model: str
    finish_reason: str
    input_tokens: int
    output_tokens: int
    cost_microdollars: int
    reservation_microdollars: int


class JevResult(TypedDict):
    model: str
    probability: float
    input_tokens: int
    cost_microdollars: int
    reservation_microdollars: int


class Check(TypedDict):
    """One jev-batch check as validated from the caller's JSON."""
    id: str
    kind: CheckKind
    statement: str
    line: int
    fragment: str


class CheckResult(TypedDict):
    kind: CheckKind
    statement: str
    source: str
    line: int
    fragment: str
    choice: Choice
    probabilities: dict[str, float]
    confidence: float
    review_required: bool
    ordering_scope_probability: NotRequired[float]


class JevBatchResult(TypedDict):
    model: str
    source_sha256: str
    input_tokens: int
    cost_microdollars: int
    reservation_microdollars: int
    checks: dict[str, CheckResult]


class Judgment(TypedDict, total=False):
    """The judged part of a CheckResult, copied onto a draft claim."""
    choice: Choice
    probabilities: dict[str, float]
    confidence: float
    ordering_scope_probability: float


class ClaimEntry(TypedDict):
    kind: CheckKind
    statement: str
    line: object  # as drafted; _citation_error reports a non-integer line
    fragment: str
    citation_check: str
    jev: Judgment | None


class Verification(TypedDict, total=False):
    """Jev's part of a draft-verify result: totals on success (error None),
    the reason and whatever was paid for on failure."""
    error: str | None
    model: str
    input_tokens: int
    cost_microdollars: int
    reservation_microdollars: int
    unrecorded_response: Any
    question_claims: dict[str, str]


class DraftVerifyResult(TypedDict):
    source: str
    source_sha256: str
    draft: DraftMeta
    verification: Verification | None
    claims: dict[str, ClaimEntry]
    questions: list[str]
    review_required: bool


class ProviderError(ValueError):
    """A request failed after its cost was reserved; the reservation stays until settled."""

    def __init__(self, ticket: int, error: object) -> None:
        super().__init__(f"request failed ({error}); reservation {ticket} kept: check the provider's "
                         f"usage, then run 'settle {ticket} <actual microdollars>'")


def _post(ticket: int, url: str, payload: dict[str, Any], key: str) -> Any:
    try:
        return post_json(url, payload, key)
    except urllib.error.HTTPError as error:
        # The body carries the provider's reason (e.g. max_tokens_exceeded).
        try:
            body = error.read(500).decode("utf-8", "replace").strip()
        except Exception:  # the body is diagnostic only
            body = ""
        raise ProviderError(ticket, f"{error}{': ' + body if body else ''}") from error
    except (OSError, ValueError, http.client.HTTPException) as error:  # URLError is an OSError
        raise ProviderError(ticket, error) from error


class LedgerError(ValueError):
    """The provider answered and was paid, but the ledger could not record it."""

    def __init__(self, ticket: int, cost: int, response: Any, error: object) -> None:
        self.response = response
        super().__init__(f"ledger update failed ({error}); the paid answer is reported with this error; "
                         f"run 'settle {ticket} {cost}' once the ledger is free")


def _settle(budget: Budget, ticket: int, cost: int, response: Any) -> None:
    try:
        budget.settle(ticket, cost)
    except sqlite3.Error as error:
        raise LedgerError(ticket, cost, response, error) from error


class JevAnswerError(ValueError):
    """Jev answered and was charged, but the answer failed validation."""

    def __init__(self, message: str, input_tokens: int, cost: int) -> None:
        self.input_tokens, self.cost = input_tokens, cost
        super().__init__(message)


class IncompleteResponse(ValueError):
    def __init__(self, result: FlashResult) -> None:
        self.result = result
        # Set by a caller that kept the truncated text on disk.
        self.saved_to: str | None = None
        super().__init__(f"DeepSeek response incomplete (finish_reason={result['finish_reason']}); usage was recorded")


def _tokens(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("provider returned invalid token usage")
    return value


def _usage(response: Any) -> dict[str, Any]:
    if not isinstance(response, dict) or not isinstance(response.get("usage"), dict):
        raise ValueError("provider response lacks token usage; reservation retained")
    usage: dict[str, Any] = response["usage"]
    return usage


def flash(budget: Budget, prompt: str, key: str | None, max_tokens: int = 4096) -> FlashResult:
    if not prompt or not key or not 1 <= max_tokens <= 16384:
        raise ValueError("prompt, key, and max_tokens in 1..16384 are required")
    # A deliberately conservative estimate, not a provider-enforced ceiling.
    estimated_input = len(prompt.encode("utf-8")) + 1000
    reserved = math.ceil(estimated_input * 0.3 + max_tokens * 1.2)
    ticket = budget.reserve("deepseek-flash", reserved)
    payload = {"model": "deepseek-flash", "messages": [{"role": "user", "content": prompt}],
               "max_tokens": max_tokens, "thinking": {"type": "disabled"}}
    response = _post(ticket, FLASH_URL, payload, key)
    usage = _usage(response)
    prompt_tokens = _tokens(usage.get("prompt_tokens"))
    output_tokens = _tokens(usage.get("completion_tokens"))
    cost = math.ceil(prompt_tokens * 0.3 + output_tokens * 1.2)
    _settle(budget, ticket, cost, response)
    try:
        choice = response["choices"][0]
        content = choice["message"]["content"]
        model = response["model"]
        finish = choice["finish_reason"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("DeepSeek response lacks an answer") from error
    if not isinstance(content, str) or not content:
        raise ValueError("DeepSeek returned an empty answer")
    result: FlashResult = {"model": model, "text": content, "finish_reason": finish,
              "input_tokens": prompt_tokens, "output_tokens": output_tokens,
              "cost_microdollars": cost, "reservation_microdollars": reserved}
    if finish != "stop":
        raise IncompleteResponse(result)
    return result


def jev(budget: Budget, source: str, question: str, key: str | None, model: str = "jev-latest") -> JevResult:
    if not source or not question or not key:
        raise ValueError("source, question, and key are required")
    payload = {"model": model, "state": {"source": source},
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


def _jev_request(budget: Budget, payload: dict[str, Any], key: str) -> tuple[Any, int, int, int]:
    estimated_input = len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) + 1000
    reserved = max(1, math.ceil(estimated_input * 0.042))
    ticket = budget.reserve("jev", reserved)
    response = _post(ticket, JEV_URL, payload, key)
    input_tokens = _tokens(_usage(response).get("input_tokens"))
    cost = math.ceil(input_tokens * 0.042)
    _settle(budget, ticket, cost, response)
    return response, input_tokens, cost, reserved


MIN_FRAGMENT = 4


def _citation_error(source_lines: list[str], line: object, fragment: object) -> str | None:
    """Return why a line/fragment citation fails against the source, or None.

    The fragment must be one line of at least MIN_FRAGMENT non-space characters,
    found within the pack-wide window of three lines around the cited line.
    """
    if isinstance(line, bool) or not isinstance(line, int):
        return "citation line is not an integer"
    if not 1 <= line <= len(source_lines):
        return "citation line is outside source"
    if not isinstance(fragment, str) or "\n" in fragment or len("".join(fragment.split())) < MIN_FRAGMENT:
        return f"citation fragment must be a single line of at least {MIN_FRAGMENT} non-space characters"
    if not any(fragment in text for text in source_lines[max(0, line - 4):min(len(source_lines), line + 3)]):
        return f"citation fragment missing near line {line}"
    return None


def jev_batch(budget: Budget, source: str, source_ref: str, checks: object, key: str | None,
              model: str = "jev-latest") -> JevBatchResult:
    """Evaluate independent cited claims or ordering checks against one source."""
    if not all(isinstance(x, str) and x.strip() for x in (source, source_ref, key, model)):
        raise ValueError("source, source reference, key, and model are required")
    assert key is not None  # checked above; all() does not narrow the type
    if not isinstance(checks, list) or not checks:
        raise ValueError("checks must be a nonempty list")
    questions: dict[str, dict[str, Any]] = {}
    seen_ids: set[str] = set()
    validated: list[Check] = []
    source_lines = source.splitlines()
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            raise ValueError("each check must be an object")
        ident, kind = check.get("id"), check.get("kind")
        statement, fragment, line = check.get("statement"), check.get("fragment"), check.get("line")
        if not (isinstance(ident, str) and ident.strip() and isinstance(statement, str) and statement.strip()
                and isinstance(fragment, str) and fragment.strip()):
            raise ValueError("each check requires a nonempty id, statement, and fragment")
        if ident in seen_ids:
            raise ValueError(f"duplicate check id: {ident}")
        seen_ids.add(ident)
        if kind not in ("claim", "ordering"):
            raise ValueError(f"unknown check kind: {kind}")
        error = _citation_error(source_lines, line, fragment)
        if error:
            raise ValueError(f"{ident}: {error}")
        assert isinstance(line, int)  # _citation_error rejected anything else
        validated.append({"id": ident, "kind": kind, "statement": statement, "line": line,
                          "fragment": fragment})
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
    try:
        answers = response.get("answers")
        if not isinstance(answers, dict) or set(answers) != set(questions):
            raise ValueError("Jev response has missing or unexpected answers; usage was recorded")
        model = response.get("model")
        if not isinstance(model, str) or not model:
            raise ValueError("Jev response lacks a model; usage was recorded")
        results: dict[str, CheckResult] = {}
        for index, check in enumerate(validated):
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
            result: CheckResult = {"kind": check["kind"], "statement": check["statement"],
                                   "source": source_ref, "line": check["line"], "fragment": check["fragment"],
                                   "choice": choice, "probabilities": probabilities,
                                   "confidence": confidence, "review_required": True}
            results[check["id"]] = result
            if check["kind"] == "ordering":
                scope = answers[f"scope_{index}"]
                if not isinstance(scope, dict) or scope.get("type") != "noul":
                    raise ValueError("Jev response has an invalid ordering scope answer; usage was recorded")
                probability = scope.get("noul")
                if (isinstance(probability, bool) or not isinstance(probability, (int, float))
                        or not 0 <= probability <= 1):
                    raise ValueError("Jev response has an invalid ordering scope probability; usage was recorded")
                result["ordering_scope_probability"] = probability
    except ValueError as error:
        raise JevAnswerError(str(error), input_tokens, cost) from error
    return {"model": model, "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "input_tokens": input_tokens, "cost_microdollars": cost,
            "reservation_microdollars": reserved, "checks": results}


class InvalidDraft(ValueError):
    """A Flash draft that is not the required JSON structure. Keeps the raw text."""

    def __init__(self, message: str, text: str) -> None:
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


PLACEHOLDER = "..."


def _parse_draft(text: str) -> tuple[list[dict[str, Any]], list[str]]:
    body = text.strip()
    try:
        draft = json.loads(body)
    except json.JSONDecodeError as error:
        # Tolerate prose or a code fence around exactly one draft object. Every
        # decodable object with a claims list and a questions list is a candidate;
        # more than one (for example an echoed template) is ambiguous.
        candidates, covered = [], 0
        decoder = json.JSONDecoder()
        for start in (i for i, char in enumerate(body) if char == "{"):
            if start < covered:  # inside an object that already decoded
                continue
            try:
                candidate, covered = decoder.raw_decode(body, start)
            except json.JSONDecodeError:
                continue
            if (isinstance(candidate, dict) and isinstance(candidate.get("claims"), list)
                    and isinstance(candidate.get("questions"), list)):
                candidates.append(candidate)
        if len(candidates) > 1:
            raise InvalidDraft(f"{len(candidates)} draft objects found; exactly one is required", text) from error
        if not candidates:
            raise InvalidDraft(f"not JSON ({error.msg})", text) from error
        draft = candidates[0]
    if not isinstance(draft, dict) or not isinstance(draft.get("claims"), list):
        raise InvalidDraft("a claims list is required", text)
    questions = draft.get("questions")
    if not isinstance(questions, list) or not all(isinstance(q, str) and q.strip() for q in questions):
        raise InvalidDraft("a questions list of nonempty strings is required", text)
    if any(q.strip() == PLACEHOLDER for q in questions):
        raise InvalidDraft("a question repeats the template placeholder", text)
    seen = set()
    for claim in draft["claims"]:
        if not isinstance(claim, dict):
            raise InvalidDraft("each claim must be an object", text)
        ident = claim.get("id")
        if not all(isinstance(claim.get(k), str) and claim[k].strip() for k in ("id", "statement", "fragment")):
            raise InvalidDraft("each claim requires a nonempty id, statement, and fragment", text)
        if PLACEHOLDER in (claim["statement"].strip(), claim["fragment"].strip()):
            raise InvalidDraft(f"{ident}: repeats the template placeholder", text)
        if ident in seen:
            raise InvalidDraft(f"duplicate claim id {ident}", text)
        seen.add(ident)
        if claim.get("kind") not in ("claim", "ordering"):
            raise InvalidDraft(f"{ident}: unknown kind {claim.get('kind')!r}", text)
    return draft["claims"], questions


def draft_verify(budget: Budget, source: str, source_ref: str, task: str, flash_key: str, jev_key: str,
                 model: str = "jev-latest", max_tokens: int = 12000) -> DraftVerifyResult:
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
    results: dict[str, ClaimEntry] = {}
    citable: list[Check] = []
    for claim in claims:
        error = _citation_error(source_lines, claim.get("line"), claim["fragment"])
        results[claim["id"]] = {"kind": claim["kind"], "statement": claim["statement"],
                                "line": claim.get("line"), "fragment": claim["fragment"],
                                "citation_check": error or "ok", "jev": None}
        if not error:
            citable.append({"id": claim["id"], "kind": claim["kind"], "statement": claim["statement"],
                            "line": claim["line"], "fragment": claim["fragment"]})
    verification: Verification | None = None
    if citable:
        try:
            batch = jev_batch(budget, source, source_ref, citable, jev_key, model)
        except LedgerError as error:
            # Jev answered and was paid, but the ledger is unavailable: keep the answer.
            verification = {"error": str(error), "unrecorded_response": error.response,
                            "question_claims": {f"{prefix}_{index}": check["id"]
                                                for index, check in enumerate(citable)
                                                for prefix in ("choice", "scope")
                                                if prefix == "choice" or check["kind"] == "ordering"}}
        except (ValueError, OSError, BudgetExceeded, sqlite3.Error) as error:
            # The Flash draft is paid for: keep it and its citation checks.
            verification = {"error": str(error)}
            if isinstance(error, JevAnswerError):
                verification["input_tokens"] = error.input_tokens
                verification["cost_microdollars"] = error.cost
        else:
            for ident, judged in batch["checks"].items():
                judgment: Judgment = {"choice": judged["choice"], "probabilities": judged["probabilities"],
                                      "confidence": judged["confidence"]}
                if "ordering_scope_probability" in judged:
                    judgment["ordering_scope_probability"] = judged["ordering_scope_probability"]
                results[ident]["jev"] = judgment
            verification = {"model": batch["model"], "input_tokens": batch["input_tokens"],
                            "cost_microdollars": batch["cost_microdollars"],
                            "reservation_microdollars": batch["reservation_microdollars"], "error": None}
    draft_meta: DraftMeta = {"model": drafted["model"], "finish_reason": drafted["finish_reason"],
                             "input_tokens": drafted["input_tokens"], "output_tokens": drafted["output_tokens"],
                             "cost_microdollars": drafted["cost_microdollars"],
                             "reservation_microdollars": drafted["reservation_microdollars"]}
    return {"source": source_ref, "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "draft": draft_meta, "verification": verification, "claims": results,
            "questions": questions, "review_required": True}


TEXT_SUFFIXES = (".md", ".txt", ".rst")


def blind(budget: Budget, args: argparse.Namespace, key: str | None) -> int:
    if not args.requirements or not args.contracts:
        raise ValueError("blind pass requires requirements and event contracts")
    for spec in args.requirements + args.contracts:
        # Flash gets prepared prose only: no source file, no class blocks.
        name = spec.split(":", 1)[0]
        if Path(name).suffix.lower() not in TEXT_SUFFIXES or (spec in args.contracts and ":" in spec):
            raise ValueError(f"blind takes only prepared text files ({', '.join(TEXT_SUFFIXES)}): "
                             f"requirements as FILE or FILE:PATTERN, contracts as a whole FILE: {spec!r}")
    pack_root = Path(__file__).resolve().parent.parent
    # Keep the exact dispatched package next to the output: it is the record of
    # what the blind pass saw, and a temporary path would be gone after the run.
    package_path = args.output.with_suffix(".package.md")
    package_only = getattr(args, "package_only", False)
    if not package_only and not package_path.is_file():
        raise ValueError(f"run blind with --package-only first and read {package_path}")
    with tempfile.TemporaryDirectory() as scratch:
        assembled = Path(scratch) / "package.md"
        package_args = argparse.Namespace(
            repo=args.repo, analysis_dir=args.analysis,
            requirements=args.requirements, contracts=args.contracts,
            out=str(assembled), for_dispatch=False,
        )
        # assemble reports on stdout and names the temporary file: keep stdout
        # for blind's own JSON and pass the report to stderr.
        with contextlib.redirect_stdout(sys.stderr):
            assembled_ok = part_b_pack.assemble(package_args, pack_root) == 0
        if not assembled_ok:
            raise ValueError("blind input package failed validation")
        package = assembled.read_text(encoding="utf-8")
    package += ("\nThe coverage checklist must use one exact line per event or pair "
                "in the form '- [x] EVENT_ID', with no other text on that line.\n")
    if package_only:
        package_path.write_text(package, encoding="utf-8")
        print(json.dumps({"package": str(package_path), "characters": len(package)}, indent=2))
        return 0
    if package_path.read_text(encoding="utf-8") != package:
        # Send only what the agent inspected.
        raise ValueError(f"the inputs changed: the package differs from the inspected {package_path}; "
                         "run --package-only again and read it")
    try:
        result = flash(budget, package, key, args.max_tokens)
    except IncompleteResponse as error:
        # Never leave a truncated table where a finished one is expected.
        partial = args.output.with_suffix(".partial.md")
        partial.write_text(error.result["text"], encoding="utf-8")
        error.saved_to = str(partial)
        raise
    args.output.write_text(result["text"], encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "text"}, indent=2))
    check_args = argparse.Namespace(repo=args.repo, analysis_dir=args.analysis, check=str(args.output))
    return part_b_pack.check(check_args)


def main() -> int:
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
    jev_parser.add_argument("--model", default="jev-latest", help="TypeSafe model name or alias")
    batch_parser = commands.add_parser("jev-batch")
    batch_parser.add_argument("input", type=Path, help="UTF-8 source shared by the checks")
    batch_parser.add_argument("checks", type=Path, help="JSON array of checks")
    batch_parser.add_argument("--model", default="jev-latest", help="TypeSafe model name or alias")
    batch_parser.add_argument("--output", type=Path, help="also write the result JSON to this file")
    draft_parser = commands.add_parser("draft-verify", help="Flash drafts cited claims; Jev judges them")
    draft_parser.add_argument("input", type=Path, help="UTF-8 source the claims must cite")
    draft_parser.add_argument("task", type=Path, help="UTF-8 file with the bounded drafting task")
    draft_parser.add_argument("--output", type=Path, required=True, help="JSON result file")
    draft_parser.add_argument("--model", default="jev-latest", help="TypeSafe model name or alias")
    draft_parser.add_argument("--max-tokens", type=int, default=12000,
                              help="Flash output budget (a 248-line source needed about 5,200; 4096 truncated it)")
    blind_parser = commands.add_parser("blind")
    blind_parser.add_argument("analysis")
    blind_parser.add_argument("--repo", default=".")
    blind_parser.add_argument("--requirements", action="append", required=True)
    blind_parser.add_argument("--contracts", action="append", required=True)
    blind_parser.add_argument("--output", type=Path, required=True)
    blind_parser.add_argument("--max-tokens", type=int, default=8192)
    blind_parser.add_argument("--package-only", action="store_true",
                              help="write <output stem>.package.md for inspection; make no call")
    args = parser.parse_args()
    for path in [getattr(args, "output", None)]:
        # Fail before anything is paid for if the result cannot be written.
        if path is not None and (path.is_dir() or not path.parent.is_dir() or not os.access(path.parent, os.W_OK)):
            print(f"LOCAL MODELS: output {path} is a directory, or {path.parent} does not exist or is not writable",
                  file=sys.stderr)
            return 1
    result: Mapping[str, object]  # printed as JSON; each command has its own shape
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
            if missing or not flash_key or not jev_key:
                raise ValueError(f"draft-verify needs {' and '.join(missing)}")
            try:
                verified = draft_verify(budget, args.input.read_text(encoding="utf-8"), str(args.input),
                                      args.task.read_text(encoding="utf-8"), flash_key, jev_key,
                                      args.model, args.max_tokens)
            except InvalidDraft as error:
                args.output.with_suffix(".draft.txt").write_text(error.text, encoding="utf-8")
                raise
            except IncompleteResponse as error:
                # A truncated draft is paid for: keep it on disk, not on stdout.
                saved = args.output.with_suffix(".draft.txt")
                saved.write_text(error.result["text"], encoding="utf-8")
                error.saved_to = str(saved)
                raise
            args.output.write_text(json.dumps(verified, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            failed = verified["verification"] is not None and verified["verification"].get("error")
            claims = verified["claims"].values()
            choices: dict[str, int] = {}
            for claim in claims:
                judgment = claim["jev"]
                if judgment and "choice" in judgment:
                    choices[judgment["choice"]] = choices.get(judgment["choice"], 0) + 1
            result = {"output": str(args.output), "claims_total": len(verified["claims"]),
                      "citation_failures": sum(claim["citation_check"] != "ok" for claim in claims),
                      "jev_choices": choices, "questions": len(verified["questions"]),
                      "draft": verified["draft"], "verification": verified["verification"]}
            if failed:
                print(json.dumps(result, ensure_ascii=False, indent=2))
                print(f"LOCAL MODELS: Jev verification failed; draft kept in {args.output}: {failed}", file=sys.stderr)
                return 1
        elif args.command == "jev-batch":
            result = jev_batch(budget, args.input.read_text(encoding="utf-8"), str(args.input),
                               json.loads(args.checks.read_text(encoding="utf-8")), os.environ.get("TYPESAFE_API_KEY"), args.model)
            if args.output:
                args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            result = jev(budget, args.input.read_text(encoding="utf-8"), args.question,
                         os.environ.get("TYPESAFE_API_KEY"), args.model)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except LedgerError as error:
        print(json.dumps(error.response, ensure_ascii=False, indent=2))
        print(f"LOCAL MODELS: {error}", file=sys.stderr)
        return 1
    except IncompleteResponse as error:
        shown: Mapping[str, object]
        if error.saved_to:
            shown = {key: value for key, value in error.result.items() if key != "text"}
            shown = {**shown, "text_saved_to": error.saved_to}
        else:
            shown = error.result
        print(json.dumps(shown, ensure_ascii=False, indent=2))
        print(f"LOCAL MODELS: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError, BudgetExceeded, urllib.error.URLError, sqlite3.Error) as error:
        print(f"LOCAL MODELS: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
