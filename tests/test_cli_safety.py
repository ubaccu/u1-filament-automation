import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from u1_filament_automation.cli import main
from u1_filament_automation.models import OrcaInstallation, SpoolmanInventory


class CliSafetyTests(unittest.TestCase):
    def _installation(self, path: Path) -> OrcaInstallation:
        return OrcaInstallation(path=path, profile_count=0, source="test")

    def _inventory(self) -> SpoolmanInventory:
        return SpoolmanInventory(
            url="http://127.0.0.1:7912",
            vendors=[{"id": 1, "name": "Deeplee"}],
            filaments=[
                {
                    "id": 2,
                    "vendor_id": 1,
                    "material": "PLA",
                    "name": "Rapid Marrone",
                    "color_hex": "9C7860",
                }
            ],
            spools=[{"id": 4, "filament_id": 2}],
        )

    def _inventory_with_second_filament(self) -> SpoolmanInventory:
        inventory = self._inventory()
        return SpoolmanInventory(
            url=inventory.url,
            vendors=inventory.vendors,
            filaments=[
                *inventory.filaments,
                {
                    "id": 3,
                    "vendor_id": 1,
                    "material": "PLA",
                    "name": "Rapid Beige",
                    "color_hex": "D9C3A5",
                },
            ],
            spools=[*inventory.spools, {"id": 5, "filament_id": 3}],
        )

    def _r3d_inventory(self) -> SpoolmanInventory:
        return SpoolmanInventory(
            url="http://127.0.0.1:7912",
            vendors=[{"id": 1, "name": "R3d"}],
            filaments=[
                {
                    "id": 8,
                    "vendor_id": 1,
                    "material": "PLA",
                    "name": "R3D PLA RAPID GRIGIO",
                    "color_hex": "777777",
                }
            ],
            spools=[{"id": 8, "filament_id": 8}],
        )

    def test_gui_can_start_without_a_hard_coded_printer_ip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "connections.json"
            with patch("u1_filament_automation.cli.run_gui", return_value=0) as run:
                result = main([
                    "gui",
                    "--sandbox-dir",
                    str(root / "sandbox"),
                    "--config-file",
                    str(config),
                    "--no-browser",
                ])
        self.assertEqual(result, 0)
        self.assertEqual(run.call_args.kwargs["moonraker_url"], "")
        self.assertEqual(
            run.call_args.kwargs["spoolman_url"],
            "http://127.0.0.1:7912",
        )
        self.assertIsNone(run.call_args.kwargs["ssh_target"])

    def test_apply_without_second_confirmation_is_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_dir = Path(temporary) / "user" / "default" / "filament"
            real_dir.mkdir(parents=True)
            output = io.StringIO()
            with patch(
                "u1_filament_automation.cli.discover_orca",
                return_value=[self._installation(real_dir)],
            ), redirect_stdout(output):
                result = main(["sync", "--apply"])

            self.assertEqual(result, 2)
            self.assertIn("[BLOCCATO]", output.getvalue())
            self.assertEqual(list(real_dir.iterdir()), [])

    def test_sandbox_cannot_overlap_real_orca(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_dir = Path(temporary) / "user" / "default" / "filament"
            real_dir.mkdir(parents=True)
            with patch(
                "u1_filament_automation.cli.discover_orca",
                return_value=[self._installation(real_dir)],
            ), redirect_stdout(io.StringIO()):
                result = main(
                    ["sync", "--apply", "--sandbox-dir", str(real_dir)]
                )

            self.assertEqual(result, 2)
            self.assertEqual(list(real_dir.iterdir()), [])

    def test_sandbox_writes_only_to_separate_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            sandbox_dir = root / "safe-test-output"
            real_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            (system_dir / "Snapmaker PLA SnapSpeed @U1.json").write_text(
                json.dumps({"version": "2.2.53.2"}), encoding="utf-8"
            )

            with patch(
                "u1_filament_automation.cli.discover_orca",
                return_value=[self._installation(real_dir)],
            ), patch(
                "u1_filament_automation.cli.first_working_inventory",
                return_value=(self._inventory(), []),
            ), redirect_stdout(io.StringIO()):
                result = main(
                    ["sync", "--apply", "--sandbox-dir", str(sandbox_dir)]
                )

            self.assertEqual(result, 0)
            self.assertEqual(list(real_dir.iterdir()), [])
            self.assertEqual(len(list(sandbox_dir.glob("*.json"))), 1)
            self.assertEqual(len(list(sandbox_dir.glob("*.info"))), 1)

    def test_watch_creates_only_new_profiles_in_sandbox(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            sandbox_dir = root / "watch-sandbox"
            real_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            (system_dir / "Snapmaker PLA SnapSpeed @U1.json").write_text(
                json.dumps({"version": "2.2.53.2"}), encoding="utf-8"
            )

            with patch(
                "u1_filament_automation.cli.discover_orca",
                return_value=[self._installation(real_dir)],
            ), patch(
                "u1_filament_automation.cli.first_working_inventory",
                side_effect=[
                    (self._inventory(), []),
                    (self._inventory_with_second_filament(), []),
                ],
            ), patch(
                "u1_filament_automation.cli.time.sleep"
            ) as sleep, redirect_stdout(io.StringIO()):
                result = main(
                    [
                        "watch",
                        "--apply",
                        "--sandbox-dir",
                        str(sandbox_dir),
                        "--cycles",
                        "2",
                        "--interval",
                        "5",
                    ]
                )

            self.assertEqual(result, 0)
            self.assertEqual(list(real_dir.iterdir()), [])
            self.assertEqual(len(list(sandbox_dir.glob("*.json"))), 2)
            self.assertEqual(len(list(sandbox_dir.glob("*.info"))), 2)
            sleep.assert_called_once_with(5.0)

    def test_watch_real_write_without_confirmation_is_blocked_before_services(self):
        with patch(
            "u1_filament_automation.cli.discover_orca"
        ) as discover, redirect_stdout(io.StringIO()):
            result = main(["watch", "--apply"])

        self.assertEqual(result, 2)
        discover.assert_not_called()

    def test_pa_profile_real_write_without_confirmation_is_blocked_first(self):
        with patch(
            "u1_filament_automation.cli.discover_orca"
        ) as discover, patch(
            "u1_filament_automation.cli.first_working_inventory"
        ) as inventory, redirect_stdout(io.StringIO()):
            result = main(["pa-profile", "saved-log.txt", "--apply"])

        self.assertEqual(result, 2)
        discover.assert_not_called()
        inventory.assert_not_called()

    def test_pa_auto_real_write_without_confirmation_connects_to_nothing(self):
        with patch(
            "u1_filament_automation.cli.discover_orca"
        ) as discover, patch(
            "u1_filament_automation.cli.MoonrakerClient"
        ) as moonraker, redirect_stdout(io.StringIO()):
            result = main(
                [
                    "pa-auto",
                    "--moonraker-url",
                    "http://192.168.1.51",
                    "--apply",
                ]
            )

        self.assertEqual(result, 2)
        discover.assert_not_called()
        moonraker.assert_not_called()

    def test_pa_latest_real_write_without_confirmation_connects_to_nothing(self):
        with patch(
            "u1_filament_automation.cli.discover_orca"
        ) as discover, patch(
            "u1_filament_automation.cli.MoonrakerClient"
        ) as moonraker, redirect_stdout(io.StringIO()):
            result = main(
                [
                    "pa-latest",
                    "--moonraker-url",
                    "http://192.168.1.51",
                    "--apply",
                ]
            )

        self.assertEqual(result, 2)
        discover.assert_not_called()
        moonraker.assert_not_called()

    def test_pa_profile_updates_only_existing_sandbox_profile(self):
        profile_name = "R3d PLA RAPID GRIGIO @Snapmaker U1 (0.4 nozzle)"
        logfile = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "apa_chain_v6_real_log.txt"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_dir = root / "user" / "default" / "filament"
            sandbox_dir = root / "sandbox"
            real_dir.mkdir(parents=True)
            sandbox_dir.mkdir()
            profile_path = sandbox_dir / f"{profile_name}.json"
            profile_path.write_text(
                json.dumps(
                    {
                        "name": profile_name,
                        "inherits": "Snapmaker PLA SnapSpeed @U1",
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()
            with patch(
                "u1_filament_automation.cli.discover_orca",
                return_value=[self._installation(real_dir)],
            ), patch(
                "u1_filament_automation.cli.first_working_inventory",
                return_value=(self._r3d_inventory(), []),
            ), redirect_stdout(output):
                result = main(
                    [
                        "pa-profile",
                        str(logfile),
                        "--apply",
                        "--sandbox-dir",
                        str(sandbox_dir),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertEqual(list(real_dir.iterdir()), [])
            payload = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["pressure_advance"], ["0.010364"])
            self.assertEqual(payload["adaptive_pressure_advance"], ["1"])
            self.assertIn("profili reali intatti", output.getvalue())
            self.assertEqual(
                len(list((sandbox_dir / ".u1fa" / "backups").iterdir())),
                1,
            )

    def test_pa_auto_ignores_cached_suite_and_applies_only_new_suite(self):
        profile_name = "R3d PLA RAPID GRIGIO @Snapmaker U1 (0.4 nozzle)"
        log = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "apa_chain_v6_real_log.txt"
        ).read_text(encoding="utf-8")

        def store(text, start):
            return [
                {
                    "message": line,
                    "time": start + index / 1000,
                    "type": "response",
                }
                for index, line in enumerate(text.splitlines())
            ]

        cached = store(log, 1)
        new_suite = store(log, 100)
        client = unittest.mock.Mock()
        client.gcode_store.side_effect = [cached, [*cached, *new_suite]]

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_dir = root / "user" / "default" / "filament"
            sandbox_dir = root / "sandbox"
            real_dir.mkdir(parents=True)
            sandbox_dir.mkdir()
            profile_path = sandbox_dir / f"{profile_name}.json"
            profile_path.write_text(
                json.dumps({"name": profile_name, "marker": "preserve"}),
                encoding="utf-8",
            )
            output = io.StringIO()
            with patch(
                "u1_filament_automation.cli.discover_orca",
                return_value=[self._installation(real_dir)],
            ), patch(
                "u1_filament_automation.cli.MoonrakerClient",
                return_value=client,
            ), patch(
                "u1_filament_automation.cli.candidates_from_moonraker",
                return_value=[],
            ), patch(
                "u1_filament_automation.cli.first_working_inventory",
                return_value=(self._r3d_inventory(), []),
            ), patch(
                "u1_filament_automation.cli.time.sleep"
            ) as sleep, redirect_stdout(output):
                result = main(
                    [
                        "pa-auto",
                        "--moonraker-url",
                        "http://u1.local",
                        "--apply",
                        "--sandbox-dir",
                        str(sandbox_dir),
                        "--cycles",
                        "1",
                        "--interval",
                        "0.5",
                    ]
                )

            self.assertEqual(result, 0)
            sleep.assert_called_once_with(0.5)
            self.assertEqual(list(real_dir.iterdir()), [])
            payload = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["marker"], "preserve")
            self.assertEqual(payload["pressure_advance"], ["0.010364"])
            self.assertIn("Nuova suite ULTRA v6 completa", output.getvalue())
            self.assertEqual(
                len(list((sandbox_dir / ".u1fa" / "backups").iterdir())),
                1,
            )

    def test_pa_auto_does_not_apply_a_suite_already_in_cache(self):
        profile_name = "R3d PLA RAPID GRIGIO @Snapmaker U1 (0.4 nozzle)"
        log = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "apa_chain_v6_real_log.txt"
        ).read_text(encoding="utf-8")
        cached = [
            {
                "message": line,
                "time": index + 1,
                "type": "response",
            }
            for index, line in enumerate(log.splitlines())
        ]
        client = unittest.mock.Mock()
        client.gcode_store.side_effect = [cached, cached]

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_dir = root / "user" / "default" / "filament"
            sandbox_dir = root / "sandbox"
            real_dir.mkdir(parents=True)
            sandbox_dir.mkdir()
            profile_path = sandbox_dir / f"{profile_name}.json"
            original = json.dumps({"name": profile_name})
            profile_path.write_text(original, encoding="utf-8")
            output = io.StringIO()
            with patch(
                "u1_filament_automation.cli.discover_orca",
                return_value=[self._installation(real_dir)],
            ), patch(
                "u1_filament_automation.cli.MoonrakerClient",
                return_value=client,
            ), patch(
                "u1_filament_automation.cli.time.sleep"
            ), redirect_stdout(output):
                result = main(
                    [
                        "pa-auto",
                        "--moonraker-url",
                        "http://u1.local",
                        "--apply",
                        "--sandbox-dir",
                        str(sandbox_dir),
                        "--cycles",
                        "1",
                        "--interval",
                        "0.5",
                    ]
                )

            self.assertEqual(result, 0)
            self.assertEqual(profile_path.read_text(encoding="utf-8"), original)
            self.assertFalse((sandbox_dir / ".u1fa" / "backups").exists())
            self.assertIn("Nessuna nuova suite completa", output.getvalue())

    def test_pa_latest_recovers_cached_suite_to_explicit_sandbox_profile(self):
        profile_name = "Deeplee PLA PRO RAPID BLUE @Snapmaker U1 (0.4 nozzle)"
        log = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "apa_chain_v6_real_log.txt"
        ).read_text(encoding="utf-8")
        cached = [
            {
                "message": line,
                "time": 1000 + index,
                "type": "response",
            }
            for index, line in enumerate(log.splitlines())
        ]
        client = unittest.mock.Mock()
        client.gcode_store.return_value = cached
        completed_at = max(item["time"] for item in cached)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_dir = root / "user" / "default" / "filament"
            sandbox_dir = root / "sandbox"
            real_dir.mkdir(parents=True)
            sandbox_dir.mkdir()
            profile_path = sandbox_dir / f"{profile_name}.json"
            profile_path.write_text(
                json.dumps({"name": profile_name, "marker": "preserve"}),
                encoding="utf-8",
            )
            output = io.StringIO()
            with patch(
                "u1_filament_automation.cli.discover_orca",
                return_value=[self._installation(real_dir)],
            ), patch(
                "u1_filament_automation.cli.MoonrakerClient",
                return_value=client,
            ), patch(
                "u1_filament_automation.cli.time.time",
                return_value=completed_at + 60,
            ), redirect_stdout(output):
                result = main(
                    [
                        "pa-latest",
                        "--moonraker-url",
                        "http://u1.local",
                        "--profile-name",
                        profile_name,
                        "--apply",
                        "--sandbox-dir",
                        str(sandbox_dir),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertEqual(list(real_dir.iterdir()), [])
            payload = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["marker"], "preserve")
            self.assertEqual(payload["pressure_advance"], ["0.010364"])
            self.assertIn("recupero ultima suite PA", output.getvalue())
            self.assertEqual(
                len(list((sandbox_dir / ".u1fa" / "backups").iterdir())),
                1,
            )


if __name__ == "__main__":
    unittest.main()
