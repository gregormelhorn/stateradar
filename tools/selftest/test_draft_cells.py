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

SOURCE = ("func (p *Pool) Get() (net.Conn, error) {\n"
          "\tif p.closed { return nil, ErrClosed }\n"
          "\tp.waiters = append(p.waiters, req)\n"
          "}\n"
          "func (p *Pool) Close() { p.closed = true }\n"
          "\tif conn == nil || p.closed { return }\n")
TASK = {"states": [{"name": "Open", "condition": "not closed"}, {"name": "Closed", "condition": "closed"}],
        "events": [{"id": "E-GET", "gist": "a caller asks for a connection"},
                   {"id": "E-CLOSE", "gist": "the caller closes the pool"}]}
CELLS = [
    {"state": "Open", "event": "E-GET", "disposition": "handle", "line": 3,
     "fragment": "p.waiters = append(p.waiters, req)", "note": "queues the caller | unbounded"},
    {"state": "Open", "event": "E-CLOSE", "disposition": "transition", "target": "Closed", "line": 5,
     "fragment": "p.closed = true", "note": ""},
    {"state": "Closed", "event": "E-GET", "disposition": "reject", "line": 2,
     "fragment": "if p.closed { return nil, ErrClosed }", "note": "ErrClosed"},
]


def fake_flash(cells, questions=("Is the waiter queue bounded?",), text=None):
    text = text if text is not None else json.dumps({"cells": cells, "questions": list(questions)})
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
                patch.object(draft_cells.local_models, "flash", side_effect=fake_flash(cells)) as flash, \
                patch.object(draft_cells.local_models, "jev_batch", side_effect=fake_batch(choice)):
            budget = Budget(Path(directory) / "budget.db", 2_000_000)
            result = draft_cells.draft_cells(budget, SOURCE, "pool/pool.go", json.dumps(task), "f", "j", "jev-1.14.0")
            result["prompt"] = flash.call_args.args[1]
            return result

    def test_checks_every_cell_and_renders_the_matrix(self):
        bad = CELLS + [
            {"state": "Closed", "event": "E-CLOSE", "disposition": "transition", "target": "Gone", "line": 5,
             "fragment": "p.closed = true", "note": ""}]
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
        # A note's "|" becomes "/": every matrix tool splits rows on "|".
        self.assertIn('| **Open** | handle pool.go:3 ("p.waiters = append(p.waiters, req)") — queues the caller / '
                      'unbounded | transition → Closed pool.go:5 ("p.closed = true") |', matrix)
        # A cell with a problem keeps its disposition, loses its citation and
        # carries the placeholder, so the checker stays red until it is decided.
        self.assertIn("| transition → Gone → Q-? |", matrix)
        self.assertIn("- Closed x E-CLOSE: transition target 'Gone' is not a state", matrix)
        self.assertIn("- Is the waiter queue bounded?", matrix)
        self.assertTrue(result["review_required"])

    def test_vocabulary_citation_duplicates_and_missing_cells(self):
        cells = [
            {"state": "Open", "event": "E-GET", "disposition": "queue", "line": 3,
             "fragment": "p.waiters = append(p.waiters, req)"},
            {"state": "Open", "event": "E-CLOSE", "disposition": "handle", "line": 1,
             "fragment": "p.conns = nil // drained"},
            {"state": "Open", "event": "E-CLOSE", "disposition": "reject", "target": "Closed", "line": 5,
             "fragment": "p.closed = true"},
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

    def test_fragment_with_a_cell_bar_keeps_its_longest_piece(self):
        # Review round 1: "if a || b" broke the sidecar generator's row split.
        cells = [dict(CELLS[0]), dict(CELLS[1]), dict(CELLS[2]),
                 {"state": "Closed", "event": "E-CLOSE", "disposition": "ignore (documented)", "line": 6,
                  "fragment": "if conn == nil || p.closed { return }"}]
        result = self.run_draft(cells)
        last = result["cells"][3]
        self.assertEqual((last["fragment"], last["problems"]), ("p.closed { return }", []))
        self.assertIn('ignore (documented) pool.go:6 ("p.closed { return }")', result["matrix"])
        for row in result["matrix"].splitlines():
            if row.startswith("| **"):
                self.assertEqual(row.count("|"), 4, row)
        # No piece long enough: refused, not cited.
        short = self.run_draft([{**CELLS[0], "fragment": "a||b"}])
        self.assertTrue(short["cells"][0]["problems"])

    def test_holes_carry_a_question_placeholder_and_jev_doubts_are_listed(self):
        cells = [dict(c) for c in CELLS] + [
            {"state": "Closed", "event": "E-CLOSE", "disposition": "ignore (accidental)", "line": 5,
             "fragment": "p.closed = true", "note": "nothing happens\nagain"}]
        result = self.run_draft(cells, choice="contradicted")
        self.assertIn('ignore (accidental) → Q-? pool.go:5 ("p.closed = true") — nothing happens again |',
                      result["matrix"])
        self.assertIn("- Open x E-GET: jev contradicted (confidence 0.9)", result["matrix"])
        self.assertEqual(result["verification"]["error"], None)
        hole_with_problem = self.run_draft([{**CELLS[0], "disposition": "UNSPECIFIED", "line": 99}])
        self.assertIn("| UNSPECIFIED → Q-? —", hole_with_problem["matrix"])

    def test_more_than_eight_events_split_into_sub_tables_and_notes_reach_flash(self):
        events = [{"id": f"E-{n:02d}", "gist": f"event {n}"} for n in range(1, 11)]
        task = {"states": TASK["states"], "events": events, "notes": "Counters are abstracted."}
        result = self.run_draft([], task=task)
        self.assertIn("| State | E-01 | E-02 | E-03 | E-04 | E-05 | E-06 | E-07 | E-08 |", result["matrix"])
        self.assertIn("### Sub-table 2\n\n| State | E-09 | E-10 |", result["matrix"])
        self.assertEqual(len(result["missing"]), 20)
        self.assertIn("Notes from the analysis:\nCounters are abstracted.", result["prompt"])
        self.assertIn("- Open: not closed", result["prompt"])
        self.assertIn("6: \tif conn == nil || p.closed { return }", result["prompt"])

    def test_task_and_draft_shape_are_refused(self):
        for task, message in (({"states": [], "events": TASK["events"]}, "states must be a nonempty list"),
                              ({"states": TASK["states"] * 2, "events": TASK["events"]}, "duplicate name"),
                              ({"states": [{"name": "Open"}], "events": TASK["events"]}, "name and condition"),
                              ({"states": [{"name": "Open idle", "condition": "x"}], "events": TASK["events"]},
                               "one word"),
                              ({"states": TASK["states"], "events": [{"id": "E|1", "gist": "x"}]}, "one word")):
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

    def run_cli(self, root, flash_side_effect):
        local_models = draft_cells.local_models
        (root / "pool.go").write_text(SOURCE)
        (root / "task.json").write_text(json.dumps(TASK))
        argv = ["local_models.py", "--ledger", str(root / "l.db"), "--limit-microdollars", "2000000",
                "draft-cells", str(root / "pool.go"), str(root / "task.json"), "--output", str(root / "cells.json")]
        out, err = io.StringIO(), io.StringIO()
        with patch.object(local_models, "flash", side_effect=flash_side_effect), \
                patch.object(local_models, "jev_batch", side_effect=fake_batch()), \
                patch.object(sys, "argv", argv), \
                patch.dict("os.environ", {"DEEPSEEK_API_KEY": "f", "TYPESAFE_API_KEY": "j"}), \
                patch.dict(sys.modules, {"local_models": local_models}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = local_models.main()
        return code, out.getvalue(), err.getvalue()

    def test_cli_writes_json_and_matrix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code, out, _ = self.run_cli(root, fake_flash(CELLS))
            self.assertEqual(code, 0)
            summary = json.loads(out)
            self.assertEqual((summary["cells_total"], summary["missing"], summary["jev_choices"]),
                             (3, 1, {"supported": 3}))
            self.assertIn("| State | E-GET | E-CLOSE |", (root / "cells.md").read_text())
            self.assertEqual(len(json.loads((root / "cells.json").read_text())["cells"]), 3)

    def test_cli_keeps_an_invalid_draft(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code, _, err = self.run_cli(root, fake_flash([], text="I cannot do that"))
            self.assertEqual(code, 1)
            self.assertIn("Flash draft rejected", err)
            self.assertEqual((root / "cells.draft.txt").read_text(), "I cannot do that")
            self.assertFalse((root / "cells.json").exists())

    def test_compare_cli_counts_a_pair_from_two_draft_files_once(self):
        import subprocess
        draft = self.run_draft(CELLS)
        draft.pop("prompt")
        sidecar = {"cells": [{"state": "Open", "event": "E-GET", "disposition": "handle",
                              "citation": {"file": "pool/pool.go", "line": 3,
                                           "fragment": "p.waiters = append(p.waiters, req)"}}]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("a.json", "b.json"):
                (root / name).write_text(json.dumps(draft))
            (root / "analysis.json").write_text(json.dumps(sidecar))
            run = subprocess.run([sys.executable, draft_cells.__file__, "compare", str(root / "a.json"),
                                  str(root / "b.json"), "--sidecar", str(root / "analysis.json")],
                                 capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual((result["drafted"], result["second_cells_in_draft"]), (3, 3))

    def test_rendered_matrix_reaches_the_sidecar_generator(self):
        # Review round 1: the rendered block must parse as the pilot's matrix.
        import subprocess
        cells = CELLS + [{"state": "Closed", "event": "E-CLOSE", "disposition": "ignore (documented)", "line": 6,
                          "fragment": "if conn == nil || p.closed { return }", "note": "a | b"}]
        task = draft_cells.load_task(json.dumps(TASK))
        checked, missing = draft_cells.check_cells(task, cells, SOURCE.splitlines())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pool").mkdir()
            (root / "pool" / "pool.go").write_text(SOURCE)
            analysis = root / "domain-analysis" / "pool"
            analysis.mkdir(parents=True)
            (analysis / "disposition-matrix.md").write_text(
                "# m\n\n" + draft_cells.render(task, checked, missing, [], "pool/pool.go"))
            (analysis / "event-catalogue.md").write_text("<!-- event-ids: E-GET E-CLOSE -->\n")
            run = subprocess.run([sys.executable, str(Path(draft_cells.__file__).with_name("gen_analysis_sidecar.py")),
                                  str(analysis)], cwd=root, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            sidecar = json.loads((analysis / "analysis.json").read_text())
        got = {(c["state"], c["event"]): (c["disposition"], c.get("target"), c["citation"]["line"])
               for c in sidecar["cells"]}
        self.assertEqual(got, {("Open", "E-GET"): ("handle", None, 3), ("Open", "E-CLOSE"): ("transition", "Closed", 5),
                               ("Closed", "E-GET"): ("reject", None, 2),
                               ("Closed", "E-CLOSE"): ("ignore (documented)", None, 6)})
        self.assertEqual(draft_cells.compare({"cells": checked, "missing": missing}, sidecar)["by_jev_choice"],
                         {"not judged": {"unchanged": 4, "changed": 0, "dropped": 0}})

    def test_compare_counts_the_agents_changes_from_the_files(self):
        draft = self.run_draft(CELLS + [
            {"state": "Closed", "event": "E-CLOSE", "disposition": "ignore (accidental)", "line": 99,
             "fragment": "p.closed = true"}])
        sidecar = {"cells": [
            {"state": "Open", "event": "E-GET", "disposition": "handle",
             "citation": {"file": "pool/pool.go", "line": 3, "fragment": "p.waiters = append(p.waiters, req)"}},
            {"state": "Open", "event": "E-CLOSE", "disposition": "transition", "target": "Closed",
             "citation": {"file": "pool/pool.go", "line": 5, "fragment": "p.closed = true"}},
            {"state": "Closed", "event": "E-CLOSE", "disposition": "ignore (documented)",
             "citation": {"file": "pool/pool.go", "line": 5, "fragment": "p.closed = true"}},
            {"state": "Closed", "event": "E-LEN", "disposition": "handle"},
        ]}
        result = draft_cells.compare(draft, sidecar)
        self.assertEqual(result["by_jev_choice"], {"supported": {"unchanged": 2, "changed": 0, "dropped": 1},
                                                   "not judged": {"unchanged": 0, "changed": 1, "dropped": 0}})
        self.assertEqual(result["changed_fields"], {"disposition": 1, "citation": 1})
        self.assertEqual(result["final_cells_not_drafted"], ["Closed x E-LEN"])
        self.assertEqual(result["drafted"], 4)


if __name__ == "__main__":
    unittest.main()
