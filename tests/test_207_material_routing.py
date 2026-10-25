import unittest

from u1_filament_automation.models import SpoolmanInventory
from u1_filament_automation.spoolman import (
    NewSpoolRequest,
    create_spool_from_plan,
    plan_spool_creation,
)
from u1_filament_automation.sync import choose_base


def _request(name: str = "DEEPLEE PLA+ 2.0 ROSSO SANGUE") -> NewSpoolRequest:
    return NewSpoolRequest(
        vendor="Deeplee",
        material="PLA Rapid",
        name=name,
        color_hex="8A0303",
        density=1.24,
        diameter=1.75,
        filament_weight=1000,
        empty_spool_weight=200,
        remaining_weight=1000,
        nozzle_temperature=225,
        bed_temperature=60,
    )


class _FakeSpoolmanClient:
    def __init__(self) -> None:
        self.filament_payload = None

    def create_vendor(self, payload):
        return {"id": 4, **payload}

    def create_filament(self, payload):
        self.filament_payload = dict(payload)
        return {"id": 9, **payload}

    def create_spool(self, payload):
        return {"id": 19, **payload}


class PLArapidMaterialRouting207Tests(unittest.TestCase):
    def test_pla_rapid_is_stored_as_pla_but_routes_to_snapspeed(self):
        inventory = SpoolmanInventory(url="http://127.0.0.1:7912")
        plan = plan_spool_creation(inventory, _request())

        self.assertEqual(plan.request.material, "PLA")
        self.assertEqual(plan.request.profile_family, "PLA RAPID")
        self.assertEqual(plan.request.name, "DEEPLEE PLA RAPID PLA+ 2.0 ROSSO SANGUE")
        self.assertEqual(plan.base_profile, "Snapmaker PLA SnapSpeed @U1")
        self.assertEqual(
            plan.profile_name,
            "Deeplee PLA RAPID PLA+ 2.0 ROSSO SANGUE @Snapmaker U1 (0.4 nozzle)",
        )

    def test_spoolman_payload_receives_plain_pla(self):
        inventory = SpoolmanInventory(url="http://127.0.0.1:7912")
        plan = plan_spool_creation(inventory, _request())
        client = _FakeSpoolmanClient()

        create_spool_from_plan(client, plan)

        self.assertIsNotNone(client.filament_payload)
        self.assertEqual(client.filament_payload["material"], "PLA")
        self.assertEqual(
            client.filament_payload["name"],
            "DEEPLEE PLA RAPID PLA+ 2.0 ROSSO SANGUE",
        )

    def test_name_without_vendor_gets_persistent_rapid_marker(self):
        inventory = SpoolmanInventory(url="http://127.0.0.1:7912")
        plan = plan_spool_creation(
            inventory,
            _request("PLA+ 2.0 ROSSO SANGUE"),
        )

        self.assertEqual(plan.request.name, "PLA RAPID PLA+ 2.0 ROSSO SANGUE")
        self.assertEqual(
            plan.profile_name,
            "Deeplee PLA RAPID PLA+ 2.0 ROSSO SANGUE @Snapmaker U1 (0.4 nozzle)",
        )

    def test_existing_rapid_marker_is_not_duplicated(self):
        inventory = SpoolmanInventory(url="http://127.0.0.1:7912")
        plan = plan_spool_creation(
            inventory,
            _request("PLA RAPID PLA+ 2.0 ROSSO SANGUE"),
        )

        self.assertEqual(plan.request.name, "PLA RAPID PLA+ 2.0 ROSSO SANGUE")

    def test_legacy_spoolman_pla_rapid_still_routes_to_snapspeed(self):
        self.assertEqual(
            choose_base("Deeplee", "PLA RAPID", "PLA+ 2.0 ROSSO SANGUE"),
            "Snapmaker PLA SnapSpeed @U1",
        )


if __name__ == "__main__":
    unittest.main()
