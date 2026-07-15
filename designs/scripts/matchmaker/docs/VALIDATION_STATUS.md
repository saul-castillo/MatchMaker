# Validation status

## Confirmed in the Chipathon `/foss` container

- MatchMaker environment setup loads successfully.
- Routing-planner and verification-parser unit tests passed.
- The centroid routing demo generated GDS successfully.
- GF180 Magic loaded the target GDS and reported zero DRC violations.
- The DRC adapter returned `passed=True` and `violation_count=0`.
- Magic extracted the routed centroid GDS to SPICE.
- The original straight route was DRC-clean but connected both intended A devices and both intervening B devices.
- Bounding-box obstacle detection identified `B0` and `B1`.
- The first layer-only C-route remained electrically wrong.
- The attempted north/south access fallback failed safely because the installed GF180 primitive did not expose usable `gate_N` or `gate_S` ports.
- The explicit spatial dogleg generated a visibly external route using outward endpoint access.
- The spatial dogleg passed GF180 Magic DRC with zero violations.
- Extraction showed the dogleg route net on exactly the two intended A instances, with no B-device connection.
- The snapshot-backed one-command demo ran successfully with automatic connectivity gating and reported `connectivity passed: True` and `pre-LVS checks passed: True`.

## Cleanup added after the latest `/foss` run

The branch cleanup now also:

- removes the stale routing document that described the failed north/south C-route;
- removes the unused `routing/ports` compatibility package;
- removes the obsolete C-route fallback function and its tests;
- removes duplicate and mapping-based obstacle representations;
- makes `PhysicalDesignSnapshot` mappings read-only and internally validated;
- requires route execution to receive an explicit snapshot;
- removes routing dependence on `Component.info` metadata;
- updates tests and architecture documentation to match the cleaned boundaries.

These cleanup changes require one final `/foss` demo rerun before merge. The pure-test and compilation workflow must also pass at the cleanup head.

## Current implemented foundation

- deterministic MOS centroid placement;
- stable physical access naming;
- typed, read-only physical-design snapshot;
- snapshot-required point-to-point route execution;
- typed obstacle detection;
- explicit same-layer spatial dogleg routing;
- GF180 Magic DRC;
- Magic SPICE extraction;
- automatic extracted-connectivity checks;
- Netgen LVS runner infrastructure;
- structured artifact paths, reports, and failure results.

## Not yet demonstrated

- a fresh `/foss` rerun after the final cleanup refactor;
- a passing Netgen LVS comparison against an independent schematic netlist;
- logical `NetIntent` and automatic physical access selection;
- typed net and route-group constraints;
- a common route-plan and routing-metrics model;
- general multi-terminal routing;
- symmetry-constrained and matched-length routing;
- channel assignment for simultaneous nets;
- routing congestion and route-to-route obstacle handling.
