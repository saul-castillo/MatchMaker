from dataclasses import dataclass, field
from math import isclose

from matchmaker.physical.models import LayerRef, TerminalRef


Point = tuple[float, float]


@dataclass(frozen=True)
class RouteSegment:
    start: Point
    end: Point
    layer: LayerRef
    width: float

    def __post_init__(self) -> None:
        start = (float(self.start[0]), float(self.start[1]))
        end = (float(self.end[0]), float(self.end[1]))
        if start == end:
            raise ValueError("route segments must have nonzero length")
        if not (isclose(start[0], end[0]) or isclose(start[1], end[1])):
            raise ValueError("route segments must be Manhattan")
        if self.width <= 0:
            raise ValueError("route segment width must be positive")
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)
        object.__setattr__(self, "width", float(self.width))

    @property
    def length(self) -> float:
        return abs(self.end[0] - self.start[0]) + abs(self.end[1] - self.start[1])

    @property
    def orientation(self) -> str:
        return "vertical" if isclose(self.start[0], self.end[0]) else "horizontal"


@dataclass(frozen=True)
class ViaPlan:
    center: Point
    lower_layer: LayerRef
    upper_layer: LayerRef
    via_name: str = "default"

    def __post_init__(self) -> None:
        if self.lower_layer == self.upper_layer:
            raise ValueError("a via must connect different layers")
        if not self.via_name:
            raise ValueError("via_name must be non-empty")
        object.__setattr__(
            self,
            "center",
            (float(self.center[0]), float(self.center[1])),
        )


@dataclass(frozen=True)
class ConstraintCheck:
    name: str
    passed: bool
    hard: bool = True
    detail: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("constraint-check name must be non-empty")


@dataclass(frozen=True)
class RouteMetrics:
    total_length: float
    bend_count: int
    via_count: int
    estimated_cost: float
    resolved_width: float

    def __post_init__(self) -> None:
        if self.total_length < 0:
            raise ValueError("total_length must be non-negative")
        if self.bend_count < 0:
            raise ValueError("bend_count must be non-negative")
        if self.via_count < 0:
            raise ValueError("via_count must be non-negative")
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost must be non-negative")
        if self.resolved_width <= 0:
            raise ValueError("resolved_width must be positive")

    @classmethod
    def from_geometry(
        cls,
        segments: tuple[RouteSegment, ...],
        vias: tuple[ViaPlan, ...],
        estimated_cost: float,
        resolved_width: float,
    ) -> "RouteMetrics":
        orientations = tuple(segment.orientation for segment in segments)
        bend_count = sum(
            first != second
            for first, second in zip(orientations, orientations[1:])
        )
        return cls(
            total_length=sum(segment.length for segment in segments),
            bend_count=bend_count,
            via_count=len(vias),
            estimated_cost=float(estimated_cost),
            resolved_width=float(resolved_width),
        )


@dataclass(frozen=True)
class RoutePlan:
    """Execution-ready physical plan for one logical net."""

    net_name: str
    terminals: tuple[TerminalRef, ...]
    selected_access_point_names: tuple[str, ...]
    strategy: str
    segments: tuple[RouteSegment, ...]
    vias: tuple[ViaPlan, ...]
    metrics: RouteMetrics
    constraint_checks: tuple[ConstraintCheck, ...]
    blockers: tuple[str, ...] = ()
    provenance: tuple[str, ...] = field(default_factory=tuple)
    channel_direction: str | None = None
    channel_coordinate: float | None = None

    def __post_init__(self) -> None:
        terminals = tuple(self.terminals)
        access_names = tuple(self.selected_access_point_names)
        segments = tuple(self.segments)
        vias = tuple(self.vias)
        checks = tuple(self.constraint_checks)

        if not self.net_name:
            raise ValueError("net_name must be non-empty")
        if len(terminals) < 2:
            raise ValueError("a route plan requires at least two terminals")
        if len(access_names) != len(terminals):
            raise ValueError(
                "selected access-point count must match logical terminal count"
            )
        if any(not name for name in access_names):
            raise ValueError("selected access-point names must be non-empty")
        if not self.strategy:
            raise ValueError("route strategy must be non-empty")
        if not segments:
            raise ValueError("a route plan requires at least one segment")
        failed_hard = [check.name for check in checks if check.hard and not check.passed]
        if failed_hard:
            raise ValueError(
                "route plan contains failed hard constraints: "
                + ", ".join(failed_hard)
            )
        measured_length = sum(segment.length for segment in segments)
        if not isclose(measured_length, self.metrics.total_length, abs_tol=1e-9):
            raise ValueError("route metrics do not match segment total length")
        if len(vias) != self.metrics.via_count:
            raise ValueError("route metrics do not match via count")
        for via in vias:
            for layer in (via.lower_layer, via.upper_layer):
                layer_endpoints = {
                    point
                    for segment in segments
                    if segment.layer == layer
                    for point in (segment.start, segment.end)
                }
                if via.center not in layer_endpoints:
                    raise ValueError(
                        f"via {via.via_name!r} at {via.center!r} is not a "
                        f"segment endpoint on layer {layer!r}"
                    )

        object.__setattr__(self, "terminals", terminals)
        object.__setattr__(self, "selected_access_point_names", access_names)
        object.__setattr__(self, "segments", segments)
        object.__setattr__(self, "vias", vias)
        object.__setattr__(self, "constraint_checks", checks)
        object.__setattr__(self, "blockers", tuple(self.blockers))
        object.__setattr__(self, "provenance", tuple(self.provenance))
