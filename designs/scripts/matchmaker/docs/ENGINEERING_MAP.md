# MatchMaker Engineering Map

This is the canonical live-state document. Read it before changing the engine. Update it instead of creating another handoff. Detailed `/foss` output belongs in `VALIDATION_STATUS.md`; durable decisions belong in ADRs.

## State

```text
base: main
branch: feature/cdac-layout-foundation
PR: #5, draft
PR #1-#4: merged
active checkpoint: generated base transmission gate
```

The capacitor foundation is physically validated: 16 stable MIM instances, 128 canonical accesses, 16 obstacles, and zero Magic DRC violations. The installed base NMOS/PMOS primitives have been inspected. The next gate is generated transmission-gate GDS and DRC.

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

Primitive name grammar belongs only in the matching adapter. Layer, width, center, and orientation are copied from runtime ports or resolved by a PDK rule adapter. Tests must vary configuration.

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

Observed layer and width values are validation evidence only. The capacitor adapter reads them from runtime ports.

## Transmission-gate architecture

### Observed primitive facts

The typed base/reset switch uses NMOS W=4 µm and PMOS W=8 µm at L=0.28 µm. The installed primitives expose thousands of nested ports but only 16 simple canonical ports per device:

```text
gate_{N,E,S,W}
source_{N,E,S,W}
drain_{N,E,S,W}
well_{N,E,S,W} -> physical bulk boundary
```

Signal accesses are observed on one common runtime metal layer. NMOS and PMOS source/drain vertical offsets differ by the same amount, allowing one derived PMOS translation to align both nets. The generator does not copy those coordinates or layers into policy.

`well_*` ports are not accepted as `VDD` or `VSS` metal ports. Supply assignment waits for inspection of simple unclassified tie/substrate-tap exports.

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

No specialized geometry executor is allowed. Supply semantics are intentionally absent until the primitive tie contract is observed.

### Immediate `/foss` checkpoint

```bash
git pull --ff-only
source scripts/matchmaker/env/setup.sh
python scripts/matchmaker/examples/diagnostics/inspect_gf180_transmission_gate_devices.py
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
```

The diagnostic now prints simple unclassified ports separately. The generator command must report two physical instances, runtime access counts, two parallel signal RoutePlans, public input/output/control ports, a GDS path, and a Magic DRC result.

Do not claim transmission-gate connectivity yet. If DRC passes, add extraction evidence that exactly two distinct shared nets connect the NMOS and PMOS before treating the cell as electrically validated.

## Next development order

```text
1. inspect simple unclassified MOS tie/substrate-tap ports
2. run generated base transmission-gate GDS and Magic DRC
3. repair placement/routing policy only from observed geometry if needed
4. add exact two-shared-net extraction assertion
5. assign typed VDD/VSS access after tie-port evidence
6. validate base/reset transmission gate
7. reuse the same generator for B1/B2/B3 widths
8. build the two-transmission-gate reference selector
9. place four selectors and reset beside the capacitor array
10. generate complete unrouted CDAC and run Magic DRC
11. add committed-route resources and GF180 rule resolution
12. route VOUT, B0, and reset, then prove extraction
13. route remaining banks/references/controls/supplies
14. run independent schematic-to-layout Netgen LVS
```

## Package ownership

```text
design/          logical hierarchy, connectivity, stable naming
specs/           typed device and circuit-family specifications
placement/core/  generic plans, policies, results, stable bindings
placement/mos/   MOS-array-specific placement
placement/cdac/  capacitor and switch placement policy
physical/        physical snapshots and device access adapters
primitives/      PDK/gLayout primitive construction only
routing/intents/ logical net and route-group requests
routing/planners pure routing and topology planning
routing/plans/   common execution-ready IR
routing/routers/ mechanical geometry execution
generators/      pipeline orchestration only
verification/    DRC, extraction, connectivity, LVS, parsing
outputs/         artifact conventions
examples/        wiring and diagnostics only
```

## Invariants

1. Typed intent is independent of schematics.
2. Schematics are LVS references only.
3. Concrete values live in specs, presets, policies, or adapters.
4. Logical terminals differ from physical accesses.
5. Pure compilers and planners do not mutate layout.
6. Builders execute placement policy; they do not invent hierarchy.
7. Device adapters interpret primitive APIs once and copy runtime values.
8. Executors do not invent routing policy.
9. Generators orchestrate existing stages; they do not hide reusable policy.
10. Examples contain no reusable policy.
11. New placement returns stable bindings.
12. New routing consumes `PhysicalDesignSnapshot`.
13. Hard constraints reject before ranking.
14. Unsupported cases fail explicitly.
15. DRC never proves connectivity.
16. Connectivity-changing work requires extraction or LVS.
17. Major architecture changes require an ADR.
18. Live state stays here; physical evidence stays in `VALIDATION_STATUS.md`.

## Known debt

```text
legacy MOS placement lacks PlacementResult
committed routes are not typed resources
routing is two-terminal and same-layer only outside specialized topology planners
GF180 width/layer/via rules lack a resolver
via planning and execution are absent
multi-terminal CDAC topology planning is absent
transmission-gate supply access is unresolved
independent schematic LVS has not passed
stable logical identity is not preserved through extraction end-to-end
```
