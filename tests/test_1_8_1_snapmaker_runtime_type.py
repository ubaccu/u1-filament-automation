import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.orca_profile import build_detached_profile_payload


class SnapmakerRuntimeFilamentType181Tests(unittest.TestCase):
    def _build(self, base_name: str) -> dict:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            parent = root / "fdm_filament_base.json"
            parent.write_text(
                json.dumps(
                    {
                        "type": "filament",
                        "name": "fdm_filament_base",
                        "from": "system",
                        "filament_type": ["PETG" if "PETG" in base_name else "PLA"],
                    }
                ),
                encoding="utf-8",
            )
            base = root / f"{base_name}.json"
            base.write_text(
                json.dumps(
                    {
                        "type": "filament",
                        "name": base_name,
                        "inherits": "fdm_filament_base",
                        "from": "system",
                        "setting_id": "SYSTEM-SETTING",
                        "instantiation": "true",
                        "compatible_printers": ["Snapmaker U1 (0.4 nozzle)"],
                    }
                ),
                encoding="utf-8",
            )
            return build_detached_profile_payload(
                base,
                "Deeplee TEST @Snapmaker U1 (0.4 nozzle)",
                "Deeplee",
                "FFFFFF",
                "2.2.53.2",
            )

    def test_translucent_matches_real_u1_runtime_type(self):
        payload = self._build("Snapmaker PLA Translucent @U1 0.4 nozzle")
        self.assertEqual(payload["filament_vendor"], ["Deeplee"])
        self.assertEqual(payload["filament_type"], ["PLA TRANSLUCENT"])
        self.assertEqual(payload["default_filament_colour"], ["#FFFFFF"])
        self.assertNotIn("inherits", payload)

    def test_special_snapmaker_families_use_sender_facing_type(self):
        expected = {
            "Snapmaker PLA SnapSpeed @U1": "PLA HIGH SPEED",
            "Snapmaker PETG HF": "PETG HIGH SPEED",
            "Snapmaker PLA Silk": "PLA SILK",
            "Snapmaker PLA Wood @U1 0.4 nozzle": "PLA WOOD",
            "Snapmaker PLA Translucent @U1 0.4 nozzle": "PLA TRANSLUCENT",
            "Snapmaker PETG Translucent @U1 0.4 nozzle": "PETG TRANSLUCENT",
            "Snapmaker PLA-CF @U1 0.4 nozzle": "PLA-CF",
            "Snapmaker PETG-CF @U1 0.4 nozzle": "PETG-CF",
        }
        for base_name, runtime_type in expected.items():
            with self.subTest(base_name=base_name):
                self.assertEqual(self._build(base_name)["filament_type"], [runtime_type])

    def test_plain_material_keeps_inherited_type(self):
        self.assertEqual(
            self._build("Snapmaker PLA Basic @U1")["filament_type"],
            ["PLA"],
        )
        self.assertEqual(
            self._build("Snapmaker PETG @U1")["filament_type"],
            ["PETG"],
        )


if __name__ == "__main__":
    unittest.main()
