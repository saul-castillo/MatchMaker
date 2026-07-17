# Validation status

This file records physical evidence demonstrated in the Chipathon `/foss` environment. Architecture and development direction belong in `ENGINEERING_MAP.md`; decisions belong in ADRs.

## Validated routing foundation

The merged routing foundation demonstrated deterministic MOS centroid placement, typed physical state, logical two-terminal routing, common `RoutePlan` execution, GF180 Magic DRC, Magic extraction, and exact extracted-connectivity assertions.

### Blocked A0-to-A1 dogleg

```text
logical terminals: A0.gate, A1.gate
route strategy: dogleg
actual source access: A0__gate_W
actual target access: A1__gate_E
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
pre-LVS checks passed: True
```

### Diagonal A0-to-A2 Manhattan route

```text
logical terminals: A0.gate, A2.gate
route strategy: manhattan
actual source access: A0__gate_E
actual target access: A2__gate_W
route length: 44.8
route bends: 2
route width: 0.5
feasible route candidates: 4
rejected candidates: 110
physical access points: 128
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
pre-LVS checks passed: True
```

Failure history to preserve: an earlier direct route and an early layer-only C route were DRC-clean but electrically connected intervening B devices. DRC therefore never substitutes for extraction or LVS.

## PR #5 CDAC foundation

### Installed GF180 MIM primitive

Command:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_mim_capacitor.py
```

Observed on 2026-07-17 in `/foss` for the typed 5 µm by 5 µm request:

```text
mimcap callable: glayout.primitives.mimcap.mimcap
component bbox: (-3.1, -3.1) to (3.1, 3.1)
raw port count: 264

top_met_E/N/S/W
  logical terminal: top
  observed layer: (42, 0)
  observed width: 5.0

bottom_met_E/N/S/W
  logical terminal: bottom
  observed layer: (36, 0)
  observed width: 6.2
```

The other 256 ports are nested array/via implementation exports and are excluded from `PhysicalDesignSnapshot`. The adapter reads center, orientation, width, and layer from each placed port at runtime.

### Generated 4-bit capacitor array

Command:

```bash
python scripts/matchmaker/examples/placement/generate_cdac_capacitor_array.py
```

Observed on 2026-07-17 in `/foss`:

```text
grid shape: 4 x 4
capacitor instances: 16
group counts: {'B0': 1, 'B1': 2, 'B2': 4, 'B3': 8, 'TERM': 1}
placement pattern:
B2 B2 B3 B3
B1 B0 B3 B3
B3 B3 TERM B1
B3 B3 B2 B2
physical instances: 16
physical access points: 128
routing obstacles: 16
example top access count: 4
example bottom access count: 4
example top layers: [(42, 0)]
example bottom layers: [(36, 0)]
DRC passed: True
DRC violations: 0
```

The generated GDS was visually inspected and showed a regular, uniformly spaced 4 by 4 MIM array. This validates placement geometry and DRC only. The capacitor plates are not yet routed, so no extracted-connectivity or LVS claim is made.

### Installed GF180 MOS primitives for the base transmission gate

Command:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_transmission_gate_devices.py
```

Observed on 2026-07-17 in `/foss` using the typed reset/B0 switch dimensions:

```text
requested NMOS: W=4.0 µm, L=0.28 µm
requested PMOS: W=8.0 µm, L=0.28 µm

NMOS bbox: (-7.74, -10.065) to (7.74, 10.065)
NMOS raw ports: 2672
NMOS canonical simple ports: 16

PMOS bbox: (-5.245, -9.565) to (5.245, 9.565)
PMOS raw ports: 1392
PMOS canonical simple ports: 16
```

For both devices, simple `gate_*`, `source_*`, and `drain_*` accesses are on the runtime metal layer reported as `(36, 0)`. Their E/W access widths are 0.5 µm. The source/drain vertical offsets differ between NMOS and PMOS by the same 2.0 µm, so one derived PMOS translation can align both parallel signal nets.

The simple `well_*` ports are on well-definition layers, observed as `(204, 0)` for the NMOS and `(21, 0)` for the PMOS. They are physical bulk boundaries, not routed `VSS` or `VDD` metal ports. The supplied concise diagnostic output did not expose an additional simple unclassified metal tie/substrate-tap port, so supply semantics remain deliberately unassigned.

### Generated base transmission gate

Command:

```bash
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
```

Observed on 2026-07-17 in `/foss`:

```text
generated cell: gf180_cdac_base_transmission_gate_demo
requested switch dimensions: nmos=(W=4.0, L=0.28), pmos=(W=8.0, L=0.28)
generated bbox: (-16.48, -11.565) to (11.49, 10.065)
physical instances: 2
physical access points: 32
routing obstacles: 2
public ports:
  input_W, output_W, control_W, control_bar_W
  input_E, output_E, control_E, control_bar_E

input route:
  accesses: NMOS__source_E, PMOS__source_W
  points: (-7.92, 2.395) -> (5.425, 2.395)
  length: 13.345
  width: 0.5
  layer: (36, 0)

output route:
  accesses: NMOS__drain_E, PMOS__drain_W
  points: (-7.92, 3.195) -> (5.425, 3.195)
  length: 13.345
  width: 0.5
  layer: (36, 0)

DRC passed: True
DRC violations: 0
```

The GDS was visually inspected. It shows separated NMOS and PMOS primitive envelopes with two parallel horizontal signal straps between the inward source and drain accesses. This proves deterministic geometry generation and DRC legality. It does not yet prove that Magic extracts exactly two distinct shared signal nets.

The run also emitted two non-electrical warnings: historical dummy-keyword aliases were probed, and the child cells remained unnamed in the GDS library. Both were subsequently repaired at the GF180 primitive adapter/child-cell naming boundaries.

### Next transmission-gate checkpoint

Pull the latest PR #5 branch and rerun:

```bash
python scripts/matchmaker/examples/placement/generate_gf180_transmission_gate.py
```

The command now runs Magic extraction and requires exactly two distinct shared nets whose participants are the generated NMOS and PMOS subcircuits. Required evidence:

```text
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
shared signal net count: 2
pre-LVS checks passed: True
```

Supply-port assignment remains outside this checkpoint.

## Current demonstrated boundary

Validated:

```text
deterministic MOS centroid placement and routing
typed PhysicalDesignSnapshot
canonical MOS and MIM access filtering
straight, Manhattan L/Z, and external-dogleg strategies
common RoutePlan execution
GF180 Magic DRC and extraction for MOS routing regressions
exact MOS route connectivity assertions
typed CDAC hierarchy and CircuitManifest independent of Xschem
parameterized 3/4/5-bit CDAC specifications
algorithmic inversion-symmetric capacitor placement
stable capacitor PlacementResult bindings
canonical capacitor PhysicalDesignSnapshot
4 x 4 GF180 MIM array with zero DRC violations
installed NMOS/PMOS signatures, bboxes, and simple external ports inspected
generated base transmission-gate geometry with zero DRC violations
```

Not yet demonstrated:

```text
metal VDD/VSS access for the transmission gate
transmission-gate extraction and exact two-net connectivity
reference-selector hierarchy
complete CDAC placement
routed VOUT or bank nets
committed routes as resources
GF180 routing-rule and via resolution
CDAC extraction/connectivity
independent schematic-to-layout Netgen LVS
PVT, mismatch, or extracted-parasitic simulation
```
