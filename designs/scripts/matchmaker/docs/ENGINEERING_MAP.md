# MatchMaker Engineering Map

This is the canonical live-state document for the engine. Read it before changing code. Update it instead of creating another handoff file. Detailed physical evidence belongs in `VALIDATION_STATUS.md`; durable architectural decisions belong in ADRs.

## Current state

```text
base: main
branch: feature/cdac-layout-foundation
PR: #5
PR #1-#4: merged
CI: passing at the latest code head before this documentation update
merge scope: validated CDAC layout foundation plus an explicitly unresolved B0 selector prototype
```

PR #5 must not claim a completed selector or completed CDAC. The validated merge boundary is:

```text
typed CDAC specifications and manifest
parameterized capacitor placement
generated GF180 MIM array with zero DRC violations
generated base transmission gate with DRC, extraction, and exact connectivity
selector hierarchy, planner, failure history, and reproducible failing checkpoint
```

Scaled selectors, complete CDAC placement, CDAC routing, supplies, and LVS belong after PR #5.

## Source of truth

The generator never parses Xschem to decide layout.

```text
typed generator specification
-> CircuitManifest
-> placement and routing generation
-> generated layout/netlist
-> independent schematic comparison during LVS
```

Schematics under `designs/libs/core_matchmaker/` are independent LVS references only. They are not hierarchy, sizing, placement, coordinate, access, or routing input.

## Non-negotiable invariants

1. Concrete values live only in typed specs, named presets, explicit policies, or PDK/device adapters.
2. Algorithms do not hide bit counts, bank sizes, coordinates, primitive dimensions, port names, layers, widths, or spacing rules.
3. Primitive port grammar is interpreted once in the matching adapter.
4. Runtime geometry supplies centers, orientations, layers, widths, and envelopes.
5. New placement returns stable `PlacementResult` bindings.
6. Routing consumes typed `PhysicalDesignSnapshot` state and emits ordinary `RoutePlan` objects.
7. Executors draw plans; they do not invent policy.
8. Examples contain no reusable policy.
9. DRC never proves connectivity or analog quality.
10. Connectivity-changing work requires extraction or LVS evidence.
11. Unsupported cases fail explicitly.
12. Live state stays in this file; physical output stays in `VALIDATION_STATUS.md`.

## Canonical pipeline

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

Each module owns one translation.

## CDAC reference encoded by the generator

The reviewed GF180 preset is a parameterized instance of the generic banked-CDAC model:

```text
MIM unit: 5 µm x 5 µm request
B0: 1 unit,  NMOS 4 µm,  PMOS 8 µm
B1: 2 units, NMOS 8 µm,  PMOS 16 µm
B2: 4 units, NMOS 16 µm, PMOS 32 µm
B3: 8 units, NMOS 32 µm, PMOS 64 µm
termination: 1 unit
reset TG: NMOS 4 µm, PMOS 8 µm
MOS length: 0.28 µm
```

The specification and manifest compilers are tested with 3-, 4-, and 5-bit configurations so fixed four-bit assumptions cannot hide in algorithms.

## Code ownership map

```text
design/circuit_manifest.py
  CircuitInstance, CircuitNet, CircuitManifest

design/cdac_manifest_compiler.py
  compile_banked_cdac_manifest

design/transmission_gate_naming.py
  stable NMOS/PMOS logical names

design/reference_selector_naming.py
  stable child and net names

specs/
  MosDeviceSpec
  MimCapacitorSpec
  TransmissionGateSpec
  ReferenceSelectorSpec
  CdacBankSpec
  BankedCdacSpec
  generic scaled-binary compiler
  reviewed GF180 4-bit preset

placement/core/
  Tile, PlacementPlan, PlacedReferenceBinding, PlacementResult

placement/cdac/capacitor_array_*.py
  algorithmic inversion-symmetric array planning and generation

placement/cdac/transmission_gate_*.py
  runtime-derived NMOS/PMOS placement

placement/cdac/reference_selector_*.py
  side-by-side placement of two generated TG children

primitives/
  GF180 MIM and MOS factory adapters

physical/cdac_capacitor_snapshot.py
  canonical MIM top/bottom access filtering

physical/gf180_mos_access.py
  canonical gate/source/drain/bulk access filtering

physical/transmission_gate_snapshot.py
  NMOS/PMOS child snapshot

physical/reference_selector_snapshot.py
  generated-TG child snapshot

routing/planners/transmission_gate_topology_planner.py
  two parallel signal-net RoutePlans

routing/planners/reference_selector_topology_planner.py
  COMMON, SELECT, SELECT_BAR RoutePlans

generators/transmission_gate_generator.py
  end-to-end TG generation

generators/reference_selector_generator.py
  hierarchical selector generation

verification/netlist/shared_net_multiplicity.py
  exact participant-multiset and shared-net-count assertions
```

## Physically validated tonight

### GF180 MIM adapter and capacitor array

Observed primitive contract:

```text
requested unit: 5 µm x 5 µm
actual primitive bbox: 6.2 µm x 6.2 µm
raw ports: 264
canonical ports: 8
  top_met_{N,E,S,W} -> top
  bottom_met_{N,E,S,W} -> bottom
```

The other 256 nested implementation ports are excluded. The generated reviewed array is:

```text
grid: 4 x 4
counts: B0=1, B1=2, B2=4, B3=8, TERM=1
instances: 16
canonical accesses: 128
obstacles: 16
Magic DRC violations: 0
```

Capacitor plates are not routed yet.

### GF180 MOS adapter and base transmission gate

Observed base/reset device contract:

```text
NMOS W=4 µm, L=0.28 µm
  raw ports: 2672
  canonical ports: 16

PMOS W=8 µm, L=0.28 µm
  raw ports: 1392
  canonical ports: 16
```

