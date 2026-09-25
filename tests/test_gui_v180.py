import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation import gui
from u1_filament_automation.gui_b24 import install_b24_patch
from u1_filament_automation.gui_v180 import (
    PreparedSpoolCreationV180,
    inspect_orca_profile,
    install_v180_patch,
)
from u1_filament_automation.models import SpoolmanInventory
from u1_filament_automation.spoolman import NewSpoolRequest, SpoolCreationPlan


EXPECTED = "eSUN PLA ePLA-Lite Rosso Fuoco @Snapmaker U1 (0.4 nozzle)"
LEGACY = "eSUN ePLA-Lite Rosso Fuoco @Snapmaker U1 (0.4 nozzle)"


class _InventoryOnlySpoolman:
    def __init__(self, inventory: SpoolmanInventory):
        self._inventory = inventory
        self.write_calls = 0

    def inventory(self) -> SpoolmanInventory:
        return self._inventory

    def create_vendor(self, payload):
        self.write_calls += 1
        raise AssertionError("preview must not write vendor")

    def create_filament(self, payload):
        self.write_calls += 1
        raise AssertionError("preview must not write filament")

    def create_spool(self, payload):
        self.write_calls += 1
        raise AssertionError("preview must not write spool")


class FinalPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install_b24_patch(gui)
        install_v180_patch(gui)

    @staticmethod
    def _request() -> NewSpoolRequest:
        return NewSpoolRequest(
            vendor="eSUN",
            material="PLA",
            name="ePLA-Lite Rosso Fuoco",
            color_hex="BB2028",
            density=1.23,
            diameter=1.75,
            filament_weight=1000,
            empty_spool_weight=0,
            remaining_weight=1000,
            nozzle_temperature=220,
            bed_temperature=60,
            location="3",
        )

    @staticmethod
    def _inventory() -> SpoolmanInventory:
        return SpoolmanInventory(
            url="http://spoolman.test",
            vendors=[{"id": 7, "name": "eSUN"}],
            filaments=[{
                "id": 15,
                "vendor_id": 7,
                "material": "PLA",
                "name": "ePLA-Lite Rosso Fuoco",
                "color_hex": "BB2028",
            }],
            spools=[{"id": 14, "filament_id": 15}],
        )

    def test_exact_profile_with_dynamic_pa_is_detected_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / f"{EXPECTED}.json"
            original = json.dumps({
                "name": EXPECTED,
                "adaptive_pressure_advance": ["1"],
                "adaptive_pressure_advance_model": ["0.000,0.016934"],
                "pressure_advance": ["0.016934"],
                "custom_value": ["keep"],
            }, indent=2) + "\n"
            path.write_text(original, encoding="utf-8")

            preview = inspect_orca_profile(root, EXPECTED)

            self.assertEqual(preview.status, "exact")
            self.assertEqual(preview.adaptive_pa, "present")
            self.assertEqual(preview.path, path.resolve())
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_unique_legacy_equivalent_is_detected_without_duplicate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / f"{LEGACY}.json"
            original = json.dumps({
                "name": LEGACY,
                "adaptive_pressure_advance": ["1"],
            })
            path.write_text(original, encoding="utf-8")

            preview = inspect_orca_profile(root, EXPECTED)

            self.assertEqual(preview.status, "equivalent")
            self.assertEqual(preview.actual_name, LEGACY)
            self.assertEqual(preview.adaptive_pa, "present")
            self.assertEqual(len(list(root.glob("*.json"))), 1)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_missing_profile_is_reported_as_new(self):
        with tempfile.TemporaryDirectory() as temporary:
            preview = inspect_orca_profile(Path(temporary), EXPECTED)
        self.assertEqual(preview.status, "new")
        self.assertEqual(preview.adaptive_pa, "absent")

    def test_multiple_equivalents_are_ambiguous(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for filename, name in (
                ("legacy-a.json", LEGACY),
                ("legacy-b.json", "eSUN ePLA Lite Rosso Fuoco @Snapmaker U1 (0.4 nozzle)"),
            ):
                (root / filename).write_text(json.dumps({"name": name}), encoding="utf-8")

            preview = inspect_orca_profile(root, EXPECTED)

        self.assertEqual(preview.status, "ambiguous")
        self.assertEqual(preview.equivalent_count, 2)

    def test_controller_blocks_ambiguous_profiles_before_spoolman_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "user" / "default" / "filament"
            system_dir = root / "system" / "Snapmaker" / "filament"
            sandbox_dir = root / "sandbox"
            user_dir.mkdir(parents=True)
            system_dir.mkdir(parents=True)
            sandbox_dir.mkdir()
            (system_dir / "Snapmaker PLA Basic @U1.json").write_text(
                json.dumps({"version": "2.2.53.2"}), encoding="utf-8"
            )
            for filename, name in (
                ("legacy-a.json", LEGACY),
                ("legacy-b.json", "eSUN ePLA Lite Rosso Fuoco @Snapmaker U1 (0.4 nozzle)"),
            ):
                (user_dir / filename).write_text(json.dumps({"name": name}), encoding="utf-8")

            client = _InventoryOnlySpoolman(self._inventory())
            controller = gui.CalibrationController(
                moonraker_url="http://u1.test",
                spoolman_url="http://spoolman.test",
                sandbox_dir=sandbox_dir,
                system_dir=system_dir,
                real_orca_dir=user_dir,
                spoolman_client_factory=lambda: client,
            )

            with self.assertRaises(gui.GUIError) as caught:
                controller.prepare_spool_creation(self._request())

            self.assertIn("creazione bloccata", str(caught.exception))
            self.assertEqual(client.write_calls, 0)
            self.assertIsNone(controller._pending_creation)

    def test_preview_explicitly_preserves_existing_dynamic_pa(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / f"{EXPECTED}.json"
            path.write_text(json.dumps({
                "name": EXPECTED,
                "adaptive_pressure_advance": ["1"],
                "adaptive_pressure_advance_model": ["model-row"],
            }), encoding="utf-8")
            plan = SpoolCreationPlan(
                request=self._request(),
                vendor_id=7,
                filament_id=15,
                profile_name=EXPECTED,
                base_profile="Snapmaker PLA Basic @U1",
            )
            prepared = PreparedSpoolCreationV180(
                ticket="safe-ticket",
                plan=plan,
                profile_preview=inspect_orca_profile(root, EXPECTED),
            )

            page = gui._new_spool_preview(prepared, "csrf-token", language="it")

            self.assertIn("profilo esatto già esistente", page)
            self.assertIn("Adaptive PA: presente", page)
            self.assertIn("non verrà modificato", page)
            self.assertIn("Crea bobina e riutilizza profilo Orca", page)


if __name__ == "__main__":
    unittest.main()
