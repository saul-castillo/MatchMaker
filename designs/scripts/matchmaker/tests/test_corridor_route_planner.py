import unittest

from matchmaker.physical.models import AccessPoint, BoundingBox, TerminalRef
from matchmaker.routing.intents.net_intent import NetIntent
from matchmaker.routing.planners.corridor_route_planner import (
    envelope_from_bboxes,
    plan_external_side_bus,
    plan_gap_bridge,
    plan_transitioned_trunk_tree,
    via_center_at_envelope_side,
    via_center_at_gap_edge,
)
from matchmaker.routing.resources import RoutingLayerTransition


def _access(
    *,
    instance: str,
    terminal: str,
    name: str,
    center: tuple[float, float],
    orientation: float,
    layer=(10, 0),
) -> AccessPoint:
    return AccessPoint(
        name=name,
        terminal=TerminalRef(instance, terminal),
        primitive_port_name=name.split("__")[-1],
        center=center,
        orientation=orientation,
        width=0.5,
        layer=layer,
    )


class CorridorRoutePlannerTests(unittest.TestCase):
    def test_pair_corridor_derives_runtime_gap_and_via_locations(self):
        corridor = envelope_from_bboxes(
            (
                BoundingBox(-4.0, 2.0, 4.0, 8.0),
                BoundingBox(-5.0, -9.0, 5.0, -2.0),
            ),
            gap_axis="vertical",
        )
        self.assertEqual(corridor.gap_low, -2.0)
        self.assertEqual(corridor.gap_high, 2.0)
        self.assertEqual(corridor.gap_coordinate, 0.0)

        gap_access = _access(
            instance="M0",
            terminal="body",
            name="M0__body_S",
            center=(-2.0, 3.0),
            orientation=270,
        )
        side_access = _access(
            instance="M1",
            terminal="signal",
            name="M1__signal_E",
            center=(4.5, -5.0),
            orientation=0,
        )
        self.assertEqual(
            via_center_at_gap_edge(
                access=gap_access,
                corridor=corridor,
                adjacent_side="high",
                via_size=(0.8, 1.0),
            ),
            (-2.0, 1.5),
        )
        self.assertEqual(
            via_center_at_envelope_side(
                access=side_access,
                envelope=corridor.bbox,
                side="east",
                via_size=(0.8, 1.0),
            ),
            (5.4, -5.0),
        )

    def test_external_bus_is_cell_family_agnostic(self):
        first = _access(
            instance="R0",
            terminal="sense",
            name="R0__sense_W",
            center=(-3.0, 4.0),
            orientation=180,
        )
        second = _access(
            instance="R1",
            terminal="sense",
            name="R1__sense_W",
            center=(-3.0, -4.0),
            orientation=180,
        )
        plan = plan_external_side_bus(
            intent=NetIntent("MATCH", (first.terminal, second.terminal)),
            first=first,
            second=second,
            envelope=BoundingBox(-5.0, -6.0, 5.0, 6.0),
            side="west",
            clearance=1.0,
        )
        self.assertEqual(plan.strategy, "external_west_side_bus")
        self.assertEqual(plan.metrics.total_length, 14.5)
        self.assertEqual(plan.metrics.bend_count, 2)
        self.assertEqual(
            plan.provenance[2],
            "reusable corridor-route planner",
        )

    def test_gap_bridge_uses_only_logical_terminals_and_access_geometry(self):
        first = _access(
            instance="C0",
            terminal="plate",
            name="C0__plate_S",
            center=(-1.0, 2.0),
            orientation=270,
        )
        second = _access(
            instance="C1",
            terminal="plate",
            name="C1__plate_N",
            center=(1.0, -2.0),
            orientation=90,
        )
        plan = plan_gap_bridge(
            intent=NetIntent("PLATE", (first.terminal, second.terminal)),
            first=first,
            second=second,
            axis="vertical",
            gap_coordinate=0.0,
        )
        self.assertEqual(plan.strategy, "vertical_gap_bridge")
        self.assertEqual(plan.metrics.total_length, 6.0)
        self.assertEqual(plan.metrics.bend_count, 2)

    def test_transitioned_tree_supports_arbitrary_three_terminal_family(self):
        accesses = (
            _access(
                instance="Q0",
                terminal="bulk",
                name="Q0__bulk_S",
                center=(-2.0, 3.0),
                orientation=270,
            ),
            _access(
                instance="Q1",
                terminal="bulk",
                name="Q1__bulk_N",
                center=(2.0, -3.0),
                orientation=90,
            ),
            _access(
                instance="Q1",
                terminal="reference",
                name="Q1__reference_S",
                center=(0.0, -5.0),
                orientation=270,
            ),
        )
        plan = plan_transitioned_trunk_tree(
            intent=NetIntent(
                "BODY_REFERENCE",
                tuple(access.terminal for access in accesses),
            ),
            accesses=accesses,
            via_centers=((-2.0, 1.0), (2.0, -1.0), (0.0, -7.0)),
            transition=RoutingLayerTransition(
                source_layer=(10, 0),
                route_layer=(12, 0),
                via_name="stack",
                via_size=(0.8, 0.8),
                minimum_route_width=0.6,
            ),
            trunk_axis="vertical",
            trunk_coordinate=0.0,
        )
        self.assertEqual(plan.metrics.via_count, 3)
        self.assertEqual(
            {segment.layer for segment in plan.segments},
            {(10, 0), (12, 0)},
        )
        self.assertEqual(plan.metrics.resolved_width, 0.6)


if __name__ == "__main__":
    unittest.main()
