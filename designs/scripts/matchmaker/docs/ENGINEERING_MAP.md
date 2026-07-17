# MatchMaker Engineering Map

This is the canonical live-state document for MatchMaker. Read it before changing the engine. It is written for a future coding agent or contributor who must recover the architecture, active APIs, validation boundary, known debt, and exact next action without reconstructing chat history.

## Read order

```text
1. docs/ENGINEERING_MAP.md              architecture and current development state
2. docs/VALIDATION_STATUS.md            physical evidence demonstrated in /foss
3. docs/adr/*.md                         durable decisions and rejected alternatives
4. the module being changed
5. its tests
```

Do not create another handoff or architecture summary. Update this file. Detailed observed run output belongs only in `VALIDATION_STATUS.md`. ADRs are decision records, not status documents.

## Repository state

```text
base branch: main
active branch: feature/cdac-layout-foundation
active PR: #5, draft
PR #1: routing and verification foundation, merged
PR #2: logical net intent, access selection, and RoutePlan IR, merged
PR #3: modular dispatch and non-inline Manhattan routing, merged
PR #4: CDAC reference-library normalization, included before PR #3 merge
```

PR #5 pure tests and Python compilation pass. Physical MIM-port inspection and capacitor-array DRC remain pending in `/foss`.

## Mission

MatchMaker is a deterministic, constraint-driven analog layout synthesis engine for GF180 through gLayout. It must preserve electrical connectivity, analog matching intent, geometric constraints, stable logical identity, and verification evidence while supporting reusable MOS arrays, switches, capacitors, CDACs, comparators, and larger analog cells.

## Source-of-truth boundary

The generator never parses or derives layout intent from Xschem schematics.

```text
typed generator specification
-> logical hierarchy/net manifest
-> placement and routing generation
-> generated layout/netlist
-> independent comparison against schematic during LVS
```

Schematics under `designs/libs/core_matchmaker/` are independent electrical references for later LVS only. They are not placement input, routing input, physical-coordinate input, or a substitute for typed specifications.

## No-hardcoding rule

Reusable algorithms consume typed specifications and policies. Builders and planners must not hide fixed bit counts, bank sizes, device dimensions, coordinates, primitive port names, layer numbers, or spacing rules.

Concrete reviewed values may live in a named preset. Algorithms must still work when those values change.

```text
allowed locations for concrete values:
  typed device/circuit specification
  named technology/reference preset
  explicit placement/routing policy
  PDK rule adapter
```

## Golden pipeline

```text
high-level circuit/layout intent
-> typed device and hierarchy specification
-> logical CircuitManifest
-> typed placement intent and policy
-> deterministic PlacementPlan
-> placed geometry + stable PlacementResult bindings
-> PhysicalDesignSnapshot
-> NetIntent / RouteGroupIntent / specialized topology intent
-> RouteCandidate / RoutePlan
-> mechanical geometry execution
-> GDS
-> Magic DRC
-> Magic extraction and connectivity assertion
-> independent schematic-to-layout Netgen LVS
-> targeted repair or accepted cell
```

Each major module owns one translation. Examples, primitive wrappers, builders, executors, and verification adapters must not silently become planners.

## Existing validated routing foundation

Routing begins with logical connectivity, not fixed primitive ports.

```text
NetIntent + PhysicalDesignSnapshot
-> access-pair enumeration
-> straight / Manhattan / dogleg strategies
-> hard-constraint rejection
-> deterministic cost ranking
-> RoutePlan
-> execution
```

Implemented and physically validated:

```text
A0.gate -> A1.gate blocked external dogleg
A0.gate -> A2.gate two-bend Manhattan route
GF180 Magic DRC: zero violations
Magic extraction: passed
exact endpoint connectivity: passed
```

Detailed evidence is in `VALIDATION_STATUS.md`.

## Canonical contracts

### Logical circuit design

