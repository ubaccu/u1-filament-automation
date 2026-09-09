import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from u1_filament_automation.gui import (
    CalibrationController,
    CalibrationSelection,
    GUIError,
    JobSnapshot,
    LOGO_ASSET,
    UpdateSnapshot,
    VALIDATED_U1_ENVELOPE,
    _connections_form,
    _envelope_controls,
    _home,
    _new_spool_form,
    _new_spool_request,
    _printer_setup_form,
    _printer_setup_preview,
    _status,
    _shutdown_page,
    _updates_page,
    build_calibration_commands,
    physical_to_internal,
    validate_temperature,
)
from u1_filament_automation.models import SpoolmanInventory
from u1_filament_automation.printer import (
    AdaptivePAMacroStatus,
    CalibratorStatus,
    PrinterInstallError,
    PrinterSetupPlan,
    PrinterSetupResult,
)
from u1_filament_automation.spoolman import NewSpoolRequest, ServiceError
from u1_filament_automation.update import UpdateAsset, UpdateInfo


class GUISafetyTests(unittest.TestCase):
    def test_official_logo_is_bundled_as_a_real_png(self):
        data = LOGO_ASSET.read_bytes()
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertGreater(len(data), 1000)

    def test_physical_slots_map_to_zero_based_klipper_extruders(self):
        self.assertEqual(
            [physical_to_internal(slot) for slot in (1, 2, 3, 4)],
            [0, 1, 2, 3],
        )

    def test_invalid_physical_slots_are_blocked(self):
        for slot in (0, 5, -1):
            with self.subTest(slot=slot), self.assertRaises(GUIError):
                physical_to_internal(slot)

    def test_temperature_safety_range(self):
        self.assertEqual(validate_temperature(170), 170)
        self.assertEqual(validate_temperature(300), 300)
        for temperature in (169, 301):
            with self.subTest(temperature=temperature), self.assertRaises(GUIError):
                validate_temperature(temperature)

    def test_blue_test_selection_builds_exact_validated_commands(self):
        envelope, run = build_calibration_commands(3, 220)
        self.assertEqual(
            envelope,
            "APA_COIL_SET_ENVELOPE LOW_SPEED=100 MID_SPEED=218 "
            "HIGH_SPEED=336 LOW_ACCEL=2000 MID_ACCEL=6000 HIGH_ACCEL=10000",
        )
        self.assertEqual(run, "APA_COIL_RUN_ULTRA EXTRUDER=2 TEMP=220")
        self.assertEqual(VALIDATED_U1_ENVELOPE.name, "U1 convalidato")

    def test_envelope_controls_offer_safe_auto_and_advanced_manual_modes(self):
        italian = _envelope_controls("it")
        english = _envelope_controls("en")
        self.assertIn("Automatico dal profilo filamento (consigliato)", italian)
        self.assertIn('name="manufacturer_min_speed"', italian)
        self.assertIn('name="manufacturer_max_speed"', italian)
        self.assertIn("Automatic from filament profile (recommended)", english)
        self.assertIn("Advanced manual", english)

    def test_manual_envelope_above_u1fa_cap_is_blocked(self):
        from u1_filament_automation.gui import Envelope

        unsafe = Envelope("unsafe", 100, 218, 337, 2000, 6000, 10000)
        with self.assertRaises(GUIError):
            build_calibration_commands(1, 220, unsafe)

    def test_controller_builds_deeplee_auto_envelope_from_orca_and_vendor_limits(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user = root / "user"
            system = root / "system"
            user.mkdir()
            system.mkdir()
            profile_name = "DEEPLEE PLA BLU METALLICO @Snapmaker U1 (0.4 nozzle)"
            (user / f"{profile_name}.json").write_text(
                json.dumps({
                    "name": profile_name,
                    "inherits": "Snapmaker PLA Basic @U1",
                }),
                encoding="utf-8",
            )
            (system / "Snapmaker PLA Basic @U1.json").write_text(
                json.dumps({
                    "name": "Snapmaker PLA Basic @U1",
                    "filament_max_volumetric_speed": ["15"],
                }),
                encoding="utf-8",
            )
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                root / "sandbox",
                system,
                real_orca_dir=user,
            )
            controller._accept_inventory(SpoolmanInventory(
                url="http://spoolman.test",
                vendors=[{"id": 3, "name": "DEEPLEE"}],
                filaments=[{
                    "id": 13,
                    "vendor_id": 3,
                    "material": "PLA",
                    "name": "PLA BLU METALLICO",
                }],
                spools=[{"id": 12, "filament_id": 13}],
            ))

            selection = controller.selection(
                profile_name,
                4,
                220,
                manufacturer_min_speed=30,
                manufacturer_max_speed=70,
            )

        self.assertEqual(selection.material, "PLA")
        self.assertEqual(selection.max_volumetric_speed, 15)
        self.assertEqual(selection.max_volumetric_source, "Orca: Snapmaker PLA Basic @U1")
        self.assertEqual(selection.internal_extruder, 3)
        self.assertEqual(
            selection.commands[0],
            "APA_COIL_SET_ENVELOPE LOW_SPEED=30 MID_SPEED=50 HIGH_SPEED=70 "
            "LOW_ACCEL=2000 MID_ACCEL=6000 HIGH_ACCEL=10000",
        )

    def test_home_exposes_new_spool_flow_even_with_empty_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                root / "sandbox",
                root / "system",
            )
            page = _home(controller, "safe-token")
        self.assertIn("Aggiungi nuova bobina", page)
        self.assertIn("Bobina Spoolman → profilo Snapmaker Orca", page)
        self.assertIn("Controlla configurazione stampante", page)
        self.assertIn("Chiudi applicazione", page)
        self.assertIn("Aggiornamenti U1FA", page)
        self.assertIn("lascia U1FA aperta", page)

    def test_calibration_status_repeats_keep_apps_warning_in_both_languages(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                root / "sandbox",
                root / "system",
            )
            italian = _status(controller, language="it")
            english = _status(controller, language="en")
        self.assertIn("U1FA aperta", italian)
        self.assertIn("Snapmaker Orca completamente chiuso", italian)
        self.assertIn("keep U1FA open", english)
        self.assertIn("Snapmaker Orca completely closed", english)

    def test_error_status_offers_bilingual_read_only_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                root / "sandbox",
                root / "system",
            )
            selection = CalibrationSelection("Profilo", 4, 3, 220)
            controller._job = JobSnapshot(
                "error",
                "HTTP Error 504",
                selection,
                started_at=100.0,
            )
            italian = _status(
                controller, language="it", token="safe-token"
            )
            english = _status(
                controller, language="en", token="safe-token"
            )
        self.assertIn('action="/recover"', italian)
        self.assertIn("Recupera ultima calibrazione", italian)
        self.assertIn("non invia alcun G-code", italian)
        self.assertIn("Recover latest calibration", english)
        self.assertIn("does not start another calibration", english)

    def test_update_banner_and_page_are_bilingual_and_verified(self):
        info = UpdateInfo(
            version="1.8.0-beta.1",
            tag="v1.8.0-beta.1",
            title="U1FA Beta 2",
            notes="Correzioni sicure / Safe fixes",
            release_url="https://github.com/ubaccu/u1-filament-automation/releases/tag/v1.8.0-beta.1",
            prerelease=True,
            asset=UpdateAsset(
                "U1-Filament-Automation-v1.8.0b1-macOS-arm64.dmg",
                "https://github.com/ubaccu/u1-filament-automation/releases/download/v1.8.0-beta.1/app.dmg",
                1024,
                "a" * 64,
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                root / "sandbox",
                root / "system",
            )
            controller._update = UpdateSnapshot(
                "available",
                "Nuova versione disponibile",
                "New version available",
                info=info,
            )
            italian_home = _home(controller, "safe-token", language="it")
            english_page = _updates_page(
                controller, "safe-token", language="en"
            )
        self.assertIn("Nuova versione disponibile", italian_home)
        self.assertIn("Mostra aggiornamento", italian_home)
        self.assertIn("Download and verify update", english_page)
        self.assertIn("a" * 64, english_page)
        self.assertIn("non aggiorna il firmware", italian_home)

    def test_update_check_runs_in_background(self):
        info = UpdateInfo(
            version="1.8.0",
            tag="v1.8.0",
            title="U1FA 1.8.0",
            notes="",
            release_url="https://github.com/ubaccu/u1-filament-automation/releases/tag/v1.8.0",
            prerelease=False,
            asset=UpdateAsset(
                "U1-Filament-Automation-v1.8.0-Windows-x64-Setup.exe",
                "https://github.com/ubaccu/u1-filament-automation/releases/download/v1.8.0/app.exe",
                1,
                "b" * 64,
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                root / "sandbox",
                root / "system",
                update_checker=lambda: info,
            )
            thread = controller.start_update_check()
            thread.join(timeout=1)
            result = controller.update_snapshot()
        self.assertEqual(result.state, "available")
        self.assertEqual(result.info.version, "1.8.0")

    def test_safe_shutdown_is_available_only_without_active_calibration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                root / "sandbox",
                root / "system",
            )
            idle = _shutdown_page(controller, "token", language="it")
            controller._job = JobSnapshot("running", "calibrazione")
            running = _shutdown_page(controller, "token", language="en")
        self.assertIn('action="/shutdown"', idle)
        self.assertIn("Chiudi davvero U1FA", idle)
        self.assertIn("Closing blocked", running)
        self.assertNotIn('action="/shutdown"', running)

    def test_first_start_requests_printer_address_without_ivan_ip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "",
                "http://127.0.0.1:7912",
                root / "sandbox",
                root / "system",
            )
            page = _home(controller, "safe-token")
        self.assertIn("Connessioni da configurare", page)
        self.assertIn("Configura U1 e Spoolman", page)
        self.assertNotIn("192.168.1.51</code>", page)

    def test_connection_form_is_bilingual_and_defaults_only_spoolman(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "",
                "http://127.0.0.1:7912",
                root / "sandbox",
                root / "system",
            )
            italian = _connections_form(controller, "token", language="it")
            english = _connections_form(controller, "token", language="en")
        self.assertIn("IP o hostname della Snapmaker U1", italian)
        self.assertIn("Verifica e salva", italian)
        self.assertIn("Snapmaker U1 IP or hostname", english)
        self.assertIn("Verify and save", english)
        self.assertIn("Automatic (recommended)", english)
        self.assertIn("this computer (127.0.0.1)", english)
        self.assertNotIn("192.168.1.51", italian)
        self.assertNotIn("192.168.1.51", english)

    def test_connection_setup_derives_ssh_and_saves_only_addresses(self):
        class FakeMoonraker:
            def safety_status(self):
                return object()

        class FakeSpoolman:
            def inventory(self):
                return SpoolmanInventory(url="http://127.0.0.1:7912")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_path = root / "connections.json"
            controller = CalibrationController(
                "",
                "http://127.0.0.1:7912",
                root / "sandbox",
                root / "system",
                spoolman_client_factory=FakeSpoolman,
                connection_config_path=config_path,
            )
            with patch(
                "u1_filament_automation.gui.MoonrakerClient",
                return_value=FakeMoonraker(),
            ):
                result = controller.configure_connections(
                    "192.168.50.25",
                    "127.0.0.1:7912",
                )
            payload = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual(result.moonraker_url, "http://192.168.50.25")
        self.assertEqual(controller.ssh_target, "root@192.168.50.25")
        self.assertEqual(
            payload,
            {
                "moonraker_url": "http://192.168.50.25",
                "spoolman_url": "http://127.0.0.1:7912",
            },
        )
        self.assertNotIn("password", payload)

    def test_blank_spoolman_address_uses_local_paxx_and_u1_detection(self):
        class FakeMoonraker:
            def safety_status(self):
                return object()

        found = SpoolmanInventory(url="http://192.168.50.25:7912")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "",
                "http://127.0.0.1:7912",
                root / "sandbox",
                root / "system",
            )
            with patch(
                "u1_filament_automation.gui.MoonrakerClient",
                return_value=FakeMoonraker(),
            ), patch(
                "u1_filament_automation.gui.candidates_from_moonraker",
                return_value=["http://paxx.local:7912"],
            ), patch(
                "u1_filament_automation.gui.first_working_inventory",
                return_value=(found, []),
            ) as detect:
                result = controller.configure_connections("192.168.50.25", "")

        candidates = detect.call_args.args[0]
        self.assertIn("http://127.0.0.1:7912", candidates)
        self.assertIn("http://paxx.local:7912", candidates)
        self.assertIn("http://192.168.50.25:7912", candidates)
        self.assertEqual(result.spoolman_url, "http://192.168.50.25:7912")

    def test_color_control_shows_picker_hex_and_live_sample(self):
        page = _new_spool_form("safe-token")
        self.assertIn('id="color-picker"', page)
        self.assertIn('id="color-hex"', page)
        self.assertIn('id="color-sample"', page)
        self.assertIn('id="color-mode"', page)
        self.assertIn('name="multi_color_hexes"', page)
        self.assertIn('name="multi_color_direction"', page)
        self.assertIn('id="multi-color-direction"', page)
        self.assertIn('id="multi-color-list"', page)
        self.assertIn('id="add-multi-color"', page)
        self.assertIn("multiColors=['#D9A62E','#D8494A']", page)
        self.assertIn("sample.style.backgroundColor=normalized", page)

    def test_material_selector_offers_pla_silk_with_230_degree_default(self):
        page = _new_spool_form("safe-token")
        self.assertIn('<option value="PLA Silk">PLA Silk</option>', page)
        self.assertIn("this.value==='PLA Silk'?['1.24','230','60']", page)

    def test_selected_pink_hex_is_preserved_for_spoolman(self):
        request = _new_spool_request({
            "vendor": "Bambu Lab",
            "material": "PLA",
            "name": "PLA RAPID ROSA",
            "color_hex": "#D290DF",
            "density": "1.24",
            "diameter": "1.75",
            "filament_weight": "1000",
            "empty_spool_weight": "0",
            "remaining_weight": "1000",
            "nozzle_temperature": "225",
            "bed_temperature": "60",
        })
        self.assertEqual(request.color_hex, "D290DF")

    def test_multicolor_spool_request_preserves_ordered_hexes(self):
        request = _new_spool_request({
            "vendor": "Snapmaker",
            "material": "PLA",
            "name": "Silk Sunset Ember",
            "color_mode": "multi",
            "color_hex": "#D9A62E",
            "multi_color_hexes": "#D9A62E,#D8494A",
            "multi_color_direction": "coaxial",
            "density": "1.24",
            "diameter": "1.75",
            "filament_weight": "1000",
            "empty_spool_weight": "0",
            "remaining_weight": "1000",
            "nozzle_temperature": "220",
            "bed_temperature": "65",
        })
        self.assertEqual(request.color_hex, "D9A62E")
        self.assertEqual(request.multi_color_hexes, ("D9A62E", "D8494A"))
        self.assertEqual(request.multi_color_direction, "coaxial")

    def test_setup_preview_requires_second_password_and_explicit_confirmation(self):
        plan = PrinterSetupPlan(
            calibrator=CalibratorStatus("flow.py", "abc", "stock-compatible"),
            macro=AdaptivePAMacroStatus("macro.cfg", None, "missing", False),
            install_calibrator=True,
            create_macro=True,
            update_printer_cfg=True,
            include_already_present=False,
        )
        from u1_filament_automation.gui import PreparedPrinterSetup

        page = _printer_setup_preview(PreparedPrinterSetup("ticket", plan), "token")
        self.assertIn('type="password"', page)
        self.assertIn('name="confirm"', page)
        self.assertIn("non invia RESTART", page)
        self.assertIn("procedo sotto la mia responsabilità", page)

    def test_setup_preview_with_nothing_to_write_has_no_apply_controls(self):
        plan = PrinterSetupPlan(
            calibrator=CalibratorStatus("flow.py", "abc", "v6-installed"),
            macro=AdaptivePAMacroStatus("macro.cfg", "def", "v6-installed", True),
            install_calibrator=False,
            create_macro=False,
            update_printer_cfg=False,
            include_already_present=True,
        )
        from u1_filament_automation.gui import PreparedPrinterSetup

        italian = _printer_setup_preview(
            PreparedPrinterSetup("unused-ticket", plan),
            "token",
            language="it",
        )
        english = _printer_setup_preview(
            PreparedPrinterSetup("unused-ticket", plan),
            "token",
            language="en",
        )
        self.assertIn("U1FA AutoPA Mod risulta già installata e completa", italian)
        self.assertIn("Nessun file è stato modificato", italian)
        self.assertIn("Return to home", english)
        self.assertNotIn('name="ssh_password"', italian)
        self.assertNotIn('name="confirm"', italian)
        self.assertNotIn("Applica davvero la configurazione", italian)
        self.assertNotIn("Apply the setup", english)

    def test_gui_can_switch_to_english_and_shows_both_printer_prerequisites(self):
        page = _printer_setup_form("safe-token", language="en")
        self.assertIn('<html lang="en">', page)
        self.assertIn("Stock Snapmaker U1 setup", page)
        self.assertIn("Advanced Mode", page)
        self.assertIn("Root Access", page)
        self.assertIn("Settings → Maintenance → Advanced Mode → Agree → Enable", page)
        self.assertIn("Settings → Maintenance → Root Access → Agree → Open", page)
        self.assertIn("U1 firmware 1.6.0 is pending validation", page)
        self.assertIn("Safety and liability notice", page)
        self.assertIn("If you are unsure, do not proceed", page)
        self.assertIn("provided without warranty under GPLv3", page)
        self.assertNotIn("Impostazioni", page)
        self.assertNotIn("Manutenzione", page)
        self.assertNotIn("Modalità avanzata", page)
        self.assertIn("If you have not changed the SSH password", page)
        self.assertIn("<code>snapmaker</code>", page)
        self.assertIn("/home/lava/klipper/klippy/extras/flow_calibrator.py", page)
        self.assertIn('name="printer_access_enabled"', page)

    def test_italian_printer_setup_paths_do_not_mix_english_labels(self):
        page = _printer_setup_form("safe-token", language="it")
        self.assertIn("Impostazioni → Manutenzione → Modalità avanzata → Accetto → Abilita", page)
        self.assertIn("Impostazioni → Manutenzione → Accesso Root → Accetto → Apri", page)
        self.assertIn("Se non hai modificato la password SSH", page)
        self.assertIn("<code>snapmaker</code>", page)
        self.assertIn("Avviso di sicurezza e responsabilità", page)
        self.assertIn("Se hai dubbi, non procedere", page)
        self.assertIn("fornito senza garanzia ai sensi della GPLv3", page)
        self.assertNotIn("Settings →", page)
        self.assertNotIn("Maintenance →", page)

    def test_english_home_exposes_language_selector_and_monitor(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                root / "sandbox",
                root / "system",
            )
            controller.set_language("en")
            page = _home(controller, "safe-token", language="en")
        self.assertIn("Set up or restore U1FA AutoPA Mod", page)
        self.assertIn("Private beta for testing", page)
        self.assertIn("Automatic synchronization active", page)
        self.assertIn('href="/language?lang=it"', page)
        self.assertIn('href="/language?lang=en"', page)

    def test_monitor_waits_and_retries_when_spoolman_is_offline_at_startup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                root / "sandbox",
                root / "system",
                real_orca_dir=root / "real-orca",
                monitor_interval=5,
            )
            with patch.object(
                controller,
                "sync_external_profiles",
                side_effect=ServiceError("connection refused"),
            ):
                controller.start_profile_monitor()
                snapshot = controller.monitor_snapshot()
                page = _home(controller, "safe-token", language="en")
                self.assertEqual(snapshot.state, "error")
                self.assertIn("retrying automatically every 5 seconds", snapshot.message_en)
                self.assertIn("Automatic synchronization waiting", page)
                self.assertIsNotNone(controller._monitor_thread)
                self.assertTrue(controller._monitor_thread.is_alive())
                controller.stop_profile_monitor()

    def test_printer_setup_rechecks_state_and_uses_one_time_ticket(self):
        plan = PrinterSetupPlan(
            calibrator=CalibratorStatus("flow.py", "abc", "stock-compatible"),
            macro=AdaptivePAMacroStatus("macro.cfg", None, "missing", False),
            install_calibrator=True,
            create_macro=True,
            update_printer_cfg=False,
            include_already_present=True,
        )
        result = PrinterSetupResult(
            calibrator=CalibratorStatus("flow.py", "def", "v6-installed"),
            macro=AdaptivePAMacroStatus("macro.cfg", "ghi", "v6-installed", False),
            writes=(),
            include_already_present=True,
            power_cycle_required=True,
        )

        class FakeMoonraker:
            def has_gcode_macro(self, name):
                return False

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test", "http://spoolman.test",
                root / "sandbox", root / "system",
                ssh_target="root@printer.test",
            )
            with patch("u1_filament_automation.gui.MoonrakerClient", return_value=FakeMoonraker()), \
                 patch("u1_filament_automation.gui.require_safe_printer") as safety, \
                 patch.object(controller, "_printer_target", return_value=object()), \
                 patch("u1_filament_automation.gui.plan_printer_setup", return_value=plan), \
                 patch("u1_filament_automation.gui.install_printer_setup", return_value=result):
                prepared = controller.prepare_printer_setup("prima-password")
                receipt = controller.apply_printer_setup(
                    prepared.ticket, "seconda-password"
                )
                self.assertEqual(receipt.result, result)
                self.assertEqual(safety.call_count, 3)
                with self.assertRaises(GUIError):
                    controller.apply_printer_setup(
                        prepared.ticket, "seconda-password"
                    )

    def test_completed_calibration_updates_only_real_orca(self):
        class FakeMoonraker:
            def run_gcode(self, script):
                return None

            def gcode_store(self, count):
                return []

        class FakeReport:
            def to_dict(self):
                return {"static_fallback": 0.01, "backup_path": "backup"}

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test", "http://spoolman.test",
                root / "sandbox", root / "system",
                real_orca_dir=root / "real-orca",
            )
            selection = CalibrationSelection("Profilo", 3, 2, 220)
            with patch("u1_filament_automation.gui.MoonrakerClient", return_value=FakeMoonraker()), \
                 patch("u1_filament_automation.gui.parse_gcode_store", return_value=[]), \
                 patch("u1_filament_automation.gui.new_gcode_entries", return_value=[object()]), \
                 patch("u1_filament_automation.gui.response_text", return_value="suite"), \
                 patch("u1_filament_automation.gui.last_complete_suite_span", return_value=(object(), 0, 1)), \
                 patch("u1_filament_automation.gui.update_pa_profile", return_value=FakeReport()) as update:
                controller._run_job(selection, [])

            self.assertEqual(update.call_count, 1)
            self.assertEqual(
                os.path.normcase(os.path.realpath(update.call_args_list[0].args[0])),
                os.path.normcase(os.path.realpath(root / "real-orca")),
            )
            self.assertEqual(controller.snapshot().state, "completed")

    def test_transient_504_is_retried_without_restarting_calibration(self):
        class FakeMoonraker:
            def __init__(self):
                self.store_calls = 0
                self.scripts = []

            def run_gcode(self, script):
                self.scripts.append(script)

            def gcode_store(self, count):
                self.store_calls += 1
                if self.store_calls == 1:
                    raise PrinterInstallError(
                        "Moonraker non raggiungibile: HTTP Error 504"
                    )
                return []

        class FakeReport:
            def to_dict(self):
                return {"static_fallback": 0.01, "backup_path": "backup"}

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                root / "sandbox",
                root / "system",
                real_orca_dir=root / "real-orca",
                poll_interval=0.001,
            )
            selection = CalibrationSelection("Profilo", 4, 3, 220)
            fake = FakeMoonraker()
            with patch(
                "u1_filament_automation.gui.MoonrakerClient",
                return_value=fake,
            ), patch(
                "u1_filament_automation.gui.time.sleep"
            ) as sleep, patch(
                "u1_filament_automation.gui.parse_gcode_store",
                return_value=[],
            ), patch(
                "u1_filament_automation.gui.new_gcode_entries",
                return_value=[object()],
            ), patch(
                "u1_filament_automation.gui.response_text",
                return_value="suite",
            ), patch(
                "u1_filament_automation.gui.last_complete_suite_span",
                return_value=(object(), 0, 1),
            ), patch(
                "u1_filament_automation.gui.update_pa_profile",
                return_value=FakeReport(),
            ) as update:
                controller._run_job(selection, [], started_at=100.0)

        self.assertEqual(fake.store_calls, 2)
        self.assertEqual(len(fake.scripts), 2)
        self.assertEqual(update.call_count, 1)
        self.assertTrue(sleep.called)
        self.assertEqual(controller.snapshot().state, "completed")

    def test_run_command_timeout_is_not_reported_as_calibration_failure(self):
        class FakeMoonraker:
            def __init__(self):
                self.scripts = []

            def run_gcode(self, script):
                self.scripts.append(script)
                if script.startswith("APA_COIL_RUN_ULTRA"):
                    raise PrinterInstallError("Moonraker non raggiungibile: timed out")

            def gcode_store(self, count):
                return []

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                root / "sandbox",
                root / "system",
                real_orca_dir=root / "real-orca",
                poll_interval=0.001,
            )
            selection = CalibrationSelection("Profilo", 1, 0, 220)
            fake = FakeMoonraker()
            with patch(
                "u1_filament_automation.gui.MoonrakerClient",
                return_value=fake,
            ), patch(
                "u1_filament_automation.gui.time.time",
                side_effect=[100.0, 100.0, 100.0, 100.0, 100.0],
            ), patch(
                "u1_filament_automation.gui.time.sleep",
                side_effect=lambda _: None,
            ):
                # The bounded loop is not allowed to spin forever in this
                # unit test; replace the parser with a completed suite path.
                with patch(
                    "u1_filament_automation.gui.parse_gcode_store",
                    return_value=[],
                ), patch(
                    "u1_filament_automation.gui.new_gcode_entries",
                    return_value=[object()],
                ), patch(
                    "u1_filament_automation.gui.response_text",
                    return_value="suite",
                ), patch(
                    "u1_filament_automation.gui.last_complete_suite_span",
                    return_value=(object(), 0, 1),
                ), patch(
                    "u1_filament_automation.gui.update_pa_profile",
                    return_value=type("Report", (), {"to_dict": lambda self: {}})(),
                ):
                    controller._run_job(selection, [], started_at=100.0)

        self.assertEqual(len(fake.scripts), 2)
        self.assertEqual(controller.snapshot().state, "completed")

    def test_recovery_applies_only_suite_completed_after_selected_run(self):
        class FakeMoonraker:
            def __init__(self):
                self.store_calls = 0

            def gcode_store(self, count):
                self.store_calls += 1
                return []

        class FakeCached:
            completed_at = 101.0
            suite = object()

        class FakeReport:
            def to_dict(self):
                return {"static_fallback": 0.01, "backup_path": "backup"}

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                root / "sandbox",
                root / "system",
                real_orca_dir=root / "real-orca",
            )
            selection = CalibrationSelection("Profilo", 4, 3, 220)
            fake = FakeMoonraker()
            with patch(
                "u1_filament_automation.gui.MoonrakerClient",
                return_value=fake,
            ), patch(
                "u1_filament_automation.gui.parse_gcode_store",
                return_value=[],
            ), patch(
                "u1_filament_automation.gui.latest_cached_suite",
                return_value=FakeCached(),
            ), patch(
                "u1_filament_automation.gui.update_pa_profile",
                return_value=FakeReport(),
            ) as update:
                controller._run_recovery(selection, started_at=100.0)

        self.assertEqual(fake.store_calls, 1)
        self.assertEqual(update.call_count, 1)
        self.assertEqual(update.call_args.args[1], "Profilo")
        self.assertEqual(controller.snapshot().state, "completed")

    def test_recovery_blocks_a_suite_from_an_older_calibration(self):
        class FakeMoonraker:
            def gcode_store(self, count):
                return []

        class OldCached:
            completed_at = 90.0
            suite = object()

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                root / "sandbox",
                root / "system",
                real_orca_dir=root / "real-orca",
            )
            selection = CalibrationSelection("Profilo", 4, 3, 220)
            with patch(
                "u1_filament_automation.gui.MoonrakerClient",
                return_value=FakeMoonraker(),
            ), patch(
                "u1_filament_automation.gui.parse_gcode_store",
                return_value=[],
            ), patch(
                "u1_filament_automation.gui.latest_cached_suite",
                return_value=OldCached(),
            ), patch(
                "u1_filament_automation.gui.update_pa_profile"
            ) as update:
                controller._run_recovery(selection, started_at=100.0)

        self.assertEqual(update.call_count, 0)
        self.assertEqual(controller.snapshot().state, "error")
        self.assertIn("precedente", controller.snapshot().message)


