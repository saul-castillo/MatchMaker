import unittest

from matchmaker.verification.netlist.spice_inspector import parse_spice_subcircuits


class SpiceInspectorTests(unittest.TestCase):
    def test_parse_subcircuit_and_continuation_lines(self):
        netlist = """
* comment
.subckt demo IN OUT VSS
M1 OUT IN VSS VSS nfet_03v3
X1 OUT IN
+ VSS child
.ends demo

.subckt child D G S
R1 D S 1k
.ends child
"""
        parsed = parse_spice_subcircuits(netlist)

        self.assertEqual(set(parsed), {"demo", "child"})
        self.assertEqual(parsed["demo"].ports, ("IN", "OUT", "VSS"))
        self.assertEqual(len(parsed["demo"].mos_statements), 1)
        self.assertEqual(len(parsed["demo"].subcircuit_instance_statements), 1)
        self.assertIn("X1 OUT IN VSS child", parsed["demo"].statements)

    def test_unterminated_subcircuit_fails(self):
        with self.assertRaises(ValueError):
            parse_spice_subcircuits(".subckt demo A B\nR1 A B 1k\n")


if __name__ == "__main__":
    unittest.main()
