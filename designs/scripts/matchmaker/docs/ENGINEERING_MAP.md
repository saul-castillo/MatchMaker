# MatchMaker Engineering Map

This is the canonical live-state document. Read it before changing the engine. Update it instead of creating another handoff. Detailed `/foss` evidence belongs in `VALIDATION_STATUS.md`; durable decisions belong in ADRs.

## State

```text
base: main
branch: feature/cdac-layout-foundation
PR: #5, draft
PR #1-#4: merged
active checkpoint: repaired B0 reference selector
merge boundary: B0 selector DRC + extraction + exact connectivity
```

PR #5 intentionally stops after the repaired B0 selector is physically validated. Scaled selectors and complete CDAC assembly belong in the next branch.

## Source of truth

The generator never parses Xschem to decide layout.

```text
typed generator specification
-> CircuitManifest
-> placement and routing generation
-> generated layout/netlist
-> independent schematic comparison during LVS
```

Schematics under `designs/libs/core_matchmaker/` are independent LVS references only. They are not hierarchy, sizing, placement, coordinate, or routing input.

## No-hardcoding rule

Algorithms must not hide fixed bit counts, bank sizes, dimensions, coordinates, primitive port names, layer numbers, or spacing rules.

Concrete values may live only in:

```text
typed device/circuit specification
named reviewed preset
explicit placement/routing policy
PDK or device-access adapter
```

Primitive name grammar belongs only in the matching adapter. Layer, width, center, orientation, and envelope data come from runtime geometry or a PDK rule adapter. Tests must vary configuration.

## Pipeline

```text
typed intent
-> device/hierarchy spec
-> CircuitManifest
-> placement intent and policy
-> PlacementPlan
-> geometry + PlacementResult
-> device-specific PhysicalDesignSnapshot
-> NetIntent / route-group / topology intent
-> RouteCandidate / RoutePlan
-> mechanical execution
-> GDS
-> Magic DRC
-> extraction and exact connectivity
-> independent Netgen LVS
```

Each module owns one translation. Examples, primitive wrappers, builders, executors, and verification adapters do not become planners.

## Canonical contracts

```text
design/circuit_manifest.py
  CircuitInstance, CircuitNet, CircuitManifest

design/cdac_manifest_compiler.py
  CdacNamingPolicy, compile_banked_cdac_manifest

design/transmission_gate_naming.py
  NMOS_INSTANCE_NAME, PMOS_INSTANCE_NAME

design/reference_selector_naming.py
  VREF_SWITCH_INSTANCE_NAME, VSS_SWITCH_INSTANCE_NAME
  COMMON_NET_NAME, SELECT_NET_NAME, SELECT_BAR_NET_NAME

specs/
  MosDeviceSpec, MimCapacitorSpec, TransmissionGateSpec
  ReferenceSelectorSpec, CdacBankSpec, BankedCdacSpec
  make_scaled_binary_banked_cdac_spec
  make_gf180_4bit_banked_cdac_reference_spec

placement/core/
  Tile, PlacementPlan, PlacedReferenceBinding, PlacementResult

placement/cdac/capacitor_array_*.py
  CdacCapacitorArrayIntent
  compile_cdac_capacitor_array_plan
  build_cdac_capacitor_array

placement/cdac/transmission_gate_*.py
  TransmissionGateLayoutPolicy, TransmissionGateLayoutIntent
  build_transmission_gate_device_placement

placement/cdac/reference_selector_*.py
  ReferenceSelectorLayoutPolicy, ReferenceSelectorLayoutIntent
  build_reference_selector_child_placement

physical/models.py
  TerminalRef, AccessPoint, PlacedInstance
  RoutingObstacle, PhysicalDesignSnapshot

physical/cdac_capacitor_snapshot.py
  Gf180MimExternalAccessPolicy
  create_cdac_capacitor_array_physical_design_snapshot

physical/gf180_mos_access.py
  Gf180MosExternalAccessPolicy
  classify_gf180_mos_external_port_name

physical/transmission_gate_snapshot.py
  create_transmission_gate_device_snapshot

physical/reference_selector_snapshot.py
  create_reference_selector_child_snapshot

routing/planners/transmission_gate_topology_planner.py
  plan_transmission_gate_signal_topology

routing/planners/reference_selector_topology_planner.py
  plan_reference_selector_topology

generators/transmission_gate_generator.py
  GeneratedTransmissionGate, generate_transmission_gate

generators/reference_selector_generator.py
  GeneratedReferenceSelector, generate_reference_selector

verification/netlist/shared_net_multiplicity.py
  SharedNetMultiplicityExpectation
  evaluate_extracted_shared_net_multiplicity
```

`CircuitManifest` is compiled from typed specs without consulting schematics. New device-family placement returns stable `PlacementResult` bindings. `PhysicalDesignSnapshot.access_points_for(...)` is the supported logical-to-physical bridge.

## Validated foundation

### Routing engine

