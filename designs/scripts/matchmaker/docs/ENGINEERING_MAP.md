# MatchMaker Engineering Map

This is the canonical live-state document for the engine. Read it before changing
code. Update it instead of creating another handoff file. Detailed physical
evidence belongs in `VALIDATION_STATUS.md`; durable architectural decisions
belong in ADRs.

## Current state

```text
base: main
branch: main (direct-update workflow)
PR: none
PR #1-#5: merged
remote base before this recovery: ff61776 family-composable selector architecture
recovered change: explicit compact GF180 MOS profile and strict profile rejection
regression evidence: lost workspace reported 100 tests; recovered source syntax checked
physical status: compact-profile /foss rerun still required
active checkpoint: regenerate the vertical B0 selector without inherited substrate geometry
```

The original local commit `b7d80a6` never reached GitHub. ADR 0005 records the
reconstructed equivalent. The SHA differs, but the architectural boundary is the
same: generated transmission-gate MOS children retain conductive body ties and
explicitly disable substrate taps, deep wells, guard rings, and dummies.

The last physically accepted selector remains the three-net B0 checkpoint. No
five-net selector, scaled selector, complete CDAC placement, full extraction, or
independent LVS claim is made yet.

## Source of truth

The generator never parses Xschem to decide layout.

```text
typed generator specification
-> CircuitManifest
-> placement and routing generation
-> generated layout/netlist
-> independent schematic comparison during LVS
```

Schematics under `designs/libs/core_matchmaker/` are independent LVS references
only. They are not hierarchy, sizing, placement, coordinate, access, or routing
input.

## Non-negotiable invariants

1. Concrete values live only in typed specs, named presets, explicit policies, or
   PDK/device adapters.
2. Algorithms do not hide bit counts, bank sizes, coordinates, primitive
   dimensions, port names, layers, widths, or spacing rules.
3. Primitive port grammar is interpreted once in the matching family adapter.
4. Runtime geometry supplies centers, orientations, layers, widths, and
   envelopes.
5. New placement returns stable `PlacementResult` bindings.
6. Routing consumes typed `PhysicalDesignSnapshot` state and emits ordinary
   `RoutePlan` objects.
7. Executors draw plans; they do not invent policy.
8. Examples contain no reusable policy.
9. DRC never proves connectivity or analog quality.
10. Connectivity-changing work requires extraction or LVS evidence.
11. Unsupported cases fail explicitly.
12. Live state stays in this file; physical evidence stays in
    `VALIDATION_STATUS.md`.
13. Device-family port grammar stays in family adapters; composition and route
    templates cannot inspect family-specific names.
14. A block planner binds logical roles to reusable placement/routing primitives;
    it does not become a private geometry generator.
15. Safety-critical primitive options are explicit. `None` is not accepted when
    it would inherit geometry-affecting gLayout defaults.
16. A generated MOS profile is part of the physical interface because it changes
    the primitive envelope, available escapes, and possible substrate shorts.

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

## Reviewed GF180 CDAC instance

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

The specification and manifest compilers are tested with 3-, 4-, and 5-bit
configurations so fixed four-bit assumptions cannot hide in algorithms.

## Architectural ownership map

```text
design/
  CircuitManifest and stable logical instance/net naming

specs/
  typed MOS, MIM, transmission-gate, selector, bank, and CDAC specifications

placement/core/
  Tile, PlacementPlan, PlacementResult, transformed reference envelopes,
  generic oriented-pair composition

placement/cdac/
  capacitor-array, transmission-gate, and selector intent/builder bindings

primitives/gf180_mos_primitive_options.py
  explicit compact MOS profile, profile validation, profile diagnostics

primitives/gf180_mos_primitive_factory.py
  installed-signature alias resolution and GF180 primitive invocation

physical/gf180_mos_access.py
  gate/source/drain and conductive body-tie port grammar

physical/transmission_gate_cell_access.py
  demonstrated terminal/direction capability contract for generated TG cells

physical/hierarchical_cell_snapshot.py
  family-agnostic generated-child snapshot construction

routing/planners/corridor_route_planner.py
  side bus, gap bridge, and transitioned multi-terminal trunk templates

routing/planners/reference_selector_topology_planner.py
  thin selector role binding and matching constraints

routing/routers/route_plan_executor.py
  mechanical segment and injected via execution

verification/netlist/
  exact shared-net participant checks and extracted child-interface diagnostics

docs/adr/
  durable architecture decisions; ADR 0005 owns compact MOS profile policy
```

Generic placement and corridor modules do not import selector net names, GF180
port tokens, or numeric layers.

## Demonstrated physical boundary

### Capacitor array

