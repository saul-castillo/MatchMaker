from matchmaker.physical.models import PhysicalDesignSnapshot
from matchmaker.routing.intents.net_intent import NetIntent
from matchmaker.routing.planners.route_candidate import (
    RouteCandidate,
    RoutePlanningError,
    StrategyDispatchResult,
)
from matchmaker.routing.planners.two_terminal_strategy_dispatcher import (
    dispatch_two_terminal_routes,
)


AccessSelection = RouteCandidate


def select_two_terminal_access(
    intent: NetIntent,
    physical_design: PhysicalDesignSnapshot,
) -> AccessSelection:
    """Compatibility wrapper returning the dispatcher-selected route candidate."""
    return dispatch_two_terminal_routes(intent, physical_design).selected


__all__ = [
    "AccessSelection",
    "RoutePlanningError",
    "StrategyDispatchResult",
    "dispatch_two_terminal_routes",
    "select_two_terminal_access",
]
