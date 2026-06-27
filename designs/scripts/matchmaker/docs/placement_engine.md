# Placement Engine Guide

This guide explains how to use the current MatchMaker placement engine.

The engine currently builds MOS centroid placements. You provide structured intent, the compiler produces a tile-based placement request, and the builder returns a gLayout component that can be written to GDS.

## Basic Flow

```text
MosCentroidArrayIntent
→ compile_mos_centroid_intent_to_placement_request(...)
→ build_mos_centroid_placement_from_request(...)
→ top.write_gds(...)
```

Use this interface unless you are modifying placement internals.

## Run the Demo

Inside the container:

```bash
cd /foss/designs
source scripts/matchmaker/env/setup.sh
python scripts/matchmaker/examples/placement/build_nfet_centroid_from_intent.py
```

The demo writes output to:

```text
designs/libs/core_analog/nfet_centroid_from_intent/gds/
```

## Minimal Example

```python
from pathlib import Path

from glayout import gf180

from matchmaker.outputs.core_analog_cell_paths import create_core_analog_cell_paths
from matchmaker.placement.mos.mos_centroid_array_intent import MosCentroidArrayIntent
from matchmaker.placement.mos.mos_centroid_intent_compiler import (
    compile_mos_centroid_intent_to_placement_request,
)
from matchmaker.placement.mos.mos_centroid_placement_builder import (
    build_mos_centroid_placement_from_request,
)
from matchmaker.specs.mos_device_spec import MosDeviceSpec


DESIGNS_ROOT = Path("/foss/designs")

gf180.activate()

nfet_a = MosDeviceSpec(
    name="A",
    kind="nfet",
    width=3.0,
    length=None,
    fingers=1,
)

nfet_b = MosDeviceSpec(
    name="B",
    kind="nfet",
    width=3.0,
    length=None,
    fingers=1,
)

intent = MosCentroidArrayIntent(
    cell_name="example_nfet_centroid",
    device_a=nfet_a,
    device_b=nfet_b,
    rows=2,
    cols=6,
    pattern_strategy="common centroid",
    dummy_tile_strategy="center_pair",
)

request = compile_mos_centroid_intent_to_placement_request(intent)
top = build_mos_centroid_placement_from_request(request)

paths = create_core_analog_cell_paths(
    designs_root=DESIGNS_ROOT,
    cell_name=intent.cell_name,
)

top.write_gds(str(paths.final_gds))
```

## Input Model

You describe each MOS group with `MosDeviceSpec`.

```python
nfet_a = MosDeviceSpec(
    name="A",
    kind="nfet",
    width=3.0,
    length=None,
    fingers=1,
)
```

You describe the array with `MosCentroidArrayIntent`.

```python
intent = MosCentroidArrayIntent(
    cell_name="nfet_centroid_from_intent",
    device_a=nfet_a,
    device_b=nfet_b,
    rows=2,
    cols=6,
    pattern_strategy="common centroid",
    dummy_tile_strategy="center_pair",
)
```

The intent says what you want built. It does not directly place every device.

## Placement Strategies

You can use standard strategy names or accepted aliases. The current strategy concepts are:

```text
common_centroid
mirrored_pair
interdigitated
custom_grid
```

Accepted aliases include phrases such as:

```text
common centroid
centroid
abba
mirrored
abab
custom
explicit grid
```

This alias handling currently lives in `mos_centroid_array_intent.py`. Later versions should move strategy knowledge into a dedicated placement-strategy registry.

## Custom Grids

Use a custom grid when you need exact spatial control.

```python
intent = MosCentroidArrayIntent(
    cell_name="custom_nfet_centroid",
    device_a=nfet_a,
    device_b=nfet_b,
    pattern_strategy="custom_grid",
    group_grid=[
        ["A", "B", "D", "D", "B", "A"],
        ["B", "A", "D", "D", "A", "B"],
    ],
)
```

Rows and columns are inferred from `group_grid`. If you also provide `rows` or `cols`, they must match the grid.

## Tile Meaning

The compiler converts intent into a tile grid.

```text
A → active device group A
B → active device group B
D → dummy tile
. → empty tile
```

The grid is then converted into a placement plan. Each tile records its group, role, row, column, and orientation.

## Orientation

The current builder supports these geometric orientations:

```text
R0
MY
MX
R180
```

The builder applies geometry only. It does not rename ports. Port interpretation belongs in the future routing layer.

Current orientation policies include:

```text
mirror_top_bottom
alternate_by_row
all_r0
```

## Spacing and Dummies

Spacing is controlled by `TileSpacingPolicy`. The current modes are `bbox_plus_margin` and `fixed_pitch`.

MOS primitive dummy handling is controlled separately by `MosDummyPolicy`. The current policies are `none`, `edge_only`, and `all`.

Dummy tiles in the grid are different from primitive-level dummy devices. A `D` tile is a physical dummy tile in the array. `MosDummyPolicy` controls dummy devices attached to active MOS primitives.

## Primitive Options

Use `Gf180MosPrimitiveOptions` to make GF180 primitive-generation choices explicit.

```python
from matchmaker.primitives.gf180_mos_primitive_options import Gf180MosPrimitiveOptions

primitive_options = Gf180MosPrimitiveOptions(
    with_substrate_tap=None,
    with_tie=None,
    with_dnwell=None,
    with_guardring=None,
    sd_route_topmet=None,
    gate_route_topmet=None,
    interfinger_routing=None,
)
```

Unsupported options may be ignored by the primitive factory depending on the installed gLayout primitive signature. This is expected behavior.

## Output

The builder returns a gLayout `Component`.

Generated files are organized under:

```text
designs/libs/core_analog/<cell_name>/
  gds/
  netlist/
  reports/
    drc/
    lvs/
```

The current demo writes only GDS.

## Current Boundaries

You should not add routing logic to the placement builder. The placement layer decides where geometry goes. Routing should later consume placement metadata and handle port interpretation.

You should not put new engine logic inside examples. Examples should only show how to call the package.

The current engine does not yet support routing, pins, labels, DRC, LVS, feedback repair, capacitor arrays, resistor arrays, CDAC generation, or explicit array-level guard rings.
