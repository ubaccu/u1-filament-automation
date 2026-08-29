import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.models import ProfilePreview
from u1_filament_automation.profile_audit import compare_previews, scan_profile_names


class ProfileAuditTests(unittest.TestCase):
    def test_scan_and_compare_do_not_modify_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            profile = directory / "Deeplee PLA Rapid Marrone @Snapmaker U1 (0.4 nozzle).json"
            profile.write_text(
                json.dumps(
                    {"name": "Deeplee PLA Rapid Marrone @Snapmaker U1 (0.4 nozzle)"}
                ),
                encoding="utf-8",
            )
            before_bytes = profile.read_bytes()
            before_hash = hashlib.sha256(before_bytes).hexdigest()
            before_mtime = profile.stat().st_mtime_ns

            names, warnings = scan_profile_names([directory])
            comparisons = compare_previews(
                [
                    ProfilePreview(
                        identity="Deeplee PLA Rapid Marrone",
                        base_profile="Deeplee PLA Rapid Marrone @Snapmaker U1 base",
                        nozzle_profile="Deeplee PLA Rapid Marrone @Snapmaker U1 (0.4 nozzle)",
                        spool_ids=(4,),
                    )
                ],
                names,
            )

            self.assertFalse(warnings)
            self.assertEqual(comparisons[0].status, "existing")
            self.assertEqual(hashlib.sha256(profile.read_bytes()).hexdigest(), before_hash)
            self.assertEqual(profile.stat().st_mtime_ns, before_mtime)
            self.assertEqual(profile.read_bytes(), before_bytes)

    def test_strict_comparison_does_not_guess(self):
        preview = ProfilePreview(
            identity="Snapmaker PLA SnapSpeed Red",
            base_profile="Snapmaker PLA SnapSpeed Red @Snapmaker U1 base",
            nozzle_profile="Snapmaker PLA SnapSpeed Red @Snapmaker U1 (0.4 nozzle)",
            spool_ids=(7,),
        )
        comparison = compare_previews(
            [preview],
            ["Snapmaker PLA SnapSpeed RED old @Snapmaker U1 (0.4 nozzle)"],
        )[0]
        self.assertEqual(comparison.status, "missing")

    def test_recognizes_real_profile_names_without_color_false_matches(self):
        targets_and_existing = [
            (
                "Anycubic PETG Translucent Blue",
                "ANYCUBIC PETG Translucent Blue @Snapmaker U1 (0.4 nozzle)",
                "existing",
            ),
            (
                "Deeplee PLA Blue",
                "Deeplee PLA Blue @Snapmaker U1 (0.4 nozzle)",
                "existing",
            ),
            (
                "Deeplee PLA Pro Rapid Nero",
                "DEEPLEE PLA PRO RAPID NERO @Snapmaker U1 (0.4 nozzle)",
                "existing",
            ),
            (
                "Deeplee PLA Rapid Beige",
                "DEEPLEE PLA RAPID BEIGE @Snapmaker U1 (0.4 nozzle)",
                "existing",
            ),
            (
                "Deeplee PLA Rapid Marrone",
                "DEEPLEE PLA RAPID MARRONE @Snapmaker U1 (0.4 nozzle)",
                "existing",
            ),
            (
                "Deeplee PLA Rapid Turchese",
                "DEEPLEE PLA RAPID TURCHESE @Snapmaker U1 (0.4 nozzle)",
                "existing",
            ),
            (
                "R3d PLA Rapid Grigio",
                "R3D PLA RAPID GRIGIO @Snapmaker U1 (0.4 nozzle)",
                "existing",
            ),
            (
                "Snapmaker PLA SnapSpeed Pearl White",
                "Snapmaker SnapSpeed PLA - Pearl White @Snapmaker U1 (0.4 nozzle)",
                "equivalent",
            ),
            (
                "Snapmaker PLA SnapSpeed Red",
                "Snapmaker SnapSpeed PLA - RED @Snapmaker U1 (0.4 nozzle)",
                "equivalent",
            ),
        ]

        for identity, existing, expected_status in targets_and_existing:
            with self.subTest(identity=identity):
                preview = ProfilePreview(
                    identity=identity,
                    base_profile=f"{identity} @Snapmaker U1 base",
                    nozzle_profile=f"{identity} @Snapmaker U1 (0.4 nozzle)",
                    spool_ids=(1,),
                )
                comparison = compare_previews([preview], [existing])[0]
                self.assertEqual(comparison.status, expected_status)

        blue = ProfilePreview(
            identity="Deeplee PLA Blue",
            base_profile="Deeplee PLA Blue @Snapmaker U1 base",
            nozzle_profile="Deeplee PLA Blue @Snapmaker U1 (0.4 nozzle)",
            spool_ids=(6,),
        )
        comparison = compare_previews(
            [blue],
            [
                "Deeplee PLA+ Beige @Snapmaker U1 (0.4 nozzle)",
                "Deeplee PLA+ Brown @Snapmaker U1 (0.4 nozzle)",
            ],
        )[0]
        self.assertEqual(comparison.status, "missing")
        self.assertFalse(comparison.similar_matches)


if __name__ == "__main__":
    unittest.main()
