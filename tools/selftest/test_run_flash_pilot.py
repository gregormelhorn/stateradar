import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_flash_pilot import cost, tool_arguments


class FlashPilotTest(unittest.TestCase):
    def test_prices_cache_hits_and_peak_windows(self):
        usage = dict(prompt_tokens=1000, prompt_cache_hit_tokens=900,
                     prompt_cache_miss_tokens=100, completion_tokens=100)
        self.assertEqual(cost(usage, datetime(2026, 11, 14, 2, tzinfo=timezone.utc)), 78)
        self.assertEqual(cost(usage, datetime(2026, 11, 16, 2, tzinfo=timezone.utc)), 156)
        with self.assertRaises(ValueError):
            cost({**usage, 'prompt_cache_miss_tokens': 110},
                 datetime(2026, 11, 14, tzinfo=timezone.utc))

    def test_rejects_invalid_tool_call(self):
        for arguments in ('{"argv":[]}', '{"argv":[""]}', '{"argv":[3]}',
                          '{"argv":["cat"],"other":true}', '{}'):
            with self.assertRaises(ValueError):
                tool_arguments({'name': 'command', 'arguments': arguments})
        self.assertEqual(tool_arguments({'name': 'command', 'arguments': '{"argv":["cat","go.mod"]}'}),
                         ['cat', 'go.mod'])


if __name__ == '__main__':
    unittest.main()
