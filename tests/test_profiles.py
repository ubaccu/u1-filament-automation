import unittest

from u1_filament_automation.models import SpoolmanInventory
from u1_filament_automation.profiles import build_previews


class ProfilePreviewTests(unittest.TestCase):
    def test_same_filament_spools_share_one_profile(self):
        inventory = SpoolmanInventory(
            url="http://127.0.0.1:7912",
            vendors=[{"id": 1, "name": "Anycubic"}],
            filaments=[
                {
                    "id": 2,
                    "vendor_id": 1,
                    "material": "PETG",
                    "name": "Translucent",
                }
            ],
            spools=[
                {"id": 10, "filament_id": 2},
                {"id": 11, "filament_id": 2},
            ],
        )
        previews = build_previews(inventory, nozzle=0.4)
        self.assertEqual(len(previews), 1)
        self.assertEqual(
            previews[0].nozzle_profile,
            "Anycubic PETG Translucent @Snapmaker U1 (0.4 nozzle)",
        )
        self.assertEqual(previews[0].spool_ids, (10, 11))

    def test_removes_repeated_vendor_and_material(self):
        inventory = SpoolmanInventory(
            url="http://127.0.0.1:7912",
            vendors=[
                {"id": 1, "name": "Deeplee"},
                {"id": 2, "name": "R3d"},
                {"id": 3, "name": "Snapmaker"},
            ],
            filaments=[
                {"id": 1, "vendor_id": 1, "material": "PLA", "name": "DEEPLEE PLA RAPID MARRONE"},
                {"id": 2, "vendor_id": 2, "material": "PLA", "name": "R3D PLA RAPID GRIGIO"},
                {"id": 3, "vendor_id": 3, "material": "PLA", "name": "SnapSpeed PLA - RED"},
            ],
            spools=[
                {"id": 1, "filament_id": 1},
                {"id": 2, "filament_id": 2},
                {"id": 3, "filament_id": 3},
            ],
        )
        names = [item.nozzle_profile for item in build_previews(inventory)]
        self.assertEqual(
            names,
            [
                "Deeplee PLA Rapid Marrone @Snapmaker U1 (0.4 nozzle)",
                "R3d PLA Rapid Grigio @Snapmaker U1 (0.4 nozzle)",
                "Snapmaker PLA SnapSpeed Red @Snapmaker U1 (0.4 nozzle)",
            ],
        )


if __name__ == "__main__":
    unittest.main()
