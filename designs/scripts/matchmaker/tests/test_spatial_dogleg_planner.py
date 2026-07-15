from types import SimpleNamespace
import unittest

from matchmaker.physical.models import BoundingBox, RoutingObstacle
from matchmaker.routing.planners.spatial_dogleg_planner import (
    choose_spatial_dogleg,
)


class SpatialDoglegPlannerTests(unittest.TestCase):
    def setUp(self):
        self.requested_source = SimpleNamespace(center=(0.0, 0.0), orientation=0.0)
        self.requested_target = SimpleNamespace(center=(10.0, 0.0), orientation=0.0)
        self.ports = {
            "A0__gate_W": SimpleNamespace(center=(-2.0, 0.0), orientation=180.0),
            "A1__gate_E": SimpleNamespace(center=(12.0, 0.0), orientation=0.0),
        }
        self.obstacles = tuple(
            RoutingObstacle(
                obstacle_id=f"instance:{name}",
                owner_instance_name=name,
                bbox=BoundingBox.from_corners(corners),
            )
            for name, corners in (
                ("A0", ((-3.0, -2.0), (1.0, 2.0))),
                ("B0", ((1.0, -2.0), (5.0, 2.0))),
                ("B1", ((5.0, -2.0), (9.0, 2.0))),
                ("A1", ((9.0, -2.0), (13.0, 2.0))),
            )
        )

    def test_horizontal_blocked_route_uses_outward_ports_and_north_channel(self):
        plan = choose_spatial_dogleg(
            ports=self.ports,
            source_instance_name="A0",
            source_port_name="gate_E",
            target_instance_name="A1",
            target_port_name="gate_E",
            source_port=self.requested_source,
            target_port=self.requested_target,
            obstacles=self.obstacles,
            clearance=1.0,
        )

        self.assertEqual(plan.source_top_port_name, "A0__gate_W")
        self.assertEqual(plan.target_top_port_name, "A1__gate_E")
        self.assertEqual(plan.direction, "N")
        self.assertEqual(plan.channel_coordinate, 3.0)
        self.assertEqual(plan.source_bend, (-4.0, 0.0))
        self.assertEqual(plan.target_bend, (14.0, 0.0))

    def test_missing_outward_port_fails_safe(self):
        with self.assertRaises(RuntimeError):
            choose_spatial_dogleg(
                ports={},
                source_instance_name="A0",
                source_port_name="gate_E",
                target_instance_name="A1",
                target_port_name="gate_E",
                source_port=self.requested_source,
                target_port=self.requested_target,
                obstacles=self.obstacles,
            )

    def test_non_cardinal_terminal_name_fails_safe(self):
        with self.assertRaises(RuntimeError):
            choose_spatial_dogleg(
                ports=self.ports,
                source_instance_name="A0",
                source_port_name="gate",
                target_instance_name="A1",
                target_port_name="gate",
                source_port=self.requested_source,
                target_port=self.requested_target,
                obstacles=self.obstacles,
            )


if __name__ == "__main__":
    unittest.main()
