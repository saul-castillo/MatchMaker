from dataclasses import dataclass

from matchmaker.design.reference_selector_naming import (
    VREF_SWITCH_INSTANCE_NAME,
    VSS_SWITCH_INSTANCE_NAME,
)
from matchmaker.generators.transmission_gate_generator import (
    GeneratedTransmissionGate,
    generate_transmission_gate,
)
from matchmaker.physical.models import PhysicalDesignSnapshot
from matchmaker.physical.reference_selector_snapshot import (
    create_reference_selector_child_snapshot,
)
from matchmaker.physical.transmission_gate_cell_access import (
    TransmissionGateCellAccessPolicy,
)
from matchmaker.placement.cdac.reference_selector_builder import (
    build_reference_selector_child_placement,
)
from matchmaker.placement.cdac.reference_selector_intent import (
    ReferenceSelectorLayoutIntent,
)
from matchmaker.placement.cdac.transmission_gate_intent import (
    TransmissionGateLayoutIntent,
)
from matchmaker.placement.core.placement_result import PlacementResult
from matchmaker.routing.planners.reference_selector_topology_planner import (
    ReferenceSelectorRouteBundle,
    plan_reference_selector_topology,
)
from matchmaker.routing.routers.route_plan_executor import (
    ExecutedRoutePlan,
    execute_route_plan,
)


@dataclass(frozen=True)
class GeneratedReferenceSelector:
    intent: ReferenceSelectorLayoutIntent
    vref_switch: GeneratedTransmissionGate
    vss_switch: GeneratedTransmissionGate
    placement: PlacementResult
    physical_design: PhysicalDesignSnapshot
    routes: ReferenceSelectorRouteBundle
    executed_routes: tuple[ExecutedRoutePlan, ...]
    public_port_names: tuple[str, ...]

    @property
    def component(self):
        return self.placement.component


def _copy_component_port(component, *, new_name: str, source_name: str) -> None:
    if new_name in component.ports:
        return
    source = component.ports[source_name]
    try:
        component.add_port(name=new_name, port=source)
    except TypeError:
        component.add_port(
            name=new_name,
            center=tuple(map(float, source.center)),
            width=float(source.width),
            orientation=float(source.orientation),
            layer=source.layer,
        )


def _add_route_midpoint_port(
    component,
    *,
    name: str,
    plan,
    orientation: float,
    segment_orientation: str = "horizontal",
) -> None:
    candidates = tuple(
        segment
        for segment in plan.segments
        if segment.orientation == segment_orientation
    )
    if not candidates:
        raise RuntimeError(
            f"route {plan.net_name!r} has no {segment_orientation} segment"
        )
    segment = max(candidates, key=lambda candidate: candidate.length)
    center = (
        (segment.start[0] + segment.end[0]) / 2.0,
        (segment.start[1] + segment.end[1]) / 2.0,
    )
    component.add_port(
        name=name,
        center=center,
        width=segment.width,
        orientation=orientation,
        layer=segment.layer,
    )


def _promote_selector_ports(
    *,
    placement: PlacementResult,
    routes: ReferenceSelectorRouteBundle,
) -> tuple[str, ...]:
    component = placement.component
    _copy_component_port(
        component,
        new_name="vref_W",
        source_name=f"{VREF_SWITCH_INSTANCE_NAME}__input_W",
    )
    _copy_component_port(
        component,
        new_name="vss_E",
        source_name=f"{VSS_SWITCH_INSTANCE_NAME}__input_E",
    )
    _add_route_midpoint_port(
        component,
        name="common_N",
        plan=routes.common_plan,
        orientation=90.0,
    )
    _add_route_midpoint_port(
        component,
        name="select_N",
        plan=routes.select_plan,
        orientation=90.0,
    )
    _add_route_midpoint_port(
        component,
        name="select_bar_S",
        plan=routes.select_bar_plan,
        orientation=270.0,
        segment_orientation="vertical",
    )
    return ("vref_W", "vss_E", "common_N", "select_N", "select_bar_S")


def generate_reference_selector(
    intent: ReferenceSelectorLayoutIntent,
) -> GeneratedReferenceSelector:
    """Generate one VREF/VSS selector from two generated TG children."""

    vref_switch = generate_transmission_gate(
        TransmissionGateLayoutIntent(
            spec=intent.spec.switch,
            cell_name=f"{intent.resolved_cell_name}_vref_tg",
            policy=intent.vref_switch_policy,
        )
    )
    vss_switch = generate_transmission_gate(
        TransmissionGateLayoutIntent(
            spec=intent.spec.switch,
            cell_name=f"{intent.resolved_cell_name}_vss_tg",
            policy=intent.vss_switch_policy,
        )
    )

    placement = build_reference_selector_child_placement(
        intent=intent,
        vref_switch=vref_switch,
        vss_switch=vss_switch,
    )
    physical_design = create_reference_selector_child_snapshot(
        placement,
        access_policy=TransmissionGateCellAccessPolicy(directions=("W", "E")),
    )
    routes = plan_reference_selector_topology(
        intent=intent,
        physical_design=physical_design,
    )
    executed_routes = tuple(
        execute_route_plan(component=placement.component, plan=plan)
        for plan in routes.plans
    )
    public_ports = _promote_selector_ports(
        placement=placement,
        routes=routes,
    )
    return GeneratedReferenceSelector(
        intent=intent,
        vref_switch=vref_switch,
        vss_switch=vss_switch,
        placement=placement,
        physical_design=physical_design,
        routes=routes,
        executed_routes=executed_routes,
        public_port_names=public_ports,
    )
