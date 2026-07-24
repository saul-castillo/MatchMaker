import unittest
from pathlib import Path

from matchmaker.outputs.cdac_demo_cell_names import (
    GF180_CDAC_B0_REFERENCE_SELECTOR_DEMO_CELL_NAME,
    GF180_CDAC_BASE_TRANSMISSION_GATE_DEMO_CELL_NAME,
)
from matchmaker.verification.lvs.cdac_leaf_targets import (
    make_gf180_cdac_leaf_lvs_targets,
)


class CdacLeafLvsTargetTests(unittest.TestCase):
    def test_targets_use_canonical_generator_cell_names(self):
        targets = {
            target.name: target
            for target in make_gf180_cdac_leaf_lvs_targets(Path("/demo/designs"))
        }

        self.assertEqual(
            targets["transmission_gate"].layout_cell_name,
            GF180_CDAC_BASE_TRANSMISSION_GATE_DEMO_CELL_NAME,
        )
        self.assertEqual(
            targets["reference_selector"].layout_cell_name,
            GF180_CDAC_B0_REFERENCE_SELECTOR_DEMO_CELL_NAME,
        )

    def test_targets_bind_independent_reference_schematics(self):
        targets = {
            target.name: target
            for target in make_gf180_cdac_leaf_lvs_targets(Path("/demo/designs"))
        }

        self.assertEqual(
            targets["transmission_gate"].schematic_path,
            Path("/demo/designs/libs/core_matchmaker/7D_tg_switch/7D_tg_switch.sch"),
        )
        self.assertEqual(
            targets["reference_selector"].schematic_path,
            Path(
                "/demo/designs/libs/core_matchmaker/7D_ref_sel_2to1/"
                "7D_ref_sel_2to1.sch"
            ),
        )


if __name__ == "__main__":
    unittest.main()
