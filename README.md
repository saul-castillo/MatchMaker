# MatchMaker

MatchMaker is a deterministic, constraint-driven analog layout automation project for the SSCS Chipathon Track D analog/LLM flow. It targets GF180 through gLayout and is being developed toward reusable matched MOS structures, switch networks, capacitor arrays, CDACs, and larger verified analog cells.

## Current development flow

```text
structured placement intent
→ deterministic placement plan
→ GF180 primitive placement
→ typed PhysicalDesignSnapshot
→ logical NetIntent and typed constraints
→ automatic physical access selection
→ execution-ready RoutePlan
→ mechanical route geometry execution
→ GDS
→ Magic DRC
→ Magic SPICE extraction
→ automatic connectivity assertion
→ Netgen LVS infrastructure
```

The merged foundation demonstrated an obstacle-aware MOS-centroid gate route that passes GF180 DRC and extraction and connects exactly the two intended devices.

The current development branch migrates that regression from fixed physical ports to logical terminals. The example requests `A0.gate` to `A1.gate`; the planner must choose the outward physical access pair and external dogleg automatically.

Pure tests and compilation pass. The logical-intent migration still requires a fresh Chipathon `/foss` integration run before it is treated as physically validated.

## Start here

Before changing the engine, read:

```text
designs/scripts/matchmaker/docs/ENGINEERING_MAP.md
designs/scripts/matchmaker/docs/adr/0001-constraint-driven-hybrid-routing.md
designs/scripts/matchmaker/docs/VALIDATION_STATUS.md
```

The engineering map defines the current contracts, package ownership, dependency rules, known debt, and development order. Validation status distinguishes pure-test coverage from results demonstrated in the physical tool environment.

## Working principle

MatchMaker separates logical connectivity from physical access.

```text
NetIntent(A0.gate, A1.gate)
+ NetConstraintProfile
+ PhysicalDesignSnapshot
→ enumerate physical access candidates
→ reject hard-constraint violations
→ rank feasible candidates deterministically
→ RoutePlan
→ geometry executor
```

A logical terminal may expose several physical access points. High-level callers should not select `gate_E`, `gate_W`, or another concrete port before placement context is evaluated.

The routing architecture is hybrid:

```text
straight route
→ simple Manhattan family
→ explicit spatial dogleg/channel
→ coarse routing-graph search
→ multi-terminal topology routing
→ matched and differential templates
→ negotiated multi-net routing
```

All strategies will share common intent, physical-state, route-plan, metrics, execution, and verification contracts.

## Run the routing regression

Inside the Chipathon container:

```bash
cd /foss/designs
source scripts/matchmaker/env/setup.sh
python scripts/matchmaker/examples/routing/route_two_centroid_gates.py
```

The command generates GDS, runs DRC, extracts SPICE, and exits nonzero unless the route net has exactly the expected two participants.

Expected logical-routing output includes:

```text
logical terminals: A0.gate, A1.gate
route strategy: dogleg
actual source access: A0__gate_W
actual target access: A1__gate_E
DRC passed: True
extraction passed: True
connectivity passed: True
pre-LVS checks passed: True
```

Run pure tests with:

```bash
python -m unittest discover -s scripts/matchmaker/tests -v
```

Inspect an extracted netlist manually with:

```bash
python scripts/matchmaker/examples/verification/inspect_extracted_netlist.py nfet_centroid_gate_route_demo
```

## Repository structure

```text
designs/
  libs/core_analog/<generated_cell>/
    gds/
    netlist/
    reports/
      drc/
      extraction/
      connectivity/
      lvs/

  scripts/matchmaker/
    env/
    examples/
      placement/
      routing/
      verification/
    docs/
      ENGINEERING_MAP.md
      VALIDATION_STATUS.md
      placement_engine.md
      adr/
    src/matchmaker/
      specs/
      placement/
      physical/
      primitives/
      routing/
        intents/
        plans/
        planners/
        routers/
      verification/
      outputs/
    tests/
```

The Python package lives under `designs/scripts/matchmaker/src/matchmaker/`. Generated circuit artifacts live under `designs/libs/core_analog/`.

## Package ownership

`specs/` contains PDK-independent device specifications.

`placement/core/` contains reusable tile, plan, orientation, and spacing infrastructure.

`placement/mos/` contains MOS-specific intent compilation, dummy handling, device binding, and placement construction.

`physical/` contains placed-instance, logical-terminal, physical-access, obstacle, and physical-design snapshot models.

`primitives/` contains PDK/gLayout primitive factories.

`routing/intents/` contains logical net and route-group requests. The previous fixed-access point-to-point intent remains transitional compatibility code.

`routing/plans/` contains the common execution-ready route-plan and metrics intermediate representation.

`routing/planners/` contains pure access selection, obstacle checking, and route-plan compilation.

`routing/routers/` contains mechanical geometry execution adapters.

`verification/` contains Magic DRC, Magic extraction, Netgen LVS, process execution, SPICE inspection, and extracted-connectivity assertions.

`outputs/` owns generated artifact paths. `examples/` contains package wiring only.

## Architectural rules

- Keep intent and pure planners independent of gLayout, Magic, and Netgen.
- Do not add routing policy to placement builders, executors, or examples.
- Separate logical terminals from physical access points.
- Route planning consumes explicit `PhysicalDesignSnapshot` state.
- Filter candidates by hard constraints before ranking soft costs.
- Executors draw resolved plans and do not select access or topology.
- DRC success is not connectivity success; extraction or LVS must verify electrical intent.
- Record durable architecture decisions in `docs/adr/`.
- Update `VALIDATION_STATUS.md` without overstating `/foss` validation.

## Near-term roadmap

Completed in the current development branch:

```text
✓ logical NetIntent
✓ typed net and route-group constraints
✓ automatic two-terminal access selection
✓ common RoutePlan and routing metrics
✓ mechanical route-plan executor
✓ logical-terminal migration of the centroid regression
```

Next after physical validation:

```text
1. strategy dispatcher and structured candidate rejection reports
2. committed-route resources and route-to-route obstacles
3. multi-terminal topology planning
4. PDK width/layer/via rule resolution
5. matched and differential route groups
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
