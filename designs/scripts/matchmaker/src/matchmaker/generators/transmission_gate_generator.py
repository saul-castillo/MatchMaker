from dataclasses import dataclass

from matchmaker.design.transmission_gate_naming import (
    NMOS_INSTANCE_NAME,
    PMOS_INSTANCE_NAME,
)
from matchmaker.physical.gf180_mos_access import gf180_mos_external_port_name
from matchmaker.physical.models import PhysicalDesignSnapshot
from matchmaker.physical.transmission_gate_snapshot import (
    create_transmission_gate_device_snapshot,
)
from matchmaker.placement.cdac.transmission_gate_builder import (
    build_transmission_gate_device_placement,
)
from matchmaker.placement.cdac.transmission_gate_intent import (
    TransmissionGateLayoutIntent,
)
from matchmaker.placement.core.placement_result import PlacementResult
from matchmaker.routing.planners.transmission_gate_topology_planner import (
    TransmissionGateRouteBundle,
    plan_transmission_gate_signal_topology,
)
from matchmaker.routing.routers.route_plan_executor import (
    ExecutedRoutePlan,
    execute_route_plan,
)


@dataclass(frozen=True)
class GeneratedTransmissionGate:
    intent: TransmissionGateLayoutIntent
    placement: PlacementResult
    physical_design: PhysicalDesignSnapshot
    routes: TransmissionGateRouteBundle
    executed_routes: tuple[ExecutedRoutePlan, ...]
    public_port_names: tuple[str, ...]

    @property
    def component(self):
        return self.placement.component


def _copy_component_port(component, *, new_name: str, source_name: str) -> None:
    if new_name in component.ports:
        return
    source_port = component.ports[source_name]
    try:
        component.add_port(name=new_name, port=source_port)
    except TypeError:
        component.add_port(
            name=new_name,
            center=tuple(map(float, source_port.center)),
            width=float(source_port.width),
            orientation=float(source_port.orientation),
            layer=source_port.layer,
        )


def _promoted_access_name(
    instance_name: str,
    terminal_name: str,
    direction: str,
) -> str:
    return (
        f"{instance_name}__"
        f"{gf180_mos_external_port_name(terminal_name, direction)}"
    )


def _promote_public_ports(
    *,
    intent: TransmissionGateLayoutIntent,
    component,
) -> tuple[str, ...]:
    left_instance = (
        NMOS_INSTANCE_NAME
        if intent.policy.nmos_side == "left"
        else PMOS_INSTANCE_NAME
    )
    right_instance = (
        PMOS_INSTANCE_NAME
        if intent.policy.nmos_side == "left"
        else NMOS_INSTANCE_NAME
    )
    public_ports: list[str] = []

    for direction in intent.policy.external_directions:
        side_instance = left_instance if direction == "W" else right_instance
        for logical_name, terminal_name in (
            ("input", intent.policy.input_device_terminal),
            ("output", intent.policy.output_device_terminal),
        ):
            public_name = f"{logical_name}_{direction}"
            _copy_component_port(
                component,
                new_name=public_name,
                source_name=_promoted_access_name(
                    side_instance,
                    terminal_name,
                    direction,
                ),
            )
            public_ports.append(public_name)

        for logical_name, instance_name in (
            ("control", NMOS_INSTANCE_NAME),
            ("control_bar", PMOS_INSTANCE_NAME),
        ):
            public_name = f"{logical_name}_{direction}"
            _copy_component_port(
                component,
                new_name=public_name,
                source_name=_promoted_access_name(
                    instance_name,
                    "gate",
                    direction,
                ),
            )
            public_ports.append(public_name)

    return tuple(public_ports)


def generate_transmission_gate(
    intent: TransmissionGateLayoutIntent,
) -> GeneratedTransmissionGate:
    """Generate one transmission gate from typed intent through route execution.

    Bulk/supply semantics are intentionally excluded until the installed
    primitive's metal tie and substrate-tap exports are identified separately.
    """

    placement = build_transmission_gate_device_placement(intent)
    physical_design = create_transmission_gate_device_snapshot(placement)
    routes = plan_transmission_gate_signal_topology(
        intent=intent,
        physical_design=physical_design,
    )
    executed_routes = tuple(
        execute_route_plan(component=placement.component, plan=plan)
        for plan in routes.plans
    )
    public_ports = _promote_public_ports(
        intent=intent,
        component=placement.component,
    )
    return GeneratedTransmissionGate(
        intent=intent,
        placement=placement,
        physical_design=physical_design,
        routes=routes,
        executed_routes=executed_routes,
        public_port_names=public_ports,
    )
