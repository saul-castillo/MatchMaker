from pathlib import Path
import sys

DESIGNS_ROOT = Path("/foss/designs")
MATCHMAKER_ROOT = DESIGNS_ROOT / "scripts" / "matchmaker"

sys.path.insert(0, str(MATCHMAKER_ROOT))

from glayout import gf180

from engine.spec import DeviceSpec, CentroidArraySpec
from engine.patterns import make_abba_plan
from engine.mos_centroid_placement_builder import build_mos_centroid_placement
from engine.core_analog_cell_paths import create_core_analog_cell_paths


def main():
    gf180.activate()

    cell_name = "nfet_2x4_centroid_placement"

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
        rows=2,
        cols=4,
        pattern="ABBA",
    )

    plan = make_abba_plan(
        cell_name=spec.cell_name,
        rows=spec.rows,
        cols=spec.cols,
    )

    top = build_mos_centroid_placement(spec, plan)

    paths = create_core_analog_cell_paths(
    designs_root=DESIGNS_ROOT,
    cell_name=cell_name,
    )

    top.write_gds(str(paths.final_gds))

    print()
    print(f"Wrote NFET placement-only GDS: {paths.final_gds}")


if __name__ == "__main__":
    main()