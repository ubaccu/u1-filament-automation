import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.models import SpoolmanInventory
from u1_filament_automation.pa import last_complete_suite, last_complete_suite_span
from u1_filament_automation.pa_profile import (
    PAProfileError,
    CalibrationIdentity,
    adaptive_pa_values,
    calibration_identity,
    resolve_profile_name,
    update_pa_profile,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILE_NAME = "R3d PLA RAPID GRIGIO @Snapmaker U1 (0.4 nozzle)"


def r3d_inventory() -> SpoolmanInventory:
    return SpoolmanInventory(
        url="http://127.0.0.1:7912",
        vendors=[{"id": 1, "name": "R3d"}],
        filaments=[
            {
                "id": 10,
                "vendor_id": 1,
                "material": "PLA",
                "name": "R3D PLA RAPID GRIGIO",
                "color_hex": "777777",
            }
        ],
        spools=[{"id": 8, "filament_id": 10}],
    )


class PAProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = (
            ROOT / "tests" / "fixtures" / "apa_chain_v6_real_log.txt"
        ).read_text(encoding="utf-8")
        cls.suite = last_complete_suite(cls.log)

    def test_extracts_spoolman_tracking_identity(self):
        identity = calibration_identity(
            "🧶 SH [INFO]: Tracking: R3d R3D PLA RAPID GRIGIO "
            "(colour: 777777, Spoolman id: 8, sku: )\n"
            + self.log
        )
        self.assertEqual(identity.spool_id, 8)
        self.assertEqual(identity.tracking_label, "R3d R3D PLA RAPID GRIGIO")
        self.assertEqual(identity.flow_label, "R3d PLA Rapid")

    def test_resolves_exact_spool_id_before_names(self):
        identity = CalibrationIdentity(
            spool_id=8,
            tracking_label="nome volutamente diverso",
        )
        self.assertEqual(
            resolve_profile_name(identity, r3d_inventory()),
            PROFILE_NAME,
        )

    def test_unique_flow_label_resolves_saved_log(self):
        identity = calibration_identity(self.log)
        self.assertIsNone(identity.spool_id)
        self.assertEqual(identity.flow_label, "R3d PLA Rapid")
        self.assertEqual(
            resolve_profile_name(identity, r3d_inventory()),
            PROFILE_NAME,
        )

    def test_ambiguous_flow_label_blocks(self):
        inventory = r3d_inventory()
        inventory.filaments.append(
            {
                "id": 11,
                "vendor_id": 1,
                "material": "PLA",
                "name": "R3D PLA RAPID ROSSO",
                "color_hex": "FF0000",
            }
        )
        inventory.spools.append({"id": 9, "filament_id": 11})
        with self.assertRaises(PAProfileError):
            resolve_profile_name(calibration_identity(self.log), inventory)

    def test_identity_ignores_a_later_incomplete_calibration(self):
        combined = (
            "Tracking: R3d R3D PLA RAPID GRIGIO "
            "(Spoolman id: 8)\n"
            + self.log
            + "\nTracking: Altro PLA (Spoolman id: 99)\n"
            + "// Point: low_anchor\n"
            + "// XY: speed=100 accel=2000 -> Q=8.1\n"
        )
        _, _, suite_end = last_complete_suite_span(combined)
        identity = calibration_identity(combined, end_offset=suite_end)
        self.assertEqual(identity.spool_id, 8)
        self.assertEqual(identity.flow_label, "R3d PLA Rapid")

    def test_adaptive_pa_values_match_orca_schema(self):
        values = adaptive_pa_values(self.suite)
        self.assertEqual(values["enable_pressure_advance"], ["1"])
        self.assertEqual(values["pressure_advance"], ["0.010364"])
        self.assertEqual(values["adaptive_pressure_advance"], ["1"])
        self.assertEqual(
            values["adaptive_pressure_advance_model"][0].splitlines(),
            [item.orca_row() for item in self.suite.results],
        )
        self.assertEqual(values["adaptive_pressure_advance_overhangs"], ["0"])
        self.assertEqual(
            values["adaptive_pressure_advance_bridges"],
            ["0.005182"],
        )

    def test_manual_profile_marks_cached_spool_id_as_not_used_for_assignment(self):
        identity = CalibrationIdentity(
            spool_id=5,
            tracking_label="vecchia bobina rimasta in cache",
        )
        with tempfile.TemporaryDirectory() as temporary:
            user_dir = Path(temporary)
            profile_path = user_dir / f"{PROFILE_NAME}.json"
            profile_path.write_text(
                json.dumps({"name": PROFILE_NAME}) + "\n",
                encoding="utf-8",
            )
            report = update_pa_profile(
                user_dir,
                PROFILE_NAME,
                identity,
                self.suite,
                manual_profile=True,
            )
        self.assertTrue(report.manual_profile)
        self.assertEqual(report.profile_name, PROFILE_NAME)
        self.assertEqual(report.identity.spool_id, 5)

    def test_preview_apply_backup_preservation_and_idempotency(self):
        identity = calibration_identity(self.log)
        with tempfile.TemporaryDirectory() as temporary:
            user_dir = Path(temporary)
            profile_path = user_dir / f"{PROFILE_NAME}.json"
            original = {
                "name": PROFILE_NAME,
                "inherits": "Snapmaker PLA SnapSpeed @U1",
                "custom_user_value": ["must-stay"],
                "pressure_advance": ["0.02"],
            }
            profile_path.write_text(
                json.dumps(original, indent=4) + "\n",
                encoding="utf-8",
            )
            before = hashlib.sha256(profile_path.read_bytes()).hexdigest()
            before_mtime = profile_path.stat().st_mtime_ns

            preview = update_pa_profile(
                user_dir,
                PROFILE_NAME,
                identity,
                self.suite,
                apply=False,
            )
            self.assertEqual(preview.status, "planned")
            self.assertEqual(
                hashlib.sha256(profile_path.read_bytes()).hexdigest(), before
            )
            self.assertEqual(profile_path.stat().st_mtime_ns, before_mtime)
            self.assertFalse((user_dir / ".u1fa" / "backups").exists())

            applied = update_pa_profile(
                user_dir,
                PROFILE_NAME,
                identity,
                self.suite,
                apply=True,
            )
            self.assertEqual(applied.status, "updated")
            self.assertIsNotNone(applied.backup_path)
            self.assertTrue(applied.backup_path.is_file())
            self.assertEqual(
                json.loads(applied.backup_path.read_text(encoding="utf-8")),
                original,
            )
            updated = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(updated["custom_user_value"], ["must-stay"])
            self.assertEqual(updated["pressure_advance"], ["0.010364"])
            self.assertEqual(
                updated["adaptive_pressure_advance_model"][0].splitlines(),
                [item.orca_row() for item in self.suite.results],
            )
            backups_before = list((user_dir / ".u1fa" / "backups").iterdir())

            repeated = update_pa_profile(
                user_dir,
                PROFILE_NAME,
                identity,
                self.suite,
                apply=True,
            )
            self.assertEqual(repeated.status, "unchanged")
            self.assertIsNone(repeated.backup_path)
            self.assertEqual(
                list((user_dir / ".u1fa" / "backups").iterdir()),
                backups_before,
            )

    def test_profile_symlink_cannot_escape_sandbox(self):
        identity = calibration_identity(self.log)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sandbox = root / "sandbox"
            outside = root / "outside.json"
            sandbox.mkdir()
            outside.write_text(
                json.dumps({"name": PROFILE_NAME, "protected": True}),
                encoding="utf-8",
            )
            link = sandbox / f"{PROFILE_NAME}.json"
            try:
                link.symlink_to(outside)
            except OSError:
                self.skipTest("Link simbolici non disponibili")
            before = outside.read_bytes()

            with self.assertRaises(PAProfileError):
                update_pa_profile(
                    sandbox,
                    PROFILE_NAME,
                    identity,
                    self.suite,
                    apply=True,
                )
            self.assertEqual(outside.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
