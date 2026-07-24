# Validation status

This file records physical evidence demonstrated in the Chipathon `/foss`
environment. Architecture and development direction belong in
`ENGINEERING_MAP.md`; durable decisions belong in ADRs.

## Acceptance rules

```text
DRC cleanliness does not prove connectivity.
Extraction does not prove correct terminal identity.
Shared-net counts do not replace child-interface inspection.
Visual symmetry does not replace electrical evidence.
Pre-LVS checks do not replace independent schematic-to-layout LVS.
A source change that affects primitive geometry requires a fresh physical rerun.
A Netgen mismatch is evidence to diagnose, not a reason to tune until it passes.
```

## Capacitor foundation

Commands:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_mim_capacitor.py
python scripts/matchmaker/examples/placement/generate_cdac_capacitor_array.py
```

Observed GF180 MIM contract:

```text
requested unit: 5 µm x 5 µm
actual bbox: 6.2 µm x 6.2 µm
raw ports: 264
canonical external ports: 8
top plate layer: (42, 0)
bottom plate layer: (36, 0)
```

Generated reviewed array:

```text
grid: 4 x 4
counts: B0=1, B1=2, B2=4, B3=8, TERM=1
instances: 16
canonical accesses: 128
obstacles: 16
DRC passed: True
DRC violations: 0
```

The array was visually regular. Capacitor plates are not routed, so no extracted
connectivity or LVS claim is made.

## GF180 MOS access contract

The accepted conductive bulk grammar is limited to:

```text
tie_N_top_met_N
tie_E_top_met_E
tie_S_top_met_S
tie_W_top_met_W
```

`well_*` boundaries are geometry markers and are not electrical routing
accesses.

Measured on 2026-07-23:

```text
required terminal counts per device:
  bulk=4, drain=4, gate=4, source=4

N/S body ties:
  layer: (36, 0)
  width: 3.16

E/W body ties:
  layer: (34, 0)
  NMOS width: 7.81
  PMOS width: 11.81
```

ADR 0005 now requires the generated-TG leaf profile:

```text
conductive body ties: on
substrate taps: off
deep wells: off
guard rings: off
dummies: off on both sides
```

## Base transmission-gate evidence

Command:

```bash
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
```

The pre-compact-profile run established:

```text
instances: 2
canonical accesses: 32
public supply ports: vss_N/E/S/W, vdd_N/E/S/W
input route layer: (36, 0)
output route layer: (36, 0)
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared signal net count: 2
pre-LVS checks passed: True
```

Because the compact profile changes primitive geometry, regenerate the base TG
before running its independent LVS unless current `/foss` output confirms these
same gates.

## B0 selector validation history

All attempts use two independently generated transmission-gate child cells. The
eventual shared nets are:

```text
COMMON
SELECT
SELECT_BAR
VSS
VDD
```

### Attempt 1: internal vertical escapes — rejected

```text
DRC passed: False
DRC violations: 6
```

Control-route legs crossed child-device interiors.

### Attempt 2: folded central corridor — electrically valid, visually rejected

```text
DRC violations: 0
extraction passed: True
shared selector net count: 3
pre-LVS checks passed: True
```

The fold added unnecessary coupling, length, asymmetry, and fragility.

### Attempt 3: opposite perimeter controls — rejected

```text
SELECT length: 116.445
SELECT_BAR length: 128.635
DRC violations: 0
extraction passed: True
shared selector net count: 1
pre-LVS checks passed: False
```

The chosen SELECT_BAR access directions extended through TG interiors.

### Attempt 4: single central trunk — accepted three-net checkpoint

Observed on 2026-07-22 after commit `06220ad`:

```text
SELECT_BAR topology: two horizontal branches and one central vertical trunk
SELECT_BAR bends: 2
DRC violations: 0
extraction passed: True
shared selector net count: 3
pre-LVS checks passed: True
visual inspection: accepted
```

This checkpoint did not include shared VSS/VDD.

### Attempt 5: via-free met2 supplies — rejected

Observed on 2026-07-22 after commit `d582edc`:

```text
SELECT length: 116.445
SELECT_BAR length: 20.485
VSS length: 80.755
VDD length: 42.93
DRC violations: 0
extraction passed: True
shared selector net count: 4
pre-LVS checks passed: False
```

The result was consistent with a missing VDD connection. The 5.68:1 control
length ratio and nested perimeter routing were visually rejected.

### Attempt 6: balanced horizontal met3 controls — rejected

Observed on 2026-07-23 after commit `cc49bdb`:

```text
child placement: horizontal R0/R180
SELECT length: 71.085
SELECT vias: 2
SELECT_BAR length: 71.085
SELECT_BAR vias: 2
VSS length: 98.54
VDD length: 24.825
DRC violations: 0
extraction passed: True
shared selector net count: 4
pre-LVS checks passed: False
```

Equal control lengths closed only the numerical invariant. The four-device row,
large met3 half-perimeters, and VSS service geometry were rejected.

### Attempt 7a: vertical family-composable selector — short identified

The first vertical run from `ff61776` used:

```text
VREF_TG=R0 / VSS_TG=R180
SELECT: west met2 side bus
SELECT_BAR: matched east met2 side bus
COMMON: west transitioned trunk
VSS: east/gap transitioned trunk
VDD: direct inter-child met2 bridge
```

Observed:

```text
DRC violations: 0
extraction passed: True
shared selector net count: 4
pre-LVS checks passed: False
```

Child-interface inspection proved that PMOS VDD merged into `VSUBS`. Visual
inspection found the VDD escape crossing an inherited outer substrate ring.
This changed the diagnosis from “VDD missing” to “VDD shorted to substrate.”

### Attempt 7b: compact-profile vertical selector — accepted five-net checkpoint

Observed in `/foss` on 2026-07-24 after commit `c0de1b9`:

```text
child placement: compact vertical VREF_TG=R0 / VSS_TG=R180

