# MatchMaker Engineering Map

This is the canonical live-state document. Read it before changing the engine. Update it instead of creating another handoff. Detailed `/foss` output belongs in `VALIDATION_STATUS.md`; durable decisions belong in ADRs.

## State

```text
base: main
branch: feature/cdac-layout-foundation
PR: #5, draft
PR #1-#4: merged
CI: passing
active checkpoint: generated B0 reference selector
```

Physically validated on PR #5:

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
  2 ordinary RoutePlans
  Magic DRC: zero violations
  Magic extraction: passed
  exact shared signal nets: 2
```

The next gate is the generated B0 selector: DRC, extraction, and exactly three shared nets between its two transmission-gate children.

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

Reusable algorithms must not hide fixed bit counts, bank sizes, device dimensions, coordinates, primitive port names, layer numbers, spacing rules, or selector sizes.

Concrete values may live only in:

```text
typed device/circuit specification
named reviewed preset
explicit placement/routing policy
PDK or device-access adapter
```

Primitive grammar belongs only in its adapter. Coordinates, layers, widths, orientations, and envelopes come from runtime geometry or a PDK rule adapter. Tests must vary configuration.

## Golden pipeline

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
design/
  circuit_manifest.py
    CircuitInstance, CircuitNet, CircuitManifest
  cdac_manifest_compiler.py
    CdacNamingPolicy, compile_banked_cdac_manifest
  transmission_gate_naming.py
    NMOS_INSTANCE_NAME, PMOS_INSTANCE_NAME
  reference_selector_naming.py
    stable child and logical net names

specs/
  MosDeviceSpec
  MimCapacitorSpec
  TransmissionGateSpec
  ReferenceSelectorSpec
  CdacBankSpec
  BankedCdacSpec
  make_scaled_binary_banked_cdac_spec
  make_gf180_4bit_banked_cdac_reference_spec

placement/core/
  Tile, PlacementPlan
  PlacedReferenceBinding, PlacementResult

placement/cdac/
  capacitor_array_intent.py
  capacitor_array_plan_compiler.py
  capacitor_array_builder.py
  transmission_gate_intent.py
  transmission_gate_builder.py
  reference_selector_intent.py
  reference_selector_builder.py

physical/
  models.py
    TerminalRef, AccessPoint, PlacedInstance
    RoutingObstacle, PhysicalDesignSnapshot
  cdac_capacitor_snapshot.py
  gf180_mos_access.py
  transmission_gate_snapshot.py
  transmission_gate_cell_access.py
  reference_selector_snapshot.py

routing/planners/
  transmission_gate_topology_planner.py
  reference_selector_topology_planner.py

routing/plans/
  RoutePlan, RouteSegment, ViaPlan, RouteMetrics

routing/routers/
  route_plan_executor.py

generators/
  transmission_gate_generator.py
  transmission_gate_public_ports.py
  reference_selector_generator.py

verification/netlist/
  shared_net_multiplicity.py
```

`CircuitManifest` is compiled from typed specs without consulting a schematic. New device-family placement returns stable `PlacementResult` bindings. `PhysicalDesignSnapshot.access_points_for(...)` is the supported logical-to-physical bridge.

## Existing routing foundation

```text
NetIntent + PhysicalDesignSnapshot
-> straight / Manhattan / external-dogleg candidates
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

## CDAC capacitor foundation

The reviewed preset resolves to 15 switched unit capacitors, one termination unit, four shared selectors, one reset transmission gate, and 18 MOS devices. Generic algorithms assume none of those fixed counts.

Observed MIM contract:

```text
requested unit: 5 µm x 5 µm
actual bbox: 6.2 µm x 6.2 µm
raw ports: 264
canonical external ports: 8

top_met_{N,E,S,W} -> top
bottom_met_{N,E,S,W} -> bottom
```

Validated array:

```text
grid: 4 x 4
counts: B0=1, B1=2, B2=4, B3=8, TERM=1
instances: 16
accesses: 128
obstacles: 16
Magic DRC: zero violations
```

No capacitor plate is routed yet.

## Transmission-gate generator

### Runtime primitive contract

```text
gate_{N,E,S,W}
source_{N,E,S,W}
drain_{N,E,S,W}
well_{N,E,S,W} -> physical well boundary only
```

Signal ports are on one common runtime metal layer. NMOS and PMOS source/drain offsets differ by the same amount, so the builder derives one PMOS translation that aligns both parallel nets.

`well_*` is not a metal `VDD`/`VSS` access. Supply assignment remains blocked until a real tie/substrate-tap metal contract is observed.

### Translation

```text
TransmissionGateLayoutIntent
-> build_transmission_gate_device_placement
   bbox-derived separation
   port-derived vertical alignment
   stable NMOS/PMOS bindings
