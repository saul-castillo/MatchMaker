from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from matchmaker.physical.access_selection import normalized_cardinal_orientation
from matchmaker.physical.models import AccessPoint, BoundingBox
from matchmaker.routing.intents.net_intent import NetIntent
from matchmaker.routing.planners.rectilinear_path import source_launch_matches
from matchmaker.routing.plans.route_plan import (
    ConstraintCheck,
    RouteMetrics,
    RoutePlan,
    RouteSegment,
    ViaPlan,
)
from matchmaker.routing.resources import RoutingLayerTransition


CorridorSide = Literal["west", "east", "south", "north"]
TrunkAxis = Literal["horizontal", "vertical"]
GapSide = Literal["low", "high"]


@dataclass(frozen=True)
class PairCorridorEnvelope:
    """Runtime envelope shared by reusable pair-routing templates."""

    bbox: BoundingBox
    gap_axis: Literal["horizontal", "vertical"]
    gap_low: float
    gap_high: float

    def __post_init__(self) -> None:
        if self.gap_axis not in {"horizontal", "vertical"}:
            raise ValueError("gap_axis must be horizontal or vertical")
        if self.gap_high <= self.gap_low:
            raise ValueError("pair corridor requires a positive inter-child gap")

    @property
    def gap_coordinate(self) -> float:
        return (self.gap_low + self.gap_high) / 2.0

    @property
    def gap_size(self) -> float:
        return self.gap_high - self.gap_low


def envelope_from_bboxes(
    bboxes: Iterable[BoundingBox],
    *,
    gap_axis: Literal["horizontal", "vertical"],
) -> PairCorridorEnvelope:
    boxes = tuple(bboxes)
    if len(boxes) != 2:
        raise ValueError("pair corridor requires exactly two bounding boxes")
    first, second = boxes
    if gap_axis == "vertical":
        low, high = sorted((first, second), key=lambda box: box.ymin)
        gap_low = low.ymax
        gap_high = high.ymin
    elif gap_axis == "horizontal":
        low, high = sorted((first, second), key=lambda box: box.xmin)
        gap_low = low.xmax
        gap_high = high.xmin
    else:
        raise ValueError("gap_axis must be horizontal or vertical")
    return PairCorridorEnvelope(
        bbox=BoundingBox(
            xmin=min(box.xmin for box in boxes),
            ymin=min(box.ymin for box in boxes),
            xmax=max(box.xmax for box in boxes),
            ymax=max(box.ymax for box in boxes),
        ),
        gap_axis=gap_axis,
        gap_low=float(gap_low),
        gap_high=float(gap_high),
    )


def exterior_channel_coordinate(
    *,
    envelope: BoundingBox,
    side: CorridorSide,
    clearance: float,
    width: float,
) -> float:
    """Return a side-channel centerline from a runtime envelope and width."""

    if clearance < 0:
        raise ValueError("exterior-channel clearance must be non-negative")
    if width <= 0:
        raise ValueError("exterior-channel width must be positive")
    if side not in {"west", "east", "south", "north"}:
        raise ValueError(f"unsupported exterior-channel side: {side!r}")
    offset = clearance + width / 2.0
    return {
        "west": envelope.xmin - offset,
        "east": envelope.xmax + offset,
        "south": envelope.ymin - offset,
        "north": envelope.ymax + offset,
    }[side]


def via_center_at_envelope_side(
    *,
    access: AccessPoint,
    envelope: BoundingBox,
    side: CorridorSide,
    via_size: tuple[float, float],
) -> tuple[float, float]:
    """Place a via immediately outside one side of a composite envelope."""

    via_width, via_height = via_size
    if via_width <= 0 or via_height <= 0:
        raise ValueError("via envelope size must be positive")
    if side not in {"west", "east", "south", "north"}:
        raise ValueError(f"unsupported envelope side: {side!r}")
    expected_orientation = {
        "west": 180,
        "east": 0,
        "south": 270,
        "north": 90,
    }[side]
    actual_orientation = normalized_cardinal_orientation(
        access.orientation,
        context=f"envelope-side access {access.name!r}",
    )
    if actual_orientation != expected_orientation:
        raise RuntimeError(
            f"envelope-side via requires {access.name!r} to face {side}"
        )
    center = {
        "west": (envelope.xmin - via_width / 2.0, access.center[1]),
        "east": (envelope.xmax + via_width / 2.0, access.center[1]),
        "south": (access.center[0], envelope.ymin - via_height / 2.0),
        "north": (access.center[0], envelope.ymax + via_height / 2.0),
    }[side]
    if not source_launch_matches(access, center):
        raise RuntimeError(
            f"envelope-side via for {access.name!r} does not launch outward"
        )
    return float(center[0]), float(center[1])


