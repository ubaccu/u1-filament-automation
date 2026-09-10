import unittest
from types import SimpleNamespace

from u1_filament_automation.gui_b23 import (
    _patch_new_spool_form,
    _patch_new_spool_preview,
    _prefill_new_spool_form,
    _private_lan_url,
    render_release_notes,
)


class GUIB23Tests(unittest.TestCase):
    def _item(self):
        return SimpleNamespace(
            vendor="eSUN",
            material="PLA",
            name="ePLA-Lite Rosso Fuoco",
            color_hex="BB2028",
            multi_color_hexes=(),
            multi_color_direction="",
            nozzle_temperature=220,
            bed_temperature=60,
            density=1.23,
            diameter=1.75,
            filament_weight=1000.0,
            remaining_weight=1000.0,
            empty_spool_weight=0.0,
            location="Rack 3",
            lot_nr="",
            comment="Creato con U1 Filament Automation",
        )

    def test_storage_location_label_is_unambiguous(self):
        fake = SimpleNamespace(
            _new_spool_form=lambda token, error="", language="it": (
                '<label>Posizione (facoltativa)</label>'
                '<input name="location" maxlength="64">'
            )
        )
        _patch_new_spool_form(fake)
        page = fake._new_spool_form("token")
        self.assertIn("Posizione bobina / stoccaggio (facoltativa)", page)
        self.assertIn("Rack 3", page)
        self.assertIn("non l’estrusore U1 1–4", page)

    def test_preview_shows_location_and_edit_posts_original_values(self):
        token = "safe-token"
        ticket = "ticket-1"
        fake = SimpleNamespace(
            _new_spool_preview=lambda prepared, token, language="it": (
                '<p><strong>Base Snapmaker:</strong> Snapmaker PLA Basic @U1</p>'
                '<form method="post" action="/new-spool/create">'
                f'<input type="hidden" name="token" value="{token}"><input type="hidden" name="ticket" value="{prepared.ticket}">'
                '<a class="button secondary" href="/new-spool">Modifica dati</a>'
                '</form>'
            )
        )
        _patch_new_spool_preview(fake)
        prepared = SimpleNamespace(
            ticket=ticket,
            plan=SimpleNamespace(request=self._item()),
        )
        page = fake._new_spool_preview(prepared, token)
        self.assertIn("Posizione bobina / stoccaggio:</strong> Rack 3", page)
        self.assertIn('formaction="/new-spool/edit"', page)
        self.assertIn('name="vendor" value="eSUN"', page)
        self.assertIn('name="location" value="Rack 3"', page)
        self.assertNotIn('href="/new-spool">Modifica dati', page)

    def test_edit_prefill_includes_real_spool_values(self):
        page = '<html><body><form><input name="vendor"><input name="location"></form></body></html>'
        restored = _prefill_new_spool_form(page, self._item())
        self.assertIn('"vendor": "eSUN"', restored)
        self.assertIn('"location": "Rack 3"', restored)
        self.assertIn('"density": "1.23"', restored)
        self.assertIn('"color_hex": "#BB2028"', restored)

    def test_release_notes_markdown_is_rendered_and_escaped(self):
        rendered = render_release_notes(
            "# Italiano\n\n## Novità\n- **Profilo** `PLA`\n- <script>alert(1)</script>"
        )
        self.assertIn("<h3>Italiano</h3>", rendered)
        self.assertIn("<h3>Novità</h3>", rendered)
        self.assertIn("<strong>Profilo</strong>", rendered)
        self.assertIn("<code>PLA</code>", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>alert", rendered)

    def test_detected_selection_only_accepts_private_http_lan(self):
        self.assertTrue(_private_lan_url("http://192.168.1.51"))
        self.assertTrue(_private_lan_url("http://10.0.0.22"))
        self.assertFalse(_private_lan_url("https://192.168.1.51"))
        self.assertFalse(_private_lan_url("http://127.0.0.1"))
        self.assertFalse(_private_lan_url("http://8.8.8.8"))


if __name__ == "__main__":
    unittest.main()
