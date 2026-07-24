# MatchMaker Engineering Map

This is the canonical live-state document for the engine. Read it before changing
code. Update it instead of creating another handoff file. Detailed physical
evidence belongs in `VALIDATION_STATUS.md`; durable decisions belong in ADRs.

## Current state

```text
base: main
branch: main (direct-update workflow)
PR: none
PR #1-#5: merged
latest accepted physical checkpoint: vertical B0 selector, five shared nets
latest accepted evidence date: 2026-07-24
active checkpoint: independent base-TG and B0 schematic-to-layout Netgen LVS
```

The compact MOS profile from ADR 0005 fixed the Attempt 7 VDD-to-`VSUBS` short.
The regenerated vertical selector is now accepted at the five-net pre-LVS
boundary:

```text
Magic DRC violations: 0
Magic extraction: passed
shared selector net count: 5
pre-LVS checks: passed
visual inspection: accepted
PMOS VDD child terminals: one shared net distinct from VSUBS
```

This is not a full LVS claim. Scaled selectors, complete CDAC placement/routing,
full extraction, and full-CDAC LVS remain outside the demonstrated boundary.

## Source of truth

The generator never parses Xschem to decide layout.

```text
typed generator specification
-> CircuitManifest
-> placement and routing generation
-> generated layout/netlist
-> independent schematic comparison during LVS
```

Schematics under `designs/libs/core_matchmaker/` are independent review and LVS
references. They are not hierarchy, sizing, placement, coordinate, access, or
routing input to MatchMaker.

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
10. Extraction and shared-net counts do not replace terminal-level inspection.
11. Pre-LVS checks do not replace independent schematic-to-layout LVS.
12. Unsupported cases fail explicitly.
13. Device-family port grammar stays in family adapters; composition and route
    templates cannot inspect family-specific names.
14. A block planner binds logical roles to reusable placement/routing primitives;
    it does not become a private geometry generator.
15. Safety-critical primitive options are explicit. `None` is not accepted when
    it would inherit geometry-affecting gLayout defaults.
16. Schematic and generated layout top-cell names are independent identities.
    The LVS boundary must bind them explicitly rather than rename either source.

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
-> independent Xschem reference netlist
-> Netgen LVS
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
  explicit compact MOS profile, validation, and diagnostics

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

verification/netlist/xschem_schematic_netlist.py
  headless independent-reference SPICE export from Xschem

verification/lvs/cdac_leaf_targets.py
  explicit reviewed schematic/layout top-cell binding for base TG and B0

verification/lvs/magic_netgen_lvs.py
  Magic extraction and Netgen comparison with distinct schematic/layout names

examples/verification/run_cdac_leaf_lvs.py
  orchestration only; no reusable device or geometry policy

docs/adr/
  durable decisions; ADR 0004 owns composition and ADR 0005 owns MOS profile
```

Generic placement and corridor modules do not import selector net names, GF180
port tokens, numeric layers, Xschem paths, or Netgen commands.

## Demonstrated physical boundary

### Capacitor array

```text
requested MIM unit: 5 µm x 5 µm
actual primitive bbox: 6.2 µm x 6.2 µm
reviewed array: 4 x 4, 16 instances
Magic DRC violations: 0
```

Capacitor plates are not routed.

### Base transmission gate

The pre-compact-profile run established the two signal nets and body-tie access
grammar:

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

The compact-profile base TG must be regenerated before its independent LVS run
unless a current `/foss` output confirms the same gates.

### B0 selector: accepted five-net checkpoint

The accepted structure is a vertical `VREF_TG=R0` / `VSS_TG=R180` pair:

```text
COMMON: west met2 escapes -> two vias -> compact met3 trunk
SELECT: west met2 side bus
SELECT_BAR: matched east met2 side bus
VSS: two body ties plus low-reference input -> three vias -> east met3 trunk
VDD: direct met2 bridge in the true inter-child gap
```

Observed on 2026-07-24:

```text
VSS length: 37.44
VSS vias: 3
VDD length: 10.86
VDD vias: 0
Magic DRC violations: 0
Magic extraction: passed
shared selector net count: 5
pre-LVS checks: passed
```

The child-interface report showed both PMOS VDD terminals on one shared unnamed
net while `VSUBS` remained separate. Visual inspection accepted the compact
vertical arrangement and found no inherited outer substrate-ring crossing.

This closes the selector at the five-net pre-LVS boundary. Do not redesign or
compact it before leaf LVS.

## Exact next verification gate

First ensure the latest generated GDS files exist:

```bash
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
python scripts/matchmaker/examples/placement/generate_gf180_reference_selector.py
```

Then run independent reference netlisting and LVS:

```bash
python scripts/matchmaker/examples/verification/run_cdac_leaf_lvs.py --target all
```

The new verification boundary performs:

```text
7D_tg_switch.sch
  -> Xschem LVS SPICE netlist, top cell 7D_tg_switch
  -> compare with layout top gf180_cdac_transmission_gate_demo

7D_ref_sel_2to1.sch
  -> Xschem LVS SPICE netlist, top cell 7D_ref_sel_2to1
  -> compare with layout top gf180_cdac_b0_reference_selector_demo
```

Acceptance requires both runs to report:

```text
schematic netlist passed: True
LVS passed: True
Netgen: Circuits match uniquely.
no property errors
no port errors
```

A first LVS mismatch is diagnostic evidence, not permission to alter geometry
immediately. Inspect device counts, pin order, model names, source/drain
equivalence, hierarchy flattening, and property normalization in the report
before changing layout or schematic.

## Work after leaf LVS

```text
1. record base-TG and B0 Netgen reports
2. validate B1/B2/B3 selectors through the same generator and LVS flow
3. define complete CDAC macro placement intent
4. place capacitor array, four selectors, and reset TG
5. run whole-placement Magic DRC
6. add committed routes as typed physical resources
7. plan VOUT, bank, reset, reference, control, supply, and bulk nets
8. run full-CDAC extraction, exact connectivity, and independent Netgen LVS
```

## Known debt

```text
base-TG and B0 independent Netgen LVS are not yet recorded
scaled B1/B2/B3 selectors are not physically validated
legacy MOS placement has not been generalized beyond the current TG builder
generic transitioned-tree planning has no obstacle-aware candidate search
GF180 transition execution currently covers centered met2/met3 via stacks
composite external-pin escape planning is not generalized
multi-terminal complete-CDAC topology planning is absent
committed routes are not yet typed physical resources
stable logical identity is not preserved through extraction end-to-end
```
