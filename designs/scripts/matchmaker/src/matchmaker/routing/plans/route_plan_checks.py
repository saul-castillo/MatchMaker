from dataclasses import dataclass

from matchmaker.routing.plans.route_plan import RoutePlan, RouteSegment


@dataclass(frozen=True)
class CrossNetRouteOverlap:
    first_net: str
    second_net: str
    first_segment: RouteSegment
    second_segment: RouteSegment


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
        "different selector nets overlap on one routing layer: "
        f"{first.first_net} {first.first_segment} vs "
        f"{first.second_net} {first.second_segment}"
    )
