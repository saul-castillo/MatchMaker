from dataclasses import dataclass
from math import isclose
from typing import Iterable, Mapping, Protocol


class PortLike(Protocol):
    center: tuple[float, float]
    orientation: float


@dataclass(frozen=True)
class OrthogonalAccessDetour:
    source_top_port_name: str
    target_top_port_name: str
    direction: str
    extension: float


def _split_cardinal_port_name(port_name: str) -> tuple[str, str] | None:
    if "_" not in port_name:
        return None
    terminal_name, suffix = port_name.rsplit("_", 1)
    suffix = suffix.upper()
    if suffix not in {"N", "S", "E", "W"}:
        return None
    return terminal_name, suffix


def _coerce_obstacle(
    value: Mapping[str, object],
) -> tuple[str, tuple[tuple[float, float], tuple[float, float]]]:
    instance_name = str(value["instance_name"])
    raw_bbox = value["bbox"]
    (xmin, ymin), (xmax, ymax) = raw_bbox  # type: ignore[misc]
    return instance_name, (
        (float(xmin), float(ymin)),
        (float(xmax), float(ymax)),
    )


def _orientation_matches(port: PortLike, direction: str) -> bool:
    expected = {"E": 0, "N": 90, "W": 180, "S": 270}[direction]
    return int(round(float(port.orientation))) % 360 == expected


def _strict_interval_overlap(
    first_min: float,
    first_max: float,
    second_min: float,
    second_max: float,
) -> bool:
    return min(first_max, second_max) - max(first_min, second_min) > 1e-9


def _stub_is_clear(
    x: float,
    y0: float,
    y1: float,
    obstacles: tuple[tuple[str, tuple[tuple[float, float], tuple[float, float]]], ...],
) -> bool:
    segment_min, segment_max = sorted((y0, y1))
    for _, ((xmin, ymin), (xmax, ymax)) in obstacles:
        if xmin + 1e-9 < x < xmax - 1e-9 and _strict_interval_overlap(
            segment_min,
            segment_max,
            ymin,
            ymax,
        ):
            return False
    return True


def _horizontal_detour_candidate(
    direction: str,
    source_name: str,
    target_name: str,
    source_port: PortLike,
    target_port: PortLike,
    obstacles: tuple[tuple[str, tuple[tuple[float, float], tuple[float, float]]], ...],
    clearance: float,
    minimum_extension: float,
) -> OrthogonalAccessDetour | None:
    source_x, source_y = map(float, source_port.center)
    target_x, target_y = map(float, target_port.center)
    if not isclose(source_y, target_y, abs_tol=1e-6):
        return None

    span_min, span_max = sorted((source_x, target_x))
    relevant = [
        bbox
        for _, bbox in obstacles
        if _strict_interval_overlap(span_min, span_max, bbox[0][0], bbox[1][0])
    ]

    if direction == "N":
        boundary = max([source_y, target_y] + [bbox[1][1] for bbox in relevant])
        channel_coordinate = boundary + clearance
        extension = max(minimum_extension, channel_coordinate - source_y)
    else:
        boundary = min([source_y, target_y] + [bbox[0][1] for bbox in relevant])
        channel_coordinate = boundary - clearance
        extension = max(minimum_extension, source_y - channel_coordinate)

    if not _stub_is_clear(source_x, source_y, channel_coordinate, obstacles):
        return None
    if not _stub_is_clear(target_x, target_y, channel_coordinate, obstacles):
        return None

    return OrthogonalAccessDetour(
        source_top_port_name=source_name,
        target_top_port_name=target_name,
        direction=direction,
        extension=extension,
    )


