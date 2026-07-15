from dataclasses import dataclass
from math import isclose
from typing import Literal

from matchmaker.physical.models import AccessPoint
from matchmaker.routing.intents.net_intent import NetIntent


Point = tuple[float, float]
RouteStrategy = Literal["straight", "manhattan", "dogleg"]


class RoutePlanningError(RuntimeError):
    """Raised when no route candidate satisfies the logical routing problem."""


@dataclass(frozen=True)
class RouteCandidate:
    """One fully measured, execution-independent two-terminal route candidate."""

    source: AccessPoint
    target: AccessPoint
    strategy: RouteStrategy
    points: tuple[Point, ...]
    resolved_width: float
    blockers: tuple[str, ...]
    estimated_length: float
    bend_count: int
    estimated_cost: float
    provenance: tuple[str, ...] = ()
    channel_direction: str | None = None
    channel_coordinate: float | None = None

    def __post_init__(self) -> None:
        points = tuple((float(x), float(y)) for x, y in self.points)
        if len(points) < 2:
            raise ValueError("a route candidate requires at least two points")
        if points[0] != tuple(map(float, self.source.center)):
            raise ValueError("candidate points must begin at the selected source access")
        if points[-1] != tuple(map(float, self.target.center)):
            raise ValueError("candidate points must end at the selected target access")
        if any(first == second for first, second in zip(points, points[1:])):
            raise ValueError("route candidate contains a zero-length segment")
        for first, second in zip(points, points[1:]):
            if not (
                isclose(first[0], second[0], abs_tol=1e-9)
                or isclose(first[1], second[1], abs_tol=1e-9)
            ):
                raise ValueError("route candidate segments must be Manhattan")
        if self.resolved_width <= 0:
            raise ValueError("resolved route width must be positive")
        measured_length = polyline_length(points)
        if not isclose(measured_length, self.estimated_length, abs_tol=1e-9):
            raise ValueError("candidate length does not match its geometry")
        measured_bends = polyline_bend_count(points)
        if measured_bends != self.bend_count:
            raise ValueError("candidate bend count does not match its geometry")
        if self.estimated_cost < 0:
            raise ValueError("estimated route cost must be non-negative")

        object.__setattr__(self, "points", points)
        object.__setattr__(self, "resolved_width", float(self.resolved_width))
        object.__setattr__(self, "blockers", tuple(self.blockers))
        object.__setattr__(self, "provenance", tuple(self.provenance))

    @property
    def identity_key(self) -> tuple[object, ...]:
        return (
            self.strategy,
            self.source.name,
            self.target.name,
            self.points,
            self.source.layer,
            self.resolved_width,
        )


@dataclass(frozen=True)
class CandidateRejection:
    strategy: str
    reason: str
    source_access_name: str | None = None
    target_access_name: str | None = None
    detail: str = ""

    def __post_init__(self) -> None:
        if not self.strategy:
            raise ValueError("rejection strategy must be non-empty")
        if not self.reason:
            raise ValueError("rejection reason must be non-empty")


@dataclass(frozen=True)
class StrategyDispatchResult:
    selected: RouteCandidate
    candidates: tuple[RouteCandidate, ...]
    rejections: tuple[CandidateRejection, ...]

    def __post_init__(self) -> None:
        candidates = tuple(self.candidates)
        rejections = tuple(self.rejections)
        if self.selected not in candidates:
            raise ValueError("selected candidate must be present in candidates")
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "rejections", rejections)


def polyline_length(points: tuple[Point, ...]) -> float:
    return sum(
        abs(second[0] - first[0]) + abs(second[1] - first[1])
        for first, second in zip(points, points[1:])
    )


def polyline_bend_count(points: tuple[Point, ...]) -> int:
    orientations = tuple(
        "vertical" if isclose(first[0], second[0], abs_tol=1e-9) else "horizontal"
        for first, second in zip(points, points[1:])
    )
    return sum(first != second for first, second in zip(orientations, orientations[1:]))


def resolve_pair_width(intent: NetIntent, source: AccessPoint, target: AccessPoint) -> float:
    if intent.constraints.width is not None:
        return float(intent.constraints.width)
    return min(float(source.width), float(target.width))


def build_route_candidate(
    *,
    intent: NetIntent,
    source: AccessPoint,
    target: AccessPoint,
    strategy: RouteStrategy,
    points: tuple[Point, ...],
    blockers: tuple[str, ...] = (),
    provenance: tuple[str, ...] = (),
    channel_direction: str | None = None,
    channel_coordinate: float | None = None,
) -> RouteCandidate:
    normalized_points = tuple((float(x), float(y)) for x, y in points)
    length = polyline_length(normalized_points)
    bends = polyline_bend_count(normalized_points)
    cost = intent.constraints.length_weight * length + intent.constraints.bend_penalty * bends
    return RouteCandidate(
        source=source,
        target=target,
        strategy=strategy,
        points=normalized_points,
        resolved_width=resolve_pair_width(intent, source, target),
        blockers=tuple(blockers),
        estimated_length=length,
        bend_count=bends,
        estimated_cost=cost,
        provenance=tuple(provenance),
        channel_direction=channel_direction,
        channel_coordinate=channel_coordinate,
    )
