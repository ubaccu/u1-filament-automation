import unittest
from pathlib import Path

from u1_filament_automation.pa_capture import (
    PACaptureError,
    GCodeStoreEntry,
    latest_cached_suite,
    new_gcode_entries,
    parse_gcode_store,
    response_text,
)


def entry(message: str, timestamp: float, kind: str = "response"):
    return GCodeStoreEntry(message=message, time=timestamp, type=kind)


class PACaptureTests(unittest.TestCase):
    def test_parses_official_gcode_store_shape(self):
        parsed = parse_gcode_store(
            [
                {"message": "APA_COIL_RUN_ULTRA", "time": 1, "type": "command"},
                {
                    "message": "// Got pressure advance: 0.02",
                    "time": 2.5,
                    "type": "response",
                },
            ]
        )
        self.assertEqual(parsed[0], entry("APA_COIL_RUN_ULTRA", 1, "command"))
        self.assertEqual(parsed[1].time, 2.5)

    def test_detects_only_appended_entries(self):
        previous = (entry("old-1", 1), entry("old-2", 2))
        current = (*previous, entry("new", 3))
        self.assertEqual(new_gcode_entries(previous, current), (entry("new", 3),))

    def test_detects_fifo_shift_without_replaying_old_entries(self):
        previous = (
            entry("old-1", 1),
            entry("old-2", 2),
            entry("old-3", 3),
        )
        current = (
            entry("old-3", 3),
            entry("new-1", 4),
            entry("new-2", 5),
        )
        self.assertEqual(
            new_gcode_entries(previous, current),
            (entry("new-1", 4), entry("new-2", 5)),
        )

    def test_discontinuity_blocks_instead_of_replaying_cache(self):
        with self.assertRaises(PACaptureError):
            new_gcode_entries(
                (entry("old", 1),),
                (entry("unrelated", 99),),
            )

    def test_response_text_excludes_commands(self):
        self.assertEqual(
            response_text(
                [
                    entry("APA_COIL_RUN_ULTRA", 1, "command"),
                    entry("// Point: low_anchor", 2),
                ]
            ),
            "// Point: low_anchor",
        )

    def test_recovers_latest_complete_suite_and_completion_time(self):
        log = (
            Path(__file__).resolve().parent
            / "fixtures"
            / "apa_chain_v6_real_log.txt"
        ).read_text(encoding="utf-8")
        entries = tuple(
            entry(line, 1000 + index)
            for index, line in enumerate(log.splitlines())
        )
        cached = latest_cached_suite(entries)
        self.assertEqual(cached.suite.static_fallback, 0.010364)
        self.assertIn("R3d PLA Rapid", cached.text)
        self.assertGreater(cached.completed_at, 1000)


if __name__ == "__main__":
    unittest.main()
