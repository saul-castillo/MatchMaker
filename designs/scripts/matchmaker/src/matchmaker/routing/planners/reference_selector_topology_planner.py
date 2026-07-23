from dataclasses import dataclass
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
from matchmaker.physical.models import AccessPoint, PhysicalDesignSnapshot, TerminalRef
from matchmaker.placement.cdac.reference_selector_intent import (
    ReferenceSelectorLayoutIntent,
)
from matchmaker.routing.plans.route_plan import (
    ConstraintCheck,
    RouteMetrics,
    RoutePlan,
    RouteSegment,
)


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


def _access(
    snapshot: PhysicalDesignSnapshot,
    *,
    instance_name: str,
    terminal_name: str,
    child_port_name: str,
) -> AccessPoint:
    terminal = TerminalRef(instance_name, terminal_name)
    matches = tuple(
        access
        for access in snapshot.access_points_for(terminal)
        if access.primitive_port_name == child_port_name
    )
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one {instance_name}.{terminal_name} access named "
            f"{child_port_name!r}; found {len(matches)}"
        )
    return matches[0]


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
    segments: list[RouteSegment] = []
    for start, end in zip(points, points[1:]):
        if start == end:
            continue
        segments.append(RouteSegment(start=start, end=end, layer=layer, width=width))
    if not segments:
        raise RuntimeError("reference-selector route collapsed to zero length")
    return tuple(segments)


def _route_plan(
    *,
    net_name: str,
    first: AccessPoint,
    second: AccessPoint,
    points: tuple[tuple[float, float], ...],
    intent: ReferenceSelectorLayoutIntent,
    strategy: str,
    detail: str,
) -> RoutePlan:
    same_layer = first.layer == second.layer
    if not same_layer:
        raise RuntimeError(
            f"selector net {net_name} endpoints use different layers: "
            f"{first.layer!r} vs {second.layer!r}"
        )
    width = _resolved_width(intent=intent, first=first, second=second)
    segments = _segments_from_points(points=points, layer=first.layer, width=width)
    metrics = RouteMetrics.from_geometry(
        segments=segments,
        vias=(),
        estimated_cost=sum(segment.length for segment in segments),
        resolved_width=width,
    )
    return RoutePlan(
        net_name=net_name,
        terminals=(first.terminal, second.terminal),
        selected_access_point_names=(first.name, second.name),
        strategy=strategy,
        segments=segments,
        vias=(),
        metrics=metrics,
        constraint_checks=(
            ConstraintCheck(
                name="common_layer",
                passed=same_layer,
                hard=True,
                detail=f"resolved layer {first.layer!r}",
            ),
        ),
        provenance=(
            "typed ReferenceSelectorLayoutIntent",
            "stable generated transmission-gate child bindings",
            "runtime child-cell access coordinates, widths, layers, and bboxes",
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
        point
        for segment in segments
        for point in (segment.start, segment.end)
    }
    missing_accesses = tuple(
        access.name for access in accesses if access.center not in segment_points
    )
    if missing_accesses:
        raise RuntimeError(
            f"selector net {net_name} route omits selected accesses: "
            + ", ".join(missing_accesses)
        )

    metrics = RouteMetrics.from_geometry(
        segments=segments,
        vias=(),
        estimated_cost=sum(segment.length for segment in segments),
        resolved_width=width,
    )
    return RoutePlan(
        net_name=net_name,
        terminals=tuple(access.terminal for access in accesses),
        selected_access_point_names=tuple(access.name for access in accesses),
        strategy=strategy,
        segments=segments,
        vias=(),
        metrics=metrics,
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
            "runtime child-cell access coordinates, widths, layers, and bboxes",
            detail,
        ),
    )


def _perimeter_points(
    *,
    first: AccessPoint,
    second: AccessPoint,
    left_channel: float,
    right_channel: float,
    horizontal_channel: float,
) -> tuple[tuple[float, float], ...]:
    return (
        first.center,
        (left_channel, first.center[1]),
        (left_channel, horizontal_channel),
        (right_channel, horizontal_channel),
        (right_channel, second.center[1]),
        second.center,
    )


