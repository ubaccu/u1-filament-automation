import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.models import SpoolmanInventory
from u1_filament_automation.sync import choose_base, make_profile_name, sync_profiles


class SyncTests(unittest.TestCase):
    def test_uses_saved_template_rules(self):
        self.assertEqual(
            choose_base("Deeplee", "PLA", "Rapid Marrone"),
            "Snapmaker PLA SnapSpeed @U1",
        )
        self.assertEqual(
            choose_base("Snapmaker", "PLA", "Basic"),
            "Snapmaker PLA Basic @U1",
        )
        self.assertEqual(
            choose_base("Anycubic", "PETG", "Translucent Blue"),
            "Snapmaker PETG Translucent @U1 0.4 nozzle",
        )
        self.assertEqual(
            choose_base("Generic", "PETG", "High Speed"),
            "Snapmaker PETG HF",
        )
        self.assertEqual(
            choose_base("Snapmaker", "PLA", "Silk Sunset Ember"),
            "Snapmaker PLA Silk",
        )
        self.assertEqual(
            make_profile_name("Deeplee", "PLA", "Rapid Marrone"),
            "Deeplee PLA Rapid Marrone @Snapmaker U1 (0.4 nozzle)",
        )
        self.assertEqual(
            make_profile_name("Deeplee", "PLA", "DEEPLEE PLA RAPID MARRONE"),
            "Deeplee PLA RAPID MARRONE @Snapmaker U1 (0.4 nozzle)",
        )
        self.assertEqual(
            make_profile_name("R3d", "PLA", "R3D PLA RAPID GRIGIO"),
            "R3d PLA RAPID GRIGIO @Snapmaker U1 (0.4 nozzle)",
        )
        self.assertEqual(
            make_profile_name("Snapmaker", "PLA", "SnapSpeed PLA - RED"),
            "Snapmaker SnapSpeed PLA - RED @Snapmaker U1 (0.4 nozzle)",
        )

    def _inventory(self):
        return SpoolmanInventory(
            url="http://127.0.0.1:7912",
            vendors=[{"id": 1, "name": "Deeplee"}],
            filaments=[
                {
                    "id": 2,
                    "vendor_id": 1,
                    "material": "PLA",
                    "name": "Rapid Marrone",
                    "color_hex": "9C7860",
                }
            ],
            spools=[{"id": 4, "filament_id": 2}],
        )

    def test_preview_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            base = system_dir / "Snapmaker PLA SnapSpeed @U1.json"
            base.write_text(json.dumps({"version": "2.2.53.2"}), encoding="utf-8")
            before = sorted(user_dir.iterdir())

            report = sync_profiles(self._inventory(), user_dir, system_dir, apply=False)

            self.assertEqual(report.actions[0].status, "planned")
            self.assertEqual(sorted(user_dir.iterdir()), before)

    def test_apply_creates_json_and_info_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            base = system_dir / "Snapmaker PLA SnapSpeed @U1.json"
            base.write_text(json.dumps({"version": "9.9"}), encoding="utf-8")

            report = sync_profiles(self._inventory(), user_dir, system_dir, apply=True)
            self.assertEqual(report.actions[0].status, "created")
            json_files = list(user_dir.glob("*.json"))
            info_files = list(user_dir.glob("*.info"))
            self.assertEqual(len(json_files), 1)
            self.assertEqual(len(info_files), 1)
            payload = json.loads(json_files[0].read_text(encoding="utf-8"))
            self.assertEqual(payload["inherits"], "Snapmaker PLA SnapSpeed @U1")
            self.assertEqual(payload["version"], "9.9")
            before_hash = hashlib.sha256(json_files[0].read_bytes()).hexdigest()

            second = sync_profiles(self._inventory(), user_dir, system_dir, apply=True)
            self.assertEqual(second.actions[0].status, "existing")
            self.assertEqual(hashlib.sha256(json_files[0].read_bytes()).hexdigest(), before_hash)

    def test_watcher_respects_manual_profile_deletion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            (system_dir / "Snapmaker PLA SnapSpeed @U1.json").write_text(
                json.dumps({"version": "2.2.53.2"}), encoding="utf-8"
            )

            first = sync_profiles(self._inventory(), user_dir, system_dir, apply=True)
            managed = {first.actions[0].profile_name.casefold()}
            for path in user_dir.iterdir():
                path.unlink()

            second = sync_profiles(
                self._inventory(),
                user_dir,
                system_dir,
                apply=True,
                ignored_profile_names=managed,
            )
            self.assertEqual(second.actions[0].status, "dismissed")
            self.assertEqual(list(user_dir.iterdir()), [])

    def test_only_profile_names_limits_real_orca_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "filament"
            system_dir = root / "system"
            system_dir.mkdir()
            (system_dir / "Snapmaker PLA SnapSpeed @U1.json").write_text(
                json.dumps({"version": "2.2.53.2"}), encoding="utf-8"
            )
            inventory = self._inventory()
            inventory.filaments.append({
                "id": 3, "vendor_id": 1, "material": "PLA",
                "name": "Rapid Blu", "color_hex": "2563EB",
            })
            inventory.spools.append({"id": 5, "filament_id": 3})
            wanted = "Deeplee PLA Rapid Blu @Snapmaker U1 (0.4 nozzle)"

            report = sync_profiles(
                inventory, user_dir, system_dir, apply=True,
                only_profile_names={wanted},
            )

            self.assertEqual([item.profile_name for item in report.actions], [wanted])
            self.assertEqual(len(list(user_dir.glob("*.json"))), 1)

    def test_multicolor_profile_preserves_all_spoolman_colors(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            (system_dir / "Snapmaker PLA Silk.json").write_text(
                json.dumps({"version": "2.2.53.2"}), encoding="utf-8"
            )
            inventory = SpoolmanInventory(
                url="http://spoolman.test",
                vendors=[{"id": 7, "name": "Snapmaker"}],
                filaments=[{
                    "id": 8, "vendor_id": 7, "material": "PLA",
                    "name": "Silk Sunset Ember",
                    "multi_color_hexes": "D9A62E,D8494A",
                }],
                spools=[{"id": 9, "filament_id": 8}],
            )
            report = sync_profiles(inventory, user_dir, system_dir, apply=True)
            self.assertEqual(report.actions[0].status, "created")
            payload = json.loads(next(user_dir.glob("*.json")).read_text(encoding="utf-8"))
            self.assertEqual(payload["inherits"], "Snapmaker PLA Silk")
            self.assertEqual(payload["default_filament_colour"], ["#D9A62E", "#D8494A"])


if __name__ == "__main__":
    unittest.main()
