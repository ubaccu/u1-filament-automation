import unittest

from u1_filament_automation.gui_208 import (
    _decorate_batch,
    _decorate_home,
)


ITALIAN_GATE_ERROR = (
    "Compatibilità firmware non verificata in questa sessione: "
    "eseguire prima il controllo configurazione stampante"
)


class UX208Tests(unittest.TestCase):
    def test_discord_is_added_to_community_and_sidebar(self):
        page = (
            "<html><head></head><body><main>"
            '<section id="u1fa-community-182"><div class="u1fa-community-actions">'
            '<a class="u1fa-social-btn u1fa-coffee-cta" href="coffee">Coffee</a>'
            "</div></section>"
            '<a class="u1fa-side-coffee" href="coffee">Coffee</a>'
            '<div class="u1fa-side-language"></div>'
            '<section id="u1fa-dashboard-v20"></section>'
            "</main></body></html>"
        )
        result = _decorate_home(page, "", "it")

        self.assertEqual(result.count("https://discord.gg/VVf7ubPdAT"), 2)
        self.assertIn("u1fa-discord-community", result)
        self.assertIn("u1fa-side-discord", result)
        self.assertIn("Community Discord U1FA", result)

    def test_single_calibration_gate_becomes_guided_printer_check(self):
        escaped_error = ITALIAN_GATE_ERROR
        page = (
            "<html><head></head><body><main>"
            f'<p class="warn">{escaped_error}</p>'
            '<section id="u1fa-dashboard-v20"></section>'
            "</main></body></html>"
        )
        result = _decorate_home(page, ITALIAN_GATE_ERROR, "it")

        self.assertIn("Controllo U1 richiesto prima della calibrazione", result)
        self.assertIn('href="/printer-setup"', result)
        self.assertIn("Controlla ora", result)
        self.assertIn("Non è stato inviato alcun comando di calibrazione", result)
        self.assertNotIn(f'<p class="warn">{escaped_error}</p>', result)

    def test_batch_gate_gets_same_guided_action(self):
        page = (
            "<html><head></head><body><main>"
            "<h1>Calibrazione sequenziale</h1>"
            f'<p class="warn">{ITALIAN_GATE_ERROR}</p>'
            "</main></body></html>"
        )
        result = _decorate_batch(page, ITALIAN_GATE_ERROR, "it")

        self.assertIn("Controllo U1 richiesto prima della calibrazione", result)
        self.assertIn("Controlla ora", result)
        self.assertIn('href="/printer-setup"', result)

    def test_unrelated_error_does_not_show_printer_check_notice(self):
        page = (
            "<html><head></head><body><main>"
            '<p class="warn">Altro errore</p>'
            '<section id="u1fa-dashboard-v20"></section>'
            "</main></body></html>"
        )
        result = _decorate_home(page, "Altro errore", "it")

        self.assertNotIn("u1fa-208-printer-check", result)
        self.assertIn("Altro errore", result)


if __name__ == "__main__":
    unittest.main()
