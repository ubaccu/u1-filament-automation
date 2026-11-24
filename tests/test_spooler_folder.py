from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from u1_filament_automation import slicer_discovery as discovery


class SpoolerFolderTests(TestCase):
    def test_multiple_accounts_only_one_spooler_bundle(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp) / "OrcaSlicer"
            target = root / "user" / "42" / "filament"
            other = root / "user" / "default" / "filament"
            marker = target.parent / "_local/spooler/.spooler-profiles.json"
            marker.parent.mkdir(parents=True)
            marker.touch()
            other.mkdir(parents=True)
            with patch.object(discovery, "candidate_slicer_roots", return_value=[("orca_slicer", root, "macOS")]):
                choices = discovery.standard_filament_choices(Path(tmp) / "Snap")
                self.assertEqual(set(choices), {target.resolve(), other.resolve()})
                self.assertIsNone(discovery.choose_standard_filament_dir(choices))
                target.mkdir()
                choices = discovery.standard_filament_choices(Path(tmp) / "Snap")
                self.assertEqual(discovery.choose_standard_filament_dir(choices), target.resolve())
                marker.unlink()
                self.assertIsNone(discovery.choose_standard_filament_dir(choices))
