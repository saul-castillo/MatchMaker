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

    cell_name = "nfet_4x4_custom_centroid_placement"

    group_grid = [
        ["A", "B", "A", "B"],
        ["B", "A", "B", "A"],
        ["B", "A", "B", "A"],
        ["A", "B", "A", "B"],
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
        pattern="ABBA",
    )

    plan = make_custom_centroid_plan(
        cell_name=spec.cell_name,
        group_grid=group_grid,
    )

    print("Custom pattern:")
    print(plan.pretty_pattern())
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
    print(f"Wrote custom NFET placement-only GDS: {paths.final_gds}")


if __name__ == "__main__":
    main()