def _vertical_detour_candidate(
    direction: str,
    source_name: str,
    target_name: str,
    source_port: PortLike,
    target_port: PortLike,
    obstacles: tuple[tuple[str, tuple[tuple[float, float], tuple[float, float]]], ...],
    clearance: float,
    minimum_extension: float,
) -> OrthogonalAccessDetour | None:
    source_x, source_y = map(float, source_port.center)
    target_x, target_y = map(float, target_port.center)
    if not isclose(source_x, target_x, abs_tol=1e-6):
        return None

    span_min, span_max = sorted((source_y, target_y))
    relevant = [
        bbox
        for _, bbox in obstacles
        if _strict_interval_overlap(span_min, span_max, bbox[0][1], bbox[1][1])
    ]

    if direction == "E":
        boundary = max([source_x, target_x] + [bbox[1][0] for bbox in relevant])
        channel_coordinate = boundary + clearance
        extension = max(minimum_extension, channel_coordinate - source_x)
    else:
        boundary = min([source_x, target_x] + [bbox[0][0] for bbox in relevant])
        channel_coordinate = boundary - clearance
        extension = max(minimum_extension, source_x - channel_coordinate)

    # Rotate the same stub-clearance calculation into x/y-swapped coordinates.
    swapped_obstacles = tuple(
        (name, ((ymin, xmin), (ymax, xmax)))
        for name, ((xmin, ymin), (xmax, ymax)) in obstacles
    )
    if not _stub_is_clear(source_y, source_x, channel_coordinate, swapped_obstacles):
        return None
    if not _stub_is_clear(target_y, target_x, channel_coordinate, swapped_obstacles):
        return None

    return OrthogonalAccessDetour(
        source_top_port_name=source_name,
        target_top_port_name=target_name,
        direction=direction,
        extension=extension,
    )


def choose_orthogonal_access_detour(
    ports,
    source_instance_name: str,
    source_port_name: str,
    target_instance_name: str,
    target_port_name: str,
    source_port: PortLike,
    target_port: PortLike,
    obstacles: Iterable[Mapping[str, object]],
    separator: str = "__",
    clearance: float = 1.0,
    minimum_extension: float = 0.5,
) -> OrthogonalAccessDetour:
    """Choose equivalent cardinal terminal ports for a safe spatial detour.

    A blocked E/W access pair is rerouted through N or S access ports. A blocked
    N/S pair is rerouted through E or W access ports. The chosen channel lies
    beyond all non-endpoint obstacle bounds in the route span.
    """
    if clearance < 0:
        raise ValueError("clearance must be non-negative")
    if minimum_extension <= 0:
        raise ValueError("minimum_extension must be positive")

    source_split = _split_cardinal_port_name(source_port_name)
    target_split = _split_cardinal_port_name(target_port_name)
    if source_split is None or target_split is None:
        raise RuntimeError(
            "Blocked route endpoints do not use cardinal terminal-port names"
        )

    source_terminal, _ = source_split
    target_terminal, _ = target_split
    source_x, source_y = map(float, source_port.center)
    target_x, target_y = map(float, target_port.center)

    if isclose(source_y, target_y, abs_tol=1e-6):
        candidate_directions = ("N", "S")
        candidate_builder = _horizontal_detour_candidate
    elif isclose(source_x, target_x, abs_tol=1e-6):
        candidate_directions = ("E", "W")
        candidate_builder = _vertical_detour_candidate
    else:
        raise RuntimeError("Obstacle detours currently require inline endpoints")

    excluded = {source_instance_name, target_instance_name}
    usable_obstacles = tuple(
        coerced
        for raw in obstacles
        for coerced in (_coerce_obstacle(raw),)
        if coerced[0] not in excluded
    )

    candidates: list[OrthogonalAccessDetour] = []
    for direction in candidate_directions:
        source_name = (
            f"{source_instance_name}{separator}{source_terminal}_{direction}"
        )
        target_name = (
            f"{target_instance_name}{separator}{target_terminal}_{direction}"
        )
        try:
            candidate_source_port = ports[source_name]
            candidate_target_port = ports[target_name]
        except KeyError:
            continue

        if not _orientation_matches(candidate_source_port, direction):
            continue
        if not _orientation_matches(candidate_target_port, direction):
            continue

        candidate = candidate_builder(
            direction=direction,
            source_name=source_name,
            target_name=target_name,
            source_port=candidate_source_port,
            target_port=candidate_target_port,
            obstacles=usable_obstacles,
            clearance=clearance,
            minimum_extension=minimum_extension,
        )
        if candidate is not None:
            candidates.append(candidate)

    if not candidates:
        raise RuntimeError(
            "No clear orthogonal terminal-access detour exists for the blocked route"
        )

    direction_order = {direction: index for index, direction in enumerate(candidate_directions)}
    return min(
        candidates,
        key=lambda candidate: (
            candidate.extension,
            direction_order[candidate.direction],
        ),
    )
