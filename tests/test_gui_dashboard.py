import unittest
from pathlib import Path
from types import SimpleNamespace

from u1_filament_automation.gui_dashboard import (
    BUY_ME_A_COFFEE_URL,
    DASHBOARD_ID,
    build_dashboard,
    enhance_home_page,
    install_dashboard_patch,
)


class FakeController:
    moonraker_url = "http://192.0.2.10:7125"
    spoolman_url = "http://127.0.0.1:7912"
    real_orca_dir = Path("/tmp/Snapmaker Orca")

    def snapshot(self):
        return SimpleNamespace(state="idle")

    def update_snapshot(self):
        return SimpleNamespace(state="current")


class GUIDashboardTests(unittest.TestCase):
    def test_dashboard_shows_services_without_toolhead_assignment_cards(self):
        page = build_dashboard(FakeController(), "it")
        self.assertIn("U1FA Control Center", page)
        self.assertIn("U1 / Moonraker", page)
        self.assertIn("Spoolman", page)
        self.assertIn("Snapmaker Orca", page)
        self.assertIn("Adaptive PA", page)
        self.assertIn("Endpoint configurato", page)
        self.assertIn("Profili rilevati", page)
        self.assertNotIn("Pronto per assegnazione bobina", page)
        for index in range(4):
            self.assertNotIn(f">T{index}<", page)
        self.assertIn("sola lettura", page)

    def test_dashboard_is_bilingual(self):
        page = build_dashboard(FakeController(), "en")
        self.assertIn("Quick status", page)
        self.assertIn("Endpoint configured", page)
        self.assertNotIn("Ready for spool assignment", page)
        self.assertIn("Connections", page)
        self.assertIn("sends no command", page)

    def test_home_enhancement_is_idempotent(self):
        base = "<!doctype html><html><head></head><body><main><h1>Home</h1></main></body></html>"
        once = enhance_home_page(base, FakeController(), "it")
        twice = enhance_home_page(once, FakeController(), "it")
        self.assertEqual(once, twice)
        self.assertEqual(once.count(f'id="{DASHBOARD_ID}"'), 1)
        self.assertEqual(once.count('id="u1fa-dashboard-style-v20"'), 1)
        self.assertEqual(once.count('id="u1fa-first-setup-v20"'), 1)
        self.assertEqual(once.count('id="u1fa-support-v20"'), 1)

    def test_legacy_home_is_compacted_grouped_and_replaces_beta_box(self):
        base = """<!doctype html><html><head></head><body><main>
<h1>U1 Filament Automation</h1>
<p class="muted">Bobina Spoolman → profilo Snapmaker Orca → calibrazione Adaptive PA.</p>
<div class="card"><p class="warn"><strong>Versione beta privata per collaudo.</strong> Usa prima i controlli in sola lettura.</p></div>
<div class="card"><h2>Aggiornamenti U1FA</h2><p>legacy update</p></div>
<div class="card"><h2>Connessioni</h2><p>legacy connections</p></div>
<div class="card"><h2>0. Configurazione o ripristino U1FA AutoPA Mod</h2><p>setup</p><p><a class="button secondary" href="/printer-setup">Controlla configurazione stampante</a></p></div>
<div class="card"><h2>1. Nuova bobina</h2><p>spool</p></div>
<div class="card"><h2>2. Calibra una bobina già presente</h2><p>calibration</p></div>
<div class="card"><p><strong>Sincronizzazione automatica attiva</strong></p></div>
<div class="card"><p><strong>Protezione attiva</strong></p></div>
<div class="card"><p><strong>Applicazione</strong></p></div>
</main></body></html>"""
        page = enhance_home_page(base, FakeController(), "it")
        self.assertNotIn("legacy update", page)
        self.assertNotIn("legacy connections", page)
        self.assertNotIn("Versione beta privata per collaudo", page)
        self.assertIn("Sistema e manutenzione", page)
        self.assertIn("Gestione filamenti", page)
        self.assertIn("Sicurezza e applicazione", page)
        self.assertIn('id="u1fa-filament-group"', page)
        self.assertIn("2. Calibra una bobina già presente", page)
        self.assertNotIn("<h1>U1 Filament Automation</h1>", page)

    def test_first_setup_notice_is_visible_and_direct(self):
        base = "<!doctype html><html><head></head><body><main><h1>Home</h1></main></body></html>"
        italian = enhance_home_page(base, FakeController(), "it")
        english = enhance_home_page(base, FakeController(), "en")
        self.assertIn("Prima configurazione della U1", italian)
        self.assertIn("dopo ogni aggiornamento firmware", italian)
        self.assertIn('href="/printer-setup"', italian)
        self.assertIn("Controlla configurazione stampante", italian)
        self.assertIn("First printer setup", english)
        self.assertIn("after every U1 firmware update", english)
        self.assertIn("Check printer setup", english)

    def test_support_card_uses_exact_official_link_without_remote_image(self):
        base = "<!doctype html><html><head></head><body><main><h1>Home</h1></main></body></html>"
        page = enhance_home_page(base, FakeController(), "it")
        self.assertIn("Supporta lo sviluppo di U1FA", page)
        self.assertIn(BUY_ME_A_COFFEE_URL, page)
        self.assertIn("Buy me a coffee", page)
        self.assertIn('target="_blank"', page)
        self.assertIn('rel="noopener noreferrer"', page)
        self.assertNotIn("cdn.buymeacoffee.com", page)

    def test_patch_installation_is_idempotent(self):
        def original(controller, token, error="", language="it"):
            return "<!doctype html><html><head></head><body><main><h1>Home</h1></main></body></html>"

        fake_gui = SimpleNamespace(_home=original)
        install_dashboard_patch(fake_gui)
        first_callable = fake_gui._home
        install_dashboard_patch(fake_gui)
        self.assertIs(fake_gui._home, first_callable)
        page = fake_gui._home(FakeController(), "token")
        self.assertEqual(page.count(f'id="{DASHBOARD_ID}"'), 1)

    def test_missing_configuration_is_reported_without_probe(self):
        controller = SimpleNamespace(
            moonraker_url="",
            spoolman_url="",
            real_orca_dir=None,
            snapshot=lambda: SimpleNamespace(state="idle"),
            update_snapshot=lambda: SimpleNamespace(state="idle"),
        )
        page = build_dashboard(controller, "it")
        self.assertIn("Da configurare", page)
        self.assertIn("Non rilevato", page)


if __name__ == "__main__":
    unittest.main()