```text
A0.gate -> A1.gate blocked dogleg
A0.gate -> A2.gate Manhattan Z route
Magic DRC: zero violations
Magic extraction: passed
exact connectivity: passed
```

### CDAC capacitor array

```text
reviewed MIM request: 5 µm x 5 µm
actual primitive bbox: 6.2 µm x 6.2 µm
canonical ports per unit: 8
array: 4 x 4
counts: B0=1, B1=2, B2=4, B3=8, TERM=1
instances: 16
accesses: 128
obstacles: 16
Magic DRC: zero violations
```

The capacitor adapter reads runtime port layers and widths. No capacitor plate is routed yet.

### Base/reset transmission gate

```text
NMOS W=4 µm, PMOS W=8 µm, L=0.28 µm
instances: 2
canonical accesses: 32
input and output: ordinary RoutePlans
Magic DRC: zero violations
Magic extraction: passed
exact shared signal nets: 2
pre-LVS checks: passed
```

`well_*` ports are physical well boundaries, not accepted VDD/VSS metal accesses. Supply semantics remain unresolved rather than guessed.

## B0 reference selector architecture

The selector is hierarchical: two independently generated base transmission gates are placed side-by-side. No MOS geometry is duplicated in selector code.

```text
VREF_TG input -> VREF
VSS_TG input  -> VSS
VREF_TG output + VSS_TG output -> COMMON
VREF_TG control + VSS_TG control_bar -> SELECT
VREF_TG control_bar + VSS_TG control -> SELECT_BAR
```

Three ordinary `RoutePlan` objects are emitted and mechanically executed.

### Failed first topology

The first physical attempt selected `control_N/S` and `control_bar_N/S` ports, then immediately escaped vertically. Those vertical legs crossed child-device interiors. Result:

```text
Magic DRC: failed
violations: 6
```

Preserve this failure. A DRC-clean child does not imply that routing from an internal cardinal access is safe in every direction.

### Replacement topology

```text
COMMON
  direct inner output_E -> output_W strap

SELECT
  VREF control_W
  -> west escape outside VREF child bbox
  -> north perimeter channel
  -> east escape outside VSS child bbox
  -> VSS control_bar_E

SELECT_BAR
  VREF control_bar_E
  -> width-checked central corridor
  -> south channel below both child bboxes
  -> central corridor
  -> VSS control_W
```

All channel centerlines are derived from:

```text
runtime child bboxes
runtime endpoint widths
ReferenceSelectorLayoutPolicy.channel_clearance
ReferenceSelectorLayoutPolicy.channel_spacing
optional explicit route_width
```

No selector coordinate, layer, or primitive dimension is embedded in the planner. The planner fails explicitly if the child gap cannot support the central corridor.

## Final PR #5 checkpoint

```bash
git pull --ff-only
source scripts/matchmaker/env/setup.sh
python scripts/matchmaker/examples/placement/generate_gf180_reference_selector.py
```

Required result:

```text
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared selector net count: 3
pre-LVS checks passed: True
```

The exact three shared nets between the two TG child subcircuits must be `COMMON`, `SELECT`, and `SELECT_BAR`. Fewer, additional, or differently participating shared nets fail.

After this physical result and passing CI, update `VALIDATION_STATUS.md`, mark PR #5 ready, and squash merge. Do not add scaled selectors or full-CDAC placement to this PR.

## Next branch after PR #5

```text
1. validate B1/B2/B3 selector widths through the same generator
2. define complete CDAC macro placement intent
3. place capacitor array, four selectors, and reset TG
4. run whole-placement Magic DRC
5. add committed routes as physical resources
6. add VOUT, B0, and reset topology planning
7. extend to remaining bank/reference/control/supply nets
8. add GF180 layer/width/via resolution as required
9. run extraction, exact connectivity, and independent Netgen LVS
```

## Invariants

1. Typed intent is independent of schematics.
2. Schematics are LVS references only.
3. Concrete values live in specs, presets, policies, or adapters.
4. Logical terminals differ from physical accesses.
5. Pure compilers and planners do not mutate layout.
6. Builders execute plans; they do not invent hierarchy.
7. Adapters interpret primitive APIs once and copy runtime values.
8. Executors do not invent routing policy.
9. Examples contain no reusable policy.
10. New placement returns stable bindings.
11. New routing consumes `PhysicalDesignSnapshot`.
12. Hard constraints reject before ranking.
13. Unsupported cases fail explicitly.
14. DRC never proves connectivity.
15. Connectivity-changing work requires extraction or LVS.
16. Live state stays here; physical evidence stays in `VALIDATION_STATUS.md`.

## Known debt

```text
legacy MOS placement lacks PlacementResult
metal supply access for generated MOS cells is unresolved
committed routes are not typed resources
routing is primarily two-terminal and same-layer
GF180 width/layer/via rules lack a resolver
via planning and execution are absent
complete CDAC topology planning is absent
independent schematic LVS has not passed
stable logical identity is not preserved through extraction end-to-end
```
