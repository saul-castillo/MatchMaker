from types import SimpleNamespace
import unittest

from matchmaker.physical.models import TerminalRef
from matchmaker.physical.mos_centroid_snapshot import (
    create_mos_centroid_physical_design_snapshot,
)
from matchmaker.placement.core.tile_plan import PlacementPlan, Tile


class FakePort:
    def __init__(self, name, center, orientation, width=0.4, layer=(30, 0)):
        self.name = name
        self.center = center
        self.orientation = orientation
        self.width = width
        self.layer = layer


class FakeReference:
    def __init__(self, cell_name, bbox, ports):
        self.parent = SimpleNamespace(name=cell_name)
        self.bbox = bbox
        self._ports = tuple(ports)

    def get_ports_list(self):
        return list(self._ports)


class FakeComponent:
    def __init__(self, references):
        self.references = list(references)
        self.ports = {}

    def add_ports(self, ports, prefix=""):
        for port in ports:
            self.ports[f"{prefix}{port.name}"] = port


class PhysicalDesignSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.plan = PlacementPlan(
            cell_name="demo",
            rows=1,
            cols=2,
            tiles=(
                Tile("A0", "A", 0, 0, "R0", "active"),
                Tile("B0", "B", 0, 1, "MY", "active"),
            ),
        )
        internal_ports = (
            FakePort("multiplier_0_gate_E", (0.0, 0.0), 0.0),
            FakePort("route_internal_17", (0.0, 0.0), 0.0),
            FakePort("gate_contact", (0.0, 0.0), 0.0),
        )
        self.component = FakeComponent(
            [
                FakeReference(
                    "nfet_A_unit",
                    ((-2.0, -1.0), (0.0, 1.0)),
                    (
                        FakePort("gate_E", (0.0, 0.0), 0.0),
                        FakePort("gate_W", (-2.0, 0.0), 180.0),
                        FakePort("source_N", (-1.0, 1.0), 90.0),
                        FakePort("body_S", (-1.0, -1.0), 270.0),
                        *internal_ports,
                    ),
                ),
                FakeReference(
                    "nfet_B_unit",
                    ((1.0, -1.0), (3.0, 1.0)),
                    (
                        FakePort("gate_E", (3.0, 0.0), 0.0),
                        FakePort("gate_W", (1.0, 0.0), 180.0),
                        FakePort("drain_S", (2.0, -1.0), 270.0),
                        *internal_ports,
                    ),
                ),
            ]
        )

    def test_snapshot_captures_instances_access_and_obstacles(self):
        snapshot = create_mos_centroid_physical_design_snapshot(
            self.component,
            self.plan,
        )

        self.assertEqual(snapshot.instance("A0").cell_name, "nfet_A_unit")
        self.assertEqual(snapshot.instance("B0").orientation, "MY")
        self.assertEqual(len(snapshot.obstacles), 2)
        self.assertIn("A0__gate_E", snapshot.access_points)
        self.assertEqual(
            tuple(
                point.name
                for point in snapshot.access_points_for(TerminalRef("A0", "gate"))
            ),
            ("A0__gate_E", "A0__gate_W"),
        )

    def test_snapshot_filters_internal_primitive_ports(self):
        snapshot = create_mos_centroid_physical_design_snapshot(
            self.component,
            self.plan,
        )

        self.assertEqual(len(snapshot.access_points), 7)
        self.assertNotIn("A0__multiplier_0_gate_E", snapshot.access_points)
        self.assertNotIn("A0__route_internal_17", snapshot.access_points)
        self.assertNotIn("A0__gate_contact", snapshot.access_points)
        self.assertIn("A0__source_N", snapshot.access_points)
        self.assertEqual(
            tuple(
                point.name
                for point in snapshot.access_points_for(TerminalRef("A0", "bulk"))
            ),
            ("A0__body_S",),
        )

    def test_snapshot_mappings_are_read_only(self):
        snapshot = create_mos_centroid_physical_design_snapshot(
            self.component,
            self.plan,
        )
        with self.assertRaises(TypeError):
            snapshot.instances["extra"] = snapshot.instance("A0")
        with self.assertRaises(TypeError):
            snapshot.access_points["extra"] = snapshot.access_point("A0__gate_E")

    def test_reference_without_supported_external_ports_fails(self):
        invalid_component = FakeComponent(
            [
                FakeReference(
                    "nfet_A_unit",
                    ((-2.0, -1.0), (0.0, 1.0)),
                    (FakePort("multiplier_0_gate_E", (0.0, 0.0), 0.0),),
                ),
                self.component.references[1],
            ]
        )
        with self.assertRaises(RuntimeError):
            create_mos_centroid_physical_design_snapshot(invalid_component, self.plan)

    def test_reference_count_mismatch_fails(self):
        incomplete = FakeComponent(self.component.references[:1])
        with self.assertRaises(ValueError):
            create_mos_centroid_physical_design_snapshot(incomplete, self.plan)


if __name__ == "__main__":
    unittest.main()
