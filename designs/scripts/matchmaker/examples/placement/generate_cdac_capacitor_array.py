import argparse
import os
from collections import Counter
from pathlib import Path

from glayout import gf180

from matchmaker.design.cdac_manifest_compiler import compile_banked_cdac_manifest
from matchmaker.outputs.core_analog_cell_paths import create_core_analog_cell_paths
from matchmaker.physical.cdac_capacitor_snapshot import (
    create_cdac_capacitor_array_physical_design_snapshot,
)
from matchmaker.physical.models import TerminalRef
from matchmaker.placement.cdac.capacitor_array_builder import (
    build_cdac_capacitor_array,
)
from matchmaker.placement.cdac.capacitor_array_intent import (
    CdacCapacitorArrayIntent,
)
from matchmaker.specs.banked_cdac_spec import (
    make_gf180_4bit_banked_cdac_reference_spec,
)
from matchmaker.verification.drc.magic_drc import run_magic_drc


DEFAULT_CELL_NAME = "cdac_4b_banked_capacitor_array_demo"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the typed 4-bit reference preset's capacitor-array "
            "placement, capture its physical snapshot, and run GF180 Magic DRC."
        )
    )
    parser.add_argument(
        "--designs-root",
        type=Path,
        default=Path(os.environ.get("DESIGNS_ROOT", "/foss/designs")),
    )
    parser.add_argument("--cell-name", default=DEFAULT_CELL_NAME)
    parser.add_argument("--skip-drc", action="store_true")
    args = parser.parse_args()

    gf180.activate()
    spec = make_gf180_4bit_banked_cdac_reference_spec(
        cell_name=f"{args.cell_name}_logical"
    )
    manifest = compile_banked_cdac_manifest(spec)
    intent = CdacCapacitorArrayIntent(
        spec=spec,
        manifest=manifest,
        cell_name=args.cell_name,
    )
    placement = build_cdac_capacitor_array(intent)
    physical_design = create_cdac_capacitor_array_physical_design_snapshot(
        placement
    )
    paths = create_core_analog_cell_paths(args.designs_root, args.cell_name)
    placement.component.write_gds(paths.final_gds)

    group_counts = Counter(tile.group for tile in placement.plan.tiles)
    first_instance_name = placement.plan.tiles[0].name
    first_top = physical_design.access_points_for(
        TerminalRef(first_instance_name, "top")
    )
    first_bottom = physical_design.access_points_for(
        TerminalRef(first_instance_name, "bottom")
    )

    print(f"generated cell: {args.cell_name}")
    print(f"grid shape: {placement.plan.rows} x {placement.plan.cols}")
    print(f"capacitor instances: {len(placement.bindings)}")
    print(f"group counts: {dict(sorted(group_counts.items()))}")
    print("placement pattern:")
    print(placement.plan.pretty_pattern())
    print(f"physical instances: {len(physical_design.instances)}")
    print(f"physical access points: {len(physical_design.access_points)}")
    print(f"routing obstacles: {len(physical_design.obstacles)}")
    print(f"example top access count: {len(first_top)}")
    print(f"example bottom access count: {len(first_bottom)}")
    print(f"example top layers: {sorted({access.layer for access in first_top}, key=str)}")
    print(
        "example bottom layers: "
        f"{sorted({access.layer for access in first_bottom}, key=str)}"
    )
    print(f"GDS: {paths.final_gds}")

    if args.skip_drc:
        return 0

    drc = run_magic_drc(
        gds_path=paths.final_gds,
        cell_name=args.cell_name,
        report_path=paths.drc_report,
    )
    print(f"DRC passed: {drc.passed}")
    print(f"DRC violations: {drc.violation_count}")
    print(f"DRC report: {drc.report_path}")
    return 0 if drc.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
