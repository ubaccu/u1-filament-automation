import unittest

from u1_filament_automation.calibration_batch import (
    CalibrationBatchError,
    CalibrationBatchItem,
    build_calibration_batch,
    run_calibration_batch,
)


class CalibrationBatchTests(unittest.TestCase):
    def item(self, name, slot, temp=220):
        return CalibrationBatchItem(name, slot, temp)

    def test_accepts_one_to_four_unique_items(self):
        for count in range(1, 5):
            plan = build_calibration_batch(
                [self.item(f"Profile {index}", index) for index in range(1, count + 1)]
            )
            self.assertEqual(plan.count, count)

    def test_rejects_empty_queue(self):
        with self.assertRaises(CalibrationBatchError):
            build_calibration_batch([])

    def test_rejects_more_than_four_items(self):
        with self.assertRaises(CalibrationBatchError):
            build_calibration_batch(
                [self.item(f"P{index}", (index % 4) + 1) for index in range(5)]
            )

    def test_rejects_duplicate_slots(self):
        with self.assertRaises(CalibrationBatchError):
            build_calibration_batch([self.item("A", 1), self.item("B", 1)])

    def test_rejects_duplicate_profiles_case_insensitively(self):
        with self.assertRaises(CalibrationBatchError):
            build_calibration_batch([self.item("PLA Beige", 1), self.item("pla beige", 2)])

    def test_rejects_invalid_slot(self):
        with self.assertRaises(CalibrationBatchError):
            build_calibration_batch([self.item("A", 0)])

    def test_rejects_invalid_temperature(self):
        with self.assertRaises(CalibrationBatchError):
            build_calibration_batch([self.item("A", 1, 169)])

    def test_runs_strictly_in_queue_order(self):
        plan = build_calibration_batch([
            self.item("A", 1),
            self.item("B", 2),
            self.item("C", 3),
        ])
        seen = []
        result = run_calibration_batch(plan, lambda item: seen.append(item.profile_name))
        self.assertTrue(result.ok)
        self.assertEqual(seen, ["A", "B", "C"])
        self.assertEqual(len(result.completed), 3)

    def test_stops_at_first_failure(self):
        plan = build_calibration_batch([
            self.item("A", 1),
            self.item("B", 2),
            self.item("C", 3),
        ])
        seen = []

        def runner(item):
            seen.append(item.profile_name)
            if item.profile_name == "B":
                raise RuntimeError("simulated failure")

        result = run_calibration_batch(plan, runner)
        self.assertFalse(result.ok)
        self.assertEqual(seen, ["A", "B"])
        self.assertEqual([item.profile_name for item in result.completed], ["A"])
        self.assertEqual(result.failed_item.profile_name, "B")
        self.assertIn("simulated failure", result.error)

    def test_plan_normalizes_profile_whitespace(self):
        plan = build_calibration_batch([self.item("  PLA Beige  ", 1)])
        self.assertEqual(plan.items[0].profile_name, "PLA Beige")


if __name__ == "__main__":
    unittest.main()
