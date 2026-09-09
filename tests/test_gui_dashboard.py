import unittest
from pathlib import Path
from types import SimpleNamespace

from u1_filament_automation.gui_dashboard import (
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
    def test_dashboard_shows_services_and_four_toolheads(self):
        page = build_dashboard(FakeController(), "it")
        self.assertIn("U1FA Control Center", page)
        self.assertIn("U1 / Moonraker", page)
        self.assertIn("Spoolman", page)
        self.assertIn("Snapmaker Orca", page)
        self.assertIn("Adaptive PA", page)
        self.assertIn("Configurato", page)
        self.assertIn("Rilevato", page)
        for index in range(4):
            self.assertIn(f">T{index}<", page)
        self.assertIn("sola lettura", page)

    def test_dashboard_is_bilingual(self):
        page = build_dashboard(FakeController(), "en")
        self.assertIn("Quick status", page)
        self.assertIn("Configured", page)
        self.assertIn("Ready for spool assignment", page)
        self.assertIn("sends no command", page)

    def test_home_enhancement_is_idempotent(self):
        base = "<!doctype html><html><head></head><body><main><h1>Home</h1></main></body></html>"
        once = enhance_home_page(base, FakeController(), "it")
        twice = enhance_home_page(once, FakeController(), "it")
        self.assertEqual(once, twice)
        self.assertEqual(once.count(f'id="{DASHBOARD_ID}"'), 1)
        self.assertEqual(once.count('id="u1fa-dashboard-style-v17"'), 1)

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
