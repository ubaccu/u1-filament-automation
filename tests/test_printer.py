import base64
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from u1_filament_automation.cli import main
from u1_filament_automation.printer import (
    ADAPTIVE_PA_MACRO_PATH,
    ADAPTIVE_PA_MACRO_SHA256,
    FLOW_CALIBRATOR_PATH,
    LEGACY_BACKUP_PATH,
    PRINTER_CFG_INCLUDE,
    PRINTER_CFG_PATH,
    STOCK_SHA256,
    V6_SHA256,
    LocalPrinterTarget,
    MoonrakerClient,
    PrinterInstallError,
    PrinterSafetyStatus,
    SSHPrinterTarget,
    _remote_install_script,
    _remote_delete_path_script,
    _remote_restore_path_script,
    _remote_write_path_script,
    bundled_asset,
    inspect_calibrator,
    inspect_adaptive_pa_macro,
    install_printer_setup,
    plan_printer_setup,
    printer_cfg_includes_macro,
    require_safe_printer,
    sha256_bytes,
    validated_asset,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class FakeMoonrakerOpener:
    def __init__(
        self,
        print_state="standby",
        active=False,
        idle_state="Idle",
        machine_state=0,
    ):
        self.print_state = print_state
        self.active = active
        self.idle_state = idle_state
        self.machine_state = machine_state
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request.get_method(), request.full_url, timeout))
        if request.full_url.endswith("/printer/info"):
            return FakeResponse({"result": {"state": "ready"}})
        if request.full_url.endswith("/printer/objects/query"):
            return FakeResponse(
                {
                    "result": {
                        "status": {
                            "print_stats": {"state": self.print_state},
                            "virtual_sdcard": {"is_active": self.active},
                            "idle_timeout": {"state": self.idle_state},
                            "machine_state_manager": {
                                "main_state": self.machine_state
                            },
                        }
                    }
                }
            )
        if request.full_url.endswith("/printer/objects/list"):
            return FakeResponse(
                {
                    "result": {
                        "objects": [
                            "gcode_macro APA_COIL_RUN_ULTRA",
                            "gcode_macro APA_COIL_VERSION",
                        ]
                    }
                }
            )
        if request.full_url.endswith("/printer/restart"):
            return FakeResponse({"result": "ok"})
        raise AssertionError(request.full_url)