def via_center_at_gap_edge(
    *,
    access: AccessPoint,
    corridor: PairCorridorEnvelope,
    adjacent_side: GapSide,
    via_size: tuple[float, float],
) -> tuple[float, float]:
    """Place a via inside the pair gap next to its adjacent child."""

    via_width, via_height = via_size
    if via_width <= 0 or via_height <= 0:
        raise ValueError("via envelope size must be positive")
    if adjacent_side not in {"low", "high"}:
        raise ValueError(f"unsupported adjacent gap side: {adjacent_side!r}")
    gap_dimension = (
        via_height if corridor.gap_axis == "vertical" else via_width
    )
    if corridor.gap_size < gap_dimension:
        raise RuntimeError(
            "pair gap cannot contain the requested via envelope: "
            f"gap={corridor.gap_size}, via={gap_dimension}"
        )

    if corridor.gap_axis == "vertical":
        expected_orientation = 90 if adjacent_side == "low" else 270
        coordinate = (
            corridor.gap_low + via_height / 2.0
            if adjacent_side == "low"
            else corridor.gap_high - via_height / 2.0
        )
        center = (access.center[0], coordinate)
    else:
        expected_orientation = 0 if adjacent_side == "low" else 180
        coordinate = (
            corridor.gap_low + via_width / 2.0
            if adjacent_side == "low"
            else corridor.gap_high - via_width / 2.0
        )
        center = (coordinate, access.center[1])

    actual_orientation = normalized_cardinal_orientation(
        access.orientation,
        context=f"gap-edge access {access.name!r}",
    )
    if actual_orientation != expected_orientation:
        raise RuntimeError(
            f"gap-edge via requires {access.name!r} to face the pair gap"
        )
    if not source_launch_matches(access, center):
        raise RuntimeError(
            f"gap-edge via for {access.name!r} does not launch toward the gap"
        )
    return float(center[0]), float(center[1])


def _resolved_width(intent: NetIntent, accesses: tuple[AccessPoint, ...]) -> float:
    if intent.constraints.width is not None:
        return float(intent.constraints.width)
    return min(float(access.width) for access in accesses)


def _segments_from_points(
    *,
    points: tuple[tuple[float, float], ...],
    layer,
    width: float,
) -> tuple[RouteSegment, ...]:
    normalized: list[tuple[float, float]] = []
    for point in points:
        converted = (float(point[0]), float(point[1]))
        if not normalized or converted != normalized[-1]:
            normalized.append(converted)
    segments = tuple(
        RouteSegment(start=first, end=second, layer=layer, width=width)
        for first, second in zip(normalized, normalized[1:])
    )
    if not segments:
        raise RuntimeError(f"route points collapsed to zero length: {points!r}")
    return segments


def _route_plan(
    *,
    intent: NetIntent,
    accesses: tuple[AccessPoint, ...],
    strategy: str,
    segments: tuple[RouteSegment, ...],
    vias: tuple[ViaPlan, ...] = (),
    resolved_width: float,
    checks: tuple[ConstraintCheck, ...] = (),
    provenance: tuple[str, ...] = (),
) -> RoutePlan:
    if tuple(access.terminal for access in accesses) != intent.terminals:
        raise RuntimeError("route accesses do not follow NetIntent terminal order")
    metrics = RouteMetrics.from_geometry(
        segments=segments,
        vias=vias,
        estimated_cost=sum(segment.length for segment in segments),
        resolved_width=resolved_width,
    )
    return RoutePlan(
        net_name=intent.name,
        terminals=intent.terminals,
        selected_access_point_names=tuple(access.name for access in accesses),
        strategy=strategy,
        segments=segments,
        vias=vias,
        metrics=metrics,
        constraint_checks=checks,
        provenance=(
            "NetIntent",
            "runtime AccessPoint geometry",
            "reusable corridor-route planner",
            *provenance,
        ),
    )