def plan_reference_selector_topology(
    *,
    intent: ReferenceSelectorLayoutIntent,
    physical_design: PhysicalDesignSnapshot,
) -> ReferenceSelectorRouteBundle:
    """Plan selector signal, control, body, and supply topology.

    SELECT uses the proven outward-facing north-perimeter path. SELECT_BAR uses
    the proven inner-facing child accesses and one vertical trunk centered in the
    gap between child transmission-gate envelopes. VSS uses the measured met2
    north body ties plus the VSS-switch input; VDD uses the measured met2 south
    body ties. Both supply routes remain via-free.
    """

    vref_instance = physical_design.instance(VREF_SWITCH_INSTANCE_NAME)
    vss_instance = physical_design.instance(VSS_SWITCH_INSTANCE_NAME)
    if vref_instance.bbox.xmax > vss_instance.bbox.xmin:
        raise RuntimeError("reference-selector child bboxes overlap or are reversed")

    vref_output = _access(
        physical_design,
        instance_name=VREF_SWITCH_INSTANCE_NAME,
        terminal_name="output",
        child_port_name="output_E",
    )
    vss_output = _access(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="output",
        child_port_name="output_W",
    )
    aligned = isclose(
        vref_output.center[1],
        vss_output.center[1],
        abs_tol=intent.policy.alignment_tolerance,
    )
    if not aligned:
        raise RuntimeError(
            "reference-selector common output accesses are not horizontally aligned: "
            f"{vref_output.center!r} vs {vss_output.center!r}"
        )
    common_plan = _route_plan(
        net_name=COMMON_NET_NAME,
        first=vref_output,
        second=vss_output,
        points=(vref_output.center, vss_output.center),
        intent=intent,
        strategy="reference_selector_direct_common",
        detail="direct inner-output connection",
    )

    vref_select = _access(
        physical_design,
        instance_name=VREF_SWITCH_INSTANCE_NAME,
        terminal_name="control",
        child_port_name="control_W",
    )
    vss_select = _access(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="control_bar",
        child_port_name="control_bar_E",
    )
    select_width = _resolved_width(
        intent=intent,
        first=vref_select,
        second=vss_select,
    )
    select_offset = intent.policy.channel_clearance + select_width / 2.0
    select_left = vref_instance.bbox.xmin - select_offset
    select_right = vss_instance.bbox.xmax + select_offset
    top_channel = (
        max(vref_instance.bbox.ymax, vss_instance.bbox.ymax) + select_offset
    )
    select_plan = _route_plan(
        net_name=SELECT_NET_NAME,
        first=vref_select,
        second=vss_select,
        points=_perimeter_points(
            first=vref_select,
            second=vss_select,
            left_channel=select_left,
            right_channel=select_right,
            horizontal_channel=top_channel,
        ),
        intent=intent,
        strategy="reference_selector_north_perimeter_control",
        detail=(
            f"north perimeter channel y={top_channel}, "
            f"x={select_left}..{select_right}"
        ),
    )

    vref_select_bar = _access(
        physical_design,
        instance_name=VREF_SWITCH_INSTANCE_NAME,
        terminal_name="control_bar",
        child_port_name="control_bar_E",
    )
    vss_select_bar = _access(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="control",
        child_port_name="control_W",
    )
    select_bar_width = _resolved_width(
        intent=intent,
        first=vref_select_bar,
        second=vss_select_bar,
    )
    child_gap = vss_instance.bbox.xmin - vref_instance.bbox.xmax
    if child_gap <= select_bar_width:
        raise RuntimeError(
            "reference-selector child gap cannot contain the SELECT_BAR trunk: "
            f"gap={child_gap}, route_width={select_bar_width}"
        )
    central_x = (vref_instance.bbox.xmax + vss_instance.bbox.xmin) / 2.0
    if not (
        vref_select_bar.center[0]
        < central_x
        < vss_select_bar.center[0]
    ):
        raise RuntimeError(
            "reference-selector SELECT_BAR accesses do not face the central gap: "
            f"left={vref_select_bar.center!r}, central_x={central_x}, "
            f"right={vss_select_bar.center!r}"
        )
    select_bar_plan = _route_plan(
        net_name=SELECT_BAR_NET_NAME,
        first=vref_select_bar,
        second=vss_select_bar,
        points=(
            vref_select_bar.center,
            (central_x, vref_select_bar.center[1]),
            (central_x, vss_select_bar.center[1]),
            vss_select_bar.center,
        ),
        intent=intent,
        strategy="reference_selector_central_gap_control",
        detail=(
            f"single central-gap trunk x={central_x}, "
            f"child gap={child_gap}"
        ),
    )

    vref_vss = _access(
        physical_design,
        instance_name=VREF_SWITCH_INSTANCE_NAME,
        terminal_name="vss",
        child_port_name="vss_N",
    )
    vss_vss = _access(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="vss",
        child_port_name="vss_N",
    )
    vss_signal = _access(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="input",
        child_port_name="input_E",
    )
    vss_accesses = (vref_vss, vss_vss, vss_signal)
    vss_width = _resolved_supply_width(
        intent=intent,
        accesses=vss_accesses,
        signal_anchor=vss_signal,
    )

    child_top = max(vref_instance.bbox.ymax, vss_instance.bbox.ymax)
    top_opening = top_channel - select_width / 2.0 - child_top
    right_opening = (
        select_right - select_width / 2.0 - vss_instance.bbox.xmax
    )
    supply_lane_fits = (
        top_opening > vss_width and right_opening > vss_width
    )
    if not supply_lane_fits:
        raise RuntimeError(
            "reference-selector SELECT channel cannot contain the VSS escape: "
            f"top_opening={top_opening}, right_opening={right_opening}, "
            f"route_width={vss_width}"
        )
    vss_rail_y = child_top + top_opening / 2.0
    vss_service_x = vss_instance.bbox.xmax + right_opening / 2.0
    outward_vss_accesses = (
        vref_vss.center[1] < vss_rail_y
        and vss_vss.center[1] < vss_rail_y
        and vss_signal.center[0] < vss_service_x
        and vref_vss.center[0] < vss_vss.center[0] < vss_service_x
    )
    if not outward_vss_accesses:
        raise RuntimeError(
            "reference-selector VSS accesses do not face the north/right "
            "supply channels"
        )
    vss_plan = _route_tree_plan(
        net_name=VSS_NET_NAME,
        accesses=vss_accesses,
        segment_endpoints=(
            (
                vref_vss.center,
                (vref_vss.center[0], vss_rail_y),
            ),
            (
                vss_vss.center,
                (vss_vss.center[0], vss_rail_y),
            ),
            (
                (vref_vss.center[0], vss_rail_y),
                (vss_service_x, vss_rail_y),
            ),
            (
                vss_signal.center,
                (vss_service_x, vss_signal.center[1]),
            ),
            (
                (vss_service_x, vss_signal.center[1]),
                (vss_service_x, vss_rail_y),
            ),
        ),
        width=vss_width,
        strategy="reference_selector_north_vss_rail",
        detail=(
            f"north rail y={vss_rail_y}, right service channel "
            f"x={vss_service_x}"
        ),
        extra_checks=(
            ConstraintCheck(
                name="supply_lane_clearance",
                passed=supply_lane_fits,
                hard=True,
                detail=(
                    f"top opening {top_opening}, right opening {right_opening}"
                ),
            ),
            ConstraintCheck(
                name="outward_supply_accesses",
                passed=outward_vss_accesses,
                hard=True,
                detail="north bulk ties and east VSS input face their channels",
            ),
        ),
    )

    vref_vdd = _access(
        physical_design,
        instance_name=VREF_SWITCH_INSTANCE_NAME,
        terminal_name="vdd",
        child_port_name="vdd_S",
    )
    vss_vdd = _access(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="vdd",
        child_port_name="vdd_S",
    )
    vdd_accesses = (vref_vdd, vss_vdd)
    vdd_width = _resolved_supply_width(
        intent=intent,
        accesses=vdd_accesses,
        signal_anchor=vss_signal,
    )
    child_bottom = min(vref_instance.bbox.ymin, vss_instance.bbox.ymin)
    vdd_rail_y = (
        child_bottom - intent.policy.channel_clearance - vdd_width / 2.0
    )
    outward_vdd_accesses = (
        vref_vdd.center[1] > vdd_rail_y
        and vss_vdd.center[1] > vdd_rail_y
        and vref_vdd.center[0] < vss_vdd.center[0]
    )
    if not outward_vdd_accesses:
        raise RuntimeError(
            "reference-selector VDD accesses do not face the south supply channel"
        )
    vdd_plan = _route_tree_plan(
        net_name=VDD_NET_NAME,
        accesses=vdd_accesses,
        segment_endpoints=(
            (
                vref_vdd.center,
                (vref_vdd.center[0], vdd_rail_y),
            ),
            (
                (vref_vdd.center[0], vdd_rail_y),
                (vss_vdd.center[0], vdd_rail_y),
            ),
            (
                vss_vdd.center,
                (vss_vdd.center[0], vdd_rail_y),
            ),
        ),
        width=vdd_width,
        strategy="reference_selector_south_vdd_rail",
        detail=f"south rail y={vdd_rail_y}",
        extra_checks=(
            ConstraintCheck(
                name="outward_supply_accesses",
                passed=outward_vdd_accesses,
                hard=True,
                detail="south bulk ties face the VDD rail",
            ),
        ),
    )

    return ReferenceSelectorRouteBundle(
        common_plan=common_plan,
        select_plan=select_plan,
        select_bar_plan=select_bar_plan,
        vss_plan=vss_plan,
        vdd_plan=vdd_plan,
    )
