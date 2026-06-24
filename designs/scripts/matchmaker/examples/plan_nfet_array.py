from pathlib import Path
import sys

DESIGNS_ROOT = Path("/foss/designs")
MATCHMAKER_ROOT = DESIGNS_ROOT / "scripts" / "matchmaker"

sys.path.insert(0, str(MATCHMAKER_ROOT))

from engine.spec import DeviceSpec, CentroidArraySpec
from engine.patterns import make_abba_plan


def main():
    nfet_a = DeviceSpec(
        name="A",
        kind="nfet",
        width=3.0,
        length=0.28,
        fingers=1,
    )

    nfet_b = DeviceSpec(
        name="B",
        kind="nfet",
        width=3.0,
        length=0.28,
        fingers=1,
    )

    spec = CentroidArraySpec(
        cell_name="nfet_2x4_centroid",
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

    print(f"Cell: {spec.cell_name}")
    print(f"Device kind: {spec.device_a.kind}")
    print()
    print("Pattern:")
    print(plan.pretty_pattern())
    print()
    print("Tiles:")
    print(plan.describe_tiles())


if __name__ == "__main__":
    main()