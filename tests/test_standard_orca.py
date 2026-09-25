import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.standard_orca import (
    StandardOrcaMirrorError,
    apply_standard_orca_mirror,
    plan_standard_orca_mirror,
    set_standard_orca_mirror_enabled,
    standard_orca_mirror_enabled,
)


def write_profile(directory: Path, name: str, *, pa: str = "0.010000", inherits=""):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.json"
    payload = {
        "name": name,
        "from": "User",
        "inherits": inherits,
        "filament_settings_id": [name],
        "enable_pressure_advance": ["1"],
        "pressure_advance": [pa],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


class StandardOrcaMirrorTests(unittest.TestCase):
    def test_missing_profile_is_created_byte_for_byte_and_tracked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "snapmaker"
            target = root / "orca"
            target.mkdir()
            source_path = write_profile(source, "DEEPLEE PLA")

            plan = plan_standard_orca_mirror(source, target, "DEEPLEE PLA")
            self.assertEqual(plan.action, "create")
            result = apply_standard_orca_mirror(plan)

            target_path = target / "DEEPLEE PLA.json"
            self.assertEqual(target_path.read_bytes(), source_path.read_bytes())
            self.assertEqual(result.action, "unchanged")
            self.assertTrue((target / "DEEPLEE PLA.info").is_file())
            state = json.loads(
                (target / ".u1fa" / "standard-orca-mirror.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIn("deeplee pla.json", state["profiles"])

    def test_foreign_existing_profile_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "snapmaker"
            target = root / "orca"
            write_profile(source, "DEEPLEE PLA", pa="0.010000")
            foreign = write_profile(target, "DEEPLEE PLA", pa="0.099000")
            original = foreign.read_bytes()

            plan = plan_standard_orca_mirror(source, target, "DEEPLEE PLA")
            self.assertEqual(plan.action, "blocked")
            self.assertIn("non è gestito da U1FA", plan.reason)
            with self.assertRaises(StandardOrcaMirrorError):
                apply_standard_orca_mirror(plan)
            self.assertEqual(foreign.read_bytes(), original)

    def test_exact_existing_profile_can_be_safely_adopted_then_updated(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "snapmaker"
            target = root / "orca"
            source_path = write_profile(source, "DEEPLEE PLA", pa="0.010000")
            target.mkdir()
            target_path = target / "DEEPLEE PLA.json"
            target_path.write_bytes(source_path.read_bytes())

            plan = plan_standard_orca_mirror(source, target, "DEEPLEE PLA")
            self.assertEqual(plan.action, "adopt")
            apply_standard_orca_mirror(plan)

            write_profile(source, "DEEPLEE PLA", pa="0.020000")
            update = plan_standard_orca_mirror(source, target, "DEEPLEE PLA")
            self.assertEqual(update.action, "update")
            apply_standard_orca_mirror(update)

            payload = json.loads(target_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["pressure_advance"], ["0.020000"])
            backups = list((target / ".u1fa" / "backups").glob("*.bak"))
            self.assertEqual(len(backups), 1)

    def test_manual_change_to_managed_mirror_blocks_future_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "snapmaker"
            target = root / "orca"
            target.mkdir()
            write_profile(source, "DEEPLEE PLA", pa="0.010000")
            apply_standard_orca_mirror(
                plan_standard_orca_mirror(source, target, "DEEPLEE PLA")
            )

            target_path = target / "DEEPLEE PLA.json"
            target_path.write_text('{"manual": true}\n', encoding="utf-8")
            write_profile(source, "DEEPLEE PLA", pa="0.020000")

            plan = plan_standard_orca_mirror(source, target, "DEEPLEE PLA")
            self.assertEqual(plan.action, "blocked")
            self.assertIn("modificato fuori da U1FA", plan.reason)

    def test_profile_with_live_inheritance_is_not_mirrored(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "snapmaker"
            target = root / "orca"
            target.mkdir()
            write_profile(
                source,
                "DEEPLEE PLA",
                inherits="Snapmaker PLA Basic @U1",
            )
            with self.assertRaisesRegex(
                StandardOrcaMirrorError,
                "dipende ancora da una base Snapmaker",
            ):
                plan_standard_orca_mirror(source, target, "DEEPLEE PLA")

    def test_explicit_opt_in_marker_persists_and_can_be_disabled(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "orca"
            target.mkdir()
            self.assertFalse(standard_orca_mirror_enabled(target))

            set_standard_orca_mirror_enabled(target, True)
            self.assertTrue(standard_orca_mirror_enabled(target))

            set_standard_orca_mirror_enabled(target, False)
            self.assertFalse(standard_orca_mirror_enabled(target))

    def test_symlinked_metadata_directory_is_blocked_before_profile_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "snapmaker"
            target = root / "orca"
            external = root / "external-state"
            target.mkdir()
            external.mkdir()
            write_profile(source, "DEEPLEE PLA")
            (target / ".u1fa").symlink_to(external, target_is_directory=True)

            self.assertFalse(standard_orca_mirror_enabled(target))
            with self.assertRaisesRegex(
                StandardOrcaMirrorError,
                "link simbolico",
            ):
                plan_standard_orca_mirror(source, target, "DEEPLEE PLA")
            self.assertFalse((target / "DEEPLEE PLA.json").exists())
            self.assertEqual(list(external.iterdir()), [])

    def test_source_and_target_must_be_distinct(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_profile(root, "DEEPLEE PLA")
            with self.assertRaisesRegex(
                StandardOrcaMirrorError,
                "stessa cartella",
            ):
                plan_standard_orca_mirror(root, root, "DEEPLEE PLA")


if __name__ == "__main__":
    unittest.main()
