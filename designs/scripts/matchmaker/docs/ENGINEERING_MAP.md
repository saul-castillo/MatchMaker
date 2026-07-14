# MatchMaker Engineering Map

This is the first document to read before changing the engine. It is intentionally optimized for both human contributors and coding agents that need to recover the project architecture quickly without reconstructing it from examples or commit history.

## Mission

MatchMaker is a deterministic, constraint-driven analog layout synthesis engine. Its job is not merely to draw legal geometry. It must preserve circuit connectivity, analog matching intent, symmetry, electrical constraints, and verification evidence while translating a high-level design description into GF180 layout.

The long-term target is a reusable generator stack for matched MOS structures, switch networks, capacitor arrays, CDACs, and larger analog blocks.

## Golden pipeline

```text
high-level circuit and layout intent
→ typed device, placement, net, and route-group intent
→ deterministic intent compilation
→ placement plan
→ physical-design snapshot
→ routing problems
→ route plans
→ geometry execution
→ local geometric/connectivity checks
→ GDS
→ DRC
→ extraction and connectivity audit
→ LVS
→ targeted repair or accepted cell
```

Every major module should own one translation in this pipeline. A module should not silently perform work belonging to several stages.

## Core working principle

Routing is a constrained physical synthesis problem, not a direct call from two named ports to a route primitive.

The canonical routing input is:

```text
logical net or route group
+ logical terminals that must be connected
+ electrical and analog constraints
+ available physical access points
+ placed obstacles and keepouts
+ routing-layer resources
+ routes already committed
```

The canonical routing output is a typed `RoutePlan` containing:

```text
selected terminal access points
+ net topology
+ coarse path or routing channel
+ detailed Manhattan segments and vias
+ predicted metrics
+ evidence that hard constraints were satisfied
```

Geometry is produced only after the plan exists.

## Critical distinction: terminal versus access point

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
A0__gate_N
metal-2 access at coordinate (x, y)
```

Routing intent should eventually refer to `A0.gate`, not permanently commit to `A0__gate_E`. The access selector chooses among available physical access points using placement, obstacles, direction, layer, and route-group constraints.

The centroid routing smoke test demonstrated why this matters: a legal `gate_E` route crossed two unrelated devices, while the correct solution used outward gate access and a spatial dogleg outside the array.

## Constraint model

Constraints must be typed and divided into hard requirements and soft costs.

### Hard constraints

A plan is invalid when any hard constraint is violated. Examples:

- connect exactly the intended terminals;
- do not connect unrelated terminals;
- obey PDK width, spacing, enclosure, and via rules;
- obey allowed and forbidden routing layers;
- avoid obstacle and keepout regions;
- satisfy required net separation;
- satisfy mandatory symmetry or route-group topology;
- obey a strict maximum length, resistance, or via count when specified.

### Soft costs

Soft costs rank valid candidates. Examples:

- total wire length;
- estimated resistance and capacitance;
- via count;
- bend count;
- congestion usage;
- coupling exposure;
- deviation from matched length;
- deviation from a symmetry axis;
- use of scarce routing channels.

A planner should minimize a deterministic weighted cost only after all hard constraints pass.

### Translating analog language

Do not preserve vague phrases deep inside the engine. Compile them into typed constraints.

```text
"keep this short"
→ maximum length and/or maximum resistance

"make this thick"
→ width class, current target, and PDK-resolved minimum width

"keep this away from high potential"
→ pairwise or class-based separation constraint, optional shielding, and allowed-layer policy

"match these traces"
→ route-group constraint on topology, length, vias, bends, and symmetry

