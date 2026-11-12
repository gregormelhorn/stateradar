import importlib.util
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
                with self.assertRaises(OSError):
                    local_models.flash(budget, "task", "key", max_tokens=100)
            self.assertGreater(budget.total(), 0)

    def test_jev_records_reported_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "usage.db", 1000)
            response = {"model": "jev-test", "usage": {"input_tokens": 100},
                        "answers": {"judgment": {"noul": 0.8}}}
            with patch.object(local_models, "post_json", return_value=response):
                result = local_models.jev(budget, "source", "question?", "key")
            self.assertEqual(result["probability"], 0.8)
            self.assertEqual(budget.total(), 5)

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
                             contracts=["contracts.md"], output=root / "blind.md", max_tokens=1000)
            def fake_flash(_budget, prompt, _key, max_tokens):
                self.assertNotIn("SECRET MATRIX", prompt)
                self.assertIn("requirement details", prompt)
                return {"text": "| E01 | handle |\n\n- [x] E01\n", "finish_reason": "stop"}
            with patch.object(local_models, "flash", side_effect=fake_flash):
                self.assertEqual(local_models.blind(budget, args, "key"), 0)
            self.assertTrue(args.output.is_file())

    def test_blind_missing_coverage_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            analysis = root / "analysis"
            analysis.mkdir()
            (analysis / "event-catalogue.md").write_text("<!-- event-ids: E01 -->\n" + "event details " * 30)
            (root / "requirements.md").write_text("requirement details " * 30)
            (root / "contracts.md").write_text("contract details " * 30)
            args = Namespace(repo=str(root), analysis="analysis", requirements=["requirements.md"],
                             contracts=["contracts.md"], output=root / "blind.md", max_tokens=1000)
            with patch.object(local_models, "flash", return_value={"text": "no rows", "finish_reason": "stop"}):
                self.assertNotEqual(local_models.blind(Budget(root / "budget.db", 2_000_000), args, "key"), 0)


if __name__ == "__main__":
    unittest.main()
