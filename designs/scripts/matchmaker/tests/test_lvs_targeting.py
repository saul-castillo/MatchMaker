import unittest
from pathlib import Path

from matchmaker.verification.lvs.cdac_leaf_targets import (
    make_gf180_cdac_leaf_lvs_targets,
)
from matchmaker.verification.lvs.magic_netgen_lvs import (
    _build_netgen_lvs_argv,
)
from matchmaker.verification.netlist.xschem_schematic_netlist import (
    _build_xschem_environment,
    _build_xschem_netlist_argv,
    _contains_subcircuit,
)


class LvsTargetingTests(unittest.TestCase):
    def test_netgen_argv_supports_distinct_top_cell_names(self):
        argv = _build_netgen_lvs_argv(
            netgen_bin="netgen",
            schematic_netlist_path=Path("/tmp/reference.spice"),
            schematic_cell_name="7D_tg_switch",
            layout_netlist_path=Path("/tmp/layout.spice"),
            layout_cell_name="generated_tg",
            setup_file=Path("/tmp/setup.tcl"),
        )
        self.assertEqual(argv[3], "/tmp/reference.spice 7D_tg_switch")
        self.assertEqual(argv[4], "/tmp/layout.spice generated_tg")

    def test_xschem_argv_is_headless_spice_lvs_netlisting(self):
        argv = _build_xschem_netlist_argv(
            xschem_bin="xschem",
            schematic_path=Path("/tmp/ref.sch"),
            netlist_path=Path("/tmp/out/ref.spice"),
            rcfile=Path("/tmp/xschemrc"),
        )
        self.assertIn("-q", argv)
        self.assertIn("-x", argv)
        self.assertIn("-n", argv)
        self.assertIn("-s", argv)
        self.assertIn("set lvs_netlist 1", argv)
        self.assertIn("ref.spice", argv)

    def test_xschem_environment_is_explicit(self):
        environment = _build_xschem_environment(
            designs_root=Path("/foss/designs"),
            pdk_name="gf180mcuD",
            pdk_root=Path("/foss/pdks"),
            extra_env={"EXTRA": "value"},
        )
        self.assertEqual(environment["DESIGNS"], "/foss/designs")
        self.assertEqual(environment["PDK"], "gf180mcuD")
        self.assertEqual(environment["PDK_ROOT"], "/foss/pdks")
        self.assertEqual(environment["EXTRA"], "value")

    def test_subcircuit_detection_is_case_insensitive(self):
        netlist = ".SUBCKT 7D_tg_switch IN OUT VSS VDD CTRL CTRLB\n.ends\n"
        self.assertTrue(_contains_subcircuit(netlist, "7D_tg_switch"))
        self.assertFalse(_contains_subcircuit(netlist, "other"))

    def test_reviewed_leaf_target_mapping_is_explicit(self):
        targets = make_gf180_cdac_leaf_lvs_targets(Path("/foss/designs"))
        self.assertEqual(
            tuple(target.name for target in targets),
            ("transmission_gate", "reference_selector"),
        )
        self.assertEqual(targets[0].schematic_cell_name, "7D_tg_switch")
        self.assertEqual(
            targets[1].schematic_cell_name,
            "7D_ref_sel_2to1",
        )
        self.assertEqual(
            targets[1].layout_cell_name,
            "gf180_cdac_b0_reference_selector_demo",
        )


if __name__ == "__main__":
    unittest.main()
