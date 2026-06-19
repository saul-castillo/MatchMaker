# MatchMaker

Common-centroid layout generation for matched analog structures in GF180 using gLayout.

MatchMaker is a Chipathon Track D project developed by Team Los Pollos Hermanos. The project implements a layout generator for small matched-device structures, beginning with GF180 NFET arrays and extending to matched transistor blocks such as differential pairs and current mirrors.

## Overview

Analog layout often requires devices to be placed with controlled symmetry, orientation, and proximity in order to reduce systematic mismatch. MatchMaker addresses this placement problem by generating common-centroid structures programmatically rather than placing each unit device by hand.

The first version of the generator produces parameterized NFET common-centroid arrays, including the 2-by-2 and 2-by-4 structures used for initial testing. These primitive arrays are also used to generate higher-level matched transistor blocks. The generated layouts are written through gLayout and can be inspected as GDS outputs.

The project is currently centered on reliable placement generation and layout metadata. Routing, DRC, and LVS are handled as follow-on verification steps around the generated structures.

## Implementation status

The current generator includes the base primitive flow and first matched-block flow.

| Area                                     | Status                     |
| ---------------------------------------- | -------------------------- |
| GF180 and gLayout setup                  | Complete                   |
| Parameterized NFET array generation      | Complete                   |
| 2-by-2 common-centroid primitive         | Complete                   |
| 2-by-4 common-centroid primitive         | Complete                   |
| Differential-pair style block generation | Complete                   |
| Current-mirror style block generation    | Complete                   |
| Dummy-aware placement support            | Complete                   |
| Placement and terminal metadata          | Initial version complete   |
| Routing support                          | Next milestone             |
| DRC and LVS validation                   | Next milestone             |
| Larger circuit integration               | Planned after verification |

## Generator scope

The generator currently operates on matched NFET structures in GF180. It controls the physical arrangement of unit devices, including array dimensions, placement order, device orientation, spacing, dummy placement, and exposed terminals.

The intended output is not only a visible layout, but also a repeatable layout structure that can be used as the basis for routing and verification. This keeps the project focused on the matched-device portion of analog layout before expanding into full block-level layout generation.

## Development path

The first development stage produced the primitive common-centroid array generator. This stage is implemented for the initial 2-by-2 and 2-by-4 NFET cases.

The second stage produced matched transistor blocks using the primitive array generator. This includes differential-pair and current-mirror style layouts.

The next stage is verification and integration. The main work here is routing support, port organization, regression checks, DRC, and LVS. After that, the generated blocks can be tested inside a larger analog or mixed-signal design.

Future circuit targets include LDO bias structures, comparator input-pair layouts, and CDAC or unit-capacitor array experiments.

## CDAC and SAR ADC collaboration

A possible follow-on target is a capacitor array generator for the SAR ADC group. The CDAC is a strong candidate because its layout depends heavily on matching, symmetry, array structure, and routing discipline.

Before starting that block, the required information from the ADC team is the ADC resolution, unit capacitor geometry, array topology, matching target, routing constraints, block interface, and expected handoff format.

## Repository structure

```text
.
├── README.md
├── notebooks/
│   └── generator tests and layout demos
├── scripts/
│   └── standalone generation scripts
├── src/
│   └── reusable generator code
├── layouts/
│   └── generated GDS outputs
└── docs/
    └── notes, figures, and design documentation
```

The directory structure may change as notebook experiments are moved into reusable source code.

## Team

Team Los Pollos Hermanos
Chipathon Track D
AI and LLM for Analog Circuits

| Name or Discord | Github         | Affiliation              | Role                             |
| --------------- | -------------- | ------------------------ | -------------------------------- |
| s_a_castillo    | @saul-castillo | Brown University, EE '28 | Team lead and layout automation  |
| Zeke_956        | @zeke956       | Brown University, EE '28 | DRC and LVS verification support |
| Cpg_49          | @[TBA]         | Brown University, ME '28 | Demo integration and testing     |

## Links

* [Chipathon issue 70](https://github.com/sscs-ose/sscs-chipathon-2026/issues/70)
* [MatchMaker repository](https://github.com/saul-castillo/MatchMaker)
