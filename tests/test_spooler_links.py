import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock

from u1_filament_automation.gui import CalibrationController
from u1_filament_automation.models import SpoolmanInventory
from u1_filament_automation.pa_profile import profile_candidates
from u1_filament_automation.spoolman import SpoolmanClient
from u1_filament_automation.standard_orca import set_standard_orca_mirror_enabled, set_spooler_linking, spooler_linking_enabled


class SpoolerLinkTests(TestCase):
    def test_bulk_link_preserves_calibration_and_retries_without_writes(self):
        filament = {"id": 5, "vendor": {"name": "Deeplee"}, "material": "PLA", "name": "Rapid rosso"}
        inventory = SpoolmanInventory("http://localhost:7912", filaments=[filament],
                                      spools=[{"id": 19, "filament": filament}])
        name = profile_candidates(inventory)[0].profile_name
        with TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "Snap", Path(tmp) / "Orca"
            source.mkdir()
            target.mkdir()
            controller = Mock(real_orca_dir=source, standard_orca_dir=target)
            client = SpoolmanClient(inventory.url)
            def request(method, endpoint, payload=None):
                if endpoint == "info":
                    return {"version": "0.22.0"}
                if endpoint == "field/filament":
                    return [{"key": "orca_filament_preset", "field_type": "text"}]
                self.assertEqual(endpoint, "filament/5")
                if method == "PATCH":
                    filament["extra"] = payload["extra"]
                return filament
            client._request = Mock(side_effect=request)
            data = {"name": name, "filament_settings_id": [name], "from": "User",
                    "adaptive_pressure_advance": ["1"], "adaptive_pressure_advance_model": ["sample curve"]}
            (source / "calibrated.json").write_text(json.dumps(data))
            CalibrationController.link_spooler_profiles(controller, client, inventory)
            self.assertEqual(json.loads(filament["extra"]["orca_filament_preset"]), name)
            self.assertEqual(json.loads(next(target.glob("*.json")).read_text()), data)
            client._request.reset_mock()
            CalibrationController.link_spooler_profiles(controller, client, inventory)
            client._request.assert_not_called()
            set_standard_orca_mirror_enabled(target, True)
            set_spooler_linking(target, inventory.url, True)
            self.assertTrue(spooler_linking_enabled(target, inventory.url))
            self.assertFalse(spooler_linking_enabled(target, "http://another-server"))
            set_spooler_linking(target, inventory.url, False)
            self.assertFalse(spooler_linking_enabled(target, inventory.url))

    def test_mismatched_profile_does_not_block_other_vendor_capitalization(self):
        from types import SimpleNamespace
        from threading import Lock
        from u1_filament_automation.sync import safe_filename
        with TemporaryDirectory() as tmp:
            source, target = Path(tmp) / "source", Path(tmp) / "target"
            source.mkdir()
            target.mkdir()
            names = ["Different", "Deeplee Rosso"]
            for expected, actual in zip(names, ["Another material", "DEEPLEE Rosso"]):
                (source / (safe_filename(expected) + ".json")).write_text(json.dumps({
                    "name": actual, "filament_settings_id": [actual], "from": "User"
                }))
            controller = Mock(real_orca_dir=source, standard_orca_dir=target, _lock=Lock(),
                              _profiles=[SimpleNamespace(profile_name=n) for n in names])
            plans = CalibrationController.standard_orca_preview(controller)
            self.assertEqual([p.action for p in plans], ["blocked", "create"])
            controller.standard_orca_preview.return_value = plans
            controller._job.state = "idle"
            CalibrationController.enable_standard_orca_mirror(controller)
            self.assertEqual(json.loads(next(target.glob("*.json")).read_text())["name"], "DEEPLEE Rosso")

    def test_inherited_calibration_is_portable_and_source_untouched(self):
        from u1_filament_automation.standard_orca import apply_standard_orca_mirror, plan_standard_orca_mirror
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "user/default/filament"
            system = root / "system/Snapmaker/filament"
            dst = root / "standard"
            for folder in (src, system, dst):
                folder.mkdir(parents=True)
            (system / "Common.json").write_text('{"pressure_advance":["0.02"]}')
            (system / "Rapid.json").write_text('{"inherits":"Common","filament_flow_ratio":["1"]}')
            child = {"name":"Rosso", "filament_settings_id":["Rosso"], "inherits":"Rapid",
                     "adaptive_pressure_advance":["1"], "adaptive_pressure_advance_model":["a\nb"],
                     "filament_flow_ratio":["0.98"]}
            path = src / "Rosso.json"
            path.write_text(json.dumps(child))
            plan = plan_standard_orca_mirror(src,dst,"Rosso")
            apply_standard_orca_mirror(plan)
            effective = json.loads(plan.target_path.read_text())
            self.assertNotIn("inherits",effective)
            self.assertEqual(effective["pressure_advance"],["0.02"])
            for key in ("filament_flow_ratio","adaptive_pressure_advance_model","adaptive_pressure_advance"):
                self.assertEqual(effective[key],child[key])
            self.assertEqual(json.loads(path.read_text()), child)

    def test_legacy_vendor_position_preserves_blue_calibration(self):
        from u1_filament_automation.standard_orca import (
            StandardOrcaMirrorError, apply_standard_orca_mirror, plan_standard_orca_mirror,
        )
        from u1_filament_automation.sync import safe_filename
        suffix = " @Snapmaker U1 (0.4 nozzle)"
        expected = "Deeplee PLA RAPID PRO RAPID BLU" + suffix
        actual = "PLA RAPID DEEPLEE PRO RAPID BLU" + suffix
        with TemporaryDirectory() as tmp:
            src, dst = Path(tmp) / "snap", Path(tmp) / "orca"
            src.mkdir()
            dst.mkdir()
            path = src / (safe_filename(expected) + ".json")
            data = {"name": actual, "filament_settings_id": [actual],
                    "adaptive_pressure_advance_model": ["sample curve"]}
            path.write_text(json.dumps(data))
            plan = plan_standard_orca_mirror(src, dst, expected)
            apply_standard_orca_mirror(plan)
            mirrored = json.loads(plan.target_path.read_text())
            self.assertEqual(mirrored, dict(data, name=expected, filament_settings_id=[expected]))
            self.assertEqual(json.loads(path.read_text()), data)
            for other in (actual.replace("BLU", "NERO"), actual.replace("0.4", "0.6")):
                path.write_text(json.dumps(dict(data, name=other, filament_settings_id=[other])))
                with self.assertRaises(StandardOrcaMirrorError):
                    plan_standard_orca_mirror(src, dst, expected)
