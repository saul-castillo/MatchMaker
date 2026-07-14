# Validation status

## Confirmed in the Chipathon `/foss` container

- MatchMaker environment setup loads successfully.
- Routing-planner and verification-parser unit tests passed.
- The centroid routing demo generated GDS successfully.
- GF180 Magic loaded the target GDS and reported zero DRC violations.
- The corrected DRC adapter returned `passed=True` and `violation_count=0`.
- Magic successfully extracted the routed centroid GDS to SPICE.
- The original straight route net appeared on four top-level instances: both intended A devices and both intervening B devices. It was DRC-clean but electrically wrong.
- Bounding-box obstacle detection correctly identified `B0` and `B1`.
- The first C-route fallback remained electrically wrong: extraction still showed the routed node on the same four instances.
- The attempted north/south access fallback failed safely because the installed GF180 gate primitive did not expose usable `gate_N` or `gate_S` ports.
- The explicit spatial dogleg generated a visibly external route using outward endpoint access.
- The spatial dogleg passed GF180 Magic DRC with zero violations.
- Magic extraction showed the dogleg route net on exactly two top-level instances, both intended A devices, with no B-device connection.
- The one-command demo completed with pre-LVS checks passing.

## Added after the latest `/foss` run

The branch now also includes:

- typed `TerminalRef`, `AccessPoint`, `PlacedInstance`, `RoutingObstacle`, and `PhysicalDesignSnapshot` models;
- a MOS-centroid snapshot adapter that promotes ports and captures stable instance, access-point, and obstacle records;
- router support for consuming the explicit snapshot instead of reading obstacle state only from `Component.info`;
- exact extracted shared-net assertions based on the expected endpoint subcircuit participant multiset;
- a standard `reports/connectivity/` artifact path;
- automatic connectivity gating in `verify_generated_cell(...)`;
- automatic connectivity gating in `route_two_centroid_gates.py`, so the command now exits nonzero if the extracted net has missing or extra participants;
- pure unit tests for physical snapshots and connectivity assertions.

The latest GitHub Actions pure-test and compilation workflow passes. These new snapshot and automatic connectivity-gate changes still require one fresh `/foss` rerun before they should be treated as integration-validated.

## Current implemented foundation

- deterministic MOS centroid placement;
- stable physical access naming;
- typed physical-design snapshot;
- point-to-point route intent;
- obstacle detection;
- explicit same-layer spatial dogleg routing;
- GF180 Magic DRC;
- Magic SPICE extraction;
- manual and automatic extracted-connectivity checks;
- Netgen LVS runner infrastructure;
- structured reports and failure results.

## Not yet demonstrated

- a fresh `/foss` run of the snapshot-backed demo with automatic connectivity gating;
- a passing Netgen LVS comparison against an independent schematic netlist;
- typed net and route-group constraints;
- a common route-plan and routing-metrics model;
- general multi-terminal routing;
- symmetry-constrained and matched-length routing;
- channel assignment for several simultaneous nets;
- routing congestion and route-to-route obstacle handling.
