import importlib.util
import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from argparse import Namespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_budget import Budget, BudgetExceeded

spec = importlib.util.spec_from_file_location("local_models", Path(__file__).resolve().parents[1] / "local_models.py")
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
            with patch.object(local_models, "flash", side_effect=fake_flash):
                self.assertEqual(local_models.blind(budget, args, "key"), 0)
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
        stripped = local_models.part_b_pack.blind_catalogue(source)
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
