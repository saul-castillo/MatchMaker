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

## Current implemented foundation

The branch includes:

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

## Not yet demonstrated

- a passing Netgen LVS comparison against an independent schematic netlist;
- automatic connectivity assertions integrated into the demo exit status;
- general multi-terminal routing;
- symmetry-constrained and matched-length routing;
- channel assignment for several simultaneous nets;
- routing congestion and route-to-route obstacle handling.
