import unittest
from pathlib import Path
from types import SimpleNamespace

from u1_filament_automation.gui_dashboard import build_dashboard


class _Controller:
    moonraker_url = "http://192.0.2.10"
    spoolman_url = "http://127.0.0.1:7912"
    real_orca_dir = Path("/tmp/orca")

    def __init__(self, state: str, message_it: str = "", message_en: str = ""):
        self._update = SimpleNamespace(
            state=state,
            message_it=message_it,
            message_en=message_en,
        )

    def snapshot(self):
        return SimpleNamespace(state="idle")

    def update_snapshot(self):
        return self._update


class StartupUpdateVisibilityTests(unittest.TestCase):
    def test_home_refreshes_automatically_while_startup_check_is_running(self):
        page = build_dashboard(_Controller("checking"), "it")
        self.assertIn('id="u1fa-update-autorefresh"', page)
        self.assertIn("window.location.reload()", page)
        self.assertIn("Controllo in corso", page)

    def test_available_update_is_visible_without_manual_check(self):
        page = build_dashboard(
            _Controller(
                "available",
                "Nuova versione 2.0.4 disponibile",
                "Version 2.0.4 is available",
            ),
            "it",
        )
        self.assertNotIn('id="u1fa-update-autorefresh"', page)
        self.assertIn("Nuova versione 2.0.4 disponibile", page)
        self.assertIn("Mostra aggiornamento", page)
        self.assertIn('href="/updates"', page)
        self.assertIn("È disponibile una nuova versione di U1FA", page)

    def test_current_version_does_not_reload_home(self):
        page = build_dashboard(_Controller("current"), "it")
        self.assertNotIn('id="u1fa-update-autorefresh"', page)
        self.assertIn("Aggiornata", page)


if __name__ == "__main__":
    unittest.main()
