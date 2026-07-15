from dataclasses import dataclass

from gdsfactory.component import Component

from matchmaker.routing.plans.route_plan import RoutePlan, RouteSegment


@dataclass(frozen=True)
class ExecutedRoutePlan:
    plan: RoutePlan
    route_reference: object


def _add_segment_rectangle(component: Component, segment: RouteSegment) -> None:
    half = segment.width / 2.0
    x0, y0 = segment.start
    x1, y1 = segment.end

    if segment.orientation == "horizontal":
        xmin, xmax = sorted((x0, x1))
        points = (
            (xmin - half, y0 - half),
            (xmax + half, y0 - half),
            (xmax + half, y0 + half),
            (xmin - half, y0 + half),
        )
    else:
        ymin, ymax = sorted((y0, y1))
        points = (
            (x0 - half, ymin - half),
            (x0 + half, ymin - half),
            (x0 + half, ymax + half),
            (x0 - half, ymax + half),
        )
    component.add_polygon(points, layer=segment.layer)


def build_route_plan_geometry(plan: RoutePlan) -> Component:
    """Translate an already resolved route plan into physical geometry."""
    if plan.vias:
        raise NotImplementedError(
            "route-plan via execution is not implemented in the current slice"
        )

    route = Component()
    for segment in plan.segments:
        _add_segment_rectangle(route, segment)
    return route


def execute_route_plan(component, plan: RoutePlan) -> ExecutedRoutePlan:
    """Insert route geometry without making access or topology decisions."""
    route_component = build_route_plan_geometry(plan)
    route_reference = component << route_component
    return ExecutedRoutePlan(plan=plan, route_reference=route_reference)
