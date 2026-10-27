import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.sync import (
    _build_profile_payload,
    base_profile_path,
)


class ASAABSLocalFallback211Tests(unittest.TestCase):
    def test_prefers_installed_u1_alias_when_exact_child_name_differs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            alias = root / "Snapmaker ASA @U1 0.4 nozzle.json"
            alias.write_text("{}", encoding="utf-8")
            resolved = base_profile_path(root, "Snapmaker ASA @U1")
            self.assertEqual(resolved, alias)

    def test_asa_uses_local_generic_chain_when_u1_child_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generic = root / "fdm_filament_asa.json"
            generic.write_text(
                json.dumps(
                    {
                        "type": "filament",
                        "name": "fdm_filament_asa",
                        "filament_type": ["ASA"],
                        "filament_density": ["1.04"],
                        "filament_flow_ratio": ["0.94"],
                        "filament_max_volumetric_speed": ["7.6"],
                        "nozzle_temperature": ["255"],
                        "nozzle_temperature_initial_layer": ["255"],
                    }
                ),
                encoding="utf-8",
            )

            resolved = base_profile_path(root, "Snapmaker ASA @U1")
            self.assertEqual(resolved, generic)

            payload = _build_profile_payload(
                resolved,
                "Snapmaker ASA @U1",
                "Overture ASA TEST @Snapmaker U1 (0.4 nozzle)",
                "Overture",
                "222222",
                "2.0.11",
            )
            self.assertEqual(payload["filament_type"], ["ASA"])
            self.assertEqual(payload["compatible_printers"], ["Snapmaker U1 (0.4 nozzle)"])
            self.assertEqual(payload["filament_max_volumetric_speed"], ["8"])
            self.assertEqual(payload["hot_plate_temp"], ["110"])
            self.assertEqual(payload["hot_plate_temp_initial_layer"], ["100"])
            self.assertEqual(payload["fan_max_speed"], ["15"])

    def test_abs_uses_local_generic_chain_when_u1_child_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generic = root / "fdm_filament_abs.json"
            generic.write_text(
                json.dumps(
                    {
                        "type": "filament",
                        "name": "fdm_filament_abs",
                        "filament_type": ["ABS"],
                        "filament_density": ["1.04"],
                        "filament_flow_ratio": ["0.93"],
                        "filament_max_volumetric_speed": ["16"],
                        "nozzle_temperature": ["255"],
                        "nozzle_temperature_initial_layer": ["265"],
                        "pressure_advance": ["0.03"],
                    }
                ),
                encoding="utf-8",
            )

            resolved = base_profile_path(root, "Snapmaker ABS @U1")
            self.assertEqual(resolved, generic)

            payload = _build_profile_payload(
                resolved,
                "Snapmaker ABS @U1",
                "Overture ABS TEST @Snapmaker U1 (0.4 nozzle)",
                "Overture",
                "222222",
                "2.0.11",
            )
            self.assertEqual(payload["filament_type"], ["ABS"])
            self.assertEqual(payload["compatible_printers"], ["Snapmaker U1 (0.4 nozzle)"])
            self.assertEqual(payload["filament_flow_ratio"], ["0.95"])
            self.assertEqual(payload["filament_max_volumetric_speed"], ["8"])
            self.assertEqual(payload["hot_plate_temp"], ["110"])
            self.assertEqual(payload["hot_plate_temp_initial_layer"], ["105"])
            self.assertEqual(payload["pressure_advance"], ["0.02"])

    def test_missing_all_asa_bases_still_blocks_safely(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resolved = base_profile_path(root, "Snapmaker ASA @U1")
            self.assertEqual(resolved, root / "Snapmaker ASA @U1.json")
            self.assertFalse(resolved.is_file())


if __name__ == "__main__":
    unittest.main()
