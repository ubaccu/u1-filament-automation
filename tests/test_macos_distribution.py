import os
import shutil
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from u1_filament_automation.desktop_app import APP_URL, main
from u1_filament_automation.macos_app import application_support_dir, log_path


class MacOSDistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.build_script = cls.root / "packaging" / "macos" / "build_dmg.sh"
        cls.workflow = cls.root / ".github" / "workflows" / "build-release.yml"

    def test_user_paths_are_per_account_and_not_hard_coded(self):
        home = Path("/Users/community-user")
        self.assertEqual(
            application_support_dir(home),
            home / "Library" / "Application Support" / "U1 Filament Automation",
        )
        self.assertEqual(
            log_path(home),
            home / "Library" / "Logs" / "U1 Filament Automation" / "app.log",
        )

    def test_existing_instance_is_reopened_without_starting_another_server(self):
        with (
            patch("u1_filament_automation.desktop_app.server_is_running", return_value=True),
            patch("u1_filament_automation.desktop_app.webbrowser.open") as browser,
            patch("u1_filament_automation.desktop_app.cli_main") as cli,
        ):
            self.assertEqual(main(), 0)
        browser.assert_called_once_with(APP_URL)
        cli.assert_not_called()

    def test_builder_creates_windowed_self_contained_dmg(self):
        bash = shutil.which("bash")
        if bash is not None:
            subprocess.run(
                [bash, "-n", str(self.build_script)],
                check=True,
                capture_output=True,
                text=True,
            )
        source = self.build_script.read_text(encoding="utf-8")
        self.assertIn("--windowed", source)
        self.assertIn("PyInstaller", source)
        self.assertIn("hdiutil create", source)
        self.assertIn("/Applications", source)
        self.assertIn("MACOSX_DEPLOYMENT_TARGET", source)
        self.assertIn("Add :CFBundleShortVersionString", source)
        self.assertIn("Add :CFBundleVersion", source)
        self.assertNotIn("192.168.1.51", source)
        self.assertNotIn("ivanriccelli", source.casefold())

    def test_workflow_builds_intel_and_apple_silicon(self):
        source = self.workflow.read_text(encoding="utf-8")
        self.assertIn("macos-15-intel", source)
        self.assertIn("x86_64", source)
        self.assertIn("macos-14", source)
        self.assertIn("arm64", source)
        self.assertIn("dist/*.dmg", source)

    def test_bespok_draft_is_not_distributed(self):
        self.assertFalse((self.root / "bespok3d").exists())


if __name__ == "__main__":
    unittest.main()
