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
from matchmaker.routing.plans.route_plan import (
    ConstraintCheck,
    RouteMetrics,
    RoutePlan,
    RouteSegment,
    ViaPlan,
)
from matchmaker.routing.plans.route_plan_checks import (
    require_no_cross_net_route_overlaps,
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
        context="selector topology access",
    )


def _resolved_width(
    *,
    intent: ReferenceSelectorLayoutIntent,
    first: AccessPoint,
    second: AccessPoint,
) -> float:
    return (
        float(intent.policy.route_width)
        if intent.policy.route_width is not None
        else min(first.width, second.width)
    )


def _resolved_supply_width(
    *,
    intent: ReferenceSelectorLayoutIntent,
    accesses: tuple[AccessPoint, ...],
    signal_anchor: AccessPoint,
) -> float:
    if intent.policy.supply_route_width is not None:
        return float(intent.policy.supply_route_width)
    if intent.policy.route_width is not None:
        return float(intent.policy.route_width)
    return min(*(access.width for access in accesses), signal_anchor.width)


def _segments_from_points(
    *,
    points: tuple[tuple[float, float], ...],
    layer,
    width: float,
) -> tuple[RouteSegment, ...]:
    segments = tuple(
        RouteSegment(start=start, end=end, layer=layer, width=width)
        for start, end in zip(points, points[1:])
        if start != end
    )
    if not segments:
        raise RuntimeError("reference-selector route collapsed to zero length")
    return segments


def _metrics(
    *,
    segments: tuple[RouteSegment, ...],
    vias: tuple[ViaPlan, ...],
    width: float,
) -> RouteMetrics:
    return RouteMetrics.from_geometry(
        segments=segments,
        vias=vias,
        estimated_cost=sum(segment.length for segment in segments),
        resolved_width=width,
    )


def _route_plan(
    *,
    net_name: str,
    first: AccessPoint,
    second: AccessPoint,
    points: tuple[tuple[float, float], ...],
    intent: ReferenceSelectorLayoutIntent,
    strategy: str,
    detail: str,
    extra_checks: tuple[ConstraintCheck, ...] = (),
) -> RoutePlan:
    if first.layer != second.layer:
        raise RuntimeError(
            f"selector net {net_name} endpoints use different layers: "
            f"{first.layer!r} vs {second.layer!r}"
        )
    width = _resolved_width(intent=intent, first=first, second=second)
    segments = _segments_from_points(
        points=points,
        layer=first.layer,
        width=width,
    )
    return RoutePlan(
        net_name=net_name,
        terminals=(first.terminal, second.terminal),
        selected_access_point_names=(first.name, second.name),
        strategy=strategy,
        segments=segments,
        vias=(),
        metrics=_metrics(segments=segments, vias=(), width=width),
        constraint_checks=(
            ConstraintCheck(
                name="common_layer",
                passed=True,
                hard=True,
                detail=f"resolved layer {first.layer!r}",
            ),
            *extra_checks,
        ),
        provenance=(
            "typed ReferenceSelectorLayoutIntent",
            "stable generated transmission-gate child bindings",
            "transformed runtime access orientations, layers, widths, and bboxes",
            detail,
        ),
    )


