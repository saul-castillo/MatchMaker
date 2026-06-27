# MatchMaker

MatchMaker is a spec-driven analog layout automation project for the SSCS Chipathon Track D analog/LLM flow. The project focuses on deterministic generation of matched analog structures in GF180 using gLayout.

The current milestone is a package-based placement engine for MOS centroid arrays. It translates structured layout intent into an internal tile plan, instantiates GF180 MOS primitives, and writes GDS output into the Chipathon template library structure.

## Overview

Analog layout depends heavily on matching, symmetry, orientation, proximity, and later routing balance. MatchMaker addresses the placement portion of that problem first by generating matched-device arrays programmatically rather than placing each unit device by hand.

The current flow is:

```text
MOS centroid intent
→ internal tile grid
→ placement request
→ GF180 MOS primitive placement
→ GDS output
```

This is placement-only. Routing, pin labeling, DRC, LVS, and feedback-driven iteration are planned as separate modules.

## Current Status

The current engine supports MOS centroid placement from high-level intent or explicit custom grids. It handles active, dummy, and empty tile roles; group-to-device binding; orientation policies; spacing policies; primitive-level dummy policies; and explicit GF180 MOS primitive options.

The main working demo is:

```bash
cd /foss/designs
source scripts/matchmaker/env/setup.sh
python scripts/matchmaker/examples/placement/build_nfet_centroid_from_intent.py
```

Generated layouts are written under:

```text
designs/libs/core_analog/<cell_name>/gds/
```

## Repository Structure

```text
designs/
  libs/
    core_analog/
      <generated_cell_name>/
        gds/
        netlist/
        reports/
          drc/
          lvs/

  scripts/
    matchmaker/
      env/
        setup.sh

      examples/
        placement/
          build_nfet_centroid_from_intent.py

      docs/
        placement_engine.md

      src/
        matchmaker/
          specs/
          placement/
          primitives/
          outputs/
          routing/
          verification/
```

The Python package lives under:

```text
designs/scripts/matchmaker/src/matchmaker/
```

Generated circuit artifacts live under:

```text
designs/libs/core_analog/
```

## Package Layout

```text
matchmaker/
  specs/
    mos_device_spec.py
    mos_centroid_array_spec.py

  placement/
    core/
      tile_plan.py
      orientation_policy.py
      spacing_policy.py
      custom_grid_planner.py

    mos/
      mos_centroid_array_intent.py
      mos_centroid_intent_compiler.py
      mos_centroid_grid_compiler.py
      mos_centroid_placement_request.py
      mos_centroid_placement_builder.py
      mos_dummy_policy.py
      mos_group_device_binding.py

    capacitors/
    resistors/

  primitives/
    gf180_mos_primitive_factory.py
    gf180_mos_primitive_options.py

  outputs/
    core_analog_cell_paths.py

  routing/
    intents/
    planners/
    routers/

  verification/
    drc/
    lvs/
    feedback/
```

## Architecture

`specs/` defines structured descriptions of devices and resolved array specifications.

`placement/core/` contains reusable placement infrastructure: tiles, placement plans, orientation policies, spacing policies, and grid conversion. This layer is intentionally not MOS-specific.

`placement/mos/` contains MOS-specific centroid placement logic, including intent compilation, dummy handling, group-to-device binding, and the MOS placement builder.

`primitives/` creates PDK-specific geometry. The current implementation targets GF180 MOS primitives through gLayout.

`outputs/` manages generated file paths.

`routing/` and `verification/` are reserved for the next major stages: smart routing, DRC/LVS execution, report parsing, and feedback-driven layout iteration.

## Design Direction

MatchMaker is intended to grow as a structured generator. High-level intent should describe what is needed. Deterministic planners should translate that intent into spatial representations. Builders should instantiate geometry. Verification modules should eventually close the loop.

The tile grid is an internal placement representation. It is useful because placement is spatial, but it is not intended to be the only long-term interface. Standard placement strategies and explicit custom grids are both supported.

## Current Limitations

The engine does not yet perform routing, top-level pin creation, DRC, LVS, verification feedback, capacitor-array generation, resistor-array generation, or CDAC layout generation.

Guard-ring or tap geometry may appear in generated GDS through the underlying GF180/gLayout MOS primitive behavior. MatchMaker does not yet implement an explicit array-level isolation policy.

## Near-Term Roadmap

The next development stage is to stabilize the placement strategy interface, add explicit isolation policy, add PFET demos, and begin the routing-intent layer. DRC/LVS runners and feedback parsing should follow after the routing interface is defined.

Longer-term targets include matched transistor subblocks, capacitor arrays, CDAC layout support, and reusable verified analog layout cells.

## Team

Team Los Pollos Hermanos
SSCS Chipathon Track D: AI and LLM for Analog Circuits

| Name / Handle | GitHub         | Affiliation              | Role                                |
| ------------- | -------------- | ------------------------ | ----------------------------------- |
| s_a_castillo  | @saul-castillo | Brown University, EE '28 | Team Lead and Layout Automation     |
| Zeke_956      | @zeke956       | Brown University, EE '28 | DRC/LVS Verification Support        |
| .nthony       | @nthony237     | Brown University, ME '28 | LLM & Natural Language Integration  |

## Links

* [Chipathon issue 70](https://github.com/sscs-ose/sscs-chipathon-2026/issues/70)
* [MatchMaker repository](https://github.com/saul-castillo/MatchMaker)
