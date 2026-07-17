# MatchMaker Engineering Map

This is the canonical live-state document for MatchMaker. Read it before changing the engine. It is optimized for a future coding agent or contributor who must recover the architecture, active APIs, validation boundary, known debt, and next step without reconstructing context from chat or commit history.

## Read order

```text
1. docs/ENGINEERING_MAP.md              current architecture and development state
2. docs/VALIDATION_STATUS.md            physical evidence demonstrated in /foss
3. docs/adr/*.md                         durable decisions and rejected alternatives
4. the module being changed
5. its tests
```

Do not create another handoff or architecture summary. Update this file instead. `VALIDATION_STATUS.md` is the only place for detailed observed run output. ADRs are append-only decision records, not status documents.

## Mission

MatchMaker is a deterministic, constraint-driven analog layout synthesis engine for GF180 through gLayout. It must preserve electrical connectivity, analog matching intent, geometric constraints, and verification evidence while supporting reusable MOS arrays, switches, capacitors, CDACs, comparators, and larger analog cells.

## Repository state at this document revision

```text
base branch: main
active branch: feature/manhattan-routing-dispatcher
active PR: #3
PR #1: routing and verification foundation, merged
PR #2: logical net intent, access selection, and RoutePlan IR, merged
PR #3: modular strategy dispatch and non-inline Manhattan routing, ready for review
```

PR #3 has passed GitHub Actions, Python compilation, the original blocked A0-to-A1 dogleg regression, and the diagonal A0-to-A2 Manhattan regression in `/foss`.

## Golden pipeline

```text
high-level circuit/layout intent
-> typed device and placement intent
-> deterministic placement plan
-> placed GF180 geometry
-> PhysicalDesignSnapshot
-> NetIntent / RouteGroupIntent
-> routing strategy dispatch
-> RouteCandidate selection
-> RoutePlan
-> mechanical geometry execution
-> GDS
-> Magic DRC
-> Magic extraction and connectivity assertion
-> Netgen LVS
-> targeted repair or accepted cell
```

Each major module owns one translation. No example, executor, or verification adapter may silently become a planner.

## Core routing principle

Routing begins with logical connectivity, not fixed primitive ports.

```text
NetIntent(A0.gate, A1.gate)
+ NetConstraintProfile
+ PhysicalDesignSnapshot
-> enumerate legal physical access points
-> generate candidates with independent strategies
-> reject hard-constraint violations
-> rank feasible candidates deterministically
-> compile the selected candidate into RoutePlan
-> execute resolved geometry
```

A logical terminal such as `A0.gate` may expose several physical access points such as `A0__gate_E` and `A0__gate_W`. High-level callers must not select those physical accesses before placement context is evaluated.

## Canonical data contracts

### Logical intent

File: `src/matchmaker/routing/intents/net_intent.py`

```text
NetIntent
NetConstraintProfile
RouteGroupIntent
RouteGroupConstraintProfile
```

`NetIntent` names logical `TerminalRef` objects only. `NetConstraintProfile` currently carries semantic width class, optional explicit width, obstacle clearance, layer restrictions, maximum length/bends, cost weights, and priority.

Route-group types reserve matching, symmetry, shielding, separation, and equal bend/via requirements. Group planning is not implemented yet.

### Physical state

Files:

```text
src/matchmaker/physical/models.py
src/matchmaker/physical/mos_centroid_snapshot.py
```

Canonical models:

```text
TerminalRef
AccessPoint
PlacedInstance
RoutingObstacle
PhysicalDesignSnapshot
```

`PhysicalDesignSnapshot.access_points_for(TerminalRef(...))` is the supported bridge from electrical identity to physical choices. Routing code must not infer identity from reference order or store planning policy in `Component.info`.

The MOS adapter filters nested gLayout hierarchy ports and retains canonical external gate/source/drain/bulk cardinal accesses. The validated eight-instance centroid exposes 128 routing access points instead of 21,520 unfiltered hierarchy ports.

### Candidate and dispatch evidence

Files:

```text
src/matchmaker/routing/planners/route_candidate.py
src/matchmaker/routing/planners/two_terminal_strategy_dispatcher.py
```

Canonical models:

```text
RouteCandidate
CandidateRejection
StrategyDispatchResult
RoutePlanningError
```

A candidate records selected access points, exact path points, layer, width, strategy, length, bend count, cost, blockers, channel information, and provenance. A dispatch result retains the selected candidate, every feasible candidate, and every rejection reason.

### Route-plan IR

File: `src/matchmaker/routing/plans/route_plan.py`

```text
RoutePlan
RouteSegment
ViaPlan
RouteMetrics
ConstraintCheck
```

A valid plan contains only nonzero Manhattan segments, internally consistent metrics, and no failed hard constraint.

### Execution

File: `src/matchmaker/routing/routers/route_plan_executor.py`

The executor draws an already resolved `RoutePlan`. It does not choose terminals, access points, topology, strategy, channel, width, or layer. Via execution is not implemented and must fail explicitly.

## Current strategy architecture

Directory: `src/matchmaker/routing/planners/`

```text
straight_route_strategy.py
  clear same-layer aligned route

manhattan_route_strategy.py
  non-inline L routes for perpendicular accesses
  non-inline Z routes for parallel accesses
  midpoint, obstacle-edge, and outer channel candidates

dogleg_route_strategy.py
  aligned external channel around a blocked row or column

rectilinear_path.py
  shared Manhattan geometry, orientation, and obstacle utilities

two_terminal_strategy_dispatcher.py
  access-pair enumeration
  common layer eligibility
  strategy invocation
  hard-limit filtering
  candidate deduplication
  deterministic ranking
  structured rejection evidence

two_terminal_net_planner.py
  selected RouteCandidate -> RoutePlan
```

