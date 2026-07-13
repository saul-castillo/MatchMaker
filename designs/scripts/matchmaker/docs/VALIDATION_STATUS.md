# Validation status

## Confirmed in the Chipathon `/foss` container

- MatchMaker environment setup loads successfully.
- Original 10 routing-planner and verification-parser unit tests passed.
- The centroid routing demo generated a GDS successfully.
- The generated route selected the straight route family.
- GF180 Magic loaded the target GDS and reported zero DRC violations.
- The corrected DRC adapter returned `passed=True` and `violation_count=0`.

## Added after that container run

The branch now also includes:

- automatic `PDK` and `PDK_ROOT` subprocess configuration;
- standalone Magic layout extraction;
- one-call generated-cell DRC and extraction;
- automatic GF180 Netgen setup-file resolution;
- one-command LVS and extracted-netlist inspection CLIs;
- structured missing-executable and timeout failures;
- expanded pure unit tests and a GitHub Actions workflow.

These additions require a fresh pull and rerun in the `/foss` container before they should be treated as integration-validated.

## Not yet demonstrated

- successful layout-to-SPICE extraction of the routed centroid demo;
- connectivity audit proving whether the straight route touches the middle B devices;
- a passing Netgen LVS comparison against an independent schematic netlist;
- obstacle-aware rerouting around non-endpoint devices.
