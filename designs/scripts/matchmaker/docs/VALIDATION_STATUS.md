# Validation status

This file records physical evidence demonstrated in the Chipathon `/foss` environment. Architecture and development direction belong in `ENGINEERING_MAP.md`; durable decisions belong in ADRs.

## Merged routing foundation

Two MOS routing regressions are physically validated:

```text
A0.gate -> A1.gate
  strategy: blocked external dogleg
  DRC violations: 0
  extraction: passed
  exact endpoint connectivity: passed

A0.gate -> A2.gate
  strategy: two-bend Manhattan Z route
  length: 44.8
  width: 0.5
  feasible candidates: 4
  rejected candidates: 110
  DRC violations: 0
  extraction: passed
  exact endpoint connectivity: passed
```

Failure history to preserve: an earlier direct route and an early layer-only C route were DRC-clean but electrically connected intervening B devices. DRC never substitutes for extraction or LVS.

## PR #5 CDAC foundation

### Installed GF180 MIM primitive

Command:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_mim_capacitor.py
```

Observed on 2026-07-17 for the typed 5 µm by 5 µm unit request:

```text
primitive bbox: 6.2 µm x 6.2 µm
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

The other 256 ports are nested implementation exports and are excluded from `PhysicalDesignSnapshot`. Coordinates, orientations, widths, and layers are copied from runtime ports.

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
physical instances: 16
canonical accesses: 128
obstacles: 16
DRC passed: True
DRC violations: 0
```

The GDS was visually inspected and showed a uniform, regularly spaced array. Capacitor plates are not routed, so no array connectivity or LVS claim is made.

### Installed GF180 MOS primitives

Command:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_transmission_gate_devices.py
```

Observed for the typed base/reset switch:

```text
NMOS: W=4.0 µm, L=0.28 µm
  bbox: (-7.74, -10.065) to (7.74, 10.065)
  raw ports: 2672
  canonical simple ports: 16

PMOS: W=8.0 µm, L=0.28 µm
  bbox: (-5.245, -9.565) to (5.245, 9.565)
  raw ports: 1392
  canonical simple ports: 16
```

Both devices expose simple cardinal `gate`, `source`, and `drain` accesses on the observed runtime metal layer `(36, 0)`. E/W signal widths are 0.5 µm. The source/drain offsets differ by the same 2.0 µm, allowing one derived PMOS translation to align both parallel nets.

`well_*` ports are on well-definition layers, observed as `(204, 0)` for NMOS and `(21, 0)` for PMOS. They are not accepted as `VSS` or `VDD` metal ports. Supply semantics remain unassigned until a metal tie contract is observed.

### Generated base transmission gate

Command:

```bash
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
```

Observed on 2026-07-17:

```text
generated bbox: (-16.48, -11.565) to (11.49, 10.065)
physical instances: 2
canonical accesses: 32
obstacles: 2

input route:
  NMOS__source_E -> PMOS__source_W
  (-7.92, 2.395) -> (5.425, 2.395)
  length: 13.345
  width: 0.5
  layer: (36, 0)

output route:
  NMOS__drain_E -> PMOS__drain_W
  (-7.92, 3.195) -> (5.425, 3.195)
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

The two extracted shared nets contain exactly the generated NMOS and PMOS subcircuits as their complete participant multiset. This closes the base transmission gate as a validated pre-LVS generator primitive. Bulk/supply connection and independent schematic LVS remain separate gates.

### Active checkpoint: B0 reference selector

Implemented but not yet physically demonstrated:

```text
two generated base TG children
side-by-side placement from runtime bboxes
VREF input on the left child
VSS input on the right child
direct common-output RoutePlan
north SELECT RoutePlan
south SELECT_BAR RoutePlan
runtime-derived public ports
Magic DRC/extraction entrypoint
exact three-shared-net assertion between child TG subcircuits
```

Run:

```bash
python scripts/matchmaker/examples/placement/generate_gf180_reference_selector.py
```

Required evidence:

```text
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared selector net count: 3
pre-LVS checks passed: True
```

The expected three shared nets are `COMMON`, `SELECT`, and `SELECT_BAR`. The assertion fails if the two child transmission gates share fewer or additional nets.

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
straight, Manhattan, and external-dogleg routing regressions
```

Not yet demonstrated:

```text
B0 reference-selector physical DRC/extraction/connectivity
scaled B1/B2/B3 transmission gates and selectors
metal VDD/VSS access for generated MOS cells
complete CDAC placement
VOUT and bank routing
committed routes as typed resources
GF180 routing-rule and via resolution
CDAC extraction/connectivity
independent schematic-to-layout Netgen LVS
PVT, mismatch, or extracted-parasitic simulation
```
