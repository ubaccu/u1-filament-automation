import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.orca_profile import build_detached_profile_payload


class PLARapidRuntimeTypeTests(unittest.TestCase):
    def _build(self, base_name: str, inherited_type: str = "PLA") -> dict:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            parent = root / "fdm_filament_base.json"
            parent.write_text(
                json.dumps(
                    {
                        "type": "filament",
                        "name": "fdm_filament_base",
                        "from": "system",
                        "filament_type": [inherited_type],
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
                "Deeplee PLA RAPID TEST @Snapmaker U1 (0.4 nozzle)",
                "Deeplee",
                "0056D6",
                "2.4.0",
            )

    def test_snapspeed_uses_real_u1_200205_tray_type(self):
        payload = self._build("Snapmaker PLA SnapSpeed @U1")
        self.assertEqual(payload["filament_type"], ["PLA RAPID"])
        self.assertEqual(payload["filament_vendor"], ["Deeplee"])
        self.assertEqual(payload["default_filament_colour"], ["#0056D6"])
        self.assertNotIn("inherits", payload)

    def test_plain_pla_still_keeps_plain_pla_type(self):
        payload = self._build("Snapmaker PLA Basic @U1")
        self.assertEqual(payload["filament_type"], ["PLA"])


if __name__ == "__main__":
    unittest.main()
