# MatchMaker Engineering Map

This is the canonical live-state document for the engine. Read it before changing
code. Detailed physical evidence belongs in `VALIDATION_STATUS.md`; durable
architecture decisions belong in ADRs.

## Current state

```text
base: main
branch: main (direct-update workflow)
PR: none
latest accepted physical checkpoint: vertical B0 selector, five shared nets
latest accepted evidence date: 2026-07-24
active checkpoint: independent base-TG and B0 schematic-to-layout Netgen LVS
```

The compact MOS profile from ADR 0005 fixed the Attempt 7 VDD-to-`VSUBS` short.
The regenerated vertical selector is accepted at the five-net pre-LVS boundary:

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

```text
typed generator specification
-> CircuitManifest
-> placement and routing generation
-> generated layout/netlist
-> independent Xschem reference netlist
-> Netgen LVS
```

The generator never parses Xschem to decide layout. Schematics under
`designs/libs/core_matchmaker/` are independent review and LVS references only.

## Non-negotiable invariants

1. Concrete values live only in typed specs, named presets, explicit policies, or
   PDK/device adapters.
2. Algorithms do not hide bit counts, bank sizes, coordinates, primitive
   dimensions, port names, layers, widths, or spacing rules.
3. Primitive port grammar is interpreted once in the matching family adapter.
4. Runtime geometry supplies centers, orientations, layers, widths, and envelopes.
5. Placement returns stable `PlacementResult` bindings.
6. Routing consumes typed `PhysicalDesignSnapshot` state and emits ordinary
   `RoutePlan` objects.
7. Executors draw plans; they do not invent policy.
8. Examples contain orchestration only, not reusable policy.
9. DRC does not prove connectivity or analog quality.
10. Extraction and shared-net counts do not replace terminal-level inspection.
11. Pre-LVS checks do not replace independent schematic-to-layout LVS.
12. Unsupported cases fail explicitly.
13. Device-family grammar stays in family adapters; generic composition and route
    templates cannot inspect family-specific names.
14. Block planners bind logical roles to reusable primitives; they do not become
    private geometry generators.
15. Safety-critical primitive options are explicit. `None` is not accepted when it
    would inherit geometry-affecting gLayout defaults.
16. Schematic and generated-layout top names are independent identities and must be
    bound explicitly at the LVS boundary.
17. Generated output names are shared constants. Generators, path creation, and LVS
    targets must not duplicate cell-name literals.

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
  PlacementPlan, PlacementResult, transformed envelopes, oriented-pair composition

placement/cdac/
  capacitor-array, transmission-gate, and selector intent/builder bindings

primitives/gf180_mos_primitive_options.py
  explicit compact MOS profile, validation, and diagnostics

physical/
  device-family access grammar and family-agnostic generated-child snapshots

routing/planners/corridor_route_planner.py
  side bus, gap bridge, and transitioned multi-terminal trunk templates

routing/planners/reference_selector_topology_planner.py
  thin selector role binding and matching constraints

routing/routers/route_plan_executor.py
  mechanical segment and injected-via execution

outputs/cdac_demo_cell_names.py
  canonical generated-cell identities shared by examples and verification

outputs/core_analog_cell_paths.py
  standard generated GDS, netlist, and report directory structure

verification/netlist/xschem_schematic_netlist.py
  headless independent-reference SPICE export from Xschem

verification/lvs/cdac_leaf_targets.py
  reviewed schematic/layout top-cell binding for base TG and B0

verification/lvs/magic_netgen_lvs.py
  Magic extraction and Netgen comparison with distinct schematic/layout names

examples/verification/run_cdac_leaf_lvs.py
  orchestration only; no reusable geometry or device policy
```

Generic placement and corridor modules do not import selector net names, GF180
port tokens, numeric layers, Xschem paths, Netgen commands, or output-directory
names.

## Canonical generated-cell names

```text
base transmission gate:
  gf180_cdac_base_transmission_gate_demo

B0 reference selector:
  gf180_cdac_b0_reference_selector_demo
```

The obsolete `gf180_cdac_transmission_gate_demo` directory was created only by the
first failed LVS run, which used a duplicated literal that omitted `base_`. It is
not a reference-selector output and can be deleted. There is only one active B0
reference-selector directory.

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

The measured leaf established:

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
unless current `/foss` output confirms the same gates.

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
net while `VSUBS` remained separate. Do not redesign or compact this selector
before leaf LVS.

## Exact next verification gate

Synchronize and remove the obsolete failed-run directory:

```bash
cd /foss/designs
git pull --ff-only
rm -rf libs/core_analog/gf180_cdac_transmission_gate_demo
```

Regenerate the canonical layouts:

```bash
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
python scripts/matchmaker/examples/placement/generate_gf180_reference_selector.py
```

Then run independent reference netlisting and LVS:

```bash
python scripts/matchmaker/examples/verification/run_cdac_leaf_lvs.py --target all
```

The verification boundary is:

```text
7D_tg_switch.sch
  schematic top: 7D_tg_switch
  layout top: gf180_cdac_base_transmission_gate_demo

7D_ref_sel_2to1.sch
  schematic top: 7D_ref_sel_2to1
  layout top: gf180_cdac_b0_reference_selector_demo
```

Acceptance requires both runs to report:

```text
schematic netlist passed: True
LVS passed: True
Netgen: Circuits match uniquely.
no property errors
no port errors
```

A first LVS mismatch is diagnostic evidence, not permission to alter geometry.
Inspect device counts, pin order, model names, source/drain equivalence, hierarchy
flattening, and property normalization before changing layout or schematic.

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
