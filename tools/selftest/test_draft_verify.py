"""Red/green cases for the Flash-draft, code-check, Jev-verify cascade step."""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_budget import Budget

spec = importlib.util.spec_from_file_location("local_models", Path(__file__).resolve().parents[1] / "local_models.py")
local_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_models)

SOURCE = "The device connects.\nA failed device remains in FAILED.\nDisconnect resets the link.\n"
CHOICE = {"type": "choice", "choice": "supported", "confidence": 0.9,
          "probabilities": {"supported": 0.9, "contradicted": 0.05, "unclear": 0.05}}


def flash_response(text, finish="stop"):
    return {"model": "deepseek-flash", "usage": {"prompt_tokens": 100, "completion_tokens": 50},
            "choices": [{"message": {"content": text}, "finish_reason": finish}]}


def jev_response(questions):
    answers = {}
    for name, question in questions.items():
        answers[name] = CHOICE if question["type"] == "choice" else {"type": "noul", "noul": 0.2}
    return {"model": "jev-test", "usage": {"input_tokens": 100}, "answers": answers}


class DraftVerifyTest(unittest.TestCase):
    def run_cascade(self, draft_text, budget):
        calls = []

        def fake_post(url, payload, key):
            calls.append((url, payload, key))
            if url == local_models.FLASH_URL:
                return flash_response(draft_text)
            return jev_response(payload["questions"])

        with patch.object(local_models, "post_json", side_effect=fake_post):
            result = local_models.draft_verify(budget, SOURCE, "req.md", "List the claims.", "fk", "jk")
        return result, calls

    def test_valid_claims_go_to_jev_and_invalid_citations_are_kept(self):
        draft = json.dumps({
            "claims": [
                {"id": "C1", "kind": "claim", "statement": "Failure is permanent.", "line": 2, "fragment": "remains in FAILED"},
                {"id": "C2", "kind": "claim", "statement": "Invented.", "line": 1, "fragment": "not in the source"},
                {"id": "O1", "kind": "ordering", "statement": "Disconnect after failure.", "line": 3, "fragment": "Disconnect resets"},
            ],
            "questions": ["Does a disconnect leave FAILED?"],
        })
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1_000_000)
            result, calls = self.run_cascade(draft, budget)
        self.assertEqual([c[0] for c in calls], [local_models.FLASH_URL, local_models.JEV_URL])
        flash_prompt = calls[0][1]["messages"][0]["content"]
        self.assertIn("2: A failed device remains in FAILED.", flash_prompt)
        self.assertEqual(calls[0][2], "fk")
        self.assertEqual(calls[1][2], "jk")
        self.assertEqual(len(calls[1][1]["questions"]), 3)  # C1, O1 choice + O1 scope; C2 never sent
        self.assertEqual(result["claims"]["C1"]["citation_check"], "ok")
        self.assertEqual(result["claims"]["C1"]["jev"]["choice"], "supported")
        self.assertIn("fragment missing", result["claims"]["C2"]["citation_check"])
        self.assertIsNone(result["claims"]["C2"]["jev"])
        self.assertEqual(result["claims"]["O1"]["jev"]["ordering_scope_probability"], 0.2)
        self.assertEqual(result["questions"], ["Does a disconnect leave FAILED?"])
        self.assertTrue(result["review_required"])
        self.assertEqual(result["source_sha256"], local_models.hashlib.sha256(SOURCE.encode()).hexdigest())

    def test_fenced_json_is_accepted(self):
        draft = "```json\n" + json.dumps({"claims": [
            {"id": "C1", "kind": "claim", "statement": "s", "line": 1, "fragment": "connects"}], "questions": []}) + "\n```"
        with tempfile.TemporaryDirectory() as directory:
            result, _ = self.run_cascade(draft, Budget(Path(directory) / "usage.db", 1_000_000))
        self.assertEqual(result["claims"]["C1"]["citation_check"], "ok")

    def test_unparseable_draft_fails_without_jev_and_keeps_text(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1_000_000)
            with self.assertRaises(local_models.InvalidDraft) as caught:
                self.run_cascade("Here are the claims: C1 ...", budget)
            self.assertEqual(budget.total(), 90)  # Flash usage recorded, no Jev reservation
        self.assertIn("Here are the claims", caught.exception.text)

    def test_structurally_invalid_claim_fails_the_draft(self):
        draft = json.dumps({"claims": [{"id": "C1", "kind": "guess", "statement": "s", "line": 1, "fragment": "x"}],
                            "questions": []})
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(local_models.InvalidDraft, "kind"):
                self.run_cascade(draft, Budget(Path(directory) / "usage.db", 1_000_000))

    def test_missing_questions_list_fails_the_draft(self):
        draft = json.dumps({"claims": []})
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(local_models.InvalidDraft, "questions"):
                self.run_cascade(draft, Budget(Path(directory) / "usage.db", 1_000_000))

    def test_no_citable_claim_skips_jev(self):
        draft = json.dumps({"claims": [{"id": "C1", "kind": "claim", "statement": "s", "line": 99, "fragment": "x"}],
                            "questions": ["What is unspecified?"]})
        with tempfile.TemporaryDirectory() as directory:
            result, calls = self.run_cascade(draft, Budget(Path(directory) / "usage.db", 1_000_000))
        self.assertEqual(len(calls), 1)
        self.assertIn("outside source", result["claims"]["C1"]["citation_check"])
        self.assertIsNone(result["verification"])

    def test_fence_with_preamble_or_one_line_is_accepted(self):
        body = json.dumps({"claims": [{"id": "C1", "kind": "claim", "statement": "s", "line": 1,
                                       "fragment": "connects"}], "questions": []})
        for draft in ("Here is the result:\n```json\n" + body + "\n```", "```json " + body + "```"):
            with tempfile.TemporaryDirectory() as directory:
                result, _ = self.run_cascade(draft, Budget(Path(directory) / "usage.db", 1_000_000))
            self.assertEqual(result["claims"]["C1"]["citation_check"], "ok")

    def test_jev_failure_keeps_the_paid_draft(self):
        draft = json.dumps({"claims": [{"id": "C1", "kind": "claim", "statement": "s", "line": 1,
                                        "fragment": "connects"}], "questions": ["Q?"]})

        def fake_post(url, payload, key):
            if url == local_models.FLASH_URL:
                return flash_response(draft)
            raise OSError("HTTP Error 400")

        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1_000_000)
            with patch.object(local_models, "post_json", side_effect=fake_post):
                result = local_models.draft_verify(budget, SOURCE, "req.md", "task", "fk", "jk")
        self.assertIn("HTTP Error 400", result["verification"]["error"])
        self.assertEqual(result["claims"]["C1"]["citation_check"], "ok")
        self.assertIsNone(result["claims"]["C1"]["jev"])
        self.assertEqual(result["questions"], ["Q?"])

    def test_ledger_error_in_jev_step_keeps_the_draft(self):
        import sqlite3
        draft = json.dumps({"claims": [{"id": "C1", "kind": "claim", "statement": "s", "line": 1,
                                        "fragment": "connects"}], "questions": []})
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1_000_000)
            original = budget.reserve
            def reserve(provider, amount):
                if provider == "jev":
                    raise sqlite3.OperationalError("database is locked")
                return original(provider, amount)
            budget.reserve = reserve
            with patch.object(local_models, "post_json", return_value=flash_response(draft)):
                result = local_models.draft_verify(budget, SOURCE, "req.md", "task", "fk", "jk")
        self.assertIn("database is locked", result["verification"]["error"])

    def test_invalid_jev_answer_reports_its_settled_usage(self):
        draft = json.dumps({"claims": [{"id": "C1", "kind": "claim", "statement": "s", "line": 1,
                                        "fragment": "connects"}], "questions": []})
        def fake_post(url, payload, key):
            if url == local_models.FLASH_URL:
                return flash_response(draft)
            return {"model": "jev-test", "usage": {"input_tokens": 100}, "answers": {}}
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1_000_000)
            with patch.object(local_models, "post_json", side_effect=fake_post):
                result = local_models.draft_verify(budget, SOURCE, "req.md", "task", "fk", "jk")
        self.assertEqual(result["verification"]["input_tokens"], 100)
        self.assertEqual(result["verification"]["cost_microdollars"], 5)
        self.assertIn("answers", result["verification"]["error"])

    def test_brace_in_preamble_or_trailer_still_parses(self):
        body = json.dumps({"claims": [{"id": "C1", "kind": "claim", "statement": "s", "line": 1,
                                       "fragment": "connects"}], "questions": []})
        for draft in ("Here {is} it:\n```json\n" + body + "\n```\nHope {this} helps", body + "\n{trailing}"):
            with tempfile.TemporaryDirectory() as directory:
                result, _ = self.run_cascade(draft, Budget(Path(directory) / "usage.db", 1_000_000))
            self.assertEqual(result["claims"]["C1"]["citation_check"], "ok")

    def test_ledger_failure_at_jev_settle_keeps_the_paid_answer(self):
        draft = json.dumps({"claims": [{"id": "C1", "kind": "claim", "statement": "s", "line": 1,
                                        "fragment": "connects"}], "questions": []})
        import sqlite3
        real_settle = Budget.settle
        calls = []

        def flaky_settle(budget, ticket, cost):
            calls.append(ticket)
            if len(calls) == 2:
                raise sqlite3.OperationalError("database is locked")
            return real_settle(budget, ticket, cost)

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(Budget, "settle", flaky_settle):
                result, _ = self.run_cascade(draft, Budget(Path(directory) / "usage.db", 1_000_000))
        verification = result["verification"]
        self.assertIn("settle", verification["error"])
        self.assertNotIn("printed above", verification["error"])
        self.assertIn("choice_0", verification["unrecorded_response"]["answers"])
        self.assertEqual(verification["question_claims"]["choice_0"], "C1")

    def test_parser_skips_wrong_shape_and_refuses_two_drafts_or_placeholders(self):
        real = {"claims": [{"id": "C1", "kind": "claim", "statement": "s", "line": 1,
                            "fragment": "connects"}], "questions": []}
        with tempfile.TemporaryDirectory() as directory:
            result, _ = self.run_cascade('note {"claims": "oops"} then ' + json.dumps(real),
                                         Budget(Path(directory) / "usage.db", 1_000_000))
        self.assertEqual(result["claims"]["C1"]["citation_check"], "ok")
        echo = {"claims": [{"id": "C1", "kind": "claim", "statement": "...", "line": 1, "fragment": "..."}],
                "questions": ["..."]}
        for text in ("Example: " + json.dumps(echo) + " Answer: " + json.dumps(real), json.dumps(echo)):
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(local_models.InvalidDraft):
                    self.run_cascade(text, Budget(Path(directory) / "usage.db", 1_000_000))

    def test_cli_rejects_output_that_is_a_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "req.md").write_text(SOURCE, encoding="utf-8")
            (root / "task.md").write_text("task", encoding="utf-8")
            argv = ["local_models.py", "--ledger", str(root / "b.db"), "draft-verify", str(root / "req.md"),
                    str(root / "task.md"), "--output", str(root)]
            with patch.object(sys, "argv", argv), \
                    patch.dict("os.environ", {"DEEPSEEK_API_KEY": "fk", "TYPESAFE_API_KEY": "jk"}), \
                    patch.object(local_models, "post_json") as post, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(local_models.main(), 1)
            post.assert_not_called()

    def test_cli_rejects_unwritable_output_before_any_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "req.md").write_text(SOURCE, encoding="utf-8")
            (root / "task.md").write_text("task", encoding="utf-8")
            argv = ["local_models.py", "--ledger", str(root / "b.db"), "draft-verify", str(root / "req.md"),
                    str(root / "task.md"), "--output", str(root / "missing" / "review.json")]
            with patch.object(sys, "argv", argv), \
                    patch.dict("os.environ", {"DEEPSEEK_API_KEY": "fk", "TYPESAFE_API_KEY": "jk"}), \
                    patch.object(local_models, "post_json") as post, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(local_models.main(), 1)
            post.assert_not_called()

    def test_cli_saves_rejected_draft_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "req.md").write_text(SOURCE, encoding="utf-8")
            (root / "task.md").write_text("task", encoding="utf-8")
            argv = ["local_models.py", "--ledger", str(root / "b.db"), "draft-verify", str(root / "req.md"),
                    str(root / "task.md"), "--output", str(root / "review.json")]
            with patch.object(sys, "argv", argv), \
                    patch.dict("os.environ", {"DEEPSEEK_API_KEY": "fk", "TYPESAFE_API_KEY": "jk"}), \
                    patch.object(local_models, "post_json", return_value=flash_response("no json here")), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(local_models.main(), 1)
            self.assertEqual((root / "review.draft.txt").read_text(), "no json here")

    def test_cli_exits_nonzero_but_writes_result_when_jev_fails(self):
        draft = json.dumps({"claims": [{"id": "C1", "kind": "claim", "statement": "s", "line": 1,
                                        "fragment": "connects"}], "questions": []})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "req.md").write_text(SOURCE, encoding="utf-8")
            (root / "task.md").write_text("task", encoding="utf-8")
            argv = ["local_models.py", "--ledger", str(root / "b.db"), "draft-verify", str(root / "req.md"),
                    str(root / "task.md"), "--output", str(root / "review.json")]

            def fake_post(url, payload, key):
                if url == local_models.FLASH_URL:
                    return flash_response(draft)
                raise OSError("timeout")

            with patch.object(sys, "argv", argv), \
                    patch.dict("os.environ", {"DEEPSEEK_API_KEY": "fk", "TYPESAFE_API_KEY": "jk"}), \
                    patch.object(local_models, "post_json", side_effect=fake_post), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(local_models.main(), 1)
            self.assertIn("timeout", json.loads((root / "review.json").read_text())["verification"]["error"])

    def test_cli_writes_result_and_requires_both_keys(self):
        draft = json.dumps({"claims": [{"id": "C1", "kind": "claim", "statement": "s", "line": 1, "fragment": "connects"}],
                            "questions": []})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "req.md").write_text(SOURCE, encoding="utf-8")
            (root / "task.md").write_text("List the claims.", encoding="utf-8")
            out = root / "review.json"
            argv = ["local_models.py", "--ledger", str(root / "b.db"), "draft-verify",
                    str(root / "req.md"), str(root / "task.md"), "--output", str(out)]

            def fake_post(url, payload, key):
                return flash_response(draft) if url == local_models.FLASH_URL else jev_response(payload["questions"])

            stderr = io.StringIO()
            with patch.object(sys, "argv", argv), patch.dict("os.environ", {"DEEPSEEK_API_KEY": "fk"}, clear=True), \
                    contextlib.redirect_stderr(stderr):
                self.assertEqual(local_models.main(), 1)
            self.assertIn("TYPESAFE_API_KEY", stderr.getvalue())
            stdout = io.StringIO()
            with patch.object(sys, "argv", argv), \
                    patch.dict("os.environ", {"DEEPSEEK_API_KEY": "fk", "TYPESAFE_API_KEY": "jk"}), \
                    patch.object(local_models, "post_json", side_effect=fake_post), \
                    contextlib.redirect_stdout(stdout):
                self.assertEqual(local_models.main(), 0)
            summary = json.loads(stdout.getvalue())
            self.assertNotIn("claims", summary, "stdout carries a summary, the full result goes to --output")
            self.assertEqual(summary["claims_total"], 1)
            self.assertEqual(summary["output"], str(out))
            self.assertEqual(json.loads(out.read_text())["claims"]["C1"]["jev"]["choice"], "supported")


if __name__ == "__main__":
    unittest.main()
