from dataclasses import dataclass
import unittest

from matchmaker.routing.planners.point_to_point_route_planner import (
    choose_point_to_point_route_strategy,
)


@dataclass
class FakePort:
    center: tuple[float, float]
    orientation: float


class PointToPointRoutePlannerTests(unittest.TestCase):
    def test_inline_parallel_ports_choose_straight(self):
        source = FakePort(center=(0.0, 0.0), orientation=0)
        target = FakePort(center=(10.0, 0.0), orientation=180)
        self.assertEqual(
            choose_point_to_point_route_strategy(source, target),
            "straight",
        )

    def test_perpendicular_ports_choose_l(self):
        source = FakePort(center=(0.0, 0.0), orientation=0)
        target = FakePort(center=(10.0, 10.0), orientation=90)
        self.assertEqual(choose_point_to_point_route_strategy(source, target), "l")

    def test_same_facing_parallel_ports_choose_c(self):
        source = FakePort(center=(0.0, 0.0), orientation=0)
        target = FakePort(center=(10.0, 10.0), orientation=0)
        self.assertEqual(choose_point_to_point_route_strategy(source, target), "c")

    def test_opposite_facing_non_inline_ports_choose_smart(self):
        source = FakePort(center=(0.0, 0.0), orientation=0)
        target = FakePort(center=(10.0, 10.0), orientation=180)
        self.assertEqual(
            choose_point_to_point_route_strategy(source, target),
            "smart",
        )


if __name__ == "__main__":
    unittest.main()
