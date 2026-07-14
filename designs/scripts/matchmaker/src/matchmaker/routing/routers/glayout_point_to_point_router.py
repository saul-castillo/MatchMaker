from dataclasses import dataclass, replace
from typing import Iterable

from matchmaker.routing.intents.point_to_point_route_intent import (
    PointToPointRouteIntent,
)
from matchmaker.routing.planners.obstacle_aware_route_planner import (
    find_straight_route_blockers,
)
from matchmaker.routing.planners.orthogonal_access_detour import (
    choose_orthogonal_access_detour,
)
from matchmaker.routing.planners.point_to_point_route_planner import (
    PointToPointRoutePlan,
    plan_point_to_point_route,
)

try:
    from glayout.routing.L_route import L_route
    from glayout.routing.c_route import c_route
    from glayout.routing.smart_route import smart_route
    from glayout.routing.straight_route import straight_route
except Exception:
    from glayout.flow.routing.L_route import L_route
    from glayout.flow.routing.c_route import c_route
    from glayout.flow.routing.smart_route import smart_route
    from glayout.flow.routing.straight_route import straight_route


@dataclass(frozen=True)
class ExecutedRoute:
    plan: PointToPointRoutePlan
    route_reference: object
    blockers: tuple[str, ...] = ()
    detour_direction: str | None = None
    detour_extension: float | None = None


def _build_route_component(pdk, plan, source_port, target_port, route_kwargs):
    kwargs = dict(route_kwargs)

    if plan.strategy == "straight":
        return straight_route(pdk, source_port, target_port, **kwargs)
    if plan.strategy == "l":
        return L_route(pdk, source_port, target_port, **kwargs)
    if plan.strategy == "c":
        return c_route(pdk, source_port, target_port, **kwargs)
    if plan.strategy == "smart":
        return smart_route(pdk, source_port, target_port, **kwargs)

    raise ValueError(f"Unsupported route strategy: {plan.strategy!r}")


def _port(component, port_name: str, endpoint_role: str):
    try:
        return component.ports[port_name]
    except KeyError as error:
        raise KeyError(f"Unknown routing {endpoint_role} port: {port_name}") from error


def route_point_to_point_intent(
    component,
    pdk,
    intent: PointToPointRouteIntent,
    separator: str = "__",
) -> ExecutedRoute:
    requested_source_name = intent.source.top_port_name(separator)
    requested_target_name = intent.target.top_port_name(separator)
    source_port = _port(component, requested_source_name, "source")
    target_port = _port(component, requested_target_name, "target")

    plan = plan_point_to_point_route(
        intent=intent,
        source_port=source_port,
        target_port=target_port,
        separator=separator,
    )

    obstacles = component.info.get("matchmaker_routing_obstacles", ())
    blockers: tuple[str, ...] = ()
    detour_direction = None
    detour_extension = None
    route_kwargs = dict(intent.route_kwargs)

    if intent.avoid_obstacles and plan.strategy == "straight":
        blockers = find_straight_route_blockers(
            source_port=source_port,
            target_port=target_port,
            obstacles=obstacles,
            excluded_instance_names=(
                intent.source.instance_name,
                intent.target.instance_name,
            ),
            clearance=float(intent.obstacle_clearance),
        )

        if blockers:
            detour = choose_orthogonal_access_detour(
                ports=component.ports,
                source_instance_name=intent.source.instance_name,
                source_port_name=intent.source.port_name,
                target_instance_name=intent.target.instance_name,
                target_port_name=intent.target.port_name,
                source_port=source_port,
                target_port=target_port,
                obstacles=obstacles,
                separator=separator,
                clearance=max(float(intent.obstacle_clearance), 1.0),
            )
            source_port = _port(
                component,
                detour.source_top_port_name,
                "detour source",
            )
            target_port = _port(
                component,
                detour.target_top_port_name,
                "detour target",
            )
            plan = replace(
                plan,
                source_top_port_name=detour.source_top_port_name,
                target_top_port_name=detour.target_top_port_name,
                strategy="c",
            )
            detour_direction = detour.direction
            detour_extension = float(detour.extension)
            requested_extension = route_kwargs.get("extension")
            if requested_extension is None:
                route_kwargs["extension"] = detour_extension
            else:
                route_kwargs["extension"] = max(
                    float(requested_extension),
                    detour_extension,
                )

    route_component = _build_route_component(
        pdk=pdk,
        plan=plan,
        source_port=source_port,
        target_port=target_port,
        route_kwargs=route_kwargs,
    )
    route_reference = component << route_component

    route_log = list(component.info.get("matchmaker_routes", ()))
    route_log.append(
        {
            "net_name": plan.net_name,
            "requested_source": requested_source_name,
            "requested_target": requested_target_name,
            "source": plan.source_top_port_name,
            "target": plan.target_top_port_name,
            "strategy": plan.strategy,
            "blockers": blockers,
            "detour_direction": detour_direction,
            "detour_extension": detour_extension,
        }
    )
    component.info["matchmaker_routes"] = tuple(route_log)

    return ExecutedRoute(
        plan=plan,
        route_reference=route_reference,
        blockers=blockers,
        detour_direction=detour_direction,
        detour_extension=detour_extension,
    )


def route_point_to_point_intents(
    component,
    pdk,
    intents: Iterable[PointToPointRouteIntent],
    separator: str = "__",
) -> tuple[ExecutedRoute, ...]:
    executed_routes = []
    for intent in intents:
        executed_routes.append(
            route_point_to_point_intent(
                component=component,
                pdk=pdk,
                intent=intent,
                separator=separator,
            )
        )
    return tuple(executed_routes)
