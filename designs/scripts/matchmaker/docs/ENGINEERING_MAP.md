# MatchMaker Engineering Map

This is the first document to read before changing the engine. It is maintained for human contributors and coding agents that need to recover the architecture, current validation boundary, package ownership, and next development step without reconstructing them from examples or commit history.

## Read order

```text
1. docs/ENGINEERING_MAP.md
2. docs/adr/0001-constraint-driven-hybrid-routing.md
3. docs/adr/0002-modular-routing-strategy-dispatch.md
4. docs/VALIDATION_STATUS.md
5. the module being changed
6. its tests
```

`VALIDATION_STATUS.md` is the source of truth for results demonstrated in the Chipathon `/foss` environment. Unit tests and plausible geometry are not physical integration validation.

## Mission

MatchMaker is a deterministic, constraint-driven analog layout synthesis engine targeting GF180 through gLayout. It must translate structured circuit and layout intent into geometry while preserving connectivity, matching intent, symmetry, electrical constraints, and verification evidence.

Long-term targets include matched MOS structures, switch networks, capacitor arrays, CDACs, comparators, and larger analog cells.

## Golden pipeline

```text
high-level circuit/layout intent
-> typed device, placement, net, and route-group intent
-> deterministic placement plan
-> PhysicalDesignSnapshot
-> routing strategy dispatch
-> RouteCandidate selection
-> RoutePlan
-> mechanical geometry execution
-> GDS
-> DRC
-> extraction and connectivity audit
-> LVS
-> targeted repair or accepted cell
```

Each major module owns one translation. Planning must not be hidden in examples, geometry executors, or verification adapters.

## Stable validated flow on main

The merged flow has demonstrated:

```text
MOS centroid intent
-> deterministic GF180 placement
-> filtered PhysicalDesignSnapshot
-> logical NetIntent(A0.gate, A1.gate)
-> automatic access selection
-> external same-layer dogleg
-> RoutePlan and metrics
-> GDS
-> Magic DRC: zero violations
-> Magic extraction
-> exact connectivity: two intended A devices only
```

The logical routing demo automatically recovered `A0__gate_W` and `A1__gate_E`, reduced promoted access points from 21,520 hierarchy ports to 128 canonical MOS accesses, and passed DRC, extraction, and connectivity gating.

## Current development slice

Branch: `feature/manhattan-routing-dispatcher`

The branch separates strategy generation from dispatch and adds general same-layer non-inline Manhattan routing:

```text
NetIntent + PhysicalDesignSnapshot
-> enumerate terminal access pairs
-> straight strategy
-> L/Z Manhattan strategy
-> external dogleg strategy
-> typed candidate rejections
-> common hard-limit filtering
-> deterministic ranking
-> RoutePlan
```

Current pure tests and Python compilation pass. `/foss` validation is still required for both the default dogleg regression and a diagonal `A0.gate` to `A2.gate` Manhattan route.

## Core routing principle

Routing is constrained physical synthesis, not a call between two named primitive ports.

Canonical input:

```text
logical net or route group
+ logical terminals
+ typed hard constraints
+ typed soft-cost weights
+ physical access choices
+ placed obstacles and keepouts
+ routing-layer resources
+ committed routes
```

Canonical output:

```text
RoutePlan
+ selected access points
+ strategy/topology
+ exact Manhattan segments and vias
+ resolved width and layers
+ metrics
+ constraint evidence
+ blockers
+ provenance
```

Geometry is generated only after the plan is complete.

## Logical terminal versus physical access

Logical terminal:

```text
A0.gate
CAP3.top
SW1.output
```

Physical access:

```text
A0__gate_E
A0__gate_W
CAP3__top_N
```

`PhysicalDesignSnapshot.access_points_for(TerminalRef(...))` is the canonical bridge from electrical identity to physical choices.

Device-specific adapters own this translation. The MOS adapter recognizes canonical gate/source/drain/bulk ports and filters nested gLayout hierarchy ports. Future capacitor, resistor, switch, and comparator adapters should expose their own logical terminals and legal physical accesses without changing the generic routing contracts.

## Canonical data contracts

### Intent

`routing/intents/net_intent.py`

```text
NetIntent
NetConstraintProfile
RouteGroupIntent
RouteGroupConstraintProfile
```

`NetConstraintProfile` currently carries:

- width class and optional explicit width;
- obstacle avoidance and clearance;
- allowed and forbidden layers;
- maximum length and bend count;
- length, bend, and via cost weights;
- priority.

Route-group fields reserve typed requirements for separation, matching, symmetry, equal bend/via count, and shielding. Group planning is not implemented yet.

### Physical state

`physical/models.py`

```text
TerminalRef
AccessPoint
PlacedInstance
RoutingObstacle
PhysicalDesignSnapshot
```

Snapshot mappings are read-only. Routing code must not rediscover physical identity from reference order or store planning state in `Component.info`.

### Candidate and dispatch evidence

`routing/planners/route_candidate.py`

```text
RouteCandidate
CandidateRejection
StrategyDispatchResult
RoutePlanningError
```

A candidate contains selected accesses, exact path points, resolved width, strategy, length, bends, cost, blockers, channel data, and provenance.

A dispatch result retains:

```text
selected candidate
all feasible candidates
all rejected candidates with reasons
```

### Route-plan IR

`routing/plans/route_plan.py`

```text
RoutePlan
RouteSegment
ViaPlan
RouteMetrics
ConstraintCheck
```

A valid plan contains only nonzero Manhattan segments, internally consistent metrics, and no failed hard constraint.

## Modular routing strategies

See ADR 0002.

Current pure strategies:

