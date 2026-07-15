from dataclasses import dataclass
from math import isclose
from typing import Literal

from matchmaker.physical.models import AccessPoint, PhysicalDesignSnapshot
from matchmaker.routing.intents.net_intent import NetIntent
from matchmaker.routing.planners.obstacle_aware_route_planner import (
    find_straight_route_blockers,
)
from matchmaker.routing.planners.spatial_dogleg_planner import (
    DoglegDirection,
    choose_spatial_dogleg,
)


SelectionStrategy = Literal["straight", "dogleg"]


class RoutePlanningError(RuntimeError):
    pass


@dataclass(frozen=True)
class AccessSelection:
    source: AccessPoint
    target: AccessPoint
    strategy: SelectionStrategy
    blockers: tuple[str, ...]
    estimated_length: float
    bend_count: int
    estimated_cost: float
    source_bend: tuple[float, float] | None = None
    target_bend: tuple[float, float] | None = None
    channel_direction: DoglegDirection | None = None
    channel_coordinate: float | None = None
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class _Candidate:
    selection: AccessSelection
    sort_key: tuple[object, ...]


def _normalized_orientation(access: AccessPoint) -> int:
    orientation = int(round(float(access.orientation))) % 360
    if orientation not in {0, 90, 180, 270}:
        raise RoutePlanningError(
            f"Physical access {access.name!r} is not Manhattan: {access.orientation}"
        )
    return orientation


def _supports_straight_axis(source: AccessPoint, target: AccessPoint) -> bool:
    source_x, source_y = source.center
    target_x, target_y = target.center
    source_orientation = _normalized_orientation(source)
    target_orientation = _normalized_orientation(target)

    if isclose(source_y, target_y, abs_tol=1e-9):
        return source_orientation in {0, 180} and target_orientation in {0, 180}
    if isclose(source_x, target_x, abs_tol=1e-9):
        return source_orientation in {90, 270} and target_orientation in {90, 270}
    return False


def _layer_is_allowed(access: AccessPoint, intent: NetIntent) -> bool:
    constraints = intent.constraints
    if constraints.allowed_layers and access.layer not in constraints.allowed_layers:
        return False
    if access.layer in constraints.forbidden_layers:
        return False
    return True


def _dogleg_points(
    source: AccessPoint,
    target: AccessPoint,
    source_bend: tuple[float, float],
    target_bend: tuple[float, float],
    direction: DoglegDirection,
    channel_coordinate: float,
) -> tuple[tuple[float, float], ...]:
    if direction in {"N", "S"}:
        return (
            source.center,
            source_bend,
            (source_bend[0], channel_coordinate),
            (target_bend[0], channel_coordinate),
            target_bend,
            target.center,
        )
    return (
        source.center,
        source_bend,
        (channel_coordinate, source_bend[1]),
        (channel_coordinate, target_bend[1]),
        target_bend,
        target.center,
    )


def _polyline_length(points: tuple[tuple[float, float], ...]) -> float:
    return sum(
        abs(second[0] - first[0]) + abs(second[1] - first[1])
        for first, second in zip(points, points[1:])
    )


def _candidate_within_hard_limits(selection: AccessSelection, intent: NetIntent) -> bool:
    constraints = intent.constraints
    if constraints.max_length is not None:
        if selection.estimated_length > constraints.max_length + 1e-9:
            return False
    if constraints.max_bends is not None:
        if selection.bend_count > constraints.max_bends:
            return False
    return True


def _candidate_cost(length: float, bends: int, intent: NetIntent) -> float:
    constraints = intent.constraints
    return constraints.length_weight * length + constraints.bend_penalty * bends


