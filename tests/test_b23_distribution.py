import unittest
from pathlib import Path


class B23DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]

    def test_b23_release_contract_remains_available(self):
        self.assertTrue(
            (self.root / "src" / "u1_filament_automation" / "desktop_app_b23.py").is_file()
        )
        self.assertTrue((self.root / "RELEASE_NOTES_1.8.0b23.md").is_file())

    def test_release_notes_are_bilingual_and_safety_explicit(self):
        notes = (self.root / "RELEASE_NOTES_1.8.0b23.md").read_text(encoding="utf-8")
        self.assertLess(notes.index("# Italiano"), notes.index("# English"))
        self.assertIn("GET /server/info", notes)
        self.assertIn("non invia G-code", notes)
        self.assertIn("Posizione bobina / stoccaggio", notes)


if __name__ == "__main__":
    unittest.main()