```text
src/matchmaker/design/circuit_manifest.py
  CircuitInstance
  CircuitNet
  CircuitManifest

src/matchmaker/design/cdac_manifest_compiler.py
  CdacNamingPolicy
  compile_banked_cdac_manifest
```

`CircuitManifest` is generated from typed intent. It records stable hierarchy and logical nets without consulting a schematic.

### Device and CDAC specifications

```text
src/matchmaker/specs/mos_device_spec.py
src/matchmaker/specs/capacitor_device_spec.py
src/matchmaker/specs/transmission_gate_spec.py
src/matchmaker/specs/banked_cdac_spec.py
```

Current CDAC contracts:

```text
MimCapacitorSpec
TransmissionGateSpec
ReferenceSelectorSpec
CdacBankSpec
BankedCdacSpec
make_scaled_binary_banked_cdac_spec
make_gf180_4bit_banked_cdac_reference_spec
```

The generic binary compiler derives unit counts and selector widths from parameters. The GF180 reviewed values are isolated in the named reference preset.

### Placement

```text
src/matchmaker/placement/core/tile_plan.py
  Tile
  PlacementPlan

src/matchmaker/placement/core/placement_result.py
  PlacedReferenceBinding
  PlacementResult

src/matchmaker/placement/cdac/capacitor_array_intent.py
  CdacCapacitorArrayIntent

src/matchmaker/placement/cdac/capacitor_array_plan_compiler.py
  near-square grid inference
  180-degree inversion-orbit generation
  compatible odd-residual pairing
  deterministic fair pair distribution
  compile_cdac_capacitor_array_plan

src/matchmaker/placement/cdac/capacitor_array_builder.py
  build_cdac_capacitor_array
```

New device-family builders return stable `PlacementResult` bindings. The validated legacy MOS builder still returns only a component and remains technical debt.

### Physical routing state

```text
src/matchmaker/physical/models.py
  TerminalRef
  AccessPoint
  PlacedInstance
  RoutingObstacle
  PhysicalDesignSnapshot
```

`PhysicalDesignSnapshot.access_points_for(TerminalRef(...))` is the supported electrical-to-physical bridge. Primitive names must be adapted once in a device-specific physical adapter.

### Routing plans and execution

```text
src/matchmaker/routing/planners/route_candidate.py
src/matchmaker/routing/plans/route_plan.py
src/matchmaker/routing/routers/route_plan_executor.py
```

Canonical types:

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

Executors draw resolved plans. They do not choose terminals, accesses, topology, channels, widths, layers, or vias. Via execution is not implemented and must fail explicitly.

## Device-specific extension model

A universal analog router is not the target.

### Physical adapters

```text
MOS adapter -> gate/source/drain/bulk
capacitor adapter -> top/bottom plate
transmission-gate adapter -> input/output/control/control_bar/supplies
reference-selector adapter -> references/common/control/supplies
CDAC adapter -> banks/selectors/reset/public nets
```

### Specialized topology strategies

```text
CdacRoutingTemplateStrategy
RectilinearGraphStrategy
DifferentialPairStrategy
MatchedRouteGroupStrategy
MatchedBusStrategy
ShieldedNetStrategy
```

All consume common intent/snapshot contracts and emit common plan types. Specialized geometry execution paths are not allowed.

### PDK rule adapters

Semantic classes such as `signal`, `reference`, `high_current`, or `high_voltage` must resolve through a GF180 adapter into concrete layers, widths, spacing, vias, arrays, and enclosures. Generic code must not contain PDK rule numbers.

## Active CDAC foundation slice

### Implemented on PR #5

```text
parameterized MIM/TG/selector/bank/CDAC specs
named GF180 reviewed-reference preset
schematic-independent CircuitManifest compiler
generic PlacementResult
3/4/5-bit pure-test coverage
algorithmic grid inference
algorithmic inversion symmetry
compatible B0/termination residual pairing
explicit spacing and orientation policies
GF180 MIM primitive wrapper
MIM primitive diagnostic
capacitor-array geometry builder
GDS + Magic DRC example
```

