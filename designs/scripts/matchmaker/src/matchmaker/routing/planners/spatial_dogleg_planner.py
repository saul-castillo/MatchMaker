from dataclasses import dataclass
from math import isclose
from typing import Iterable, Literal, Protocol

from matchmaker.physical.models import RoutingObstacle


class PortLike(Protocol):
    center: tuple[float, float]
    orientation: float


DoglegDirection = Literal["N", "S", "E", "W"]


@dataclass(frozen=True)
class SpatialDoglegPlan:
    source_top_port_name: str
    target_top_port_name: str
    direction: DoglegDirection
    channel_coordinate: float
    source_bend: tuple[float, float]
    target_bend: tuple[float, float]


def _split_cardinal_port_name(port_name: str) -> tuple[str, str] | None:
    if "_" not in port_name:
        return None
    terminal_name, suffix = port_name.rsplit("_", 1)
    suffix = suffix.upper()
    if suffix not in {"N", "S", "E", "W"}:
        return None
    return terminal_name, suffix


def _orientation_matches(port: PortLike, direction: str) -> bool:
    expected = {"E": 0, "N": 90, "W": 180, "S": 270}[direction]
    return int(round(float(port.orientation))) % 360 == expected


def _strict_overlap(a0: float, a1: float, b0: float, b1: float) -> bool:
    first_min, first_max = sorted((a0, a1))
    second_min, second_max = sorted((b0, b1))
    return min(first_max, second_max) - max(first_min, second_min) > 1e-9


def _horizontal_access_is_clear(
    y: float,
    x0: float,
    x1: float,
    obstacles: tuple[RoutingObstacle, ...],
    excluded_names: set[str],
) -> bool:
    for obstacle in obstacles:
        if obstacle.display_name in excluded_names:
            continue
        bbox = obstacle.bbox
        if (
            bbox.ymin - 1e-9 <= y <= bbox.ymax + 1e-9
            and _strict_overlap(x0, x1, bbox.xmin, bbox.xmax)
        ):
            return False
    return True


def _vertical_access_is_clear(
    x: float,
    y0: float,
    y1: float,
    obstacles: tuple[RoutingObstacle, ...],
    excluded_names: set[str],
) -> bool:
    for obstacle in obstacles:
        if obstacle.display_name in excluded_names:
            continue
        bbox = obstacle.bbox
        if (
            bbox.xmin - 1e-9 <= x <= bbox.xmax + 1e-9
            and _strict_overlap(y0, y1, bbox.ymin, bbox.ymax)
        ):
            return False
    return True


def _port(ports, name: str):
    try:
        return ports[name]
    except KeyError as error:
        raise RuntimeError(f"Required dogleg access port is unavailable: {name}") from error


