import ast
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path, PurePosixPath
from unittest.mock import patch

from u1_filament_automation.firmware_compatibility import (
    CANDIDATE_205,
    DEPENDENCIES_152,
    DEPENDENCIES_205,
    EXTRAS,
    FULLVERSION_205,
    FULLVERSION_PATH,
    LEGACY_STOCK,
    MACRO_205_SHA256,
    MACRO_PATH,
    STOCK_205,
    VERSION_PATH,
    inspect_firmware,
    require_live_firmware,
)
from u1_filament_automation.printer import (
    PrinterInstallError,
    bundled_asset,
    sha256_bytes,
)
from u1_filament_automation.gui import CalibrationController, CalibrationSelection, GUIError


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class FirmwareFixtureTarget:
    """Read-only target used to exercise the same fixed paths as SSH."""

    def __init__(self, files):
        self.files = dict(files)

    def read_path_bytes(self, path: PurePosixPath) -> bytes:
        try:
            return self.files[path]
        except KeyError as exc:
            raise FileNotFoundError(str(path)) from exc


def _firmware_files(version: str, full_version: str, calibrator: bytes):
    files = {
        VERSION_PATH: version.encode() + b"\n",
        FULLVERSION_PATH: full_version.encode() + b"\n",
        EXTRAS / "flow_calibrator.py": calibrator,
        MACRO_PATH: b"# no macro in this fixture\n",
    }
    dependencies = DEPENDENCIES_152 if version == "1.5.2" else DEPENDENCIES_205
    fixture_dir = FIXTURES / ("firmware_152" if version == "1.5.2" else "firmware_205")
    for name in dependencies:
        files[EXTRAS / name] = (fixture_dir / name).read_bytes()
    return files


