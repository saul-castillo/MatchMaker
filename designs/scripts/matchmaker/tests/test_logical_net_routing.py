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
from matchmaker.routing.planners.route_candidate import RoutePlanningError
from matchmaker.routing.planners.two_terminal_net_planner import (
    plan_two_terminal_net,
    plan_two_terminal_net_with_report,
)


LAYER = (30, 0)


def _instance(name, bbox, col, row=0):
    return PlacedInstance(
        instance_name=name,
        cell_name=f"nfet_{name}_unit",
        bbox=BoundingBox(*bbox),
        role="active",
        group=name[0],
        orientation="R0",
        row=row,
        col=col,
    )


def _access(name, terminal, center, orientation, primitive_port_name):
    return AccessPoint(
        name=name,
        terminal=terminal,
        primitive_port_name=primitive_port_name,
        center=center,
        orientation=orientation,
        width=0.4,
        layer=LAYER,
    )


def _physical_design(instances, access_points, terminal_access):
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
        terminal_access=terminal_access,
        obstacles=obstacles,
    )


def _inline_snapshot(blocked=True):
    source = TerminalRef("A0", "gate")
    target = TerminalRef("A1", "gate")
    accesses = {
        "A0__gate_E": _access("A0__gate_E", source, (0.0, 0.0), 0.0, "gate_E"),
        "A0__gate_W": _access("A0__gate_W", source, (-2.0, 0.0), 180.0, "gate_W"),
        "A1__gate_E": _access("A1__gate_E", target, (12.0, 0.0), 0.0, "gate_E"),
        "A1__gate_W": _access("A1__gate_W", target, (10.0, 0.0), 180.0, "gate_W"),
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
    return _physical_design(
        instances,
        accesses,
        {
            source: ("A0__gate_E", "A0__gate_W"),
            target: ("A1__gate_E", "A1__gate_W"),
        },
    )


def _noninline_snapshot(blocked_midpoint=False):
    source = TerminalRef("S0", "gate")
    target = TerminalRef("T0", "gate")
    accesses = {
        "S0__gate_E": _access("S0__gate_E", source, (0.0, 0.0), 0.0, "gate_E"),
        "T0__gate_W": _access("T0__gate_W", target, (6.0, 6.0), 180.0, "gate_W"),
    }
    instances = {
        "S0": _instance("S0", (-2.0, -2.0, 0.0, 2.0), 0, 0),
        "T0": _instance("T0", (6.0, 4.0, 8.0, 8.0), 1, 1),
    }
    if blocked_midpoint:
        instances["X0"] = _instance("X0", (2.0, 2.0, 4.0, 4.0), 1, 0)
    return _physical_design(
        instances,
        accesses,
        {source: ("S0__gate_E",), target: ("T0__gate_W",)},
    )


def _intent(**constraint_overrides):
    return NetIntent(
        name="A_gate_pair",
        terminals=(TerminalRef("A0", "gate"), TerminalRef("A1", "gate")),
        constraints=NetConstraintProfile(**constraint_overrides),
    )


def _noninline_intent(**constraint_overrides):
    return NetIntent(
        name="diagonal_gate_pair",
        terminals=(TerminalRef("S0", "gate"), TerminalRef("T0", "gate")),
        constraints=NetConstraintProfile(**constraint_overrides),
    )


class LogicalNetRoutingTests(unittest.TestCase):
    def test_blocked_inline_net_selects_outward_dogleg(self):
        plan = plan_two_terminal_net(_intent(), _inline_snapshot(blocked=True))
        self.assertEqual(plan.strategy, "dogleg")
        self.assertEqual(
            plan.selected_access_point_names,
            ("A0__gate_W", "A1__gate_E"),
        )
        self.assertEqual(plan.blockers, ("B0", "B1"))
        self.assertEqual(plan.channel_direction, "N")
        self.assertEqual(plan.channel_coordinate, 3.0)
        self.assertEqual(plan.metrics.total_length, 28.0)
        self.assertEqual(plan.metrics.bend_count, 4)

    def test_clear_inline_net_selects_shortest_straight_route(self):
        plan = plan_two_terminal_net(_intent(), _inline_snapshot(blocked=False))
        self.assertEqual(plan.strategy, "straight")
        self.assertEqual(
            plan.selected_access_point_names,
            ("A0__gate_E", "A1__gate_W"),
        )
        self.assertEqual(plan.metrics.total_length, 10.0)
        self.assertEqual(plan.metrics.bend_count, 0)

    def test_noninline_parallel_accesses_select_z_route(self):
        result = plan_two_terminal_net_with_report(
            _noninline_intent(),
            _noninline_snapshot(),
        )
        plan = result.plan
        points = tuple(segment.start for segment in plan.segments) + (
            plan.segments[-1].end,
        )
        self.assertEqual(plan.strategy, "manhattan")
        self.assertEqual(points, ((0.0, 0.0), (3.0, 0.0), (3.0, 6.0), (6.0, 6.0)))
        self.assertEqual(plan.metrics.total_length, 12.0)
        self.assertEqual(plan.metrics.bend_count, 2)
        self.assertGreater(len(result.dispatch.rejections), 0)

    def test_manhattan_channel_moves_around_midpoint_obstacle(self):
        plan = plan_two_terminal_net(
            _noninline_intent(),
            _noninline_snapshot(blocked_midpoint=True),
        )
        self.assertEqual(plan.strategy, "manhattan")
        self.assertNotEqual(plan.segments[0].end[0], 3.0)
        self.assertEqual(plan.metrics.total_length, 12.0)

    def test_forced_straight_rejects_noninline_terminals(self):
        intent = NetIntent(
            name="diagonal_gate_pair",
            terminals=(TerminalRef("S0", "gate"), TerminalRef("T0", "gate")),
            strategy_preference="straight",
        )
        with self.assertRaises(RoutePlanningError):
            plan_two_terminal_net(intent, _noninline_snapshot())

    def test_hard_limits_reject_infeasible_candidates(self):
        with self.assertRaises(RoutePlanningError):
            plan_two_terminal_net(
                _noninline_intent(max_bends=1),
                _noninline_snapshot(),
            )
        with self.assertRaises(RoutePlanningError):
            plan_two_terminal_net(
                _intent(max_length=20.0),
                _inline_snapshot(blocked=True),
            )

    def test_width_and_layer_constraints_are_enforced(self):
        plan = plan_two_terminal_net(
            _intent(width=0.8),
            _inline_snapshot(blocked=False),
        )
        self.assertEqual(plan.metrics.resolved_width, 0.8)
        self.assertTrue(all(segment.width == 0.8 for segment in plan.segments))
        with self.assertRaises(RoutePlanningError):
            plan_two_terminal_net(
                _intent(forbidden_layers=(LAYER,)),
                _inline_snapshot(blocked=False),
            )

    def test_intent_models_reject_duplicate_identity(self):
        terminal = TerminalRef("A0", "gate")
        with self.assertRaises(ValueError):
            NetIntent(name="bad", terminals=(terminal, terminal))

        first = _intent()
        second = NetIntent(
            name=first.name,
            terminals=(TerminalRef("B0", "gate"), TerminalRef("B1", "gate")),
        )
        with self.assertRaises(ValueError):
            RouteGroupIntent(name="matched", nets=(first, second))


if __name__ == "__main__":
    unittest.main()
