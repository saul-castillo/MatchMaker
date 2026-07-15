# MatchMaker Agent Handoff

Last updated: 2026-07-15

This file is the compact current-state record for a future coding agent or contributor. Read it before modifying the engine, then consult `ENGINEERING_MAP.md`, the ADRs, and `VALIDATION_STATUS.md` for deeper rationale and evidence.

## Active repository state

- Repository: `saul-castillo/MatchMaker`
- Base branch: `main`
- Active development branch: `feature/manhattan-routing-dispatcher`
- Active pull request: PR #3, modular routing dispatcher and non-inline Manhattan planning
- PR #1 merged the routing/verification foundation.
- PR #2 merged logical-net routing intent, automatic access selection, and common `RoutePlan` IR.
- PR #3 has passed pure tests, Python compilation, the diagonal Manhattan `/foss` regression, and the original dogleg `/foss` regression. It is open, mergeable, out of draft, and ready for review.

## Mission

MatchMaker is a deterministic, constraint-driven analog layout synthesis engine for GF180 through gLayout. It must preserve electrical connectivity, analog matching intent, geometric constraints, and verification evidence while remaining modular enough to support MOS arrays, switches, capacitors, CDACs, comparators, and larger analog cells.

## Canonical pipeline

```text
high-level circuit/layout intent
-> typed device and placement intent
-> deterministic placement
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

No module should silently own more than one major translation in this pipeline.

## Current routing contracts

### Logical intent

`routing/intents/net_intent.py`

- `NetIntent`: logical net name, logical `TerminalRef` endpoints, constraints, and strategy preference.
- `NetConstraintProfile`: width class, optional explicit width, obstacle clearance, layer restrictions, length/bend limits, cost weights, and priority.
- `RouteGroupIntent` and `RouteGroupConstraintProfile`: typed placeholders for matching, symmetry, shielding, separation, and equal bend/via requirements.

Logical intent must not name primitive ports such as `gate_E` or `gate_W`.

### Physical state

`physical/models.py`

- `TerminalRef`
- `AccessPoint`
- `PlacedInstance`
- `RoutingObstacle`
- `PhysicalDesignSnapshot`

`PhysicalDesignSnapshot.access_points_for(TerminalRef(...))` is the only supported bridge from electrical identity to physical access choices.

The MOS snapshot adapter filters gLayout hierarchy ports and retains canonical external gate/source/drain/bulk cardinal accesses. The validated centroid has eight physical instances and 128 retained access points, reduced from 21,520 unfiltered hierarchy ports.

### Candidate and dispatch evidence

`routing/planners/route_candidate.py`

- `RouteCandidate`
- `CandidateRejection`
- `StrategyDispatchResult`
- `RoutePlanningError`

A candidate records exact path points, selected accesses, strategy, layer, width, length, bends, cost, blockers, channel information, and provenance. A dispatch result retains the selected candidate, all feasible candidates, and all rejection reasons.

### Route plan

`routing/plans/route_plan.py`

- `RoutePlan`
- `RouteSegment`
- `ViaPlan`
- `RouteMetrics`
- `ConstraintCheck`

A valid plan contains only nonzero Manhattan segments, internally consistent metrics, and no failed hard constraint.

### Execution

`routing/routers/route_plan_executor.py`

The executor draws an already resolved plan. It must not choose logical terminals, access points, topology, strategy, channel, width, or layer. Via execution is not yet implemented and must fail explicitly.

## Current strategy modules

`routing/planners/strategies/`

- Straight strategy: clear, same-layer, aligned route.
- Manhattan strategy: same-layer non-inline L routes for perpendicular accesses and Z routes for parallel accesses.
- External dogleg strategy: aligned route around a blocked row or column using outward access and an external channel.

`routing/planners/two_terminal_strategy_dispatcher.py` owns access-pair enumeration, layer eligibility, common hard-limit filtering, deduplication, deterministic ranking, and rejection reports.

Strategy registration is static. Do not add dynamic plugin discovery until several stable strategy families exist.

## Device-specific extension model

Device-specific knowledge belongs in physical adapters, not in the generic dispatcher.

Examples:

```text
MOS adapter -> gate/source/drain/bulk accesses
capacitor adapter -> top/bottom plate accesses
resistor adapter -> terminal accesses
transmission-gate adapter -> input/output/control accesses
comparator adapter -> input/output/clock/supply accesses
```

Analog-specific routing behavior belongs in strategy or topology modules that consume the common intent/snapshot contracts and emit common candidates/plans.

Planned examples:

```text
DifferentialPairStrategy
MatchedBusStrategy
ShieldedNetStrategy
RectilinearGraphStrategy
CdacRoutingTemplateStrategy
```

## Architectural invariants

1. Logical terminals are separate from physical access points.
2. Hard constraints reject candidates before soft-cost ranking.
3. Pure planners do not mutate gdsfactory/gLayout components.
4. Executors do not invent routing policy.
5. Examples only wire packages together; reusable policy does not live in examples.
6. New routing work consumes `PhysicalDesignSnapshot`.
7. New strategies emit common `RouteCandidate` and `RoutePlan` types.
8. Every candidate and plan retains metrics, provenance, blockers, and constraint evidence.
9. Unsupported cases fail explicitly rather than drawing unsafe fallback geometry.
10. DRC success never proves electrical correctness.
11. Every connectivity-changing integration test requires extraction or LVS evidence.
12. PDK rule numbers belong in PDK adapters or detailed physical planning, not in generic intent.
13. Major architecture changes require an ADR.

## Physically validated regressions

### A0-to-A1 blocked dogleg

```text
logical terminals: A0.gate, A1.gate
selected access: A0__gate_W, A1__gate_E
blockers: B0, B1
strategy: dogleg
GF180 Magic DRC: zero violations
Magic extraction: passed
connectivity assertion: exactly A0 and A1
pre-LVS gate: passed
```

The original direct and layer-only C routes were DRC-clean but electrically shorted B0 and B1. Preserve this failure history because it establishes why extraction gating is mandatory.

### A0-to-A2 diagonal Manhattan route

```text
logical terminals: A0.gate, A2.gate
selected access: A0__gate_E, A2__gate_W
strategy: manhattan Z route
points: (-28.57, 13.26) -> (-20.08, 13.26) -> (-20.08, -13.26) -> (-10.29, -13.26)
length: 44.8
bends: 2
width: 0.5
feasible candidates: 4
rejected candidates: 110
GF180 Magic DRC: zero violations
Magic extraction: passed
connectivity assertion: exactly A0 and A2
pre-LVS gate: passed
```

## Known implementation debt

- Placement still returns a component rather than a typed `PlacementResult`.
- Snapshot construction still relies partly on placement/reference binding assumptions.
- Only two-terminal, same-layer routing is implemented.
- Committed routes are not yet converted into routing obstacles/resources.
- Width classes and layer policies are not resolved through a GF180 PDK rule adapter.
- Via planning and execution are not implemented.
- Multi-terminal topology planning is not implemented.
- Route-group matching, differential symmetry, shielding, and separation are typed but not planned.
- Congestion-aware graph search and rip-up/reroute are not implemented.
- Independent schematic-to-layout Netgen LVS has not passed yet.
- Extracted instance identity is inferred through generated subcircuit names rather than stable logical IDs.

## Next development order

Do not jump directly to multi-net A* routing.

1. Squash-merge PR #3 after final review.
2. Treat committed routes as typed obstacles/resources in `PhysicalDesignSnapshot`.
3. Add a GF180 routing-rule adapter for semantic width classes, allowed layers, spacing, and via selection.
4. Add PDK-aware via planning and execution.
5. Add multi-terminal topology planning.
6. Add matched/differential route-group planners.
7. Add coarse rectilinear graph search and congestion accounting.
8. Add independent schematic LVS regression.
9. Add capacitor-array and CDAC physical adapters and routing templates.

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
- Have `ENGINEERING_MAP.md`, `VALIDATION_STATUS.md`, this handoff, and any relevant ADR been updated without overstating validation?
