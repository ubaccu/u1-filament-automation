import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.orca_profile import build_detached_profile_payload


class FilamentTypePreservationTests(unittest.TestCase):
    def _build(
        self,
        base_name: str,
        inherited_type: str,
        base_type: str | None = None,
    ) -> dict:
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

            base_payload = {
                "type": "filament",
                "name": base_name,
                "inherits": "fdm_filament_base",
                "from": "system",
                "setting_id": "SYSTEM-SETTING",
                "instantiation": "true",
                "compatible_printers": ["Snapmaker U1 (0.4 nozzle)"],
            }
            if base_type is not None:
                base_payload["filament_type"] = [base_type]

            base = root / f"{base_name}.json"
            base.write_text(json.dumps(base_payload), encoding="utf-8")

            return build_detached_profile_payload(
                base,
                "Deeplee PLA PRO RAPID BLU @Snapmaker U1 (0.4 nozzle)",
                "Deeplee",
                "0056D6",
                "2.4.0",
            )

    def test_snapspeed_keeps_official_pla_type(self):
        payload = self._build("Snapmaker PLA SnapSpeed @U1", "PLA")
        self.assertEqual(payload["filament_type"], ["PLA"])
        self.assertEqual(payload["filament_vendor"], ["Deeplee"])
        self.assertEqual(payload["default_filament_colour"], ["#0056D6"])
        self.assertNotIn("inherits", payload)

    def test_fast_and_decorative_pla_families_do_not_invent_subtypes(self):
        for base_name in (
            "Snapmaker PLA Silk @U1",
            "Snapmaker PLA Wood @U1 0.4 nozzle",
            "Snapmaker PLA Translucent @U1 0.4 nozzle",
        ):
            with self.subTest(base_name=base_name):
                payload = self._build(base_name, "PLA")
                self.assertEqual(payload["filament_type"], ["PLA"])

    def test_petg_hf_and_translucent_keep_official_petg_type(self):
        for base_name in (
            "Snapmaker PETG HF @U1 0.4 nozzle",
            "Snapmaker PETG Translucent @U1 0.4 nozzle",
        ):
            with self.subTest(base_name=base_name):
                payload = self._build(base_name, "PETG")
                self.assertEqual(payload["filament_type"], ["PETG"])

    def test_cf_profiles_keep_their_official_specific_type(self):
        pla_cf = self._build("Snapmaker PLA-CF @U1 0.4 nozzle", "PLA", "PLA-CF")
        petg_cf = self._build("Snapmaker PETG-CF @U1 0.4 nozzle", "PETG", "PETG-CF")
        self.assertEqual(pla_cf["filament_type"], ["PLA-CF"])
        self.assertEqual(petg_cf["filament_type"], ["PETG-CF"])


if __name__ == "__main__":
    unittest.main()
