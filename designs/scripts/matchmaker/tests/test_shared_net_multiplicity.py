import unittest

from matchmaker.verification.netlist.shared_net_multiplicity import (
    SharedNetMultiplicityExpectation,
    evaluate_shared_net_multiplicity,
)
from matchmaker.verification.netlist.spice_inspector import parse_spice_subcircuits


class SharedNetMultiplicityTests(unittest.TestCase):
    def _top(self, *, include_extra_shared_net: bool = False):
        extra = " extra" if include_extra_shared_net else ""
        text = f"""
.subckt tg_top
XNMOS input output control bulk_n{extra} nmos_cell
XPMOS input output control_bar bulk_p{extra} pmos_cell
.ends tg_top
"""
        return parse_spice_subcircuits(text)["tg_top"]

    def _expectation(self):
        return SharedNetMultiplicityExpectation(
            expected_subcircuit_names=("nmos_cell", "pmos_cell"),
            expected_match_count=2,
            description="transmission-gate input and output nets",
        )

    def test_exactly_two_shared_nets_pass(self):
        result = evaluate_shared_net_multiplicity(
            self._top(),
            self._expectation(),
        )
        self.assertTrue(result.passed)
        self.assertEqual(result.matched_nets, ("input", "output"))

    def test_extra_shared_net_fails(self):
        result = evaluate_shared_net_multiplicity(
            self._top(include_extra_shared_net=True),
            self._expectation(),
        )
        self.assertFalse(result.passed)
        self.assertEqual(len(result.matched_nets), 3)

    def test_missing_shared_net_fails(self):
        top = parse_spice_subcircuits(
            """
.subckt tg_top
XNMOS input output control bulk_n nmos_cell
XPMOS input other_output control_bar bulk_p pmos_cell
.ends tg_top
"""
        )["tg_top"]
        result = evaluate_shared_net_multiplicity(top, self._expectation())
        self.assertFalse(result.passed)
        self.assertEqual(result.matched_nets, ("input",))


if __name__ == "__main__":
    unittest.main()