The reviewed reference preset resolves to 15 switched unit capacitors, one termination unit, four shared selectors, one reset transmission gate, and 18 MOS devices. No generic algorithm assumes those counts.

### Required `/foss` checkpoint

Run in this order:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_mim_capacitor.py
python scripts/matchmaker/examples/placement/generate_cdac_capacitor_array.py
```

The diagnostic must establish actual installed-gLayout capacitor port names, centers, orientations, widths, and layers. Do not implement the capacitor physical adapter by guessing them.

### Next implementation after the diagnostic

```text
1. canonical capacitor top/bottom access adapter from observed primitive data
2. capacitor-array PhysicalDesignSnapshot
3. parameterized transmission-gate geometry builder
4. parameterized reference-selector hierarchy
5. selector/reset placement policy with reserved routing channels
6. complete unrouted CDAC placement and Magic DRC
7. committed-route resources and GF180 routing-rule resolution
8. VOUT, B0, and reset topology planning
9. extraction and exact connectivity checks
10. remaining bank/reference/control/supply routing
11. independent schematic LVS
```

## Package ownership

```text
design/          logical hierarchy and connectivity compilation
specs/           typed device and circuit-family specifications
placement/core/  generic plans, policies, results, and stable bindings
placement/mos/   MOS-specific placement
placement/cdac/  CDAC-specific placement policy and construction
physical/        placed-state snapshots and access adapters
primitives/      PDK/gLayout primitive construction only
routing/intents/ logical net and route-group requests
routing/planners pure route/topology planning
routing/plans/   common execution-ready IR
routing/routers/ mechanical geometry execution
verification/    DRC, extraction, connectivity, LVS, parsing
outputs/         generated artifact conventions
examples/        package wiring and diagnostics only
```

## Architectural invariants

1. Typed generator intent is independent of schematics.
2. Schematics are LVS references only.
3. Concrete design values live in specs, presets, policies, or PDK adapters.
4. Logical terminals are separate from physical access points.
5. Pure compilers and planners do not mutate layout components.
6. Builders execute placement plans; they do not invent hierarchy or symmetry policy.
7. Executors do not invent routing policy.
8. Examples contain no reusable engine logic.
9. New device-family placement returns stable logical bindings.
10. New routing work consumes `PhysicalDesignSnapshot`.
11. Hard constraints reject before soft-cost ranking.
12. Candidates and plans retain metrics, evidence, and provenance.
13. Unsupported cases fail explicitly.
14. DRC never proves electrical correctness.
15. Connectivity-changing integration requires extraction or LVS evidence.
16. Major architecture changes require an ADR.
17. Live state belongs here; observed physical output belongs in `VALIDATION_STATUS.md`.

## Known debt

- Legacy MOS placement does not yet return `PlacementResult`.
- MOS snapshot construction still depends partly on recovered reference bindings.
- No capacitor physical adapter exists until the `/foss` diagnostic is reviewed.
- Transmission-gate and selector layout builders do not exist yet.
- Routing is two-terminal and same-layer only.
- Committed routes are not typed routing resources.
- GF180 width/layer/via rules are not resolved through a dedicated adapter.
- Via planning and execution are absent.
- Multi-terminal CDAC topology planning is absent.
- Congestion, rip-up/reroute, group matching, and shielding are absent.
- Independent schematic-to-layout LVS has not passed.
- Extracted instance identity is not yet stable end-to-end.

## Required change discipline

Before merging engine work, answer:

- Which pipeline translation does this module own?
- Is input typed and independent of schematics and execution tools?
- Are concrete values isolated from algorithms?
- Is reusable policy in a compiler/planner rather than a builder/executor/example?
- Does the output retain stable identity and provenance?
- Are unsupported cases explicit?
- Do tests vary configuration rather than exercise only one preset?
- Does `/foss` integration prove the claimed DRC/connectivity boundary?
- Have this map and `VALIDATION_STATUS.md` been updated without duplicating or overstating evidence?
