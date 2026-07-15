from gdsfactory.component import Component

from matchmaker.routing.planners.spatial_dogleg_planner import SpatialDoglegPlan


def _add_horizontal_rectangle(component, x0, x1, y, width, layer) -> None:
    half = width / 2.0
    xmin, xmax = sorted((float(x0), float(x1)))
    component.add_polygon(
        [
            (xmin - half, y - half),
            (xmax + half, y - half),
            (xmax + half, y + half),
            (xmin - half, y + half),
        ],
        layer=layer,
    )


def _add_vertical_rectangle(component, x, y0, y1, width, layer) -> None:
    half = width / 2.0
    ymin, ymax = sorted((float(y0), float(y1)))
    component.add_polygon(
        [
            (x - half, ymin - half),
            (x + half, ymin - half),
            (x + half, ymax + half),
            (x - half, ymax + half),
        ],
        layer=layer,
    )


def build_spatial_dogleg_route(
    source_port,
    target_port,
    plan: SpatialDoglegPlan,
    width: float | None = None,
):
    """Build one same-layer U-shaped Manhattan route from a spatial dogleg plan."""
    if source_port.layer != target_port.layer:
        raise RuntimeError("Spatial dogleg endpoints must be on the same metal layer")

    route_width = float(
        width
        if width is not None
        else min(float(source_port.width), float(target_port.width))
    )
    if route_width <= 0:
        raise ValueError("Spatial dogleg route width must be positive")

    source_x, source_y = map(float, source_port.center)
    target_x, target_y = map(float, target_port.center)
    source_bend_x, source_bend_y = plan.source_bend
    target_bend_x, target_bend_y = plan.target_bend
    layer = source_port.layer
    route = Component()

    if plan.direction in {"N", "S"}:
        channel_y = float(plan.channel_coordinate)
        _add_horizontal_rectangle(
            route, source_x, source_bend_x, source_y, route_width, layer
        )
        _add_vertical_rectangle(
            route, source_bend_x, source_bend_y, channel_y, route_width, layer
        )
        _add_horizontal_rectangle(
            route, source_bend_x, target_bend_x, channel_y, route_width, layer
        )
        _add_vertical_rectangle(
            route, target_bend_x, target_bend_y, channel_y, route_width, layer
        )
        _add_horizontal_rectangle(
            route, target_x, target_bend_x, target_y, route_width, layer
        )
    else:
        channel_x = float(plan.channel_coordinate)
        _add_vertical_rectangle(
            route, source_x, source_y, source_bend_y, route_width, layer
        )
        _add_horizontal_rectangle(
            route, source_bend_x, channel_x, source_bend_y, route_width, layer
        )
        _add_vertical_rectangle(
            route, channel_x, source_bend_y, target_bend_y, route_width, layer
        )
        _add_horizontal_rectangle(
            route, target_bend_x, channel_x, target_bend_y, route_width, layer
        )
        _add_vertical_rectangle(
            route, target_x, target_y, target_bend_y, route_width, layer
        )

    return route
