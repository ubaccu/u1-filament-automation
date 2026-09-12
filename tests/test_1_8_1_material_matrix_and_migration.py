import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.gui_materials import MATERIAL_OPTIONS
from u1_filament_automation.models import SpoolmanInventory
from u1_filament_automation.orca_profile import (
    _snapmaker_runtime_filament_type,
    user_filament_id,
)
from u1_filament_automation.sync import choose_base, make_profile_name, sync_profiles


class MaterialMatrixAndManagedMigration181Tests(unittest.TestCase):
    def test_every_app_material_family_maps_to_expected_snapmaker_identity(self):
        expected = {
            "PLA": ("Snapmaker PLA Basic @U1", "PLA"),
            "PLA Rapid": ("Snapmaker PLA SnapSpeed @U1", "PLA HIGH SPEED"),
            "PLA Silk": ("Snapmaker PLA Silk", "PLA SILK"),
            "PLA Wood": ("Snapmaker PLA Wood @U1 0.4 nozzle", "PLA WOOD"),
            "PLA Translucent": (
                "Snapmaker PLA Translucent @U1 0.4 nozzle",
                "PLA TRANSLUCENT",
            ),
            "PLA-CF": ("Snapmaker PLA-CF @U1 0.4 nozzle", "PLA-CF"),
            "PETG": ("Snapmaker PETG @U1", "PETG"),
            "PETG HF": ("Snapmaker PETG HF", "PETG HIGH SPEED"),
            "PETG Translucent": (
                "Snapmaker PETG Translucent @U1 0.4 nozzle",
                "PETG TRANSLUCENT",
            ),
            "PETG-CF": ("Snapmaker PETG-CF @U1 0.4 nozzle", "PETG-CF"),
        }
        self.assertEqual(set(MATERIAL_OPTIONS), set(expected))

        for material, (base, runtime_type) in expected.items():
            with self.subTest(material=material):
                selected = choose_base("Deeplee", material, "TEST")
                self.assertEqual(selected, base)
                special = _snapmaker_runtime_filament_type(Path(f"{base}.json"))
                if runtime_type in {"PLA", "PETG"}:
                    self.assertIsNone(special)
                else:
                    self.assertEqual(special, runtime_type)

    @staticmethod
    def _inventory() -> SpoolmanInventory:
        return SpoolmanInventory(
            url="http://spoolman.test",
            vendors=[{"id": 1, "name": "Deeplee"}],
            filaments=[
                {
                    "id": 2,
                    "vendor_id": 1,
                    "material": "PLA Translucent",
                    "name": "Clear",
                    "color_hex": "FFFFFF",
                }
            ],
            spools=[{"id": 3, "filament_id": 2}],
        )

    @staticmethod
    def _write_translucent_base(system_dir: Path) -> None:
        (system_dir / "fdm_filament_pla.json").write_text(
            json.dumps(
                {
                    "type": "filament",
                    "name": "fdm_filament_pla",
                    "from": "system",
                    "filament_type": ["PLA"],
                    "filament_density": ["1.24"],
                }
            ),
            encoding="utf-8",
        )
        (system_dir / "Snapmaker PLA Translucent @U1 base.json").write_text(
            json.dumps(
                {
                    "type": "filament",
                    "name": "Snapmaker PLA Translucent @U1 base",
                    "inherits": "fdm_filament_pla",
                    "from": "system",
                    "filament_id": "SYSTEM01",
                    "instantiation": "false",
                }
            ),
            encoding="utf-8",
        )
        (system_dir / "Snapmaker PLA Translucent @U1 0.4 nozzle.json").write_text(
            json.dumps(
                {
                    "version": "2.2.53.2",
                    "type": "filament",
                    "name": "Snapmaker PLA Translucent @U1 0.4 nozzle",
                    "inherits": "Snapmaker PLA Translucent @U1 base",
                    "from": "system",
                    "setting_id": "SYSTEM-SETTING",
                    "instantiation": "true",
                    "compatible_printers": ["Snapmaker U1 (0.4 nozzle)"],
                    "filament_vendor": ["Snapmaker"],
                    "filament_type": ["PLA"],
                }
            ),
            encoding="utf-8",
        )

    def test_existing_managed_translucent_profile_is_repaired_not_dismissed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            self._write_translucent_base(system_dir)

            profile_name = make_profile_name(
                "Deeplee", "PLA Translucent", "Clear"
            )
            profile_path = user_dir / f"{profile_name}.json"
            profile_path.write_text(
                json.dumps(
                    {
                        "type": "filament",
                        "name": profile_name,
                        "from": "User",
                        "filament_id": user_filament_id(profile_name),
                        "filament_settings_id": [profile_name],
                        "filament_vendor": ["Deeplee"],
                        "filament_type": ["PLA"],
                        "default_filament_colour": ["#FFFFFF"],
                        "filament_colour": ["#FFFFFF"],
                        "pressure_advance": ["0.019"],
                    },
                    indent=4,
                )
                + "\n",
                encoding="utf-8",
            )

            report = sync_profiles(
                self._inventory(),
                user_dir,
                system_dir,
                apply=True,
                ignored_profile_names={profile_name.casefold()},
            )
            payload = json.loads(profile_path.read_text(encoding="utf-8"))

            self.assertEqual(report.actions[0].status, "repaired")
            self.assertEqual(payload["filament_type"], ["PLA TRANSLUCENT"])
            self.assertEqual(payload["filament_vendor"], ["Deeplee"])
            self.assertEqual(payload["pressure_advance"], ["0.019"])
            self.assertTrue(
                (user_dir / f"{profile_name}.json.u1fa-pre181.bak").is_file()
            )

    def test_deleted_managed_profile_is_still_respected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            self._write_translucent_base(system_dir)

            profile_name = make_profile_name(
                "Deeplee", "PLA Translucent", "Clear"
            )
            report = sync_profiles(
                self._inventory(),
                user_dir,
                system_dir,
                apply=True,
                ignored_profile_names={profile_name.casefold()},
            )

            self.assertEqual(report.actions[0].status, "dismissed")
            self.assertFalse((user_dir / f"{profile_name}.json").exists())


if __name__ == "__main__":
    unittest.main()
