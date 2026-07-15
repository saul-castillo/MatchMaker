# MatchMaker Engineering Map

This is the first document to read before changing the engine. It is optimized for human contributors and coding agents that need to recover the architecture, implementation boundary, and next development step without reconstructing them from examples or commit history.

## Mission

MatchMaker is a deterministic, constraint-driven analog layout synthesis engine. It must preserve circuit connectivity, matching intent, symmetry, electrical constraints, and verification evidence while translating structured design intent into GF180 layout.

Long-term targets include matched MOS structures, switch networks, capacitor arrays, CDACs, and larger reusable analog cells.

## Read order

```text
1. docs/ENGINEERING_MAP.md
2. docs/adr/0001-constraint-driven-hybrid-routing.md
3. docs/VALIDATION_STATUS.md
4. the package module being changed
5. the relevant tests
```

`VALIDATION_STATUS.md` is the source of truth for what has actually been demonstrated in the Chipathon `/foss` environment. A unit test or plausible implementation is not an integration-validated layout flow.

## Golden pipeline

```text
high-level circuit and layout intent
→ typed device, placement, net, and route-group intent
→ deterministic intent compilation
→ placement plan
→ physical-design snapshot
→ routing problem
→ route plan
→ geometry execution
→ local geometric and connectivity checks
→ GDS
→ DRC
→ extraction and connectivity audit
→ LVS
→ targeted repair or accepted cell
```

Every major module should own one translation in this pipeline. A module should not silently perform work belonging to several stages.

## Current demonstrated slice

```text
MOS centroid intent
→ placement request
→ GF180 MOS placement
→ typed PhysicalDesignSnapshot
→ obstacle-aware point-to-point routing
→ explicit same-layer spatial dogleg
→ GDS
→ Magic DRC
→ Magic extraction
→ automatic exact-participant connectivity assertion
```

The snapshot-backed demo has been demonstrated in `/foss`: zero DRC violations, successful extraction, and a routed node connected to exactly the two intended A devices.

## Core working principle

Routing is a constrained physical-synthesis problem, not a direct call from two named ports to a route primitive.

Canonical routing input:

```text
logical net or route group
+ logical terminals that must be connected
+ electrical and analog constraints
+ available physical access points
+ placed obstacles and keepouts
+ routing-layer resources
+ routes already committed
```

Canonical routing output:

```text
typed RoutePlan
+ selected terminal access points
+ topology
+ coarse path or routing channel
+ detailed Manhattan segments and vias
+ predicted metrics
+ hard-constraint evidence
+ strategy provenance
```

Geometry is produced only after a plan exists.

## Terminal versus access point

A logical terminal is an electrical concept:

```text
A0.gate
A0.drain
CAP3.top
SW1.output
```

A physical access point is one legal place where that terminal can be contacted:

```text
A0__gate_E
A0__gate_W
metal-2 access at coordinate (x, y)
```

Routing intent should converge toward logical `TerminalRef` objects rather than permanently selecting a physical port before the placement context is evaluated.

Current physical models:

```text
physical/models.py
  TerminalRef
  AccessPoint
  PlacedInstance
  RoutingObstacle
  PhysicalDesignSnapshot
```

The current point-to-point intent still names concrete access ports. That is transitional debt. The next routing milestone replaces it with logical net intent and an explicit access-selection planner.

## Physical-design snapshot

Routing consumes one explicit physical state object:

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

Current construction path:

```text
physical/mos_centroid_snapshot.py
  create_mos_centroid_physical_design_snapshot(...)
```

The snapshot mappings are read-only. Route execution requires the snapshot; planners must not recover physical state from `Component.info` or invent independent instance bindings.

The MOS centroid adapter still binds placement tiles to component references by order because the placement builder returns only a component. Target placement output:

```python
PlacementResult(
    component=...,
    instance_bindings={tile_name: physical_reference_id},
    physical_design=PhysicalDesignSnapshot(...),
)
```

## Constraint model

Constraints are typed and divided into hard requirements and soft costs.

### Hard constraints

A route is invalid when any hard constraint fails:

- connect exactly the intended terminals;
- do not connect unrelated terminals;
- obey PDK width, spacing, enclosure, and via rules;
- obey allowed and forbidden routing layers;
- avoid obstacles and keepouts;
- satisfy required net separation;
- satisfy mandatory symmetry or topology;
- obey strict maximum length, resistance, or via count when specified.

### Soft costs

Soft costs rank only valid candidates:

- wire length;
- estimated resistance and capacitance;
- via count;
- bend count;
- congestion;
- coupling exposure;
- matched-length error;
- symmetry-axis deviation;
- scarce-channel usage.

Hard constraints are checked before cost ranking.

### Translating analog language

```text
"keep this short"
→ max_length and/or max_resistance

"make this thick"
→ width class, current target, PDK-resolved width

"keep this away from high potential"
→ pairwise or class separation, optional shielding, layer policy

"match these traces"
→ topology, length, via, bend, and symmetry constraints

"sensitive node"
→ coupling/separation class and routing priority
```

Separation, shielding, matching, and symmetry relate multiple nets. They belong in route-group or explicit pairwise constraints, not only in isolated per-net tags.

## Hybrid routing architecture

Use a deterministic strategy ladder behind a common planner interface:

