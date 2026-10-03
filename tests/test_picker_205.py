from __future__ import annotations

import unittest
from types import SimpleNamespace

from u1_filament_automation.gui_picker import enhance_profile_picker_page
from u1_filament_automation.models import SpoolmanInventory


class FakeController:
    def __init__(self, profiles, inventory):
        self._profiles = tuple(profiles)
        self._inventory = inventory

    def profiles(self):
        return self._profiles


class ProfilePicker205Tests(unittest.TestCase):
    def setUp(self):
        self.alpha = SimpleNamespace(profile_name="Alpha PLA Green", spool_ids=(2,))
        self.beta = SimpleNamespace(profile_name="beta PETG Blue", spool_ids=(3,))
        self.zeta = SimpleNamespace(profile_name="Zeta PLA Red", spool_ids=(1,))
        self.inventory = SpoolmanInventory(
            url="http://spoolman.local",
            filaments=[
                {"id": 10, "color_hex": "FF0000"},
                {"id": 20, "color_hex": "00ff00"},
                {"id": 30, "multi_color_hexes": "0000FF,FFFFFF"},
            ],
            spools=[
                {"id": 1, "filament_id": 10},
                {"id": 2, "filament_id": 20},
                {"id": 3, "filament_id": 30},
            ],
        )
        self.controller = FakeController(
            (self.zeta, self.beta, self.alpha),
            self.inventory,
        )

    def test_single_picker_is_sorted_alphabetically_and_shows_hex_colour(self):
        page = (
            '<html><body><select name="profile_name" required>'
            '<option value="Zeta PLA Red">Zeta PLA Red</option>'
            '<option value="Alpha PLA Green">Alpha PLA Green</option>'
            '</select></body></html>'
        )
        rendered = enhance_profile_picker_page(page, self.controller, "en")
        self.assertLess(rendered.index("Alpha PLA Green"), rendered.index("beta PETG Blue"))
        self.assertLess(rendered.index("beta PETG Blue"), rendered.index("Zeta PLA Red"))
        self.assertIn("#00FF00", rendered)
        self.assertIn("#0000FF / #FFFFFF", rendered)
        self.assertIn('data-u1fa-colors="#FF0000"', rendered)
        self.assertIn('data-u1fa-profile-picker="1"', rendered)
        self.assertIn("u1fa-profile-color-swatch", rendered)

    def test_batch_picker_keeps_empty_option_and_uses_italian_spool_label(self):
        page = (
            '<html><body><select name="profile_name_2">'
            '<option value="">— non usare —</option>'
            '<option value="Zeta PLA Red">Zeta PLA Red</option>'
            '</select></body></html>'
        )
        rendered = enhance_profile_picker_page(page, self.controller, "it")
        self.assertIn('<option value="">— non usare —</option>', rendered)
        self.assertLess(rendered.index("Alpha PLA Green"), rendered.index("Zeta PLA Red"))
        self.assertIn("bobine [2]", rendered)
        self.assertIn("Colore:", rendered)

    def test_unknown_colour_does_not_break_picker(self):
        controller = FakeController(
            (SimpleNamespace(profile_name="No Color PLA", spool_ids=(9,)),),
            SpoolmanInventory(
                url="http://spoolman.local",
                filaments=[{"id": 90, "color_hex": "not-a-colour"}],
                spools=[{"id": 9, "filament_id": 90}],
            ),
        )
        page = '<select name="profile_name"><option>No Color PLA</option></select>'
        rendered = enhance_profile_picker_page(page, controller, "en")
        self.assertIn("No Color PLA", rendered)
        self.assertIn('data-u1fa-colors=""', rendered)


if __name__ == "__main__":
    unittest.main()
