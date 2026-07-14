from dataclasses import dataclass
from math import isclose
from typing import Literal, Protocol

from matchmaker.routing.intents.point_to_point_route_intent import (
    PointToPointRouteIntent,
)


class PortLike(Protocol):
    center: tuple[float, float]
    orientation: float


ResolvedRouteStrategy = Literal["straight", "l", "c", "smart", "dogleg"]


@dataclass(frozen=True)
class PointToPointRoutePlan:
    net_name: str
    source_top_port_name: str
    target_top_port_name: str
    strategy: ResolvedRouteStrategy


def _normalized_orientation(port: PortLike) -> int:
    orientation = int(round(float(port.orientation))) % 360
    if orientation not in {0, 90, 180, 270}:
        raise ValueError(
            f"Routing ports must be Manhattan; got orientation={port.orientation!r}"
        )
    return orientation


def _ports_parallel(source_port: PortLike, target_port: PortLike) -> bool:
    source_orientation = _normalized_orientation(source_port)
    target_orientation = _normalized_orientation(target_port)
    return (source_orientation - target_orientation) % 180 == 0


def _ports_inline(source_port: PortLike, target_port: PortLike) -> bool:
    source_orientation = _normalized_orientation(source_port)
    source_x, source_y = map(float, source_port.center)
    target_x, target_y = map(float, target_port.center)

    if source_orientation in {0, 180}:
        return isclose(source_y, target_y, abs_tol=1e-9)

    return isclose(source_x, target_x, abs_tol=1e-9)


def choose_point_to_point_route_strategy(
    source_port: PortLike,
    target_port: PortLike,
) -> ResolvedRouteStrategy:
    """
    Choose the smallest deterministic gLayout route family that fits the ports.

    straight: parallel and inline
    l: perpendicular
    c: parallel, same-facing, and non-inline
    smart: parallel, opposite-facing, and non-inline
    """
    source_orientation = _normalized_orientation(source_port)
    target_orientation = _normalized_orientation(target_port)

    if _ports_parallel(source_port, target_port):
        if _ports_inline(source_port, target_port):
            return "straight"
        if source_orientation == target_orientation:
            return "c"
        return "smart"

    return "l"


def plan_point_to_point_route(
    intent: PointToPointRouteIntent,
    source_port: PortLike,
    target_port: PortLike,
    separator: str = "__",
) -> PointToPointRoutePlan:
    strategy = intent.strategy
    if strategy == "auto":
        strategy = choose_point_to_point_route_strategy(source_port, target_port)

    return PointToPointRoutePlan(
        net_name=intent.net_name,
        source_top_port_name=intent.source.top_port_name(separator),
        target_top_port_name=intent.target.top_port_name(separator),
        strategy=strategy,
    )
