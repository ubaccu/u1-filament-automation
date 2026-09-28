import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import u1_filament_automation.printer as printer
import u1_filament_automation.spoolman as spoolman


class _Headers:
    @staticmethod
    def get_content_charset():
        return "utf-8"


class _Response:
    headers = _Headers()

    def __init__(self, body=b'{"ok": true}'):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.body


class U1FA201HotfixTests(unittest.TestCase):
    def _check_crlf_asset(self, name: str, expected_sha256: str) -> None:
        canonical = printer._canonical_asset_bytes(printer.bundled_asset(name).read_bytes())
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), expected_sha256)

        crlf = canonical.replace(b"\n", b"\r\n")
        self.assertNotEqual(hashlib.sha256(crlf).hexdigest(), expected_sha256)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_bytes(crlf)
            with patch.object(printer, "bundled_asset", return_value=path):
                validated = printer.validated_asset(name, expected_sha256)

        self.assertEqual(validated, canonical)
        self.assertNotIn(b"\r\n", validated)

    def test_windows_crlf_macro_205_is_canonicalized_before_hashing(self):
        self._check_crlf_asset(
            "adaptive_pa_macro_205.cfg",
            printer.ADAPTIVE_PA_MACRO_205_SHA256,
        )

    def test_windows_crlf_calibrator_205_is_canonicalized_before_hashing(self):
        self._check_crlf_asset(
            "flow_calibrator_205_candidate.py",
            printer.CANDIDATE_205,
        )

    def test_spoolman_default_https_uses_system_plus_bundled_ca_context(self):
        captured = {}
        marker = object()

        def fake_urlopen(request, timeout, context):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["context"] = context
            return _Response()

        with (
            patch.object(spoolman, "urlopen", side_effect=fake_urlopen),
            patch.object(spoolman, "github_ssl_context", return_value=marker),
        ):
            result = spoolman.request_json(
                "https://spoolman.example/api/v1/vendor",
                timeout=4.0,
            )

        self.assertEqual(result, {"ok": True})
        self.assertEqual(captured["url"], "https://spoolman.example/api/v1/vendor")
        self.assertEqual(captured["timeout"], 4.0)
        self.assertIs(captured["context"], marker)

    def test_spoolman_custom_opener_remains_injectable(self):
        captured = {}

        def custom_opener(request, timeout):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            return _Response()

        result = spoolman.request_json(
            "http://127.0.0.1:7912/api/v1/vendor",
            timeout=1.5,
            opener=custom_opener,
        )
        self.assertEqual(result, {"ok": True})
        self.assertEqual(captured["timeout"], 1.5)


if __name__ == "__main__":
    unittest.main()
