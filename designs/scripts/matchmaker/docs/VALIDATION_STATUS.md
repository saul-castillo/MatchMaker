# Validation status

## Confirmed in the Chipathon `/foss` container

The merged routing foundation has demonstrated:

- MatchMaker environment setup loads successfully.
- Routing-planner and verification-parser unit tests pass.
- The centroid routing demo generates GDS successfully.
- GF180 Magic loads the target GDS and reports zero DRC violations.
- Magic extracts the routed centroid GDS to SPICE.
- A direct route and the first layer-only C-route were DRC-clean but electrically wrong: both connected the intended A devices and the intervening B devices.
- Bounding-box obstacle detection identifies `B0` and `B1`.
- The explicit same-layer spatial dogleg uses outward endpoint access and runs outside the array.
- The dogleg passes GF180 Magic DRC with zero violations.
- Extraction shows the dogleg net on exactly the two intended A instances, with no B-device connection.
- The snapshot-backed one-command flow reports `connectivity passed: True` and `pre-LVS checks passed: True`.

## Added on `feature/logical-net-routing-ir`

The current development branch adds:

- logical `NetIntent` using `TerminalRef` rather than concrete primitive-port names;
- typed `NetConstraintProfile` and `RouteGroupConstraintProfile` models;
- deterministic automatic access candidate generation;
- allowed/forbidden-layer, obstacle, maximum-length, and maximum-bend filtering;
- deterministic length and bend cost ranking;
- common `RoutePlan`, `RouteSegment`, `ViaPlan`, `RouteMetrics`, and `ConstraintCheck` models;
- a mechanical same-layer route-plan executor;
- migration of the centroid demo from fixed `gate_E` endpoints to logical `A0.gate` and `A1.gate` terminals;
- pure tests covering clear straight selection, blocked outward dogleg selection, explicit width, layer rejection, and hard length rejection.

GitHub Actions pure tests and Python compilation pass for the initial implementation. Documentation updates may trigger an additional workflow run.

## Required `/foss` validation for this branch

Run:

```bash
python -m unittest discover -s scripts/matchmaker/tests -v
python scripts/matchmaker/examples/routing/route_two_centroid_gates.py
```

The migrated demo must show:

```text
logical terminals: A0.gate, A1.gate
route strategy: dogleg
actual source access: A0__gate_W
actual target access: A1__gate_E
DRC passed: True
extraction passed: True
connectivity passed: True
pre-LVS checks passed: True
```

The generated geometry and extracted participant set should match the previously validated result.

## Current implementation boundary

Implemented:

- deterministic MOS centroid placement;
- typed, read-only `PhysicalDesignSnapshot`;
- logical two-terminal net intent;
- typed per-net and route-group constraint models;
- automatic same-layer straight/dogleg access selection;
- common route-plan and metrics IR;
- mechanical same-layer segment execution;
- GF180 Magic DRC and extraction;
- automatic extracted-connectivity checks;
- Netgen LVS runner infrastructure.

Not yet demonstrated or implemented:

- a fresh `/foss` run of the logical-intent demo;
- a passing independent schematic Netgen LVS comparison;
- via planning and execution;
- PDK-resolved width classes and layer policies;
- general non-inline Manhattan access planning;
- multi-terminal topology planning;
- matched, differential, symmetry, shielding, and separation group planning;
- route-to-route obstacle and congestion handling;
- stable logical instance identity through extraction.
