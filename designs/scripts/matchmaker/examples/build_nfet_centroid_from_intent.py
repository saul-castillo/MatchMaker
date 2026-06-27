from pathlib import Path
import sys

DESIGNS_ROOT = Path("/foss/designs")
MATCHMAKER_ROOT = DESIGNS_ROOT / "scripts" / "matchmaker"

sys.path.insert(0, str(MATCHMAKER_ROOT))

from glayout import gf180

from engine.spec import DeviceSpec
from engine.mos_centroid_array_intent import MosCentroidArrayIntent
from engine.mos_centroid_intent_compiler import (
    compile_mos_centroid_intent_to_grid,
    compile_mos_centroid_intent_to_placement_request,
)
from engine.mos_centroid_placement_builder import (
    build_mos_centroid_placement_from_request,
)
from engine.core_analog_cell_paths import create_core_analog_cell_paths


def main():
    gf180.activate()

    cell_name = "nfet_centroid_from_intent"

    nfet_a = DeviceSpec(
        name="A",
        kind="nfet",
        width=3.0,
        length=None,
        fingers=1,
    )

    nfet_b = DeviceSpec(
        name="B",
        kind="nfet",
        width=3.0,
        length=None,
        fingers=1,
    )

    intent = MosCentroidArrayIntent(
        cell_name=cell_name,
        device_a=nfet_a,
        device_b=nfet_b,
        rows=2,
        cols=6,
        pattern_style="abba",
        dummy_tile_strategy="center_pair",
    )

    group_grid = compile_mos_centroid_intent_to_grid(intent)

    print("Intent-generated grid:")
    for row in group_grid:
        print(" ".join(row))
    print()

    request = compile_mos_centroid_intent_to_placement_request(intent)

    print("Compiled tiles:")
    print(request.plan.describe_tiles())
    print()

    top = build_mos_centroid_placement_from_request(request)

    paths = create_core_analog_cell_paths(
        designs_root=DESIGNS_ROOT,
        cell_name=cell_name,
    )

    top.write_gds(str(paths.final_gds))

    print()
    print(f"Wrote intent-based NFET centroid placement: {paths.final_gds}")


if __name__ == "__main__":
    main()