def plan_external_side_bus(
    *,
    intent: NetIntent,
    first: AccessPoint,
    second: AccessPoint,
    envelope: BoundingBox,
    side: CorridorSide,
    clearance: float,
) -> RoutePlan:
    """Connect two outward-facing accesses through one exterior side channel."""

    if len(intent.terminals) != 2:
        raise ValueError("external side bus requires exactly two terminals")
    if clearance < 0:
        raise ValueError("external side-bus clearance must be non-negative")
    if first.layer != second.layer:
        raise RuntimeError("external side-bus accesses require one common layer")

    accesses = (first, second)
    width = _resolved_width(intent, accesses)
    expected_orientation = {
        "west": 180,
        "east": 0,
        "south": 270,
        "north": 90,
    }[side]
    if any(
        normalized_cardinal_orientation(
            access.orientation,
            context=f"side-bus access {access.name!r}",
        )
        != expected_orientation
        for access in accesses
    ):
        raise RuntimeError(
            f"external {side} side bus requires both accesses to face "
            f"{expected_orientation} degrees"
        )

    coordinate = exterior_channel_coordinate(
        envelope=envelope,
        side=side,
        clearance=clearance,
        width=width,
    )
    if side == "west":
        points = (
            first.center,
            (coordinate, first.center[1]),
            (coordinate, second.center[1]),
            second.center,
        )
    elif side == "east":
        points = (
            first.center,
            (coordinate, first.center[1]),
            (coordinate, second.center[1]),
            second.center,
        )
    elif side == "south":
        points = (
            first.center,
            (first.center[0], coordinate),
            (second.center[0], coordinate),
            second.center,
        )
    else:
        points = (
            first.center,
            (first.center[0], coordinate),
            (second.center[0], coordinate),
            second.center,
        )

    segments = _segments_from_points(
        points=points,
        layer=first.layer,
        width=width,
    )
    return _route_plan(
        intent=intent,
        accesses=accesses,
        strategy=f"external_{side}_side_bus",
        segments=segments,
        resolved_width=width,
        checks=(
            ConstraintCheck(
                name="outward_accesses",
                passed=True,
                hard=True,
                detail=f"both accesses face {side}",
            ),
            ConstraintCheck(
                name="outside_runtime_envelope",
                passed=True,
                hard=True,
                detail=f"{side} channel coordinate {coordinate}",
            ),
        ),
        provenance=(f"runtime {side} pair corridor",),
    )


def plan_gap_bridge(
    *,
    intent: NetIntent,
    first: AccessPoint,
    second: AccessPoint,
    axis: Literal["horizontal", "vertical"],
    gap_coordinate: float,
) -> RoutePlan:
    """Connect two accesses through the midline of their separating gap."""

    if len(intent.terminals) != 2:
        raise ValueError("gap bridge requires exactly two terminals")
    if first.layer != second.layer:
        raise RuntimeError("gap-bridge accesses require one common layer")
    accesses = (first, second)
    width = _resolved_width(intent, accesses)

    if axis == "vertical":
        points = (
            first.center,
            (first.center[0], gap_coordinate),
            (second.center[0], gap_coordinate),
            second.center,
        )
    elif axis == "horizontal":
        points = (
            first.center,
            (gap_coordinate, first.center[1]),
            (gap_coordinate, second.center[1]),
            second.center,
        )
    else:
        raise ValueError("gap-bridge axis must be horizontal or vertical")

    normalized_points = tuple(
        point
        for index, point in enumerate(points)
        if index == 0 or point != points[index - 1]
    )
    if not source_launch_matches(first, normalized_points[1]):
        raise RuntimeError("first gap-bridge access does not launch toward the gap")
    if not source_launch_matches(second, normalized_points[-2]):
        raise RuntimeError("second gap-bridge access does not launch toward the gap")

    segments = _segments_from_points(
        points=points,
        layer=first.layer,
        width=width,
    )
    return _route_plan(
        intent=intent,
        accesses=accesses,
        strategy=f"{axis}_gap_bridge",
        segments=segments,
        resolved_width=width,
        checks=(
            ConstraintCheck(
                name="gap_facing_accesses",
                passed=True,
                hard=True,
                detail=f"{axis} gap midline {gap_coordinate}",
            ),
        ),
        provenance=(f"runtime {axis} pair gap",),
    )


