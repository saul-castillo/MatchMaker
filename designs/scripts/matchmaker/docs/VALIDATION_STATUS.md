# Validation status

## Confirmed in the Chipathon `/foss` container

- MatchMaker environment setup loads successfully.
- Original routing-planner and verification-parser unit tests passed.
- The centroid routing demo generated GDS successfully.
- GF180 Magic loaded the target GDS and reported zero DRC violations.
- The corrected DRC adapter returned `passed=True` and `violation_count=0`.
- Magic successfully extracted the routed centroid GDS to SPICE.
- The original straight route net appeared on four top-level instances: both intended A devices and both intervening B devices. It was DRC-clean but electrically wrong.
- Bounding-box obstacle detection correctly identified `B0` and `B1`.
- The first C-route fallback remained electrically wrong: extraction still showed the routed node on the same four instances.
- The attempted north/south access fallback failed safely because the installed GF180 gate primitive did not expose usable `gate_N` or `gate_S` ports.

## Added after the latest container run

The branch now also includes:

- automatic `PDK` and `PDK_ROOT` subprocess configuration;
- standalone Magic layout extraction;
- one-call generated-cell DRC and extraction;
- automatic GF180 Netgen setup-file resolution;
- one-command LVS and extracted-netlist inspection CLIs;
- shared-net summaries for extracted top-level instances;
- structured missing-executable and timeout failures;
- expanded pure unit tests and a GitHub Actions workflow;
- obstacle metadata recorded from placed tile bounding boxes;
- automatic rejection of blocked straight routes;
- an explicit same-layer spatial dogleg route;
- outward access selection using `gate_W` on the left endpoint and `gate_E` on the right endpoint;
- vertical legs placed beyond the full array x-envelope;
- a horizontal channel placed above or below the full array y-envelope;
- fail-safe rejection when an endpoint cannot reach the outside channel.

The spatial-dogleg physical route requires a fresh pull and `/foss` rerun before it should be treated as integration-validated.

## Not yet demonstrated

- a DRC-clean spatial dogleg reroute of the centroid demo;
- extraction showing the rerouted net on only the two intended A instances;
- a passing Netgen LVS comparison against an independent schematic netlist;
- general multi-terminal, symmetry-constrained, and channel-assignment routing.
