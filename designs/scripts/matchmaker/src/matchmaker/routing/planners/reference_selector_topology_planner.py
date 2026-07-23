from dataclasses import dataclass, replace
from math import isclose

from matchmaker.design.reference_selector_naming import (
    COMMON_NET_NAME,
    SELECT_BAR_NET_NAME,
    SELECT_NET_NAME,
    VDD_NET_NAME,
    VREF_SWITCH_INSTANCE_NAME,
    VSS_NET_NAME,
    VSS_SWITCH_INSTANCE_NAME,
)
from matchmaker.physical.access_selection import unique_access_facing
from matchmaker.physical.models import AccessPoint, PhysicalDesignSnapshot, TerminalRef
from matchmaker.placement.cdac.reference_selector_intent import (
    ReferenceSelectorLayoutIntent,
)
from matchmaker.routing.intents.net_intent import NetConstraintProfile, NetIntent
from matchmaker.routing.planners.corridor_route_planner import (
    envelope_from_bboxes,
    plan_external_side_bus,
    plan_gap_bridge,
    plan_transitioned_trunk_tree,
    via_center_at_envelope_side,
    via_center_at_gap_edge,
)
from matchmaker.routing.plans.route_plan import ConstraintCheck, RoutePlan
from matchmaker.routing.plans.route_plan_checks import (
    ViaEnvelope,
    require_no_cross_net_route_overlaps,
    require_no_cross_net_via_envelope_overlaps,
    require_via_envelopes_clear_routes,
)
from matchmaker.routing.resources import RoutingLayerTransition


@dataclass(frozen=True)
class ReferenceSelectorRouteBundle:
    common_plan: RoutePlan
    select_plan: RoutePlan
    select_bar_plan: RoutePlan
    vss_plan: RoutePlan
    vdd_plan: RoutePlan

    @property
    def plans(self) -> tuple[RoutePlan, ...]:
        return (
            self.common_plan,
            self.select_plan,
            self.select_bar_plan,
            self.vss_plan,
            self.vdd_plan,
        )


def _access_facing(
    snapshot: PhysicalDesignSnapshot,
    *,
    instance_name: str,
    terminal_name: str,
    orientation: int,
) -> AccessPoint:
    return unique_access_facing(
        snapshot,
        terminal=TerminalRef(instance_name, terminal_name),
        orientation=orientation,
        context="selector family access",
    )


def _net_intent(
    *,
    name: str,
    terminals: tuple[TerminalRef, ...],
    width: float | None,
) -> NetIntent:
    return NetIntent(
        name=name,
        terminals=terminals,
        constraints=NetConstraintProfile(
            width_class=(
                "supply" if name in {VSS_NET_NAME, VDD_NET_NAME} else "signal"
            ),
            width=width,
            avoid_obstacles=True,
        ),
    )


def _supply_width(
    *,
    intent: ReferenceSelectorLayoutIntent,
    accesses: tuple[AccessPoint, ...],
    signal_anchor: AccessPoint,
) -> float:
    if intent.policy.supply_route_width is not None:
        return float(intent.policy.supply_route_width)
    if intent.policy.route_width is not None:
        return float(intent.policy.route_width)
    return min(signal_anchor.width, *(access.width for access in accesses))


def _with_check(plan: RoutePlan, check: ConstraintCheck) -> RoutePlan:
    return replace(plan, constraint_checks=(*plan.constraint_checks, check))


def _via_envelopes(
    *,
    net_name: str,
    centers: tuple[tuple[float, float], ...],
    transition: RoutingLayerTransition,
) -> tuple[ViaEnvelope, ...]:
    return tuple(
        ViaEnvelope(
            net_name=net_name,
            center=center,
            size=transition.via_size,
            layers=(transition.source_layer, transition.route_layer),
        )
        for center in centers
    )