Strategy registration is static. Do not add dynamic plugin discovery until several stable strategy families exist and registration itself becomes a demonstrated problem.

## Device-specific extension model

A single universal analog router is not the target. MatchMaker uses common contracts with device adapters and specialized strategy/topology modules.

### Physical adapters

Adapters translate placed device structure into logical terminals, physical access choices, obstacles, and local keepouts.

```text
MOS adapter -> gate/source/drain/bulk
capacitor adapter -> top/bottom plate
resistor adapter -> terminal accesses
transmission-gate adapter -> input/output/control
comparator adapter -> input/output/clock/supply
```

Device construction details must not leak into the generic dispatcher.

### Routing strategies and topology modules

Planned examples:

```text
RectilinearGraphStrategy
DifferentialPairStrategy
MatchedRouteGroupStrategy
MatchedBusStrategy
ShieldedNetStrategy
CdacRoutingTemplateStrategy
```

They must consume common intent/snapshot contracts and emit common candidate/plan types. Specialized analog topology is allowed; specialized execution paths are not.

### PDK rule adapters

Semantic intent such as `signal`, `high_current`, or `high_voltage` must eventually resolve through a GF180 routing-rule adapter into concrete layers, widths, spacing, via types, via arrays, and enclosures. Generic intent and strategy code must not hard-code PDK rule numbers.

## Package ownership

```text
specs/
  PDK-independent device specifications

placement/core/
  reusable tile, grid, plan, orientation, and spacing infrastructure

placement/mos/
  MOS intent compilation, dummy policy, binding, and placement

physical/
  placed instances, logical terminals, physical accesses, obstacles, snapshots

primitives/
  PDK/gLayout primitive construction

routing/intents/
  logical net and route-group requests

routing/planners/
  pure strategies, dispatch, obstacle checks, candidate/plan compilation

routing/plans/
  common execution-ready route IR and metrics

routing/routers/
  mechanical geometry execution

verification/
  DRC, extraction, connectivity assertions, LVS, report parsing

outputs/
  generated-cell paths and artifact conventions

examples/
  package wiring only; no reusable engine policy
```

## Architectural invariants

1. Logical terminals are separate from physical access points.
2. Hard constraints reject candidates before soft-cost ranking.
3. Pure planners do not mutate gdsfactory or gLayout components.
4. Executors do not invent routing policy.
5. Examples contain no reusable engine logic.
6. New routing work consumes `PhysicalDesignSnapshot`.
7. New strategies emit common `RouteCandidate` and `RoutePlan` types.
8. Candidates and plans retain metrics, blockers, constraint evidence, and provenance.
9. Unsupported cases fail explicitly rather than drawing unsafe fallback geometry.
10. DRC success never proves electrical correctness.
11. Every connectivity-changing integration test requires extraction or LVS evidence.
12. PDK rule numbers belong in PDK adapters or detailed physical planning.
13. Major architecture changes require an ADR.
14. Live architecture/status belongs here; observed physical evidence belongs in `VALIDATION_STATUS.md`.

## Physically validated regressions

Detailed commands and observed output are in `VALIDATION_STATUS.md`.

### Blocked A0-to-A1 dogleg

```text
logical terminals: A0.gate, A1.gate
selected access: A0__gate_W, A1__gate_E
blockers: B0, B1
strategy: dogleg
GF180 Magic DRC: zero violations
Magic extraction: passed
connectivity: exactly A0 and A1
pre-LVS gate: passed
```

Failure history to preserve: the original direct route and layer-only C route were DRC-clean but electrically connected B0 and B1. This is why extraction/connectivity gating is mandatory.

### Diagonal A0-to-A2 Manhattan route

```text
logical terminals: A0.gate, A2.gate
selected access: A0__gate_E, A2__gate_W
strategy: two-bend Manhattan Z route
length: 44.8
width: 0.5
feasible candidates: 4
rejected candidates: 110
GF180 Magic DRC: zero violations
Magic extraction: passed
connectivity: exactly A0 and A2
pre-LVS gate: passed
```

## Known implementation debt

- Placement returns a component rather than a typed `PlacementResult`.
- Snapshot construction still relies partly on placement/reference binding assumptions.
- Routing is two-terminal and same-layer only.
- Committed routes are not represented as obstacles or routing resources.
- Width classes and layer policies are not resolved through a GF180 rule adapter.
- Via planning and execution are not implemented.
- Multi-terminal topology planning is not implemented.
- Matching, differential symmetry, shielding, and separation are typed but not planned.
- Congestion-aware graph search and rip-up/reroute are not implemented.
- Independent schematic-to-layout Netgen LVS has not passed.
- Extracted instance identity is inferred from generated subcircuit names rather than stable logical IDs.

## Next development order

Do not jump directly to multi-net A* routing.

```text
1. squash-merge PR #3
2. represent committed routes as typed obstacles/resources in PhysicalDesignSnapshot
3. add GF180 routing-rule resolution for width, layer, spacing, and via selection
4. add PDK-aware via planning and execution
5. add multi-terminal topology planning
6. add matched/differential route-group planners
7. add coarse rectilinear graph search and congestion accounting
8. add an independent schematic LVS regression
9. add capacitor/CDAC physical adapters and routing templates
```

## Required change discipline

Before merging engine work, answer:

- Which pipeline translation does this module own?
- Is its input typed and independent of execution tools?
- Is reusable policy in a planner rather than an executor or example?
- Are hard constraints distinct from soft costs?
- Does the output retain evidence and provenance?
- Are unsupported cases explicit?
- Do unit tests cover pure behavior?
- Does `/foss` integration prove DRC and extracted connectivity?
- Have this map, `VALIDATION_STATUS.md`, and any relevant ADR been updated without duplicating status or overstating validation?
