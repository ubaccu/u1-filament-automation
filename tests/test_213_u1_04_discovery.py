import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.orca_profile_discovery import recommend_installed_profile


class U104Discovery213Tests(unittest.TestCase):
    def _touch(self, root: Path, *names: str) -> None:
        for name in names:
            (root / f"{name}.json").write_text("{}", encoding="utf-8")

    def test_asa_prefers_exact_u1_04_alias_over_other_nozzles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._touch(
                root,
                "Snapmaker ASA @U1 0.2 nozzle",
                "Snapmaker ASA @U1 0.4 nozzle",
                "Snapmaker ASA @U1 0.6 nozzle",
            )
            result = recommend_installed_profile(root, "Snapmaker ASA @U1")

        self.assertEqual(result.confidence, "exact")
        self.assertEqual(result.suggested_profile, "Snapmaker ASA @U1 0.4 nozzle")
        self.assertEqual(result.candidates, ("Snapmaker ASA @U1 0.4 nozzle",))

    def test_abs_prefers_exact_u1_04_alias_over_other_nozzles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._touch(
                root,
                "Snapmaker ABS @U1 0.2 nozzle",
                "Snapmaker ABS @U1 0.4 nozzle",
                "Snapmaker ABS @U1 0.6 nozzle",
            )
            result = recommend_installed_profile(root, "Snapmaker ABS @U1")

        self.assertEqual(result.confidence, "exact")
        self.assertEqual(result.suggested_profile, "Snapmaker ABS @U1 0.4 nozzle")

    def test_wrong_nozzle_only_does_not_become_exact_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._touch(
                root,
                "Snapmaker ASA @U1 0.2 nozzle",
                "Snapmaker ASA @U1 0.6 nozzle",
            )
            result = recommend_installed_profile(root, "Snapmaker ASA @U1")

        self.assertNotEqual(result.confidence, "exact")


if __name__ == "__main__":
    unittest.main()
