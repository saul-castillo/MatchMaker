from dataclasses import dataclass

from matchmaker.physical.models import LayerRef
from matchmaker.routing.plans.route_plan import RoutePlan, RouteSegment


@dataclass(frozen=True)
class CrossNetRouteOverlap:
    first_net: str
    second_net: str
    first_segment: RouteSegment
    second_segment: RouteSegment


@dataclass(frozen=True)
class ViaEnvelopeRouteOverlap:
    via_net: str
    route_net: str
    via_center: tuple[float, float]
    route_segment: RouteSegment


@dataclass(frozen=True)
class ViaEnvelope:
    """Physical footprint occupied by one planned layer transition."""

    net_name: str
    center: tuple[float, float]
    size: tuple[float, float]
    layers: tuple[LayerRef, ...]

    def __post_init__(self) -> None:
        if not self.net_name:
            raise ValueError("via-envelope net_name must be non-empty")
        if len(self.size) != 2 or any(dimension <= 0 for dimension in self.size):
            raise ValueError("via-envelope size must be positive")
        if not self.layers:
            raise ValueError("via-envelope layers must be non-empty")


@dataclass(frozen=True)
class CrossNetViaEnvelopeOverlap:
    first: ViaEnvelope
    second: ViaEnvelope


def _bounds(segment: RouteSegment) -> tuple[float, float, float, float]:
    half = segment.width / 2.0
    return (
        min(segment.start[0], segment.end[0]) - half,
        min(segment.start[1], segment.end[1]) - half,
        max(segment.start[0], segment.end[0]) + half,
        max(segment.start[1], segment.end[1]) + half,
    )


def _touch_or_overlap(first: RouteSegment, second: RouteSegment) -> bool:
    if first.layer != second.layer:
        return False
    first_xmin, first_ymin, first_xmax, first_ymax = _bounds(first)
    second_xmin, second_ymin, second_xmax, second_ymax = _bounds(second)
    return (
        max(first_xmin, second_xmin) <= min(first_xmax, second_xmax)
        and max(first_ymin, second_ymin) <= min(first_ymax, second_ymax)
    )


def _rectangle_touch_or_overlap(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> bool:
    return (
        max(first[0], second[0]) <= min(first[2], second[2])
        and max(first[1], second[1]) <= min(first[3], second[3])
    )


def _via_bounds(via: ViaEnvelope) -> tuple[float, float, float, float]:
    width, height = via.size
    return (
        float(via.center[0]) - width / 2.0,
        float(via.center[1]) - height / 2.0,
        float(via.center[0]) + width / 2.0,
        float(via.center[1]) + height / 2.0,
    )


def find_cross_net_route_overlaps(
    plans: tuple[RoutePlan, ...],
) -> tuple[CrossNetRouteOverlap, ...]:
    overlaps: list[CrossNetRouteOverlap] = []
    for first_index, first_plan in enumerate(plans):
        for second_plan in plans[first_index + 1 :]:
            if first_plan.net_name == second_plan.net_name:
                continue
            for first_segment in first_plan.segments:
                for second_segment in second_plan.segments:
                    if _touch_or_overlap(first_segment, second_segment):
                        overlaps.append(
                            CrossNetRouteOverlap(
                                first_net=first_plan.net_name,
                                second_net=second_plan.net_name,
                                first_segment=first_segment,
                                second_segment=second_segment,
                            )
                        )
    return tuple(overlaps)


def require_no_cross_net_route_overlaps(plans: tuple[RoutePlan, ...]) -> None:
    overlaps = find_cross_net_route_overlaps(plans)
    if not overlaps:
        return
    first = overlaps[0]
    raise RuntimeError(
        "different nets overlap on one routing layer: "
        f"{first.first_net} {first.first_segment} vs "
        f"{first.second_net} {first.second_segment}"
    )


def find_cross_net_via_envelope_overlaps(
    envelopes: tuple[ViaEnvelope, ...],
) -> tuple[CrossNetViaEnvelopeOverlap, ...]:
    overlaps: list[CrossNetViaEnvelopeOverlap] = []
    for first_index, first in enumerate(envelopes):
        for second in envelopes[first_index + 1 :]:
            if first.net_name == second.net_name:
                continue
            if not set(first.layers) & set(second.layers):
                continue
            if _rectangle_touch_or_overlap(
                _via_bounds(first),
                _via_bounds(second),
            ):
                overlaps.append(
                    CrossNetViaEnvelopeOverlap(first=first, second=second)
                )
    return tuple(overlaps)


def require_no_cross_net_via_envelope_overlaps(
    envelopes: tuple[ViaEnvelope, ...],
) -> None:
    overlaps = find_cross_net_via_envelope_overlaps(envelopes)
    if not overlaps:
        return
    first = overlaps[0]
    raise RuntimeError(
        "different nets have touching via envelopes: "
        f"{first.first.net_name} at {first.first.center} vs "
        f"{first.second.net_name} at {first.second.center}"
    )


def find_via_envelope_route_overlaps(
    *,
    via_net: str,
    via_centers: tuple[tuple[float, float], ...],
    via_size: tuple[float, float],
    layer,
    plans: tuple[RoutePlan, ...],
) -> tuple[ViaEnvelopeRouteOverlap, ...]:
    """Find other-net route rectangles touched by physical via envelopes."""

    via_width, via_height = via_size
    if via_width <= 0 or via_height <= 0:
        raise ValueError("via envelope size must be positive")
    overlaps: list[ViaEnvelopeRouteOverlap] = []
    for center in via_centers:
        via_bounds = (
            float(center[0]) - via_width / 2.0,
            float(center[1]) - via_height / 2.0,
            float(center[0]) + via_width / 2.0,
            float(center[1]) + via_height / 2.0,
        )
        for plan in plans:
            if plan.net_name == via_net:
                continue
            for segment in plan.segments:
                if segment.layer != layer:
                    continue
                segment_bounds = _bounds(segment)
                if _rectangle_touch_or_overlap(via_bounds, segment_bounds):
                    overlaps.append(
                        ViaEnvelopeRouteOverlap(
                            via_net=via_net,
                            route_net=plan.net_name,
                            via_center=(float(center[0]), float(center[1])),
                            route_segment=segment,
                        )
                    )
    return tuple(overlaps)


def require_via_envelopes_clear_routes(
    *,
    via_net: str,
    via_centers: tuple[tuple[float, float], ...],
    via_size: tuple[float, float],
    layer,
    plans: tuple[RoutePlan, ...],
) -> None:
    overlaps = find_via_envelope_route_overlaps(
        via_net=via_net,
        via_centers=via_centers,
        via_size=via_size,
        layer=layer,
        plans=plans,
    )
    if not overlaps:
        return
    first = overlaps[0]
    raise RuntimeError(
        f"{first.via_net} via envelope at {first.via_center} touches "
        f"{first.route_net} {first.route_segment} on layer {layer!r}"
    )
