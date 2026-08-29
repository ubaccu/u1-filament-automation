import json
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from u1_filament_automation.cli import main
from u1_filament_automation.pa import PAParseError, last_complete_suite


ROOT = Path(__file__).resolve().parents[1]


class PAParserTests(unittest.TestCase):
    def test_parses_saved_validated_v6_log(self):
        log = (ROOT / "tests" / "fixtures" / "apa_chain_v6_real_log.txt").read_text(
            encoding="utf-8"
        )
        suite = last_complete_suite(log)

        self.assertEqual(
            [item.point for item in suite.results],
            ["low_anchor", "high_flow", "high_force", "stress", "center"],
        )
        self.assertEqual(
            [item.pressure_advance for item in suite.results],
            [0.009086, 0.03121, 0.010364, 0.013084, 0.007569],
        )
        self.assertEqual(
            [item.orca_row() for item in suite.results],
            [
                "0.009086,8.1416,2000",
                "0.03121,27.355776,2000",
                "0.010364,8.1416,10000",
                "0.013084,27.355776,10000",
                "0.007569,17.748688,6000",
            ],
        )
        self.assertEqual(suite.static_fallback, 0.010364)
        json.dumps(suite.to_dict())

    def test_rejects_incomplete_suite(self):
        with self.assertRaises(PAParseError):
            last_complete_suite("// Got pressure advance: 0.02")

    def test_cli_reads_saved_log_without_discovering_orca(self):
        logfile = ROOT / "tests" / "fixtures" / "apa_chain_v6_real_log.txt"
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = main(["pa-parse", str(logfile)])

        self.assertEqual(exit_code, 0)
        self.assertIn("Nessun collegamento a stampante", output.getvalue())
        self.assertIn("center: 0.007569,17.748688,6000", output.getvalue())
        self.assertIn("Fallback PA statico (mediana): 0.010364", output.getvalue())


if __name__ == "__main__":
    unittest.main()
