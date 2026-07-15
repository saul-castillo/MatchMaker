# Validation status

This file records physical evidence demonstrated in the Chipathon `/foss` environment. Architecture and development direction belong in `ENGINEERING_MAP.md`; decisions belong in ADRs.

## Validated routing foundation

The merged foundation demonstrated:

- MatchMaker environment setup loads successfully.
- Routing and verification unit tests pass.
- The MOS centroid demo generates GDS successfully.
- Logical `NetIntent(A0.gate, A1.gate)` automatically selects physical access.
- The blocked direct path identifies `B0` and `B1`.
- The planner selects outward `A0__gate_W` and `A1__gate_E` access.
- The external same-layer dogleg runs outside the device row.
- Promoted access was reduced from 21,520 hierarchy ports to 128 canonical MOS accesses across eight instances.
- GF180 Magic DRC reports zero violations.
- Magic extracts the routed layout to SPICE.
- Extracted connectivity contains exactly the two intended A instances and no B instances.
- The one-command flow reports `connectivity passed: True` and `pre-LVS checks passed: True`.

Failure history: the original direct route and the first layer-only C route were DRC-clean but electrically connected the intervening B devices. This is the evidence behind the rule that DRC cannot substitute for extraction or LVS.

## PR #3 validation: modular strategy dispatch

Implementation includes:

- common `RouteCandidate`, `CandidateRejection`, and `StrategyDispatchResult` models;
- independent straight, Manhattan, and external-dogleg strategy modules;
- deterministic dispatch, hard-limit filtering, deduplication, ranking, provenance, and rejection evidence;
- same-layer non-inline L routes for perpendicular accesses;
- same-layer non-inline Z routes for parallel accesses;
- midpoint, obstacle-edge, and outer channel candidates;
- outward endpoint-orientation checking;
- full-polyline obstacle checking;
- `plan_two_terminal_net_with_report(...)`;
- a parameterized centroid routing example.

GitHub Actions unit tests and Python compilation pass. The obsolete fixed-port intent, fixed-port planner/router, dogleg-specific executor, compatibility selector, and superseded tests were removed before merge.

### Confirmed: blocked A0-to-A1 dogleg regression

Command:

```bash
python scripts/matchmaker/examples/routing/route_two_centroid_gates.py
```

Confirmed invariants:

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

The modular dispatcher preserved the validated obstacle-aware dogleg and exact A0/A1 connectivity.

### Confirmed: diagonal A0-to-A2 Manhattan regression

Command:

```bash
python scripts/matchmaker/examples/routing/route_two_centroid_gates.py \
  --cell-name nfet_centroid_diagonal_gate_route_demo \
  --source-instance A0 \
  --target-instance A2
```

Observed result:

```text
logical terminals: A0.gate, A2.gate
route strategy: manhattan
direct-route blockers: (none)
actual source access: A0__gate_E
actual target access: A2__gate_W
route points: (-28.57, 13.26) -> (-20.08, 13.26) -> (-20.08, -13.26) -> (-10.29, -13.26)
route length: 44.8
route bends: 2
route width: 0.5
route estimated cost: 45.3
feasible route candidates: 4
rejected route candidates: 110
physical instances: 8
physical access points: 128
DRC passed: True
DRC violations: 0
extraction passed: True
connectivity passed: True
pre-LVS checks passed: True
```

Extraction identified exactly the intended A0 and A2 instances. The generated GDS displayed the expected non-inline same-layer Z geometry.

## Current validated implementation boundary

- deterministic MOS centroid placement;
- typed read-only `PhysicalDesignSnapshot`;
- filtered canonical MOS terminal access;
- logical two-terminal net intent;
- typed per-net and route-group constraints;
- modular same-layer straight, Manhattan L/Z, and external-dogleg planning;
- structured candidate and rejection reports;
- common route-plan and metrics IR;
- mechanical same-layer execution;
- GF180 Magic DRC and extraction;
- exact extracted-connectivity assertions;
- Netgen LVS runner infrastructure.

## Not yet implemented or demonstrated

- a passing independent schematic-to-layout Netgen LVS comparison;
- committed routes as obstacles/resources;
- PDK-resolved width classes and layer policies;
- via planning and execution;
- multi-terminal topology planning;
- matched, differential, symmetry, shielding, and separation group planning;
- congestion-aware graph search and rip-up/reroute;
- stable logical instance identity through extraction;
- capacitor/CDAC physical adapters and routing templates.
