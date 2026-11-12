import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "jev_eval.py"


class JevEvaluationTest(unittest.TestCase):
    def run_evaluation(self, labels, batch):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "labels.json").write_text(json.dumps(labels))
            (root / "batch.json").write_text(json.dumps(batch))
            return subprocess.run([sys.executable, str(TOOL), str(root / "labels.json"),
                                   str(root / "batch.json")], capture_output=True, text=True)

    def examples(self):
        checks = {}
        labels = {}
        for ident, expected, choice in [("a", "supported", "supported"),
                                         ("b", "contradicted", "supported"),
                                         ("c", "supported", "unclear")]:
            evidence = {"kind": "claim", "statement": ident, "source": "req.md",
                        "line": 1, "fragment": "text"}
            labels[ident] = {**evidence, "expected": expected, "reviewer": "reviewer"}
            checks[ident] = {**evidence, "choice": choice, "review_required": True}
        return ({"source_sha256": "a" * 64, "checks": labels},
                {"source_sha256": "a" * 64, "model": "jev-test", "input_tokens": 100,
                 "cost_microdollars": 5, "checks": checks})

    def test_reports_false_support_and_unclear_separately(self):
        labels, batch = self.examples()
        run = self.run_evaluation(labels, batch)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["exact_matches"], 1)
        self.assertEqual(result["false_support_ids"], ["b"])
        self.assertEqual(result["unclear_ids"], ["c"])
        self.assertEqual(result["cost_microdollars"], 5)

    def test_refuses_missing_or_stale_cases(self):
        labels, batch = self.examples()
        del batch["checks"]["b"]
        run = self.run_evaluation(labels, batch)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("IDs differ", run.stderr)
        labels, batch = self.examples()
        batch["checks"]["b"]["statement"] = "different claim"
        run = self.run_evaluation(labels, batch)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("identity differs", run.stderr)
        labels, batch = self.examples()
        batch["source_sha256"] = "b" * 64
        run = self.run_evaluation(labels, batch)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("source hash", run.stderr)

    def test_refuses_unattributed_and_empty_labels(self):
        labels, batch = self.examples()
        labels["checks"]["a"]["reviewer"] = ""
        run = self.run_evaluation(labels, batch)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("reviewer", run.stderr)
        labels["checks"] = {}
        run = self.run_evaluation(labels, batch)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("nonempty", run.stderr)


if __name__ == "__main__":
    unittest.main()
