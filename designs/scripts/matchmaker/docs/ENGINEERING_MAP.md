# MatchMaker Engineering Map

This is the first document to read before changing the engine. It is written for human contributors and coding agents that need to recover the architecture, implementation boundary, and next development step without reconstructing them from examples or commit history.

## Mission

MatchMaker is a deterministic, constraint-driven analog layout synthesis engine. It translates structured circuit and layout intent into GF180 geometry while preserving connectivity, matching intent, symmetry, electrical constraints, and verification evidence.

Long-term targets include matched MOS structures, switch networks, capacitor arrays, CDACs, and larger reusable analog cells.

## Read order

```text
1. docs/ENGINEERING_MAP.md
2. docs/adr/0001-constraint-driven-hybrid-routing.md
3. docs/VALIDATION_STATUS.md
4. the package module being changed
5. the relevant tests
```

`VALIDATION_STATUS.md` is the source of truth for results demonstrated in the Chipathon `/foss` environment. Pure tests and plausible geometry do not constitute physical integration validation.

## Golden pipeline

```text
high-level circuit and layout intent
→ typed device, placement, net, and route-group intent
→ deterministic intent compilation
→ placement plan
→ PhysicalDesignSnapshot
→ routing problem
→ RoutePlan
→ geometry execution
→ GDS
→ DRC
→ extraction and connectivity audit
→ LVS
→ targeted repair or accepted cell
```

Each major module should own one translation in this pipeline. Do not hide planning inside an executor, verification tool, or example.

## Stable demonstrated foundation

The merged routing foundation demonstrated:

```text
MOS centroid intent
→ placement request
→ GF180 MOS placement
→ typed PhysicalDesignSnapshot
→ obstacle-aware fixed-access route request
→ external same-layer spatial dogleg
→ GDS
→ Magic DRC: zero violations
→ Magic extraction
→ exact shared-net participant assertion: two intended A devices only
```

This result proved that DRC-clean geometry can still be electrically wrong and established extraction/connectivity gating as mandatory.

## Current development slice

The `feature/logical-net-routing-ir` branch migrates the same regression from physical-port intent to logical-net intent:

```text
NetIntent(A0.gate, A1.gate)
+ NetConstraintProfile
+ PhysicalDesignSnapshot
→ automatic access candidate generation
→ hard-constraint filtering
→ deterministic cost ranking
→ RoutePlan
→ mechanical route-plan execution
→ existing DRC, extraction, and connectivity gate
```

The example no longer selects `gate_E`, `gate_W`, or any other physical port. The planner must recover the previously validated outward `A0__gate_W` and `A1__gate_E` access pair from placement context.

The pure tests and compilation workflow cover this branch. A fresh `/foss` run is still required before the migrated flow is considered physically validated.

## Core routing principle

Routing is a constrained physical-synthesis problem, not a direct call between two named ports.

Canonical input:

```text
logical net or route group
+ logical terminals
+ typed hard constraints
+ typed soft-cost weights
+ available physical access points
+ placed obstacles and keepouts
+ routing-layer resources
+ already committed routes
```

Canonical output:

```text
RoutePlan
+ selected access points
+ strategy and topology
+ exact Manhattan segments and vias
+ width and layer decisions
+ metrics
+ constraint-check evidence
+ blockers and strategy provenance
```

Geometry is generated only after the plan is complete.

## Terminal versus access point

A logical terminal is an electrical concept:

```text
A0.gate
A0.drain
CAP3.top
SW1.output
```

A physical access point is one legal contact location for that terminal:

```text
A0__gate_E
A0__gate_W
metal-2 access at coordinate (x, y)
```

Current physical models live in `physical/models.py`:

```text
TerminalRef
AccessPoint
PlacedInstance
RoutingObstacle
PhysicalDesignSnapshot
```

`PhysicalDesignSnapshot.access_points_for(TerminalRef(...))` is the canonical bridge from electrical identity to physical choices.

## Canonical routing data contracts

### Logical intent

`routing/intents/net_intent.py`

```text
NetIntent
NetConstraintProfile
RouteGroupIntent
RouteGroupConstraintProfile
```

`NetIntent` names logical terminals only. It does not name primitive ports.

`NetConstraintProfile` currently represents:

- semantic width class and optional explicit width;
- obstacle avoidance and clearance;
- allowed and forbidden layers;
- maximum length and bend count;
- length, bend, and via cost weights;
- routing priority.

`RouteGroupConstraintProfile` reserves typed fields for separation, matched length, symmetry, equal bend/via count, and shielding. Group planning is not implemented yet.

### Physical state

`physical/models.py`

```python
PhysicalDesignSnapshot(
    component=...,
    instances={instance_name: PlacedInstance(...)},
    access_points={access_name: AccessPoint(...)},
    terminal_access={TerminalRef(...): (access_name, ...)},
    obstacles=(RoutingObstacle(...), ...),
    keepouts=(...),
    committed_routes=(...),
)
```

Snapshot mappings are read-only. New routing code must consume this object rather than inspect reference order, infer identities independently, or store policy in `Component.info`.

### Route-plan IR

`routing/plans/route_plan.py`

```text
RoutePlan
RouteSegment
ViaPlan
RouteMetrics
ConstraintCheck
```

A valid `RoutePlan` contains only Manhattan, nonzero segments and no failed hard constraint. Metrics are checked against the plan geometry.

### Planning

`routing/planners/two_terminal_access_selector.py`

Current candidate pipeline:

