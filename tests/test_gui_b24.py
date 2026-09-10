import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation import gui, pa_profile
from u1_filament_automation.gui_b24 import install_b24_patch
from u1_filament_automation.models import SpoolmanInventory
from u1_filament_automation.pa import PAResult, PASuite
from u1_filament_automation.pa_profile import CalibrationIdentity, PAProfileError
from u1_filament_automation.profile_equivalence import profile_names_equivalent
from u1_filament_automation.sync import make_profile_name, sync_profiles


EXPECTED = "eSUN PLA ePLA-Lite Rosso Fuoco @Snapmaker U1 (0.4 nozzle)"
LEGACY = "eSUN ePLA-Lite Rosso Fuoco @Snapmaker U1 (0.4 nozzle)"


class B24EquivalentProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install_b24_patch(gui)

    def _inventory(self) -> SpoolmanInventory:
        return SpoolmanInventory(
            url="http://spoolman.test",
            vendors=[{"id": 7, "name": "eSUN"}],
            filaments=[{
                "id": 15,
                "vendor_id": 7,
                "material": "PLA",
                "name": "ePLA-Lite Rosso Fuoco",
                "color_hex": "BB2028",
            }],
            spools=[{"id": 14, "filament_id": 15}],
        )

    def test_equivalence_is_narrow_and_matches_epla_legacy_name(self):
        self.assertTrue(profile_names_equivalent(EXPECTED, LEGACY))
        self.assertTrue(profile_names_equivalent(LEGACY, EXPECTED))
        self.assertFalse(
            profile_names_equivalent(
                "Brand PLA Basic Red @Snapmaker U1 (0.4 nozzle)",
                "Brand Basic Red @Snapmaker U1 (0.4 nozzle)",
            )
        )
        self.assertFalse(
            profile_names_equivalent(
                "Brand PETG ePLA-Lite Red @Snapmaker U1 (0.4 nozzle)",
                LEGACY,
            )
        )

    def test_sync_reuses_one_equivalent_profile_without_creating_duplicate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            (system_dir / "Snapmaker PLA Basic @U1.json").write_text(
                json.dumps({"version": "2.2.53.2"}), encoding="utf-8"
            )
            legacy_path = user_dir / f"{LEGACY}.json"
            legacy_path.write_text(
                json.dumps({
                    "name": LEGACY,
                    "filament_settings_id": [LEGACY],
                    "inherits": "Snapmaker PLA Basic @U1",
                    "default_filament_colour": ["#BB2028"],
                }),
                encoding="utf-8",
            )

            self.assertEqual(
                make_profile_name("eSUN", "PLA", "ePLA-Lite Rosso Fuoco"),
                EXPECTED,
            )
            report = sync_profiles(
                self._inventory(), user_dir, system_dir, apply=True
            )

            self.assertEqual(report.actions[0].status, "existing")
            self.assertEqual(len(list(user_dir.glob("*.json"))), 1)
            self.assertFalse((user_dir / f"{EXPECTED}.json").exists())
            self.assertEqual(gui.find_profile_path(user_dir, EXPECTED), legacy_path.resolve())

    def test_pa_update_targets_equivalent_existing_json_and_keeps_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            user_dir = Path(temporary)
            legacy_path = user_dir / f"{LEGACY}.json"
            legacy_path.write_text(
                json.dumps({
                    "name": LEGACY,
                    "inherits": "Snapmaker PLA Basic @U1",
                    "custom_value": ["keep"],
                }, indent=4) + "\n",
                encoding="utf-8",
            )
            suite = PASuite((
                PAResult("low_anchor", 0.016, 7.5, 2000),
                PAResult("high_flow", 0.018, 14.9, 10000),
            ))

            report = pa_profile.update_pa_profile(
                user_dir,
                EXPECTED,
                CalibrationIdentity(spool_id=14),
                suite,
                apply=True,
            )

            self.assertEqual(report.status, "updated")
            self.assertEqual(report.profile_path, legacy_path.resolve())
            self.assertIsNotNone(report.backup_path)
            self.assertTrue(report.backup_path.is_file())
            payload = json.loads(legacy_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["custom_value"], ["keep"])
            self.assertEqual(payload["adaptive_pressure_advance"], ["1"])
            self.assertFalse((user_dir / f"{EXPECTED}.json").exists())

    def test_multiple_equivalent_profiles_block_pa_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            user_dir = Path(temporary)
            for filename, name in (
                ("legacy-a.json", LEGACY),
                ("legacy-b.json", "eSUN ePLA Lite Rosso Fuoco @Snapmaker U1 (0.4 nozzle)"),
            ):
                (user_dir / filename).write_text(
                    json.dumps({"name": name}), encoding="utf-8"
                )

            with self.assertRaises(PAProfileError):
                gui.find_profile_path(user_dir, EXPECTED)


if __name__ == "__main__":
    unittest.main()
