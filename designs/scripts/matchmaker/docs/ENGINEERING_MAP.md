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

Do not create another handoff or architecture summary. Update this file instead. `VALIDATION_STATUS.md` is the only place for detailed observed physical-run output. ADRs are append-only decision records, not status documents.

## Mission

MatchMaker is a deterministic, constraint-driven analog layout synthesis engine for GF180 through gLayout. It must preserve electrical connectivity, analog matching intent, geometric constraints, and verification evidence while supporting reusable MOS arrays, switches, capacitors, CDACs, comparators, and larger analog cells.

## Repository state at this revision

```text
base branch: main
active branch: feature/cdac-layout-foundation
active PR: not opened yet
PR #1: routing and verification foundation, merged
PR #2: logical net intent, access selection, and RoutePlan IR, merged
PR #3: modular strategy dispatch and non-inline Manhattan routing, merged
PR #4: CDAC reference-library documentation and normalization, merged through PR #3
```

The current development slice is the first generator path for the banked 4-bit CDAC family.

## Non-negotiable source-of-truth boundary

The generator does **not** parse or derive layout intent from Xschem schematics.

```text
typed generator intent/specification
-> placement and routing generation
-> generated layout/netlist
-> independent comparison against schematic during LVS
```

The schematics in `designs/libs/core_matchmaker/` are independent electrical references for later LVS. They are not placement input, routing input, a source of physical coordinates, or a substitute for typed generator specifications.

## No-hardcoding rule

Reusable algorithms consume typed specifications and policies. Builders and planners must not contain hidden design-instance literals such as fixed bit counts, fixed bank sizes, fixed coordinates, primitive port names, layer numbers, or device dimensions.

A named preset may encode a reviewed concrete design, such as the current GF180 4-bit banked-CDAC reference. Preset values are configuration data. Algorithms must continue to work when those values change.

Every device-specific literal must therefore live in one of:

```text
typed device/circuit specification
named technology/reference preset
PDK rule adapter
explicit placement/routing policy
```

Never place such literals inside generic compilation, placement, routing, or execution logic.

## Golden pipeline

```text
high-level circuit/layout intent
-> typed device and hierarchy specification
-> typed placement intent and policy
-> deterministic placement plan
-> placed GF180 geometry + stable instance bindings
-> PhysicalDesignSnapshot
-> NetIntent / RouteGroupIntent / specialized topology intent
-> routing strategy or topology planning
-> RouteCandidate / RoutePlan
-> mechanical geometry execution
-> GDS
-> Magic DRC
-> Magic extraction and connectivity assertion
-> independent schematic-to-layout Netgen LVS
-> targeted repair or accepted cell
```

Each major module owns one translation. No example, executor, primitive wrapper, or verification adapter may silently become a planner.

## Current validated routing foundation

Routing begins with logical connectivity, not fixed primitive ports.

```text
NetIntent(A0.gate, A1.gate)
+ NetConstraintProfile
+ PhysicalDesignSnapshot
-> enumerate legal physical access points
-> generate candidates with independent strategies
-> reject hard-constraint violations
-> rank feasible candidates deterministically
-> compile selected candidate into RoutePlan
-> execute resolved geometry
```

Implemented strategy modules:

