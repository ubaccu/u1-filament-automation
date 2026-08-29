import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.config import (
    ConfigError,
    ConnectionConfig,
    load_connection_config,
    normalize_service_url,
    save_connection_config,
)


class ConnectionConfigTests(unittest.TestCase):
    def test_normalizes_ip_hostname_and_ports(self):
        self.assertEqual(
            normalize_service_url("192.168.1.51", "U1"),
            "http://192.168.1.51",
        )
        self.assertEqual(
            normalize_service_url("http://127.0.0.1:7912/", "Spoolman"),
            "http://127.0.0.1:7912",
        )
        self.assertEqual(
            normalize_service_url("https://u1.local", "U1"),
            "https://u1.local",
        )

    def test_rejects_credentials_paths_and_unsupported_schemes(self):
        for value in (
            "ftp://192.168.1.51",
            "http://root:secret@192.168.1.51",
            "http://192.168.1.51/admin",
            "http://192.168.1.51:99999",
        ):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                normalize_service_url(value, "U1")

    def test_round_trip_uses_user_selected_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "connections.json"
            original = ConnectionConfig(
                "http://192.168.1.51",
                "http://127.0.0.1:7912",
            )
            self.assertEqual(save_connection_config(original, path), path)
            self.assertEqual(load_connection_config(path), original)

    def test_invalid_saved_config_is_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "connections.json"
            path.write_text(json.dumps({"moonraker_url": ""}), encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_connection_config(path)


if __name__ == "__main__":
    unittest.main()
