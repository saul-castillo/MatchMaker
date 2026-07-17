from dataclasses import dataclass
import unittest

from matchmaker.physical.cdac_capacitor_snapshot import (
    Gf180MimExternalAccessPolicy,
    classify_gf180_mim_external_port_name,
    create_cdac_capacitor_array_physical_design_snapshot,
)
from matchmaker.physical.models import TerminalRef
from matchmaker.placement.core.placement_result import (
    PlacedReferenceBinding,
    PlacementResult,
)
from matchmaker.placement.core.tile_plan import PlacementPlan, Tile


@dataclass
class _FakePort:
    name: str
    center: tuple[float, float]
    orientation: float
    width: float
    layer: tuple[int, int]


class _FakeReference:
    def __init__(self, ports, bbox=((-3.0, -2.0), (3.0, 2.0))):
        self._ports = tuple(ports)
        self.bbox = bbox

    def get_ports_list(self):
        return list(self._ports)


class _FakeComponent:
    def __init__(self):
        self.ports = {}

    def add_ports(self, ports, prefix=""):
        for port in ports:
            self.ports[f"{prefix}{port.name}"] = port


def _external_ports(top_layer=(91, 7), bottom_layer=(73, 2)):
    orientation_by_direction = {"E": 0.0, "N": 90.0, "W": 180.0, "S": 270.0}
    ports = []
    for terminal, layer, width in (
        ("top", top_layer, 5.0),
        ("bottom", bottom_layer, 6.0),
    ):
        for direction in ("N", "E", "S", "W"):
            ports.append(
                _FakePort(
                    name=f"{terminal}_met_{direction}",
                    center=(float(len(ports)), float(-len(ports))),
                    orientation=orientation_by_direction[direction],
                    width=width,
                    layer=layer,
                )
            )
    return ports


def _placement_result(ports):
    component = _FakeComponent()
    tile = Tile(
        name="C_B0_0",
        group="B0",
        row=0,
        col=0,
        orientation="R0",
        role="active",
    )
    plan = PlacementPlan(
        cell_name="capacitor_array_test",
        rows=1,
        cols=1,
        tiles=(tile,),
    )
    reference = _FakeReference(ports)
    binding = PlacedReferenceBinding(
        instance_name=tile.name,
        cell_name="unit_mim_capacitor",
        reference=reference,
        row=tile.row,
        col=tile.col,
        orientation=tile.orientation,
        role=tile.role,
        group=tile.group,
    )
    return PlacementResult(
        component=component,
        plan=plan,
        bindings={tile.name: binding},
    )


class Gf180MimAccessPolicyTests(unittest.TestCase):
    def test_exact_external_names_are_classified(self):
        self.assertEqual(
            classify_gf180_mim_external_port_name("top_met_E"),
            "top",
        )
        self.assertEqual(
            classify_gf180_mim_external_port_name("bottom_met_N"),
            "bottom",
        )

    def test_nested_and_nonmetal_exports_are_rejected(self):
        self.assertIsNone(
            classify_gf180_mim_external_port_name(
                "array_row0_col0_top_met_E"
            )
        )
        self.assertIsNone(classify_gf180_mim_external_port_name("top_via_E"))
        self.assertIsNone(classify_gf180_mim_external_port_name("top_met_Q"))

    def test_port_grammar_is_explicitly_configurable(self):
        policy = Gf180MimExternalAccessPolicy(
            electrode_aliases={"platea": "top", "plateb": "bottom"},
            conductor_token="metal",
            directions=("E", "W"),
        )
        self.assertEqual(policy.classify("platea_metal_E"), "top")
        self.assertEqual(policy.classify("plateb_metal_W"), "bottom")
        self.assertIsNone(policy.classify("top_met_E"))


class CdacCapacitorSnapshotTests(unittest.TestCase):
    def test_snapshot_retains_only_eight_external_accesses(self):
        ports = _external_ports()
        ports.extend(
            [
                _FakePort(
                    name="array_row0_col0_top_met_E",
                    center=(0.0, 0.0),
                    orientation=0.0,
                    width=0.5,
                    layer=(42, 0),
                ),
                _FakePort(
                    name="array_row0_col0_bottom_via_E",
                    center=(0.0, 0.0),
                    orientation=0.0,
                    width=0.26,
                    layer=(38, 0),
                ),
            ]
        )
        placement = _placement_result(ports)

        snapshot = create_cdac_capacitor_array_physical_design_snapshot(placement)

        self.assertEqual(len(snapshot.instances), 1)
        self.assertEqual(len(snapshot.access_points), 8)
        self.assertEqual(len(snapshot.obstacles), 1)
        self.assertEqual(len(placement.component.ports), 8)
        self.assertEqual(snapshot.obstacles[0].kind, "mim_capacitor")

        top = snapshot.access_points_for(TerminalRef("C_B0_0", "top"))
        bottom = snapshot.access_points_for(TerminalRef("C_B0_0", "bottom"))
        self.assertEqual(len(top), 4)
        self.assertEqual(len(bottom), 4)
        self.assertEqual({access.layer for access in top}, {(91, 7)})
        self.assertEqual({access.layer for access in bottom}, {(73, 2)})
        self.assertEqual({access.width for access in top}, {5.0})
        self.assertEqual({access.width for access in bottom}, {6.0})
        self.assertTrue(
            all(access.name.startswith("C_B0_0__") for access in top + bottom)
        )

    def test_layer_numbers_are_captured_from_ports_not_adapter_literals(self):
        first = create_cdac_capacitor_array_physical_design_snapshot(
            _placement_result(_external_ports(top_layer=(8, 1), bottom_layer=(9, 2)))
        )
        second = create_cdac_capacitor_array_physical_design_snapshot(
            _placement_result(_external_ports(top_layer=(108, 3), bottom_layer=(209, 4)))
        )

        self.assertEqual(
            {access.layer for access in first.access_points_for(TerminalRef("C_B0_0", "top"))},
            {(8, 1)},
        )
        self.assertEqual(
            {access.layer for access in second.access_points_for(TerminalRef("C_B0_0", "top"))},
            {(108, 3)},
        )

    def test_missing_external_access_family_fails_explicitly(self):
        placement = _placement_result(
            [
                _FakePort(
                    name="array_row0_col0_top_met_E",
                    center=(0.0, 0.0),
                    orientation=0.0,
                    width=0.5,
                    layer=(42, 0),
                )
            ]
        )
        with self.assertRaises(RuntimeError):
            create_cdac_capacitor_array_physical_design_snapshot(placement)


if __name__ == "__main__":
    unittest.main()
