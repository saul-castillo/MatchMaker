# Validation status

This file records physical evidence demonstrated in the Chipathon `/foss` environment. Architecture and development direction belong in `ENGINEERING_MAP.md`; durable decisions belong in ADRs.

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

Earlier direct and layer-only routes were DRC-clean but electrically connected intervening devices. DRC never substitutes for extraction or LVS.

## PR #5 CDAC foundation

All observations below were made on 2026-07-17 in `/foss` using `gf180mcuD`.

### Installed GF180 MIM primitive

Command:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_mim_capacitor.py
```

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

The other 256 ports are nested implementation exports and are excluded. The adapter reads center, orientation, width, and layer from runtime geometry.

### Generated reviewed capacitor array

Command:

```bash
python scripts/matchmaker/examples/placement/generate_cdac_capacitor_array.py
```

```text
grid: 4 x 4
counts: B0=1, B1=2, B2=4, B3=8, TERM=1
pattern:
  B2 B2 B3 B3
  B1 B0 B3 B3
  B3 B3 TERM B1
  B3 B3 B2 B2
instances: 16
canonical accesses: 128
obstacles: 16
DRC passed: True
DRC violations: 0
```

The GDS was visually inspected and showed a regular, uniformly spaced array. Capacitor plates are not routed, so no extracted-connectivity or LVS claim is made.

### Installed GF180 MOS primitives

Command:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_transmission_gate_devices.py
```

```text
NMOS: W=4.0 µm, L=0.28 µm
  bbox: (-7.74, -10.065) to (7.74, 10.065)
  raw ports: 2672
  canonical ports: 16

PMOS: W=8.0 µm, L=0.28 µm
  bbox: (-5.245, -9.565) to (5.245, 9.565)
  raw ports: 1392
  canonical ports: 16
```

Both devices expose cardinal gate/source/drain accesses on the observed runtime metal layer `(36, 0)`. E/W signal widths are 0.5 µm. `well_*` ports are well-definition boundaries and are not accepted as VDD/VSS metal accesses.

The historical `canonical external port count: 16` above was emitted by the
former adapter, which still classified four `well_*` boundaries as bulk
accesses. It therefore proves neither conductive body-tie access nor supply
connectivity. Main now recognizes only exact cardinal `tie_*_top_met_*` exports
as bulk, but that revised contract has not yet been run in `/foss`.

### Generated base/reset transmission gate

Command:

```bash
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
```

```text
generated bbox: (-16.48, -11.565) to (11.49, 10.065)
instances: 2
canonical accesses: 32
obstacles: 2

input route:
  NMOS__source_E -> PMOS__source_W
  length: 13.345
  width: 0.5
  layer: (36, 0)

output route:
  NMOS__drain_E -> PMOS__drain_W
  length: 13.345
  width: 0.5
  layer: (36, 0)

DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared signal net count: 2
pre-LVS checks passed: True
```

The two extracted shared nets contain exactly the generated NMOS and PMOS subcircuits as their complete participant multiset. This closes the base TG as a validated pre-LVS generator primitive. Supply connection and independent schematic LVS remain separate gates.

## B0 reference-selector validation history

Command for all four attempts:

```bash
python scripts/matchmaker/examples/placement/generate_gf180_reference_selector.py
```

The selector hierarchy contains two independently generated base TG child cells and three intended shared nets: `COMMON`, `SELECT`, and `SELECT_BAR`.

### Attempt 1: internal vertical escapes

```text
generated bbox: (-29.97, -13.065) to (29.97, 13.065)
child instances: 2
physical accesses: 24
obstacles: 2
public ports: vref_W, vss_E, common_N, select_N, select_bar_S

COMMON:
  VREF_TG__output_E -> VSS_TG__output_W
  length: 15.345
  bends: 0

SELECT:
  VREF_TG__control_N -> VSS_TG__control_bar_N
  length: 80.975
  bends: 2

SELECT_BAR:
  VREF_TG__control_bar_S -> VSS_TG__control_S
  length: 33.225
  bends: 2

DRC passed: False
DRC violations: 6
```

Visual inspection showed the control-route vertical legs crossing child-device interiors before reaching their external channels.

### Attempt 2: folded central corridor

```text
COMMON: direct inner output strap
SELECT: north perimeter route
SELECT_BAR: central-gap route with two close vertical legs and a short bottom U-turn
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared selector net count: 3
pre-LVS checks passed: True
```

This attempt was electrically valid but rejected as final analog geometry. The center fold added unnecessary local coupling, length, asymmetry, and fragility.

### Attempt 3: opposite perimeter controls