```text
straight_route_strategy.py
  clear same-layer aligned route

manhattan_route_strategy.py
  non-inline L routes for perpendicular accesses
  non-inline Z routes for parallel accesses
  midpoint, obstacle-edge, and outer-channel candidates

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

The A0-to-A1 blocked dogleg and A0-to-A2 non-inline Manhattan regressions have passed GF180 Magic DRC, extraction, and exact connectivity checks in `/foss`. Detailed evidence remains in `VALIDATION_STATUS.md`.

## Canonical data contracts

### Logical routing intent

File: `src/matchmaker/routing/intents/net_intent.py`

```text
NetIntent
NetConstraintProfile
RouteGroupIntent
RouteGroupConstraintProfile
```

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

### Routing candidate and plan evidence

Files:

```text
src/matchmaker/routing/planners/route_candidate.py
src/matchmaker/routing/plans/route_plan.py
```

Canonical models:

```text
RouteCandidate
CandidateRejection
StrategyDispatchResult
RoutePlanningError
RoutePlan
RouteSegment
ViaPlan
RouteMetrics
ConstraintCheck
```

### Execution

File: `src/matchmaker/routing/routers/route_plan_executor.py`

The executor draws an already resolved `RoutePlan`. It does not choose terminals, access points, topology, strategy, channel, width, or layer. Via execution is not implemented and must fail explicitly.

## Device-specific extension model

A single universal analog router is not the target. MatchMaker uses common contracts with device adapters and specialized strategy/topology modules.

### Physical adapters

Adapters translate placed device structure into logical terminals, physical access choices, obstacles, and local keepouts.

```text
MOS adapter -> gate/source/drain/bulk
capacitor adapter -> top/bottom plate
transmission-gate adapter -> input/output/control/control_bar/supplies
reference-selector adapter -> VREF/VSS/common/control/control_bar/supplies
CDAC adapter -> capacitor banks, selectors, reset switch, public nets
```

Device construction details must not leak into the generic dispatcher.

### Routing strategies and topology modules

Planned families:

```text
CdacRoutingTemplateStrategy
RectilinearGraphStrategy
DifferentialPairStrategy
MatchedRouteGroupStrategy
MatchedBusStrategy
ShieldedNetStrategy
```

They consume common intent/snapshot contracts and emit common candidate/plan types. Specialized analog topology is allowed; specialized geometry executors are not.

### PDK rule adapters

Semantic intent such as `signal`, `reference`, `high_current`, or `high_voltage` must resolve through a GF180 rule adapter into concrete layers, widths, spacing, via types, via arrays, and enclosures. Generic intent and strategy code must not hard-code PDK rule numbers.

## CDAC layout-foundation slice

### Independent typed input

The first generator target is a parameterized banked binary CDAC family. Its source of truth will be typed specifications under `specs/` and typed CDAC placement intent under `placement/cdac/`.

A named preset will reproduce the reviewed GF180 4-bit reference:

```text
binary bank unit counts: 1, 2, 4, 8
termination units: 1
minimum MIM geometry: supplied by the preset
selector sizing: supplied per bank by the preset
reset switch sizing: supplied by the preset
```

No compiler or builder may assume four bits, sixteen capacitors, a 4x4 grid, or the reviewed transistor widths.

### First implementation checkpoints

```text
1. typed capacitor, transmission-gate, selector, bank, and CDAC specifications
2. parameterized logical hierarchy/net manifest generated from those specifications
3. generic PlacementResult with stable instance-reference bindings
4. algorithmic inversion-symmetric capacitor-array placement compiler
5. installed-gLayout GF180 MIM primitive diagnostic and wrapper
6. capacitor-array geometry builder and physical adapter
7. parameterized transmission-gate/reference-selector hierarchy
8. complete CDAC placement with reserved routing channels
9. specialized CDAC topology planning beginning with VOUT, B0, and reset
10. DRC, extraction/connectivity, and later independent schematic LVS
```

### Initial placement policy

The capacitor compiler receives total unit counts and optional grid dimensions. When dimensions are omitted it infers a near-square factorization. It creates 180-degree inversion pairs algorithmically, distributes even-count banks across those pairs, and pairs odd residual groups only when their unit devices are physically compatible. It must reject impossible symmetry requests rather than silently produce an asymmetric array.

The current reviewed B0 unit and equal-valued termination unit may occupy one inversion pair because both use the same unit-capacitor specification. That relationship must be represented explicitly by policy and validated by the compiler.

### First physical acceptance boundary

The first non-negotiable generated artifact is:

```text
typed CDAC specification
-> deterministic capacitor and selector placement
-> stable logical instance bindings
-> CDAC PhysicalDesignSnapshot
-> GDS
-> GF180 Magic DRC with zero violations
```

Electrical routing will then be added incrementally. A CDAC is not considered generated or verified until extracted connectivity and independent LVS demonstrate the intended hierarchy.

## Package ownership

```text
specs/
  typed PDK-facing device and circuit-family specifications