def _transition_route_plan(
    *,
    net_name: str,
    first: AccessPoint,
    second: AccessPoint,
    first_via_center: tuple[float, float],
    route_points: tuple[tuple[float, float], ...],
    second_via_center: tuple[float, float],
    transition: RoutingLayerTransition,
    intent: ReferenceSelectorLayoutIntent,
    strategy: str,
    detail: str,
    extra_checks: tuple[ConstraintCheck, ...] = (),
) -> RoutePlan:
    if first.layer != second.layer or first.layer != transition.source_layer:
        raise RuntimeError(
            f"selector net {net_name} control accesses do not match the "
            f"transition source layer {transition.source_layer!r}"
        )
    if route_points[0] != first_via_center or route_points[-1] != second_via_center:
        raise RuntimeError("control route points must begin and end at via centers")

    source_width = _resolved_width(intent=intent, first=first, second=second)
    route_width = max(
        source_width,
        transition.minimum_route_width,
    )
    source_segments = (
        RouteSegment(
            start=first.center,
            end=first_via_center,
            layer=transition.source_layer,
            width=source_width,
        ),
        RouteSegment(
            start=second_via_center,
            end=second.center,
            layer=transition.source_layer,
            width=source_width,
        ),
    )
    route_segments = _segments_from_points(
        points=route_points,
        layer=transition.route_layer,
        width=route_width,
    )
    segments = (source_segments[0], *route_segments, source_segments[1])
    vias = (
        ViaPlan(
            center=first_via_center,
            lower_layer=transition.source_layer,
            upper_layer=transition.route_layer,
            via_name=transition.via_name,
        ),
        ViaPlan(
            center=second_via_center,
            lower_layer=transition.source_layer,
            upper_layer=transition.route_layer,
            via_name=transition.via_name,
        ),
    )
    return RoutePlan(
        net_name=net_name,
        terminals=(first.terminal, second.terminal),
        selected_access_point_names=(first.name, second.name),
        strategy=strategy,
        segments=segments,
        vias=vias,
        metrics=_metrics(segments=segments, vias=vias, width=route_width),
        constraint_checks=(
            ConstraintCheck(
                name="layer_transition",
                passed=True,
                hard=True,
                detail=(
                    f"{transition.source_layer!r} -> "
                    f"{transition.route_layer!r} with {transition.via_name}"
                ),
            ),
            *extra_checks,
        ),
        provenance=(
            "typed ReferenceSelectorLayoutIntent",
            "typed RoutingLayerTransition",
            "transformed runtime access orientations, layers, widths, and bboxes",
            detail,
        ),
    )


def _route_tree_plan(
    *,
    net_name: str,
    accesses: tuple[AccessPoint, ...],
    segment_endpoints: tuple[
        tuple[tuple[float, float], tuple[float, float]], ...
    ],
    width: float,
    strategy: str,
    detail: str,
    extra_checks: tuple[ConstraintCheck, ...] = (),
) -> RoutePlan:
    layers = {access.layer for access in accesses}
    if len(layers) != 1:
        raise RuntimeError(
            f"selector net {net_name} endpoints use different layers: "
            + ", ".join(map(repr, sorted(layers, key=repr)))
        )
    layer = next(iter(layers))
    segments = tuple(
        RouteSegment(start=start, end=end, layer=layer, width=width)
        for start, end in segment_endpoints
        if start != end
    )
    if not segments:
        raise RuntimeError(f"selector net {net_name} collapsed to zero length")

    segment_points = {
        point for segment in segments for point in (segment.start, segment.end)
    }
    missing_accesses = tuple(
        access.name for access in accesses if access.center not in segment_points
    )
    if missing_accesses:
        raise RuntimeError(
            f"selector net {net_name} route omits selected accesses: "
            + ", ".join(missing_accesses)
        )

    return RoutePlan(
        net_name=net_name,
        terminals=tuple(access.terminal for access in accesses),
        selected_access_point_names=tuple(access.name for access in accesses),
        strategy=strategy,
        segments=segments,
        vias=(),
        metrics=_metrics(segments=segments, vias=(), width=width),
        constraint_checks=(
            ConstraintCheck(
                name="common_layer",
                passed=True,
                hard=True,
                detail=f"resolved layer {layer!r}",
            ),
            *extra_checks,
        ),
        provenance=(
            "typed ReferenceSelectorLayoutIntent",
            "stable generated transmission-gate child bindings",
            "transformed runtime access orientations, layers, widths, and bboxes",
            detail,
        ),
    )


def _with_check(plan: RoutePlan, check: ConstraintCheck) -> RoutePlan:
    return replace(plan, constraint_checks=(*plan.constraint_checks, check))


