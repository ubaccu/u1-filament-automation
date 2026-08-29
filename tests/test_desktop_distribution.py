import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from u1_filament_automation.desktop_app import (
    ASKPASS_MODE_ENV,
    ASKPASS_PASSWORD_ENV,
    application_data_dir,
    desktop_log_path,
    emit_askpass_password,
    main,
)


class DesktopDistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.workflow = cls.root / ".github" / "workflows" / "build-release.yml"

    def test_windows_paths_follow_current_user_environment(self):
        home = Path("C:/Users/community-user")
        local = "C:/Users/community-user/AppData/Local"
        self.assertEqual(
            application_data_dir(home, "Windows", {"LOCALAPPDATA": local}),
            Path(local) / "U1 Filament Automation",
        )
        self.assertEqual(
            desktop_log_path(home, "Windows", {"LOCALAPPDATA": local}),
            Path(local) / "U1 Filament Automation" / "logs" / "app.log",
        )

    def test_linux_paths_respect_xdg(self):
        home = Path("/home/community-user")
        self.assertEqual(
            application_data_dir(home, "Linux", {"XDG_DATA_HOME": "/data/user"}),
            Path("/data/user/U1 Filament Automation"),
        )
        self.assertEqual(
            desktop_log_path(home, "Linux", {"XDG_STATE_HOME": "/state/user"}),
            Path("/state/user/U1 Filament Automation/app.log"),
        )

    def test_internal_askpass_rejects_empty_or_multiline_secret(self):
        self.assertEqual(emit_askpass_password({}, "Linux"), 1)
        self.assertEqual(
            emit_askpass_password({ASKPASS_PASSWORD_ENV: "bad\nsecret"}, "Linux"),
            1,
        )

    def test_internal_askpass_mode_never_starts_server(self):
        read_fd, write_fd = os.pipe()
        try:
            with (
                patch.dict(
                    os.environ,
                    {ASKPASS_MODE_ENV: "1", ASKPASS_PASSWORD_ENV: "snapmaker"},
                    clear=False,
                ),
                patch("u1_filament_automation.desktop_app.server_is_running") as server,
                patch("u1_filament_automation.desktop_app.os.write") as write,
            ):
                self.assertEqual(main(), 0)
            server.assert_not_called()
            write.assert_called_once_with(1, b"snapmaker\n")
        finally:
            os.close(read_fd)
            os.close(write_fd)

    def test_windows_installer_and_linux_appimage_are_defined(self):
        windows_script = self.root / "packaging" / "windows" / "build_installer.ps1"
        inno = self.root / "packaging" / "windows" / "U1FA.iss"
        linux_script = self.root / "packaging" / "linux" / "build_appimage.sh"
        self.assertTrue(windows_script.is_file())
        self.assertTrue(inno.is_file())
        subprocess.run(
            ["/bin/bash", "-n", str(linux_script)],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("PyInstaller", windows_script.read_text(encoding="utf-8"))
        self.assertIn("Inno Setup", windows_script.read_text(encoding="utf-8"))
        self.assertIn("appimagetool", linux_script.read_text(encoding="utf-8"))
        self.assertIn("adaptive_pa_macro.cfg", windows_script.read_text(encoding="utf-8"))
        self.assertIn("adaptive_pa_macro.cfg", linux_script.read_text(encoding="utf-8"))

    def test_single_workflow_builds_every_platform_and_one_release(self):
        source = self.workflow.read_text(encoding="utf-8")
        self.assertIn("macos-15-intel", source)
        self.assertIn("windows-2025", source)
        self.assertIn("ubuntu-22.04", source)
        self.assertIn("--prerelease", source)
        self.assertEqual(source.count("gh release create"), 1)
        self.assertNotIn("192.168.1.51", source)
        self.assertNotIn("ivanriccelli", source.casefold())


if __name__ == "__main__":
    unittest.main()