def choose_spatial_dogleg(
    ports,
    source_instance_name: str,
    source_port_name: str,
    target_instance_name: str,
    target_port_name: str,
    source_port: PortLike,
    target_port: PortLike,
    obstacles: Iterable[RoutingObstacle],
    separator: str = "__",
    clearance: float = 1.0,
    minimum_outward_extension: float = 0.5,
) -> SpatialDoglegPlan:
    """Plan a U-shaped route outside the full placed-device envelope."""
    if clearance < 0:
        raise ValueError("clearance must be non-negative")
    if minimum_outward_extension <= 0:
        raise ValueError("minimum_outward_extension must be positive")

    source_split = _split_cardinal_port_name(source_port_name)
    target_split = _split_cardinal_port_name(target_port_name)
    if source_split is None or target_split is None:
        raise RuntimeError("Blocked endpoints do not use cardinal terminal-port names")

    source_terminal, _ = source_split
    target_terminal, _ = target_split
    source_x, source_y = map(float, source_port.center)
    target_x, target_y = map(float, target_port.center)
    obstacle_tuple = tuple(obstacles)
    if not obstacle_tuple:
        raise RuntimeError("Spatial dogleg routing requires placed-obstacle metadata")

    global_xmin = min(obstacle.bbox.xmin for obstacle in obstacle_tuple)
    global_ymin = min(obstacle.bbox.ymin for obstacle in obstacle_tuple)
    global_xmax = max(obstacle.bbox.xmax for obstacle in obstacle_tuple)
    global_ymax = max(obstacle.bbox.ymax for obstacle in obstacle_tuple)
    excluded = {source_instance_name, target_instance_name}

    if isclose(source_y, target_y, abs_tol=1e-6):
        source_is_left = source_x < target_x
        source_direction = "W" if source_is_left else "E"
        target_direction = "E" if source_is_left else "W"
        source_name = (
            f"{source_instance_name}{separator}{source_terminal}_{source_direction}"
        )
        target_name = (
            f"{target_instance_name}{separator}{target_terminal}_{target_direction}"
        )
        actual_source = _port(ports, source_name)
        actual_target = _port(ports, target_name)
        if not _orientation_matches(actual_source, source_direction):
            raise RuntimeError(f"Dogleg source port has wrong orientation: {source_name}")
        if not _orientation_matches(actual_target, target_direction):
            raise RuntimeError(f"Dogleg target port has wrong orientation: {target_name}")

        actual_source_x, actual_source_y = map(float, actual_source.center)
        actual_target_x, actual_target_y = map(float, actual_target.center)
        source_bend_x = (
            min(actual_source_x - minimum_outward_extension, global_xmin - clearance)
            if source_direction == "W"
            else max(actual_source_x + minimum_outward_extension, global_xmax + clearance)
        )
        target_bend_x = (
            min(actual_target_x - minimum_outward_extension, global_xmin - clearance)
            if target_direction == "W"
            else max(actual_target_x + minimum_outward_extension, global_xmax + clearance)
        )
        if not _horizontal_access_is_clear(
            actual_source_y,
            actual_source_x,
            source_bend_x,
            obstacle_tuple,
            excluded,
        ):
            raise RuntimeError("Source terminal cannot reach the outside routing channel")
        if not _horizontal_access_is_clear(
            actual_target_y,
            actual_target_x,
            target_bend_x,
            obstacle_tuple,
            excluded,
        ):
            raise RuntimeError("Target terminal cannot reach the outside routing channel")

        north_channel = global_ymax + clearance
        south_channel = global_ymin - clearance
        north_cost = abs(north_channel - actual_source_y) + abs(
            north_channel - actual_target_y
        )
        south_cost = abs(south_channel - actual_source_y) + abs(
            south_channel - actual_target_y
        )
        direction: DoglegDirection = "N" if north_cost <= south_cost else "S"
        channel = north_channel if direction == "N" else south_channel
        return SpatialDoglegPlan(
            source_top_port_name=source_name,
            target_top_port_name=target_name,
            direction=direction,
            channel_coordinate=channel,
            source_bend=(source_bend_x, actual_source_y),
            target_bend=(target_bend_x, actual_target_y),
        )

    if isclose(source_x, target_x, abs_tol=1e-6):
        source_is_lower = source_y < target_y
        source_direction = "S" if source_is_lower else "N"
        target_direction = "N" if source_is_lower else "S"
        source_name = (
            f"{source_instance_name}{separator}{source_terminal}_{source_direction}"
        )
        target_name = (
            f"{target_instance_name}{separator}{target_terminal}_{target_direction}"
        )
        actual_source = _port(ports, source_name)
        actual_target = _port(ports, target_name)
        if not _orientation_matches(actual_source, source_direction):
            raise RuntimeError(f"Dogleg source port has wrong orientation: {source_name}")
        if not _orientation_matches(actual_target, target_direction):
            raise RuntimeError(f"Dogleg target port has wrong orientation: {target_name}")

        actual_source_x, actual_source_y = map(float, actual_source.center)
        actual_target_x, actual_target_y = map(float, actual_target.center)
        source_bend_y = (
            min(actual_source_y - minimum_outward_extension, global_ymin - clearance)
            if source_direction == "S"
            else max(actual_source_y + minimum_outward_extension, global_ymax + clearance)
        )
        target_bend_y = (
            min(actual_target_y - minimum_outward_extension, global_ymin - clearance)
            if target_direction == "S"
            else max(actual_target_y + minimum_outward_extension, global_ymax + clearance)
        )
        if not _vertical_access_is_clear(
            actual_source_x,
            actual_source_y,
            source_bend_y,
            obstacle_tuple,
            excluded,
        ):
            raise RuntimeError("Source terminal cannot reach the outside routing channel")
        if not _vertical_access_is_clear(
            actual_target_x,
            actual_target_y,
            target_bend_y,
            obstacle_tuple,
            excluded,
        ):
            raise RuntimeError("Target terminal cannot reach the outside routing channel")

        east_channel = global_xmax + clearance
        west_channel = global_xmin - clearance
        east_cost = abs(east_channel - actual_source_x) + abs(
            east_channel - actual_target_x
        )
        west_cost = abs(west_channel - actual_source_x) + abs(
            west_channel - actual_target_x
        )
        direction = "E" if east_cost <= west_cost else "W"
        channel = east_channel if direction == "E" else west_channel
        return SpatialDoglegPlan(
            source_top_port_name=source_name,
            target_top_port_name=target_name,
            direction=direction,
            channel_coordinate=channel,
            source_bend=(actual_source_x, source_bend_y),
            target_bend=(actual_target_x, target_bend_y),
        )

    raise RuntimeError("Spatial dogleg routing currently requires inline endpoints")
