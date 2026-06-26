from pathlib import Path
import sys

DESIGNS_ROOT = Path("/foss/designs")
MATCHMAKER_ROOT = DESIGNS_ROOT / "scripts" / "matchmaker"

sys.path.insert(0, str(MATCHMAKER_ROOT))

from glayout import gf180

from engine.spec import DeviceSpec, CentroidArraySpec
from engine.custom_centroid_pattern_planner import make_custom_centroid_plan
from engine.mos_centroid_placement_builder import build_mos_centroid_placement
from engine.core_analog_cell_paths import create_core_analog_cell_paths


def main():
    gf180.activate()

    cell_name = "nfet_centroid_with_dummy_tiles"

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

    plan = make_custom_centroid_plan(
        cell_name=spec.cell_name,
        group_grid=group_grid,
    )

    print("Pattern:")
    print(plan.pretty_pattern())
    print()
    print("Tiles:")
    print(plan.describe_tiles())
    print()

    top = build_mos_centroid_placement(
        spec=spec,
        plan=plan,
    )

    paths = create_core_analog_cell_paths(
        designs_root=DESIGNS_ROOT,
        cell_name=cell_name,
    )

    top.write_gds(str(paths.final_gds))

    print()
    print(f"Wrote NFET centroid with dummy tiles: {paths.final_gds}")


if __name__ == "__main__":
    main()