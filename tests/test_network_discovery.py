import json
import unittest

from u1_filament_automation.network_discovery import (
    MoonrakerCandidate,
    discover_moonraker_candidates,
    lan_hosts,
    probe_moonraker,
)


class _Headers:
    def get_content_charset(self):
        return "utf-8"


class _Response:
    def __init__(self, payload):
        self.headers = _Headers()
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


class NetworkDiscoveryTests(unittest.TestCase):
    def test_lan_hosts_are_bounded_to_private_24_and_exclude_local(self):
        hosts = lan_hosts(["192.168.1.44"])
        self.assertEqual(len(hosts), 253)
        self.assertIn("192.168.1.1", hosts)
        self.assertIn("192.168.1.254", hosts)
        self.assertNotIn("192.168.1.44", hosts)

    def test_probe_uses_only_get_and_requires_snapmaker_u1_object(self):
        seen = []

        def opener(request, timeout):
            seen.append((request.full_url, request.get_method(), timeout))
            if request.full_url.endswith("/server/info"):
                return _Response({"result": {"klippy_connected": True, "components": []}})
            return _Response(
                {
                    "result": {
                        "objects": [
                            "toolhead",
                            "print_stats",
                            "machine_state_manager",
                        ]
                    }
                }
            )

        candidate = probe_moonraker("192.168.1.51", timeout=0.2, opener=opener)
        self.assertEqual(candidate, MoonrakerCandidate("http://192.168.1.51", "192.168.1.51"))
        self.assertEqual(
            seen,
            [
                ("http://192.168.1.51/server/info", "GET", 0.2),
                ("http://192.168.1.51/printer/objects/list", "GET", 0.2),
            ],
        )

    def test_probe_rejects_generic_moonraker_without_u1_object(self):
        def opener(request, timeout):
            if request.full_url.endswith("/server/info"):
                return _Response({"result": {"klippy_connected": True}})
            return _Response({"result": {"objects": ["toolhead", "print_stats"]}})

        self.assertIsNone(probe_moonraker("192.168.1.99", opener=opener))

    def test_probe_rejects_non_moonraker_json(self):
        def opener(request, timeout):
            return _Response({"status": "ok"})

        self.assertIsNone(probe_moonraker("192.168.1.99", opener=opener))

    def test_discovery_returns_only_hosts_that_answer_as_u1(self):
        wanted = "192.168.9.88"

        def fake_probe(host, timeout):
            if host == wanted:
                return MoonrakerCandidate(f"http://{host}", host)
            return None

        found = discover_moonraker_candidates(
            addresses=["192.168.9.10"],
            timeout=0.01,
            max_workers=16,
            probe=fake_probe,
        )
        self.assertEqual(found, (MoonrakerCandidate(f"http://{wanted}", wanted),))


if __name__ == "__main__":
    unittest.main()
