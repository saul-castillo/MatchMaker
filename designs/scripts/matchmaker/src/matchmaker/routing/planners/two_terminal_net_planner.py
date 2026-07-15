from dataclasses import dataclass

from matchmaker.physical.models import PhysicalDesignSnapshot
from matchmaker.routing.intents.net_intent import NetIntent
from matchmaker.routing.planners.route_candidate import StrategyDispatchResult
from matchmaker.routing.planners.two_terminal_strategy_dispatcher import (
    dispatch_two_terminal_routes,
)
from matchmaker.routing.plans.route_plan import (
    ConstraintCheck,
    RouteMetrics,
    RoutePlan,
    RouteSegment,
)


@dataclass(frozen=True)
class TwoTerminalPlanningResult:
    plan: RoutePlan
    dispatch: StrategyDispatchResult


def plan_two_terminal_net_with_report(
    intent: NetIntent,
    physical_design: PhysicalDesignSnapshot,
) -> TwoTerminalPlanningResult:
    """Compile one logical two-terminal net and retain strategy evidence."""
    if len(intent.terminals) != 2:
        raise ValueError("plan_two_terminal_net requires exactly two terminals")

    dispatch = dispatch_two_terminal_routes(intent, physical_design)
    selection = dispatch.selected
    segments = tuple(
        RouteSegment(
            start=first,
            end=second,
            layer=selection.source.layer,
            width=selection.resolved_width,
        )
        for first, second in zip(selection.points, selection.points[1:])
    )
    metrics = RouteMetrics.from_geometry(
        segments=segments,
        vias=(),
        estimated_cost=selection.estimated_cost,
        resolved_width=selection.resolved_width,
    )

    constraints = intent.constraints
    checks = (
        ConstraintCheck(
            name="logical-terminal-count",
            passed=len(intent.terminals) == 2,
            detail="current planner slice supports exactly two terminals",
        ),
        ConstraintCheck(
            name="same-layer-access",
            passed=selection.source.layer == selection.target.layer,
            detail=f"selected layer: {selection.source.layer}",
        ),
        ConstraintCheck(
            name="obstacle-avoidance",
            passed=True,
            detail=(
                f"selected {selection.strategy} path avoids direct blockers: "
                + ", ".join(selection.blockers)
                if selection.blockers
                else f"selected {selection.strategy} path is clear"
            ),
        ),
        ConstraintCheck(
            name="maximum-length",
            passed=(
                constraints.max_length is None
                or metrics.total_length <= constraints.max_length + 1e-9
            ),
            detail=f"length={metrics.total_length}; limit={constraints.max_length}",
        ),
        ConstraintCheck(
            name="maximum-bends",
            passed=(
                constraints.max_bends is None
                or metrics.bend_count <= constraints.max_bends
            ),
            detail=f"bends={metrics.bend_count}; limit={constraints.max_bends}",
        ),
    )

    plan = RoutePlan(
        net_name=intent.name,
        terminals=intent.terminals,
        selected_access_point_names=(selection.source.name, selection.target.name),
        strategy=selection.strategy,
        segments=segments,
        vias=(),
        metrics=metrics,
        constraint_checks=checks,
        blockers=selection.blockers,
        provenance=(
            "NetIntent",
            "PhysicalDesignSnapshot",
            "two-terminal strategy dispatcher",
            f"feasible candidates={len(dispatch.candidates)}",
            f"rejected candidates={len(dispatch.rejections)}",
            *selection.provenance,
            "two-terminal route-plan compilation",
        ),
        channel_direction=selection.channel_direction,
        channel_coordinate=selection.channel_coordinate,
    )
    return TwoTerminalPlanningResult(plan=plan, dispatch=dispatch)


def plan_two_terminal_net(
    intent: NetIntent,
    physical_design: PhysicalDesignSnapshot,
) -> RoutePlan:
    """Compatibility API returning only the selected execution-ready plan."""
    return plan_two_terminal_net_with_report(intent, physical_design).plan
