import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.models import SpoolmanInventory
from u1_filament_automation.sync import make_profile_name, sync_profiles


class SpoolmanDensity181Tests(unittest.TestCase):
    @staticmethod
    def _write_base(system_dir: Path) -> None:
        (system_dir / "Snapmaker PLA Translucent @U1 0.4 nozzle.json").write_text(
            json.dumps(
                {
                    "version": "2.2.53.2",
                    "type": "filament",
                    "name": "Snapmaker PLA Translucent @U1 0.4 nozzle",
                    "from": "system",
                    "setting_id": "SYSTEM-SETTING",
                    "instantiation": "true",
                    "compatible_printers": ["Snapmaker U1 (0.4 nozzle)"],
                    "filament_vendor": ["Snapmaker"],
                    "filament_type": ["PLA"],
                    "filament_density": ["1.32"],
                    "default_filament_colour": ["#FFFFFF"],
                    "filament_colour": ["#FFFFFF"],
                }
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _inventory(density=1.25) -> SpoolmanInventory:
        filament = {
            "id": 18,
            "vendor_id": 3,
            "material": "PLA TRANSLUCENT",
            "name": "Transparent",
            "color_hex": "CAF0FE",
        }
        if density is not None:
            filament["density"] = density
        return SpoolmanInventory(
            url="http://spoolman.test",
            vendors=[{"id": 3, "name": "Deeplee"}],
            filaments=[filament],
            spools=[{"id": 15, "filament_id": 18}],
        )

    def test_new_profile_uses_spoolman_density_instead_of_snapmaker_base(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            self._write_base(system_dir)

            report = sync_profiles(
                self._inventory(1.25),
                user_dir,
                system_dir=system_dir,
                apply=True,
            )

            profile_name = make_profile_name(
                "Deeplee", "PLA TRANSLUCENT", "Transparent"
            )
            payload = json.loads(
                (user_dir / f"{profile_name}.json").read_text(encoding="utf-8")
            )

            self.assertEqual(report.actions[0].status, "created")
            self.assertEqual(payload["filament_density"], ["1.25"])
            self.assertEqual(payload["filament_vendor"], ["Deeplee"])
            self.assertEqual(payload["filament_type"], ["PLA TRANSLUCENT"])
            self.assertEqual(payload["default_filament_colour"], ["#CAF0FE"])

    def test_missing_spoolman_density_keeps_snapmaker_base_density(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            self._write_base(system_dir)

            sync_profiles(
                self._inventory(None),
                user_dir,
                system_dir=system_dir,
                apply=True,
            )

            profile_name = make_profile_name(
                "Deeplee", "PLA TRANSLUCENT", "Transparent"
            )
            payload = json.loads(
                (user_dir / f"{profile_name}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(payload["filament_density"], ["1.32"])

    def test_preview_does_not_write_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            self._write_base(system_dir)

            report = sync_profiles(
                self._inventory(1.25),
                user_dir,
                system_dir=system_dir,
                apply=False,
            )

            self.assertEqual(report.actions[0].status, "planned")
            self.assertEqual(list(user_dir.glob("*.json")), [])


if __name__ == "__main__":
    unittest.main()