```text
straight_route_strategy.py
  clear outward-compatible inline connection

manhattan_route_strategy.py
  perpendicular-access L paths
  parallel-access Z paths
  midpoint, obstacle-edge, and outer channel candidates

dogleg_route_strategy.py
  aligned external spatial channel around a blocked row/column
```

`two_terminal_strategy_dispatcher.py` owns common access enumeration, layer compatibility, hard-limit filtering, deduplication, deterministic ranking, and rejection summaries.

`two_terminal_net_planner.py` compiles the selected candidate into `RoutePlan` and retains strategy evidence through `plan_two_terminal_net_with_report(...)`.

## Strategy/plugin model

Do not build one universal analog router prematurely.

There are three extension categories:

### Physical adapters

```text
MOS adapter
capacitor adapter
resistor adapter
transmission-gate adapter
comparator adapter
```

They expose logical terminals, physical accesses, obstacles, and local keepouts.

### Routing strategies

```text
StraightRouteStrategy
ManhattanRouteStrategy
SpatialDoglegStrategy
RectilinearGraphStrategy
DifferentialPairStrategy
MatchedBusStrategy
ShieldedNetStrategy
CdacRoutingTemplateStrategy
```

They consume common intent and snapshot contracts and emit common route candidates/plans.

### PDK rule adapters

They will resolve semantic intent such as `signal`, `high_current`, or `high_voltage` into GF180-specific widths, layers, spacing, vias, arrays, and enclosures.

Strategy registration is currently static. Dynamic plugin discovery is unnecessary until several stable strategy families exist.

## Hard constraints and soft costs

Hard constraints reject candidates:

- intended connectivity;
- no unrelated terminals;
- allowed/forbidden layers;
- obstacle and keepout avoidance;
- maximum length, bends, vias, or resistance;
- width, spacing, enclosure, and via legality;
- mandatory symmetry, matching, shielding, or separation.

Soft costs rank valid candidates:

- length;
- bends and vias;
- estimated resistance/capacitance;
- congestion;
- coupling exposure;
- matched-length error;
- symmetry deviation;
- scarce resource use.

Hard checks always precede ranking.

## Execution boundary

`routing/routers/route_plan_executor.py`

The executor draws resolved `RouteSegment` geometry. It does not choose terminals, access points, topology, strategy, channel, width, or layer. Via execution remains unimplemented and fails explicitly.

## Verification boundary

```text
DRC pass != connectivity pass
```

Every routing integration test that changes connectivity must include extraction or LVS evidence.

Current verification:

```text
Magic DRC
-> Magic SPICE extraction
-> exact shared-net participant assertion
-> Netgen LVS infrastructure
```

The current connectivity assertion infers participants through extracted subcircuit names. Stable logical instance identity through extraction remains future work.

## Package ownership

```text
specs/
  PDK-independent device specifications

placement/core/
  reusable tile, grid, plan, orientation, and spacing infrastructure

placement/mos/
  MOS intent compilation, dummy policy, binding, and placement

physical/
  placed instances, terminals, accesses, obstacles, and snapshots

primitives/
  PDK/gLayout primitive construction

routing/intents/
  logical net and route-group requests

routing/planners/
  pure strategy modules, dispatch, obstacle checks, and plan compilation

routing/plans/
  common execution-ready IR and metrics

routing/routers/
  mechanical geometry execution

verification/
  DRC, extraction, connectivity assertions, LVS, and report parsing

outputs/
  generated artifact paths

examples/
  integration wiring only; no reusable routing policy
```

## Dependency rules

1. Intent and constraint models do not import gLayout, gdsfactory, Magic, or Netgen.
2. Pure planners do not mutate components.
3. Device adapters expose physical choices but do not choose global routes.
4. PDK rule resolution belongs downstream of semantic intent.
5. Executors do not invent access or topology policy.
6. Verification adapters own external-tool invocation and parsing.
7. Examples contain no reusable engine logic.
8. New strategies require pure tests and `/foss` integration validation.
9. DRC success is never reported as electrical success.
10. Major architecture decisions require an ADR.

## Known debt

Do not copy these limitations into new subsystems:

- placement returns only a component rather than typed `PlacementResult` bindings;
- MOS snapshot construction still binds tiles to references by order;
- logical planning is two-terminal and same-layer only;
- via planning and execution are absent;
- width classes and layer policies are not PDK-resolved;
- committed routes are not yet obstacles/resources;
- no multi-terminal topology planner exists;
- route-group constraints are typed but not enforced;
- extraction lacks stable logical instance identity.

## Development order

Current branch acceptance:

```text
1. default A0-A1 dogleg regression remains DRC/extraction/connectivity clean
2. diagonal A0-A2 route selects Manhattan strategy
3. diagonal route passes DRC and extraction
4. extracted diagonal net contains exactly A0 and A2
```

After merge:

```text
1. committed-route resources and route-to-route obstacles
2. PDK width/layer/via rule resolution
3. PDK-aware via planning and execution
4. multi-terminal topology planning
5. matched and differential route-group strategies
6. coarse rectilinear graph search and congestion
7. independent schematic LVS
8. verification-driven repair
9. capacitor-array and CDAC templates
```

Do not jump directly to multi-net maze routing before committed-route resources and PDK rule resolution exist.

## Change checklist

Before committing engine work, verify:

- Which pipeline translation does this module own?
- Is the input typed and independent of execution tools?
- Is device-specific knowledge in an adapter or strategy rather than generic execution?
- Is policy inside a planner rather than an example?
- Are hard constraints separate from soft costs?
- Does the plan retain geometry, metrics, blockers, rejections, and provenance?
- Does the integration test prove connectivity?
- Has `VALIDATION_STATUS.md` been updated without overstating `/foss` evidence?
- Does the change require an ADR?
