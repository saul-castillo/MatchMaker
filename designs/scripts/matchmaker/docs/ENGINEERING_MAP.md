# MatchMaker Engineering Map

This is the canonical live-state document. Read it before changing the engine. Update it instead of creating another handoff. Detailed `/foss` output belongs in `VALIDATION_STATUS.md`; durable decisions belong in ADRs.

## State

```text
base: main
branch: feature/cdac-layout-foundation
PR: #5, draft
PR #1-#4: merged
CI: passing
active checkpoint: parameterized transmission-gate generator
```

The 4 by 4 GF180 MIM capacitor array is now generated with 16 stable instances, 128 canonical accesses, 16 obstacles, and zero Magic DRC violations.

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
-> PhysicalDesignSnapshot
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

specs/
  MosDeviceSpec, MimCapacitorSpec, TransmissionGateSpec
  ReferenceSelectorSpec, CdacBankSpec, BankedCdacSpec
  make_scaled_binary_banked_cdac_spec
  make_gf180_4bit_banked_cdac_reference_spec

placement/core/
  Tile, PlacementPlan, PlacedReferenceBinding, PlacementResult

placement/cdac/
  CdacCapacitorArrayIntent
  compile_cdac_capacitor_array_plan
  build_cdac_capacitor_array

physical/models.py
  TerminalRef, AccessPoint, PlacedInstance
  RoutingObstacle, PhysicalDesignSnapshot

physical/cdac_capacitor_snapshot.py
  Gf180MimExternalAccessPolicy
  classify_gf180_mim_external_port_name
  create_cdac_capacitor_array_physical_design_snapshot

routing/
  NetIntent, RouteCandidate, RoutePlan
  straight / Manhattan / dogleg strategies
  mechanical RoutePlan executor
```

`CircuitManifest` is compiled from typed specs without consulting a schematic. New device-family placement returns stable `PlacementResult` bindings. `PhysicalDesignSnapshot.access_points_for(...)` is the supported logical-to-physical bridge.

## Validated evidence

Detailed commands and results are in `VALIDATION_STATUS.md`.

MOS routing:

```text
A0.gate -> A1.gate blocked dogleg
A0.gate -> A2.gate Manhattan Z route
Magic DRC: zero violations
Magic extraction: passed
exact connectivity: passed
```

Installed GF180 MIM primitive:

```text
requested unit: 5 µm x 5 µm
bbox: 6.2 µm x 6.2 µm
raw ports: 264
canonical ports: 8
nested ports ignored: 256

top_met_{N,E,S,W} -> top
bottom_met_{N,E,S,W} -> bottom
```

Observed top and bottom layer/width values are evidence only; adapters read them at runtime.

CDAC capacitor array:

```text
grid: 4 x 4
counts: B0=1, B1=2, B2=4, B3=8, TERM=1
instances: 16
access points: 128
obstacles: 16
Magic DRC: zero violations
```

No capacitor plate is routed yet. There is no CDAC extraction or LVS claim.

## PR #5 completed

```text
parameterized MIM/TG/selector/bank/CDAC specs
named GF180 reviewed preset
schematic-independent CircuitManifest
3/4/5-bit tests
generic PlacementResult
algorithmic grid inference and inversion symmetry
compatible B0/termination residual pairing
GF180 MIM wrapper and diagnostic
capacitor-array geometry builder
canonical capacitor access adapter
capacitor PhysicalDesignSnapshot
GDS and zero-violation Magic DRC
```

## Active transmission-gate checkpoint

Current command:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_transmission_gate_devices.py
```

Sequence:

```text
1. inspect installed NMOS/PMOS signatures and canonical ports
2. define explicit transmission-gate placement policy
3. place NMOS and PMOS with stable bindings
4. select parallel source/drain accesses from runtime ports
5. expose input/output/control/control_bar/supplies
6. generate base reset/B0 transmission gate
7. run Magic DRC
8. prove extracted input/output connectivity
9. reuse the builder for B1/B2/B3 widths
10. build the two-TG reference selector
```

Do not guess MOS access names, layers, or envelopes before reviewing the diagnostic.

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
committed routes are not typed resources
routing is two-terminal and same-layer only
GF180 width/layer/via rules lack a resolver
via planning and execution are absent
multi-terminal CDAC topology planning is absent
independent schematic LVS has not passed
stable logical identity is not preserved through extraction end-to-end
```