```text
requested MIM unit: 5 µm x 5 µm
actual primitive bbox: 6.2 µm x 6.2 µm
reviewed array: 4 x 4, 16 instances
Magic DRC violations: 0
```

Capacitor plates are not routed.

### Base transmission gate before compact-profile recovery

```text
NMOS: W=4 µm, L=0.28 µm
PMOS: W=8 µm, L=0.28 µm
signal layer: runtime met2 (36, 0)
conductive body ties: four cardinal exports per device
Magic DRC violations: 0
Magic extraction: passed
exact shared signal nets: 2
pre-LVS checks: passed
```

This evidence established the signal topology and measured body-tie access
contract. It did not prove that inherited outer geometry was safe for composite
supply escapes.

### Accepted B0 selector boundary

The accepted pre-LVS selector checkpoint contains two generated TG children and
exactly three shared nets:

```text
COMMON
SELECT
SELECT_BAR
```

Attempt 4 used a direct COMMON route, a clean outer SELECT route, and a single
central SELECT_BAR trunk. It passed DRC, extraction, exact three-net
connectivity, and visual inspection. Supply routing and independent LVS were not
part of that accepted run.

## Family-composable selector architecture

ADR 0004 separates four reusable boundaries:

```text
family adapter
  logical terminals <-> family port grammar

oriented-pair composer
  two generated children + axis/side/orientation/gap
  -> runtime-envelope PlacementResult

corridor planners
  side bus / gap bridge / transitioned trunk
  -> ordinary RoutePlan objects

block binding
  selector logical roles and matching constraints only
```

The active B0 topology uses a vertical `VREF_TG=R0` / `VSS_TG=R180` pair:

```text
COMMON: west met2 escapes -> two vias -> compact met3 trunk
SELECT: west met2 side bus
SELECT_BAR: matched east met2 side bus
VSS: body ties plus low-reference input -> three vias -> east met3 trunk
VDD: direct met2 bridge in the true inter-child gap
```

## Attempt 7 root cause and recovery

The first `/foss` run of the vertical family-composable selector was DRC-clean
and extracted, but only four shared child nets remained. Child-interface
inspection showed that VDD was not merely absent: PMOS `vdd_*` merged into
`VSUBS`.

The PMOS supply escape crossed an inherited outer substrate ring. The former
profile requested `with_tie=True` but left other geometry-affecting options as
`None`, allowing installed gLayout defaults to add expansive geometry.

ADR 0005 therefore requires this exact generated-TG leaf profile:

```text
conductive body ties: on
substrate taps: off
deep wells: off
guard rings: off
dummies: off on both sides
```

`TransmissionGateLayoutIntent` rejects both inherited and conflicting profiles
before geometry generation. The MOS diagnostic prints the selected profile and a
normalized bounding-box size so envelope changes are visible.

This is an architecture correction, not a physical acceptance claim.

## Exact next verification gate

Run in `/foss`:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_transmission_gate_devices.py
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
python scripts/matchmaker/examples/placement/generate_gf180_reference_selector.py
```

Require:

```text
profile: ties on; substrate taps, deep wells, guard rings, dummies off
base TG: zero DRC violations, extraction passed, exact two signal nets
selector placement: compact vertical R0/R180 pair
SELECT and SELECT_BAR: matched two-bend side buses, zero vias
COMMON: two west-side transitions
VSS: three east/gap-side transitions
VDD: direct bridge confined to the inter-child gap
selector: zero DRC violations, extraction passed, exactly five shared child nets
child-interface report: VDD distinct from VSUBS
visual inspection: no inherited outer ring crossing or full-perimeter loops
```

After this passes, export independent schematic SPICE references and run Netgen
LVS on the base TG and B0 selector before scaling B1/B2/B3.

## Work after selector closure

```text
1. pass base-TG and B0 selector Netgen LVS
2. validate B1/B2/B3 through the same generator and LVS flow
3. define complete CDAC macro placement intent
4. place capacitor array, four selectors, and reset TG
5. run whole-placement Magic DRC
6. add committed routes as typed physical resources
7. plan VOUT, bank, reset, reference, control, supply, and bulk nets
8. run full-CDAC extraction, exact connectivity, and independent Netgen LVS
```

## Known debt

```text
compact-profile base TG and vertical five-net B0 require /foss rerun
scaled B1/B2/B3 selectors are not validated
legacy MOS placement has not been generalized beyond the current TG builder
generic transitioned-tree planning has no obstacle-aware candidate search
GF180 transition execution currently covers centered met2/met3 via stacks
composite external-pin escape planning is not generalized
multi-terminal complete-CDAC topology planning is absent
committed routes are not yet typed physical resources
independent schematic LVS has not passed
stable logical identity is not preserved through extraction end-to-end
```
