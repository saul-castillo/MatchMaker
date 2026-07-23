import unittest

from matchmaker.physical.models import TerminalRef
from matchmaker.routing.plans.route_plan import (
    ConstraintCheck,
    RouteMetrics,
    RoutePlan,
    RouteSegment,
)
from matchmaker.routing.plans.route_plan_checks import (
    find_cross_net_route_overlaps,
    require_no_cross_net_route_overlaps,
)


def _plan(name: str, segment: RouteSegment) -> RoutePlan:
    return RoutePlan(
        net_name=name,
        terminals=(TerminalRef("A", name), TerminalRef("B", name)),
        selected_access_point_names=(f"A__{name}", f"B__{name}"),
        strategy="test",
        segments=(segment,),
        vias=(),
        metrics=RouteMetrics.from_geometry(
            segments=(segment,),
            vias=(),
            estimated_cost=segment.length,
            resolved_width=segment.width,
        ),
        constraint_checks=(ConstraintCheck(name="test", passed=True),),
    )


class RoutePlanChecksTests(unittest.TestCase):
    def test_same_layer_crossing_is_reported(self):
        first = _plan(
            "FIRST",
            RouteSegment((0.0, 0.0), (4.0, 0.0), (36, 0), 0.5),
        )
        second = _plan(
            "SECOND",
            RouteSegment((2.0, -2.0), (2.0, 2.0), (36, 0), 0.5),
        )
        overlaps = find_cross_net_route_overlaps((first, second))
        self.assertEqual(len(overlaps), 1)
        with self.assertRaises(RuntimeError):
            require_no_cross_net_route_overlaps((first, second))

    def test_crossing_on_different_layers_is_allowed(self):
        first = _plan(
            "FIRST",
            RouteSegment((0.0, 0.0), (4.0, 0.0), (36, 0), 0.5),
        )
        second = _plan(
            "SECOND",
            RouteSegment((2.0, -2.0), (2.0, 2.0), (42, 0), 0.5),
        )
        self.assertEqual(find_cross_net_route_overlaps((first, second)), ())
        require_no_cross_net_route_overlaps((first, second))


if __name__ == "__main__":
    unittest.main()
