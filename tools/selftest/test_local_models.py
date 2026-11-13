import importlib.util
import contextlib
import io
import json
import re
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from argparse import Namespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_budget import Budget, BudgetExceeded

spec = importlib.util.spec_from_file_location("local_models", Path(__file__).resolve().parents[1] / "local_models.py")
assert spec is not None and spec.loader is not None
local_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local_models)


class ModelTest(unittest.TestCase):
    def test_flash_charges_usage_and_blocks_over_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            response = {"model": "deepseek-flash", "usage": {"prompt_tokens": 100, "completion_tokens": 50},
                        "choices": [{"message": {"content": "draft"}, "finish_reason": "stop"}]}
            with patch.object(local_models, "post_json", return_value=response):
                result = local_models.flash(budget, "task", "key", max_tokens=100)
            self.assertEqual(result["text"], "draft")
            self.assertEqual(result["cost_microdollars"], 90)
            self.assertEqual(budget.total(), 90)

    def test_failed_request_keeps_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            with patch.object(local_models, "post_json", side_effect=OSError("timeout")):
                with self.assertRaisesRegex(local_models.ProviderError, "reservation 1 kept"):
                    local_models.flash(budget, "task", "key", max_tokens=100)
            self.assertEqual(budget.calls()[0]["status"], "reserved")
            self.assertEqual(budget.total(), budget.calls()[0]["amount_microdollars"])

    def test_truncated_http_response_names_the_reservation(self):
        import http.client
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            with patch.object(local_models, "post_json", side_effect=http.client.IncompleteRead(b"{")):
                with self.assertRaisesRegex(local_models.ProviderError, "reservation 1 kept"):
                    local_models.jev(budget, "source", "question?", "key")

    def test_settle_failure_keeps_the_paid_answer(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            response = {"model": "jev-test", "usage": {"input_tokens": 100},
                        "answers": {"judgment": {"noul": 0.8}}}
            def settle(ticket, amount):
                raise sqlite3.OperationalError("database is locked")
            budget.settle = settle
            with patch.object(local_models, "post_json", return_value=response):
                with self.assertRaises(local_models.LedgerError) as caught:
                    local_models.jev(budget, "source", "question?", "key")
            self.assertEqual(caught.exception.response, response)
            self.assertIn("settle 1 5", str(caught.exception))

    def test_http_error_body_reaches_the_agent(self):
        import urllib.error
        error = urllib.error.HTTPError("https://example.test", 400, "Bad Request", {},
                                       io.BytesIO(b'{"error": "max_tokens_exceeded"}'))
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            with patch.object(local_models, "post_json", side_effect=error):
                with self.assertRaisesRegex(local_models.ProviderError, "max_tokens_exceeded"):
                    local_models.jev(budget, "source", "question?", "key")

    def test_jev_cli_passes_pinned_model(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.md").write_text("source text", encoding="utf-8")
            response = {"model": "jev-1.14.0", "usage": {"input_tokens": 10}, "answers": {"judgment": {"noul": 0.4}}}
            argv = ["local_models.py", "--ledger", str(root / "b.db"), "jev", str(root / "source.md"),
                    "Is it?", "--model", "jev-1.14.0"]
            with patch.object(sys, "argv", argv), patch.dict("os.environ", {"TYPESAFE_API_KEY": "key"}), \
                    patch.object(local_models, "post_json", return_value=response) as post, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(local_models.main(), 0)
            self.assertEqual(post.call_args.args[1]["model"], "jev-1.14.0")

    def test_blind_refuses_source_code_requirements_and_class_contracts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analysis = root / "analysis"
            analysis.mkdir()
            (analysis / "event-catalogue.md").write_text("<!-- event-ids: E01 -->\n" + "event details " * 30)
            (root / "requirements.md").write_text("requirement details " * 30)
            (root / "reqs.py").write_text("# requirements\n" + "x = 1\n" * 60)
            (root / "ev.py").write_text("class Ev:\n    def f(self):\n        return secret_impl()\n" * 20)
            budget = Budget(root / "budget.db", 2_000_000)
            for requirements, contracts in ((["reqs.py"], ["requirements.md"]), (["requirements.md"], ["ev.py:Ev"])):
                args = Namespace(repo=str(root), analysis="analysis", requirements=requirements,
                                 contracts=contracts, output=root / "blind.md", max_tokens=1000, package_only=False)
                with patch.object(local_models, "flash") as flash:
                    with self.assertRaisesRegex(ValueError, "prepared text file"):
                        local_models.blind(budget, args, "key")
                    flash.assert_not_called()

    def test_blind_package_only_makes_no_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analysis = root / "analysis"
            analysis.mkdir()
            (analysis / "event-catalogue.md").write_text("<!-- event-ids: E01 -->\n" + "event details " * 30)
            (root / "requirements.md").write_text("requirement details " * 30)
            (root / "contracts.md").write_text("contract details " * 30)
            args = Namespace(repo=str(root), analysis="analysis", requirements=["requirements.md"],
                             contracts=["contracts.md"], output=root / "blind.md", max_tokens=1000, package_only=True)
            with patch.object(local_models, "flash") as flash, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(local_models.blind(Budget(root / "budget.db", 2_000_000), args, "key"), 0)
                flash.assert_not_called()
            self.assertIn("contract details", (root / "blind.package.md").read_text())
            self.assertFalse((root / "blind.md").exists())

    def test_blind_stdout_names_only_the_kept_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analysis = root / "analysis"
            analysis.mkdir()
            (analysis / "event-catalogue.md").write_text("<!-- event-ids: E01 -->\n" + "event details " * 30)
            (root / "requirements.md").write_text("requirement details " * 30)
            (root / "contracts.md").write_text("contract details " * 30)
            args = Namespace(repo=str(root), analysis="analysis", requirements=["requirements.md"],
                             contracts=["contracts.md"], output=root / "blind.md", max_tokens=1000, package_only=True)
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(local_models.blind(Budget(root / "budget.db", 2_000_000), args, "key"), 0)
            self.assertEqual(json.loads(out.getvalue())["package"], str(root / "blind.package.md"))

    def test_sqlite_errors_are_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as directory:
            argv = ["local_models.py", "--ledger", str(Path(directory) / "missing" / "b.db"), "status"]
            stderr = io.StringIO()
            with patch.object(sys, "argv", argv), contextlib.redirect_stderr(stderr):
                self.assertEqual(local_models.main(), 1)
            self.assertIn("LOCAL MODELS:", stderr.getvalue())

    def test_citation_rejects_multiline_and_trivial_fragments(self):
        lines = ["The device connects.", "A failed device remains in FAILED."]
        self.assertIsNotNone(local_models._citation_error(lines, 1, "e"))
        self.assertIsNotNone(local_models._citation_error(lines, 1, "connects.\nA failed"))
        self.assertIn("integer", local_models._citation_error(lines, "2", "remains in FAILED"))
        self.assertIsNone(local_models._citation_error(lines, 2, "remains in FAILED"))

    def test_jev_batch_cli_writes_output_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "source.md").write_text("source text", encoding="utf-8")
            (root / "checks.json").write_text(json.dumps([{"id": "C1", "kind": "claim", "statement": "claim",
                                                           "fragment": "source text", "line": 1}]))
            response = {"model": "jev-test", "usage": {"input_tokens": 100}, "answers": {
                "choice_0": {"type": "choice", "choice": "supported", "confidence": 1.0,
                             "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}}}}
            argv = ["local_models.py", "--ledger", str(root / "b.db"), "jev-batch", str(root / "source.md"),
                    str(root / "checks.json"), "--output", str(root / "batch.json")]
            with patch.object(sys, "argv", argv), patch.dict("os.environ", {"TYPESAFE_API_KEY": "key"}), \
                    patch.object(local_models, "post_json", return_value=response), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(local_models.main(), 0)
            self.assertEqual(json.loads((root / "batch.json").read_text())["checks"]["C1"]["choice"], "supported")

    def test_jev_records_reported_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            response = {"model": "jev-test", "usage": {"input_tokens": 100},
                        "answers": {"judgment": {"noul": 0.8}}}
            with patch.object(local_models, "post_json", return_value=response):
                result = local_models.jev(budget, "source", "question?", "key")
            self.assertEqual(result["probability"], 0.8)
            self.assertEqual(budget.total(), 5)

    def test_batch_sends_one_shared_source_and_keeps_identifiers(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            checks = [
                {"id": "C1", "kind": "claim", "statement": "The device remains failed.", "fragment": "remains failed", "line": 1},
                {"id": "O1", "kind": "ordering", "statement": "Disconnect after failure", "fragment": "remains failed", "line": 1},
            ]
            choice = {"type": "choice", "choice": "unclear", "confidence": 0.3,
                      "probabilities": {"supported": 0.2, "contradicted": 0.2, "unclear": 0.6}}
            response = {"model": "jev-test", "usage": {"input_tokens": 100}, "answers": {
                "choice_0": choice, "choice_1": choice, "scope_1": {"type": "noul", "noul": 0.15}}}
            with patch.object(local_models, "post_json", return_value=response) as post:
                result = local_models.jev_batch(budget, "The device remains failed.", "requirements.md", checks, "key", model="jev-1.14.0")
            self.assertEqual(list(result["checks"]), ["C1", "O1"])
            self.assertEqual(result["checks"]["O1"]["source"], "requirements.md")
            self.assertTrue(result["checks"]["O1"]["review_required"])
            self.assertEqual(result["checks"]["O1"]["ordering_scope_probability"], 0.15)
            self.assertEqual(len(post.call_args.args[1]["questions"]), 3)
            self.assertEqual(post.call_args.args[1]["questions"]["scope_1"]["type"], "noul")
            self.assertEqual(post.call_args.args[1]["model"], "jev-1.14.0")
            self.assertEqual(budget.total(), 5)

    def test_batch_rejects_missing_fragment_before_request(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            checks = [{"id": "C1", "kind": "claim", "statement": "claim", "fragment": "absent", "line": 1}]
            with patch.object(local_models, "post_json") as post:
                with self.assertRaisesRegex(ValueError, "fragment"):
                    local_models.jev_batch(budget, "source", "source.md", checks, "key")
            post.assert_not_called()
            self.assertEqual(budget.total(), 0)

    def test_batch_missing_answer_fails_after_recording_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            checks = [{"id": "C1", "kind": "claim", "statement": "claim", "fragment": "source", "line": 1}]
            response = {"model": "jev-test", "usage": {"input_tokens": 100}, "answers": {}}
            with patch.object(local_models, "post_json", return_value=response):
                with self.assertRaisesRegex(ValueError, "answer"):
                    local_models.jev_batch(budget, "source", "source.md", checks, "key")
            self.assertEqual(budget.total(), 5)

    def test_batch_missing_scope_answer_does_not_produce_a_verdict(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            check = {"id": "O1", "kind": "ordering", "statement": "ordering", "fragment": "source", "line": 1}
            choice = {"type": "choice", "choice": "unclear", "confidence": 0.3,
                      "probabilities": {"supported": 0.2, "contradicted": 0.2, "unclear": 0.6}}
            response = {"model": "jev-test", "usage": {"input_tokens": 100}, "answers": {"choice_0": choice}}
            with patch.object(local_models, "post_json", return_value=response):
                with self.assertRaisesRegex(ValueError, "answer"):
                    local_models.jev_batch(budget, "source", "source.md", [check], "key")
            self.assertEqual(budget.total(), 5)

    def test_batch_rejects_fragment_far_from_cited_line(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            checks = [{"id": "C1", "kind": "claim", "statement": "claim", "fragment": "target", "line": 1}]
            source = "first\n" + "other\n" * 8 + "target\n"
            with patch.object(local_models, "post_json") as post:
                with self.assertRaisesRegex(ValueError, "near"):
                    local_models.jev_batch(budget, source, "source.md", checks, "key")
            post.assert_not_called()

    def test_batch_rejects_duplicate_ids_before_request(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            check = {"id": "C1", "kind": "claim", "statement": "claim", "fragment": "source", "line": 1}
            with patch.object(local_models, "post_json") as post:
                with self.assertRaisesRegex(ValueError, "duplicate"):
                    local_models.jev_batch(budget, "source", "source.md", [check, check], "key")
            post.assert_not_called()

    def test_batch_rejects_invalid_probability_after_accounting(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            check = {"id": "C1", "kind": "claim", "statement": "claim", "fragment": "source", "line": 1}
            response = {"model": "jev-test", "usage": {"input_tokens": 100}, "answers": {
                "choice_0": {"type": "choice", "choice": "supported", "confidence": 0.7,
                       "probabilities": {"supported": 1.1, "contradicted": 0, "unclear": 0}}}}
            with patch.object(local_models, "post_json", return_value=response):
                with self.assertRaisesRegex(ValueError, "invalid choice"):
                    local_models.jev_batch(budget, "source", "source.md", [check], "key")
            self.assertEqual(budget.total(), 5)

    def test_batch_rejects_inconsistent_distribution(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            check = {"id": "C1", "kind": "claim", "statement": "claim", "fragment": "source", "line": 1}
            response = {"model": "jev-test", "usage": {"input_tokens": 100}, "answers": {
                "choice_0": {"type": "choice", "choice": "supported", "confidence": 1.0,
                             "probabilities": {"supported": 0.9, "contradicted": 0.9, "unclear": 0.9}}}}
            with patch.object(local_models, "post_json", return_value=response):
                with self.assertRaisesRegex(ValueError, "distribution"):
                    local_models.jev_batch(budget, "source", "source.md", [check], "key")
            self.assertEqual(budget.total(), 5)

    def test_batch_cli_reads_source_and_check_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("source", encoding="utf-8")
            checks = root / "checks.json"
            checks.write_text(json.dumps([{"id": "C1", "kind": "claim", "statement": "claim",
                                           "fragment": "source", "line": 1}]))
            response = {"model": "jev-test", "usage": {"input_tokens": 100}, "answers": {
                "choice_0": {"type": "choice", "choice": "supported", "confidence": 1.0,
                             "probabilities": {"supported": 1.0, "contradicted": 0.0, "unclear": 0.0}}}}
            argv = ["local_models.py", "--ledger", str(root / "budget.db"), "jev-batch", str(source), str(checks)]
            output = io.StringIO()
            with patch.object(sys, "argv", argv), patch.dict("os.environ", {"TYPESAFE_API_KEY": "key"}), \
                    patch.object(local_models, "post_json", return_value=response), contextlib.redirect_stdout(output):
                self.assertEqual(local_models.main(), 0)
            self.assertEqual(json.loads(output.getvalue())["checks"]["C1"]["source"], str(source))

    def test_missing_usage_keeps_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            with patch.object(local_models, "post_json", return_value={}):
                with self.assertRaises(ValueError):
                    local_models.jev(budget, "source", "question?", "key")
            self.assertGreater(budget.total(), 0)

    def test_null_usage_is_reported_and_keeps_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            with patch.object(local_models, "post_json", return_value={"usage": None}):
                with self.assertRaises(ValueError):
                    local_models.jev(budget, "source", "question?", "key")
            self.assertGreater(budget.total(), 0)

    def test_truncated_flash_fails_after_accounting(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            response = {"model": "deepseek-flash", "usage": {"prompt_tokens": 100, "completion_tokens": 50},
                        "choices": [{"message": {"content": "partial"}, "finish_reason": "length"}]}
            with patch.object(local_models, "post_json", return_value=response):
                with self.assertRaises(ValueError):
                    local_models.flash(budget, "task", "key", max_tokens=100)
            self.assertEqual(budget.total(), 90)

    def test_large_cost_cannot_be_hidden_by_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 100)
            ticket = budget.reserve("test", 20)
            budget.settle(ticket, 120)
            self.assertEqual(budget.total(), 120)
            with self.assertRaises(BudgetExceeded):
                budget.reserve("test", 1)

    def test_blind_uses_only_packaged_inputs_and_checks_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analysis = root / "analysis"
            analysis.mkdir()
            (analysis / "event-catalogue.md").write_text("<!-- event-ids: E01 -->\n" + "event details " * 30)
            (root / "requirements.md").write_text("requirement details " * 30)
            (root / "contracts.md").write_text("contract details " * 30)
            (root / "disposition-matrix.md").write_text("SECRET MATRIX")
            budget = Budget(root / "budget.db", 2_000_000)
            args = Namespace(repo=str(root), analysis="analysis", requirements=["requirements.md"],
                             contracts=["contracts.md"], output=root / "blind.md", max_tokens=1000, package_only=False)
            self.inspect_package(budget, args)
            def fake_flash(_budget, prompt, _key, max_tokens):
                self.assertNotIn("SECRET MATRIX", prompt)
                self.assertIn("requirement details", prompt)
                return {"text": "| E01 | handle |\n\n- [x] E01\n", "finish_reason": "stop"}
            out, err = io.StringIO(), io.StringIO()
            with patch.object(local_models, "flash", side_effect=fake_flash), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(local_models.blind(budget, args, "key"), 0)
            # Second pilot: stdout is one JSON document; the coverage line goes to stderr.
            json.loads(out.getvalue())
            self.assertIn("PART-B COVERAGE: OK", err.getvalue())
            # The prompt's blockquote leaves no stray ">" line in the task text.
            self.assertNotRegex((root / "blind.package.md").read_text(), r"(?m)^>")
            self.assertTrue(args.output.is_file())
            package = root / "blind.package.md"
            self.assertTrue(package.is_file(), "the dispatched package is kept next to the output")
            self.assertIn("requirement details", package.read_text())
            self.assertNotIn("SECRET MATRIX", package.read_text())

    def test_blind_missing_coverage_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analysis = root / "analysis"
            analysis.mkdir()
            (analysis / "event-catalogue.md").write_text("<!-- event-ids: E01 -->\n" + "event details " * 30)
            (root / "requirements.md").write_text("requirement details " * 30)
            (root / "contracts.md").write_text("contract details " * 30)
            args = Namespace(repo=str(root), analysis="analysis", requirements=["requirements.md"],
                             contracts=["contracts.md"], output=root / "blind.md", max_tokens=1000, package_only=False)
            budget = Budget(root / "budget.db", 2_000_000)
            self.inspect_package(budget, args)
            with patch.object(local_models, "flash", return_value={"text": "no rows", "finish_reason": "stop"}):
                self.assertNotEqual(local_models.blind(budget, args, "key"), 0)

    def inspect_package(self, budget, args):
        inspect = Namespace(**{**vars(args), "package_only": True})
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(local_models.blind(budget, inspect, "key"), 0)

    def test_blind_requirements_may_select_one_section(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analysis = root / "analysis"
            analysis.mkdir()
            (analysis / "event-catalogue.md").write_text("<!-- event-ids: E01 -->\n" + "event details " * 30)
            (root / "requirements.md").write_text("# Other\n" + "unrelated text " * 30 + "\n# Link\n"
                                                  + "selected requirement " * 30 + "\n")
            (root / "contracts.md").write_text("contract details " * 30)
            args = Namespace(repo=str(root), analysis="analysis", requirements=["requirements.md:# Link"],
                             contracts=["contracts.md"], output=root / "blind.md", max_tokens=1000, package_only=True)
            self.inspect_package(Budget(root / "budget.db", 2_000_000), args)
            package = (root / "blind.package.md").read_text()
            self.assertIn("selected requirement", package)
            self.assertNotIn("unrelated text", package)

    def test_blind_catalogue_drops_code_fragments_and_analysis_references(self):
        # Pilot 2026-11-13: rule 3 puts code fragments into catalogue citations,
        # and the catalogue went to Part B verbatim.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analysis = root / "analysis"
            analysis.mkdir()
            (analysis / "event-catalogue.md").write_text(
                "<!-- event-ids: E01 -->\n| E01 | waiter wakes (observed-in-code, channel.go:139 "
                "(\"if !ok {\")) → Q-01, PA-21 |\n" + "event details " * 30)
            (root / "requirements.md").write_text("requirement details " * 30)
            (root / "contracts.md").write_text("contract details " * 30)
            args = Namespace(repo=str(root), analysis="analysis", requirements=["requirements.md"],
                             contracts=["contracts.md"], output=root / "blind.md", max_tokens=1000, package_only=True)
            self.inspect_package(Budget(root / "budget.db", 2_000_000), args)
            package = (root / "blind.package.md").read_text()
            self.assertIn("waiter wakes", package)
            self.assertIn("observed-in-code, channel.go)", package)
            for leaked in ("if !ok", "channel.go:139", "Q-01", "PA-21"):
                self.assertNotIn(leaked, package)

    def make_blind_inputs(self, root, catalogue=None, extraction=None):
        analysis = root / "analysis"
        analysis.mkdir()
        (analysis / "event-catalogue.md").write_text(catalogue or "<!-- event-ids: E01 -->\n" + "event details " * 30)
        if extraction is not None:
            (analysis / "extraction.md").write_text(extraction)
        (root / "requirements.md").write_text("requirement details " * 30)
        (root / "contracts.md").write_text("contract details " * 30)
        return Namespace(repo=str(root), analysis="analysis", requirements=["requirements.md"],
                         contracts=["contracts.md"], output=root / "blind.md", max_tokens=1000, package_only=True)

    def test_blind_carries_doctrine_lines_from_a_table(self):
        # Pilot 2026-11-13: '### Doctrine-line sweep' with a table was skipped silently.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.make_blind_inputs(root, extraction=(
                "## Step 1\n\n### Doctrine-line sweep\n\n| id | source | text |\n|---|---|---|\n"
                "| DOC-1 | README.md:15 | \"support for connection waiting\" |\n"
                "| DOC-2 | README.md:14 | \"an invalid connection will be discarded after a failed ping\" |\n"
                "| DOC-3 | README.md:13 | \"a timed-out connection will be closed and discarded\" |\n\n## Step 2\n"))
            self.inspect_package(Budget(root / "budget.db", 2_000_000), args)
            self.assertIn("support for connection waiting", (root / "blind.package.md").read_text())

    def test_blind_refuses_doctrine_ids_it_cannot_extract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.make_blind_inputs(root, extraction="Doctrine DOC-1 and DOC-2 are described in prose only.\n")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(ValueError):
                    local_models.blind(Budget(root / "budget.db", 2_000_000), args, "key")

    def test_blind_catalogue_strips_the_pilots_own_leaks(self):
        source = (Path(__file__).resolve().parents[2] / "docs" / "evidence" / "routed-pilot-2026-11-13"
                  / "partb" / "event-catalogue.pre-strip.md").read_text()
        partb = Path(__file__).resolve().parents[2] / "docs" / "evidence" / "routed-pilot-2026-11-13" / "partb"
        keep = local_models.part_b_pack.domain_ids((partb / "requirements.md").read_text(),
                                                   (partb / "contracts.md").read_text())
        stripped = local_models.part_b_pack.blind_catalogue(source, keep)
        for leak in (r'\("', r"\bQ-\d", r"\bL-\d", r"\bPA-\d", r"\bSYS-\d", r"\bT-[A-Z]*\d",
                     r"\.go:\d", r"\bFinding\b"):
            self.assertIsNone(re.search(leak, stripped), leak)
        self.assertIn("Get()", stripped)
        quoted = local_models.part_b_pack.blind_catalogue(
            '| E | a (channel.go:50 ("return nil, errors.New("pool is closed")")) |\n'
            '| F | b (channel.go:51 (\u201cc.mu.Lock()\u201d), see Q-01, DR-002) |\n')
        for leak in ("errors.New", "c.mu.Lock", ":50", "Q-01", "DR-002"):
            self.assertNotIn(leak, quoted)
        self.assertNotIn(", ,", quoted)
        self.assertIn("P-01a", stripped)  # pair ids are catalogue content, not analysis references

    def test_blind_catalogue_keeps_prose_and_domain_terms(self):
        strip = local_models.part_b_pack.blind_catalogue
        text = strip('Waits (channel.go:10 ("x := 1") then the caller retries, see channel.go:12 ("y := 2")).\n'
                     'Call `c.Get("key")` or fail with `errors.New("pool is closed")`; listen on :8080.\n'
                     'The T-1 threshold, level L-3 cache, an F-16, (channel.go:186, :194-196) lint L-4, see L-9.\n',
                     {"T-1", "L-3", "F-16"})
        self.assertIn("then the caller retries", text)
        self.assertNotIn("x := 1", text)
        self.assertNotIn("y := 2", text)
        for kept in ('c.Get("key")', 'errors.New("pool is closed")', ":8080", "T-1 threshold", "L-3 cache", "F-16"):
            self.assertIn(kept, text)
        for gone in (":186", ":194", "L-4", "L-9"):
            self.assertNotIn(gone, text)

    def test_blind_keeps_ids_the_requirements_use_and_reports_them(self):
        # Round 3 review: "the T-1 threshold" quoted in a doctrine line was
        # stripped from the catalogue, and an undefined "see L-9" survived.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.make_blind_inputs(
                root, catalogue="<!-- event-ids: E01 -->\n| E01 | timer fires after the T-1 threshold, see L-9 |\n"
                + "event details " * 30,
                extraction="### Doctrine lines\n\n- DOC-1 \"the T-1 threshold bounds the wait\"\n"
                + "".join(f"- DOC-{n} \"a waiting caller is woken when a connection is returned\"\n"
                          for n in range(2, 6)))
            err = io.StringIO()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
                local_models.blind(Budget(root / "budget.db", 2_000_000), args, "key")
            package = (root / "blind.package.md").read_text()
            self.assertIn("after the T-1 threshold", package)
            self.assertNotIn("L-9", package)
            self.assertIn("kept in the catalogue", err.getvalue())
            self.assertIn("T-1", err.getvalue())
            self.assertRegex(err.getvalue(), r"removed as analysis references[^\n]*L-9")

    def test_blind_refuses_a_package_with_a_leftover_fragment(self):
        # Method review round 7: an unescaped "|" inside a fragment on a table
        # row is a cell bar, so the fragment cannot be ended; the package is
        # refused rather than sent with code in it.
        for row in ('| E01 | channel.go:7 ("a | b") then | x ("y") |',
                    '| E01 | channel.go:7 ("fd := open(p, O_RDWR | O_CREATE)") | next |',
                    '| E01 | channel.go:7 (\u201ctypographic | quote\u201d) | next |'):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                args = self.make_blind_inputs(
                    root, catalogue="<!-- event-ids: E01 -->\n" + row + "\n" + "event details " * 30)
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaisesRegex(ValueError, r"never send"):
                        local_models.blind(Budget(root / "budget.db", 2_000_000), args, "key")
                self.assertFalse((root / "blind.package.md").exists())
        # Other citation spellings (round 8): an en-dash range strips like
        # "-"; "line 7", single quotes and a second file name are refused.
        P = local_models.part_b_pack
        self.assertEqual(P.blind_catalogue('| E01 | channel.go:17\u201319 ("x := 1") | next |'),
                         "| E01 | channel.go | next |")
        cited = frozenset({"channel.go", "pool.go"})
        for row in ('| z2 | channel.go:7\u20139 ("a | b") | next |', '| z4 | channel.go line 7 ("a | b") | next |',
                    "| z5 | channel.go:7 ( 'a | b' ) | next |",
                    '| z6 | channel.go:7 ("ok") and in `pool.go` ("v | w") | next |'):
            self.assertTrue(P.leftover_fragments(P.blind_catalogue(row, later_names=cited), frozenset(), cited), row)
        for row in ('| za | channel.go (line 7) ("a | b") | next |',
                    '| zb | channel.go at line 7, inside the Get loop just before the lock ("a | b") | next |',
                    '| zc | channel.go#L7 ("a | b") | n |'):
            self.assertTrue(P.leftover_fragments(P.blind_catalogue(row, later_names=cited), frozenset(), cited), row)
        self.assertEqual(P.blind_catalogue('| E01 | channel.go:17\u201419 ("x := 1") | next |'),
                         "| E01 | channel.go | next |")
        for row in ('| zf | channel.go (line 7; Get loop) ("a | b") | next |',
                    '| zg | channel.go at line 7, inside the Get loop just before the lock is taken by '
                    'the caller ("a | b") | next |'):
            self.assertTrue(P.leftover_fragments(P.blind_catalogue(row, later_names=cited), frozenset(), cited), row)
        # Known gaps (documented at _LEFT_TAIL): a quote after the citation's
        # own ";" or ")" reads as prose and is not refused.
        for row in ('| zh | channel.go:7; the code reads ("a | b") | next |',
                    '| zi | channel.go:7) and then ("a | b") | next |'):
            self.assertEqual(P.leftover_fragments(P.blind_catalogue(row, later_names=cited), frozenset(), cited),
                             [], row)
        # A dash outside a citation (a kept quote) stays verbatim.
        self.assertEqual(P.blind_catalogue('| E | README.md:4 ("open 10:30\u201311:00 daily") | n |',
                                           keep_quotes_from=frozenset({"README.md"})),
                         '| E | README.md ("open 10:30\u201311:00 daily") | n |')
        # A quoted parenthetical after the citation's own ")" or ";" is prose (code review, PR #5).
        for line in ('Waits (channel.go:10 ("x := 1")) and the doc calls it ("lazy") here.',
                     '* Get blocks (channel.go:135); callers call this ("waiting").',
                     '* Get returns ErrClosed (pool.go:6), described as ("pool is closed") in the README.',
                     "* the state (channel.go:88) is named ('Idle') by users."):
            self.assertEqual(P.leftover_fragments(P.blind_catalogue(line, later_names=cited), frozenset(), cited),
                             [], line)
        # A long token never makes the stripping quadratic.
        started = time.monotonic()
        P.blind_catalogue("a" * 100_000 + " " + "ab/" * 30_000, later_names=cited)
        self.assertLess(time.monotonic() - started, 5)
        # Quoted prose in another cell is not a fragment.
        self.assertEqual(P.leftover_fragments('| x | channel.go | Get loop retries ("until ok") |',
                                              frozenset(), cited), [])
        # Escaped as markdown tables need, the same fragment strips whole.
        self.assertEqual(local_models.part_b_pack.blind_catalogue(
            '| E01 | channel.go:7 ("fd := open(p, O_RDWR \\| O_CREATE)") | next |'), "| E01 | channel.go | next |")

    def test_blind_catalogue_round3_cases(self):
        strip = local_models.part_b_pack.blind_catalogue
        # One-argument call: prose between citations survives on its own.
        self.assertIn("then the caller retries",
                      strip('Waits (channel.go:10 ("x := 1") then the caller retries, see channel.go:12 ("y")).'))
        # A fragment that itself holds host:port or file:line tokens is removed whole.
        for text, leak in (('c (client.go:40 ("conn, err := net.Dial("tcp", "db.example.com:5432")")) |', "net.Dial"),
                           ('d (channel.go:50 ("// see util.go:3 for x")) |', "for x"),
                           ("(channel.go:175-176 and :194-196) x", ":194")):
            self.assertNotIn(leak, strip(text))
        # A quote from a prose document is normative text and stays; the line number goes.
        doc = strip('1. DOC-1 — README.md:12 ("The connection type in the pool is interface{}")',
                    keep_quotes_from=frozenset({"README.md"}))
        self.assertIn("The connection type in the pool is interface{}", doc)
        self.assertNotIn(":12", doc)
        self.assertNotIn("interface{}", strip('README.md:12 ("The connection type in the pool is interface{}")'))
        # Two citations on one line: each code fragment goes whole.
        for text in ('| e | x | channel.go:50 ("f("a") + g()") then channel.go:52 ("y := 2") |',
                     'client.go:40 ("net.Dial("tcp", "db.example.com:5432")") and pool.go:3 ("x := 1")'):
            out = strip(text)
            for leak in ("g()", "net.Dial", '")', "x := 1", "y := 2"):
                self.assertNotIn(leak, out)
        # Debris: no "see ;", no empty leading space, no double space.
        self.assertEqual(strip("(Q-01) The pool, see DR-002; then waits."), "The pool; then waits.")
        self.assertEqual(strip("A wake-up (L-4, G-01) is lost"), "A wake-up is lost")
        # "see" in prose stays; a host token after an inner quote-paren is not a citation.
        self.assertEqual(strip("The pool behaves as callers see. What the waiter does not see, the owner does."),
                         "The pool behaves as callers see. What the waiter does not see, the owner does.")
        self.assertEqual(strip('client.go:40 ("f("a") dial db.example.com:5432") |'), "client.go |")
        self.assertEqual(strip('client.go:40 ("f("a") dial db.example.com:5432 now") |'), "client.go |")
        self.assertEqual(strip("See Q-01 for details."), "For details.")
        self.assertEqual(strip("x. Cf. DR-002. y"), "x. y")
        self.assertEqual(strip("SEE Q-01 for details."), "For details.")
        # A later bare citation followed by prose still ends a fragment with inner quote-parens.
        for text, want in (('| e | channel.go:50 ("f("a") + g()") then channel.go:52 holds the rest |',
                            "| e | channel.go then channel.go holds the rest |"),
                           ('channel.go:139 ("return nil, errors.New("connection closed")") and channel.go:140 returns',
                            "channel.go and channel.go returns"),
                           ('channel.go:10 ("f("a") g") pool.go:3 holds the lock', "channel.go pool.go holds the lock"),
                           ('| e | gen_server.erl:50 ("f("a") + g()") then util.lua:52 holds |',
                            "| e | gen_server.erl then util.lua holds |")):
            self.assertEqual(strip(text, later_names=frozenset({"pool.go", "util.lua"})), want)
        # No boundary and no later citation: the fragment runs to the last quote-paren, no code tail survives.
        self.assertNotIn("rest", strip('init.lua:3 ("connect("a") ; rest") then srv.rs:5432 now'))
        # A fragment never crosses a table cell, and a later uncited quote keeps its prose.
        for text, want in (
                ('| ping_failed | callback errors | channel.go:124 ("if err != nil {") | Get loop retries ("until ok") |',
                 '| ping_failed | callback errors | channel.go | Get loop retries ("until ok") |'),
                ('| e | channel.go:10 ("x := 1") | the README says ("the pool waits") when full |',
                 '| e | channel.go | the README says ("the pool waits") when full |'),
                ('| E01 | channel.go:10 ("x := 1") | the caller calls Close("now") |',
                 '| E01 | channel.go | the caller calls Close("now") |'),
                ('| E01 | waits (channel.go:10 ("x")), then logs ("done") quickly |',
                 '| E01 | waits (channel.go), then logs ("done") quickly |'),
                ('Waits (channel.go:10 ("x := 1")) and the doc calls it ("lazy") here.',
                 'Waits (channel.go) and the doc calls it ("lazy") here.'),
                ('channel.go:8 ("a") the doc (see README.md ("wait for it")) says so',
                 'channel.go the doc (see README.md ("wait for it")) says so')):
            out = strip(text)
            self.assertEqual(out, want)
            self.assertEqual(out.count("|"), text.count("|"))
        # Outside table rows "|" is code: fragments with || or |x| strip whole; on a table row
        # an unescaped || inside balanced quotes strips too, and the cell bars stay.
        for text, want in (('- bullet: channel.go:5 ("if a || b {") and pool.go:3 holds', "- bullet: channel.go and pool.go holds"),
                           ('- bullet2: channel.go:5 ("x := a | b") then prose', "- bullet2: channel.go then prose"),
                           ('- gate: idle check (channel.go:115 ("if timeout > 0 || ok {")), then Ping',
                            "- gate: idle check (channel.go), then Ping"),
                           ("* closure (lib.rs:10 (\"v.iter().map(|x| x + 1)\")).", "* closure (lib.rs)."),
                           ('| t | channel.go:115 ("if c.idleTimeout > 0 || ok {") | next |', "| t | channel.go | next |"),
                           ('| g | channel.go:10 ("x") See Q-12; Cf. T-F05 |', "| g | channel.go |")):
            self.assertEqual(strip(text, later_names=frozenset({"pool.go"})), want)
        # Backstop: a fragment the patterns could not end is reported.
        self.assertEqual(local_models.part_b_pack.leftover_fragments('a channel.go ("if x {") b README.md ("ok")',
                                                                     frozenset({"README.md"})), ['channel.go ("'])
        # Code names in prose are not reported when only cited file names count.
        self.assertEqual(local_models.part_b_pack.leftover_fragments(
            'Calls `c.Get("key")` then errors.New("closed"); channel.go ("x', frozenset(),
            frozenset({"channel.go"})), ['channel.go ("'])
        # A table row never loses or gains a cell (round 6): fragments end inside their cell.
        P = local_models.part_b_pack
        for text, want in (('| s2 | channel.go:5 ("x") tail prose | other cell ("quoted prose") | third |',
                            '| s2 | channel.go tail prose | other cell ("quoted prose") | third |'),
                           ('| v | channel.go:7 ("a \\| b") then | x ("y") |', '| v | channel.go then | x ("y") |'),
                           ('| w | channel.go:7 ("if a || f("b") {") | pool.go:2 ("c") |', '| w | channel.go | pool.go |')):
            got = strip(text, later_names=frozenset({"pool.go"}))
            self.assertEqual(got, want)
            self.assertEqual(P.changed_table_rows(text, got), [])
        self.assertEqual(P.changed_table_rows("| a | b |", "| a b |"), ["| a b |"])
        # Removing an id never joins lines; a changed line count is reported.
        for text in ("| a | b |\n→ Q-07 continues the note\n| c | d |", "| a | x (L-4,\nG-01) |"):
            got = strip(text)
            self.assertEqual(got.count("\n"), text.count("\n"))
            self.assertEqual(P.changed_table_rows(text, got), [])
        self.assertEqual(strip("| a | b |\n→ Q-07 continues the note"), "| a | b |\ncontinues the note")
        self.assertEqual(P.changed_table_rows("a\nb", "ab"), ["line count changed: 2 -> 1"])
        # A wrapped code line that starts with "||" is prose, not a table row.
        self.assertIsNone(P._TABLE_ROW.match("|| len(c.conns) == 0 {\")),"))
        # More lines of the same file after a citation go with it (second pilot:
        # "unlock at 136, 151, 156 or 160" and ", 194" reached the package).
        for text, want in (("| a | unlock channel.go:136, 151, 156 or 160; factory call channel.go:154 |",
                            "| a | unlock channel.go; factory call channel.go |"),
                           ("| a | unlock before any Close call, channel.go:175, 194 |",
                            "| a | unlock before any Close call, channel.go |"),
                           ("channel.go:12, 3 callers wait", "channel.go, 3 callers wait"),
                           ("see channel.go:10 and 2 more", "see channel.go and 2 more")):
            self.assertEqual(strip(text), want)
        # A host whose ending looks like a file extension is not a later citation.
        self.assertEqual(strip('client.go:40 ("f("a") dial api.example.rs:8443 now") |'), "client.go |")
        # A removed sentence-initial label keeps the capital after "," or ";", in parentheses and in cells.
        self.assertEqual(strip("x. See DR-1; then y."), "x. Then y.")
        self.assertEqual(strip("See Q-01, which covers it."), "Which covers it.")
        self.assertEqual(strip("The pool waits (See Q-01)."), "The pool waits.")
        self.assertEqual(strip("| a | See Q-01 |"), "| a | |")
        # A reference word left at the end of a cell or line goes too.
        self.assertEqual(strip("| a; see T-F05 and L-4 |\nx, cf. Q-1\n"), "| a |\nx\n")
        # Quotes are kept by exact path: vendor/lib/README.md does not ride on README.md.
        self.assertEqual(strip('vendor/lib/README.md:9 ("lock A then B") and README.md:3 ("waiting")',
                               keep_quotes_from=frozenset({"README.md"})),
                         'vendor/lib/README.md and README.md ("waiting")')
        # A dangling conjunction goes with the removed id.
        self.assertEqual(strip("see T-F05 and L-4.", {"T-F05"}), "see T-F05.")
        # Removing ids keeps the separator between two clauses.
        self.assertEqual(strip("level L-3 cache; recorded as lint L-4; G-01 holds", {"L-3"}), "level L-3 cache; holds")
        self.assertEqual(strip("waits; see Q-1, Q-2 and more"), "waits; and more")

    def test_blind_keeps_source_quotes_but_not_analysis_quotes_or_glosses(self):
        # Method review round 4: quotes from the analysis's own .md files and
        # ids in a doctrine row's gloss must not reach Part B.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalogue = ("<!-- event-ids: E01 -->\n| E01 | waiter wakes (as-is-validation.md:12 (\"TestPool_Get hangs "
                         "forever after Release\"), README.md:15 (\"support for connection waiting\"), "
                         "requirements.md:3 (\"a waiter is woken on Put\")) see T-F05 |\n" + "event details " * 30)
            doctrine = "### Doctrine lines\n\n" + "".join(
                f'- DOC-{n} README.md:15 ("support for connection waiting, retry after T-1") (gloss, cf. T-F05)\n'
                for n in range(1, 5))
            args = self.make_blind_inputs(root, catalogue=catalogue, extraction=doctrine)
            (root / "analysis" / "as-is-validation.md").write_text("validation notes\n")
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                local_models.blind(Budget(root / "budget.db", 2_000_000), args, "key")
            package = (root / "blind.package.md").read_text()
            self.assertNotIn("hangs forever", package)
            self.assertIn('README.md ("support for connection waiting")', package)
            self.assertIn('requirements.md ("a waiter is woken on Put")', package)
            self.assertNotIn("T-F05", package)
            self.assertIn("retry after T-1", package)

    def test_quote_files_match_exact_paths_outside_the_analysis_directory(self):
        quote_files = local_models.part_b_pack.quote_files
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "analysis").mkdir()
            (root / "analysis" / "summary.md").write_text("x")
            got = quote_files('- DOC-1 docs/README.md:3 ("a")\n- DOC-2 analysis/open-questions.md:4 ("b")\n',
                              ["summary.md", "docs/req.md:Waiting", str(root / "contracts.md")],
                              root, root / "analysis")
            self.assertEqual(got, frozenset({"summary.md", "docs/req.md", "contracts.md", "docs/README.md"}))

    def test_cited_names_come_from_fragments_and_existing_files(self):
        cited_names = local_models.part_b_pack.cited_names
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "util.lua").write_text("x")
            text = 'a.go:1 ("x") then util.lua:5 and db.example.com:5432 and b.rs:3 holds'
            self.assertEqual(cited_names(text), frozenset({"a.go"}))
            self.assertEqual(cited_names(text, root), frozenset({"a.go", "util.lua"}))
            # A file in a subdirectory cited by its base name counts too.
            (root / "sub").mkdir()
            (root / "sub" / "deep.go").write_text("x")
            row = '| e | channel.go:50 ("f("a") + g()") then deep.go:3 holds the lock |'
            self.assertIn("deep.go", cited_names(row, root))
            self.assertEqual(local_models.part_b_pack.blind_catalogue(row, later_names=cited_names(row, root)),
                             "| e | channel.go then deep.go holds the lock |")

    def test_cli_blind_truncation_goes_to_a_partial_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.make_blind_inputs(root)
            self.inspect_package(Budget(root / "budget.db", 2_000_000), args)
            argv = ["local_models.py", "--ledger", str(root / "budget.db"), "blind", "analysis", "--repo", str(root),
                    "--requirements", "requirements.md", "--contracts", "contracts.md",
                    "--output", str(root / "blind.md")]
            out = io.StringIO()
            truncated = {"model": "deepseek-flash", "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                         "choices": [{"message": {"content": "| E01 | half"}, "finish_reason": "length"}]}
            with patch.object(sys, "argv", argv), patch.dict("os.environ", {"DEEPSEEK_API_KEY": "k"}), \
                    patch.object(local_models, "post_json", return_value=truncated), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(local_models.main(), 1)
            self.assertFalse((root / "blind.md").exists())
            self.assertEqual((root / "blind.partial.md").read_text(), "| E01 | half")
            self.assertNotIn("| E01 | half", out.getvalue())

    def test_blind_doctrine_lines_are_stripped_and_need_a_heading(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            table = ("| DOC-1 | README.md:15, channel.go:21 | \"support for connection waiting\" → SYS-7 |\n"
                     "| DOC-2 | README.md:14 | \"an invalid connection will be discarded after a failed ping\" |\n"
                     "| DOC-3 | README.md:13 | \"a timed-out connection will be closed and discarded\" |\n")
            args = self.make_blind_inputs(root, extraction="### Doctrine lines\n\n" + table)
            self.inspect_package(Budget(root / "budget.db", 2_000_000), args)
            package = (root / "blind.package.md").read_text()
            self.assertIn("support for connection waiting", package)
            for leak in ("channel.go:21", "SYS-7", "README.md:15"):
                self.assertNotIn(leak, package)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.make_blind_inputs(root, extraction="## Status\n\n" + table)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaisesRegex(ValueError, "doctrine"):
                    local_models.blind(Budget(root / "budget.db", 2_000_000), args, "key")

    def test_blind_refuses_a_stripped_catalogue_that_lost_its_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.make_blind_inputs(root, catalogue="<!-- event-ids: Q-1 E02 -->\n" + "event details " * 30)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaisesRegex(ValueError, "event ids"):
                    local_models.blind(Budget(root / "budget.db", 2_000_000), args, "key")

    def test_blind_catalogue_keeps_the_word_finding_in_prose(self):
        text = local_models.part_b_pack.blind_catalogue("Finding the oldest waiter is FIFO. Finding → Q-12 stays.\n")
        self.assertIn("Finding the oldest waiter", text)
        self.assertNotIn("Q-12", text)

    def test_part_b_pack_cli_reports_input_errors_without_a_traceback(self):
        import subprocess
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_blind_inputs(root, extraction="Doctrine DOC-1 in prose only.\n")
            run = subprocess.run([sys.executable, str(Path(local_models.__file__).parent / "part_b_pack.py"),
                                  "analysis", "--repo", str(root), "--requirements", "requirements.md",
                                  "--contracts", "contracts.md", "--out", str(root / "p.md")],
                                 capture_output=True, text=True)
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertIn("PART-B PACK:", run.stderr)
        self.assertNotIn("Traceback", run.stderr)

    def test_blind_sends_only_the_inspected_package(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analysis = root / "analysis"
            analysis.mkdir()
            (analysis / "event-catalogue.md").write_text("<!-- event-ids: E01 -->\n" + "event details " * 30)
            (root / "requirements.md").write_text("requirement details " * 30)
            (root / "contracts.md").write_text("contract details " * 30)
            budget = Budget(root / "budget.db", 2_000_000)
            args = Namespace(repo=str(root), analysis="analysis", requirements=["requirements.md"],
                             contracts=["contracts.md"], output=root / "blind.md", max_tokens=1000, package_only=False)
            with patch.object(local_models, "flash") as flash:
                with self.assertRaisesRegex(ValueError, "package-only"):
                    local_models.blind(budget, args, "key")
                self.inspect_package(budget, args)
                (root / "contracts.md").write_text("changed after inspection " * 30)
                with self.assertRaisesRegex(ValueError, "differs from the inspected"):
                    local_models.blind(budget, args, "key")
                flash.assert_not_called()
            self.assertIn("contract details", (root / "blind.package.md").read_text())


if __name__ == "__main__":
    unittest.main()