Observed final run:

```text
COMMON strategy: reference_selector_direct_common
COMMON length: 15.345
COMMON bends: 0

SELECT strategy: reference_selector_north_perimeter_control
SELECT accesses: VREF_TG__control_W, VSS_TG__control_bar_E
SELECT length: 116.445
SELECT bends: 4
SELECT width: 0.5
SELECT layer: (36, 0)

SELECT_BAR strategy: reference_selector_south_perimeter_control
SELECT_BAR accesses: VREF_TG__control_bar_W, VSS_TG__control_E
SELECT_BAR length: 128.635
SELECT_BAR bends: 4
SELECT_BAR width: 0.5
SELECT_BAR layer: (36, 0)

DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: False
shared selector net count: 1
pre-LVS checks passed: False
```

The GDS was visually cleaner and symmetric, but only one shared child-level net was extracted. The two intended control nets were not recognized as shared selector nets. Therefore this selector is not validated and must not be treated as a reusable primitive.

Likely access-direction issue to verify next:

```text
with nmos_side="left":
  NMOS control outer access = W
  PMOS control_bar outer access = E

SELECT uses the proven outer pair:
  VREF control_W -> VSS control_bar_E

SELECT_BAR Attempt 3 used:
  VREF control_bar_W -> VSS control_E
```

The latter pair points through the internal TG device arrangement rather than using the previously proven inter-child-gap accesses `VREF control_bar_E` and `VSS control_W`. This is a working hypothesis, not yet a proven root cause.

### Attempt 4: single central trunk (accepted)

Observed on 2026-07-22 after commit `06220ad`:

```text
SELECT_BAR strategy: reference_selector_central_gap_control
SELECT_BAR accesses: VREF_TG__control_bar_E, VSS_TG__control_W
SELECT_BAR topology: two horizontal branches, one central vertical trunk
SELECT_BAR bends: 2

DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared selector net count: 3
pre-LVS checks passed: True
```

Visual inspection accepted the central-trunk topology. The route has no folded
U-turn or close parallel vertical legs, the perimeter `SELECT` route remains
separate from `SELECT_BAR`, and no device-interior crossing was observed.

This closes B0 as a reusable pre-LVS selector primitive. The result proves the
three intended shared selector nets in the extracted hierarchy; it does not yet
prove complete schematic equivalence because explicit VDD/VSS bulk/well routing
and an independent Netgen comparison remain outstanding.

## Current demonstrated boundary

Validated:

```text
typed generator hierarchy independent of Xschem
parameterized 3/4/5-bit CDAC specifications
schematic-independent CircuitManifest
stable PlacementResult bindings
algorithmic inversion-symmetric capacitor placement
canonical MIM and MOS physical adapters
4 x 4 MIM array with zero DRC violations
base TG with zero DRC violations
base TG extraction and exact two-signal-net connectivity
B0 selector with zero DRC violations
B0 selector extraction and exact three-shared-net connectivity
accepted single-trunk selector control topology
straight, Manhattan, and external-dogleg routing regressions
```

Not validated:

```text
scaled B1/B2/B3 selectors
metal VDD/VSS access for generated MOS cells
complete CDAC placement
VOUT and bank routing
committed routes as typed resources
GF180 routing-rule and via resolution
CDAC extraction/connectivity
independent schematic-to-layout Netgen LVS
PVT, mismatch, or extracted-parasitic simulation
```

## Next physical checkpoint

Validate the revised conductive bulk-tie contract first:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_transmission_gate_devices.py
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
```

The diagnostic must report exactly four `bulk` accesses per device, named
`tie_N_top_met_N`, `tie_E_top_met_E`, `tie_S_top_met_S`, and
`tie_W_top_met_W`, along with their runtime layers and widths. The TG run must
show promoted `vss_*`/`vdd_*` ports while retaining zero DRC violations,
successful extraction, and exactly two shared signal nets. Any missing tie,
unexpected layer split, DRC failure, or connectivity change blocks selector
supply routing.

After that evidence is recorded, add explicit generated-MOS supply topology and
run independent Magic/Netgen LVS on the base TG and B0 selector before scaling
the selector hierarchy. The existing pre-LVS checks intentionally cover only
the signal/control shared-net multiplicities; they do not substitute for a
complete device-and-net comparison against the hand-authored schematics.

After leaf LVS passes, validate B1/B2/B3 with the same flow. Full-CDAC LVS becomes
meaningful only after all four selectors, the reset TG, all 16 MIM capacitors,
top-level pins, and every signal, reference, control, supply, and bulk connection
are present in one extracted layout netlist.
