from pathlib import Path
import sys

DESIGNS_ROOT = Path("/foss/designs")
MATCHMAKER_ROOT = DESIGNS_ROOT / "scripts" / "matchmaker"

sys.path.insert(0, str(MATCHMAKER_ROOT))

from glayout import gf180

from engine.spec import DeviceSpec, CentroidArraySpec
from engine.mos_centroid_grid_compiler import (
    compile_mos_centroid_grid_to_placement_request,
)
from engine.mos_centroid_placement_builder import (
    build_mos_centroid_placement_from_request,
)
from engine.mos_centroid_spacing_policy import MosCentroidSpacingPolicy
from engine.core_analog_cell_paths import create_core_analog_cell_paths


def main():
    gf180.activate()

    cell_name = "nfet_centroid_from_grid_compiler"

    group_grid = [
        ["A", "B", "D", "D", "B", "A"],
        ["B", "A", "D", "D", "A", "B"],
    ]

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

    spec = CentroidArraySpec(
        cell_name=cell_name,
        device_a=nfet_a,
        device_b=nfet_b,
        rows=len(group_grid),
        cols=len(group_grid[0]),
        pattern="custom",
    )

    request = compile_mos_centroid_grid_to_placement_request(
        spec=spec,
        group_grid=group_grid,
        spacing_policy=MosCentroidSpacingPolicy(
            kind="bbox_plus_margin",
            x_margin=2.0,
            y_margin=2.0,
        ),
    )

    print("Compiled pattern:")
    print(request.plan.pretty_pattern())
    print()
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
    print(f"Wrote grid-compiled NFET centroid placement: {paths.final_gds}")


if __name__ == "__main__":
    main()