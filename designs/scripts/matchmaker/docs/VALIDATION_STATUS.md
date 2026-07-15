# Validation status

## Confirmed in the Chipathon `/foss` container

The merged `main` flow has demonstrated:

- MatchMaker environment setup loads successfully.
- Routing and verification unit tests pass.
- The MOS centroid demo generates GDS successfully.
- Logical `NetIntent(A0.gate, A1.gate)` automatically selects physical access.
- The blocked direct path identifies `B0` and `B1`.
- The planner selects outward `A0__gate_W` and `A1__gate_E` access.
- The external same-layer dogleg runs outside the device row.
- Promoted routing access was reduced from 21,520 hierarchy ports to 128 canonical MOS accesses across eight instances.
- GF180 Magic DRC reports zero violations.
- Magic extracts the routed layout to SPICE.
- Extracted connectivity contains exactly the two intended A instances and no B instances.
- The one-command flow reports `connectivity passed: True` and `pre-LVS checks passed: True`.

## Implemented on `feature/manhattan-routing-dispatcher`

The current branch adds:

- common `RouteCandidate`, `CandidateRejection`, and `StrategyDispatchResult` models;
- modular straight, Manhattan, and external-dogleg strategy planners;
- deterministic strategy dispatch with common hard-limit filtering;
- candidate deduplication, ranking, provenance, and rejection evidence;
- same-layer non-inline L routes for perpendicular accesses;
- same-layer non-inline Z routes for parallel accesses;
- midpoint, obstacle-edge, and outer channel candidates;
- outward endpoint-orientation checking;
- full-polyline obstacle checking;
- `plan_two_terminal_net_with_report(...)`;
- a parameterized centroid routing demo for selecting arbitrary instance pairs.

GitHub Actions unit tests and Python compilation pass for the implementation branch.

## Required `/foss` validation for PR #3

First rerun the existing dogleg regression:

```bash
python scripts/matchmaker/examples/routing/route_two_centroid_gates.py
```

Required result:

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

Then run the diagonal Manhattan regression:

```bash
python scripts/matchmaker/examples/routing/route_two_centroid_gates.py \
  --cell-name nfet_centroid_diagonal_gate_route_demo \
  --source-instance A0 \
  --target-instance A2
```

Expected planning result:

```text
logical terminals: A0.gate, A2.gate
route strategy: manhattan
actual source access: A0__gate_E
actual target access: A2__gate_W
route bends: 2
DRC passed: True
extraction passed: True
connectivity passed: True
pre-LVS checks passed: True
```

The exact selected channel coordinate may depend on transformed GF180 access geometry. The required invariants are a clear non-inline same-layer Manhattan route and extracted connectivity on exactly A0 and A2.

## Current implementation boundary

Implemented and physically validated on `main`:

- deterministic MOS centroid placement;
- typed read-only `PhysicalDesignSnapshot`;
- filtered canonical MOS terminal access;
- logical two-terminal net intent;
- typed per-net and route-group constraint models;
- same-layer straight and external-dogleg planning;
- common route-plan and metrics IR;
- mechanical same-layer execution;
- GF180 Magic DRC and extraction;
- exact extracted-connectivity assertions;
- Netgen LVS runner infrastructure.

Implemented but awaiting `/foss` validation on PR #3:

- modular strategy dispatch;
- rejection reports;
- same-layer non-inline L/Z Manhattan routing.

Not yet implemented or demonstrated:

- independent schematic Netgen LVS pass;
- committed routes as obstacles/resources;
- PDK-resolved width classes and layer policies;
- via planning and execution;
- multi-terminal topology planning;
- matched, differential, symmetry, shielding, and separation group planning;
- congestion-aware graph search and rip-up/reroute;
- stable logical instance identity through extraction.
