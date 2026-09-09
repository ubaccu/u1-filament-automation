import unittest
from types import SimpleNamespace

from u1_filament_automation.gui import _new_spool_form
from u1_filament_automation.gui_materials import (
    MATERIAL_OPTIONS,
    enhance_new_spool_page,
    install_material_ui_patch,
)
from u1_filament_automation.sync import choose_base


class GUIMaterialTests(unittest.TestCase):
    def test_all_supported_material_families_are_exposed(self):
        page = enhance_new_spool_page(_new_spool_form("safe-token"), "it")
        for material in MATERIAL_OPTIONS:
            self.assertIn(
                f'<option value="{material}">{material}</option>',
                page,
            )
        self.assertNotIn("PLA SnapSpeed</option>", page)
        self.assertEqual(page.count('<option value="PLA Rapid">'), 1)

    def test_material_choices_map_to_existing_snapmaker_bases(self):
        expected = {
            "PLA": "Snapmaker PLA Basic @U1",
            "PLA Rapid": "Snapmaker PLA SnapSpeed @U1",
            "PLA Silk": "Snapmaker PLA Silk",
            "PLA Wood": "Snapmaker PLA Wood @U1 0.4 nozzle",
            "PLA Translucent": "Snapmaker PLA Translucent @U1 0.4 nozzle",
            "PLA-CF": "Snapmaker PLA-CF @U1 0.4 nozzle",
            "PETG": "Snapmaker PETG @U1",
            "PETG HF": "Snapmaker PETG HF",
            "PETG Translucent": "Snapmaker PETG Translucent @U1 0.4 nozzle",
            "PETG-CF": "Snapmaker PETG-CF @U1 0.4 nozzle",
        }
        for material, base in expected.items():
            with self.subTest(material=material):
                self.assertEqual(
                    choose_base("Generic", material, "Blue"),
                    base,
                )

    def test_pla_rapid_is_generic_name_but_uses_snapspeed(self):
        italian = enhance_new_spool_page(_new_spool_form("safe-token"), "it")
        english = enhance_new_spool_page(
            _new_spool_form("safe-token", language="en"),
            "en",
        )
        self.assertIn("PLA Rapid è la voce generica", italian)
        self.assertIn("maps it to the Snapmaker PLA SnapSpeed", english)
        self.assertEqual(
            choose_base("Deeplee", "PLA Rapid", "Blue"),
            "Snapmaker PLA SnapSpeed @U1",
        )

    def test_petg_variants_keep_petg_family_defaults(self):
        page = enhance_new_spool_page(_new_spool_form("safe-token"), "it")
        self.assertIn("v.indexOf('PETG')===0?['1.27','240','75']", page)
        self.assertIn("this.value==='PLA Silk'?['1.24','230','60']", page)
        self.assertIn("['1.24','220','60']", page)

    def test_patch_installation_is_idempotent(self):
        def original(token: str, error: str = "", language: str = "it") -> str:
            return (
                '<select name="material" id="material">'
                '<option value="PLA">PLA</option>'
                '<option value="PLA Silk">PLA Silk</option>'
                '<option value="PETG">PETG</option>'
                '</select>'
                '<form method="post" action="/new-spool/preview"></form>'
            )

        fake_gui = SimpleNamespace(_new_spool_form=original)
        install_material_ui_patch(fake_gui)
        first_callable = fake_gui._new_spool_form
        install_material_ui_patch(fake_gui)
        self.assertIs(fake_gui._new_spool_form, first_callable)
        page = fake_gui._new_spool_form("token")
        self.assertEqual(page.count('<option value="PLA Rapid">'), 1)
        self.assertEqual(page.count('id="u1fa-material-families-hint"'), 1)


if __name__ == "__main__":
    unittest.main()