```text
1. direct straight route
2. simple L/C route family
3. explicit spatial dogleg or reserved channel
4. coarse rectilinear routing graph with A* or equivalent search
5. multi-terminal topology plus branch routing
6. multi-net congestion handling and negotiated rip-up/reroute
```

Analog templates remain first-class strategies:

```text
StraightRoutePlanner
SpatialDoglegPlanner
DifferentialPairTemplatePlanner
MatchedBusPlanner
CdacRoutingTemplatePlanner
RectilinearGraphPlanner
```

Templates and search planners must emit the same `RoutePlan` representation and use the same constraint and metric checks.

## Routing stages

### 1. Net and route-group compilation

Resolve logical connectivity and typed constraints into a `RoutingProblem`.

### 2. Topology planning

Two-terminal topology is trivial. Multi-terminal nets require a tree, bus, star, chain, H-tree, or analog-specific topology before detailed segments are drawn.

### 3. Access selection

Choose physical access candidates for every logical terminal. Access selection must understand transformed orientation, obstacles, route-group rules, and layer availability.

### 4. Coarse path or channel planning

Choose which side of obstacles, reserved channel, or coarse routing graph a net uses. This stage handles global spatial relations and congestion.

### 5. Detailed geometry planning

Resolve exact Manhattan segments, widths, layers, vias, and corner geometry using PDK rules.

### 6. Execution

Convert an already-resolved plan into gLayout/gdsfactory geometry. Executors are mechanically simple and do not invent topology or access policy.

### 7. Validation and feedback

Run cheap local checks first, then DRC, extraction/connectivity assertions, and LVS. Failures return structured evidence rather than triggering arbitrary geometry mutation.

## Connectivity verification

DRC proves geometric legality, not electrical intent. The first smoke test produced a DRC-clean route that connected four devices instead of two.

```text
DRC pass != connectivity pass
```

Current connectivity API:

```text
verification/netlist/connectivity_assertions.py
  SharedNetConnectivityExpectation
  SharedNetConnectivityResult
  evaluate_extracted_shared_net_connectivity(...)
```

The current assertion identifies expected participants by extracted subcircuit-name multiset. This is sufficient for the present generated demo but not the final identity model. Future extraction work should preserve stable logical instance identity so assertions can refer directly to instance IDs such as `A0` and `A1`.

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
  routing requests; current API still names physical access ports

routing/planners/
  pure route-family, obstacle, and spatial planning

routing/routers/
  physical route execution adapters

verification/
  DRC, extraction, connectivity assertions, LVS, and report parsing

outputs/
  artifact paths and generated-cell filesystem conventions

examples/
  package wiring only; no reusable engine policy
```

## Dependency rules

1. Intent and constraint models do not import gLayout, gdsfactory, Magic, or Netgen.
2. Pure planners operate on typed geometry and metadata and do not mutate a component.
3. PDK-specific rule resolution belongs in PDK adapters or physical execution.
4. Geometry executors may import gLayout/gdsfactory but do not invent high-level policy.
5. Verification adapters own external-tool invocation and parsing.
6. Examples contain no reusable engine logic.
7. A new routing strategy requires a pure planner test and an execution/integration test.
8. DRC success is never reported as connectivity success.
9. Route execution requires `PhysicalDesignSnapshot`.
10. Major architectural choices require an ADR.

## Current architectural debt

Do not copy these limitations into new subsystems:

- placement returns only a component rather than a typed `PlacementResult`;
- snapshot construction binds tiles to references by order;
- point-to-point intent fixes access ports such as `gate_E`;
- the current router combines access replacement, strategy selection, and execution;
- route plans do not yet share one complete typed geometry/metrics model;
- extracted instance identity is inferred through generated subcircuit names;
- no typed net or route-group constraint model exists.

## Development sequence

Completed foundation:

```text
✓ extracted-connectivity assertion API
✓ automatic connectivity gate in the routed demo
✓ TerminalRef and AccessPoint
✓ PlacedInstance and RoutingObstacle
✓ read-only PhysicalDesignSnapshot
✓ snapshot-required route execution
✓ typed-obstacle straight blocker and spatial dogleg planners
```

Next milestone:

```text
1. logical NetIntent and typed NetConstraintProfile
2. RouteGroupIntent and inter-net constraints
3. automatic access-selection planner
4. common RoutePlan, RouteSegment, ViaPlan, and RouteMetrics
5. strategy dispatcher for straight, Manhattan, and dogleg planners
```

Then:

```text
6. multi-terminal topology planning
7. matched and differential route-group planners
8. coarse routing graph and congestion model
9. independent schematic LVS
10. targeted verification-driven repair
11. capacitor-array and CDAC routing templates
```

Do not jump directly to multi-net A* routing before the constraint and common-plan contracts exist.

## Change checklist

Before committing engine work, verify:

- Which pipeline translation does this module own?
- Is the input typed and independent of execution tools where possible?
- Is policy inside a planner rather than an executor or example?
- Does the change introduce hidden physical state outside the snapshot?
- Are hard constraints distinct from soft costs?
- Is logical terminal identity separate from physical access?
- Does the test prove connectivity when connectivity matters?
- Has `VALIDATION_STATUS.md` been updated without overstating `/foss` validation?
- Does a major design decision require a new ADR?
