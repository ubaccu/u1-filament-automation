from __future__ import annotations

import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

from u1_filament_automation import gui
from u1_filament_automation.gui import CalibrationSelection, Envelope, JobSnapshot
from u1_filament_automation.gui_language import (
    _translate_error_en,
    _translate_runtime_message_en,
    install_language_fix,
    load_language_preference,
    save_language_preference,
)


class LanguagePreferenceTests(unittest.TestCase):
    def test_preference_round_trip_survives_new_controller(self):
        with tempfile.TemporaryDirectory() as tmp:
            preference_path = Path(tmp) / "preferences.json"

            class FakeController:
                def __init__(self):
                    self._lock = threading.Lock()
                    self._language = "it"

                def language(self):
                    with self._lock:
                        return self._language

                def set_language(self, language):
                    with self._lock:
                        self._language = language

            fake_gui = SimpleNamespace(
                CalibrationController=FakeController,
                GUIError=RuntimeError,
                _preview=lambda selection, token, language="it": "",
                _status=lambda controller, language="it", token="": "",
                _handler=lambda controller, token: object,
            )
            install_language_fix(fake_gui, preference_path)

            first = FakeController()
            self.assertEqual(first.language(), "it")
            first.set_language("en")
            self.assertEqual(first.language(), "en")

            second = FakeController()
            self.assertEqual(second.language(), "en")
            self.assertEqual(load_language_preference(preference_path), "en")

    def test_invalid_or_corrupt_preference_falls_back_to_italian(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "preferences.json"
            target.write_text("not-json", encoding="utf-8")
            self.assertEqual(load_language_preference(target), "it")
            target.write_text('{"language":"fr"}\n', encoding="utf-8")
            self.assertEqual(load_language_preference(target), "it")

    def test_save_rejects_unsupported_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "preferences.json"
            with self.assertRaises(Exception):
                save_language_preference("fr", target)
            self.assertFalse(target.exists())


class EnglishCoverageTests(unittest.TestCase):
    def _selection(self) -> CalibrationSelection:
        return CalibrationSelection(
            profile_name="TEST PLA",
            physical_slot=1,
            internal_extruder=0,
            temperature=220,
            envelope=Envelope(
                name="Automatico filamento",
                low_speed=90,
                mid_speed=150,
                high_speed=210,
                low_accel=2000,
                mid_accel=6000,
                high_accel=10000,
            ),
            envelope_mode="auto",
            material="PLA",
            max_volumetric_speed=20.0,
            max_volumetric_source="correzione manuale",
            max_speed_from_flow=222,
            limiting_source="volumetric_flow",
            pa_k_min=0.15,
            pa_k_max=0.45,
            pa_k_source="Snapmaker U1 2.0.0.205 · ugello 0.4 mm",
        )

    def test_preview_removes_known_italian_dynamic_fragments(self):
        page = gui._preview(self._selection(), "token", "en")
        self.assertIn("manual override", page)
        self.assertIn("0.4 mm nozzle", page)
        self.assertNotIn("correzione manuale", page)
        self.assertNotIn("ugello 0.4 mm", page)

    def test_status_preserves_detailed_runtime_message_in_english(self):
        selection = self._selection()
        job = JobSnapshot(
            "running",
            "Connessione Moonraker temporaneamente interrotta; nuovo tentativo 3/8 tra 6 secondi. La calibrazione non viene riavviata.",
            selection,
            started_at=1.0,
        )
        controller = SimpleNamespace(snapshot=lambda: job)
        page = gui._status(controller, "en", "token")
        self.assertIn("Moonraker connection temporarily interrupted", page)
        self.assertIn("retry 3/8 in 6 seconds", page)
        self.assertNotIn("Connessione Moonraker temporaneamente interrotta", page)

    def test_english_form_translates_gui_error_text(self):
        page = gui._new_spool_form(
            "token",
            "Cartella reale di Snapmaker Orca non configurata",
            "en",
        )
        self.assertIn("Snapmaker Orca profile folder is not configured", page)
        self.assertNotIn("Cartella reale di Snapmaker Orca non configurata", page)

    def test_runtime_batch_message_is_translated(self):
        translated = _translate_runtime_message_en(
            "Coda completata: 4/4 bobine calibrate; ultimo profilo Snapmaker Orca aggiornato con backup."
        )
        self.assertEqual(
            translated,
            "Queue completed: 4/4 spools calibrated; the final Snapmaker Orca profile was updated after creating a backup.",
        )

    def test_common_gui_error_is_translated(self):
        self.assertEqual(
            _translate_error_en("Una calibrazione è già in corso"),
            "A calibration is already running",
        )


class LanguageRouteTests(unittest.TestCase):
    def test_invalid_language_request_does_not_reset_en(self):
        class Controller:
            def __init__(self):
                self.value = "en"

            def language(self):
                return self.value

            def set_language(self, language):
                if language not in {"it", "en"}:
                    raise gui.GUIError("invalid")
                self.value = language

        controller = Controller()
        server = gui.ThreadingHTTPServer(("127.0.0.1", 0), gui._handler(controller, "token"))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
            connection.request("GET", "/language?lang=fr")
            response = connection.getresponse()
            response.read()
            self.assertEqual(response.status, 303)
            self.assertEqual(controller.value, "en")
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
