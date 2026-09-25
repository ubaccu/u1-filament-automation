import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.slicer_discovery import discover_slicers


class SlicerDiscoveryTests(unittest.TestCase):
    def test_snapmaker_and_standard_orca_are_discovered_separately_on_macos(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            snap = home / "Library" / "Application Support" / "Snapmaker_Orca" / "user" / "default" / "filament"
            standard = home / "Library" / "Application Support" / "OrcaSlicer" / "user" / "default" / "filament"
            snap.mkdir(parents=True)
            standard.mkdir(parents=True)
            (snap / "snap.json").write_text("{}", encoding="utf-8")
            (standard / "orca.json").write_text("{}", encoding="utf-8")

            found = discover_slicers(home=home, system="Darwin", environ={})

        self.assertEqual([item.kind for item in found], ["snapmaker_orca", "orca_slicer"])
        self.assertTrue(found[0].preferred)
        self.assertFalse(found[1].preferred)
        self.assertEqual(found[0].profile_count, 1)
        self.assertEqual(found[1].profile_count, 1)

    def test_standard_orca_never_replaces_snapmaker_preference(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            standard = home / ".config" / "OrcaSlicer" / "user" / "only" / "filament"
            standard.mkdir(parents=True)
            found = discover_slicers(home=home, system="Linux", environ={})
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].kind, "orca_slicer")
        self.assertFalse(found[0].preferred)

    def test_environment_overrides_are_read_only_candidates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            snap = root / "snap" / "user" / "a" / "filament"
            standard = root / "standard" / "user" / "b" / "filament"
            snap.mkdir(parents=True)
            standard.mkdir(parents=True)
            found = discover_slicers(
                home=root / "home",
                system="Darwin",
                environ={
                    "U1FA_SNAPMAKER_ORCA_DIR": str(root / "snap"),
                    "U1FA_ORCA_SLICER_DIR": str(root / "standard"),
                },
            )
        self.assertEqual({item.kind for item in found}, {"snapmaker_orca", "orca_slicer"})


if __name__ == "__main__":
    unittest.main()
