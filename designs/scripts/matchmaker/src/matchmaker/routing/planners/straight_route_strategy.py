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
    RouteCandidate,
    build_route_candidate,
)


def plan_straight_candidate(
    *,
    intent: NetIntent,
    physical_design: PhysicalDesignSnapshot,
    source: AccessPoint,
    target: AccessPoint,
) -> tuple[RouteCandidate | None, CandidateRejection | None]:
    """Evaluate one source/target access pair as a direct Manhattan route."""
    source_name = source.name
    target_name = target.name
    source_point = tuple(map(float, source.center))
    target_point = tuple(map(float, target.center))

    aligned = isclose(source_point[0], target_point[0], abs_tol=1e-9) or isclose(
        source_point[1], target_point[1], abs_tol=1e-9
    )
    if not aligned:
        return None, CandidateRejection(
            strategy="straight",
            reason="not-inline",
            source_access_name=source_name,
            target_access_name=target_name,
        )

    if not source_launch_matches(source, target_point) or not target_arrival_matches(
        target, source_point
    ):
        return None, CandidateRejection(
            strategy="straight",
            reason="endpoint-orientation",
            source_access_name=source_name,
            target_access_name=target_name,
            detail="direct segment does not leave both accesses outward",
        )

    blockers = find_rectilinear_path_blockers(
        points=(source_point, target_point),
        obstacles=physical_design.obstacles + physical_design.keepouts,
        excluded_instance_names=(
            source.terminal.instance_name,
            target.terminal.instance_name,
        ),
        clearance=float(intent.constraints.obstacle_clearance),
    )
    if intent.constraints.avoid_obstacles and blockers:
        return None, CandidateRejection(
            strategy="straight",
            reason="blocked",
            source_access_name=source_name,
            target_access_name=target_name,
            detail=", ".join(blockers),
        )

    return (
        build_route_candidate(
            intent=intent,
            source=source,
            target=target,
            strategy="straight",
            points=(source_point, target_point),
            blockers=() if intent.constraints.avoid_obstacles else blockers,
            provenance=(
                "straight-route strategy",
                "outward-compatible inline access pair",
                "direct path obstacle check",
            ),
        ),
        None,
    )
