import unittest

from matchmaker.design.cdac_manifest_compiler import compile_banked_cdac_manifest
from matchmaker.placement.cdac.capacitor_array_intent import (
    CdacCapacitorArrayIntent,
)
from matchmaker.placement.cdac.capacitor_array_plan_compiler import (
    compile_cdac_capacitor_array_plan,
    infer_near_square_grid_shape,
)
from matchmaker.specs.banked_cdac_spec import (
    make_gf180_4bit_banked_cdac_reference_spec,
    make_scaled_binary_banked_cdac_spec,
)
from matchmaker.specs.capacitor_device_spec import MimCapacitorSpec


def _generic_spec(bits: int):
    return make_scaled_binary_banked_cdac_spec(
        cell_name=f"cdac_{bits}b_test",
        bits=bits,
        unit_capacitor=MimCapacitorSpec(
            name="unit_cap",
            width=6.0,
            length=4.0,
            model="test_mim",
        ),
        base_nmos_width=3.0,
        base_pmos_width=6.0,
        mos_length=0.3,
        termination_unit_count=1,
        include_reset_switch=True,
    )


class BankedCdacSpecificationTests(unittest.TestCase):
    def test_reference_preset_matches_reviewed_hierarchy(self):
        spec = make_gf180_4bit_banked_cdac_reference_spec()

        self.assertEqual(spec.resolution_bits, 4)
        self.assertEqual(
            tuple(bank.unit_count for bank in spec.ordered_banks),
            (1, 2, 4, 8),
        )
        self.assertEqual(spec.switched_unit_count, 15)
        self.assertEqual(spec.total_unit_count, 16)
        self.assertEqual(spec.transistor_count, 18)
        self.assertEqual(spec.unit_capacitor.width, 5.0)
        self.assertEqual(spec.unit_capacitor.length, 5.0)
        self.assertEqual(spec.unit_capacitor.model, "cap_mim_2f0fF")
        self.assertEqual(
            tuple(bank.selector.switch.nmos.width for bank in spec.ordered_banks),
            (4.0, 8.0, 16.0, 32.0),
        )
        self.assertEqual(
            tuple(bank.selector.switch.pmos.width for bank in spec.ordered_banks),
            (8.0, 16.0, 32.0, 64.0),
        )

    def test_binary_compiler_changes_counts_and_widths_with_bit_count(self):
        spec = _generic_spec(bits=3)

        self.assertEqual(spec.resolution_bits, 3)
        self.assertEqual(spec.total_unit_count, 8)
        self.assertEqual(spec.transistor_count, 14)
        self.assertEqual(
            tuple(bank.selector.switch.nmos.width for bank in spec.ordered_banks),
            (3.0, 6.0, 12.0),
        )
        self.assertEqual(
            tuple(bank.selector.switch.pmos.width for bank in spec.ordered_banks),
            (6.0, 12.0, 24.0),
        )

    def test_invalid_bit_count_is_rejected(self):
        with self.assertRaises(ValueError):
            make_scaled_binary_banked_cdac_spec(
                cell_name="bad",
                bits=0,
                unit_capacitor=MimCapacitorSpec("unit", 5.0, 5.0),
                base_nmos_width=4.0,
                base_pmos_width=8.0,
                mos_length=0.28,
            )


