import hashlib
import subprocess
import unittest
from pathlib import PurePosixPath
from unittest.mock import patch

import u1_filament_automation.firmware_compatibility as fc
from u1_filament_automation.printer import SSHPrinterTarget


class Target:
    def __init__(self, files):
        self.files = dict(files)

    def read_path_bytes(self, path: PurePosixPath) -> bytes:
        try:
            return self.files[path]
        except KeyError as exc:
            raise FileNotFoundError(str(path)) from exc


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PAXX209CompatibilityTests(unittest.TestCase):
    def _files(self, *, print_task=b"paxx-12-24-print-task", flow=b"stock-205-flow", macro=None):
        filament = b"stock-205-filament"
        machine = b"stock-205-machine"
        files = {
            fc.VERSION_PATH: b"2.0.0\n",
            fc.FULLVERSION_PATH: b"2.0.0-paxx12-24\n",
            fc.BUILD_VERSION_PATH: b"2.0.0-paxx12-24-test-build\n",
            fc.EXTRAS / "flow_calibrator.py": flow,
            fc.EXTRAS / "filament_parameters.py": filament,
            fc.EXTRAS / "machine_state_manager.py": machine,
            fc.EXTRAS / "print_task_config.py": print_task,
        }
        if macro is not None:
            files[fc.MACRO_PATH] = macro
        deps = {
            "filament_parameters.py": sha(filament),
            "machine_state_manager.py": sha(machine),
            "print_task_config.py": sha(b"paxx-12-24-print-task"),
        }
        return files, deps

    def test_exact_paxx_12_24_stock_calibrator_is_installable(self):
        files, deps = self._files()
        with (
            patch.object(fc, "PAXX_200_V24_DEPENDENCIES", deps),
            patch.object(fc, "STOCK_205", sha(b"stock-205-flow")),
        ):
            report = fc.inspect_firmware(Target(files))

        self.assertEqual(report.state, "paxx-200-v24-compatible")
        self.assertTrue(report.live_install_allowed)
        self.assertFalse(report.live_calibration_allowed)

    def test_paxx_12_24_unknown_print_task_hash_stays_blocked(self):
        files, deps = self._files(print_task=b"unexpected-print-task")
        with (
            patch.object(fc, "PAXX_200_V24_DEPENDENCIES", deps),
            patch.object(fc, "STOCK_205", sha(b"stock-205-flow")),
        ):
            report = fc.inspect_firmware(Target(files))

        self.assertEqual(report.state, "unknown-blocked")
        self.assertFalse(report.live_install_allowed)
        self.assertIn("print_task_config.py", report.message)

    def test_paxx_12_24_installed_autopa_can_calibrate_with_valid_macro(self):
        macro = b"validated-205-macro"
        files, deps = self._files(flow=b"autopa-205-flow", macro=macro)
        with (
            patch.object(fc, "PAXX_200_V24_DEPENDENCIES", deps),
            patch.object(fc, "CANDIDATE_205", sha(b"autopa-205-flow")),
            patch.object(fc, "TESTED_205", sha(b"autopa-205-flow")),
            patch.object(fc, "MACRO_205_SHA256", sha(macro)),
            patch.object(fc, "MACRO_205_TESTED_SHA256", sha(macro)),
        ):
            report = fc.inspect_firmware(Target(files))

        self.assertEqual(report.state, "paxx-200-v24-autopa-installed")
        self.assertTrue(report.live_install_allowed)
        self.assertTrue(report.live_calibration_allowed)


class SSH209Tests(unittest.TestCase):
    def test_command_accepts_only_new_host_keys(self):
        target = SSHPrinterTarget("root@192.168.1.14")
        command = target._command()

        self.assertIn("StrictHostKeyChecking=accept-new", command)
        self.assertNotIn("StrictHostKeyChecking=no", command)

    def test_total_ssh_timeout_has_windows_askpass_margin(self):
        target = SSHPrinterTarget("root@192.168.1.14", timeout=5.0)
        completed = subprocess.CompletedProcess(
            args=["ssh"], returncode=0, stdout='{"ok": true}\n', stderr=""
        )
        with (
            patch("u1_filament_automation.printer.shutil.which", return_value="ssh"),
            patch("u1_filament_automation.printer.subprocess.run", return_value=completed) as run,
        ):
            target._run_script("print('ok')")

        self.assertEqual(run.call_args.kwargs["timeout"], 10.0)


if __name__ == "__main__":
    unittest.main()
