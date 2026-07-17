# Validation status

This file records physical evidence demonstrated in the Chipathon `/foss` environment. Architecture and development direction belong in `ENGINEERING_MAP.md`; decisions belong in ADRs.

## Validated routing foundation

The merged routing foundation demonstrated:

- deterministic MOS centroid placement;
- typed read-only `PhysicalDesignSnapshot`;
- canonical MOS access filtering;
- logical `NetIntent` and typed constraints;
- deterministic straight, Manhattan, and external-dogleg planning;
- common `RoutePlan` execution;
- GF180 Magic DRC with zero violations;
- Magic SPICE extraction;
- exact extracted-connectivity assertions.

Failure history: the first direct route and layer-only C route were DRC-clean but electrically connected intervening B devices. DRC therefore never substitutes for extraction or LVS.

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
rejected route candidates: 110
physical access points: 128
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
pre-LVS checks passed: True
```

Extraction identified exactly the intended A0 and A2 instances. The generated GDS displayed the expected non-inline same-layer Z geometry.

## PR #5 CDAC foundation checkpoints

### Confirmed: installed GF180 MIM primitive inspection

Command:

```bash
python scripts/matchmaker/examples/diagnostics/inspect_gf180_mim_capacitor.py
```

Observed on 2026-07-17 in `/foss`:

```text
active PDK: gf180
mimcap callable: glayout.primitives.mimcap.mimcap
mimcap signature: (pdk, size=(5.0, 5.0)) -> Component
requested size: (5.0, 5.0)
component name: unit_mim_capacitor
component bbox: (-3.1, -3.1) to (3.1, 3.1)
raw port count: 264
```

The raw exports contain 256 nested array/via/implementation ports and eight simple external metal accesses:

```text
top_met_E/N/S/W
  layer: (42, 0)
  width: 5.0

bottom_met_E/N/S/W
  layer: (36, 0)
  width: 6.2
```

The physical adapter therefore accepts only the exact external three-token grammar and rejects names such as `array_row0_col0_top_met_E`. Layer, width, center, and orientation are copied from the actual placed ports at runtime; the observed numeric values are not hard-coded into the adapter.

### Confirmed: initial 4 x 4 capacitor-array geometry

Command used:

```bash
python scripts/matchmaker/examples/placement/generate_cdac_capacitor_array.py
```

A GDS view was supplied showing sixteen uniform MIM units in a regular 4 x 4 array with consistent spacing. This confirms that the primitive wrapper and placement builder produced the intended array geometry.

The screenshot alone does not establish:

- the logical bank assignment pattern;
- the 128-access physical snapshot count;
- Magic DRC success;
- extraction or connectivity.

Those claims remain pending until the updated command output is observed.

### Next required `/foss` result

Pull the latest PR #5 branch and rerun:

```bash
python scripts/matchmaker/examples/placement/generate_cdac_capacitor_array.py
```

The next validated boundary requires:

```text
grid shape: 4 x 4
capacitor instances: 16
physical instances: 16
physical access points: 128
routing obstacles: 16
example top access count: 4
example bottom access count: 4
DRC passed: True
DRC violations: 0
```

Until that output is recorded, the capacitor array is visually generated but not yet claimed as DRC-validated.

## Current demonstrated boundary

- deterministic MOS centroid placement and routing;
- typed physical-design state;
- filtered canonical MOS and MIM access grammars;
- logical two-terminal routing;
- common same-layer route-plan execution;
- GF180 Magic DRC/extraction/connectivity for the MOS regressions;
- typed CDAC hierarchy and net manifest independent of Xschem;
- parameterized 3/4/5-bit CDAC specification tests;
- algorithmic inversion-symmetric capacitor placement;
- actual GF180 MIM primitive inspection;
- visual generation of the 16-unit capacitor array.

## Not yet demonstrated

- Magic DRC for the generated capacitor array;
- full capacitor-array `PhysicalDesignSnapshot` output in `/foss`;
- transmission-gate or selector generated layout;
- complete CDAC placement;
- committed routes as obstacles/resources;
- GF180 routing-rule and via resolution;
- multi-terminal CDAC topology planning;
- CDAC extraction and exact connectivity;
- passing independent schematic-to-layout Netgen LVS;
- PVT, mismatch, or extracted-parasitic CDAC performance.