class PrinterInstallerTests(unittest.TestCase):
    def test_bundled_assets_match_recovered_backup(self):
        self.assertEqual(
            sha256_bytes(bundled_asset("flow_calibrator_stock.py").read_bytes()),
            STOCK_SHA256,
        )
        self.assertEqual(
            sha256_bytes(bundled_asset("flow_calibrator_v6.py").read_bytes()),
            V6_SHA256,
        )
        self.assertEqual(
            sha256_bytes(
                bundled_asset("adaptive_pa_macro.cfg").read_bytes()
            ),
            ADAPTIVE_PA_MACRO_SHA256,
        )

    def test_complete_setup_installs_flow_macro_and_existing_include(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = LocalPrinterTarget(Path(temporary))
            target.seed_stock_if_missing()
            target.seed_config_if_missing()

            plan = plan_printer_setup(target, loaded_by_klipper=False)
            self.assertTrue(plan.install_calibrator)
            self.assertTrue(plan.create_macro)
            self.assertFalse(plan.update_printer_cfg)
            result = install_printer_setup(
                target, loaded_by_klipper=False, power_cycle_required=False
            )

            self.assertEqual(inspect_calibrator(target).state, "v6-installed")
            self.assertEqual(
                sha256_bytes(target.read_path_bytes(ADAPTIVE_PA_MACRO_PATH)),
                ADAPTIVE_PA_MACRO_SHA256,
            )
            self.assertEqual([item.action for item in result.writes], ["created", "installed"])
            self.assertFalse(result.power_cycle_required)

    def test_setup_adds_missing_include_with_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = LocalPrinterTarget(Path(temporary))
            target.seed_stock_if_missing()
            config = target.path_for(PRINTER_CFG_PATH)
            config.parent.mkdir(parents=True)
            original = b"[include base/*.cfg]\n"
            config.write_bytes(original)

            result = install_printer_setup(target, loaded_by_klipper=False)

            self.assertIn(PRINTER_CFG_INCLUDE.encode(), config.read_bytes())
            cfg_write = next(item for item in result.writes if item.path == str(config))
            self.assertEqual(Path(cfg_write.backup_path).read_bytes(), original)

    def test_glob_include_already_covers_adaptive_macro(self):
        self.assertTrue(printer_cfg_includes_macro(b"[include *.cfg]\n"))
        self.assertTrue(
            printer_cfg_includes_macro(b"[include adaptive_pa_*.cfg]\n")
        )
        self.assertFalse(printer_cfg_includes_macro(b"[include base/*.cfg]\n"))

    def test_unknown_macro_blocks_complete_setup_before_any_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = LocalPrinterTarget(Path(temporary))
            target.seed_stock_if_missing()
            target.seed_config_if_missing()
            macro = target.path_for(ADAPTIVE_PA_MACRO_PATH)
            macro.write_bytes(b"macro dell'utente")

            with self.assertRaises(PrinterInstallError):
                install_printer_setup(target, loaded_by_klipper=False)

            self.assertEqual(inspect_calibrator(target).state, "stock-compatible")
            self.assertEqual(macro.read_bytes(), b"macro dell'utente")

    def test_failed_flow_install_rolls_back_macro_and_printer_cfg(self):
        class FailingFlowTarget(LocalPrinterTarget):
            def install_atomic(self, expected_sha256, new_data):
                raise PrinterInstallError("guasto simulato")

        with tempfile.TemporaryDirectory() as temporary:
            target = FailingFlowTarget(Path(temporary))
            target.seed_stock_if_missing()
            config = target.path_for(PRINTER_CFG_PATH)
            config.parent.mkdir(parents=True)
            original = b"[include base/*.cfg]\n"
            config.write_bytes(original)

            with self.assertRaises(PrinterInstallError):
                install_printer_setup(target, loaded_by_klipper=False)

            self.assertEqual(config.read_bytes(), original)
            self.assertFalse(target.path_for(ADAPTIVE_PA_MACRO_PATH).exists())
            self.assertEqual(inspect_calibrator(target).state, "stock-compatible")

    def test_exact_adaptive_pa_macro_is_complete_when_loaded(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = LocalPrinterTarget(Path(temporary))
            macro_path = target.path_for(ADAPTIVE_PA_MACRO_PATH)
            macro_path.parent.mkdir(parents=True)
            macro_path.write_bytes(
                Path("vendor/apa-chain-v6-safe/adaptive_pa_macro.cfg").read_bytes()
            )
            status = inspect_adaptive_pa_macro(target, loaded_by_klipper=True)
            self.assertEqual(status.state, "v6-installed")
            self.assertEqual(status.sha256, ADAPTIVE_PA_MACRO_SHA256)
            self.assertTrue(status.complete)

    def test_missing_or_unloaded_adaptive_pa_macro_is_incomplete(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = LocalPrinterTarget(Path(temporary))
            missing = inspect_adaptive_pa_macro(target, loaded_by_klipper=False)
            self.assertEqual(missing.state, "missing")
            self.assertFalse(missing.complete)

            macro_path = target.path_for(ADAPTIVE_PA_MACRO_PATH)
            macro_path.parent.mkdir(parents=True)
            macro_path.write_bytes(b"macro non riconosciuta")
            unknown = inspect_adaptive_pa_macro(target, loaded_by_klipper=True)
            self.assertEqual(unknown.state, "unknown-blocked")
            self.assertFalse(unknown.complete)

    def test_moonraker_confirms_ultra_macro_is_loaded(self):
        client = MoonrakerClient("http://u1.local", opener=FakeMoonrakerOpener())
        self.assertTrue(client.has_gcode_macro("APA_COIL_RUN_ULTRA"))
        self.assertFalse(client.has_gcode_macro("MACRO_INESISTENTE"))

    def test_moonraker_gcode_store_uses_read_only_official_endpoint(self):
        requests = []

        def opener(request, timeout):
            requests.append((request.get_method(), request.full_url, timeout))
            return FakeResponse(
                {
                    "result": {
                        "gcode_store": [
                            {
                                "message": "// Klipper state: Ready",
                                "time": 1.5,
                                "type": "response",
                            }
                        ]
                    }
                }
            )

        client = MoonrakerClient("http://u1.local", opener=opener)
        items = client.gcode_store(1000)
        self.assertEqual(items[0]["message"], "// Klipper state: Ready")
        self.assertEqual(
            requests,
            [("GET", "http://u1.local/server/gcode_store?count=1000", 5.0)],
        )

    def test_moonraker_run_gcode_uses_official_endpoint_and_exact_script(self):
        captured = {}

        def opener(request, timeout):
            captured["method"] = request.get_method()
            captured["url"] = request.full_url
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse({"result": "ok"})

        client = MoonrakerClient("http://u1.local", opener=opener)
        client.run_gcode("APA_COIL_RUN_ULTRA EXTRUDER=2 TEMP=220")
        self.assertEqual(captured["method"], "POST")
        self.assertEqual(captured["url"], "http://u1.local/printer/gcode/script")
        self.assertEqual(
            captured["body"],
            {"script": "APA_COIL_RUN_ULTRA EXTRUDER=2 TEMP=220"},
        )

    def test_local_sandbox_install_backup_and_restore(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = LocalPrinterTarget(Path(temporary))
            self.assertTrue(target.seed_stock_if_missing())
            self.assertEqual(inspect_calibrator(target).state, "stock-compatible")

            installed = target.install_atomic(
                STOCK_SHA256,
                validated_asset("flow_calibrator_v6.py", V6_SHA256),
            )
            self.assertEqual(installed.sha256_after, V6_SHA256)
            self.assertTrue(Path(installed.backup_path).is_file())
            self.assertEqual(
                sha256_bytes(Path(installed.backup_path).read_bytes()), STOCK_SHA256
            )

            restored = target.restore_atomic(installed.backup_path, V6_SHA256)
            self.assertEqual(restored.sha256_after, STOCK_SHA256)
            self.assertEqual(inspect_calibrator(target).state, "stock-compatible")

    def test_recovered_legacy_backup_is_trusted_only_at_exact_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = LocalPrinterTarget(Path(temporary))
            target.seed_stock_if_missing()
            installed = target.install_atomic(
                STOCK_SHA256,
                validated_asset("flow_calibrator_v6.py", V6_SHA256),
            )
            legacy = target.root.joinpath(*LEGACY_BACKUP_PATH.parts[1:])
            legacy.write_bytes(validated_asset("flow_calibrator_stock.py", STOCK_SHA256))
            restored = target.restore_atomic(str(legacy), V6_SHA256)
            self.assertEqual(restored.sha256_after, STOCK_SHA256)
            self.assertTrue(Path(installed.backup_path).is_file())

    def test_unknown_file_is_never_installed(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = LocalPrinterTarget(Path(temporary))
            target.path.parent.mkdir(parents=True)
            target.path.write_bytes(b"firmware sconosciuto")
            before = target.path.read_bytes()
            with self.assertRaises(PrinterInstallError):
                target.install_atomic(
                    STOCK_SHA256,
                    validated_asset("flow_calibrator_v6.py", V6_SHA256),
                )
            self.assertEqual(target.path.read_bytes(), before)
            self.assertEqual(list(target.path.parent.glob("*U1FA_BACKUP_*")), [])

    def test_firmware_update_with_unknown_original_blocks_setup_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = LocalPrinterTarget(Path(temporary))
            target.path.parent.mkdir(parents=True)
            target.path.write_bytes(b"nuovo flow_calibrator firmware 1.6 non validato")
            before = target.path.read_bytes()
            with self.assertRaisesRegex(PrinterInstallError, "non riconosciuta"):
                plan_printer_setup(target, loaded_by_klipper=False)
            self.assertEqual(target.path.read_bytes(), before)
            self.assertEqual(list(target.root.rglob("*U1FA_BACKUP_*")), [])

    @unittest.skipIf(os.name == "nt", "gli script remoti sono eseguiti sulla U1 POSIX")
    def test_remote_script_rechecks_hash_and_writes_atomically(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "flow_calibrator.py"
            target.write_bytes(validated_asset("flow_calibrator_stock.py", STOCK_SHA256))
            v6 = validated_asset("flow_calibrator_v6.py", V6_SHA256)
            import base64

            script = _remote_install_script(
                str(target),
                STOCK_SHA256,
                V6_SHA256,
                base64.b64encode(v6).decode("ascii"),
            )
            result = subprocess.run(
                ["python3", "-"],
                input=script,
                text=True,
                capture_output=True,
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(sha256_bytes(target.read_bytes()), V6_SHA256)
            self.assertEqual(
                sha256_bytes(Path(payload["backup_path"]).read_bytes()), STOCK_SHA256
            )

    @unittest.skipIf(os.name == "nt", "gli script remoti sono eseguiti sulla U1 POSIX")
    def test_remote_generic_scripts_create_update_restore_and_delete(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            macro = root / "adaptive_pa_macro.cfg"
            macro_data = b"[gcode_macro TEST]\ngcode:\n  M400\n"
            create_script = _remote_write_path_script(
                str(macro), None, sha256_bytes(macro_data),
                base64.b64encode(macro_data).decode("ascii"),
            )
            created = subprocess.run(
                ["python3", "-"], input=create_script, text=True,
                capture_output=True, check=True,
            )
            self.assertTrue(json.loads(created.stdout)["ok"])
            self.assertEqual(macro.read_bytes(), macro_data)

            config = root / "printer.cfg"
            before = b"[include base.cfg]\n"
            after = before + b"[include adaptive_pa_macro.cfg]\n"
            config.write_bytes(before)
            update_script = _remote_write_path_script(
                str(config), sha256_bytes(before), sha256_bytes(after),
                base64.b64encode(after).decode("ascii"),
            )
            updated = subprocess.run(
                ["python3", "-"], input=update_script, text=True,
                capture_output=True, check=True,
            )
            update_payload = json.loads(updated.stdout)
            self.assertTrue(update_payload["ok"])
            self.assertEqual(config.read_bytes(), after)

            restore_script = _remote_restore_path_script(
                str(config), update_payload["backup_path"],
                sha256_bytes(after), sha256_bytes(before),
            )
            restored = subprocess.run(
                ["python3", "-"], input=restore_script, text=True,
                capture_output=True, check=True,
            )
            self.assertTrue(json.loads(restored.stdout)["ok"])
            self.assertEqual(config.read_bytes(), before)

            deleted = subprocess.run(
                ["python3", "-"],
                input=_remote_delete_path_script(str(macro), sha256_bytes(macro_data)),
                text=True, capture_output=True, check=True,
            )
            self.assertTrue(json.loads(deleted.stdout)["ok"])
            self.assertFalse(macro.exists())

    def test_moonraker_state_uses_official_read_only_endpoints(self):
        opener = FakeMoonrakerOpener()
        client = MoonrakerClient("http://u1.local", opener=opener)
        status = client.safety_status()
        self.assertTrue(status.safe_to_modify)
        self.assertEqual(
            [item[1].removeprefix("http://u1.local") for item in opener.requests],
            ["/printer/info", "/printer/objects/query"],
        )

    def test_snapmaker_numeric_zero_is_idle(self):
        status = MoonrakerClient(
            "http://u1.local", opener=FakeMoonrakerOpener(machine_state=0)
        ).safety_status()
        self.assertEqual(status.machine_state, "0")
        self.assertTrue(status.safe_to_modify)

    def test_snapmaker_nonzero_machine_states_are_blocked(self):
        for machine_state in range(1, 14):
            status = MoonrakerClient(
                "http://u1.local",
                opener=FakeMoonrakerOpener(machine_state=machine_state),
            ).safety_status()
            with self.subTest(machine_state=machine_state):
                self.assertFalse(status.safe_to_modify)

    def test_password_auth_uses_hidden_temporary_askpass(self):
        captured = {}

        def fake_run(command, **kwargs):
            captured["command"] = command
            captured["environment"] = kwargs["env"]
            captured["start_new_session"] = kwargs["start_new_session"]
            payload = {
                "ok": True,
                "data": base64.b64encode(b"calibratore").decode("ascii"),
            }
            return subprocess.CompletedProcess(
                command, 0, stdout=json.dumps(payload) + "\n", stderr=""
            )

        target = SSHPrinterTarget(
            "root@192.168.1.51",
            ask_password=True,
            password_provider=lambda: "snapmaker",
        )
        with patch("u1_filament_automation.printer.subprocess.run", fake_run):
            self.assertEqual(target.read_bytes(), b"calibratore")

        command_text = " ".join(captured["command"])
        self.assertIn("BatchMode=no", command_text)
        self.assertIn("NumberOfPasswordPrompts=1", command_text)
        self.assertNotIn("snapmaker", command_text)
        self.assertTrue(captured["start_new_session"])
        self.assertEqual(
            captured["environment"]["U1FA_SSH_PASSWORD"], "snapmaker"
        )
        self.assertFalse(Path(captured["environment"]["SSH_ASKPASS"]).exists())

    def test_missing_system_ssh_client_is_reported_before_connection(self):
        target = SSHPrinterTarget("root@u1.local")
        with (
            patch("u1_filament_automation.printer.shutil.which", return_value=None),
            patch("u1_filament_automation.printer.subprocess.run") as run,
            self.assertRaisesRegex(PrinterInstallError, "OpenSSH Client not found"),
        ):
            target.read_bytes()
        run.assert_not_called()

    def test_printing_or_paused_state_blocks_modification(self):
        for state in ("printing", "paused"):
            client = MoonrakerClient(
                "http://u1.local", opener=FakeMoonrakerOpener(print_state=state)
            )
            with self.subTest(state=state), self.assertRaises(PrinterInstallError):
                require_safe_printer(client)

    def test_virtual_sd_active_blocks_even_if_standby(self):
        status = PrinterSafetyStatus("ready", "standby", True, "Idle", "IDLE")
        self.assertFalse(status.safe_to_modify)

    def test_flow_calibration_and_manual_activity_are_blocked(self):
        self.assertFalse(
            PrinterSafetyStatus(
                "ready", "standby", False, "Idle", "FLOW_CALIBRATION"
            ).safe_to_modify
        )
        self.assertFalse(
            PrinterSafetyStatus(
                "ready", "standby", False, "Printing", "IDLE"
            ).safe_to_modify
        )

    def test_cli_sandbox_runs_full_install_without_printer(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = io.StringIO()
            with redirect_stdout(output):
                result = main(
                    ["printer-install", "--sandbox-root", temporary, "--apply"]
                )
            self.assertEqual(result, 0)
            self.assertIn("Modalità SANDBOX locale", output.getvalue())
            target = LocalPrinterTarget(Path(temporary))
            self.assertEqual(inspect_calibrator(target).state, "v6-installed")
            self.assertEqual(len(list(target.path.parent.glob("*U1FA_BACKUP_*"))), 1)

    def test_cli_real_write_without_confirmation_connects_to_nothing(self):
        output = io.StringIO()
        with patch("u1_filament_automation.cli._printer_target") as target_factory:
            with redirect_stdout(output):
                result = main(
                    [
                        "printer-install",
                        "--ssh-target",
                        "lava@192.168.1.51",
                        "--moonraker-url",
                        "http://192.168.1.51",
                        "--apply",
                    ]
                )
        self.assertEqual(result, 2)
        self.assertIn("Nessun collegamento", output.getvalue())
        target_factory.assert_not_called()

    def test_real_install_requires_manual_power_cycle_and_never_soft_restarts(self):
        class NoAutomaticRestart:
            def safety_status(self):
                return PrinterSafetyStatus(
                    "ready", "standby", False, "Idle", "IDLE"
                )

            def restart_klipper(self):
                raise AssertionError("il soft restart non deve essere chiamato")

            def has_gcode_macro(self, name):
                return False

        with tempfile.TemporaryDirectory() as temporary:
            target = LocalPrinterTarget(Path(temporary))
            target.seed_stock_if_missing()
            target.seed_config_if_missing()
            output = io.StringIO()
            with patch(
                "u1_filament_automation.cli._printer_target",
                return_value=(target, NoAutomaticRestart()),
            ), redirect_stdout(output):
                result = main(
                    [
                        "printer-install",
                        "--ssh-target",
                        "lava@192.168.1.51",
                        "--moonraker-url",
                        "http://192.168.1.51",
                        "--apply",
                        "--confirm-printer-write",
                    ]
                )
            self.assertEqual(result, 0)
            self.assertIn("Spegnere completamente", output.getvalue())
            self.assertIn("semplice RESTART", output.getvalue())
            self.assertEqual(inspect_calibrator(target).state, "v6-installed")

    def test_invalid_python_is_rejected_before_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = LocalPrinterTarget(Path(temporary))
            target.seed_stock_if_missing()
            with self.assertRaises(PrinterInstallError):
                target.install_atomic(STOCK_SHA256, b"def codice_non_valido(:\n")
            self.assertEqual(inspect_calibrator(target).state, "stock-compatible")
            self.assertEqual(list(target.path.parent.glob("*U1FA_BACKUP_*")), [])

    def test_default_path_is_recovered_u1_path(self):
        self.assertEqual(
            str(FLOW_CALIBRATOR_PATH),
            "/home/lava/klipper/klippy/extras/flow_calibrator.py",
        )


if __name__ == "__main__":
    unittest.main()
