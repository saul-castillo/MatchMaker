from dataclasses import dataclass
from math import isclose

from matchmaker.design.reference_selector_naming import (
    COMMON_NET_NAME,
    SELECT_BAR_NET_NAME,
    SELECT_NET_NAME,
    VREF_SWITCH_INSTANCE_NAME,
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

    @property
    def plans(self) -> tuple[RoutePlan, RoutePlan, RoutePlan]:
        return self.common_plan, self.select_plan, self.select_bar_plan


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


def plan_reference_selector_topology(
    *,
    intent: ReferenceSelectorLayoutIntent,
    physical_design: PhysicalDesignSnapshot,
) -> ReferenceSelectorRouteBundle:
    """Plan the common output and complementary control topology.

    Control routes first leave each child through horizontal gate accesses. Their
    vertical channel legs therefore remain outside child bboxes instead of
    crossing the generated MOS interiors.
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
    perimeter_offset = intent.policy.channel_clearance + select_width / 2.0
    left_channel = vref_instance.bbox.xmin - perimeter_offset
    right_channel = vss_instance.bbox.xmax + perimeter_offset
    top_channel = (
        max(vref_instance.bbox.ymax, vss_instance.bbox.ymax) + perimeter_offset
    )
    select_plan = _route_plan(
        net_name=SELECT_NET_NAME,
        first=vref_select,
        second=vss_select,
        points=(
            vref_select.center,
            (left_channel, vref_select.center[1]),
            (left_channel, top_channel),
            (right_channel, top_channel),
            (right_channel, vss_select.center[1]),
            vss_select.center,
        ),
        intent=intent,
        strategy="reference_selector_north_perimeter_control",
        detail=(
            f"north perimeter channel y={top_channel}, "
            f"x={left_channel}..{right_channel}"
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
    required_corridor = select_bar_width + intent.policy.channel_spacing
    if child_gap <= required_corridor:
        raise RuntimeError(
            "reference-selector child gap cannot support the inner control corridor: "
            f"gap={child_gap}, required>{required_corridor}"
        )
    available_edge_clearance = (child_gap - required_corridor) / 2.0
    inner_clearance = min(
        intent.policy.channel_clearance,
        available_edge_clearance,
    )
    left_inner_channel = (
        vref_instance.bbox.xmax + inner_clearance + select_bar_width / 2.0
    )
    right_inner_channel = (
        vss_instance.bbox.xmin - inner_clearance - select_bar_width / 2.0
    )
    bottom_channel = (
        min(vref_instance.bbox.ymin, vss_instance.bbox.ymin)
        - intent.policy.channel_clearance
        - select_bar_width / 2.0
    )
    select_bar_plan = _route_plan(
        net_name=SELECT_BAR_NET_NAME,
        first=vref_select_bar,
        second=vss_select_bar,
        points=(
            vref_select_bar.center,
            (left_inner_channel, vref_select_bar.center[1]),
            (left_inner_channel, bottom_channel),
            (right_inner_channel, bottom_channel),
            (right_inner_channel, vss_select_bar.center[1]),
            vss_select_bar.center,
        ),
        intent=intent,
        strategy="reference_selector_south_inner_control",
        detail=(
            f"south channel y={bottom_channel}, inner corridor "
            f"x={left_inner_channel}..{right_inner_channel}"
        ),
    )

    return ReferenceSelectorRouteBundle(
        common_plan=common_plan,
        select_plan=select_plan,
        select_bar_plan=select_bar_plan,
    )
