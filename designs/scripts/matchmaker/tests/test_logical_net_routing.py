import unittest

from matchmaker.physical.models import (
    AccessPoint,
    BoundingBox,
    PhysicalDesignSnapshot,
    PlacedInstance,
    RoutingObstacle,
    TerminalRef,
)
from matchmaker.routing.intents.net_intent import (
    NetConstraintProfile,
    NetIntent,
    RouteGroupIntent,
)
from matchmaker.routing.planners.two_terminal_access_selector import (
    RoutePlanningError,
)
from matchmaker.routing.planners.two_terminal_net_planner import (
    plan_two_terminal_net,
)


LAYER = (30, 0)


def _instance(name, bbox, col):
    return PlacedInstance(
        instance_name=name,
        cell_name=f"nfet_{name}_unit",
        bbox=BoundingBox(*bbox),
        role="active",
        group=name[0],
        orientation="R0",
        row=0,
        col=col,
    )


def _snapshot(blocked: bool = True) -> PhysicalDesignSnapshot:
    source_terminal = TerminalRef("A0", "gate")
    target_terminal = TerminalRef("A1", "gate")
    access_points = {
        "A0__gate_E": AccessPoint(
            name="A0__gate_E",
            terminal=source_terminal,
            primitive_port_name="gate_E",
            center=(0.0, 0.0),
            orientation=0.0,
            width=0.4,
            layer=LAYER,
        ),
        "A0__gate_W": AccessPoint(
            name="A0__gate_W",
            terminal=source_terminal,
            primitive_port_name="gate_W",
            center=(-2.0, 0.0),
            orientation=180.0,
            width=0.4,
            layer=LAYER,
        ),
        "A1__gate_E": AccessPoint(
            name="A1__gate_E",
            terminal=target_terminal,
            primitive_port_name="gate_E",
            center=(12.0, 0.0),
            orientation=0.0,
            width=0.4,
            layer=LAYER,
        ),
        "A1__gate_W": AccessPoint(
            name="A1__gate_W",
            terminal=target_terminal,
            primitive_port_name="gate_W",
            center=(10.0, 0.0),
            orientation=180.0,
            width=0.4,
            layer=LAYER,
        ),
    }
    instances = {
        "A0": _instance("A0", (-3.0, -2.0, 1.0, 2.0), 0),
        "A1": _instance("A1", (9.0, -2.0, 13.0, 2.0), 3),
    }
    if blocked:
        instances.update(
            {
                "B0": _instance("B0", (1.0, -2.0, 5.0, 2.0), 1),
                "B1": _instance("B1", (5.0, -2.0, 9.0, 2.0), 2),
            }
        )
    obstacles = tuple(
        RoutingObstacle(
            obstacle_id=f"instance:{name}",
            owner_instance_name=name,
            bbox=instance.bbox,
        )
        for name, instance in instances.items()
    )
    return PhysicalDesignSnapshot(
        component=object(),
        instances=instances,
        access_points=access_points,
        terminal_access={
            source_terminal: ("A0__gate_E", "A0__gate_W"),
            target_terminal: ("A1__gate_E", "A1__gate_W"),
        },
        obstacles=obstacles,
    )


def _intent(**constraint_overrides) -> NetIntent:
    return NetIntent(
        name="A_gate_pair",
        terminals=(TerminalRef("A0", "gate"), TerminalRef("A1", "gate")),
        constraints=NetConstraintProfile(**constraint_overrides),
    )


class LogicalNetRoutingTests(unittest.TestCase):
    def test_blocked_logical_net_selects_outward_dogleg_access(self):
        plan = plan_two_terminal_net(_intent(), _snapshot(blocked=True))

        self.assertEqual(plan.strategy, "dogleg")
        self.assertEqual(
            plan.selected_access_point_names,
            ("A0__gate_W", "A1__gate_E"),
        )
        self.assertEqual(plan.blockers, ("B0", "B1"))
        self.assertEqual(plan.channel_direction, "N")
        self.assertEqual(plan.channel_coordinate, 3.0)
        self.assertEqual(len(plan.segments), 5)
        self.assertEqual(plan.metrics.total_length, 28.0)
        self.assertEqual(plan.metrics.bend_count, 4)

    def test_clear_logical_net_selects_shortest_direct_access_pair(self):
        plan = plan_two_terminal_net(_intent(), _snapshot(blocked=False))

        self.assertEqual(plan.strategy, "straight")
        self.assertEqual(
            plan.selected_access_point_names,
            ("A0__gate_E", "A1__gate_W"),
        )
        self.assertEqual(plan.metrics.total_length, 10.0)
        self.assertEqual(plan.metrics.bend_count, 0)

    def test_explicit_width_is_resolved_into_route_segments(self):
        plan = plan_two_terminal_net(
            _intent(width=0.8),
            _snapshot(blocked=False),
        )
        self.assertEqual(plan.metrics.resolved_width, 0.8)
        self.assertTrue(all(segment.width == 0.8 for segment in plan.segments))

    def test_hard_maximum_length_rejects_all_candidates(self):
        with self.assertRaises(RoutePlanningError):
            plan_two_terminal_net(
                _intent(max_length=20.0),
                _snapshot(blocked=True),
            )

    def test_forbidden_layer_rejects_terminal_access(self):
        with self.assertRaises(RoutePlanningError):
            plan_two_terminal_net(
                _intent(forbidden_layers=(LAYER,)),
                _snapshot(blocked=False),
            )

    def test_net_intent_rejects_duplicate_terminals(self):
        terminal = TerminalRef("A0", "gate")
        with self.assertRaises(ValueError):
            NetIntent(name="bad", terminals=(terminal, terminal))

    def test_route_group_requires_unique_net_names(self):
        first = _intent()
        second = NetIntent(
            name=first.name,
            terminals=(TerminalRef("B0", "gate"), TerminalRef("B1", "gate")),
        )
        with self.assertRaises(ValueError):
            RouteGroupIntent(name="matched", nets=(first, second))


if __name__ == "__main__":
    unittest.main()