class FirmwareCompatibilityTests(unittest.TestCase):
    def test_official_205_allows_only_guarded_install(self):
        target = FirmwareFixtureTarget(
            _firmware_files(
                "2.0.0",
                FULLVERSION_205,
                bundled_asset("flow_calibrator_stock_205.py").read_bytes(),
            )
        )
        report = inspect_firmware(target)
        self.assertEqual(report.state, "stock-205-compatible")
        self.assertEqual(report.hashes["flow_calibrator.py"], STOCK_205)
        self.assertTrue(report.live_install_allowed)
        self.assertFalse(report.live_calibration_allowed)
        self.assertEqual(require_live_firmware(target), report)
        with self.assertRaises(PrinterInstallError):
            require_live_firmware(target, calibration=True)

    def test_candidate_205_is_hash_pinned_but_needs_exact_macro_for_calibration(self):
        candidate = bundled_asset("flow_calibrator_205_candidate.py").read_bytes()
        self.assertEqual(sha256_bytes(candidate), CANDIDATE_205)
        files = _firmware_files("2.0.0", FULLVERSION_205, candidate)
        report = inspect_firmware(FirmwareFixtureTarget(files))
        self.assertEqual(report.state, "candidate-205-installed")
        self.assertEqual(report.hashes["flow_calibrator.py"], CANDIDATE_205)
        self.assertTrue(report.live_install_allowed)
        self.assertFalse(report.live_calibration_allowed)

        files[MACRO_PATH] = bundled_asset("adaptive_pa_macro_205.cfg").read_bytes()
        report = inspect_firmware(FirmwareFixtureTarget(files))
        self.assertEqual(report.hashes["adaptive_pa_macro.cfg"], MACRO_205_SHA256)
        self.assertTrue(report.live_calibration_allowed)
        self.assertEqual(require_live_firmware(
            FirmwareFixtureTarget(files), calibration=True
        ), report)

    def test_legacy_v6_on_205_is_incompatible(self):
        report = inspect_firmware(
            FirmwareFixtureTarget(
                _firmware_files(
                    "2.0.0",
                    FULLVERSION_205,
                    bundled_asset("flow_calibrator_v6.py").read_bytes(),
                )
            )
        )
        self.assertEqual(report.state, "legacy-v6-on-new-firmware-blocked")

    def test_future_version_and_missing_component_fail_closed(self):
        files = _firmware_files(
            "2.0.0", FULLVERSION_205, bundled_asset("flow_calibrator_stock_205.py").read_bytes()
        )
        files[VERSION_PATH] = b"2.0.1\n"
        self.assertEqual(inspect_firmware(FirmwareFixtureTarget(files)).state, "unknown-blocked")
        del files[EXTRAS / "print_task_config.py"]
        files[VERSION_PATH] = b"2.0.0\n"
        report = inspect_firmware(FirmwareFixtureTarget(files))
        self.assertEqual(report.state, "unknown-blocked")
        self.assertIn(str(EXTRAS / "print_task_config.py"), report.missing)

    def test_legacy_152_baseline_remains_install_compatible(self):
        stock = bundled_asset("flow_calibrator_stock.py").read_bytes()
        self.assertEqual(sha256_bytes(stock), LEGACY_STOCK)
        report = inspect_firmware(
            FirmwareFixtureTarget(_firmware_files("1.5.2", "1.5.2", stock))
        )
        self.assertEqual(report.state, "legacy-compatible")
        self.assertTrue(report.live_install_allowed)
        self.assertFalse(report.live_calibration_allowed)

    def test_candidate_205_compiles_and_uses_new_firmware_api(self):
        stock_path = bundled_asset("flow_calibrator_stock_205.py")
        candidate_path = bundled_asset("flow_calibrator_205_candidate.py")
        compile(stock_path.read_text(encoding="utf-8"), str(stock_path), "exec")
        compile(candidate_path.read_text(encoding="utf-8"), str(candidate_path), "exec")
        tree = ast.parse(candidate_path.read_text(encoding="utf-8"))
        functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        self.assertIn("cmd_FLOW_CHAIN_STATUS", functions)
        self.assertIn("cmd_FLOW_CHAIN_CLOSE", functions)
        self.assertIn("cmd_FLOW_CALIBRATE", functions)

        api_calls = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr in {"get_flow_k", "get_filament_parameters", "is_allow_to_print"}:
                api_calls.append((node.func.attr, len(node.args)))
        self.assertTrue(api_calls)
        self.assertTrue(all(argument_count == 5 for _, argument_count in api_calls))
        source = candidate_path.read_text(encoding="utf-8")
        self.assertIn("FLOW_CHAIN_STATUS", source)
        self.assertIn("FLOW_CHAIN_CLOSE", source)
        self.assertIn("CHAIN_LAST", source)
        self.assertIn("APA_MEASURE_ONLY", source)
        self.assertIn("APA_STABILIZE", source)
        self.assertIn("apa_stabilize_time", source)
        self.assertIn("thermal stabilization", source)
        self.assertIn("native/internal flow K not modified", source)
        self.assertIn("restored previous PA", source)

    def test_chain_macro_has_one_final_cell_and_a_manual_safe_close(self):
        macro = bundled_asset("adaptive_pa_macro_205.cfg").read_text(encoding="utf-8")
        run_all = macro.split("[gcode_macro APA_COIL_RUN_ALL]", 1)[1].split(
            "[gcode_macro APA_COIL_RUN_ULTRA]", 1
        )[0]
        self.assertEqual(run_all.count("CHAIN_LAST=0"), 4)
        self.assertEqual(run_all.count("CHAIN_LAST=1"), 1)
        self.assertIn("APA_COIL_RUN_ALL", macro.split(
            "[gcode_macro APA_COIL_RUN_ULTRA]", 1
        )[1])
        self.assertIn("[gcode_macro APA_COIL_CHAIN_CLOSE]", macro)
        self.assertIn("FLOW_CHAIN_CLOSE", macro)
        self.assertGreaterEqual(macro.count("APA_MEASURE_ONLY=1"), 3)
        self.assertIn('params.ALGORITHM|default("AUTO")', macro)
        self.assertIn("OS_COUNT", macro)

    def test_candidate_manual_chain_close_is_idempotent_and_turns_heater_off(self):
        candidate = bundled_asset("flow_calibrator_205_candidate.py")
        package_name = "_u1fa_flow_205_test"
        module_name = f"{package_name}.flow_calibrator"
        package = types.ModuleType(package_name)
        package.__path__ = []
        motion_report = types.ModuleType(f"{package_name}.motion_report")
        motion_report.PrinterMotionReport = object
        queuefile = types.ModuleType("queuefile")
        queuefile.async_write_file = lambda *args, **kwargs: None
        spec = importlib.util.spec_from_file_location(module_name, candidate)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {
            package_name: package,
            f"{package_name}.motion_report": motion_report,
            "queuefile": queuefile,
            module_name: module,
        }):
            spec.loader.exec_module(module)

        class Extruder:
            def get_heater(self):
                return "heater"

        class Toolhead:
            def __init__(self):
                self.extruder = Extruder()
                self.wait_count = 0

            def get_extruder(self):
                return self.extruder

            def wait_moves(self):
                self.wait_count += 1

        class Heaters:
            def __init__(self):
                self.calls = []

            def set_temperature(self, heater, temperature):
                self.calls.append((heater, temperature))

        class MachineState:
            def get_status(self):
                return {"main_state": "FLOW_CALIBRATION"}

        class Printer:
            def __init__(self, heaters):
                self.events = []
                self.heaters = heaters

            def lookup_object(self, name, default=None):
                return {
                    "heaters": self.heaters,
                    "machine_state_manager": MachineState(),
                }.get(name, default)

            def send_event(self, name):
                self.events.append(name)

        class GCode:
            def __init__(self):
                self.commands = []

            def run_script_from_command(self, command):
                self.commands.append(command)

        class Command:
            def __init__(self):
                self.messages = []

            def respond_info(self, message):
                self.messages.append(message)

        calibrator = module.FlowCalibrator.__new__(module.FlowCalibrator)
        calibrator._apa_chain_active = True
        calibrator._toolhead = Toolhead()
        heaters = Heaters()
        calibrator._printer = Printer(heaters)
        calibrator._gcode = GCode()
        final_cleanups = []
        calibrator._end_of_calibration = lambda extruder: final_cleanups.append(extruder)
        command = Command()

        calibrator.cmd_FLOW_CHAIN_CLOSE(command)
        self.assertFalse(calibrator._apa_chain_active)
        self.assertEqual(calibrator._printer.events, ["flow_calibration:end"])
        self.assertEqual(len(final_cleanups), 1)
        self.assertEqual(heaters.calls[-1], ("heater", 0))
        self.assertIn("SET_MAIN_STATE MAIN_STATE=IDLE", calibrator._gcode.commands)

        calibrator.cmd_FLOW_CHAIN_CLOSE(command)
        self.assertEqual(calibrator._printer.events, ["flow_calibration:end"])
        self.assertEqual(len(final_cleanups), 1)

    def test_live_calibration_requires_a_firmware_check_after_ssh_is_configured(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = CalibrationController(
                "http://u1.local",
                "http://spoolman.local",
                root / "sandbox",
                root / "system",
                ssh_target="root@u1.local",
            )
            selection = CalibrationSelection("test", 1, 0, 220)
            with self.assertRaises(GUIError):
                controller.start(selection)
            self.assertEqual(controller.snapshot().state, "blocked")
            self.assertNotIn("G-code", controller.snapshot().message)


if __name__ == "__main__":
    unittest.main()
