from __future__ import annotations

import unittest

from u1_filament_automation import gui_language
from u1_filament_automation.gui_language_extra import translate_error_en


class EnglishTechnicalErrorCoverageTests(unittest.TestCase):
    def test_envelope_errors_are_translated(self):
        self.assertEqual(
            translate_error_en("Il flusso volumetrico massimo deve essere tra 0 e 100 mm3/s"),
            "Maximum volumetric flow must be between 0 and 100 mm3/s",
        )
        self.assertEqual(
            translate_error_en("Profilo Orca non leggibile: TEST.json: permission denied"),
            "Orca profile is not readable: TEST.json: permission denied",
        )

    def test_pa_profile_errors_are_translated(self):
        self.assertEqual(
            translate_error_en("La bobina Spoolman ID 42 corrisponde a più profili"),
            "Spoolman spool ID 42 matches multiple profiles",
        )
        self.assertEqual(
            translate_error_en("Creazione del backup fallita: disk full"),
            "Backup creation failed: disk full",
        )

    def test_printer_setup_errors_are_translated(self):
        self.assertEqual(
            translate_error_en("Versione del calibratore non riconosciuta: configurazione bloccata"),
            "Unrecognized calibrator version: setup blocked",
        )
        self.assertEqual(
            translate_error_en("Verifica finale macro Adaptive PA fallita"),
            "Final Adaptive PA macro verification failed",
        )

    def test_unknown_firmware_detail_contains_no_italian_tokens(self):
        translated = translate_error_en(
            "Firmware/componenti non convalidati: FULLVERSION trovato=<vuoto> atteso=2.0.0.205; file mancanti=/tmp/x / Firmware or components not validated."
        )
        self.assertIn("Firmware or components not validated", translated)
        self.assertIn("found=<empty>", translated)
        self.assertIn("expected=2.0.0.205", translated)
        self.assertIn("missing files=/tmp/x", translated)
        self.assertNotIn("trovato=", translated)
        self.assertNotIn("atteso=", translated)
        self.assertNotIn("file mancanti=", translated)

    def test_delete_partial_state_suffix_is_fully_english(self):
        translated = translate_error_en(
            "Cancellazione interrotta eliminando la bobina Spoolman ID 8: timeout Bobine già eliminate / Spools already deleted: 2, 4."
        )
        self.assertIn("Deletion stopped while removing Spoolman spool ID 8", translated)
        self.assertIn("Spools already deleted: 2, 4.", translated)
        self.assertNotIn("Cancellazione", translated)
        self.assertNotIn("Bobine già eliminate", translated)

    def test_material_creation_error_is_translated(self):
        self.assertEqual(
            translate_error_en(
                "Materiale non ancora associato a un profilo base Snapmaker; creazione bloccata"
            ),
            "Material is not yet associated with a Snapmaker base profile; creation blocked",
        )

    def test_main_language_module_uses_extended_translator(self):
        self.assertEqual(
            gui_language._translate_error_en("Filamento Spoolman non trovato o ID ambiguo"),
            "Spoolman filament not found or ID is ambiguous",
        )


if __name__ == "__main__":
    unittest.main()
