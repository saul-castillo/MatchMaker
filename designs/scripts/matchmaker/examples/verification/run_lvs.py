import argparse
import os
from pathlib import Path

from matchmaker.outputs.core_analog_cell_paths import create_core_analog_cell_paths
from matchmaker.verification.lvs.magic_netgen_lvs import run_magic_netgen_lvs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Magic extraction and Netgen LVS for a generated cell."
    )
    parser.add_argument("cell_name", help="Generated layout top-cell name.")
    parser.add_argument("schematic_netlist", type=Path)
    parser.add_argument(
        "--schematic-cell-name",
        help=(
            "Top subcircuit name in the schematic netlist. Defaults to the "
            "generated layout cell name."
        ),
    )
    parser.add_argument(
        "--designs-root",
        type=Path,
        default=Path(os.environ.get("DESIGNS_ROOT", "/foss/designs")),
    )
    args = parser.parse_args()

    paths = create_core_analog_cell_paths(args.designs_root, args.cell_name)
    result = run_magic_netgen_lvs(
        gds_path=paths.final_gds,
        schematic_netlist_path=args.schematic_netlist,
        cell_name=args.cell_name,
        schematic_cell_name=args.schematic_cell_name,
        layout_netlist_path=paths.extracted_netlist,
        report_path=paths.lvs_report,
    )

    print(f"layout cell: {args.cell_name}")
    print(
        "schematic cell: "
        f"{args.schematic_cell_name or args.cell_name}"
    )
    print(f"LVS passed: {result.passed}")
    print(f"layout netlist: {result.layout_netlist_path}")
    print(f"LVS report: {result.report_path}")
    if result.failure_reason is not None:
        print(f"failure: {result.failure_reason}")

    if not result.passed:
        process = result.lvs_process or result.extraction_process
        print("\n--- tool output tail ---")
        print(process.combined_output[-3000:])
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
