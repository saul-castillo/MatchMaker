from collections import Counter

from matchmaker.physical.models import AccessPoint, PhysicalDesignSnapshot
from matchmaker.routing.intents.net_intent import NetIntent
from matchmaker.routing.planners.dogleg_route_strategy import plan_dogleg_candidate
from matchmaker.routing.planners.manhattan_route_strategy import plan_manhattan_candidates
from matchmaker.routing.planners.route_candidate import (
    CandidateRejection,
    RouteCandidate,
    RoutePlanningError,
    StrategyDispatchResult,
)
from matchmaker.routing.planners.straight_route_strategy import plan_straight_candidate


_STRATEGY_ORDER = {
    "straight": 0,
    "manhattan": 1,
    "dogleg": 2,
}


def _layer_is_allowed(access: AccessPoint, intent: NetIntent) -> bool:
    constraints = intent.constraints
    if constraints.allowed_layers and access.layer not in constraints.allowed_layers:
        return False
    return access.layer not in constraints.forbidden_layers


def _candidate_within_hard_limits(candidate: RouteCandidate, intent: NetIntent) -> bool:
    constraints = intent.constraints
    if constraints.max_length is not None:
        if candidate.estimated_length > constraints.max_length + 1e-9:
            return False
    if constraints.max_bends is not None:
        if candidate.bend_count > constraints.max_bends:
            return False
    return True


def _candidate_sort_key(candidate: RouteCandidate) -> tuple[object, ...]:
    return (
        candidate.estimated_cost,
        _STRATEGY_ORDER[candidate.strategy],
        candidate.bend_count,
        candidate.source.name,
        candidate.target.name,
        candidate.points,
    )


def _enabled_strategies(intent: NetIntent) -> tuple[str, ...]:
    if intent.strategy_preference == "auto":
        return ("straight", "manhattan", "dogleg")
    return (intent.strategy_preference,)


def _append_candidate(
    *,
    candidate: RouteCandidate,
    intent: NetIntent,
    candidates: dict[tuple[object, ...], RouteCandidate],
    rejections: list[CandidateRejection],
) -> None:
    if not _candidate_within_hard_limits(candidate, intent):
        constraints = intent.constraints
        detail = (
            f"length={candidate.estimated_length}, max_length={constraints.max_length}; "
            f"bends={candidate.bend_count}, max_bends={constraints.max_bends}"
        )
        rejections.append(
            CandidateRejection(
                strategy=candidate.strategy,
                reason="hard-limit",
                source_access_name=candidate.source.name,
                target_access_name=candidate.target.name,
                detail=detail,
            )
        )
        return

    existing = candidates.get(candidate.identity_key)
    if existing is None or _candidate_sort_key(candidate) < _candidate_sort_key(existing):
        candidates[candidate.identity_key] = candidate


def _failure_summary(rejections: tuple[CandidateRejection, ...]) -> str:
    if not rejections:
        return "no strategy produced a candidate"
    counts = Counter(rejection.reason for rejection in rejections)
    return ", ".join(
        f"{reason}={count}" for reason, count in sorted(counts.items())
    )


def dispatch_two_terminal_routes(
    intent: NetIntent,
    physical_design: PhysicalDesignSnapshot,
) -> StrategyDispatchResult:
    """Run enabled routing strategies and select the lowest-cost valid candidate."""
    if len(intent.terminals) != 2:
        raise RoutePlanningError(
            "two-terminal strategy dispatch requires exactly two logical terminals"
        )

    source_terminal, target_terminal = intent.terminals
    source_accesses = tuple(
        sorted(
            (
                access
                for access in physical_design.access_points_for(source_terminal)
                if _layer_is_allowed(access, intent)
            ),
            key=lambda access: access.name,
        )
    )
    target_accesses = tuple(
        sorted(
            (
                access
                for access in physical_design.access_points_for(target_terminal)
                if _layer_is_allowed(access, intent)
            ),
            key=lambda access: access.name,
        )
    )
    if not source_accesses:
        raise RoutePlanningError(f"No allowed physical access points for {source_terminal}")
    if not target_accesses:
        raise RoutePlanningError(f"No allowed physical access points for {target_terminal}")

    enabled = _enabled_strategies(intent)
    candidates: dict[tuple[object, ...], RouteCandidate] = {}
    rejections: list[CandidateRejection] = []

    for source in source_accesses:
        for target in target_accesses:
            if source.layer != target.layer:
                rejections.append(
                    CandidateRejection(
                        strategy="dispatcher",
                        reason="layer-transition-required",
                        source_access_name=source.name,
                        target_access_name=target.name,
                    )
                )
                continue

            if "straight" in enabled:
                candidate, rejection = plan_straight_candidate(
                    intent=intent,
                    physical_design=physical_design,
                    source=source,
                    target=target,
                )
                if rejection is not None:
                    rejections.append(rejection)
                if candidate is not None:
                    _append_candidate(
                        candidate=candidate,
                        intent=intent,
                        candidates=candidates,
                        rejections=rejections,
                    )

            if "manhattan" in enabled:
                generated, rejected = plan_manhattan_candidates(
                    intent=intent,
                    physical_design=physical_design,
                    source=source,
                    target=target,
                )
                rejections.extend(rejected)
                for candidate in generated:
                    _append_candidate(
                        candidate=candidate,
                        intent=intent,
                        candidates=candidates,
                        rejections=rejections,
                    )

            if "dogleg" in enabled:
                candidate, rejection = plan_dogleg_candidate(
                    intent=intent,
                    physical_design=physical_design,
                    source=source,
                    target=target,
                    force=intent.strategy_preference == "dogleg",
                )
                if rejection is not None:
                    rejections.append(rejection)
                if candidate is not None:
                    _append_candidate(
                        candidate=candidate,
                        intent=intent,
                        candidates=candidates,
                        rejections=rejections,
                    )

    ordered_candidates = tuple(sorted(candidates.values(), key=_candidate_sort_key))
    rejection_tuple = tuple(rejections)
    if not ordered_candidates:
        raise RoutePlanningError(
            f"No feasible route candidate for logical net {intent.name!r}: "
            + _failure_summary(rejection_tuple)
        )

    return StrategyDispatchResult(
        selected=ordered_candidates[0],
        candidates=ordered_candidates,
        rejections=rejection_tuple,
    )
