import unittest
from pathlib import Path
from types import SimpleNamespace

from u1_filament_automation.gui_materials import install_material_ui_patch


class FakeController:
    moonraker_url = "http://192.0.2.10:7125"
    spoolman_url = "http://127.0.0.1:7912"
    real_orca_dir = Path("/tmp/Snapmaker Orca")

    def snapshot(self):
        return SimpleNamespace(state="idle")

    def update_snapshot(self):
        return SimpleNamespace(state="current")


class GUIHomeCleanupTests(unittest.TestCase):
    def _module(self):
        def home(controller, token, error="", language="it"):
            if language == "en":
                return """<!doctype html><html><head></head><body><main>
<h1>U1 Filament Automation</h1>
<p class="muted">Spoolman spool → Snapmaker Orca profile → Adaptive PA calibration.</p>
<div class="card"><p class="warn"><strong>Private beta for testing.</strong> Read-only first.</p></div>
<div class="card"><h2>U1FA updates</h2><p>legacy update</p></div>
<div class="card"><h2>Connections</h2><p>legacy connections</p></div>
<div class="card"><h2>0. Set up or restore U1FA AutoPA Mod</h2><p>setup</p><p><a class="button secondary" href="/printer-setup">Check printer setup</a></p></div>
<div class="card"><h2>1. New spool</h2><p>spool</p></div>
<div class="card"><h2>2. Calibrate an existing spool</h2><p>calibration</p></div>
<div class="card"><p><strong>Active protection</strong></p></div>
</main></body></html>"""
            return """<!doctype html><html><head></head><body><main>
<h1>U1 Filament Automation</h1>
<p class="muted">Bobina Spoolman → profilo Snapmaker Orca → calibrazione Adaptive PA.</p>
<div class="card"><p class="warn"><strong>Versione beta privata per collaudo.</strong> Prima sola lettura.</p></div>
<div class="card"><h2>Aggiornamenti U1FA</h2><p>legacy update</p></div>
<div class="card"><h2>Connessioni</h2><p>legacy connections</p></div>
<div class="card"><h2>0. Configurazione o ripristino U1FA AutoPA Mod</h2><p>setup</p><p><a class="button secondary" href="/printer-setup">Controlla configurazione stampante</a></p></div>
<div class="card"><h2>1. Nuova bobina</h2><p>spool</p></div>
<div class="card"><h2>2. Calibra una bobina già presente</h2><p>calibration</p></div>
<div class="card"><p><strong>Protezione attiva</strong></p></div>
</main></body></html>"""

        def new_spool_form(token, error="", language="it"):
            return '<form method="post" action="/new-spool/preview"><select name="material" id="material"><option value="PLA">PLA</option></select></form>'

        module = SimpleNamespace(_home=home, _new_spool_form=new_spool_form)
        install_material_ui_patch(module)
        return module

    def test_italian_home_has_one_setup_entry_and_no_point_zero(self):
        module = self._module()
        page = module._home(FakeController(), "token", language="it")
        self.assertIn("Prima configurazione della U1", page)
        self.assertIn("usa il pulsante Controlla configurazione stampante qui sotto", page)
        self.assertNotIn("<h2>0. Configurazione o ripristino U1FA AutoPA Mod</h2>", page)
        self.assertNotIn("Sistema e manutenzione", page)
        self.assertEqual(page.count('href="/printer-setup"'), 1)
        self.assertIn("Gestione filamenti", page)
        self.assertIn("Sicurezza e applicazione", page)

    def test_english_home_has_one_setup_entry_and_no_point_zero(self):
        module = self._module()
        page = module._home(FakeController(), "token", language="en")
        self.assertIn("First printer setup", page)
        self.assertIn("use the Check printer setup button below", page)
        self.assertNotIn("<h2>0. Set up or restore U1FA AutoPA Mod</h2>", page)
        self.assertNotIn("System and maintenance", page)
        self.assertEqual(page.count('href="/printer-setup"'), 1)
        self.assertIn("Filament management", page)
        self.assertIn("Safety and application", page)


if __name__ == "__main__":
    unittest.main()