VSS strategy: transitioned_vertical_trunk_tree
VSS length: 37.44
VSS vias: 3
VSS layers: (36, 0), (42, 0)

VDD strategy: vertical_gap_bridge
VDD accesses: VREF_TG__vdd_S, VSS_TG__vdd_S
VDD length: 10.86
VDD bends: 2
VDD vias: 0
VDD layer: (36, 0)

DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared selector net count: 5
pre-LVS checks passed: True
```

The five shared nets consisted of four Magic-generated unnamed nets plus
`VSUBS`, as expected from the extracted hierarchy. The child-interface report
provided the terminal-level evidence missing from earlier attempts:

```text
both VREF/VSS child PMOS VDD terminals -> the same unnamed shared net
both child VSUBS terminals -> VSUBS
VDD net != VSUBS
```

Visual inspection accepted the compact vertical two-row arrangement. No supply
escape crossed an inherited outer substrate ring. The external buses remain
longer than ideal, but no further geometric optimization is permitted before
leaf LVS.

**Acceptance:** Attempt 7b closes B0 at the five-net pre-LVS boundary.

## Current demonstrated boundary

Validated:

```text
typed generator hierarchy independent of Xschem
parameterized 3/4/5-bit CDAC specifications
schematic-independent CircuitManifest
stable PlacementResult bindings
algorithmic inversion-symmetric capacitor placement
canonical MIM and MOS access adapters
explicit compact GF180 MOS leaf profile
4 x 4 MIM array with zero DRC violations
base-TG two-signal-net pre-LVS topology from the measured leaf
B0 vertical selector with zero DRC violations
B0 extraction and exact five-shared-net connectivity
VDD terminal identity distinct from VSUBS
accepted family-composable selector topology
```

Not validated:

```text
independent base-TG Netgen LVS
independent B0 selector Netgen LVS
scaled B1/B2/B3 selectors
complete CDAC placement and routing
CDAC extraction and exact connectivity
full-CDAC Netgen LVS
PVT, mismatch, or extracted-parasitic simulation
```

## Next verification checkpoint: leaf LVS

The independent review schematics are:

```text
designs/libs/core_matchmaker/7D_tg_switch/7D_tg_switch.sch
  schematic top: 7D_tg_switch
  generated layout top: gf180_cdac_transmission_gate_demo

designs/libs/core_matchmaker/7D_ref_sel_2to1/7D_ref_sel_2to1.sch
  schematic top: 7D_ref_sel_2to1
  generated layout top: gf180_cdac_b0_reference_selector_demo
```

Regenerate the layouts, then run:

```bash
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
python scripts/matchmaker/examples/placement/generate_gf180_reference_selector.py
python scripts/matchmaker/examples/verification/run_cdac_leaf_lvs.py --target all
```

The runner exports each Xschem reference as an LVS SPICE netlist and explicitly
binds its schematic top-cell name to the different generated layout top-cell
name. Acceptance requires:

```text
schematic netlist passed: True
LVS passed: True
Circuits match uniquely.
no property errors
no port errors
```

Record the complete reports under each generated cell's `reports/lvs/`
directory. If Netgen fails, preserve the report and diagnose pin order, model
names, hierarchy flattening, device properties, and source/drain equivalence
before changing geometry.

Only after both leaf cells pass LVS should B1/B2/B3 scaling begin.
