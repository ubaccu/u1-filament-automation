import hashlib
import unittest
from pathlib import PurePosixPath
from unittest.mock import patch

import u1_filament_automation.firmware_compatibility as fc


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


class PAXX184HotfixTests(unittest.TestCase):
    def _files(self, build: str):
        flow = b"legacy-stock-fixture\n"
        filament = b"filament-parameters-fixture\n"
        machine = b"machine-state-fixture\n"
        print_task = b"paxx-print-task-fixture\n"
        files = {
            fc.VERSION_PATH: b"1.5.2\n",
            fc.FULLVERSION_PATH: b"1.5.2\n",
            fc.BUILD_VERSION_PATH: (build + "\n").encode(),
            fc.EXTRAS / "flow_calibrator.py": flow,
            fc.EXTRAS / "filament_parameters.py": filament,
            fc.EXTRAS / "machine_state_manager.py": machine,
            fc.EXTRAS / "print_task_config.py": print_task,
        }
        return files, flow, filament, machine, print_task

    def test_exact_paxx_build_is_installable_before_macro_exists(self):
        self.assertEqual(fc.PAXX_152_V21_BUILD, "1.5.2-paxx12-21-2a88932")
        files, flow, filament, machine, print_task = self._files(fc.PAXX_152_V21_BUILD)
        deps = {
            "filament_parameters.py": sha(filament),
            "machine_state_manager.py": sha(machine),
            # Keep legacy baseline deliberately different from the PAXX file.
            "print_task_config.py": sha(b"legacy-print-task"),
        }
        with (
            patch.object(fc, "LEGACY_STOCK", sha(flow)),
            patch.object(fc, "DEPENDENCIES_152", deps),
            patch.object(fc, "PAXX_152_V21_PRINT_TASK_CONFIG", sha(print_task)),
        ):
            report = fc.inspect_firmware(Target(files))

        self.assertEqual(report.state, "paxx-152-v21-compatible")
        self.assertTrue(report.live_install_allowed)
        self.assertFalse(report.live_calibration_allowed)
        self.assertNotIn(str(fc.MACRO_PATH), report.missing)

    def test_old_truncated_build_id_is_blocked(self):
        files, flow, filament, machine, print_task = self._files("1.5.2-paxx12-21-2a8893")
        deps = {
            "filament_parameters.py": sha(filament),
            "machine_state_manager.py": sha(machine),
            "print_task_config.py": sha(b"legacy-print-task"),
        }
        with (
            patch.object(fc, "LEGACY_STOCK", sha(flow)),
            patch.object(fc, "DEPENDENCIES_152", deps),
            patch.object(fc, "PAXX_152_V21_PRINT_TASK_CONFIG", sha(print_task)),
        ):
            report = fc.inspect_firmware(Target(files))

        self.assertEqual(report.state, "unknown-blocked")
        self.assertFalse(report.live_install_allowed)
        self.assertIn("2a8893", report.message)
        self.assertIn("2a88932", report.message)
        self.assertNotIn(str(fc.MACRO_PATH), report.missing)


if __name__ == "__main__":
    unittest.main()