-> create_transmission_gate_device_snapshot
-> plan_transmission_gate_signal_topology
   source parallel net
   drain parallel net
-> execute ordinary RoutePlans
-> expose input/output/control/control_bar ports
```

Validated result:

```text
bbox: (-16.48, -11.565) to (11.49, 10.065)
instances: 2
accesses: 32
input:  source_E -> source_W
output: drain_E -> drain_W
route length: 13.345 each
route width: 0.5
Magic DRC: zero violations
Magic extraction: passed
exact shared signal nets: 2
```

This closes the base/reset TG at the pre-LVS level. The same generator must be reused for scaled B1/B2/B3 widths.

## Reference-selector generator

### Architecture

The selector is generated from two already-generated transmission-gate children. MOS geometry is never duplicated.

```text
ReferenceSelectorLayoutIntent
-> generate VREF child TG
-> generate VSS child TG
-> side-by-side placement from runtime child bboxes
-> reference-selector child PhysicalDesignSnapshot
-> three ordinary RoutePlans
   COMMON: direct inner output connection
   SELECT: north control channel
   SELECT_BAR: south control channel
-> mechanical execution
-> derived public VREF/VSS/common/select ports
```

The side-by-side topology is intentional. A stacked arrangement would geometrically cross the complementary control nets on one routing layer.

Control mapping:

```text
VREF TG NMOS gate  <- SELECT
VREF TG PMOS gate  <- SELECT_BAR
VSS TG NMOS gate   <- SELECT_BAR
VSS TG PMOS gate   <- SELECT
```

The child gap, north/south channel coordinates, route layers, widths, and public-port locations are derived from typed policy, child bboxes, and runtime ports. No selector coordinate or metal layer is hard-coded.

### Active `/foss` checkpoint

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

The exact three shared nets must connect the VREF and VSS TG child subcircuits and correspond to `COMMON`, `SELECT`, and `SELECT_BAR`. Any missing or additional shared net fails.

## Next development order

```text
1. physically validate the B0 reference selector
2. repair selector policy only from observed geometry if needed
3. generate and validate B1/B2/B3 scaled selectors with the same code path
4. resolve metal bulk/tie access without treating well geometry as supply metal
5. place four selectors and one reset TG beside the capacitor array
6. generate the complete unrouted CDAC placement and run Magic DRC
7. add committed routes as typed physical resources
8. add VOUT, B0, and reset topology planning
9. extend to remaining bank/reference/control/supply nets
10. run extraction, exact connectivity checks, and independent Netgen LVS
```

## Device-specific extension model

```text
MOS adapter -> gate/source/drain/bulk
capacitor adapter -> top/bottom
transmission-gate adapter -> input/output/control/control_bar/supplies
reference-selector adapter -> references/common/control/supplies
CDAC adapter -> banks/selectors/reset/public nets
```

Specialized planners consume common intent/snapshot contracts and emit common `RoutePlan` types. Specialized geometry executors are prohibited.

## Invariants

1. Typed intent is independent of schematics.
2. Schematics are LVS references only.
3. Concrete values live in specs, presets, policies, or adapters.
4. Logical terminals differ from physical accesses.
5. Pure compilers and planners do not mutate layout.
6. Builders execute plans; they do not invent hierarchy or connectivity.
7. Adapters interpret primitive APIs once and copy runtime values.
8. Executors do not invent routing policy.
9. Examples contain no reusable engine logic.
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
metal supply access for generated MOS cells is unresolved
committed routes are not typed resources
routing is two-terminal and same-layer only outside specialized templates
GF180 width/layer/via rules lack a resolver
via planning and execution are absent
full multi-terminal CDAC topology planning is absent
independent schematic LVS has not passed
stable logical identity is not preserved through extraction end-to-end
```
