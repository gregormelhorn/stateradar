import importlib.util
import io
import json
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "jev_local", Path(__file__).resolve().parents[1] / "jev_local.py"
)
jev_local = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jev_local)


class JevLocalTest(unittest.TestCase):
    @staticmethod
    def http_error(code, retry_after=None):
        headers = {"Retry-After": retry_after} if retry_after else {}
        return urllib.error.HTTPError("https://example.test", code, "error", headers, io.BytesIO(b"{}"))

    def test_post_retries_rate_limit_and_overload_then_succeeds(self):
        ok = io.BytesIO(json.dumps({"ok": True}).encode())
        calls = [self.http_error(429, "2"), self.http_error(529), ok]
        def fake_urlopen(request, timeout):
            self.assertEqual(timeout, jev_local.TIMEOUT_SECONDS)
            result = calls.pop(0)
            if isinstance(result, Exception):
                raise result
            return result
        with patch.object(jev_local.urllib.request, "urlopen", side_effect=fake_urlopen), \
                patch.object(jev_local.time, "sleep") as sleep:
            self.assertEqual(jev_local.post_json("https://example.test", {}, "key"), {"ok": True})
        self.assertEqual(sleep.call_args_list[0].args[0], 2.0)
        self.assertEqual(sleep.call_count, 2)

    def test_post_gives_up_after_bounded_retries(self):
        with patch.object(jev_local.urllib.request, "urlopen", side_effect=lambda *a, **k: (_ for _ in ()).throw(self.http_error(529))) as urlopen, \
                patch.object(jev_local.time, "sleep"):
            with self.assertRaises(urllib.error.HTTPError):
                jev_local.post_json("https://example.test", {}, "key")
        self.assertEqual(urlopen.call_count, jev_local.MAX_RETRIES + 1)

    def test_post_retries_service_unavailable(self):
        calls = [self.http_error(503), io.BytesIO(b'{"ok": true}')]
        def fake_urlopen(request, timeout):
            result = calls.pop(0)
            if isinstance(result, Exception):
                raise result
            return result
        with patch.object(jev_local.urllib.request, "urlopen", side_effect=fake_urlopen), \
                patch.object(jev_local.time, "sleep"):
            self.assertEqual(jev_local.post_json("https://example.test", {}, "key"), {"ok": True})

    def test_non_finite_retry_after_falls_back_to_backoff(self):
        for header in ("nan", "inf", "Wed, 21 Oct 2026 07:28:00 GMT"):
            delay = jev_local._retry_delay(self.http_error(429, header), 1)
            self.assertEqual(delay, 2.0, header)

    def test_unmetered_evaluate_path_is_gone(self):
        self.assertFalse(hasattr(jev_local, "evaluate"), "every Jev call must go through the ledger")

    def test_post_does_not_retry_client_errors(self):
        with patch.object(jev_local.urllib.request, "urlopen", side_effect=self.http_error(400)) as urlopen, \
                patch.object(jev_local.time, "sleep") as sleep:
            with self.assertRaises(urllib.error.HTTPError):
                jev_local.post_json("https://example.test", {}, "key")
        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
