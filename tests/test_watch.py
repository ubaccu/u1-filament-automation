import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.models import SpoolmanInventory
from u1_filament_automation.sync import SyncAction, SyncReport
from u1_filament_automation.watch import (
    WatchStateError,
    default_watch_state_path,
    load_managed_profiles,
    managed_profiles_from_report,
    save_managed_profiles,
)


class WatchStateTests(unittest.TestCase):
    def test_state_round_trip_is_bound_to_orca_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "orca" / "filament"
            state = root / "watch-state.json"
            save_managed_profiles(state, target, {"Profilo Uno", "PROFILO DUE"})
            self.assertEqual(
                load_managed_profiles(state, target),
                {"profilo uno", "profilo due"},
            )
            with self.assertRaises(WatchStateError):
                load_managed_profiles(state, root / "altra-cartella")

    def test_corrupt_state_blocks_instead_of_recreating_profiles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state = root / "watch-state.json"
            state.write_text("non-json", encoding="utf-8")
            with self.assertRaises(WatchStateError):
                load_managed_profiles(state, root / "filament")

    def test_report_marks_only_created_and_existing_as_managed(self):
        report = SyncReport(
            user_dir=Path("/tmp/user"),
            system_dir=Path("/tmp/system"),
            apply=True,
            actions=(
                SyncAction("created", "Creato", "Base", "FFFFFF", (1,)),
                SyncAction("existing", "Esiste", "Base", "FFFFFF", (2,)),
                SyncAction("skipped", "Saltato", None, "FFFFFF", (3,)),
            ),
        )
        self.assertEqual(
            managed_profiles_from_report(report),
            {"creato", "esiste"},
        )

    def test_sandbox_state_stays_inside_sandbox(self):
        sandbox = Path("/tmp/u1fa-sandbox")
        self.assertEqual(
            default_watch_state_path(sandbox, sandbox=True),
            sandbox / ".u1fa" / "watch-state.json",
        )


if __name__ == "__main__":
    unittest.main()
