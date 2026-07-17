# ADR 0002: Modular routing strategy dispatch

Status: Accepted

## Context

MatchMaker has a stable logical routing contract:

```text
NetIntent + PhysicalDesignSnapshot -> RoutePlan -> geometry -> verification
```

The first implementation selected between a clear straight route and an external dogleg inside one access-selector module. That was sufficient for the initial centroid regression but does not scale cleanly to non-inline Manhattan routes, graph search, matched groups, CDAC templates, or device-specific routing behavior.

A single universal router is also not appropriate for analog layout. Different route classes have different feasibility rules and topology requirements, while all routes still need common intent, physical state, metrics, execution, and verification contracts.

## Decision

Use a deterministic strategy dispatcher over independent pure planner modules.

Each strategy:

- consumes `NetIntent`, `PhysicalDesignSnapshot`, and candidate physical access points;
- performs only its own topology and geometric feasibility checks;
- returns zero or more typed `RouteCandidate` objects plus typed rejection evidence;
- never mutates the layout component;
- never executes geometry.

The dispatcher:

- enumerates logical-terminal access pairs;
- applies common layer eligibility;
- invokes enabled strategies;
- applies common hard limits such as maximum length and bend count;
- deduplicates candidates;
- ranks valid candidates deterministically;
- returns `StrategyDispatchResult` containing the selected candidate, all feasible candidates, and all rejections.

Current strategies are:

```text
straight_route_strategy.py
manhattan_route_strategy.py
  - perpendicular-access L routes
  - parallel-access Z routes
  - midpoint, obstacle-edge, and outer channel candidates
dogleg_route_strategy.py
  - aligned external spatial channel
```

All strategies emit the same `RouteCandidate`, and the selected candidate is compiled into the common `RoutePlan`.

## Device-specific extension model

Device-specific knowledge does not belong inside the generic dispatcher.

Physical adapters expose logical terminals and valid access points:

```text
MOS adapter -> gate/source/drain/bulk accesses
capacitor adapter -> top/bottom plate accesses
switch adapter -> input/output/control accesses
```

Analog topology planners may be added as strategies:

```text
DifferentialPairStrategy
MatchedBusStrategy
ShieldedNetStrategy
CdacRoutingTemplateStrategy
RectilinearGraphStrategy
```

They must use the same candidate, plan, executor, and verification contracts.

## Consequences

Positive:

- routing policy is no longer concentrated in one growing selector;
- specialized analog planners can be added without changing execution;
- candidate rejection evidence becomes inspectable;
- strategy behavior can be unit-tested independently;
- unsupported cases fail explicitly;
- deterministic tie-breaking is centralized.

Costs and limitations:

- candidate enumeration may grow quickly as access counts and strategy counts increase;
- the current dispatcher is two-terminal and same-layer only;
- route-to-route obstacles, congestion, vias, and PDK rule resolution remain future work;
- strategy registration is static rather than plugin-discovered.

## Invariants

1. Strategies are pure planners and do not mutate components.
2. Executors do not choose topology, access, channel, layer, or width.
3. Hard constraints reject candidates before soft-cost ranking.
4. Every candidate records provenance and exact geometry.
5. New strategies require pure tests and `/foss` integration validation.
6. DRC does not substitute for extracted connectivity or LVS.

## Next evolution

1. incorporate committed routes as obstacles and routing resources;
2. add PDK width, layer, and via rule resolution;
3. add multi-terminal topology planning;
4. add matched and differential route-group strategies;
5. add coarse graph search and congestion negotiation;
6. add CDAC-specific topology templates.