class BankedCdacManifestTests(unittest.TestCase):
    def test_manifest_is_compiled_from_spec_without_schematic_input(self):
        spec = make_gf180_4bit_banked_cdac_reference_spec()
        manifest = compile_banked_cdac_manifest(spec)

        capacitor_instances = tuple(
            instance
            for instance in manifest.instances
            if instance.instance_kind == "mim_capacitor"
        )
        selector_instances = tuple(
            instance
            for instance in manifest.instances
            if instance.instance_kind == "reference_selector"
        )
        reset_instances = tuple(
            instance
            for instance in manifest.instances
            if instance.instance_kind == "transmission_gate"
        )

        self.assertEqual(len(capacitor_instances), 16)
        self.assertEqual(len(selector_instances), 4)
        self.assertEqual(len(reset_instances), 1)
        self.assertEqual(len(manifest.instance("C_B3_7").parameters), 4)
        self.assertIn("VOUT", manifest.public_net_names)
        self.assertIn("B0", manifest.public_net_names)
        self.assertIn("B3B", manifest.public_net_names)
        self.assertIn("RST", manifest.public_net_names)
        self.assertIn(
            "independent of Xschem schematic hierarchy",
            manifest.provenance,
        )

        vout = manifest.net("VOUT")
        capacitor_top_terminals = tuple(
            terminal
            for terminal in vout.terminals
            if terminal.instance_name.startswith("C_")
        )
        self.assertEqual(len(capacitor_top_terminals), 16)
        self.assertTrue(
            any(
                terminal.instance_name == "RESET_TG"
                and terminal.terminal_name == "input"
                for terminal in vout.terminals
            )
        )

    def test_manifest_scales_for_non_reference_bit_count(self):
        spec = _generic_spec(bits=3)
        manifest = compile_banked_cdac_manifest(spec)

        self.assertEqual(
            len(
                tuple(
                    instance
                    for instance in manifest.instances
                    if instance.instance_kind == "mim_capacitor"
                )
            ),
            8,
        )
        self.assertEqual(
            len(
                tuple(
                    instance
                    for instance in manifest.instances
                    if instance.instance_kind == "reference_selector"
                )
            ),
            3,
        )
        self.assertNotIn("B3", manifest.public_net_names)


class CdacCapacitorPlacementTests(unittest.TestCase):
    def _plan(self, bits: int = 4, **intent_overrides):
        spec = _generic_spec(bits=bits)
        manifest = compile_banked_cdac_manifest(spec)
        intent = CdacCapacitorArrayIntent(
            spec=spec,
            manifest=manifest,
            **intent_overrides,
        )
        return compile_cdac_capacitor_array_plan(intent)

    def test_grid_shape_is_inferred_from_total_units(self):
        self.assertEqual(infer_near_square_grid_shape(16), (4, 4))
        self.assertEqual(infer_near_square_grid_shape(8), (2, 4))
        self.assertEqual(infer_near_square_grid_shape(18), (3, 6))

    def test_reference_family_compiles_to_balanced_inversion_grid(self):
        plan = self._plan(bits=4)

        self.assertEqual((plan.rows, plan.cols), (4, 4))
        self.assertEqual(len(plan.tiles), 16)
        counts = {
            group: sum(tile.group == group for tile in plan.tiles)
            for group in {tile.group for tile in plan.tiles}
        }
        self.assertEqual(
            counts,
            {"B0": 1, "B1": 2, "B2": 4, "B3": 8, "TERM": 1},
        )

        by_coordinate = {(tile.row, tile.col): tile for tile in plan.tiles}
        for tile in plan.tiles:
            mirror = by_coordinate[
                (plan.rows - 1 - tile.row, plan.cols - 1 - tile.col)
            ]
            if tile.group in {"B0", "TERM"}:
                self.assertEqual({tile.group, mirror.group}, {"B0", "TERM"})
            else:
                self.assertEqual(tile.group, mirror.group)

    def test_three_bit_family_uses_two_by_four_grid(self):
        plan = self._plan(bits=3)
        self.assertEqual((plan.rows, plan.cols), (2, 4))
        self.assertEqual(len(plan.tiles), 8)
        self.assertFalse(any(tile.name.startswith("C_B3_") for tile in plan.tiles))

    def test_explicit_grid_must_match_unit_count(self):
        with self.assertRaises(ValueError):
            self._plan(bits=4, rows=2, cols=4)

    def test_residual_pair_policy_can_require_strict_group_symmetry(self):
        with self.assertRaises(ValueError):
            self._plan(bits=4, residual_pair_policy="reject")

    def test_compilation_is_deterministic(self):
        first = self._plan(bits=5)
        second = self._plan(bits=5)
        first_tiles = tuple(
            (tile.name, tile.group, tile.row, tile.col, tile.orientation)
            for tile in first.tiles
        )
        second_tiles = tuple(
            (tile.name, tile.group, tile.row, tile.col, tile.orientation)
            for tile in second.tiles
        )
        self.assertEqual(first_tiles, second_tiles)


if __name__ == "__main__":
    unittest.main()
