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

Failure history to preserve: earlier direct and layer-only routes were DRC-clean but electrically connected intervening devices. DRC never substitutes for extraction or LVS.

## PR #5 CDAC foundation

### Installed GF180 MIM primitive

Command:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_mim_capacitor.py
```

Observed on 2026-07-17:

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

The other 256 ports are nested primitive implementation exports and are excluded. Layer, width, center, and orientation are read from runtime ports.

### Generated 4-bit capacitor array

Command:

```bash
python scripts/matchmaker/examples/placement/generate_cdac_capacitor_array.py
```

Observed on 2026-07-17:

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

The GDS was visually inspected and showed a regular, uniformly spaced array. Capacitor plates are not routed; no extracted-connectivity or LVS claim is made.

### Installed GF180 MOS primitives

Command:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_transmission_gate_devices.py
```

Observed for the base/reset switch:

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

Both devices expose cardinal gate/source/drain accesses on the observed runtime metal layer `(36, 0)`. E/W signal widths are 0.5 µm. `well_*` is on well-definition layers and is not accepted as VDD/VSS metal access.

### Generated base transmission gate

Command:

```bash
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
```

Observed on 2026-07-17:

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

## B0 reference-selector iterations

### Attempt 1: internal vertical escape — failed

Observed on 2026-07-17:

```text
child instances: 2
physical accesses: 24
obstacles: 2

COMMON:
  VREF_TG__output_E -> VSS_TG__output_W

SELECT:
  VREF_TG__control_N -> VSS_TG__control_bar_N

SELECT_BAR:
  VREF_TG__control_bar_S -> VSS_TG__control_S

DRC passed: False
DRC violations: 6
```

The vertical control legs crossed child-device interiors before reaching external channels. This topology is rejected.

### Attempt 2: north perimeter plus folded center/south route — electrically passed, rejected physically

Observed on 2026-07-17:

```text
COMMON strategy: reference_selector_direct_common
COMMON points:
  (-6.425, 3.945) -> (8.92, 3.945)
COMMON length: 15.345
COMMON bends: 0

SELECT strategy: reference_selector_north_perimeter_control
SELECT accesses:
  VREF_TG__control_W -> VSS_TG__control_bar_E
SELECT points:
  (-22.48, -2.445)
  -> (-32.22, -2.445)
  -> (-32.22, 13.065)
  -> (32.22, 13.065)
  -> (32.22, -6.445)
  -> (24.975, -6.445)
SELECT length: 116.445
SELECT bends: 4

SELECT_BAR strategy: reference_selector_south_inner_control
SELECT_BAR accesses:
  VREF_TG__control_bar_E -> VSS_TG__control_W
SELECT_BAR points:
  (-6.995, -6.445)
  -> (-0.5, -6.445)
  -> (-0.5, -13.065)
  -> (0.5, -13.065)
  -> (0.5, -2.445)
  -> (9.49, -2.445)
SELECT_BAR length: 33.725
SELECT_BAR bends: 4

DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared selector net count: 3
pre-LVS checks passed: True
```

The GDS showed two closely spaced central vertical legs connected by a short bottom U-turn. Although legal and correctly connected, this topology is rejected because it adds unnecessary local coupling, asymmetry, route folding, and sensitivity to child spacing.

### Accepted design pending final physical rerun

The planner now uses matching opposite perimeter routes:

```text
COMMON
  direct output_E -> output_W

SELECT
  VREF control_W
  -> west external escape
  -> north perimeter
  -> east external escape
  -> VSS control_bar_E

SELECT_BAR
  VREF control_bar_W
  -> west external escape
  -> south perimeter
  -> east external escape
  -> VSS control_E
```

The central corridor and its spacing parameter were removed. Coordinates remain derived from runtime child bboxes, endpoint widths, and typed perimeter clearance.

Run:

```bash
git pull --ff-only
source scripts/matchmaker/env/setup.sh
python scripts/matchmaker/examples/placement/generate_gf180_reference_selector.py
```

Required evidence before PR #5 can merge:

```text
SELECT strategy: reference_selector_north_perimeter_control
SELECT_BAR strategy: reference_selector_south_perimeter_control
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared selector net count: 3
pre-LVS checks passed: True
```

## Current demonstrated boundary

Validated:

```text
typed generator hierarchy independent of Xschem
parameterized 3/4/5-bit CDAC specifications
algorithmic inversion-symmetric capacitor placement
canonical MIM and MOS physical adapters
4 x 4 MIM array with zero DRC violations
base transmission gate with zero DRC violations
base transmission-gate extraction
exact two-signal-net connectivity
B0 selector hierarchical generation
B0 selector exact three-net connectivity on discarded folded topology
straight, Manhattan, and external-dogleg routing regressions
```

Not yet demonstrated:

```text
accepted symmetric-perimeter B0 selector physical rerun
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
