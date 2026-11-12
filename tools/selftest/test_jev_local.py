import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "jev_local", Path(__file__).resolve().parents[1] / "jev_local.py"
)
jev_local = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jev_local)


class JevLocalTest(unittest.TestCase):
    def test_request_uses_named_state_and_returns_probability_and_usage(self):
        response = {
            "model": "jev-test",
            "answers": {"ordering": {"type": "noul", "noul": 0.7}},
            "usage": {"input_tokens": 100, "output_tokens": 2},
        }
        with patch.object(jev_local, "post_json", return_value=response) as post:
            result = jev_local.evaluate("source text", "Does the text describe this ordering?", "key")
        self.assertEqual(result["probability"], 0.7)
        self.assertEqual(result["input_tokens"], 100)
        self.assertEqual(post.call_args.args[1]["state"], {"source": "source text"})

    def test_missing_usage_fails_instead_of_reporting_zero_cost(self):
        response = {"model": "jev-test", "answers": {"ordering": {"type": "noul", "noul": 0.7}}}
        with patch.object(jev_local, "post_json", return_value=response):
            with self.assertRaises(ValueError):
                jev_local.evaluate("source", "question", "key")


if __name__ == "__main__":
    unittest.main()
