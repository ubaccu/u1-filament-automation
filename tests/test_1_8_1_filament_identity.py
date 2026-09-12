import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.models import SpoolmanInventory
from u1_filament_automation.orca_profile import user_filament_id
from u1_filament_automation.sync import sync_profiles


class FilamentIdentity181Tests(unittest.TestCase):
    @staticmethod
    def _inventory(vendor: str = "Deeplee") -> SpoolmanInventory:
        return SpoolmanInventory(
            url="http://spoolman.test",
            vendors=[{"id": 1, "name": vendor}],
            filaments=[
                {
                    "id": 2,
                    "vendor_id": 1,
                    "material": "PLA",
                    "name": "Basic Blu",
                    "color_hex": "002E7A",
                }
            ],
            spools=[{"id": 3, "filament_id": 2}],
        )

    @staticmethod
    def _write_inherited_base(system_dir: Path) -> None:
        (system_dir / "Snapmaker PLA Basic @U1 base.json").write_text(
            json.dumps(
                {
                    "type": "filament",
                    "name": "Snapmaker PLA Basic @U1 base",
                    "from": "system",
                    "filament_id": "SYSTEM01",
                    "filament_vendor": ["Snapmaker"],
                    "filament_type": ["PLA"],
                    "filament_load_time": ["2"],
                    "filament_density": ["1.24"],
                }
            ),
            encoding="utf-8",
        )
        (system_dir / "Snapmaker PLA Basic @U1.json").write_text(
            json.dumps(
                {
                    "version": "2.2.53.2",
                    "type": "filament",
                    "name": "Snapmaker PLA Basic @U1",
                    "from": "system",
                    "setting_id": "SYSTEM-SETTING",
                    "instantiation": "true",
                    "inherits": "Snapmaker PLA Basic @U1 base",
                    "compatible_printers": ["Snapmaker U1 (0.4 nozzle)"],
                    "filament_vendor": ["Snapmaker"],
                    "filament_type": ["PLA"],
                    "filament_max_volumetric_speed": ["15"],
                }
            ),
            encoding="utf-8",
        )

    def test_new_profile_is_detached_and_matches_spoolman_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            self._write_inherited_base(system_dir)

            report = sync_profiles(
                self._inventory(), user_dir, system_dir, apply=True
            )

            self.assertEqual(report.actions[0].status, "created")
            payload = json.loads(
                next(user_dir.glob("*.json")).read_text(encoding="utf-8")
            )
            profile_name = "Deeplee PLA Basic Blu @Snapmaker U1 (0.4 nozzle)"
            self.assertNotIn("inherits", payload)
            self.assertNotIn("setting_id", payload)
            self.assertNotIn("instantiation", payload)
            self.assertEqual(payload["filament_vendor"], ["Deeplee"])
            self.assertEqual(payload["filament_type"], ["PLA"])
            self.assertEqual(payload["default_filament_colour"], ["#002E7A"])
            self.assertEqual(payload["filament_colour"], ["#002E7A"])
            self.assertEqual(payload["filament_id"], user_filament_id(profile_name))
            self.assertTrue(payload["filament_id"].startswith("P"))
            self.assertEqual(len(payload["filament_id"]), 8)

            # Values from both the parent and selected U1 child survive the
            # detachment, so removing inherits does not lose print settings.
            self.assertEqual(payload["filament_load_time"], ["2"])
            self.assertEqual(payload["filament_density"], ["1.24"])
            self.assertEqual(payload["filament_max_volumetric_speed"], ["15"])
            self.assertEqual(
                payload["compatible_printers"], ["Snapmaker U1 (0.4 nozzle)"]
            )

    def test_filament_id_matches_orca_user_id_convention(self):
        profile_name = "Deeplee PLA Basic Blu @Snapmaker U1 (0.4 nozzle)"
        # Orca hashes the identity before the @ suffix.
        expected = "P" + hashlib.md5(
            b"Deeplee PLA Basic Blu"
        ).hexdigest()[:7]
        self.assertEqual(user_filament_id(profile_name), expected)

    def test_multiword_vendor_is_preserved_exactly(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            self._write_inherited_base(system_dir)

            sync_profiles(
                self._inventory("Bambu Lab"), user_dir, system_dir, apply=True
            )
            payload = json.loads(
                next(user_dir.glob("*.json")).read_text(encoding="utf-8")
            )

            self.assertEqual(payload["filament_vendor"], ["Bambu Lab"])
            self.assertNotIn("inherits", payload)

    def test_existing_180_profile_is_migrated_without_losing_pa(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            self._write_inherited_base(system_dir)
            profile_name = "Deeplee PLA Basic Blu @Snapmaker U1 (0.4 nozzle)"
            profile_path = user_dir / f"{profile_name}.json"
            original = {
                "name": profile_name,
                "from": "User",
                "filament_settings_id": [profile_name],
                "filament_vendor": ["Snapmaker"],
                "default_filament_colour": ["#002E7A"],
                "filament_colour": ["#002E7A"],
                "inherits": "Snapmaker PLA Basic @U1",
                "pressure_advance": ["0.019"],
                "adaptive_pressure_advance": ["1"],
                "adaptive_pressure_advance_model": [
                    "0.019,8.0,2000|0.021,20.0,6000"
                ],
                "filament_max_volumetric_speed": ["18"],
            }
            original_bytes = (json.dumps(original, indent=4) + "\n").encode("utf-8")
            profile_path.write_bytes(original_bytes)

            report = sync_profiles(
                self._inventory(), user_dir, system_dir, apply=True
            )
            payload = json.loads(profile_path.read_text(encoding="utf-8"))

            self.assertEqual(report.actions[0].status, "repaired")
            self.assertIn("identità Orca/vendor", report.actions[0].message)
            self.assertNotIn("inherits", payload)
            self.assertNotIn("setting_id", payload)
            self.assertNotIn("instantiation", payload)
            self.assertEqual(payload["filament_vendor"], ["Deeplee"])
            self.assertEqual(payload["filament_type"], ["PLA"])
            self.assertEqual(payload["filament_id"], user_filament_id(profile_name))
            self.assertEqual(payload["pressure_advance"], ["0.019"])
            self.assertEqual(payload["adaptive_pressure_advance"], ["1"])
            self.assertEqual(
                payload["adaptive_pressure_advance_model"],
                ["0.019,8.0,2000|0.021,20.0,6000"],
            )
            self.assertEqual(payload["filament_max_volumetric_speed"], ["18"])
            backup = user_dir / f"{profile_name}.json.u1fa-pre181.bak"
            self.assertTrue(backup.is_file())
            self.assertEqual(backup.read_bytes(), original_bytes)

    def test_existing_181_profile_is_not_rewritten_again(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            self._write_inherited_base(system_dir)

            first = sync_profiles(
                self._inventory(), user_dir, system_dir, apply=True
            )
            self.assertEqual(first.actions[0].status, "created")
            profile_path = next(user_dir.glob("*.json"))
            before = hashlib.sha256(profile_path.read_bytes()).hexdigest()

            second = sync_profiles(
                self._inventory(), user_dir, system_dir, apply=True
            )
            after = hashlib.sha256(profile_path.read_bytes()).hexdigest()

            self.assertEqual(second.actions[0].status, "existing")
            self.assertEqual(after, before)
            self.assertEqual(list(user_dir.glob("*.u1fa-pre181.bak")), [])

    def test_interrupted_migration_reuses_single_existing_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            self._write_inherited_base(system_dir)
            profile_name = "Deeplee PLA Basic Blu @Snapmaker U1 (0.4 nozzle)"
            profile_path = user_dir / f"{profile_name}.json"
            profile_path.write_text(
                json.dumps(
                    {
                        "name": profile_name,
                        "from": "User",
                        "filament_settings_id": [profile_name],
                        "filament_vendor": ["Snapmaker"],
                        "inherits": "Snapmaker PLA Basic @U1",
                        "pressure_advance": ["0.019"],
                    },
                    indent=4,
                )
                + "\n",
                encoding="utf-8",
            )
            backup = user_dir / f"{profile_name}.json.u1fa-pre181.bak"
            first_backup = b"first safe backup"
            backup.write_bytes(first_backup)

            report = sync_profiles(
                self._inventory(), user_dir, system_dir, apply=True
            )

            self.assertEqual(report.actions[0].status, "repaired")
            self.assertEqual(backup.read_bytes(), first_backup)
            self.assertEqual(
                list(user_dir.glob(f"{profile_name}.json.u1fa-pre181*.bak")),
                [backup],
            )

    def test_nonwhite_manual_colour_survives_identity_migration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            self._write_inherited_base(system_dir)
            profile_name = "Deeplee PLA Basic Blu @Snapmaker U1 (0.4 nozzle)"
            profile_path = user_dir / f"{profile_name}.json"
            profile_path.write_text(
                json.dumps(
                    {
                        "name": profile_name,
                        "from": "User",
                        "filament_settings_id": [profile_name],
                        "inherits": "Snapmaker PLA Basic @U1",
                        "default_filament_colour": ["#123456"],
                        "filament_colour": ["#123456"],
                    },
                    indent=4,
                )
                + "\n",
                encoding="utf-8",
            )

            sync_profiles(self._inventory(), user_dir, system_dir, apply=True)
            payload = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["default_filament_colour"], ["#123456"])
            self.assertEqual(payload["filament_colour"], ["#123456"])
            self.assertEqual(payload["filament_vendor"], ["Deeplee"])

    def test_missing_parent_is_skipped_instead_of_writing_incomplete_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            (system_dir / "Snapmaker PLA Basic @U1.json").write_text(
                json.dumps(
                    {
                        "version": "2.2.53.2",
                        "inherits": "Missing parent",
                    }
                ),
                encoding="utf-8",
            )

            report = sync_profiles(
                self._inventory(), user_dir, system_dir, apply=True
            )

            self.assertEqual(report.actions[0].status, "skipped")
            self.assertIn("profilo padre Orca non trovato", report.actions[0].message)
            self.assertEqual(list(user_dir.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
