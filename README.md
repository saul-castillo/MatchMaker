# MatchMaker

MatchMaker is a deterministic, constraint-driven analog layout automation project for the SSCS Chipathon Track D analog/LLM flow. The project targets GF180 through gLayout and is being developed toward reusable matched MOS structures, switch networks, capacitor arrays, CDACs, and larger verified analog cells.

## Current flow

```text
structured layout intent
→ deterministic placement plan
→ GF180 primitive placement
→ typed physical-design snapshot
→ point-to-point route planning
→ route geometry
→ GDS
→ Magic DRC
→ Magic SPICE extraction
→ automatic connectivity assertion
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

The command generates the routed GDS, runs DRC, extracts SPICE, and fails unless the extracted route net has exactly the expected two endpoint participants.

Inspect extracted connectivity manually with:

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
          connectivity/
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
          physical/
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

`physical/` contains typed placed-instance, logical-terminal, physical-access, obstacle, and physical-design snapshot models. Its MOS centroid adapter is transitional until placement builders return stable instance bindings directly.

`primitives/` contains PDK/gLayout primitive factories.

`routing/intents/`, `routing/ports/`, `routing/planners/`, and `routing/routers/` implement the first routing slice. New routing work should consume `PhysicalDesignSnapshot`; promoted ports and `Component.info` remain compatibility adapters only.

`verification/` contains Magic DRC, Magic extraction, Netgen LVS, process execution, SPICE inspection, and extracted-connectivity assertions.

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

Completed architectural foundation:

```text
✓ automatic extracted-connectivity assertions
✓ typed PhysicalDesignSnapshot
✓ logical TerminalRef and physical AccessPoint models
```

Next development order:

```text
1. typed net and route-group constraints
2. common RoutePlan and routing metrics
3. routing-strategy dispatcher
4. multi-terminal topology planning
5. matched and differential routing
6. congestion-aware multi-net routing
7. independent schematic LVS and repair feedback
8. capacitor-array and CDAC routing templates
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
