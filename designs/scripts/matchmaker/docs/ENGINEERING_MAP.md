# MatchMaker Engineering Map

This is the canonical live-state document for the engine. Read it before changing code. Update it instead of creating another handoff file. Detailed physical evidence belongs in `VALIDATION_STATUS.md`; durable architectural decisions belong in ADRs.

## Current state

```text
base: main
branch: main (direct-update workflow)
PR: none
PR #1-#5: merged
local checks: 76 pure-Python tests passing; source/examples compile
active checkpoint: via-free B0 VSS/VDD topology awaits /foss validation
```

PR #5 merged the following validated boundary:

```text
typed CDAC specifications and manifest
parameterized capacitor placement
generated GF180 MIM array with zero DRC violations
generated base transmission gate with DRC, extraction, and exact connectivity
selector hierarchy, planner, failure history, and reproducible failing checkpoint
```

The current `main` checkpoint closes the B0 selector control topology at the
pre-LVS boundary. Scaled selectors, complete CDAC placement, CDAC routing,
supplies, and independent LVS remain outside that demonstrated boundary.

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
  canonical gate/source/drain and conductive bulk-tie access filtering

physical/transmission_gate_snapshot.py
  NMOS/PMOS child snapshot

physical/reference_selector_snapshot.py
  generated-TG child snapshot

routing/planners/transmission_gate_topology_planner.py
  two parallel signal-net RoutePlans

routing/planners/reference_selector_topology_planner.py
  COMMON, SELECT, SELECT_BAR, VSS, VDD RoutePlans

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

The corrected conductive bulk-tie contract was measured in `/foss` on
2026-07-23:

```text
NMOS and PMOS terminal counts:
  gate=4, source=4, drain=4, bulk=4

tie_N_top_met_N and tie_S_top_met_S:
  layer: (36, 0)
  width: 3.16 µm

tie_E_top_met_E and tie_W_top_met_W:
  layer: (34, 0)
  NMOS width: 7.81 µm
  PMOS width: 11.81 µm
```

The four `well_*` boundaries remain unclassified geometry, not electrical
ports. The north/south body ties therefore share met2 `(36, 0)` with the TG
signal accesses and permit direct same-layer selector supply routing.

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
promoted ports: vss_{N,E,S,W}, vdd_{N,E,S,W}
```

This closes the base/reset TG as a validated pre-LVS generator primitive.

`well_*` ports are well-definition boundaries, not accepted VDD/VSS metal
accesses. The earlier 16-access diagnostic count came from a classifier that
still admitted those boundaries, so it is historical evidence for the generated
geometry only—not evidence of a routable bulk contract.

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

The pre-squash PR #5 history preserves the exact Attempt 2 route and confirms that
`VREF control_bar_E` and `VSS control_W` produced DRC-clean geometry and all three
expected extracted shared nets. The accepted central-trunk run now independently
confirms that this inner-gap pair extracts correctly. Because both the access pair
and route shape differ from Attempt 3, the result does not isolate access direction
as the sole cause of that attempt's failure.

## Validated B0 selector checkpoint

Implemented directly on `main` for this checkpoint:

- the clean north-perimeter `SELECT` route is unchanged;
- `SELECT_BAR` selects the electrically proven inner-gap accesses;
- the planner derives one trunk x-coordinate from the two runtime child bboxes;
- two horizontal branches and one vertical trunk replace the folded U-turn;
- the planner fails if the gap cannot contain the resolved route width or if the
  selected accesses do not face the trunk;
- `select_bar_S` is placed on the vertical trunk;
- focused pure-Python planner tests and source/example compilation pass.

The resulting `SELECT_BAR` topology is:

```text
VREF control_bar_E
-> horizontal branch to one derived central x
-> one vertical trunk
-> horizontal branch to VSS control_W
```

This removes the U-turn and close parallel legs while retaining the access pair
that previously extracted correctly. It still emits ordinary `RoutePlan`
segments and uses the existing mechanical executor.

Observed in the Chipathon `/foss` environment on 2026-07-22:

```text
SELECT_BAR accesses: VREF_TG__control_bar_E, VSS_TG__control_W
SELECT_BAR topology: two horizontal branches, one central vertical trunk
SELECT_BAR bends: 2
Magic DRC violations: 0
Magic extraction: passed
connectivity: passed
exact shared selector nets: 3
pre-LVS checks: passed
visual inspection: accepted
```

This closes the three-net control/signal topology as a reusable pre-LVS
checkpoint. That accepted run predates the current VDD/VSS routes, and no
independent schematic netlist has yet been compared with the extracted layout.

## Active B0 supply-routing checkpoint

The installed gLayout primitive source distinguishes conductive body ties from
well boundaries. MatchMaker models only the exact cardinal body-tie metal
exports:

```text
tie_N_top_met_N
tie_E_top_met_E
tie_S_top_met_S
tie_W_top_met_W
```

The base TG intent explicitly requests `with_tie=True`; its device snapshot
requires a bulk terminal and rejects `well_*` as routing access. The generator
promotes each NMOS tie as `vss_{N,E,S,W}` and each PMOS tie as
`vdd_{N,E,S,W}`. The `/foss` diagnostic and generation run confirm that this
contract preserves zero DRC violations, successful extraction, and the exact
two TG signal nets.

The selector snapshot now includes `vss` and `vdd` child terminals. The B0
planner uses the measured same-layer contract without vias:

```text
VSS:
  VREF_TG vss_N + VSS_TG vss_N + VSS_TG input_E
  north rail inside the existing SELECT perimeter
  right-side service channel to the low-reference input

