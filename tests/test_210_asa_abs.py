import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.gui import _material_pa_k_range
from u1_filament_automation.gui_materials import MATERIAL_OPTIONS
from u1_filament_automation.models import SpoolmanInventory
from u1_filament_automation.orca_profile import build_detached_profile_payload
from u1_filament_automation.spoolman import NewSpoolRequest, plan_spool_creation
from u1_filament_automation.sync import base_profile_path, choose_base


def _request(material: str) -> NewSpoolRequest:
    return NewSpoolRequest(
        vendor="Overture",
        material=material,
        name=f"{material} TEST",
        color_hex="202020",
        density=1.04,
        diameter=1.75,
        filament_weight=1000,
        empty_spool_weight=200,
        remaining_weight=1000,
        nozzle_temperature=255,
        bed_temperature=110,
    )


class ASAABS210Tests(unittest.TestCase):
    def test_material_menu_exposes_asa_and_abs(self):
        self.assertIn("ASA", MATERIAL_OPTIONS)
        self.assertIn("ABS", MATERIAL_OPTIONS)

    def test_asa_routes_to_official_u1_profile_and_stays_asa_in_spoolman(self):
        inventory = SpoolmanInventory(url="http://127.0.0.1:7912")
        plan = plan_spool_creation(inventory, _request("ASA"))
        self.assertEqual(plan.request.material, "ASA")
        self.assertEqual(plan.request.profile_family, "ASA")
        self.assertEqual(plan.base_profile, "Snapmaker ASA @U1")
        self.assertEqual(choose_base("Overture", "ASA", "ASA TEST"), "Snapmaker ASA @U1")

    def test_abs_routes_to_official_u1_profile_and_stays_abs_in_spoolman(self):
        inventory = SpoolmanInventory(url="http://127.0.0.1:7912")
        plan = plan_spool_creation(inventory, _request("ABS"))
        self.assertEqual(plan.request.material, "ABS")
        self.assertEqual(plan.request.profile_family, "ABS")
        self.assertEqual(plan.base_profile, "Snapmaker ABS @U1")
        self.assertEqual(choose_base("Overture", "ABS", "ABS TEST"), "Snapmaker ABS @U1")

    def test_asa_and_abs_keep_standard_k_sweep(self):
        self.assertEqual(_material_pa_k_range("ASA"), (None, None, ""))
        self.assertEqual(_material_pa_k_range("ABS"), (None, None, ""))

    def test_official_asa_profile_materializes_with_asa_type_and_u1_mvf(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "fdm_filament_asa.json").write_text(
                json.dumps({
                    "type": "filament",
                    "name": "fdm_filament_asa",
                    "filament_type": ["ASA"],
                    "filament_density": ["1.04"],
                    "filament_max_volumetric_speed": ["7.6"],
                    "nozzle_temperature": ["255"],
                }),
                encoding="utf-8",
            )
            (root / "Snapmaker ASA @U1 base.json").write_text(
                json.dumps({
                    "type": "filament",
                    "name": "Snapmaker ASA @U1 base",
                    "inherits": "fdm_filament_asa",
                    "filament_max_volumetric_speed": ["8"],
                    "hot_plate_temp": ["110"],
                }),
                encoding="utf-8",
            )
            child = root / "Snapmaker ASA @U1.json"
            child.write_text(
                json.dumps({
                    "type": "filament",
                    "name": "Snapmaker ASA @U1",
                    "inherits": "Snapmaker ASA @U1 base",
                    "compatible_printers": ["Snapmaker U1 (0.4 nozzle)"],
                }),
                encoding="utf-8",
            )

            self.assertEqual(base_profile_path(root, "Snapmaker ASA @U1"), child)
            payload = build_detached_profile_payload(
                child,
                "Overture ASA TEST @Snapmaker U1 (0.4 nozzle)",
                "Overture",
                "202020",
                "2.0.10",
            )
            self.assertEqual(payload["filament_type"], ["ASA"])
            self.assertEqual(payload["filament_max_volumetric_speed"], ["8"])
            self.assertEqual(payload["hot_plate_temp"], ["110"])

    def test_official_abs_profile_materializes_with_abs_type_and_u1_mvf(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "fdm_filament_abs.json").write_text(
                json.dumps({
                    "type": "filament",
                    "name": "fdm_filament_abs",
                    "filament_type": ["ABS"],
                    "filament_density": ["1.04"],
                    "filament_max_volumetric_speed": ["16"],
                    "nozzle_temperature": ["255"],
                }),
                encoding="utf-8",
            )
            (root / "Snapmaker ABS @U1 base.json").write_text(
                json.dumps({
                    "type": "filament",
                    "name": "Snapmaker ABS @U1 base",
                    "inherits": "fdm_filament_abs",
                    "filament_max_volumetric_speed": ["8"],
                    "hot_plate_temp": ["110"],
                    "pressure_advance": ["0.02"],
                }),
                encoding="utf-8",
            )
            child = root / "Snapmaker ABS @U1.json"
            child.write_text(
                json.dumps({
                    "type": "filament",
                    "name": "Snapmaker ABS @U1",
                    "inherits": "Snapmaker ABS @U1 base",
                    "compatible_printers": ["Snapmaker U1 (0.4 nozzle)"],
                }),
                encoding="utf-8",
            )

            self.assertEqual(base_profile_path(root, "Snapmaker ABS @U1"), child)
            payload = build_detached_profile_payload(
                child,
                "Overture ABS TEST @Snapmaker U1 (0.4 nozzle)",
                "Overture",
                "202020",
                "2.0.10",
            )
            self.assertEqual(payload["filament_type"], ["ABS"])
            self.assertEqual(payload["filament_max_volumetric_speed"], ["8"])
            self.assertEqual(payload["hot_plate_temp"], ["110"])


if __name__ == "__main__":
    unittest.main()
