from math import isclose
from typing import Iterable, Protocol

from matchmaker.physical.models import RoutingObstacle


class PortLike(Protocol):
    center: tuple[float, float]
    orientation: float


def find_straight_route_blockers(
    source_port: PortLike,
    target_port: PortLike,
    obstacles: Iterable[RoutingObstacle],
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

    for obstacle in obstacles:
        obstacle_name = obstacle.display_name
        if obstacle_name in excluded:
            continue

        xmin = obstacle.bbox.xmin - clearance
        ymin = obstacle.bbox.ymin - clearance
        xmax = obstacle.bbox.xmax + clearance
        ymax = obstacle.bbox.ymax + clearance

        if horizontal:
            segment_min, segment_max = sorted((source_x, target_x))
            overlaps_axis = min(segment_max, xmax) - max(segment_min, xmin) > 1e-9
            crosses_other_axis = ymin - 1e-9 <= source_y <= ymax + 1e-9
        else:
            segment_min, segment_max = sorted((source_y, target_y))
            overlaps_axis = min(segment_max, ymax) - max(segment_min, ymin) > 1e-9
            crosses_other_axis = xmin - 1e-9 <= source_x <= xmax + 1e-9

        if overlaps_axis and crosses_other_axis:
            blockers.append(obstacle_name)

    return tuple(blockers)