```text
enumerate source and target AccessPoint pairs
→ reject forbidden or incompatible layers
→ retain same-layer inline launch pairs
→ detect direct-path blockers
→ emit clear straight candidate or external dogleg candidate
→ reject maximum-length and maximum-bend violations
→ rank by deterministic cost and stable name tie-breaks
```

`routing/planners/two_terminal_net_planner.py` converts the selected candidate into exact segments, resolved width, metrics, and constraint checks.

The current slice intentionally supports two-terminal, same-layer straight and external-dogleg plans only. Unsupported cases fail rather than silently falling back to unsafe geometry.

### Execution

`routing/routers/route_plan_executor.py`

The executor consumes `RoutePlan` and draws its resolved segments. It does not select access, topology, channel, width, or strategy. Via execution remains unimplemented and fails explicitly.

The old fixed-access point-to-point router remains transitional compatibility code. New examples and new features should use logical `NetIntent` and `RoutePlan`.

## Hard constraints and soft costs

Hard constraints determine feasibility:

- exact intended connectivity;
- no unintended terminals;
- allowed and forbidden layers;
- obstacle and keepout avoidance;
- width, spacing, enclosure, and via legality;
- maximum length, resistance, bend, or via limits;
- required symmetry, topology, separation, or shielding.

Soft costs rank feasible candidates:

- wire length;
- bend and via count;
- estimated resistance and capacitance;
- congestion;
- coupling exposure;
- matched-length error;
- symmetry-axis deviation;
- scarce-channel usage.

Hard constraints are always evaluated before ranking.

## Hybrid strategy ladder

Do not build one universal router prematurely. Strategies share the same intent, snapshot, plan, and verification contracts:

```text
1. direct straight route
2. simple Manhattan family
3. explicit spatial dogleg or reserved channel
4. coarse rectilinear graph search
5. multi-terminal topology plus branch routing
6. matched and differential templates
7. congestion-aware negotiated multi-net routing
```

Analog templates remain first-class planners rather than special geometry mutations inside examples.

## Verification boundary

```text
DRC pass != connectivity pass
```

Every routing integration test that changes connectivity must include extraction or LVS evidence. Current generated-cell verification provides:

```text
Magic DRC
→ Magic SPICE extraction
→ exact shared-net participant assertion
→ Netgen LVS infrastructure
```

The current participant assertion uses extracted subcircuit-name multisets. Stable logical instance identity in extracted netlists remains future work.

## Package ownership

```text
specs/
  PDK-independent device specifications

placement/core/
  reusable tiles, plans, orientation, spacing, and grid infrastructure

placement/mos/
  MOS intent compilation, dummy policy, binding, and placement

physical/
  placed instances, terminals, access points, obstacles, and snapshots

primitives/
  PDK/gLayout primitive construction

routing/intents/
  logical net and route-group requests; legacy fixed-access intent remains

routing/plans/
  common execution-ready route-plan IR and metrics

routing/planners/
  pure access selection, obstacle checks, and route-plan compilation

routing/routers/
  mechanical physical execution adapters

verification/
  DRC, extraction, connectivity assertions, LVS, and report parsing

outputs/
  artifact paths and generated-cell filesystem conventions

examples/
  package wiring only; no reusable engine policy
```

## Dependency rules

1. Intent and constraint models do not import gLayout, gdsfactory, Magic, or Netgen.
2. Pure planners operate on typed state and do not mutate components.
3. PDK rule resolution belongs in PDK adapters or detailed physical planning.
4. Executors may import gLayout/gdsfactory but do not invent access or topology policy.
5. Verification adapters own external-tool invocation and parsing.
6. Examples contain no reusable engine logic.
7. New strategies require pure planner tests and `/foss` integration validation.
8. DRC success is never reported as electrical success.
9. New routing work consumes `PhysicalDesignSnapshot`.
10. Major architectural decisions require an ADR.

## Known debt

Do not copy these limitations into new subsystems:

- placement returns only a component rather than a typed `PlacementResult`;
- snapshot construction binds tiles to references by order;
- the legacy point-to-point API still names physical access ports;
- current logical planning supports only two-terminal same-layer routes;
- width classes do not yet resolve through a PDK rule adapter;
- via planning and execution are not implemented;
- committed routes are not yet incorporated as routing obstacles/resources;
- extracted instance identity is inferred through generated subcircuit names.

## Development order

Completed in the current branch:

```text
✓ logical NetIntent
✓ typed per-net and route-group constraints
✓ automatic two-terminal access selection
✓ common RoutePlan, RouteSegment, ViaPlan, and RouteMetrics
✓ mechanical route-plan executor
✓ migration of the centroid regression to logical terminals
```

Next, after `/foss` validation:

```text
1. strategy dispatcher with candidate provenance and rejection reports
2. committed-route resources and route-to-route obstacles
3. multi-terminal topology planning
4. PDK width/layer/via rule resolution
5. matched and differential route-group planners
6. coarse routing graph and congestion model
7. independent schematic LVS
8. targeted verification-driven repair
9. capacitor-array and CDAC routing templates
```

Do not jump to multi-net A* routing before the current logical-intent and common-plan contracts are physically validated.

## Change checklist

Before committing engine work, verify:

- Which pipeline translation does this module own?
- Is the input typed and independent of execution tools?
- Is policy inside a planner rather than an executor or example?
- Does the change introduce hidden physical state outside the snapshot?
- Are hard constraints separate from soft costs?
- Is logical terminal identity separate from physical access?
- Does the plan retain metrics, blockers, checks, and provenance?
- Does the integration test prove connectivity?
- Has `VALIDATION_STATUS.md` been updated without overstating `/foss` validation?
- Does the decision require a new ADR?
