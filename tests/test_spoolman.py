import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from u1_filament_automation.spoolman import (
    NewSpoolRequest,
    SpoolmanClient,
    create_spool_from_plan,
    extract_spoolman_urls,
    plan_spool_creation,
    read_inventory,
)
from u1_filament_automation.models import SpoolmanInventory


class _Handler(BaseHTTPRequestHandler):
    posts = []
    payloads = {
        "/api/v1/vendor": [{"id": 1, "name": "Test"}],
        "/api/v1/filament": [{"id": 2, "vendor_id": 1, "material": "PLA"}],
        "/api/v1/spool": [{"id": 3, "filament_id": 2}],
    }

    def do_GET(self):
        if self.path not in self.payloads:
            self.send_error(404)
            return
        data = json.dumps(self.payloads[self.path]).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        self.posts.append((self.path, payload, self.headers.get("Content-Type")))
        data = json.dumps({"id": 99, **payload}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        return


class SpoolmanTests(unittest.TestCase):
    def test_reads_inventory(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            inventory = read_inventory(
                f"http://127.0.0.1:{server.server_address[1]}",
                timeout=1,
            )
            self.assertEqual(inventory.counts(), {"vendors": 1, "filaments": 1, "spools": 1})
        finally:
            server.shutdown()
            server.server_close()

    def test_extracts_spoolman_url_from_moonraker_config(self):
        payload = {
            "result": {
                "config": {
                    "spoolman": {"server": "http://192.168.1.20:7912"}
                }
            }
        }
        self.assertEqual(
            extract_spoolman_urls(payload),
            ["http://192.168.1.20:7912"],
        )

    def test_client_posts_json_to_official_spool_endpoint(self):
        _Handler.posts = []
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = SpoolmanClient(
                f"http://127.0.0.1:{server.server_address[1]}",
                timeout=1,
            )
            created = client.create_spool({"filament_id": 7, "used_weight": 0})
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(created["id"], 99)
        self.assertEqual(
            _Handler.posts,
            [
                (
                    "/api/v1/spool",
                    {"filament_id": 7, "used_weight": 0},
                    "application/json",
                )
            ],
        )


class _CreationClient:
    def __init__(self, inventory):
        self.current = inventory
        self.calls = []
        self.next_id = 100

    def _id(self):
        self.next_id += 1
        return self.next_id

    def create_vendor(self, payload):
        self.calls.append(("vendor", payload))
        result = {"id": self._id(), **payload}
        self.current.vendors.append(result)
        return result

    def create_filament(self, payload):
        self.calls.append(("filament", payload))
        result = {"id": self._id(), **payload}
        self.current.filaments.append(result)
        return result

    def create_spool(self, payload):
        self.calls.append(("spool", payload))
        result = {"id": self._id(), **payload}
        self.current.spools.append(result)
        return result


def _new_blue():
    return NewSpoolRequest(
        vendor="Deeplee",
        material="PLA",
        name="PLA PRO RAPID BLUE",
        color_hex="#2563eb",
        density=1.24,
        diameter=1.75,
        filament_weight=1000,
        empty_spool_weight=220,
        remaining_weight=850,
        nozzle_temperature=220,
        bed_temperature=60,
        location="U1 slot 3",
        lot_nr="BLUE-01",
    )


class SpoolCreationTests(unittest.TestCase):
    def test_preview_plans_complete_chain_without_writes(self):
        inventory = SpoolmanInventory(url="http://spoolman.test")
        client = _CreationClient(inventory)

        plan = plan_spool_creation(inventory, _new_blue())

        self.assertEqual(client.calls, [])
        self.assertEqual(plan.vendor_action, "create")
        self.assertEqual(plan.filament_action, "create")
        self.assertEqual(plan.base_profile, "Snapmaker PLA SnapSpeed @U1")
        self.assertEqual(
            plan.profile_name,
            "Deeplee PLA PRO RAPID BLUE @Snapmaker U1 (0.4 nozzle)",
        )

    def test_creates_vendor_filament_and_spool_with_official_fields(self):
        inventory = SpoolmanInventory(url="http://spoolman.test")
        client = _CreationClient(inventory)
        plan = plan_spool_creation(inventory, _new_blue())

        result = create_spool_from_plan(client, plan)

        self.assertTrue(result.vendor_created)
        self.assertTrue(result.filament_created)
        self.assertEqual([name for name, _ in client.calls], ["vendor", "filament", "spool"])
        vendor_payload = client.calls[0][1]
        filament_payload = client.calls[1][1]
        spool_payload = client.calls[2][1]
        self.assertEqual(vendor_payload, {"name": "Deeplee", "empty_spool_weight": 220.0})
        self.assertEqual(filament_payload["vendor_id"], result.vendor_id)
        self.assertEqual(filament_payload["material"], "PLA")
        self.assertEqual(filament_payload["name"], "PLA PRO RAPID BLUE")
        self.assertEqual(filament_payload["color_hex"], "2563EB")
        self.assertEqual(filament_payload["settings_extruder_temp"], 220)
        self.assertEqual(spool_payload["filament_id"], result.filament_id)
        self.assertEqual(spool_payload["initial_weight"], 1000.0)
        self.assertEqual(spool_payload["used_weight"], 150.0)
        self.assertEqual(spool_payload["location"], "U1 slot 3")

    def test_reuses_exact_vendor_and_filament_but_always_creates_new_spool(self):
        inventory = SpoolmanInventory(
            url="http://spoolman.test",
            vendors=[{"id": 4, "name": "DEEPLEE"}],
            filaments=[{
                "id": 9,
                "vendor": {"id": 4, "name": "Deeplee"},
                "material": "pla",
                "name": "pla pro rapid blue",
                "color_hex": "#2563eb",
            }],
        )
        client = _CreationClient(inventory)
        plan = plan_spool_creation(inventory, _new_blue())

        result = create_spool_from_plan(client, plan)

        self.assertFalse(result.vendor_created)
        self.assertFalse(result.filament_created)
        self.assertEqual(result.vendor_id, 4)
        self.assertEqual(result.filament_id, 9)
        self.assertEqual([name for name, _ in client.calls], ["spool"])

    def test_invalid_remaining_weight_is_blocked_before_any_write(self):
        invalid = NewSpoolRequest(
            **{
                **_new_blue().__dict__,
                "remaining_weight": 1200,
            }
        )
        client = _CreationClient(SpoolmanInventory(url="http://spoolman.test"))
        with self.assertRaises(ValueError):
            plan_spool_creation(client.current, invalid)
        self.assertEqual(client.calls, [])

    def test_multicolor_filament_uses_spoolman_multi_color_hexes(self):
        request = NewSpoolRequest(
            vendor="Snapmaker",
            material="PLA",
            name="Silk Sunset Ember",
            color_hex="#D9A62E",
            multi_color_hexes=("#D9A62E", "#D8494A"),
            density=1.24,
            diameter=1.75,
            filament_weight=1000,
            empty_spool_weight=0,
            remaining_weight=1000,
            nozzle_temperature=220,
            bed_temperature=65,
        )
        inventory = SpoolmanInventory(url="http://spoolman.test")
        client = _CreationClient(inventory)
        plan = plan_spool_creation(inventory, request)
        self.assertEqual(plan.base_profile, "Snapmaker PLA Silk")
        create_spool_from_plan(client, plan)
        filament_payload = client.calls[1][1]
        self.assertNotIn("color_hex", filament_payload)
        self.assertEqual(filament_payload["multi_color_hexes"], "D9A62E,D8494A")
        self.assertEqual(filament_payload["multi_color_direction"], "coaxial")

    def test_multicolor_direction_is_validated_and_sent(self):
        request = NewSpoolRequest(
            **{
                **_new_blue().__dict__,
                "multi_color_hexes": ("#D9A62E", "#D8494A"),
                "multi_color_direction": "longitudinal",
            }
        )
        inventory = SpoolmanInventory(url="http://spoolman.test")
        client = _CreationClient(inventory)
        plan = plan_spool_creation(inventory, request)
        create_spool_from_plan(client, plan)
        self.assertEqual(client.calls[1][1]["multi_color_direction"], "longitudinal")

    def test_invalid_multicolor_direction_is_blocked_before_any_write(self):
        invalid = NewSpoolRequest(
            **{
                **_new_blue().__dict__,
                "multi_color_hexes": ("#D9A62E", "#D8494A"),
                "multi_color_direction": "diagonal",
            }
        )
        with self.assertRaises(ValueError):
            invalid.validated()


if __name__ == "__main__":
    unittest.main()
