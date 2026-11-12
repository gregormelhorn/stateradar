import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_budget import Budget, BudgetExceeded


class BudgetTest(unittest.TestCase):
    def test_reservations_survive_restart_and_block_overspend(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "budget.sqlite"
            budget = Budget(path, 2_000_000)
            reservation = budget.reserve("jev", 1_200_000)
            with self.assertRaises(BudgetExceeded):
                Budget(path, 2_000_000).reserve("flash", 900_000)
            budget.settle(reservation, 200_000)
            Budget(path, 2_000_000).reserve("flash", 900_000)

    def test_unknown_call_keeps_reserved_amount(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "budget.sqlite", 100)
            budget.reserve("jev", 100)
            with self.assertRaises(BudgetExceeded):
                budget.reserve("jev", 1)

    def test_settlement_above_reservation_records_real_amount(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "budget.sqlite", 100)
            reservation = budget.reserve("flash", 20)
            budget.settle(reservation, 101)
            with self.assertRaises(BudgetExceeded):
                budget.reserve("flash", 1)

    def test_limit_can_be_raised_without_losing_existing_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "budget.sqlite"
            budget = Budget(path, 100)
            budget.reserve("jev", 100)
            budget.set_limit(200)
            Budget(path, 200).reserve("flash", 100)
            self.assertEqual(Budget(path, 200).total(), 200)

    def test_concurrent_reservations_cannot_share_the_same_balance(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = Budget(Path(directory) / "budget.sqlite", 100)
            def reserve():
                try:
                    budget.reserve("flash", 60)
                    return "reserved"
                except BudgetExceeded:
                    return "blocked"
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda _: reserve(), range(2)))
            self.assertCountEqual(results, ["reserved", "blocked"])


if __name__ == "__main__":
    unittest.main()
