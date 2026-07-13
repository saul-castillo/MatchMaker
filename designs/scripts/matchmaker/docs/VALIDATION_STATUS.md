# Validation status

## Confirmed in the Chipathon `/foss` container

- MatchMaker environment setup loads successfully.
- Original 10 routing-planner and verification-parser unit tests passed.
- The centroid routing demo generated a GDS successfully.
- The original generated route selected the straight route family.
- GF180 Magic loaded the target GDS and reported zero DRC violations.
- The corrected DRC adapter returned `passed=True` and `violation_count=0`.
- Magic successfully extracted the routed centroid GDS to SPICE.
- Extracted connectivity showed the original straight route net on four top-level instances: both intended A devices and both intervening B devices. The route was DRC-clean but electrically wrong.

## Added after that container run

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
- same-facing blocked routes converted to C-route detours;
- fail-safe rejection for blocked opposite-facing inline routes until a general channel detour is implemented.

The pure unit-test workflow passes on GitHub. The new obstacle-aware physical route still requires a fresh pull and `/foss` rerun before it should be treated as integration-validated.

## Not yet demonstrated

- a DRC-clean and extraction-confirmed obstacle-aware reroute of the centroid demo;
- confirmation that the new route net appears on only the two intended A instances;
- a passing Netgen LVS comparison against an independent schematic netlist;
- general obstacle-aware routing for opposite-facing ports, multi-terminal nets, and symmetry-constrained nets.
