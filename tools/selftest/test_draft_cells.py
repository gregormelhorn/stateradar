"""Red/green cases for draft-cells: Flash drafts matrix cells, code checks them, Jev judges each."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import draft_cells  # noqa: E402
from local_budget import Budget  # noqa: E402

SOURCE = ("func (p *Pool) Get() {\n"
          "\tif p.closed { return nil, ErrClosed }\n"
          "\tp.waiters = append(p.waiters, req)\n"
          "}\n")
TASK = {"states": [{"name": "Open", "condition": "not closed"}, {"name": "Closed", "condition": "closed"}],
        "events": [{"id": "E-GET", "gist": "a caller asks for a connection"},
                   {"id": "E-CLOSE", "gist": "the caller closes the pool"}]}
CELLS = [
    {"state": "Open", "event": "E-GET", "disposition": "handle", "line": 3,
     "fragment": "p.waiters = append(p.waiters, req)", "note": "queues the caller | unbounded"},
    {"state": "Open", "event": "E-CLOSE", "disposition": "transition", "target": "Closed", "line": 2,
     "fragment": "if p.closed { return nil, ErrClosed }", "note": ""},
    {"state": "Closed", "event": "E-GET", "disposition": "reject", "line": 2,
     "fragment": "if p.closed { return nil, ErrClosed }", "note": "ErrClosed"},
]


def fake_flash(cells, questions=("Is the waiter queue bounded?",)):
    text = json.dumps({"cells": cells, "questions": list(questions)})
    return lambda _budget, _prompt, _key, _max: {"model": "deepseek-flash", "text": text, "finish_reason": "stop",
                                                 "input_tokens": 10, "output_tokens": 10,
                                                 "cost_microdollars": 5, "reservation_microdollars": 9}


def fake_batch(choice="supported"):
    def batch(_budget, _source, _ref, checks, _key, model):
        fake_batch.seen = checks
        return {"model": model, "input_tokens": 50, "cost_microdollars": 2,
                "checks": {c["id"]: {"choice": choice, "probabilities": {choice: 1.0}, "confidence": 0.9}
                           for c in checks}}
    return batch


class DraftCellsTest(unittest.TestCase):
    def run_draft(self, cells, choice="supported", task=TASK):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(draft_cells.local_models, "flash", side_effect=fake_flash(cells)), \
                patch.object(draft_cells.local_models, "jev_batch", side_effect=fake_batch(choice)):
            budget = Budget(Path(directory) / "budget.db", 2_000_000)
            return draft_cells.draft_cells(budget, SOURCE, "pool/pool.go", json.dumps(task), "f", "j", "jev-1.14.0")

    def test_checks_every_cell_and_renders_the_matrix(self):
        bad = CELLS + [
            {"state": "Closed", "event": "E-CLOSE", "disposition": "transition", "target": "Gone", "line": 2,
             "fragment": "if p.closed { return nil, ErrClosed }", "note": ""}]
        result = self.run_draft(bad)
        problems = {(c["state"], c["event"]): c["problems"] for c in result["cells"]}
        self.assertEqual(problems[("Open", "E-GET")], [])
        self.assertEqual(problems[("Closed", "E-CLOSE")], ["transition target 'Gone' is not a state"])
        self.assertEqual(result["missing"], [])
        # Only clean cells go to Jev, each as a claim that names state, event and outcome.
        sent = fake_batch.seen
        self.assertEqual(len(sent), 3)
        self.assertTrue(all(c["kind"] == "claim" for c in sent))
        self.assertIn("In state Open (not closed), when E-CLOSE (the caller closes the pool) occurs", sent[1]["statement"])
        self.assertIn("transition to Closed", sent[1]["statement"])
        matrix = result["matrix"]
        self.assertIn("<!-- states: Open, Closed -->", matrix)
        self.assertIn("| State | E-GET | E-CLOSE |", matrix)
        self.assertIn('| **Open** | handle pool.go:3 ("p.waiters = append(p.waiters, req)") — queues the caller \\| '
                      'unbounded | transition → Closed pool.go:2 ("if p.closed { return nil, ErrClosed }") |', matrix)
        # A cell with a problem keeps its disposition but loses its citation, and goes on the review list.
        self.assertIn("| transition → Gone |", matrix)
        self.assertIn("- Closed x E-CLOSE: transition target 'Gone' is not a state", matrix)
        self.assertIn("- Is the waiter queue bounded?", matrix)
        self.assertTrue(result["review_required"])

    def test_vocabulary_citation_duplicates_and_missing_cells(self):
        cells = [
            {"state": "Open", "event": "E-GET", "disposition": "queue", "line": 3,
             "fragment": "p.waiters = append(p.waiters, req)"},
            {"state": "Open", "event": "E-CLOSE", "disposition": "handle", "line": 1,
             "fragment": "p.conns = nil // drained"},
            {"state": "Open", "event": "E-CLOSE", "disposition": "reject", "target": "Closed", "line": 2,
             "fragment": "if p.closed { return nil, ErrClosed }"},
            {"state": "Shut", "event": "E-GET", "disposition": "reject", "line": 2,
             "fragment": "if p.closed { return nil, ErrClosed }"},
        ]
        result = self.run_draft(cells)
        problems = [c["problems"] for c in result["cells"]]
        self.assertIn("disposition 'queue' is outside the vocabulary", problems[0])
        self.assertIn("citation fragment missing near line 1", problems[1])
        self.assertIn("second cell for this state and event", problems[1])
        self.assertIn("only a transition has a target", problems[2])
        self.assertIn("second cell for this state and event", problems[2])
        self.assertIn("unknown state 'Shut'", problems[3])
        self.assertEqual(result["missing"], ["Closed x E-GET", "Closed x E-CLOSE"])
        self.assertIn("MISSING", result["matrix"])
        self.assertIsNone(result["verification"], "no cell was clean, so Jev was not called")

    def test_holes_carry_a_question_placeholder_and_jev_doubts_are_listed(self):
        cells = [dict(c) for c in CELLS] + [
            {"state": "Closed", "event": "E-CLOSE", "disposition": "ignore (accidental)", "line": 2,
             "fragment": "if p.closed { return nil, ErrClosed }", "note": "nothing happens"}]
        result = self.run_draft(cells, choice="contradicted")
        self.assertIn('ignore (accidental) → Q-? pool.go:2 ("if p.closed { return nil, ErrClosed }")', result["matrix"])
        self.assertIn("- Open x E-GET: jev contradicted (confidence 0.9)", result["matrix"])
        self.assertEqual(result["verification"]["error"], None)

    def test_task_and_draft_shape_are_refused(self):
        for task, message in (({"states": [], "events": TASK["events"]}, "states must be a nonempty list"),
                              ({"states": TASK["states"] * 2, "events": TASK["events"]}, "duplicate name"),
                              ({"states": [{"name": "Open"}], "events": TASK["events"]}, "name and condition")):
            with self.assertRaisesRegex(ValueError, message):
                draft_cells.load_task(json.dumps(task))
        with self.assertRaisesRegex(ValueError, "a cells list is required"):
            draft_cells._parse_cells('{"claims": []}')
        cells, questions = draft_cells._parse_cells("```json\n" + json.dumps({"cells": CELLS}) + "\n```")
        self.assertEqual((len(cells), questions), (3, []))

    def test_jev_failure_keeps_the_paid_draft(self):
        def broken(*_args):
            raise ValueError("Jev response has an invalid choice answer; usage was recorded")
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(draft_cells.local_models, "flash", side_effect=fake_flash(CELLS)), \
                patch.object(draft_cells.local_models, "jev_batch", side_effect=broken):
            result = draft_cells.draft_cells(Budget(Path(directory) / "b.db", 2_000_000), SOURCE, "pool.go",
                                             json.dumps(TASK), "f", "j")
        self.assertIn("invalid choice", result["verification"]["error"])
        self.assertEqual(len(result["cells"]), 3)

    def test_cli_writes_json_and_matrix(self):
        local_models = draft_cells.local_models
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pool.go").write_text(SOURCE)
            (root / "task.json").write_text(json.dumps(TASK))
            argv = ["local_models.py", "--ledger", str(root / "l.db"), "--limit-microdollars", "2000000",
                    "draft-cells", str(root / "pool.go"), str(root / "task.json"), "--output", str(root / "cells.json")]
            out = io.StringIO()
            with patch.object(local_models, "flash", side_effect=fake_flash(CELLS)), \
                    patch.object(local_models, "jev_batch", side_effect=fake_batch()), \
                    patch.object(sys, "argv", argv), \
                    patch.dict("os.environ", {"DEEPSEEK_API_KEY": "f", "TYPESAFE_API_KEY": "j"}), \
                    patch.dict(sys.modules, {"local_models": local_models}), \
                    contextlib.redirect_stdout(out):
                self.assertEqual(local_models.main(), 0)
            summary = json.loads(out.getvalue())
            self.assertEqual((summary["cells_total"], summary["missing"], summary["jev_choices"]),
                             (3, 1, {"supported": 3}))
            self.assertIn("| State | E-GET | E-CLOSE |", (root / "cells.md").read_text())
            self.assertEqual(len(json.loads((root / "cells.json").read_text())["cells"]), 3)


if __name__ == "__main__":
    unittest.main()
