import sys
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parents[1]
DESIGNS_ROOT = ENGINE_ROOT.parents[1]

sys.path.insert(0, str(ENGINE_ROOT))

from engine.spec import DeviceSpec, CentroidArraySpec
from engine.build_array import build_centroid_array
from engine.patterns import print_pattern


def main():
    cell_name = "nfet_2x4_centroid"

    nfet_a = DeviceSpec(
        name="A",
        kind="nfet",
        width=1.0,
        length=0.28,
        fingers=4,
    )

    nfet_b = DeviceSpec(
        name="B",
        kind="nfet",
        width=1.0,
        length=0.28,
        fingers=4,
    )

    spec = CentroidArraySpec(
        cell_name=cell_name,
        device_a=nfet_a,
        device_b=nfet_b,
        rows=2,
        cols=4,
        pattern="ABBA",
    )

    output_dir = DESIGNS_ROOT / "libs" / "core_analog" / cell_name
    result = build_centroid_array(spec, output_dir)

    print(f"Cell: {result['cell_name']}")
    print(f"Output directory: {result['output_dir']}")
    print()
    print("Generated centroid placement pattern:")
    print_pattern(result["pattern"])


if __name__ == "__main__":
    main()
