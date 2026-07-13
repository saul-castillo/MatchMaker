from dataclasses import dataclass, replace
from math import isclose
from typing import Iterable, Mapping, Protocol

from matchmaker.routing.planners.point_to_point_route_planner import (
    PointToPointRoutePlan,
)


class PortLike(Protocol):
    center: tuple[float, float]
    orientation: float


@dataclass(frozen=True)
class RoutingObstacle:
    instance_name: str
    bbox: tuple[tuple[float, float], tuple[float, float]]


def _normalized_orientation(port: PortLike) -> int:
    orientation = int(round(float(port.orientation))) % 360
    if orientation not in {0, 90, 180, 270}:
        raise ValueError(
            f"Routing ports must be Manhattan; got orientation={port.orientation!r}"
        )
    return orientation


def _coerce_obstacle(value: RoutingObstacle | Mapping[str, object]) -> RoutingObstacle:
    if isinstance(value, RoutingObstacle):
        return value

    instance_name = str(value["instance_name"])
    raw_bbox = value["bbox"]
    (xmin, ymin), (xmax, ymax) = raw_bbox  # type: ignore[misc]
    return RoutingObstacle(
        instance_name=instance_name,
        bbox=(
            (float(xmin), float(ymin)),
            (float(xmax), float(ymax)),
        ),
    )


def find_straight_route_blockers(
    source_port: PortLike,
    target_port: PortLike,
    obstacles: Iterable[RoutingObstacle | Mapping[str, object]],
    excluded_instance_names: Iterable[str] = (),
    clearance: float = 0.0,
) -> tuple[str, ...]:
    """Return non-endpoint obstacles intersected by an inline route centerline."""
    if clearance < 0:
        raise ValueError("clearance must be non-negative")

    source_x, source_y = map(float, source_port.center)
    target_x, target_y = map(float, target_port.center)
    excluded = set(excluded_instance_names)
    blockers: list[str] = []

    horizontal = isclose(source_y, target_y, abs_tol=1e-9)
    vertical = isclose(source_x, target_x, abs_tol=1e-9)
    if not horizontal and not vertical:
        return ()

    for raw_obstacle in obstacles:
        obstacle = _coerce_obstacle(raw_obstacle)
        if obstacle.instance_name in excluded:
            continue

        (xmin, ymin), (xmax, ymax) = obstacle.bbox
        xmin -= clearance
        ymin -= clearance
        xmax += clearance
        ymax += clearance

        if horizontal:
            segment_min, segment_max = sorted((source_x, target_x))
            overlaps_axis = min(segment_max, xmax) - max(segment_min, xmin) > 1e-9
            crosses_other_axis = ymin - 1e-9 <= source_y <= ymax + 1e-9
        else:
            segment_min, segment_max = sorted((source_y, target_y))
            overlaps_axis = min(segment_max, ymax) - max(segment_min, ymin) > 1e-9
            crosses_other_axis = xmin - 1e-9 <= source_x <= xmax + 1e-9

        if overlaps_axis and crosses_other_axis:
            blockers.append(obstacle.instance_name)

    return tuple(blockers)


def apply_obstacle_avoidance(
    plan: PointToPointRoutePlan,
    source_port: PortLike,
    target_port: PortLike,
    obstacles: Iterable[RoutingObstacle | Mapping[str, object]],
    source_instance_name: str,
    target_instance_name: str,
    clearance: float = 0.0,
) -> tuple[PointToPointRoutePlan, tuple[str, ...]]:
    """
    Replace a blocked straight route with a C detour when the ports face alike.

    Opposite-facing blocked inline ports are rejected rather than routed through
    an obstacle. A later channel router can provide a general dogleg solution.
    """
    if plan.strategy != "straight":
        return plan, ()

    blockers = find_straight_route_blockers(
        source_port=source_port,
        target_port=target_port,
        obstacles=obstacles,
        excluded_instance_names=(source_instance_name, target_instance_name),
        clearance=clearance,
    )
    if not blockers:
        return plan, ()

    source_orientation = _normalized_orientation(source_port)
    target_orientation = _normalized_orientation(target_port)
    if source_orientation != target_orientation:
        joined = ", ".join(blockers)
        raise RuntimeError(
            "Blocked inline route has opposite-facing ports and no safe detour "
            f"family is implemented yet; blockers: {joined}"
        )

    return replace(plan, strategy="c"), blockers
