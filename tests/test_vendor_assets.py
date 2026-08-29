import hashlib
import py_compile
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "apa-chain-v6-safe"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class VendorAssetTests(unittest.TestCase):
    def test_recovered_v6_files_match_saved_hashes_and_compile(self):
        self.assertEqual(
            sha256(VENDOR / "flow_calibrator_U1_ORIGINALE_BACKUP.py"),
            "dcbc26d5c726eb464b8e2a31d2856a816f3170bbda1ed5facb57fb19a816e894",
        )
        self.assertEqual(
            sha256(VENDOR / "flow_calibrator.py"),
            "74ff744304657547e513fe74c3d42beb55f35eebd4d8f3e0749f0c7febc089ce",
        )
        self.assertEqual(
            sha256(VENDOR / "adaptive_pa_macro.cfg"),
            "db181aa5ee12b93886230a6b71cfd105c92a56cf4651e5e5dca7788aac7daeb4",
        )
        self.assertEqual(
            sha256(VENDOR / "flow_calibrator_v6_changes.diff"),
            "cf7141fa4bd7ec2c29a107c3192d9c8d65dcf5b0d309e81eaf46e857fe401975",
        )
        py_compile.compile(str(VENDOR / "flow_calibrator.py"), doraise=True)

    def test_saved_diff_recreates_exact_v6_file(self):
        patch_command = shutil.which("patch")
        if patch_command is None:
            self.skipTest("comando patch non disponibile")

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "flow_calibrator.py"
            shutil.copyfile(
                VENDOR / "flow_calibrator_U1_ORIGINALE_BACKUP.py",
                target,
            )
            diff = VENDOR / "flow_calibrator_v6_changes.diff"
            subprocess.run(
                [patch_command, "--silent", str(target), str(diff)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                sha256(target),
                "74ff744304657547e513fe74c3d42beb55f35eebd4d8f3e0749f0c7febc089ce",
            )


if __name__ == "__main__":
    unittest.main()
