import unittest
from types import SimpleNamespace

from u1_filament_automation.gui import _new_spool_form
from u1_filament_automation.gui_materials import (
    enhance_new_spool_page,
    install_material_ui_patch,
)
from u1_filament_automation.sync import choose_base


class GUIMaterialTests(unittest.TestCase):
    def test_pla_wood_option_uses_existing_snapmaker_base(self):
        page = enhance_new_spool_page(_new_spool_form("safe-token"), "it")
        self.assertIn('<option value="PLA Wood">PLA Wood</option>', page)
        self.assertIn("Snapmaker PLA Wood", page)
        self.assertEqual(
            choose_base("Generic", "PLA Wood", "Walnut"),
            "Snapmaker PLA Wood @U1 0.4 nozzle",
        )

    def test_pla_wood_hint_is_bilingual_and_keeps_standard_defaults(self):
        italian = enhance_new_spool_page(_new_spool_form("safe-token"), "it")
        english = enhance_new_spool_page(
            _new_spool_form("safe-token", language="en"),
            "en",
        )
        self.assertIn("correggile secondo i dati del produttore", italian)
        self.assertIn("adjust them to the spool manufacturer's specifications", english)
        self.assertIn('id="density" type="number" min="0.1" max="10" step="0.01" value="1.24"', italian)
        self.assertIn('id="nozzle-temp" type="number" min="170" max="300" value="220"', italian)
        self.assertIn('id="bed-temp" type="number" min="0" max="150" value="60"', italian)

    def test_patch_installation_is_idempotent(self):
        def original(token: str, error: str = "", language: str = "it") -> str:
            return (
                '<select><option value="PLA Silk">PLA Silk</option></select>'
                '<form method="post" action="/new-spool/preview"></form>'
            )

        fake_gui = SimpleNamespace(_new_spool_form=original)
        install_material_ui_patch(fake_gui)
        first_callable = fake_gui._new_spool_form
        install_material_ui_patch(fake_gui)
        self.assertIs(fake_gui._new_spool_form, first_callable)
        page = fake_gui._new_spool_form("token")
        self.assertEqual(page.count('<option value="PLA Wood">'), 1)
        self.assertEqual(page.count('id="u1fa-pla-wood-hint"'), 1)


if __name__ == "__main__":
    unittest.main()
