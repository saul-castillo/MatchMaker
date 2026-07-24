import argparse
import os
from pathlib import Path

from matchmaker.outputs.core_analog_cell_paths import create_core_analog_cell_paths
from matchmaker.verification.lvs.cdac_leaf_targets import (
    make_gf180_cdac_leaf_lvs_targets,
)
from matchmaker.verification.lvs.magic_netgen_lvs import run_magic_netgen_lvs
from matchmaker.verification.netlist.xschem_schematic_netlist import (
    run_xschem_schematic_netlist,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export the independent Xschem base-TG/B0 references and run "
            "Magic/Netgen LVS against the generated layouts."
        )
    )
    parser.add_argument(
        "--designs-root",
        type=Path,
        default=Path(os.environ.get("DESIGNS_ROOT", "/foss/designs")),
    )
    parser.add_argument(
        "--target",
        choices=("all", "transmission_gate", "reference_selector"),
        default="all",
    )
    args = parser.parse_args()

    selected = tuple(
        target
        for target in make_gf180_cdac_leaf_lvs_targets(args.designs_root)
        if args.target == "all" or target.name == args.target
    )

    all_passed = True
    for target in selected:
        paths = create_core_analog_cell_paths(
            args.designs_root,
            target.layout_cell_name,
        )
        reference_netlist = (
            paths.netlist_dir / target.reference_netlist_filename
        )

        print(f"\n=== {target.name} ===")
        print(f"layout cell: {target.layout_cell_name}")
        print(f"schematic cell: {target.schematic_cell_name}")
        print(f"schematic: {target.schematic_path}")

        netlist_result = run_xschem_schematic_netlist(
            schematic_path=target.schematic_path,
            schematic_cell_name=target.schematic_cell_name,
            output_netlist_path=reference_netlist,
            designs_root=args.designs_root,
        )
        print(f"schematic netlist passed: {netlist_result.passed}")
        print(f"schematic netlist: {netlist_result.netlist_path}")
        if not netlist_result.passed:
            print(f"schematic netlist failure: {netlist_result.failure_reason}")
            print(netlist_result.process.combined_output[-3000:])
            all_passed = False
            continue

        lvs_result = run_magic_netgen_lvs(
            gds_path=paths.final_gds,
            schematic_netlist_path=reference_netlist,
            cell_name=target.layout_cell_name,
            schematic_cell_name=target.schematic_cell_name,
            layout_netlist_path=paths.extracted_netlist,
            report_path=paths.lvs_report,
        )
        print(f"LVS passed: {lvs_result.passed}")
        print(f"layout netlist: {lvs_result.layout_netlist_path}")
        print(f"LVS report: {lvs_result.report_path}")
        if lvs_result.failure_reason is not None:
            print(f"LVS failure: {lvs_result.failure_reason}")
        if not lvs_result.passed:
            process = lvs_result.lvs_process or lvs_result.extraction_process
            print(process.combined_output[-3000:])
            all_passed = False

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