placement/core/
  reusable tile, grid, plan, result, orientation, and spacing infrastructure

placement/mos/
  MOS intent compilation, dummy policy, binding, and placement

placement/cdac/
  CDAC array policy, compilation, hierarchy placement, and stable bindings

physical/
  placed instances, logical terminals, physical accesses, obstacles, snapshots

primitives/
  PDK/gLayout primitive construction and canonical port adaptation

routing/intents/
  logical net and route-group requests

routing/planners/
  pure strategies, topology planners, dispatch, obstacle checks, plan compilation

routing/plans/
  common execution-ready route IR and metrics

routing/routers/
  mechanical geometry execution

verification/
  DRC, extraction, connectivity assertions, LVS, report parsing

outputs/
  generated-cell paths and artifact conventions

examples/
  package wiring and diagnostics only; no reusable engine policy
```

## Architectural invariants

1. Typed generator intent is independent of Xschem schematics.
2. Schematics are independent LVS references only.
3. Logical terminals are separate from physical access points.
4. Device/reference values live in typed specs or named presets, not hidden algorithm literals.
5. Hard constraints reject candidates before soft-cost ranking.
6. Pure planners do not mutate gdsfactory or gLayout components.
7. Executors do not invent placement or routing policy.
8. Examples contain no reusable engine logic.
9. Placement builders return stable logical instance bindings for new device families.
10. New routing work consumes `PhysicalDesignSnapshot`.
11. New strategies emit common `RouteCandidate` and `RoutePlan` types.
12. Candidates and plans retain metrics, blockers, constraint evidence, and provenance.
13. Unsupported cases fail explicitly rather than drawing unsafe fallback geometry.
14. DRC success never proves electrical correctness.
15. Every connectivity-changing integration test requires extraction or LVS evidence.
16. PDK rule numbers belong in PDK adapters or detailed physical planning.
17. Major architecture changes require an ADR.
18. Live architecture/status belongs here; observed physical evidence belongs in `VALIDATION_STATUS.md`.

## Known implementation debt

- The validated MOS placement path still returns a component rather than `PlacementResult`.
- MOS snapshot construction still relies partly on placement/reference binding assumptions.
- Routing is two-terminal and same-layer only.
- Committed routes are not represented as typed obstacles or routing resources.
- Width classes and layer policies are not resolved through a GF180 rule adapter.
- Via planning and execution are not implemented.
- Multi-terminal topology planning is not implemented.
- Matching, differential symmetry, shielding, and separation are typed but not planned.
- Congestion-aware graph search and rip-up/reroute are not implemented.
- Independent schematic-to-layout Netgen LVS has not passed.
- Extracted instance identity is inferred from generated subcircuit names rather than stable logical IDs.
- No capacitor or transmission-gate primitive adapter exists yet.

## Immediate development order

```text
1. typed CDAC/device specs and reference preset
2. logical hierarchy/net manifest derived from typed specs
3. generic PlacementResult and algorithmic capacitor-array plan
4. GF180 MIM primitive diagnostic and adapter
5. capacitor-array placement, snapshot, GDS, and DRC
6. transmission-gate and selector hierarchy placement
7. complete unrouted CDAC placement and DRC
8. committed-route resources and GF180 routing-rule resolution
9. VOUT/B0/reset topology planning and extracted connectivity
10. remaining bank/reference/control/supply routing
11. independent schematic LVS
```

## Required change discipline

Before merging engine work, answer:

- Which pipeline translation does this module own?
- Is its input typed and independent of schematics and execution tools?
- Are concrete design values isolated in specs, presets, or PDK adapters?
- Is reusable policy in a compiler/planner rather than a builder, executor, or example?
- Are hard constraints distinct from soft costs?
- Does the output retain evidence, provenance, and stable logical identity?
- Are unsupported cases explicit?
- Do pure tests cover configurable behavior rather than only the reference preset?
- Does `/foss` integration prove DRC and extracted connectivity where applicable?
- Have this map, `VALIDATION_STATUS.md`, and any relevant ADR been updated without duplicating status or overstating validation?