def plan_transitioned_trunk_tree(
    *,
    intent: NetIntent,
    accesses: tuple[AccessPoint, ...],
    via_centers: tuple[tuple[float, float], ...],
    transition: RoutingLayerTransition,
    trunk_axis: TrunkAxis,
    trunk_coordinate: float,
) -> RoutePlan:
    """Connect a multi-terminal family on an upper-layer rectilinear trunk."""

    if len(intent.terminals) < 2:
        raise ValueError("transitioned trunk tree requires at least two terminals")
    if len(accesses) != len(intent.terminals):
        raise ValueError("transitioned tree access count must match terminals")
    if len(via_centers) != len(accesses):
        raise ValueError("transitioned tree requires one via per access")
    if trunk_axis not in {"horizontal", "vertical"}:
        raise ValueError("trunk_axis must be horizontal or vertical")
    if any(access.layer != transition.source_layer for access in accesses):
        raise RuntimeError("tree accesses do not match transition source layer")

    source_width = _resolved_width(intent, accesses)
    route_width = max(source_width, transition.minimum_route_width)
    source_segments: list[RouteSegment] = []
    projections: list[tuple[float, float]] = []
    route_segments: list[RouteSegment] = []

    for access, via_center in zip(accesses, via_centers):
        via_center = (float(via_center[0]), float(via_center[1]))
        if via_center == tuple(map(float, access.center)):
            raise RuntimeError("tree via center must escape beyond its access")
        if not source_launch_matches(access, via_center):
            raise RuntimeError(
                f"tree via for {access.name!r} does not follow access orientation"
            )
        source_segments.append(
            RouteSegment(
                start=access.center,
                end=via_center,
                layer=transition.source_layer,
                width=source_width,
            )
        )
        projection = (
            (float(trunk_coordinate), via_center[1])
            if trunk_axis == "vertical"
            else (via_center[0], float(trunk_coordinate))
        )
        projections.append(projection)
        if projection != via_center:
            route_segments.append(
                RouteSegment(
                    start=via_center,
                    end=projection,
                    layer=transition.route_layer,
                    width=route_width,
                )
            )

    if trunk_axis == "vertical":
        trunk_points = tuple(
            (float(trunk_coordinate), coordinate)
            for coordinate in sorted({point[1] for point in projections})
        )
    else:
        trunk_points = tuple(
            (coordinate, float(trunk_coordinate))
            for coordinate in sorted({point[0] for point in projections})
        )
    route_segments.extend(
        RouteSegment(
            start=first,
            end=second,
            layer=transition.route_layer,
            width=route_width,
        )
        for first, second in zip(trunk_points, trunk_points[1:])
        if first != second
    )
    if not route_segments:
        raise RuntimeError("transitioned tree upper-layer geometry collapsed")

    vias = tuple(
        ViaPlan(
            center=center,
            lower_layer=transition.source_layer,
            upper_layer=transition.route_layer,
            via_name=transition.via_name,
        )
        for center in via_centers
    )
    return _route_plan(
        intent=intent,
        accesses=accesses,
        strategy=f"transitioned_{trunk_axis}_trunk_tree",
        segments=tuple((*source_segments, *route_segments)),
        vias=vias,
        resolved_width=route_width,
        checks=(
            ConstraintCheck(
                name="layer_transition",
                passed=True,
                hard=True,
                detail=(
                    f"{transition.source_layer!r} -> "
                    f"{transition.route_layer!r} with {transition.via_name}"
                ),
            ),
            ConstraintCheck(
                name="shared_trunk",
                passed=True,
                hard=True,
                detail=f"{trunk_axis} trunk coordinate {trunk_coordinate}",
            ),
        ),
        provenance=("typed RoutingLayerTransition",),
    )