def plan_reference_selector_topology(
    *,
    intent: ReferenceSelectorLayoutIntent,
    physical_design: PhysicalDesignSnapshot,
    control_transition: RoutingLayerTransition,
) -> ReferenceSelectorRouteBundle:
    """Plan a balanced R0/R180 selector with explicit layer resources.

    COMMON and VSS stay on the measured signal layer. Complementary controls
    escape through identical via stacks to a higher routing layer and use
    rotationally symmetric half-perimeter paths. VDD uses the facing conductive
    east/west PMOS body ties on their measured lower metal layer.
    """

    vref_instance = physical_design.instance(VREF_SWITCH_INSTANCE_NAME)
    vss_instance = physical_design.instance(VSS_SWITCH_INSTANCE_NAME)
    if vref_instance.bbox.xmax > vss_instance.bbox.xmin:
        raise RuntimeError("reference-selector child bboxes overlap or are reversed")

    child_gap = vss_instance.bbox.xmin - vref_instance.bbox.xmax
    central_x = (vref_instance.bbox.xmax + vss_instance.bbox.xmin) / 2.0
    child_top = max(vref_instance.bbox.ymax, vss_instance.bbox.ymax)
    child_bottom = min(vref_instance.bbox.ymin, vss_instance.bbox.ymin)

    vref_output = _access_facing(
        physical_design,
        instance_name=VREF_SWITCH_INSTANCE_NAME,
        terminal_name="output",
        orientation=0,
    )
    vss_output = _access_facing(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="output",
        orientation=180,
    )
    common_faces_gap = (
        vref_output.center[0] < central_x < vss_output.center[0]
    )
    if not common_faces_gap:
        raise RuntimeError("reference-selector COMMON accesses do not face the gap")
    common_plan = _route_plan(
        net_name=COMMON_NET_NAME,
        first=vref_output,
        second=vss_output,
        points=(
            vref_output.center,
            (central_x, vref_output.center[1]),
            (central_x, vss_output.center[1]),
            vss_output.center,
        ),
        intent=intent,
        strategy="reference_selector_central_common",
        detail=f"single central-gap trunk x={central_x}",
        extra_checks=(
            ConstraintCheck(
                name="gap_facing_accesses",
                passed=common_faces_gap,
                hard=True,
                detail="east VREF output and west VSS output face the child gap",
            ),
        ),
    )

    select_left = _access_facing(
        physical_design,
        instance_name=VREF_SWITCH_INSTANCE_NAME,
        terminal_name="control",
        orientation=180,
    )
    select_right = _access_facing(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="control_bar",
        orientation=180,
    )
    select_bar_left = _access_facing(
        physical_design,
        instance_name=VREF_SWITCH_INSTANCE_NAME,
        terminal_name="control_bar",
        orientation=0,
    )
    select_bar_right = _access_facing(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="control",
        orientation=0,
    )

    control_accesses = (
        select_left,
        select_right,
        select_bar_left,
        select_bar_right,
    )
    if any(
        access.layer != control_transition.source_layer
        for access in control_accesses
    ):
        raise RuntimeError(
            "selector control accesses do not share the transition layer"
        )

    control_width = max(
        _resolved_width(
            intent=intent,
            first=select_left,
            second=select_right,
        ),
        _resolved_width(
            intent=intent,
            first=select_bar_left,
            second=select_bar_right,
        ),
        control_transition.minimum_route_width,
    )
    via_width, via_height = control_transition.via_size
    if child_gap <= via_width:
        raise RuntimeError(
            "reference-selector child gap cannot contain the control via: "
            f"gap={child_gap}, via_width={via_width}"
        )

    outer_offset = (
        intent.policy.channel_clearance + max(control_width, via_width) / 2.0
    )
    left_control_x = vref_instance.bbox.xmin - outer_offset
    right_control_x = vss_instance.bbox.xmax + outer_offset
    top_control_y = (
        child_top + intent.policy.channel_clearance + control_width / 2.0
    )
    bottom_control_y = (
        child_bottom - intent.policy.channel_clearance - control_width / 2.0
    )

    transformed_order_is_safe = (
        select_bar_left.center[1] < select_right.center[1]
        and select_left.center[0] > left_control_x
        and select_right.center[0] > central_x
        and select_bar_left.center[0] < central_x
        and select_bar_right.center[0] < right_control_x
    )
    if not transformed_order_is_safe:
        raise RuntimeError(
            "reference-selector transformed control accesses do not support "
            "the balanced half-perimeter topology"
        )

    common_ymin = min(vref_output.center[1], vss_output.center[1])
    common_ymax = max(vref_output.center[1], vss_output.center[1])
    common_half_width = common_plan.metrics.resolved_width / 2.0
    central_vias_clear_common = (
        select_right.center[1] - via_height / 2.0
        > common_ymax + common_half_width
        and select_bar_left.center[1] + via_height / 2.0
        < common_ymin - common_half_width
    )
    if not central_vias_clear_common:
        raise RuntimeError(
            "reference-selector central control vias do not clear COMMON"
        )
    central_via_check = ConstraintCheck(
        name="central_vias_clear_common",
        passed=True,
        hard=True,
        detail=(
            f"via height {via_height}, COMMON y-range "
            f"{common_ymin}..{common_ymax}"
        ),
    )

    select_plan = _transition_route_plan(
        net_name=SELECT_NET_NAME,
        first=select_left,
        second=select_right,
        first_via_center=(left_control_x, select_left.center[1]),
        route_points=(
            (left_control_x, select_left.center[1]),
            (left_control_x, top_control_y),
            (central_x, top_control_y),
            (central_x, select_right.center[1]),
        ),
        second_via_center=(central_x, select_right.center[1]),
        transition=control_transition,
        intent=intent,
        strategy="reference_selector_balanced_north_control",
        detail="west outer escape, north half-perimeter, central-gap landing",
        extra_checks=(central_via_check,),
    )
    select_bar_plan = _transition_route_plan(
        net_name=SELECT_BAR_NET_NAME,
        first=select_bar_left,
        second=select_bar_right,
        first_via_center=(central_x, select_bar_left.center[1]),
        route_points=(
            (central_x, select_bar_left.center[1]),
            (central_x, bottom_control_y),
            (right_control_x, bottom_control_y),
            (right_control_x, select_bar_right.center[1]),
        ),
        second_via_center=(right_control_x, select_bar_right.center[1]),
        transition=control_transition,
        intent=intent,
        strategy="reference_selector_balanced_south_control",
        detail="central-gap landing, south half-perimeter, east outer escape",
        extra_checks=(central_via_check,),
    )

    controls_length_matched = isclose(
        select_plan.metrics.total_length,
        select_bar_plan.metrics.total_length,
        abs_tol=intent.policy.alignment_tolerance,
    )
    if not controls_length_matched:
        raise RuntimeError(
            "balanced selector controls are not length matched: "
            f"SELECT={select_plan.metrics.total_length}, "
            f"SELECT_BAR={select_bar_plan.metrics.total_length}"
        )
    length_check = ConstraintCheck(
        name="control_length_match",
        passed=controls_length_matched,
        hard=True,
        detail=(
            f"SELECT={select_plan.metrics.total_length}, "
            f"SELECT_BAR={select_bar_plan.metrics.total_length}"
        ),
    )
    select_plan = _with_check(select_plan, length_check)
    select_bar_plan = _with_check(select_bar_plan, length_check)

    vref_vss = _access_facing(
        physical_design,
        instance_name=VREF_SWITCH_INSTANCE_NAME,
        terminal_name="vss",
        orientation=90,
    )
    vss_vss = _access_facing(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="vss",
        orientation=90,
    )
    vss_signal = _access_facing(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="input",
        orientation=0,
    )
    vss_accesses = (vref_vss, vss_vss, vss_signal)
    vss_width = _resolved_supply_width(
        intent=intent,
        accesses=vss_accesses,
        signal_anchor=vss_signal,
    )

    top_opening = top_control_y - control_width / 2.0 - child_top
    right_via_edge = right_control_x + via_width / 2.0
    vss_service_x = max(
        vss_signal.center[0],
        right_via_edge + intent.policy.channel_clearance + vss_width / 2.0,
    )
    vss_rail_y = child_top + top_opening / 2.0
    supply_lane_fits = top_opening > vss_width
    outward_vss_accesses = (
        vref_vss.center[1] < vss_rail_y
        and vss_vss.center[1] < vss_rail_y
        and vss_signal.center[0] <= vss_service_x
        and vref_vss.center[0] < vss_vss.center[0] < vss_service_x
    )
    if not supply_lane_fits or not outward_vss_accesses:
        raise RuntimeError(
            "reference-selector VSS accesses do not fit the north/right "
            "supply channels"
        )
    vss_plan = _route_tree_plan(
        net_name=VSS_NET_NAME,
        accesses=vss_accesses,
        segment_endpoints=(
            (vref_vss.center, (vref_vss.center[0], vss_rail_y)),
            (vss_vss.center, (vss_vss.center[0], vss_rail_y)),
            ((vref_vss.center[0], vss_rail_y), (vss_service_x, vss_rail_y)),
            (vss_signal.center, (vss_service_x, vss_signal.center[1])),
            ((vss_service_x, vss_signal.center[1]), (vss_service_x, vss_rail_y)),
        ),
        width=vss_width,
        strategy="reference_selector_north_vss_rail",
        detail=(
            f"north rail y={vss_rail_y}, service channel x={vss_service_x} "
            "outside the east control via"
        ),
        extra_checks=(
            ConstraintCheck(
                name="supply_lane_clearance",
                passed=supply_lane_fits,
                hard=True,
                detail=f"top opening {top_opening}, route width {vss_width}",
            ),
            ConstraintCheck(
                name="outward_supply_accesses",
                passed=outward_vss_accesses,
                hard=True,
                detail="north body ties and physical-east VSS input face channels",
            ),
        ),
    )

    vref_vdd = _access_facing(
        physical_design,
        instance_name=VREF_SWITCH_INSTANCE_NAME,
        terminal_name="vdd",
        orientation=0,
    )
    vss_vdd = _access_facing(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="vdd",
        orientation=180,
    )
    vdd_accesses = (vref_vdd, vss_vdd)
    if vref_vdd.layer == common_plan.segments[0].layer:
        raise RuntimeError(
            "reference-selector facing VDD ties must use a layer below the "
            "signal/control accesses"
        )
    vdd_width = _resolved_supply_width(
        intent=intent,
        accesses=vdd_accesses,
        signal_anchor=vss_signal,
    )
    outward_vdd_accesses = (
        vref_vdd.center[0] < central_x < vss_vdd.center[0]
    )
    if not outward_vdd_accesses:
        raise RuntimeError("reference-selector VDD accesses do not face the gap")
    vdd_low_y = min(vref_vdd.center[1], vss_vdd.center[1])
    vdd_plan = _route_tree_plan(
        net_name=VDD_NET_NAME,
        accesses=vdd_accesses,
        segment_endpoints=(
            (vref_vdd.center, (central_x, vref_vdd.center[1])),
            (vss_vdd.center, (central_x, vss_vdd.center[1])),
            (
                (central_x, vref_vdd.center[1]),
                (central_x, vss_vdd.center[1]),
            ),
            ((central_x, vdd_low_y), (central_x, bottom_control_y)),
        ),
        width=vdd_width,
        strategy="reference_selector_central_lower_metal_vdd",
        detail=(
            "facing east/west PMOS ties join in the child gap and escape south"
        ),
        extra_checks=(
            ConstraintCheck(
                name="outward_supply_accesses",
                passed=outward_vdd_accesses,
                hard=True,
                detail="physical east/west PMOS ties face the child gap",
            ),
        ),
    )

    bundle = ReferenceSelectorRouteBundle(
        common_plan=common_plan,
        select_plan=select_plan,
        select_bar_plan=select_bar_plan,
        vss_plan=vss_plan,
        vdd_plan=vdd_plan,
    )
    require_no_cross_net_route_overlaps(bundle.plans)
    return bundle
