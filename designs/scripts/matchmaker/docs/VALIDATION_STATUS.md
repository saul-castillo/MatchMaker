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
A reconstructed source change must be rerun before inheriting the lost workspace's physical claim.
```

## Merged routing foundation

```text
A0.gate -> A1.gate
  strategy: blocked external dogleg
  DRC violations: 0
  extraction: passed
  exact endpoint connectivity: passed

A0.gate -> A2.gate
  strategy: two-bend Manhattan Z route
  route length: 44.8
  route width: 0.5
  feasible candidates: 4
  rejected candidates: 110
  DRC violations: 0
  extraction: passed
  exact endpoint connectivity: passed
```

Earlier direct and layer-only routes were DRC-clean but electrically connected
intervening devices.

## Capacitor foundation

Command:

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

top_met_E/N/S/W
  logical terminal: top
  observed layer: (42, 0)
  observed width: 5.0

bottom_met_E/N/S/W
  logical terminal: bottom
  observed layer: (36, 0)
  observed width: 6.2
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

Command:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_transmission_gate_devices.py
```

Measured on 2026-07-23 before the compact-profile correction:

```text
NMOS: W=4.0 µm, L=0.28 µm
  bbox: (-7.74, -10.065) to (7.74, 10.065)
  raw ports: 2672

PMOS: W=8.0 µm, L=0.28 µm
  bbox: (-5.245, -9.565) to (5.245, 9.565)
  raw ports: 1392

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

The accepted conductive bulk grammar is limited to:

```text
tie_N_top_met_N
tie_E_top_met_E
tie_S_top_met_S
tie_W_top_met_W
```

`well_*` boundaries remain geometry markers and are not electrical routing
accesses.

## Base transmission-gate evidence

Command:

```bash
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
```

Observed before the compact-profile correction:

```text
instances: 2
canonical accesses: 32
public supply ports: vss_N/E/S/W, vdd_N/E/S/W

input route:
  NMOS source -> PMOS source
  layer: (36, 0)
  width: 0.5

output route:
  NMOS drain -> PMOS drain
  layer: (36, 0)
  width: 0.5

DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared signal net count: 2
pre-LVS checks passed: True
```

This closes the two signal nets for the measured leaf geometry. Because the
recovered source now changes geometry-affecting primitive options, the base TG
must be rerun before the compact profile inherits this physical acceptance.

## B0 selector validation history

Command for all recorded selector attempts:

```bash
python scripts/matchmaker/examples/placement/generate_gf180_reference_selector.py
```

The hierarchy contains two independently generated TG child cells. The eventual
five shared nets are:

```text
COMMON
SELECT
SELECT_BAR
VSS
VDD
```

### Attempt 1: internal vertical escapes — rejected

```text
COMMON: direct inner output strap
SELECT: internal north escape
SELECT_BAR: internal south escape
DRC passed: False
DRC violations: 6
```

Visual inspection showed control-route legs crossing child-device interiors.

### Attempt 2: folded central corridor — electrically valid, visually rejected

```text
COMMON: direct inner output strap
SELECT: north perimeter route
SELECT_BAR: central-gap route with close parallel legs and a short U-turn
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared selector net count: 3
pre-LVS checks passed: True
```

The fold added unnecessary coupling, length, asymmetry, and fragility.

### Attempt 3: opposite perimeter controls — rejected

```text
SELECT length: 116.445
SELECT bends: 4
SELECT_BAR length: 128.635
SELECT_BAR bends: 4
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: False
shared selector net count: 1
pre-LVS checks passed: False
```

The chosen SELECT_BAR access directions extended through the TG interiors rather
than using the previously proven gap-facing pair.

### Attempt 4: single central trunk — accepted three-net checkpoint

Observed on 2026-07-22 after commit `06220ad`:

```text
SELECT_BAR accesses: VREF_TG control_bar_E, VSS_TG control_W
SELECT_BAR topology: two horizontal branches and one central vertical trunk
SELECT_BAR bends: 2
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared selector net count: 3
pre-LVS checks passed: True
visual inspection: accepted
```

This remains the last accepted B0 selector boundary. It does not include shared
VSS/VDD routing or independent LVS.

### Attempt 5: via-free met2 supplies — rejected

Observed on 2026-07-22 after commit `d582edc`:

```text
SELECT length: 116.445
SELECT_BAR length: 20.485
VSS length: 80.755
VDD length: 42.93
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: False
shared selector net count: 4
pre-LVS checks passed: False
```

The result was consistent with a missing VDD connection. Visual inspection also
rejected the 5.68:1 control-length ratio and nested perimeter routing.

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
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: False
shared selector net count: 4
pre-LVS checks passed: False
```

