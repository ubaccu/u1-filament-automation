from __future__ import annotations

import unittest

from u1_filament_automation.gui_picker_language_206 import localize_picker_search


class PickerLanguage206Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.page = (
            "<input placeholder='Cerca filamento / Search filament…'>"
            "<div>Nessun filamento trovato / No filament found</div>"
        )

    def test_italian_picker_text_is_italian_only(self):
        page = localize_picker_search(self.page, "it")
        self.assertIn("Cerca filamento…", page)
        self.assertIn("Nessun filamento trovato", page)
        self.assertNotIn("Search filament", page)
        self.assertNotIn("No filament found", page)
        self.assertNotIn(" / ", page)

    def test_english_picker_text_is_english_only(self):
        page = localize_picker_search(self.page, "en")
        self.assertIn("Search filament…", page)
        self.assertIn("No filament found", page)
        self.assertNotIn("Cerca filamento", page)
        self.assertNotIn("Nessun filamento trovato", page)
        self.assertNotIn(" / ", page)


if __name__ == "__main__":
    unittest.main()