def plan_reference_selector_topology(
    *,
    intent: ReferenceSelectorLayoutIntent,
    physical_design: PhysicalDesignSnapshot,
    upper_route_transition: RoutingLayerTransition,
) -> ReferenceSelectorRouteBundle:
    """Bind selector roles to reusable vertical-pair corridor templates.

    Family adapters advertise only safe generated-cell accesses. The selector
    binds those logical terminals to generic side-bus, gap-bridge, and
    transitioned-tree plans; it contains no primitive port tokens, numeric
    layers, or fixed device coordinates.
    """

    if intent.policy.child_axis != "vertical":
        raise RuntimeError(
            "compact selector topology currently requires a vertical pair"
        )
    if intent.policy.vref_child_side != "high":
        raise RuntimeError(
            "compact selector topology requires VREF on the high/north side"
        )

    vref_instance = physical_design.instance(VREF_SWITCH_INSTANCE_NAME)
    vss_instance = physical_design.instance(VSS_SWITCH_INSTANCE_NAME)
    if vss_instance.bbox.ymax > vref_instance.bbox.ymin:
        raise RuntimeError("vertical selector child bboxes overlap or are reversed")

    corridor = envelope_from_bboxes(
        (vref_instance.bbox, vss_instance.bbox),
        gap_axis="vertical",
    )

    select_terminals = (
        TerminalRef(VREF_SWITCH_INSTANCE_NAME, "control"),
        TerminalRef(VSS_SWITCH_INSTANCE_NAME, "control_bar"),
    )
    select_accesses = (
        _access_facing(
            physical_design,
            instance_name=VREF_SWITCH_INSTANCE_NAME,
            terminal_name="control",
            orientation=180,
        ),
        _access_facing(
            physical_design,
            instance_name=VSS_SWITCH_INSTANCE_NAME,
            terminal_name="control_bar",
            orientation=180,
        ),
    )
    select_plan = plan_external_side_bus(
        intent=_net_intent(
            name=SELECT_NET_NAME,
            terminals=select_terminals,
            width=intent.policy.route_width,
        ),
        first=select_accesses[0],
        second=select_accesses[1],
        envelope=corridor.bbox,
        side="west",
        clearance=intent.policy.channel_clearance,
    )

    select_bar_terminals = (
        TerminalRef(VREF_SWITCH_INSTANCE_NAME, "control_bar"),
        TerminalRef(VSS_SWITCH_INSTANCE_NAME, "control"),
    )
    select_bar_accesses = (
        _access_facing(
            physical_design,
            instance_name=VREF_SWITCH_INSTANCE_NAME,
            terminal_name="control_bar",
            orientation=0,
        ),
        _access_facing(
            physical_design,
            instance_name=VSS_SWITCH_INSTANCE_NAME,
            terminal_name="control",
            orientation=0,
        ),
    )
    select_bar_plan = plan_external_side_bus(
        intent=_net_intent(
            name=SELECT_BAR_NET_NAME,
            terminals=select_bar_terminals,
            width=intent.policy.route_width,
        ),
        first=select_bar_accesses[0],
        second=select_bar_accesses[1],
        envelope=corridor.bbox,
        side="east",
        clearance=intent.policy.channel_clearance,
    )

    controls_length_matched = isclose(
        select_plan.metrics.total_length,
        select_bar_plan.metrics.total_length,
        abs_tol=intent.policy.alignment_tolerance,
    )
    controls_bend_matched = (
        select_plan.metrics.bend_count == select_bar_plan.metrics.bend_count
    )
    if not controls_length_matched or not controls_bend_matched:
        raise RuntimeError(
            "vertical selector controls are not matched: "
            f"SELECT=({select_plan.metrics.total_length}, "
            f"{select_plan.metrics.bend_count} bends), "
            f"SELECT_BAR=({select_bar_plan.metrics.total_length}, "
            f"{select_bar_plan.metrics.bend_count} bends)"
        )
    control_match_check = ConstraintCheck(
        name="matched_control_family",
        passed=True,
        hard=True,
        detail=(
            f"length={select_plan.metrics.total_length}, "
            f"bends={select_plan.metrics.bend_count}"
        ),
    )
    select_plan = _with_check(select_plan, control_match_check)
    select_bar_plan = _with_check(select_bar_plan, control_match_check)

    common_terminals = (
        TerminalRef(VREF_SWITCH_INSTANCE_NAME, "output"),
        TerminalRef(VSS_SWITCH_INSTANCE_NAME, "output"),
    )
    common_accesses = (
        _access_facing(
            physical_design,
            instance_name=VREF_SWITCH_INSTANCE_NAME,
            terminal_name="output",
            orientation=180,
        ),
        _access_facing(
            physical_design,
            instance_name=VSS_SWITCH_INSTANCE_NAME,
            terminal_name="output",
            orientation=180,
        ),
    )
    if any(
        access.layer != upper_route_transition.source_layer
        for access in common_accesses
    ):
        raise RuntimeError(
            "COMMON family accesses do not match the transition source layer"
        )
    common_via_centers = tuple(
        via_center_at_envelope_side(
            access=access,
            envelope=corridor.bbox,
            side="west",
            via_size=upper_route_transition.via_size,
        )
        for access in common_accesses
    )
    common_plan = plan_transitioned_trunk_tree(
        intent=_net_intent(
            name=COMMON_NET_NAME,
            terminals=common_terminals,
            width=intent.policy.route_width,
        ),
        accesses=common_accesses,
        via_centers=common_via_centers,
        transition=upper_route_transition,
        trunk_axis="vertical",
        trunk_coordinate=min(center[0] for center in common_via_centers),
    )

    vss_terminals = (
        TerminalRef(VREF_SWITCH_INSTANCE_NAME, "vss"),
        TerminalRef(VSS_SWITCH_INSTANCE_NAME, "vss"),
        TerminalRef(VSS_SWITCH_INSTANCE_NAME, "input"),
    )
    vss_accesses = (
        _access_facing(
            physical_design,
            instance_name=VREF_SWITCH_INSTANCE_NAME,
            terminal_name="vss",
            orientation=270,
        ),
        _access_facing(
            physical_design,
            instance_name=VSS_SWITCH_INSTANCE_NAME,
            terminal_name="vss",
            orientation=90,
        ),
        _access_facing(
            physical_design,
            instance_name=VSS_SWITCH_INSTANCE_NAME,
            terminal_name="input",
            orientation=0,
        ),
    )
    if any(
        access.layer != upper_route_transition.source_layer
        for access in vss_accesses
    ):
        raise RuntimeError(
            "VSS family accesses do not match the transition source layer"
        )
    vss_via_centers = (
        via_center_at_gap_edge(
            access=vss_accesses[0],
            corridor=corridor,
            adjacent_side="high",
            via_size=upper_route_transition.via_size,
        ),
        via_center_at_gap_edge(
            access=vss_accesses[1],
            corridor=corridor,
            adjacent_side="low",
            via_size=upper_route_transition.via_size,
        ),
        via_center_at_envelope_side(
            access=vss_accesses[2],
            envelope=corridor.bbox,
            side="east",
            via_size=upper_route_transition.via_size,
        ),
    )
    vss_width = _supply_width(
        intent=intent,
        accesses=vss_accesses,
        signal_anchor=vss_accesses[2],
    )
    vss_plan = plan_transitioned_trunk_tree(
        intent=_net_intent(
            name=VSS_NET_NAME,
            terminals=vss_terminals,
            width=vss_width,
        ),
        accesses=vss_accesses,
        via_centers=vss_via_centers,
        transition=upper_route_transition,
        trunk_axis="vertical",
        trunk_coordinate=max(center[0] for center in vss_via_centers),
    )

    vdd_terminals = (
        TerminalRef(VREF_SWITCH_INSTANCE_NAME, "vdd"),
        TerminalRef(VSS_SWITCH_INSTANCE_NAME, "vdd"),
    )
    vdd_accesses = (
        _access_facing(
            physical_design,
            instance_name=VREF_SWITCH_INSTANCE_NAME,
            terminal_name="vdd",
            orientation=270,
        ),
        _access_facing(
            physical_design,
            instance_name=VSS_SWITCH_INSTANCE_NAME,
            terminal_name="vdd",
            orientation=90,
        ),
    )
    if vdd_accesses[0].layer != vdd_accesses[1].layer:
        raise RuntimeError("VDD gap accesses require one common layer")
    vdd_width = _supply_width(
        intent=intent,
        accesses=vdd_accesses,
        signal_anchor=vss_accesses[2],
    )
    vdd_plan = plan_gap_bridge(
        intent=_net_intent(
            name=VDD_NET_NAME,
            terminals=vdd_terminals,
            width=vdd_width,
        ),
        first=vdd_accesses[0],
        second=vdd_accesses[1],
        axis="vertical",
        gap_coordinate=corridor.gap_coordinate,
    )

    bundle = ReferenceSelectorRouteBundle(
        common_plan=common_plan,
        select_plan=select_plan,
        select_bar_plan=select_bar_plan,
        vss_plan=vss_plan,
        vdd_plan=vdd_plan,
    )
    for layer in (
        upper_route_transition.source_layer,
        upper_route_transition.route_layer,
    ):
        require_via_envelopes_clear_routes(
            via_net=COMMON_NET_NAME,
            via_centers=common_via_centers,
            via_size=upper_route_transition.via_size,
            layer=layer,
            plans=bundle.plans,
        )
        require_via_envelopes_clear_routes(
            via_net=VSS_NET_NAME,
            via_centers=vss_via_centers,
            via_size=upper_route_transition.via_size,
            layer=layer,
            plans=bundle.plans,
        )
    require_no_cross_net_via_envelope_overlaps(
        (
            *_via_envelopes(
                net_name=COMMON_NET_NAME,
                centers=common_via_centers,
                transition=upper_route_transition,
            ),
            *_via_envelopes(
                net_name=VSS_NET_NAME,
                centers=vss_via_centers,
                transition=upper_route_transition,
            ),
        )
    )
    require_no_cross_net_route_overlaps(bundle.plans)
    return bundle
