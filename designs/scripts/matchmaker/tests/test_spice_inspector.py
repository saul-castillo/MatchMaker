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

        instance = parsed["demo"].subcircuit_instances[0]
        self.assertEqual(instance.name, "X1")
        self.assertEqual(instance.nodes, ("OUT", "IN", "VSS"))
        self.assertEqual(instance.subcircuit_name, "child")

    def test_shared_instance_nets_report_multi_instance_connections(self):
        netlist = """
.subckt top
X1 route a child
X2 route b child
X3 route c child
X4 other d child
.ends top
.subckt child A B
.ends child
"""
        top = parse_spice_subcircuits(netlist)["top"]
        self.assertEqual(
            top.shared_instance_nets(minimum_instance_count=2),
            {"route": ("X1", "X2", "X3")},
        )

    def test_unterminated_subcircuit_fails(self):
        with self.assertRaises(ValueError):
            parse_spice_subcircuits(".subckt demo A B\nR1 A B 1k\n")


if __name__ == "__main__":
    unittest.main()
