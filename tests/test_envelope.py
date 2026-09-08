import json
import tempfile
import unittest
from pathlib import Path

from u1_filament_automation.envelope import (
    EnvelopeError,
    calculate_automatic_envelope,
    resolve_max_volumetric_speed,
)


class AutomaticEnvelopeTests(unittest.TestCase):
    def test_deeplee_limits_cap_the_orca_flow_envelope(self):
        result = calculate_automatic_envelope(15, 30, 70)
        self.assertEqual(
            (result.low_speed, result.mid_speed, result.high_speed),
            (30, 50, 70),
        )
        self.assertEqual(result.max_speed_from_flow, 184)
        self.assertEqual(result.limiting_source, "manufacturer")
        self.assertTrue(result.weak_signal_warning)

    def test_orca_flow_is_primary_when_no_manufacturer_limit_is_given(self):
        result = calculate_automatic_envelope(15)
        self.assertEqual(
            (result.low_speed, result.mid_speed, result.high_speed),
            (92, 138, 184),
        )
        self.assertEqual(result.limiting_source, "volumetric_flow")
        self.assertFalse(result.weak_signal_warning)

    def test_invalid_or_reversed_limits_are_blocked(self):
        with self.assertRaises(EnvelopeError):
            calculate_automatic_envelope(0)
        with self.assertRaises(EnvelopeError):
            calculate_automatic_envelope(15, 80, 70)

    def test_max_flow_is_resolved_through_orca_inheritance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user = root / "user"
            system = root / "system"
            user.mkdir()
            system.mkdir()
            child = user / "DEEPLEE PLA BLU METALLICO.json"
            child.write_text(
                json.dumps({
                    "name": "DEEPLEE PLA BLU METALLICO",
                    "inherits": "Snapmaker PLA Basic @U1",
                }),
                encoding="utf-8",
            )
            base = system / "Snapmaker PLA Basic @U1.json"
            base.write_text(
                json.dumps({
                    "name": "Snapmaker PLA Basic @U1",
                    "filament_max_volumetric_speed": ["15"],
                }),
                encoding="utf-8",
            )

            resolved = resolve_max_volumetric_speed(child, user, system)

        self.assertEqual(resolved.value, 15)
        self.assertEqual(resolved.profile_name, "Snapmaker PLA Basic @U1")


if __name__ == "__main__":
    unittest.main()
