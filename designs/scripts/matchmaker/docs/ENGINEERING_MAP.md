# MatchMaker Engineering Map

This is the canonical live-state document. Read it before changing the engine. Update it instead of creating another handoff. Detailed `/foss` output belongs in `VALIDATION_STATUS.md`; durable decisions belong in ADRs.

## State

```text
base: main
branch: feature/cdac-layout-foundation
PR: #5, draft
PR #1-#4: merged
active checkpoint: base transmission-gate extraction and exact two-net connectivity
```

Physically demonstrated on PR #5:

```text
4 x 4 GF180 MIM array
  16 stable instances
  128 canonical accesses
  16 obstacles
  Magic DRC: zero violations

base/reset transmission gate
  NMOS W=4 µm, PMOS W=8 µm, L=0.28 µm
  2 stable instances
  32 canonical accesses
  2 ordinary RoutePlans for parallel signal nets
  Magic DRC: zero violations
```

The next gate is Magic extraction proving that the generated NMOS and PMOS share exactly two distinct signal nets.

## Source of truth

The generator never parses Xschem to decide layout.

```text
typed generator specification
-> CircuitManifest
-> placement and routing generation
-> generated layout/netlist
-> independent schematic comparison during LVS
```

Schematics under `designs/libs/core_matchmaker/` are LVS references only. They are not hierarchy, sizing, placement, coordinate, or routing input.

## No-hardcoding rule

Algorithms must not hide fixed bit counts, bank sizes, dimensions, coordinates, primitive port names, layer numbers, or spacing rules.

Concrete values may live only in:

```text
typed device/circuit specification
named reviewed preset
explicit placement/routing policy
PDK or device-access adapter
```

Primitive name grammar belongs only in the matching adapter. Layer, width, center, orientation, and envelope data are copied from runtime geometry or resolved by a PDK rule adapter. Tests must vary configuration.

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

placement/cdac/transmission_gate_intent.py
  TransmissionGateLayoutPolicy
  TransmissionGateLayoutIntent

placement/cdac/transmission_gate_builder.py
  build_transmission_gate_device_placement

physical/models.py
  TerminalRef, AccessPoint, PlacedInstance
  RoutingObstacle, PhysicalDesignSnapshot

physical/cdac_capacitor_snapshot.py
  Gf180MimExternalAccessPolicy
  classify_gf180_mim_external_port_name
  create_cdac_capacitor_array_physical_design_snapshot

physical/gf180_mos_access.py
  Gf180MosExternalAccessPolicy
  classify_gf180_mos_external_port_name
  gf180_mos_external_port_name

physical/transmission_gate_snapshot.py
  create_transmission_gate_device_snapshot

routing/planners/transmission_gate_topology_planner.py
  TransmissionGateRouteBundle
  plan_transmission_gate_signal_topology

generators/transmission_gate_generator.py
  GeneratedTransmissionGate
  generate_transmission_gate

verification/netlist/shared_net_multiplicity.py
  SharedNetMultiplicityExpectation
  SharedNetMultiplicityResult
  evaluate_shared_net_multiplicity
  evaluate_extracted_shared_net_multiplicity
```

`CircuitManifest` is compiled from typed specs without consulting a schematic. New device-family placement returns stable `PlacementResult` bindings. `PhysicalDesignSnapshot.access_points_for(...)` is the supported logical-to-physical bridge.

## Existing routing foundation

```text
NetIntent + PhysicalDesignSnapshot
-> access-pair enumeration
-> straight / Manhattan / dogleg strategies
-> hard-constraint rejection
-> deterministic ranking
-> RoutePlan
-> mechanical execution
```

Validated MOS regressions:

```text
A0.gate -> A1.gate blocked dogleg
A0.gate -> A2.gate Manhattan Z route
Magic DRC: zero violations
Magic extraction: passed
exact connectivity: passed
```

## Validated CDAC capacitor foundation

```text
reviewed unit request: 5 µm x 5 µm
actual primitive bbox: 6.2 µm x 6.2 µm
raw primitive ports: 264
canonical external ports: 8

top_met_{N,E,S,W} -> top
bottom_met_{N,E,S,W} -> bottom