Simple `gate/source/drain` cardinal accesses share one runtime metal layer. One runtime-derived PMOS translation aligns the source and drain signal nets.

Generated TG result:

```text
instances: 2
canonical accesses: 32
input RoutePlan: NMOS source -> PMOS source
output RoutePlan: NMOS drain -> PMOS drain
Magic DRC violations: 0
Magic extraction: passed
exact shared signal nets: 2
pre-LVS checks: passed
```

This closes the base/reset TG as a validated pre-LVS generator primitive.

`well_*` ports are well-definition boundaries, not accepted VDD/VSS metal accesses. Supply semantics remain unresolved rather than guessed.

## B0 reference-selector work and failure history

The selector is hierarchical: two generated base TG cells are placed side-by-side. Selector code does not duplicate MOS geometry.

Logical topology:

```text
VREF_TG input -> VREF
VSS_TG input  -> VSS
VREF_TG output + VSS_TG output -> COMMON
VREF_TG control + VSS_TG control_bar -> SELECT
VREF_TG control_bar + VSS_TG control -> SELECT_BAR
```

Three ordinary `RoutePlan` objects are emitted and mechanically executed.

### Attempt 1: internal vertical escapes

Used `control_N/S` and `control_bar_N/S`, then escaped vertically through child interiors.

```text
Magic DRC: failed
violations: 6
```

Lesson: a valid cardinal access is not automatically safe in its nominal orientation once embedded hierarchically.

### Attempt 2: north perimeter plus folded central corridor

```text
COMMON: direct inner output strap
SELECT: north perimeter
SELECT_BAR: two close central vertical legs plus a short south U-turn
Magic DRC violations: 0
Magic extraction: passed
exact shared selector nets: 3
pre-LVS checks: passed
```

This was electrically valid but rejected as final analog geometry because the fold added local coupling, unnecessary length, asymmetry, and fragility.

### Attempt 3: opposite north/south perimeter controls

```text
COMMON: direct inner output strap
SELECT: control_W -> north perimeter -> control_bar_E
SELECT_BAR: control_bar_W -> south perimeter -> control_E

SELECT length: 116.445, bends: 4
SELECT_BAR length: 128.635, bends: 4
Magic DRC violations: 0
Magic extraction: passed
shared selector net count: 1
connectivity: failed
pre-LVS checks: failed
```

Only one shared child-level net was extracted, consistent with `COMMON`; the two control nets were not recognized as shared selector nets.

The likely cause is access direction relative to the internal TG device placement, not the perimeter channel itself. With `nmos_side="left"` in each TG:

```text
NMOS control outer access: W
PMOS control_bar outer access: E
```

Therefore:

```text
VREF control_W and VSS control_bar_E are safe outer accesses for SELECT.
VREF control_bar_E and VSS control_W are the electrically proven accesses for SELECT_BAR,
but both face the inter-child gap rather than the outer selector perimeter.
```

Attempt 3 instead used `VREF control_bar_W` and `VSS control_E`; those directions point through each TG interior. DRC remained clean, but child-level extraction did not recognize the intended shared control nets.

This diagnosis must be verified from the extracted netlist before changing code.

## Exact next-session task

Create a fresh branch from merged `main`, suggested name:

```text
feature/cdac-selector-connectivity
```

Do not begin scaled selectors or complete CDAC assembly first.

Recovery sequence:

1. Reproduce Attempt 3 and inspect the extracted selector netlist and connectivity report.
2. Compare the child subcircuit pin participation of Attempt 2 and Attempt 3.
3. Verify which `control/control_bar` W/E accesses are true extractable child pins after hierarchy placement.
4. Preserve the clean north-perimeter `SELECT` path.
5. Replace the folded `SELECT_BAR` path with a single-trunk central-gap topology using the proven inner-gap accesses:

```text
VREF control_bar_E
-> horizontal branch to one derived central x
-> one vertical trunk
-> horizontal branch to VSS control_W
```

This removes the U-turn and close parallel legs while retaining the access pair that previously extracted correctly. A branch port may be placed on the central trunk. Use ordinary RoutePlan segments; do not add a specialized executor.
6. Require DRC=0, extraction passed, exact shared selector net count=3, and visual acceptance.
7. Only then validate B1/B2/B3 scaled selectors.

## Merge posture for PR #5

PR #5 is suitable to merge as a foundation when all of the following are true:

```text
CI passes
ENGINEERING_MAP.md reflects the unresolved selector boundary
VALIDATION_STATUS.md records all three selector attempts
PR description does not claim selector completion
PR remains explicit that full CDAC placement/routing and LVS are not complete
```

The selector prototype stays in the branch because it provides the hierarchy, typed contracts, pure tests, reproducible failure, and the correct starting point for the next branch. It is not a validated reusable selector primitive yet.

## Work after selector closure

```text
1. validate B1/B2/B3 selector widths through the same generator
2. define complete CDAC macro placement intent
3. place capacitor array, four selectors, and reset TG
4. run whole-placement Magic DRC
5. add committed routes as typed physical resources
6. add VOUT, B0, and reset topology planning
7. extend to remaining bank/reference/control/supply nets
8. add GF180 layer/width/via resolution as required
9. run extraction, exact connectivity, and independent Netgen LVS
```

## Known debt

```text
metal VDD/VSS access for generated TGs is unresolved
reference-selector control connectivity is unresolved
legacy MOS placement lacks PlacementResult
committed routes are not typed resources
routing is primarily two-terminal and same-layer
GF180 width/layer/via rules lack a resolver
via planning and execution are absent
multi-terminal CDAC topology planning is absent
independent schematic LVS has not passed
stable logical identity is not preserved through extraction end-to-end
```