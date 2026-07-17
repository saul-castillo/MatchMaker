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
    width = (
        float(intent.policy.route_width)
        if intent.policy.route_width is not None
        else min(first.width, second.width)
    )
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
            "runtime child-cell access coordinates and layers",
            detail,
        ),
    )


def plan_reference_selector_topology(
    *,
    intent: ReferenceSelectorLayoutIntent,
    physical_design: PhysicalDesignSnapshot,
) -> ReferenceSelectorRouteBundle:
    """Plan the common output and complementary control topology."""

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
        child_port_name="control_N",
    )
    vss_select = _access(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="control_bar",
        child_port_name="control_bar_N",
    )
    top_channel = (
        max(instance.bbox.ymax for instance in physical_design.instances.values())
        + intent.policy.channel_clearance
    )
    select_plan = _route_plan(
        net_name=SELECT_NET_NAME,
        first=vref_select,
        second=vss_select,
        points=(
            vref_select.center,
            (vref_select.center[0], top_channel),
            (vss_select.center[0], top_channel),
            vss_select.center,
        ),
        intent=intent,
        strategy="reference_selector_north_control_channel",
        detail=f"north control channel at y={top_channel}",
    )

    vref_select_bar = _access(
        physical_design,
        instance_name=VREF_SWITCH_INSTANCE_NAME,
        terminal_name="control_bar",
        child_port_name="control_bar_S",
    )
    vss_select_bar = _access(
        physical_design,
        instance_name=VSS_SWITCH_INSTANCE_NAME,
        terminal_name="control",
        child_port_name="control_S",
    )
    bottom_channel = (
        min(instance.bbox.ymin for instance in physical_design.instances.values())
        - intent.policy.channel_clearance
    )
    select_bar_plan = _route_plan(
        net_name=SELECT_BAR_NET_NAME,
        first=vref_select_bar,
        second=vss_select_bar,
        points=(
            vref_select_bar.center,
            (vref_select_bar.center[0], bottom_channel),
            (vss_select_bar.center[0], bottom_channel),
            vss_select_bar.center,
        ),
        intent=intent,
        strategy="reference_selector_south_control_channel",
        detail=f"south control channel at y={bottom_channel}",
    )

    return ReferenceSelectorRouteBundle(
        common_plan=common_plan,
        select_plan=select_plan,
        select_bar_plan=select_bar_plan,
    )
