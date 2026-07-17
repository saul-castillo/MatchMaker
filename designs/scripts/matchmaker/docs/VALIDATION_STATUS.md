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
```

Not yet demonstrated:

```text
generated transmission-gate geometry
reference-selector hierarchy
complete CDAC placement
routed VOUT or bank nets
committed routes as resources
GF180 routing-rule and via resolution
CDAC extraction/connectivity
independent schematic-to-layout Netgen LVS
PVT, mismatch, or extracted-parasitic simulation
```
