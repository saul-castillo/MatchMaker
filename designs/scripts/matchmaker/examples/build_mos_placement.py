from pathlib import Path
import sys

DESIGNS_ROOT = Path("/foss/designs")
MATCHMAKER_ROOT = DESIGNS_ROOT / "scripts" / "matchmaker"

sys.path.insert(0, str(MATCHMAKER_ROOT))

from glayout import gf180

from engine.spec import DeviceSpec, CentroidArraySpec
from engine.patterns import make_abba_plan
from engine.mos_centroid_placement_builder import build_mos_centroid_placement


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

    out_dir = DESIGNS_ROOT / "libs" / "core_analog" / cell_name / "gds"
    out_dir.mkdir(parents=True, exist_ok=True)

    gds_path = out_dir / f"{cell_name}.gds"
    top.write_gds(str(gds_path))

    print()
    print(f"Wrote placement-only GDS: {gds_path}")


if __name__ == "__main__":
    main()