VDD:
  VREF_TG vdd_S + VSS_TG vdd_S
  separate south rail below both child envelopes
```

Supply width is explicit policy when overridden. By default it derives from
the narrowest selected supply/signal access, which resolves to 0.5 µm for B0.
Lane coordinates derive from runtime child bboxes and the existing SELECT
channel. The planner fails if the north/right lane cannot contain the resolved
width or if the chosen ports do not face their channels. The generator now
expects five exact child-shared nets: `COMMON`, `SELECT`, `SELECT_BAR`, `VSS`,
and `VDD`.

This route topology is locally regression-tested but not yet physically
validated. It makes no LVS claim.

### Exact next verification gate

1. run the B0 selector generator in `/foss`;
2. require zero DRC violations, successful extraction, and exactly five shared
   child nets;
3. visually confirm that VSS remains inside the SELECT perimeter, VDD remains
   south of both children, and neither rail touches the control topology;
4. export independent schematic SPICE references for the base TG and B0 selector;
5. pass Magic extraction and Netgen LVS for both leaf blocks;
6. then validate B1/B2/B3 scaled selectors with the same DRC, extraction,
   connectivity, visual, and LVS gates.

## Work after selector closure

```text
1. close TG/selector supply and bulk topology and pass leaf-cell Netgen LVS
2. validate B1/B2/B3 selector widths through the same generator and LVS flow
3. define complete CDAC macro placement intent
4. place capacitor array, four selectors, and reset TG
5. run whole-placement Magic DRC
6. add committed routes as typed physical resources
7. add VOUT, B0, and reset topology planning
8. extend to remaining bank/reference/control/supply nets
9. add GF180 layer/width/via resolution as required
10. run full-CDAC extraction, exact connectivity, and independent Netgen LVS
```

## Known debt

```text
selector supply rails are implemented but not physically validated
legacy MOS placement lacks PlacementResult
committed routes are not typed resources
routing is primarily two-terminal and same-layer
GF180 width/layer/via rules lack a resolver
via planning and execution are absent
multi-terminal CDAC topology planning is absent
independent schematic LVS has not passed
stable logical identity is not preserved through extraction end-to-end
```