"sensitive node"
→ coupling/separation class and routing priority
```

A net property alone is not always sufficient. Separation, shielding, matching, and symmetry commonly relate two or more nets and therefore belong in a `RouteGroupIntent` or explicit inter-net constraint.

## Hybrid routing architecture

MatchMaker should not attempt to build one universal industrial router immediately. The efficient architecture is a deterministic strategy ladder behind a common planner interface.

```text
1. direct straight route
2. simple L/C route family
3. explicit spatial dogleg or reserved channel
4. coarse rectilinear routing graph with A* or equivalent search
5. multi-terminal topology plus branch routing
6. multi-net congestion handling and negotiated rip-up/reroute
```

Specialized analog templates should remain valid strategies. A symmetric differential pair, repeated switch bank, or CDAC bus may be routed more reliably by a template than by unconstrained graph search. Template planners and search planners should both emit the same `RoutePlan` representation and be evaluated by the same constraints and metrics.

## Routing stages

Keep these stages separate even when the first implementation is small.

### 1. Net and route-group compilation

Resolve logical connectivity and constraints into a `RoutingProblem`.

### 2. Topology planning

For two-terminal nets, topology is trivial. For multi-terminal nets, choose a tree or analog-specific topology before drawing segments. Initial general support can use a deterministic minimum-spanning-tree approximation; matching-critical structures may use a template topology.

### 3. Access selection

Choose physical access candidates for every logical terminal. Access selection must understand transformed instance orientation and should not be hard-coded inside examples.

### 4. Coarse path or channel planning

Choose which side of obstacles, reserved channel, or coarse routing graph the net will use. This stage handles global spatial relations and congestion.

### 5. Detailed geometry planning

Resolve exact Manhattan segments, widths, layers, vias, and corner geometry using PDK rules.

### 6. Execution

A geometry executor converts the already-resolved plan into gLayout/gdsfactory geometry. Executors should be mechanically simple and should not invent routing policy.

### 7. Validation and feedback

Run cheap local checks first, then DRC, extraction/connectivity checks, and LVS. Failures should return structured evidence to the planner rather than trigger arbitrary geometry mutations.

## Physical-design snapshot

Routing should consume a stable physical database rather than infer placement state from reference order or scattered `Component.info` keys.

The target representation is conceptually:

```python
PhysicalDesignSnapshot(
    component=...,
    instances={instance_id: PlacedInstance(...)},
    terminal_access={TerminalRef(...): (AccessPoint(...), ...)},
    obstacles=(Obstacle(...), ...),
    keepouts=(Keepout(...), ...),
    layer_stack=RoutingLayerModel(...),
    committed_routes=(RouteRecord(...), ...),
)
```

The current promoted-port namespace and `component.info` obstacle metadata are transitional adapters. They are useful for the present smoke tests, but new multi-net work should migrate toward an explicit placement/physical-design result object.

## Package ownership

Current package boundaries:

```text
specs/
  PDK-independent device specifications

placement/core/
  reusable tiles, plans, orientation, spacing, and grid infrastructure

placement/mos/
  MOS-specific intent compilation, dummy policy, binding, and placement

primitives/
  PDK/gLayout primitive construction

routing/intents/
  routing requests and endpoint descriptions; currently transitional

routing/ports/
  promoted physical-access discovery; currently transitional

routing/planners/
  pure geometric and obstacle-aware planning

routing/routers/
  physical route execution adapters

verification/
  DRC, extraction, LVS, report parsing, and connectivity inspection

outputs/
  artifact paths and generated-cell filesystem conventions

examples/
  package wiring only; no engine policy
```

Target additions should introduce explicit physical-design, constraint, topology, access, route-group, and metrics models without moving gLayout dependencies into pure planning code.

## Dependency rules

These rules are architectural invariants.

1. Intent and constraint models must not import gLayout, gdsfactory, Magic, or Netgen.
2. Pure planners must operate on typed geometry and metadata, not mutate a component.
3. PDK-specific rule resolution belongs in PDK adapters or physical execution, not generic intent models.
4. Geometry builders and executors may import gLayout/gdsfactory but should not invent high-level policy.
5. Verification adapters own external-tool invocation and report parsing.
6. Examples contain no reusable engine logic.
7. A new routing strategy requires a pure planner test and an execution/integration test.
8. DRC success is not connectivity success. Extraction or LVS must confirm electrical intent.
9. Hidden state in `Component.info` should not become the long-term inter-module API.
10. Free-form user language must be compiled into typed constraints before planning.

## Current validated milestone

The current branch has demonstrated:

```text
MOS centroid placement
→ stable promoted gate access
→ blocked straight-route detection
→ outward access selection
→ explicit spatial dogleg outside the array
→ GDS generation
→ GF180 Magic DRC with zero violations
→ Magic SPICE extraction
→ routed node present on exactly the two intended A instances
```

This is a verified point-to-point obstacle-avoidance slice, not a general router and not formal LVS.

## Known architectural debt

- `PointToPointRouteIntent` still binds directly to physical port names.
- Placement returns a raw component rather than a typed placement/physical-design result.
- Obstacle and route metadata are stored in `Component.info`.
- Route planning is two-terminal only.
- Existing routes are not yet treated as obstacles or congestion resources.
- There is no central constraint model or route-group model.
- There is no routing-layer resource graph.
- Connectivity assertions are not yet part of the demo exit criteria.
- Netgen LVS has not yet passed against an independent schematic.

## Development sequence

Do not jump directly from the current dogleg to a large maze router. Use this order:

```text
1. automatic extracted-connectivity assertions
2. PhysicalDesignSnapshot / PlacementResult manifest
3. logical TerminalRef and AccessPoint models
4. typed NetIntent and RoutingConstraintProfile
5. common RoutePlan and route metrics
6. strategy dispatcher for straight, L/C, and dogleg planners
7. multi-terminal topology planning
8. route-group constraints for matched and differential nets
9. coarse routing graph and congestion model
10. multi-net rip-up/reroute
11. LVS-driven repair loop
12. capacitor-array and CDAC-specific routing templates
```

## Change protocol

When adding a major model or module:

1. update this map if ownership or the pipeline changes;
2. add or amend an ADR under `docs/adr/` for a durable architectural decision;
3. add pure tests for planning behavior;
4. add one container integration example when geometry or verification changes;
5. update `VALIDATION_STATUS.md` with only results actually demonstrated in `/foss`;
6. keep the README at the milestone level and avoid duplicating low-level details there.