def select_two_terminal_access(
    intent: NetIntent,
    physical_design: PhysicalDesignSnapshot,
) -> AccessSelection:
    """Select physical access and a coarse path for a two-terminal logical net.

    Candidate generation is deterministic. Hard constraints reject candidates
    before soft costs are compared. The current slice supports same-layer inline
    straight routes and same-layer external spatial doglegs.
    """
    if len(intent.terminals) != 2:
        raise RoutePlanningError(
            "two-terminal access selection requires exactly two logical terminals"
        )

    source_terminal, target_terminal = intent.terminals
    source_accesses = tuple(
        access
        for access in physical_design.access_points_for(source_terminal)
        if _layer_is_allowed(access, intent)
    )
    target_accesses = tuple(
        access
        for access in physical_design.access_points_for(target_terminal)
        if _layer_is_allowed(access, intent)
    )
    if not source_accesses:
        raise RoutePlanningError(
            f"No allowed physical access points for {source_terminal}"
        )
    if not target_accesses:
        raise RoutePlanningError(
            f"No allowed physical access points for {target_terminal}"
        )

    obstacles = physical_design.obstacles + physical_design.keepouts
    excluded_instances = (
        source_terminal.instance_name,
        target_terminal.instance_name,
    )
    candidates: dict[tuple[object, ...], _Candidate] = {}

    for source in source_accesses:
        for target in target_accesses:
            if source.layer != target.layer:
                continue
            if not _supports_straight_axis(source, target):
                continue

            blockers = find_straight_route_blockers(
                source_port=source,
                target_port=target,
                obstacles=obstacles,
                excluded_instance_names=excluded_instances,
                clearance=float(intent.constraints.obstacle_clearance),
            )
            direct_is_legal = not blockers or not intent.constraints.avoid_obstacles

            if (
                direct_is_legal
                and intent.strategy_preference in {"auto", "straight"}
            ):
                length = _polyline_length((source.center, target.center))
                cost = _candidate_cost(length, 0, intent)
                selection = AccessSelection(
                    source=source,
                    target=target,
                    strategy="straight",
                    blockers=() if intent.constraints.avoid_obstacles else blockers,
                    estimated_length=length,
                    bend_count=0,
                    estimated_cost=cost,
                    provenance=(
                        "logical-terminal access enumeration",
                        "clear same-layer inline candidate",
                    ),
                )
                if _candidate_within_hard_limits(selection, intent):
                    key = ("straight", source.name, target.name)
                    candidates[key] = _Candidate(
                        selection=selection,
                        sort_key=(cost, 0, source.name, target.name),
                    )

            should_try_dogleg = intent.strategy_preference == "dogleg" or (
                intent.strategy_preference == "auto"
                and intent.constraints.avoid_obstacles
                and bool(blockers)
            )
            if not should_try_dogleg:
                continue

            try:
                dogleg = choose_spatial_dogleg(
                    ports=physical_design.access_points,
                    source_instance_name=source_terminal.instance_name,
                    source_port_name=source.primitive_port_name,
                    target_instance_name=target_terminal.instance_name,
                    target_port_name=target.primitive_port_name,
                    source_port=source,
                    target_port=target,
                    obstacles=obstacles,
                    clearance=max(float(intent.constraints.obstacle_clearance), 1.0),
                )
            except RuntimeError:
                continue

            actual_source = physical_design.access_point(
                dogleg.source_top_port_name
            )
            actual_target = physical_design.access_point(
                dogleg.target_top_port_name
            )
            if actual_source.layer != actual_target.layer:
                continue
            if not _layer_is_allowed(actual_source, intent):
                continue
            if not _layer_is_allowed(actual_target, intent):
                continue

            points = _dogleg_points(
                source=actual_source,
                target=actual_target,
                source_bend=dogleg.source_bend,
                target_bend=dogleg.target_bend,
                direction=dogleg.direction,
                channel_coordinate=float(dogleg.channel_coordinate),
            )
            length = _polyline_length(points)
            cost = _candidate_cost(length, 4, intent)
            selection = AccessSelection(
                source=actual_source,
                target=actual_target,
                strategy="dogleg",
                blockers=blockers,
                estimated_length=length,
                bend_count=4,
                estimated_cost=cost,
                source_bend=dogleg.source_bend,
                target_bend=dogleg.target_bend,
                channel_direction=dogleg.direction,
                channel_coordinate=float(dogleg.channel_coordinate),
                provenance=(
                    "logical-terminal access enumeration",
                    "blocked inline candidate",
                    "outward access selection",
                    "external spatial channel",
                ),
            )
            if not _candidate_within_hard_limits(selection, intent):
                continue
            key = (
                "dogleg",
                actual_source.name,
                actual_target.name,
                dogleg.direction,
                float(dogleg.channel_coordinate),
            )
            candidate = _Candidate(
                selection=selection,
                sort_key=(
                    cost,
                    1,
                    actual_source.name,
                    actual_target.name,
                    dogleg.direction,
                ),
            )
            existing = candidates.get(key)
            if existing is None or candidate.sort_key < existing.sort_key:
                candidates[key] = candidate

    if not candidates:
        raise RoutePlanningError(
            f"No feasible access/path candidate for logical net {intent.name!r}"
        )

    return min(candidates.values(), key=lambda candidate: candidate.sort_key).selection
