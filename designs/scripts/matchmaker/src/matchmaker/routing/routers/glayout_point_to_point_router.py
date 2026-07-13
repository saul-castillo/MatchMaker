from dataclasses import dataclass
from typing import Iterable

from matchmaker.routing.intents.point_to_point_route_intent import (
    PointToPointRouteIntent,
)
from matchmaker.routing.planners.obstacle_aware_route_planner import (
    apply_obstacle_avoidance,
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


def route_point_to_point_intent(
    component,
    pdk,
    intent: PointToPointRouteIntent,
    separator: str = "__",
) -> ExecutedRoute:
    source_top_port_name = intent.source.top_port_name(separator)
    target_top_port_name = intent.target.top_port_name(separator)

    try:
        source_port = component.ports[source_top_port_name]
    except KeyError as error:
        raise KeyError(f"Unknown routing source port: {source_top_port_name}") from error

    try:
        target_port = component.ports[target_top_port_name]
    except KeyError as error:
        raise KeyError(f"Unknown routing target port: {target_top_port_name}") from error

    plan = plan_point_to_point_route(
        intent=intent,
        source_port=source_port,
        target_port=target_port,
        separator=separator,
    )

    blockers: tuple[str, ...] = ()
    if intent.avoid_obstacles:
        plan, blockers = apply_obstacle_avoidance(
            plan=plan,
            source_port=source_port,
            target_port=target_port,
            obstacles=component.info.get("matchmaker_routing_obstacles", ()),
            source_instance_name=intent.source.instance_name,
            target_instance_name=intent.target.instance_name,
            clearance=float(intent.obstacle_clearance),
        )

    route_component = _build_route_component(
        pdk=pdk,
        plan=plan,
        source_port=source_port,
        target_port=target_port,
        route_kwargs=intent.route_kwargs,
    )
    route_reference = component << route_component

    route_log = list(component.info.get("matchmaker_routes", ()))
    route_log.append(
        {
            "net_name": plan.net_name,
            "source": plan.source_top_port_name,
            "target": plan.target_top_port_name,
            "strategy": plan.strategy,
            "blockers": blockers,
        }
    )
    component.info["matchmaker_routes"] = tuple(route_log)

    return ExecutedRoute(
        plan=plan,
        route_reference=route_reference,
        blockers=blockers,
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
