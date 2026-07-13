from types import SimpleNamespace
import unittest

from matchmaker.routing.planners.obstacle_aware_route_planner import (
    RoutingObstacle,
    apply_obstacle_avoidance,
    find_straight_route_blockers,
)
from matchmaker.routing.planners.point_to_point_route_planner import (
    PointToPointRoutePlan,
)


class ObstacleAwareRoutePlannerTests(unittest.TestCase):
    def setUp(self):
        self.source = SimpleNamespace(center=(0.0, 0.0), orientation=0.0)
        self.target = SimpleNamespace(center=(10.0, 0.0), orientation=0.0)
        self.plan = PointToPointRoutePlan(
            net_name="gate",
            source_top_port_name="A0__gate_E",
            target_top_port_name="A1__gate_E",
            strategy="straight",
        )

    def test_inline_obstacle_is_reported(self):
        blockers = find_straight_route_blockers(
            self.source,
            self.target,
            [RoutingObstacle("B0", ((3.0, -1.0), (5.0, 1.0)))],
        )
        self.assertEqual(blockers, ("B0",))

    def test_off_axis_obstacle_is_ignored(self):
        blockers = find_straight_route_blockers(
            self.source,
            self.target,
            [RoutingObstacle("B0", ((3.0, 2.0), (5.0, 4.0)))],
        )
        self.assertEqual(blockers, ())

    def test_endpoint_instances_are_excluded(self):
        blockers = find_straight_route_blockers(
            self.source,
            self.target,
            [RoutingObstacle("A0", ((-1.0, -1.0), (1.0, 1.0)))],
            excluded_instance_names=("A0", "A1"),
        )
        self.assertEqual(blockers, ())

    def test_blocked_same_facing_straight_route_becomes_c_route(self):
        resolved, blockers = apply_obstacle_avoidance(
            plan=self.plan,
            source_port=self.source,
            target_port=self.target,
            obstacles=[RoutingObstacle("B0", ((3.0, -1.0), (5.0, 1.0)))],
            source_instance_name="A0",
            target_instance_name="A1",
        )
        self.assertEqual(resolved.strategy, "c")
        self.assertEqual(blockers, ("B0",))

    def test_blocked_opposite_facing_route_fails_safe(self):
        opposite = SimpleNamespace(center=(10.0, 0.0), orientation=180.0)
        with self.assertRaises(RuntimeError):
            apply_obstacle_avoidance(
                plan=self.plan,
                source_port=self.source,
                target_port=opposite,
                obstacles=[RoutingObstacle("B0", ((3.0, -1.0), (5.0, 1.0)))],
                source_instance_name="A0",
                target_instance_name="A1",
            )


if __name__ == "__main__":
    unittest.main()
