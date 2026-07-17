from math import isclose

from matchmaker.physical.models import AccessPoint, PhysicalDesignSnapshot
from matchmaker.routing.intents.net_intent import NetIntent
from matchmaker.routing.planners.rectilinear_path import (
    normalized_access_orientation,
    source_launch_matches,
    target_arrival_matches,
)
from matchmaker.routing.planners.rectilinear_path import find_rectilinear_path_blockers
from matchmaker.routing.planners.route_candidate import (
    CandidateRejection,
    Point,
    RouteCandidate,
    build_route_candidate,
    resolve_pair_width,
)


def _axis(access: AccessPoint) -> str:
    return "horizontal" if normalized_access_orientation(access) in {0, 180} else "vertical"


def _is_inline(source: AccessPoint, target: AccessPoint) -> bool:
    return isclose(source.center[0], target.center[0], abs_tol=1e-9) or isclose(
        source.center[1], target.center[1], abs_tol=1e-9
    )


def _channel_coordinates(
    *,
    axis: str,
    source: AccessPoint,
    target: AccessPoint,
    physical_design: PhysicalDesignSnapshot,
    intent: NetIntent,
) -> tuple[float, ...]:
    source_coordinate = float(source.center[0] if axis == "x" else source.center[1])
    target_coordinate = float(target.center[0] if axis == "x" else target.center[1])
    width = resolve_pair_width(intent, source, target)
    margin = max(float(intent.constraints.obstacle_clearance), width / 2.0, 0.5)
    coordinates = {(source_coordinate + target_coordinate) / 2.0}

    excluded = {
        source.terminal.instance_name,
        target.terminal.instance_name,
    }
    relevant_obstacles = tuple(
        obstacle
        for obstacle in physical_design.obstacles + physical_design.keepouts
        if obstacle.display_name not in excluded
    )
    for obstacle in relevant_obstacles:
        lower = obstacle.bbox.xmin if axis == "x" else obstacle.bbox.ymin
        upper = obstacle.bbox.xmax if axis == "x" else obstacle.bbox.ymax
        coordinates.add(float(lower) - margin)
        coordinates.add(float(upper) + margin)

    all_obstacles = physical_design.obstacles + physical_design.keepouts
    if all_obstacles:
        global_lower = min(
            obstacle.bbox.xmin if axis == "x" else obstacle.bbox.ymin
            for obstacle in all_obstacles
        )
        global_upper = max(
            obstacle.bbox.xmax if axis == "x" else obstacle.bbox.ymax
            for obstacle in all_obstacles
        )
        coordinates.add(float(global_lower) - margin)
        coordinates.add(float(global_upper) + margin)

    coordinates.add(min(source_coordinate, target_coordinate) - margin)
    coordinates.add(max(source_coordinate, target_coordinate) + margin)
    return tuple(sorted(coordinates))


def _candidate_points(
    *,
    source: AccessPoint,
    target: AccessPoint,
    physical_design: PhysicalDesignSnapshot,
    intent: NetIntent,
) -> tuple[tuple[str, tuple[Point, ...]], ...]:
    source_point = tuple(map(float, source.center))
    target_point = tuple(map(float, target.center))
    source_axis = _axis(source)
    target_axis = _axis(target)
    drafts: list[tuple[str, tuple[Point, ...]]] = []

    if source_axis != target_axis:
        drafts.extend(
            (
                (
                    "L-horizontal-first",
                    (
                        source_point,
                        (target_point[0], source_point[1]),
                        target_point,
                    ),
                ),
                (
                    "L-vertical-first",
                    (
                        source_point,
                        (source_point[0], target_point[1]),
                        target_point,
                    ),
                ),
            )
        )
    elif source_axis == "horizontal":
        for coordinate in _channel_coordinates(
            axis="x",
            source=source,
            target=target,
            physical_design=physical_design,
            intent=intent,
        ):
            drafts.append(
                (
                    "Z-vertical-channel",
                    (
                        source_point,
                        (coordinate, source_point[1]),
                        (coordinate, target_point[1]),
                        target_point,
                    ),
                )
            )
    else:
        for coordinate in _channel_coordinates(
            axis="y",
            source=source,
            target=target,
            physical_design=physical_design,
            intent=intent,
        ):
            drafts.append(
                (
                    "Z-horizontal-channel",
                    (
                        source_point,
                        (source_point[0], coordinate),
                        (target_point[0], coordinate),
                        target_point,
                    ),
                )
            )

    unique: dict[tuple[Point, ...], str] = {}
    for topology, points in drafts:
        if any(first == second for first, second in zip(points, points[1:])):
            continue
        unique.setdefault(points, topology)
    return tuple((topology, points) for points, topology in unique.items())


def plan_manhattan_candidates(
    *,
    intent: NetIntent,
    physical_design: PhysicalDesignSnapshot,
    source: AccessPoint,
    target: AccessPoint,
) -> tuple[tuple[RouteCandidate, ...], tuple[CandidateRejection, ...]]:
    """Generate clear same-layer non-inline L/Z candidates for one access pair."""
    if _is_inline(source, target):
        return (), (
            CandidateRejection(
                strategy="manhattan",
                reason="inline-reserved-for-straight-or-dogleg",
                source_access_name=source.name,
                target_access_name=target.name,
            ),
        )

    candidates: list[RouteCandidate] = []
    rejections: list[CandidateRejection] = []
    excluded = (
        source.terminal.instance_name,
        target.terminal.instance_name,
    )

    drafts = _candidate_points(
        source=source,
        target=target,
        physical_design=physical_design,
        intent=intent,
    )
    if not drafts:
        return (), (
            CandidateRejection(
                strategy="manhattan",
                reason="no-rectilinear-topology",
                source_access_name=source.name,
                target_access_name=target.name,
            ),
        )

    for topology, points in drafts:
        if not source_launch_matches(source, points[1]) or not target_arrival_matches(
            target, points[-2]
        ):
            rejections.append(
                CandidateRejection(
                    strategy="manhattan",
                    reason="endpoint-orientation",
                    source_access_name=source.name,
                    target_access_name=target.name,
                    detail=topology,
                )
            )
            continue

        blockers = find_rectilinear_path_blockers(
            points=points,
            obstacles=physical_design.obstacles + physical_design.keepouts,
            excluded_instance_names=excluded,
            clearance=float(intent.constraints.obstacle_clearance),
        )
        if intent.constraints.avoid_obstacles and blockers:
            rejections.append(
                CandidateRejection(
                    strategy="manhattan",
                    reason="blocked",
                    source_access_name=source.name,
                    target_access_name=target.name,
                    detail=f"{topology}: {', '.join(blockers)}",
                )
            )
            continue

        candidates.append(
            build_route_candidate(
                intent=intent,
                source=source,
                target=target,
                strategy="manhattan",
                points=points,
                blockers=() if intent.constraints.avoid_obstacles else blockers,
                provenance=(
                    "manhattan-route strategy",
                    topology,
                    "outward-compatible endpoint access",
                    "full polyline obstacle check",
                ),
            )
        )

    return tuple(candidates), tuple(rejections)
