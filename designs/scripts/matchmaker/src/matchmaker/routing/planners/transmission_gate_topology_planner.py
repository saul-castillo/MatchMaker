from dataclasses import dataclass
from math import isclose

from matchmaker.physical.gf180_mos_access import gf180_mos_external_port_name
from matchmaker.physical.models import AccessPoint, PhysicalDesignSnapshot, TerminalRef
from matchmaker.placement.cdac.transmission_gate_builder import (
    NMOS_INSTANCE_NAME,
    PMOS_INSTANCE_NAME,
)
from matchmaker.placement.cdac.transmission_gate_intent import (
    TransmissionGateLayoutIntent,
)
from matchmaker.routing.plans.route_plan import (
    ConstraintCheck,
    RouteMetrics,
    RoutePlan,
    RouteSegment,
)


@dataclass(frozen=True)
class TransmissionGateRouteBundle:
    input_plan: RoutePlan
    output_plan: RoutePlan

    @property
    def plans(self) -> tuple[RoutePlan, RoutePlan]:
        return self.input_plan, self.output_plan


def _access_by_primitive_name(
    physical_design: PhysicalDesignSnapshot,
    terminal: TerminalRef,
    primitive_port_name: str,
) -> AccessPoint:
    matches = tuple(
        access
        for access in physical_design.access_points_for(terminal)
        if access.primitive_port_name == primitive_port_name
    )
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one access for {terminal.instance_name}."
            f"{terminal.terminal_name} named {primitive_port_name!r}; "
            f"found {len(matches)}"
        )
    return matches[0]


def _plan_parallel_terminal(
    *,
    net_name: str,
    terminal_name: str,
    intent: TransmissionGateLayoutIntent,
    physical_design: PhysicalDesignSnapshot,
) -> RoutePlan:
    nmos_terminal = TerminalRef(NMOS_INSTANCE_NAME, terminal_name)
    pmos_terminal = TerminalRef(PMOS_INSTANCE_NAME, terminal_name)
    nmos_access = _access_by_primitive_name(
        physical_design,
        nmos_terminal,
        gf180_mos_external_port_name(
            terminal_name,
            intent.policy.inner_nmos_direction,
        ),
    )
    pmos_access = _access_by_primitive_name(
        physical_design,
        pmos_terminal,
        gf180_mos_external_port_name(
            terminal_name,
            intent.policy.inner_pmos_direction,
        ),
    )

    same_layer = nmos_access.layer == pmos_access.layer
    aligned = isclose(
        nmos_access.center[1],
        pmos_access.center[1],
        abs_tol=intent.policy.alignment_tolerance,
    )
    if not same_layer:
        raise RuntimeError(
            f"transmission-gate {terminal_name} accesses are on different layers: "
            f"{nmos_access.layer!r} vs {pmos_access.layer!r}"
        )
    if not aligned:
        raise RuntimeError(
            f"transmission-gate {terminal_name} accesses are not horizontally aligned: "
            f"{nmos_access.center!r} vs {pmos_access.center!r}"
        )

    resolved_width = (
        float(intent.policy.route_width)
        if intent.policy.route_width is not None
        else min(nmos_access.width, pmos_access.width)
    )
    segment = RouteSegment(
        start=nmos_access.center,
        end=pmos_access.center,
        layer=nmos_access.layer,
        width=resolved_width,
    )
    metrics = RouteMetrics.from_geometry(
        segments=(segment,),
        vias=(),
        estimated_cost=segment.length,
        resolved_width=resolved_width,
    )
    return RoutePlan(
        net_name=net_name,
        terminals=(nmos_terminal, pmos_terminal),
        selected_access_point_names=(nmos_access.name, pmos_access.name),
        strategy="transmission_gate_parallel_terminal",
        segments=(segment,),
        vias=(),
        metrics=metrics,
        constraint_checks=(
            ConstraintCheck(
                name="common_layer",
                passed=same_layer,
                hard=True,
                detail=f"resolved layer {nmos_access.layer!r}",
            ),
            ConstraintCheck(
                name="horizontal_alignment",
                passed=aligned,
                hard=True,
                detail=(
                    f"y={nmos_access.center[1]} and y={pmos_access.center[1]}"
                ),
            ),
        ),
        provenance=(
            "typed TransmissionGateLayoutIntent",
            "stable NMOS/PMOS PlacementResult bindings",
            "runtime GF180 MOS external access data",
        ),
    )


def plan_transmission_gate_signal_topology(
    *,
    intent: TransmissionGateLayoutIntent,
    physical_design: PhysicalDesignSnapshot,
) -> TransmissionGateRouteBundle:
    """Plan the two parallel signal nets of one transmission gate."""

    input_plan = _plan_parallel_terminal(
        net_name="input",
        terminal_name=intent.policy.input_device_terminal,
        intent=intent,
        physical_design=physical_design,
    )
    output_plan = _plan_parallel_terminal(
        net_name="output",
        terminal_name=intent.policy.output_device_terminal,
        intent=intent,
        physical_design=physical_design,
    )
    return TransmissionGateRouteBundle(
        input_plan=input_plan,
        output_plan=output_plan,
    )
