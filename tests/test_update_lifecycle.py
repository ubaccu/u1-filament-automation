import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

from u1_filament_automation.update_lifecycle import (
    _opened_page,
    _schedule_server_shutdown,
    install_update_lifecycle_patch,
    installer_open_allowed,
)


class UpdateLifecycleTests(unittest.TestCase):
    def test_active_calibration_states_block_installer_auto_close(self):
        active = frozenset({"checking", "running", "recovering"})
        for state in active:
            with self.subTest(state=state):
                self.assertFalse(installer_open_allowed(state, active))
        for state in ("idle", "completed", "error", "blocked"):
            with self.subTest(state=state):
                self.assertTrue(installer_open_allowed(state, active))

    def test_success_page_explains_automatic_close_in_both_languages(self):
        fake_gui = SimpleNamespace(
            _page=lambda title, body, language="it": f"{language}|{title}|{body}"
        )
        path = Path("/tmp/U1FA-test.dmg")
        italian = _opened_page(fake_gui, path, "it")
        english = _opened_page(fake_gui, path, "en")
        self.assertIn("si chiuderà automaticamente", italian)
        self.assertIn("errore «in uso»", italian)
        self.assertIn("will now close automatically", english)
        self.assertIn("No command is sent", english)

    def test_server_shutdown_is_scheduled_after_success_response(self):
        called = threading.Event()

        class FakeServer:
            def shutdown(self):
                called.set()

        thread = _schedule_server_shutdown(FakeServer(), delay=0)
        thread.join(timeout=1)
        self.assertTrue(called.is_set())

    def test_handler_patch_installation_is_idempotent(self):
        def original_handler(controller, token):
            class BaseHandler:
                pass
            return BaseHandler

        fake_gui = SimpleNamespace(_handler=original_handler)
        install_update_lifecycle_patch(fake_gui)
        first = fake_gui._handler
        install_update_lifecycle_patch(fake_gui)
        self.assertIs(first, fake_gui._handler)
        self.assertTrue(getattr(first, "_u1fa_update_lifecycle_patch", False))


if __name__ == "__main__":
    unittest.main()
