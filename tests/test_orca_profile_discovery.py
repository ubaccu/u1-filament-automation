import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from u1_filament_automation.gui_materials import install_material_ui_patch
from u1_filament_automation.orca_profile_discovery import (
    installed_snapmaker_profiles,
    recommend_installed_profile,
)


class OrcaProfileDiscoveryTests(unittest.TestCase):
    def _system_dir(self, root: Path, *names: str) -> Path:
        system = root / "system" / "Snapmaker" / "filament"
        system.mkdir(parents=True)
        for name in names:
            (system / f"{name}.json").write_text(
                '{"version":"2.2.53.2"}\n',
                encoding="utf-8",
            )
        return system

    def test_exact_installed_profile_has_highest_confidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            system = self._system_dir(
                Path(temporary),
                "Snapmaker PLA Basic @U1",
                "Snapmaker PLA Silk",
            )
            result = recommend_installed_profile(
                system,
                "Snapmaker PLA Basic @U1",
            )
        self.assertEqual(result.confidence, "exact")
        self.assertEqual(result.suggested_profile, "Snapmaker PLA Basic @U1")

    def test_known_silk_naming_alias_is_treated_as_exact(self):
        with tempfile.TemporaryDirectory() as temporary:
            system = self._system_dir(
                Path(temporary),
                "Snapmaker PLA Silk @U1",
            )
            result = recommend_installed_profile(system, "Snapmaker PLA Silk")
        self.assertEqual(result.confidence, "exact")
        self.assertEqual(result.suggested_profile, "Snapmaker PLA Silk @U1")

    def test_renamed_high_speed_profile_is_suggested_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            system = self._system_dir(
                Path(temporary),
                "Snapmaker PLA High Speed @U1",
                "Snapmaker PLA Basic @U1",
            )
            result = recommend_installed_profile(
                system,
                "Snapmaker PLA SnapSpeed @U1",
            )
        self.assertEqual(result.confidence, "smart")
        self.assertEqual(result.suggested_profile, "Snapmaker PLA High Speed @U1")

    def test_close_candidates_are_reported_as_ambiguous(self):
        with tempfile.TemporaryDirectory() as temporary:
            system = self._system_dir(
                Path(temporary),
                "Snapmaker PLA High Speed @U1",
                "Snapmaker PLA Rapid @U1",
            )
            result = recommend_installed_profile(
                system,
                "Snapmaker PLA SnapSpeed @U1",
            )
        self.assertEqual(result.confidence, "ambiguous")
        self.assertIsNone(result.suggested_profile)
        self.assertEqual(len(result.candidates), 2)

    def test_standard_pla_never_falls_back_to_special_variant(self):
        with tempfile.TemporaryDirectory() as temporary:
            system = self._system_dir(
                Path(temporary),
                "Snapmaker PLA Silk @U1",
                "Snapmaker PLA-CF @U1 0.4 nozzle",
            )
            result = recommend_installed_profile(
                system,
                "Snapmaker PLA Basic @U1",
            )
        self.assertEqual(result.confidence, "unavailable")
        self.assertIsNone(result.suggested_profile)

    def test_scan_is_strictly_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            system = self._system_dir(
                Path(temporary),
                "Snapmaker PETG @U1",
                "Snapmaker PETG HF",
            )
            before = {
                path.name: path.read_bytes()
                for path in system.iterdir()
            }
            names = installed_snapmaker_profiles(system)
            recommend_installed_profile(system, "Snapmaker PETG @U1")
            after = {
                path.name: path.read_bytes()
                for path in system.iterdir()
            }
        self.assertEqual(before, after)
        self.assertEqual(
            names,
            ("Snapmaker PETG @U1", "Snapmaker PETG HF"),
        )

    def test_preview_patch_shows_smart_suggestion_without_changing_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            system = self._system_dir(
                Path(temporary),
                "Snapmaker PLA High Speed @U1",
            )

            class FakeController:
                def __init__(self):
                    self.system_dir = system

                def prepare_spool_creation(self, request):
                    return SimpleNamespace(
                        ticket="ticket-b22",
                        plan=SimpleNamespace(
                            base_profile="Snapmaker PLA SnapSpeed @U1"
                        ),
                    )

            def preview(prepared, token, language="it"):
                return (
                    "<html><body>"
                    f"<p><strong>Base Snapmaker:</strong> {prepared.plan.base_profile}</p>"
                    "</body></html>"
                )

            def form(token, error="", language="it"):
                return (
                    '<select name="material" id="material"><option value="PLA">PLA</option></select>'
                    '<form method="post" action="/new-spool/preview"></form>'
                )

            fake_gui = SimpleNamespace(
                CalibrationController=FakeController,
                _new_spool_preview=preview,
                _new_spool_form=form,
            )
            install_material_ui_patch(fake_gui)
            controller = FakeController()
            prepared = controller.prepare_spool_creation(object())
            page = fake_gui._new_spool_preview(prepared, "safe-token", language="it")

        self.assertEqual(
            prepared.plan.base_profile,
            "Snapmaker PLA SnapSpeed @U1",
        )
        self.assertIn("Suggerimento intelligente b22", page)
        self.assertIn("Snapmaker PLA High Speed @U1", page)
        self.assertIn("non viene applicato automaticamente", page)


if __name__ == "__main__":
    unittest.main()
