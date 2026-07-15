from types import SimpleNamespace
import unittest

from matchmaker.physical.models import BoundingBox, RoutingObstacle
from matchmaker.routing.planners.obstacle_aware_route_planner import (
    find_straight_route_blockers,
)


class ObstacleAwareRoutePlannerTests(unittest.TestCase):
    def setUp(self):
        self.source = SimpleNamespace(center=(0.0, 0.0), orientation=0.0)
        self.target = SimpleNamespace(center=(10.0, 0.0), orientation=0.0)

    @staticmethod
    def obstacle(name, corners):
        return RoutingObstacle(
            obstacle_id=f"instance:{name}",
            owner_instance_name=name,
            bbox=BoundingBox.from_corners(corners),
        )

    def test_inline_obstacle_is_reported(self):
        blockers = find_straight_route_blockers(
            self.source,
            self.target,
            [self.obstacle("B0", ((3.0, -1.0), (5.0, 1.0)))],
        )
        self.assertEqual(blockers, ("B0",))

    def test_off_axis_obstacle_is_ignored(self):
        blockers = find_straight_route_blockers(
            self.source,
            self.target,
            [self.obstacle("B0", ((3.0, 2.0), (5.0, 4.0)))],
        )
        self.assertEqual(blockers, ())

    def test_endpoint_instances_are_excluded(self):
        blockers = find_straight_route_blockers(
            self.source,
            self.target,
            [self.obstacle("A0", ((-1.0, -1.0), (1.0, 1.0)))],
            excluded_instance_names=("A0", "A1"),
        )
        self.assertEqual(blockers, ())

    def test_clearance_expands_obstacle_bounds(self):
        blockers = find_straight_route_blockers(
            self.source,
            self.target,
            [self.obstacle("B0", ((3.0, 0.5), (5.0, 1.0)))],
            clearance=0.5,
        )
        self.assertEqual(blockers, ("B0",))


if __name__ == "__main__":
    unittest.main()
