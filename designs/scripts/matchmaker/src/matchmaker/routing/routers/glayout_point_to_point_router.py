from dataclasses import dataclass, replace
from typing import Iterable

from matchmaker.physical.models import PhysicalDesignSnapshot
from matchmaker.routing.intents.point_to_point_route_intent import (
    PointToPointRouteIntent,
)
from matchmaker.routing.planners.obstacle_aware_route_planner import (
    find_straight_route_blockers,
)
from matchmaker.routing.planners.point_to_point_route_planner import (
    PointToPointRoutePlan,
    plan_point_to_point_route,
)
from matchmaker.routing.planners.spatial_dogleg_planner import (
    SpatialDoglegPlan,
    choose_spatial_dogleg,
)
from matchmaker.routing.routers.spatial_dogleg_route import (
    build_spatial_dogleg_route,
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
    detour_channel_coordinate: float | None = None


def _build_route_component(
    pdk,
    plan,
    source_port,
    target_port,
    route_kwargs,
    dogleg_plan: SpatialDoglegPlan | None = None,
):
    kwargs = dict(route_kwargs)

    if plan.strategy == "straight":
        return straight_route(pdk, source_port, target_port, **kwargs)
    if plan.strategy == "l":
        return L_route(pdk, source_port, target_port, **kwargs)
    if plan.strategy == "c":
        return c_route(pdk, source_port, target_port, **kwargs)
    if plan.strategy == "smart":
        return smart_route(pdk, source_port, target_port, **kwargs)
    if plan.strategy == "dogleg":
        if dogleg_plan is None:
            raise RuntimeError("Spatial dogleg plan is missing")
        width = kwargs.pop("width", None)
        if kwargs:
            unsupported = ", ".join(sorted(kwargs))
            raise ValueError(
                f"Unsupported spatial dogleg route kwargs: {unsupported}"
            )
        return build_spatial_dogleg_route(
            source_port=source_port,
            target_port=target_port,
            plan=dogleg_plan,
            width=width,
        )

    raise ValueError(f"Unsupported route strategy: {plan.strategy!r}")


def _physical_port(
    component,
    physical_design: PhysicalDesignSnapshot,
    port_name: str,
    endpoint_role: str,
):
    physical_design.access_point(port_name)
    try:
        return component.ports[port_name]
    except KeyError as error:
        raise KeyError(f"Unknown routing {endpoint_role} port: {port_name}") from error


def _validate_snapshot(component, physical_design: PhysicalDesignSnapshot) -> None:
    if physical_design.component is not component:
        raise ValueError(
            "physical_design.component must be the same component passed to the router"
        )


def route_point_to_point_intent(
    component,
    pdk,
    intent: PointToPointRouteIntent,
    physical_design: PhysicalDesignSnapshot,
    separator: str = "__",
) -> ExecutedRoute:
    _validate_snapshot(component, physical_design)

    requested_source_name = intent.source.top_port_name(separator)
    requested_target_name = intent.target.top_port_name(separator)
    source_port = _physical_port(
        component,
        physical_design,
        requested_source_name,
        "source",
    )
    target_port = _physical_port(
        component,
        physical_design,
        requested_target_name,
        "target",
    )

    plan = plan_point_to_point_route(
        intent=intent,
        source_port=source_port,
        target_port=target_port,
        separator=separator,
    )

    blockers: tuple[str, ...] = ()
    dogleg_plan = None

    if intent.avoid_obstacles and plan.strategy == "straight":
        blockers = find_straight_route_blockers(
            source_port=source_port,
            target_port=target_port,
            obstacles=physical_design.obstacles,
            excluded_instance_names=(
                intent.source.instance_name,
                intent.target.instance_name,
            ),
            clearance=float(intent.obstacle_clearance),
        )

        if blockers:
            dogleg_plan = choose_spatial_dogleg(
                ports=component.ports,
                source_instance_name=intent.source.instance_name,
                source_port_name=intent.source.port_name,
                target_instance_name=intent.target.instance_name,
                target_port_name=intent.target.port_name,
                source_port=source_port,
                target_port=target_port,
                obstacles=physical_design.obstacles,
                separator=separator,
                clearance=max(float(intent.obstacle_clearance), 1.0),
            )
            source_port = _physical_port(
                component,
                physical_design,
                dogleg_plan.source_top_port_name,
                "dogleg source",
            )
            target_port = _physical_port(
                component,
                physical_design,
                dogleg_plan.target_top_port_name,
                "dogleg target",
            )
            plan = replace(
                plan,
                source_top_port_name=dogleg_plan.source_top_port_name,
                target_top_port_name=dogleg_plan.target_top_port_name,
                strategy="dogleg",
            )

    route_component = _build_route_component(
        pdk=pdk,
        plan=plan,
        source_port=source_port,
        target_port=target_port,
        route_kwargs=intent.route_kwargs,
        dogleg_plan=dogleg_plan,
    )
    route_reference = component << route_component

    return ExecutedRoute(
        plan=plan,
        route_reference=route_reference,
        blockers=blockers,
        detour_direction=(
            dogleg_plan.direction if dogleg_plan is not None else None
        ),
        detour_channel_coordinate=(
            float(dogleg_plan.channel_coordinate)
            if dogleg_plan is not None
            else None
        ),
    )


def route_point_to_point_intents(
    component,
    pdk,
    intents: Iterable[PointToPointRouteIntent],
    physical_design: PhysicalDesignSnapshot,
    separator: str = "__",
) -> tuple[ExecutedRoute, ...]:
    return tuple(
        route_point_to_point_intent(
            component=component,
            pdk=pdk,
            intent=intent,
            physical_design=physical_design,
            separator=separator,
        )
        for intent in intents
    )
