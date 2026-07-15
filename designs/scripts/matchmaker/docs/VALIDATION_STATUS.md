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

## Confirmed on `feature/logical-net-routing-ir`

The logical-net routing branch has now been rerun successfully in `/foss` and demonstrates:

- logical `NetIntent` using `TerminalRef` rather than concrete primitive-port names;
- typed `NetConstraintProfile` and `RouteGroupConstraintProfile` models;
- deterministic automatic access candidate generation;
- allowed/forbidden-layer, obstacle, maximum-length, and maximum-bend filtering;
- deterministic length and bend cost ranking;
- common `RoutePlan`, `RouteSegment`, `ViaPlan`, `RouteMetrics`, and `ConstraintCheck` models;
- a mechanical same-layer route-plan executor;
- migration of the centroid demo from fixed `gate_E` endpoints to logical `A0.gate` and `A1.gate` terminals;
- automatic recovery of the validated `A0__gate_W` and `A1__gate_E` outward dogleg;
- route metrics of approximately 118.24 layout units, four bends, width 0.5, and estimated cost approximately 119.24;
- reduction of promoted MOS routing access points from 21,520 unfiltered hierarchy ports to 128 canonical external terminal accesses across eight instances;
- GF180 Magic DRC with zero violations;
- successful Magic SPICE extraction;
- exact extracted connectivity on the two intended A instances only;
- `connectivity passed: True` and `pre-LVS checks passed: True`.

GitHub Actions pure tests and Python compilation pass at the filtered-access branch head.

## Current implementation boundary

Implemented:

- deterministic MOS centroid placement;
- typed, read-only `PhysicalDesignSnapshot`;
- filtered canonical external MOS access points;
- logical two-terminal net intent;
- typed per-net and route-group constraint models;
- automatic same-layer straight/dogleg access selection;
- common route-plan and metrics IR;
- mechanical same-layer segment execution;
- GF180 Magic DRC and extraction;
- automatic extracted-connectivity checks;
- Netgen LVS runner infrastructure.

Not yet demonstrated or implemented:

- a passing independent schematic Netgen LVS comparison;
- via planning and execution;
- PDK-resolved width classes and layer policies;
- general non-inline Manhattan access planning;
- multi-terminal topology planning;
- matched, differential, symmetry, shielding, and separation group planning;
- route-to-route obstacle and congestion handling;
- stable logical instance identity through extraction.
