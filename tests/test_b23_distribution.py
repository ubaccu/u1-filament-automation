import unittest
from pathlib import Path

import u1_filament_automation


class B23DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]

    def test_version_is_b23(self):
        self.assertEqual(u1_filament_automation.__version__, "1.8.0b23")
        pyproject = (self.root / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('version = "1.8.0b23"', pyproject)

    def test_all_desktop_bootstraps_use_b23_entrypoint(self):
        for platform_name in ("macos", "windows", "linux"):
            with self.subTest(platform=platform_name):
                source = (
                    self.root / "packaging" / platform_name / "u1fa_bootstrap.py"
                ).read_text(encoding="utf-8")
                self.assertIn(
                    "from u1_filament_automation.desktop_app_b23 import main",
                    source,
                )

    def test_release_notes_are_bilingual_and_safety_explicit(self):
        notes = (self.root / "RELEASE_NOTES_1.8.0b23.md").read_text(encoding="utf-8")
        self.assertLess(notes.index("# Italiano"), notes.index("# English"))
        self.assertIn("GET /server/info", notes)
        self.assertIn("non invia G-code", notes)
        self.assertIn("Posizione bobina / stoccaggio", notes)


if __name__ == "__main__":
    unittest.main()
