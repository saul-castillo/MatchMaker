from dataclasses import dataclass

from glayout import gf180

from matchmaker.design.reference_selector_naming import (
    VREF_SWITCH_INSTANCE_NAME,
    VSS_SWITCH_INSTANCE_NAME,
)
from matchmaker.generators.transmission_gate_generator import (
    GeneratedTransmissionGate,
    generate_transmission_gate,
)
from matchmaker.physical.access_selection import unique_access_facing
from matchmaker.physical.models import PhysicalDesignSnapshot, TerminalRef
from matchmaker.physical.reference_selector_snapshot import (
    create_reference_selector_child_snapshot,
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
from matchmaker.primitives.gf180_via_geometry import Gf180ViaGeometryFactory
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
    physical_design: PhysicalDesignSnapshot,
    routes: ReferenceSelectorRouteBundle,
) -> tuple[str, ...]:
    component = placement.component
    vref_input = unique_access_facing(
        physical_design,
        terminal=TerminalRef(VREF_SWITCH_INSTANCE_NAME, "input"),
        orientation=0,
        context="public selector input access",
    )
    vref_vdd = unique_access_facing(
        physical_design,
        terminal=TerminalRef(VREF_SWITCH_INSTANCE_NAME, "vdd"),
        orientation=90,
        context="public selector VDD access",
    )
    _copy_component_port(
        component,
        new_name="vref_E",
        source_name=vref_input.name,
    )
    _copy_component_port(
        component,
        new_name="vdd_N",
        source_name=vref_vdd.name,
    )
    _add_route_midpoint_port(
        component,
        name="vss_E",
        plan=routes.vss_plan,
        orientation=0.0,
        segment_orientation="vertical",
    )
    _add_route_midpoint_port(
        component,
        name="common_W",
        plan=routes.common_plan,
        orientation=180.0,
        segment_orientation="vertical",
    )
    _add_route_midpoint_port(
        component,
        name="select_W",
        plan=routes.select_plan,
        orientation=180.0,
        segment_orientation="vertical",
    )
    _add_route_midpoint_port(
        component,
        name="select_bar_E",
        plan=routes.select_bar_plan,
        orientation=0.0,
        segment_orientation="vertical",
    )
    return (
        "vref_E",
        "vss_E",
        "vdd_N",
        "common_W",
        "select_W",
        "select_bar_E",
    )


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
    physical_design = create_reference_selector_child_snapshot(placement)
    upper_route_source_access = unique_access_facing(
        physical_design,
        terminal=TerminalRef(VREF_SWITCH_INSTANCE_NAME, "output"),
        orientation=180,
        context="selector upper-route transition source",
    )
    via_geometry_factory = Gf180ViaGeometryFactory(gf180)
    upper_route_transition = via_geometry_factory.describe_transition(
        source_layer=upper_route_source_access.layer,
        route_generic_layer=intent.policy.upper_route_glayer,
    )
    routes = plan_reference_selector_topology(
        intent=intent,
        physical_design=physical_design,
        upper_route_transition=upper_route_transition,
    )
    executed_routes = tuple(
        execute_route_plan(
            component=placement.component,
            plan=plan,
            via_geometry_factory=via_geometry_factory,
        )
        for plan in routes.plans
    )
    public_ports = _promote_selector_ports(
        placement=placement,
        physical_design=physical_design,
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