array grid: 4 x 4
counts: B0=1, B1=2, B2=4, B3=8, TERM=1
instances: 16
accesses: 128
obstacles: 16
Magic DRC: zero violations
```

Observed layer and width values are evidence only. The capacitor adapter reads them from runtime ports. No capacitor plate is routed yet.

## Transmission-gate architecture

### Observed primitive contract

The typed base/reset switch uses NMOS W=4 µm and PMOS W=8 µm at L=0.28 µm. The installed primitives expose thousands of nested ports but only 16 simple canonical ports per device:

```text
gate_{N,E,S,W}
source_{N,E,S,W}
drain_{N,E,S,W}
well_{N,E,S,W} -> physical bulk boundary
```

Signal accesses are on one common runtime metal layer. NMOS and PMOS source/drain vertical offsets differ by the same amount, allowing one derived PMOS translation to align both nets. The generator does not copy those coordinates or layers into policy.

`well_*` ports are not accepted as `VDD` or `VSS` metal ports. The concise diagnostic did not expose another simple unclassified tie/substrate-tap access. Supply assignment remains blocked rather than guessed.

### Implemented translation boundaries

```text
TransmissionGateLayoutIntent
-> build_transmission_gate_device_placement
   derives separation from actual bboxes
   derives PMOS vertical translation from source/drain ports
   returns stable NMOS/PMOS PlacementResult

PlacementResult
-> create_transmission_gate_device_snapshot
   retains only simple external MOS ports
   copies runtime layer/width/center/orientation

intent + snapshot
-> plan_transmission_gate_signal_topology
   selects inward source and drain accesses
   requires same layer and horizontal alignment
   emits two ordinary RoutePlans

placement + plans
-> generate_transmission_gate
   executes ordinary RoutePlans
   exposes input/output/control/control_bar ports
```

No specialized geometry executor is allowed. Supply semantics are intentionally absent until a metal tie contract is demonstrated.

### Current physical result

```text
generated bbox: (-16.48, -11.565) to (11.49, 10.065)
instances: 2
accesses: 32
obstacles: 2
input route:  source_E -> source_W, length 13.345, width 0.5
output route: drain_E -> drain_W, length 13.345, width 0.5
route layer: runtime (36, 0)
Magic DRC: zero violations
```

The GDS visually shows two separated primitive envelopes and two parallel horizontal signal straps. DRC does not prove connectivity.

### Immediate `/foss` checkpoint

```bash
git pull --ff-only
source scripts/matchmaker/env/setup.sh
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
```

The command now performs:

```text
GDS generation
-> Magic DRC
-> Magic extraction
-> exact shared-net multiplicity assertion
```

Required result:

```text
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared signal net count: 2
pre-LVS checks passed: True
```

The assertion requires exactly two distinct shared nets with the generated NMOS and PMOS subcircuits as the complete participant multiset. One shared net, three shared nets, or an extra participant fails.

## Cleanup completed at this checkpoint

```text
historical dummy keyword aliases are resolved against the installed signature
unsupported dummy-alias warnings are no longer expected
child MOS cells are explicitly renamed before GDS writing
pure modules no longer import gLayout through package __init__ side effects
CI retains a compact uploaded test log for future failure diagnosis
```

## Next development order

```text
1. pass transmission-gate DRC, extraction, and exact two-net connectivity
2. inspect deeper primitive tie/substrate-tap exports only if supply access is required
3. define typed VDD/VSS access policy from observed metal ports
4. validate the same generator at B1/B2/B3 scaled widths
5. build a parameterized two-transmission-gate reference selector
6. prove selector input/common/control connectivity
7. place four scaled selectors and reset beside the capacitor array
8. generate the complete unrouted CDAC placement and run Magic DRC
9. add committed routes as typed physical resources
10. add VOUT, B0, and reset topology planning
11. extend to remaining bank/reference/control/supply nets
12. run extraction, exact connectivity checks, and independent Netgen LVS
```

## Device-specific extension model

```text
MOS adapter -> gate/source/drain/bulk
capacitor adapter -> top/bottom
transmission-gate adapter -> input/output/control/control_bar/supplies
reference-selector adapter -> references/common/control/supplies
CDAC adapter -> banks/selectors/reset/public nets
```

Specialized planners consume common intent/snapshot contracts and emit common plan types. Specialized execution paths are prohibited.

## Invariants

1. Typed intent is independent of schematics.
2. Schematics are LVS references only.
3. Concrete values live in specs, presets, policies, or adapters.
4. Logical terminals differ from physical accesses.
5. Pure compilers/planners do not mutate layout.
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
16. Major architecture changes require an ADR.
17. Live state stays here; physical evidence stays in `VALIDATION_STATUS.md`.

## Known debt

```text
legacy MOS placement lacks PlacementResult
metal supply access for generated transmission gates is unresolved
committed routes are not typed resources
routing is two-terminal and same-layer only
GF180 width/layer/via rules lack a resolver
via planning and execution are absent
multi-terminal CDAC topology planning is absent
independent schematic LVS has not passed
stable logical identity is not preserved through extraction end-to-end
```