class _GUIFakeSpoolman:
    def __init__(self):
        self.current = SpoolmanInventory(url="http://spoolman.test")
        self.calls = []
        self.next_id = 10

    def inventory(self):
        return self.current

    def _created(self, kind, payload):
        self.next_id += 1
        result = {"id": self.next_id, **payload}
        self.calls.append((kind, payload))
        getattr(self.current, {"vendor": "vendors", "filament": "filaments", "spool": "spools"}[kind]).append(result)
        return result

    def create_vendor(self, payload):
        return self._created("vendor", payload)

    def create_filament(self, payload):
        return self._created("filament", payload)

    def create_spool(self, payload):
        return self._created("spool", payload)


class GUISpoolCreationTests(unittest.TestCase):
    def test_integrated_monitor_creates_external_spool_profile_once_and_respects_deletion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sandbox = root / "sandbox"
            real_orca = root / "real-orca"
            system = root / "system"
            system.mkdir()
            (system / "Snapmaker PLA SnapSpeed @U1.json").write_text(
                json.dumps({"version": "test"}),
                encoding="utf-8",
            )
            fake = _GUIFakeSpoolman()
            fake.current.vendors.append({"id": 1, "name": "External"})
            fake.current.filaments.append({
                "id": 2,
                "vendor_id": 1,
                "material": "PLA",
                "name": "PLA RAPID GREEN",
                "color_hex": "00FF00",
            })
            fake.current.spools.append({"id": 3, "filament_id": 2})
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                sandbox,
                system,
                spoolman_client_factory=lambda: fake,
                real_orca_dir=real_orca,
            )
            controller._monitor_state_path = root / "watch-state.json"
            first = controller.sync_external_profiles()
            profile = real_orca / "External PLA RAPID GREEN @Snapmaker U1 (0.4 nozzle).json"
            self.assertTrue(profile.is_file())
            self.assertEqual(first.counts().get("created"), 1)
            profile.unlink()
            second = controller.sync_external_profiles()
            self.assertFalse(profile.exists())
            self.assertEqual(second.counts().get("dismissed"), 1)

    def test_one_time_confirmation_creates_only_real_profile_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sandbox = root / "sandbox"
            real_orca = root / "real-orca"
            system = root / "system"
            system.mkdir()
            (system / "Snapmaker PLA SnapSpeed @U1.json").write_text(
                json.dumps({"version": "test"}),
                encoding="utf-8",
            )
            fake = _GUIFakeSpoolman()
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                sandbox,
                system,
                spoolman_client_factory=lambda: fake,
                real_orca_dir=real_orca,
            )
            request = NewSpoolRequest(
                vendor="Deeplee",
                material="PLA",
                name="PLA PRO RAPID BLUE",
                color_hex="2563EB",
                density=1.24,
                diameter=1.75,
                filament_weight=1000,
                empty_spool_weight=220,
                remaining_weight=1000,
                nozzle_temperature=220,
                bed_temperature=60,
            )

            prepared = controller.prepare_spool_creation(request)
            self.assertEqual(fake.calls, [])
            receipt = controller.create_prepared_spool(prepared.ticket)

            self.assertTrue(receipt.real_profile_path.is_file())
            self.assertEqual(list(sandbox.glob("*.json")), [])
            self.assertEqual([kind for kind, _ in fake.calls], ["vendor", "filament", "spool"])

    def test_existing_real_profile_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sandbox = root / "sandbox"
            real_orca = root / "real-orca"
            system = root / "system"
            real_orca.mkdir()
            system.mkdir()
            (system / "Snapmaker PLA SnapSpeed @U1.json").write_text(
                json.dumps({"version": "test"}), encoding="utf-8"
            )
            profile_name = "Deeplee PLA RAPID BLUE @Snapmaker U1 (0.4 nozzle)"
            existing = real_orca / f"{profile_name}.json"
            existing.write_text('{"owned_by":"user"}\n', encoding="utf-8")
            fake = _GUIFakeSpoolman()
            controller = CalibrationController(
                "http://printer.test",
                "http://spoolman.test",
                sandbox,
                system,
                spoolman_client_factory=lambda: fake,
                real_orca_dir=real_orca,
            )
            request = NewSpoolRequest(
                vendor="Deeplee", material="PLA", name="PLA RAPID BLUE",
                color_hex="2563EB", density=1.24, diameter=1.75,
                filament_weight=1000, empty_spool_weight=220,
                remaining_weight=1000, nozzle_temperature=220,
                bed_temperature=60,
            )

            prepared = controller.prepare_spool_creation(request)
            receipt = controller.create_prepared_spool(prepared.ticket)

            self.assertEqual(
                os.path.normcase(os.path.realpath(receipt.real_profile_path)),
                os.path.normcase(os.path.realpath(existing)),
            )
            self.assertEqual(existing.read_text(encoding="utf-8"), '{"owned_by":"user"}\n')
            with self.assertRaises(GUIError):
                controller.create_prepared_spool(prepared.ticket)
            self.assertEqual([kind for kind, _ in fake.calls], ["vendor", "filament", "spool"])


if __name__ == "__main__":
    unittest.main()
