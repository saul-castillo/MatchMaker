import argparse
import os
from pathlib import Path

from matchmaker.verification.generated_cell_verifier import verify_generated_cell


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run MatchMaker pre-LVS DRC and extraction for a generated cell."
    )
    parser.add_argument("cell_name")
    parser.add_argument(
        "--designs-root",
        type=Path,
        default=Path(os.environ.get("DESIGNS_ROOT", "/foss/designs")),
    )
    parser.add_argument(
        "--drc-only",
        action="store_true",
        help="Skip layout-to-SPICE extraction.",
    )
    args = parser.parse_args()

    result = verify_generated_cell(
        designs_root=args.designs_root,
        cell_name=args.cell_name,
        run_extraction=not args.drc_only,
    )

    print(f"cell: {args.cell_name}")
    print(f"DRC passed: {result.drc.passed}")
    print(f"DRC violations: {result.drc.violation_count}")
    print(f"DRC report: {result.paths.drc_report}")

    if result.extraction is not None:
        print(f"extraction passed: {result.extraction.passed}")
        print(f"extracted netlist: {result.extraction.netlist_path}")
        print(f"extraction report: {result.paths.extraction_report}")
        if result.extraction.failure_reason is not None:
            print(f"extraction failure: {result.extraction.failure_reason}")

    print(f"pre-LVS checks passed: {result.passed}")

    if not result.passed:
        failed_process = (
            result.extraction.process
            if result.extraction is not None and not result.extraction.passed
            else result.drc.process
        )
        print("\n--- tool output tail ---")
        print(failed_process.combined_output[-2500:])
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
