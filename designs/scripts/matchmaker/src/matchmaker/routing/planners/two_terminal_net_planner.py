from matchmaker.physical.models import PhysicalDesignSnapshot
from matchmaker.routing.intents.net_intent import NetIntent
from matchmaker.routing.planners.two_terminal_access_selector import (
    AccessSelection,
    select_two_terminal_access,
)
from matchmaker.routing.plans.route_plan import (
    ConstraintCheck,
    RouteMetrics,
    RoutePlan,
    RouteSegment,
)


def _route_points(selection: AccessSelection) -> tuple[tuple[float, float], ...]:
    if selection.strategy == "straight":
        return (selection.source.center, selection.target.center)

    if (
        selection.source_bend is None
        or selection.target_bend is None
        or selection.channel_direction is None
        or selection.channel_coordinate is None
    ):
        raise RuntimeError("dogleg access selection is missing channel geometry")

    if selection.channel_direction in {"N", "S"}:
        return (
            selection.source.center,
            selection.source_bend,
            (selection.source_bend[0], selection.channel_coordinate),
            (selection.target_bend[0], selection.channel_coordinate),
            selection.target_bend,
            selection.target.center,
        )
    return (
        selection.source.center,
        selection.source_bend,
        (selection.channel_coordinate, selection.source_bend[1]),
        (selection.channel_coordinate, selection.target_bend[1]),
        selection.target_bend,
        selection.target.center,
    )


def _resolve_width(intent: NetIntent, selection: AccessSelection) -> float:
    if intent.constraints.width is not None:
        return float(intent.constraints.width)
    return min(float(selection.source.width), float(selection.target.width))


def plan_two_terminal_net(
    intent: NetIntent,
    physical_design: PhysicalDesignSnapshot,
) -> RoutePlan:
    """Compile one two-terminal logical net into an execution-ready plan."""
    if len(intent.terminals) != 2:
        raise ValueError("plan_two_terminal_net requires exactly two terminals")

    selection = select_two_terminal_access(intent, physical_design)
    width = _resolve_width(intent, selection)
    points = _route_points(selection)
    segments = tuple(
        RouteSegment(
            start=first,
            end=second,
            layer=selection.source.layer,
            width=width,
        )
        for first, second in zip(points, points[1:])
        if first != second
    )
    metrics = RouteMetrics.from_geometry(
        segments=segments,
        vias=(),
        estimated_cost=selection.estimated_cost,
        resolved_width=width,
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
            passed=(
                not constraints.avoid_obstacles
                or selection.strategy == "dogleg"
                or not selection.blockers
            ),
            detail=(
                "blocked direct path rerouted through external channel"
                if selection.blockers
                else "selected direct path has no blockers"
            ),
        ),
        ConstraintCheck(
            name="maximum-length",
            passed=(
                constraints.max_length is None
                or metrics.total_length <= constraints.max_length + 1e-9
            ),
            detail=(
                f"length={metrics.total_length}; limit={constraints.max_length}"
            ),
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

    return RoutePlan(
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
            *selection.provenance,
            "two-terminal route-plan compilation",
        ),
        channel_direction=selection.channel_direction,
        channel_coordinate=selection.channel_coordinate,
    )
