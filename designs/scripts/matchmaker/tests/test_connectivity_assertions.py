from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from matchmaker.verification.netlist.connectivity_assertions import (
    SharedNetConnectivityExpectation,
    evaluate_extracted_shared_net_connectivity,
)


class ConnectivityAssertionTests(unittest.TestCase):
    def _evaluate(self, top_statements: str, expected: tuple[str, ...]):
        text = f"""
.subckt top
{top_statements}
.ends top
.subckt cell_a d g
.ends cell_a
.subckt cell_b d g
.ends cell_b
.subckt cell_c d g
.ends cell_c
"""
        with TemporaryDirectory() as directory:
            path = Path(directory) / "top.spice"
            path.write_text(text)
            return evaluate_extracted_shared_net_connectivity(
                netlist_path=path,
                top_cell_name="top",
                expectation=SharedNetConnectivityExpectation(
                    expected_subcircuit_names=expected,
                    description="test route",
                ),
            )

    def test_exact_two_instance_shared_net_passes(self):
        result = self._evaluate(
            "XA d0 route cell_a\nXB d1 route cell_b\nXC d2 other cell_c",
            ("cell_a", "cell_b"),
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.matched_net, "route")
        self.assertEqual(len(result.actual_instances), 2)

    def test_extra_unintended_participant_fails(self):
        result = self._evaluate(
            "XA d0 route cell_a\nXB d1 route cell_b\nXC d2 route cell_c",
            ("cell_a", "cell_b"),
        )
        self.assertFalse(result.passed)
        self.assertEqual(result.candidate_match_count, 0)

    def test_duplicate_expected_subcircuit_names_are_counted(self):
        result = self._evaluate(
            "XA d0 route cell_a\nXB d1 route cell_a\nXC d2 other cell_c",
            ("cell_a", "cell_a"),
        )
        self.assertTrue(result.passed)

    def test_missing_top_subcircuit_fails_cleanly(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "layout.spice"
            path.write_text(".subckt other\n.ends other\n")
            result = evaluate_extracted_shared_net_connectivity(
                netlist_path=path,
                top_cell_name="top",
                expectation=SharedNetConnectivityExpectation(
                    expected_subcircuit_names=("cell_a", "cell_b"),
                ),
            )
        self.assertFalse(result.passed)
        self.assertIn("was not found", result.failure_reason or "")


if __name__ == "__main__":
    unittest.main()
