from math import isclose

from matchmaker.physical.models import AccessPoint, PhysicalDesignSnapshot
from matchmaker.routing.intents.net_intent import NetIntent
from matchmaker.routing.planners.rectilinear_path import (
    find_rectilinear_path_blockers,
    source_launch_matches,
    target_arrival_matches,
)
from matchmaker.routing.planners.route_candidate import (
    CandidateRejection,
    Point,
    RouteCandidate,
    build_route_candidate,
)
from matchmaker.routing.planners.spatial_dogleg_planner import choose_spatial_dogleg


def _layer_is_allowed(access: AccessPoint, intent: NetIntent) -> bool:
    constraints = intent.constraints
    if constraints.allowed_layers and access.layer not in constraints.allowed_layers:
        return False
    return access.layer not in constraints.forbidden_layers


def _is_inline(source: AccessPoint, target: AccessPoint) -> bool:
    return isclose(source.center[0], target.center[0], abs_tol=1e-9) or isclose(
        source.center[1], target.center[1], abs_tol=1e-9
    )


def _dogleg_points(
    *,
    source: AccessPoint,
    target: AccessPoint,
    source_bend: Point,
    target_bend: Point,
    direction: str,
    channel_coordinate: float,
) -> tuple[Point, ...]:
    if direction in {"N", "S"}:
        return (
            tuple(map(float, source.center)),
            source_bend,
            (source_bend[0], channel_coordinate),
            (target_bend[0], channel_coordinate),
            target_bend,
            tuple(map(float, target.center)),
        )
    return (
        tuple(map(float, source.center)),
        source_bend,
        (channel_coordinate, source_bend[1]),
        (channel_coordinate, target_bend[1]),
        target_bend,
        tuple(map(float, target.center)),
    )


def plan_dogleg_candidate(
    *,
    intent: NetIntent,
    physical_design: PhysicalDesignSnapshot,
    source: AccessPoint,
    target: AccessPoint,
    force: bool = False,
) -> tuple[RouteCandidate | None, CandidateRejection | None]:
    """Evaluate one aligned access pair as an external spatial dogleg."""
    if not _is_inline(source, target):
        return None, CandidateRejection(
            strategy="dogleg",
            reason="not-inline",
            source_access_name=source.name,
            target_access_name=target.name,
        )

    direct_points = (
        tuple(map(float, source.center)),
        tuple(map(float, target.center)),
    )
    direct_blockers = find_rectilinear_path_blockers(
        points=direct_points,
        obstacles=physical_design.obstacles + physical_design.keepouts,
        excluded_instance_names=(
            source.terminal.instance_name,
            target.terminal.instance_name,
        ),
        clearance=float(intent.constraints.obstacle_clearance),
    )
    if not force and not direct_blockers:
        return None, CandidateRejection(
            strategy="dogleg",
            reason="direct-path-clear",
            source_access_name=source.name,
            target_access_name=target.name,
        )

    try:
        dogleg = choose_spatial_dogleg(
            ports=physical_design.access_points,
            source_instance_name=source.terminal.instance_name,
            source_port_name=source.primitive_port_name,
            target_instance_name=target.terminal.instance_name,
            target_port_name=target.primitive_port_name,
            source_port=source,
            target_port=target,
            obstacles=physical_design.obstacles + physical_design.keepouts,
            clearance=max(float(intent.constraints.obstacle_clearance), 1.0),
        )
    except RuntimeError as error:
        return None, CandidateRejection(
            strategy="dogleg",
            reason="dogleg-unavailable",
            source_access_name=source.name,
            target_access_name=target.name,
            detail=str(error),
        )

    actual_source = physical_design.access_point(dogleg.source_top_port_name)
    actual_target = physical_design.access_point(dogleg.target_top_port_name)
    if actual_source.layer != actual_target.layer:
        return None, CandidateRejection(
            strategy="dogleg",
            reason="layer-transition-required",
            source_access_name=actual_source.name,
            target_access_name=actual_target.name,
        )
    if not _layer_is_allowed(actual_source, intent) or not _layer_is_allowed(
        actual_target, intent
    ):
        return None, CandidateRejection(
            strategy="dogleg",
            reason="layer-forbidden",
            source_access_name=actual_source.name,
            target_access_name=actual_target.name,
        )

    points = _dogleg_points(
        source=actual_source,
        target=actual_target,
        source_bend=tuple(map(float, dogleg.source_bend)),
        target_bend=tuple(map(float, dogleg.target_bend)),
        direction=dogleg.direction,
        channel_coordinate=float(dogleg.channel_coordinate),
    )
    if not source_launch_matches(actual_source, points[1]) or not target_arrival_matches(
        actual_target, points[-2]
    ):
        return None, CandidateRejection(
            strategy="dogleg",
            reason="endpoint-orientation",
            source_access_name=actual_source.name,
            target_access_name=actual_target.name,
        )

    route_blockers = find_rectilinear_path_blockers(
        points=points,
        obstacles=physical_design.obstacles + physical_design.keepouts,
        excluded_instance_names=(
            actual_source.terminal.instance_name,
            actual_target.terminal.instance_name,
        ),
        clearance=float(intent.constraints.obstacle_clearance),
    )
    if intent.constraints.avoid_obstacles and route_blockers:
        return None, CandidateRejection(
            strategy="dogleg",
            reason="dogleg-blocked",
            source_access_name=actual_source.name,
            target_access_name=actual_target.name,
            detail=", ".join(route_blockers),
        )

    return (
        build_route_candidate(
            intent=intent,
            source=actual_source,
            target=actual_target,
            strategy="dogleg",
            points=points,
            blockers=direct_blockers,
            provenance=(
                "dogleg-route strategy",
                "blocked inline candidate" if direct_blockers else "forced dogleg",
                "outward terminal access",
                "external spatial channel",
                "full polyline obstacle check",
            ),
            channel_direction=dogleg.direction,
            channel_coordinate=float(dogleg.channel_coordinate),
        ),
        None,
    )
