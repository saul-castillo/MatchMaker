# MatchMaker

MatchMaker is a deterministic, constraint-driven analog layout automation project for the SSCS Chipathon Track D analog/LLM flow. The project targets GF180 through gLayout and is being developed toward reusable matched MOS structures, switch networks, capacitor arrays, CDACs, and larger verified analog cells.

## Current flow

```text
structured layout intent
→ deterministic placement plan
→ GF180 primitive placement
→ physical terminal access and obstacle metadata
→ point-to-point route planning
→ route geometry
→ GDS
→ Magic DRC
→ Magic SPICE extraction
→ connectivity inspection
→ Netgen LVS infrastructure
```

The current integration milestone demonstrates a MOS centroid array with an obstacle-aware gate connection. The engine rejects a direct route that would cross unrelated devices, selects outward gate access, builds an explicit spatial dogleg outside the array, passes GF180 Magic DRC, and extracts a routed node connected to exactly the two intended devices.

This is a verified point-to-point routing slice. General multi-terminal routing, matched routing, differential routing, multi-net congestion handling, and a passing independent schematic LVS comparison remain future work.

## Start here

Before changing the engine, read:

```text
designs/scripts/matchmaker/docs/ENGINEERING_MAP.md
```

That document defines the pipeline, package ownership, dependency rules, known architectural debt, and development order. Durable design decisions are recorded under:

```text
designs/scripts/matchmaker/docs/adr/
```

The accepted routing architecture is documented in:

```text
designs/scripts/matchmaker/docs/adr/0001-constraint-driven-hybrid-routing.md
```

## Working principle

MatchMaker separates logical connectivity from physical access. A logical terminal such as `A0.gate` may have several physical access candidates such as east or west gate ports. Routing should select access points, topology, channels, layers, widths, and detailed segments from typed constraints and a physical-design snapshot rather than from fixed procedural geometry.

The routing architecture is hybrid:

```text
straight route
→ simple Manhattan family
→ explicit spatial dogleg/channel
→ coarse routing-graph search
→ multi-terminal topology routing
→ negotiated multi-net routing
```

Analog-specific templates and graph-search strategies will share a common route-plan and verification contract.

## Run the current routing and verification demo

Inside the Chipathon container:

```bash
cd /foss/designs
source scripts/matchmaker/env/setup.sh
python scripts/matchmaker/examples/routing/route_two_centroid_gates.py
```

The command generates the routed GDS, runs DRC, extracts SPICE, and writes reports.

Inspect extracted connectivity with:

```bash
python scripts/matchmaker/examples/verification/inspect_extracted_netlist.py nfet_centroid_gate_route_demo
```

Run the pure Python tests with:

```bash
python -m unittest discover -s scripts/matchmaker/tests -v
```

## Repository structure

```text
designs/
  libs/
    core_analog/
      <generated_cell_name>/
        gds/
        netlist/
        reports/
          drc/
          extraction/
          lvs/

  scripts/
    matchmaker/
      env/
      examples/
        placement/
        routing/
        verification/
      docs/
        ENGINEERING_MAP.md
        VALIDATION_STATUS.md
        placement_engine.md
        routing_verification_foundation.md
        adr/
      src/
        matchmaker/
          specs/
          placement/
          primitives/
          routing/
          verification/
          outputs/
      tests/
```

The Python package lives under:

```text
designs/scripts/matchmaker/src/matchmaker/
```

Generated circuit artifacts live under:

```text
designs/libs/core_analog/
```

## Package ownership

`specs/` contains PDK-independent device specifications.

`placement/core/` contains reusable tile, plan, orientation, and spacing infrastructure.

`placement/mos/` contains MOS-specific intent compilation, dummy handling, device binding, and placement construction.

`primitives/` contains PDK/gLayout primitive factories.

`routing/intents/`, `routing/ports/`, `routing/planners/`, and `routing/routers/` currently implement the first routing slice. The promoted-port and `Component.info` metadata interfaces are transitional and will migrate toward an explicit physical-design snapshot.

`verification/` contains Magic DRC, Magic extraction, Netgen LVS, process execution, and SPICE connectivity inspection.

`outputs/` owns generated artifact paths.

`examples/` should contain package wiring only, not reusable engine logic.

## Architectural rules

- Keep high-level intent and pure planners independent of gLayout, Magic, and Netgen.
- Do not add routing policy to placement builders or examples.
- Separate logical terminals from physical access points.
- Treat electrical, geometric, matching, symmetry, and separation requirements as typed constraints.
- Filter candidates by hard constraints before ranking soft costs.
- DRC success is not connectivity success; extraction or LVS must verify electrical intent.
- Record major architectural decisions in `docs/adr/`.
- Update `docs/VALIDATION_STATUS.md` only with results demonstrated in the `/foss` environment.

## Near-term roadmap

```text
1. automatic extracted-connectivity assertions
2. typed PlacementResult / PhysicalDesignSnapshot
3. logical TerminalRef and AccessPoint models
4. typed net and route-group constraints
5. common RoutePlan and routing metrics
6. routing-strategy dispatcher
7. multi-terminal topology planning
8. matched and differential routing
9. congestion-aware multi-net routing
10. independent schematic LVS and repair feedback
11. capacitor-array and CDAC routing templates
```

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
