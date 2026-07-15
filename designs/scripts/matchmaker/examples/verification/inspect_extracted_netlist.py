import argparse
import os
from pathlib import Path

from matchmaker.outputs.core_analog_cell_paths import create_core_analog_cell_paths
from matchmaker.verification.netlist.spice_inspector import parse_spice_subcircuits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize the extracted SPICE for a generated MatchMaker cell."
    )
    parser.add_argument("cell_name")
    parser.add_argument(
        "--designs-root",
        type=Path,
        default=Path(os.environ.get("DESIGNS_ROOT", "/foss/designs")),
    )
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--shared-net-min",
        type=int,
        default=2,
        help="Show nets used by at least this many top-level X instances.",
    )
    args = parser.parse_args()

    paths = create_core_analog_cell_paths(args.designs_root, args.cell_name)
    if not paths.extracted_netlist.is_file():
        print(f"extracted netlist not found: {paths.extracted_netlist}")
        print(
            "run verify_generated_cell.py or route_two_centroid_gates.py first"
        )
        return 1

    subcircuits = parse_spice_subcircuits(paths.extracted_netlist.read_text())
    print(f"netlist: {paths.extracted_netlist}")
    print(f"subcircuits: {len(subcircuits)}")

    top = subcircuits.get(args.cell_name)
    if top is None:
        print(f"top subcircuit {args.cell_name!r} was not found")
        print("available subcircuits:")
        for name in sorted(subcircuits):
            print(f"  {name}")
        return 1

    print(f"top ports: {' '.join(top.ports) if top.ports else '(none)'}")
    print(f"top device statements: {len(top.device_statements)}")
    print(f"top MOS statements: {len(top.mos_statements)}")
    print(f"top subcircuit instances: {len(top.subcircuit_instance_statements)}")

    shared_nets = top.shared_instance_nets(args.shared_net_min)
    print(f"shared top-instance nets: {len(shared_nets)}")
    for net_name, instance_names in sorted(
        shared_nets.items(),
        key=lambda item: (-len(item[1]), item[0]),
    ):
        print(
            f"  {net_name}: {len(instance_names)} instances -> "
            + ", ".join(instance_names)
        )

    print("\n--- top-level device statements ---")
    for statement in top.device_statements[: args.limit]:
        print(statement)

    remaining = len(top.device_statements) - args.limit
    if remaining > 0:
        print(f"... {remaining} more statements")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
