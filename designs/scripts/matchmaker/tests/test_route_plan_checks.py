import unittest

from matchmaker.physical.models import TerminalRef
from matchmaker.routing.plans.route_plan import (
    ConstraintCheck,
    RouteMetrics,
    RoutePlan,
    RouteSegment,
)
from matchmaker.routing.plans.route_plan_checks import (
    ViaEnvelope,
    find_cross_net_via_envelope_overlaps,
    find_via_envelope_route_overlaps,
    find_cross_net_route_overlaps,
    require_no_cross_net_via_envelope_overlaps,
    require_no_cross_net_route_overlaps,
    require_via_envelopes_clear_routes,
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

    def test_via_envelope_touching_other_net_is_reported(self):
        other = _plan(
            "OTHER",
            RouteSegment((0.0, 0.0), (4.0, 0.0), (36, 0), 0.5),
        )
        overlaps = find_via_envelope_route_overlaps(
            via_net="VSS",
            via_centers=((2.0, 0.6),),
            via_size=(0.8, 0.8),
            layer=(36, 0),
            plans=(other,),
        )
        self.assertEqual(len(overlaps), 1)
        with self.assertRaises(RuntimeError):
            require_via_envelopes_clear_routes(
                via_net="VSS",
                via_centers=((2.0, 0.6),),
                via_size=(0.8, 0.8),
                layer=(36, 0),
                plans=(other,),
            )

    def test_via_envelope_on_other_layer_is_ignored(self):
        other = _plan(
            "OTHER",
            RouteSegment((0.0, 0.0), (4.0, 0.0), (42, 0), 0.5),
        )
        self.assertEqual(
            find_via_envelope_route_overlaps(
                via_net="VSS",
                via_centers=((2.0, 0.0),),
                via_size=(0.8, 0.8),
                layer=(36, 0),
                plans=(other,),
            ),
            (),
        )

    def test_cross_net_via_envelopes_are_layer_aware(self):
        first = ViaEnvelope(
            net_name="FIRST",
            center=(0.0, 0.0),
            size=(1.0, 1.0),
            layers=((36, 0), (42, 0)),
        )
        touching = ViaEnvelope(
            net_name="SECOND",
            center=(0.9, 0.0),
            size=(1.0, 1.0),
            layers=((36, 0), (42, 0)),
        )
        other_layer = ViaEnvelope(
            net_name="THIRD",
            center=(0.0, 0.0),
            size=(1.0, 1.0),
            layers=((46, 0), (49, 0)),
        )
        self.assertEqual(
            len(find_cross_net_via_envelope_overlaps((first, touching))),
            1,
        )
        with self.assertRaises(RuntimeError):
            require_no_cross_net_via_envelope_overlaps((first, touching))
        self.assertEqual(
            find_cross_net_via_envelope_overlaps((first, other_layer)),
            (),
        )


if __name__ == "__main__":
    unittest.main()
