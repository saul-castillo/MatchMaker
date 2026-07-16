# MatchMaker

MatchMaker is a deterministic, constraint-driven analog layout synthesis project for the SSCS Chipathon Track D analog/LLM flow. It targets GF180 through gLayout and is being developed toward reusable matched MOS structures, switch networks, capacitor arrays, CDACs, comparators, and larger verified analog cells.

## Current validated flow

```text
structured device and placement intent
-> deterministic GF180 placement
-> PhysicalDesignSnapshot
-> logical NetIntent and typed constraints
-> modular routing-strategy dispatch
-> selected RouteCandidate
-> execution-ready RoutePlan
-> mechanical route geometry
-> GDS
-> Magic DRC
-> Magic SPICE extraction
-> exact connectivity assertion
-> Netgen LVS infrastructure
```

The current two-terminal, same-layer router supports clear straight routes, non-inline Manhattan L/Z routes, and external obstacle-avoiding doglegs. Both the blocked A0-to-A1 dogleg and diagonal A0-to-A2 Manhattan regressions pass GF180 DRC, extraction, and exact connectivity checks.

## Start here

Before changing the engine, read:

```text
designs/scripts/matchmaker/docs/ENGINEERING_MAP.md
designs/scripts/matchmaker/docs/VALIDATION_STATUS.md
designs/scripts/matchmaker/docs/adr/
```

`ENGINEERING_MAP.md` is the canonical live-state document. `VALIDATION_STATUS.md` records only physical results demonstrated in the Chipathon `/foss` environment. ADRs preserve durable architectural decisions.

For repository, circuit-library, and documentation placement, read:

- [Project documentation map](docs/project_documentation_map.md)
- [Core MatchMaker reference library](designs/libs/core_matchmaker/README.md)
- [Current 4-bit banked CDAC reference](designs/libs/core_matchmaker/7D_cdac_4b_banked_scaled_selectors/README.md)

## Run the regressions

Inside the Chipathon container:

```bash
cd /foss/designs
source scripts/matchmaker/env/setup.sh
python -m unittest discover -s scripts/matchmaker/tests -v
```

Blocked dogleg regression:

```bash
python scripts/matchmaker/examples/routing/route_two_centroid_gates.py
```

Diagonal Manhattan regression:

```bash
python scripts/matchmaker/examples/routing/route_two_centroid_gates.py \
  --cell-name nfet_centroid_diagonal_gate_route_demo \
  --source-instance A0 \
  --target-instance A2
```

Each routing command generates GDS, runs DRC, extracts SPICE, and exits nonzero unless the routed net contains exactly the expected endpoint instances.

## Repository layout

```text
designs/
  libs/core_matchmaker/<reference_cell>/
    <reference_cell>.sch
    <reference_cell>.sym

  libs/tb_matchmaker/<testbench>/
    <testbench>.sch

  libs/core_analog/<generated_cell>/
    gds/
    netlist/
    reports/{drc,extraction,connectivity,lvs}/

  scripts/matchmaker/
    docs/
    env/
    examples/
    src/matchmaker/
      outputs/
      physical/
      placement/
      primitives/
      routing/
      specs/
      verification/
    tests/
```

The Python package lives under `designs/scripts/matchmaker/src/matchmaker/`. Hand-authored reference circuits and testbenches live under `designs/libs/core_matchmaker/` and `designs/libs/tb_matchmaker/`. Generated cell artifacts live under `designs/libs/core_analog/`.

## Working principle

Logical connectivity is separate from physical access. Callers request terminals such as `A0.gate`; the router evaluates available physical accesses, obstacles, constraints, and strategy candidates before producing geometry.

MatchMaker uses common intent, snapshot, candidate, plan, execution, and verification contracts with specialized physical adapters and routing strategies. Device-specific knowledge belongs in adapters. Analog-specific topology belongs in strategy modules. Executors only draw resolved plans.

## Current boundary

Implemented and physically validated:

- deterministic MOS centroid placement;
- filtered typed physical-design snapshots;
- logical two-terminal net intent and typed constraints;
- deterministic strategy dispatch with rejection evidence;
- same-layer straight, Manhattan L/Z, and external-dogleg routing;
- route metrics and provenance;
- GF180 Magic DRC and extraction;
- exact extracted-connectivity assertions.

Not yet implemented or demonstrated:

- committed routes as obstacles/resources;
- GF180 width/layer/via rule resolution;
- via planning and execution;
- multi-terminal topology planning;
- matched, differential, shielding, and separation group planning;
- congestion-aware graph routing;
- a passing independent schematic-to-layout LVS regression;
- capacitor/CDAC physical adapters and routing templates.

## Team

Team Los Pollos Hermanos  
SSCS Chipathon Track D: AI and LLM for Analog Circuits

| Name / Handle | GitHub | Affiliation | Role |
| --- | --- | --- | --- |
| s_a_castillo | @saul-castillo | Brown University, EE '28 | Team Lead and Layout Automation |
| Zeke_956 | @zeke956 | Brown University, EE '28 | DRC/LVS Verification Support |
| .nthony | @nthony237 | Brown University, ME '28 | LLM & Natural Language Integration |

## Links

- [Chipathon issue 70](https://github.com/sscs-ose/sscs-chipathon-2026/issues/70)
- [MatchMaker repository](https://github.com/saul-castillo/MatchMaker)