Equal control lengths closed only the numerical symmetry invariant. The
four-device row, met3 half-perimeters, and large VSS service geometry were
visually rejected.

### Attempt 7: family-composable vertical selector — root cause identified

The first `/foss` run of the vertical architecture from `ff61776` used:

```text
placement: compact-intent vertical VREF_TG=R0 / VSS_TG=R180 pair
SELECT: west met2 side bus
SELECT_BAR: matched east met2 side bus
COMMON: west met2-to-met3 transitioned trunk
VSS: east/gap met2-to-met3 transitioned trunk
VDD: direct inter-child met2 bridge
```

Observed acceptance state:

```text
DRC: clean
extraction: passed
shared selector net count: 4
five-net connectivity: failed
```

The child-interface diagnostic showed that PMOS `vdd_*` did not remain a distinct
VDD net. It merged into `VSUBS`. Layout inspection identified a PMOS VDD escape
crossing an inherited outer substrate ring.

This changed the diagnosis from “VDD is missing” to “VDD is shorted to
substrate.” The former leaf profile requested body ties but left substrate taps,
deep wells, guard rings, and dummies inherited from the installed gLayout
defaults.

The lost local workspace fixed this in commit `b7d80a6`, reported 100 tests
passing, and remained one commit ahead of remote. That Git object was never
published and could not be recovered. ADR 0005 and the current recovery branch
reconstruct the same architectural correction:

```text
conductive body ties: on
substrate taps: off
deep wells: off
guard rings: off
dummies: off
```

The recovered intent rejects inherited or conflicting profiles before geometry
generation. The diagnostic now prints the profile and normalized bbox size.

No compact-profile physical result is claimed yet. The selector and base TG must
be rerun in `/foss`.

## Current demonstrated boundary

Validated:

```text
typed generator hierarchy independent of Xschem
parameterized 3/4/5-bit CDAC specifications
schematic-independent CircuitManifest
stable PlacementResult bindings
algorithmic inversion-symmetric capacitor placement
canonical MIM and MOS access adapters
measured conductive GF180 body-tie access grammar
4 x 4 MIM array with zero DRC violations
pre-recovery base TG with zero DRC violations and exact two-signal-net connectivity
B0 selector with zero DRC violations and exact three-shared-net connectivity
accepted single-trunk selector control topology
straight, Manhattan, and external-dogleg routing regressions
```

Not validated:

```text
compact-profile base TG physical rerun
compact-profile vertical R0/R180 B0 five-net selector
proof that VDD remains distinct from VSUBS
GF180 met2/met3 COMMON/VSS via execution under the compact leaf envelope
scaled B1/B2/B3 selectors
complete CDAC placement and routing
CDAC extraction and exact connectivity
independent schematic-to-layout Netgen LVS
PVT, mismatch, or extracted-parasitic simulation
```

## Next physical checkpoint

Run:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_transmission_gate_devices.py
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
python scripts/matchmaker/examples/placement/generate_gf180_reference_selector.py
```

The diagnostic must report:

```text
explicit compact primitive profile:
  ties=on
  substrate_taps=off
  deep_wells=off
  guard_rings=off
  dummies=off
bbox sizes consistent with the compact leaf geometry
four required bulk accesses per device
```

The base TG must retain:

```text
DRC violations: 0
extraction passed: True
shared signal net count: 2
pre-LVS checks passed: True
```

The selector must report:

```text
child orientations: VREF_TG=R0, VSS_TG=R180
SELECT strategy: external_west_side_bus
SELECT bends: 2
SELECT vias: 0
SELECT_BAR strategy: external_east_side_bus
SELECT_BAR bends: 2
SELECT_BAR vias: 0
SELECT length == SELECT_BAR length
COMMON strategy: transitioned_vertical_trunk_tree
COMMON vias: 2
VSS strategy: transitioned_vertical_trunk_tree
VSS vias: 3
VDD strategy: vertical_gap_bridge
DRC violations: 0
extraction passed: True
shared selector net count: 5
pre-LVS checks passed: True
```

The child-interface report must show VDD as an independent shared child net and
must not map any PMOS VDD terminal to `VSUBS`. Visual inspection must confirm
that no supply escape crosses an inherited outer ring.

After that evidence is recorded, run independent Magic/Netgen LVS on the base TG
and B0 selector. Only then proceed to B1/B2/B3 scaling and full-CDAC assembly.
