from math import isclose
from typing import Iterable

from matchmaker.physical.access_selection import normalized_cardinal_orientation
from matchmaker.physical.models import AccessPoint, RoutingObstacle
from matchmaker.routing.planners.route_candidate import Point, RoutePlanningError


_CARDINAL_VECTOR = {
    0: (1, 0),
    90: (0, 1),
    180: (-1, 0),
    270: (0, -1),
}


def normalized_access_orientation(access: AccessPoint) -> int:
    try:
        return normalized_cardinal_orientation(
            access.orientation,
            context=f"Physical access {access.name!r}",
        )
    except ValueError as error:
        raise RoutePlanningError(str(error)) from error


def movement_direction(start: Point, end: Point) -> tuple[int, int]:
    dx = float(end[0]) - float(start[0])
    dy = float(end[1]) - float(start[1])
    if isclose(dx, 0.0, abs_tol=1e-9) and isclose(dy, 0.0, abs_tol=1e-9):
        raise ValueError("movement direction requires distinct points")
    if not isclose(dx, 0.0, abs_tol=1e-9) and not isclose(dy, 0.0, abs_tol=1e-9):
        raise ValueError("movement direction requires a Manhattan segment")
    if not isclose(dx, 0.0, abs_tol=1e-9):
        return (1 if dx > 0 else -1, 0)
    return (0, 1 if dy > 0 else -1)


def source_launch_matches(access: AccessPoint, next_point: Point) -> bool:
    return movement_direction(tuple(map(float, access.center)), next_point) == _CARDINAL_VECTOR[
        normalized_access_orientation(access)
    ]


def target_arrival_matches(access: AccessPoint, previous_point: Point) -> bool:
    return movement_direction(tuple(map(float, access.center)), previous_point) == _CARDINAL_VECTOR[
        normalized_access_orientation(access)
    ]


def _strict_overlap(a0: float, a1: float, b0: float, b1: float) -> bool:
    first_min, first_max = sorted((float(a0), float(a1)))
    second_min, second_max = sorted((float(b0), float(b1)))
    return min(first_max, second_max) - max(first_min, second_min) > 1e-9


def _segment_crosses_expanded_obstacle(
    start: Point,
    end: Point,
    obstacle: RoutingObstacle,
    clearance: float,
) -> bool:
    xmin = obstacle.bbox.xmin - clearance
    ymin = obstacle.bbox.ymin - clearance
    xmax = obstacle.bbox.xmax + clearance
    ymax = obstacle.bbox.ymax + clearance

    if isclose(start[1], end[1], abs_tol=1e-9):
        y = float(start[1])
        return (
            ymin + 1e-9 < y < ymax - 1e-9
            and _strict_overlap(start[0], end[0], xmin, xmax)
        )
    if isclose(start[0], end[0], abs_tol=1e-9):
        x = float(start[0])
        return (
            xmin + 1e-9 < x < xmax - 1e-9
            and _strict_overlap(start[1], end[1], ymin, ymax)
        )
    raise ValueError("obstacle checking requires Manhattan segments")


def find_rectilinear_path_blockers(
    *,
    points: tuple[Point, ...],
    obstacles: Iterable[RoutingObstacle],
    excluded_instance_names: Iterable[str] = (),
    clearance: float = 0.0,
) -> tuple[str, ...]:
    """Return obstacles crossed by any segment of a Manhattan polyline.

    Clearance expands obstacle bounds. A segment exactly on the expanded boundary
    is considered clear, which matches the existing external-channel planner.
    """
    if clearance < 0:
        raise ValueError("clearance must be non-negative")
    if len(points) < 2:
        raise ValueError("a path requires at least two points")

    excluded = set(excluded_instance_names)
    blockers: list[str] = []
    seen: set[str] = set()
    obstacle_tuple = tuple(obstacles)

    for start, end in zip(points, points[1:]):
        if start == end:
            continue
        for obstacle in obstacle_tuple:
            name = obstacle.display_name
            if name in excluded or name in seen:
                continue
            if _segment_crosses_expanded_obstacle(start, end, obstacle, clearance):
                seen.add(name)
                blockers.append(name)

    return tuple(blockers)
