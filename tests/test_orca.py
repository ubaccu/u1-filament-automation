import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.orca import discover_orca


class OrcaDiscoveryTests(unittest.TestCase):
    def test_discovers_default_macos_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            filament = (
                home
                / "Library"
                / "Application Support"
                / "Snapmaker_Orca"
                / "user"
                / "default"
                / "filament"
            )
            filament.mkdir(parents=True)
            (filament / "one.json").write_text("{}", encoding="utf-8")
            found = discover_orca(home=home, system="Darwin", environ={})
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].path, filament.resolve())
            self.assertEqual(found[0].profile_count, 1)

    def test_accepts_explicit_filament_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            explicit = root / "explicit-filament"
            home = root / "home"
            explicit.mkdir()
            home.mkdir()
            found = discover_orca(
                explicit_dir=str(explicit),
                home=home,
                system="Darwin",
                environ={},
            )
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0].path, explicit.resolve())

    def test_discovers_windows_profile_from_appdata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "Roaming" / "Snapmaker_Orca"
            filament = root / "user" / "windows-user" / "filament"
            filament.mkdir(parents=True)
            found = discover_orca(
                home=Path(temporary),
                system="Windows",
                environ={"APPDATA": str(root.parent)},
            )
            self.assertEqual([item.path for item in found], [filament.resolve()])

    def test_discovers_linux_config_and_data_profiles(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            first = home / ".config" / "Snapmaker_Orca" / "user" / "default" / "filament"
            second = home / ".local" / "share" / "Snapmaker_Orca" / "user" / "maker" / "filament"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            found = discover_orca(home=home, system="Linux", environ={})
            self.assertEqual(
                {item.path for item in found},
                {first.resolve(), second.resolve()},
            )


if __name__ == "__main__":
    unittest.main()
